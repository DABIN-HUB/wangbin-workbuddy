"""Focused, synthetic report presentation regressions; no calculation formulas change."""
from __future__ import annotations
import json
from pathlib import Path
from decimal import Decimal

import pytest

from wangbin_solar_pv.report_export import (
    ReportModel, _chart_axis_geometry, _chart_axis_labels, _item_evidence, _professional_metric_rows,
    _sheet_data, _appendix_content, _reader_term_applicability,
)
from wangbin_solar_pv.report_claims import _specific_project_judgment


def _model():
    normalized = {
        "project.evaluation_years": 3, "system.dc_capacity": 165,
        "grid.transformer_capacity": 250, "grid.available_capacity": 110,
        "capex.items": [
            {"row_id": "modules", "fields": {"capex.items.category": "modules", "capex.items.quantity": 300,
                "capex.items.unit_price": 700, "capex.items.amount": 210000, "capex.items.payment_date": "2026-12-01"}},
            {"row_id": "inverters", "fields": {"capex.items.category": "inverters", "capex.items.quantity": 2,
                "capex.items.unit_price": 36000, "capex.items.amount": 72000, "capex.items.payment_date": "2026-12-01"}},
        ], "finance.working_capital": 12000, "finance.project_discount_rate": 0.075,
        "finance.cashflow_timing": "PERIOD_END", "project.price_basis": "nominal",
        "project.cashflow_tax_basis": "post_tax",
    }
    def metric(mid, value, unit, formula="F-TEST", status="CALCULATED", reason=None):
        return {"metric_id": mid, "value": value, "unit": unit, "formula_id": formula,
                "status": status, "source_ids": ["SYNTH-1"], "reason": reason}
    metrics = [
        metric("dc_capacity", 165, "kWp"), metric("ac_capacity", 100, "kWac"),
        metric("energy.monthly.year.1", [100 + n for n in range(12)], "kWh"),
        metric("energy.year.1", 1266, "kWh"),
        metric("financial.capex.total", 282000, "CNY", "F-CAPEX-TOTAL"),
        metric("financial.unit_investment", 1709.090909, "CNY", "F-UNIT-INVESTMENT"),
        metric("financial.phase3e.project_cash_flow", [-294000, 120000, 130000, 140000], "元", "F-PROJECT-CASH-FLOW"),
        metric("financial.phase3e.project_npv", 1000, "元", "F-PROJECT-NPV"),
        metric("financial.phase3e.project_irr", 0.12, "1", "F-PROJECT-IRR"),
        metric("financial.phase3e.static_payback", 2.5, "year", "F-STATIC-PAYBACK"),
        metric("financial.phase3e.dynamic_payback", 2.8, "year", "F-DYNAMIC-PAYBACK"),
        metric("financial.phase3e.equity-investor-cash-flow", None, "元", "F-EQUITY", "BLOCKED_MISSING_INPUT", "股东分配事件未提供"),
    ]
    formula = {"formula_id": "F-CAPEX-TOTAL", "chinese_name": "分类投资估算总额",
               "text_equation": "CAPEX = Σ_i C_i", "calculation_boundary": "分类成本清单",
               "unit": "元", "every_symbol_definition": [
                   {"symbol": "CAPEX", "definition_zh": "投资估算总额", "unit": "元", "role": "output"},
                   {"symbol": "C_i", "definition_zh": "第i项成本", "unit": "元", "role": "input"}],
               "subscript_definition": {"i": "清单项目序号"}, "set_and_range_definition": ["i为成本清单项目"]}
    result = {"result_hash": "hash", "project_id": "SYNTHETIC", "pv_type": "industrial_rooftop",
              "status": "PARTIAL", "scenario_id": "BASE", "run_id": "r1", "input_hash": "ih",
              "source_snapshot_id": "ss", "model_version": "m", "currency": "CNY", "evaluation_date": "2026-12-31",
              "maturity": {"real_project": "SYNTHETIC"},
              "inputs": {"normalized": normalized, "used_sources": {k: ["SYNTH-1"] for k in normalized}},
              "source_snapshot": {"phase2": {"records": [
                  {"field_id": k, "value": v, "unit": "1", "source_id": "SYNTH-1", "field_instance_id": k}
                  for k, v in normalized.items()]}, "datasets": {}},
              "formula_snapshot": {"financial_definitions": {"F-CAPEX-TOTAL": formula}},
              "results": {"metrics": metrics}, "evidence": {"financial-ledger": {"annual": [
                  {"period": "CONSTRUCTION", "capex_cash_paid": 282000, "working_capital_increase": 12000},
                  {"period": "OPERATING_YEAR_1", "capex_cash_paid": 0, "replacement_cash_paid": 0,
                   "revenue_cash_receipts": 150000, "self_use_avoided_expenditure": 0,
                   "opex_cash_paid": 20000, "cash_tax_total_project": 10000}]}}}
    return ReportModel(result, tuple(metrics), {m["metric_id"]: m for m in metrics})


