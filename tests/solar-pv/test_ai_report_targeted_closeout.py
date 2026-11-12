"""Bounded Phase D regressions explicitly requested by the closeout review."""
from copy import deepcopy
import pytest
from test_ai_report_engine import catalog, registry, model, protocol_fixture
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.reporting.evidence_pack_builder import build_pack, source_ids
from wangbin_solar_pv.reporting.claim_validator import validate_chapter, render_text
from wangbin_solar_pv.reporting.reader_display import fact_display
from wangbin_solar_pv.reporting.pilot_evidence import terminal_declaration
from wangbin_solar_pv.serialization import digest


@pytest.mark.parametrize('field,value,text', [
    ('project.price_basis', 'nominal', '名义价格'),
    ('project.cashflow_tax_basis', 'post_tax', '项目税后现金流'),
    ('finance.cashflow_timing', 'PERIOD_END', '评价期间期末'),
    ('resource.uncertainty_basis', 'Not quantified as a meteorological confidence interval', '未量化为气象置信区间'),
])
def test_scoped_translation_retains_raw_fact(field, value, text):
    f = {'field_id': field, 'value': value, 'unit': None, 'status': 'ASSUMED'}
    original = deepcopy(f)
    assert fact_display(f) == (text, '')
    assert f == original
    assert fact_display({**f, 'field_id': 'another.field'}) == (value, '')
    assert fact_display({**f, 'value': 'unrecognized'}) == ('unrecognized', '')
    assert fact_display({**f, 'status': 'UNKNOWN'}) == ('尚无可用结果', '')


def test_no_debt_is_not_missing_or_zero_dscr(model, registry):
    pack = build_pack(model, registry, 'CH16', source_ids(model.result))
    debt = pack['facts']['input:finance.debt_ratio']
    assert debt['value'] == 0 and debt['display'] == '0.00' and debt['display_unit'] == '%'
    dscr = pack['facts']['metric:financial.phase3e.dscr']
    assert dscr['value'] is None and dscr['status'] == 'UNDEFINED' and dscr['reason'] == 'ZERO_DEBT_SERVICE'
    assert pack['facts']['metric:financial.phase3e.cfads']['status'] == 'BLOCKED_MISSING_INPUT'
    assert fact_display({**debt, 'value': None}) == ('尚无可用结果', '')


def test_bound_target_fields_and_terminal_records(model, registry):
    before = deepcopy(model.result)
    pack = build_pack(model, registry, 'CH16', source_ids(model.result))
    refs = pack['sections']['CH16.01']['fact_refs']
    residuals = [r for r in refs if r.endswith(':residual_value')]
    assert len(residuals) == 4
    assert all(pack['facts'][r]['status'] == 'ASSUMED' for r in residuals)
    for key in ['mode', 'working_capital_treatment', 'availability']:
        f = pack['facts']['pilot:terminal.' + key]
        assert 'pilot:terminal.' + key in refs
        assert f['provenance']['result_identity'] == model.identity
        assert f['boundary'] == 'DECLARATION_AND_EXISTING_RECORD_NOT_ACTUAL_RECEIPT'
        assert isinstance(f['value'], str) and f['status'] == 'ASSUMED'
    assert not any(r.startswith('pilot:terminal.') for r in pack['sections']['CH16.04']['fact_refs'])
    for field in ['project.evaluation_years', 'project.price_basis', 'project.cashflow_tax_basis', 'finance.cashflow_timing']:
        assert 'input:' + field in pack['sections']['CH16.04']['fact_refs']
    assert model.result == before


@pytest.mark.parametrize('mutation', ['wrong-type', 'wrong-project', 'wrong-scenario', 'wrong-upstream', 'wrong-hash'])
def test_terminal_cross_identity_is_rejected(model, mutation):
    bad = deepcopy(model)
    snap = bad.result['source_snapshot']['phase3e_terminal']
    if mutation == 'wrong-type': snap['binding']['pv_type'] = 'other_type'
    elif mutation == 'wrong-project': snap['binding']['project_id'] = 'another_project'
    elif mutation == 'wrong-scenario': snap['binding']['scenario_id'] = 'CANDIDATE'
    elif mutation == 'wrong-upstream': snap['binding']['phase3d_result_hash'] = '0' * 64
    else: snap['source_content_hash'] = '0' * 64
    snap['binding_hash'] = digest(snap['binding'])
    with pytest.raises(ContractError, match='PILOT_TERMINAL_IDENTITY'):
        terminal_declaration(bad, source_ids(bad.result))


def test_missing_or_unauthorized_terminal_never_becomes_zero(model):
    bad = deepcopy(model)
    assert terminal_declaration(bad, set())[0] == {}
    del bad.result['source_snapshot']['phase3e_terminal']
    facts, reasons = terminal_declaration(bad, source_ids(bad.result))
    assert facts == {} and reasons
    bad = deepcopy(model)
    del bad.result['evidence']['phase3e-terminal-reconciliation']
    facts, reasons = terminal_declaration(bad, source_ids(bad.result))
    assert facts['mode']['value'] == 'NO_DISPOSITION' and 'availability' not in facts and reasons


def test_residual_input_cannot_be_a_calculated_cash_claim(model, registry):
    pack = build_pack(model, registry, 'CH16', source_ids(model.result))
    out = protocol_fixture(pack)
    sec = out['sections'][0]
    ref = next(r for r in pack['sections']['CH16.01']['fact_refs'] if r.endswith(':residual_value'))
    source = pack['facts'][ref]['source_ids']
    text = '处置现金为[[fact:' + ref + ']]。'
    sec['paragraphs'] = [text]
    sec['fact_refs'] = [ref]
    sec['source_refs'] = source
    sec['claims'] = [{'claim_id': sec['claim_ids'][0], 'kind': 'CALCULATED_METRIC', 'text': text,
                      'fact_refs': [ref], 'source_refs': source, 'conditions': [], 'paragraph_indexes': [0],
                      'effect': 'DESCRIPTIVE', 'basis_status': 'LIMITED'}]
    sec['claim_ids'] = [sec['claim_ids'][0]]
    with pytest.raises(ContractError, match='CHAPTER_CLAIM_BASIS'):
        validate_chapter(out, pack, registry.chapter('CH16'))
    with pytest.raises(ContractError, match='CHAPTER_UNBOUND_NUMBER'):
        render_text('终期处置回款为0元。', pack)
    with pytest.raises(ContractError, match='CHAPTER_FACT_REFERENCE'):
        render_text('终期回款[[fact:scenario:another_candidate:terminal_cash]]。', pack)


def test_uncertainty_fact_is_scoped_and_assumed(model, registry):
    pack = build_pack(model, registry, 'CH08', source_ids(model.result))
    ref = 'input:resource.uncertainty_basis'
    assert ref in pack['sections']['CH08.06']['fact_refs']
    assert pack['facts'][ref]['status'] == 'ASSUMED'
    assert render_text('当前资料[[fact:' + ref + ']]。', pack) == '当前资料未量化为气象置信区间。'
    assert pack['facts'][ref]['source_ids'] == [f'SYNTHETIC-PHASE7L-R2-{model.result["pv_type"]}-v2']
