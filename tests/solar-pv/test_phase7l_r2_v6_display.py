"""Reader-facing v6 tables must use the sealed, provenance-bound R2 values."""
from __future__ import annotations

from pathlib import Path

import pytest

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.report_export import (
    ReportModel, _capex_word_rows, _formula_status, _input_label, _plan_word_rows,
    _professional_metric_rows, _project_cash_word_rows, _word_number,
)
from wangbin_solar_pv.serialization import loads


_CASES = Path(__file__).resolve().parents[2] / "reports/solar-pv/phase7l-r2-full-cases"


def _model(category: str) -> ReportModel:
    return ReportModel.from_result(loads((_CASES / category / "project/canonical.json").read_bytes()), Catalog())


@pytest.mark.parametrize("category", ("industrial_rooftop", "utility_scale_ground"))
def test_word_capex_and_project_cash_rows_show_entire_existing_periods(category):
    model = _model(category)
    capex = _capex_word_rows(model)
    ledger = model.result["evidence"]["financial-ledger"]["annual"]
    flow = model.metric("financial.phase3e.project_cash_flow")
    cash = _project_cash_word_rows(model)
    assert len(capex) == len(model.result["inputs"]["normalized"]["capex.items"]) == 5
    assert any("第13年更换" in row[4] for row in capex)
    assert len(cash) == len(ledger) == len(flow["value"]) == 26
    assert cash[0][0] == "建设期" and cash[1][0] == "第1年"
    assert cash[0][4] == "不适用（建设期）"
    assert cash[13][4] != "0"
    for index, row in enumerate(cash):
        assert row[1] != "UNKNOWN"
        assert row[1] == _word_number(flow["value"][index])
    flow["value"][1] = 12345
    assert _project_cash_word_rows(model)[1][1] == "12,345"
    model.result["inputs"]["normalized"]["capex.items"][0]["fields"]["capex.items.amount"] = -1
    assert _capex_word_rows(model)[0][0] == "UNKNOWN"


@pytest.mark.parametrize("category", ("industrial_rooftop", "utility_scale_ground"))
def test_plan_table_uses_validated_tasks_and_does_not_claim_path_algorithm(category):
    model = _model(category)
    rows = _plan_word_rows(model)
    assert len(rows) == 5
    assert rows[0][4] == "无"
    assert rows[1][4] == "任务1"
    assert all("输入标记" in row[5] or "计划标记" in row[5] for row in rows)
    assert all("SYNTHETIC" not in str(row) for row in rows)
    model.result["inputs"]["normalized"]["schedule.tasks"][1]["fields"]["schedule.tasks.start_date"] = "2028-01-01"
    assert _plan_word_rows(model)[0][0] == "UNKNOWN"


def test_roof_age_and_zero_service_dscr_keep_distinct_meanings():
    assert _input_label("roof.age") == "屋顶条件·已使用年限"
    assert _input_label("roof.remaining_life") == "屋顶条件·剩余使用年限"
    model = _model("industrial_rooftop")
    dscr = _professional_metric_rows(model, ("financial.phase3e.dscr",))[0]
    assert dscr[1] == "数学上未定义" and "无债务" in dscr[3] and "不是0倍" in dscr[3]
    assert model.metric("financial.phase3e.project_npv")["status"] == "CALCULATED"
    assert model.metric("npv")["status"] == "NOT_IMPLEMENTED"
    assert model.metric("npv")["reason"] == "OUTSIDE_PHASE3B"
    assert "已计算1项、早期阶段留置占位1项" in _formula_status(model, "F-NPV")
    assert "方法未实现" not in _formula_status(model, "F-NPV")