def test_lifecycle_capex_and_unit_investment_have_explicit_boundaries():
    model = _model()
    headers, rows = _sheet_data(model, "M10", "CAPEX", "industrial_rooftop")
    assert headers[1:3] == ["状态", "值"]
    assert any(row[0] == "initial_capex_cash_paid" and row[1] == "LEDGER" and row[2] == 282000 for row in rows)
    assert any(row[0] == "lifecycle_capex_cash_paid" and row[2] == 282000 for row in rows)
    assert any(row[0] == "working_capital_increase" and row[2] == 12000 for row in rows)
    unit_row = next(row for row in rows if row[0] == "financial.unit_investment")
    assert "kWp" in unit_row[3]
    word_row = _professional_metric_rows(model, ("financial.unit_investment",))[0]
    assert word_row[2] == "元/kWp" and "直流" in word_row[3]


def test_resource_monthly_never_reuses_generation_array_and_d3_metadata_is_not_monthly_values():
    model = _model()
    _, resource = _sheet_data(model, "M04", "资源月度", "industrial_rooftop")
    _, generation = _sheet_data(model, "M06", "发电预测-月度", "industrial_rooftop")
    assert any(row[1] == 100 for row in generation)
    assert not any(100 in row or "energy.monthly.year.1" in row for row in resource)
    model.result["source_snapshot"]["datasets"] = {"datasets": {"resource.timeseries": {
        "header": {"field_id": "resource.timeseries", "source_id": "SYNTH-1"}, "row_count": 8760}}}
    _, resource = _sheet_data(model, "M04", "资源月度", "industrial_rooftop")
    assert any("8760" in str(row) for row in resource)
    assert not any(100 in row for row in resource)


def test_cash_flow_equity_and_indicators_are_separate_and_unavailable_equity_is_visible():
    model = _model()
    project = _sheet_data(model, "M14", "项目现金流", "industrial_rooftop")[1]
    equity = _sheet_data(model, "M15", "资本金现金流", "industrial_rooftop")[1]
    indicators = _sheet_data(model, "M16", "财务指标", "industrial_rooftop")[1]
    assert any("project_cash_flow" in str(row) and "-294000" in str(row) for row in project)
    assert not any("project_cash_flow" in str(row) for row in equity)
    assert any("equity-investor-cash-flow" in str(row) and "股东分配事件未提供" in str(row) for row in equity)
    assert any("project_npv" in str(row) for row in indicators)
    assert not any("project_cash_flow" in str(row) for row in indicators)


def test_lifecycle_capex_includes_deferred_initial_payments_and_replacement():
    model = _model()
    annual = model.result["evidence"]["financial-ledger"]["annual"]
    annual[0]["capex_cash_paid"] = 200000
    annual[1]["capex_cash_paid"] = 92000
    annual[1]["replacement_cash_paid"] = 10000
    rows = _sheet_data(model, "M10", "CAPEX", "industrial_rooftop")[1]
    assert next(row[2] for row in rows if row[0] == "initial_capex_cash_paid") == 200000
    assert next(row[2] for row in rows if row[0] == "lifecycle_capex_cash_paid") == 292000


