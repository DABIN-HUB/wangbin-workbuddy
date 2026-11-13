"""Explicit, local CH08 host handoff. This module never invokes a model."""
import argparse
from datetime import datetime, timezone
import re

from ..catalog import Catalog
from ..errors import ContractError
from ..local_files import Workspace
from ..report_export import ReportModel
from ..serialization import digest, dumps
from .chapter_registry import Registry
from .chapter_writer import prepare, accept, resume, _request
from .llm_provider import ModelConfig, integration_status
from .report_assembler import assemble_chapter
from .host_workspace import HostWorkspace
from .host_output import PROTOCOL as DELIVERY_PROTOCOL, publish_response, publication_state
from . import host_input_view as input_view

PROTOCOL_VERSION = 'native-host-session/2.0'
NOT_EXPOSED = 'NOT_EXPOSED_BY_HOST'
ORIGINS = {'WORKBUDDY_HOST', 'USER_SUPPLIED', 'PROTOCOL_REPLAY'}


def _relative(workspace, name):
    if not isinstance(name, str) or not name or name.startswith(('/', '\\')) or ':' in name:
        raise ContractError('HOST_RELATIVE_PATH_REQUIRED')
    return workspace.path(name)


def open_session(workspace, run_name, grant_name, catalog, *, create=False):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,95}', run_name):
        raise ContractError('GENERATION_RUN_ID')
    grant, _ = workspace.read(_relative(workspace, grant_name))
    required = {'schema_version', 'canonical', 'canonical_sha256', 'pv_type',
                'authorized_source_ids', 'host_processing_authorized', 'model_config'}
    if (not isinstance(grant, dict) or set(grant) not in (required, required | {'input_view_policy'})
            or grant['schema_version'] != 'host-authorization/2.0'
            or grant['host_processing_authorized'] is not True
            or grant['pv_type'] not in {'industrial_rooftop', 'utility_scale_ground'}):
        raise ContractError('HOST_AUTHORIZATION_REQUIRED')
    if 'input_view_policy' in grant:
        input_view.policy(grant['input_view_policy'])
    sources = grant['authorized_source_ids']
    if (not isinstance(sources, list) or any(not isinstance(s, str) or not s for s in sources)
            or len(set(sources)) != len(sources)):
        raise ContractError('REPORT_SOURCE_AUTHORIZATION')
    canonical, sha = workspace.read(_relative(workspace, grant['canonical']))
    if sha != grant['canonical_sha256']:
        raise ContractError('HOST_CANONICAL_HASH_CHANGED')
    model = ReportModel.from_result(canonical, catalog)
    if canonical['pv_type'] != grant['pv_type']:
        raise ContractError('REPORT_CATEGORY_MISMATCH')
    config = ModelConfig(**grant['model_config'])
    config.to_dict()
    registry = Registry(catalog)
    target = workspace.path(run_name, json_only=False)
    if create and not target.exists():
        target.mkdir(mode=0o700)
    store = HostWorkspace(target)
    binding = {'protocol_version': PROTOCOL_VERSION, 'grant_hash': digest(grant),
               'identity': model.identity, 'spec_hash': registry.hash, 'model_config': config.to_dict()}
    if 'input_view_policy' in grant:
        binding['input_view_policy'] = dict(grant['input_view_policy'])
    with store.lock('host-authorization.json'):
        if store.path('host-authorization.json').exists():
            if store.read('host-authorization.json')[0] != binding:
                raise ContractError('HOST_AUTHORIZATION_CHANGED')
        elif create and not store.path('state.json').exists():
            store._write('host-authorization.json', binding)
        else:
            raise ContractError('HOST_AUTHORIZATION_REQUIRED')
    return store, grant, model, registry, config


