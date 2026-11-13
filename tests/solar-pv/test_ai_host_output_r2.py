"""User-authorized R2 protocol checks. No fixture is AI writing or host evidence."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from dataclasses import replace

import pytest

from test_ai_report_engine import catalog, registry, model, protocol_fixture
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.local_files import Workspace
from wangbin_solar_pv.serialization import digest, dumps
from wangbin_solar_pv.reporting.claim_validator import check_text, validate_chapter
from wangbin_solar_pv.reporting.evidence_pack_builder import build_pack, source_ids
from wangbin_solar_pv.reporting.host_output import (
    PROTOCOL, NOT_EXPOSED, publish_response, verify_publication, publication_state,
)
from wangbin_solar_pv.reporting.llm_provider import ModelConfig


@pytest.fixture(scope='module')
def evidence(model, registry):
    return build_pack(model, registry, 'CH08', source_ids(model.result)), registry.chapter('CH08')


@pytest.fixture
def draft(tmp_path, evidence):
    pack, chapter = evidence
    request = {'request_id': 'CH08-1', 'host_delivery': PROTOCOL,
               'model_id': 'protocol-fixture-only', 'binding': {'identity': pack['identity']},
               'evidence_pack': pack,
               'expires_at': (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()}
    request['request_hash'] = digest(request)
    response = {'request_hash': request['request_hash'], 'model_id': request['model_id'],
                'host_call_id': NOT_EXPOSED, 'output': protocol_fixture(pack)}
    store = Workspace(tmp_path)
    store.create('CH08-1-draft.json', response)
    config = ModelConfig('protocol-fixture-only', max_output_bytes=262144)
    return store, request, response, pack, chapter, config


def publish(draft):
    store, request, _, pack, chapter, config = draft
    return publish_response(store, request, pack, chapter, config)


def mutate(draft, fn):
    store, _, response, *_ = draft
    fn(response)
    store.path('CH08-1-draft.json').write_text(dumps(response), encoding='utf8')


def test_compact_claims_and_atomic_publication(draft):
    store, request, response, pack, chapter, _ = draft
    assert len(response['output']['sections']) == 6
    assert all(len(s['claims']) == 1 for s in response['output']['sections'])
    assert validate_chapter(response['output'], pack, chapter)['semantic_gate'] == 'NOT_VERIFIED'
    raw = store.path('CH08-1-draft.json').read_bytes()
    assert publication_state(store, request) == 'INCOMPLETE_OUTPUT'
    receipt = publish(draft)
    assert receipt['status'] == 'PUBLISHED_NOT_ACCEPTED'
    assert receipt['raw_draft_sha256'] == sha256(raw).hexdigest()
    assert receipt['output_hash'] == digest(response['output'])
    assert receipt['paragraph_sha256'] == {
        s['section_id']: [sha256(p.encode('utf8')).hexdigest() for p in s['paragraphs']]
        for s in response['output']['sections']}
    assert store.path('CH08-1-draft.json').read_bytes() == raw
    assert store.read('CH08-1-response.json')[0] == response
    assert not store.path('CH08-1-result.json').exists()
    before = store.read('CH08-1-response.json')[1]
    assert publish(draft) == receipt == verify_publication(store, request)
    assert store.read('CH08-1-response.json')[1] == before


@pytest.mark.parametrize('text', ['CH08', 'CH07.01', 'CH08.02-T01', 'PHASE1_METHOD_REVIEW_REQUIRED',
                                 'CH99', '25年', '7.5%', '100万元', '0元', '1.5%', '-2',
                                 '１２年', '年份2026', '普通句子1e9'])
def test_raw_ids_and_numbers_still_rejected(evidence, text):
    pack, _ = evidence
    with pytest.raises(ContractError, match='CHAPTER_UNBOUND_NUMBER'):
        check_text(text, pack['facts'], pack['terms'])


def test_registered_metadata_and_fact_term_slots(evidence):
    pack, chapter = evidence
    output = protocol_fixture(pack)
    validate_chapter(output, pack, chapter)
    ref = next(iter(pack['facts']))
    assert check_text('[[fact:' + ref + ']]', pack['facts'], pack['terms']) == {ref}
    term = next(iter(pack['terms']))
    assert check_text('[[term:' + term + ']]', pack['facts'], pack['terms']) == set()
    with pytest.raises(ContractError, match='CHAPTER_TERM_REFERENCE'):
        check_text('[[term:CH99]]', pack['facts'], pack['terms'])
    with pytest.raises(ContractError, match='CHAPTER_FACT_REFERENCE'):
        check_text('[[fact:invented]]', pack['facts'], pack['terms'])


@pytest.mark.parametrize('failure', ['paragraph-lineage', 'source', 'support', 'risk-zero', 'risk-paid',
                                    'risk-actual', 'risk-disposal', 'wrong-fact', 'missing-paragraph',
                                    'wrong-chapter', 'wrong-order', 'missing-section', 'wrong-table'])
def test_original_strict_rules_not_relaxed(evidence, failure):
    pack, chapter = evidence
    output = protocol_fixture(pack)
    section = output['sections'][0]
    claim = section['claims'][0]
    code = None
    if failure == 'paragraph-lineage':
        extra = next(f for f in pack['sections'][section['section_id']]['fact_refs'] if f not in claim['fact_refs'])
        section['paragraphs'][0] += '并列引用[[fact:' + extra + ']]。'
        code = 'CHAPTER_CLAIM_PARAGRAPH_LINEAGE'
    elif failure == 'source':
        claim['source_refs'] = []
        code = 'CHAPTER_CLAIM_LINEAGE'
    elif failure in {'support', 'risk-zero', 'risk-paid', 'risk-actual', 'risk-disposal'}:
        section = next(s for s in output['sections'] if any(
            pack['facts'][f]['status'] == 'ASSUMED' for f in pack['sections'][s['section_id']]['fact_refs']))
        ref = next(f for f in pack['sections'][section['section_id']]['fact_refs'] if pack['facts'][f]['status'] == 'ASSUMED')
        text = '这只是未核验的协议引用[[fact:' + ref + ']]。'
        section.update(paragraphs=[text], fact_refs=[ref], source_refs=pack['facts'][ref]['source_ids'], metric_refs=[])
        claim = section['claims'][0]
        claim.update(text=text, fact_refs=[ref], source_refs=section['source_refs'])
        if failure == 'support':
            claim['basis_status'] = 'SUPPORTED'; code = 'CHAPTER_CLAIM_SUPPORT_STATE'
        else:
            meaning = {'risk-zero': 'ZERO_VALUE', 'risk-paid': 'PAID_FEE',
                       'risk-actual': 'CASH_RECEIPT', 'risk-disposal': 'DISPOSAL_CASH'}[failure]
            claim['risk_assertions'] = [{'meaning': meaning, 'basis': 'ACTUAL' if failure == 'risk-actual' else 'FORECAST', 'fact_refs': [ref]}]
            code = 'SEMANTIC_RISK_BLOCKED'
    elif failure == 'wrong-fact': claim['fact_refs'] = ['invented']; code = 'CHAPTER_CLAIM_LINEAGE'
    elif failure == 'missing-paragraph': section['paragraphs'].append('额外协议段落。'); code = 'CHAPTER_CLAIM_COVERAGE'
    elif failure == 'wrong-chapter': output['chapter_id'] = 'CH99'; code = 'CHAPTER_IDENTITY'
    elif failure == 'wrong-order': output['sections'].reverse(); code = 'CHAPTER_SECTION_COVERAGE'
    elif failure == 'missing-section': output['sections'].pop(); code = 'CHAPTER_SECTION_COVERAGE'
    elif failure == 'wrong-table': section['table_refs'] = ['CH99-T01']; code = 'CHAPTER_SCOPED_REFERENCE'
    with pytest.raises(ContractError, match=code):
        validate_chapter(output, pack, chapter)


def test_undeclared_free_text_risk_is_never_professional_pass(evidence):
    pack, chapter = evidence
    output = protocol_fixture(pack)
    output['chapter_intro'] = '合成数据是实测，所有公式均获批，残值就是现金。'
    result = validate_chapter(output, pack, chapter)
    assert result['semantic_gate'] == 'NOT_VERIFIED'
    assert result['professional_review'] == 'PENDING_REVIEW'


@pytest.mark.parametrize('fragment', ['{', '{"output":{}}', '{"output":{}', ''])
def test_incomplete_and_envelope_failures_preserved(draft, fragment):
    store, request, *_ = draft
    path = store.path('CH08-1-draft.json'); path.write_text(fragment, encoding='utf8')
    before = path.read_bytes()
    expected = 'MODEL_RESPONSE_ENVELOPE' if fragment == '{"output":{}}' else 'INCOMPLETE_OUTPUT'
    with pytest.raises(ContractError, match=expected): publish(draft)
    assert path.read_bytes() == before
    assert store.read('CH08-1-failure.json')[0]['code'] == expected
    assert not store.path('CH08-1-response.json').exists()
    assert not store.path('CH08-1-result.json').exists()
    with pytest.raises(ContractError, match='CHAPTER_ATTEMPT_ALREADY_CLOSED'): publish(draft)


@pytest.mark.parametrize('field', ['request_hash', 'model_id', 'host_call_id'])
def test_response_identity(draft, field):
    mutate(draft, lambda r: r.__setitem__(field, 'incorrect'))
    with pytest.raises(ContractError, match='MODEL_RESPONSE_IDENTITY'): publish(draft)


def test_expired(draft):
    draft[1]['expires_at'] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    with pytest.raises(ContractError, match='MODEL_REQUEST_EXPIRED'): publish(draft)


def test_output_budget(draft):
    store, request, _, pack, chapter, config = draft
    with pytest.raises(ContractError, match='MODEL_OUTPUT_BUDGET_EXCEEDED'):
        publish_response(store, request, pack, chapter, replace(config, max_output_bytes=1))


def test_published_newline_counts_toward_budget(draft):
    store, request, response, pack, chapter, config = draft
    raw = dumps(response).encode('utf8')
    store.path('CH08-1-draft.json').write_bytes(raw)
    with pytest.raises(ContractError, match='MODEL_OUTPUT_BUDGET_EXCEEDED'):
        publish_response(store, request, pack, chapter, replace(config, max_output_bytes=len(raw)))
    assert not store.path('CH08-1-response.json').exists()


def test_response_no_clobber(draft):
    store = draft[0]
    store.create('CH08-1-response.json', {'protected': True})
    before = store.read('CH08-1-response.json')[1]
    with pytest.raises(ContractError, match='OUTPUT_EXISTS'): publish(draft)
    assert store.read('CH08-1-response.json')[1] == before


@pytest.mark.parametrize('target', ['draft', 'response', 'publication', 'publication-intent'])
def test_publication_mutation(draft, target):
    publish(draft)
    store, request, *_ = draft
    path = store.path('CH08-1-' + target + '.json')
    value = store.read(path)[0]
    if target in {'draft', 'response'}: value['output']['chapter_intro'] = '改变的协议文字。'
    else: value['request_hash'] = 'changed'
    path.write_text(dumps(value), encoding='utf8')
    with pytest.raises(ContractError, match='HOST_PUBLICATION_CHANGED'):
        verify_publication(store, request)


@pytest.mark.parametrize('crash_at', ['response', 'publication'])
def test_publication_crash_recovery_same_bytes_only(draft, monkeypatch, crash_at):
    store, request, response, *_ = draft
    original = store.create
    def interrupted(name, data):
        if name == 'CH08-1-' + crash_at + '.json': raise OSError('simulated publication interruption')
        return original(name, data)
    monkeypatch.setattr(store, 'create', interrupted)
    with pytest.raises(OSError): publish(draft)
    assert publication_state(store, request) == 'OUTPUT_PUBLICATION_INTERRUPTED'
    assert not store.path('CH08-1-result.json').exists()
    monkeypatch.setattr(store, 'create', original)
    assert publish(draft)['output_hash'] == digest(response['output'])
    assert store.read('CH08-1-response.json')[0] == response


def test_changed_draft_not_recoverable(draft, monkeypatch):
    store = draft[0]; original = store.create
    def interrupted(name, data):
        if name.endswith('-publication.json'): raise OSError('simulated publication interruption')
        return original(name, data)
    monkeypatch.setattr(store, 'create', interrupted)
    with pytest.raises(OSError): publish(draft)
    monkeypatch.setattr(store, 'create', original)
    mutate(draft, lambda r: r['output'].__setitem__('chapter_intro', '不同的协议文字。'))
    with pytest.raises(ContractError, match='HOST_PUBLICATION_CHANGED'): publish(draft)
    assert not store.path('CH08-1-publication.json').exists()