def test_scenario_receipts_require_explicit_baseline_hash_and_separate_kind():
    model = _model()
    model.result["evidence"]["scenario_receipts"] = [
        {"kind": "SENSITIVITY", "scenario_id": "OPTIMISTIC", "run_id": "r2", "result_hash": "rh2", "baseline_result_hash": "wrong", "status": "CALCULATED"},
        {"kind": "ALTERNATIVE", "scenario_id": "PLAN-B", "run_id": "r3", "result_hash": "rh3", "baseline_result_hash": "hash", "status": "PARTIAL"}]
    s = _sheet_data(model, "M17", "敏感性", "industrial_rooftop")[1]
    a = _sheet_data(model, "M18", "方案比较", "industrial_rooftop")[1]
    assert s[0][1] == "NOT_TESTED"
    assert any("rh3" in row and "PLAN-B" in row for row in a)
    model.result["evidence"]["scenario_receipts"][0]["baseline_result_hash"] = "hash"
    assert any("rh2" in row for row in _sheet_data(model, "M17", "敏感性", "industrial_rooftop")[1])


def test_chart_labels_include_unit_and_period():
    monthly = _chart_axis_labels({"metric_id": "energy.monthly.year.1", "title": "月度发电量变化", "unit": "kWh"})
    annual = _chart_axis_labels({"metric_id": "energy.annual_array", "title": "逐年发电量变化", "unit": "kWh"})
    assert "首年" in monthly[0] and "月份" in monthly[1] and "kWh" in monthly[2]
    assert "运营年" in annual[1] and "kWh" in annual[2]


def test_chart_axis_follows_increasing_decreasing_and_constant_series():
    for values in ([1, 2, 3], [3, 2, 1], [5, 5, 5]):
        ticks, points = _chart_axis_geometry(values, top=50, bottom=450)
        assert ticks[0][0] < ticks[-1][0]
        assert ticks[0][1] > ticks[-1][1]
        if values[0] < values[-1]:
            assert points[0] > points[-1]
        elif values[0] > values[-1]:
            assert points[0] < points[-1]
        else:
            assert len(set(points)) == 1


def test_appendices_show_frozen_equation_symbols_and_controlled_bilingual_terms():
    model = _model()
    formula = _appendix_content(model, "APP11.01")
    symbols = _appendix_content(model, "APP11.02")
    glossary = _appendix_content(model, "APP12.01")
    assert "F-CAPEX-TOTAL" in formula and "CAPEX = Σ_i C_i" in formula
    assert "C_i" in symbols and "清单项目序号" in symbols and "元" in symbols
    assert "直流" in glossary and "Direct Current" in glossary and "DC" in glossary
    assert "AC" in glossary and "Alternating Current" in glossary
    assert "Photovoltaic" in glossary and "PV" in glossary


def test_unit_investment_claim_uses_dc_denominator_not_frozen_currency_only_unit():
    model = _model()
    from wangbin_solar_pv.report_export import CHAPTERS
    title = next(items for cid, _, items in CHAPTERS if cid == "CH01")[2]
    claim = _item_evidence(model, "industrial_rooftop", "CH01", title, item_no=3)
    assert "元/kWp" in claim["central_claim"]
    assert "单位投资为1,709.090909 CNY" not in claim["central_claim"]


def test_gap_record_names_actual_missing_bound_field_not_title_guess():
    model = _model()
    model.result["inputs"]["normalized"].pop("system.dc_capacity")
    from wangbin_solar_pv.report_export import CHAPTERS
    title = next(items for cid, _, items in CHAPTERS if cid == "CH01")[1]
    evidence = _item_evidence(model, "industrial_rooftop", "CH01", title, item_no=2)
    assert "system.dc_capacity" in evidence["unresolved"]
    assert "GHI/DNI/DHI" not in evidence["unresolved"]


def test_equipment_section_lists_actual_component_categories_not_civil_costs():
    model = _model()
    model.result["inputs"]["normalized"]["capex.items"].append({"row_id": "mount", "fields": {
        "capex.items.category": "mounting", "capex.items.amount": 90000,
        "capex.items.quantity": 1, "capex.items.unit_price": 90000}})
    from wangbin_solar_pv.report_export import CHAPTERS
    title = next(items for cid, _, items in CHAPTERS if cid == "CH14")[1]
    text = " ".join(_item_evidence(model, "industrial_rooftop", "CH14", title, item_no=2)["narrative"])
    assert "组件" in text and "支架" in text and "逆变器" in text


