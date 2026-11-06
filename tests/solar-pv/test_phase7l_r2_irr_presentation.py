"""Reader-facing IRR root-set semantics over isolated, never resealed results."""
from copy import deepcopy
from decimal import Decimal as D
from pathlib import Path

from wangbin_solar_pv.calculation.financial_metrics import _irr
from wangbin_solar_pv.report_claims import CHAPTER_FIELDS, CHAPTER_METRICS, build_claim, category_fields
from wangbin_solar_pv.report_export import (ReportModel, _display_metric, _irr_presentation,
                                            _metric_label, _project_summary, _professional_metric_rows,
                                            _sheet_data, _word_value)
from wangbin_solar_pv.serialization import loads

CASE = Path(__file__).resolve().parents[2] / "reports/solar-pv/phase7l-r2-full-cases/industrial_rooftop/project/canonical.json"


def _model():
    result = loads(CASE.read_bytes())
    metrics = tuple(result["results"]["metrics"])
    return ReportModel(result, metrics, {row["metric_id"]: row for row in metrics})


def _claim(model, item):
    chapter, index = item.split(".")
    i = int(index) - 1
    return build_claim(model, item, item, "研究问题", "复核该项直接条件", category_fields(
        item, CHAPTER_FIELDS[chapter][i], model.result["pv_type"], False),
        CHAPTER_METRICS[chapter][i], model.result["pv_type"], _word_value, _metric_label)["central_claim"]


def _irr_metric(model, status):
    metric = model.metric_by_id["financial.phase3e.project_irr"]
    metric.update(status=status["status"], value=status["value"], reason=status.get("reason"),
                  details=deepcopy(status["details"]))
    return metric


def test_single_root_keeps_annual_percent_and_qualified_comparison():
    model = _model()
    metric = model.metric("financial.phase3e.project_irr")
    display, note = _irr_presentation(metric)
    assert display.endswith("%") and "唯一已认证根" in note
    assert "IRR高于同口径折现率" in _claim(model, "CH16.04")


def test_two_roots_15_percent_never_become_one_return_in_any_reader_path():
    model = _model()
    root_set = _irr([D("-100"), D("230"), D("-132")],
                    {"minimum": D("0"), "maximum": D("0.5")}, {"root_tolerance": D("1e-12")})
    assert root_set["status"] == "UNDEFINED" and root_set["details"]["root_count"] == 2
    metric = _irr_metric(model, root_set)
    model.result["inputs"]["normalized"]["finance.project_discount_rate"] = D("0.15")
    for record in model.result["source_snapshot"]["phase2"]["records"]:
        if record["field_id"] == "finance.project_discount_rate":
            record["value"] = D("0.15")
    display, note = _irr_presentation(metric)
    assert "根1" in display and "根2" in display and "10.00%" in display and "20.00%" in display
    assert "搜索域" in note and "非唯一" in note
    for item in ("CH01.03", "CH16.04", "CH18.01"):
        claim = _claim(model, item)
        assert "根1" in claim and "根2" in claim and "非唯一" in claim
        assert "IRR高于折现率" not in claim and "唯一IRR高于" not in claim
    summary = _project_summary(model)
    assert "根1" in summary and "根2" in summary and "项目净现值" in summary
    professional = _professional_metric_rows(model, ("financial.phase3e.project_irr",))[0]
    assert "根1" in professional[1] and "根2" in professional[1]
    model_rows = _sheet_data(model, "M16", "财务指标", model.result["pv_type"])[1]
    irr_row = next(row for row in model_rows if row[0] == "financial.phase3e.project_irr")
    assert irr_row[1] == "UNDEFINED" and "根1" in irr_row[2] and "根2" in irr_row[2]
    assert "认证根原值" in irr_row[6] and irr_row[7] == "UNKNOWN"
    review_rows = _sheet_data(model, "M19", "一致性", model.result["pv_type"])[1]
    review_row = next(row for row in review_rows if row[:2] == ["metric_status", "financial.phase3e.project_irr"])
    assert "根1" in review_row[3] and "根2" in review_row[3]
    assert "根1" in _display_metric(metric)


def test_no_root_and_unexhausted_root_set_not_reported_as_zero_or_certified():
    model = _model()
    no_root = {"status": "UNDEFINED", "value": None, "reason": "NO_ROOT", "details": {
        "roots": [], "root_count": 0, "domain": {"minimum": D("0"), "maximum": D("0.5")},
        "unexhausted": False}}
    metric = _irr_metric(model, no_root)
    assert _irr_presentation(metric)[0] == "搜索域内无根"
    assert "不等于IRR为0" in _claim(model, "CH16.04")
    metric["details"]["unexhausted"] = True
    assert _irr_presentation(metric)[0] == "根集待核验"
    assert "尚未核验" in _claim(model, "CH18.01")


def test_close_roots_retained_when_rounding_would_coincide():
    model = _model()
    metric = _irr_metric(model, {"status": "UNDEFINED", "value": None, "reason": "MULTIPLE_ROOTS",
                                 "details": {"roots": [D("0.10000000"), D("0.10000001")],
                                             "root_count": 2, "domain": {"minimum": D("0"), "maximum": D("0.5")},
                                             "unexhausted": False}})
    display, _note = _irr_presentation(metric)
    assert "根1" in display and "根2" in display
    assert display.split("、")[0] != display.split("、")[1]
    assert "根1" in _claim(model, "CH18.01") and "根2" in _claim(model, "CH18.01")