def _provenance(store, request_id, accepted=None):
    response, _ = store.read(request_id + '-response.json')
    provenance, _ = store.read(request_id + '-provenance.json')
    keys = {'schema_version', 'request_hash', 'output_hash', 'model_id', 'origin',
            'session_reference', 'call_reference', 'token_usage', 'cost', 'remote_timeout'}
    if (not isinstance(provenance, dict) or set(provenance) != keys
            or provenance['schema_version'] != 'host-provenance/2.0'
            or provenance['origin'] not in ORIGINS):
        raise ContractError('HOST_PROVENANCE_INVALID')
    # No billing/timeout attestation adapter exists. Never accept invented usage.
    if any(provenance[key] != NOT_EXPOSED for key in ('token_usage', 'cost', 'remote_timeout')):
        raise ContractError('HOST_UNVERIFIED_TELEMETRY')
    for key in ('session_reference', 'call_reference'):
        value = provenance[key]
        if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,239}', value):
            raise ContractError('HOST_PROVENANCE_INVALID')
    if (set(response) != {'request_hash', 'model_id', 'host_call_id', 'output'}
            or provenance['request_hash'] != response['request_hash']
            or provenance['output_hash'] != digest(response['output'])
            or provenance['model_id'] != response['model_id']
            or response['host_call_id'] != NOT_EXPOSED):
        raise ContractError('HOST_PROVENANCE_BINDING')
    # A source label never authenticates a provider. Fixture/replay labels must
    # not be used to impersonate a fresh WorkBuddy session.
    if provenance['origin'] == 'WORKBUDDY_HOST' and (
            response['model_id'] == 'protocol-fixture-only'
            or response['model_id'].startswith('hermes-assisted-')):
        raise ContractError('HOST_ORIGIN_CONFLICT')
    if accepted is not None and (accepted['request_hash'] != response['request_hash']
            or accepted['model_id'] != response['model_id']
            or accepted['host_call_id'] != response['host_call_id']
            or accepted['chapter_output_hash'] != provenance['output_hash']):
        raise ContractError('HOST_RESPONSE_CHANGED')
    record = {'schema_version': PROTOCOL_VERSION, 'request_hash': provenance['request_hash'],
              'output_hash': provenance['output_hash'], 'provenance_hash': digest(provenance),
              'origin': provenance['origin'], 'session_reference': provenance['session_reference'],
              'call_reference': provenance['call_reference'],
              'model_execution': 'PROTOCOL_REPLAY' if provenance['origin'] == 'PROTOCOL_REPLAY' else
                                 'USER_SUPPLIED' if provenance['origin'] == 'USER_SUPPLIED' else
                                 'HOST_DECLARED_UNVERIFIED',
              'independent_model_verification': 'NOT_VERIFIED',
              'professional_review': 'PROFESSIONAL_REVIEW_REQUIRED',
              'workbuddy_integration': 'MODEL_INTEGRATION_BLOCKED'}
    return response, record


