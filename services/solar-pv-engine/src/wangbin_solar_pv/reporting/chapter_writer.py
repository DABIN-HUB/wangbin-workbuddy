"""Durable bounded host exchange; no pretend model calls or mutable success cache."""
from datetime import datetime, timedelta, timezone
import re
from uuid import uuid4

from ..errors import ContractError
from ..local_files import Workspace
from ..serialization import digest, dumps
from .chapter_result_schema import result_schema
from .claim_validator import validate_chapter, SLOT
from .evidence_pack_builder import build_pack
from .llm_provider import ModelConfig


def _now():
    return datetime.now(timezone.utc)


def _id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,95}', value):
        raise ContractError('GENERATION_RUN_ID')
    return value


def _upstream(store, state, chapter, model, registry, config, cache):
    dependencies = {}
    for cid in chapter['dependencies']:
        candidates = [r for r in state['requests'] if r['chapter_id'] == cid
                      and store.path(r['request_id'] + '-result.json').exists()]
        if not candidates:
            dependencies[cid] = {'status': 'NOT_SUPPLIED_DO_NOT_INVENT'}
            continue
        rid = candidates[-1]['request_id']
        if rid not in cache:
            cache[rid] = resume(store, rid, model, registry, config, _cache=cache)
        accepted, evidence = cache[rid]
        used = {ref for section in accepted['output']['sections'] for ref in section['fact_refs']}
        for text in [accepted['output']['chapter_intro'], *accepted['output']['chapter_findings'], *accepted['output']['decision_implications']]:
            used.update(SLOT.findall(text))
        dependencies[cid] = {
            'status': 'REFERENCES_VALID_SEMANTICS_PENDING_NOT_ENGINEERING_FACT',
            'request_id': rid, 'identity': accepted['identity'],
            'chapter_output_hash': accepted['chapter_output_hash'],
            'evidence_hash': accepted['evidence_hash'],
            'findings': accepted['output']['chapter_findings'],
            'decision_implications': accepted['output']['decision_implications'],
            'claims': [claim for section in accepted['output']['sections'] for claim in section['claims']],
            'facts': {ref: evidence['facts'][ref] for ref in sorted(used)},
            'professional_review': accepted['professional_review'],
            'decision_state': accepted['output']['decision_state']}
    return dependencies


def prepare(workspace, run_name, model, registry, chapter_id, config, allowed_source_ids):
    _id(run_name)
    cfg = config.to_dict()
    pack = build_pack(model, registry, chapter_id, allowed_source_ids)
    chapter = registry.chapter(chapter_id)
    binding = {'identity': model.identity, 'spec_hash': registry.hash, 'model_config': cfg,
               'authorized_sources': sorted(set(allowed_source_ids))}
    root = workspace.path(run_name, json_only=False)
    if not root.exists():
        root.mkdir(mode=0o700)
    store = Workspace(root)
    # Shared run lock covers initialization, reservation and request publication.
    with store.lock('state.json'):
        if store.path('state.json').exists():
            state, old_hash = store.read('state.json')
            if state['binding'] != binding:
                raise ContractError('GENERATION_CACHE_IDENTITY_CHANGED')
        else:
            state = {'binding': binding, 'generation_run_id': str(uuid4()), 'requests': []}
            old_hash = None
        attempts = sum(r['chapter_id'] == chapter_id for r in state['requests'])
        if attempts >= cfg['max_attempts_per_chapter'] or len(state['requests']) >= cfg['max_requests']:
            raise ContractError('MODEL_REQUEST_BUDGET_EXHAUSTED')
        request_id = f'{chapter_id}-{attempts + 1}'
        upstream = _upstream(store, state, chapter, model, registry, config, {})
        request = {'schema_version': 'chapter-request/2.0', 'request_id': request_id,
                   'generation_run_id': state['generation_run_id'], 'binding': binding,
                   'chapter_id': chapter_id, 'report_spec_version': pack['report_spec_version'],
                   'prompt_version': pack['prompt_version'], 'model_id': cfg['model_id'],
                   'created_at': _now().isoformat(),
                   'expires_at': (_now() + timedelta(seconds=cfg['timeout_seconds'])).isoformat(),
                   'instructions': registry.spec['global_rules'], 'chapter_spec': chapter,
                   'evidence_pack': pack, 'output_schema': result_schema(),
                   'upstream': upstream, 'dependency_hash': digest(upstream),
                   'upstream_status': {cid: item['status'] for cid, item in upstream.items()},
                   'decision_gate': 'DEFER_ONLY_PENDING_PROFESSIONAL_REVIEW',
                   'execution_state': 'AWAITING_AUTHORIZED_HOST',
                   'semantic_review': 'PENDING_REVIEW'}
        request['request_hash'] = digest(request)
        if len(dumps(request).encode('utf-8')) > cfg['max_request_bytes']:
            raise ContractError('MODEL_CONTEXT_BUDGET_EXCEEDED')
        state['requests'].append({'request_id': request_id, 'chapter_id': chapter_id,
                                  'request_hash': request['request_hash']})
        # A crash consumes the reservation, not an unbounded retry opportunity.
        store._write('state.json', state, expected_digest=old_hash)
        store.create(request_id + '-request.json', request)
    return request


