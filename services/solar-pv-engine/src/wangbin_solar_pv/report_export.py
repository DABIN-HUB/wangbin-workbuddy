"""Phase 5 unified industrial-rooftop report exporter.

The exporter is deliberately a read-only presentation layer over one validated
Phase 3G canonical result. It never recalculates financial values. PDF output
is produced only by an installed DOCX renderer; a missing renderer is a
reported BLOCKED state, never an empty or renamed file.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from typing import Any

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .calculation.result_contract import validate_result
from .errors import ContractError
from .local_files import Workspace
from .serialization import digest, dumps
from .source_xlsx import create_source_workbook, SHEETS as SOURCE_SHEETS


CHAPTERS = (
    ("CH01", "执行摘要与初步结论", ("项目识别及方案版本", "DC/AC及发电指标", "投资及财务指标", "消纳售电与资料成熟度", "阻断风险和四态建议")),
    ("CH02", "总论与编制依据", ("项目背景与目的", "评价范围与价格现金流口径", "标准与政策适用", "资料目录与数据年份", "假设、版本及免责")),
    ("CH03", "工程概况及建设必要性", ("业主与投资运营主体", "站址及工程分类", "建设及权属模式", "用能及售电模式", "规模目标与建设必要性")),
    ("CH04", "选址及建设条件", ("位置坐标与边界", "地形海拔与面积核算", "土地屋顶权属与期限", "遮挡与结构安全", "交通生态灾害限制", "专项建设条件与缺口")),
    ("CH05", "太阳能资源与气象", ("数据集元信息与授权", "辐照分量与单位", "温度风速与12个月", "逐年差异与典型气象年", "平面转置与气象适配", "误差与交叉验证降级")),
    ("CH06", "工程任务、规模与方案比选", ("任务与可利用面积", "组件排列与数量", "DC/AC规模与比例", "基准与可行替代方案", "比选口径与选择理由", "分类专项方案")),
    ("CH07", "光伏系统初步设计", ("组件与逆变器选择", "支架及几何参数", "串并联与电压电流校核", "损失分项与物理顺序", "系统结构及接口", "储能或分类专项设计")),
    ("CH08", "发电量预测与效率评价", ("预测方法及能量边界", "月度与首年电量", "逐年衰减和更换", "PR、等效小时和容量因子", "不可利用与限发校核", "不确定性与结果限制")),
    ("CH09", "电气系统与电网接入", ("接入点与电压", "变压器线路与容量约束", "升压保护及送出工程", "并网与交易核验", "限发与尚待电网确认")),
    ("CH10", "电力消纳与电价售电方案", ("负荷资料与同粒度匹配", "自用、上网与限发平衡", "分时电价与可避免费用", "合同与交易结算模式", "逐时市场价与其他收益", "储能调度独立边界")),
    ("CH11", "总平面与土建施工条件", ("总平面与功能分区", "地基与支架基础", "结构承载与安全疏散", "施工物流道路与排水", "专项勘察及工程量缺口")),
    ("CH12", "环境、生态、安全及社会影响", ("节能减排与因子", "环境生态与水土保持", "消防与施工运行安全", "社会影响与利益主体", "专项评估与合规阻断")),
    ("CH13", "实施组织与建设计划", ("开发前提与组织分工", "初设采购施工调试验收", "依赖关系与关键路径", "建设风险与缓释", "里程碑与进入下一阶段条件")),
    ("CH14", "工程投资估算 CAPEX", ("估算依据与边界", "设备材料投资", "工程建设与场址专项", "前期与管理及预备费", "建设期利息与资金进度", "税口径与单位投资校核")),
    ("CH15", "运营费用 OPEX 与折旧税费", ("年度运营费", "资产分类折旧与残值", "更换与寿命计划", "税制与实际现金税金", "非现金与年度汇总校核")),
    ("CH16", "财务效益与投资回报", ("收入与残值", "项目投资现金流", "股东现金流与融资偿债", "NPV与IRR", "静态动态回收期", "LCOE与可交付电量", "DSCR与债务条件", "盈亏平衡与目标差距")),
    ("CH17", "敏感性、情景与风险", ("单因素敏感性", "悲观基准乐观组合", "阈值与稳健性", "风险清单与证据状态", "属性及反向约束校核")),
    ("CH18", "综合结论及后续工作", ("四态唯一建议", "结论证据及独立否决", "推进条件与触发阈值", "资料缺口与专项核查", "决策里程碑及免责")),
)
APPENDICES = (
    ("APP01", "项目资料索引"), ("APP02", "12个月气象与发电量"), ("APP03", "设备及损失参数"),
    ("APP04", "CAPEX明细"), ("APP05", "OPEX、折旧、更换与税费"), ("APP06", "全周期项目与资本金现金流"),
    ("APP07", "偿债明细"), ("APP08", "敏感性与情景数据"), ("APP09", "政策适用性"),
    ("APP10", "未完成事项"), ("APP11", "公式逐符号字典"), ("APP12", "全部术语中英词典"),
    ("APP13", "版本与数据质量说明"),
)

MODEL_SHEETS = (
    ("M01", "项目参数"), ("M02", "术语和公式说明"), ("M03", "数据质量"), ("M04", "资源月度"),
    ("M05", "系统容量与损耗"), ("M06", "发电预测-月度"), ("M07", "逐年衰减"), ("M08", "负荷与消纳"),
    ("M09", "电价与收入"), ("M10", "CAPEX"), ("M11", "OPEX"), ("M12", "折旧与税费"),
    ("M13", "融资与偿债"), ("M14", "项目现金流"), ("M15", "资本金现金流"), ("M16", "财务指标"),
    ("M17", "敏感性"), ("M18", "方案比较"), ("M19", "一致性校验"),
)

_WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


@dataclass(frozen=True)
class ReportModel:
    result: dict[str, Any]
    metrics: tuple[dict[str, Any], ...]
    metric_by_id: dict[str, dict[str, Any]]

    @classmethod
    def from_result(cls, result: dict[str, Any], catalog) -> "ReportModel":
        validated = validate_result(result, catalog)
        metrics = tuple(validated["results"]["metrics"])
        return cls(validated, metrics, {m["metric_id"]: m for m in metrics})

    @property
    def identity(self) -> dict[str, str]:
        return {key: self.result[key] for key in ("model_version", "run_id", "input_hash", "source_snapshot_id", "result_hash")}

    def metric(self, metric_id: str) -> dict[str, Any] | None:
        return self.metric_by_id.get(metric_id)

    def value(self, metric_id: str) -> Any:
        metric = self.metric(metric_id)
        return None if metric is None or metric.get("status") != "CALCULATED" else metric.get("value")

    def status(self, metric_id: str) -> str:
        metric = self.metric(metric_id)
        return "UNKNOWN" if metric is None else metric.get("status", "UNKNOWN")


class ExportError(ContractError):
    """Stable report-export failure with a public, path-free code."""


def _safe_stem(value: str) -> tuple[str, str | None]:
    if not isinstance(value, str) or not value.strip():
        value = "未命名项目"
    original = value
    value = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", "_", value).strip(" .")
    if not value or value.upper().split(".")[0] in _WINDOWS_RESERVED:
        value = "项目-" + value
    value = value[:80].rstrip(" .")
    if not value:
        raise ContractError("REPORT_PROJECT_NAME_INVALID")
    return value, (original if value != original else None)


def _string(value: Any) -> str:
    if value is None:
        return "UNKNOWN"
    if isinstance(value, (dict, list)):
        return dumps(value)
    return str(value)


def _display_metric(metric: dict[str, Any]) -> str:
    if metric.get("status") == "CALCULATED":
        return _string(metric.get("value"))
    return f"{metric.get('status', 'UNKNOWN')}：{metric.get('reason') or '未提供可用数值'}"


def _metric_rows(model: ReportModel, *, prefixes: tuple[str, ...] = ()) -> list[list[Any]]:
    rows = []
    for metric in model.metrics:
        if prefixes and not metric["metric_id"].startswith(prefixes):
            continue
        rows.append([metric["metric_id"], metric["status"], _display_metric(metric), metric.get("unit") or "UNKNOWN",
                     metric.get("formula_id") or "UNKNOWN", ",".join(metric.get("source_ids") or []) or "UNKNOWN",
                     metric.get("reason") or ""])
    return rows


def _normalized_rows(model: ReportModel, *, prefixes: tuple[str, ...] = ()) -> list[list[Any]]:
    normalized = model.result["inputs"].get("normalized", {})
    used_sources = model.result["inputs"].get("used_sources", {})
    return [[key, _string(value), "INPUT", ",".join(used_sources.get(key, [])) if isinstance(used_sources, dict) else _string(used_sources)]
            for key, value in sorted(normalized.items()) if not prefixes or key.startswith(prefixes)]


def _identity_rows(model: ReportModel) -> list[list[Any]]:
    return [[key, value, "CANONICAL"] for key, value in model.identity.items()]


def _header(ws, model: ReportModel, sheet_id: str, title: str) -> None:
    ws.append([sheet_id, title, "STATIC_SNAPSHOT", "草稿，资料不足，未决策就绪"])
    for key, value in model.identity.items():
        ws.append([key, value, "IDENTITY"])
    ws.append(["project_id", model.result["project_id"], "CANONICAL"])
    ws.append(["scenario_id", model.result["scenario_id"], "CANONICAL"])
    ws.append(["状态说明", "STATIC_SNAPSHOT；Excel修改后必须重新运行引擎生成新run", "BOUNDARY"])


def _style_sheet(ws, header_row: int) -> None:
    ws.freeze_panes = f"A{header_row + 1}"
    ws.auto_filter.ref = f"A{header_row}:{get_column_letter(max(1, ws.max_column))}{ws.max_row}"
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF", size=12)
        cell.fill = PatternFill("solid", fgColor="16446B")
    for cell in ws[header_row]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2B6D9A")
    for column in range(1, ws.max_column + 1):
        width = min(55, max(14, max((len(_string(ws.cell(row, column).value)) for row in range(1, min(ws.max_row, 40) + 1)), default=14) + 2))
        ws.column_dimensions[get_column_letter(column)].width = width
    for row in ws.iter_rows():
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if isinstance(cell.value, str):
                cell.data_type = "s"
                cell.number_format = "@"


def _sheet_data(model: ReportModel, sheet_id: str, title: str) -> tuple[list[str], list[list[Any]]]:
    normalized = model.result["inputs"].get("normalized", {})
    metrics = model.metrics
    if sheet_id == "M01":
        rows = _identity_rows(model) + [["pv_type", model.result["pv_type"], "CANONICAL"], ["currency", model.result["currency"], "CANONICAL"],
            ["evaluation_date", model.result["evaluation_date"], "CANONICAL"], ["calculation_status", model.result["status"], "CANONICAL"]] + _normalized_rows(model, prefixes=("project.", "site.", "system."))
        headers = ["参数", "值", "来源"]
    elif sheet_id == "M02":
        rows = [[m["formula_id"], m["metric_id"], m["unit"] or "UNKNOWN", m["status"], m.get("reason") or "", ",".join(m.get("report_locations") or [])] for m in metrics]
        headers = ["formula_id", "metric_id", "单位", "状态", "边界/原因", "章节"]
    elif sheet_id == "M03":
        rows = [["maturity.calculation", model.result["maturity"]["calculation"], "CANONICAL"], ["maturity.real_project", model.result["maturity"]["real_project"], "CANONICAL"], ["maturity.four_files", "DRAFT_PARTIAL", "EXPORTER"]]
        rows += [[m["metric_id"], m["status"], m.get("reason") or "", ",".join(m.get("source_ids") or []) or "UNKNOWN"] for m in metrics]
        rows += [["finding", item.get("code", "UNKNOWN"), item.get("status", "UNKNOWN"), "需保留并人工关闭"] for item in model.result.get("findings", [])]
        headers = ["质量轴/指标", "状态/值", "原因", "来源/说明"]
    elif sheet_id in {"M04", "M06"}:
        metric = model.metric("energy.monthly.year.1")
        values = metric.get("value") if metric and metric.get("status") == "CALCULATED" else None
        rows = [[index, value if values is not None else "UNKNOWN", "energy.monthly.year.1" if values is not None else "UNKNOWN", metric.get("status") if metric else "UNKNOWN"] for index, value in enumerate(values or [None] * 12, 1)]
        headers = ["月份", "kWh", "formula/metric", "状态"]
    elif sheet_id == "M05":
        rows = [["dc_capacity", _display_metric(model.metric("dc_capacity")), "kWp", "F-DC-CAPACITY"], ["ac_capacity", _display_metric(model.metric("ac_capacity")), "kWac", "F-AC-CAPACITY"], ["dc_ac_ratio", _display_metric(model.metric("dc_ac_ratio")), "1", "F-DC-AC-RATIO"]]
        losses = normalized.get("system.losses")
        if isinstance(losses, list):
            rows.extend([["loss." + str(item.get("row_id", "UNKNOWN")), _string(item.get("fields", {}).get("system.losses.value")), "1", "INPUT"] for item in losses])
        headers = ["项目", "值", "单位", "来源/公式"]
    elif sheet_id == "M07":
        value = model.value("energy.annual_array")
        rows = [[index, item, "kWh", "energy.annual_array"] for index, item in enumerate(value or [None], 1)]
        headers = ["运营年", "电量", "单位", "来源"]
    elif sheet_id == "M08":
        rows = _metric_rows(model, prefixes=("consumption", "energy.delivered"))
        headers = ["metric_id", "状态", "值", "单位", "公式", "来源", "原因"]
    elif sheet_id == "M09":
        rows = _metric_rows(model, prefixes=("revenue",)) + _normalized_rows(model, prefixes=("project.sales", "revenue.", "tariff."))
        headers = ["metric/field", "状态/值", "显示值", "单位/来源", "公式", "来源", "原因"]
    elif sheet_id in {"M10", "M11", "M12", "M13"}:
        prefixes = {"M10": ("capex.",), "M11": ("opex.",), "M12": ("assets.", "tax."), "M13": ("finance.",)}[sheet_id]
        rows = _normalized_rows(model, prefixes=prefixes) + _metric_rows(model, prefixes=("financial.",))
        headers = ["field/metric", "值", "状态/来源", "source_ids"]
    elif sheet_id in {"M14", "M15", "M16"}:
        rows = _metric_rows(model, prefixes=("financial.", "npv"))
        headers = ["metric_id", "状态", "值/阻断原因", "单位", "公式", "来源", "原因"]
    elif sheet_id == "M17":
        rows = [["sensitivity", "NOT_TESTED", "未提供合法独立敏感性重算结果", "UNKNOWN"]]
        rows += [[item.get("code", "finding"), item.get("status", "UNKNOWN"), "请补充来源后执行", "UNKNOWN"] for item in model.result.get("findings", [])]
        headers = ["因素/证据", "状态", "说明", "值"]
    elif sheet_id == "M18":
        rows = [["BASE", model.result["scenario_id"], model.result["status"], "仅有当前SYNTHETIC基准；无合法替代方案"], ["alternative", "NOT_TESTED", "UNKNOWN", "未建模，不比较"]]
        headers = ["方案", "场景", "状态", "说明"]
    else:
        rows = [["identity", key, value, "一致性依据"] for key, value in model.identity.items()]
        rows += [["metric_status", m["metric_id"], m["status"], _display_metric(m)] for m in metrics]
        headers = ["检查", "对象", "实际", "说明"]
    return headers, rows


def _write_model_xlsx(model: ReportModel, output: Path) -> dict[str, Any]:
    book = Workbook()
    book.remove(book.active)
    for sheet_id, title in MODEL_SHEETS:
        ws = book.create_sheet(title)
        _header(ws, model, sheet_id, title)
        headers, rows = _sheet_data(model, sheet_id, title)
        ws.append(headers)
        header_row = ws.max_row
        for row in rows:
            ws.append([_string(value) for value in row])
        _style_sheet(ws, header_row)
    output_tmp = output.with_name("." + output.stem + ".tmp.xlsx")
    book.save(output_tmp)
    if output_tmp.stat().st_size > 32 * 1024 * 1024:
        output_tmp.unlink(missing_ok=True)
        raise ContractError("REPORT_XLSX_SIZE_LIMIT")
    inspected = load_workbook(output_tmp, read_only=True, data_only=False)
    try:
        if inspected.sheetnames != [name for _, name in MODEL_SHEETS] or len(inspected.sheetnames) != 19:
            raise ContractError("REPORT_XLSX_SHEETS")
        for ws in inspected:
            if ws[1][0].value not in {sid for sid, _ in MODEL_SHEETS}:
                raise ContractError("REPORT_XLSX_IDENTITY")
    finally:
        inspected.close()
    os.replace(output_tmp, output)
    return {"path": output.name, "size": output.stat().st_size, "sha256": _sha256(output), "sheets": [name for _, name in MODEL_SHEETS], "mode": "STATIC_SNAPSHOT"}


def _set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def _add_table(document: Document, headers: list[str], rows: list[list[Any]], caption: str | None = None) -> None:
    if caption:
        paragraph = document.add_paragraph(caption)
        paragraph.style = "Caption"
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        cell.text = _string(header)
        _set_cell_shading(cell, "16446B")
        for run in cell.paragraphs[0].runs:
            run.font.bold = True
            run.font.color.rgb = None
    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            cells[index].text = _string(value)
            cells[index].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
    document.add_paragraph()


def _add_toc(document: Document) -> None:
    paragraph = document.add_paragraph()
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText"); instruction.set(qn("xml:space"), "preserve"); instruction.text = "TOC \\o \"1-3\" \\h \\z \\u"
    separate = OxmlElement("w:fldChar"); separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t"); text.text = "目录将在 Word/LibreOffice 中更新"
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    run._r.extend((begin, instruction, separate, text, end))


def _item_state(model: ReportModel, chapter_id: str, title: str) -> tuple[str, str]:
    keywords = {
        "DC/AC": ("dc_capacity", "ac_capacity"), "发电": ("energy.year.1", "energy.monthly.year.1"),
        "电量": ("energy.year.1", "energy.delivered.year.1"), "消纳": ("consumption.year.1", "consumption.self_ratio.year.1"),
        "收入": ("revenue.year.1",), "投资": ("financial.capex.total", "financial.unit_investment"),
        "财务": ("financial.phase3e.project_npv",), "NPV": ("financial.phase3e.project_npv",),
        "IRR": ("financial.phase3e.project_irr",), "回收期": ("financial.phase3e.static_payback",),
        "LCOE": ("financial.phase3e.lcoe",), "DSCR": ("financial.phase3e.dscr",),
    }
    selected = []
    for token, ids in keywords.items():
        if token in title:
            selected.extend(ids)
    if not selected:
        selected = ["energy.year.1"] if chapter_id in {"CH05", "CH08"} else []
    statuses = [model.status(metric_id) for metric_id in selected]
    if any(status == "CALCULATED" for status in statuses):
        return "EVIDENCED", "本项引用同一 canonical 结果中的已计算指标：" + ", ".join(f"{mid}={_display_metric(model.metric(mid))}" for mid in selected if model.metric(mid))
    if any(status.startswith("BLOCKED") or status == "NOT_IMPLEMENTED" for status in statuses):
        reasons = [model.metric(mid).get("reason") for mid in selected if model.metric(mid) and model.metric(mid).get("reason")]
        return "PENDING_VERIFICATION", "本项未生成合法数值；上游状态为 " + ", ".join(statuses) + "。" + (" 原因：" + ";".join(reasons) if reasons else "")
    return "UNKNOWN", "未找到本项对应的经验证字段或公式结果；需补充来源后复核。"


def _write_docx(model: ReportModel, output: Path, display_name: str) -> dict[str, Any]:
    document = Document()
    section = document.sections[0]
    section.top_margin = Cm(2.0); section.bottom_margin = Cm(2.0); section.left_margin = Cm(2.4); section.right_margin = Cm(2.0)
    styles = document.styles
    styles["Normal"].font.name = "等线"; styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "等线"); styles["Normal"].font.size = Pt(10.5)
    for heading in ("Heading 1", "Heading 2", "Heading 3"):
        styles[heading].font.name = "黑体"; styles[heading]._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
    title = document.add_paragraph(); title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("工商业屋顶光伏预可研报告"); run.bold = True; run.font.size = Pt(22); run.font.name = "黑体"
    subtitle = document.add_paragraph(); subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.add_run("草稿，资料不足，未决策就绪\nDRAFT_PARTIAL").bold = True
    document.add_paragraph()
    _add_table(document, ["项目身份", "值", "状态"], [["项目名称", display_name, "显示名；canonical未提供正式名称时使用project_id"], ["项目类型", model.result["pv_type"], "CANONICAL"], ["评价日期", model.result["evaluation_date"], "CANONICAL"], ["状态", model.result["status"], "上游结果"], *[[key, value, "CANONICAL"] for key, value in model.identity.items()]])
    document.add_paragraph("本文件为基于单一 canonical calculation result JSON 的开发样件。它不替代正式可研、设计、结构鉴定、并网意见、合同审核或投资决策。UNKNOWN、BLOCKED、NOT_IMPLEMENTED 和 NOT_TESTED 均保留原状态，不以零值代替。")
    document.add_heading("目录", level=1); _add_toc(document)
    document.add_page_break()
    document.add_heading("执行摘要", level=1)
    _add_table(document, ["metric_id", "状态", "值/原因", "单位", "公式", "来源", "阻断原因"], _metric_rows(model, prefixes=("dc_capacity", "ac_capacity", "energy.year", "consumption.year", "revenue.year", "financial."))[:18], "表1 执行摘要指标（canonical原值）")
    document.add_paragraph("初步结论：当前结果为 PARTIAL，且资料为 SYNTHETIC 场景。由于项目级真实资源、政策、报价及财务现金流证据未闭合，报告只能作为开发样件，不能据此作出真实投资决策。")
    for chapter_id, chapter_title, items in CHAPTERS:
        document.add_heading(f"{chapter_id} {chapter_title}", level=1)
        for number, item in enumerate(items, 1):
            document.add_heading(f"{chapter_id}.{number:02d} {item}", level=2)
            state, content = _item_state(model, chapter_id, item)
            document.add_paragraph(f"内容状态：{state}。{content}")
            document.add_paragraph(f"适用边界：工商业屋顶（industrial_rooftop）；本项仅读取本次运行的 canonical 结果，不在报告层重新计算。需补充或关闭的资料、授权和专业复核事项保留在质量与缺口表中。")
    document.add_heading("结果与公式索引", level=1)
    _add_table(document, ["metric_id", "状态", "值/原因", "单位", "formula_id", "source_ids", "阻断原因"], _metric_rows(model), "表2 全量结果指标索引")
    for app_id, app_title in APPENDICES:
        document.add_heading(f"{app_id} {app_title}", level=1)
        document.add_heading(f"{app_id}.01 资料或结果明细", level=2)
        document.add_paragraph("本附录保留稳定编号和语义内容。可提供的数据仅来自本次 canonical、来源快照和公式执行映射；未提供的原始附件、合同、授权文件和真实项目资料不在公开样件中复制。")
        document.add_heading(f"{app_id}.02 状态、限制与后续核验", level=2)
        document.add_paragraph("当前状态为 DRAFT_PARTIAL。请按缺口清单补充合法来源并重新运行引擎；不得在此文件中手工替换财务数字或将 SYNTHETIC 标记改为 REAL。")
    document.add_heading("术语与公式说明", level=1)
    _add_table(document, ["公式/指标", "定义版本", "单位", "状态", "符号与边界"], [[m["formula_id"], m.get("formula_version", "UNKNOWN"), m.get("unit") or "UNKNOWN", m["status"], "详见同一 metric 的 input_field_ids、method_parameter_ids、source_ids"] for m in model.metrics])
    document.add_heading("版本与质量声明", level=1)
    document.add_paragraph("四文件身份均应绑定同一 model_version、run_id、input_hash、source_snapshot_id 和 result_hash。XLSX 为 STATIC_SNAPSHOT；在 Excel 中修改输入不会自动使报告或旧结果有效，必须重新运行引擎生成新的运行身份。PDF 只有在真实转换器可用并成功解析时才会生成。")
    footer = document.sections[0].footer.paragraphs[0]; footer.alignment = WD_ALIGN_PARAGRAPH.CENTER; footer.add_run("DRAFT_PARTIAL · 草稿，资料不足，未决策就绪 · ")
    fld = OxmlElement("w:fldSimple"); fld.set(qn("w:instr"), "PAGE"); footer._p.append(fld)
    tmp = output.with_name("." + output.name + ".tmp")
    document.save(tmp)
    os.replace(tmp, output)
    return {"path": output.name, "size": output.stat().st_size, "sha256": _sha256(output), "chapters": 18, "chapter_items": 100, "appendices": 13, "appendix_items": 26}


def _sha256(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _convert_pdf(docx: Path, output: Path) -> dict[str, Any]:
    renderer = shutil.which("soffice") or shutil.which("libreoffice")
    if not renderer:
        return {"status": "BLOCKED", "reason": "PDF_RENDERER_UNAVAILABLE", "renderer": None}
    with tempfile.TemporaryDirectory(prefix="solar-pv-pdf-") as tmp:
        try:
            completed = subprocess.run([renderer, "--headless", "--convert-to", "pdf", "--outdir", tmp, str(docx)], capture_output=True, text=True, timeout=180, check=False)
        except (OSError, subprocess.TimeoutExpired):
            return {"status": "BLOCKED", "reason": "PDF_RENDERER_FAILED", "renderer": Path(renderer).name}
        generated = Path(tmp) / (docx.stem + ".pdf")
        if completed.returncode != 0 or not generated.is_file() or generated.stat().st_size == 0:
            return {"status": "BLOCKED", "reason": "PDF_RENDERER_FAILED", "renderer": Path(renderer).name}
        os.replace(generated, output)
    return {"status": "GENERATED", "renderer": Path(renderer).name, "path": output.name, "size": output.stat().st_size, "sha256": _sha256(output)}


def _assert_same_identity(files: dict[str, Any], identity: dict[str, str]) -> None:
    for entry in files.values():
        if entry.get("status") == "BLOCKED":
            continue
        if any(entry.get(key) not in (None, identity[key]) for key in identity):
            raise ContractError("REPORT_IDENTITY_MISMATCH")


def export_rooftop_report(result: dict[str, Any], catalog, workspace: Workspace, output_dir: str, *, formula_map: dict[str, Any] | None = None) -> dict[str, Any]:
    """Generate a bounded DRAFT_PARTIAL report set from one canonical result."""
    if not isinstance(workspace, Workspace) or not isinstance(output_dir, str) or not output_dir.strip():
        raise ContractError("REPORT_OUTPUT_TARGET")
    root = workspace.path(output_dir, json_only=False)
    if root.exists():
        if not root.is_dir():
            raise ContractError("REPORT_OUTPUT_TARGET")
    else:
        root.mkdir()
    model = ReportModel.from_result(result, catalog)
    normalized = model.result["inputs"].get("normalized", {})
    display_name, name_mapping = _safe_stem(normalized.get("project.name") or model.result["project_id"])
    stem = display_name
    files: dict[str, Any] = {}
    started = time.perf_counter()
    docx_path = root / f"{stem}-光伏预可研报告.docx"
    xlsx_path = root / f"{stem}-测算模型.xlsx"
    source_name = f"{stem}-资料来源与假设清单.xlsx"
    if any(path.exists() for path in (docx_path, xlsx_path, root / source_name)):
        raise ContractError("REPORT_OUTPUT_EXISTS")
    files["F01"] = _write_docx(model, docx_path, display_name)
    files["F03"] = _write_model_xlsx(model, xlsx_path)
    source_started = time.perf_counter()
    source_receipt = create_source_workbook(model.result, catalog, Workspace(root), source_name, formula_map=formula_map)
    files["F04"] = {**source_receipt, "generation_seconds": round(time.perf_counter() - source_started, 6)}
    pdf_path = root / f"{stem}-光伏预可研报告.pdf"
    files["F02"] = _convert_pdf(docx_path, pdf_path)
    identity = model.identity
    for entry in files.values():
        if entry.get("status") != "BLOCKED":
            entry.update(identity)
    _assert_same_identity(files, identity)
    receipt = {
        "status": "DRAFT_PARTIAL" if files["F02"].get("status") != "GENERATED" else "DRAFT_PARTIAL",
        "phase": "PHASE5_INDUSTRIAL_ROOFTOP_REPORT_EXPORT",
        "project_id": model.result["project_id"], "pv_type": model.result["pv_type"],
        "display_name": display_name, "name_mapping": name_mapping,
        "identity": identity, "files": files,
        "coverage": {"chapters": 18, "chapter_items": 100, "appendices": 13, "appendix_items": 26, "model_sheets": 19, "source_sheets": 10},
        "pdf_status": files["F02"].get("status"),
        "calculation_status": model.result["status"], "four_file_gate": "BLOCKED" if files["F02"].get("status") != "GENERATED" else "NOT_FORMAL_ACCEPTANCE",
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "not_decision_ready": True,
        "sensitive_raw_attachments_included": False,
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt["manifest"] = {"path": manifest_path.name, "size": manifest_path.stat().st_size, "sha256": _sha256(manifest_path)}
    return receipt
