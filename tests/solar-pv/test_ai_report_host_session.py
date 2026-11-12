"""Explicitly authorized offline host-contract checks. Never AI content evidence."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import json

import pytest

from test_ai_report_engine import catalog, registry, model, protocol_fixture, ROOT
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.local_files import Workspace
from wangbin_solar_pv.serialization import digest, dumps, loads
from wangbin_solar_pv.reporting.evidence_pack_builder import source_ids, build_pack
from wangbin_solar_pv.reporting.claim_validator import validate_chapter
from wangbin_solar_pv.reporting.host_session import execute, open_session, NOT_EXPOSED


@pytest.fixture
def host(tmp_path, model, catalog):
    raw = (ROOT / 'tests/fixtures/solar-pv/phase7l-r2-delivery' / model.result['pv_type'] / 'canonical.json').read_bytes()
    (tmp_path / 'canonical.json').write_bytes(raw)
    grant = {'schema_version': 'host-authorization/2.0', 'canonical': 'canonical.json',
             'canonical_sha256': sha256(raw).hexdigest(), 'pv_type': model.result['pv_type'],
             'authorized_source_ids': sorted(source_ids(model.result)), 'host_processing_authorized': True,
             'model_config': {'model_id': 'protocol-fixture-only', 'timeout_seconds': 3600,
                              'max_request_bytes': 2097152, 'max_output_bytes': 262144, 'max_requests': 2}}
    (tmp_path / 'grant.json').write_text(dumps(grant), encoding='utf8')
    workspace = Workspace(tmp_path)
    def run(action, request_id=None, docx=None):
        return execute(action, workspace, 'run', 'grant.json', catalog, request_id, docx)
    prepared = run('prepare')
    store = Workspace(tmp_path / 'run')
    req = store.read(prepared['request_id'] + '-request.json')[0]
    return workspace, store, grant, req, run


def response_files(store, request):
    output = protocol_fixture(request['evidence_pack'])
    response = {'request_hash': request['request_hash'], 'model_id': request['model_id'],
                'host_call_id': NOT_EXPOSED, 'output': output}
    provenance = {'schema_version': 'host-provenance/2.0', 'request_hash': request['request_hash'],
                  'output_hash': digest(output), 'model_id': request['model_id'], 'origin': 'PROTOCOL_REPLAY',
                  'session_reference': NOT_EXPOSED, 'call_reference': NOT_EXPOSED,
                  'token_usage': NOT_EXPOSED, 'cost': NOT_EXPOSED, 'remote_timeout': NOT_EXPOSED}
    store.create(request['request_id'] + '-response.json', response)
    store.create(request['request_id'] + '-provenance.json', provenance)
    return response, provenance


def replace_json(store, filename, fn):
    obj, old = store.read(filename)
    fn(obj)
    with store.lock(filename):
        store.replace(filename, obj, old)


def test_no_model_missing_response_and_checkpoint(host):
    _, store, _, req, run = host
    assert req['execution_state'] == 'AWAITING_AUTHORIZED_HOST'
    assert not store.path('CH08-1-result.json').exists()
    cp = run('checkpoint')
    assert cp['cursor'] == 'CH08-1' and cp['requests'][0]['status'] == 'AWAITING_AUTHORIZED_HOST'
    with pytest.raises(FileNotFoundError):
        run('accept', 'CH08-1')
    assert not store.path('CH08-1-result.json').exists()


def test_idempotent_accept_and_restart(host, catalog):
    workspace, store, _, req, run = host
    response_files(store, req)
    first = run('accept', 'CH08-1')
    before = store.read('CH08-1-result.json')[1]
    assert run('accept', 'CH08-1') == first
    assert store.read('CH08-1-result.json')[1] == before
    restarted = execute('checkpoint', Workspace(workspace.root), 'run', 'grant.json', catalog)
    assert restarted['requests'][0]['status'] == 'ACCEPTED_REVALIDATED'
    assert first['host_record']['model_execution'] == 'PROTOCOL_REPLAY'
    assert first['host_record']['workbuddy_integration'] == 'MODEL_INTEGRATION_BLOCKED'
    assert first['host_record']['professional_review'] == 'PROFESSIONAL_REVIEW_REQUIRED'


def test_docx_and_nonoverwrite(host):
    _, store, _, req, run = host
    response_files(store, req); run('accept', 'CH08-1')
    result = run('resume', 'CH08-1', 'protocol-only.docx')
    assert result['artifact']['scope'] == 'PARTIAL_CHAPTER_REVIEW_ONLY'
    assert result['artifact']['professional_review'] == 'PENDING_REVIEW'
    with pytest.raises(ContractError, match='OUTPUT_EXISTS'):
        run('resume', 'CH08-1', 'protocol-only.docx')


@pytest.mark.parametrize('field,value', [('origin', 'WORKBUDDY_HOST'), ('token_usage', '100'),
                                       ('output_hash', 'bad'), ('request_hash', 'bad')])
def test_invalid_provenance(host, field, value):
    _, store, _, req, run = host
    response_files(store, req)
    replace_json(store, 'CH08-1-provenance.json', lambda p: p.__setitem__(field, value))
    with pytest.raises(ContractError, match='HOST_'):
        run('accept', 'CH08-1')
    assert not store.path('CH08-1-result.json').exists()


def test_no_fabricated_call_id(host):
    _, store, _, req, run = host
    response_files(store, req)
    replace_json(store, 'CH08-1-response.json', lambda p: p.__setitem__('host_call_id', 'local-uuid'))
    with pytest.raises(ContractError, match='HOST_PROVENANCE_BINDING'):
        run('accept', 'CH08-1')


def test_changed_output_not_idempotent(host):
    _, store, _, req, run = host
    response_files(store, req); run('accept', 'CH08-1')
    replace_json(store, 'CH08-1-response.json', lambda p: p['output'].__setitem__('chapter_intro', '改变正文。'))
    with pytest.raises(ContractError, match='HOST_PROVENANCE_BINDING'):
        run('accept', 'CH08-1')


@pytest.mark.parametrize('field,value', [('authorized_source_ids', []), ('host_processing_authorized', False),
                                       ('canonical', '../outside.json'), ('canonical_sha256', 'bad'),
                                       ('model_config', {'model_id': 'another-model'})])
def test_grant_changes_block_resume(host, field, value):
    workspace, _, _, _, run = host
    replace_json(workspace, 'grant.json', lambda p: p.__setitem__(field, value))
    with pytest.raises(ContractError):
        run('checkpoint')


def test_expiry_and_cancel(host, monkeypatch):
    _, store, _, req, run = host
    response_files(store, req)
    monkeypatch.setattr('wangbin_solar_pv.reporting.chapter_writer._now',
                        lambda: datetime.now(timezone.utc) + timedelta(days=1))
    with pytest.raises(ContractError, match='MODEL_REQUEST_EXPIRED'):
        run('accept', 'CH08-1')
    assert run('checkpoint')['requests'][0]['status'] == 'FAILED'
    assert run('cancel')['status'] == 'CANCELLED_LOCALLY'
    with pytest.raises(ContractError, match='HOST_RUN_CANCELLED'):
        run('prepare')


def test_budget_and_chapter_gate(host):
    _, _, _, _, run = host
    assert run('prepare')['request_id'] == 'CH08-2'
    with pytest.raises(ContractError, match='MODEL_REQUEST_BUDGET_EXHAUSTED'):
        run('prepare')
    with pytest.raises(ContractError, match='HOST_CHAPTER_GATE'):
        run('resume', 'CH10-1')


def test_output_budget(host, catalog):
    workspace, store, _, _, _ = host
    replace_json(workspace, 'grant.json', lambda p: p['model_config'].__setitem__('max_output_bytes', 1))
    execute('prepare', workspace, 'small', 'grant.json', catalog)
    small = Workspace(workspace.root / 'small');req = small.read('CH08-1-request.json')[0]
    response_files(small, req)
    with pytest.raises(ContractError, match='MODEL_OUTPUT_BUDGET_EXCEEDED'):
        execute('accept', workspace, 'small', 'grant.json', catalog, 'CH08-1')


def test_residual_cash_structured_risk_and_free_text_boundary(model, registry):
    pack = build_pack(model, registry, 'CH16', source_ids(model.result))
    output = protocol_fixture(pack)
    section = output['sections'][0]
    ref = next(r for r in pack['sections'][section['section_id']]['fact_refs'] if r.endswith(':residual_value'))
    text = '已验证终期处置回款为[[fact:' + ref + ']]。'
    section.update(paragraphs=[text], fact_refs=[ref], source_refs=pack['facts'][ref]['source_ids'], metric_refs=[])
    claim = section['claims'][0]
    claim.update(text=text, fact_refs=[ref], source_refs=section['source_refs'])
    # Legacy free text has NOT been given a professional pass.
    assert validate_chapter(output, pack, registry.chapter('CH16'))['semantic_gate'] == 'NOT_VERIFIED'
    claim['risk_assertions'] = [{'meaning': 'DISPOSAL_CASH', 'basis': 'ACTUAL', 'fact_refs': [ref]}]
    with pytest.raises(ContractError, match='SEMANTIC_RISK_BLOCKED'):
        validate_chapter(output, pack, registry.chapter('CH16'))


@pytest.mark.parametrize('meaning,ref_suffix', [('PAID_FEE', '.transaction_cost_cash_paid'),
                                              ('EQUITY_RETURN', 'financial.phase3e.project_npv'),
                                              ('DSCR_MULTIPLE', 'financial.phase3e.dscr'),
                                              ('ZERO_VALUE', 'financial.phase3e.dscr')])
def test_risk_boundary_rejects_missing_or_wrong_meaning(model, registry, meaning, ref_suffix):
    from wangbin_solar_pv.reporting.semantic_risks import validate_risk_assertions
    pack = build_pack(model, registry, 'CH16', source_ids(model.result))
    ref = next(r for r in pack['facts'] if r.endswith(ref_suffix))
    claim = {'fact_refs': [ref], 'risk_assertions': [{'meaning': meaning, 'basis': 'FORECAST', 'fact_refs': [ref]}]}
    with pytest.raises(ContractError, match='SEMANTIC_RISK_BLOCKED'):
        validate_risk_assertions(claim, pack['facts'])


def test_forecast_receipt_not_actual_receipt(model, registry):
    from wangbin_solar_pv.reporting.semantic_risks import validate_risk_assertions
    pack = build_pack(model, registry, 'CH16', source_ids(model.result))
    ref = 'pilot:cash.OPERATING_YEAR_1.revenue_cash_receipts'
    claim = {'fact_refs': [ref], 'risk_assertions': [{'meaning': 'CASH_RECEIPT', 'basis': 'FORECAST', 'fact_refs': [ref]}]}
    validate_risk_assertions(claim, pack['facts'])
    claim['risk_assertions'][0]['basis'] = 'ACTUAL'
    with pytest.raises(ContractError, match='SEMANTIC_RISK_BLOCKED'):
        validate_risk_assertions(claim, pack['facts'])


def test_request_publication_crash_consumes_attempt(host):
    _, store, _, _, run = host
    store.path('CH08-1-request.json').unlink()
    cp = run('checkpoint')
    assert cp['requests'][0]['status'] == 'REQUEST_PUBLICATION_INTERRUPTED'
    assert cp['remaining_requests'] == 1
    assert run('prepare')['request_id'] == 'CH08-2'


def test_provenance_publication_crash_recovery(host):
    _, store, _, req, run = host
    response_files(store, req); run('accept', 'CH08-1')
    before = store.read('CH08-1-result.json')[1]
    store.path('CH08-1-host-record.json').unlink()
    assert run('checkpoint')['requests'][0]['status'] == 'ACCEPT_RECOVERY_REQUIRED'
    run('accept', 'CH08-1')
    assert store.read('CH08-1-result.json')[1] == before
    assert run('checkpoint')['requests'][0]['status'] == 'ACCEPTED_REVALIDATED'


def test_cancel_does_not_require_valid_model_output(host):
    _, store, _, req, run = host
    response_files(store, req); run('accept', 'CH08-1')
    replace_json(store, 'CH08-1-response.json', lambda p: p['output'].__setitem__('chapter_intro', '改变正文。'))
    assert run('cancel')['status'] == 'CANCELLED_LOCALLY'
    with pytest.raises(ContractError, match='HOST_RUN_CANCELLED'):
        run('resume', 'CH08-1')


def test_grant_cannot_be_bypassed_by_changing_state_sources(host):
    _, store, _, _, run = host
    replace_json(store, 'state.json', lambda p: p['binding'].__setitem__('authorized_sources', []))
    with pytest.raises(ContractError, match='HOST_AUTHORIZATION_CHANGED'):
        run('checkpoint')


def test_cli_rejects_traversal_before_accept(host):
    _, store, _, req, run = host
    response_files(store, req)
    with pytest.raises(ContractError):
        run('accept', 'CH08-1', '../outside.docx')
    assert not store.path('CH08-1-result.json').exists()


def test_crash_recovery_cannot_relabel_provenance(host):
    _, store, _, req, run = host
    response_files(store, req); run('accept', 'CH08-1')
    store.path('CH08-1-host-record.json').unlink()
    replace_json(store, 'CH08-1-provenance.json', lambda p: p.__setitem__('origin', 'USER_SUPPLIED'))
    with pytest.raises(ContractError, match='HOST_PROVENANCE_CHANGED'):
        run('accept', 'CH08-1')
