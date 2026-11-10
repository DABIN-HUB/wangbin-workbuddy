"""R9 reader display is unit-driven and never alters the frozen results."""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import re

import pytest
from docx import Document
from docx.oxml.ns import qn
from docx.table import Table

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.report_claims import _project_irr_claim, _specific_project_judgment
from wangbin_solar_pv.report_display_numbers import decision_number, decision_percent
from wangbin_solar_pv.report_export import (
    ReportModel, _professional_metric_rows, _project_summary, _write_docx,
    _reader_glossary_ids, _reader_term_applicability, _formula_reader_evaluation, _npv_instances_note,
)
from wangbin_solar_pv.serialization import loads

CASES = Path(__file__).resolve().parents[2] / "reports/solar-pv/phase7l-r3-final-v5"


@pytest.fixture(scope="module", params=("industrial_rooftop", "utility_scale_ground"))
def model(request):
    canonical = loads((CASES / request.param / "canonical.json").read_bytes())
    return ReportModel.from_result(canonical, Catalog())


def test_unit_formats_are_not_magnitude_rules():
    assert decision_number(Decimal("999.999"), "CNY") == "1,000"
    assert decision_number(Decimal("4.175559"), "year") == "4.18"
    assert decision_number(Decimal("-31954.4"), "CNY") == "-31,954"
    assert decision_percent(Decimal("0.2287232636")) == "22.87%"
    assert decision_number(Decimal("NaN"), "CNY") == "UNKNOWN"


def test_decision_precision_and_canonical_values(model):
    roof = model.result["pv_type"] == "industrial_rooftop"
    expected = ("670,443", "22.87%", "4.18") if roof else ("260,919", "11.16%", "7.03")
    ids = ("financial.phase3e.project_npv", "financial.phase3e.project_irr",
           "financial.phase3e.static_payback")
    displayed = _professional_metric_rows(model, ids)
    assert tuple(row[1] for row in displayed) == expected
    assert model.metric(ids[0])["value"] != Decimal(expected[0].replace(",", ""))
    assert expected[0] in _project_summary(model)
    assert expected[1] in _project_irr_claim(model)
    assert expected[1] in _project_summary(model)
    assert len(_reader_glossary_ids(model.result["pv_type"])) == 24
    assert all(_reader_term_applicability(model, term) for term in _reader_glossary_ids(model.result["pv_type"]))


def test_cash_flow_reader_explains_per_component_rounding_residual(model):
    text = _specific_project_judgment(model, "CH16.02", str)
    if model.result["pv_type"] == "utility_scale_ground":
        assert "净流入147,369元；分项整数相减比未取整账簿净额多1元，仅为列示尾差" in text
    else:
        assert "净流入115,926元" in text
        assert "列示尾差" not in text
    assert model.metric("financial.phase3e.project_cash_flow")["value"][1] != Decimal(
        decision_number(model.metric("financial.phase3e.project_cash_flow")["value"][1], "CNY").replace(",", ""))


