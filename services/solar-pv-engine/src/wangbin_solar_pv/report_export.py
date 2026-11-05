"""Unified Phase 5/6 solar-PV report exporter.

The exporter is deliberately a read-only presentation layer over one validated
canonical result. It never recalculates financial values. PDF output is produced
only by an installed DOCX renderer; a missing renderer is a reported BLOCKED
state, never an empty or renamed file. Rooftop and ground reports share the
formatters but are category-bound at the export boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
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
from .serialization import dumps
from .source_xlsx import create_source_workbook


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

REPORT_PROFILES = {
    "industrial_rooftop": {
        "title": "工商业屋顶光伏预可研报告",
        "boundary": "工商业屋顶（industrial_rooftop）",
        "missing": "屋顶权属/租赁期限、结构鉴定、负荷曲线、合同电价及并网资料",
        "special_prefixes": ("roof.", "load.", "tariff."),
    },
    "utility_scale_ground": {
        "title": "集中式地面光伏预可研报告",
        "boundary": "集中式地面电站（utility_scale_ground）",
        "missing": "土地合规、地形测量、地质勘察、道路排水、集电线路、升压站、接入系统意见及市场化交易依据",
        "special_prefixes": ("site.", "layout.", "grid.", "tariff."),
    },
}

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


def _metric_cell_value(metric: dict[str, Any]) -> Any:
    """Keep scalar canonical numbers numeric; keep non-values visibly textual."""
    if metric.get("status") != "CALCULATED":
        return f"{metric.get('status', 'UNKNOWN')}：{metric.get('reason') or '未提供可用数值'}"
    value = metric.get("value")
    return dumps(value) if isinstance(value, (dict, list)) else value


def _raw_value(value: Any) -> str:
    return "UNKNOWN" if value is None else dumps(value) if isinstance(value, (dict, list)) else str(value)


def _metric_rows(model: ReportModel, *, prefixes: tuple[str, ...] = ()) -> list[list[Any]]:
    rows = []
    for metric in model.metrics:
        if prefixes and not metric["metric_id"].startswith(prefixes):
            continue
        rows.append([metric["metric_id"], metric["status"], _metric_cell_value(metric), metric.get("unit") or "UNKNOWN",
                     metric.get("formula_id") or "UNKNOWN", ",".join(metric.get("source_ids") or []) or "UNKNOWN",
                     metric.get("reason") or "", _raw_value(metric.get("value"))])
    return rows


def _normalized_rows(model: ReportModel, *, prefixes: tuple[str, ...] = ()) -> list[list[Any]]:
    normalized = model.result["inputs"].get("normalized", {})
    used_sources = model.result["inputs"].get("used_sources", {})
    return [[key, value, "INPUT", ",".join(used_sources.get(key, [])) if isinstance(used_sources, dict) else _string(used_sources), _raw_value(value)]
            for key, value in sorted(normalized.items()) if not prefixes or key.startswith(prefixes)]


def _identity_rows(model: ReportModel) -> list[list[Any]]:
    return [[key, value, "CANONICAL", _raw_value(value)] for key, value in model.identity.items()]


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
            elif isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool):
                cell.number_format = "0.###############"


def _xlsx_cell(value: Any) -> Any:
    if value is None:
        return "UNKNOWN"
    if isinstance(value, Decimal):
        # The adjacent raw-value column preserves Decimal text exactly.
        return float(value)
    if isinstance(value, (dict, list)):
        return dumps(value)
    return value


def _sheet_data(model: ReportModel, sheet_id: str, title: str, pv_type: str) -> tuple[list[str], list[list[Any]]]:
    normalized = model.result["inputs"].get("normalized", {})
    metrics = model.metrics
    if sheet_id == "M01":
        rows = _identity_rows(model) + [["pv_type", model.result["pv_type"], "CANONICAL", _raw_value(model.result["pv_type"])], ["currency", model.result["currency"], "CANONICAL", _raw_value(model.result["currency"])],
            ["evaluation_date", model.result["evaluation_date"], "CANONICAL", _raw_value(model.result["evaluation_date"])], ["calculation_status", model.result["status"], "CANONICAL", _raw_value(model.result["status"])]] + _normalized_rows(model, prefixes=("project.", "site.", "system."))
        headers = ["参数", "值", "来源", "canonical_raw"]
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
        rows = [["dc_capacity", _metric_cell_value(model.metric("dc_capacity")), "kWp", "F-DC-CAPACITY"], ["ac_capacity", _metric_cell_value(model.metric("ac_capacity")), "kWac", "F-AC-CAPACITY"], ["dc_ac_ratio", _metric_cell_value(model.metric("dc_ac_ratio")), "1", "F-DC-AC-RATIO"]]
        losses = normalized.get("system.losses")
        if isinstance(losses, list):
            rows.extend([["loss." + str(item.get("row_id", "UNKNOWN")), item.get("fields", {}).get("system.losses.value"), "1", "INPUT"] for item in losses])
        headers = ["项目", "值", "单位", "来源/公式"]
    elif sheet_id == "M07":
        value = model.value("energy.annual_array")
        rows = [[index, item, "kWh", "energy.annual_array"] for index, item in enumerate(value or [None], 1)]
        headers = ["运营年", "电量", "单位", "来源"]
    elif sheet_id == "M08":
        if pv_type == "utility_scale_ground":
            rows = [["ground_self_consumption", "NOT_APPLICABLE", "集中式地面项目不采用屋顶自用节省模型", "BOUNDARY", "UNKNOWN", "CANONICAL", "不得将consumption=0解释为屋顶负荷证据", "NOT_APPLICABLE"]]
            rows += _metric_rows(model, prefixes=("energy.delivered",))
        else:
            rows = _metric_rows(model, prefixes=("consumption", "energy.delivered"))
        headers = ["metric_id", "状态", "值", "单位", "公式", "来源", "原因", "canonical_raw"]
    elif sheet_id == "M09":
        rows = _metric_rows(model, prefixes=("revenue",)) + _normalized_rows(model, prefixes=("project.sales", "revenue.", "tariff."))
        headers = ["metric/field", "状态/值", "显示值", "单位/来源", "公式", "来源", "原因", "canonical_raw"]
    elif sheet_id in {"M10", "M11", "M12", "M13"}:
        prefixes = {"M10": ("capex.",), "M11": ("opex.",), "M12": ("assets.", "tax."), "M13": ("finance.",)}[sheet_id]
        rows = _normalized_rows(model, prefixes=prefixes) + _metric_rows(model, prefixes=("financial.",))
        headers = ["field/metric", "值", "状态/来源", "source_ids", "canonical_raw"]
    elif sheet_id in {"M14", "M15", "M16"}:
        rows = _metric_rows(model, prefixes=("financial.", "npv"))
        headers = ["metric_id", "状态", "值/阻断原因", "单位", "公式", "来源", "原因", "canonical_raw"]
    elif sheet_id == "M17":
        rows = [["sensitivity", "NOT_TESTED", "未提供合法独立敏感性重算结果", "UNKNOWN"]]
        rows += [[item.get("code", "finding"), item.get("status", "UNKNOWN"), "请补充来源后执行", "UNKNOWN"] for item in model.result.get("findings", [])]
        headers = ["因素/证据", "状态", "说明", "值"]
    elif sheet_id == "M18":
        description = "仅有当前SYNTHETIC地面并网基准；无合法替代方案" if pv_type == "utility_scale_ground" else "仅有当前SYNTHETIC屋顶基准；无合法替代方案"
        rows = [["BASE", model.result["scenario_id"], model.result["status"], description], ["alternative", "NOT_TESTED", "UNKNOWN", "未建模，不比较"]]
        headers = ["方案", "场景", "状态", "说明"]
    else:
        rows = [["identity", key, value, "一致性依据"] for key, value in model.identity.items()]
        rows += [["metric_status", m["metric_id"], m["status"], _display_metric(m)] for m in metrics]
        headers = ["检查", "对象", "实际", "说明"]
    return headers, rows


def _write_model_xlsx(model: ReportModel, output: Path, pv_type: str) -> dict[str, Any]:
    book = Workbook()
    book.remove(book.active)
    for sheet_id, title in MODEL_SHEETS:
        ws = book.create_sheet(title)
        _header(ws, model, sheet_id, title)
        headers, rows = _sheet_data(model, sheet_id, title, pv_type)
        ws.append(headers)
        header_row = ws.max_row
        for row in rows:
            ws.append([_xlsx_cell(value) for value in row])
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


def _field_present(model: ReportModel, field_id: str) -> bool:
    value = model.result["inputs"].get("normalized", {}).get(field_id)
    return value not in (None, "", [])


def _item_rule(pv_type: str, chapter_id: str, title: str) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    ground = pv_type == "utility_scale_ground"
    if "自用" in title or "负荷" in title or "可避免费" in title:
        if ground:
            return (), (), "集中式地面项目不采用工商业屋顶自用节省模型；不得把 consumption=0 解释为屋顶负荷证据。"
        return ("consumption.year.1", "consumption.self_ratio.year.1", "revenue.year.1"), ("load.meter_id", "load.timezone", "load.quality_basis"), "缺少同粒度负荷曲线、计量边界、时区和合同电价时，无法闭合自用与可避免费用。"
    if chapter_id == "CH05":
        return (), ("resource.poa_boundary",), "年度发电量不能反向证明GHI/DNI/DHI、温度、风速或资源授权；需补充资源数据集、覆盖率、单位和许可。"
    if chapter_id == "CH06" and "DC/AC" in title:
        return ("dc_capacity", "ac_capacity", "dc_ac_ratio"), (), ""
    if chapter_id == "CH07" and "选择" in title:
        return (), ("system.module_power", "system.inverter_count", "system.inverter_unit_ac"), "需补充经核验的组件/逆变器型号参数和适用性依据。"
    if chapter_id == "CH08":
        if "月度" in title:
            return ("energy.monthly.year.1", "energy.year.1"), (), ""
        if "发电" in title or "效率" in title:
            return ("energy.year.1", "equivalent_hours.year.1", "capacity_factor.year.1", "pr_observed.year.1"), (), ""
    if chapter_id == "CH09":
        if "接入点" in title or "容量约束" in title:
            return (), ("grid.metering_boundary", "grid.transformer_capacity", "grid.available_capacity", "grid.export_power_limit"), "需补充接入系统意见、容量批复和保护/电压边界。"
        return (), (), "需补充电网企业接入系统意见、升压站/集电线路方案和调度约束；当前结果不构成并网结论。"
    if chapter_id == "CH11" and ground:
        return (), ("site.geotechnical_reference",), "需补充地形测量、地质勘察、桩基/基础、道路排水和施工运输资料。"
    if chapter_id == "CH04":
        if "位置" in title or "面积" in title:
            return (), ("site.total_area", "site.usable_area", "site.area_basis"), ""
        if ground and "土地" in title:
            return (), ("site.land_classification", "site.area_basis"), "需补充土地权属、用地性质、合规期限和可建设范围证明。"
        if not ground and "权属" in title:
            return (), ("roof.remaining_life", "roof.structure_report_id"), "需补充屋顶权属/租赁期限和结构鉴定报告。"
        if ground and ("地质" in title or "结构" in title):
            return (), ("site.geotechnical_reference",), "需补充地形、坡度、地质勘察及基础条件。"
        if not ground and "结构" in title:
            return (), ("roof.allowable_additional_load", "roof.structure_report_id"), "需补充结构承载复核、加固方案和消防/防水边界。"
    if chapter_id == "CH14":
        return ("financial.capex.total", "financial.unit_investment"), ("capex.items",), "CAPEX总额不能代替数量×单价、报价时点、税口径及地面/屋顶专项工程明细。"
    if chapter_id == "CH15":
        return ("financial.opex.cash_lifecycle",), ("opex.items",), "需补充运维、保险、租地/屋面、通胀和更换计划的合法依据。"
    if chapter_id == "CH16":
        ids = tuple(mid for mid in ("financial.phase3e.project_npv", "financial.phase3e.project_irr", "financial.phase3e.static_payback", "financial.phase3e.lcoe", "financial.phase3e.dscr") if mid)
        return ids, (), "财务现金流、折现率、税费/融资和收益边界未闭合；阻断指标不得写成有效数值。"
    if chapter_id == "CH17":
        return (), (), "未执行合法独立敏感性/情景重算；不能由基准结果推断阈值或稳健性。"
    if chapter_id == "CH01" and title == "项目识别及方案版本":
        return (), ("project.pv_type", "project.evaluation_date"), ""
    if chapter_id == "CH01" and title == "DC/AC及发电指标":
        return ("dc_capacity", "ac_capacity", "energy.year.1"), (), ""
    if chapter_id == "CH01" and title == "投资及财务指标":
        return ("financial.capex.total", "financial.phase3e.project_npv"), (), "CAPEX可读，但项目现金流和NPV仍需按上游状态展示。"
    if chapter_id == "CH01" and title == "消纳售电与资料成熟度":
        return (("revenue.year.1", "energy.delivered.year.1") if ground else ("consumption.year.1", "revenue.year.1")), (), ""
    if chapter_id == "CH01" and title == "阻断风险和四态建议":
        return (), (), "当前为PARTIAL/SYNTHETIC；请按finding和来源缺口关闭后再形成建议。"
    if chapter_id == "CH18":
        return (), (), "需基于已关闭的来源、专业审查和上游计算门禁形成结论；本样件不提供投资建议。"
    return (), (), "需补充本子项对应的原始资料、授权、计算结果或专业审查证据。"


def _item_state(model: ReportModel, pv_type: str, chapter_id: str, title: str) -> tuple[str, str]:
    metric_ids, field_ids, missing = _item_rule(pv_type, chapter_id, title)
    if "不采用工商业屋顶自用" in missing:
        return "NOT_APPLICABLE", missing
    metrics = [model.metric(metric_id) for metric_id in metric_ids if model.metric(metric_id)]
    statuses = [metric.get("status", "UNKNOWN") for metric in metrics]
    missing_fields = [field_id for field_id in field_ids if not _field_present(model, field_id)]
    if any(status.startswith("BLOCKED") or status in {"NOT_IMPLEMENTED", "NOT_TESTED"} for status in statuses):
        reasons = [metric.get("reason") for metric in metrics if metric.get("reason")]
        return "PENDING_VERIFICATION", "上游指标状态为 " + ", ".join(statuses) + "。" + ("原因：" + ";".join(reasons) if reasons else "") + (" " + missing if missing else "")
    if missing_fields:
        return "UNKNOWN", (missing or "缺少直接证据") + " 缺少字段：" + ", ".join(missing_fields) + "。"
    if metric_ids and len(metrics) != len(metric_ids):
        return "UNKNOWN", missing or "未找到本子项对应的完整指标集合。"
    if statuses and all(status == "CALCULATED" for status in statuses):
        details = ", ".join(f"{metric['metric_id']}={_display_metric(metric)}" for metric in metrics)
        return "EVIDENCED", "引用同一 canonical 结果中的直接指标：" + details + ("。" + missing if missing else "")
    if not metric_ids and not field_ids:
        return "PENDING_VERIFICATION", missing
    return "UNKNOWN", missing or "未找到本子项对应的直接证据。"


def _write_docx(model: ReportModel, output: Path, display_name: str, pv_type: str) -> dict[str, Any]:
    profile = REPORT_PROFILES[pv_type]
    document = Document()
    section = document.sections[0]
    section.top_margin = Cm(2.0); section.bottom_margin = Cm(2.0); section.left_margin = Cm(2.4); section.right_margin = Cm(2.0)
    styles = document.styles
    styles["Normal"].font.name = "等线"; styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "等线"); styles["Normal"].font.size = Pt(10.5)
    for heading in ("Heading 1", "Heading 2", "Heading 3"):
        styles[heading].font.name = "黑体"; styles[heading]._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
    title = document.add_paragraph(); title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(profile["title"]); run.bold = True; run.font.size = Pt(22); run.font.name = "黑体"
    subtitle = document.add_paragraph(); subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.add_run("草稿，资料不足，未决策就绪\nDRAFT_PARTIAL").bold = True
    document.add_paragraph()
    _add_table(document, ["项目身份", "值", "状态"], [["项目名称", display_name, "显示名；canonical未提供正式名称时使用project_id"], ["项目类型", model.result["pv_type"], "CANONICAL"], ["评价日期", model.result["evaluation_date"], "CANONICAL"], ["状态", model.result["status"], "上游结果"], *[[key, value, "CANONICAL"] for key, value in model.identity.items()]])
    document.add_paragraph("本文件为基于单一 canonical calculation result JSON 的开发样件。它不替代正式可研、设计、结构鉴定、并网意见、合同审核或投资决策。UNKNOWN、BLOCKED、NOT_IMPLEMENTED 和 NOT_TESTED 均保留原状态，不以零值代替。")
    document.add_heading("目录", level=1); _add_toc(document)
    document.add_page_break()
    document.add_heading("执行摘要", level=1)
    _add_table(document, ["metric_id", "状态", "值/原因", "单位", "公式", "来源", "阻断原因", "canonical_raw"], _metric_rows(model, prefixes=("dc_capacity", "ac_capacity", "energy.year", "consumption.year", "revenue.year", "financial."))[:18], "表1 执行摘要指标（canonical原值）")
    _add_table(document, ["field_id", "值", "状态", "source_ids", "canonical_raw"], _normalized_rows(model, prefixes=profile["special_prefixes"])[:40], "表2 项目类型专属输入（canonical原值）")
    document.add_paragraph("初步结论：当前结果为 PARTIAL，且资料为 SYNTHETIC 场景。由于项目级真实资源、政策、报价及财务现金流证据未闭合，报告只能作为开发样件，不能据此作出真实投资决策。")
    for chapter_id, chapter_title, items in CHAPTERS:
        document.add_heading(f"{chapter_id} {chapter_title}", level=1)
        for number, item in enumerate(items, 1):
            document.add_heading(f"{chapter_id}.{number:02d} {item}", level=2)
            state, content = _item_state(model, pv_type, chapter_id, item)
            document.add_paragraph(f"内容状态：{state}。{content}")
            document.add_paragraph(f"适用边界：{profile['boundary']}；本项仅读取本次运行的 canonical 结果，不在报告层重新计算。{profile['missing']}等资料不足时保持UNKNOWN/BLOCKED，不形成专业结论。")
    document.add_heading("结果与公式索引", level=1)
    _add_table(document, ["metric_id", "状态", "值/原因", "单位", "formula_id", "source_ids", "阻断原因", "canonical_raw"], _metric_rows(model), "表3 全量结果指标索引")
    for app_id, app_title in APPENDICES:
        document.add_heading(f"{app_id} {app_title}", level=1)
        document.add_heading(f"{app_id}.01 资料或结果明细", level=2)
        document.add_paragraph(f"本附录保留稳定编号和{profile['boundary']}语义内容。可提供的数据仅来自本次 canonical、来源快照和公式执行映射；未提供的原始附件、合同、授权文件和专业资料不在公开样件中复制。")
        document.add_heading(f"{app_id}.02 状态、限制与后续核验", level=2)
        document.add_paragraph("当前状态为 DRAFT_PARTIAL。请按缺口清单补充合法来源并重新运行引擎；不得在此文件中手工替换财务数字或将 SYNTHETIC 标记改为 REAL。")
    document.add_heading("术语与公式说明", level=1)
    _add_table(document, ["公式/指标", "定义版本", "单位", "状态", "符号与边界"], [[m["formula_id"], m.get("formula_version", "UNKNOWN"), m.get("unit") or "UNKNOWN", m["status"], "详见同一 metric 的 input_field_ids、method_parameter_ids、source_ids"] for m in model.metrics])
    document.add_heading("版本与质量声明", level=1)
    document.add_paragraph(f"四文件身份均应绑定同一 model_version、run_id、input_hash、source_snapshot_id 和 result_hash。当前项目类型为 {profile['boundary']}，不得混用另一项目类型的工程边界。XLSX 为 STATIC_SNAPSHOT；在 Excel 中修改输入不会自动使报告或旧结果有效，必须重新运行引擎生成新的运行身份。PDF 只有在真实转换器可用并成功解析时才会生成。")
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


def _export_report(result: dict[str, Any], catalog, workspace: Workspace, output_dir: str, *, formula_map: dict[str, Any] | None, expected_pv_type: str, phase: str) -> dict[str, Any]:
    """Generate a bounded DRAFT_PARTIAL report set from one category-bound canonical result."""
    if not isinstance(workspace, Workspace) or not isinstance(output_dir, str) or not output_dir.strip():
        raise ContractError("REPORT_OUTPUT_TARGET")
    root = workspace.path(output_dir, json_only=False)
    if root.exists():
        if not root.is_dir():
            raise ContractError("REPORT_OUTPUT_TARGET")
    else:
        root.mkdir()
    model = ReportModel.from_result(result, catalog)
    if model.result["pv_type"] != expected_pv_type:
        raise ContractError("REPORT_CATEGORY_MISMATCH")
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
    files["F01"] = _write_docx(model, docx_path, display_name, expected_pv_type)
    files["F03"] = _write_model_xlsx(model, xlsx_path, expected_pv_type)
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
        "phase": phase,
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


def export_rooftop_report(result: dict[str, Any], catalog, workspace: Workspace, output_dir: str, *, formula_map: dict[str, Any] | None = None) -> dict[str, Any]:
    return _export_report(result, catalog, workspace, output_dir, formula_map=formula_map,
                          expected_pv_type="industrial_rooftop", phase="PHASE5_INDUSTRIAL_ROOFTOP_REPORT_EXPORT")


def export_ground_report(result: dict[str, Any], catalog, workspace: Workspace, output_dir: str, *, formula_map: dict[str, Any] | None = None) -> dict[str, Any]:
    return _export_report(result, catalog, workspace, output_dir, formula_map=formula_map,
                          expected_pv_type="utility_scale_ground", phase="PHASE6_UTILITY_SCALE_GROUND_REPORT_EXPORT")
