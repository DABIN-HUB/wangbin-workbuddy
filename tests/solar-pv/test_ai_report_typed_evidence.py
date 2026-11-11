"""Typed adapters: synthetic inputs remain assumptions, not AI pilot content."""
from copy import deepcopy

import pytest

from test_ai_report_engine import catalog, registry, model
from wangbin_solar_pv.reporting.evidence_pack_builder import build_pack, source_ids, safe_text
from wangbin_solar_pv.reporting.evidence_adapters import input_facts


def test_resource_children_have_real_instances_and_periods(model, registry):
    pack = build_pack(model, registry, 'CH05', source_ids(model.result))
    facts = [f for f in pack['facts'].values() if f.get('field_id') == 'resource.monthly.ghi']
    assert len(facts) == 12
    assert [f['period']['month'] for f in facts] == list(range(1, 13))
    assert all(f['provenance']['field_instance_id'] and f['provenance']['row_id'] for f in facts)
    assert all(f['provenance']['synthetic_or_assumed'] for f in facts)
    assert not any(f.get('field_id') == 'resource.timeseries' for f in pack['facts'].values())


def test_schedule_and_actions_are_controlled_cells(model, registry):
    pack = build_pack(model, registry, 'CH13', source_ids(model.result))
    table = pack['tables']['CH13.02-T01']
    assert table['rows']
    original = model.result['inputs']['normalized']['schedule.tasks']
    assert [r['row_id'] for r in table['rows']] == [r['row_id'] for r in original]
    for row in table['rows']:
        assert len(row['bindings']['duration']) == 2
        assert row['cells']['start'] != '未登记，待核验'
    action = build_pack(model, registry, 'CH18', source_ids(model.result))['tables']['CH18.04-T01']
    assert action['rows']
    assert all(r['cells']['materials'] == '未登记，待核验' and r['cells']['completion'] == '未登记，待核验' for r in action['rows'])


def test_capex_and_ledger_preserve_zero_and_replacement(model, registry):
    pack = build_pack(model, registry, 'CH14', source_ids(model.result))
    assert any(f.get('field_id', '').startswith('capex.items.') for f in pack['facts'].values())
    finance = build_pack(model, registry, 'CH15', source_ids(model.result))
    replacement = [f for f in finance['facts'].values() if f.get('provenance', {}).get('business_object') == 'replacement_cash_paid']
    assert any(f['value'] == 0 for f in replacement)
    assert any(f['value'] > 0 for f in replacement)
    assert all(f['provenance']['result_identity'] == model.identity for f in replacement)
    assert not build_pack(model, registry, 'CH15', [])['facts']


def test_monthly_settlement_does_not_fabricate_hourly_data(model, registry):
    pack = build_pack(model, registry, 'CH10', source_ids(model.result))
    delivered = [f for f in pack['facts'].values() if f.get('provenance', {}).get('business_object') == 'delivered_kwh']
    assert len(delivered) == 12
    if model.result['pv_type'] == 'utility_scale_ground':
        assert not any(f.get('provenance', {}).get('business_object') == 'self_value' for f in pack['facts'].values())


@pytest.mark.parametrize('mutation', ['unit', 'instance', 'source', 'value', 'row', 'license'])
def test_nested_corruption_never_becomes_fact(model, mutation):
    broken = deepcopy(model)
    records = broken.result['source_snapshot']['phase2']['records']
    atom = next(r for r in records if r['field_id'] == 'resource.monthly.ghi')
    if mutation == 'unit': atom['unit'] = 'kWh'
    elif mutation == 'instance': atom['field_instance_id'] = 'invented'
    elif mutation == 'source': atom['source_id'] = 'unapproved'
    elif mutation == 'value': atom['value'] = 0
    elif mutation == 'license': atom['license_status'] = 'UNKNOWN'
    else: broken.result['inputs']['normalized']['resource.monthly'][0]['row_id'] = 'different'
    facts, reason = input_facts(broken, 'resource.monthly.ghi', source_ids(model.result), safe_text)
    assert not facts and reason


def test_unrun_scenarios_are_not_comparison(model, registry):
    pack = build_pack(model, registry, 'CH17', source_ids(model.result))
    assert pack['tables']['CH17.02-T01']['status'] == 'NO_EXECUTED_COMPARISON'
    assert not pack['tables']['CH17.02-T01']['rows']