def checkpoint(store, model, registry, config, allowed_sources, *, input_view_policy=None):
    state = store.read('state.json')[0] if store.path('state.json').exists() else {'requests': []}
    expected_binding = {
            'identity': model.identity, 'spec_hash': registry.hash, 'model_config': config.to_dict(),
            'authorized_sources': sorted(set(allowed_sources)), 'scenario_bundle_hash': digest(None)}
    if input_view_policy is not None:
        expected_binding['input_view_policy'] = input_view.policy(input_view_policy)
    if 'binding' in state and state['binding'] != expected_binding:
        raise ContractError('HOST_AUTHORIZATION_CHANGED')
    items = []
    for row in state['requests']:
        rid = row['request_id']
        if not re.fullmatch(r'CH08-[1-3]', rid) or row['chapter_id'] != 'CH08':
            raise ContractError('HOST_CHAPTER_GATE')
        if not store.path(rid + '-request.json').exists():
            if any(store.path(rid + suffix).exists() for suffix in ('-result.json', '-host-record.json')):
                raise ContractError('HOST_REQUEST_MISSING')
            items.append({'request_id': rid, 'status': 'REQUEST_PUBLICATION_INTERRUPTED',
                          'request_hash': row['request_hash'], 'chapter_id': 'CH08'})
            continue
        request, _ = _request(store, rid, model, registry, config)
        item = {'request_id': rid, 'chapter_id': request['chapter_id'], 'request_hash': request['request_hash']}
        if store.path(rid + '-result.json').exists():
            accepted, _ = resume(store, rid, model, registry, config, _inspection=True)
            _, record = _provenance(store, rid, accepted)
            if store.read(rid + '-host-intent.json')[0] != record:
                raise ContractError('HOST_PROVENANCE_CHANGED')
            if store.path(rid + '-host-record.json').exists():
                if store.read(rid + '-host-record.json')[0] != record:
                    raise ContractError('HOST_PROVENANCE_CHANGED')
                item.update(status='ACCEPTED_REVALIDATED', output_hash=accepted['chapter_output_hash'])
            else:
                item['status'] = 'ACCEPT_RECOVERY_REQUIRED'
        elif store.path(rid + '-failure.json').exists():
            item.update(status='FAILED', code=store.read(rid + '-failure.json')[0]['code'])
        else:
            expired = datetime.now(timezone.utc) > datetime.fromisoformat(request['expires_at'])
            item['status'] = ('EXPIRED' if expired else publication_state(store, request)
                              if request.get('host_delivery') else 'AWAITING_AUTHORIZED_HOST')
        items.append(item)
    cancelled = store.path('host-cancelled.json').exists()
    cursor = next((r['request_id'] for r in reversed(items)
                   if r['status'] in {'AWAITING_AUTHORIZED_HOST', 'ACCEPT_RECOVERY_REQUIRED',
                                      'INCOMPLETE_OUTPUT', 'OUTPUT_PUBLICATION_INTERRUPTED',
                                      'OUTPUT_PUBLISHED_NOT_ACCEPTED'}), None)
    return {'schema_version': PROTOCOL_VERSION, 'requests': items,
            'cursor': None if cancelled else cursor,
            'status': 'CANCELLED_LOCALLY' if cancelled else 'CHECKPOINT_REVALIDATED',
            'remaining_requests': config.max_requests - len(items),
            'remote_cancellation': NOT_EXPOSED, 'workbuddy_integration': 'MODEL_INTEGRATION_BLOCKED'}


