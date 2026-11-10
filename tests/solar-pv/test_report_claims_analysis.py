"""Focused editorial checks against sealed R2 values; never recalculate the project."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from wangbin_solar_pv.report_claims import CHAPTER_FIELDS, CHAPTER_METRICS, build_claim
from wangbin_solar_pv.report_export import ReportModel

CASES = Path(__file__).resolve().parents[2] / 'reports' / 'solar-pv' / 'phase7l-r2-full-cases'


@pytest.fixture(params=['industrial_rooftop', 'utility_scale_ground'])
def model(request):
    category = request.param
    result = json.loads((CASES / category / 'project' / 'canonical.json').read_text(encoding='utf-8'))
    metrics = tuple(result['results']['metrics'])
    return ReportModel(result, metrics, {row['metric_id']: row for row in metrics})


def claim(model, item):
    chapter, number = item.split('.')
    index = int(number) - 1
    return build_claim(model, item, item, '研究问题', '核对来源', CHAPTER_FIELDS[chapter][index],
                       CHAPTER_METRICS[chapter][index], model.result['pv_type'],
                       lambda n: f'{n:,.2f}' if isinstance(n, (int, float)) else str(n),
                       lambda mid: mid)


def test_ch03_site_category_keeps_project_types_separate(model):
    text = claim(model, 'CH03.02')['central_claim']
    if model.result['pv_type'] == 'industrial_rooftop':
        assert '屋面自用' in text or '屋面' in text
        assert '地面集中送出' not in text
    else:
        assert '地面集中送出' in text
        assert '屋顶自用' not in text


def test_ch10_roof_separates_load_savings_export_and_receipts(model):
    if model.result['pv_type'] != 'industrial_rooftop':
        pytest.skip('roof-only')
    text = claim(model, 'CH10.02')['central_claim']
    assert all(word in text for word in ('160,600', '84,713', '122,056', '35,579', '负荷', '节费', '售电'))
    assert '自用比例' in text and '负荷覆盖率' in text and '主要来自自用节费' in text
    assert '全部上网' not in text
    assert 'load.series' not in claim(model, 'CH10.01')['unresolved']
    original = model.metric_by_id['revenue.year.1']['details']['ledger']['export_sales_revenue']
    model.metric_by_id['revenue.year.1']['details']['ledger']['export_sales_revenue'] = original + 100
    assert '35,679' in claim(model, 'CH10.02')['central_claim']


def test_ground_uses_market_price_series_and_curtailment_without_rooftop_load(model):
    if model.result['pv_type'] != 'utility_scale_ground':
        pytest.skip('ground-only')
    text = claim(model, 'CH10.04')['central_claim'] + claim(model, 'CH10.05')['central_claim']
    assert claim(model, 'CH10.04')['central_claim'] != claim(model, 'CH10.05')['central_claim']
    assert '8760' not in claim(model, 'CH10.04')['central_claim']
    assert '8760' in claim(model, 'CH10.05')['central_claim']
    assert '市场' in text and '价格' in text and '203,893' in text
    assert not any(word in text for word in ('自用节费', '屋顶负荷', '厂区负荷'))
    assert 'tariff.market_series' not in claim(model, 'CH10.05')['unresolved']
    grid = claim(model, 'CH10.02')['central_claim']
    assert '限发' in grid and '1.5%' in grid
    assert claim(model, 'CH10.01')['claim_status'] == 'NOT_APPLICABLE'
    assert claim(model, 'CH10.03')['state'] == 'NOT_APPLICABLE'


def test_month_and_annual_curves_and_year13_replacement_are_distinct(model):
    monthly = claim(model, 'CH08.02')['central_claim']
    assert all(x in monthly for x in ('1月', '12月', '峰', '谷'))
    assert '月合计的差异主要随28/30/31天变化' in monthly
    annual = claim(model, 'CH08.03')['central_claim']
    assert all(x in annual for x in ('第12年', '第13年', '第14年', '6天', '无性能恢复'))
    original = model.metric_by_id['energy.annual_array']['value'][13]
    model.metric_by_id['energy.annual_array']['value'][13] = original + 1000
    assert claim(model, 'CH08.03')['central_claim'] != annual


def test_schedule_dependency_summary_is_not_task_table_and_marker_is_conditional(model):
    plan = claim(model, 'CH13.02')['central_claim']
    dependency = claim(model, 'CH13.03')['central_claim']
    assert '持续自然日' in plan and '持续自然日' not in dependency
    assert '任务“' not in plan
    assert '前置' in dependency and '关键路径' in dependency
    assert '计划' in dependency and ('未批准' in dependency or '不代表' in dependency)
    assert 'schedule.tasks.predecessor_ids' not in claim(model, 'CH13.03')['unresolved']


def test_status_and_missing_input_are_not_conflated(model):
    item = 'CH10.05' if model.result['pv_type'] == 'utility_scale_ground' else 'CH10.01'
    evidence = claim(model, item)
    assert evidence['claim_status'] != 'NOT_APPLICABLE'
    fid = 'tariff.market_series' if model.result['pv_type'] == 'utility_scale_ground' else 'load.series'
    assert fid not in evidence['unresolved']
    altered = copy.deepcopy(model)
    altered.result['artifact_manifest'] = []
    missing = claim(altered, item)
    assert fid in missing['unresolved']
    if fid == 'load.series':
        assert '160,600' not in missing['central_claim']


def test_generic_sections_use_scoped_facts_without_repeating_global_synthetic_notice(model):
    for item in ('CH06.03', 'CH07.02', 'CH15.01'):
        evidence = claim(model, item)
        assert '按合成输入为' not in evidence['central_claim']
        assert '合成或未验证资料不构成真实项目第三方证明' not in evidence['unresolved']
        assert evidence['canonical_result_hash'] == model.result['result_hash']


def test_supplied_market_series_with_blocked_revenue_is_not_called_absent(model):
    if model.result['pv_type'] != 'utility_scale_ground':
        pytest.skip('ground-only')
    revenue = model.metric_by_id['revenue.year.1']
    revenue['status'] = 'BLOCKED_UNPROVED_METHOD'
    revenue['value'] = None
    text = claim(model, 'CH10.05')
    assert '时序已登记' in text['central_claim']
    assert '收入' in text['central_claim'] and '未' in text['central_claim']
    assert 'tariff.market_series' not in text['unresolved']
    assert text['claim_status'] == 'LIMITED_BY_MISSING_EVIDENCE'


def test_ground_curtailment_narrative_changes_with_bound_input(model):
    if model.result['pv_type'] != 'utility_scale_ground':
        pytest.skip('ground-only')
    original = claim(model, 'CH10.02')['central_claim']
    value = 0.025
    model.result['inputs']['normalized']['grid.curtailment_assumption'] = value
    record = next(x for x in model.result['source_snapshot']['phase2']['records']
                  if x['field_id'] == 'grid.curtailment_assumption')
    record['value'] = value
    updated = claim(model, 'CH10.02')['central_claim']
    assert '2.5%' in updated and updated != original


def test_capacity_judgment_uses_bound_ratio_not_just_field_inventory(model):
    text = claim(model, 'CH06.03')['central_claim']
    assert '1.1' in text and '直流' in text and '交流' in text
    assert '对应' in text and '接入' in text
    assert 'dc_capacity：' not in text


def test_optional_supporting_inputs_do_not_block_observed_calculations(model):
    category = model.result['pv_type']
    targets = ('CH10.01', 'CH08.03') if category == 'industrial_rooftop' else (
        'CH10.04', 'CH10.05', 'CH08.03')
    for item in targets:
        evidence = claim(model, item)
        assert evidence['claim_status'] == 'EVIDENCE_BOUND_CONDITIONAL', (item, evidence['unresolved'])
        assert '缺少直接输入' not in evidence['unresolved']
