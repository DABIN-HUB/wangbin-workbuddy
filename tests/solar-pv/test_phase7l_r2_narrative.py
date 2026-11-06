"""R2 narrative: assertions against sealed 25-year snapshots, never rewrite them."""
from copy import deepcopy
from pathlib import Path

import pytest

from wangbin_solar_pv.report_claims import CHAPTER_FIELDS, CHAPTER_METRICS, build_claim, category_fields
from wangbin_solar_pv.report_export import ReportModel, _word_value, _metric_label
from wangbin_solar_pv.serialization import loads

CASES = Path(__file__).resolve().parents[2] / "reports/solar-pv/phase7l-r1-full-cases"
R2_CASES = CASES.parent / "phase7l-r2-full-cases"


def model(category):
    result = loads((CASES / category / "project/canonical.json").read_bytes())
    metrics = tuple(result["results"]["metrics"])
    return ReportModel(result, metrics, {m["metric_id"]: m for m in metrics})


def claim(m, item_id):
    chapter, index = item_id.split(".")
    i = int(index) - 1
    return build_claim(m, item_id, item_id, "研究问题", "复核该项直接条件", category_fields(
        item_id, CHAPTER_FIELDS[chapter][i], m.result["pv_type"],
        m.result["inputs"]["normalized"].get("project.has_storage") is True),
        CHAPTER_METRICS[chapter][i], m.result["pv_type"], _word_value, _metric_label)


@pytest.mark.parametrize("category", ["industrial_rooftop", "utility_scale_ground"])
def test_all_100_sections_have_bounded_narratives_not_generic_fact_dump(category):
    m = model(category)
    sections = [claim(m, f"{ch}.{i:02d}") for ch, fields in CHAPTER_FIELDS.items()
                for i in range(1, len(fields) + 1)]
    assert len(sections) == 100
    assert all(c["central_claim"] and c["central_claim"] == c["summary"] for c in sections)
    assert all("本次测算显示：" not in c["central_claim"] and "{'" not in c["central_claim"]
               and "SYNTHETIC-" not in c["central_claim"] for c in sections)


@pytest.mark.parametrize("category", ["industrial_rooftop", "utility_scale_ground"])
def test_resource_monthly_uses_sourced_variables_not_energy_as_irradiance(category):
    m = model(category)
    c = claim(m, "CH05.02")
    assert "辐照" in c["central_claim"] and "kWh/㎡" in c["central_claim"]
    assert "发电量为" not in c["central_claim"]
    assert "resource.monthly" in c["supporting_input_field_ids"] or "resource.monthly.ghi" in c["supporting_input_field_ids"]
    m.result["inputs"]["normalized"]["resource.monthly"][0]["fields"]["resource.monthly.ghi"] = 9999
    changed = claim(m, "CH05.02")
    assert "9,999" not in changed["central_claim"]


def test_dynamic_phase2_bound_values_and_missing_source():
    m = model("industrial_rooftop")
    original = claim(m, "CH04.02")["central_claim"]
    assert "3,000" in original
    m.result["inputs"]["normalized"]["site.usable_area"] = 9999
    assert "9,999" not in claim(m, "CH04.02")["central_claim"]
    for row in m.result["source_snapshot"]["phase2"]["records"]:
        if row["field_id"] == "site.usable_area":
            row["value"] = 9999
    assert "9,999" in claim(m, "CH04.02")["central_claim"]


def test_project_metric_partial_does_not_promote_equity_or_scenarios():
    m = model("utility_scale_ground")
    assert m.result["status"] == "PARTIAL"
    assert "NPV" in claim(m, "CH18.01")["central_claim"]
    assert "IRR" in claim(m, "CH16.04")["central_claim"]
    assert "投资者" in claim(m, "CH16.03")["central_claim"]
    assert "敏感性斜率为" not in claim(m, "CH17.01")["central_claim"]
    assert "未执行" in claim(m, "CH17.02")["central_claim"]


