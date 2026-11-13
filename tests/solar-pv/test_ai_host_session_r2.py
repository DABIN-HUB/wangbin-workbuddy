"""Real local native-session wiring over synthetic canonicals; NOT WorkBuddy E2E."""
from hashlib import sha256
import subprocess
import sys

import pytest

from test_ai_report_engine import catalog, registry, model, protocol_fixture, ROOT
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.local_files import Workspace
from wangbin_solar_pv.serialization import dumps, digest
from wangbin_solar_pv.reporting.chapter_writer import prepare, accept, resume
from wangbin_solar_pv.reporting.evidence_pack_builder import source_ids
from wangbin_solar_pv.reporting.host_output import PROTOCOL, publish_response, NOT_EXPOSED
from wangbin_solar_pv.reporting.host_session import execute
from wangbin_solar_pv.reporting.host_workspace import HostWorkspace
from wangbin_solar_pv.reporting.llm_provider import ModelConfig


@pytest.fixture
def prepared_r2(tmp_path, model, registry):
    config = ModelConfig('protocol-fixture-only', timeout_seconds=3600, max_request_bytes=2097152,
                         max_output_bytes=262144, max_requests=2)
    request = prepare(HostWorkspace(tmp_path), 'run', model, registry, 'CH08', config,
                      source_ids(model.result), host_delivery=PROTOCOL)
    store = HostWorkspace(tmp_path / 'run')
    response = {'request_hash': request['request_hash'], 'model_id': config.model_id,
                'host_call_id': NOT_EXPOSED, 'output': protocol_fixture(request['evidence_pack'])}
    store.create('CH08-1-draft.json', response)
    return store, request, response, config


def provenance(request, response):
    return {'schema_version': 'host-provenance/2.0', 'request_hash': request['request_hash'],
            'output_hash': digest(response['output']), 'model_id': request['model_id'],
            'origin': 'PROTOCOL_REPLAY', 'session_reference': NOT_EXPOSED,
            'call_reference': NOT_EXPOSED, 'token_usage': NOT_EXPOSED,
            'cost': NOT_EXPOSED, 'remote_timeout': NOT_EXPOSED}


def test_real_native_cli_roundtrip(tmp_path, model, registry, catalog):
    raw = (ROOT / 'tests/fixtures/solar-pv/phase7l-r2-delivery' / model.result['pv_type'] / 'canonical.json').read_bytes()
    (tmp_path / 'canonical.json').write_bytes(raw)
    config = ModelConfig('protocol-fixture-only', timeout_seconds=3600, max_request_bytes=2097152,
                         max_output_bytes=262144, max_requests=2)
    grant = {'schema_version': 'host-authorization/2.0', 'canonical': 'canonical.json',
             'canonical_sha256': sha256(raw).hexdigest(), 'pv_type': model.result['pv_type'],
             'authorized_source_ids': sorted(source_ids(model.result)),
             'host_processing_authorized': True, 'model_config': config.to_dict()}
    workspace = Workspace(tmp_path); workspace.create('grant.json', grant)
    def run(action, request_id=None, docx=None):
        return execute(action, workspace, 'native', 'grant.json', catalog, request_id, docx)
    item = run('prepare-r2'); store = HostWorkspace(tmp_path / 'native')
    request = store.read(item['request_id'] + '-request.json')[0]
    assert request['host_delivery'] == PROTOCOL
    assert request['request_hash'] == digest({k: v for k, v in request.items() if k != 'request_hash'})
    assert len(request['writing_guidance']) > 0 and item['model_invoked'] is False
    response = {'request_hash': request['request_hash'], 'model_id': request['model_id'],
                'host_call_id': NOT_EXPOSED, 'output': protocol_fixture(request['evidence_pack'])}
    store.create('CH08-1-draft.json', response)
    assert run('publish', 'CH08-1')['status'] == 'PUBLISHED_NOT_ACCEPTED'
    # Actual generic CLI processes must not consume or poison the native run.
    for action in ('prepare', 'accept', 'resume'):
        command = [sys.executable, '-B', '-m', 'wangbin_solar_pv.reporting', action,
                   '--canonical', str(tmp_path / 'canonical.json'), '--workspace', str(tmp_path),
                   '--run', 'native', '--model', config.model_id, '--request-id', 'CH08-1',
                   '--response', 'CH08-1-response.json', '--chapter', 'CH08', '--docx', 'bypass.docx']
        blocked = subprocess.run(command, capture_output=True, text=True, timeout=20)
        assert blocked.returncode == 2 and 'HOST_NATIVE_ENTRY_REQUIRED' in blocked.stdout
    assert not store.path('CH08-1-result.json').exists()
    assert not store.path('CH08-1-failure.json').exists()
    assert not store.path('bypass.docx', json_only=False).exists()
    store.create('CH08-1-provenance.json', provenance(request, response))
    accepted = run('accept', 'CH08-1')
    assert accepted['host_record']['model_execution'] == 'PROTOCOL_REPLAY'
    artifact = run('resume', 'CH08-1', 'protocol-only.docx')['artifact']
    assert artifact['scope'] == 'PARTIAL_CHAPTER_REVIEW_ONLY'
    assert artifact['professional_review'] == 'PENDING_REVIEW'
    assert store.path('protocol-only.docx', json_only=False).is_file()
    assert (tmp_path / 'canonical.json').read_bytes() == raw
    assert run('cancel')['status'] == 'CANCELLED_LOCALLY'
    assert run('checkpoint')['status'] == 'CANCELLED_LOCALLY'
    with pytest.raises(ContractError, match='HOST_RUN_CANCELLED'):
        resume(store, 'CH08-1', model, registry, config)


