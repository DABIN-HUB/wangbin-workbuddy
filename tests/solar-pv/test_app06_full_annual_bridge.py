"""APP06 displays every cash event in the sealed R2 project cash-flow series."""
from __future__ import annotations

from decimal import Decimal
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from docx import Document

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.report_export import ReportModel, _project_annual_bridge_rows, _write_docx
from wangbin_solar_pv.serialization import loads

_CASES = Path(__file__).resolve().parents[2] / "reports/solar-pv/phase7l-r2-delivery-final-fee-v4"
_HASHES = {
    "industrial_rooftop": "ca4bdff3f5e89e6770d43f4dad3b4efd57d965aba6c9ba0f1b4299f99295a43f",
    "utility_scale_ground": "69882cc39020f03fb3ef6cdb1a10b188c324de0f66066392970776b7495ad138",
}
# Independently specified CNY cash events: construction, ordinary, replacement, terminal.
_CASE_EVENTS = {
    "industrial_rooftop": (("建设期", "467,000", "12,000", "-479,000"),
                           ("第1年", "0", "0", "115,926.33"),
                           ("第13年", "72,000", "0", "23,990.24"),
                           ("第25年", "0", "12,000", "100,095.56")),
    "utility_scale_ground": (("建设期", "950,000", "12,000", "-962,000"),
                             ("第1年", "0", "0", "147,369.34"),
                             ("第13年", "135,000", "0", "-31,954.21"),
                             ("第25年", "0", "12,000", "85,310.9")),
}


@pytest.fixture(scope="module", params=tuple(_HASHES))
def exported(request):
    category = request.param
    model = ReportModel.from_result(loads((_CASES / category / "canonical.json").read_bytes()), Catalog())
    upstream = loads((_CASES / category / "calculation/phase3d.json").read_bytes())
    assert model.result["result_hash"] == _HASHES[category]
    assert model.result["source_snapshot"]["phase3e_terminal"]["phase3d_result_hash"] == upstream["result_hash"]
    with TemporaryDirectory(prefix="app06-bridge-", dir=os.getenv("TMPDIR")) as folder:
        path = Path(folder) / "report.docx"
        _write_docx(model, path, category, category)
        yield category, model, Document(path)


def _table(document, header):
    matches = [table for table in document.tables if table.rows[0].cells[0].text == "期别"
               and header in [cell.text for cell in table.rows[0].cells]]
    assert len(matches) == 1
    return matches[0]


def _money(value):
    return Decimal(value.replace(",", ""))


def test_app06_construction_ordinary_replacement_terminal_rows_close(exported):
    category, model, document = exported
    table = _table(document, "营运资金回收（元）")
    headers = [cell.text for cell in table.rows[0].cells]
    assert headers == ["期别", "运营收支净额（元）", "资本支出付款（元）", "营运资金增加（元）",
                       "营运资金回收（元）", "终期资产现金（元）", "项目净现金流（元）"]
    rows = [[cell.text for cell in row.cells] for row in table.rows[1:]]
    assert len(rows) == 26
    flow = model.metric("financial.phase3e.project_cash_flow")["value"]
    for i, row in enumerate(rows):
        assert row[0] == ("建设期" if i == 0 else f"第{i}年")
        # Presented values are rounded independently, so allow a one-cent display tolerance.
        operating = Decimal(0) if i == 0 else _money(row[1])
        recovered = Decimal(0) if i == 0 else _money(row[4])
        reconstructed = operating - _money(row[2]) - _money(row[3]) + recovered + _money(row[5])
        assert abs(reconstructed - _money(row[6])) <= Decimal("0.01"), (category, i, row)
        assert abs(_money(row[6]) - flow[i]) <= Decimal("0.01"), (category, i, row)
    for i, (period, capex, capital, net) in zip((0, 1, 13, 25), _CASE_EVENTS[category]):
        row = rows[i]
        assert row[0] == period and row[2] == capex and row[6] == net
        assert row[3 if i == 0 else 4] == capital
        assert row[4 if i == 0 else 3] == ("不适用（建设期）" if i == 0 else "0")
        assert row[5] == "0"  # sourced no-disposition, never residual book value
    assert rows[0][1] == "不适用（建设期）"
    assert rows[13][4] == "0" and rows[25][4] == "12,000"


def test_app06_operating_detail_includes_terminal_year_and_no_bank_receipt_for_savings(exported):
    _category, model, document = exported
    table = _table(document, "上网回款（元）")
    headers = [cell.text for cell in table.rows[0].cells]
    assert "自用节费（元）" in headers and "预计另付交易费（元）" in headers
    rows = [[cell.text for cell in row.cells] for row in table.rows[1:]]
    assert len(rows) == 25
    assert rows[-1][0] == "第25年"
    if model.result["pv_type"] == "industrial_rooftop":
        assert rows[-1][2] == "122,056" and rows[-1][1] != rows[-1][2]
    else:
        assert rows[-1][2] == "0"


@pytest.mark.parametrize("field,year", (("working_capital_release", 25), ("capex_cash_paid", 13)))
def test_app06_fails_closed_when_a_required_event_is_missing(exported, field, year):
    _category, model, _document = exported
    original = model.result["evidence"]["financial-ledger"]["annual"][year].pop(field)
    try:
        assert _project_annual_bridge_rows(model) is None
    finally:
        model.result["evidence"]["financial-ledger"]["annual"][year][field] = original


def test_app06_fails_closed_when_sourced_terminal_event_disagrees_with_project_flow(exported):
    _category, model, _document = exported
    terminal = model.result["evidence"]["phase3e-terminal-reconciliation"]["terminal_cash"]
    original = terminal[-1]
    terminal[-1] = Decimal("12000")  # Must not count the already-ledgered WC release twice.
    try:
        assert _project_annual_bridge_rows(model) is None
    finally:
        terminal[-1] = original