def _request(store, request_id, model, registry, config, _cache=None):
    _id(request_id)
    request, _ = store.read(request_id + '-request.json')
    if request['request_hash'] != digest({k: v for k, v in request.items() if k != 'request_hash'}):
        raise ContractError('CHAPTER_REQUEST_HASH')
    state, _ = store.read('state.json')
    if (request['binding'] != state['binding'] or request['generation_run_id'] != state['generation_run_id']
            or not any(r['request_id'] == request_id and r['request_hash'] == request['request_hash']
                       for r in state['requests'])):
        raise ContractError('CHAPTER_REQUEST_RESERVATION')
    if (request['binding']['identity'] != model.identity or request['binding']['spec_hash'] != registry.hash
            or request['binding']['model_config'] != config.to_dict()):
        raise ContractError('GENERATION_CACHE_IDENTITY_CHANGED')
    pack = build_pack(model, registry, request['chapter_id'], request['binding']['authorized_sources'])
    if pack != request['evidence_pack'] or request['chapter_spec'] != registry.chapter(request['chapter_id']):
        raise ContractError('CHAPTER_EVIDENCE_CHANGED')
    upstream = _upstream(store, state, registry.chapter(request['chapter_id']), model, registry, config,
                         {} if _cache is None else _cache)
    if request.get('upstream') != upstream or request.get('dependency_hash') != digest(upstream):
        raise ContractError('CHAPTER_DEPENDENCY_CHANGED')
    return request, pack


def accept(store, request_id, response, model, registry, config):
    _id(request_id)
    with store.lock(request_id + '-result.json'):
        if store.path(request_id + '-result.json').exists() or store.path(request_id + '-failure.json').exists():
            raise ContractError('CHAPTER_ATTEMPT_ALREADY_CLOSED')
        try:
            request, pack = _request(store, request_id, model, registry, config)
            if _now() > datetime.fromisoformat(request['expires_at']):
                raise ContractError('MODEL_REQUEST_EXPIRED')
            if len(dumps(response).encode('utf-8')) > config.max_output_bytes:
                raise ContractError('MODEL_OUTPUT_BUDGET_EXCEEDED')
            if not isinstance(response, dict) or set(response) != {'request_hash', 'model_id', 'host_call_id', 'output'}:
                raise ContractError('MODEL_RESPONSE_ENVELOPE')
            if response['request_hash'] != request['request_hash'] or response['model_id'] != config.model_id:
                raise ContractError('MODEL_RESPONSE_IDENTITY')
            _id(response['host_call_id'])
            validation = validate_chapter(response['output'], pack, registry.chapter(request['chapter_id']))
            accepted = {'generation_run_id': request['generation_run_id'], 'request_hash': request['request_hash'],
                        'identity': model.identity, 'report_spec_version': pack['report_spec_version'],
                        'prompt_version': pack['prompt_version'], 'model_id': config.model_id,
                        'host_call_id': response['host_call_id'], 'chapter_id': request['chapter_id'],
                        'output': response['output'], **validation,
                        'dependency_hash': request['dependency_hash'],
                        'model_execution': ('PROTOCOL_FIXTURE' if config.model_id == 'protocol-fixture-only' else
                                            'HERMES_ASSISTED_UNVERIFIED' if config.model_id.startswith('hermes-assisted-') else
                                            'HOST_DECLARED_UNVERIFIED'),
                        'llm_integration': 'HOST_DECLARED_NOT_INDEPENDENTLY_VERIFIED'}
            store._write(request_id + '-result.json', accepted)
            return accepted
        except ContractError as exc:
            # Preserve only the stable code; never log an arbitrary model/provider error body.
            store.create(request_id + '-failure.json', {'request_id': request_id, 'code': exc.code,
                                                        'status': 'FAILED', 'recorded_at': _now().isoformat()})
            raise


def resume(store, request_id, model, registry, config, _cache=None):
    request, pack = _request(store, request_id, model, registry, config, _cache)
    accepted, _ = store.read(request_id + '-result.json')
    keys = ('request_hash', 'generation_run_id', 'report_spec_version', 'prompt_version', 'model_id', 'chapter_id', 'dependency_hash')
    if (any(accepted.get(key) != request[key] for key in keys) or accepted['identity'] != model.identity
            or accepted.get('llm_integration') != 'HOST_DECLARED_NOT_INDEPENDENTLY_VERIFIED'):
        raise ContractError('CHAPTER_CACHE_IDENTITY')
    validation = validate_chapter(accepted['output'], pack, registry.chapter(request['chapter_id']))
    if any(accepted.get(k) != v for k, v in validation.items()):
        raise ContractError('CHAPTER_CACHE_OUTPUT_CHANGED')
    return accepted, pack
