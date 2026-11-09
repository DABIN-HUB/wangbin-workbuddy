"""R2 Word presentation regressions over sealed R1 calculation snapshots."""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from decimal import Decimal

import pytest
from docx import Document
from openpyxl import load_workbook


from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.report_export import REPORT_CONTENT_VERSION, ReportModel, _appendix_rows, _metric_rows, _professional_metric_rows, _write_docx, _claim_binding_error, _item_evidence
from wangbin_solar_pv.serialization import loads

_CASES = Path(__file__).resolve().parents[2] / "reports/solar-pv/phase7l-r1-full-cases"


def _model(category="utility_scale_ground"):
    result = json.loads((_CASES / category / "project/canonical.json").read_text(encoding="utf-8"))
    metrics = tuple(result["results"]["metrics"])
    return ReportModel(result, metrics, {m["metric_id"]: m for m in metrics})


@pytest.fixture(scope="module")
def exported():
    category = "utility_scale_ground"
    model = ReportModel.from_result(loads((_CASES / category / "project/canonical.json").read_bytes()), Catalog())
    with TemporaryDirectory(prefix="r2-export-", dir=os.getenv("TMPDIR")) as directory:
        path = Path(directory) / "report.docx"
        receipt = _write_docx(model, path, "地面合成项目", category)
        yield model, Document(path), receipt


def _all_text(document):
    return "\n".join([p.text for p in document.paragraphs] +
                     [cell.text for table in document.tables for row in table.rows for cell in row.cells])


def test_partial_snapshot_keeps_calculated_project_returns_separate_from_blocked_equity(exported):
    model, document, _ = exported
    assert model.result["status"] == "PARTIAL"
    paragraphs = [p.text for p in document.paragraphs]
    begin = paragraphs.index("摘要")
    summary = "\n".join(paragraphs[begin:paragraphs.index("一、执行摘要与初步结论", begin)])
    assert "项目净现值" in summary and "项目内部收益率" in summary and "回收期" in summary
    assert "营运资金" in summary and "后期更换" in summary and "25年" in summary
    assert "股东" in summary and "未核验" in summary
    assert "项目投资收益水平作确定性判断" not in summary
    text = _all_text(document)
    assert "项目净现值" in text and "平准化度电成本" in text
    assert "合成假设已提供；未真实核验" in text
    assert "GRID_DELIVERABLE" not in text and "Concept protection only" not in text
    assert "pending" not in text.lower()
    npv = _professional_metric_rows(model, ("financial.phase3e.project_npv",))[0][1]
    assert npv in text
    assert "缺股东出资" in text or "股东分配" in text


def test_irr_roots_are_percentages_without_silent_selection():
    model = _model()
    metric = model.metric("financial.phase3e.project_irr")
    rows = _professional_metric_rows(model, ("financial.phase3e.project_irr",))
    assert rows[0][2] == "—"  # The value already includes %, so the unit column must not repeat it.
    model_rows = [row for row in _metric_rows(model, prefixes=("financial.phase3e.project_irr",))
                  if row[0] == "financial.phase3e.project_irr"]
    assert len(model_rows) == 1 and model_rows[0][2].endswith("%") and model_rows[0][3] == "—"
    assert "11.95%" in rows[0][1] and "单根" in rows[0][3]
    metric.update(status="UNDEFINED", reason="MULTIPLE_ROOTS", value=None,
                  details={"roots": [0.12, 0.25], "root_count": 2,
                           "domain": {"minimum": 0, "maximum": 0.5}, "unexhausted": False})
    row = _professional_metric_rows(model, ("financial.phase3e.project_irr",))[0]
    assert "12.00%" in row[1] and "25.00%" in row[1] and "多根" in row[3]
    metric.update(status="UNDEFINED", reason="NO_ROOT", value=None,
                  details={"roots": [], "root_count": 0,
                           "domain": {"minimum": 0, "maximum": 0.5}, "unexhausted": False})
    row = _professional_metric_rows(model, ("financial.phase3e.project_irr",))[0]
    assert "无根" in row[1] and "12%" not in row[1]


