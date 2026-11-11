"""Dependency and typed-claim protocol checks; never real model evidence."""
from copy import deepcopy
import pytest

from test_ai_report_engine import catalog, registry, model, protocol_fixture, response_for
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.local_files import Workspace
from wangbin_solar_pv.reporting.chapter_writer import prepare, accept, resume
from wangbin_solar_pv.reporting.claim_validator import validate_chapter, render_text
from wangbin_solar_pv.reporting.evidence_pack_builder import build_pack, source_ids
from wangbin_solar_pv.reporting.llm_provider import ModelConfig


def test_upstream_bound_and_changed_output_invalidates(tmp_path, model, registry):
    workspace = Workspace(tmp_path)
    config = ModelConfig('protocol-fixture-only', timeout_seconds=900)
    sources = source_ids(model.result)
    first = prepare(workspace, 'run', model, registry, 'CH07', config, sources)
    store = Workspace(tmp_path / 'run')
    original = accept(store, first['request_id'], response_for(first), model, registry, config)
    downstream = prepare(workspace, 'run', model, registry, 'CH08', config, sources)
    upstream = downstream['upstream']['CH07']
    assert upstream['chapter_output_hash'] == original['chapter_output_hash']
    assert upstream['professional_review'] == 'PENDING_REVIEW'
    assert upstream['facts'] and upstream['claims']
    accept(store, downstream['request_id'], response_for(downstream), model, registry, config)
    resume(store, downstream['request_id'], model, registry, config)
    second = prepare(workspace, 'run', model, registry, 'CH07', config, sources)
    response = response_for(second)
    response['output']['chapter_findings'] = ['新的协议结果，仍非专业结论。']
    accept(store, second['request_id'], response, model, registry, config)
    with pytest.raises(ContractError, match='CHAPTER_DEPENDENCY_CHANGED'):
        resume(store, downstream['request_id'], model, registry, config)


@pytest.mark.parametrize('mutation', ['claim-id', 'source', 'coverage', 'ready', 'supported', 'unconditional'])
def test_claim_requires_basis(model, registry, mutation):
    pack = build_pack(model, registry, 'CH08', source_ids(model.result))
    output = protocol_fixture(pack)
    claim = output['sections'][0]['claims'][0]
    if mutation == 'claim-id': claim['claim_id'] = 'unbound'
    elif mutation == 'source': claim['source_refs'] = []
    elif mutation == 'coverage': claim['paragraph_indexes'] = [23]
    elif mutation == 'ready': claim['effect'] = 'ENGINEERING_READY'
    elif mutation == 'supported': claim['basis_status'] = 'SUPPORTED'
    elif mutation == 'unconditional': claim['kind'] = 'RECOMMENDATION'
    with pytest.raises(ContractError):
        validate_chapter(output, pack, registry.chapter('CH08'))


def test_controlled_unit_terms_do_not_open_numeric_escape(model, registry):
    pack = build_pack(model, registry, 'CH05', source_ids(model.result))
    assert render_text('辐照量单位为[[term:unit:kWh/m2]]。', pack) == '辐照量单位为kWh/m2。'
    with pytest.raises(ContractError, match='CHAPTER_UNBOUND_NUMBER'):
        render_text('辐照量为100kWh/m2。', pack)
    with pytest.raises(ContractError, match='CHAPTER_TERM_REFERENCE'):
        render_text('[[term:unit:1000万元]]', pack)


def test_summary_and_conclusion_cannot_certify_unreviewed_investment(model, registry):
    for cid in ['CH01', 'CH18']:
        pack = build_pack(model, registry, cid, source_ids(model.result))
        output = protocol_fixture(pack)
        output['decision_state'] = 'NOT_EVALUATED'
        with pytest.raises(ContractError, match='CHAPTER_DECISION_REQUIRES_REVIEW'):
            validate_chapter(output, pack, registry.chapter(cid))
