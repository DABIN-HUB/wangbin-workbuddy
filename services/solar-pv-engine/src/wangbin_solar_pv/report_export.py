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
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
from importlib.resources import files
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
from docx.enum.section import WD_SECTION_START
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from openpyxl.chart import LineChart, Reference
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from PIL import Image, ImageDraw, ImageFont

from .calculation.result_contract import validate_result
from .errors import ContractError
from .local_files import Workspace
from .report_narrative import guidance, validate_fixture
from .report_numbering import heading_number, add_numbered_heading, validate_numbering
from .report_claims import APPENDIX_RULES, APPENDIX_TITLES, CHAPTER_FIELDS, CHAPTER_METRICS, RESOURCE_MONTHLY_UNITS, build_claim, category_fields, _dataset_rows, _source_value, _task_display_name
from .report_display_numbers import decision_number, decision_percent
from .report_equations import CONFLICT_ID, convert_equations
from .report_resource_display import prepare_resource_word_rows
from .report_word_styles import WORD_FORMAT, borders as word_table_borders, configure as configure_word, equation_paragraph, render_script_o_glyph, set_run_font
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
        "industrial_rooftop": "工商业屋顶光伏项目",
        "utility_scale_ground": "集中式地面光伏项目",
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

REPORT_CONTENT_VERSION = "phase7l-r10-reader-review"
READER_REPORT_CONTENT_VERSION = "phase7l-r11-reader-review"
REPORT_DISCLAIMER = "本报告内容仅供参考，正式使用时需根据实际情况调整。"
READER_FORMULA_IDS = frozenset({"F-NPV", "F-IRR-PROJECT", "F-STATIC-PAYBACK",
                                "F-DYNAMIC-PAYBACK", "F-LCOE", "F-DSCR"})
# Display aliases only: the frozen outline, stable IDs, and full export stay unchanged.
READER_ITEM_TITLES = {
    "CH05.06": "资源不确定性与资料比对",
    "CH14.06": "投资税费口径与单位造价",
    "CH15.05": "折旧、税费与年度汇总",
    "CH17.05": "敏感性方向与约束",
    "CH18.02": "结论依据与关键限制",
    "CH18.05": "后续决策节点与适用范围",
    "APP01.02": "重要输入与来源对照",
    "APP04.02": "投资范围与付款依据",
    "APP07.02": "无债务项目的偿债指标",
    "APP08.02": "情景阈值及影响方向",
    "APP13.01": "版本与测算身份",
    "APP13.02": "资料成熟度与适用范围",
}
READER_APPENDIX_LEADS = {
    "APP01": "示例输入及资料来源对照见下文和配套清单；权属、接网原件仍待核验。",
    "APP02": "十二个月的资源和电量按各自边界列示；气象资料的原始分量及授权仍须核实。",
    "APP03": "组件、逆变器和阵列布置采用示例参数；损失率按记录的顺序和适用边界列示。",
    "APP04": "投资分项区分建设期采购与后续更换；示例单价不是供应商正式报价。",
    "APP05": "运营付款、交易费用、折旧及税费分别列示；折旧不作为现金支出。",
    "APP06": "建设期和运营期的项目现金流逐期列示，不把项目净流量当成股东分配。",
    "APP07": "偿债指标须与实际融资和本息安排对照；无债务时不填造偿债比率。",
    "APP08": "尚无独立的单因素与组合情景结果，本节仅说明后续分析所需的资料。",
    "APP09": "适用的政策条款和有效期尚待逐项确认，不能据此推定项目已经获批。",
    "APP10": "权属、接网、工程量与报价等前提未闭合，所列事项不表示已经完成验收。",
    "APP11": "本节列示六项核心方法的可编辑公式；完整原始定义仍保留在配套词典。",
    "APP12": "此处只解释报告中常见的技术与财务术语，完整词典保留在配套清单。",
    "APP13": "本示例的测算身份可在配套工作簿逐项复核；资料成熟度仍不足以支持投资决定。",
}


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


def _word_money(value: Any) -> str:
    """Format CNY at two decimals without changing ledger values."""
    try:
        amount = Decimal(str(value).replace(",", ""))
        return (f"{amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):,.2f}"
                if amount.is_finite() else _word_value(value))
    except InvalidOperation:
        return _word_value(value)


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
    if re.fullmatch(r"SYNTHETIC-\d+Wp-MODEL-NOT-SUPPLIER", text):
        return "示例组件型号（非厂家数据表）"
    if re.fullmatch(r"SYNTHETIC-\d+kW-MODEL", text):
        return "示例逆变器型号（非厂家选型）"
    for source, label in (("GRID_DELIVERABLE", "电网可交付电量边界"),
                          ("Concept protection only; engineering review pending", "仅为概念性保护方案，待工程审查"),
                          ("FICTIONAL_NOT_APPROVED_METER_NODE", "仅用于合成测算的未审批计量点"),
                          ("SYNTHETIC-SAME-NODE-UNMETERED", "合成同节点计量标识，未装实际电表"),
                          ("SYNTHETIC-MODELED-8760H-LOAD-ONLY", "仅有8760小时合成负荷模型，非实测"),
                          ("SYNTHETIC-PLANNING-NOTE-NO-FIRE-APPROVAL", "合成规划备注，尚无消防批准"),
                          ("SYNTHETIC-PLANNING-NOTE-NO-STRUCTURAL-SIGNOFF", "合成规划备注，尚无结构专业签章"),
                          ("SYNTHETIC-PLANNING-NOTE-NO-GRID-OPINION", "合成规划备注，尚无正式电网接入意见"),
                          ("SYNTHETIC-PLANNING-NOTE-NO-PERMIT", "合成规划备注，尚无正式许可"),
                          ("AVAILABLE_PRE_CONSUMPTION", "消纳前可用电量口径"),
                          ("NOT_APPLICABLE", "不适用"),
                          ("ZERO_DEBT_SERVICE", "本期无应偿债务本息")):
        text = text.replace(source, label)
    text = re.sub(r"\bOPERATING_YEAR_(\d+)\b", lambda match: f"第{match.group(1)}年", text)
    return "待核验" if text.strip().casefold() == "pending" else text


def _word_metric_value(metric: dict[str, Any]) -> str:
    if metric.get("metric_id") == "financial.phase3e.project_irr":
        return _irr_presentation(metric)[0]
    if metric.get("status") != "CALCULATED":
        reason = str(metric.get("reason") or "未提供可用数值")
        return f"{metric.get('status', 'UNKNOWN')}：{reason[:180]}"
    return _word_value(metric.get("value"))

def _reader_metric_value(metric: dict[str, Any]) -> str:
    """Format a decision metric by its declared unit, never by its magnitude."""
    value = metric.get("value")
    if metric.get("status") != "CALCULATED" or isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return _word_metric_value(metric)
    return decision_number(value, _metric_unit(metric))

def _decision_metric_text(metric: dict[str, Any]) -> str:
    """Keep certified IRR roots and all other decision metrics on one display policy."""
    if metric.get("metric_id") == "financial.phase3e.project_irr":
        return _irr_presentation(metric)[0]
    return _reader_metric_value(metric)

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
        return decision_percent(roots[0]), f"单根；{bounds}唯一已认证根；年度项目税后口径"
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
                     "—" if irr else _metric_unit(metric),
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


def _chart_font_candidates() -> tuple[Path, ...]:
    """Use installed local fonts rather than the default font's tofu boxes."""
    windows = Path(os.getenv("WINDIR", "C:/Windows")) / "Fonts"
    return (windows / "simsun.ttc", windows / "msyh.ttc", windows / "simhei.ttf",
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
            Path("/System/Library/Fonts/PingFang.ttc"))


def _chart_fonts(labels: tuple[str, str, str]) -> tuple[dict[str, ImageFont.FreeTypeFont], dict[str, Any]]:
    """Refuse a chart when any required character renders as a missing glyph."""
    glyphs = set("".join(labels)) - {" "}
    for path in _chart_font_candidates():
        if not path.is_file():
            continue
        try:
            fonts = {name: ImageFont.truetype(str(path), size)
                     for name, size in (("title", 28), ("label", 22), ("tick", 22))}
            title_font = fonts["title"]
            missing = title_font.getmask("\U0010ffff")
            missing_shape = missing.size, bytes(missing)
            if any(mask.getbbox() is None or (mask.size, bytes(mask)) == missing_shape
                   for char in glyphs for mask in (title_font.getmask(char),)):
                continue
        except (OSError, ValueError):
            continue
        return fonts, {"path": str(path), "family": title_font.getname()[0],
                       "glyphs_checked": len(glyphs), "title_size_px": 28}
    raise ContractError("REPORT_CHART_FONT_GLYPHS_MISSING")