def test_formula_groups_keep_all_symbols_once_and_shared_index_once(exported):
    model, document, _ = exported
    definitions = [*model.result["formula_snapshot"]["engineering_definitions"].values(),
                   *model.result["formula_snapshot"]["consumption_definitions"].values(),
                   *model.result["formula_snapshot"]["financial_definitions"].values()]
    _, symbols = _appendix_rows(model, "APP11.02")
    assert len({p.text.split(" ", 1)[0] for p in document.paragraphs
                if p.style.name == "Solar Formula Title" and p.text.startswith("F-")}) == 89
    fid = "F-ANNUAL-OPEX"
    formula = next(f for f in definitions if f["formula_id"] == fid)
    assert {row[1] for row in symbols if row[0] == fid} == {s["symbol"] for s in formula["every_symbol_definition"]}
    # Read the actual generated formula group, not a formatting helper.
    start = next(i for i, p in enumerate(document.paragraphs) if p.text.startswith(fid + " "))
    following = next(i for i in range(start + 1, len(document.paragraphs))
                     if document.paragraphs[i].text.startswith("F-") and document.paragraphs[i].style.name == "Solar Formula Title")
    group = "\n".join(p.text for p in document.paragraphs[start:following])
    assert formula["text_equation"] in group and "本次引用" in group
    assert group.count("逐个下标词素") == 1
    assert "k∈𝒪_y" in group and formula["calculation_boundary"] in group
    assert formula["dimensional_check"].replace("every_symbol_definition", "本式完整符号表") in group
    assert "本式共通契约：" in group and "运算符第" in group and "记法与歧义第" in group
    full_text = _all_text(document)
    for key in ("operator_definition", "notation_contract"):
        for meaning in formula[key].values():
            assert meaning.replace("every_symbol_definition", "本式完整符号表").replace(
                "set_and_range_definition", "本式下标与求和范围") in full_text
    assert formula["unit_convention"] in full_text
    assert not any("\"definition\":" in cell.text or "\"token\":" in cell.text
                   for table in document.tables for row in table.rows for cell in row.cells)


def test_same_symbol_keeps_per_formula_meaning():
    _, rows = _appendix_rows(_model(), "APP11.02")
    curtail = next(row for row in rows if row[0] == "F-AVAILABLE-ENERGY" and row[1] == "E_available,t")
    balance = next(row for row in rows if row[0] == "F-SELF-CONSUMPTION" and row[1] == "E_available,t")
    assert curtail[2] == "同一计量点时段内限发前可用交流电量"
    assert balance[2] == "同计量点限发前可用电量"


def test_bound_repeated_input_does_not_accept_rebound_value():
    model = _model()
    evidence = _item_evidence(model, "utility_scale_ground", "CH14", "工程建设与场址专项", item_no=3)
    record = {**evidence, "input_field_ids": evidence["field_ids"],
              "metric_ids": evidence["metric_ids"]}
    assert not _claim_binding_error(model, record)
    model.result["inputs"]["normalized"]["capex.items"][0]["fields"]["capex.items.category"] = "invented"
    assert _claim_binding_error(model, record)


def test_formula_index_separates_reference_execution_block_and_inapplicability(exported):
    model, document, _ = exported
    assert "42条" in _all_text(document) and "89条" in _all_text(document)
    _, formulas = _appendix_rows(model, "APP11.01")
    assert any("已计算" in row[5] for row in formulas)
    assert any("阻断" in row[5] for row in formulas)
    assert any("不适用" in row[5] for row in formulas)
    npv = next(row for row in formulas if row[0] == "F-NPV")
    assert "已计算1项、早期阶段留置占位1项" in npv[5]
    assert "方法未实现" not in npv[5]


def test_bilingual_glossary_defines_meaning_and_scope(exported):
    _, document, _ = exported
    text = _all_text(document)
    assert "Net Present Value" in text and "NPV" in text and "净现值" in text
    assert "现金流" in text and "折现" in text
    assert "Levelized Cost of Energy" in text and "LCOE" in text


def test_reader_input_summary_shows_professional_name_value_unit_and_source_state(exported):
    _, document, _ = exported
    summary = next(table for table in document.tables if table.rows[0].cells[0].text == "建设及接网关键条件")
    body = "\n".join(cell.text for row in summary.rows[1:] for cell in row.cells)
    assert "并网条件·可接入容量" in body
    assert "kWac" in body and "合成假设已提供；未真实核验" in body
    assert "相关参数" not in body and "GRID_DELIVERABLE" not in body