def test_core_accept_cannot_skip_publication(prepared_r2, model, registry):
    store, request, response, config = prepared_r2
    with pytest.raises(ContractError, match='INCOMPLETE_OUTPUT'):
        accept(store, request['request_id'], response, model, registry, config)
    assert not store.path('CH08-1-result.json').exists()


def test_core_resume_rechecks_publication(prepared_r2, model, registry):
    store, request, response, config = prepared_r2
    publish_response(store, request, request['evidence_pack'], registry.chapter('CH08'), config)
    accept(store, 'CH08-1', response, model, registry, config)
    before = store.read('CH08-1-result.json')[1]
    assert resume(store, 'CH08-1', model, registry, config)[0]['chapter_output_hash'] == digest(response['output'])
    store.path('CH08-1-publication.json').unlink()
    with pytest.raises(ContractError, match='INCOMPLETE_OUTPUT'):
        resume(store, 'CH08-1', model, registry, config)
    assert store.read('CH08-1-result.json')[1] == before


@pytest.mark.parametrize('action', ['accept', 'publish', 'prepare', 'resume'])
def test_core_cancel_guard(prepared_r2, model, registry, action):
    store, request, response, config = prepared_r2
    publish_response(store, request, request['evidence_pack'], registry.chapter('CH08'), config)
    if action == 'resume':
        accept(store, 'CH08-1', response, model, registry, config)
    store.create('host-cancelled.json', {'status': 'CANCELLED_LOCALLY'})
    with pytest.raises(ContractError, match='HOST_RUN_CANCELLED'):
        if action == 'accept':
            accept(store, 'CH08-1', response, model, registry, config)
        elif action == 'resume':
            resume(store, 'CH08-1', model, registry, config)
        elif action == 'publish':
            publish_response(store, request, request['evidence_pack'], registry.chapter('CH08'), config)
        else:
            prepare(HostWorkspace(store.root.parent), 'run', model, registry, 'CH08', config,
                    source_ids(model.result), host_delivery=PROTOCOL)
    if action != 'resume':
        assert not store.path('CH08-1-result.json').exists()


def test_failed_output_uses_remaining_budget(prepared_r2, model, registry):
    store, request, _, config = prepared_r2
    store.path('CH08-1-draft.json').write_text('{', encoding='utf8')
    with pytest.raises(ContractError, match='INCOMPLETE_OUTPUT'):
        publish_response(store, request, request['evidence_pack'], registry.chapter('CH08'), config)
    second = prepare(HostWorkspace(store.root.parent), 'run', model, registry, 'CH08', config,
                     source_ids(model.result), host_delivery=PROTOCOL)
    assert second['request_id'] == 'CH08-2'
    with pytest.raises(ContractError, match='MODEL_REQUEST_BUDGET_EXHAUSTED'):
        prepare(HostWorkspace(store.root.parent), 'run', model, registry, 'CH08', config,
                source_ids(model.result), host_delivery=PROTOCOL)


def test_actual_process_exit_during_publication(prepared_r2, model, registry):
    store, request, response, config = prepared_r2
    script = '''import os, sys
from wangbin_solar_pv.reporting.host_workspace import HostWorkspace
from wangbin_solar_pv.reporting.host_output import publish_response
from wangbin_solar_pv.reporting.llm_provider import ModelConfig
store = HostWorkspace(sys.argv[1])
request = store.read('CH08-1-request.json')[0]
original = store.create
def crash(name, data):
    original(name, data)
    if name == 'CH08-1-response.json':
        os._exit(23)
store.create = crash
with store.lock('host-operation.json'):
    publish_response(store, request, request['evidence_pack'], request['chapter_spec'], ModelConfig(**request['binding']['model_config']))
'''
    process = subprocess.run([sys.executable, '-B', '-c', script, str(store.root)],
                             capture_output=True, text=True, timeout=20)
    assert process.returncode == 23, process.stderr
    assert store.path('CH08-1-response.json').exists()
    assert not store.path('CH08-1-publication.json').exists()
    before = store.read('CH08-1-response.json')[1]
    with store.lock('host-operation.json'):
        receipt = publish_response(store, request, request['evidence_pack'], registry.chapter('CH08'), config)
    assert receipt['output_hash'] == digest(response['output'])
    assert store.read('CH08-1-response.json')[1] == before
    assert not store.path('CH08-1-result.json').exists()