def _chart_png(spec: dict[str, Any], *, font_metadata: dict[str, Any] | None = None) -> BytesIO:
    """Render one canonical series as a small, dependency-local PNG."""
    width, height = 1200, 500
    image = Image.new("RGB", (width, height), f"#{_D_STYLE['white']}")
    draw = ImageDraw.Draw(image)
    title, x_label, y_label = _chart_axis_labels(spec)
    fonts, selected = _chart_fonts((title, x_label, y_label))
    western_candidates = (Path(os.getenv("WINDIR", "C:/Windows")) / "Fonts" / "times.ttf",
                          Path("/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf"),
                          Path("/Library/Fonts/Times New Roman.ttf"))
    western_path = next((candidate for candidate in western_candidates if candidate.is_file()), None)
    if western_path is None:
        raise ContractError("REPORT_CHART_WESTERN_FONT_MISSING")
    western = {name: ImageFont.truetype(str(western_path), font.size)
               for name, font in fonts.items()}
    selected["western_path"] = str(western_path)
    selected["western_family"] = western["title"].getname()[0]
    if font_metadata is not None:
        font_metadata.update(selected)
    def draw_mixed(xy, text, role):
        x, y = xy
        for segment in re.findall(r"[\x00-\x7f]+|[^\x00-\x7f]+", text):
            font = western[role] if segment.isascii() else fonts[role]
            draw.text((x, y), segment, fill="#000000", font=font)
            x += draw.textlength(segment, font=font)
        return x - xy[0]

    draw_mixed((86, 15), title, "title")
    draw_mixed((86, 52), y_label, "label")
    left, top, right, bottom = 98, 100, width - 36, height - 68
    label_width = sum(draw.textlength(part, font=western["label"] if part.isascii() else fonts["label"])
                      for part in re.findall(r"[\x00-\x7f]+|[^\x00-\x7f]+", x_label))
    draw_mixed(((left + right - label_width) // 2, height - 30), x_label, "label")
    values = spec["values"]
    ticks, y_values = _chart_axis_geometry(values, top=top, bottom=bottom)
    for tick, y in ticks:
        draw.line((left, y, right, y), fill="#D0D0D0", width=1)
        draw_mixed((8, y - 9), f"{tick:,.0f}", "tick")
    draw.line((left, top, left, bottom), fill="#000000", width=2)
    draw.line((left, bottom, right, bottom), fill="#000000", width=2)
    step = (right - left) / max(1, len(values) - 1)
    points = []
    for index, y in enumerate(y_values):
        x = int(left + index * step)
        points.append((x, y))
        if len(values) <= 12 or index == 0 or (index + 1) % 5 == 0 or index == len(values) - 1:
            label = str(index + 1).zfill(2)
            draw_mixed((x - 10, bottom + 12), label, "tick")
    draw.line(points, fill="#000000", width=4, joint="curve")
    for x, y in points:
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill="#FFFFFF", outline="#000000", width=2)
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


def _appendix_formula_definitions(model: ReportModel) -> list[dict[str, Any]]:
    """List the frozen registry without marking unreferenced formulas executed."""
    if model.catalog is None:
        return _formula_definitions(model)
    if model.result.get("formula_snapshot", {}).get("definition_hash") != model.catalog.definition_hash:
        raise ContractError("REPORT_FORMULA_DEFINITION_IDENTITY_MISMATCH")
    return [model.catalog.formulas[fid] for fid in sorted(model.catalog.formulas)]


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


def _formula_dimensional_text(formula: dict[str, Any]) -> str:
    """Only explain operations visible in this equation; shared source text is indexed separately."""
    equation = formula.get("text_equation") or formula.get("latex") or ""
    checks = []
    if "×" in equation or "\\cdot" in equation:
        checks.append("乘法应逐项核对因子单位与乘积单位")
    if "/" in equation or "\\frac" in equation:
        checks.append("除法应核对分子/分母单位与非零分母")
    if "^" in equation:
        checks.append("幂运算应核对底数与指数的量纲及定义域")
    if "Σ" in equation or "\\sum" in equation:
        checks.append("求和应核对索引范围及各项结果单位")
    if "{" in equation and "}" in equation:
        checks.append("结果集合应核对元素单位与求根定义域，不当作单个标量")
    return "；".join(checks) + "。" if checks else ""


def _formula_dimensional_contracts(definitions: list[dict[str, Any]]) -> tuple[list[str], dict[str, int]]:
    """Index identical effective contracts, without merging formula-local notation."""
    texts: list[str] = []
    indices: dict[str, int] = {}
    for formula in definitions:
        if formula.get("dimensional_check"):
            text = _formula_contract_text(formula["dimensional_check"])
            if text not in indices:
                indices[text] = len(texts) + 1
                texts.append(text)
    return texts, indices


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


def _formula_status(model: ReportModel, fid: str, *, reader_language: bool = False) -> str:
    metrics = [m for m in model.metrics if m.get("formula_id") == fid]
    if not metrics:
        return "仅作方法说明；本项目未引用或执行"
    calculated = sum(m.get("status") == "CALCULATED" for m in metrics)
    blocked = sum(str(m.get("status", "")).startswith("BLOCKED") for m in metrics)
    inapplicable = sum(m.get("status") == "NOT_APPLICABLE" for m in metrics)
    unimplemented = sum(m.get("status") == "NOT_IMPLEMENTED" for m in metrics)
    historical_placeholder = sum(m.get("reason") == "OUTSIDE_PHASE3B"
                                 for m in metrics if m.get("status") == "NOT_IMPLEMENTED")
    unimplemented -= historical_placeholder
    undefined = sum(m.get("status") == "UNDEFINED" for m in metrics)
    unknown = len(metrics) - calculated - blocked - inapplicable - unimplemented - historical_placeholder - undefined
    states = (("已计算", calculated), ("尚无可用结果" if reader_language else "阻断", blocked),
              ("不适用", inapplicable),
              ("其他评价口径未测算" if reader_language else "早期阶段留置占位", historical_placeholder),
              ("当前方法尚无计算结果" if reader_language else "方法未实现", unimplemented),
              ("数学未定义", undefined), ("待核对", unknown))
    return "本次引用；" + "、".join(f"{name}{count}项" for name, count in states if count) + "。"


def _glossary_common_boundaries(terms: list[dict[str, Any]]) -> dict[str, str]:
    counts = Counter(term.get("distinction_and_boundary", "") for term in terms)
    common: dict[str, str] = {}
    for term in terms:
        text = term.get("distinction_and_boundary", "")
        if text and counts[text] > 1 and text not in common:
            common[text] = f"B{len(common) + 1:02d}"
    return common


def _reader_glossary_ids(pv_type: str) -> tuple[str, ...]:
    """Reader index only; the frozen complete glossary still follows it in APP12."""
    common = ("TERM-PV", "TERM-DC", "TERM-AC", "TERM-KWP", "TERM-POWER", "TERM-ENERGY",
              "TERM-POA-IRRADIATION", "TERM-PR", "TERM-CAPEX", "TERM-OPEX", "TERM-NPV",
              "TERM-IRR", "TERM-PROJECT-CASH-FLOW", "TERM-EQUITY-CASH-FLOW", "TERM-LCOE",
              "TERM-WORKING-CAPITAL", "TERM-DEPRECIATION", "TERM-VAT", "TERM-TMY")
    rooftop = ("TERM-SELF-CONSUMPTION", "TERM-EXPORT-LIMIT", "TERM-PPA", "TERM-LOAD", "TERM-GHI-IRRADIATION")
    ground = ("TERM-CURTAILMENT", "TERM-EXPORT-LIMIT", "TERM-GHI-IRRADIATION",
              "TERM-LEVERED", "TERM-DSCR")
    return common + (rooftop if pv_type == "industrial_rooftop" else ground)

def _debt_source_state(model: ReportModel) -> str:
    normalized = model.result.get("inputs", {}).get("normalized", {})
    records = model.result.get("source_snapshot", {}).get("phase2", {}).get("records", ())
    ratio = _source_value(normalized, records, "finance.debt_ratio")
    if type(ratio) not in {int, float, Decimal}:
        return "UNKNOWN"
    value = Decimal(str(ratio))
    return "NO_DEBT" if value == 0 else "HAS_DEBT" if value > 0 else "UNKNOWN"


def _dscr_reader_note(model: ReportModel, debt_state: str) -> str:
    if (model.metric("financial.phase3e.dscr") or {}).get("status") == "CALCULATED":
        return "DSCR已有计算值，仍须逐期核对可偿债现金与应偿本息。"
    if debt_state == "NO_DEBT":
        return "本次无应偿本息，DSCR无定义而不是0倍。"
    if debt_state == "HAS_DEBT":
        return "本次有债务假设但DSCR无可用值，须核对偿债计划与零分母期。"
    return "债务比例与偿债日程尚未闭合，不推定DSCR为0倍或已达标。"


def _formula_reader_evaluation(model: ReportModel) -> str:
    npv_calculated = (model.metric("financial.phase3e.project_npv") or {}).get("status") == "CALCULATED"
    irr_calculated = (model.metric("financial.phase3e.project_irr") or {}).get("status") == "CALCULATED"
    return ("评价与适用：NPV（F-NPV）按声明折现率汇总项目税后现金流；本项目"
            + ("已有可用NPV计算值" if npv_calculated else "NPV尚无可用计算值")
            + "。IRR（F-IRR-PROJECT）仅按搜索域内认证根呈现；本项目"
            + ("已有IRR计算结果" if irr_calculated else "IRR尚无可用计算值")
            + "。静态与动态回收期（F-STATIC-PAYBACK、F-DYNAMIC-PAYBACK）是不同评价方法，"
              "各自是否取得数值以指标状态为准。LCOE（F-LCOE）："
            + _reader_term_applicability(model, "TERM-LCOE")
            + "DSCR（F-DSCR）：" + _dscr_reader_note(model, _debt_source_state(model))
            + "项目回报不等于股东回报。")


def _npv_instances_note(model: ReportModel, outputs: list[dict[str, Any]]) -> str:
    project = model.metric("financial.phase3e.project_npv")
    if project and project.get("status") == "CALCULATED":
        return "本项目净现值已按项目税后现金流测算；其他评价口径是否适用，须分别核对现金流和折现条件。"
    return "本项目净现值尚无可用结果；须补齐项目现金流及折现条件后再评价。"


def _reader_term_applicability(model: ReportModel, term_id: str) -> str:
    """Reader navigation only; never claim that a listed method was executed."""
    def calculated(metric_id: str) -> bool:
        return (model.metric(metric_id) or {}).get("status") == "CALCULATED"

    common = {
        "TERM-PV": "本报告评价光伏方案，不代表工程设计已获批。",
        "TERM-DC": "本项目直流装机与交流送出容量分别列示。",
        "TERM-AC": "逆变输出与电网接入条件仍须分别校核。",
        "TERM-KWP": "本项目直流装机按峰值容量列示。",
        "TERM-POWER": "设备额定功率与实际发电量分列。",
        "TERM-ENERGY": "发电量、可交付电量与上网电量按边界分列。",
        "TERM-POA-IRRADIATION": "本次阵列面资源为合成输入，尚待站址核验。",
        "TERM-PR": "首年性能比是模型结果，尚无实测运行值。",
        "TERM-CAPEX": "首期投资与后续设备更换分别列账，非已付款。",
        "TERM-OPEX": "年度运维支出与非现金折旧分别列账。",
        "TERM-NPV": ("项目税后净现值仅在本次输入与折现假设边界下成立。" if calculated("financial.phase3e.project_npv")
                     else "项目净现值尚未形成可用结果，不将方法定义当作已计算值。"),
        "TERM-IRR": ("项目IRR已有计算结果，根集唯一性须单独核对；不等于股东回报。"
                     if calculated("financial.phase3e.project_irr") else
                     "项目IRR尚无可用计算值，不能据此推定项目或股东回报。"),
        "TERM-PROJECT-CASH-FLOW": "建设与运营年度项目收支见现金流附录。",
        "TERM-EQUITY-CASH-FLOW": ("投资者现金流已有计算值，仍须核对出资、融资与分配事件。"
                                  if calculated("financial.phase3e.equity-investor-cash-flow") else
                                  "投资者现金流尚无可用计算值，不以项目现金流替代股东回报。"),
        "TERM-LCOE": ("LCOE已有计算值，仍须核对全期成本与可交付电量边界。"
                      if calculated("financial.phase3e.lcoe") else
                      "LCOE尚无可用数值，须核对全期成本、电量与折现边界。"),
        "TERM-WORKING-CAPITAL": "本项目现金流分别列示占用与终期回收。",
        "TERM-DEPRECIATION": "折旧影响税基，不当作第二次现金付款。",
        "TERM-VAT": "税金计提与现金付款分别列示，实际适用税率待核。",
        "TERM-TMY": "本报告涉及气象方法，不表示已取得完整实测典型年。",
        "TERM-EXPORT-LIMIT": "接入与可送出限额仍须正式电网意见核定。",
        "TERM-GHI-IRRADIATION": "本次资源为合成输入，真实站址资料仍待核。",
    }
    rooftop = {
        "TERM-SELF-CONSUMPTION": "屋顶方案按合成厂区负荷预测自用，真实比例待核。",
        "TERM-PPA": "本项目仍缺真实签署的购售电和结算协议。",
        "TERM-LOAD": "厂区负荷为合成模型，不是实际计量记录。",
    }
    ground = {"TERM-CURTAILMENT": "地面方案的送出约束为合成假设，须电网核定。"}
    if term_id in {"TERM-LEVERED", "TERM-DSCR"}:
        debt_state = _debt_source_state(model)
        ground.update({
            "TERM-LEVERED": ("本次登记无债务，不将项目回报写成融资后股东回报。" if debt_state == "NO_DEBT" else
                             "本次有债务假设，须核对提款和本息；项目回报不能替代股东回报。" if debt_state == "HAS_DEBT" else
                             "债务比例尚未获得来源绑定，不能推定无债务或融资后回报。"),
            "TERM-DSCR": _dscr_reader_note(model, debt_state),
        })
    category = rooftop if model.result["pv_type"] == "industrial_rooftop" else ground
    return category.get(term_id) or common[term_id]


def _appendix_rows(model: ReportModel, app_id: str) -> tuple[list[str], list[list[Any]]]:
    definitions = _appendix_formula_definitions(model) if app_id in {"APP11.01", "APP11.02"} else []
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
        terms = json.loads(files("wangbin_solar_pv").joinpath("report-glossary.json").read_text(encoding="utf-8"))["terms"]
        if (len(terms) != len({term["term_id"] for term in terms})
                or any(not term.get("chinese_name") or not term.get("english_name")
                       or not term.get("definition_zh") for term in terms)):
            raise ContractError("REPORT_GLOSSARY_INCOMPLETE")
        introductory = {"PV": 0, "DC": 1, "AC": 2}
        terms.sort(key=lambda term: (0, introductory[term["abbreviation"]])
                   if term.get("abbreviation") in introductory else (1, 0))
        common = _glossary_common_boundaries(terms)
        rows = []
        for term in terms:
            definition = term["definition_zh"]
            if (definition.startswith("该计算方法的定义、符号、输入输出及异常边界见 ")
                    and "；" in definition):
                # The full registry definition stays in the versioned JSON; the
                # individual engineering distinction is easier to read here.
                definition = definition.split("；", 1)[1]
            boundary = term.get("distinction_and_boundary", "")
            if term["term_id"] in {"TERM-HASH", "TERM-BIPV"}:
                boundary = "原词典历史说明另列"
            elif boundary in common:
                boundary = "共通边界" + common[boundary]
            rows.append([term["chinese_name"], term["english_name"], term.get("abbreviation") or "无缩写",
                         definition, (term.get("unit_or_dimension") or "—") + "；" + boundary])
        return ["中文", "English", "缩写", "读者释义", "单位及核查边界"], rows
    if app_id == "APP12.02":
        return ["单位/符号", "含义", "不得混用的边界"], [
            ["kWp", "直流峰值千瓦", "不等于 kWac"], ["kWac", "交流额定千瓦", "不等于 kWh"],
            ["kWh", "电量千瓦时", "不等于辐照量 kWh/㎡"], ["kWh/㎡", "单位面积辐照量", "不等于交付电量"],
            ["W/㎡", "瞬时单位面积辐照度", "不是按月累计的kWh/㎡"],
            ["kVA", "视在容量", "不能不经功率因数与电网意见换算为可接入kW"],
            ["V", "电压伏特", "标称串电压与低温开路电压、MPPT窗口分别验证"],
            ["A", "电流安培", "组件短路电流与逆变器输入电流分别校核"],
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
        fee_source = model.result.get("evidence", {}).get("financial-ledger", {}).get("trading_fee_payment")
        if fee_source:
            for entry in model.result["evidence"]["financial-ledger"]["annual"][1:]:
                for key, label in (("transaction_cost_accrued", "3C交易费本期计提"),
                                   ("transaction_cost_payable_opening", "交易费期初应付"),
                                   ("transaction_cost_cash_paid", "交易费预计支付"),
                                   ("transaction_cost_payable_closing", "交易费期末应付")):
                    value = entry[key]
                    rows.append([entry["period"] + "." + key, "ASSUMED", value, "CNY",
                                 "TRADING_FEE_PAYMENT_SOURCE/1.0", fee_source["source_id"],
                                 label + "；合成年度预测，非真实付款", _raw_value(value)])
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


def _add_table(document: Document, headers: list[str], rows: list[list[Any]], caption: str | None = None,
               *, widths_cm: tuple[float, ...] | None = None,
               nowrap_columns: tuple[int, ...] = (),
               layout_type: str = "TECHNICAL_DETAIL_TABLE",
               continuation_identity: bool = False) -> None:
    """Use a bounded portrait layout; never silently squeeze a wide ledger into equal columns."""
    reader_preview = getattr(document, "_solar_reader_preview", False)
    layouts = {"SUMMARY_TABLE", "PLAN_TABLE", "FINANCIAL_TABLE", "ANNUAL_LEDGER_TABLE",
               "TECHNICAL_DETAIL_TABLE", "ISSUE_TABLE"}
    if layout_type not in layouts or any(len(row) != len(headers) for row in rows):
        raise ContractError("REPORT_WORD_TABLE_LAYOUT")
    if len(headers) > 6 and layout_type in {"FINANCIAL_TABLE", "ANNUAL_LEDGER_TABLE", "ISSUE_TABLE"}:
        raise ContractError("REPORT_WORD_TABLE_TOO_WIDE")
    table_number = len(document.tables) + 1
    if caption:
        paragraph = document.add_paragraph(f"表{table_number} {caption.rstrip('。；：,.、 ')}", style="Caption")
        paragraph.paragraph_format.keep_with_next = True
    table = document.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    if widths_cm is not None and len(widths_cm) != len(headers):
        raise ContractError("REPORT_WORD_TABLE_WIDTHS")
    if widths_cm is None:
        weights = [max(4, min(18, len(str(header)))) for header in headers]
        for column in range(len(headers)):
            if layout_type == "ANNUAL_LEDGER_TABLE" and column == 0:
                weights[column] = 7
            elif layout_type in {"FINANCIAL_TABLE", "ANNUAL_LEDGER_TABLE"}:
                weights[column] = max(weights[column], 12 if column else 9)
            elif layout_type == "ISSUE_TABLE":
                weights[column] = max(weights[column], 12)
        widths = tuple(WORD_FORMAT.text_width_cm * weight / sum(weights) for weight in weights)
    else:
        widths = tuple(widths_cm)
    scale = min(1.0, WORD_FORMAT.text_width_cm / sum(widths))
    widths = tuple(width * scale for width in widths)
    if min(widths) < 1.35 and layout_type != "TECHNICAL_DETAIL_TABLE":
        raise ContractError("REPORT_WORD_TABLE_NARROW_COLUMN")
    tbl_pr = table._tbl.tblPr
    layout = tbl_pr.first_child_found_in("w:tblLayout")
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tbl_pr.append(layout)
    layout.set(qn("w:type"), "fixed")
    for column, width in enumerate(widths):
        table.columns[column].width = Cm(width)
    tbl_w = tbl_pr.first_child_found_in("w:tblW")
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.insert(0, tbl_w)
    tbl_w.set(qn("w:w"), str(int(sum(widths) * 567)))
    tbl_w.set(qn("w:type"), "dxa")
    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        # The repeating header must contain only the actual column label.
        cell.text = _string(header)
        cell.width = Cm(widths[index])
        if layout_type == "ANNUAL_LEDGER_TABLE" and index > 0:
            cell._tc.get_or_add_tcPr().append(OxmlElement("w:noWrap"))
        for paragraph in cell.paragraphs:
            paragraph.style = "Solar Table"
            paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
            paragraph.paragraph_format.keep_with_next = False
            for run in paragraph.runs:
                set_run_font(run, size=WORD_FORMAT.table_pt, bold=True)

    header_pr = table.rows[0]._tr.get_or_add_trPr()
    header_pr.append(OxmlElement("w:tblHeader"))
    header_pr.append(OxmlElement("w:cantSplit"))
    for cell in table.rows[0].cells:
        for paragraph in cell.paragraphs:
            paragraph.paragraph_format.keep_with_next = True
    for row_index, row in enumerate(rows):
        cells = table.add_row().cells
        for index, value in enumerate(row):
            monetary = reader_preview and ((layout_type == "ANNUAL_LEDGER_TABLE" and index > 0)
                                           or "（元）" in headers[index])
            cells[index].text = (_word_money(value) if monetary and re.fullmatch(
                r"[−-]?[\d,]+(?:\.\d+)?", str(value).strip()) else _string(value))
            cells[index].width = Cm(widths[index])
            numeric = (isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)) or bool(
                re.fullmatch(r"[−-]?[\d,]+(?:\.\d+)?%?", str(value).strip()))
            if index in nowrap_columns or (numeric and
                                           (monetary or layout_type in {"FINANCIAL_TABLE", "ANNUAL_LEDGER_TABLE"})):
                cells[index]._tc.get_or_add_tcPr().append(OxmlElement("w:noWrap"))
            cells[index].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
            for paragraph in cells[index].paragraphs:
                paragraph.style = "Solar Table"
                paragraph.alignment = (WD_ALIGN_PARAGRAPH.RIGHT if numeric and
                                       (monetary or layout_type in {"FINANCIAL_TABLE", "ANNUAL_LEDGER_TABLE", "SUMMARY_TABLE"})
                                       else WD_ALIGN_PARAGRAPH.LEFT)
                if (row_index == 0 and len(rows) > 1 or
                        reader_preview and layout_type == "FINANCIAL_TABLE" and
                        len(rows) <= 10 and row_index < len(rows) - 1):
                    paragraph.paragraph_format.keep_with_next = True
                for run in paragraph.runs:
                    set_run_font(run, size=WORD_FORMAT.table_pt)
        tr_pr = cells[0]._tc.getparent().get_or_add_trPr()
        tr_pr.append(OxmlElement("w:cantSplit"))
    word_table_borders(table)



def _chart_interpretation(model: ReportModel, spec: dict[str, Any]) -> str:
    """Explain only patterns supported by this series and its bound inputs."""
    values = spec["values"]
    fmt = _word_number
    if spec["metric_id"] == "energy.monthly.year.1":
        records = model.result.get("source_snapshot", {}).get("phase2", {}).get("records", ())
        months = _source_value(model.result["inputs"].get("normalized", {}), records, "resource.monthly")
        days = ({row.get("fields", {}).get("resource.monthly.month"):
                 row.get("fields", {}).get("resource.monthly.days") for row in months}
                if isinstance(months, list) and len(months) == 12 else {})
        peak, low = max(range(12), key=values.__getitem__), min(range(12), key=values.__getitem__)
        comparison = (f"首年合成月序列中，第{peak + 1}月为{fmt(values[peak])}kWh，"
                      f"第{low + 1}月为{fmt(values[low])}kWh。")
        if len(days) == 12 and all(type(days.get(i)) is int and days[i] > 0 for i in range(1, 13)):
            daily = [Decimal(str(value)) / days[i] for i, value in enumerate(values, 1)]
            if max(daily) - min(daily) <= max(abs(max(daily)), Decimal(1)) * Decimal("1e-9"):
                return comparison + "各月日均预测接近，月合计差异主要来自合成月份的天数，不代表当地资源季节性。"
        return comparison + "月间差异仍须结合逐月资源、天数与损失输入解释，不推断当地实测季节规律。"
    peak, low = max(range(len(values)), key=values.__getitem__), min(range(len(values)), key=values.__getitem__)
    text = (f"年度合成预测从第1年{fmt(values[0])}kWh变化至第{len(values)}年"
            f"{fmt(values[-1])}kWh；最高在第{peak + 1}年，最低在第{low + 1}年。")
    records = model.result.get("source_snapshot", {}).get("phase2", {}).get("records", ())
    normalized = model.result["inputs"].get("normalized", {})
    degradation = _source_value(normalized, records, "system.annual_degradation")
    if degradation is not None:
        text += f"年度变化包含{fmt(Decimal(str(degradation)) * 100)}%的衰减假设。"
    replacements = _source_value(normalized, records, "assets.replacements")
    if isinstance(replacements, list):
        for row in replacements:
            fields = row.get("fields", {})
            year = fields.get("assets.replacements.year")
            if type(year) is not int or not 1 < year < len(values):
                continue
            metric = model.metric(f"energy.year.{year}") or {}
            performance = metric.get("details", {}).get("performance", {}) if metric.get("status") == "CALCULATED" else {}
            event = performance.get("event") or {}
            if (event.get("asset_id") == fields.get("assets.replacements.asset_id")
                    and event.get("downtime_days") == fields.get("assets.replacements.downtime_days")):
                text += (f"第{year}年计划更换计入{event['downtime_days']}天停机，当年预测{fmt(values[year - 1])}kWh，"
                         f"第{year + 1}年{fmt(values[year])}kWh；停机结束后的回升不能解释为组件性能恢复。")
            break
    return text + "这条曲线不是实际运行记录。"


def _add_canonical_charts(document: Document, model: ReportModel, specs: list[dict[str, Any]], source_map: dict[str, str],
                          heading: str | None = None) -> list[dict[str, Any]]:
    """Embed visual evidence only when canonical chart specs are valid."""
    if not specs:
        return []
    if heading:
        document.add_paragraph(heading, style="Solar Figure Group")
    receipts = []
    for spec in specs:
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        font_metadata: dict[str, Any] = {}
        paragraph.add_run().add_picture(_chart_png(spec, font_metadata=font_metadata), width=Cm(WORD_FORMAT.text_width_cm))
        figure_no = len([p for p in document.paragraphs if p.style.name == "Caption" and p.text.startswith("图")]) + 1
        document.add_paragraph(f"图{figure_no} {spec['title'].rstrip('。；：,.、 ')}", style="Caption")
        document.add_paragraph(_chart_interpretation(model, spec))
        receipts.append({"metric_id": spec["metric_id"], "points": len(spec["values"]),
                         "source": "CANONICAL", "formula_id": spec["formula_id"],
                         "source_ids": list(spec["source_ids"]), "format": "PNG_EMBEDDED",
                         "font": font_metadata})
    return receipts


def _add_toc(document: Document) -> None:
    """A real, refreshable Word TOC with no made-up cached page numbers."""
    paragraph = document.add_paragraph(style="TOC 1")
    paragraph.paragraph_format.space_after = Pt(6)
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar"); begin.set(qn("w:fldCharType"), "begin"); begin.set(qn("w:dirty"), "true")
    instruction = OxmlElement("w:instrText"); instruction.set(qn("xml:space"), "preserve"); instruction.text = 'TOC \\o "1-3" \\h \\z \\u'
    separate = OxmlElement("w:fldChar"); separate.set(qn("w:fldCharType"), "separate")
    run._r.extend((begin, instruction, separate))
    end = OxmlElement("w:fldChar"); end.set(qn("w:fldCharType"), "end")
    paragraph.add_run()._r.append(end)
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
    fee_snapshot = model.result.get("source_snapshot", {}).get("trading_fee_payment")
    fee_evidence = model.result.get("evidence", {}).get("financial-ledger", {}).get("trading_fee_payment")
    if fee_snapshot and fee_evidence:
        fee_source_id = fee_snapshot["contract"]["source"]["source_id"]
        if (fee_evidence.get("source_id") != fee_source_id or
                fee_evidence.get("raw_sha256") != fee_snapshot.get("raw_sha256")):
            return True
        known_sources.add(fee_source_id)
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
    "financial.unit_investment": "全期含更换CAPEX单位直流投资",
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
    "revenue.year.1": "首年预测经济收益或售电收入",
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
        "age": "已使用年限", "azimuth": "方位角", "design_added_load": "设计附加荷载",
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


def _professional_metric_rows(model: ReportModel, metric_ids: tuple[str, ...],
                              *, reader_preview: bool = False) -> list[list[str]]:
    """Show only explicitly selected, named decision metrics; keep the full ledger in Excel."""
    rows = []
    for metric_id in metric_ids:
        metric = model.metric(metric_id)
        if metric is None:
            continue
        status = metric.get("status", "UNKNOWN")
        if metric_id == "financial.phase3e.project_irr" and status in {"CALCULATED", "UNDEFINED"}:
            display, roots_note = _irr_presentation(metric)
            note = "项目税后年度口径，非股东回报" if status == "CALCULATED" else f"项目税后年度现金流；{roots_note}"
        elif status == "CALCULATED":
            display = ("逐期详见附录F及测算模型 M14（含建设期）"
                       if reader_preview and metric_id == "financial.phase3e.project_cash_flow"
                       else _decision_metric_text(metric))
            note = {
                "financial.capex.total": "含后期更换，不等于建设期付款",
                "financial.phase3e.project_npv": "项目税后；折现率见正文",
                "revenue.year.1": "含自用节费与余电销售" if model.result.get("pv_type") == "industrial_rooftop" else "仅上网销售收入",
            }.get(metric_id, "")
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
                    "缺投资门槛及其计量单位" if reader_preview and metric_id == "financial.phase3e.investment-hurdle-gap" else
                    "缺用户投资门槛" if metric_id == "financial.phase3e.investment-hurdle-gap" else
                    str(metric.get("reason") or "必要现金事件或方法依据尚未闭合")[:160])
        elif status == "NOT_APPLICABLE":
            display, note = "不适用", "本项目无对应债务或业务适用条件；具体依据见测算模型"
        elif status == "NOT_IMPLEMENTED":
            display, note = "方法尚未实现", "所需方法或计算接口未接通；不以缺输入替代说明"
        elif status == "UNDEFINED":
            display, note = "数学上未定义", "当前现金流/评价边界下无有效数值"
            if metric_id == "financial.phase3e.dscr" and metric.get("reason") == "ZERO_DEBT_SERVICE":
                note = ("本项目无债务，每期应偿本息为零；DSCR无定义，不是0倍" if
                        model.result["inputs"].get("normalized", {}).get("finance.debt_ratio") == 0 else
                        "存在应偿本息为零的期间；该期DSCR无定义，不是0倍")
        else:
            display, note = "状态待核对", "当前结果状态未知；不可当作不适用"
        unit = _metric_unit(metric)
        if reader_preview and metric_id == "financial.phase3e.investment-hurdle-gap" and status != "CALCULATED":
            unit = "待确定"
        label = (_metric_label(metric_id) if metric_id != "revenue.year.1" else
                 "首年预测上网销售收入" if model.result.get("pv_type") == "utility_scale_ground" else
                 "首年预测综合经济收益（自用节费＋余电销售）")
        if reader_preview and metric_id == "financial.capex.total":
            label = "全期资本支出（含更换）"
        rows.append([label, display,
                     "—" if metric_id.endswith("project_irr") and status in {"CALCULATED", "UNDEFINED"} else
                     "—" if status != "CALCULATED" and str(unit).startswith("集合") else
                     "比值" if unit == "1" else "元" if unit == "CNY" else "年" if unit == "year" else unit,
                     "全期含后期更换；直流kWp为分母，首建金额另列" if metric_id == "financial.unit_investment" and status == "CALCULATED" else note])
    return rows