def test_equipment_fractional_unit_price_does_not_fake_a_rounded_product():
    model = _model()
    module = model.result["inputs"]["normalized"]["capex.items"][0]["fields"]
    module.update({"capex.items.quantity": 2, "capex.items.unit_price": Decimal("12.49"),
                   "capex.items.amount": Decimal("24.98"), "capex.items.quantity_unit": "unit"})
    text = _specific_project_judgment(model, "CH14.02", str)
    assert "组件2件、单价12.49元/件，分项金额25元（原始分项24.98元）" in text
    assert "2件×12元" not in text
    model.result["inputs"]["normalized"]["capex.items"].append({"row_id": "cables", "fields": {
        "capex.items.category": "cables", "capex.items.quantity": 100,
        "capex.items.quantity_unit": "米", "capex.items.unit_price": Decimal("12.49"),
        "capex.items.amount": Decimal("1249"), "capex.items.payment_date": "2026-12-01"}})
    text = _specific_project_judgment(model, "CH14.02", str)
    assert "电缆100米、单价12.49元/米，分项金额1,249元" in text


def test_reader_glossary_does_not_invent_zero_debt_or_calculated_returns():
    model = _model()
    model.result["pv_type"] = "utility_scale_ground"
    normalized = model.result["inputs"]["normalized"]
    normalized["finance.debt_ratio"] = Decimal("0.4")
    model.result["source_snapshot"]["phase2"]["records"].append({
        "field_id": "finance.debt_ratio", "value": normalized["finance.debt_ratio"],
        "source_id": "SYNTH-1", "field_instance_id": "finance.debt_ratio", "unit": "ratio",
    })
    model.metric_by_id["financial.phase3e.project_npv"]["status"] = "BLOCKED_MISSING_INPUT"
    model.metric_by_id["financial.phase3e.project_irr"]["status"] = "UNDEFINED"
    assert "有债务假设" in _reader_term_applicability(model, "TERM-LEVERED")
    assert "有债务假设但DSCR无可用值" in _reader_term_applicability(model, "TERM-DSCR")
    assert "尚未形成可用结果" in _reader_term_applicability(model, "TERM-NPV")
    assert "尚无可用计算值" in _reader_term_applicability(model, "TERM-IRR")
    model.metric_by_id["financial.phase3e.dscr"] = {"status": "CALCULATED", "value": [Decimal("1.2")]}
    assert "DSCR已有计算值" in _reader_term_applicability(model, "TERM-DSCR")
    model.result["source_snapshot"]["phase2"]["records"].pop()
    assert "债务比例尚未获得来源绑定" in _reader_term_applicability(model, "TERM-LEVERED")


def test_equipment_excludes_civil_construction_and_valued_cash_flow_is_not_called_blocked():
    model = _model()
    model.result["inputs"]["normalized"].pop("system.dc_capacity")
    model.result["inputs"]["normalized"]["capex.items"].append({
        "row_id": "civil", "fields": {"capex.items.category": "construction", "capex.items.amount": 300000}})
    from wangbin_solar_pv.report_export import CHAPTERS
    for item_id in ("CH01.02", "CH14.02", "CH16.02"):
        chapter, number = item_id.split(".")
        title = next(items for cid, _, items in CHAPTERS if cid == chapter)[int(number)-1]
        text = " ".join(_item_evidence(model, "industrial_rooftop", chapter, title, item_no=int(number))["narrative"])
        if item_id == "CH01.02":
            assert "165" in text and "直流" in text
        if item_id == "CH14.02":
            assert "construction" not in text and "组件" in text
        if item_id == "CH16.02":
            assert "缺口阻断回报" not in text


def test_target_narratives_bind_project_facts_without_title_keyword_gap_inference():
    model = _model()
    model.result["source_snapshot"]["phase2"]["records"] = [
        {**record, "unit": {"grid.transformer_capacity": "kVA", "grid.available_capacity": "kWac",
                             "finance.working_capital": "currency"}.get(record["field_id"], record["unit"])}
        for record in model.result["source_snapshot"]["phase2"]["records"]]
    for item_id, expected in (("CH01.02", "165"), ("CH08.02", "1266"),
                              ("CH09.02", "250"), ("CH14.02", "210000"),
                              ("CH16.02", "-294000"), ("CH16.04", "1000")):
        chapter, number = item_id.split(".")
        from wangbin_solar_pv.report_export import CHAPTERS
        title = next(items for cid, _, items in CHAPTERS if cid == chapter)[int(number) - 1]
        evidence = _item_evidence(model, "industrial_rooftop", chapter, title, item_no=int(number))
        assert expected in " ".join(evidence["narrative"]).replace(",", ""), item_id
        if item_id == "CH09.02":
            assert "250kVA" in " ".join(evidence["narrative"])
            assert "110kWac" in " ".join(evidence["narrative"])
        if item_id == "CH16.02":
            assert "12,000元" in " ".join(evidence["narrative"])
        assert "需补充带授权和覆盖期的GHI" not in evidence["unresolved"], item_id
        assert evidence["canonical_result_hash"] == "hash"


