"""Existing producer summaries are projected, never calculated by prose."""
from copy import deepcopy
import pytest
from test_ai_report_engine import catalog, registry, model
from wangbin_solar_pv.reporting.evidence_pack_builder import build_pack, source_ids
from wangbin_solar_pv.reporting.pilot_evidence import pilot_facts
from wangbin_solar_pv.errors import ContractError


def test_annual_settlement_is_exact_source_projection(model, registry):
    pack = build_pack(model, registry, 'CH10', source_ids(model.result))
    ledger = model.metric('revenue.year.1')['details']['ledger']
    for key in ['export_kwh', 'export_sales_revenue', 'gross_benefit', 'transaction_cost']:
        f = pack['facts']['pilot:settlement.' + key]
        assert f['value'] == ledger[key]
        assert f['provenance']['result_identity'] == model.identity
        assert ('pilot:settlement.' + key) in pack['sections']['CH10.02']['fact_refs']
    if model.result['pv_type'] == 'industrial_rooftop':
        assert pack['facts']['pilot:settlement.self_value']['value'] == ledger['self_value']
        assert pack['facts']['pilot:settlement.self_ratio']['value'] == model.metric('consumption.self_ratio.year.1')['value']
    else:
        assert 'pilot:settlement.self_value' not in pack['facts']
        assert pack['facts']['pilot:method.settlement.price_source']['value'] == 'MARKET_SERIES'
        assert not any('load.' in x for x in pack['sections']['CH10.01']['missing_evidence'])


def test_generation_loss_is_not_double_deducted(model, registry):
    p = build_pack(model, registry, 'CH08', source_ids(model.result))
    assert p['facts']['pilot:energy.loss.curtailment']['value'] == model.metric('energy.year.1')['details']['losses_kwh']['curtailment']
    assert p['facts']['pilot:energy.available']['value'] == model.metric('available_kwh.year.1')['value']


def test_missing_cash_payment_never_inherits_accrual(model, registry):
    p = build_pack(model, registry, 'CH16', source_ids(model.result))
    f = p['facts']['pilot:cash.OPERATING_YEAR_1.transaction_cost_cash_paid']
    assert f['value'] is None and f['status'] == 'UNKNOWN'
    assert f['display'] == '尚无可用结果'
    assert p['facts']['pilot:cash.OPERATING_YEAR_1.revenue_cash_receipts']['value'] == model.result['evidence']['financial-ledger']['annual'][1]['revenue_cash_receipts']
    assert p['tables']['CH16.02-T01']['fact_ids'] == ['metric:financial.phase3e.project_cash_flow:item:' + str(i) for i in range(26)]


def test_no_authorization_no_pilot_values(model):
    assert pilot_facts(model, 'CH10.02', set())[0] == {}


def test_wrong_period_rejected(model):
    bad = deepcopy(model)
    bad.result['evidence']['financial-ledger']['annual'][1]['period'] = 'CONSTRUCTION'
    with pytest.raises(ContractError, match='PILOT_LEDGER_PERIOD_IDENTITY'):
        pilot_facts(bad, 'CH16.01', source_ids(model.result))


def test_method_license_not_inherited_from_result(model):
    bad = deepcopy(model)
    bad.result['source_snapshot']['methods']['parameters']['settlement.price_source']['license_status'] = 'UNKNOWN'
    assert 'pilot:method.settlement.price_source' not in pilot_facts(bad, 'CH10.05', source_ids(model.result))[0]