def _project_summary(model: ReportModel) -> str:
    """Decision-facing overview; all amounts come from this canonical snapshot."""
    inputs = model.result["inputs"].get("normalized", {})
    ground = model.result["pv_type"] == "utility_scale_ground"

    def quantity(mid: str, unit: str) -> str | None:
        metric = model.metric(mid)
        return f"{_decision_metric_text(metric)} {unit}" if metric and metric.get("status") == "CALCULATED" else None

    dc, generation = quantity("dc_capacity", "kWp"), quantity("energy.year.1", "kWh")
    delivery = quantity("energy.delivered.year.1", "kWh")
    lead = (f"本项目拟利用厂房屋面建设{dc or '待定规模的'}光伏系统，发电后优先供厂区使用，余电上网。" if not ground else
            f"本项目拟建设{dc or '待定规模的'}地面光伏系统，按集中送出、全额上网方案评价。")
    if generation:
        lead += f"在当前测算条件下，首年预测发电{generation}。"
    if delivery and ground:
        lead += f"预计可交付电量{delivery}；交付预测仍须经电网接入及结算条件确认。"

    revenue = model.metric("revenue.year.1") or {}
    components = revenue.get("details", {}).get("ledger", {}) if revenue.get("status") == "CALCULATED" else {}
    if not ground and all(isinstance(components.get(key), (int, float, Decimal)) and not isinstance(components[key], bool)
                          for key in ("self_kwh", "self_value", "export_kwh", "export_sales_revenue")):
        value = lambda key, unit: f"{_reader_metric_value({'value': components[key], 'unit': unit, 'status': 'CALCULATED'})} {unit}"
        benefits = (f"首年预测自用{value('self_kwh', 'kWh')}，可减少购电支出{value('self_value', '元')}；"
                    f"余电上网{value('export_kwh', 'kWh')}，预计售电收入{value('export_sales_revenue', '元')}。"
                    "节费不属于售电回款，两项在现金流中分别处理。")
    elif ground and isinstance(components.get("export_sales_revenue"), (int, float, Decimal)):
        sales = _reader_metric_value({"value": components["export_sales_revenue"], "unit": "CNY", "status": "CALCULATED"})
        benefits = f"首年预计上网销售收入{sales} 元，实际回款取决于交易价格、计量与结算协议。"
    else:
        benefits = "售电或节费尚缺少可引用的分项结果，不能由预测发电量推算实际收入。"

    npv = quantity("financial.phase3e.project_npv", "元")
    irr = model.metric("financial.phase3e.project_irr") or {}
    irr_display, irr_note = _irr_presentation(irr) if irr else ("尚无结果", "")
    discount = inputs.get("finance.project_discount_rate")
    basis = (f"、折现率{_word_number(Decimal(str(discount)) * 100)}%" if isinstance(discount, (int, float, Decimal)) else "")
    if npv:
        years = inputs.get("project.evaluation_years")
        returns = f"按{years}年评价期{basis}的项目税后年度现金流测算，项目净现值（NPV）为{npv}。" if years else f"按项目税后年度现金流测算，项目净现值（NPV）为{npv}。"
        if irr.get("status") == "CALCULATED" and irr_display != "根集待核验":
            returns += f"内部收益率（IRR）为{irr_display}。"
        elif irr.get("status") == "UNDEFINED":
            returns += f"IRR{irr_display}；{irr_note}。"
        else:
            returns += "IRR尚未形成可供解读的单一数值。"
        returns += "这是当前假设下的项目回报，不等于股东回报或投资批准。"
    else:
        returns = "项目税后净现值尚未形成可引用结果，应先闭合现金流及对应评价条件。"
    assumptions = "上述电量、成本和结算均以当前登记的假设资料为基础，并非实际经营业绩；完整计算精度及来源见配套工作簿。"
    risks = ("厂房屋面权属和使用期限、结构荷载、防水消防、真实日间负荷及余电接入仍待核验。"
             if not ground else "土地使用条件、地勘与道路排水、集中送出及市场交易价格仍待核验。")
    if ground:
        ledger = model.result.get("evidence", {}).get("financial-ledger", {}).get("annual", [])
        renewals = [(row.get("period"), row.get("replacement_cash_paid")) for row in ledger[1:]
                    if isinstance(row.get("replacement_cash_paid"), (int, float, Decimal)) and row["replacement_cash_paid"]]
        if renewals:
            risks += "另需为" + "、".join(f"{_reader_text(str(period))}预计更换支出"
                                           f"{_reader_metric_value({'value': value, 'unit': 'CNY', 'status': 'CALCULATED'})} 元"
                                           for period, value in renewals) + "安排资金，不能将其当作首期投资。"
    advice = ("建议下一阶段先取得屋面权属和结构资料、厂区逐时用电记录及电网接入意见，再更新工程量与收益测算。"
              if not ground else "建议下一阶段先落实用地与地勘、场区道路排水及接网方案，并以可执行交易价格更新测算。")
    return "\n\n".join((lead + benefits, returns, assumptions + risks, advice))


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


