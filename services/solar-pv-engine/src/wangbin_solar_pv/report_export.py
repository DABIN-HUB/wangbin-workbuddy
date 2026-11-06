"""Unified Phase 5/6 solar-PV report exporter.

The exporter is deliberately a read-only presentation layer over one validated
canonical result. It never recalculates financial values. PDF output is produced
only by an installed DOCX renderer; a missing renderer is a reported BLOCKED
state, never an empty or renamed file. Rooftop and ground reports share the
formatters but are category-bound at the export boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
import calendar
from datetime import date
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Mm, Pt, RGBColor
from openpyxl.chart import LineChart, Reference
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from PIL import Image, ImageDraw, ImageFont

from .calculation.result_contract import validate_result
from .errors import ContractError
from .local_files import Workspace
from .report_narrative import guidance, validate_fixture
from .report_claims import APPENDIX_RULES, APPENDIX_TITLES, CHAPTER_FIELDS, CHAPTER_METRICS, RESOURCE_MONTHLY_UNITS, build_claim, category_fields, _dataset_rows, _source_value
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
        "boundary": "工商业屋顶项目",
        "missing": "屋顶权属/租赁期限、结构鉴定、负荷曲线、合同电价及并网资料",
        "special_prefixes": ("roof.", "load.", "tariff."),
    },
    "utility_scale_ground": {
        "title": "集中式地面光伏预可研报告",
        "boundary": "集中式地面电站",
        "missing": "土地合规、地形测量、地质勘察、道路排水、集电线路、升压站、接入系统意见及市场化交易依据",
        "special_prefixes": ("site.", "layout.", "grid.", "tariff."),
    },
}


def _cover_project_name(pv_type: str) -> str:
    """Keep internal run identifiers out of the reader-facing cover."""
    return {
        "industrial_rooftop": "工商业屋顶光伏项目（阶段性样件）",
        "utility_scale_ground": "集中式地面光伏项目（阶段性样件）",
    }[pv_type]


_WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}

# D: white space, charcoal text, one restrained champagne-gold accent. Keep this
# palette in the exporter rather than in the calculation layer: visual changes
# must not alter canonical values or their identity.
_D_STYLE = {
    "ink": "1F2937",
    "muted": "6B7280",
    "accent": "9A7B4F",
    "accent_light": "F4EEE7",
    "line": "D9E2EC",
    "surface": "F8FAFC",
    "white": "FFFFFF",
}

REPORT_CONTENT_VERSION = "phase7l-r2-v5"


@dataclass(frozen=True)
class ReportModel:
    result: dict[str, Any]
    metrics: tuple[dict[str, Any], ...]
    metric_by_id: dict[str, dict[str, Any]]
    catalog: Any | None = None

    @classmethod
    def from_result(cls, result: dict[str, Any], catalog) -> "ReportModel":
        validated = validate_result(result, catalog)
        metrics = tuple(validated["results"]["metrics"])
        return cls(validated, metrics, {m["metric_id"]: m for m in metrics}, catalog)

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


def _word_number(value: Any) -> str:
    """Format a canonical scalar for readable Word presentation only."""
    if isinstance(value, Decimal):
        value = float(value)
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        if not math.isfinite(value):
            return "UNKNOWN"
        if abs(value) >= 1000:
            text = f"{value:,.2f}"
        elif abs(value) >= 1:
            text = f"{value:.4f}"
        else:
            text = f"{value:.6f}"
        return text.rstrip("0").rstrip(".")
    return str(value)


def _word_value(value: Any) -> str:
    """Collapse arrays/objects instead of allowing raw canonical JSON into DOCX."""
    if value is None:
        return "UNKNOWN"
    if isinstance(value, (int, float, Decimal, bool)):
        return _word_number(value)
    if isinstance(value, list):
        if not value:
            return "序列（0项）"
        scalar = [item for item in value if isinstance(item, (int, float, Decimal)) and not isinstance(item, bool)]
        if len(scalar) == len(value):
            return f"序列（{len(value)}项；首值 {_word_number(value[0])}；末值 {_word_number(value[-1])}）"
        return f"序列（{len(value)}项；详细值见测算模型.xlsx）"
    if isinstance(value, dict):
        keys = list(value)[:3]
        suffix = "、".join(str(key) for key in keys)
        return f"对象（{len(value)}个字段；{suffix}{'…' if len(value) > 3 else ''}）"
    text = _reader_text(str(value))
    return text if len(text) <= 180 else text[:177].rstrip() + "…"

def _reader_text(text: str) -> str:
    """Translate display-only tokens; canonical and audit identities are untouched."""
    for source, label in (("GRID_DELIVERABLE", "电网可交付电量边界"),
                          ("Concept protection only; engineering review pending", "仅为概念性保护方案，待工程审查"),
                          ("FICTIONAL_NOT_APPROVED_METER_NODE", "仅用于合成测算的未审批计量点"),
                          ("AVAILABLE_PRE_CONSUMPTION", "消纳前可用电量口径"),
                          ("NOT_APPLICABLE", "不适用"),
                          ("ZERO_DEBT_SERVICE", "本期无应偿债务本息")):
        text = text.replace(source, label)
    text = re.sub(r"\bOPERATING_YEAR_(\d+)\b", lambda match: f"第{match.group(1)}年", text)
    return re.sub(r"\bpending\b", "待核验", text, flags=re.IGNORECASE)


def _word_metric_value(metric: dict[str, Any]) -> str:
    if metric.get("metric_id") == "financial.phase3e.project_irr":
        return _irr_presentation(metric)[0]
    if metric.get("status") != "CALCULATED":
        reason = str(metric.get("reason") or "未提供可用数值")
        return f"{metric.get('status', 'UNKNOWN')}：{reason[:180]}"
    return _word_value(metric.get("value"))

def _irr_presentation(metric: dict[str, Any]) -> tuple[str, str]:
    """Present the reported root set, not an arbitrarily chosen IRR."""
    details = metric.get("details") or {}
    domain = details.get("domain") or {}
    roots = details.get("roots")
    if (not isinstance(roots, list) or details.get("unexhausted") is not False
            or type(details.get("root_count")) is not int or details["root_count"] != len(roots)
            or not isinstance(domain, dict)
            or any(isinstance(domain.get(bound), bool) or not isinstance(domain.get(bound), (int, float, Decimal))
                   for bound in ("minimum", "maximum"))
            or any(isinstance(root, bool) or not isinstance(root, (int, float, Decimal)) for root in roots)):
        return "根集待核验", "根集、搜索域或穷尽状态未核实；不选取单个根"
    bounds = (f"搜索域{_word_number(Decimal(str(domain['minimum'])) * 100)}%至"
              f"{_word_number(Decimal(str(domain['maximum'])) * 100)}%内")
    status, reason = metric.get("status"), metric.get("reason")
    if status == "UNDEFINED" and reason == "NO_ROOT" and not roots:
        return "搜索域内无根", f"{bounds}无根，不表示整个实数域无根；IRR不等于0"
    if status == "UNDEFINED" and reason == "MULTIPLE_ROOTS" and len(roots) > 1 and metric.get("value") is None:
        values = [Decimal(str(root)) * 100 for root in roots]
        # Keep root indices even if their rounded percentage strings coincide.
        precision = next((digits for digits in range(2, 19)
                          if len({f"{value:.{digits}f}" for value in values}) == len(values)), None)
        labels = [f"根{index}≈{value:.{precision}f}%" if precision is not None
                  else f"根{index}≈{value}%" for index, value in enumerate(values, 1)]
        return "、".join(labels), f"多根；{bounds}存在{len(roots)}个已认证根；IRR非唯一，不与折现率择优比较"
    if (status == "CALCULATED" and len(roots) == 1
            and isinstance(metric.get("value"), (int, float, Decimal))
            and not isinstance(metric["value"], bool) and metric["value"] == roots[0]):
        return f"{Decimal(str(roots[0])) * 100:.2f}%", f"单根；{bounds}唯一已认证根；年度项目税后口径"
    return "根集待核验", "指标状态与所列根不一致；不选取单个根"


def _word_sources(source_ids: list[str] | tuple[str, ...], source_map: dict[str, str]) -> str:
    refs = [source_map.get(source, source) for source in source_ids]
    return "、".join(refs[:6]) + ("、…" if len(refs) > 6 else "") if refs else "无直接来源"


def _source_ref_map(model: ReportModel) -> dict[str, str]:
    source_ids = set()
    for metric in model.metrics:
        source_ids.update(metric.get("source_ids") or [])
    used_sources = model.result["inputs"].get("used_sources", {})
    if isinstance(used_sources, dict):
        for sources in used_sources.values():
            if isinstance(sources, list):
                source_ids.update(str(source) for source in sources)
    return {source: f"S{index:02d}" for index, source in enumerate(sorted(source_ids), 1)}


def _display_metric(metric: dict[str, Any]) -> str:
    if metric.get("metric_id") == "financial.phase3e.project_irr":
        display, note = _irr_presentation(metric)
        return f"{display}；{note}"
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
        irr = metric["metric_id"] == "financial.phase3e.project_irr"
        display, note = _irr_presentation(metric) if irr else (None, None)
        rows.append([metric["metric_id"], metric["status"], display if irr else _metric_cell_value(metric),
                     "%" if irr else _metric_unit(metric),
                     metric.get("formula_id") or "UNKNOWN", ",".join(metric.get("source_ids") or []) or "UNKNOWN",
                     f"{metric.get('reason') or ''}；{note}；认证根原值={dumps((metric.get('details') or {}).get('roots'))}" if irr else metric.get("reason") or "",
                     _raw_value(metric.get("value"))])
    return rows


def _metric_unit(metric: dict[str, Any]) -> str:
    # Frozen F-UNIT-INVESTMENT metadata says CNY, but its denominator is DC kWp.
    if metric.get("formula_id") == "F-UNIT-INVESTMENT" and metric.get("metric_id") == "financial.unit_investment":
        return "元/kWp"
    return metric.get("unit") or "UNKNOWN"


def _normalized_rows(model: ReportModel, *, prefixes: tuple[str, ...] = ()) -> list[list[Any]]:
    normalized = model.result["inputs"].get("normalized", {})
    used_sources = model.result["inputs"].get("used_sources", {})
    return [[key, value, "INPUT", ",".join(used_sources.get(key, [])) if isinstance(used_sources, dict) else _string(used_sources), _raw_value(value)]
            for key, value in sorted(normalized.items()) if not prefixes or key.startswith(prefixes)]


def _financial_input_rows(model: ReportModel, *, prefixes: tuple[str, ...]) -> list[list[Any]]:
    """Align Phase 2 inputs with the eight-column financial metric layout."""
    return [[field, status, value, "UNKNOWN", "INPUT", source or "UNKNOWN", "", raw]
            for field, value, status, source, raw in _normalized_rows(model, prefixes=prefixes)]


def _identity_rows(model: ReportModel) -> list[list[Any]]:
    return [[key, value, "CANONICAL", _raw_value(value)] for key, value in model.identity.items()]


def _canonical_chart_specs(model: ReportModel) -> list[dict[str, Any]]:
    """Return chartable series without deriving or filling any result data.

    A chart is legal only for a calculated canonical metric with a finite
    numeric array.  Missing, blocked, scalar, malformed, or untraceable
    metrics deliberately produce no chart instead of a zero-filled visual.
    """
    specs: list[dict[str, Any]] = []
    for metric_id, minimum_points, exact_points in (
        ("energy.monthly.year.1", 2, 12),
        ("energy.annual_array", 2, None),
    ):
        metric = model.metric(metric_id)
        values = metric.get("value") if metric and metric.get("status") == "CALCULATED" else None
        if (not metric or not isinstance(values, list) or len(values) < minimum_points
                or (exact_points is not None and len(values) != exact_points)
                or not metric.get("formula_id") or not metric.get("source_ids")):
            continue
        numeric: list[float] = []
        for value in values:
            if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
                break
            number = float(value)
            if not math.isfinite(number):
                break
            numeric.append(number)
        else:
            specs.append({
                "metric_id": metric_id,
                "title": "月度发电量变化" if metric_id.startswith("energy.monthly") else "逐年发电量变化",
                "values": numeric,
                "unit": metric.get("unit") or "UNKNOWN",
                "formula_id": metric["formula_id"],
                "source_ids": tuple(metric["source_ids"]),
            })
    return specs


def _chart_axis_geometry(values: list[float], *, top: int, bottom: int) -> tuple[list[tuple[float, int]], list[int]]:
    """Use one ascending numerical scale for tick labels and points."""
    low, high = min(values), max(values)
    padding = max(abs(low) * 0.05, 1.0) if low == high else (high - low) * 0.08
    low, high = low - padding, high + padding
    ticks = [(low + index * (high - low) / 4, int(bottom - index * (bottom - top) / 4))
             for index in range(5)]
    points = [int(bottom - (value - low) / (high - low) * (bottom - top)) for value in values]
    return ticks, points


def _chart_axis_labels(spec: dict[str, Any]) -> tuple[str, str, str]:
    monthly = spec["metric_id"] == "energy.monthly.year.1"
    title = spec.get("title", "发电量变化") + ("（首年）" if monthly else "（评价期）")
    return title, ("月份" if monthly else "运营年（第1年起）"), f"发电量（{spec.get('unit') or 'UNKNOWN'}）"


def _chart_png(spec: dict[str, Any]) -> BytesIO:
    """Render one canonical series as a small, dependency-local PNG."""
    width, height = 1200, 500
    image = Image.new("RGB", (width, height), f"#{_D_STYLE['white']}")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    title, x_label, y_label = _chart_axis_labels(spec)
    draw.text((72, 26), title, fill=f"#{_D_STYLE['ink']}", font=font)
    draw.text((86, 48), y_label, fill=f"#{_D_STYLE['muted']}", font=font)
    draw.text((width // 2, height - 30), x_label, fill=f"#{_D_STYLE['muted']}", font=font)
    left, top, right, bottom = 86, 62, width - 36, height - 68
    values = spec["values"]
    ticks, y_values = _chart_axis_geometry(values, top=top, bottom=bottom)
    for tick, y in ticks:
        draw.line((left, y, right, y), fill=f"#{_D_STYLE['line']}", width=1)
        draw.text((8, y - 7), f"{tick:,.0f}", fill=f"#{_D_STYLE['muted']}", font=font)
    draw.line((left, top, left, bottom), fill=f"#{_D_STYLE['ink']}", width=2)
    draw.line((left, bottom, right, bottom), fill=f"#{_D_STYLE['ink']}", width=2)
    step = (right - left) / max(1, len(values) - 1)
    points = []
    for index, y in enumerate(y_values):
        x = int(left + index * step)
        points.append((x, y))
        label = str(index + 1).zfill(2)
        draw.text((x - 5, bottom + 12), label, fill=f"#{_D_STYLE['muted']}", font=font)
    draw.line(points, fill=f"#{_D_STYLE['accent']}", width=4, joint="curve")
    for x, y in points:
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=f"#{_D_STYLE['accent']}")
    stream = BytesIO()
    image.save(stream, format="PNG", optimize=True)
    stream.seek(0)
    return stream


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
    ws.sheet_view.showGridLines = False
    ws.sheet_properties.tabColor = _D_STYLE["accent"]
    for cell in ws[1]:
        cell.font = Font(bold=True, color=_D_STYLE["white"], size=11)
        cell.fill = PatternFill("solid", fgColor=_D_STYLE["ink"])
    for cell in ws[header_row]:
        cell.font = Font(bold=True, color=_D_STYLE["ink"])
        cell.fill = PatternFill("solid", fgColor=_D_STYLE["accent_light"])
    ws.row_dimensions[1].height = 22
    ws.row_dimensions[header_row].height = 20
    for column in range(1, ws.max_column + 1):
        width = min(55, max(14, max((len(_string(ws.cell(row, column).value)) for row in range(1, min(ws.max_row, 40) + 1)), default=14) + 2))
        ws.column_dimensions[get_column_letter(column)].width = width
    for row_index, row in enumerate(ws.iter_rows(), 1):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            if row_index > header_row and row_index % 2 == 0:
                cell.fill = PatternFill("solid", fgColor=_D_STYLE["surface"])
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


def _embed_xlsx_chart(ws, spec: dict[str, Any], header_row: int, data_start: int, anchor: str) -> dict[str, Any]:
    """Embed an Excel-native chart over cells already populated from canonical data."""
    data_end = data_start + len(spec["values"]) - 1
    chart = LineChart()
    title, x_label, y_label = _chart_axis_labels(spec)
    chart.title = f"Canonical · {title}"
    chart.y_axis.title = y_label
    chart.x_axis.title = x_label
    chart.style = 13
    chart.height = 7.0
    chart.width = 15.5
    chart.legend = None
    chart.add_data(Reference(ws, min_col=2, min_row=header_row, max_row=data_end), titles_from_data=True)
    chart.set_categories(Reference(ws, min_col=1, min_row=data_start, max_row=data_end))
    series = chart.series[0]
    series.graphicalProperties.line.solidFill = _D_STYLE["accent"]
    series.graphicalProperties.line.width = 26000
    series.marker.symbol = "circle"
    series.marker.size = 5
    ws.add_chart(chart, anchor)
    return {"metric_id": spec["metric_id"], "points": len(spec["values"]), "sheet": ws.title,
            "source": "CANONICAL", "formula_id": spec["formula_id"], "source_ids": list(spec["source_ids"])}


def _formula_definitions(model: ReportModel) -> list[dict[str, Any]]:
    snapshot = model.result.get("formula_snapshot", {})
    referenced = {metric["formula_id"] for metric in model.metrics if metric.get("formula_id")}
    definitions = {}
    for group in ("engineering_definitions", "consumption_definitions", "financial_definitions"):
        for fid, definition in snapshot.get(group, {}).items():
            if fid in referenced and isinstance(definition, dict):
                definitions[fid] = definition
    missing = referenced - definitions.keys()
    if missing and model.catalog is not None:
        if snapshot.get("definition_hash") != model.catalog.definition_hash:
            raise ContractError("REPORT_FORMULA_DEFINITION_IDENTITY_MISMATCH")
        for fid in missing:
            if fid in model.catalog.formulas:
                definitions[fid] = model.catalog.formulas[fid]
    return [definitions[fid] for fid in sorted(definitions)]


# This is an editorial bilingual glossary, not a formula or a source of measured data.
_GLOSSARY = (
    ("光伏", "Photovoltaic", "PV", "利用光伏效应将太阳辐照转化为电能；装机不等于并网许可"),
    ("直流", "Direct Current", "DC", "组件输出的单向电流侧；峰值装机以 kWp 标示，不是交流输出"),
    ("交流", "Alternating Current", "AC", "逆变器输出的交变电流侧；额定容量以 kWac 标示"),
    ("资本性支出", "Capital Expenditure", "CAPEX", "形成或更新长期资产的资本支出；区分初始建设款与运营期更换款"),
    ("运营性支出", "Operating Expenditure", "OPEX", "运营中发生的费用；现金运维与非现金折旧分别核算"),
    ("净现值", "Net Present Value", "NPV", "按指定折现率折现各期项目净现金流后的合计；年度项目口径不等于逐笔日期口径"),
    ("内部收益率", "Internal Rate of Return", "IRR", "使指定现金流净现值为零的折现率根集；项目与投资者、税前与税后不混用"),
    ("平准化度电成本", "Levelized Cost of Energy", "LCOE", "折现成本与同边界折现可交付电量之比；终期现金边界未闭合时不计算"),
    ("可供偿债现金流", "Cash Flow Available for Debt Service", "CFADS", "在约定偿债口径下可用于支付本息的现金流；不是股东实收分红"),
    ("偿债覆盖倍数", "Debt Service Coverage Ratio", "DSCR", "可供偿债现金流与同期应偿本息之比；无债务时不适用"),
    ("阵列面辐照", "Plane-of-Array Irradiation", "POA", "入射到组件阵列平面的辐照量；单位面积资源不是发电电量"),
    ("系统性能比", "Performance Ratio", "PR", "实际发电与按阵列面辐照及标称容量推算的参照发电之比；须保持同一时段和系统边界"),
)

def _formula_index_lines(formula: dict[str, Any]) -> list[str]:
    """Flatten frozen notation into editable prose, once per formula."""
    lines: list[str] = []
    seen: set[tuple[str, str]] = set()
    def add(token: str, meaning: str) -> None:
        if (token, meaning) not in seen:
            seen.add((token, meaning))
            lines.append(f"{token}：{meaning}")
    for key, value in (formula.get("subscript_definition") or {}).items():
        add(key, value)
    for item in formula.get("set_and_range_definition") or []:
        if isinstance(item, dict):
            add(item.get("token", "范围"), item.get("definition", "未定义"))
        else:
            add("范围", str(item))
    superscripts = formula.get("superscript_definition")
    if isinstance(superscripts, dict):
        for key, value in superscripts.items():
            if key != "说明" or "无上下标" not in value:
                add(f"上标{key}", value)
    elif isinstance(superscripts, str) and superscripts:
        add("上标说明", superscripts)
    return lines


def _formula_contract_text(value: Any) -> str:
    """Render a frozen notation contract as prose, never as an object dump."""
    if isinstance(value, dict):
        text = "；".join(f"{key}：{meaning}" for key, meaning in value.items())
    elif isinstance(value, str):
        text = value
    else:
        raise ContractError("REPORT_FORMULA_NOTATION_TYPE")
    return (text.replace("every_symbol_definition", "本式完整符号表")
            .replace("set_and_range_definition", "本式下标与求和范围"))


def _formula_shared_contracts(definitions: list[dict[str, Any]]) -> tuple[list[tuple[str, str, int]], dict[tuple[str, str], int]]:
    """Deduplicate identical *notation* contracts; never merge per-formula symbols."""
    kinds = {"operator_definition": "运算符", "notation_contract": "记法与歧义",
             "unit_convention": "单位约定"}
    groups: list[tuple[str, str, int]] = []
    ids: dict[tuple[str, str], int] = {}
    for formula in definitions:
        for key, label in kinds.items():
            value = formula.get(key)
            if not value:
                continue
            text = _formula_contract_text(value)
            pair = (key, text)
            if pair not in ids:
                number = 1 + sum(group[0] == label for group in groups)
                ids[pair] = number
                groups.append((label, text, number))
    return groups, ids


def _formula_status(model: ReportModel, fid: str) -> str:
    metrics = [m for m in model.metrics if m.get("formula_id") == fid]
    if not metrics:
        return "仅作方法说明；本项目未引用或执行"
    calculated = sum(m.get("status") == "CALCULATED" for m in metrics)
    blocked = sum(str(m.get("status", "")).startswith("BLOCKED") for m in metrics)
    inapplicable = sum(m.get("status") == "NOT_APPLICABLE" for m in metrics)
    unimplemented = sum(m.get("status") == "NOT_IMPLEMENTED" for m in metrics)
    undefined = sum(m.get("status") == "UNDEFINED" for m in metrics)
    unknown = len(metrics) - calculated - blocked - inapplicable - unimplemented - undefined
    states = (("已计算", calculated), ("阻断", blocked), ("不适用", inapplicable),
              ("方法未实现", unimplemented), ("数学未定义", undefined), ("待核对", unknown))
    return "本次引用；" + "、".join(f"{name}{count}项" for name, count in states if count) + "。"


def _appendix_rows(model: ReportModel, app_id: str) -> tuple[list[str], list[list[Any]]]:
    definitions = _formula_definitions(model)
    if app_id == "APP11.01":
        return (["公式ID", "正式名称", "公式文本", "结果单位", "适用边界", "本次状态"],
                [[f["formula_id"], f.get("chinese_name", "未定义"),
                  f.get("text_equation") or f.get("latex") or "未提供公式文本",
                  f.get("unit") or "未定义", f.get("calculation_boundary") or "未定义",
                  _formula_status(model, f["formula_id"])] for f in definitions])
    if app_id == "APP11.02":
        return (["公式ID", "完整符号", "定义", "单位", "下标与求和范围"],
                [[f["formula_id"], s.get("symbol") or "未定义", s.get("definition_zh") or "未定义",
                  s.get("unit") or "未定义",
                  "；".join(_formula_index_lines(f)) if i == 0 else ""]
                 for f in definitions for i, s in enumerate(f.get("every_symbol_definition", ()))])
    if app_id == "APP12.01":
        return ["中文", "English", "缩写", "定义及适用边界"], [list(row) for row in _GLOSSARY]
    if app_id == "APP12.02":
        return ["单位/符号", "含义", "不得混用的边界"], [
            ["kWp", "直流峰值千瓦", "不等于 kWac"], ["kWac", "交流额定千瓦", "不等于 kWh"],
            ["kWh", "电量千瓦时", "不等于辐照量 kWh/㎡"], ["kWh/㎡", "单位面积辐照量", "不等于交付电量"],
            ["元/kWp", "每直流峰值千瓦单位投资", "不等于元/Wp或未说明边界的CNY"]]
    raise ValueError(app_id)


def _appendix_content(model: ReportModel, item_id: str) -> str:
    _headers, rows = _appendix_rows(model, item_id)
    if not rows:
        return "本次结果未绑定可列示的正式公式定义；不补造符号或英文全称。"
    return "；".join(" / ".join(map(str, row)) for row in rows[:3])


def _resource_rows(model: ReportModel) -> tuple[list[str], list[list[Any]]]:
    """Show source-bound monthly resource inputs, never generated electricity."""
    normalized = model.result["inputs"].get("normalized", {})
    units = {field.removeprefix("resource.monthly."): unit
             for field, unit in RESOURCE_MONTHLY_UNITS.items()
             if field not in {"resource.monthly.days", "resource.monthly.month", "resource.monthly.row_id"}}
    headers = ["月份", "GHI (kWh/㎡)", "DNI (kWh/㎡)", "DHI (kWh/㎡)",
               "POA (kWh/㎡)", "气温 (°C)", "风速 (m/s)", "覆盖率", "来源与使用边界"]
    records = model.result.get("source_snapshot", {}).get("phase2", {}).get("records", ())
    rows = []
    monthly = normalized.get("resource.monthly")
    parents = [record for record in records if record.get("field_id") == "resource.monthly"]
    source = parents[0] if len(parents) == 1 else None
    evaluation = model.result.get("evaluation_date")

    def active(atom: dict[str, Any] | None) -> bool:
        if not isinstance(atom, dict) or atom.get("status") not in {"ASSUMED", "VERIFIED"}:
            return False
        if (not atom.get("source_id") or not atom.get("source_url_or_attachment")
                or atom.get("license_status") != "AUTHORIZED"):
            return False
        try:
            today = date.fromisoformat(evaluation)
            return (not atom.get("effective_from") or date.fromisoformat(atom["effective_from"][:10]) <= today) and (
                not atom.get("effective_to") or date.fromisoformat(atom["effective_to"][:10]) >= today)
        except (TypeError, ValueError):
            return False

    def parent_bound(atom: dict[str, Any] | None) -> bool:
        return (active(atom) and atom["source_id"] == source["source_id"]
                and atom["source_url_or_attachment"] == source["source_url_or_attachment"]
                and atom.get("source_section_or_cell") == source.get("source_section_or_cell")
                and atom.get("source_kind") == source.get("source_kind"))

    flat = {}
    for record in records:
        instance = record.get("field_instance_id")
        if instance:
            flat.setdefault(instance, []).append(record)
    source_rows = {}
    nested_instances = {}
    if source and isinstance(source.get("value"), list):
        for row in source["value"]:
            if isinstance(row, dict):
                source_rows.setdefault(row.get("row_id"), []).append(row)
                for child in row.get("fields", {}).values():
                    if isinstance(child, dict) and child.get("field_instance_id"):
                        instance = child["field_instance_id"]
                        nested_instances[instance] = nested_instances.get(instance, 0) + 1
    period = {}
    for fid in ("resource.period_start", "resource.period_end"):
        matches = [record for record in records if record.get("field_id") == fid]
        if (len(matches) == 1 and source and parent_bound(matches[0])
                and matches[0].get("value") == normalized.get(fid)):
            try:
                period[fid] = date.fromisoformat(matches[0]["value"])
            except (TypeError, ValueError):
                pass
    start, end = period.get("resource.period_start"), period.get("resource.period_end")
    # The frozen monthly path consumes one complete local calendar year. A
    # month number without a sourced dataset and site time zone is ambiguous.
    metadata = {}
    for fid in ("resource.dataset_id", "resource.version", "site.timezone"):
        matches = [record for record in records if record.get("field_id") == fid]
        if (len(matches) == 1 and source and parent_bound(matches[0])
                and matches[0].get("field_instance_id") == fid and matches[0].get("unit") is None
                and matches[0].get("value") == normalized.get(fid)):
            metadata[fid] = matches[0]["value"]
    try:
        zone = ZoneInfo(metadata["site.timezone"])
    except (KeyError, TypeError, ValueError, ZoneInfoNotFoundError):
        zone = None
    calendar_bound = (start is not None and end is not None and
                      start == date(start.year, 1, 1) and end == date(start.year, 12, 31)
                      and zone is not None and bool(metadata.get("resource.dataset_id"))
                      and bool(metadata.get("resource.version")))
    months = {}
    row_ids = {}
    if isinstance(monthly, list):
        for item in monthly:
            if isinstance(item, dict):
                row_id = item.get("row_id")
                month = item.get("fields", {}).get("resource.monthly.month")
                row_ids[row_id] = row_ids.get(row_id, 0) + 1
                months[month] = months.get(month, 0) + 1

    if source and active(source) and isinstance(monthly, list):
        for item in monthly:
            fields = item.get("fields", {}) if isinstance(item, dict) else {}
            month = fields.get("resource.monthly.month")
            row_id = item.get("row_id") if isinstance(item, dict) else None
            if not isinstance(month, int) or isinstance(month, bool) or month < 1 or month > 12:
                continue
            matching_rows = source_rows.get(row_id, [])
            sourced = matching_rows[0].get("fields", {}) if len(matching_rows) == 1 else {}
            if not isinstance(sourced, dict):
                sourced = {}
            month_start = date(start.year, month, 1) if calendar_bound else None
            month_end = (date(start.year, month, calendar.monthrange(start.year, month)[1])
                         if month_start else None)

            def bound(fid: str, value: Any, unit: str | None) -> dict[str, Any] | None:
                atom = sourced.get(fid)
                if (not isinstance(atom, dict) or atom.get("field_id") != fid
                        or atom.get("value") != value or atom.get("unit") != unit
                        or not parent_bound(atom)
                        or atom.get("field_instance_id") != f"resource.monthly:{row_id}:{fid.removeprefix('resource.monthly.')}"):
                    return None
                matches = flat.get(atom["field_instance_id"], [])
                if (len(matches) != 1 or matches[0] != atom
                        or nested_instances.get(atom["field_instance_id"]) != 1):
                    return None
                return atom

            month_ok = (isinstance(row_id, str) and bool(row_id) and row_ids.get(row_id) == 1
                        and months.get(month) == 1 and month_start is not None
                        and start <= month_start <= month_end <= end
                        and fields.get("resource.monthly.row_id") == row_id
                        and bound("resource.monthly.month", month, None) is not None
                        and bound("resource.monthly.row_id", row_id, None) is not None)
            cells = []
            lineage = []
            for key, unit in units.items():
                fid = "resource.monthly." + key
                value = fields.get(fid)
                atom = bound(fid, value, unit) if month_ok and value is not None else None
                cells.append(value if atom else "UNKNOWN")
                if atom:
                    lineage.append(f"{fid}={atom['field_instance_id']}({atom['status']},{unit},{atom['source_id']})")
            identity = (f"数据集{metadata['resource.dataset_id']}（{metadata['resource.version']}）；"
                        f"本地时区{zone.key}；{month_start.isoformat()}—{month_end.isoformat()}；"
                        f"{source['source_id']}；{source['source_url_or_attachment']}"
                        if lineage else "UNKNOWN")
            note = (f"{identity}；row_id={row_id}；辐照为已提供月累计量，气温及风速为已提供月统计值；"
                    "Phase 2 资源输入，非D3实测或发电量"
                    + ("；" + "；".join(lineage) if lineage else "；行/字段来源未闭合"))
            rows.append([month, *cells, note])
        rows.sort(key=lambda row: row[0])
    if not rows:
        dataset = _dataset_rows(model.result).get("resource.timeseries")
        if dataset:
            rows.append(["未聚合", *(["UNKNOWN"] * 7),
                         f"D3时序{dataset['row_count']}条；未取得有来源的月度资源输入，不以月发电量代替"])
        else:
            rows.append(["UNKNOWN", *(["UNKNOWN"] * 7), "未提供有来源的月度资源输入；不可用月发电量代替"])
    return headers, rows


def _capex_boundary_rows(model: ReportModel) -> list[list[Any]]:
    ledger = model.result.get("evidence", {}).get("financial-ledger", {}).get("annual", ())
    if not isinstance(ledger, list) or not ledger:
        return [["initial_capex_cash_paid", "LEDGER_MISSING", "UNKNOWN", "CNY", "", "", "未提供建设期账簿", "UNKNOWN"]]
    construction = [row for row in ledger if row.get("period") == "CONSTRUCTION"]
    if not construction or any("capex_cash_paid" not in row for row in construction):
        return [["initial_capex_cash_paid", "LEDGER_MISSING", "UNKNOWN", "CNY", "", "", "建设期付款未闭合", "UNKNOWN"]]
    initial = sum(Decimal(str(row["capex_cash_paid"])) for row in construction)
    operating = [row for row in ledger if row.get("period", "").startswith("OPERATING_YEAR_")]
    rows = [["initial_capex_cash_paid", "LEDGER", initial, "CNY", "", "", "建设期现金付款（不含营运资金）", str(initial)]]
    if operating and all("capex_cash_paid" in row and "replacement_cash_paid" in row for row in operating):
        lifecycle = initial + sum(Decimal(str(row["capex_cash_paid"])) for row in operating)
        replacement = sum(Decimal(str(row["replacement_cash_paid"])) for row in operating)
        rows.append(["lifecycle_capex_cash_paid", "LEDGER", lifecycle, "CNY", "", "", "全部期间资本现金付款（含递延初始付款及更换）", str(lifecycle)])
        rows.append(["replacement_cash_paid", "LEDGER", replacement, "CNY", "", "", "运营期更换现金支出，已含在全期资本付款内", str(replacement)])
    else:
        rows.append(["lifecycle_capex_cash_paid", "LEDGER_INCOMPLETE", "UNKNOWN", "CNY", "", "", "更换付款序列未闭合", "UNKNOWN"])
    if all("working_capital_increase" in row for row in construction):
        capital = sum(Decimal(str(row["working_capital_increase"])) for row in construction)
        rows.append(["working_capital_increase", "LEDGER", capital, "CNY", "", "", "建设期营运资金单列", str(capital)])
    return rows


def _scenario_rows(model: ReportModel, kind: str) -> list[list[Any]]:
    receipts = model.result.get("evidence", {}).get("scenario_receipts", ())
    matched = [row for row in receipts if isinstance(row, dict)
               and row.get("baseline_result_hash") == model.result["result_hash"]
               and row.get("result_hash") and row.get("scenario_id")
               and row.get("run_id") and row.get("kind") == kind] if isinstance(receipts, list) else []
    if not matched:
        return [[kind, "NOT_TESTED", "当前canonical没有绑定基准结果哈希的独立情景回执；不推断情景结果", "UNKNOWN"]]
    return [[row["scenario_id"], row.get("status") or "UNKNOWN", row["run_id"], row["result_hash"]]
            for row in matched]


def _sheet_data(model: ReportModel, sheet_id: str, title: str, pv_type: str) -> tuple[list[str], list[list[Any]]]:
    normalized = model.result["inputs"].get("normalized", {})
    metrics = model.metrics
    if sheet_id == "M01":
        rows = _identity_rows(model) + [["pv_type", model.result["pv_type"], "CANONICAL", _raw_value(model.result["pv_type"])], ["currency", model.result["currency"], "CANONICAL", _raw_value(model.result["currency"])],
            ["evaluation_date", model.result["evaluation_date"], "CANONICAL", _raw_value(model.result["evaluation_date"])], ["calculation_status", model.result["status"], "CANONICAL", _raw_value(model.result["status"])]]
        rows += [[field, value, source or "UNKNOWN", raw]
                 for field, value, _status, source, raw in _normalized_rows(model, prefixes=("project.", "site.", "system."))]
        headers = ["参数", "值", "来源", "canonical_raw"]
    elif sheet_id == "M02":
        rows = [[f["formula_id"], f.get("chinese_name") or "UNKNOWN",
                 f.get("text_equation") or f.get("latex") or "未提供公式文本",
                 f.get("unit") or "UNKNOWN", f.get("calculation_boundary") or "UNKNOWN",
                 "；".join(f"{s.get('symbol')}: {s.get('definition_zh')} ({s.get('unit')})"
                           for s in f.get("every_symbol_definition", ())) or "未提供逐符号定义"]
                for f in _formula_definitions(model)]
        headers = ["formula_id", "正式名称", "公式文本", "单位", "适用边界", "逐符号定义"]
    elif sheet_id == "M03":
        rows = [["maturity.calculation", model.result["maturity"]["calculation"], "CANONICAL"], ["maturity.real_project", model.result["maturity"]["real_project"], "CANONICAL"], ["maturity.four_files", "DRAFT_PARTIAL", "EXPORTER"]]
        rows += [[m["metric_id"], m["status"], m.get("reason") or "", ",".join(m.get("source_ids") or []) or "UNKNOWN"] for m in metrics]
        rows += [["finding", item.get("code", "UNKNOWN"), item.get("status", "UNKNOWN"), "需保留并人工关闭"] for item in model.result.get("findings", [])]
        headers = ["质量轴/指标", "状态/值", "原因", "来源/说明"]
    elif sheet_id == "M04":
        headers, rows = _resource_rows(model)
    elif sheet_id == "M06":
        metric = model.metric("energy.monthly.year.1")
        values = metric.get("value") if metric and metric.get("status") == "CALCULATED" and isinstance(metric.get("value"), list) else None
        rows = [[index, value, "energy.monthly.year.1", "kWh", metric.get("status")]
                for index, value in enumerate(values, 1)] if values is not None else [
                    ["UNKNOWN", "UNKNOWN", "energy.monthly.year.1", "kWh", metric.get("status") if metric else "UNKNOWN"]]
        headers = ["月份", "发电量", "formula/metric", "单位", "状态"]
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
        rows = _metric_rows(model, prefixes=("revenue",)) + _financial_input_rows(model, prefixes=("project.sales", "revenue.", "tariff."))
        headers = ["metric/field", "状态", "值", "单位", "公式", "来源", "原因", "canonical_raw"]
    elif sheet_id in {"M10", "M11", "M12", "M13"}:
        prefixes = {"M10": ("capex.",), "M11": ("opex.",), "M12": ("assets.", "tax."), "M13": ("finance.",)}[sheet_id]
        rows = _financial_input_rows(model, prefixes=prefixes)
        if sheet_id == "M10":
            rows += _capex_boundary_rows(model) + _metric_rows(model, prefixes=("financial.capex.", "financial.unit_investment"))
        else:
            financial_prefix = {"M11": ("financial.opex.",), "M12": ("financial.asset.", "financial.tax."),
                                "M13": ("financial.debt.", "financial.phase3e.cfads", "financial.phase3e.dscr")}[sheet_id]
            rows += _metric_rows(model, prefixes=financial_prefix)
        headers = ["field/metric", "状态", "值", "单位", "公式", "来源", "边界/原因", "canonical_raw"]
    elif sheet_id == "M14":
        rows = _metric_rows(model, prefixes=("financial.phase3e.project_cash_flow", "financial.phase3e.project_pretax_cash_flow",
                                             "financial.phase3e.cumulative_cash_flow", "financial.phase3e.discounted_cumulative_cash"))
        headers = ["metric_id", "状态", "值/阻断原因", "单位", "公式", "来源", "原因", "canonical_raw"]
    elif sheet_id == "M15":
        rows = _metric_rows(model, prefixes=("financial.phase3e.equity-investor-cash-flow",
                                             "financial.phase3e.equity-available-cash-flow"))
        headers = ["metric_id", "状态", "值/阻断原因", "单位", "公式", "来源", "原因", "canonical_raw"]
    elif sheet_id == "M16":
        rows = [row for row in _metric_rows(model, prefixes=("financial.phase3e.",))
                if not any(term in row[0] for term in ("cash_flow", "cash-flow", "cumulative", "cash-funding", "cfads", "equity-available"))]
        headers = ["metric_id", "状态", "值/阻断原因", "单位", "公式", "来源", "原因", "canonical_raw"]
    elif sheet_id == "M17":
        rows = _scenario_rows(model, "SENSITIVITY")
        headers = ["因素/场景", "状态", "运行ID/说明", "结果哈希/值"]
    elif sheet_id == "M18":
        rows = [["BASE", model.result["scenario_id"], model.result["status"], model.result["result_hash"]]]
        rows += _scenario_rows(model, "ALTERNATIVE")
        headers = ["方案", "场景/状态", "状态/运行ID", "说明/结果哈希"]
    else:
        rows = [["identity", key, value, "一致性依据"] for key, value in model.identity.items()]
        rows += [["metric_status", m["metric_id"], m["status"], _display_metric(m)] for m in metrics]
        headers = ["检查", "对象", "实际", "说明"]
    return headers, rows


def _write_model_xlsx(model: ReportModel, output: Path, pv_type: str) -> dict[str, Any]:
    book = Workbook()
    book.remove(book.active)
    specs = {spec["metric_id"]: spec for spec in _canonical_chart_specs(model)}
    charts: list[dict[str, Any]] = []
    for sheet_id, title in MODEL_SHEETS:
        ws = book.create_sheet(title)
        _header(ws, model, sheet_id, title)
        headers, rows = _sheet_data(model, sheet_id, title, pv_type)
        ws.append(headers)
        header_row = ws.max_row
        for row in rows:
            ws.append([_xlsx_cell(value) for value in row])
        _style_sheet(ws, header_row)
        if sheet_id == "M06" and "energy.monthly.year.1" in specs:
            charts.append(_embed_xlsx_chart(ws, specs["energy.monthly.year.1"], header_row, header_row + 1, "F2"))
        elif sheet_id == "M07" and "energy.annual_array" in specs:
            charts.append(_embed_xlsx_chart(ws, specs["energy.annual_array"], header_row, header_row + 1, "F2"))
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
    return {"path": output.name, "size": output.stat().st_size, "sha256": _sha256(output),
            "sheets": [name for _, name in MODEL_SHEETS], "mode": "STATIC_SNAPSHOT", "charts": charts}


def _set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def _add_table(document: Document, headers: list[str], rows: list[list[Any]], caption: str | None = None,
               *, widths_cm: tuple[float, ...] | None = None, font_size: float = 8.5) -> None:
    if caption:
        paragraph = document.add_paragraph(caption)
        paragraph.style = "Caption"
        for run in paragraph.runs:
            run.font.color.rgb = RGBColor.from_string(_D_STYLE["muted"])
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    layout = tbl_pr.first_child_found_in("w:tblLayout")
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tbl_pr.append(layout)
    layout.set(qn("w:type"), "fixed")
    if widths_cm:
        for column, width in enumerate(widths_cm):
            for cell in table.columns[column].cells:
                cell.width = Cm(width)
    tbl_width = sum(widths_cm) if widths_cm else 0
    if tbl_width:
        tbl_w = tbl_pr.first_child_found_in("w:tblW")
        if tbl_w is None:
            tbl_w = OxmlElement("w:tblW")
            tbl_pr.insert(0, tbl_w)
        tbl_w.set(qn("w:w"), str(int(tbl_width * 567)))
        tbl_w.set(qn("w:type"), "dxa")
    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        cell.text = _string(header)
        _set_cell_shading(cell, _D_STYLE["ink"])
        cell_pr = cell._tc.get_or_add_tcPr()
        margins = cell_pr.first_child_found_in("w:tcMar")
        if margins is None:
            margins = OxmlElement("w:tcMar")
            cell_pr.append(margins)
        for side in ("top", "start", "bottom", "end"):
            margin = OxmlElement(f"w:{side}")
            margin.set(qn("w:w"), "72")
            margin.set(qn("w:type"), "dxa")
            margins.append(margin)
        for run in cell.paragraphs[0].runs:
            run.font.bold = True
            run.font.color.rgb = RGBColor.from_string(_D_STYLE["white"])
            run.font.size = Pt(font_size)
    header_pr = table.rows[0]._tr.get_or_add_trPr()
    header_pr.append(OxmlElement("w:tblHeader"))
    for row_index, row in enumerate(rows, 1):
        cells = table.add_row().cells
        for index, value in enumerate(row):
            cells[index].text = _string(value)
            cells[index].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
            cell_pr = cells[index]._tc.get_or_add_tcPr()
            margins = cell_pr.first_child_found_in("w:tcMar")
            if margins is None:
                margins = OxmlElement("w:tcMar")
                cell_pr.append(margins)
            for side in ("top", "start", "bottom", "end"):
                margin = OxmlElement(f"w:{side}")
                margin.set(qn("w:w"), "72")
                margin.set(qn("w:type"), "dxa")
                margins.append(margin)
            if row_index % 2 == 0:
                _set_cell_shading(cells[index], _D_STYLE["surface"])
            for run in cells[index].paragraphs[0].runs:
                run.font.color.rgb = RGBColor.from_string(_D_STYLE["ink"])
                run.font.size = Pt(font_size)
            if widths_cm and index < len(widths_cm):
                cells[index].width = Cm(widths_cm[index])
        tr_pr = cells[0]._tc.getparent().get_or_add_trPr()
        tr_pr.append(OxmlElement("w:cantSplit"))



def _add_canonical_charts(document: Document, specs: list[dict[str, Any]], source_map: dict[str, str],
                          heading: str | None = None) -> list[dict[str, Any]]:
    """Embed visual evidence only when canonical chart specs are valid."""
    if not specs:
        return []
    if heading:
        document.add_heading(heading, level=2)
    receipts = []
    for spec in specs:
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.add_run().add_picture(_chart_png(spec), width=Cm(16.4))
        document.add_paragraph(
            f"图示反映{spec.get('title', '本次发电量测算')}。数据来自当前合成测算的已计算序列，"
            f"资料引用 {_word_sources(spec['source_ids'], source_map)}；完整计算绑定见测算模型和资料来源清单。"
        )
        receipts.append({"metric_id": spec["metric_id"], "points": len(spec["values"]),
                         "source": "CANONICAL", "formula_id": spec["formula_id"],
                         "source_ids": list(spec["source_ids"]), "format": "PNG_EMBEDDED"})
    return receipts


def _add_toc(document: Document) -> None:
    """Cache a readable outline inside a real TOC field; no invented pages."""
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_after = Pt(6)
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin"); begin.set(qn("w:dirty"), "true")
    instruction = OxmlElement("w:instrText"); instruction.set(qn("xml:space"), "preserve"); instruction.text = 'TOC \\o "1-3" \\h \\z \\u'
    separate = OxmlElement("w:fldChar"); separate.set(qn("w:fldCharType"), "separate")
    run._r.extend((begin, instruction, separate))
    document.add_paragraph("章节索引（页码待 Word/渲染器刷新）")
    for chapter_id, chapter_title, _items in CHAPTERS:
        document.add_paragraph(f"{chapter_id} {chapter_title}")
    for app_id, app_title in APPENDICES:
        document.add_paragraph(f"{app_id} {app_title}")
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    document.paragraphs[-1].add_run()._r.append(end)
    settings = document.settings._element
    update = settings.find(qn("w:updateFields"))
    if update is None:
        update = OxmlElement("w:updateFields")
        settings.append(update)
    update.set(qn("w:val"), "true")


def _paragraph_signature(text: str) -> str:
    """Normalize paragraph text for duplicate-template diagnostics."""
    text = re.sub(r"\s+", "", text)
    text = re.sub(r"CH\d{2}(?:\.\d{2})?", "", text)
    text = re.sub(r"APP\d{2}(?:\.\d{2})?", "", text)
    # Preserve quoted subject names: they carry the chapter-specific meaning that
    # distinguishes legitimate evidence limitations from a copied template.
    text = re.sub(r"S\d{2}", "来源", text)
    text = re.sub(r"\d+(?:\.\d+)?", "数值", text)
    return text


def _validate_checklist_coverage(checklist: list[dict[str, Any]]) -> dict[str, int]:
    """Validate the frozen chapter/appendix ID coverage against generated records."""
    expected = {f"{chapter_id}.{number:02d}"
                for chapter_id, _title, items in CHAPTERS
                for number, _item in enumerate(items, 1)}
    expected.update({f"{app_id}.{number:02d}"
                     for app_id, _title in APPENDICES
                     for number in (1, 2)})
    actual = [str(record.get("id", "")) for record in checklist]
    actual_set = set(actual)
    if len(actual) != len(actual_set) or actual_set != expected:
        missing = sorted(expected - actual_set)
        unexpected = sorted(actual_set - expected)
        raise ContractError(f"REPORT_CHECKLIST_COVERAGE:{missing[:5]}:{unexpected[:5]}")
    return {
        "chapters": len(CHAPTERS),
        "chapter_items": sum(len(items) for _chapter_id, _title, items in CHAPTERS),
        "appendices": len(APPENDICES),
        "appendix_items": len(APPENDICES) * 2,
    }


def _bound_report_input(normalized: dict[str, Any], provenance: list[dict[str, Any]], fid: str) -> Any:
    """Recheck a cited scalar or repeated child against its Phase 2 source atom."""
    return _source_value(normalized, provenance, fid)


def _claim_binding_error(model: ReportModel, record: dict[str, Any]) -> bool:
    """Check cited IDs against this canonical result, never editorial background."""
    if record["canonical_result_hash"] != model.result["result_hash"]:
        return True
    normalized = model.result["inputs"].get("normalized", {})
    provenance = model.result.get("source_snapshot", {}).get("phase2", {}).get("records", ())
    datasets = _dataset_rows(model.result)
    known_sources = ({row["source_id"] for row in provenance if row.get("source_id")}
                     | {row["header"]["source_id"] for row in datasets.values()
                        if row.get("header", {}).get("source_id")})
    known_instances = ({row.get("field_instance_id") for row in provenance}
                       | {row["header"].get("field_instance_id") for row in datasets.values()})
    metric_ids = set(record["metric_ids"])
    for metric_id in record["supporting_metric_ids"]:
        metric = model.metric(metric_id)
        if metric_id not in metric_ids or metric is None or metric.get("status") != "CALCULATED":
            return True
    if not set(record["supporting_input_field_ids"]).issubset(record["input_field_ids"]):
        return True
    if any(_bound_report_input(normalized, provenance, fid) in (None, "", [], {}) and fid not in datasets
           for fid in record["supporting_input_field_ids"]):
        return True
    if not set(record["field_instance_ids"]).issubset(known_instances):
        return True
    metric_sources = {source for metric_id in metric_ids if (metric := model.metric(metric_id))
                      for source in (metric.get("source_ids") or ())}
    if not set(record["source_ids"]).issubset(known_sources | metric_sources):
        return True
    formulas = {model.metric(mid).get("formula_id") for mid in record["supporting_metric_ids"]}
    return not set(record["supporting_formula_ids"]).issubset(formulas)


def _scan_duplicate_paragraphs(document: Document, checklist: list[dict[str, Any]]) -> dict[str, Any]:
    """Scan generated body paragraphs rather than trusting template metadata."""
    current_heading = "未标记章节"
    paragraphs = []
    for index, paragraph in enumerate(document.paragraphs):
        text = paragraph.text.strip()
        if paragraph.style and paragraph.style.name.startswith("Heading"):
            current_heading = text
        if len(text) >= 40:
            paragraphs.append((index, text, current_heading))
    exact: dict[str, list[int]] = {}
    approximate: dict[str, list[int]] = {}
    context: dict[int, str] = {}
    for index, text, heading in paragraphs:
        exact.setdefault(text, []).append(index)
        approximate.setdefault(_paragraph_signature(text), []).append(index)
        context[index] = heading
    exact_findings = [{"paragraph_indexes": indexes, "count": len(indexes), "text": text[:240]}
                      for text, indexes in exact.items() if len(indexes) > 1]
    approximate_findings = [{"paragraph_indexes": indexes, "count": len(indexes), "signature": signature[:240]}
                            for signature, indexes in approximate.items() if len(indexes) > 2]
    for finding in exact_findings + approximate_findings:
        finding["headings"] = sorted({context[index] for index in finding["paragraph_indexes"]})
    exact_texts = {item["text"] for item in exact_findings}
    approximate_signatures = {item["signature"] for item in approximate_findings}
    for record in checklist:
        content = str(record.get("content_summary") or "")
        record["summary_length"] = len(content)
        record["duplicate_template"] = content[:240] in exact_texts or _paragraph_signature(content)[:240] in approximate_signatures
        record["duplicate_group"] = None
        if content[:240] in exact_texts:
            record["duplicate_group"] = "exact-paragraph"
        elif _paragraph_signature(content)[:240] in approximate_signatures:
            record["duplicate_group"] = "approximate-template"
    return {
        "paragraph_count_scanned": len(paragraphs),
        "exact_duplicate_count": len(exact_findings),
        "approximate_template_count": len(approximate_findings),
        "exact_duplicates": exact_findings[:20],
        "approximate_templates": approximate_findings[:20],
        "status": "PASS" if not exact_findings and not approximate_findings else "REVIEW_REQUIRED",
    }


def _chapter_intro(chapter_id: str, chapter_title: str) -> str:
    intros = {
        "CH01": "本章先行归纳项目规模、发电和投资信息，并说明当前阶段能够支持的判断范围。",
        "CH02": "本章说明研究目的、编制依据、评价口径和资料基础，明确哪些内容仍待核实。",
        "CH03": "本章从建设对象、实施主体、用能关系和建设需求出发，说明项目必要性判断的依据和限制。",
        "CH04": "本章分别考察屋顶或地面场址的物理边界、权属、安全和施工条件。",
        "CH05": "本章关注资源数据的来源、覆盖范围、气象变量和预测不确定性。",
        "CH06": "本章说明工程任务、容量配置、组件排列及方案比选的适用边界。",
        "CH07": "本章将设备参数、阵列布置、系统连接和损失因素转写为初步工程方案。",
        "CH08": "本章呈现月度及年度发电预测、效率指标、衰减和结果限制。",
        "CH09": "本章分析接入点、电气设备、送出条件和需要电网确认的事项。",
        "CH10": "本章按项目类型说明负荷消纳或集中并网、结算和售电条件。",
        "CH11": "本章说明总平面、基础、结构、道路排水和施工组织所需的工程条件。",
        "CH12": "本章梳理环境、生态、消防、施工运行安全及社会影响的资料边界。",
        "CH13": "本章按照前置条件和依赖关系说明实施组织、采购施工和后续里程碑。",
        "CH14": "本章说明投资估算的费用边界、构成、计价依据和需要复核的事项。",
        "CH15": "本章区分运营现金费用、折旧、更换和税费，说明长期成本的资料基础。",
        "CH16": "本章先说明财务评价口径，再区分已有测算和暂不具备评价条件的指标。",
        "CH17": "本章识别影响项目推进的风险，并区分已执行的分析与尚待重算的情景。",
        "CH18": "本章综合各专业边界形成阶段性结论，并提出下一阶段应完成的工作。",
    }
    return intros.get(chapter_id, f"本章说明{chapter_title}的研究范围、阶段性结果和后续工作要求。")


def _scan_professional_language(document: Document, pv_type: str, checklist: list[dict[str, Any]]) -> dict[str, Any]:
    """Detect residual audit-template prose in the generated body."""
    body = "\n".join(paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip())
    legacy_patterns = {
        "分析重点标签": r"分析重点（CH\d+",
        "已知证据标签": r"已知证据（",
        "判定标签": r"判定（CH\d+",
        "状态依据标签": r"状态依据（CH\d+",
        "canonical执行说明": r"仅读取\s*canonical",
        "本项围绕模板": r"本项围绕",
        "模板化缺口": r"需补充本子项对应的原始资料",
    }
    programming_patterns = {
        "运行状态标识": r"(?<![A-Za-z0-9_-])(?:DRAFT_PARTIAL|BLOCKED_MISSING_INPUT|SYNTHETIC|STATIC_SNAPSHOT)(?![A-Za-z0-9_-])",
        "内部字段标识": r"\b(?:formula_id|source_ids|canonical_raw|method_parameter_ids|metric_id|field_id)\b",
    }
    legacy_counts = {name: len(re.findall(pattern, body)) for name, pattern in legacy_patterns.items()}
    programming_counts = {name: len(re.findall(pattern, body)) for name, pattern in programming_patterns.items()}
    professional_markers = sum(body.count(marker) for marker in ("本阶段", "下一阶段", "尚未取得", "不能", "建议", "依据"))
    category_markers = ("屋顶", "自发自用") if pv_type == "industrial_rooftop" else ("集中并网", "交易电价")
    category_specific = all(marker in body for marker in category_markers)
    claim_statuses = {record.get("claim_status") for record in checklist}
    evidence_grounded = claim_statuses.issubset({"EVIDENCE_BOUND_CONDITIONAL", "LIMITED_BY_MISSING_EVIDENCE", "NOT_APPLICABLE", "TRACEABILITY_ONLY"})
    return {
        "body_paragraphs": len([p for p in document.paragraphs if p.text.strip()]),
        "legacy_template_counts": legacy_counts,
        "programming_language_counts": programming_counts,
        "professional_marker_count": professional_markers,
        "category_specific": "STATIC_MARKER_PRESENT" if category_specific else "REVIEW_REQUIRED",
        "evidence_grounded": "CONTENT_REVIEW_REQUIRED" if evidence_grounded else "REVIEW_REQUIRED",
        "professional_narrative": "CONTENT_REVIEW_REQUIRED",
        "no_generic_template_abuse": "CONTENT_REVIEW_REQUIRED",
        "no_programming_language_in_body": "STATIC_SCAN_CLEAR" if not any(programming_counts.values()) else "REVIEW_REQUIRED",
    }


def _word_evidence_lines(evidence: dict[str, Any], source_map: dict[str, str], item_id: str) -> list[str]:
    lines = []
    for row in evidence["rows"][:4]:
        value = row.get("value", "UNKNOWN")
        lines.append(f"{item_id} / {row.get('id', 'UNKNOWN')}：{_word_value(value)} {row.get('unit', 'UNKNOWN')}（{row.get('status', 'UNKNOWN')}）")
    if evidence.get("source_ids"):
        lines.append(f"资料：{_word_sources(evidence['source_ids'], source_map)}（完整 ID 见资料来源与假设清单.xlsx）")
    return lines


def _add_professional_narrative(document: Document, evidence: dict[str, Any]) -> None:
    """Write consulting prose; audit identifiers remain in the checklist/XLSX."""
    for text in evidence.get("narrative", ()):
        paragraph = document.add_paragraph(_reader_text(text))
        paragraph.paragraph_format.keep_together = True


def _word_metric_rows(model: ReportModel, source_map: dict[str, str], prefixes: tuple[str, ...] = ()) -> list[list[str]]:
    rows = []
    for metric in model.metrics:
        if prefixes and not metric["metric_id"].startswith(prefixes):
            continue
        rows.append([metric["metric_id"], _word_metric_value(metric), _metric_unit(metric),
                     metric.get("status", "UNKNOWN"), metric.get("formula_id") or "UNKNOWN",
                     _word_sources(metric.get("source_ids") or [], source_map)])
    return rows


_METRIC_LABELS = {
    "dc_capacity": "直流侧装机容量",
    "ac_capacity": "交流侧额定容量",
    "dc_ac_ratio": "直交流容配比",
    "energy.year.1": "首年发电量",
    "available_kwh.year.1": "首年可利用发电量",
    "energy.mean_annual": "评价期年均发电量",
    "energy.delivered.year.1": "首年可交付电量",
    "financial.capex.total": "评价期资本支出估算（含更换，须按账簿复核）",
    "financial.unit_investment": "评价期CAPEX单位直流投资",
    "financial.opex.cash_lifecycle": "全周期现金运营费用",
    "financial.phase3e.project_npv": "项目净现值",
    "financial.phase3e.project_irr": "项目内部收益率",
    "financial.phase3e.project_cash_flow": "项目投资全期现金流",
    "financial.phase3e.equity-investor-cash-flow": "资本金投资者全期现金流",
    "financial.phase3e.static_payback": "静态投资回收期",
    "financial.phase3e.dynamic_payback": "动态投资回收期",
    "financial.phase3e.lcoe": "平准化度电成本",
    "financial.phase3e.dscr": "债务偿付覆盖倍数",
    "financial.phase3e.cfads": "可供偿债现金流",
    "financial.phase3e.break-even-price": "盈亏平衡电价",
    "financial.phase3e.investment-hurdle-gap": "投资目标差距",
    "financial.tax.cash_lifecycle": "全周期现金税费",
    "financial.asset.ending_book_value": "期末资产账面价值",
    "revenue.year.1": "首年收入",
    "consumption.year.1": "首年消纳电量",
}


def _metric_label(metric_id: str) -> str:
    if metric_id in _METRIC_LABELS:
        return _METRIC_LABELS[metric_id]
    if metric_id.startswith("energy.monthly"):
        return "月度发电量"
    if metric_id.startswith("energy.annual"):
        return "年度发电量"
    if metric_id.startswith("financial.ledger"):
        return "年度现金费用"
    generic_labels = {
        "equivalent_hours": "等效利用小时数",
        "capacity_factor": "容量因数",
        "pr_observed": "系统性能比",
        "consumption.self_ratio": "自用比例",
        "energy.year": "年度发电量",
        "energy.monthly": "月度发电量",
        "revenue.year": "年度收入",
    }
    for prefix, label in generic_labels.items():
        if metric_id.startswith(prefix):
            suffix = metric_id[len(prefix):].strip(".")
            if suffix.isdigit():
                return f"第{suffix}年{label}"
            return label
    return metric_id.replace(".", " · ")


def _input_label(field_id: str) -> str:
    """Translate normalized input keys to reader-facing project terms."""
    prefixes = {
        "roof.": "屋顶条件",
        "load.": "负荷资料",
        "tariff.": "电价与结算",
        "site.": "场址条件",
        "layout.": "总平面条件",
        "grid.": "并网条件",
    }
    suffixes = {
        "remaining_life": "剩余使用年限", "structure_report_id": "结构鉴定资料",
        "allowable_additional_load": "允许附加荷载", "meter_id": "计量边界",
        "timezone": "时区", "quality_basis": "质量说明", "poa_boundary": "辐照边界",
        "land_classification": "用地性质", "total_area": "总面积", "usable_area": "可利用面积",
        "area_basis": "面积依据", "transformer_capacity": "变压器容量",
        "available_capacity": "可接入容量", "export_power_limit": "送出功率限制",
        "connection_point": "接入点", "connection_voltage": "接入电压",
        "curtailment_assumption": "限发假设", "curtailment_basis": "限发依据",
        "line_length": "线路长度", "metering_boundary": "并网计量边界",
        "opinion_attachment_id": "接入意见附件", "opinion_status": "接入意见状态",
        "opinion_valid_until": "接入意见有效期", "permit_reference": "并网许可依据",
        "power_factor": "功率因数", "protection_plan": "保护方案",
        "transaction_opinion": "电力交易意见", "upgrade_plan": "增容方案",
        "annual_energy": "年度负荷电量", "meter_boundary": "负荷计量边界",
        "profile_attachment_id": "负荷曲线附件", "work_schedule": "工作时段",
        "age": "使用年限", "azimuth": "方位角", "design_added_load": "设计附加荷载",
        "fire_access_reference": "消防通道依据", "material": "屋面材质",
        "slope": "屋面坡度", "structure_type": "屋面结构类型",
        "waterproof_plan": "防水方案",
    }
    for prefix, label in prefixes.items():
        if field_id.startswith(prefix):
            suffix_key = field_id[len(prefix):].split(".")[-1]
            suffix = suffixes.get(suffix_key, suffix_key.replace("_", " "))
            return f"{label}·{suffix}"
    return "项目专属输入"


def _professional_metric_rows(model: ReportModel, metric_ids: tuple[str, ...]) -> list[list[str]]:
    """Show only explicitly selected, named decision metrics; keep the full ledger in Excel."""
    rows = []
    for metric_id in metric_ids:
        metric = model.metric(metric_id)
        if metric is None:
            continue
        status = metric.get("status", "UNKNOWN")
        if metric_id == "financial.phase3e.project_irr" and status in {"CALCULATED", "UNDEFINED"}:
            display, roots_note = _irr_presentation(metric)
            note = f"项目年度税后现金流；{roots_note}；合成测算"
        elif status == "CALCULATED":
            display = _word_metric_value(metric)
            note = "合成参数测算；非实测或合同承诺"
        elif status.startswith("BLOCKED"):
            display = "暂不具备有效评价条件"
            note = (str(metric.get("reason") or "当前评价项未形成有效结果")[:160]
                    if metric_id in {"financial.phase3e.project_cash_flow", "financial.phase3e.project_npv",
                                     "financial.phase3e.project_irr", "financial.phase3e.static_payback",
                                     "financial.phase3e.dynamic_payback"} else
                    "缺股东出资、分配及退出现金事件" if metric_id == "financial.phase3e.equity-investor-cash-flow" else
                    "缺可供偿债现金的定义与控制" if metric_id == "financial.phase3e.cfads" else
                    "缺终期成本现金边界" if metric_id == "financial.phase3e.lcoe" else
                    "缺同边界价格情景重算" if metric_id == "financial.phase3e.break-even-price" else
                    "缺用户投资门槛" if metric_id == "financial.phase3e.investment-hurdle-gap" else
                    str(metric.get("reason") or "必要现金事件或方法依据尚未闭合")[:160])
        elif status == "NOT_APPLICABLE":
            display, note = "不适用", "本项目无对应债务或业务适用条件；具体依据见测算模型"
        elif status == "NOT_IMPLEMENTED":
            display, note = "方法尚未实现", "所需方法或计算接口未接通；不以缺输入替代说明"
        elif status == "UNDEFINED":
            display, note = "数学上未定义", "当前现金流/评价边界下无有效数值"
        else:
            display, note = "状态待核对", "当前结果状态未知；不可当作不适用"
        unit = _metric_unit(metric)
        rows.append([_metric_label(metric_id), display,
                     "%" if metric_id.endswith("project_irr") else
                     "—" if status != "CALCULATED" and str(unit).startswith("集合") else
                     "比值" if unit == "1" else unit,
                     "按直流kWp计；分子为评价期CAPEX，非仅建设期付款" if metric_id == "financial.unit_investment" and status == "CALCULATED" else note])
    return rows


def _project_summary(model: ReportModel) -> str:
    """Keep calculated project returns separate from real-source and equity gates."""
    inputs = model.result["inputs"].get("normalized", {})
    ledger = model.result.get("evidence", {}).get("financial-ledger", {}).get("annual", [])
    years = inputs.get("project.evaluation_years")
    lines = [f"本次采用{years}年评价期的合成项目测算；计算完整度与真实工程资料成熟度分别判断。" if years else
             "本次为合成项目阶段性测算；评价期须核对输入。"]
    if ledger:
        initial = ledger[0].get("capex_cash_paid")
        working = ledger[0].get("working_capital_increase")
        if initial is not None:
            lines.append(f"建设期初始资本支出现金付款 {_word_number(initial)}元；" +
                         (f"营运资金投入 {_word_number(working)}元。" if working is not None else "营运资金待核对。"))
        renewals = [(row.get("period", "运营期"), row["replacement_cash_paid"]) for row in ledger[1:]
                    if isinstance(row.get("replacement_cash_paid"), (int, float, Decimal)) and row["replacement_cash_paid"]]
        if renewals:
            lines.append("后期更换 " + "、".join(f"{_reader_text(str(period))} {_word_number(amount)}元"
                                             for period, amount in renewals) +
                         "；这部分计入全期CAPEX，但不是初始建设款。")
    ids = ("financial.phase3e.project_npv", "financial.phase3e.project_irr",
           "financial.phase3e.static_payback", "financial.phase3e.dynamic_payback")
    calculated = []
    for mid in ids:
        if model.status(mid) == "CALCULATED" or (mid.endswith("project_irr") and model.status(mid) == "UNDEFINED"):
            label, value, unit, note = _professional_metric_rows(model, (mid,))[0]
            calculated.append(f"{label} {value}{'' if mid.endswith('project_irr') or value.endswith('%') else unit}"
                              + (f"（{note}）" if mid.endswith("project_irr") else ""))
    if calculated:
        discount = inputs.get("finance.project_discount_rate")
        basis = f"，项目折现率{_word_number(discount * 100)}%" if isinstance(discount, (int, float, Decimal)) else ""
        lines.append("按年度项目税后现金流评价" + basis + "：" + "、".join(calculated) +
                     "。上述是项目而非投资者回报，不构成真实投资批准。")
    else:
        lines.append("项目NPV、IRR及回收期须按各自指标状态核验；当前不推断投资回报。")
    blocked = _professional_metric_rows(model, ("financial.phase3e.equity-investor-cash-flow", "financial.phase3e.lcoe"))
    if blocked:
        lines.append("独立限制：" + "；".join(f"{row[0]}：{row[3]}" for row in blocked) + "。")
    lines.append("阶段性判断仅支持当前合成假设下的方案与项目收益核查；真实产权、现场条件、并网意见及合同证据仍未核验，不构成投资批准。")
    return "".join(lines)


_CHAPTER_METHOD = {
    "CH01": "项目概况与阶段性判断",
    "CH02": "研究范围、依据与边界",
    "CH03": "建设对象、主体与需求条件",
    "CH04": "站址、屋顶及建设条件",
    "CH05": "太阳能资源与气象资料",
    "CH06": "工程规模与方案配置",
    "CH07": "光伏系统初步设计",
    "CH08": "发电量预测与效率评价",
    "CH09": "电气系统与并网条件",
    "CH10": "电力消纳与交易安排",
    "CH11": "总平面、土建与施工条件",
    "CH12": "环境、安全与社会影响",
    "CH13": "实施组织与建设计划",
    "CH14": "工程投资估算",
    "CH15": "运营费用、折旧与税费",
    "CH16": "财务效益与投资回报",
    "CH17": "敏感性、情景与风险",
    "CH18": "综合结论与后续工作",
}


def _evidence_facts(evidence: dict[str, Any]) -> list[str]:
    facts = []
    for row in evidence.get("rows", []):
        if row.get("kind") != "metric" or row.get("status") != "CALCULATED":
            continue
        facts.append(f"{_metric_label(row['id'])}为{_word_value(row['value'])}{row.get('unit') or ''}")
    return facts[:4]


def _professional_missing(title: str, chapter_id: str, pv_type: str) -> str:
    """State missing material as impact plus an actionable next step."""
    ground = pv_type == "utility_scale_ground"
    if chapter_id == "CH05":
        return "目前缺少具有明确站址适用性、覆盖期和质量说明的辐照及气象资料，因此只能核查模型流程，不能评价资源等级或据此确认长期发电可靠性；下一阶段应补充经授权的资源数据，并开展代表性和不确定性复核。"
    if chapter_id == "CH04" and not ground:
        return "尚未取得屋顶权属或租赁期限、结构鉴定、荷载复核及防水消防资料，屋面可建设边界和长期运营条件因此不能确定；下一阶段应完成权利期限核查和具名结构、消防专业复核。"
    if chapter_id == "CH04" and ground:
        return "尚未取得土地权属及用地性质、测绘、地勘和可建设范围资料，场址规模及建设条件因此不能确定；下一阶段应补充合规文件和现场勘察成果。"
    if chapter_id == "CH09":
        return "尚未取得接入系统意见、可接入容量、保护整定和送出工程依据，装机规模不能替代并网条件证明；下一阶段应取得电网接入论证并完成电气校核。"
    if chapter_id == "CH10":
        if ground:
            return "尚未取得集中并网、交易价格、结算规则和限发边界资料，因此不能确认可结算电量和售电收益；下一阶段应落实接入及交易条件。"
        return "尚未取得同一计量边界和时区下的负荷曲线、合同电价及余电上网规则，因此不能确认自发自用比例和可避免费用；下一阶段应补齐计量与合同资料。"
    if chapter_id in {"CH14", "CH15"}:
        return "现有金额可用于检验费用汇总逻辑，但尚未形成与具体工程条件匹配的设备清单、工程量、报价及税费依据，因此不能视为正式投资或长期运营成本；下一阶段应补齐报价、数量和口径复核。"
    if chapter_id == "CH16":
        return "现有部分投资和运营测算尚不足以闭合项目现金流；实际收付、融资安排、终期现金事件及适用边界仍不完整，因此本阶段不对投资收益水平作确定性判断。"
    if chapter_id == "CH17":
        return "当前未形成独立情景重算及结果差异，不能由单一基准结果外推敏感性或稳健性；下一阶段应明确扰动因子、边界和重算身份。"
    if chapter_id == "CH11" and ground:
        return "尚未取得地形、地质、基础、道路排水及施工运输资料，土建工程量和施工组织因此不能确定；下一阶段应完成专项勘察和初步设计。"
    if chapter_id == "CH07":
        return "设备及系统参数尚缺少经核验的型号、数据表和适用性依据，当前只能作为方案边界检查；下一阶段应完成设备选型和系统校核。"
    if chapter_id == "CH13":
        return "项目审批、采购、施工和并网前置条件尚未闭合，不能据此确定开工或并网日期；下一阶段应形成责任分工和里程碑清单。"
    return f"与“{title}”直接相关的原始资料或专业复核尚未闭合，因此本阶段仅保留条件性判断；下一阶段应补充对应资料并复核其对方案的影响。"


def _professional_narrative(model: ReportModel, pv_type: str, chapter_id: str, title: str,
                            evidence: dict[str, Any], *, item_no: int = 1,
                            editorial_fixture: dict[str, Any] | None = None) -> tuple[list[str], str, str]:
    """Build category-aware consulting prose from bound evidence, not template labels."""
    facts = _evidence_facts(evidence)
    fact_text = "；".join(facts) + "。" if facts else ""
    profile = REPORT_PROFILES[pv_type]
    ground = pv_type == "utility_scale_ground"
    if evidence["state"] == "NOT_APPLICABLE":
        return [f"{title}在{profile['boundary']}的评价边界内不构成适用事项，相关模型不作替代性套用。"], "不适用", "NOT_APPLICABLE"
    if chapter_id == "CH05":
        lead = f"{title}的评价应以站址资源数据、时间覆盖和质量控制为基础。{fact_text}"
    elif chapter_id == "CH08":
        lead = f"{title}按当前资源时序、容量配置和损失参数进行预测。{fact_text}"
    elif chapter_id == "CH10":
        mode = "集中并网、交易电价和限发边界" if ground else "负荷匹配、自发自用和余电上网"
        lead = f"{title}按{mode}组织分析。{fact_text}"
    elif chapter_id == "CH14":
        lead = f"{title}采用当前工程费用参数进行阶段性估算。{fact_text}"
    elif chapter_id == "CH16":
        lead = f"{title}应建立在评价期、投资口径、收入、成本和融资现金事件完整的基础上。{fact_text}"
    elif chapter_id == "CH17":
        lead = f"{title}用于识别影响项目推进的关键条件和待验证风险。{fact_text}"
    elif chapter_id == "CH18":
        lead = f"{title}综合建设条件、技术方案、发电预测、消纳并网和财务边界形成阶段性意见。{fact_text}"
    else:
        lead = f"{title}纳入{_CHAPTER_METHOD.get(chapter_id, '相关工程条件')}的研究范围。{fact_text}"
    chapter_items = next(items for cid, _chapter_title, items in CHAPTERS if cid == chapter_id)
    research_focus = guidance(f"{chapter_id}.{item_no:02d}", chapter_items)
    editorial = [f"“{title}”的研究重点是{research_focus}"]
    if editorial_fixture:
        record = editorial_fixture["chapters"][chapter_id]
        if item_no == 1:
            editorial.append(f"围绕“{title}”，本章背景采用编辑性测试假设：{record['background']}")
        elif item_no % 3 == 2:
            editorial.append(f"围绕“{title}”，在编辑性测试边界内的拟议做法为：{record['proposal']}")
        else:
            editorial.append(f"围绕“{title}”，该设定的核验要求是：{record['verification']}")
    if evidence["state"] == "EVIDENCED":
        tail = f"在“{title}”的当前边界内，已有结果仅适用于合成输入和本次计算，可用于方案检查，不能替代现场实测、审批文件或正式设计审查。"
        claim_status = "EVIDENCE_BOUND_CONDITIONAL"
    else:
        missing = _topic_missing(title, chapter_id, pv_type, _professional_missing(title, chapter_id, pv_type))
        tail = f"“{title}”仍受以下条件约束：{missing}"
        claim_status = "LIMITED_BY_MISSING_EVIDENCE"
    paragraphs = [lead, *editorial, tail]
    return paragraphs, "".join(paragraphs), claim_status


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


def _topic_context(pv_type: str, chapter_id: str, title: str) -> str:
    """Return a subject-specific review focus for one fixed report item."""
    profile = REPORT_PROFILES[pv_type]
    chapter_focus = {
        "CH01": "项目身份、评价边界、成熟度和可决策条件",
        "CH02": "编制依据、口径版本、评价范围和免责边界",
        "CH03": "建设必要性、业主/运营模式和项目分类",
        "CH04": "站址或屋顶物理边界、权属、面积及建设约束",
        "CH05": "资源数据集、气象变量、时间粒度和不确定性",
        "CH06": "任务规模、容量配置、方案比选和分类适用性",
        "CH07": "组件、逆变器、支架、电气参数和损失链",
        "CH08": "月度/年度发电、衰减、效率、限发和预测边界",
        "CH09": "接入点、变压器/线路、升压送出和电网确认",
        "CH10": "负荷消纳、上网结算、价格合同和市场边界",
        "CH11": "总平面、基础、道路排水、结构/施工条件",
        "CH12": "生态、消防、施工运行安全和社会影响",
        "CH13": "采购施工调试、责任分工、里程碑和进入条件",
        "CH14": "CAPEX边界、数量单价、税口径和专项工程",
        "CH15": "OPEX、折旧、更换、税费和年度现金影响",
        "CH16": "项目/资本金现金流、回报指标、偿债和阈值",
        "CH17": "敏感性、情景、风险证据和反向约束",
        "CH18": "证据闭合、否决条件、推进门槛和后续核查",
    }
    detail = chapter_focus.get(chapter_id, "本项目类型的专业边界和证据链")
    if pv_type == "utility_scale_ground" and any(word in title for word in ("屋顶", "自用", "荷载")):
        detail += "；本地面项目不套用工商业屋顶自用或屋面承载模型"
    if pv_type == "industrial_rooftop" and any(word in title for word in ("土地", "地勘", "排水", "升压站")):
        detail += "；屋顶项目不把集中式地面土地/地勘/升压结论当作已取得证据"
    return f"本项围绕“{title}”核对{detail}，项目边界为{profile['boundary']}。"


def _topic_missing(title: str, chapter_id: str, pv_type: str, fallback: str) -> str:
    """Explain the missing evidence in terms a reviewer can act on."""
    if "资源" in title or chapter_id == "CH05":
        return "需补充带授权和覆盖期的GHI/DNI/DHI、温度、风速、单位、时区、质量标记及交叉验证记录。"
    if any(word in title for word in ("价格", "售电", "电价", "合同", "交易")):
        return "需补充生效日期、适用节点、税费口径、购售电合同/交易规则及价格来源，不能用展示价格替代合同证据。"
    if any(word in title for word in ("负荷", "消纳", "自用", "上网", "限发")):
        return "需补充同一计量边界和时区下的逐时或15分钟负荷、计量质量、结算规则及限发记录。"
    if any(word in title for word in ("土地", "地形", "地质", "道路", "排水", "基础")):
        return "需补充土地权属/用地性质、测绘、地勘、坡度、道路排水、基础和可建设边界文件。"
    if any(word in title for word in ("结构", "遮挡", "防水", "消防", "承载")):
        return "需补充结构鉴定、荷载复核、遮挡测量、防水/消防边界和具名审查意见。"
    if any(word in title for word in ("组件", "逆变器", "支架", "串并联", "电气")):
        return "需补充设备型号、数据表、适用环境、串并联校核、保护整定和供应商来源。"
    if any(word in title for word in ("CAPEX", "投资", "成本", "OPEX", "折旧", "税")):
        return "需补充逐项数量×单价、报价时点、税率/可抵扣边界、运维合同、更换计划和来源授权。"
    if any(word in title for word in ("融资", "偿债", "现金流", "IRR", "NPV", "回收", "LCOE", "DSCR")):
        return "需补充融资协议、提款/还本付息、折现率、税费、现金流时点和适用指标的可追溯输入。"
    if "敏感" in title or "情景" in title or "阈值" in title:
        return "需补充独立情景控制、变化因子、边界值、重算运行身份和结果差异；不能由单一基准外推。"
    if "政策" in title or "标准" in title or "合规" in title:
        return "需补充适用区域、有效期、原文条款、授权状态和逐条适用性判断。"
    if fallback:
        return fallback
    return f"需补充与“{title}”直接对应的原始字段、来源位置、授权状态、计算结果或专业审查记录。"


def _item_evidence(model: ReportModel, pv_type: str, chapter_id: str, title: str, *, item_no: int = 1,
                   editorial_fixture: dict[str, Any] | None = None) -> dict[str, Any]:
    items = next(items for cid, _chapter_title, items in CHAPTERS if cid == chapter_id)
    item_id = f"{chapter_id}.{item_no:02d}"
    rule = guidance(item_id, items)
    fields = category_fields(item_id, CHAPTER_FIELDS[chapter_id][item_no - 1], pv_type,
                             model.result["inputs"].get("normalized", {}).get("project.has_storage") is not False)
    metrics = CHAPTER_METRICS[chapter_id][item_no - 1]
    if item_id in {"CH01.05", "CH18.01"}:
        fields = tuple(dict.fromkeys((*fields, "site.rights_status", "grid.opinion_status")))
        metrics = (*metrics, "financial.phase3e.project_cash_flow")
    if pv_type == "utility_scale_ground" and item_id in {"CH01.04", "CH10.02"}:
        metrics = tuple(metric for metric in metrics if not metric.startswith("consumption."))
    claim = build_claim(model, item_id, title, f"{title}：{rule.rstrip('。')}？", rule,
                        fields, metrics,
                        pv_type, _word_value, _metric_label)
    cited_metrics = tuple(dict.fromkeys((*metrics, *claim["supporting_metric_ids"])))
    cited_fields = tuple(dict.fromkeys((*fields, *claim["supporting_input_field_ids"])))
    return {**claim, "field_ids": list(cited_fields), "metric_ids": list(cited_metrics),
            "missing": claim["unresolved"] if claim["state"] != "NOT_APPLICABLE" else "",
            "conclusion": claim["decision"]}


def profile_name(pv_type: str) -> str:
    return REPORT_PROFILES[pv_type]["boundary"]


def _appendix_rule(app_id: str, pv_type: str) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    if app_id == "APP01": return (), (), "逐项列出本次运行使用的输入、方法、bundle、canonical和来源身份。"
    if app_id == "APP02": return ("energy.monthly.year.1", "energy.year.1"), ("resource.poa_boundary",), "核对12个月资源与发电结果的时间粒度、单位和来源。"
    if app_id == "APP03": return ("dc_capacity", "ac_capacity", "dc_ac_ratio"), ("system.losses",), "核对组件、逆变器、容量比和损失分项的输入与计算绑定。"
    if app_id == "APP04": return ("financial.capex.total", "financial.unit_investment"), ("capex.items",), "核对CAPEX逐项金额、币种、税口径、报价时点和项目类型专项项。"
    if app_id == "APP05": return ("financial.opex.cash_lifecycle",), ("opex.items", "assets.depreciation", "assets.replacements"), "核对运维、折旧、更换和税费年度边界。"
    if app_id == "APP06": return ("financial.phase3e.project_npv", "financial.phase3e.project_irr"), (), "核对项目与资本金现金流、评价期、折现率和未决指标。"
    if app_id == "APP07": return ("financial.phase3e.dscr",), ("finance.debt_schedule",), "核对债务余额、还本付息、CFADS和DSCR适用性。"
    if app_id == "APP08": return (), (), "核对敏感性/情景控制、变化因子、运行身份和结果差异。"
    if app_id == "APP09": return (), (), "核对政策适用区域、有效期、条款原文和授权状态。"
    if app_id == "APP10": return (), (), "集中列出当前 findings、阻断码、缺失字段和下一步资料。"
    if app_id == "APP11": return (), (), "列出公式文本、变量、单位、边界条件、输入和来源。"
    if app_id == "APP12": return (), (), "列出本报告出现的中文术语、英文全称、缩写和首次释义。"
    return (), (), "记录版本、运行身份、数据质量轴、静态快照和复核状态。"


def _appendix_evidence(model: ReportModel, pv_type: str, app_id: str, item_no: int) -> dict[str, Any]:
    item_id = f"{app_id}.{item_no:02d}"
    question, rule, field_ids, metric_ids = APPENDIX_RULES[item_id]
    title = APPENDIX_TITLES[item_id]
    field_ids = category_fields(item_id, field_ids, pv_type,
                                model.result["inputs"].get("normalized", {}).get("project.has_storage") is not False)
    claim = build_claim(model, item_id, title, question, rule, field_ids, metric_ids,
                        pv_type, _word_value, _metric_label)
    cited_fields = tuple(dict.fromkeys((*field_ids, *claim["supporting_input_field_ids"])))
    cited_metrics = tuple(dict.fromkeys((*metric_ids, *claim["supporting_metric_ids"])))
    return {**claim, "field_ids": list(cited_fields), "metric_ids": list(cited_metrics),
            "missing": claim["unresolved"] if claim["state"] != "NOT_APPLICABLE" else "",
            "conclusion": claim["decision"]}


def _add_evidence_table(document: Document, evidence: dict[str, Any], caption: str) -> None:
    rows = [[row["kind"], row["id"], row["value"], row["unit"], row["status"], row["formula_id"], ", ".join(row["source_ids"]) or "UNKNOWN"]
            for row in evidence["rows"][:12]]
    _add_table(document, ["类型", "指标/字段", "值", "单位", "状态", "公式/绑定", "source_ids"], rows, caption)


def _write_docx(model: ReportModel, output: Path, display_name: str, pv_type: str,
                editorial_fixture: dict[str, Any] | None = None) -> dict[str, Any]:
    profile = REPORT_PROFILES[pv_type]
    source_map = _source_ref_map(model)
    document = Document()
    section = document.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.top_margin = Mm(18)
    section.bottom_margin = Mm(18)
    section.left_margin = Mm(22)
    section.right_margin = Mm(18)
    section.header_distance = Mm(8)
    section.footer_distance = Mm(8)
    styles = document.styles
    styles["Normal"].font.name = "等线"
    styles["Normal"]._element.rPr.rFonts.set(qn("w:eastAsia"), "等线")
    styles["Normal"].font.size = Pt(10)
    styles["Normal"].font.color.rgb = RGBColor.from_string(_D_STYLE["ink"])
    styles["Normal"].paragraph_format.line_spacing = 1.15
    styles["Normal"].paragraph_format.space_after = Pt(4)
    for heading, size in (("Heading 1", 15), ("Heading 2", 11.5), ("Heading 3", 10.5)):
        styles[heading].font.name = "黑体"
        styles[heading]._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
        styles[heading].font.color.rgb = RGBColor.from_string(_D_STYLE["ink"])
        styles[heading].font.size = Pt(size)
        styles[heading].paragraph_format.space_before = Pt(10 if heading == "Heading 1" else 6)
        styles[heading].paragraph_format.space_after = Pt(4)
        styles[heading].paragraph_format.keep_with_next = True
    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header_run = header.add_run(f"{profile['title']} · 阶段性草稿")
    header_run.font.size = Pt(8)
    header_run.font.color.rgb = RGBColor.from_string(_D_STYLE["muted"])

    # D-style cover: one restrained page, no audit hashes or raw status table.
    brand = document.add_paragraph()
    brand.paragraph_format.space_before = Pt(28)
    brand_run = brand.add_run("星核实验室  StarCore Lab")
    brand_run.bold = True
    brand_run.font.size = Pt(11)
    brand_run.font.color.rgb = RGBColor.from_string(_D_STYLE["accent"])
    title = document.add_paragraph()
    title.paragraph_format.space_before = Pt(36)
    title_run = title.add_run(profile["title"])
    title_run.bold = True
    title_run.font.size = Pt(23)
    title_run.font.name = "黑体"
    title_run.font.color.rgb = RGBColor.from_string(_D_STYLE["ink"])
    rule = document.add_paragraph("━━━━━━━━━━━━━━━━━━━━━━━━")
    rule.paragraph_format.space_after = Pt(14)
    for run in rule.runs:
        run.font.color.rgb = RGBColor.from_string(_D_STYLE["accent"])
        run.font.size = Pt(10)
    project = document.add_paragraph(display_name)
    project.paragraph_format.space_after = Pt(16)
    for run in project.runs:
        run.bold = True
        run.font.size = Pt(16)
        run.font.color.rgb = RGBColor.from_string(_D_STYLE["ink"])
    synthetic_calculation = (str(model.result["project_id"]).startswith("SYNTHETIC")
                             and model.result["maturity"].get("real_project") != "VERIFIED")
    sample_status = ("合成计算 · 部分结果 · 未经现场核验"
                     if synthetic_calculation else "资料不充分样件 · 阶段性草稿")
    if editorial_fixture:
        sample_status = "合成计算及编辑假设样件 · 结果仍为部分完成"
    _add_table(document, ["项目类型", "编制状态", "评价日期"],
               [[profile["boundary"], sample_status, str(model.result["evaluation_date"])]],
               widths_cm=(5.3, 6.0, 5.7), font_size=9)
    cover_note = document.add_paragraph("本报告为基于本次统一测算结果的预可研开发样件。计算结果、资料成熟度和财务限制均按当前状态呈现，不替代正式可研、设计审查、并网意见、合同审核或投资决策。")
    cover_note.paragraph_format.space_before = Pt(20)
    cover_note.paragraph_format.line_spacing = 1.3
    if editorial_fixture:
        identity_note = document.add_paragraph("资料身份：EDITORIAL_TEST_ASSUMPTION（仅用于合成项目编辑性测试，不作为真实第三方证据，也不进入计算引擎）。")
        identity_note.paragraph_format.space_before = Pt(8)
        for run in identity_note.runs:
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor.from_string(_D_STYLE["muted"])
    cover_footer = document.add_paragraph("版本状态：阶段性草稿  ·  仅限本地审阅  ·  资料不足，暂不具备决策条件")
    for run in cover_footer.runs:
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor.from_string(_D_STYLE["muted"])
    document.add_page_break()

    document.add_heading("目录", level=1)
    _add_toc(document)
    document.add_page_break()
    document.add_heading("执行摘要", level=1)
    basis_text = ("本阶段同时使用明确标识的编辑性测试假设，用于检验工程背景与计算结果的衔接；这些假设不进入计算引擎，也不构成第三方证据。"
                  if editorial_fixture else
                  "本次使用当前来源快照及已计算指标；缺失或未核验的真实工程事实不以占位值补足，具体项目收益见下表与初步结论。")
    document.add_paragraph(f"本项目属于{profile['boundary']}。{basis_text}以下结果按指标实际状态列示，不以整体部分完成状态覆盖已计算项目指标。")
    key_ids = ("dc_capacity", "ac_capacity", "energy.year.1", "consumption.year.1",
               "energy.delivered.year.1", "revenue.year.1", "financial.capex.total",
               "financial.phase3e.project_npv", "financial.phase3e.project_irr",
               "financial.phase3e.static_payback", "financial.phase3e.dynamic_payback")
    key_rows = _professional_metric_rows(model, key_ids)
    _add_table(document, ["专业指标", "本阶段结果", "单位", "说明"], key_rows,
               "关键结果（完整精度和追溯字段见测算模型.xlsx）", widths_cm=(4.0, 4.8, 2.0, 5.0))
    normalized = model.result["inputs"].get("normalized", {})
    input_rows = []
    records = model.result.get("source_snapshot", {}).get("phase2", {}).get("records", ())
    input_sources = {record.get("field_id"): record for record in records if record.get("source_id")}
    for key, value in sorted(normalized.items()):
        if profile["special_prefixes"] and key.startswith(profile["special_prefixes"]):
            display = _word_value(value)
            source = input_sources.get(key, {})
            unit = source.get("unit")
            if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool) and unit not in (None, "", "1"):
                display += f" {unit}"
            state = "合成假设已提供；未真实核验" if source.get("status") == "ASSUMED" else (
                "来源已核验" if source.get("status") == "VERIFIED" else "已提供；来源状态待核验")
            input_rows.append([_input_label(key), display, state, "详细字段见来源清单"])
    _add_table(document, ["项目类型专属输入", "展示值", "采用情况", "追溯位置"], input_rows[:16],
               "项目类型专属输入摘要（不展开原始对象）", widths_cm=(4.2, 5.0, 3.0, 5.0))
    document.add_paragraph("初步结论：" + _project_summary(model))
    chart_specs = _canonical_chart_specs(model)
    chart_receipts: list[dict[str, Any]] = []
    checklist: list[dict[str, Any]] = []

    for chapter_id, chapter_title, items in CHAPTERS:
        document.add_heading(f"{chapter_id} {chapter_title}", level=1)
        document.add_paragraph(_chapter_intro(chapter_id, chapter_title))
        if chapter_id == "CH08":
            chart_receipts = _add_canonical_charts(document, chart_specs, source_map, "发电量变化")
        for number, item in enumerate(items, 1):
            item_id = f"{chapter_id}.{number:02d}"
            document.add_heading(f"{item_id} {item}", level=2)
            evidence = _item_evidence(model, pv_type, chapter_id, item, item_no=number,
                                       editorial_fixture=editorial_fixture)
            _add_professional_narrative(document, evidence)
            checklist.append({"id": item_id, "title": item,
                              "content_summary": evidence["summary"][:600], "input_field_ids": evidence["field_ids"],
                              "metric_ids": evidence["metric_ids"], "source_ids": evidence["source_ids"],
                              "claim_id": evidence["claim_id"], "canonical_result_hash": evidence["canonical_result_hash"],
                              "core_question": evidence["core_question"],
                              "central_claim": evidence["central_claim"],
                              "supporting_metric_ids": evidence["supporting_metric_ids"],
                              "supporting_input_field_ids": evidence["supporting_input_field_ids"],
                              "supporting_formula_ids": evidence["supporting_formula_ids"],
                              "field_instance_ids": evidence["field_instance_ids"],
                              "causal_reasoning": evidence["causal_reasoning"], "decision": evidence["decision"],
                              "unresolved": evidence["unresolved"], "next_action": evidence["next_action"],
                              "professional_content_status": evidence["state"], "claim_status": evidence["claim_status"], "structure_status": "GENERATED",
                              "duplicate_template": False, "wrong_evidence_binding": False,
                              "visual_layout_status": "NOT_TESTED", "missing_materials": evidence["missing"],
                              "final_conclusion": evidence["conclusion"]})

    document.add_heading("结果与公式索引", level=1)
    document.add_paragraph("本节仅列示与投资评价直接相关的专业指标。完整数值精度、计算口径和来源绑定保留在配套测算模型中，正文不重复展开审计字段。")
    blocked = [metric for metric in model.metrics if str(metric.get("status", "")).startswith("BLOCKED")]
    index_ids = ("financial.capex.total", "financial.opex.cash_lifecycle",
                 "financial.tax.cash_lifecycle", "financial.asset.ending_book_value",
                 "financial.phase3e.project_cash_flow", "financial.phase3e.project_npv",
                 "financial.phase3e.project_irr", "financial.phase3e.static_payback",
                 "financial.phase3e.dynamic_payback", "financial.phase3e.equity-investor-cash-flow",
                 "financial.phase3e.cfads", "financial.phase3e.lcoe",
                 "financial.phase3e.break-even-price", "financial.phase3e.investment-hurdle-gap")
    index_rows = _professional_metric_rows(model, index_ids)
    _add_table(document, ["专业指标", "本阶段结果", "单位", "说明"], index_rows,
               "财务与项目指标摘要", widths_cm=(4.0, 4.8, 2.0, 5.0))
    if blocked:
        if model.status("financial.phase3e.project_npv") == "CALCULATED":
            document.add_paragraph("以下阻断仅适用于各自指标；不撤销已计算的项目净现值。IRR、回收期须以其自身状态为准；股东现金事件与平准化成本边界须独立补证。")
        else:
            document.add_paragraph("以下指标按各自阻断理由补证；不能由尚未计算的项目回报或其他指标推断有效收益。")
    for app_id, app_title in APPENDICES:
        document.add_heading(f"{app_id} {app_title}", level=1)
        document.add_paragraph(f"{app_id}《{app_title}》提供受控追溯摘要；完整字段、原始精度和来源编号保留在配套 Excel。")
        for item_no in (1, 2):
            item_id = f"{app_id}.{item_no:02d}"
            item_title = APPENDIX_TITLES[item_id]
            document.add_heading(f"{item_id} {item_title}", level=2)
            evidence = _appendix_evidence(model, pv_type, app_id, item_no)
            if app_id in {"APP11", "APP12"}:
                detail = (f"本次列示{len(_formula_definitions(model))}条被引用定义"
                          + (f"，冻结字典共{len(model.catalog.formulas)}条" if model.catalog else "")
                          + "；列示、引用与成功执行不等同。具体符号及边界按公式分组见下一节。"
                          if item_id == "APP11.01" else
                          "各公式的完整符号、下标、集合与适用边界分别列示；定义存在不代表已执行。"
                          if item_id == "APP11.02" else
                          "受控中英文术语按名称、全称、缩写、实际含义及适用边界列示。")
                evidence["narrative"] = [detail]
                evidence["summary"] = detail
            for text in evidence["narrative"]:
                document.add_paragraph(_reader_text(text))
            if item_id == "APP02.01":
                resource_headers, resource_rows = _resource_rows(model)
                # Keep the individual month and its source identity together in
                # the reader-facing appendix; F03 retains every field atom.
                resource_display = [row[:8] + [str(row[8]).split("；辐照为", 1)[0]]
                                    for row in resource_rows]
                _add_table(document, resource_headers, resource_display,
                           "月度资源与逐行来源（完整字段实例见测算模型 M04）",
                           widths_cm=(1.0, 1.4, 1.4, 1.4, 1.4, 1.5, 1.5, 1.4, 5.8),
                           font_size=7)
            if app_id in {"APP11", "APP12"}:
                appendix_headers, appendix_rows = _appendix_rows(model, item_id)
                if item_id == "APP11.01" and appendix_rows:
                    _add_table(document, ["正式编号", "中文名称", "本次引用与执行"],
                               [[row[0], row[1], row[5]] for row in appendix_rows],
                               "公式索引（不等于冻结公式全部执行）", font_size=9)
                elif item_id == "APP11.02":
                    definitions = _formula_definitions(model)
                    shared, shared_ids = _formula_shared_contracts(definitions)
                    if shared:
                        document.add_heading("共通记法契约（按原文一致性分组）", level=3)
                        document.add_paragraph("相同契约仅在此处完整定义一次；每条公式在下方注明所适用的组号。逐符号定义及量纲仍逐公式列出。")
                        for label, text, number in shared:
                            document.add_paragraph(f"{label}第{number}组：{text}")
                    for formula in definitions:
                        fid = formula["formula_id"]
                        heading = document.add_heading(f"{fid} {formula.get('chinese_name', '未定义')}", level=3)
                        heading.paragraph_format.keep_with_next = True
                        document.add_paragraph(f"公式：{formula.get('text_equation') or formula.get('latex') or '未提供'}（结果单位：{formula.get('unit') or '未定义'}）")
                        document.add_paragraph("适用边界：" + _reader_text(str(formula.get("calculation_boundary") or "未定义")))
                        document.add_paragraph("本项目状态：" + _formula_status(model, fid))
                        references = [f"{label}第{shared_ids[key, _formula_contract_text(formula[key])]}组"
                                      for key, label in (("operator_definition", "运算符"),
                                                         ("notation_contract", "记法与歧义"),
                                                         ("unit_convention", "单位约定")) if formula.get(key)]
                        if references:
                            document.add_paragraph("本式共通契约：" + "；".join(references))
                        if formula.get("dimensional_check"):
                            document.add_paragraph("本式量纲校核：" + _formula_contract_text(formula["dimensional_check"]))
                        symbols = [[s.get("symbol") or "未定义", s.get("definition_zh") or "未定义",
                                    s.get("unit") or "未定义"] for s in formula.get("every_symbol_definition", ())]
                        if symbols:
                            _add_table(document, ["完整符号", "中文定义", "单位"], symbols,
                                       "完整符号（仅属于本公式）", widths_cm=(3, 11, 3), font_size=9)
                        index_lines = _formula_index_lines(formula)
                        if index_lines:
                            document.add_paragraph("下标、索引、集合与求和范围：" + "；".join(index_lines))
                elif appendix_rows:
                    _add_table(document, appendix_headers, appendix_rows,
                               f"{item_id} · 受控编辑词典", font_size=9)
            checklist.append({"id": item_id, "title": item_title,
                              "content_summary": evidence["summary"][:600], "input_field_ids": evidence["field_ids"],
                              "metric_ids": evidence["metric_ids"], "source_ids": evidence["source_ids"],
                              "claim_id": evidence["claim_id"], "canonical_result_hash": evidence["canonical_result_hash"],
                              "core_question": evidence["core_question"],
                              "central_claim": evidence["central_claim"],
                              "supporting_metric_ids": evidence["supporting_metric_ids"],
                              "supporting_input_field_ids": evidence["supporting_input_field_ids"],
                              "supporting_formula_ids": evidence["supporting_formula_ids"],
                              "field_instance_ids": evidence["field_instance_ids"],
                              "causal_reasoning": evidence["causal_reasoning"], "decision": evidence["decision"],
                              "unresolved": evidence["unresolved"], "next_action": evidence["next_action"],
                              "professional_content_status": evidence["state"], "claim_status": evidence["claim_status"], "structure_status": "GENERATED",
                              "duplicate_template": False, "wrong_evidence_binding": False,
                              "visual_layout_status": "NOT_TESTED", "missing_materials": evidence["missing"],
                              "final_conclusion": evidence["conclusion"]})

    document.add_heading("术语与公式说明", level=1)
    document.add_paragraph("公式定义、版本、变量、单位、输入字段和完整来源绑定见测算模型.xlsx 的公式说明工作表，以及资料来源与假设清单.xlsx 的公式/方法工作表。正文不复制原始对象或过高精度小数。")
    document.add_heading("版本与质量声明", level=1)
    document.add_paragraph(f"项目边界：{profile['boundary']}。报告内容版本：{REPORT_CONTENT_VERSION}；该版本只表示写作与排版，不修改计算结果身份。配套 Excel 为本次测算快照；修改 Excel 不会使本报告或旧结果自动有效，必须重新运行计算程序生成新的统一身份。PDF 只有在真实转换器可用并成功解析时才生成；本次渲染、页面视觉和目录页码门禁以质量清单实际状态为准。")
    _add_table(document, ["身份字段", "统一测算值"], [[key, str(value)] for key, value in model.identity.items()],
               "统一测算身份（仅在此处展示一次）", widths_cm=(4.5, 12.5), font_size=8.5)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("合成分析草稿 · 真实项目须经专业核验 · ")
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    footer._p.append(fld)
    coverage = _validate_checklist_coverage(checklist)
    claim_fields = ("claim_id", "core_question", "central_claim", "claim_status",
                    "causal_reasoning", "decision", "unresolved", "next_action")
    if (len({record["claim_id"] for record in checklist}) != len(checklist)
            or len({record["core_question"] for record in checklist}) != len(checklist)
            or any(not all(record.get(key) for key in claim_fields) for record in checklist)):
        raise ContractError("REPORT_CLAIM_COVERAGE")
    for record in checklist:
        record["wrong_evidence_binding"] = _claim_binding_error(model, record)
    if any(record["wrong_evidence_binding"] for record in checklist):
        raise ContractError("REPORT_CLAIM_BINDING")
    duplicate_scan = _scan_duplicate_paragraphs(document, checklist)
    language_scan = _scan_professional_language(document, pv_type, checklist)
    tmp = output.with_name("." + output.name + ".tmp")
    document.save(tmp)
    os.replace(tmp, output)
    return {"path": output.name, "size": output.stat().st_size, "sha256": _sha256(output),
            "report_content_version": REPORT_CONTENT_VERSION,
            **coverage,
            "charts": chart_receipts, "content_checklist": checklist,
            "duplicate_scan": duplicate_scan, "language_scan": language_scan,
            "toc_status": "FIELD_REQUIRES_RENDER_REFRESH",
            "page_size": "A4", "table_policy": "COMPACT_SUMMARY_AND_XLSX_TRACEABILITY"}


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


def _export_report(result: dict[str, Any], catalog, workspace: Workspace, output_dir: str, *, formula_map: dict[str, Any] | None,
                   expected_pv_type: str, phase: str,
                   editorial_fixture: dict[str, Any] | None = None) -> dict[str, Any]:
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
    try:
        editorial_fixture = validate_fixture(editorial_fixture, pv_type=expected_pv_type,
                                              result_hash=model.result["result_hash"])
    except ValueError as exc:
        raise ContractError(str(exc)) from exc
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
    artifact_started = time.perf_counter()
    cover_name = (editorial_fixture.get("project_alias") if editorial_fixture else None) or _cover_project_name(expected_pv_type)
    files["F01"] = _write_docx(model, docx_path, cover_name, expected_pv_type,
                                editorial_fixture=editorial_fixture)
    files["F01"]["generation_seconds"] = round(time.perf_counter() - artifact_started, 6)
    checklist = files["F01"].pop("content_checklist")
    coverage = _validate_checklist_coverage(checklist)
    duplicate_scan = files["F01"].get("duplicate_scan", {})
    language_scan = files["F01"].get("language_scan", {})
    checklist_path = root / "content-checklist.json"
    checklist_payload = {
        "schema_version": "phase7i-content-checklist-v1",
        "claim_contract_version": "phase7l-central-claim-v1",
        "report_content_version": REPORT_CONTENT_VERSION,
        "project_id": model.result["project_id"], "pv_type": model.result["pv_type"],
        "identity": model.identity,
        "coverage": coverage,
        "records": checklist,
        "quality_axes": {"structure_status": "GENERATED", "coverage_status": "PASS", "substantive_content_status": "CONTENT_REVIEW_REQUIRED",
                         "central_claim_contract": "PASS", "central_claim_contract_scope": "STRUCTURAL_FIELDS_AND_BINDINGS_ONLY",
                         "substantive_claim_review": "NOT_REVIEWED",
                         "legal_evidence_status": "SYNTHETIC_OR_SOURCE_BOUND", "visual_layout_status": "NOT_TESTED",
                         "editorial_fixture_status": "BOUND_IDENTITY" if editorial_fixture else "NOT_SELECTED",
                         "editorial_fixture_kind": editorial_fixture.get("evidence_kind") if editorial_fixture else None,
                         "golden_sample_chapters": editorial_fixture.get("golden_sample_chapters", []) if editorial_fixture else [],
                         "no_duplicate_template_abuse": "CONTENT_REVIEW_REQUIRED",
                         "professional_narrative": "CONTENT_REVIEW_REQUIRED",
                         "no_programming_language_in_body": language_scan.get("no_programming_language_in_body", "UNKNOWN"),
                         "no_generic_template_abuse": "CONTENT_REVIEW_REQUIRED",
                         "chapter_semantic_alignment": "CONTENT_REVIEW_REQUIRED",
                         "evidence_grounded_claims": "CONTENT_REVIEW_REQUIRED",
                         "category_specific_narrative": "CONTENT_REVIEW_REQUIRED",
                         "document_content_review": "NOT_REVIEWED"},
        "duplicate_scan": duplicate_scan,
        "language_scan": language_scan,
    }
    checklist_path.write_text(json.dumps(checklist_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files["F05"] = {"path": checklist_path.name, "size": checklist_path.stat().st_size,
                     "sha256": _sha256(checklist_path), "records": len(checklist),
                     "structure_status": "GENERATED", "visual_layout_status": "NOT_TESTED",
                     "duplicate_scan": duplicate_scan, "language_scan": language_scan}
    canonical_path = root / "canonical.json"
    canonical_path.write_text(dumps(result) + "\n", encoding="utf-8")
    files["F06"] = {"path": canonical_path.name, "size": canonical_path.stat().st_size,
                     "sha256": _sha256(canonical_path), "status": "GENERATED"}
    artifact_started = time.perf_counter()
    files["F03"] = _write_model_xlsx(model, xlsx_path, expected_pv_type)
    files["F03"]["generation_seconds"] = round(time.perf_counter() - artifact_started, 6)
    source_started = time.perf_counter()
    source_receipt = create_source_workbook(model.result, catalog, Workspace(root), source_name, formula_map=formula_map)
    files["F04"] = {**source_receipt, "generation_seconds": round(time.perf_counter() - source_started, 6)}
    pdf_path = root / f"{stem}-光伏预可研报告.pdf"
    artifact_started = time.perf_counter()
    files["F02"] = _convert_pdf(docx_path, pdf_path)
    files["F02"]["generation_seconds"] = round(time.perf_counter() - artifact_started, 6)
    identity = model.identity
    for entry in files.values():
        if entry.get("status") != "BLOCKED":
            entry.update(identity)
    _assert_same_identity(files, identity)
    receipt = {
        "status": "DRAFT_PARTIAL" if files["F02"].get("status") != "GENERATED" else "DRAFT_PARTIAL",
        "phase": phase,
        "report_content_version": REPORT_CONTENT_VERSION,
        "project_id": model.result["project_id"], "pv_type": model.result["pv_type"],
        "display_name": display_name, "name_mapping": name_mapping,
        "identity": identity, "files": files,
        "charts": {"docx": files["F01"].get("charts", []), "xlsx": files["F03"].get("charts", [])},
        "coverage": {**coverage, "model_sheets": 19, "source_sheets": 10},
        "pdf_status": files["F02"].get("status"),
        "quality_gates": {
            "PAGE_SIZE_A4": files["F01"].get("page_size", "UNKNOWN"),
            "COVER_STYLE_D": "GENERATED",
            "TOC_VALID": files["F01"].get("toc_status", "UNKNOWN"),
            "TABLE_LAYOUT": "COMPACT_SUMMARY_AND_XLSX_TRACEABILITY",
            "CONTENT_READABILITY": "NOT_TESTED_RENDER",
            "NO_OVERFLOW": "NOT_TESTED_RENDER",
            "NO_DUPLICATE_TEMPLATE_ABUSE": "CONTENT_REVIEW_REQUIRED",
            "EXACT_DUPLICATE_SCAN": duplicate_scan.get("status", "UNKNOWN"),
            "PROFESSIONAL_NARRATIVE": "CONTENT_REVIEW_REQUIRED",
            "NO_PROGRAMMING_LANGUAGE_IN_BODY": language_scan.get("no_programming_language_in_body", "UNKNOWN"),
            "NO_GENERIC_TEMPLATE_ABUSE": "CONTENT_REVIEW_REQUIRED",
            "CHAPTER_SEMANTIC_ALIGNMENT": "CONTENT_REVIEW_REQUIRED",
            "EVIDENCE_GROUNDED_CLAIMS": "CONTENT_REVIEW_REQUIRED",
            "CENTRAL_CLAIM_CONTRACT": "PASS",
            "CENTRAL_CLAIM_CONTRACT_SCOPE": "STRUCTURAL_FIELDS_AND_BINDINGS_ONLY",
            "CATEGORY_SPECIFIC_NARRATIVE": "CONTENT_REVIEW_REQUIRED",
            "EDITORIAL_FIXTURE_IDENTITY": "PASS" if editorial_fixture else "NOT_SELECTED",
            "GOLDEN_SAMPLE_COVERAGE": "STRUCTURAL_COVERAGE_ONLY" if editorial_fixture and len(editorial_fixture.get("golden_sample_chapters", [])) >= 10 else "NOT_SELECTED",
            "DOCUMENT_CONTENT_REVIEW": "NOT_REVIEWED",
            "CHAPTER_COVERAGE": "PASS",
            "CHART_DATA_CONSISTENCY": "STATIC_CANONICAL_BINDING" if files["F01"].get("charts") else "NOT_APPLICABLE",
            "CANONICAL_IDENTITY": "PASS",
            "CANONICAL_DATA_CONSISTENCY": "STATIC_BINDING_CHECK",
            "D_BUSINESS_STYLE_REGRESSION": "NOT_TESTED_RENDER",
            "XLSX_CONTENT": "STATIC_STRUCTURE_CHECK",
            "PDF_RENDER": files["F02"].get("status", "UNKNOWN"),
            "VISUAL_REVIEW": "NOT_TESTED",
            "FOUR_FILE_GATE": "BLOCKED" if files["F02"].get("status") != "GENERATED" else "NOT_FORMAL_ACCEPTANCE",
        },
        "calculation_status": model.result["status"], "four_file_gate": "BLOCKED" if files["F02"].get("status") != "GENERATED" else "NOT_FORMAL_ACCEPTANCE",
        "editorial_mode": ("SYNTHETIC_DEMO" if editorial_fixture else
                           "SYNTHETIC_CALCULATION_PARTIAL" if str(model.result["project_id"]).startswith("SYNTHETIC")
                           and model.result["status"] == "PARTIAL" else "PARTIAL_CANONICAL"),
        "editorial_fixture": {"kind": editorial_fixture["evidence_kind"], "result_hash": editorial_fixture["result_hash"],
                              "golden_sample_chapters": editorial_fixture.get("golden_sample_chapters", [])}
        if editorial_fixture else None,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "not_decision_ready": True,
        "sensitive_raw_attachments_included": False,
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt["manifest"] = {"path": manifest_path.name, "size": manifest_path.stat().st_size, "sha256": _sha256(manifest_path)}
    return receipt


def export_rooftop_report(result: dict[str, Any], catalog, workspace: Workspace, output_dir: str, *, formula_map: dict[str, Any] | None = None,
                          editorial_fixture: dict[str, Any] | None = None) -> dict[str, Any]:
    return _export_report(result, catalog, workspace, output_dir, formula_map=formula_map,
                          expected_pv_type="industrial_rooftop", phase="PHASE5_INDUSTRIAL_ROOFTOP_REPORT_EXPORT",
                          editorial_fixture=editorial_fixture)


def export_ground_report(result: dict[str, Any], catalog, workspace: Workspace, output_dir: str, *, formula_map: dict[str, Any] | None = None,
                         editorial_fixture: dict[str, Any] | None = None) -> dict[str, Any]:
    return _export_report(result, catalog, workspace, output_dir, formula_map=formula_map,
                          expected_pv_type="utility_scale_ground", phase="PHASE6_UTILITY_SCALE_GROUND_REPORT_EXPORT",
                          editorial_fixture=editorial_fixture)