_CASES = Path(__file__).resolve().parents[2] / "reports" / "solar-pv" / "phase7l-r1-full-cases"
_TARGETS = ("CH01.02", "CH08.02", "CH09.02", "CH14.02", "CH16.02", "CH16.04")


def _sealed_model(category):
    result = json.loads((_CASES / category / "project" / "canonical.json").read_text(encoding="utf-8"))
    assert result["pv_type"] == category
    assert result["project_id"] == {
        "industrial_rooftop": "SYNTHETIC-PHASE7L-ROOF-25Y-165KWP",
        "utility_scale_ground": "SYNTHETIC-PHASE7L-GROUND-25Y-330KWP",
    }[category]
    assert result["inputs"]["normalized"]["project.evaluation_years"] == 25
    assert result["source_snapshot"]["phase2"]["source_snapshot_id"]
    assert result["maturity"]["real_project"] == "NOT_VERIFIED"
    metrics = tuple(result["results"]["metrics"])
    return ReportModel(result, metrics, {m["metric_id"]: m for m in metrics})


def _section(model, category, item_id):
    from wangbin_solar_pv.report_export import CHAPTERS
    chapter, part = item_id.split(".")
    title = next(items for cid, _, items in CHAPTERS if cid == chapter)[int(part) - 1]
    claim = _item_evidence(model, category, chapter, title, item_no=int(part))
    assert claim["canonical_result_hash"] == model.result["result_hash"]
    return claim["central_claim"]


@pytest.mark.parametrize("category,capacity,energy,grid,initial,replacement,year1,npv", [
    ("industrial_rooftop", "165", "245,313", "110", "467,000", "72,000", "116,943", "679,602"),
    ("utility_scale_ground", "330", "486,427", "290", "950,000", "135,000", "153,206", "321,668"),
])
@pytest.mark.parametrize("item_id", _TARGETS)
def test_sealed_25y_six_conclusions_use_project_specific_canonical_evidence(
        category, capacity, energy, grid, initial, replacement, year1, npv, item_id):
    model = _sealed_model(category)
    text = _section(model, category, item_id)
    from wangbin_solar_pv.report_display_numbers import decision_number
    assert energy == decision_number(model.metric("energy.year.1")["value"], "kWh")
    assert npv == decision_number(model.metric("financial.phase3e.project_npv")["value"], "CNY")
    if item_id == "CH16.02":
        assert year1 == decision_number(model.metric("financial.phase3e.project_cash_flow")["value"][1], "CNY")
    assert "本项目本次输入与计算的直接事实为" not in text
    assert "其他直接计算结果" not in text
    assert "合成" in text or "假设" in text
    if item_id == "CH01.02":
        assert all(word in text for word in (capacity, "25年", energy, "kWp", "kW"))
        assert ("屋面" if category == "industrial_rooftop" else "土地") in text
    elif item_id == "CH08.02":
        assert all(word in text for word in (energy, "12个月", "汇总", "kWh", "衰减"))
        assert "实测" in text
    elif item_id == "CH09.02":
        assert grid in text and "kVA" in text and "kW" in text
        assert ("功率因数未提供" if category == "industrial_rooftop" else "功率因数0.95") in text
        assert all(word in text for word in ("限值", "待", "接入"))
    elif item_id == "CH14.02":
        assert all(word in text for word in (initial, replacement, "含税", "13%", "组件", "逆变器", "支架", "第13年"))
        assert "报价" in text and "元/" in text
    elif item_id == "CH16.02":
        assert all(word in text for word in (initial, year1, "12,000", "运维", "税", "第13年", "银行流水"))
        assert ("自用" if category == "industrial_rooftop" else "上网") in text
    elif item_id == "CH16.04":
        assert all(word in text for word in (npv, "7.5%", "IRR", "静态", "动态", "年度", "投资者"))
        assert "逐笔日期" in text


