"""R9 reader display is unit-driven and never alters the frozen results."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import re

import pytest
from docx import Document
from docx.oxml.ns import qn
from docx.table import Table

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.errors import ContractError
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
    note = next(p for p in document.paragraphs if p.text.startswith("文字表达：O_y = Σ(k∈𝒪_y)"))
    assert any(run.text == "𝒪" and run._r.xpath("./w:rPr/w:rFonts")[0].get(qn("w:hAnsi")) == "Cambria Math"
               for run in note.runs)
    assert "冻结LaTeX：" not in note.text and "Σ(k∈𝒪_y)" in note.text
    evaluation = next(p.text for p in document.paragraphs if p.text.startswith("评价与适用："))
    assert "本项目已有可用NPV计算值" in evaluation
    assert "本次无应偿本息，DSCR无定义而不是0倍" in evaluation
    npv = next(p.text for p in document.paragraphs if p.text.startswith("本项目净现值已按"))
    assert "其他评价口径是否适用" in npv


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
    npv = next(text for text in paragraphs if text.startswith("本项目净现值尚无可用结果"))
    assert "补齐项目现金流及折现条件" in npv
    assert "本项目净现值已按" not in npv


def test_r10_reader_preview_separates_frozen_word_appendix_contract(model, tmp_path):
    path = tmp_path / "reader-preview.docx"
    receipt = _write_docx(model, path, "示例项目", model.result["pv_type"], reader_preview=True)
    document = Document(path)
    paragraphs = [p.text for p in document.paragraphs]
    assert receipt["full_word_appendix_contract"] == "NOT_SATISFIED_READER_PREVIEW"
    assert receipt["frozen_word_identity_contract"] == "NOT_SATISFIED_READER_PREVIEW"
    assert receipt["numbering"]["formulas"] == 6
    assert len(document.tables) == receipt["numbering"]["tables"] == 35
    assert len(document.tables[-2].rows) == 25
    static_title = next(p for p in document.paragraphs if p.text.startswith("F-STATIC-PAYBACK "))
    assert static_title.paragraph_format.page_break_before is True
    for number, table in enumerate(document.tables, 1):
        assert table.rows[0]._tr.xpath("./w:trPr/w:tblHeader")
        assert all("\n表" not in cell.text and f"表{number}" not in cell.text
                   for cell in table.rows[0].cells)
        assert all(len(row.cells) == len(table.rows[0].cells) for row in table.rows)
    equipment = document.tables[10]
    assert len(equipment.columns) == 3
    assert [cell.text for cell in equipment.rows[0].cells] == ["设备／布置输入", "合成方案值", "参数类别"]
    assert all(cell.text in {"组件与组串", "逆变器", "阵列与安全布置"}
               for row in equipment.rows[1:] for cell in row.cells[2:])
    resource_note = next(p for p in document.paragraphs if p.text.startswith("辐照物理口径专项说明："))
    assert resource_note.paragraph_format.keep_together is True
    month_caption = ("表9 首年月度发电与上网（kWh；示例预测）" if model.result["pv_type"] == "utility_scale_ground"
                     else "表9 首年月度发电与消纳（kWh；示例预测）")
    assert month_caption in paragraphs
    assert "项目判断：资料尚待核验，暂不具备投资决策条件" in paragraphs
    assert sum(p.startswith(("1. 气象与场址：", "2. 设备、造价与更换：",
                             "3. 权属、接入与交易：", "4. 政策与资料授权：")) for p in paragraphs) == 4
    assert any("元/Wp与元/kWp的换算口径尚待专业核验" in text for text in paragraphs)
    assert sum(p == "本报告内容仅供参考，正式使用时需根据实际情况调整。" for p in paragraphs) == 1
    assert any("受限储备" in cell.text and "不与收款法重复调整" in cell.text
               for row in document.tables[-2].rows for cell in row.cells)

    reader_texts = paragraphs + [cell.text for table in document.tables for row in table.rows for cell in row.cells]
    assert not any(word in text for text in reader_texts for word in (
        "冻结LaTeX", "阶段性样件", "开发样件", "测试报告", "测试假设", "阶段验收",
        "SYNTHETIC-", "UNKNOWN", "质量清单门禁", "canonical"))


def test_r10_reader_preview_rejects_verified_real_project(model, tmp_path):
    result = deepcopy(model.result)
    result["project_id"] = "REAL-PROJECT"
    result["maturity"]["real_project"] = "VERIFIED"
    result["status"] = "COMPLETE"
    with pytest.raises(ContractError, match="REPORT_READER_PREVIEW_SYNTHETIC_ONLY"):
        _write_docx(replace(model, result=result), tmp_path / "rejected.docx",
                    "已核验项目", model.result["pv_type"], reader_preview=True)
    assert not (tmp_path / "rejected.docx").exists()
