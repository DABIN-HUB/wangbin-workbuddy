"""Approved D2: typed method controls, not a replacement input field dictionary.

No control has a numeric default. A valid partial configuration is not proof
that a selected numerical chain has every required method. `require` fails
closed; the calling calculation declares its branch-specific requirements.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
import re
from urllib.parse import parse_qs, urlsplit

from ..errors import ContractError
from ..schemas import StrictValidator
from ..serialization import digest, dumps
from . import METHOD_SCHEMA_VERSION
from .common import exact_json_numbers

P0_TYPES = ["industrial_rooftop", "utility_scale_ground"]


def _spec(kind, unit, zh, english, boundary, **constraints):
    return {"value_type": kind, "unit": unit, "meaning_zh": zh, "english_name": english,
            "boundary_id": boundary, "constraints": constraints}


def _choice(zh, english, boundary, choices):
    return _spec("string", None, zh, english, boundary, enum=choices)


def _fractions(zh, english, boundary):
    return _spec("array", "1", zh, english, boundary, minItems=1, maxItems=101,
                 items={"type": "number", "minimum": 0, "maximum": 1})


# Only absent executable controls are introduced. Annual degradation, actual
# prices/rates, equipment, asset/loan schedules remain in the frozen 469 fields.
PARAMETERS = {
    "precision.digits": _spec("integer", "digit", "中间计算有效数字位数；非金额显示小数位", "Intermediate decimal significant digits", "NUMERICAL", minimum=34, maximum=1024),
    "precision.abs_tolerance": _spec("number", "1", "按指标单位解释的绝对校验容差", "Absolute numerical comparison tolerance", "NUMERICAL", exclusiveMinimum=0, maximum=Decimal("0.01")),
    "precision.rel_tolerance": _spec("number", "1", "独立数值校验相对容差", "Relative numerical comparison tolerance", "NUMERICAL", exclusiveMinimum=0, maximum=Decimal("0.01")),
    "time.cashflow_timing": _choice("现金流年末或实际日期计量选择", "Cash flow timing convention", "FINANCIAL_TIME", ["YEAR_END", "DATED"]),
    "time.horizon_basis": _choice("评价期与运营期的显式对应，建设年不暗中删除", "Evaluation horizon and operating year interpretation", "FINANCIAL_TIME", ["FINANCIAL_END_YEAR", "OPERATING_YEARS"]),
    "time.day_count": _choice("合同计息与日期折现的年分数规则", "Interest and discount day count convention", "FINANCIAL_TIME", ["ACT_365F", "ACT_ACT", "30E_360"]),
    "thermal.method": _choice("电池温度子模型或无需温度模型的路径", "Cell temperature model selection", "CELL_TEMPERATURE", ["SANDIA", "CELL_TEMPERATURE_SUPPLIED", "NOT_REQUIRED_PR"]),
    "thermal.a": _spec("number", "1", "桑迪亚组件温度指数模型系数a，必须有安装和组件依据", "Sandia module temperature coefficient a", "MODULE_TEMPERATURE", minimum=-20, maximum=0),
    "thermal.b": _spec("number", "s/m", "桑迪亚组件温度风速指数系数b", "Sandia module temperature wind coefficient b", "MODULE_TEMPERATURE", minimum=-10, maximum=0),
    "thermal.delta_temperature": _spec("number", "degC", "参考辐照度下电池与组件温差参数", "Cell to module temperature difference at reference irradiance", "CELL_TEMPERATURE", minimum=0, maximum=100),
    "thermal.minimum_cell_temperature": _spec("number", "degC", "选定组件温度近似的有效温度下界", "Minimum model-valid cell temperature", "CELL_TEMPERATURE", minimum=Decimal("-273.15"), maximum=200),
    "thermal.maximum_cell_temperature": _spec("number", "degC", "选定组件温度近似的有效温度上界", "Maximum model-valid cell temperature", "CELL_TEMPERATURE", minimum=Decimal("-273.15"), maximum=200),
    "constants.stc_irradiance": _spec("number", "kW/m2", "标准测试条件参考辐照度及其明确来源", "Standard Test Conditions reference irradiance", "STC_REFERENCE", exclusiveMinimum=0, maximum=10),
    "constants.stc_cell_temperature": _spec("number", "degC", "标准测试条件电池温度及其明确来源", "Standard Test Conditions cell temperature", "STC_REFERENCE", minimum=Decimal("-273.15"), maximum=200),
    "energy.method": _choice("阵列面辐照性能比法或分时直交流模型", "Energy yield method selection", "ENERGY_MODEL", ["POA_PR", "INTERVAL_DC_AC"]),
    "energy.pr": _spec("number", "1", "明确边界的性能比情景，不能覆盖逐时模型的已算损失", "Explicit Performance Ratio scenario", "PR_PRE_CURTAILMENT", minimum=0, maximum=Decimal("1.5")),
    "energy.auxiliary_kw": _spec("number", "kW", "选定期间和计量边界内尚未扣除的显式站用功率情景；缺失不默认为零", "Explicit auxiliary station power not yet deducted within the selected period and boundary; absence is not zero", "AUXILIARY_POWER", minimum=0),
    "energy.pr_includes_initial_degradation": _spec("boolean", None, "上游性能比是否明确包含首年初始衰减", "Initial degradation included in upstream Performance Ratio", "LOSS_ACCOUNTING"),
    "energy.upstream_included_losses": _spec("array", None, "上游结果已包含的损失ID集合；用于拒绝重复扣损", "Loss identifiers already included upstream", "LOSS_ACCOUNTING", maxItems=100, uniqueItems=True, items={"type": "string", "minLength": 1, "maxLength": 120}),
    "energy.resource_repetition": _choice("明确代表年重复情景或逐年资源输入，不伪装真实多年天气", "Resource year repetition method", "RESOURCE_YEAR", ["EXPLICIT_REPRESENTATIVE_SCENARIO", "YEAR_SPECIFIC"]),
    "energy.dc_allocation": _fractions("各台同规格逆变器的显式直流容量分配比例；数量与原设备表一致且总和为一", "Explicit DC allocation fractions to the declared identical inverters", "INVERTER_DC_ALLOCATION"),
    "degradation.method": _choice("年度固定率或逐段性能滚动方法", "Degradation retention method", "PERFORMANCE_RETENTION", ["ANNUAL", "PIECEWISE"]),
    "degradation.performance_ceiling": _spec("number", "1", "更换恢复后的明确性能上限，非增容默认值", "Declared post-replacement performance ceiling", "PERFORMANCE_RETENTION", exclusiveMinimum=0, maximum=2),
    "replacement.method": _choice("按原始资产更新事件处理或明确无更新情景", "Asset replacement treatment", "ASSET_REPLACEMENT", ["EXPLICIT_ASSET_EVENTS", "NONE_DECLARED"]),
    "replacement.rules": _spec("array", None, "按原更新事件ID关联的显式性能恢复及年度等效停机场景，不替代原资产事实", "Source-linked replacement recovery and equivalent downtime rules", "ASSET_REPLACEMENT", maxItems=100, items={
        "type": "object", "additionalProperties": False,
        "required": ["event_id", "scope", "capacity_fraction", "target_retention", "timing"],
        "properties": {
            "event_id": {"type": "string", "minLength": 1, "maxLength": 96},
            "scope": {"enum": ["MODULES_UNIFORM_FRACTION", "INVERTERS_UNIFORM_FRACTION"]},
            "capacity_fraction": {"type": "number", "exclusiveMinimum": 0, "maximum": 1},
            "target_retention": {"type": ["number", "null"], "minimum": 0, "maximum": 2},
            "timing": {"const": "YEAR_START_RECOVERY_UNIFORM_EQUIVALENT_DOWNTIME"},
            "inverter_ids": {"type": "array", "minItems": 1, "maxItems": 101, "uniqueItems": True,
                             "items": {"type": "string", "minLength": 1, "maxLength": 96}},
        }}),
    "cash.method": _choice("直接现金法或权责与营运资金桥；两者不重叠", "Direct cash or accrual working capital bridge", "CASH_BRIDGE", ["DIRECT_CASH", "ACCRUAL_WORKING_CAPITAL"]),
    "cash.self_use_treatment": _choice("自用节省使用增量避免支出桥，不能伪造到账发票", "Self consumption incremental avoided expenditure bridge", "SELF_USE_CASH", ["INCREMENTAL_AVOIDED_EXPENDITURE", "CONTRACT_PPA"]),
    "cash.collection_fractions": _fractions("逐财务期明确预测收款比例，非自动将开票当已收", "Explicit projected collection fractions by financial period", "RECEIPT_FORECAST"),
    "cash.opex_payment_fractions": _fractions("逐期明确预测运营费用付现比例", "Explicit projected operating payment fractions", "OPEX_CASH_FORECAST"),
    "cash.capex_payment_fractions": _fractions("逐期建设价款付款分配比例；总和须按选定余额桥复核", "Explicit capital expenditure payment allocation fractions", "CAPEX_CASH_FORECAST"),
    "cash.tax_payment_fractions": _fractions("逐期明确所得税预测缴纳比例，计提与付现分别滚动", "Explicit projected income tax payment fractions", "INCOME_TAX_CASH"),
    "cash.vat_payment_fractions": _fractions("逐期增值税预测付现比例，不能用负留抵隐藏欠税", "Explicit projected Value Added Tax payment fractions", "VAT_CASH"),
    "cash.opening_cash": _spec("number", "currency", "主体期初现金明确余额，缺失不能补零", "Explicit opening entity cash balance", "ENTITY_CASH", minimum=0),
    "cash.opening_receivables": _spec("number", "currency", "收款桥期初应收明确余额", "Explicit opening receivables", "RECEIPT_FORECAST", minimum=0),
    "cash.opening_advances": _spec("number", "currency", "收款桥期初预收明确余额", "Explicit opening customer advances", "RECEIPT_FORECAST", minimum=0),
    "cash.terminal_collection_fraction": _spec("number", "1", "终期应收可回收比例的明确情景", "Terminal receivables collection fraction", "TERMINAL_CASH", minimum=0, maximum=1),
    "tax.method": _choice("已提供来源的逐期假设税制或完整核验税制；不内置地区税率", "Source-linked tax method selection", "TAX_LEDGER", ["EXPLICIT_SCENARIO_LEDGER", "VERIFIED_REGIME_LEDGER"]),
    "tax.loss_usage_fraction": _spec("number", "1", "适用期正税基允许使用历史亏损的明确比例", "Declared taxable income loss offset limit", "TAX_LOSS_LEDGER", minimum=0, maximum=1),
    "tax.opening_project_losses": _spec("number", "currency", "无杠杆项目期初亏损余额；非实际主体申报事实", "Opening unlevered project tax losses", "PROJECT_TAX", minimum=0),
    "tax.opening_equity_losses": _spec("number", "currency", "融资后口径期初亏损余额", "Opening levered tax losses", "EQUITY_TAX", minimum=0),
    "tax.opening_income_payable": _spec("number", "currency", "所得税期初应交未交余额", "Opening income tax payable", "INCOME_TAX_CASH", minimum=0),
    "tax.opening_income_prepaid": _spec("number", "currency", "所得税期初预缴余额", "Opening prepaid income tax", "INCOME_TAX_CASH", minimum=0),
    "tax.opening_vat_credit": _spec("number", "currency", "期初可用增值税留抵余额", "Opening Value Added Tax credit balance", "VAT_CREDIT", minimum=0),
    "tax.opening_vat_payable": _spec("number", "currency", "期初增值税应交未交余额", "Opening Value Added Tax payable", "VAT_CASH", minimum=0),
    "tax.self_use_basis": _choice("自用节省所得税反事实边界，不自动认定真实税制", "Counterfactual self use income tax treatment", "SELF_USE_TAX", ["TAXABLE_INCREMENTAL_SAVING", "NONTAXABLE_DECLARED_SCENARIO"]),
    "tax.asset_depreciation_timing": _choice("明确折旧起算规则，部分年度不能当完整年", "Asset depreciation commencement convention", "DEPRECIATION", ["DAILY_PRORATA_ACT_ACT", "NEXT_MONTH", "FULL_OPERATION_YEAR"]),
    "tax.vat_refund_fraction": _spec("number", "1", "有明确资格假设的留抵退还比例，不能凭空产生退税", "Declared eligible Value Added Tax refund fraction", "VAT_REFUND", minimum=0, maximum=1),
    "debt.drawdown_basis": _choice("债务提款按已给计划或明确比例情景", "Debt drawdown schedule basis", "DEBT_CASH", ["EXPLICIT_RAW_SCHEDULE", "CAPEX_PROPORTIONAL_SCENARIO", "NO_DEBT_DECLARED"]),
    "debt.principal_payment_fractions": _fractions("逐期预测本金实付比例，独立于应还计划", "Explicit projected principal payment fractions", "DEBT_PRINCIPAL_CASH"),
    "debt.interest_payment_fractions": _fractions("逐期预测利息实付比例，独立于计提利息", "Explicit projected interest payment fractions", "DEBT_INTEREST_CASH"),
    "debt.interest_capitalization_fractions": _fractions("逐期未付利息资本化比例，与付现互斥", "Explicit unpaid interest capitalization fractions", "DEBT_CAPITALIZATION"),
    "debt.fee_payment_fractions": _fractions("逐期融资费用实付比例，不能默认应付即已付", "Explicit financing fee cash payment fractions", "DEBT_FEE_CASH"),
    "debt.opening_principal": _spec("number", "currency", "债务期初本金明确余额", "Explicit opening principal balance", "DEBT_PRINCIPAL", minimum=0),
    "debt.opening_interest_payable": _spec("number", "currency", "债务期初未资本化应付利息余额", "Opening noncapitalized interest payable", "DEBT_INTEREST", minimum=0),
    "equity.distribution_fractions": _fractions("逐期可供分配现金的明确分配比例；滞留现金另记", "Explicit shareholder distribution fractions", "EQUITY_DISTRIBUTIONS"),
    "equity.minimum_cash_reserve": _spec("number", "currency", "明确最低主体现金储备要求", "Explicit minimum entity cash reserve", "ENTITY_CASH", minimum=0),
    "cfads.method": _choice("偿债前现金与强制更新支出的契约情景范围", "Cash Flow Available for Debt Service scope", "CFADS", ["OPERATING_CASH_AFTER_TAX_MANDATORY_CAPEX", "EXPLICIT_PROTOCOL"]),
    "irr.minimum_rate": _spec("number", "1", "内部收益率搜索域下界，严格大于负一", "Internal Rate of Return search lower bound", "IRR_DOMAIN", exclusiveMinimum=-1),
    "irr.method": _choice("以有理现金流多项式隔离全部实根，不用单次局部求根冒充唯一解", "Exact rational cash flow polynomial real root isolation", "IRR_METHOD", ["EXACT_RATIONAL_POLYNOMIAL_ISOLATION"]),
    "irr.maximum_rate": _spec("number", "1", "内部收益率搜索域上界，不挑选有利解", "Internal Rate of Return search upper bound", "IRR_DOMAIN", exclusiveMinimum=-1),
    "irr.root_tolerance": _spec("number", "1", "根隔离区间精度，需同时核验净现值残差", "Internal Rate of Return isolating interval tolerance", "IRR_DOMAIN", exclusiveMinimum=0, maximum=Decimal("0.001")),
    "irr.maximum_degree": _spec("integer", "year", "年度现金流多项式求根次数硬预算", "Maximum periodic cash flow polynomial degree", "IRR_RESOURCES", minimum=1, maximum=100),
    "break_even.minimum_price": _spec("number", "currency/kWh", "盈亏平衡电价有界搜索下界，允许明确负价", "Net Present Value break even price lower bound", "BREAK_EVEN_PRICE"),
    "break_even.method": _choice("全链重算的已证明单调搜索或分段仿射全根搜索；缺完整性证明不能宣称全根", "Full recalculation certified monotone or piecewise affine price root search", "BREAK_EVEN_METHOD", ["CERTIFIED_MONOTONE_RECALCULATION", "PIECEWISE_AFFINE_ALL_ROOTS"]),
    "break_even.maximum_price": _spec("number", "currency/kWh", "盈亏平衡电价有界搜索上界", "Net Present Value break even price upper bound", "BREAK_EVEN_PRICE"),
    "break_even.price_tolerance": _spec("number", "currency/kWh", "盈亏电价根区间宽度容差", "Break even price interval tolerance", "BREAK_EVEN_PRICE", exclusiveMinimum=0),
    "break_even.maximum_iterations": _spec("integer", "iteration", "盈亏平衡逐次全链重算次数上限", "Maximum full-chain break even iterations", "BREAK_EVEN_RESOURCES", minimum=1, maximum=10000),
    "prices.escalation_fraction": _spec("number", "1", "明确合同价格增长情景，不替代一般通胀或真实电价", "Explicit contractual price escalation scenario", "PRICE_YEAR", exclusiveMinimum=-1),
    "consumption.load_repetition": _choice("负荷逐年给定或明确代表年情景；不声称真实年度自用", "Load year repetition method", "LOAD_YEAR", ["EXPLICIT_REPRESENTATIVE_SCENARIO", "YEAR_SPECIFIC", "NO_LOAD_GROUND", "NO_LOAD_FULL_EXPORT"]),
    "consumption.commercial_export_limit_kw": _spec("number", "kW", "本阶段商业可接受的外送功率上限；与3B物理交付约束分开，缺失不推定无限或零", "Explicit commercially accepted export power ceiling, separate from upstream physical delivery constraints", "COMMERCIAL_EXPORT", minimum=0),
    "settlement.price_source": _choice("外售采用有效期价格表或同时间轴市场序列；不混用二者", "Export settlement price source", "PRICE_SOURCE", ["PERIOD_TABLE", "MARKET_SERIES"]),
    "settlement.revenue_method": _choice("自持避免购电、投资方购电协议固定价/折扣或全额外售；不叠加双方收益", "Owner avoided purchase, investor Power Purchase Agreement fixed or discounted settlement, or export-only revenue", "REVENUE_PERSPECTIVE", ["OWNER_AVOIDED_COST", "PPA_FIXED", "PPA_DISCOUNT", "EXPORT_ONLY"]),
    "settlement.currency": _spec("string", None, "可相加结算项的共同币种，必须等于项目币种；不隐含汇率换算", "Common additive settlement currency, equal to project currency without implicit foreign exchange", "ECONOMIC_BASIS", pattern="^[A-Z]{3}$"),
    "settlement.price_year": _spec("integer", "year", "可相加结算项的共同基准价年，须与原金额信封一致", "Common price reference year consistent with original economic evidence", "ECONOMIC_BASIS", minimum=1900, maximum=2200),
    "settlement.tax_basis": _choice("结算项共同含税或未税口径，混合口径拒绝相加；不是税款计算", "Common tax-inclusive or tax-exclusive settlement basis without calculating tax payments", "ECONOMIC_BASIS", ["inclusive", "exclusive"]),
    "settlement.price_basis": _choice("结算项共同名义或实际价格口径，不自动作通胀转换", "Common nominal or real settlement prices without implicit inflation conversion", "ECONOMIC_BASIS", ["nominal", "real"]),
    "settlement.fee_treatment": _choice("交易费单列扣减或已经包含在合同净价中；不重复扣费", "Separate transaction expense or fee already included in quoted net settlement price", "TRANSACTION_EXPENSE", ["SEPARATE_LEDGER", "ALREADY_IN_PRICE"]),
    "settlement.negative_price_treatment": _choice("有合同和原始负价依据时按带符号单价结算，不擅自增加经济弃光策略", "Settle signed contract prices without inventing economic curtailment dispatch", "NEGATIVE_PRICE", ["SETTLE_SIGNED_CONTRACT_PRICE"]),
    "settlement.ppa_discount_factor": _spec("number", "1", "有明确合同/情景来源的购电协议结算乘数：同段可避免购电单价乘本系数；不得与固定购电协议价混用", "Source-linked Power Purchase Agreement multiplier on the same-interval avoidable purchase price, exclusive of a fixed quoted agreement price", "PPA_SETTLEMENT", minimum=0, maximum=1),
    "settlement.other_benefit_months": _spec("array", None, "按原其他收益row_id显式指定记入月份；不把只有年度的金额自动摊到每月", "Explicit month allocation by original other-benefit row identifier, without fabricated uniform monthly spreading", "OTHER_BENEFIT_ALLOCATION", maxItems=1000000, items={
        "type": "object", "additionalProperties": False, "required": ["row_id", "month"],
        "properties": {"row_id": {"type": "string", "minLength": 1, "maxLength": 96},
                       "month": {"type": "integer", "minimum": 1, "maximum": 12}}}),
    "scenarios.relative_shocks": _spec("array", "1", "明确单因素相对扰动幅度，不内置默认正负百分比", "Explicit relative single factor sensitivity shocks", "SCENARIO_CONTROL", minItems=1, maxItems=50, items={"type": "number", "exclusiveMinimum": -1}),
}


def method_schema():
    string = {"type": "string", "minLength": 1, "maxLength": 4000}
    properties = {}
    for pid, definition in PARAMETERS.items():
        fields = {
            "value": {"type": definition["value_type"], **deepcopy(definition["constraints"])},
            "value_type": {"const": definition["value_type"]}, "unit": {"const": definition["unit"]},
            "meaning_zh": {"const": definition["meaning_zh"]}, "english_name": {"const": definition["english_name"]},
            "version": {"const": "1.0.0"}, "boundary_id": {"const": definition["boundary_id"]},
            "pv_types": {"type": "array", "items": {"enum": P0_TYPES}, "minItems": 1, "uniqueItems": True},
            "source_id": string, "source_reference": string,
            "source_kind": {"enum": ["SYNTHETIC", "USER_PROVIDED", "DOCUMENT_EXTRACTED", "EXTERNAL_SOURCE", "MATHEMATICAL_DEFINITION"]},
            "status": {"enum": ["ASSUMED", "VERIFIED", "UNVERIFIED"]},
            "license_status": {"enum": ["AUTHORIZED", "REQUIRES_REVIEW", "UNKNOWN", "DENIED"]},
            "reviewer": {"type": ["string", "null"], "minLength": 1},
        }
        properties[pid] = {"type": "object", "additionalProperties": False, "properties": fields, "required": list(fields)}
    fields = {"schema_version": {"const": METHOD_SCHEMA_VERSION}, "config_id": string,
              "data_mode": {"enum": ["SYNTHETIC", "DECLARED_INPUTS"]},
              "pv_types": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"enum": P0_TYPES}},
              "parameters": {"type": "object", "additionalProperties": False, "properties": properties}}
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": METHOD_SCHEMA_VERSION,
            "type": "object", "additionalProperties": False, "properties": fields, "required": list(fields)}


def make_parameter(parameter_id, value, *, source_id, source_reference, status, source_kind,
                   pv_types=None, license_status="REQUIRES_REVIEW", reviewer=None):
    if parameter_id not in PARAMETERS:
        raise ContractError("UNKNOWN_METHOD_PARAMETER")
    spec = PARAMETERS[parameter_id]
    return {"value": deepcopy(value), "value_type": spec["value_type"], "unit": spec["unit"],
            "meaning_zh": spec["meaning_zh"], "english_name": spec["english_name"], "version": "1.0.0",
            "boundary_id": spec["boundary_id"], "pv_types": list(P0_TYPES if pv_types is None else pv_types),
            "source_id": source_id, "source_reference": source_reference, "source_kind": source_kind,
            "status": status, "license_status": license_status, "reviewer": reviewer}


@dataclass(frozen=True, slots=True)
class MethodConfig:
    _data: dict

    @classmethod
    def from_dict(cls, data):
        exact_json_numbers(data)
        if next(StrictValidator(method_schema()).iter_errors(data), None) is not None:
            raise ContractError("METHOD_CONFIG_SCHEMA")
        for pid, parameter in data["parameters"].items():
            for reference in (parameter["source_id"], parameter["source_reference"]):
                if re.search(r"(?:^|\s)[A-Za-z]:[\\/]", reference) or reference.startswith(("/", "\\", "file:")):
                    raise ContractError("PRIVATE_PATH_REFERENCE", pid)
                for address in re.findall(r"https?://[^\s]+", reference):
                    try:
                        url = urlsplit(address)
                        credential_keys = {"token", "api_key", "api-key", "password", "access_token", "client_secret", "secret", "authorization"}
                        if url.username or url.password or any(k.casefold() in credential_keys for k in parse_qs(url.query, keep_blank_values=True)):
                            raise ContractError("CREDENTIAL_URL", pid)
                    except ValueError as error:
                        if isinstance(error, ContractError):
                            raise
                        raise ContractError("METHOD_SOURCE_REFERENCE", pid) from None
            if not set(data["pv_types"]) <= set(parameter["pv_types"]):
                raise ContractError("METHOD_PARAMETER_CATEGORY", pid)
            if parameter["source_kind"] == "SYNTHETIC" and (data["data_mode"] != "SYNTHETIC" or parameter["status"] != "ASSUMED"):
                raise ContractError("SYNTHETIC_IS_NOT_VERIFIED", pid)
            if parameter["license_status"] == "DENIED":
                raise ContractError("METHOD_SOURCE_NOT_AUTHORIZED", pid)
            if parameter["status"] == "VERIFIED" and (not parameter["reviewer"] or parameter["license_status"] != "AUTHORIZED"):
                raise ContractError("METHOD_VERIFICATION_EVIDENCE", pid)
        parameters = data["parameters"]
        for low, high in [("irr.minimum_rate", "irr.maximum_rate"), ("break_even.minimum_price", "break_even.maximum_price"), ("thermal.minimum_cell_temperature", "thermal.maximum_cell_temperature")]:
            if low in parameters and high in parameters and parameters[low]["value"] >= parameters[high]["value"]:
                raise ContractError("METHOD_PARAMETER_ORDER", low)
        return cls(deepcopy(data))

    @property
    def hash(self):
        return digest(self._data)

    @property
    def data_mode(self):
        return self._data["data_mode"]

    def to_dict(self):
        return deepcopy(self._data)

    def require(self, parameter_id):
        record = self._data["parameters"].get(parameter_id)
        if record is None or record["status"] not in {"ASSUMED", "VERIFIED"}:
            raise ContractError("BLOCKED_METHOD_REVIEW", parameter_id)
        if self.data_mode != "SYNTHETIC" and record["source_kind"] == "SYNTHETIC":
            raise ContractError("BLOCKED_METHOD_REVIEW", parameter_id)
        return deepcopy(record["value"])

    def evidence(self, parameter_ids=None):
        ids = self._data["parameters"] if parameter_ids is None else parameter_ids
        return {pid: deepcopy(self._data["parameters"][pid]) for pid in ids}