def test_not_applicable_distinct_from_unknown_and_category_isolation():
    ground = model("utility_scale_ground")
    roof = model("industrial_rooftop")
    assert claim(ground, "CH10.01")["claim_status"] == "NOT_APPLICABLE"
    assert claim(roof, "CH10.01")["claim_status"] != "NOT_APPLICABLE"
    assert claim(roof, "CH16.07")["claim_status"] == "NOT_APPLICABLE"
    assert "finance.debt_ratio" in claim(roof, "CH16.07")["supporting_input_field_ids"]
    assert claim(roof, "CH16.07")["source_ids"]
    assert "project.pv_type" in claim(ground, "CH10.01")["supporting_input_field_ids"]
    assert "屋面" not in claim(ground, "CH11.03")["central_claim"]
    assert "地勘" not in claim(roof, "CH11.03")["central_claim"]
    unknown = model("industrial_rooftop")
    unknown.result["inputs"]["normalized"].pop("project.has_storage")
    assert claim(unknown, "CH10.06")["claim_status"] != "NOT_APPLICABLE"


def test_capex_opex_distinct_and_dynamic_ledger_changes():
    m = model("industrial_rooftop")
    civil = claim(m, "CH14.03")["central_claim"]
    opex = claim(m, "CH15.01")["central_claim"]
    assert "土建" in civil and "运维" in opex and civil != opex
    m.result["evidence"]["financial-ledger"]["annual"][1]["opex_cash_paid"] = 54321
    assert "54,321" in claim(m, "CH15.01")["central_claim"]


def test_replacement_year_uses_actual_outage_and_no_invented_uplift():
    m = model("industrial_rooftop")
    text = claim(m, "CH08.03")["central_claim"]
    assert "第13年" in text and "6天" in text and "无性能恢复" in text


def test_sourced_schedule_uses_task_dates_dependencies_not_invented_milestones():
    result = loads((R2_CASES / "industrial_rooftop" / "project/canonical.json").read_bytes())
    metrics = tuple(result["results"]["metrics"])
    m = ReportModel(result, metrics, {row["metric_id"]: row for row in metrics})
    text = claim(m, "CH13.03")["central_claim"]
    assert "前置依赖链" in text and "前置任务" in text
    assert "2027-01-01" in claim(m, "CH13.02")["central_claim"]
    m.result["inputs"]["normalized"]["schedule.tasks"][1]["fields"]["schedule.tasks.finish_date"] = "2028-01-01"
    assert "前置依赖链" not in claim(m, "CH13.03")["central_claim"]


def test_unknown_financial_metric_never_becomes_calculated():
    m = model("industrial_rooftop")
    m.metric_by_id["financial.phase3e.project_npv"]["status"] = "UNKNOWN"
    assert "679,601" not in claim(m, "CH18.01")["central_claim"]


def test_calculated_metric_change_and_category_specific_area_language():
    roof = model("industrial_rooftop")
    ground = model("utility_scale_ground")
    assert "屋面障碍" not in claim(ground, "CH04.02")["central_claim"]
    assert "道路" in claim(ground, "CH04.02")["central_claim"]
    old = claim(roof, "CH18.01")["central_claim"]
    roof.metric_by_id["financial.phase3e.project_npv"]["value"] = 123456
    new = claim(roof, "CH18.01")["central_claim"]
    assert old != new and "123,456元" in new
    assert "项目IRR" in new and "股东回报" in new


def test_conclusion_respects_status_without_leaking_internal_enums():
    m = model("industrial_rooftop")
    text = claim(m, "CH18.02")["central_claim"]
    assert "待取得正式核验" in text
    assert "pending" not in text and "SYNTHETIC-" not in text


@pytest.mark.parametrize("category", ["industrial_rooftop", "utility_scale_ground"])
def test_actual_r2_schedule_is_sourced_and_rejected_when_nested_source_changes(category):
    result = loads((R2_CASES / category / "project/canonical.json").read_bytes())
    metrics = tuple(result["results"]["metrics"])
    m = ReportModel(result, metrics, {row["metric_id"]: row for row in metrics})
    text = claim(m, "CH13.02")["central_claim"]
    assert text.count("合成任务“") == 5 and "前置任务" in text
    assert "个日历日" in text and "2027-01-01" in text
    assert "施工任务、持续时间与前置依赖尚未提供" not in text
    assert "SYNTHETIC-" not in text
    assert "前置依赖链" in claim(m, "CH13.03")["central_claim"]
    assert "拟投运里程碑" in claim(m, "CH13.05")["central_claim"]
    parent = next(row for row in m.result["source_snapshot"]["phase2"]["records"]
                  if row["field_id"] == "schedule.tasks")
    predecessor = parent["value"][1]["fields"]["schedule.tasks.predecessor_ids"]["value"][0]
    predecessor["source_id"] = "unbound-other-project"
    assert "前置依赖链" not in claim(m, "CH13.03")["central_claim"]