@pytest.mark.parametrize("category,foreign,forbidden", [
    ("industrial_rooftop", "utility_scale_ground", ("地勘", "集中送出", "土地权属", "486,427", "135,000", "321,668")),
    ("utility_scale_ground", "industrial_rooftop", ("屋面", "防水", "厂区负荷", "245,313", "72,000", "679,602")),
])
def test_sealed_25y_sections_reject_cross_category_evidence(category, foreign, forbidden):
    model = _sealed_model(category)
    other = _sealed_model(foreign)
    # Deliberately offer the other category's normalized fields; the six sections
    # must use their own category's actual Phase 2 and canonical bindings.
    for key, value in other.result["inputs"]["normalized"].items():
        if key.startswith(("roof.", "agri.", "fishery.")):
            model.result["inputs"]["normalized"][key] = value
    for item_id in _TARGETS:
        text = _section(model, category, item_id)
        assert not any(word in text for word in forbidden), (category, item_id, text)


def test_sealed_25y_sections_reject_rebound_normalized_values_without_phase2_record():
    model = _sealed_model("industrial_rooftop")
    ground = _sealed_model("utility_scale_ground")
    model.result["inputs"]["normalized"]["grid.available_capacity"] = 290
    model.result["inputs"]["normalized"]["capex.items"] = ground.result["inputs"]["normalized"]["capex.items"]
    grid = _section(model, "industrial_rooftop", "CH09.02")
    equipment = _section(model, "industrial_rooftop", "CH14.02")
    assert "290kW" not in grid and "可用接入余量" in grid
    assert "420,000" not in equipment and "不能由总额倒推" in equipment


@pytest.mark.parametrize("category", ("industrial_rooftop", "utility_scale_ground"))
def test_sealed_25y_report_reconciles_resource_generation_capex_and_cash_boundaries(category):
    model = _sealed_model(category)
    n = model.result["inputs"]["normalized"]
    ledger = model.result["evidence"]["financial-ledger"]["annual"]
    values = model.metric_by_id
    assert len(n["resource.monthly"]) == len(values["energy.monthly.year.1"]["value"]) == 12
    assert abs(sum(Decimal(str(x)) for x in values["energy.monthly.year.1"]["value"])
               - Decimal(str(values["energy.year.1"]["value"]))) < Decimal("0.01")
    initial, renewal = ledger[0]["capex_cash_paid"], ledger[13]["replacement_cash_paid"]
    assert initial + renewal == values["financial.capex.total"]["value"]
    cash = values["financial.phase3e.project_cash_flow"]["value"]
    assert cash[0] == -initial - ledger[0]["working_capital_increase"]
    first = ledger[1]
    assert abs(Decimal(str(cash[1])) - (Decimal(str(first["revenue_cash_receipts"]))
               + Decimal(str(first["self_use_avoided_expenditure"]))
               - Decimal(str(first["opex_cash_paid"]))
               - Decimal(str(first["cash_tax_total_project"])))) < Decimal("0.01")
    assert values["financial.phase3e.equity-investor-cash-flow"]["status"] != "CALCULATED"
    for item_id in _TARGETS:
        text = _section(model, category, item_id)
        assert "已获接入许可" not in text or "不视为已获接入许可" in text
        assert "实际银行流水" not in text or "不是实际银行流水" in text


@pytest.mark.parametrize("category", ("industrial_rooftop", "utility_scale_ground"))
def test_report_resolves_referenced_extension_formula_from_matching_frozen_catalog(category):
    from wangbin_solar_pv.catalog import Catalog
    from wangbin_solar_pv.report_export import _appendix_rows
    from wangbin_solar_pv.serialization import loads

    result = loads((_CASES / category / "project" / "canonical.json").read_bytes())
    catalog = Catalog()
    model = ReportModel.from_result(result, catalog)
    _, formulas = _appendix_rows(model, "APP11.01")
    _, symbols = _appendix_rows(model, "APP11.02")
    formula = next(row for row in formulas if row[0] == "F-AVERAGE-ANNUAL-ENERGY")
    assert formula[2] == catalog.formulas["F-AVERAGE-ANNUAL-ENERGY"]["text_equation"]
    assert {row[1] for row in symbols if row[0] == formula[0]} >= {"E_mean", "E_y", "N", "y"}