def test_known_synthetic_display_markers_are_chinese_without_translating_unknown_text():
    from wangbin_solar_pv.report_export import _reader_text
    assert _reader_text("SYNTHETIC-SAME-NODE-UNMETERED") == "合成同节点计量标识，未装实际电表"
    assert _reader_text("SYNTHETIC-PLANNING-NOTE-NO-GRID-OPINION") == "合成规划备注，尚无正式电网接入意见"
    assert _reader_text("unmapped free-text approval pending elsewhere") == "unmapped free-text approval pending elsewhere"


def test_toc_contains_editable_outline_without_pretending_to_have_refreshed_pages(exported):
    _, document, receipt = exported
    xml = document.element.body.xml
    assert 'TOC \\o "1-3"' in xml
    headings = [p.text for p in document.paragraphs if p.style.name == "Heading 1"]
    assert "一、执行摘要与初步结论" in headings and "附录K 公式逐符号字典" in headings
    assert "PAGEREF" not in xml
    assert receipt["toc_status"] == "FIELD_REQUIRES_RENDER_REFRESH"
    assert receipt["report_content_version"] == REPORT_CONTENT_VERSION


def test_input_display_changes_with_snapshot_and_distinguishes_assumption_from_approval():
    model = _model("industrial_rooftop")
    first = _professional_metric_rows(model, ("financial.phase3e.project_npv",))[0][1]
    model.metric("financial.phase3e.project_npv")["value"] = 1234.5
    second = _professional_metric_rows(model, ("financial.phase3e.project_npv",))[0][1]
    assert first != second and second == "1,234.5"


def test_actual_r2_formula_text_and_summary_do_not_leak_internal_status():
    from wangbin_solar_pv.report_export import _formula_index_lines, _reader_text, _project_summary

    cases = _CASES.parent / "phase7l-r2-full-cases"
    for category in ("industrial_rooftop", "utility_scale_ground"):
        result = loads((cases / category / "project/canonical.json").read_bytes())
        model = ReportModel.from_result(result, Catalog())
        summary = _project_summary(model)
        assert "后期更换 第13年" in summary
        assert "OPERATING_YEAR_" not in summary
        assert "NOT_APPLICABLE" not in _reader_text("无融资返回 NOT_APPLICABLE")
        formulas = model.result["formula_snapshot"]
        for group in ("engineering_definitions", "consumption_definitions", "financial_definitions"):
            for formula in formulas[group].values():
                lines = _formula_index_lines(formula)
                assert len(lines) == len(set(lines))
                assert all("{'" not in line and '{"' not in line for line in lines)


@pytest.mark.parametrize("category", ("industrial_rooftop", "utility_scale_ground"))
def test_delivered_r3_word_workbooks_and_canonical_keep_project_metric_identity(category):
    # Verify the versioned R3 export against the independently archived fee-v4 result.
    folder = _CASES.parent / "phase7l-r3-final-v5" / category
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    result = loads((folder / "canonical.json").read_bytes())
    prior = loads((_CASES.parent / "phase7l-r2-delivery-final-fee-v4" /
                   category / "canonical.json").read_bytes())
    assert result["result_hash"] == prior["result_hash"]
    model = ReportModel.from_result(result, Catalog())
    assert manifest["identity"] == model.identity
    # This is an immutable R3 archive, not a fresh export using today's default.
    assert manifest["report_content_version"] == "phase7l-r3-v1-professional-content-and-full-cash-bridge"
    for key in ("F01", "F03", "F04", "F06"):
        entry = manifest["files"][key]
        artifact = folder / entry.get("path", entry.get("file"))
        assert artifact.is_file()
        assert hashlib.sha256(artifact.read_bytes()).hexdigest() == entry["sha256"]
    doc = Document(folder / manifest["files"]["F01"]["path"])
    text = _all_text(doc)
    assert "第13年" in text and "GRID_DELIVERABLE" not in text and "pending" not in text.lower()
    assert "项目净现值" in text and "项目内部收益率" in text
    for metric_id in ("financial.phase3e.project_npv", "financial.phase3e.project_irr",
                      "financial.phase3e.static_payback", "financial.phase3e.dynamic_payback"):
        metric = model.metric(metric_id)
        assert metric["status"] == "CALCULATED"
        displayed = _professional_metric_rows(model, (metric_id,))[0][1]
        assert displayed.split("（", 1)[0] in text
    book = load_workbook(folder / manifest["files"]["F03"]["path"], read_only=True)
    source = load_workbook(folder / manifest["files"]["F04"]["file"], read_only=True)
    try:
        assert len(book.sheetnames) == 19 and len(source.sheetnames) == 10
        data = {row[0]: row for row in book.worksheets[15].iter_rows(values_only=True)
                if row and isinstance(row[0], str)}
        for metric_id in ("financial.phase3e.project_npv", "financial.phase3e.project_irr"):
            original = Decimal(data[metric_id][7])
            assert original == model.metric(metric_id)["value"]
            if metric_id.endswith("project_irr"):
                assert data[metric_id][3] == "—"
                assert abs(Decimal(data[metric_id][2].rstrip("%")) / 100 - original) < Decimal("0.0001")
            else:
                assert abs(Decimal(str(data[metric_id][2])) - original) < Decimal("0.000000001")
        source_identity = {row[0]: row[1] for row in source.worksheets[0].iter_rows(
            min_row=3, max_row=8, values_only=True) if row and row[0]}
        assert source_identity["result_hash"] == model.identity["result_hash"]
    finally:
        book.close()
        source.close()