def _r4_special_narrative(model: ReportModel, pv_type: str, chapter_id: str,
                          item_no: int) -> str | None:
    """Return evidence-backed R4 prose for the high-stakes engineering items.

    These paragraphs intentionally stay in the presentation layer.  They read
    canonical inputs, ledger events and metric details but never repair, round
    or recompute the frozen calculation result.
    """
    normalized = model.result["inputs"].get("normalized", {})
    ground = pv_type == "utility_scale_ground"

    def number(value: Any) -> str:
        return _word_number(value) if value is not None else "UNKNOWN"

    if chapter_id == "CH05" and item_no == 2:
        rows = normalized.get("resource.monthly")
        values = [row.get("fields", {}) for row in rows] if isinstance(rows, list) else []
        complete = len(values) == 12 and all(
            all(isinstance(fields.get(f"resource.monthly.{key}"), (int, float, Decimal))
                and not isinstance(fields.get(f"resource.monthly.{key}"), bool)
                for key in ("ghi", "dni", "dhi", "poa"))
            for fields in values)
        additive = complete and all(
            abs(Decimal(str(fields["resource.monthly.ghi"]))
                - Decimal(str(fields["resource.monthly.dni"]))
                - Decimal(str(fields["resource.monthly.dhi"]))) <= Decimal("0.000001")
            for fields in values)
        energy = model.metric("energy.year.1") or {}
        poa = energy.get("details", {}).get("poa_kwh_m2")
        pattern = ("当前12个月合成表逐月满足GHI=DNI+DHI；这只是现有录入值的数值模式，"
                   "不是可普遍采用的物理恒等式。GHI为水平面期间辐照量，DNI为法向直射期间辐照量，"
                   "DHI为水平面散射期间辐照量，三者不能在未给出太阳天顶角、时间积分和投影关系时直接相加。"
                   if additive else
                   "当前月度表未呈现可直接验证的GHI、DNI、DHI简单相加模式；仍须按原始时间序列和投影关系核对。")
        return (pattern + f"本次发电链消费的是阵列面POA辐照量及其时间积分，首年能量记录的POA为{number(poa)} kWh/㎡；"
                "由于现有输入为合成月度汇总且缺少逐时太阳位置/质量控制证据，不能据此宣称DNI法向口径或资源代表性已经通过。")

    if chapter_id in {"CH06", "CH07"} and item_no in ({3} if chapter_id == "CH06" else {1, 3}):
        dc = model.value("dc_capacity")
        ac = model.value("ac_capacity")
        count = normalized.get("system.module_count")
        power = normalized.get("system.module_power")
        per_string = normalized.get("system.modules_per_string")
        strings = normalized.get("system.parallel_strings")
        voc = normalized.get("system.module_voc")
        nominal_string = (Decimal(str(per_string)) * Decimal(str(voc))
                          if isinstance(per_string, (int, float, Decimal))
                          and isinstance(voc, (int, float, Decimal)) else None)
        ratio = (Decimal(str(dc)) / Decimal(str(ac))
                 if isinstance(dc, (int, float, Decimal)) and isinstance(ac, (int, float, Decimal)) and ac else None)
        if chapter_id == "CH06":
            return (f"当前{('地面集中式' if ground else '屋顶')}方案为{number(dc)} kWp直流、{number(ac)} kWac交流，"
                    f"容配比约{number(ratio)}；该比例说明直流阵列相对逆变器存在名义裕量，"
                    "只能用于方案边界比较，不能替代并网容量和限发校核。")
        if item_no == 1:
            return (f"设备配置为{number(count)}块×{number(power)} Wp组件，"
                    f"{number(strings)}串、每串{number(per_string)}块，组件名义开路电压{number(voc)} V。"
                    "这些参数与直流装机的数量关系一致，属于当前合成方案的设备边界；型号数据表、认证和环境适用性仍需逐项核验。")
        return (f"按当前输入，每串名义开路电压约为{number(nominal_string)} V（{number(per_string)}×{number(voc)} V），"
                "这是标准条件下的名义比较，不是低温最大开路电压、MPPT窗口或输入电流匹配的通过证明。"
                "低温校核至少需要组件电压温度系数和当地最低设计温度，高温MPPT及逆变器电流还需用完整数据表复核。")

    if chapter_id == "CH09" and item_no in {1, 2, 5}:
        ac = model.value("ac_capacity")
        available = normalized.get("grid.available_capacity")
        export_limit = normalized.get("grid.export_power_limit")
        return (f"本{('地面集中式' if ground else '屋顶')}方案逆变器交流额定容量为{number(ac)} kWac，"
                f"录入的申报可接入余量为{number(available)} kWac，送出有功限制为{number(export_limit)} kW。"
                "三者分别代表设备额定、接入边界和调度/计量边界，不能互相替代；"
                "容量差异本身不证明已经发生相应电量损失。当前现金与能量结果按既有送出/计量边界计算，"
                "是否获准接入、限发如何执行及实际结算仍须以具名电网意见和计量记录核验。")

    if chapter_id == "CH14" and item_no == 4:
        rate = normalized.get("capex.contingency_rate")
        capex = model.value("financial.capex.total")
        return (f"当前输入登记预备费率{number(Decimal(str(rate)) * 100) if rate is not None else 'UNKNOWN'}%，"
                f"评价期CAPEX为{number(capex)}元；现有结果没有另按该费率自动叠加预备费用。"
                "因此本报告只能确认费率已登记，不能确认预备费已经包含在总投资或报价中；"
                "正式投资估算应取得分项报价、适用基数、税口径和付款边界后再勾稽，不能用CAPEX×1.04替换本次结果。")

    if chapter_id == "CH18" and item_no == 1:
        annual = model.result.get("evidence", {}).get("financial-ledger", {}).get("annual", ())
        replacement = next((row for row in annual if row.get("period") == "OPERATING_YEAR_13"), None)
        terminal = next((row for row in annual if row.get("period") == "OPERATING_YEAR_25"), None)
        if replacement and terminal:
            return (f"全期现金桥显示第13年更换支出{number(replacement.get('replacement_cash_paid'))}元，"
                    f"该年项目净现金流为{number((model.value('financial.phase3e.project_cash_flow') or [])[13])}元；"
                    "年度净流出不等于某一付款瞬间已经发生资金缺口，但确实形成准备金、可动用现金或其他合法资金安排压力。"
                    f"第25年营运资金回收为{number(terminal.get('working_capital_release'))}元，"
                    "终期资产现金为0元，年末差额由营运资金回收解释而不是残值。"
                    "在实施前应核对更换付款计划和资金来源；当前资料没有日期化余额，不能宣称付款覆盖已满足。")

    if chapter_id == "CH17" and item_no == 4:
        focus = "资源代表性、设备与结构、接入与送出、自用消纳/市场电价、交易结算、CAPEX及预备费、第13年更换资金、权属地勘消防实施"
        return (f"当前风险清单应按{focus}分别管理。其共同影响路径是：资料或边界变化会先改变可建设条件、"
                "可交付电量或现金事件，再传导到项目现金流和回报指标；当前来源均为合成或待核实状态，"
                "没有正式合同、审批或现场实测可以替代。下一步应为每项风险指定责任人和关闭材料：资源用授权时序与交叉验证，"
                "设备/结构用数据表和专业校核，接入用电网意见，交易用合同与计量，CAPEX用报价勾稽，"
                "更换用付款计划和资金安排，权属/地勘/消防用具名文件。")
    return None


def _professional_narrative(model: ReportModel, pv_type: str, chapter_id: str, title: str,
                            evidence: dict[str, Any], *, item_no: int = 1,
                            editorial_fixture: dict[str, Any] | None = None) -> tuple[list[str], str, str]:
    """Build category-aware consulting prose from bound evidence, not template labels."""
    facts = _evidence_facts(evidence)
    fact_text = "；".join(facts) + "。" if facts else ""
    profile = REPORT_PROFILES[pv_type]
    ground = pv_type == "utility_scale_ground"
    special = _r4_special_narrative(model, pv_type, chapter_id, item_no)
    if special:
        if evidence["state"] == "EVIDENCED":
            tail = ("该判断仅适用于当前同一canonical中的合成输入和计算边界；"
                    "不替代现场实测、具名审批、设备数据表或正式专业签审。")
            claim_status = "EVIDENCE_BOUND_CONDITIONAL"
        else:
            tail = _topic_missing(title, chapter_id, pv_type,
                                  _professional_missing(title, chapter_id, pv_type))
            claim_status = "LIMITED_BY_MISSING_EVIDENCE"
        paragraphs = [special, tail]
        return paragraphs, "".join(paragraphs), claim_status
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
    if chapter_id == "CH01" and title in {"阻断风险和四态建议", "阶段建议"}:
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
                   editorial_fixture: dict[str, Any] | None = None,
                   reader_preview: bool = False) -> dict[str, Any]:
    items = next(items for cid, _chapter_title, items in CHAPTERS if cid == chapter_id)
    item_id = f"{chapter_id}.{item_no:02d}"
    rule = guidance(item_id, items)
    fields = category_fields(item_id, CHAPTER_FIELDS[chapter_id][item_no - 1], pv_type,
                             model.result["inputs"].get("normalized", {}).get("project.has_storage") is not False)
    metrics = CHAPTER_METRICS[chapter_id][item_no - 1]
    # Reader-facing findings added beyond the frozen minimum subsection matrix
    # must carry their own source/metric bindings in the checklist as well.
    extra_fields = {
        "CH01.01": ("project.evaluation_years",),
        "CH03.05": ("project.sales_mode",),
        "CH06.02": ("layout.fire_setback",),
        "CH06.03": ("grid.available_capacity", "grid.export_power_limit"),
        "CH06.06": ("project.has_storage",),
        "CH07.01": ("system.module_count",),
        "CH07.06": ("project.has_storage",),
        "CH12.01": ("environment.grid_emission_factor",),
        "CH14.05": ("finance.debt_ratio",),
    }
    extra_metrics = {
        "CH01.01": ("dc_capacity",),
        "CH03.02": ("dc_capacity",),
        "CH03.05": ("dc_capacity", "consumption.year.1"),
        "CH06.01": ("dc_capacity",),
        "CH06.04": ("dc_capacity", "ac_capacity"),
        "CH06.05": ("dc_capacity", "ac_capacity"),
        "CH06.06": ("dc_capacity", "ac_capacity"),
        "CH07.01": ("dc_ac_ratio",),
        "CH10.05": ("revenue.year.1",),
        "CH12.01": ("energy.delivered.year.1",),
        "CH15.03": ("financial.phase3e.project_cash_flow",),
        "CH15.04": ("financial.phase3e.project_cash_flow",),
        "CH17.01": ("energy.delivered.year.1", "revenue.year.1"),
        "CH14.04": ("financial.capex.total",),
        "CH18.03": ("financial.phase3e.project_cash_flow",),
    }
    fields = tuple(dict.fromkeys((*fields, *extra_fields.get(item_id, ()))))
    metrics = tuple(dict.fromkeys((*metrics, *extra_metrics.get(item_id, ()))))
    if item_id in {"CH01.05", "CH18.01"}:
        fields = tuple(dict.fromkeys((*fields, "site.rights_status", "grid.opinion_status")))
        metrics = (*metrics, "financial.phase3e.project_cash_flow")
    metrics = tuple(dict.fromkeys(metrics))
    if pv_type == "utility_scale_ground" and item_id in {"CH01.04", "CH03.05", "CH10.02"}:
        metrics = tuple(metric for metric in metrics if not metric.startswith("consumption."))
    if pv_type == "utility_scale_ground" and item_id == "CH03.04":
        metrics = (*metrics, "energy.delivered.year.1")
    claim = build_claim(model, item_id, title, f"{title}：{rule.rstrip('。')}？", rule,
                        fields, metrics,
                        pv_type, _word_value, _metric_label, reader_preview=reader_preview)
    cited_metrics = tuple(dict.fromkeys((*metrics, *claim["supporting_metric_ids"])))
    cited_fields = tuple(dict.fromkeys((*fields, *claim["supporting_input_field_ids"])))
    return {**claim, "field_ids": list(cited_fields), "metric_ids": list(cited_metrics),
            "missing": claim["unresolved"] if claim["state"] != "NOT_APPLICABLE" else "",
            "conclusion": claim["decision"]}


def profile_name(pv_type: str) -> str:
    return REPORT_PROFILES[pv_type]["boundary"]


def _monthly_balance_rows(model: ReportModel) -> list[list[str]]:
    """Display existing, aligned monthly results; never apportion annual totals."""
    energy = model.value("energy.monthly.year.1")
    revenue = model.metric("revenue.year.1") or {}
    consumption = model.metric("consumption.year.1") or {}
    monthly = revenue.get("details", {}).get("monthly")
    inputs = model.result["inputs"].get("normalized", {})
    records = model.result.get("source_snapshot", {}).get("phase2", {}).get("records", ())
    resource = _source_value(inputs, records, "resource.monthly")
    unavailable = [["UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN",
                    "逐月身份、来源或电量平衡待确认"]]
    if (not isinstance(energy, list) or len(energy) != 12 or
            revenue.get("status") != "CALCULATED" or consumption.get("status") != "CALCULATED" or
            not isinstance(monthly, list) or len(monthly) != 12 or
            monthly != consumption.get("details", {}).get("monthly") or
            not isinstance(resource, list) or len(resource) != 12 or
            [row.get("fields", {}).get("resource.monthly.month") for row in resource] != list(range(1, 13))):
        return unavailable
    keys = ("self_kwh", "export_kwh", "curtailed_kwh", "delivered_kwh", "available_kwh")
    rows = []
    for month, (generated, settled) in enumerate(zip(energy, monthly), 1):
        if (isinstance(generated, bool) or not isinstance(generated, (int, float, Decimal)) or
                not isinstance(settled, dict) or
                any(isinstance(settled.get(key), bool) or
                    not isinstance(settled.get(key), (int, float, Decimal)) for key in keys)):
            return unavailable
        available = Decimal(str(settled["available_kwh"]))
        if (abs(available - sum(Decimal(str(settled[key])) for key in
                              ("self_kwh", "export_kwh", "curtailed_kwh"))) > Decimal("0.01") or
                abs(Decimal(str(settled["delivered_kwh"])) - available
                    + Decimal(str(settled["curtailed_kwh"]))) > Decimal("0.01")):
            return unavailable
        rows.append([str(month), _word_number(generated), _word_number(settled["self_kwh"]),
                     _word_number(settled["export_kwh"]), _word_number(settled["curtailed_kwh"]),
                     _word_number(settled["delivered_kwh"]), _word_number(available),
                     "合成月度结果；非实际计量"])
    return rows


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


def _appendix_evidence(model: ReportModel, pv_type: str, app_id: str, item_no: int,
                       *, reader_preview: bool = False) -> dict[str, Any]:
    item_id = f"{app_id}.{item_no:02d}"
    question, rule, field_ids, metric_ids = APPENDIX_RULES[item_id]
    title = APPENDIX_TITLES[item_id]
    field_ids = category_fields(item_id, field_ids, pv_type,
                                model.result["inputs"].get("normalized", {}).get("project.has_storage") is not False)
    claim = build_claim(model, item_id, title, question, rule, field_ids, metric_ids,
                        pv_type, _word_value, _metric_label, reader_preview=reader_preview)
    cited_fields = tuple(dict.fromkeys((*field_ids, *claim["supporting_input_field_ids"])))
    cited_metrics = tuple(dict.fromkeys((*metric_ids, *claim["supporting_metric_ids"])))
    return {**claim, "field_ids": list(cited_fields), "metric_ids": list(cited_metrics),
            "missing": claim["unresolved"] if claim["state"] != "NOT_APPLICABLE" else "",
            "conclusion": claim["decision"]}