def test_each_of_120_tables_is_bound_to_its_caption_and_header(model, tmp_path):
    path = tmp_path / "candidate.docx"
    _write_docx(model, path, "R9结构回归", model.result["pv_type"])
    document = Document(path)
    captions = [p for p in document.paragraphs if p.style.name == "Caption" and re.match(r"表\d+ ", p.text)]
    assert len(document.tables) == len(captions) == 120
    expected = {
        9: ("月", "发电", "自用", "上网"),
        10: ("月", "结算截弃", "交付", "可用（结算前）", "性质"),
        16: ("运营年", "运维计提", "运维预计付款", "非现金折旧", "更换预计付款"),
        17: ("运营年", "交易费计提", "交易费预计付款"),
        19: ("运营年", "应税所得", "所得税计提", "所得税预计付款"),
        20: ("运营年", "其他现金税费", "增值税净现金额", "列示舍入差额", "项目现金税费合计"),
        22: ("期别", "上网回款", "自用节费", "预计另付交易费"),
        23: ("期别", "运维现金", "项目现金税费", "列示舍入差额", "运营收支净额"),
        24: ("期别", "运营收支净额", "资本支出付款", "营运资金增加"),
        25: ("期别", "营运资金回收", "终期资产现金", "项目净现金流"),
        26: ("核验事项", "状态", "影响判断", "所需材料"),
        117: ("中文术语", "缩写", "简明释义", "本项目适用说明"),
        118: ("中文", "English", "缩写", "读者释义", "单位及核查边界"),
        119: ("单位/符号", "含义", "不得混用的边界"),
    }
    for number, caption in enumerate(captions, 1):
        assert caption.text.startswith(f"表{number} ")
        assert caption._p.getnext().tag == qn("w:tbl")
        table = Table(caption._p.getnext(), document)
        header = tuple(cell.text for cell in table.rows[0].cells)
        assert header and len(table.rows) > 1
        assert table.rows[0]._tr.trPr.find(qn("w:tblHeader")) is not None
        assert all(len(row.cells) == len(header) for row in table.rows)
        if number in expected:
            assert header == expected[number]
        if number == 19:
            assert "计提与预计付款分别列示" in caption.text
            assert "计提及预计付款不同" not in caption.text
    assert len(document.tables[116].rows) == 25  # 24 reader definitions + header
    assert len(document.tables[117].rows) == 190  # entire frozen 189-term registry
    note = next(p for p in document.paragraphs if p.text.startswith("冻结文本定义：O_y = Σ(k∈𝒪_y)"))
    assert any(run.text == "𝒪" and run._r.xpath("./w:rPr/w:rFonts")[0].get(qn("w:hAnsi")) == "Cambria Math"
               for run in note.runs)
    assert "冻结LaTeX：" in note.text and "Σ(k∈𝒪_y)" in note.text
    evaluation = next(p.text for p in document.paragraphs if p.text.startswith("评价与适用："))
    assert "本项目已有可用NPV计算值" in evaluation
    assert "本次无应偿本息，DSCR无定义而不是0倍" in evaluation
    npv = next(p.text for p in document.paragraphs if p.text.startswith("F-NPV 输出实例分别为："))
    assert "已计算的项目NPV不因其他实例未实现而失效" in npv


def test_formula_reader_navigation_fragment_respects_blocked_metrics_and_debt(model, tmp_path):
    changed = deepcopy(model)
    normalized = changed.result["inputs"]["normalized"]
    normalized["finance.debt_ratio"] = Decimal("0.4")
    records = changed.result["source_snapshot"]["phase2"]["records"]
    assert any(record["field_id"] == "finance.debt_ratio" for record in records)
    for record in records:
        if record["field_id"] == "finance.debt_ratio":
            record["value"] = normalized["finance.debt_ratio"]
    for metric_id in ("financial.phase3e.project_npv", "financial.phase3e.project_irr"):
        changed.metric_by_id[metric_id]["status"] = "BLOCKED_MISSING_INPUT"
        changed.metric_by_id[metric_id]["value"] = None
    path = tmp_path / "blocked-metrics-and-debt.docx"
    document = Document()
    document.add_paragraph(_formula_reader_evaluation(changed))
    outputs = [m for m in changed.metrics if m.get("formula_id") == "F-NPV"]
    assert outputs
    document.add_paragraph(_npv_instances_note(changed, outputs))
    document.save(path)
    paragraphs = [p.text for p in Document(path).paragraphs]
    evaluation = next(text for text in paragraphs if text.startswith("评价与适用："))
    assert "本项目NPV尚无可用计算值" in evaluation
    assert "本项目IRR尚无可用计算值" in evaluation
    assert "本次有债务假设但DSCR无可用值" in evaluation
    assert "在无债务的本次项目中" not in evaluation
    npv = next(text for text in paragraphs if text.startswith("F-NPV 输出实例分别为："))
    assert "本次项目NPV未形成可用数值" in npv
    assert "已计算的项目NPV不因其他实例未实现而失效" not in npv