@pytest.mark.parametrize("category", ("industrial_rooftop", "utility_scale_ground"))
def test_delivered_r2_word_workbooks_and_canonical_keep_project_metric_identity(category):
    # The original R2 artifacts were recovered byte-for-byte; pin the minimal
    # archived subset in Git so regression runs do not depend on local scratch.
    folder = Path(__file__).resolve().parents[2] / "tests/fixtures/solar-pv/phase7l-r2-delivery" / category
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    assert hashlib.sha256((folder / "manifest.json").read_bytes()).hexdigest() == {
        "industrial_rooftop": "cec094082957fb10e1f9f12628e5be58eb75d7dc703423f21edf1a9c0319914f",
        "utility_scale_ground": "8f05ef9f112bc5c469a43243e5ff3c77cdbc975da2ab7b88f825798c80ca11bc",
    }[category]
    for key in ("F01", "F03", "F04", "F06"):
        entry = manifest["files"][key]
        artifact = folder / entry.get("path", entry.get("file"))
        assert hashlib.sha256(artifact.read_bytes()).hexdigest() == entry["sha256"]
    result = loads((folder / "canonical.json").read_bytes())
    model = ReportModel.from_result(result, Catalog())
    assert manifest["identity"] == model.identity
    doc = Document(folder / manifest["files"]["F01"]["path"])
    text = _all_text(doc)
    assert "第13年" in text and "GRID_DELIVERABLE" not in text and "pending" not in text.lower()
    assert "项目净现值" in text and "项目内部收益率" in text
    for metric_id in ("financial.phase3e.project_npv", "financial.phase3e.project_irr",
                      "financial.phase3e.static_payback", "financial.phase3e.dynamic_payback"):
        metric = model.metric(metric_id)
        assert metric["status"] == "CALCULATED"
        displayed = _professional_metric_rows(model, (metric_id,))[0][1]
        assert displayed.split("（", 1)[0] in text
    book = load_workbook(folder / manifest["files"]["F03"]["path"], read_only=True)
    source = load_workbook(folder / manifest["files"]["F04"]["file"], read_only=True)
    try:
        assert len(book.sheetnames) == 19 and len(source.sheetnames) == 10
        data = {row[0]: row for row in book.worksheets[15].iter_rows(values_only=True)
                if row and isinstance(row[0], str)}
        for metric_id in ("financial.phase3e.project_npv", "financial.phase3e.project_irr"):
            original = Decimal(data[metric_id][7])
            assert original == model.metric(metric_id)["value"]
            assert abs(Decimal(str(data[metric_id][2])) - original) < Decimal("0.000000001")
        source_identity = {row[0]: row[1] for row in source.worksheets[0].iter_rows(
            min_row=3, max_row=8, values_only=True) if row and row[0]}
        assert source_identity["result_hash"] == model.identity["result_hash"]
    finally:
        book.close()
        source.close()