def _plan_word_rows(model: ReportModel) -> list[list[Any]]:
    normalized = model.result["inputs"].get("normalized", {})
    records = model.result.get("source_snapshot", {}).get("phase2", {}).get("records", ())
    tasks = _source_value(normalized, records, "schedule.tasks")
    if not isinstance(tasks, list):
        return [["UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "任务来源尚未闭合"]]
    task_labels = {item.get("row_id"): f"任务{index}" for index, item in enumerate(tasks, 1)}
    rows = []
    for index, item in enumerate(tasks, 1):
        fields = item["fields"]
        task_id = fields.get("schedule.tasks.task_id")
        if not isinstance(task_id, str) or task_id != item.get("row_id"):
            return [["UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "任务身份尚未闭合"]]
        original_name = fields.get("schedule.tasks.name")
        kind = _task_display_name(original_name) if isinstance(original_name, str) and original_name else "待核对任务（原名见来源清单）"
        start, finish = fields.get("schedule.tasks.start_date"), fields.get("schedule.tasks.finish_date")
        try:
            days = (date.fromisoformat(finish) - date.fromisoformat(start)).days + 1
            duration = f"{days}自然日（含起止日）" if days > 0 else "UNKNOWN"
        except (TypeError, ValueError):
            duration = "UNKNOWN"
        predecessors = fields.get("schedule.tasks.predecessor_ids")
        dependency = ("、".join(task_labels.get(predecessor, "未知任务（见来源）") for predecessor in predecessors)
                      if isinstance(predecessors, list) and predecessors else "无")
        marker = "列为计划重点" if fields.get("schedule.tasks.critical_path") is True else "一般任务"
        def short_date(value: Any) -> str:
            try:
                return date.fromisoformat(value).strftime("%Y.%m.%d")
            except (TypeError, ValueError):
                return "待确定"
        rows.append([f"任务{index} · {kind}", short_date(start), short_date(finish),
                     duration, dependency, marker])
    return rows


def _capex_word_rows(model: ReportModel) -> list[list[Any]]:
    normalized = model.result["inputs"].get("normalized", {})
    records = model.result.get("source_snapshot", {}).get("phase2", {}).get("records", ())
    items = _source_value(normalized, records, "capex.items")
    if not isinstance(items, list):
        return [["UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "CAPEX分项来源尚未闭合"]]
    renewals = {row.get("row_id"): row.get("fields", {}).get("assets.replacements.year")
                for row in normalized.get("assets.replacements", ()) if isinstance(row, dict)}
    categories = {"modules": "组件", "inverters": "逆变器", "mounting": "支架及安装材料",
                  "construction": "工程建设"}
    rows = []
    for item in items:
        fields = item["fields"]
        row_id = item["row_id"]
        category = categories.get(fields.get("capex.items.category"), "其他分项（详见来源清单）")
        quantity = fields.get("capex.items.quantity")
        quantity_unit = fields.get("capex.items.quantity_unit")
        amount = fields.get("capex.items.amount")
        period = (f"运营第{renewals[row_id]}年更换" if row_id in renewals else "建设期分项")
        rows.append([category, f"{_word_number(quantity)} {'件' if quantity_unit == 'unit' else quantity_unit}" if quantity is not None else "UNKNOWN",
                     _word_number(amount) if amount is not None else "UNKNOWN",
                     fields.get("capex.items.payment_date") or "UNKNOWN", period])
    return rows


def _next_stage_rows(model: ReportModel) -> list[list[str]]:
    """Proposed evidence gates, not assigned owners or promises of completion."""
    ground = model.result["pv_type"] == "utility_scale_ground"
    if ground:
        gates = [
            ("优先", "用地权利及用途", "决定场区能否合法使用", "土地使用与规划文件", "权利、边界及期限经专业复核", "业主、用地主管部门"),
            ("优先", "地勘与基础", "影响基础形式和工程费用", "测绘、地勘与基础初设", "形成与场区对应的勘察和核量结果", "业主、勘察设计单位"),
            ("优先", "集中接网与交易", "决定可交付电量和结算价格", "电网接入意见、计量及交易条款", "确认送出能力和可执行结算边界", "电网企业、交易主体"),
            ("随后", "道路排水及施工", "影响场区工程量与施工窗口", "道路排水初设与工程量", "形成与地形一致的施工方案", "设计单位、施工单位"),
        ]
        ledger = model.result.get("evidence", {}).get("financial-ledger", {}).get("annual", ())
        if any(row.get("replacement_cash_paid") for row in ledger[1:]):
            gates.append(("随后", "更换资金安排", "影响更换年度现金需求", "设备更换计划及资金方案",
                          "核对付款计划和可动用资金", "业主、财务部门"))
    else:
        gates = [
            ("优先", "屋面使用权及期限", "决定建筑使用与运营边界", "权属或租赁文件", "权利及期限经专业复核", "业主、产权主体"),
            ("优先", "结构、防水与消防", "决定组件能否安全安装", "结构鉴定、荷载与消防资料", "专业复核确认可用屋面及节点", "业主、设计单位"),
            ("优先", "真实厂区负荷", "影响自用电量与节费", "逐时用电及电费结算记录", "同一计量边界下复核自用比例", "业主、用电管理部门"),
            ("优先", "并网与余电送出", "影响接入容量及余电收入", "正式接网意见及结算条款", "明确可接入与余电结算边界", "电网企业、业主"),
        ]
    return [list(row) for row in gates]


def _project_cash_word_rows(model: ReportModel) -> list[list[Any]]:
    metric = model.metric("financial.phase3e.project_cash_flow")
    annual = model.result.get("evidence", {}).get("financial-ledger", {}).get("annual", ())
    values = metric.get("value") if metric and metric.get("status") == "CALCULATED" else None
    if (not isinstance(values, list) or not isinstance(annual, list) or len(values) != len(annual)
            or not values or any(not isinstance(value, (int, float, Decimal)) or isinstance(value, bool)
                                 for value in values)):
        return [["UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN"]]
    rows = []
    for ledger, amount in zip(annual, values):
        period = ledger.get("period")
        if not isinstance(period, str) or not period:
            return [["UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN"]]
        rows.append(["建设期" if period == "CONSTRUCTION" else _reader_text(period), _word_number(amount),
                     _word_number(ledger["capex_cash_paid"]) if "capex_cash_paid" in ledger else "UNKNOWN",
                     _word_number(ledger["working_capital_increase"]) if "working_capital_increase" in ledger else "UNKNOWN",
                     _word_number(ledger["replacement_cash_paid"]) if "replacement_cash_paid" in ledger else
                     "不适用（建设期）" if period == "CONSTRUCTION" else "UNKNOWN"])
    return rows


def _project_annual_bridge_rows(model: ReportModel, *, reader_preview: bool = False) -> tuple[list[list[str]], list[list[str]]] | None:
    """Display the ledger's annual events against the sourced 3E project flow."""
    annual = model.result.get("evidence", {}).get("financial-ledger", {}).get("annual")
    metric = model.metric("financial.phase3e.project_cash_flow") or {}
    values = metric.get("value") if metric.get("status") == "CALCULATED" else None
    terminal = model.result.get("evidence", {}).get("phase3e-terminal-reconciliation", {}).get("terminal_cash")
    if (not isinstance(annual, list) or not isinstance(values, list) or not isinstance(terminal, list)
            or len(annual) < 2 or len(annual) != len(values) or len(annual) != len(terminal)
            or annual[0].get("period") != "CONSTRUCTION"):
        return None
    detail, bridge = [], []
    format_amount = _word_money if reader_preview else _word_number
    operating_fields = ("revenue_cash_receipts", "self_use_avoided_expenditure", "transaction_cost_cash_paid",
                        "opex_cash_paid", "cash_tax_total_project")
    for index, (ledger, amount, terminal_cash) in enumerate(zip(annual, values, terminal)):
        period = ledger.get("period")
        if period != ("CONSTRUCTION" if index == 0 else f"OPERATING_YEAR_{index}"):
            return None
        required = ("capex_cash_paid", "working_capital_increase") + (() if index == 0 else
                    ("working_capital_release", *operating_fields))
        if any(not isinstance(ledger.get(key), (int, float, Decimal)) or isinstance(ledger[key], bool)
               for key in required):
            return None
        if (not isinstance(amount, (int, float, Decimal)) or isinstance(amount, bool)
                or not isinstance(terminal_cash, (int, float, Decimal)) or isinstance(terminal_cash, bool)):
            return None
        if index == 0:
            operating = Decimal(0)  # 3E construction has no operating cash benefit.
            release = Decimal(0)  # 3D records release only in operating years.
        else:
            receipts, savings, fee, opex, tax = (Decimal(str(ledger[key])) for key in operating_fields)
            operating = receipts + savings - fee - opex - tax
            release = Decimal(str(ledger["working_capital_release"]))
            shown = lambda value: Decimal(format_amount(value).replace(",", ""))
            display_difference = (shown(operating) - shown(receipts) - shown(savings) + shown(fee)
                                  + shown(opex) + shown(tax))
            detail.append([_reader_text(period), *(format_amount(ledger[key]) for key in operating_fields),
                           format_amount(display_difference), format_amount(operating)])
        # Reconcile at ledger precision; never make an incomplete or inconsistent bridge look complete.
        reconstructed = (operating - Decimal(str(ledger["capex_cash_paid"]))
                         - Decimal(str(ledger["working_capital_increase"])) + release
                         + Decimal(str(terminal_cash)))
        if abs(reconstructed - Decimal(str(amount))) > Decimal("0.00000001"):
            return None
        bridge.append(["建设期" if index == 0 else _reader_text(period),
                       "不适用（建设期）" if index == 0 else format_amount(operating),
                       format_amount(ledger["capex_cash_paid"]), format_amount(ledger["working_capital_increase"]),
                       "不适用（建设期）" if index == 0 else format_amount(release),
                       format_amount(terminal_cash), format_amount(amount)])
    return detail, bridge


def _add_evidence_table(document: Document, evidence: dict[str, Any], caption: str) -> None:
    rows = [[row["kind"], row["id"], row["value"], row["unit"], row["status"], row["formula_id"], ", ".join(row["source_ids"]) or "UNKNOWN"]
            for row in evidence["rows"][:12]]
    _add_table(document, ["类型", "指标/字段", "值", "单位", "状态", "公式/绑定", "source_ids"], rows, caption)


def _write_docx(model: ReportModel, output: Path, display_name: str, pv_type: str,
                editorial_fixture: dict[str, Any] | None = None,
                content_version: str | None = None,
                reader_preview: bool = False) -> dict[str, Any]:
    profile = REPORT_PROFILES[pv_type]
    source_map = _source_ref_map(model)
    if content_version is None:
        content_version = READER_REPORT_CONTENT_VERSION if reader_preview else REPORT_CONTENT_VERSION
    document = Document()
    document._solar_reader_preview = reader_preview
    format_amount = _word_money if reader_preview else _word_number
    configure_word(document)
    document.core_properties.keywords = WORD_FORMAT.identifier
    document.add_paragraph("星核实验室 StarCore Lab", style="Solar Cover Info")
    document.add_paragraph(profile["title"], style="Solar Cover Title")
    document.add_paragraph(display_name, style="Solar Cover Subtitle")
    synthetic_calculation = (str(model.result["project_id"]).startswith("SYNTHETIC")
                             and model.result["maturity"].get("real_project") != "VERIFIED")
    # This abbreviated reader view is approved only for the two synthetic R10
    # examples. A real project's source and maturity prose needs its own review.
    if reader_preview and not synthetic_calculation:
        raise ContractError("REPORT_READER_PREVIEW_SYNTHETIC_ONLY")
    sample_status = ("示例资料 · 部分指标已测算 · 未经现场核验"
                     if synthetic_calculation else
                     "资料已有核验记录 · 本阶段指标已测算"
                     if model.result.get("status") == "COMPLETE" and model.result["maturity"].get("real_project") == "VERIFIED" else
                     "资料待核验 · 本阶段指标已测算"
                     if model.result.get("status") == "COMPLETE" else
                     "资料待核验 · 部分指标尚无可用结果")
    if editorial_fixture:
        sample_status = "示例资料 · 补充背景仅用于方案描述 · 未经现场核验"
    for label, value in (("项目类型", profile["boundary"]), ("资料情况", sample_status),
                         ("评价日期", str(model.result["evaluation_date"]))):
        document.add_paragraph(f"{label}：{value}", style="Solar Cover Info")
    if model.result.get("status") != "COMPLETE" or model.result.get("maturity", {}).get("real_project") != "VERIFIED":
        document.add_paragraph("项目判断：资料尚待核验，暂不具备投资决策条件", style="Solar Cover Info")
    cover_note = document.add_paragraph(REPORT_DISCLAIMER)
    cover_note.paragraph_format.space_before = Pt(16)
    if editorial_fixture:
        identity_note = document.add_paragraph("部分背景采用单独标注的示例资料，不作为现场实测、第三方证明或测算输入。")
        identity_note.paragraph_format.space_before = Pt(8)
    front = document.add_section(WD_SECTION_START.NEW_PAGE)
    front.header.is_linked_to_previous = False
    front.footer.is_linked_to_previous = False
    document.add_paragraph("摘要", style="Solar Abstract Title")
    basis_text = ("工程背景中另有明确标识的示例资料，仅用于描述拟议方案；这些资料不参与测算，也不构成第三方证明。"
                  if editorial_fixture else "")
    for paragraph in _project_summary(model).split("\n\n"):
        document.add_paragraph(paragraph, style="Solar Abstract")
    if basis_text:
        document.add_paragraph(basis_text, style="Solar Abstract")
    key_ids = ("dc_capacity", "energy.year.1", "revenue.year.1", "financial.capex.total",
               "financial.phase3e.project_npv", "financial.phase3e.project_irr")
    key_rows = _professional_metric_rows(model, key_ids, reader_preview=reader_preview)
    maturity = model.result.get("maturity", {}).get("real_project")
    material_label = ("A：资料已经核实" if maturity == "VERIFIED" else
                      "B：使用当前假设资料" if model.result.get("source_snapshot", {}).get("phase2", {}).get("records") else
                      "C：尚缺关键来源资料")
    _add_table(document, ["专业指标", "本阶段结果", "单位", "说明"], key_rows,
               ("关键预测结果（详细数据与原始精度见配套测算模型）" if reader_preview else
                f"关键预测结果（资料成熟度{material_label}；完整精度见配套测算模型）"),
               widths_cm=(5.0, 2.8, 2.1, 7.1), layout_type="SUMMARY_TABLE")
    document.add_paragraph(("本报告使用示例资料，来源仍待核验；表中数值是基于当前条件的预测，"
                            "不能据此作投资决策。" if reader_preview else
                            "资料成熟度反映当前证据核验程度，不代表测算结果已具备投资决策条件。"),
                           style="Solar Abstract")
    normalized = model.result["inputs"].get("normalized", {})
    records = model.result.get("source_snapshot", {}).get("phase2", {}).get("records", ())
    keywords = ("工商业屋顶光伏；发电量预测；厂区消纳；投资评价" if pv_type == "industrial_rooftop" else
                "集中式地面光伏；发电量预测；并网送出；投资评价")
    keyword_line = document.add_paragraph(style="Solar Keywords")
    set_run_font(keyword_line.add_run("关键词"), chinese="黑体", size=12, bold=True)
    keyword_line.add_run("：" + keywords)
    # Keep the contents front matter independent from the abstract's closing
    # tables and keyword line.  A TOC that starts in the remaining space on
    # the abstract page is difficult to scan and can split its first entries
    # away from the contents heading.
    document.add_page_break()
    document.add_paragraph("目录", style="Solar Contents Title")
    _add_toc(document)
    section = document.add_section(WD_SECTION_START.NEW_PAGE)
    section.header.is_linked_to_previous = False
    section.footer.is_linked_to_previous = False
    header = section.header.paragraphs[0]
    header.style = "Solar Header"
    header.add_run(profile["title"])
    footer = section.footer.paragraphs[0]
    footer.style = "Solar Footer"
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)
    page_start = OxmlElement("w:pgNumType")
    page_start.set(qn("w:start"), "1")
    section._sectPr.append(page_start)
    configure_word(document)
    formal_formulas = _appendix_formula_definitions(model)
    reader_formulas = ([formula for formula in formal_formulas
                        if formula["formula_id"] in READER_FORMULA_IDS]
                       if reader_preview else formal_formulas)
    if reader_preview and len(reader_formulas) != len(READER_FORMULA_IDS):
        raise ContractError("REPORT_READER_FORMULA_IDENTITY")
    reader_appendices = (tuple((app_id, "常用公式与方法索引" if app_id == "APP11" else
                               "常用术语与单位" if app_id == "APP12" else title)
                              for app_id, title in APPENDICES) if reader_preview else APPENDICES)
    reader_appendix_titles = ({**APPENDIX_TITLES, "APP11.01": "公式索引",
                               "APP11.02": "常用公式与符号", "APP12.01": "常用术语",
                               **{item_id: title for item_id, title in READER_ITEM_TITLES.items()
                                  if item_id.startswith("APP")}}
                              if reader_preview else APPENDIX_TITLES)
    math_objects = convert_equations(formal_formulas)
    chart_specs = _canonical_chart_specs(model)
    chart_receipts: list[dict[str, Any]] = []
    checklist: list[dict[str, Any]] = []

    bookmark_index = 1
    display_chapters = tuple((chapter_id, chapter_title,
                              tuple(("土地使用权与期限" if pv_type == "utility_scale_ground" else "屋面使用权与期限")
                                    if chapter_id == "CH04" and index == 3 else
                                    "阶段建议" if (chapter_id == "CH18" and index == 1) or
                                    (chapter_id == "CH01" and index == 5) else
                                    READER_ITEM_TITLES.get(f"{chapter_id}.{index:02d}", name) if reader_preview else name
                                    for index, name in enumerate(items, 1)))
                             for chapter_id, chapter_title, items in CHAPTERS)
    for chapter_id, chapter_title, items in display_chapters:
        chapter_heading = add_numbered_heading(document, heading_number(chapter_id, chapter_title), bookmark_index)
        bookmark_index += 1
        chapter_heading.paragraph_format.page_break_before = chapter_id != "CH01"
        # The first subsection supplies the substantive opening. A stock
        # "本章说明…" paragraph before every chapter adds no project finding.
        if chapter_id == "CH08":
            chart_receipts = _add_canonical_charts(document, model, chart_specs, source_map, "发电量变化")
        for number, item in enumerate(items, 1):
            item_id = f"{chapter_id}.{number:02d}"
            add_numbered_heading(document, heading_number(item_id, item, parent_stable_id=chapter_id,
                                                          parent_level=1), bookmark_index)
            bookmark_index += 1
            evidence = _item_evidence(model, pv_type, chapter_id, item, item_no=number,
                                       editorial_fixture=editorial_fixture, reader_preview=reader_preview)
            _add_professional_narrative(document, evidence)
            if item_id == "CH13.02":
                _add_table(document, ["任务", "开始", "结束", "持续时间", "前置任务", "计划性质"],
                           _plan_word_rows(model), "实施计划（日期为登记的预排日期；计划重点未经关键路径算法验证）",
                           widths_cm=(5.2, 2.65, 2.65, 2.2, 2.1, 2.2), nowrap_columns=(1, 2),
                           layout_type="PLAN_TABLE")
            if item_id == "CH18.04":
                gates = _next_stage_rows(model)
                _add_table(document, ["顺序", "核验事项", "影响", "所需材料", "完成标准"],
                           [row[:5] for row in gates], "下一阶段推进事项（建议顺序，不表示风险等级）",
                           widths_cm=(1.8, 3.2, 3.5, 4.2, 4.3), layout_type="ISSUE_TABLE")
                document.add_paragraph("建议协调对象并非已任命责任人：" + "；".join(
                    f"{row[1]}—{row[5]}" for row in gates) + "。")
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

    document.add_paragraph("结果与公式索引", style="Solar Unnumbered Title")
    document.add_paragraph("本节仅列示与投资评价直接相关的专业指标。完整数值精度、计算口径和来源绑定保留在配套测算模型中，正文不重复展开审计字段。")
    blocked = [metric for metric in model.metrics if str(metric.get("status", "")).startswith("BLOCKED")]
    index_ids = ("financial.capex.total", "financial.opex.cash_lifecycle",
                 "financial.tax.cash_lifecycle", "financial.asset.ending_book_value",
                 "financial.phase3e.project_cash_flow", "financial.phase3e.project_npv",
                 "financial.phase3e.project_irr", "financial.phase3e.static_payback",
                 "financial.phase3e.dynamic_payback", "financial.phase3e.equity-investor-cash-flow",
                 "financial.phase3e.cfads", "financial.phase3e.dscr", "financial.phase3e.lcoe",
                 "financial.phase3e.break-even-price", "financial.phase3e.investment-hurdle-gap")
    groups = (
        ("投资与项目收益", index_ids[:9]),
        ("融资与资本金评价", index_ids[9:12]),
        ("尚未具备评价条件的指标", index_ids[12:]),
    )
    for title, ids in groups:
        selected = _professional_metric_rows(model, ids, reader_preview=reader_preview)
        _add_table(document, ["专业指标", "本阶段结果", "单位", "说明"], selected,
                   title + "（完整精度见测算模型 M16）",
                   widths_cm=((4.1, 4.5, 2.0, 6.4) if reader_preview and title == "尚未具备评价条件的指标"
                              else (4.1, 4.5, 1.6, 6.8)),
                   nowrap_columns=(2,) if reader_preview and title == "尚未具备评价条件的指标" else (),
                   layout_type="FINANCIAL_TABLE")
    if blocked:
        if model.status("financial.phase3e.project_npv") == "CALCULATED":
            document.add_paragraph("以下阻断仅适用于各自指标；不撤销已计算的项目净现值。IRR、回收期须以其自身状态为准；股东现金事件与平准化成本边界须独立补证。")
        else:
            document.add_paragraph("以下指标按各自阻断理由补证；不能由尚未计算的项目回报或其他指标推断有效收益。")
    for app_id, app_title in reader_appendices:
        appendix_heading = add_numbered_heading(document, heading_number(app_id, app_title), bookmark_index)
        bookmark_index += 1
        appendix_heading.paragraph_format.page_break_before = True
        document.add_paragraph(READER_APPENDIX_LEADS[app_id] if reader_preview else
                               f"本附录《{app_title}》列示本项目相关资料；原始精度与来源编号见配套工作簿。")
        for item_no in (1, 2):
            item_id = f"{app_id}.{item_no:02d}"
            item_title = reader_appendix_titles[item_id]
            add_numbered_heading(document, heading_number(item_id, item_title,
                                                          parent_stable_id=app_id, parent_level=1), bookmark_index)
            bookmark_index += 1
            evidence = _appendix_evidence(model, pv_type, app_id, item_no, reader_preview=reader_preview)
            if app_id in {"APP11", "APP12"}:
                detail = (("全部公式及其原始定义见配套来源工作簿；元/Wp与元/kWp的换算口径尚待专业核验，"
                           "不得采用未经核实的换算结果。下表仅为索引，不表示本项目逐式执行。" if reader_preview else
                           f"冻结字典共列示{len(formal_formulas)}条正式定义，本次结果引用{len(_formula_definitions(model))}条；"
                           "列示、引用与成功执行不等同。具体符号及边界按公式分组见下一节。")
                          if item_id == "APP11.01" else
                          ("下列常用公式按本项目结果状态分别说明；完整公式、逐符号定义与原始记法见配套工作簿。"
                           if reader_preview else
                           "各公式的完整符号、下标、集合与适用边界分别列示；定义存在不代表已执行。")
                          if item_id == "APP11.02" else
                          ("本节仅解释本项目常用术语；全部术语原始定义及适用边界见资料来源与假设清单的词典。"
                           if reader_preview else
                           "完整术语词典含本项目尚未采用的方法，收录不表示相关技术已实施。")
                          if item_id == "APP12.01" else
                          "功率、能量、辐照与投资单位分开解释，不能混作同一物理量。")
                evidence["narrative"] = [detail]
                evidence["summary"] = detail
            for text in evidence["narrative"]:
                document.add_paragraph(_reader_text(text))
            if reader_preview and item_id == "APP01.02":
                source_index = (
                    "1. 气象与场址：资料来源与假设清单 S02「气象与地理来源」；逐月输入见测算模型 M04，多年实测与授权待核。",
                    "2. 设备、造价与更换：清单 S04「设备与成本来源」；设备及资本支出分别见模型 M05、M10，正式报价待核。",
                    f"3. 权属、接入与交易：清单 S01「输入台账」和 S07「冲突与缺口」；"
                    f"{'屋顶权属' if pv_type == 'industrial_rooftop' else '土地权利'}、正式接网及交易原件待补。",
                    "4. 政策与资料授权：清单 S03「政策适用性」和 S10「资料授权说明」；适用条款、有效期及授权待核。",
                )
                for entry in source_index:
                    document.add_paragraph(entry)
            if reader_preview and item_id == "APP13.01":
                document.add_paragraph(
                    "本读者预览版不在正文列示五项测算身份原值。可在同套测算模型的 M01「项目参数」"
                    "第2—6行及资料来源与假设清单的 S01「输入台账」第3—7行分别核对"
                    "model_version、run_id、input_hash、source_snapshot_id、result_hash；"
                    "两处须逐项相同。完整版的正文身份条款不能由本预览版替代。")
            if item_id == "APP02.01":
                _headers, resource_rows = _resource_rows(model)
                resource_intro, irradiance, weather, _mapping = prepare_resource_word_rows(
                    model.result, resource_rows, _word_number)
                if reader_preview:
                    timezone = normalized.get("site.timezone")
                    resource_intro = (f"下表为按月汇总的示例气象资料，采用{timezone}时区；"
                                      "每行来源索引须与变量列一同使用，逐字段原值、单位、数据集版本及来源号见测算模型 M04。"
                                      "月度气象资源不是发电量，也不代表场址多年实测。")
                document.add_paragraph(resource_intro)
                _add_table(document, ["月份", "GHI (kWh/㎡)", "DNI (kWh/㎡)", "DHI (kWh/㎡)",
                                      "POA (kWh/㎡)", "来源索引"], irradiance,
                           "月度辐照资源（来源索引须结合变量列读取）",
                           widths_cm=(1.2, 2.4, 2.4, 2.4, 2.4, 5.8))
                _add_table(document, ["月份", "气温 (°C)", "风速 (m/s)", "覆盖率（%）", "来源索引"], weather,
                           "月度气象资源（覆盖率由原始比值乘100展示）",
                           widths_cm=(1.2, 2.8, 2.8, 2.8, 7.0))
                resource_note = document.add_paragraph(
                    "辐照物理口径专项说明：本表数值单位为kWh/㎡，表示期间辐照量而非W/m²辐照度；"
                    "GHI是水平面全球辐照量，DNI是法向直射辐照量，DHI是水平面散射辐照量，POA是阵列面辐照量。"
                    "当前合成表若出现GHI=DNI+DHI的逐月数值模式，不应被解释为一般物理恒等式；"
                    "太阳天顶角、法向到水平投影、时间积分和质量控制仍需原始逐时资料证明。"
                    "发电计算沿既有POA/时间积分链消费资源，不以报告表格中的简单相加替代物理转换。"
                )
                if reader_preview:
                    resource_note.paragraph_format.keep_together = True
            if item_id == "APP02.02":
                document.add_paragraph("下表按已记录的月份顺序对应既有发电与结算月度结果；"
                                       "可用列表示结算前、已计入发电链限发的月度电量；结算截弃是另一边界。"
                                       "未绑定逐月发电链限发损失时不按全年比例分摊，也不把月表的可用列称为限发前电量。"
                                       "月份身份或电量平衡无法确认时标为待核验。")
                monthly = _monthly_balance_rows(model)
                for title, names, columns, widths, repeat_identity in (
                    (("首年月度发电与上网（kWh；示例预测）" if pv_type == "utility_scale_ground"
                      else "首年月度发电与消纳（kWh；示例预测）"),
                     ("月", "发电", "自用", "上网"), (0, 1, 2, 3), (2.0, 5.0, 5.0, 5.0), False),
                    ("首年月度交付与结算边界（kWh；与上表同月）",
                     ("月", "结算截弃", "交付", "可用（结算前）", "性质"),
                     (0, 4, 5, 6, 7), (1.6, 3.4, 3.4, 4.0, 4.6), True),
                ):
                    _add_table(document, list(names), [[row[index] for index in columns] for row in monthly],
                               title, widths_cm=widths, layout_type="TECHNICAL_DETAIL_TABLE",
                               continuation_identity=reader_preview and repeat_identity)
                available = model.metric("available_kwh.year.1") or {}
                energy = model.metric("energy.year.1") or {}
                loss = (energy.get("details") or {}).get("losses_kwh", {}).get("curtailment")
                if (available.get("status") == energy.get("status") == "CALCULATED"
                        and all(isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)
                                for value in (available.get("value"), energy.get("value"), loss))
                        and abs(Decimal(str(available["value"])) - Decimal(str(energy["value"]))
                                - Decimal(str(loss))) <= Decimal("0.01")):
                    document.add_paragraph(
                        f"全年限发前可利用电量{_word_number(available['value'])}kWh，"
                        f"发电链限发损失{_word_number(loss)}kWh，"
                        f"限发后发电量{_word_number(energy['value'])}kWh。"
                        "这是年度已计算值的勾稽，不把年度限发损失分摊到未绑定的月份；"
                        "月度两位小数独立取整，与年度高精度总量可能存在尾差。")
            if item_id == "APP03.01":
                equipment_fields = ("system.module_model", "system.module_count", "system.module_power",
                                    "system.module_voc", "system.module_vmp", "system.module_isc",
                                    "system.module_imp", "system.modules_per_string", "system.parallel_strings",
                                    "system.inverter_model",
                                    "system.inverter_count", "system.inverter_unit_ac", "system.inverter_mppt_min",
                                    "system.inverter_mppt_max", "system.inverter_max_dc_voltage",
                                    "system.inverter_max_input_current", "layout.tilt", "layout.azimuth",
                                    "layout.row_pitch", "layout.fire_setback")
                equipment_rows = []
                equipment_labels = {
                    "module_model": "组件型号", "module_count": "组件数量", "module_power": "组件功率（Wp）",
                    "module_voc": "组件开路电压（V）", "module_vmp": "组件最大功率电压（V）",
                    "module_isc": "组件短路电流（A）", "module_imp": "组件最大功率电流（A）",
                    "modules_per_string": "每串组件数", "parallel_strings": "并联组串数", "inverter_model": "逆变器型号",
                    "inverter_count": "逆变器台数", "inverter_unit_ac": "单台交流功率（kW）",
                    "inverter_mppt_min": "MPPT电压下限（V）", "inverter_mppt_max": "MPPT电压上限（V）",
                    "inverter_max_dc_voltage": "直流电压上限（V）", "inverter_max_input_current": "输入电流上限（A）",
                    "tilt": "倾角（°）", "azimuth": "方位角（°）", "row_pitch": "行距（m）",
                    "fire_setback": "消防退让（m）",
                }
                for fid in equipment_fields:
                    value = _source_value(normalized, records, fid)
                    if value is not None:
                        group = ("组件与组串" if fid.startswith("system.module") or fid == "system.parallel_strings" else
                                 "逆变器" if fid.startswith("system.inverter") else "阵列与安全布置")
                        equipment_rows.append([equipment_labels[fid.rsplit(".", 1)[-1]], _word_value(value),
                                               group if reader_preview else fid])
                _add_table(document, (["设备／布置输入", "合成方案值", "参数类别"] if reader_preview else
                                      ["设备／布置输入", "合成方案值", "字段索引"]),
                           equipment_rows,
                           "设备参数（示例值；原字段和来源见测算模型 M05）" if reader_preview else
                           "设备原子参数（不代表供货商数据表或电气专项校核）",
                           widths_cm=(7.0, 6.0, 4.0) if reader_preview else (5.0, 4.0, 8.0))
            if item_id == "APP03.02":
                loss_rows = []
                losses = _source_value(normalized, records, "system.losses")
                loss_names = {"shading": "遮挡", "soiling": "积尘", "snow": "积雪",
                              "mismatch": "组件失配", "dc_cable": "直流线缆", "ac_cable": "交流线缆",
                              "transformer": "变压器", "export_line": "送出线路", "curtailment": "限发"}
                boundaries = {"DC": "直流侧", "AC": "交流侧", "GRID": "电网送出侧"}
                methods = {"INDEPENDENT_CONSTANT_RATE": "按顺序独立应用的固定损失率"}
                periods = {"ALL_OPERATING_YEARS": "全部运营年度"}
                if isinstance(losses, list):
                    for row in losses:
                        atom = row.get("fields", {})
                        kind = atom.get("system.losses.kind")
                        boundary = atom.get("system.losses.boundary")
                        method = atom.get("system.losses.method")
                        period = atom.get("system.losses.period")
                        ratio = atom.get("system.losses.value")
                        included = atom.get("system.losses.included_in_source")
                        loss_rows.append([_word_value(atom.get("system.losses.sequence")),
                                          loss_names.get(kind, "类别待核验") if reader_preview else _word_value(kind),
                                          (f"{_word_money(Decimal(str(ratio)) * 100)}%" if reader_preview and
                                           isinstance(ratio, (int, float, Decimal)) and not isinstance(ratio, bool)
                                           else _word_value(ratio)),
                                          boundaries.get(boundary, "边界待核验") if reader_preview else _word_value(boundary),
                                          ("是" if included else "否") if reader_preview and isinstance(included, bool)
                                          else _word_value(included),
                                          methods.get(method, "方法待核验") if reader_preview else _word_value(method),
                                          periods.get(period, "期间待核验") if reader_preview else _word_value(period)])
                for title, names, columns, widths, repeat_identity in (
                    ("系统损失类别及显示百分比（按原始比值乘100；顺序与已含标志不可忽略）" if reader_preview else
                     "系统损失类别及原始比值（顺序与已含标志不可忽略）",
                     ("序", "损失类型", "损失率（%）" if reader_preview else "原始比例", "边界", "来源已含"),
                     (0, 1, 2, 3, 4), (1.5, 4.2, 3.2, 4.2, 3.9), True),
                    ("系统损失方法与适用期间（同序对应上表）",
                     ("序", "方法", "期间"), (0, 5, 6), (1.5, 7.7, 7.8), False),
                ):
                    _add_table(document, list(names), [[row[index] for index in columns] for row in loss_rows],
                               title, widths_cm=widths, layout_type="TECHNICAL_DETAIL_TABLE",
                               continuation_identity=reader_preview and repeat_identity)
                degradation = _source_value(normalized, records, "system.annual_degradation")
                document.add_paragraph("年度衰减输入为" + (_word_value(degradation) if degradation is not None else "UNKNOWN") +
                                       "（原始比值）；后期设备更换停机见年度发电结果，不由更换事件推定性能恢复增益。")
            if item_id == "APP04.01":
                _add_table(document, ["投资分项", "数量", "金额（元）", "付款日期", "期间及性质"],
                           _capex_word_rows(model),
                           "资本支出分项" if reader_preview else
                           "CAPEX分项：建设期与后期更换分开列示；行ID、原金额、税口径与来源见测算模型 M10。",
                           widths_cm=(5.0, 2.5, 3.0, 2.6, 3.9))
                if reader_preview:
                    document.add_paragraph("建设期与后期更换分别列示；原始金额、税费口径与来源见测算模型 M10。")
                rate = model.result["inputs"].get("normalized", {}).get("capex.contingency_rate")
                if isinstance(rate, (int, float, Decimal)) and not isinstance(rate, bool):
                    document.add_paragraph(f"预备费率输入为{_word_number(Decimal(str(rate)) * 100)}%；"
                                           "现有CAPEX分项、汇总与建设期付款均未单列按此费率计算的预备费。"
                                           "已列报价是否内含预备费无法由该比率证明，本报告不额外叠加；正式估算须确认适用基数与报价边界。")
            if item_id == "APP04.02":
                boundary = _capex_boundary_rows(model)
                labels = {"initial_capex_cash_paid": "建设期资本现金付款", "lifecycle_capex_cash_paid": "全期资本现金付款",
                          "replacement_cash_paid": "其中：后期更换付款", "working_capital_increase": "建设期营运资金投入"}
                _add_table(document, ["费用边界", "金额（元）", "核算口径"],
                           [[labels.get(row[0], row[0]), row[2], row[6]] for row in boundary],
                           "资本支出、营运资金与后期更换的独立边界", widths_cm=(5.0, 3.5, 8.5))
            if item_id == "APP05.01":
                ledger = model.result.get("evidence", {}).get("financial-ledger", {})
                annual = (ledger.get("annual", ()) if
                          model.status("financial.phase3e.project_cash_flow") == "CALCULATED" else ())
                if annual:
                    document.add_paragraph("建设期不作为运营年：" + "；".join(
                        f"{name}：{_word_value(annual[0].get(key)) if key in annual[0] else '未提供'}"
                        for name, key in (("运维计提", "opex_accrued"), ("运维预计付款", "opex_cash_paid"),
                                          ("非现金折旧", "depreciation"), ("更换预计付款", "replacement_cash_paid"))) +
                        "。缺失记录不作零值处理。")
                    operations = annual[1:]
                    for title, fields in (
                        ("年度运维、折旧与更换（元；均为预测）",
                         (("运维计提", "opex_accrued"), ("运维预计付款", "opex_cash_paid"),
                          ("非现金折旧", "depreciation"), ("更换预计付款", "replacement_cash_paid"))),
                        ("年度交易费计提及预计付款（元；与运维费分开）",
                         (("交易费计提", "transaction_cost_accrued"),
                          ("交易费预计付款", "transaction_cost_cash_paid"))),
                    ):
                        _add_table(document, ["运营年", *(name for name, _ in fields)],
                                   [[f"第{index}年", *(_word_value(row.get(key)) for _, key in fields)]
                                    for index, row in enumerate(operations, 1)], title,
                                   layout_type="ANNUAL_LEDGER_TABLE", continuation_identity=reader_preview)
                    operating = [row.get("opex_cash_paid") for row in annual[1:]]
                    lifecycle_opex = model.value("financial.opex.cash_lifecycle")
                    if (len(operating) == len(annual) - 1
                            and all(isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)
                                    for value in operating + [lifecycle_opex])):
                        displayed = sum(Decimal(format_amount(value).replace(",", "")) for value in operating)
                        discrepancy = Decimal(format_amount(lifecycle_opex).replace(",", "")) - displayed
                        document.add_paragraph(
                            f"{len(operating)}个运营年度运维预计付款显示值合计{format_amount(displayed)}{' ' if reader_preview else ''}元，"
                            f"全期现金运维指标为{format_amount(lifecycle_opex)}{' ' if reader_preview else ''}元；"
                            f"两者展示差额（全期指标减年度显示值之和）为{format_amount(discrepancy)}{' ' if reader_preview else ''}元。"
                            "年度与全期分别按未取整账簿计算后列示，展示差额不是新增付款。")
                fee_source = ledger.get("trading_fee_payment")
                if fee_source and len(ledger.get("annual", ())) > 1:
                    first = ledger["annual"][1]
                    _add_table(document, ["首年费用项目", "本期计提（元）", "预计支付（元）", "期初／期末应付（元）", "来源与边界"],
                               [["单列交易费用", _word_number(first["transaction_cost_accrued"]),
                                 _word_number(first["transaction_cost_cash_paid"]),
                                 _word_number(first["transaction_cost_payable_opening"]) + "／" +
                                 _word_number(first["transaction_cost_payable_closing"]),
                                 "来源详见配套清单；示例年度预测，非实付"]],
                               "首年交易费" if reader_preview else
                               "交易费不并入运维费；全期计提、预计付款和应付逐期核对见测算模型 M14。",
                               widths_cm=(3.25, 2.75, 2.75, 3.4, 4.85) if reader_preview else
                               (2.7, 2.75, 2.75, 3.4, 5.4))
                    if reader_preview:
                        document.add_paragraph("交易费不并入运维费；全期计提、预计付款和应付逐期核对见测算模型 M14。")
            if item_id == "APP05.02":
                annual = (model.result.get("evidence", {}).get("financial-ledger", {}).get("annual", ())
                          if model.status("financial.phase3e.project_cash_flow") == "CALCULATED" else ())
                if annual:
                    def tax_display(row: dict[str, Any]) -> tuple[str, str]:
                        required = ("cash_tax_total_project", "income_tax_cash_paid_project",
                                    "other_cash_taxes_project")
                        if any(not isinstance(row.get(key), (int, float, Decimal)) or
                               isinstance(row.get(key), bool) for key in required):
                            return "待核验", "待核验"
                        vat = Decimal(str(row[required[0]])) - sum(
                            Decimal(str(row[key])) for key in required[1:])
                        if abs(vat) < Decimal("0.0000001"):
                            vat = Decimal(0)  # Remove binary-source noise only from presentation.
                        shown = lambda value: Decimal(format_amount(value).replace(",", ""))
                        rounding = shown(row[required[0]]) - shown(row[required[1]]) - shown(row[required[2]]) - shown(vat)
                        return format_amount(vat), format_amount(rounding)
                    document.add_paragraph("增值税净现金额按本次年度账簿中的项目现金税费合计扣除"
                                           "所得税预计付款和其他现金税费列示，包含计入账簿的"
                                           "增值税预计支付与退税的净影响；仅是既有结果的展示勾稽，"
                                           "不表示税款已经实际缴纳。各分项独立显示取整产生的分位尾差"
                                           "单列为舍入差额，不充作真实增值税；建设期缺少税费事件时标为待核验。")
                    document.add_paragraph("建设期税费记录未闭合时标记未提供，不把空缺解释为零或实缴。")
                    tax_rows = [[f"第{index}年", *(_word_value(row.get(key)) for key in
                                 ("taxable_income_project", "income_tax_accrual_project",
                                  "income_tax_cash_paid_project", "other_cash_taxes_project")),
                                 *tax_display(row), _word_value(row.get("cash_tax_total_project"))]
                                for index, row in enumerate(annual[1:], 1)]
                    for title, columns in (
                        ("税基与所得税（元；计提与预计付款分别列示）", (0, 1, 2, 3)),
                        ("增值税与其他现金税费（元；净额和舍入差额分列）", (0, 4, 5, 6, 7)),
                    ):
                        names = ("运营年", "应税所得", "所得税计提", "所得税预计付款",
                                 "其他现金税费", "增值税净现金额", "列示舍入差额", "项目现金税费合计")
                        _add_table(document, [names[index] for index in columns],
                                   [[row[index] for index in columns] for row in tax_rows], title,
                                   layout_type="ANNUAL_LEDGER_TABLE", continuation_identity=reader_preview)
                    taxes = [row.get("cash_tax_total_project") for row in annual[1:]]
                    lifecycle = model.value("financial.tax.cash_lifecycle")
                    if (len(taxes) == 25 and all(isinstance(tax, (int, float, Decimal)) and
                                                  not isinstance(tax, bool) for tax in taxes)
                            and isinstance(lifecycle, (int, float, Decimal)) and not isinstance(lifecycle, bool)):
                        displayed = sum(Decimal(format_amount(tax).replace(",", "")) for tax in taxes)
                        discrepancy = Decimal(format_amount(lifecycle).replace(",", "")) - displayed
                        document.add_paragraph(
                            f"25个运营年度显示值合计{format_amount(displayed)}{' ' if reader_preview else ''}元，"
                            f"全期现金税费指标为{format_amount(lifecycle)}{' ' if reader_preview else ''}元；"
                            f"两者展示差额（全期指标减年度显示值之和）为{format_amount(discrepancy)}{' ' if reader_preview else ''}元。"
                            "年度与全期分别由未取整账簿计算后列示，不把此差额填作税款。")
            if item_id == "APP06.01":
                fee_source = model.result.get("evidence", {}).get("financial-ledger", {}).get("trading_fee_payment")
                if fee_source:
                    document.add_paragraph("示例测算按交易费当年发生、当年全额预计支付处理，期初无交易费欠款；"
                                           "这仅是年度预测假设，不代表真实合同或实际付款记录；"
                                           "来源原文及编号见配套资料来源与假设清单。")
                _add_table(document, ["期别", "项目税后净现金流（元）", "资本支出付款（元）", "营运资金增加（元）", "其中更换付款（元）"],
                           _project_cash_word_rows(model), "建设期及运营全期项目现金流（已计算值，非资本金现金流）",
                           widths_cm=(2.2, 4.0, 3.6, 3.5, 3.7), continuation_identity=reader_preview)
                annual_bridge = _project_annual_bridge_rows(model, reader_preview=reader_preview)
                if annual_bridge is not None:
                    detail_rows, bridge_rows = annual_bridge
                    for title, names, columns in (
                        ("运营收益及交易费（元；自用节费不是银行到账）",
                         ("期别", "上网回款", "自用节费", "预计另付交易费"), (0, 1, 2, 3)),
                        ("运营支出及收支净额（元；尾差仅为显示）",
                         ("期别", "运维现金", "项目现金税费", "列示舍入差额", "运营收支净额"), (0, 4, 5, 6, 7)),
                    ):
                        _add_table(document, list(names), [[row[index] for index in columns] for row in detail_rows],
                                   title, layout_type="ANNUAL_LEDGER_TABLE", continuation_identity=reader_preview)
                    for title, names, columns in (
                        ("建设及年度资本现金事件（元；更换已含在资本支出）",
                         ("期别", "运营收支净额", "资本支出付款", "营运资金增加"), (0, 1, 2, 3)),
                        ("营运资金回收与项目现金流（元；终期资产现金单列）",
                         ("期别", "营运资金回收", "终期资产现金", "项目净现金流"), (0, 4, 5, 6)),
                    ):
                        _add_table(document, list(names), [[row[index] for index in columns] for row in bridge_rows],
                                   title, layout_type="ANNUAL_LEDGER_TABLE", continuation_identity=reader_preview)
                    final_ledger = model.result.get("evidence", {}).get("financial-ledger", {}).get("annual", [])
                    final_row = next((row for row in final_ledger if row.get("period") == "OPERATING_YEAR_25"), None)
                    if final_row is not None:
                        document.add_paragraph(
                            f"终期勾稽：第25年营运资金回收{_word_number(final_row.get('working_capital_release'))}"
                            f"{' ' if reader_preview else ''}元，" +
                            ("终期资产现金按本次测算为 0 元；" if reader_preview
                             else "终期资产现金按当前canonical为0元；")
                            + "因此第25年净现金流与运营收支的差额由营运资金回收解释，"
                            "不是未列示的残值或其他未知收款。"
                        )
                else:
                    document.add_paragraph("逐期付现账簿、终期来源或已计算项目现金流缺失／不一致；"
                                           "本页不能声称已完成全期收支桥，须在计算层重新核验。")
            if item_id == "APP06.02":
                equity = model.metric("financial.phase3e.equity-investor-cash-flow")
                if equity and equity.get("status") != "CALCULATED":
                    document.add_paragraph("资本金现金流尚未形成可列示的逐期序列；该缺口仅限资本金口径，"
                                           "不撤销APP06.01已计算的项目全期现金流。具体阻断实例和原因见测算模型 M15。")
            if item_id == "APP07.02":
                dscr = model.metric("financial.phase3e.dscr")
                if dscr and dscr.get("status") == "UNDEFINED" and dscr.get("reason") == "ZERO_DEBT_SERVICE":
                    document.add_paragraph("本项目债务服务为零，DSCR在原计算契约中为未定义而非0倍；"
                                           "无债务事实与零分母状态同时成立，不将其改写为已计算或其他口径的不适用。")
            if item_id == "APP10.01":
                explanations = {
                    "NO_REAL_PROJECT_VERIFICATION": ("真实工程条件未验证", "取得权属、现场工程和接网原件"),
                    "INTERVAL_MEAN_NOT_SUBINTERVAL_CLIPPING": ("逐时均值不能表示瞬时削峰", "取得更细时段的设备和电网约束数据"),
                    "REPEATED_RESOURCE_YEAR_NOT_MULTIPLE_OBSERVED_YEARS": ("多年发电只重复合成年资源", "取得多年授权的逐时气象资料"),
                    "REPLACEMENT_YEAR_START_AND_UNIFORM_DOWNTIME_NOT_REAL_DATES": ("更换停机并非实际日期", "取得设备寿命与真实施工窗口"),
                    "INTERVAL_MEAN_SAME_GRID_NOT_INSTANTANEOUS_LOAD_MATCH": ("逐时匹配不代表瞬时自用", "取得真实厂区负荷及计量曲线"),
                    "ECONOMIC_BASIS_NOT_TAX_PAYMENT_OR_CURRENCY_CONVERSION": ("经济收益不等同实际税款或收款", "取得税单与结算凭证"),
                    "REPEATED_LOAD_AND_BASE_PERIOD_PRICES_ARE_EXPLICIT_SCENARIOS_NOT_OBSERVED_FUTURE_YEARS":
                        ("负荷与价格的后续年份仍为情景", "取得连续负荷与有效交易价格资料"),
                    "GRID_ACCEPTANCE_UNCONFIRMED_SCENARIO_NOT_APPROVAL": ("可交付电量以接入条件为前提", "取得正式接网及保护计量意见"),
                    "TRANSACTION_FEE_PAYMENT_SYNTHETIC_ASSUMPTION": ("交易费支付仅为合成安排", "取得合同账期及支付记录"),
                    "PHASE3E_PARTIAL_MISSING_FROZEN_INPUTS": ("部分经济评价指标仍受阻", "补齐各指标专属的现金事件与依据"),
                    "SOURCED_PROJECT_NPV_SYNTHETIC_ONLY": ("项目净现值不代表实际投资批准", "取得工程报价、业主权利及真实交易资料"),
                }
                titles = {
                    "NO_REAL_PROJECT_VERIFICATION": "真实项目条件", "INTERVAL_MEAN_NOT_SUBINTERVAL_CLIPPING": "时段削峰限制",
                    "REPEATED_RESOURCE_YEAR_NOT_MULTIPLE_OBSERVED_YEARS": "多年资源代表性",
                    "REPLACEMENT_YEAR_START_AND_UNIFORM_DOWNTIME_NOT_REAL_DATES": "更换停机日期",
                    "INTERVAL_MEAN_SAME_GRID_NOT_INSTANTANEOUS_LOAD_MATCH": "负荷匹配粒度",
                    "ECONOMIC_BASIS_NOT_TAX_PAYMENT_OR_CURRENCY_CONVERSION": "经济收益与付款口径",
                    "REPEATED_LOAD_AND_BASE_PERIOD_PRICES_ARE_EXPLICIT_SCENARIOS_NOT_OBSERVED_FUTURE_YEARS": "负荷价格情景",
                    "GRID_ACCEPTANCE_UNCONFIRMED_SCENARIO_NOT_APPROVAL": "接网认可条件",
                    "TRANSACTION_FEE_PAYMENT_SYNTHETIC_ASSUMPTION": "交易费计划付款",
                    "PHASE3E_PARTIAL_MISSING_FROZEN_INPUTS": "部分评价指标受阻",
                    "SOURCED_PROJECT_NPV_SYNTHETIC_ONLY": "合成项目净现值",
                }
                statuses = {"BLOCKED": "阻断", "KNOWN_LIMITATION": "已知限制", "DECLARED_SCENARIO": "声明情景",
                            "CONDITIONAL": "待条件核验", "ASSUMED": "合成假设", "PARTIAL": "部分完成"}
                if pv_type == "utility_scale_ground":
                    explanations["REPEATED_LOAD_AND_BASE_PERIOD_PRICES_ARE_EXPLICIT_SCENARIOS_NOT_OBSERVED_FUTURE_YEARS"] = (
                        "后续年份市场价格仍为情景", "取得有效的市场结算价格资料")
                    document.add_paragraph("本项目为全额上网，不存在厂区自用负荷匹配；计算快照中的"
                                           "逐时自用匹配通用限制保留在配套测算模型，不作为本项目的待核事项。")
                findings = [row for row in model.result.get("findings", ())
                            if not (pv_type == "utility_scale_ground" and row.get("code") ==
                                    "INTERVAL_MEAN_SAME_GRID_NOT_INSTANTANEOUS_LOAD_MATCH")]
                _add_table(document, ["核验事项", "状态", "影响判断", "所需材料"],
                           [[titles.get(row.get("code"), "其他待核事项"),
                             statuses.get(row.get("status"), "状态待核"),
                             *explanations.get(row.get("code"), ("影响待专业复核", "取得该项发现的原始证明材料"))]
                            for row in findings],
                           "待复核发现项（原始编码及身份见测算模型 M03；非真实责任人签收）",
                           widths_cm=(3.3, 2.2, 5.3, 6.2), layout_type="ISSUE_TABLE")
            if app_id in {"APP11", "APP12"}:
                appendix_headers, appendix_rows = _appendix_rows(model, item_id)
                if reader_preview and item_id == "APP11.01":
                    appendix_rows = [row[:-1] + [_formula_status(model, row[0], reader_language=True)]
                                     for row in appendix_rows]
                if item_id == "APP11.01" and appendix_rows:
                    document.add_paragraph(("公式阅读导航（下文只介绍相关评价方法；完整定义及逐符号说明见配套资料来源与假设清单的变量-术语词典工作表，不代表各方法均已用于本项目）。"
                                            if reader_preview else
                                            "公式阅读导航（以下仅解释本报告用到的评价路径；完整89条正式定义、原始文字和逐符号边界见下一节与测算模型 M02，不代表89条均已执行）。"),
                                           style="Solar Formula Title")
                    document.add_paragraph("发电与配置：直流装机、逆变容量和损失链确定预测发电；阵列面资源、设备效率、年度衰减与限发分别核对，不把发电量直接视为实际售电量。")
                    document.add_paragraph(
                        ("收益与现金：厂区自用节费及余电销售分别核对用电和结算边界；" if pv_type == "industrial_rooftop"
                         else "收益与现金：集中上网销售按送出及交易结算条件核对，不计厂区自用节费；")
                        + "CAPEX、OPEX、税金、更换和营运资金进入项目年度净现金流，后期更换不冒充首期投资。")
                    document.add_paragraph(_formula_reader_evaluation(model))
                    _add_table(document, ["正式编号", "中文名称", "本次引用与执行"],
                               [[row[0], row[1], row[5]] for row in appendix_rows],
                               "公式索引（不代表全部方法已执行）", continuation_identity=reader_preview)
                    npv_outputs = [m for m in model.metrics if m.get("formula_id") == "F-NPV"]
                    if npv_outputs:
                        document.add_paragraph(_npv_instances_note(model, npv_outputs))
                elif item_id == "APP11.02":
                    definitions = reader_formulas
                    shared, shared_ids = _formula_shared_contracts(definitions)
                    if shared and not reader_preview:
                        document.add_paragraph("共通记法契约（按原文一致性分组）", style="Solar Formula Title")
                        document.add_paragraph("相同契约仅在此处完整定义一次；各公式注明所适用的组号，逐式符号与运算检查仍独立列出。")
                        for label, text, number in shared:
                            document.add_paragraph(f"{label}第{number}组：{text}")
                    dimension_texts, dimension_ids = _formula_dimensional_contracts(definitions)
                    if dimension_texts and not reader_preview:
                        document.add_paragraph("共通量纲约定（按有效定义的完整文本分组）", style="Solar Formula Title")
                        for number, text in enumerate(dimension_texts, 1):
                            document.add_paragraph(f"量纲第{number}组：{text}")
                    for formula_no, formula in enumerate(definitions, 1):
                        fid = formula["formula_id"]
                        formula_title = document.add_paragraph(
                            f"{fid} {formula.get('chinese_name', '未定义')}", style="Solar Formula Title")
                        if reader_preview and fid == "F-STATIC-PAYBACK":
                            formula_title.paragraph_format.page_break_before = True
                        equation = formula.get("text_equation") or formula.get("latex") or "未提供"
                        unit = formula.get("unit") or "未定义"
                        equation_paragraph(document, math_objects[fid], f"（{formula_no}）")
                        if not reader_preview:
                            original = document.add_paragraph(f"文字表达：{equation}", style="Solar Formula Note")
                            original.paragraph_format.keep_together = True
                            if formula.get("latex"):
                                document.add_paragraph("原始公式记法：" + str(formula["latex"]),
                                                       style="Solar Formula Note")
                        if fid == CONFLICT_ID:
                            document.add_paragraph(("该单位换算口径尚待专业核验；正式使用前须核对单位与换算关系。"
                                                    if reader_preview else
                                                    "显示冲突，方法待裁定：冻结LaTeX与冻结文本及单位定义不一致；数学对象依文本定义排版，不得据此判定公式语义验收通过。"),
                                                   style="Solar Formula Note")
                        document.add_paragraph(f"结果单位：{unit}", style="Solar Formula Note")
                        boundary = str(formula.get("calculation_boundary") or "未定义")
                        if reader_preview and pv_type == "utility_scale_ground" and fid == "F-AVAILABLE-ENERGY":
                            boundary = boundary.split("屋顶若计量点不同", 1)[0].rstrip("，；。") + "。"
                        document.add_paragraph("适用边界：" + _reader_text(boundary))
                        document.add_paragraph("本项目状态：" + _formula_status(model, fid, reader_language=reader_preview))
                        references = [f"{label}第{shared_ids[key, _formula_contract_text(formula[key])]}组"
                                      for key, label in (("operator_definition", "运算符"),
                                                         ("notation_contract", "记法与歧义"),
                                                         ("unit_convention", "单位约定")) if formula.get(key)]
                        if references and not reader_preview:
                            document.add_paragraph("本式共通契约：" + "；".join(references))
                        if formula.get("dimensional_check") and not reader_preview:
                            dimension = dimension_ids[_formula_contract_text(formula["dimensional_check"])]
                            operation = _formula_dimensional_text(formula)
                            document.add_paragraph(f"本式量纲校核：量纲第{dimension}组。" +
                                                   ("方程运算另须核对：" + operation if operation else ""))
                        symbols = [[s.get("symbol") or "未定义", s.get("definition_zh") or "未定义",
                                    s.get("unit") or "未定义"] for s in formula.get("every_symbol_definition", ())]
                        if symbols:
                            _add_table(document, ["完整符号", "中文定义", "单位"], symbols,
                                       "完整符号（仅属于本公式）", widths_cm=(3, 11, 3))
                        index_lines = _formula_index_lines(formula)
                        if index_lines:
                            document.add_paragraph("下标、索引、集合与求和范围：" + "；".join(index_lines))
                elif appendix_rows:
                    if item_id == "APP12.01":
                        terms = json.loads(files("wangbin_solar_pv").joinpath("report-glossary.json")
                                           .read_text(encoding="utf-8"))["terms"]
                        selected = set(_reader_glossary_ids(pv_type))
                        reader_definitions = {
                            "TERM-VAT": "货物和服务增值环节按适用规则计税；实际税率须以项目所在地及业务资料核实。",
                            "TERM-WORKING-CAPITAL": "经营性流动资产减经营性流动负债的净占用；不含已单列现金、债务、税资产负债或受限储备，除非有明确桥项；不与收款法重复调整。",
                        }
                        reader_rows = [[term["chinese_name"], term.get("abbreviation") or "—",
                                        reader_definitions.get(term["term_id"], term["definition_zh"]),
                                        _reader_term_applicability(model, term["term_id"])]
                                       for term in sorted(terms, key=lambda term: (0, {"PV": 0, "DC": 1, "AC": 2}[term["abbreviation"]])
                                                          if term.get("abbreviation") in {"PV", "DC", "AC"} else (1, 0))
                                       if term["term_id"] in selected]
                        # The audit dictionary remains complete below; this index is a navigation aid only.
                        _add_table(document, ["中文术语", "缩写", "简明释义", "本项目适用说明"], reader_rows,
                                   ("本项目常用术语（完整原始定义见资料来源工作簿）" if reader_preview else
                                    "本项目常用术语速览（完整词典见下表）"),
                                   widths_cm=(3.0, 2.2, 5.9, 5.9), layout_type="SUMMARY_TABLE",
                                   continuation_identity=reader_preview)
                        document.add_paragraph("词条用于解释相关概念，不表示本项目已采用该项技术；原始定义及来源见资料来源工作簿。")
                        if not reader_preview:
                            for text, label in _glossary_common_boundaries(terms).items():
                                document.add_paragraph(f"共通使用边界{label}：{text}")
                    if not reader_preview or item_id == "APP12.02":
                        _add_table(document, appendix_headers, appendix_rows,
                                   "完整术语词典" if item_id == "APP12.01" else "单位与符号使用边界",
                                   widths_cm=(2.3, 4.7, 9.0) if reader_preview and item_id == "APP12.02" else None)
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

    document.add_paragraph("术语与公式说明", style="Solar Unnumbered Title")
    document.add_paragraph("完整公式原文、符号、单位、术语定义和来源编号见配套资料来源与假设清单的变量-术语词典工作表；详细计算精度见测算模型。")
    if not reader_preview:
        document.add_paragraph("来源与版本记录", style="Solar Unnumbered Title")
        document.add_paragraph("配套工作簿记录了本次测算使用的输入和计算结果；项目条件变化后须重新核对来源并更新测算，不能直接沿用原评价结论。")
        identity_labels = {"model_version": "模型版本", "run_id": "运行ID", "input_hash": "输入哈希",
                           "source_snapshot_id": "来源快照ID", "result_hash": "结果哈希"}
        _add_table(document, ["身份字段", "统一测算值"],
                   [[identity_labels.get(key, key), str(value)] for key, value in model.identity.items()],
                   "统一测算身份", widths_cm=(3.2, 13.8), nowrap_columns=(1,))
    render_script_o_glyph(document)
    numbering = validate_numbering(document, display_chapters, reader_appendices, reader_appendix_titles,
                                   [formula["formula_id"] for formula in reader_formulas])
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
            "report_content_version": content_version,
            "reader_preview": reader_preview,
            "full_word_appendix_contract": "NOT_SATISFIED_READER_PREVIEW" if reader_preview else "FULL_CONTENT_RETAINED",
            "frozen_word_identity_contract": "NOT_SATISFIED_READER_PREVIEW" if reader_preview else "FULL_CONTENT_RETAINED",
            "word_format_version": WORD_FORMAT.identifier,
            "numbering": numbering,
            **coverage,
            "charts": chart_receipts, "content_checklist": checklist,
            "duplicate_scan": duplicate_scan, "language_scan": language_scan,
            "toc_status": "FIELD_REQUIRES_RENDER_REFRESH",
            "page_size": "A4", "table_policy": "BLACK_WHITE_THREE_LINE_AND_XLSX_TRACEABILITY"}


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
                   editorial_fixture: dict[str, Any] | None = None,
                   content_version: str = REPORT_CONTENT_VERSION,
                   reader_preview: bool = False) -> dict[str, Any]:
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
    raw_name = _source_value(normalized, model.result.get("source_snapshot", {}).get("phase2", {}).get("records", ()),
                             "project.name") or model.result["project_id"]
    cover_name = ((editorial_fixture.get("project_alias") if editorial_fixture else None)
                  or (_cover_project_name(expected_pv_type) if str(raw_name).startswith(("FICTIONAL", "SYNTHETIC"))
                      else str(raw_name)))
    display_name, name_mapping = _safe_stem(cover_name)
    if display_name == cover_name:
        name_mapping = raw_name
    stem = display_name
    files: dict[str, Any] = {}
    started = time.perf_counter()
    docx_path = root / f"{stem}-光伏预可研报告.docx"
    xlsx_path = root / f"{stem}-测算模型.xlsx"
    source_name = f"{stem}-资料来源与假设清单.xlsx"
    if any(path.exists() for path in (docx_path, xlsx_path, root / source_name)):
        raise ContractError("REPORT_OUTPUT_EXISTS")
    artifact_started = time.perf_counter()
    files["F01"] = _write_docx(model, docx_path, cover_name, expected_pv_type,
                                editorial_fixture=editorial_fixture, content_version=content_version,
                                reader_preview=reader_preview)
    files["F01"]["generation_seconds"] = round(time.perf_counter() - artifact_started, 6)
    checklist = files["F01"].pop("content_checklist")
    coverage = _validate_checklist_coverage(checklist)
    duplicate_scan = files["F01"].get("duplicate_scan", {})
    language_scan = files["F01"].get("language_scan", {})
    checklist_path = root / "content-checklist.json"
    checklist_payload = {
        "schema_version": "phase7i-content-checklist-v1",
        "claim_contract_version": "phase7l-central-claim-v1",
        "report_content_version": content_version,
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
        "report_content_version": content_version,
        "reader_preview": reader_preview,
        "frozen_word_appendix_status": ("NOT_SATISFIED_READER_PREVIEW" if reader_preview else
                                        "FULL_CONTENT_RETAINED"),
        "frozen_word_identity_status": ("NOT_SATISFIED_READER_PREVIEW" if reader_preview else
                                        "FULL_CONTENT_RETAINED"),
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
            "WORD_FORMAT_PROFILE": files["F01"].get("word_format_version", "UNKNOWN"),
            "TABLE_LAYOUT": files["F01"].get("table_policy", "UNKNOWN"),
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
                          editorial_fixture: dict[str, Any] | None = None,
                          content_version: str = REPORT_CONTENT_VERSION,
                          reader_preview: bool = False) -> dict[str, Any]:
    return _export_report(result, catalog, workspace, output_dir, formula_map=formula_map,
                          expected_pv_type="industrial_rooftop", phase="PHASE5_INDUSTRIAL_ROOFTOP_REPORT_EXPORT",
                          editorial_fixture=editorial_fixture, content_version=content_version,
                          reader_preview=reader_preview)


def export_ground_report(result: dict[str, Any], catalog, workspace: Workspace, output_dir: str, *, formula_map: dict[str, Any] | None = None,
                         editorial_fixture: dict[str, Any] | None = None,
                         content_version: str = REPORT_CONTENT_VERSION,
                         reader_preview: bool = False) -> dict[str, Any]:
    return _export_report(result, catalog, workspace, output_dir, formula_map=formula_map,
                          expected_pv_type="utility_scale_ground", phase="PHASE6_UTILITY_SCALE_GROUND_REPORT_EXPORT",
                          editorial_fixture=editorial_fixture, content_version=content_version,
                          reader_preview=reader_preview)