def execute(action, workspace, run_name, grant_name, catalog, request_id=None, docx=None):
    if action not in {'prepare', 'prepare-r2', 'prepare-r2-shared', 'publish', 'accept', 'resume', 'checkpoint', 'cancel'}:
        raise ContractError('HOST_ACTION_INVALID')
    store, grant, model, registry, config = open_session(
        workspace, run_name, grant_name, catalog, create=action in {'prepare', 'prepare-r2', 'prepare-r2-shared'})
    # Serializes local host actions; core state/result locks remain unchanged.
    with store.lock('host-operation.json'):
        if action == 'cancel':
            if not store.path('host-cancelled.json').exists():
                store.create('host-cancelled.json', {'status': 'CANCELLED_LOCALLY',
                                                   'remote_cancellation': NOT_EXPOSED})
            return {'status': 'CANCELLED_LOCALLY', 'remote_cancellation': NOT_EXPOSED}
        if action != 'checkpoint' and store.path('host-cancelled.json').exists():
            raise ContractError('HOST_RUN_CANCELLED')
        if action in {'prepare', 'prepare-r2', 'prepare-r2-shared'} and (
                (action == 'prepare-r2-shared') != ('input_view_policy' in grant)):
            raise ContractError('HOST_INPUT_POLICY')
        current = checkpoint(store, model, registry, config, grant['authorized_source_ids'],
                             input_view_policy=grant.get('input_view_policy'))
        if action == 'checkpoint':
            return current
        if docx:
            if action not in {'accept', 'resume'} or not docx.endswith('.docx') or any(c in docx for c in '/\\:'):
                raise ContractError('HOST_RELATIVE_PATH_REQUIRED')
            store.path(docx, json_only=False)
        if action in {'prepare', 'prepare-r2', 'prepare-r2-shared'}:
            req = prepare(HostWorkspace(workspace.root), run_name, model, registry, 'CH08', config,
                          grant['authorized_source_ids'],
                          host_delivery=DELIVERY_PROTOCOL if action != 'prepare' else None,
                          input_view_policy=grant.get('input_view_policy'))
            result = {'request_id': req['request_id'], 'request_hash': req['request_hash'],
                    'execution_state': req['execution_state'],
                    'request_file': run_name + '/' + req['request_id'] + '-request.json',
                    'model_invoked': False}
            if action == 'prepare-r2-shared':
                result['input_view_file'] = run_name + '/' + req['request_id'] + '-input-view.json'
                result['input_manifest_file'] = run_name + '/' + req['request_id'] + '-input-manifest.json'
            return result
        if not isinstance(request_id, str) or not re.fullmatch(r'CH08-[1-3]', request_id):
            raise ContractError('HOST_CHAPTER_GATE')
        if action == 'publish':
            request, pack = _request(store, request_id, model, registry, config)
            return publish_response(store, request, pack, registry.chapter('CH08'), config)
        if action == 'accept':
            response, record = _provenance(store, request_id)
            intent = request_id + '-host-intent.json'
            if store.path(intent).exists():
                if store.read(intent)[0] != record:
                    raise ContractError('HOST_PROVENANCE_CHANGED')
            else:
                store.create(intent, record)
            if store.path(request_id + '-result.json').exists():
                accepted, _ = resume(store, request_id, model, registry, config)
                _provenance(store, request_id, accepted)
            else:
                accepted = accept(store, request_id, response, model, registry, config)
            filename = request_id + '-host-record.json'
            if store.path(filename).exists():
                if store.read(filename)[0] != record:
                    raise ContractError('HOST_PROVENANCE_CHANGED')
            else:
                store.create(filename, record)
        else:
            accepted, _ = resume(store, request_id, model, registry, config)
            _, record = _provenance(store, request_id, accepted)
            if not store.path(request_id + '-host-record.json').exists():
                raise ContractError('HOST_ACCEPT_RECOVERY_REQUIRED')
        result = {'request_id': request_id, 'chapter_output_hash': accepted['chapter_output_hash'],
                  'identity': model.identity, 'host_record': record}
        if docx:
            result['artifact'] = assemble_chapter(store, request_id, model, registry, config, docx)
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['status', 'prepare', 'prepare-r2', 'prepare-r2-shared', 'publish', 'accept',
                                        'resume', 'checkpoint', 'cancel'])
    parser.add_argument('--workspace')
    parser.add_argument('--grant')
    parser.add_argument('--run')
    parser.add_argument('--request-id')
    parser.add_argument('--baseline-dir')
    parser.add_argument('--docx')
    args = parser.parse_args(argv)
    try:
        if args.action == 'status':
            print(dumps({**integration_status(), 'protocol_version': PROTOCOL_VERSION,
                         'pilot_chapters': ['CH08'], 'model_execution': 'HOST_DECLARED_UNVERIFIED',
                         'host_telemetry': NOT_EXPOSED}))
            return 3
        if not all((args.workspace, args.grant, args.run)):
            raise ContractError('HOST_ARGUMENTS_REQUIRED')
        result = execute(args.action, Workspace(args.workspace), args.run, args.grant,
                         Catalog(args.baseline_dir), args.request_id, args.docx)
        print(dumps(result))
        return 0
    except ContractError as exc:
        print(dumps({'status': 'BLOCKED', 'code': exc.code}))
        return 2
    except (OSError, ValueError, KeyError, TypeError):
        print(dumps({'status': 'BLOCKED', 'code': 'HOST_LOCAL_IO_OR_CONTRACT'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
