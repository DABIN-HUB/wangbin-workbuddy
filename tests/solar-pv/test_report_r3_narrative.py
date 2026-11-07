"""R3 prose assertions against the sealed fee-v4 canonical, without recomputation."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from wangbin_solar_pv.report_claims import APPENDIX_RULES, CHAPTER_FIELDS, CHAPTER_METRICS, build_claim
from wangbin_solar_pv.report_export import ReportModel
from wangbin_solar_pv.report_narrative import ITEM_QUESTIONS

ROOT = Path(__file__).resolve().parents[2] / 'reports/solar-pv/phase7l-r2-delivery-final-fee-v4'


@pytest.fixture(params=('industrial_rooftop', 'utility_scale_ground'))
def model(request):
    result = json.loads((ROOT / request.param / 'canonical.json').read_text(encoding='utf-8'))
    metrics = tuple(result['results']['metrics'])
    return ReportModel(result, metrics, {row['metric_id']: row for row in metrics})


def claim(model, item):
    if item.startswith('CH'):
        chapter, no = item.split('.')
        fields, metrics = CHAPTER_FIELDS[chapter][int(no)-1], CHAPTER_METRICS[chapter][int(no)-1]
    else:
        _, _, fields, metrics = APPENDIX_RULES[item]
    return build_claim(model, item, item, item, item, fields, metrics,
                       model.result['pv_type'], lambda x: f'{x:,.2f}' if isinstance(x, (int, float)) else str(x),
                       lambda x: x)


def test_appendix_monthly_reconciliation_flags_mutated_total(model):
    changed = copy.deepcopy(model)
    changed.metric_by_id['energy.monthly.year.1']['value'][0] += 100
    assert '不一致' in claim(changed, 'APP02.02')['central_claim']


def test_grid_upgrade_plan_does_not_leak_english_placeholder(model):
    text = claim(model, 'CH09.03')['central_claim']
    assert 'No upgrade confirmed' not in text
    assert 'Concept protection' not in text
    assert '保护' in text and '送出' in text


def test_financial_guidance_separates_annual_project_cash_from_dated_investor_cash():
    assert '年度期末' in ITEM_QUESTIONS['CH16'][3]
    assert '日期' in ITEM_QUESTIONS['CH16'][2]
    assert '必须以完整且有日期的现金事件' not in ITEM_QUESTIONS['CH16'][3]


def test_all_126_items_have_distinct_scoped_body_without_raw_arrays(model):
    ids = [f'{chapter}.{i:02d}' for chapter, parts in CHAPTER_FIELDS.items()
           for i in range(1, len(parts)+1)] + list(APPENDIX_RULES)
    bodies = [claim(model, item)['central_claim'] for item in ids]
    assert len(ids) == 126 and len(set(bodies)) == 126
    for item, body in zip(ids, bodies):
        assert body and '本项尚未形成可引用的项目直接结果' not in body, item
        assert '本次证据：' not in body, item
        assert not any(token in body for token in ('为[', 'UNKNOWN', '为nan', '：nan')), item
        assert 'factory-roof calculation demo' not in body and 'ground PV calculation demo' not in body, item


def test_area_and_roof_load_decision_use_sourced_values(model):
    roof = model.result['pv_type'] == 'industrial_rooftop'
    area = claim(model, 'CH04.02')['central_claim']
    assert ('3,500' if roof else '10,000') in area and ('3,000' if roof else '9,000') in area
    assert '扣除' in area and '测绘' in area
    load = claim(model, 'CH04.04')['central_claim']
    if roof:
        assert '0.2' in load and '0.12' in load and '结构' in load
    else:
        assert '桩基' in load and '屋面允许附加荷载' not in load


def test_strings_and_connection_do_not_claim_certification(model):
    text = claim(model, 'CH07.03')['central_claim']
    assert ('750' if model.result['pv_type'] == 'industrial_rooftop' else '1000') in text
    assert '低温' in text and '安全' not in text.split('；')[0]
    connection = claim(model, 'CH09.05')['central_claim']
    assert ('100' if model.result['pv_type'] == 'industrial_rooftop' else '280') in connection
    assert '批准' in connection or '批复' in connection


def test_lifecycle_spend_and_blocked_equity_lcoe_threshold_are_not_promoted(model):
    capex = claim(model, 'CH14.01')['central_claim']
    assert ('467,000' if model.result['pv_type'] == 'industrial_rooftop' else '950,000') in capex
    assert ('539,000' if model.result['pv_type'] == 'industrial_rooftop' else '1,085,000') in capex
    assert '更换' in capex
    assert '股东' in claim(model, 'CH16.03')['central_claim']
    assert '终期' in claim(model, 'CH16.06')['central_claim']
    assert '反向' in claim(model, 'CH16.08')['central_claim']
    assert 'BLOCKED' not in claim(model, 'CH16.06')['central_claim']


def test_appendix_cash_flows_are_bounded_not_serialized(model):
    project = claim(model, 'APP06.01')['central_claim']
    investor = claim(model, 'APP06.02')['central_claim']
    assert '建设期' in project and '项目' in project and '第1年' in project
    assert '股东' in investor and '未' in investor and project != investor
    assert '为[' not in project
    assert '逐年' in claim(model, 'APP05.02')['central_claim']
    assert '哈希' in claim(model, 'APP13.01')['central_claim']


def test_rooftop_and_ground_settlement_cannot_be_conflated(model):
    text = claim(model, 'CH01.04')['central_claim']
    if model.result['pv_type'] == 'industrial_rooftop':
        assert '自用' in text and '余电' in text and '节费' in text
    else:
        assert '集中' in text and '市场' in text and '自用节费' not in text


def test_deeper_site_design_finance_and_environment_evidence(model):
    grounding = claim(model, 'CH03.03')['central_claim']
    assert '2052' in grounding and '权' in grounding and '评价期' in grounding
    arrangement = claim(model, 'CH06.02')['central_claim']
    assert ('300' if model.result['pv_type'] == 'industrial_rooftop' else '600') in arrangement
    assert '行距' in arrangement and '消防' in arrangement
    assert '报价' in claim(model, 'CH14.03')['central_claim'] or '核量' in claim(model, 'CH14.03')['central_claim']
    tax = claim(model, 'CH15.05')['central_claim']
    assert '折旧' in tax and '更换' in tax and '现金' in tax
    environmental = claim(model, 'CH12.01')['central_claim']
    assert 'kgCO2e/kWh' in environmental and '未' in environmental


def test_ground_price_status_and_roof_load_rebind(model):
    if model.result['pv_type'] != 'industrial_rooftop':
        pytest.skip('roof only')
    original = claim(model, 'CH01.04')['central_claim']
    altered = copy.deepcopy(model)
    altered.result['artifact_manifest'] = []
    assert '160,600' not in claim(altered, 'CH01.04')['central_claim']
    assert '160,600' in original


def test_area_mutation_suspends_layout_conclusion(model):
    changed = copy.deepcopy(model)
    changed.result['inputs']['normalized']['site.usable_area'] += 10
    row = next(x for x in changed.result['source_snapshot']['phase2']['records']
               if x['field_id'] == 'site.usable_area')
    row['value'] += 10
    assert '不符' in claim(changed, 'CH06.01')['central_claim']


def test_changed_or_unbound_source_does_not_keep_roof_load_comparison(model):
    if model.result['pv_type'] != 'industrial_rooftop':
        pytest.skip('roof only')
    original = claim(model, 'CH04.04')['central_claim']
    changed = copy.deepcopy(model)
    normalized = changed.result['inputs']['normalized']
    normalized['roof.design_added_load'] = 0.22
    record = next(x for x in changed.result['source_snapshot']['phase2']['records']
                  if x['field_id'] == 'roof.design_added_load')
    record['value'] = 0.22
    assert '高于' in claim(changed, 'CH04.04')['central_claim']
    record['value'] = 0.12
    assert '高于' not in claim(changed, 'CH04.04')['central_claim']
    assert claim(changed, 'CH04.04')['central_claim'] != original
