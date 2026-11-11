"""Per-item editorial claim bindings for the frozen solar-PV report outline.

Only canonical normalized inputs and canonical metrics may support a claim. An
editorial fixture is never an evidence source. Missing results remain missing.
"""
from __future__ import annotations

from datetime import date
from zoneinfo import ZoneInfo
from functools import lru_cache
from decimal import Decimal
import json
from pathlib import Path
from typing import Any, Callable

from .report_appendix_findings import appendix_finding
from .report_display_numbers import decision_number, decision_percent

# Frozen outline field bindings, copied by item ID (not inferred from the title).
CHAPTER_FIELDS: dict[str, tuple[str, ...]] = {
    # OUTLINE_FIELDS
    'CH01': (
        'project.name project.pv_type site.address',  # CH01.01
        'system.dc_capacity system.ac_capacity project.evaluation_years roof.remaining_life site.rights_status site.land_classification',  # CH01.02
        'capex.items finance.project_discount_rate finance.equity_discount_rate',  # CH01.03
        'project.sales_mode load.series tariff.periods',  # CH01.04
        'risk.items targets.project_irr targets.payback_years',  # CH01.05
    ),
    'CH02': (
        'project.owner project.developer',  # CH02.01
        'project.evaluation_date project.evaluation_years project.currency project.price_basis project.cashflow_tax_basis',  # CH02.02
        'policy.applicability',  # CH02.03
        'attachments.register resource.period_start resource.period_end',  # CH02.04
        'scenarios.options risk.items',  # CH02.05
    ),
    'CH03': (
        'project.owner project.investor project.operator',  # CH03.01
        'project.pv_type site.address site.latitude site.longitude',  # CH03.02
        'project.ownership_mode site.rights_holder site.rights_document_id site.rights_expiry project.evaluation_date project.evaluation_years',  # CH03.03
        'project.sales_mode load.monthly_bills tariff.contract_id',  # CH03.04
        'system.dc_capacity targets.budget_ceiling targets.project_irr',  # CH03.05
    ),
    'CH04': (
        'site.address site.latitude site.longitude site.crs site.boundary_vertices',  # CH04.01
        'site.elevation site.terrain_slope site.total_area site.usable_area site.exclusion_area',  # CH04.02
        'site.rights_holder site.land_classification site.rights_status site.rights_expiry',  # CH04.03
        'site.shading_fraction roof.allowable_additional_load roof.design_added_load roof.remaining_life',  # CH04.04
        'site.transport_access site.ecology_reference site.disaster_reference site.local_restrictions',  # CH04.05
        'site.geotechnical_reference site.flood_reference risk.items',  # CH04.06
    ),
    'CH05': (
        'resource.dataset_id resource.version resource.provider resource.license_id',  # CH05.01
        'resource.monthly.ghi resource.monthly.dni resource.monthly.dhi resource.monthly.poa',  # CH05.02
        'resource.monthly.ambient_temperature resource.monthly.wind_speed resource.monthly.month',  # CH05.03
        'resource.annual_comparison resource.is_tmy resource.tmy_method',  # CH05.04
        'resource.model_method resource.poa_boundary layout.tilt layout.azimuth',  # CH05.05
        'resource.uncertainty_fraction resource.uncertainty_basis resource.timeseries',  # CH05.06
    ),
    'CH06': (
        'site.usable_area layout.fire_setback layout.ground_coverage_ratio',  # CH06.01
        'system.module_count system.module_length system.module_width layout.row_pitch',  # CH06.02
        'system.dc_capacity system.ac_capacity system.dc_ac_ratio',  # CH06.03
        'scenarios.options',  # CH06.04
        'targets.budget_ceiling grid.available_capacity risk.items',  # CH06.05
        'storage.base_pv_type storage.energy_capacity agri.minimum_light_transmission',  # CH06.06
    ),
    'CH07': (
        'system.module_model system.module_power system.module_efficiency system.inverter_model system.inverter_unit_ac',  # CH07.01
        'system.mounting_type layout.azimuth layout.tilt layout.row_pitch',  # CH07.02
        'system.modules_per_string system.parallel_strings system.module_voc system.inverter_max_dc_voltage system.inverter_max_input_current',  # CH07.03
        'system.losses',  # CH07.04
        'system.topology system.capacity_boundary grid.connection_point',  # CH07.05
        'storage.coupling storage.soc_min storage.soc_max storage.fire_safety_reference',  # CH07.06
    ),
    'CH08': (
        'resource.model_method resource.poa_boundary system.capacity_boundary',  # CH08.01
        'resource.monthly system.losses system.first_year_degradation system.annual_degradation',  # CH08.02
        'system.degradation_segments system.annual_degradation assets.replacements',  # CH08.03
        'system.dc_capacity system.ac_capacity system.losses',  # CH08.04
        'system.unavailability grid.curtailment_assumption',  # CH08.05
        'resource.uncertainty_basis risk.items',  # CH08.06
    ),
    'CH09': (
        'grid.connection_point grid.connection_voltage grid.metering_boundary',  # CH09.01
        'grid.transformer_capacity grid.power_factor grid.available_capacity grid.line_length grid.export_power_limit grid.opinion_status',  # CH09.02
        'grid.upgrade_plan grid.protection_plan capex.items',  # CH09.03
        'grid.opinion_status grid.opinion_attachment_id grid.opinion_valid_until grid.transaction_opinion',  # CH09.04
        'grid.export_power_limit grid.curtailment_basis risk.items',  # CH09.05
    ),
    'CH10': (
        'load.monthly_bills load.series load.timezone',  # CH10.01
        'project.sales_mode grid.export_power_limit load.series',  # CH10.02
        'tariff.periods tariff.non_avoidable_charges',  # CH10.03
        'tariff.contract_id tariff.ppa_price tariff.revenue_share tariff.transaction_fee',  # CH10.04
        'tariff.market_series revenue.other_items',  # CH10.05
        'storage.dispatch storage.charge_efficiency storage.discharge_efficiency storage.grid_charging',  # CH10.06
    ),
    'CH11': (
        'site.boundary_vertices layout.row_pitch layout.fire_setback',  # CH11.01
        'site.geotechnical_reference system.mounting_type fishery.foundation_method',  # CH11.02
        'roof.structure_report_id roof.design_added_load roof.fire_access_reference',  # CH11.03
        'site.transport_access site.flood_reference roof.waterproof_plan',  # CH11.04
        'risk.items capex.items',  # CH11.05
    ),
    'CH12': (
        'environment.grid_emission_factor environment.factor_period',  # CH12.01
        'site.ecology_reference environment.approval_reference',  # CH12.02
        'environment.fire_reference roof.fire_access_reference storage.fire_safety_reference',  # CH12.03
        'site.rights_holder public.asset_authorization residential.property_consent',  # CH12.04
        'policy.applicability risk.items',  # CH12.05
    ),
    'CH13': (
        'project.developer project.operator schedule.tasks',  # CH13.01
        'schedule.tasks schedule.construction_start schedule.commissioning_date',  # CH13.02
        'schedule.tasks.predecessor_ids schedule.tasks.critical_path',  # CH13.03
        'risk.items site.transport_access',  # CH13.04
        'targets.risk_preference risk.items',  # CH13.05
    ),
    'CH14': (
        'capex.estimate_basis capex.user_budget project.currency',  # CH14.01
        'capex.items',  # CH14.02
        'capex.items.category site.geotechnical_reference',  # CH14.03
        'capex.items.category capex.contingency_rate',  # CH14.04
        'capex.includes_construction_interest finance.debt_schedule schedule.tasks',  # CH14.05
        'capex.items.tax_included capex.items.vat_rate capex.includes_storage capex.includes_land',  # CH14.06
    ),
    'CH15': (
        'opex.items',  # CH15.01
        'assets.depreciation',  # CH15.02
        'assets.replacements storage.replacement_rule',  # CH15.03
        'tax.regime_reference tax.corporate_income_rate tax.vat_recovery_timing tax.surcharge_basis',  # CH15.04
        'opex.items assets.depreciation assets.replacements',  # CH15.05
    ),
    'CH16': (
        'tariff.periods tariff.market_series revenue.other_items assets.depreciation.residual_value',  # CH16.01
        'capex.items opex.items tax.regime_reference finance.working_capital project.sales_mode',  # CH16.02
        'finance.debt_schedule finance.debt_ratio finance.loan_rate',  # CH16.03
        'finance.project_discount_rate finance.equity_discount_rate project.price_basis project.evaluation_years finance.cashflow_timing project.cashflow_tax_basis',  # CH16.04
        'targets.payback_years targets.payback_basis',  # CH16.05
        'system.capacity_boundary grid.export_power_limit project.cashflow_tax_basis',  # CH16.06
        'finance.cfads_definition finance.debt_schedule.dscr_covenant',  # CH16.07
        'targets.project_irr targets.equity_irr targets.budget_ceiling',  # CH16.08
    ),
    'CH17': (
        'scenarios.options capex.items tariff.periods resource.uncertainty_fraction',  # CH17.01
        'scenarios.options',  # CH17.02
        'targets.project_irr targets.equity_irr targets.payback_years',  # CH17.03
        'risk.items policy.applicability',  # CH17.04
        'scenarios.options',  # CH17.05
    ),
    'CH18': (
        'risk.items targets.project_irr targets.payback_years',  # CH18.01
        'site.rights_status grid.opinion_status risk.items',  # CH18.02
        'targets.risk_preference scenarios.options',  # CH18.03
        'risk.items attachments.register',  # CH18.04
        'schedule.tasks project.evaluation_date',  # CH18.05
    ),
}

CHAPTER_FIELDS = {chapter: tuple(part.split() for part in parts)
                  for chapter, parts in CHAPTER_FIELDS.items()}

# Explicit result bindings. Empty tuples mean the question needs documentary
# evidence, not a loosely related metric from the same chapter.
CHAPTER_METRICS: dict[str, tuple[str, ...]] = {
    "CH01": ("", "dc_capacity ac_capacity dc_ac_ratio energy.year.1 energy.mean_annual", "financial.capex.total financial.unit_investment financial.phase3e.project_irr financial.phase3e.project_npv financial.phase3e.lcoe", "consumption.year.1 revenue.year.1 energy.delivered.year.1", ""),
    "CH02": ("", "financial.phase3e.project_cash_flow financial.phase3e.equity-investor-cash-flow", "", "", ""),
    "CH03": ("", "", "", "consumption.year.1 revenue.year.1", "dc_capacity"),
    "CH04": ("", "", "", "", "", ""),
    "CH05": ("", "", "", "", "", ""),
    "CH06": ("dc_capacity", "dc_capacity", "dc_capacity ac_capacity dc_ac_ratio", "", "", ""),
    "CH07": ("dc_capacity ac_capacity", "", "", "", "", ""),
    "CH08": ("energy.year.1", "energy.monthly.year.1 energy.year.1", "energy.annual_array", "pr_observed.year.1 equivalent_hours.year.1 capacity_factor.year.1", "available_kwh.year.1 energy.delivered.year.1", ""),
    "CH09": ("", "ac_capacity", "", "", ""),
    "CH10": ("consumption.year.1", "consumption.year.1 energy.delivered.year.1", "revenue.year.1", "revenue.year.1", "", ""),
    "CH11": ("", "", "", "", ""),
    "CH12": ("", "", "", "", ""),
    "CH13": ("", "", "", "", ""),
    "CH14": ("financial.capex.total", "financial.capex.total", "financial.capex.total", "", "", "financial.unit_investment"),
    "CH15": ("financial.opex.cash_lifecycle", "financial.asset.ending_book_value", "", "financial.tax.cash_lifecycle", "financial.opex.cash_lifecycle"),
    "CH16": ("revenue.year.1", "financial.phase3e.project_cash_flow", "financial.phase3e.equity-investor-cash-flow", "financial.phase3e.project_npv financial.phase3e.project_irr financial.phase3e.static_payback financial.phase3e.dynamic_payback", "financial.phase3e.static_payback financial.phase3e.dynamic_payback", "financial.phase3e.lcoe energy.delivered.year.1", "financial.phase3e.dscr financial.phase3e.cfads", "financial.phase3e.break-even-price financial.phase3e.investment-hurdle-gap"),
    "CH17": ("", "", "", "", ""),
    "CH18": ("", "", "", "", ""),
}
CHAPTER_METRICS = {chapter: tuple(part.split() for part in parts) for chapter, parts in CHAPTER_METRICS.items()}

# Every appendix subitem has its own question, documentary binding and result
# binding. The second item is not an automatic duplicate of the first.
APPENDIX_TITLES = {
    'APP01.01': '来源与附件索引',
    'APP01.02': '输入血缘索引',
    'APP02.01': '月度气象与资源',
    'APP02.02': '月度能量平衡',
    'APP03.01': '设备与布局原子参数',
    'APP03.02': '损失与衰减链',
    'APP04.01': '逐项含税及分类明细',
    'APP04.02': '报价与投资勾稽',
    'APP05.01': '运营更换及资产计划',
    'APP05.02': '适用税与年度勾稽',
    'APP06.01': '项目投资全期现金流',
    'APP06.02': '资本金全期现金流',
    'APP07.01': '有债务偿债计划',
    'APP07.02': '无债务或零分母说明',
    'APP08.01': '单因素与组合底表',
    'APP08.02': '阈值与变化方向核对',
    'APP09.01': '政策条款与有效期',
    'APP09.02': '核验与限制意见',
    'APP10.01': '待核与冲突清单',
    'APP10.02': '推进条件与里程碑',
    'APP11.01': '全部公式注册',
    'APP11.02': '全部符号逐一解释',
    'APP12.01': '中英全称缩写',
    'APP12.02': '首次释义与单位区分',
    'APP13.01': '同源版本与哈希',
    'APP13.02': '成熟度与审阅边界',
}

APPENDIX_RULES: dict[str, tuple[str, str, tuple[str, ...], tuple[str, ...]]] = {
    "APP01.01": ("本次使用的资料是否逐份有身份、授权和可读位置？", "核验来源登记、附件位置与授权，不把资料登记当作已读全文。", (), ()),
    "APP01.02": ("关键输入能否回溯到字段实例与原始来源？", "逐项核对输入血缘，缺少实例位置时保留追溯缺口。", (), ()),
    "APP02.01": ("12个月气象资料的分量、覆盖和单位能否核查？", "取得资源原始月表及授权；月发电量不能倒推辐照分量。", ("resource.monthly", "resource.period_start", "resource.period_end"), ()),
    "APP02.02": ("月度发电、消纳与交付电量能否同边界对账？", "核对时区、月度能量和结算边界，不由发电量代替交付。", ("resource.monthly", "load.series"), ("energy.monthly.year.1", "energy.year.1", "energy.delivered.year.1", "consumption.year.1", "revenue.year.1")),
    "APP03.01": ("设备和布局的原子参数是否有可核验型号？", "取得组件、逆变器和支架数据表并逐字段复核。", ("system.module_model", "system.module_count", "system.module_power", "system.module_voc", "system.module_vmp", "system.module_isc", "system.module_imp", "system.modules_per_string", "system.inverter_model", "system.inverter_count", "system.inverter_unit_ac", "system.inverter_mppt_min", "system.inverter_mppt_max", "system.inverter_max_dc_voltage", "system.inverter_max_input_current", "layout.tilt", "layout.azimuth", "layout.row_pitch", "layout.fire_setback"), ("dc_capacity", "ac_capacity")),
    "APP03.02": ("每项损失与退化是否只计入一次？", "核查损失顺序、已含标志与衰减时点。", ("system.losses", "system.annual_degradation"), ("energy.annual_array",)),
    "APP04.01": ("费用清单是否覆盖设备、土建、预备与专项投资？", "逐项核实工程量、数量单价、税与分类专项范围。", ("capex.items", "capex.includes_land", "capex.includes_storage"), ("financial.capex.total",)),
    "APP04.02": ("报价、付款与投资总额能否勾稽？", "补充报价有效期及付款时点，避免应付替代实付。", ("capex.items", "finance.debt_schedule"), ("financial.capex.total",)),
    "APP05.01": ("年度现金运维与更换、非现金折旧是否分账？", "核对全期运维、更换与残值计划，折旧不作为现金支出。", ("opex.items", "assets.depreciation", "assets.replacements"), ("financial.opex.cash_lifecycle", "financial.phase3e.project_cash_flow")),
    "APP05.02": ("适用税制与实际税金能否逐年衔接？", "取得税制与现金支付依据，对账应计、应付及实付。", ("tax.regime_reference", "tax.vat_recovery_timing"), ("financial.tax.cash_lifecycle", "financial.phase3e.project_cash_flow")),
    "APP06.01": ("建设至终期的项目投资现金事件是否闭合？", "取得有日期的投资、税、营运资金和终期收付记录。", ("finance.working_capital",), ("financial.phase3e.project_cash_flow",)),
    "APP06.02": ("资本金全期现金流是否独立包含提款和偿债？", "核实股东出资、提款、本息和分配，不能沿用项目现金流。", ("finance.debt_schedule",), ("financial.phase3e.equity-investor-cash-flow",)),
    "APP07.01": ("有债务时偿债计划与可偿债现金是否逐期匹配？", "取得合同还本付息日程与CFADS定义后计算覆盖倍数。", ("finance.debt_schedule", "finance.cfads_definition"), ("financial.phase3e.dscr",)),
    "APP07.02": ("无债务与偿债零分母是否被正确区分？", "核查债务比例与每期偿债额，零分母不得填零倍。", ("finance.debt_ratio", "finance.debt_schedule"), ("financial.phase3e.dscr",)),
    "APP08.01": ("单因素和组合情景是否分别独立测算？", "分别列明各因素变化、其余条件及对应结果，再比较不同情景。", ("scenarios.options",), ()),
    "APP08.02": ("阈值与变化方向能否按同一口径核对？", "补充投资目标、重算结果，并核对投资和电量变化对收益的影响方向。", ("targets.project_irr", "targets.payback_years"), ("financial.phase3e.break-even-price",)),
    "APP09.01": ("政策原文、地区及生效日期能否定位？", "取得政策文号、原文条款与有效期，不推定现行适用。", ("policy.applicability",), ()),
    "APP09.02": ("政策适用或冲突是否经过逐条审查？", "按项目地区和类型记录有效、过期、待核和冲突依据。", ("policy.applicability",), ()),
    "APP10.01": ("阻断事项是否逐一具名并给出关闭证据？", "核对当前发现项、责任人及关闭材料，不将未核实项目视为关闭。", ("risk.items",), ()),
    "APP10.02": ("资料关闭后才允许进入哪些决策里程碑？", "核对权属、工程、并网及现金流门槛与重启条件。", ("schedule.tasks", "targets.risk_preference"), ()),
    "APP11.01": ("所引用公式能否对应注册定义和版本？", "从正式公式快照核验名称、输入、边界及验证记录，不在报告中补造公式。", (), ()),
    "APP11.02": ("出现的符号是否逐一有单位、定义和来源？", "对照公式工作表复核上下标、求和范围和每个输入来源。", (), ()),
    "APP12.01": ("正文术语是否有中文、英文全称与缩写对应？", "核对术语索引、首次定义与使用位置，不把缩写当定义。", (), ()),
    "APP12.02": ("功率、能量与辐照量单位是否在首次出现处区分？", "检查DC/AC、辐照度/辐照量和单位投资的口径。", (), ()),
    "APP13.01": ("配套文件是否与本次统一结果身份一致？", "比对模型、运行、输入、来源和结果哈希，不沿用历史附件。", (), ()),
    "APP13.02": ("质量与审阅状态是否与可用证据一致？", "区分合成资料、未验证来源、静态快照与页面审阅状态。", (), ()),
}

# Explicit object-level judgments. No title interpolation or chapter-level boilerplate:
# every clause states the mechanism and the precise epistemic boundary.
ITEM_JUDGMENTS = {
 'CH01': (
  '项目身份只界定合成测算对象，不能确认真实业主或获批方案。',
  '直交流容量刻画设备配置，预测电量不能当作现场保证电量。',
  '工程投资汇总与投资回报不是同一结论；现金事件不完整时不能由造价推出收益。',
  '发电、交付和结算跨越损失、计量及交易边界，模型收入不是实际回款。',
  '局部计算结果不足以解除权属、接网及完整现金流的独立决策门槛。'),
 'CH02': (
  '项目名称或开发主体输入不能证明建设需求和主体授权。',
  '年度项目评价使用预测的期末现金流，不要求逐笔银行流水；带日期指标和投资者出资分红另有事件边界。',
  '政策须按地区、生效期和条款核验；登记条目不是批准文件。',
  '资料登记只提供出处线索，不能证明原件、覆盖年份或授权已核实。',
  '合成参数是研究假设，不是现场或合同事实；变更应重算。'),
 'CH03': (
  '投资、建设和运营责任不能从模型字段推定为已授权法人安排。',
  '分类决定屋顶自用或地面集中送出的研究路径，坐标仍需测绘定位。',
  '可运营年限取决于使用权期限，投资模式不能补足权利文件。',
  '售电模式只是结算计算边界，不是已签署的购售电承诺。',
  '规模目标只描述拟议任务，不能单独证明真实需求和建设必要性。'),
 'CH04': (
  '项目名称及面积输入不能定位场址红线；坐标、坐标系和边界尚无可核验的测绘依据。',
  '可用面积仍需结合实测坡度或屋面障碍落位，不能据面积输入认定可建。',
  '土地或屋面权利期限须覆盖运营期；分类标识不证明合法使用。',
  '遮挡输入及设计荷载不能代替结构鉴定、遮挡实测和消防审查。',
  '运输、生态及灾害暴露未经调查时，施工可达性仍未确定。',
  '地勘及防洪尚无正式结论时，不应锁定基础和场址工程方案。'),
 'CH05': (
  '资源数据标识不等于获授权的长期气象记录，覆盖期和质量须核验。',
  '水平面与阵列面辐照不同；发电结果不能倒推缺失的辐照分量。',
  '气温和风速分别影响温度损失及抗风设计，月份序列不能证明极端工况。',
  '单一合成年或典型年设定不能证明多年资源代表性。',
  '倾角、方位角和转置方法影响阵列面资源，未经原始辐照核验不评资源等级。',
  '缺少独立交叉验证时，预测不确定性不能转化为保证发电区间。'),
 'CH06': (
  '建设任务须落在扣除退让区的有效面积内，容量目标不足以证明可建。',
  '组件数量和行距必须同时满足遮挡、检修及消防退让要求。',
  '容配比刻画设备配置，不等于变压器余量或电网接入许可。',
  '只有基准输入而无同边界备选方案，不构成技术经济比选。',
  '预算、接入容量和场址约束需并列比较；无备选结果不排序推荐。',
  '分类专项须取得屋面结构消防或地面用地地勘送出依据，不跨类型套用。'),
 'CH07': (
  '额定参数可构成初步容量组合，型号认证仍须设备数据表证明。',
  '倾角和行距受遮挡与支架受力双重约束，不能只按发电效率优化。',
  '串并联须按极端温度核查电压、电流和逆变器范围，名义容量不证明安全。',
  '遮挡、温度、线路及逆变损失须按物理顺序和已含边界去重。',
  '拓扑必须落实汇流、保护及计量交接点才能形成可审查接口。',
  '没有配置储能时不得计入充放电收益或声称储能消防合规。'),
 'CH08': (
  '阵列面资源、容量、损失和退化共同限定预测，单一资源值不能解释总电量。',
  '月度序列仅描述合成输入的季节分布，首年总量不是保证值。',
  '年度衰减与更换事件时点不同，电量曲线不证明更换计划已落实。',
  '性能比、等效小时和容量因数分母不同，不能互证现场效率。',
  '可利用量与交付量受不可用和限发约束，交付预测不是结算电量。',
  '长期电量可信度仍取决于资源代表性，不由首年结果外推保证。'),
 'CH09': (
  '接入点与电压输入仅供初设定位，不能代表电网批准。',
  '交流装机、变压器和可接入容量是不同约束，额定功率不证明送出裕度。',
  '保护及送出工程量依赖线路方案和整定审查，不能从设备清单推断。',
  '并网技术意见与交易准入须分别取得，模型状态不能替代具名外部意见。',
  '限发及送出上限影响可交付量，调度条件未经核实不能承诺消纳。'),
 'CH10': (
  '屋顶自用须将同边界负荷与发电逐时匹配，月账单不足以证明比例。',
  '交付预测包含自用和上网部分，不是全部上网或已结算售电量。',
  '节省电费须按生效分时合同和可避免费用核算，不能全额套用零售价。',
  '售电主体、价格和交易费须合同核验，模型收入不构成收款承诺。',
  '市场现货价及其他收益无有效时序和执行规则时不应补进基准。',
  '储能调度需独立SOC、效率及交易约束；未配置时收益不适用。'),
 'CH11': (
  '总平面须预留排除区、检修和消防空间，输入边界不能代替实测布置图。',
  '屋面锚固依赖结构鉴定，地面桩基依赖地勘；支架类型不定基础。',
  '荷载及通道需要具名专业复核，报告编号或预留宽度不是审查结论。',
  '物流吊装与排水限制施工窗口，现阶段不宜锁定施工组织。',
  '专项勘察及工程量缺口传导至造价和工期，费用汇总不能反证工程量。'),
 'CH12': (
  '减排量需同边界交付电量及适用排放因子，不能由发电量单独宣称。',
  '生态及水保义务取决于场址调查和审批，登记资料不是专题评估。',
  '消防通道、储能消防及施工风险各有责任边界，未经审查不能称合规。',
  '产权人和周边主体同意须有文件支持，项目身份不代表已获同意。',
  '政策及专项评价须逐条核验，风险清单不是行政合规结论。'),
 'CH13': (
  '开发投资运营分工须对应权属、接网及资金条件，主体名称不落实责任。',
  '采购施工调试日期须按审批与交付依赖排定，计划不是开工许可。',
  '关键路径取决于前置关系和审批时长，未核验时不能承诺并网日。',
  '施工通道、供货和电网窗口分别可能延误进度，缓释责任须落实。',
  '启动节点须由权属、专业审查及资金共同触发，不由评价日触发。'),
 'CH14': (
  '估算总额按本次费用分类汇集，合成价格不是可采购报价。',
  '设备费须按数量、单价、规格及税口径勾稽，总额不代替分项报价。',
  '屋面加固或地面基础道路送出须专项核量，否则造价边界可能遗漏。',
  '管理、前期及预备费用须核查类别及基数，避免总投资重复计列。',
  '建设期利息由提款日期、利率及进度决定，不按CAPEX比例猜测。',
  '单位投资分子须明确税及专项范围，分母须说明直流或交流装机。'),
 'CH15': (
  '现金运维费按项目汇集，保险及场地费仍需合同与期间依据。',
  '折旧和账面价值是会计分摊，不等于处置所得或终期现金。',
  '设备更换同时影响停机及现金支出，不能用单一退化率代替。',
  '现金税费须按税基和支付事件区分应计、应付及实付。',
  '现金运维、非现金折旧和更换支出分账后才能避免重复列费。'),
 'CH16': (
  '收入预测不是实际回款，账面残值不能自动计入终期现金。',
  '项目现金流须闭合投资、运营、税和终期实际收付，缺口阻断回报。',
  '融资后可供权益分配现金不等于投资者出资、实际分红或退出回款；借款提款不是股东收款。',
  '净现值按声明的年度期末现金流与折现率评价；逐笔日期NPV另需有日期事件，IRR需核根集。',
  '回收期依赖逐期现金结余，不能由单年收入推算年限。',
  '平准化度电成本须配对无杠杆成本与同边界全期交付电量。',
  '偿债倍数需合同债务服务及可供偿债现金，零债务不能记作零倍。',
  '盈亏平衡及目标差距需明确门槛和反向重算，不凭基准收入猜测。'),
 'CH17': (
  '基准结果没有单因素扰动运行，不能报告敏感性斜率。',
  '悲观乐观组合须各自定义参数并重算，单一基准不是三情景。',
  '稳健性门槛须现金流和扰动均闭合后检验，不推断耐受区间。',
  '权属、资源、工程和并网风险可分别阻断项目，风险登记不量化概率。',
  '变化方向须结合来源授权、计量边界和项目类型复核，单次结果不足以证明稳健性。'),
 'CH18': (
  '当前只能暂缓实质投资决定，先关闭独立否决条件。',
  '权利、结构或地勘及电网意见可各自否决推进，局部财务数值不能覆盖。',
  '进入下一阶段须先取得权属、工程及接入证据，再检验现金流门槛。',
  '待核事项须按场址、资源、售电及财务分别取证，版本更新不等于关闭。',
  '决策里程碑以具名审批和专业复核为前提，评价日期不是开工承诺。'),
}
APPENDIX_JUDGMENTS = {
 'APP01.01': '资料登记只提供出处线索，原件位置、授权和可读性仍须逐份核查。',
 'APP01.02': '字段实例同时指向来源及原始位置，输入血缘才足以复核。',
 'APP02.01': '月度气象须核单位、覆盖期及授权，不能由发电量倒推辐照。',
 'APP02.02': '月发电、消纳与交付须同月同时区对账，总发电不代替结算。',
 'APP03.01': '装机结果可追溯设备输入，型号认证仍须数据表核查。',
 'APP03.02': '损失顺序及退化时点决定是否重复扣减，年度曲线不证明审查。',
 'APP04.01': '总投资只在本次分类范围内成立，专项费用仍须逐项核量。',
 'APP04.02': '报价、应付和实付不同，账面总额不证明付款发生。',
 'APP05.01': '运维现金、折旧和更换须分列年度，折旧不是现金支出。',
 'APP05.02': '现金税金与条款仍需应计、应付及实付逐年对账。',
 'APP06.01': '项目全期现金流须覆盖建设至终期实际事件，收入不补缺口。',
 'APP06.02': '资本金现金流须独立记录出资和债务事件，不沿用项目现金流。',
 'APP07.01': '债务覆盖只在确有合同债务服务时计算，无债务不算偿债合格。',
 'APP07.02': '无债务不适用、零分母未定义，两者都不是零倍覆盖。',
 'APP08.01': '单因素及组合情景各需独立运行，基准结果不是情景底表。',
 'APP08.02': '保本界限须按同一目标口径重算，并核对变化方向；展示值不足以证明可承受波动。',
 'APP09.01': '政策须定位文号、地区及有效期，适用意向不是现行证明。',
 'APP09.02': '政策冲突须逐条审查，未核验文本不能形成合法性意见。',
 'APP10.01': '阻断事项须关联关闭材料和责任，发现项存在不等于解除。',
 'APP10.02': '推进门槛须映射权属、工程、接网及现金流证据，不由日期满足。',
 'APP11.01': '公式快照只是定义索引，适用边界仍须逐条核对。',
 'APP11.02': '符号须解释单位、下标及求和边界，编号不定义变量。',
 'APP12.01': '缩写须对应中英全称和首次出现位置，避免同名异义。',
 'APP12.02': '功率、能量及辐照单位不可互换，单位投资须说明装机分母。',
 'APP13.01': '配套文件须指向同次模型、运行、输入、来源及结果，不能拼接历史快照。',
 'APP13.02': '章节完整、测算充分、来源真实与页面可读须分别判断，不能相互替代。',
}

# Display only numerical input assumptions with unambiguous local meanings.
# Documentary identifiers remain provenance references, never approved facts.
INPUT_FACT_LABELS = {
    'site.total_area': '录入场址总面积', 'site.usable_area': '录入可利用面积',
    'site.exclusion_area': '录入排除区面积',
    'roof.allowable_additional_load': '允许附加荷载假设',
    'roof.design_added_load': '设计附加荷载假设',
    'roof.remaining_life': '屋面剩余年限假设',
    'layout.row_pitch': '阵列行距假设', 'layout.tilt': '阵列倾角假设',
    'layout.azimuth': '阵列方位角假设',
    'grid.transformer_capacity': '变压器容量输入',
    'grid.available_capacity': '可接入容量输入',
    'grid.export_power_limit': '送出功率限制输入',
    'system.module_count': '组件数量输入',
    'system.modules_per_string': '每串组件数输入',
    'system.parallel_strings': '并联组串数输入',
    'resource.uncertainty_fraction': '资源误差比例假设',
}


# Reader-facing names for the bounded per-section evidence cards. Unlisted
# documentary IDs are not printed as if they were verified engineering facts.
FIELD_LABELS = {
    'project.owner': '建设主体', 'project.developer': '开发主体',
    'project.name': '项目名称', 'project.pv_type': '项目类别',
    'project.investor': '投资主体', 'project.operator': '运营主体',
    'project.ownership_mode': '投资方式', 'project.sales_mode': '售电方式',
    'project.evaluation_years': '评价期', 'project.evaluation_date': '评价基准日',
    'project.price_basis': '价格口径', 'project.cashflow_tax_basis': '税口径',
    'site.address': '拟议场址', 'site.total_area': '场址总面积',
    'site.usable_area': '可用面积', 'site.exclusion_area': '排除区面积',
    'site.elevation': '场址高程', 'site.terrain_slope': '地形坡度',
    'site.shading_fraction': '遮挡比例', 'site.rights_status': '权属核验',
    'site.rights_expiry': '权利期限', 'site.transport_access': '运输条件',
    'system.mounting_type': '支架形式', 'system.topology': '电气拓扑',
    'resource.is_tmy': '典型气象年来源',
    'resource.period_start': '资源起始日期', 'resource.period_end': '资源截止日期',
    'targets.risk_preference': '风险偏好',
    'capex.includes_construction_interest': '资本支出是否包含建设期利息',
    'capex.estimate_basis': '估算依据',
    'grid.protection_plan': '保护方案', 'grid.upgrade_plan': '电网改造计划',
    'roof.waterproof_plan': '防水方案',
    'roof.allowable_additional_load': '屋面允许附加荷载',
    'roof.design_added_load': '设计附加荷载', 'roof.remaining_life': '屋面剩余年限',
    'layout.tilt': '阵列倾角', 'layout.azimuth': '阵列方位角',
    'layout.row_pitch': '阵列行距', 'layout.fire_setback': '消防退让',
    'layout.ground_coverage_ratio': '用地覆盖率',
    'system.dc_capacity': '直流装机', 'system.ac_capacity': '交流装机',
    'system.dc_ac_ratio': '容配比', 'system.module_count': '组件数量',
    'system.module_power': '单块组件功率', 'system.module_efficiency': '组件效率',
    'system.inverter_unit_ac': '单台逆变器额定功率',
    'system.modules_per_string': '每串组件数', 'system.parallel_strings': '并联组串数',
    'system.module_voc': '组件开路电压',
    'system.inverter_max_dc_voltage': '逆变器直流上限电压',
    'system.inverter_max_input_current': '逆变器最大输入电流',
    'system.first_year_degradation': '首年衰减',
    'system.annual_degradation': '后续年衰减',
    'system.unavailability': '不可用比例',
    'grid.connection_voltage': '接入电压', 'grid.transformer_capacity': '变压器视在容量',
    'grid.available_capacity': '申报可接入容量',
    'grid.export_power_limit': '申报送出有功上限',
    'grid.power_factor': '功率因数', 'grid.line_length': '线路长度',
    'grid.opinion_status': '正式接网意见',
    'finance.project_discount_rate': '项目折现率',
    'finance.equity_discount_rate': '股权折现率',
    'finance.working_capital': '营运资金投入', 'finance.debt_ratio': '债务比例',
    'capex.contingency_rate': '预备费率', 'tax.corporate_income_rate': '所得税率',
    'resource.uncertainty_fraction': '资源不确定性输入',
    'environment.grid_emission_factor': '减排因子假设',
    'schedule.construction_start': '计划开工',
    'schedule.commissioning_date': '计划投运',
}

ENUM_LABELS = {
    'pending': '待取得正式核验', 'owner_invested': '业主自投',
    'industrial_rooftop': '工商业屋面', 'utility_scale_ground': '集中式地面',
    'FIXED': '固定支架', 'FIXED_STRING_INVERTERS': '固定支架组串式逆变器',
    'self_use_surplus_export': '自发自用、余电上网',
    'full_export': '全额上网', 'nominal': '名义价格',
    'post_tax': '税后', 'PERIOD_END': '年度期末',
    'balanced': '均衡风险偏好', 'GRID_DELIVERABLE': '并网交付边界',
}

RATE_FIELDS = {'site.shading_fraction', 'layout.ground_coverage_ratio',
               'system.module_efficiency', 'system.first_year_degradation',
               'system.annual_degradation', 'system.unavailability',
               'finance.project_discount_rate', 'finance.equity_discount_rate',
               'finance.debt_ratio', 'capex.contingency_rate',
               'tax.corporate_income_rate', 'resource.uncertainty_fraction'}


REPEATED_FIELDS = ('resource.monthly', 'capex.items', 'opex.items',
                   'schedule.tasks', 'assets.replacements', 'assets.depreciation',
                   'system.losses', 'tariff.periods', 'risk.items',
                   'attachments.register', 'policy.applicability', 'scenarios.options',
                   'finance.debt_schedule', 'revenue.other_items')


def _parent_field(fid: str) -> str:
    return next((parent for parent in REPEATED_FIELDS if fid.startswith(parent + '.')), fid)


def _source_atom_value(atom: Any, known_sources: set[str]) -> Any:
    """Unwrap each sourced child, including atomic predecessor lists."""
    if isinstance(atom, list):
        return [_source_atom_value(child, known_sources) for child in atom]
    if isinstance(atom, dict) and 'value' in atom:
        if atom.get('source_id') not in known_sources or atom.get('status') in {'REJECTED', 'INVALID'}:
            return object()  # Never match an accepted normalized input.
        return _source_atom_value(atom['value'], known_sources)
    return atom


RESOURCE_MONTHLY_UNITS = {
    'resource.monthly.ghi': 'kWh/m2', 'resource.monthly.dni': 'kWh/m2',
    'resource.monthly.dhi': 'kWh/m2', 'resource.monthly.poa': 'kWh/m2',
    'resource.monthly.ambient_temperature': 'degC',
    'resource.monthly.wind_speed': 'm/s', 'resource.monthly.coverage': '1',
    'resource.monthly.days': 'day', 'resource.monthly.month': None,
    'resource.monthly.row_id': None,
}


def _sourced_rows(value: Any, records: tuple | list, group: str) -> list | None:
    """Bind each repeated child to its stable Phase 2 row and flat atom."""
    parents = [record for record in records if record.get('field_id') == group]
    if len(parents) != 1 or not isinstance(value, list) or not value:
        return None
    parent = parents[0]
    source_id, origin = parent.get('source_id'), parent.get('source_url_or_attachment')
    kind, status = parent.get('source_kind'), parent.get('status')
    if (parent.get('field_instance_id') != group
            or not isinstance(source_id, str) or not source_id
            or not isinstance(origin, str) or not origin
            or status not in {'ASSUMED', 'VERIFIED'}
            or parent.get('license_status') != 'AUTHORIZED'
            or not parent.get('source_section_or_cell')
            or (kind == 'ASSUMPTION') != (status == 'ASSUMED')
            or kind not in {'USER_PROVIDED', 'DOCUMENT_EXTRACTED',
                            'EXTERNAL_SOURCE', 'CALCULATED', 'ASSUMPTION'}):
        return None

    flat = {}
    for record in records:
        if record.get('field_instance_id'):
            flat.setdefault(record['field_instance_id'], []).append(record)
    nested_instances = set()

    def same_source(atom: Any, fid: str, instance: str) -> bool:
        return (isinstance(atom, dict) and atom.get('field_id') == fid
                and (group != 'resource.monthly'
                     or (fid in RESOURCE_MONTHLY_UNITS and atom.get('unit') == RESOURCE_MONTHLY_UNITS[fid]))
                and atom.get('field_instance_id') == instance
                and atom.get('source_id') == source_id
                and atom.get('source_url_or_attachment') == origin
                and atom.get('source_kind') == kind
                and atom.get('status') in {'ASSUMED', 'VERIFIED'}
                and atom.get('license_status') == 'AUTHORIZED'
                and atom.get('source_section_or_cell') == parent['source_section_or_cell']
                and (kind == 'ASSUMPTION') == (atom['status'] == 'ASSUMED'))

    def bound(atom: Any, fid: str, instance: str, expected: Any) -> bool:
        return (same_source(atom, fid, instance)
                and instance not in nested_instances
                and len(flat.get(instance, ())) == 1
                and flat[instance][0] == atom
                and type(atom.get('value')) is type(expected)
                and atom['value'] == expected)

    source_rows = parent.get('value')
    if not isinstance(source_rows, list) or len(source_rows) != len(value):
        return None
    by_id = {}
    for row in source_rows:
        if not isinstance(row, dict) or not isinstance(row.get('row_id'), str) or not row['row_id'] or row['row_id'] in by_id:
            return None
        by_id[row['row_id']] = row
    seen = set()
    for row in value:
        if not isinstance(row, dict) or not isinstance(row.get('row_id'), str) or not row['row_id'] or row['row_id'] in seen:
            return None
        row_id = row['row_id']
        seen.add(row_id)
        source = by_id.get(row_id)
        fields = row.get('fields')
        atoms = source.get('fields') if isinstance(source, dict) else None
        if not isinstance(fields, dict) or not isinstance(atoms, dict) or fields.keys() != atoms.keys():
            return None
        for fid, expected in fields.items():
            if not isinstance(fid, str) or not fid.startswith(group + '.'):
                return None
            instance = f'{group}:{row_id}:{fid.removeprefix(group + ".")}'
            atom = atoms[fid]
            if group == 'schedule.tasks' and fid == 'schedule.tasks.predecessor_ids' and isinstance(expected, list):
                if (not isinstance(atom, dict) or not isinstance(atom.get('value'), list)
                        or len(atom['value']) != len(expected)
                        or not same_source(atom, fid, instance)
                        or instance in nested_instances
                        or len(flat.get(instance, ())) != 1 or flat[instance][0] != atom):
                    return None
                nested_instances.add(instance)
                for index, (predecessor, task_id) in enumerate(zip(atom['value'], expected)):
                    if (not isinstance(task_id, str)
                            or not isinstance(predecessor, dict)
                            or predecessor.get('field_instance_id') not in {
                                f'{group}:{row_id}:predecessor:{task_id}',
                                f'{instance}:element:{index}'}
                            or not bound(predecessor, fid, predecessor['field_instance_id'], task_id)):
                        return None
                    nested_instances.add(predecessor['field_instance_id'])
            elif not bound(atom, fid, instance, expected):
                return None
            else:
                nested_instances.add(instance)
        if group + '.row_id' in fields and fields[group + '.row_id'] != row_id:
            return None
    return value

def _source_value(normalized: dict, records: tuple | list, fid: str) -> Any:
    """Return only matching Phase 2 atoms, including repeated parent children."""
    parent = _parent_field(fid)
    value = normalized.get(parent)
    if not _has_value(value):
        return None
    if parent in {'schedule.tasks', 'resource.monthly'}:
        rows = _sourced_rows(value, records, parent)
        if rows is None:
            return None
        if parent == 'resource.monthly':
            source = next(record for record in records if record.get('field_id') == parent)
            months = [row['fields'].get('resource.monthly.month') for row in rows]
            if (len(rows) != 12 or any(type(month) is not int for month in months)
                    or set(months) != set(range(1, 13))):
                return None
            metadata = {}
            for key in ('resource.period_start', 'resource.period_end', 'resource.dataset_id',
                        'resource.version', 'site.timezone'):
                matches = [record for record in records if record.get('field_id') == key]
                if (len(matches) != 1 or matches[0].get('field_instance_id') != key
                        or matches[0].get('value') != normalized.get(key)
                        or any(matches[0].get(identity) != source.get(identity) for identity in
                               ('source_id', 'source_url_or_attachment', 'source_kind', 'source_section_or_cell'))
                        or matches[0].get('unit') is not None
                        or matches[0].get('status') not in {'ASSUMED', 'VERIFIED'}
                        or matches[0].get('license_status') != 'AUTHORIZED'):
                    return None
                metadata[key] = matches[0]['value']
            try:
                start = date.fromisoformat(metadata['resource.period_start'])
                end = date.fromisoformat(metadata['resource.period_end'])
                ZoneInfo(metadata['site.timezone'])
            except (KeyError, TypeError, ValueError):
                return None
            if (start != date(start.year, 1, 1) or end != date(start.year, 12, 31)
                    or not metadata['resource.dataset_id'] or not metadata['resource.version']):
                return None
        if fid == parent:
            return rows
        children = [row['fields'][fid] for row in rows if fid in row['fields']]
        return children or None
    known_sources = {record['source_id'] for record in records
                     if record.get('source_id') and record.get('status') not in {'REJECTED', 'INVALID'}}
    for record in records:
        if (record.get('field_id') != parent or not record.get('source_id')
                or record.get('status') in {'REJECTED', 'INVALID'}):
            continue
        source = record.get('value')
        if isinstance(value, list) and isinstance(source, list):
            source = [{"row_id": row.get("row_id"), "fields": {
                key: _source_atom_value(atom, known_sources)
                for key, atom in row.get('fields', {}).items()}}
                      for row in source if isinstance(row, dict)]
        if source != value:
            continue
        if parent == fid:
            return value
        children = [row['fields'][fid] for row in value if isinstance(row, dict)
                    and fid in row.get('fields', {})]
        return children or None
    return None


def _text_value(fid: str, value: Any, fmt: Callable[[Any], str]) -> str | None:
    if isinstance(value, bool):
        return '是' if value else '否'
    if isinstance(value, (int, float, Decimal)):
        number = Decimal(str(value)) * (100 if fid in RATE_FIELDS else 1)
        unit = '%' if fid in RATE_FIELDS else _reader_unit(fid, {
            'site.total_area': 'm2', 'site.usable_area': 'm2', 'site.exclusion_area': 'm2',
            'layout.row_pitch': 'm', 'layout.fire_setback': 'm',
            'layout.azimuth': 'degree', 'layout.tilt': 'degree',
            'site.elevation': 'm', 'site.terrain_slope': 'degree',
            'roof.allowable_additional_load': 'kN/m2',
            'roof.design_added_load': 'kN/m2',
            'grid.connection_voltage': 'kV', 'grid.line_length': 'km',
            'system.inverter_max_input_current': 'A',
            'roof.remaining_life': 'year', 'project.evaluation_years': 'year',
            'grid.transformer_capacity': 'kVA', 'grid.available_capacity': 'kWac',
            'grid.export_power_limit': 'kW', 'system.dc_capacity': 'kWp',
            'system.ac_capacity': 'kWac', 'system.inverter_unit_ac': 'kWac',
            'system.module_power': 'Wp',
            'finance.working_capital': 'CNY', 'system.module_voc': 'V',
            'system.inverter_max_dc_voltage': 'V',
        }.get(fid))
        return fmt(number) + unit
    if isinstance(value, str):
        if fid == 'capex.estimate_basis' and value == 'SYNTHETIC item costs; no supplier quotations or approved budget':
            return '按合成分项成本编制；无供应商报价或批准预算'
        if fid == 'site.transport_access' and value == 'Concept only; road and lifting access not surveyed':
            return '仅为概念方案；道路及吊装条件未经勘察'
        if value in ENUM_LABELS:
            return ENUM_LABELS[value]
        if value.startswith(('SYNTHETIC-', 'SYNTHETIC_', 'FICTIONAL_NOT_', 'NO_')):
            return None
        if value == 'FICTIONAL: same model owner':
            return '同一合成演示主体'
        if fid == 'project.name' and value.startswith('FICTIONAL: '):
            if 'factory-roof calculation demo' in value:
                return '工商业屋面合成测算方案（无真实场址）'
            if 'ground PV calculation demo' in value:
                return '集中式地面合成测算方案（无真实场址）'
        if value.startswith('FICTIONAL'):
            return value.replace('FICTIONAL ENTITY: ', '合成演示主体：').replace('FICTIONAL: ', '合成演示主体：').replace('FICTIONAL ', '合成演示').replace(' (not registered)', '（未核实注册）')
        if value.startswith(('Synthetic ', 'No real ', 'Not quantified ', 'Authored offline')):
            return None
        if len(value) <= 80 and all(c not in value for c in '{}[]'):
            return value
    return None


def _has_value(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def _task_display_name(name: str) -> str:
    """Translate authored planning roles for readers without changing sources."""
    if not name.startswith('SYNTHETIC '):
        return name
    description = name.removeprefix('SYNTHETIC ')
    roles = (
        ('roof layout', '屋面排布与结构复核计划'),
        ('rights/fire/grid review gate', '权属、消防及接网待核节点计划'),
        ('site/drainage/connection', '场址、排水及接网概念方案计划'),
        ('title/geotechnical/grid review gate', '用地、地勘及接网待核节点计划'),
        ('rooftop installation', '屋面安装施工计划（须先取得真实许可）'),
        ('ground civil and array', '地面土建与阵列施工计划（须先取得真实许可）'),
        ('electrical testing and meter', '电气调试与计量核查计划（非投运批准）'),
        ('grid interface testing', '并网接口联调计划（非接网批准）'),
        ('commissioning milestone', '拟投运里程碑（非获准投运）'),
    )
    return next((label for phrase, label in roles if phrase in description.lower()), description)

def _reader_unit(field_id: str, unit: str | None) -> str:
    """Keep engineering units, not source-schema tokens, in consulting prose."""
    if field_id == "financial.unit_investment":
        return "元/kWp"
    if field_id == "system.module_count":
        return "块"
    if field_id == "system.modules_per_string":
        return "块/串"
    if field_id == "system.parallel_strings":
        return "串"
    return {"degree": "°", "m2": "㎡", "kN/m2": "kN/㎡", "CNY": "元", "year": "年", "piece": "件", "1": ""}.get(unit or "", unit or "")


@lru_cache(maxsize=4)
def _bound_upstream_datasets(directory: str, expected_hash: str, project_id: str,
                             pv_type: str, phase2_id: str) -> dict[str, Any]:
    """Read only the canonical-declared generation artifact, not an editorial file.

    Phase 3e currently preserves its generation hash in artifact_manifest but
    drops D3 dataset summaries from source_snapshot.datasets. Do not infer D3
    provenance from calculated energy alone or an unrelated local bundle.
    """
    try:
        path = Path(directory) / "result.json"
        if not path.is_file() or path.stat().st_size > 5_000_000:
            return {}
        upstream = json.loads(path.read_text(encoding="utf-8"))
        if (upstream.get("result_hash") != expected_hash
                or upstream.get("project_id") != project_id
                or upstream.get("pv_type") != pv_type
                or upstream.get("source_snapshot", {}).get("phase2", {}).get("source_snapshot_id") != phase2_id):
            return {}
        return upstream.get("source_snapshot", {}).get("datasets", {}).get("datasets", {})
    except (OSError, ValueError, TypeError, AttributeError):
        return {}


def _dataset_rows(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    snapshot = result.get("source_snapshot", {})
    container = snapshot.get("datasets", {})
    rows = container.get("datasets", {}) if isinstance(container, dict) else {}
    if not rows:
        for artifact in result.get("artifact_manifest", ()):
            if artifact.get("kind") == "UPSTREAM_PHASE3B_GENERATION" and artifact.get("result_hash") == result.get("inputs", {}).get("generation_result_hash"):
                rows = _bound_upstream_datasets(
                    artifact["directory"], artifact["result_hash"], result["project_id"],
                    result["pv_type"], snapshot.get("phase2", {}).get("source_snapshot_id", ""))
                break
    return {fid: row for fid, row in rows.items()
            if isinstance(row, dict) and row.get("header", {}).get("field_id") == fid
            and isinstance(row.get("row_count"), int) and row["row_count"] > 0}


def category_fields(item_id: str, fields: tuple[str, ...], pv_type: str,
                    has_storage: bool) -> tuple[str, ...]:
    """Preserve the outline while excluding other product types' evidence gates."""
    ground = pv_type == "utility_scale_ground"
    excluded = ("roof.", "public.", "residential.", "agri.", "fishery.") if ground else (
        "public.", "residential.", "agri.", "fishery.")
    selected = tuple(field for field in fields
                     if not field.startswith(excluded)
                     and (has_storage or not field.startswith("storage."))
                     and (not ground or field not in {"load.series", "load.monthly_bills"}))
    if ground and item_id in {"CH04.04", "CH11.03"}:
        selected += ("site.geotechnical_reference",)
    if item_id.startswith("CH05.") or item_id == "APP02.01":
        selected += ("resource.timeseries",)
    if item_id == "CH06.06":
        selected += (("site.geotechnical_reference", "grid.connection_point") if ground
                     else ("roof.structure_report_id", "roof.fire_access_reference"))
    return tuple(dict.fromkeys(selected))


def _project_irr_claim(model: Any) -> str:
    """Reader-facing project IRR root-set status; never select a favoured root."""
    metric = model.metric('financial.phase3e.project_irr')
    if not metric:
        return '项目IRR尚无可核验结果'
    details = metric.get('details') or {}
    roots, domain = details.get('roots'), details.get('domain')
    if (not isinstance(roots, list) or not isinstance(domain, dict)
            or details.get('unexhausted') is not False or type(details.get('root_count')) is not int
            or details['root_count'] != len(roots)
            or any(isinstance(domain.get(key), bool) or not isinstance(domain.get(key), (int, float, Decimal))
                   for key in ('minimum', 'maximum'))
            or any(isinstance(root, bool) or not isinstance(root, (int, float, Decimal)) for root in roots)):
        return '项目IRR根集尚未核验，不推断单一回报率'
    bounds = (f"声明搜索域{Decimal(str(domain['minimum'])) * 100}%至"
              f"{Decimal(str(domain['maximum'])) * 100}%内")
    if metric.get('status') == 'UNDEFINED' and metric.get('reason') == 'NO_ROOT' and not roots:
        return f'项目IRR在{bounds}无根，不等于IRR为0，也不代表整个实数域无根'
    if (metric.get('status') == 'UNDEFINED' and metric.get('reason') == 'MULTIPLE_ROOTS'
            and metric.get('value') is None and len(roots) > 1):
        values = [Decimal(str(root)) * 100 for root in roots]
        precision = next((digits for digits in range(2, 19)
                          if len({f'{value:.{digits}f}' for value in values}) == len(values)), None)
        labels = [f'根{index}≈{value:.{precision}f}%' if precision is not None else
                  f'根{index}≈{value}%' for index, value in enumerate(values, 1)]
        return (f'项目IRR在{bounds}有{len(roots)}个已认证根（' + '、'.join(labels) +
                '），非唯一IRR，不据此择优比较折现率')
    if (metric.get('status') == 'CALCULATED' and len(roots) == 1
            and metric.get('value') == roots[0]):
        return f'项目IRR在{bounds}唯一已认证根为{decision_percent(roots[0])}'
    return '项目IRR指标状态与根集不一致，不推断单一回报率'


def _specific_project_judgment(model: Any, item_id: str, format_value: Callable[[Any], str]) -> str:
    """Write six bounded conclusions from this run's Phase 2, ledger and metrics."""
    result = model.result
    n = result["inputs"].get("normalized", {})
    records = result.get("source_snapshot", {}).get("phase2", {}).get("records", ())
    ground = result.get("pv_type") == "utility_scale_ground"
    def inp(fid):
        # Do not turn a matching value from an unrelated source into a claim.
        return _source_value(n, records, fid)

    def metric(mid):
        row = model.metric(mid)
        return row.get("value") if row and row.get("status") == "CALCULATED" else None

    def money(number):
        return f"{decision_number(number, 'CNY')}元"

    def pct(number):
        return f"{format_value(Decimal(str(number)) * 100)}%"

    dc, ac, year1 = metric("dc_capacity"), metric("ac_capacity"), metric("energy.year.1")
    years = inp("project.evaluation_years")
    if item_id == "CH01.02":
        if dc is None or ac is None or years is None:
            return "本次容量与评价期尚不能在同一来源快照下核定，暂不推定项目建设规模。"
        location = ("厂房屋面剩余年限按" + format_value(inp("roof.remaining_life")) + "年假设，仍需权属、结构荷载、防水和消防通道复核"
                    if not ground and inp("roof.remaining_life") is not None else
                    "地面场址的土地权属、地勘与道路排水仍需逐项核验" if ground else
                    "屋面权属与结构条件尚需复核")
        energy = f"；首年合成资源下预测发电{decision_number(year1, 'kWh')}kWh" if year1 is not None else "；首年发电结果尚未形成"
        ratio = metric('dc_ac_ratio')
        mean = metric('energy.mean_annual')
        return (f"本项目拟采用{format_value(dc)}kWp直流（Direct Current，DC）光伏组件及"
                f"{format_value(ac)}kW交流（Alternating Current，AC）逆变器，"
                + (f"直交流容配比为{format_value(ratio)}，" if ratio is not None else '')
                + f"以{format_value(years)}年评价运行表现{energy}。"
                + (f"评价期年均预测发电{decision_number(mean, 'kWh')}kWh。" if mean is not None else '')
                + "组件侧额定容量与交流侧输出能力"
                "并不相同，后续发电及收益仍取决于资源、系统损失和接网条件。\n\n"
                f"目前的规模和电量是合成方案的预测，不是获批装机或保底上网电量；{location}。")
    if item_id == "CH08.02":
        months = metric("energy.monthly.year.1")
        if (not isinstance(months, list) or len(months) != 12 or year1 is None
                or any(isinstance(x, bool) or not isinstance(x, (int, float, Decimal)) for x in months)):
            return "首年月度与年度发电未同时形成可对账结果，暂不推断季节发电。"
        reconciled = abs(sum(Decimal(str(x)) for x in months) - Decimal(str(year1))) < Decimal("0.01")
        displayed_sum = sum(Decimal(format_value(x).replace(',', '')) for x in months)
        displayed_year = Decimal(decision_number(year1, 'kWh').replace(',', ''))
        if reconciled and displayed_sum != displayed_year:
            reconciliation = (f'12个月显示值汇总{format_value(displayed_sum)}kWh，'
                              f'年度决策显示为{decision_number(year1, "kWh")}kWh；'
                              '差异来自月度明细与年度决策显示精度不同，不把两者称作相等')
        elif reconciled:
            reconciliation = (f'12个月显示值汇总{format_value(displayed_sum)}kWh，'
                              f'与年度指标{decision_number(year1, "kWh")}kWh一致')
        else:
            reconciliation = '月度与年度原值未闭合，须先查清口径'
        peak = max(range(12), key=lambda i: months[i])
        low = min(range(12), key=lambda i: months[i])
        peak_label = '、'.join(str(i + 1) for i, x in enumerate(months)
                              if format_value(x) == format_value(months[peak]))
        resource_months = _source_value(n, records, 'resource.monthly')
        day_note = ''
        if isinstance(resource_months, list) and len(resource_months) == 12:
            by_month = {row['fields'].get('resource.monthly.month'): row['fields'].get('resource.monthly.days')
                        for row in resource_months}
            if (len(by_month) == 12 and all(type(by_month.get(i)) is int and by_month[i] > 0
                                             for i in range(1, 13))):
                daily = [Decimal(str(value)) / by_month[i] for i, value in enumerate(months, 1)]
                if max(daily) - min(daily) <= max(abs(max(daily)), Decimal(1)) * Decimal('1e-9'):
                    day_note = ('本合成曲线各月日均预测接近，月合计的差异主要随28/30/31天变化；'
                                '不将其描述成已证明的季节气象规律。')
        depreciation = _source_value(n, records, "system.annual_degradation")
        tail = (f"后续年份按{pct(depreciation)}年衰减假设另行重算" if depreciation is not None
                else "后续年份衰减假设尚需核对")
        boundary = "屋顶自用与余电上网" if not ground else "地面集中送出"
        return (f"首年12个月预测发电中，1月{format_value(months[0])}kWh、"
                f"12月{format_value(months[-1])}kWh；显示峰值在{peak_label}月"
                f"（{format_value(months[peak])}kWh），谷值在{low + 1}月"
                f"（{format_value(months[low])}kWh）。{reconciliation}。{day_note}"
                f"月发电不是辐照实测或{boundary}结算电量；{tail}。")
    if item_id == "CH09.02":
        transformer, available, export = (inp("grid.transformer_capacity"),
                                         inp("grid.available_capacity"), inp("grid.export_power_limit"))
        if ac is None or transformer is None or available is None:
            return "变压器、可用接入余量与交流铭牌尚未同时绑定，不能作出并网可行结论。"
        constraint = (f"可用接入余量低于{format_value(ac)}kWac交流铭牌，不能以变压器额定容量直接认定可全额送出"
                      if Decimal(str(available)) < Decimal(str(ac)) else
                      "可用接入余量不低于交流铭牌，但仍不等于核准可送出功率")
        export_text = f"；送出限值假设另为{format_value(export)}kW" if export is not None else ""
        point = "屋顶自用后的余电" if not ground else "地面电站集中上网的全部电量"
        opinion = inp("grid.opinion_status")
        opinion_text = "待取得" if opinion == "pending" else (str(opinion) if opinion else "待核")
        factor = inp("grid.power_factor")
        factor_text = (f"本次功率因数{format_value(factor)}仍是合成假设" if factor is not None
                       else "功率因数未提供，不将kVA强行折算为可接入kW")
        return (f"{format_value(transformer)}kVA变压器是设备视在容量，不能直接与kWac有功容量比较；"
                f"{factor_text}。本次填报可用接入余量{format_value(available)}kWac，{constraint}{export_text}。"
                f"{point}还受保护、线路与计量边界约束；正式接网意见{opinion_text}，"
                "仅属合成条件，正式电网接入与送出限值待批复，不视为已获接入许可。")
    if item_id == "CH14.02":
        def precise_money(number):
            text = format(Decimal(str(number)), ",f")
            return (text.rstrip("0").rstrip(".") if "." in text else text) + "元"

        def item_amount(number):
            exact, rounded = precise_money(number), money(number)
            return rounded if exact == rounded else f"{rounded}（原始分项{exact}）"

        def equipment_description(row):
            category = row["capex.items.category"]
            name = equipment[category]
            source_unit = row.get("capex.items.quantity_unit")
            unit = "件" if source_unit == "unit" else source_unit
            unit = unit if isinstance(unit, str) and unit.strip() else None
            count = f"{format_value(row['capex.items.quantity'])}{unit}" if unit else (
                f"{format_value(row['capex.items.quantity'])}（数量单位待核）")
            price = f"{precise_money(row['capex.items.unit_price'])}/{unit}" if unit else (
                f"{precise_money(row['capex.items.unit_price'])}（计价单位待核）")
            return f"{name}{count}、单价{price}，分项金额{item_amount(row['capex.items.amount'])}"

        items = inp("capex.items")
        rows = [r.get("fields", {}) for r in items if isinstance(r, dict)] if isinstance(items, list) else []
        initial = [r for r in rows if str(r.get("capex.items.payment_date", ""))[:4] <= str(result.get("evaluation_date", ""))[:4]]
        later = [r for r in rows if r not in initial]
        equipment = {"modules": "组件", "inverters": "逆变器", "mounting": "支架",
                     "cables": "电缆", "transformer_switchgear": "变压器及开关设备",
                     "grid_export": "并网送出设备", "storage": "储能设备"}
        listed = [r for r in initial if r.get("capex.items.category") in equipment]
        if not listed:
            return "本次未取得可绑定的设备分项数量、单价和税口径，设备费用不能由总额倒推。"
        largest = max(listed, key=lambda r: Decimal(str(r.get("capex.items.amount", 0))))
        descriptions = [equipment_description(r)
                        for r in listed if all(r.get('capex.items.' + key) is not None for key in ('quantity', 'unit_price', 'amount'))]
        if not descriptions:
            return "设备分项的数量或单价不完整，暂不能形成逐项费用判断。"
        tax = {r.get("capex.items.vat_rate") for r in listed}
        tax_note = (f"均按含税价、增值税率{pct(next(iter(tax)))}输入"
                    if len(tax) == 1 and None not in tax and all(r.get("capex.items.tax_included") is True for r in listed)
                    else "税价口径需按各分项来源分别核对")
        ledger = result.get("evidence", {}).get("financial-ledger", {}).get("annual", ())
        construction = ledger[0] if ledger and ledger[0].get("period") == "CONSTRUCTION" else {}
        initial_cost = construction.get("capex_cash_paid")
        lifecycle = metric("financial.capex.total")
        replacement = [r for r in later if r.get("capex.items.category") == "inverters"]
        future = ("；计划在" + "、".join(
            f"第{int(r['capex.items.payment_date'][:4]) - int(result['evaluation_date'][:4])}年逆变器更换"
            f"{money(r['capex.items.amount'])}" for r in replacement
            if str(r.get("capex.items.payment_date", ""))[:4].isdigit())
            + "，属于后期支出，不是初始设备采购" if replacement else "")
        initial_text = (f"建设期计划支付资本支出{money(initial_cost)}" if initial_cost is not None
                        else "建设期支付资本支出尚待核对")
        lifecycle_text = (f"，25年CAPEX合计{money(lifecycle)}" if lifecycle is not None and years == 25
                          else f"，评价期CAPEX合计{money(lifecycle)}" if lifecycle is not None else "")
        civil = [r for r in initial if r.get("capex.items.category") == "construction"]
        civil_text = (f"，其中工程建设分项{money(civil[0]['capex.items.amount'])}另列，不能充作设备费"
                      if civil and civil[0].get("capex.items.amount") is not None else "")
        return (f"本次设备清单以{equipment[largest['capex.items.category']]}"
                f"{money(largest['capex.items.amount'])}占已列初始设备分项最大份额："
                f"{'、'.join(descriptions)}；上述{tax_note}。{initial_text}{lifecycle_text}{civil_text}{future}。"
                "这些是合成数量与价格而非供应商签署报价，实际工程量、税额抵扣及采购付款仍须核验。")
    if item_id == "CH16.02":
        flow = metric("financial.phase3e.project_cash_flow")
        ledger = result.get("evidence", {}).get("financial-ledger", {}).get("annual", ())
        if not isinstance(flow, list) or len(flow) < 2 or len(ledger) < 2:
            return "项目现金流未与建设期及运营年账簿同时闭合，不能将收入预测写成实际收款。"
        build, first = ledger[:2]
        start, wc = build.get("capex_cash_paid"), build.get("working_capital_increase")
        receipts, savings = first.get("revenue_cash_receipts"), first.get("self_use_avoided_expenditure")
        transaction = first.get("transaction_cost_cash_paid")
        opex, tax = first.get("opex_cash_paid"), first.get("cash_tax_total_project")
        if any(v is None for v in (start, wc, receipts, opex, tax)):
            return "项目现金流虽有结果，但缺少与之配套的投资、营运资金或首年收支账簿，不能作分项解释。"
        benefit = (f"合成的余电预计回款{money(receipts)}与自用节费{money(savings)}"
                   if not ground and savings is not None else f"预计上网回款{money(receipts)}")
        fee_basis = result.get("boundaries", {}).get("SETTLEMENT", {}).get("fee_treatment")
        fee_note = ("历史封存账簿未单列交易费预计支付，当前财务结论须以新版来源闭合结果为准，"
                    if transaction is None else
                    f"预计另行支付交易费用{money(transaction)}，其所得税影响已在项目现金税费中反映，"
                    if fee_basis == "SEPARATE_LEDGER" else
                    "售电价格已含交易费用，不另行重复扣减，" if fee_basis == "ALREADY_IN_PRICE" and not transaction else
                    "交易费用结算口径尚未闭合，")
        replacements = [r for r in ledger[1:] if r.get("replacement_cash_paid")]
        renewal = ""
        if replacements and str(replacements[0].get("period", "")).startswith("OPERATING_YEAR_"):
            replacement = replacements[0]
            year = int(replacement["period"].removeprefix("OPERATING_YEAR_"))
            renewal = f"；第{year}年计划更换支出{money(replacement['replacement_cash_paid'])}，已在当年现金流扣除"
            if year < len(flow) and flow[year] < 0:
                renewal += (f"；该年项目年度净现金流{money(flow[year])}，应就更换年度单独安排资金计划"
                            "，年度净流出不能推断具体付款瞬间的资金缺口")
        display_residual = ""
        # Only compare separately rounded reader numbers when the first year
        # has no other capital or working-capital cash event to explain the
        # difference. The canonical ledger and cash flow remain untouched.
        other_events = ("capex_cash_paid", "replacement_cash_paid", "working_capital_increase",
                        "working_capital_release", "terminal_asset_cash")
        if (transaction is not None and (ground or savings is not None)
                and not any(first.get(key) for key in other_events)):
            def rounded_yuan(value):
                return Decimal(decision_number(value, "CNY").replace(",", ""))
            shown_sum = (rounded_yuan(receipts) + rounded_yuan(savings or 0)
                         - rounded_yuan(transaction) - rounded_yuan(opex) - rounded_yuan(tax))
            difference = shown_sum - rounded_yuan(flow[1])
            if difference:
                direction = "多" if difference > 0 else "少"
                display_residual = f"；分项整数相减比未取整账簿净额{direction}{money(abs(difference))}，仅为列示尾差"
        return (f"项目税后年度现金流建设期为{money(flow[0])}，由建设期计划资本支出{money(start)}"
                f"和营运资金投入{money(wc)}构成；运营首年{benefit}，"
                f"{fee_note}再扣运维现金{money(opex)}与项目现金税费{money(tax)}后，"
                f"对应首年净流入{money(flow[1])}{display_residual}{renewal}。"
                "本项是合成年度项目收支预测，不是实际银行流水、已收回款或投资者分红；"
                "股东出资及分配事件未闭合，不能由项目净流量替代。")
    if item_id == "CH16.04":
        npv = metric("financial.phase3e.project_npv")
        static, dynamic = metric("financial.phase3e.static_payback"), metric("financial.phase3e.dynamic_payback")
        discount = inp("finance.project_discount_rate")
        flow = metric("financial.phase3e.project_cash_flow")
        if (any(x is None for x in (npv, discount, years))
                or not isinstance(flow, list)
                or inp("project.price_basis") != "nominal"
                or inp("project.cashflow_tax_basis") != "post_tax"
                or inp("finance.cashflow_timing") != "PERIOD_END"):
            return "项目税后NPV与折现率尚未在同一计算边界闭合，不可替代为投资者收益。"
        irr_metric = model.metric('financial.phase3e.project_irr') or {}
        single = (irr_metric.get('status') == 'CALCULATED'
                  and '唯一已认证根' in _project_irr_claim(model))
        outcome = ("在本次假设下NPV为正且唯一IRR高于同口径折现率，模型项目回报超过折现假设"
                   if single and npv > 0 and Decimal(str(irr_metric['value'])) > Decimal(str(discount)) else
                   "NPV为正，但IRR非唯一或未高于同口径折现率，不据此下单根回报结论"
                   if npv > 0 else "本次NPV未为正，不据此下正收益结论")
        payback = (f"静态回收期{decision_number(static, 'year')}年、动态回收期{decision_number(dynamic, 'year')}年，"
                   if static is not None and dynamic is not None else "回收期按其独立指标状态核查，")
        irr_text = (f"项目IRR（内部收益率）为{decision_percent(irr_metric['value'])}"
                    if single else _project_irr_claim(model))
        return (f"以{format_value(years)}年名义价格、税后项目年度现金流为基础，按"
                f"{pct(discount)}折现率计算的项目净现值（NPV）为{money(npv)}。净现值衡量"
                "预测现金流折现后相对于投资的余额；"
                f"{irr_text}。内部收益率反映使项目净现值为零的折现率，"
                f"{payback}{outcome}。\n\n"
                "这些指标使用年度期末而非逐笔日期现金事件；项目回报不能替代投资者实际出资和分配回报。"
                "股东现金事件、签署交易条件与现场审批尚未闭合，不能仅凭正的预测净现值批准投资。")
    return ""


def _settlement_narrative(model: Any, item_id: str, fmt: Callable[[Any], str]) -> str | None:
    """Explain the *calculated* settlement ledger without inventing a tariff or payment."""
    result = model.result
    n = result['inputs'].get('normalized', {})
    records = result.get('source_snapshot', {}).get('phase2', {}).get('records', ())
    revenue = model.metric('revenue.year.1')
    consumption = model.metric('consumption.year.1')
    if (not revenue or revenue.get('status') != 'CALCULATED'
            or not consumption or consumption.get('status') != 'CALCULATED'):
        return None
    ledger = revenue.get('details', {}).get('ledger', {})
    if not isinstance(ledger, dict):
        return None
    required = ('export_kwh', 'export_sales_revenue', 'delivered_kwh', 'curtailed_kwh',
                'self_kwh', 'self_value', 'transaction_cost')
    if any(isinstance(ledger.get(key), bool) or not isinstance(ledger.get(key), (int, float, Decimal))
           for key in required):
        return None
    money = lambda key: f'{fmt(ledger[key])}元'
    energy = lambda key: f'{fmt(ledger[key])}kWh'
    ground = result.get('pv_type') == 'utility_scale_ground'
    datasets = _dataset_rows(result)
    if ground:
        price = datasets.get('tariff.market_series')
        lineage = result.get('evidence', {}).get('settlement-input-lineage', {}).get('tariff.market_series', {})
        price_bound = (price and price['header'].get('source_id') == lineage.get('source_id')
                       and lineage.get('status') in {'ASSUMED', 'VERIFIED'})
        path = (f"结算采用已登记的{price['row_count']}条市场价格时序，"
                "不是分时表中的单一售电价" if price_bound else
                "市场价格时序未能与结算血缘对应，不推断实际采用的价格路径")
        if item_id == 'CH10.02':
            assumption = _source_value(n, records, 'grid.curtailment_assumption')
            limit = (f"申报限发比例{(Decimal(str(assumption)) * 100).normalize():g}%" if isinstance(assumption, (int, float, Decimal))
                     and not isinstance(assumption, bool) else "限发参数尚未绑定")
            generation = model.metric('energy.year.1')
            losses = generation.get('details', {}).get('losses_kwh', {}) if generation and generation.get('status') == 'CALCULATED' else {}
            curtailment = losses.get('curtailment')
            physical = (f"发电计算中的限发损失为{fmt(curtailment)}kWh" if isinstance(curtailment, (int, float, Decimal))
                        else "发电链的限发损失尚未核对")
            return (f"集中式项目{limit}，{physical}；结算账簿另列首年截弃{energy('curtailed_kwh')}、"
                    f"交付{energy('delivered_kwh')}、上网{energy('export_kwh')}。"
                    "发电链损失与结算账簿截弃口径不同，不可相加或称实际上网；" + path + '。')
        if item_id in {'CH10.04', 'CH10.05'}:
            if not price_bound:
                return "市场价格时序未能绑定结算血缘；虽有收入指标，不能解释采用的售电价路径或代写结算金额。"
            if item_id == 'CH10.04':
                return (f"地面方案预计将{energy('export_kwh')}送入集中交易，按本次已绑定的"
                        f"逐时市场价格路径形成首年预测售电收入{money('export_sales_revenue')}。"
                        f"交易费用{money('transaction_cost')}单独列支，不从销售额中隐藏抵扣。\n\n"
                        "逐时交易价格变化会改变销售收入，但本次没有独立扰动测算，不能据此量化跌价风险。"
                        "交易主体、结算周期、计量节点与真实回款仍以有效合同和记录为准。")
            return (f"{path}；该时序参与首年预测上网销售收入"
                    f"{money('export_sales_revenue')}的结算。固定分时表情景价不能冒充实际采用的逐时市场价格，"
                    "其他收益未得到独立执行依据时不追加。")
        return None
    load = datasets.get('load.series')
    load_lineage = result.get('evidence', {}).get('settlement-input-lineage', {}).get('load.series', {})
    load_bound = (load and load['header'].get('source_id') == load_lineage.get('source_id')
                  and load_lineage.get('status') in {'ASSUMED', 'VERIFIED'})
    if item_id in {'CH10.01', 'CH10.02', 'CH10.03', 'CH10.04'} and not load_bound:
        return "负荷时序未能与结算血缘对应，不能核实逐时自用比例或自用—余电结算边界。"
    if item_id == 'CH10.01':
        return (f"首年负荷与发电按同一时区的{load['row_count']}条负荷时序配对，"
                f"模型自用{energy('self_kwh')}、余电上网{energy('export_kwh')}。"
                "月账单不替代逐时匹配，亦非实际计量结算。")
    if item_id == 'CH10.02':
        if not load_bound:
            return "负荷时序未能与结算血缘对应，不能核实自用与上网分界。"
        self_ratio = model.metric('consumption.self_ratio.year.1')
        load_coverage = model.metric('consumption.load_coverage.year.1')
        ratios = ((self_ratio, '逐时配对形成的自用比例'), (load_coverage, '同口径负荷覆盖率'))
        ratio_note = '；'.join(
            f'{label}{fmt(Decimal(str(item["value"])) * 100)}%'
            for item, label in ratios if item and item.get('status') == 'CALCULATED'
            and isinstance(item.get('value'), (int, float, Decimal)) and not isinstance(item['value'], bool))
        driver = ('当前价值主要来自自用节费' if ledger['self_value'] > ledger['export_sales_revenue'] else
                  '当前价值主要来自余电销售' if ledger['self_value'] < ledger['export_sales_revenue'] else
                  '两类价值在当前假设下相当')
        return (f"同边界负荷配对后，首年自用{energy('self_kwh')}形成节费"
                f"{money('self_value')}；余电上网{energy('export_kwh')}形成售电收入"
                f"{money('export_sales_revenue')}；交付总量{energy('delivered_kwh')}，"
                f"另有截弃{energy('curtailed_kwh')}。{ratio_note + '；' if ratio_note else ''}{driver}，节费不是电网回款；"
                "生产班次及分时负荷的真实匹配需在同一时区和计量边界下复核，"
                "上网销售收入也不是全部发电量的零售价格。")
    if item_id == 'CH10.03':
        return (f"自用对应的可避免费用预测为{money('self_value')}，"
                "只按适用分时可避免费用计，不把固定或需量等不可避免费用一并抵扣；"
                "仍须核对生效合同和计量时段。")
    if item_id == 'CH10.04':
        return (f"预测余电上网销售收入{money('export_sales_revenue')}，交易费用"
                f"{money('transaction_cost')}；自用节费{money('self_value')}另列，"
                "合同价及收款主体尚不能由计划价格推定为已签约。")
    return None


def _research_finding(model: Any, item_id: str, fmt: Callable[[Any], str],
                      *, reader_preview: bool = False) -> str | None:
    """Project-bound comparisons; no conclusion from an unbound input or blocked metric."""
    result = model.result
    normalized = result['inputs'].get('normalized', {})
    records = result.get('source_snapshot', {}).get('phase2', {}).get('records', ())
    get = lambda fid: _source_value(normalized, records, fid)
    def metric(mid: str) -> Any:
        row = model.metric(mid)
        return row.get('value') if row and row.get('status') == 'CALCULATED' else None
    def number(x: Any) -> bool:
        return isinstance(x, (int, float, Decimal)) and not isinstance(x, bool)
    ground = result.get('pv_type') == 'utility_scale_ground'
    ledger = result.get('evidence', {}).get('financial-ledger', {}).get('annual', ())
    build = ledger[0] if (ledger and ledger[0].get('period') == 'CONSTRUCTION'
                          and metric('financial.phase3e.project_cash_flow') is not None) else {}
    if item_id == 'CH01.04':
        dataset = 'tariff.market_series' if ground else 'load.series'
        observed = _dataset_rows(result).get(dataset)
        lineage = result.get('evidence', {}).get('settlement-input-lineage', {}).get(dataset, {})
        if (not observed or observed['header'].get('source_id') != lineage.get('source_id')
                or lineage.get('status') not in {'ASSUMED', 'VERIFIED'}):
            return ('市场价格时序尚未与集中结算血缘对应，不能解释全额上网收入。' if ground else
                    '厂区负荷时序尚未与逐时结算血缘对应，不能解释自用比例或节费。')
        revenue = model.metric('revenue.year.1') or {}
        details = revenue.get('details', {}).get('ledger', {}) if revenue.get('status') == 'CALCULATED' else {}
        delivered = metric('energy.delivered.year.1')
        if number(delivered) and all(number(details.get(k)) for k in ('self_kwh', 'self_value', 'export_kwh', 'export_sales_revenue')):
            if ground:
                return (f'本地面方案以集中送出和市场交易为收益路径，首年预测交付{fmt(delivered)}kWh。'
                        f'按已绑定的市场价格时序，预计上网销售收入{fmt(details["export_sales_revenue"])}元。'
                        '厂区负荷匹配不适用于这一方案；实际销售还取决于接网计量、交易准入及结算合同。')
            return (f'屋面方案拟优先以光伏电量满足厂区日间用电，首年预计交付{fmt(delivered)}kWh。'
                    f'逐时匹配的自用电量{fmt(details["self_kwh"])}kWh可实现购电节费'
                    f'{fmt(details["self_value"])}元；其余{fmt(details["export_kwh"])}kWh预测上网，'
                    f'形成售电收入{fmt(details["export_sales_revenue"])}元。\n\n'
                    '节省购电费不是电网支付的销售回款。厂区实际日间负荷与余电计量结算条件'
                    '会改变两类收益的比例，正式投资前须以真实负荷和有效合同复核。')
    if item_id == 'CH03.03':
        expiry, baseline, years = get('site.rights_expiry'), get('project.evaluation_date'), get('project.evaluation_years')
        if isinstance(expiry, str) and isinstance(baseline, str) and type(years) is int:
            try:
                end = date.fromisoformat(baseline).replace(year=date.fromisoformat(baseline).year + years)
                rights = date.fromisoformat(expiry)
            except ValueError:
                pass
            else:
                condition = ('晚于' if rights >= end else '早于')
                return (f'模型评价期自{baseline}延至{end.isoformat()}，录入的'
                        + ('屋面使用权' if not ground else '地面土地使用权')
                        + f'期限为{expiry}，{condition}模型终点；这只核对日期假设，不证明权属有效。'
                          '须查验权利人、证载用途及可转让或续期条件。')
    if item_id == 'CH06.02':
        count, pitch, setback = (get(fid) for fid in ('system.module_count', 'layout.row_pitch', 'layout.fire_setback'))
        if all(number(x) for x in (count, pitch, setback)):
            return (f'拟布置{fmt(count)}块组件，行距输入{fmt(pitch)}m、消防退让{fmt(setback)}m；'
                    + ('地面道路和排水占地须从实际地块扣除，' if ground else '屋面天窗、检修和消防通道须从可用面扣除，')
                    + '仅凭组件数及间距不能证明现场排布，须提交实测总平面与遮挡复核。')
    if item_id == 'CH12.01':
        factor, energy = get('environment.grid_emission_factor'), metric('energy.delivered.year.1')
        unit = next((row.get('unit') for row in records if row.get('field_id') == 'environment.grid_emission_factor'
                     and row.get('value') == factor), None)
        if number(factor) and number(energy) and unit == 'kgCO2e/kWh':
            return (f'首年交付电量为合成预测{fmt(energy)}kWh，录入减排因子'
                    f'{fmt(factor)}kgCO2e/kWh；两者尚未形成可引用减排量，'
                    '因子地区、适用期间、替代电源及核算边界未得到外部核验，不宣称实际减排。')
    if item_id == 'CH14.03':
        return ('地面项目的土建投资除设备支架外还可能涉及桩基、道路排水及集中送出。'
                '当前设备清单不能证明这些专项工程量已纳入报价；地勘与接入方案将直接影响总投资。'
                if ground else '屋顶项目的土建与安装费用还受锚固、防水、消防通道及可能的结构加固影响。'
                '当前组件清单不能覆盖这些专项工程量；结构复核后须核量询价，才能确定投资估算的完整性。')
    if item_id in {'CH04.02', 'CH06.01'}:
        total, usable, excluded = (get('site.' + suffix) for suffix in ('total_area', 'usable_area', 'exclusion_area'))
        if all(number(v) for v in (total, usable, excluded)):
            if Decimal(str(total)) - Decimal(str(excluded)) != Decimal(str(usable)):
                return (f'录入的总面积{fmt(total)}㎡扣除排除区{fmt(excluded)}㎡后，'
                        f'与申报可用面积{fmt(usable)}㎡不符；在核对测绘面积和排除区之前，'
                        '不能据此判断阵列排布和装机规模。')
            if item_id == 'CH04.02':
                return (f'方案记录的总面积为{fmt(total)}㎡，扣除排除区{fmt(excluded)}㎡后，'
                        f'拟用于布置的面积为{fmt(usable)}㎡。'
                        + ('地面阵列还需在同一地块内安排基础、施工及检修道路和排水设施；'
                           '这些工程会改变阵列行列与可建设范围。' if ground else
                           '厂房屋面还要为女儿墙、天窗、设备基础、消防及检修通道留出位置；'
                           '面积输入并没有替代逐栋屋面测绘和遮挡调查。')
                        + '取得现场测绘边界和布置图后才能确认这片面积是否适合当前装机。')
            dc = metric('dc_capacity')
            capacity = f'拟议直流规模{fmt(dc)}kWp' if dc is not None else '拟议规模'
            return (f'{capacity}暂以{fmt(usable)}㎡可用面积为排布条件。'
                    + ('阵列行距、地形坡度及道路排水需要在总平面上同时落位，桩基条件也会改变排布。'
                       if ground else '组件间距、天窗位置及消防通道必须在逐栋屋面图上落实，不能占用维护空间。')
                    + '目前没有经过现场校核的排布图，不能仅凭面积输入确认该规模可建。')
    if item_id == 'CH04.04':
        if ground:
            shading = get('site.shading_fraction')
            return ((f'阵列遮挡比例按合成输入{fmt(Decimal(str(shading))*100)}%设定；' if number(shading) else '')
                    + '地面阵列桩基承载及排布须取得地勘和测绘，不适用屋面荷载验算。')
        allowable, added = get('roof.allowable_additional_load'), get('roof.design_added_load')
        if number(allowable) and number(added):
            comparison = ('高于' if added > allowable else '未高于')
            return (f'屋面设计附加荷载输入{fmt(added)}kN/㎡，{comparison}允许附加荷载假设'
                    f'{fmt(allowable)}kN/㎡；该比较只校核录入假设，不能证明原结构安全。'
                    '须连同结构鉴定、锚固、防水和消防通道取得具名复核。')
        return '屋面荷载假设未在同一来源下绑定，不能比较承载余量；结构鉴定与消防通道仍需核查。'
    if item_id == 'CH07.03':
        count, voc, limit = (get(x) for x in ('system.modules_per_string', 'system.module_voc', 'system.inverter_max_dc_voltage'))
        if all(number(v) for v in (count, voc, limit)):
            nominal = Decimal(str(count)) * Decimal(str(voc))
            unit_gap = ' ' if reader_preview else ''
            return (f'每串{fmt(count)}块、组件标称开路电压{fmt(voc)}{unit_gap}V形成标称串电压'
                    f'{fmt(nominal)}{unit_gap}V，对照逆变器直流上限{fmt(limit)}{unit_gap}V；'
                    '低温Voc上浮、MPPT工作电压和各路输入电流仍须依据实际设备数据表与场址极值逐项验算，'
                    '本次标称对照不证明电气安全。')
    if item_id == 'CH09.03':
        upgrade, protection = get('grid.upgrade_plan'), get('grid.protection_plan')
        if upgrade and protection:
            return ('合成输入仅声明电网改造费用敞口尚未核量、保护方案停留在概念阶段；'
                    + ('屋面余电送出接入' if not ground else '地面集中送出')
                    + '须根据接入点、线路与整定审查确定工程量，并反馈至专项造价。')
    if item_id == 'CH09.05':
        limit = get('grid.export_power_limit')
        opinion = get('grid.opinion_status')
        if number(limit):
            return (f'本次送出有功上限输入{fmt(limit)}kW，只是模型约束；'
                    + ('厂内自用后的余电仍需在交接计量点核对，' if not ground else
                       '集中上网还须核查线路、保护与交易接口，')
                    + ('正式电网意见仍待取得，不能将计划限值写成批准容量。' if opinion == 'pending' else
                       '必须查验正式电网批复与有效期后才能引用批准容量。'))
    if item_id in {'CH14.01', 'CH14.06'}:
        total, initial, unit = metric('financial.capex.total'), build.get('capex_cash_paid'), metric('financial.unit_investment')
        if number(total) and number(initial):
            difference = Decimal(str(total)) - Decimal(str(initial))
            if item_id == 'CH14.01':
                return (f'本次评价期CAPEX合计{fmt(total)}元，建设期账簿计划支付{fmt(initial)}元，'
                        f'差额{fmt(difference)}元需按后续更换及支付期间核对，不能并入首期采购。'
                        '合成分项单价未取得供应商报价，' +
                        ('屋面加固和防水工程量须另行核定。' if not ground else '地面道路排水、基础与送出工程量须另行核定。'))
            if number(unit) and number(metric('dc_capacity')):
                return (f'全期含更换的CAPEX合计{fmt(total)}元，按直流装机{fmt(metric("dc_capacity"))}kWp'
                        f'列示的全期单位投资为{fmt(unit)}元/kWp；首建计划支出另为{fmt(initial)}元，'
                        '不是同一单位造价口径。含税及专项工程范围仍须核对。')
    if item_id == 'CH16.03':
        row = model.metric('financial.phase3e.equity-investor-cash-flow') or {}
        debt = get('finance.debt_ratio')
        if row.get('status') != 'CALCULATED':
            return (f'债务比例按{fmt(Decimal(str(debt))*100)}%输入；' if number(debt) else '') + (
                '股东出资、实际分配及退出收款事件未形成独立投资者现金流；项目NPV和融资后权益可用现金'
                '都不能替代股东IRR，须取得股东现金事件及对应日期后重算。')
    if item_id == 'CH16.05':
        static, dynamic = metric('financial.phase3e.static_payback'), metric('financial.phase3e.dynamic_payback')
        if number(static) and number(dynamic):
            shown = lambda value: decision_number(value, 'year') if reader_preview else fmt(value)
            return (f'按本次已计算的项目年度净流量，静态回收{shown(static)}年、折现后动态回收'
                    f'{shown(dynamic)}年；折现推迟收回时点，不是实际银行回款日，'
                    '须保留期末现金流和折现率口径。')
    if item_id == 'CH16.06':
        lcoe = model.metric('financial.phase3e.lcoe') or {}
        delivered = metric('energy.delivered.year.1')
        if lcoe.get('status') != 'CALCULATED':
            return (f'首年交付预测{fmt(delivered)}kWh，' if number(delivered) else '') + (
                '平准化度电成本仍受全期无杠杆成本及终期现金成本边界阻断；不能用首年电量'
                '或单位投资代算LCOE，须闭合终期成本与全期同边界交付量后重算。')
    if item_id == 'CH16.08':
        threshold = model.metric('financial.phase3e.break-even-price') or {}
        if threshold.get('status') != 'CALCULATED':
            return ('基准项目NPV虽可计算，盈亏平衡电价仍缺按相同费用和电量口径的反向价格重算；'
                    '不得用基准上网价格推定保本价或目标差距，须固定成本和交付边界逐次重算验证方向。')
    return None


def _project_narrative(model: Any, item_id: str, judgment: str,
                       fields: tuple[str, ...], metrics: tuple[str, ...],
                       fmt: Callable[[Any], str], label_metric: Callable[[str], str],
                       *, reader_preview: bool = False) -> str:
    """Compose evidence and consequence for the actual item's fixed research object.

    No title keyword classifier: only explicitly bound fields, metrics and the
    section's own authored engineering judgment can enter the body.
    """
    result = model.result
    n = result['inputs'].get('normalized', {})
    records = result.get('source_snapshot', {}).get('phase2', {}).get('records', ())
    get = lambda fid: _source_value(n, records, fid)
    calculated = lambda mid: (row.get('value') if (row := model.metric(mid))
                              and row.get('status') == 'CALCULATED' else None)
    ground = result.get('pv_type') == 'utility_scale_ground'
    finding = _research_finding(model, item_id, fmt, reader_preview=reader_preview)
    if finding is not None:
        return finding
    if item_id == 'CH02.01':
        return (('本次报告研究利用现有厂房屋面建设光伏系统、厂区优先自用及余电上网的可行性。'
                 '主要分析可利用屋面、系统配置、发电与经济收益之间的关系。' if not ground else
                 '本次报告研究地面阵列、场区建设与集中送出相结合的方案，'
                 '主要分析可利用土地、发电、送出和市场售电收入之间的关系。')
                + '当前开发主体为合成演示对象，编制本报告的目的在于识别继续研究所需的关键资料，'
                '并非代表真实业主已授权建设。')
    if item_id == 'CH02.02':
        baseline, years = get('project.evaluation_date'), get('project.evaluation_years')
        if baseline and years is not None:
            return (f'本次以{baseline}为评价基准日，按{fmt(years)}年研究建设及运行期间的发电、'
                    '年度费用、税费和项目回报。价格采用名义口径，项目现金流按税后年度期末口径评价；'
                    '这些假设影响不同年份支出与收入的折现比较。股东出资和分配没有独立现金事件，'
                    '不能把已计算的项目回报当作投资者实际收益。')
    if item_id == 'CH02.04':
        start, end = get('resource.period_start'), get('resource.period_end')
        if start and end:
            return (f'发电预测采用登记为{start}至{end}的合成气象资源，设备、场址、'
                    '费用和结算条件也来自本次输入快照。资料及计算结果均保留逐项来源索引，'
                    '以便检查数字在不同章节是否采用同一口径。'
                    '但来源登记不等于取得原始气象授权、现场图纸、合同报价或实际用电记录；'
                    '本阶段只据已绑定的合成材料形成条件性分析。')
    if item_id == 'CH02.05':
        return ('本报告把已计算的装机、发电及项目现金流与真实工程成熟度分别看待。'
                + ('厂区负荷、屋面权利和结构条件仍需原始资料确认。' if not ground else
                   '土地权利、地勘、集中接网与真实交易价格仍需原始资料确认。')
                + '基准方案之外尚无独立情景测算；条件变化时应沿相同来源和计算口径更新结果，'
                '现有预测不构成建设批准或保底收益。')
    if item_id == 'CH03.02':
        dc = calculated('dc_capacity')
        scale = f'{fmt(dc)}kWp' if dc is not None else '待核定规模的'
        if ground:
            return (f'项目拟在地面建设{scale}光伏阵列，发电后按地面集中送出方式参与上网交易。'
                    '可建地块、基础位置与送出线路需要在同一测绘边界内确定；目前缺少可定位的地块坐标、'
                    '签署地勘和正式接入资料，现阶段不能据此锁定场址与施工方案。')
        return (f'项目拟利用现有厂房屋面建设{scale}屋顶光伏系统，发电优先供厂区使用，余电送入电网。'
                '屋顶面积输入尚未落实到逐栋建筑，建筑使用权、结构安全和厂区配电接口会共同限制可安装范围。'
                '取得逐栋测绘、权利文件和接入意见后，才能确定实际布置和余电路径。')
    if item_id == 'CH04.01':
        return (('厂房屋面是拟议建设载体，面积输入用于初步估算阵列空间。' if not ground else
                 '拟议场区面积用于初步安排地面阵列、道路与附属设施。')
                + '当前没有可核对的地址坐标与实测边界，尚不能确定'
                + ('地块红线、' if ground else '逐栋屋面边界、')
                + '障碍和相邻设施。下一阶段须取得测绘资料及可定位的总平面，再确定组件与送出路径。')
    if item_id == 'CH04.03':
        expiry = get('site.rights_expiry')
        return ((f'当前方案记录的使用权期限为{expiry}，' if expiry else '目前缺少可核对的使用期限，')
                + ('但厂房屋面的实际权利、租赁与防水维护责任仍要由原件确认。' if not ground else
                   '但地块性质、用途、实际权利与建设期限仍需由正式土地文件确认。')
                + '期限输入仅供评价期假设使用，不等于权属审查已通过；未确定合法使用条件前不能锁定施工方案。')
    if item_id == 'CH04.06':
        return (('屋面结构、防水层和消防通道资料是确定支架、锚固及吊装方案的前提。'
                 '若原结构需加固，还会改变造价和施工时段。' if not ground else
                 '场区地勘、防洪排水和实际边界会影响支架基础、道路及电缆送出工程。'
                 '缺少这些成果时，工程量和建设费用仍有较大不确定性。')
                + '应先取得专项调查及初步设计，再将工程量与投资估算对应，不能用概算总额反推已包含所有工程。')
    if item_id == 'CH05.04':
        return ('目前只有一个用于演示的合成年份，并非由多年观测筛选出的典型气象年。'
                '将这一年作为后续运营期资源输入，可生成条件性的多年发电预测，'
                '却不能说明场址逐年辐照波动或证明当地长期资源代表性。'
                '下一阶段需要可授权的多年逐时气象资料及相邻站点对照。')
    if item_id == 'CH05.05':
        tilt, azimuth = get('layout.tilt'), get('layout.azimuth')
        if tilt is not None and azimuth is not None:
            return (f'阵列暂按倾角{fmt(tilt)}°、方位角{fmt(azimuth)}°接受合成的阵列面辐照输入。'
                    '倾角和方向改变组件受光方式，故不能直接把水平面辐照数值当成组件面资源。'
                    '当前缺少可独立复核的逐时转置和遮挡资料，场址实际阵列面资源及最优朝向仍需验证。')
    if item_id == 'CH05.06':
        uncertainty = get('resource.uncertainty_fraction')
        if uncertainty is not None:
            return (f'资源不确定性以{fmt(Decimal(str(uncertainty)) * 100)}%输入假设表示，'
                    '但并无真实测站交叉验证或多年份误差统计。'
                    '太阳能资源偏差会影响预测电量及对应收益；这个假设不是置信区间，'
                    '不能直接推成保底发电量或独立敏感性结果。应取得原始逐时数据再校验资源代表性。')
    if item_id == 'CH01.01':
        dc = calculated('dc_capacity')
        years = get('project.evaluation_years')
        if dc is not None and years is not None:
            setting = ('以厂房屋面消纳为主、余电上网' if not ground else
                       '利用地面场址集中送出并参与电力交易')
            return (f'本项目拟建设{fmt(dc)}kWp光伏系统，{setting}。现阶段以'
                    f'{fmt(years)}年为评价期，对设备、发电、投资与回报进行初步分析。'
                    '建设意向及使用条件尚属合成研究资料，不代表已取得真实业主授权或工程审批。')
    if item_id == 'CH01.03':
        investment = calculated('financial.capex.total')
        unit = calculated('financial.unit_investment')
        npv = calculated('financial.phase3e.project_npv')
        if investment is not None:
            outcome = (f'当前项目税后净现值（Net Present Value，NPV）为{decision_number(npv, "CNY")}元，说明在所用折现率及'
                       '预测现金流假设下形成正的模型净现值。' if npv is not None and npv > 0 else
                       f'当前项目税后净现值（Net Present Value，NPV）为{decision_number(npv, "CNY")}元，仍须结合折现率判断回报。'
                       if npv is not None else '项目净现值尚未形成可引用的计算结果。')
            return (f'评价期资本性支出合计{decision_number(investment, "CNY")}元，包含建设与后续设备更换，'
                    '不能全部视为建设期一次性付款。' +
                    (f'按直流装机口径列示的全期含更换单位投资为{fmt(unit)}元/kWp。' if unit is not None else '') + outcome +
                    ('' if '唯一已认证根' in _project_irr_claim(model) else _project_irr_claim(model) + '。') +
                    '这是项目现金流而非股东分红的评价，实际投资决定还依赖工程量、价格及权属。')
    if item_id == 'CH01.05' and (result.get('status') != 'COMPLETE' or
                                result.get('maturity', {}).get('real_project') != 'VERIFIED'):
        return ('建议暂缓投资决策，先开展专项核验。已有的项目回报预测可以用于识别下一步研究价值，'
                '但屋面权属、结构与消防、厂区负荷及余电接入尚未由真实资料闭合。' if not ground else
                '建议暂缓投资决策，先开展专项核验。已有的项目回报预测可以用于识别下一步研究价值，'
                '但土地权属、地勘及道路排水、集中接网和交易价格尚未由真实资料闭合。')
    if item_id == 'CH07.01':
        count, power = get('system.module_count'), get('system.module_power')
        dc, ac = calculated('dc_capacity'), calculated('ac_capacity')
        ratio = calculated('dc_ac_ratio')
        if all(x is not None for x in (count, power, dc, ac, ratio)):
            unit_gap = ' ' if reader_preview else ''
            return (f'拟配置{fmt(count)}块、每块额定功率{fmt(power)}{unit_gap}W的组件，'
                    f'形成{fmt(dc)}kWp直流装机；逆变器交流侧额定容量为{fmt(ac)}kW，'
                    f'直交流容配比为{fmt(ratio)}。组件侧略高于交流侧有助于在非额定辐照条件下'
                    '利用逆变设备，但高辐照时能否充分输出以及是否出现削峰，须结合资源、温度和逆变器限制判断。\n\n'
                    + ('屋面结构与防水要求将约束支架及组件布置。' if not ground else
                       '地块排布、基础与集中送出条件将约束设备布置。') +
                    '当前型号与容量只是初步配置，设备性能和低温电气安全尚待数据表校核。')
    if item_id == 'CH07.02':
        tilt, azimuth, pitch = (get(fid) for fid in ('layout.tilt', 'layout.azimuth', 'layout.row_pitch'))
        if all(value is not None for value in (tilt, azimuth, pitch)):
            return (f'当前阵列按倾角{fmt(tilt)}°、方位角{fmt(azimuth)}°与行距{fmt(pitch)}m布置。'
                    '倾角与方向影响阵列面受光，行距则影响遮挡与通行，不能单凭额定装机确定最终排布。'
                    + ('屋顶还需核定承载、锚固、防水及消防通道的可用区域。' if not ground else
                       '地面还需结合坡度、基础位置、检修道路及排水确定可用阵列面积。'))
    if item_id == 'CH07.04':
        losses = get('system.losses')
        if isinstance(losses, list) and losses:
            return (f'当前方案分别登记{len(losses)}项系统损失输入，涵盖阵列受光、直流输送、逆变及交流送出等环节。'
                    '遮挡与积灰会减少组件接收到的有效辐照，线路及设备效率则影响可交付电量；'
                    '不能把未经确认的损失项简单累加或再次扣减已包含在上游资源中的影响。'
                    '各项顺序、数值与来源已含标志列在设备附录，真实设备和现场遮挡资料仍需校核。')
    if item_id == 'CH07.05':
        topology = get('system.topology')
        if topology:
            return (f'本次以{_text_value("system.topology", topology, fmt) or "组串式方案"}组织初步电气系统。'
                    + ('组件直流侧经逆变后先对接厂区配电与自用计量，余电再进入电网计量边界。'
                       if not ground else '组件直流侧经逆变、集电和升压送出后进入集中交易计量边界。')
                    + '保护配置、电缆路由和交接点尚未形成正式接入设计，不能从拓扑名称推定电气方案获批。')
    if item_id == 'CH07.06' and get('project.has_storage') is False:
        return (('本次屋顶方案没有配置储能，发电优先自用、余电上网的电量路径不包含储能充放电。'
                 '但锚固、防水和建筑消防需要单独形成设计。' if not ground else
                 '本次地面方案没有配置储能，电量按集中送出和交易条件进入结算，'
                 '无需假设储能调度收益；基础与集电送出仍需专项设计。')
                + '如果后续新增储能，应重新明确接入与消防、投资及结算条件，不能沿用当前项目测算。')
    if item_id == 'CH08.01':
        energy = calculated('energy.year.1')
        if energy is not None:
            return (f'本次以合成阵列面资源、组件规模及已有损失参数形成首年预测发电{decision_number(energy, "kWh")}kWh。'
                    '这个结果反映设备在当前气象与系统效率假设下的输出，'
                    + ('厂区自用和余电结算尚需在此后按负荷与计量边界分配。' if not ground else
                       '地面项目的集中送出与结算电量还需按电网和交易限制另行区分。')
                    + '气象输入不是当地多年实测，模型输出并非保底发电承诺。')
    if item_id == 'CH08.04':
        pr, hours, factor = (calculated(mid) for mid in ('pr_observed.year.1',
                                                         'equivalent_hours.year.1', 'capacity_factor.year.1'))
        if all(value is not None for value in (pr, hours, factor)):
            pr_boundary = (model.metric('pr_observed.year.1') or {}).get('boundary_id')
            energy_boundary = ('消费分配前的可利用电量' if pr_boundary == 'AVAILABLE_PRE_CONSUMPTION'
                               else '可送出的预测电量' if pr_boundary == 'GRID_DELIVERABLE'
                               else '当前指标声明的电量边界')
            return (f'首年预测性能比（Performance Ratio，PR）为{fmt(Decimal(str(pr)) * 100)}%，'
                    f'等效利用小时（Equivalent full-load hours）为{fmt(hours)}小时，'
                    f'容量因子（Capacity Factor，CF_cap）为{fmt(Decimal(str(factor)) * 100)}%。'
                    f'性能比关注阵列面辐照与{energy_boundary}的关系；等效小时与容量因子分别按'
                    '装机容量及年度时间口径评价利用水平，三者不能互作现场实测效率证明。'
                    '其可信度仍取决于资源代表性和系统损失假设。')
    if item_id == 'CH08.05':
        availability = get('system.unavailability')
        available, energy = calculated('available_kwh.year.1'), calculated('energy.year.1')
        details = (model.metric('energy.year.1') or {}).get('details', {})
        losses = details.get('losses_kwh', {})
        unavailable, curtailed = losses.get('availability'), losses.get('curtailment')
        if (all(isinstance(value, (int, float, Decimal)) and not isinstance(value, bool)
                for value in (availability, available, energy, unavailable, curtailed))
                and Decimal(str(unavailable)) >= 0 and Decimal(str(curtailed)) >= 0
                and abs(Decimal(str(available)) - Decimal(str(energy))
                        - Decimal(str(curtailed))) <= Decimal('0.01')):
            return (f'不可用比例输入为{fmt(Decimal(str(availability)) * 100)}%，'
                    f'发电损失链在形成可利用量之前已扣除不可用损失{fmt(unavailable)}kWh；'
                    f'限发前可利用电量{fmt(available)}kWh再扣除发电链限发{fmt(curtailed)}kWh，'
                    f'得到限发后发电量{fmt(energy)}kWh。不可用损失不在这两个年度电量之间再次扣减；'
                    '交付及结算截弃仍须按后续计量边界单独核对。')
    if item_id == 'CH03.04' and ground:
        revenue = calculated('revenue.year.1')
        delivered = calculated('energy.delivered.year.1')
        if revenue is not None and delivered is not None:
            return (f'本方案不以厂区自用节费为收益来源。首年预测交付{fmt(delivered)}kWh，'
                    f'按本次价格路径对应的上网销售毛额为{fmt(revenue)}元；这不是已结算或到账的金额。'
                    '地块送出、计量点和交易准入会决定电量能否按该方式出售，'
                    '应以正式接网意见和交易合同核定结算边界。')
    if item_id == 'CH09.01':
        voltage = get('grid.connection_voltage')
        if voltage is not None:
            return (f'初步模型以{fmt(voltage)}kV作为接入电压，'
                    + ('拟由场区集中送出，尚未取得真实接入站点和线路走向。' if ground else
                       '拟经厂区配电系统接入，仍需确认余电计量节点与内部配电接口。')
                    + '登记的接入点仅是未获批准的合成占位，不能据此确定可接入容量、'
                    '保护配置或施工位置；应以电网接入意见及现场一次图重新核定。')
    if item_id == 'CH09.04':
        return (('地面集中送出须分别确认接入系统方案、计量交界点和市场交易准入；'
                 '预测的全额上网收入仍取决于可执行的售电和结算安排。' if ground else
                 '厂区内部配电改造、余电计量和电网接入意见应分开核验；'
                 '自用节费不构成余电已获交易许可的证据。')
                + '目前正式接网意见与交易文件均未取得，下一阶段需由具名电网及交易主体确认接口和结算规则。')
    if item_id == 'CH15.03':
        replacements = get('assets.replacements')
        annual = result.get('evidence', {}).get('financial-ledger', {}).get('annual', ())
        if (isinstance(replacements, list) and len(replacements) == 1 and
                isinstance(replacements[0].get('fields'), dict) and
                calculated('financial.phase3e.project_cash_flow') is not None):
            item = replacements[0]['fields']
            year, days = item.get('assets.replacements.year'), item.get('assets.replacements.downtime_days')
            payment = next((row.get('replacement_cash_paid') for row in annual
                            if row.get('period') == f'OPERATING_YEAR_{year}'), None)
            if (item.get('assets.replacements.asset_id') == 'scenario-inverters'
                    and year is not None and days is not None and payment is not None):
                return (f'模型将逆变器更换安排在运营第{year}年，计划现金支出{fmt(payment)}元，'
                        f'对应{fmt(days)}天停机；该年不仅增加付款，也会减少可交付电量。'
                        '这是一条合成设备寿命与施工窗口假设，不是采购合同、实际付款或性能恢复记录。'
                        '应核对设备寿命、替换范围、报价和停机安排，再同步修订年度电量与现金流。')
    if item_id == 'CH15.04':
        annual = result.get('evidence', {}).get('financial-ledger', {}).get('annual', ())
        tax = annual[1].get('cash_tax_total_project') if len(annual) > 1 else None
        rate = get('tax.corporate_income_rate')
        if tax is not None and rate is not None and calculated('financial.phase3e.project_cash_flow') is not None:
            return (f'按合成税制和{fmt(Decimal(str(rate)) * 100)}%所得税率，'
                    f'首年项目账簿预计现金税费为{fmt(tax)}元，已计入项目年度现金流。'
                    '这是模型的预计支付口径，不是税款实际缴纳证明；应计税额、应付余额与'
                    '真实支付日期需要分别取得税务申报及付款凭证核对。')
    if item_id == 'CH10.05' and not ground:
        revenue = calculated('revenue.year.1')
        if revenue is not None:
            return (f'屋面项目首年预测经济收益{fmt(revenue)}元来自当前自用节费及余电销售边界，'
                    '并非另有逐时市场交易或补贴收入。没有合同及执行依据的其他收益不计入基准；'
                    '购电价格与余电结算价格的变化应分别更新对应收入分项。')
    if item_id == 'CH14.05' and get('finance.debt_ratio') == 0:
        return ('当前合成融资方案明确不安排债务，建设期资本支出按项目资金计划列示，'
                '不能从投资额推算建设期贷款利息，也不能把未列利息当成实际融资条件已落实。'
                '如后续采用借款，应依据提款时点、利率及还款合同重算资金成本。')
    if item_id == 'CH16.01':
        row = model.metric('revenue.year.1') or {}
        ledger = row.get('details', {}).get('ledger', {}) if row.get('status') == 'CALCULATED' else {}
        receipts, savings = ledger.get('export_sales_revenue'), ledger.get('self_value')
        if receipts is not None and savings is not None:
            return (f'首年预测上网销售收入{fmt(receipts)}元，' +
                    (f'厂区自用另可避免购电支出{fmt(savings)}元。' if not ground else
                     '集中式项目没有厂区自用节费。') +
                    ('' if ground else '减少购电支出不是银行收到的售电款，') +
                    '实际现金流还须考虑交易费、运营付款及税费。'
                    '终期账面残值也不能直接作为处置收款。')
    if item_id == 'CH14.04':
        rate = get('capex.contingency_rate')
        total = calculated('financial.capex.total')
        if rate is not None and total is not None:
            return (f'现有评价期资本性支出汇总为{fmt(total)}元。输入中设置了'
                    f'{fmt(Decimal(str(rate)) * 100)}%预备费率，但当前汇总与建设期账簿'
                    '未再按该比例独立增加费用，也不能据此推定报价已包含预备费。'
                    '这使未来的结构加固与防水费用仍可能改变投资边界。' if not ground else
                    f'现有评价期资本性支出汇总为{fmt(total)}元。输入中设置了'
                    f'{fmt(Decimal(str(rate)) * 100)}%预备费率，但当前汇总与建设期账簿'
                    '未再按该比例独立增加费用，也不能据此推定报价已包含预备费。'
                    '地面基础、道路排水及送出工程量的变化可能改变投资边界。')
    if item_id == 'CH06.03':
        dc, ac = calculated('dc_capacity'), calculated('ac_capacity')
        ratio = calculated('dc_ac_ratio')
        if all(isinstance(x, (int, float, Decimal)) and not isinstance(x, bool)
               for x in (dc, ac, ratio)):
            available, export = get('grid.available_capacity'), get('grid.export_power_limit')
            limits = (f'对应的接入余量和送出功率另分别按{fmt(available)}kW、{fmt(export)}kW输入；'
                      if available is not None and export is not None else '')
            return (f'当前直流装机{fmt(dc)}kWp搭配交流额定{fmt(ac)}kW逆变器，'
                    f'直交流容配比为{fmt(ratio)}。直流组件标称规模和逆变器输出能力并不相同；'
                    + limits + '实际接入条件须以电网意见核定，不能从铭牌容量推断已获并网许可或限发电量。')
    if item_id == 'CH02.03':
        focus = ('用地、生态水保及集中送出' if ground else '建筑结构、防火和余电接入')
        return ('本次研究采用输入资料中登记的政策及技术条件作为待查线索，尚无经逐条比对的'
                f'适用法规和标准清单。本项目还需确认{focus}要求；应以项目所在地、实施时间和正式文件逐项确定适用条款，'
                '现阶段不能作合规或审批已通过的结论。')
    if item_id == 'CH03.05':
        dc = calculated('dc_capacity')
        if dc is not None:
            if ground:
                return (f'本次拟以{fmt(dc)}kWp直流规模在地面布置光伏阵列，电量按集中送出和市场售电方案评价。'
                        '土地面积、基础和道路排水将影响阵列的实际布置，接入条件与交易价格则决定可出售电量的收益。'
                        '当前容量和收入来自同一合成方案；真实土地权利、接网意见与交易安排尚未取得，'
                        '项目回报测算不能代替建设必要性论证。下一阶段应先确认用地、送出工程及市场交易条件。')
            self_use = calculated('consumption.year.1')
            use_text = (f'首年预测自用电量{fmt(self_use)}kWh说明模拟负荷与发电有一定匹配，'
                        if isinstance(self_use, (int, float, Decimal)) else '')
            return (f'本次拟利用厂房屋面建设{fmt(dc)}kWp光伏系统，优先由厂区消纳发电量，余电送入电网。'
                    '这样可利用现有建筑空间，减少部分白天购电支出，并取得余电销售收入。'
                    + use_text + '但负荷输入并非真实厂区用电记录，不能据此认定该规模已经符合企业需求。'
                    '取得实际电费账单、屋面布置与结构资料后，才能进一步确定装机和消纳方案。')
    if item_id in {'CH06.04', 'CH06.05', 'CH06.06'}:
        dc, ac = calculated('dc_capacity'), calculated('ac_capacity')
        if dc is not None and ac is not None:
            base = f'基准方案采用{fmt(dc)}kWp组件和{fmt(ac)}kW逆变器。'
            if item_id == 'CH06.04':
                return (base + ('场区阵列排布和基础做法会同时影响用地与投资，下一阶段可比较不同排布及基础方案。'
                                if ground else '屋面可用面积、逆变器配置和余电送出能力共同约束装机，下一阶段可比较不同装机与接线方案。')
                        + '当前没有同一边界的备选方案及其发电、投资结果，不能称已选出经济最优方案。')
            if item_id == 'CH06.05':
                return ('当前方案作为初步研究基准，并非经多方案技术经济比选后选定。'
                        + ('地面基础、道路排水及集中送出工程量尚未通过现场设计确定；'
                                '若改变排布，应同时重估工程费、发电和交易条件。' if ground else
                                '屋面承载与可利用空间尚未通过现场鉴定；若调整容量，应同时复核组件布置、'
                                '逆变器、接入余量及自用电量。') + '当前只有基准投资估算，不宜对未测算方案排序。')
            return (('地面阵列排布与基础选型需结合地勘承载条件、坡度及可建设边界；'
                     '道路排水又决定设备运输和基础施工窗口，集中送出路线会影响电气及土建投资。'
                     '本次尚没有可比较的地勘与线路方案，应先测绘并取得接网条件后形成专项初设。' if ground else
                     '屋顶方案需单独落实结构承载、防水修复、消防通道和生产协调。')
                    + ('' if ground else '这些工程条件决定方案能否实施，不因基准模型已有发电及财务结果而自动满足。'))
    if item_id == 'CH04.05':
        return ('地面设备运输、施工道路和场内排水尚停留在概念方案；实际道路宽度、坡度及排水方向'
                '将影响运输组织、基础施工和占地，须通过测绘及施工组织方案落实。' if ground else
                '屋顶设备运输和吊装目前仅有概念安排。组件进入厂区后还需避开生产通道，落实吊装位置、'
                '屋面临时堆载及防水保护；在确定施工方案前，不能把物流可达等同于屋面可施工。')
    if item_id.startswith('CH11.'):
        works = {
            'CH11.01': ('地面施工须先确认地块红线、道路与排水方向，随后才能确定阵列和设备区的位置。'
                        '现有面积输入没有实测坐标或高程，不能用概念布置图代替施工总平面。' if ground else
                        '屋顶施工须以逐栋结构图和可用屋面图为基础，确定组件、锚固点与消防检修通道。'
                        '现有屋面面积输入不能反映天窗、设备及厂区生产通道的位置。'),
            'CH11.02': ('地面支架基础形式和数量取决于地层、地下水与地形，现有地勘引用尚无签署成果。'
                        '桩基与支架设计需在勘察后配套确定，不能由设备清单倒推基础工程量。' if ground else
                        '屋顶支架需与原结构可靠连接，锚固点选取还受防水层和屋面构造约束。'
                        '没有结构鉴定与节点设计，不能把支架数量直接转化为可施工的基础做法。'),
            'CH11.03': ('地面阵列抗风及支架结构取决于基础承载与实际布置，疏散和集电线路需在总图上落实。'
                        '缺少签署地勘与结构设计，不能认定现有方案安全合格。' if ground else
                        '屋顶结构荷载、锚固、防水与建筑消防疏散须联合复核。现有两个荷载输入只是方案假设，'
                        '没有原结构鉴定和消防通道图，不能判定建筑安全合格。'),
            'CH11.04': ('设备运输道路、排水与电缆沟需结合自然坡度布置，雨季通行与施工扰动也须考虑。'
                        '未取得高程与排水去向前，不能确定道路沟渠工程量。' if ground else
                        '屋顶组件吊装需落实厂区进场路线、起吊位置及临时堆放荷载。'
                        '施工须避开生产和消防通道，开孔及电缆敷设也需要保护屋面防水层。'),
            'CH11.05': ('除组件与逆变器外，地面项目还需基础、道路、排水及送出施工。'
                        '当前仅列概念性土建费用，没有测绘、地勘和完整工程量清单；'
                        '应先确定基础与送出初设，再核量询价，避免实际投资遗漏。' if ground else
                        '屋顶工程费用不仅取决于组件安装，还涉及锚固、防水恢复、吊装和可能的结构加固。'
                        '当前费用是合成概算，缺少结构鉴定和逐栋施工图；应把这些专项工程量列出后再更新报价。'),
        }
        return works[item_id]
    if item_id in {'CH12.02', 'CH12.03', 'CH12.04', 'CH12.05'}:
        return {
            'CH12.02': ('地面阵列施工可能改变地表径流与植被，应先确认土地现状、排水去向及水保要求。'
                        '当前仅有场址登记信息，不能替代生态调查或正式审批。' if ground else
                        '屋顶光伏不直接占用新增地面，但锚固、材料堆放及废旧设备处置仍需与厂区环境管理衔接。'
                        '实际屋面状态和废弃物处理安排尚未取得，不能作环保已达标结论。'),
            'CH12.03': ('地面电缆和送出线路的路径、保护设施及消防间距需在场区图上落实。'
                        '没有现场布置和接网方案，不能仅凭设备铭牌确认电气与消防安全。' if ground else
                        '屋顶阵列须保留建筑消防通道并处理直流拉弧、隔离和电缆穿屋面风险。'
                        '当前消防通道和结构资料尚未实测，需由建筑及电气专业联合审核。'),
            'CH12.04': ('地面项目建设可能影响土地使用者及周边道路通行，送出线路的路径也需与相关利益主体沟通。'
                        '现无正式用地权利或外部协商材料，不能断言周边无影响。' if ground else
                        '屋顶施工涉及原建筑使用者和厂区生产安排，停电、吊装与消防通道变化均需征得实际使用方确认。'
                        '合成业主信息不能代替正式授权或生产协调方案。'),
            'CH12.05': ('土地、生态水保、消防及送出要求各涉及不同专业审查。当前没有可逐项确认适用性的正式文件，'
                        '下一阶段须取得场址调查和主管部门要求，在审批完成前不得把登记资料写为合规结论。'
                        if ground else '屋顶结构、防火和建筑使用管理均需按实际建筑与所在地规定审查。'
                        '现有消防和结构参考信息并非签署意见；在专业结论形成前不应批准现场安装。'),
        }[item_id]
    if item_id in {'CH13.01', 'CH13.04'}:
        tasks = get('schedule.tasks')
        if isinstance(tasks, list) and tasks:
            return (('地面项目应先落实土地和地勘、道路排水条件，再据此形成阵列和送出初设。' if ground else
                     '屋顶项目应先取得真实负荷、屋面权属与结构复核，再据此确定安装和接网方案。')
                    + ('采购可与不依赖前置核验的设计工作衔接，但施工须以权属、工程安全和接网条件落实为前提。'
                       if item_id == 'CH13.01' else
                       '设备采购时点须与设计定稿及现场施工窗口衔接；完成并网调试和相应手续后才能正式运行。')
                    + f'本次合成实施计划列出{len(tasks)}项预排任务，实际日期仍需以相关文件和实际进度调整。')
    if item_id.startswith('CH17.'):
        energy, revenue = calculated('energy.delivered.year.1'), calculated('revenue.year.1')
        npv = calculated('financial.phase3e.project_npv')
        if item_id == 'CH17.01':
            observed = (f'基准首年交付电量预测{fmt(energy)}kWh，' if energy is not None else '')
            return (observed + ('辐照偏低会减少可供分配的发电量；厂区白天负荷偏低则可能减少自用节费，'
                               '同时增加可上网余电，两项收益不能按同一方向推断。'
                               if not ground else '资源偏差会先改变可上网电量，市场价格偏差又会改变同一电量的销售收入。')
                    + (f'首年综合经济收益预测{fmt(revenue)}元。' if revenue is not None and not ground else
                       f'首年预测售电收入{fmt(revenue)}元。' if revenue is not None else '')
                    + '目前没有独立扰动后的电量和现金流结果，不能给出收入敏感性幅度；'
                    + ('应先以真实资源和交易数据设置同边界情景。' if ground else
                       '应先以真实资源、交易和厂区负荷数据设置同边界情景。'))
        if item_id == 'CH17.02':
            return (('屋顶方案需同时考虑白天负荷不足、屋面结构加固和余电接入受限：'
                     '即使光伏发电符合预测，自用比例或实际建设费变化仍可能改变项目收益。' if not ground else
                     '地面方案需同时考虑资源偏差、市场电价和基础送出费用：'
                     '电量、售价与工程量可能相互作用，不宜只改变其中一个输入推断最差情景。')
                    + '当前只有一套基准现金流，未执行悲观与乐观组合的独立计算，故不列三情景回报。')
        if item_id == 'CH17.03':
            return ((f'当前基准项目税后净现值为{fmt(npv)}元，' if npv is not None else
                     '当前项目回报尚无可引用净现值，')
                    + '但这不是电价、资源或投资变化的耐受上限。业主目标与独立价格、费用情景尚未形成，'
                    '不能从基准结果倒推保本电价或投资门槛；需要分别改变有来源的输入并重算现金流。')
        if item_id == 'CH17.04':
            return (('地面土地、地勘与送出工程尚未由正式资料确认，基础和线路费用存在上调风险；'
                     '售电还依赖实际交易价格及计量结算条件。' if ground else
                     '屋面权属、结构与防水资料尚未确认，加固可能增加建设费；'
                     '实际用电曲线和接网意见可能改变自用、余电及对应收益。')
                    + '风险登记仅记录待查事项，下一阶段需分别取得签署文件、工程报价和交易资料，'
                    '据此确定应对措施，不能把当前模型回报视为风险已经消除。')
        return (('地面工程必须先完成用地、地勘及接网审查，'
                 '第13年设备更换还需预留实际付款来源。' if ground else
                 '屋顶项目必须先确认合法使用期限、建筑结构安全、真实厂区负荷和余电接入。')
                + '任何单项条件未满足都可能阻止实施；目前没有完成独立逆向约束测算，'
                '因此只能给出需要关闭的条件，不能给出定量临界值。')
    if item_id in {'CH18.02', 'CH18.04', 'CH18.05'}:
        if item_id == 'CH18.02':
            return (('地面项目的模型回报不能覆盖土地权利、场址地勘和正式接网意见。'
                     '其中任一条件不成立，都可能使当前阵列与送出方案无法实施。' if ground else
                     '屋顶项目的屋面权利、结构承载与建筑消防待取得正式核验；模型回报不能证明这些条件。'
                     '即使用电收益可观，只要屋面无法安全使用或余电不能按计划接入，方案仍须调整。')
                    + '应分别取得真实权利文件、专业设计与电网答复，不能以合成登记替代批准。')
        if item_id == 'CH18.04':
            return (('应取得土地权属、测绘地勘、道路排水和集中接网资料，逐项检查基础与送出报价；'
                     '实际交易价格也需有可执行依据。' if ground else
                     '应取得厂区逐时用电记录、屋面权属、结构鉴定、防水消防图和余电接入意见；'
                     '只有这样才能复核自用电量、施工方案与相关费用。')
                    + '资料登记表用于追踪尚缺的专业成果，不把登记数量或预计完成日当作已关闭事项。')
        return (('可以先开展地块测绘、地勘和接网沟通，同时完善送出及设备更换付款计划；'
                 '这些工作完成后再据实更新价格、工程量和项目现金流。' if ground else
                 '可以先收集电费账单并开展屋面测绘和结构初查，同时与电网沟通余电接入；'
                 '拿到结果后再调整容量与自用收益测算。')
                + '在正式权利、安全、接网与更新后的经济评价未完成前，不应形成真实项目投资批准。')
    if item_id.startswith('CH10.'):
        settlement = _settlement_narrative(model, item_id, fmt)
        if settlement is not None:
            return settlement
        if ground and item_id in {'CH10.04', 'CH10.05'}:
            price = _dataset_rows(result).get('tariff.market_series')
            lineage = result.get('evidence', {}).get('settlement-input-lineage', {}).get('tariff.market_series', {})
            if price and price['header'].get('source_id') == lineage.get('source_id'):
                return (f"市场价格时序已登记{price['row_count']}条，但首年收入指标未形成有效计算值；"
                        "不能由固定分时价格或时序登记数量代填结算收入。")
    facts = []
    for fid in fields:
        if fid not in FIELD_LABELS:
            continue
        value = get(fid)
        rendered = _text_value(fid, value, fmt)
        if rendered is not None:
            facts.append(f'{FIELD_LABELS[fid]}：{rendered}')
    for mid in metrics:
        if item_id in {'CH18.01', 'CH17.03'} or (item_id == 'CH08.03' and mid.startswith('energy.year.')) or (item_id == 'CH01.05' and mid == 'financial.phase3e.project_npv'):
            continue
        if ground and item_id == 'CH03.04' and mid.startswith('consumption.'):
            continue
        if mid == 'financial.phase3e.project_irr' and item_id.startswith('CH01.'):
            facts.append(_project_irr_claim(model))
            continue
        value = calculated(mid)
        if not isinstance(value, (int, float, Decimal)) or isinstance(value, bool):
            continue
        row = model.metric(mid)
        unit = _reader_unit(mid, row.get('unit'))
        if mid.endswith(('_irr',)) or mid in {'pr_observed.year.1', 'capacity_factor.year.1'}:
            value, unit = Decimal(str(value)) * 100, '%'
        if unit == 'CNY':
            unit = '元'
        facts.append(f'{label_metric(mid)}：{fmt(value)}{unit}')
    # Different arrays carry different physical meanings; never stringify the
    # normalized list or use an arbitrary count as a resource finding.
    if item_id.startswith('CH05.'):
        months = get('resource.monthly')
        if isinstance(months, list) and months:
            if item_id == 'CH05.02':
                parts = []
                for key, label in (('ghi', '水平面总辐照'), ('dni', '直接辐照'),
                                   ('dhi', '散射辐照'), ('poa', '阵列面辐照')):
                    numbers = [row.get('fields', {}).get('resource.monthly.' + key) for row in months]
                    if len(numbers) == 12 and all(isinstance(x, (float, int, Decimal)) for x in numbers):
                        parts.append(f'{label}按12个月输入求和为{fmt(sum(Decimal(str(x)) for x in numbers))}kWh/㎡')
                if parts:
                    return ('；'.join(parts) + '。表中单位为kWh/㎡，表示期间辐照量而非W/m²辐照度；'
                            'GHI是水平面全球辐照量，DNI是法向直射辐照量，DHI是水平面散射辐照量，'
                            'POA是阵列面辐照量。DNI到水平面的投影受太阳天顶角影响，不能把GHI=DNI+DHI当作一般物理恒等式；'
                            '当前合成月值仅能作口径受限的算术汇总，不是多年实测资源或已核定发电量；' + judgment)
            if item_id == 'CH05.03':
                temperatures = [r.get('fields', {}).get('resource.monthly.ambient_temperature') for r in months]
                winds = [r.get('fields', {}).get('resource.monthly.wind_speed') for r in months]
                identities = [r.get('fields', {}).get('resource.monthly.month') for r in months]
                if (len(months) == 12 and identities == list(range(1, 13))
                        and all(isinstance(v, (int, float, Decimal)) and not isinstance(v, bool)
                                for v in temperatures + winds)):
                    if len(set(temperatures)) == len(set(winds)) == 1:
                        return (f'本次合成气象数据将12个月的月均气温均设为{fmt(temperatures[0])}℃，'
                                f'月均风速均设为{fmt(winds[0])}m/s。温度会改变组件运行效率，'
                                '风速则影响散热与支架设计；同值输入无法反映实际季节变化，'
                                '月均风速也不能代替极端风速设计值。逐月原始输入列于资源附录，'
                                '后续应取得有时间范围和来源授权的当地气象资料。')
                    return (f'本次采用12个月的合成月均气温和风速输入；气温分别落在'
                            f'{fmt(min(temperatures))}至{fmt(max(temperatures))}℃，风速为'
                            f'{fmt(min(winds))}至{fmt(max(winds))}m/s。这些月均输入影响组件温度损失的预测，'
                            '但不是极端温度或结构设计风速；实际逐时与极值资料仍须另行取得。')
        if item_id == 'CH05.01':
            start, end = get('resource.period_start'), get('resource.period_end')
            if start and end:
                facts.append(f'合成资源时段为{start}至{end}')
    if item_id == 'CH02.04':
        attachments = get('attachments.register')
        if isinstance(attachments, list):
            facts.append(f'已登记{len(attachments)}项合成附件；登记数量不代表原件或授权已核验')
    if item_id == 'CH07.04':
        losses = get('system.losses')
        if isinstance(losses, list):
            names = {'shading': '遮挡', 'soiling': '积灰', 'mismatch': '失配',
                     'dc_cable': '直流线损', 'ac_cable': '交流线损'}
            for row in losses:
                atom = row.get('fields', {})
                kind, value = atom.get('system.losses.kind'), atom.get('system.losses.value')
                if kind in names and isinstance(value, (int, float, Decimal)):
                    facts.append(f'{names[kind]}损失假设{fmt(Decimal(str(value)) * 100)}%')
            facts = facts[:3]
    if item_id == 'CH08.03':
        annual = calculated('energy.annual_array')
        changes = get('assets.replacements')
        if isinstance(annual, list) and len(annual) > 1:
            facts.insert(0, f'年度曲线首年{fmt(annual[0])}kWh、末年{fmt(annual[-1])}kWh')
            if isinstance(changes, list):
                for row in changes[:2]:
                    atom = row.get('fields', {})
                    year = atom.get('assets.replacements.year')
                    if type(year) is int and 1 < year < len(annual):
                        metric = model.metric(f'energy.year.{year}')
                        performance = metric.get('details', {}).get('performance', {}) if metric and metric.get('status') == 'CALCULATED' else {}
                        event = performance.get('event') or {}
                        if (event.get('asset_id') != atom.get('assets.replacements.asset_id')
                                or event.get('downtime_days') != atom.get('assets.replacements.downtime_days')):
                            facts.append(f'第{year}年更换计划尚未与发电事件对齐，不推断更换效果')
                            continue
                        facts.append(f'第{year - 1}年{fmt(annual[year - 2])}kWh、'
                                     f'第{year}年{fmt(annual[year - 1])}kWh、'
                                     f'第{year + 1}年{fmt(annual[year])}kWh；'
                                     f'更换年计入{event["downtime_days"]}天停机，'
                                     + ('无性能恢复增益' if performance.get('replacement_uplift') == 0 else
                                        '性能恢复须以事件记录核对'))
            if facts:
                return '；'.join(facts[:3]) + '。更换年电量变化同时包含衰减与停机，不将次年反弹归因于未记录的组件性能恢复。'
    if item_id.startswith('CH13.'):
        tasks = get('schedule.tasks')
        if isinstance(tasks, list) and tasks:
            names = {r.get('fields', {}).get('schedule.tasks.task_id'):
                     _task_display_name(r.get('fields', {}).get('schedule.tasks.name', ''))
                     for r in tasks if r.get('fields', {}).get('schedule.tasks.task_id')}
            if item_id == 'CH13.03':
                edges = []
                for row in tasks:
                    task = row.get('fields', {})
                    current = names.get(task.get('schedule.tasks.task_id'))
                    if not current:
                        continue
                    for predecessor in task.get('schedule.tasks.predecessor_ids') or []:
                        if predecessor in names:
                            edges.append(f'{names[predecessor]}→{current}')
                if edges:
                    first, following = edges[0].split('→', 1)
                    need = ('土地权利、地勘及集中接网意见' if ground else
                            '屋面权利、结构消防和余电接网意见')
                    return (f'在这条前置依赖链中，“{first}”是“{following}”的前置任务，'
                            '因为工程条件尚不清楚时，采购数量和施工组织均难以确定。'
                            f'对本项目而言，{need}仍须落实，施工完成后还需完成电气调试与并网手续，'
                            '才能按计划投运。任务中的关键路径标记不代表已按真实审批和交付时长'
                            '完成进度计算；前置条件未批准时，不能用预排日期承诺投运。')
                return '任务已提供，但缺少可追溯的前置边，不能推断关键路径。'
            if item_id == 'CH13.02':
                starts = [row['fields'].get('schedule.tasks.start_date') for row in tasks]
                finishes = [row['fields'].get('schedule.tasks.finish_date') for row in tasks]
                if all(isinstance(value, str) and value for value in starts + finishes):
                    baseline = get('project.evaluation_date')
                    chronology = (f'其中部分计划日期早于设定的评价基准日{baseline}（最早{min(starts)}）。'
                                  '由于没有实际进度和交付记录，本报告不据此判断工程是否已实施；'
                                  '正式启动前应重新确认前置条件与实施时间。'
                                  if isinstance(baseline, str) and min(starts) <= baseline else '')
                    return (f'现有实施计划属于模型登记的{len(tasks)}项来源绑定的合成任务，均为预排，'
                            f'计划窗口为{min(starts)}至{max(finishes)}；'
                            '各项持续自然日、前置任务和计划标记在下表逐项列明。'
                            + chronology +
                            '开工、并网及投运须以各前置条件实际落实和相关手续为准，计划标记不是已核定的关键路径。')
            task_facts = []
            for row in tasks:
                task = row.get('fields', {})
                name = task.get('schedule.tasks.name')
                start, finish = task.get('schedule.tasks.start_date'), task.get('schedule.tasks.finish_date')
                if not name or not start or not finish:
                    continue
                predecessors = task.get('schedule.tasks.predecessor_ids') or []
                previous = ('；前置任务：' + '、'.join(names.get(pid, '未核实任务') for pid in predecessors)
                            if predecessors else '；前置任务：无')
                path = '，列为计划关键路径' if task.get('schedule.tasks.critical_path') is True else ''
                try:
                    duration = (date.fromisoformat(str(finish)) - date.fromisoformat(str(start))).days + 1
                except ValueError:
                    continue
                if duration > 0:
                    task_facts.append(f'任务“{_task_display_name(name)}”安排{start}至{finish}，'
                                      f'{duration}个日历日{previous}{path}')

            if item_id == 'CH13.05':
                milestones = [row for row in tasks if 'milestone' in
                              str(row.get('fields', {}).get('schedule.tasks.task_id', '')).lower()]
                if milestones:
                    milestone = milestones[0]['fields']
                    predecessor = '、'.join(names.get(pid, '未核实任务')
                                           for pid in milestone.get('schedule.tasks.predecessor_ids', []))
                    baseline = get('project.evaluation_date')
                    earliest = min((r.get('fields', {}).get('schedule.tasks.start_date', '') for r in tasks), default='')
                    chronology = ('部分前置任务预排日期早于评价日，完成状态没有实证，须重新核定计划后才能据此推进。'
                                  if isinstance(baseline, str) and earliest and earliest <= baseline else '')
                    return (f"拟投运里程碑按合成任务安排为{milestone['schedule.tasks.start_date']}，"
                            f"前置任务为{predecessor or '无'}。{chronology}里程碑日期不是实际开工、获批并网或完成投运手续；" + judgment)
            if item_id == 'CH13.01':
                facts.append(f'另录入{len(tasks)}项合成实施任务，组织责任仍须在正式文件中落实')
            if item_id == 'CH13.04':
                facts.append(f'实施进度按{len(tasks)}项合成任务预排，真实通道与审批窗口尚需核实')
            if not task_facts and item_id in {'CH13.02', 'CH13.03'}:
                facts.append(f'已提供{len(tasks)}项任务，但名称或起止日期不完整，不能锁定持续时间')
        else:
            facts.append('施工任务、持续时间与前置依赖尚未提供，不能倒排关键路径')
    if item_id.startswith('CH14.'):
        items = get('capex.items')
        if isinstance(items, list) and items and item_id in {'CH14.01', 'CH14.03', 'CH14.04', 'CH14.05'}:
            categories = {'construction': '工程建设', 'mounting': '支架',
                          'cables': '电缆', 'transformer': '变压器',
                          'electrical': '电气', 'modules': '组件', 'inverters': '逆变器',
                          'land': '用地', 'grid': '送出', 'contingency': '预备'}
            focus = ({'CH14.03': {'construction', 'land', 'grid'},
                      'CH14.04': {'contingency'}, 'CH14.05': set()}.get(item_id))
            parts = [f"{categories[row['fields']['capex.items.category']]}计划费用{fmt(row['fields']['capex.items.amount'])}元"
                     for row in items if row.get('fields', {}).get('capex.items.category') in categories
                     and isinstance(row['fields'].get('capex.items.amount'), (float, int))
                     and (focus is None or row['fields']['capex.items.category'] in focus)]
            facts.extend(parts[:3])
    if item_id.startswith('CH15.'):
        if item_id == 'CH15.05':
            return ('年度项目现金流同时受到运维付款、税费和设备更换支出的影响。运维是持续的运营现金支出，'
                    '折旧只进入利润与所得税计算，不应再从现金流扣一次；第13年设备更换则是单独的计划现金支付。'
                    '复核逐年账簿时须区分费用计提与实际预计付款，避免把交易费或更换费用重复计入。')
        opex_items = get('opex.items')
        if isinstance(opex_items, list) and item_id == 'CH15.01':
            names = {'maintenance': '检修维护', 'insurance': '保险', 'land_lease': '场地租赁'}
            for row in opex_items[:3]:
                detail = row.get('fields', {})
                category = detail.get('opex.items.category')
                amount = detail.get('opex.items.base_amount')
                if category in names and isinstance(amount, (int, float)):
                    facts.append(f'{names[category]}首年基价输入{fmt(amount)}元')
        annual = result.get('evidence', {}).get('financial-ledger', {}).get('annual', ())
        if calculated('financial.phase3e.project_cash_flow') is not None and len(annual) > 1:
            key = {'CH15.01': ('opex_cash_paid', '首年运维现金支出'),
                   'CH15.02': ('depreciation', '首年非现金折旧'),
                   'CH15.04': ('cash_tax_total_project', '首年项目现金税费'),
                   }.get(item_id)
            if key and annual[1].get(key[0]) is not None:
                facts.insert(0, f'{key[1]}按年度账簿为{fmt(annual[1][key[0]])}元')
            replacements = [r for r in annual[1:] if r.get('replacement_cash_paid')]
            if replacements and item_id == 'CH15.03':
                r = replacements[0]
                facts.append(f"第{r['period'].removeprefix('OPERATING_YEAR_')}年更换现金支出为{fmt(r['replacement_cash_paid'])}元")
    if item_id.startswith(('CH17.', 'CH18.')):
        npv = calculated('financial.phase3e.project_npv')
        irr = calculated('financial.phase3e.project_irr')
        if item_id in {'CH18.01', 'CH17.03'}:
            if npv is not None:
                facts.insert(0, f'合成项目税后年度NPV计算为{fmt(npv)}元')
            facts.insert(1 if npv is not None else 0, _project_irr_claim(model))
        if item_id.startswith('CH17.'):
            scenario = get('scenarios.options')
            if not scenario:
                facts.append({
                    'CH17.01': '资源不确定性仅给出输入边界，未重算辐照、电量及收入扰动，不能报告敏感性斜率',
                    'CH17.02': '悲观与乐观组合尚未执行独立测算，单一基准现金流不能充作三情景',
                    'CH17.03': '目标门槛与基准项目回报不同，尚无改变价格或投资后重算的耐受阈值',
                    'CH17.04': '资源、送出、电价和工程投资风险各需来源及应对责任，基准回报不表示风险已消除',
                    'CH17.05': '反向约束需各自改变有来源的输入并重新验证计量和费用边界，不能从基准推断',
                }[item_id])
            risk_actions = {
                'CH17.01': '资源代表性风险的影响路径是辐照偏差传导至发电量、收入和现金流；当前仅有合成月序列，下一步应取得带时间戳的原始气象数据并完成代表性复核',
                'CH17.02': '设备技术风险可能通过温度、遮挡、失配或停机降低交付电量；当前为铭牌和损失参数输入，下一步应取得设备数据表并完成低温Voc、MPPT、电流和损失边界校核',
                'CH17.03': '电网接入与送出风险可能通过可交付电量和结算边界影响收入；当前接入余量及送出限值是合成条件，下一步应取得正式接网意见、保护定值和计量边界文件',
                'CH17.04': '资源、送出、电价、交易结算和CAPEX风险分别可能压缩收入、增加支出或延迟回款；当前只有基准账簿和风险登记，下一步应逐项绑定合同、报价和审批证据，不以基准回报推断风险已消除',
                'CH17.05': '权属、地勘、消防和实施风险可能在开工前形成独立否决；当前尚无正式现场文件，下一步应按权属、地勘、消防和施工组织分别取得签署版核验材料',
            }
            facts.append(risk_actions[item_id])
    if item_id in {'CH17.04', 'CH18.02', 'CH18.04'}:
        risks = get('risk.items')
        if isinstance(risks, list) and risks:
            categories = {'DOCUMENTARY': '权属及专业文件', 'GRID': '接网',
                          'RESOURCE': '资源代表性', 'ENGINEERING': '施工工程'}
            labels = [categories[r.get('fields', {}).get('risk.items.category')]
                      for r in risks if r.get('fields', {}).get('risk.items.category') in categories]
            if labels:
                facts.append('风险清单登记' + '、'.join(dict.fromkeys(labels[:3])) + '核验事项')
    if item_id == 'CH18.01':
        year1 = calculated('energy.delivered.year.1')
        payback = calculated('financial.phase3e.static_payback')
        ledger = result.get('evidence', {}).get('financial-ledger', {}).get('annual', ())
        if calculated('financial.phase3e.project_cash_flow') is not None and ledger and ledger[0].get('capex_cash_paid') is not None:
            facts.append(f"建设期资本支出按账簿计划支付{fmt(ledger[0]['capex_cash_paid'])}元")
        if year1 is not None:
            facts.append(f'首年交付预测{fmt(year1)}kWh')
        if payback is not None:
            facts.append(f'项目静态回收期{fmt(payback)}年')
    if item_id == 'CH16.03' and calculated('financial.phase3e.equity-investor-cash-flow') is None:
        facts.append('投资者出资—分配现金流未形成；融资后权益可用现金不等于股东IRR')

    if item_id == 'CH01.05' and calculated('financial.phase3e.project_npv') is not None:
        facts.append(f"项目年度NPV已按合成假设计算为{fmt(calculated('financial.phase3e.project_npv'))}元")
        judgment = '项目现金流已形成，并不解除权属、接网、真实来源和投资者现金流的独立决策门槛。'
    if item_id == 'CH11.03' and ground and get('site.geotechnical_reference'):
        facts.append('地勘仅有合成方案引用，未取得签署的地基承载及桩基设计依据')
    if item_id == 'CH04.02' and ground:
        judgment = '可用地面积还须结合实测坡度、道路、排水和设备间距核定，不能仅凭面积输入认定可建。'
    if item_id == 'CH04.04' and ground:
        judgment = '地面阵列遮挡及桩基承载需依据排布和地勘复核，不能沿用屋面荷载判断。'
    if item_id == 'CH14.03':
        judgment = ('地面基础、道路与送出工程须专项核量，不能以设备费用覆盖。' if ground else
                    '屋面加固与防水须专项核量，不能以组件费用覆盖。')
    if item_id == 'CH18.01':
        judgment = ('这些已计算项目指标仅支持合成假设下的阶段性比较，'
                    '不构成股东回报或真实项目投资批准；权属、工程及接网仍需独立核验。'
                    if npv is not None else
                    '项目收益指标未形成完整可引用结果，暂不能作投资回报判断；权属与接网仍需核验。')
    elif item_id == 'CH18.02':
        judgment = ('屋顶权属、结构与接网意见各可独立限制项目实施。' if not ground else
                    '土地使用、地勘道路排水与集中接网意见各可独立限制项目实施。')
    if item_id == 'CH03.01':
        owner, investor, operator = get('project.owner'), get('project.investor'), get('project.operator')
        if owner and investor and operator:
            principal = _text_value('project.owner', owner, fmt)
            if principal and owner == investor:
                return (f'本次合成方案把建设和投资责任均赋予{principal}，运营主体记为'
                        f'{_text_value("project.operator", operator, fmt) or "未核实主体"}。'
                        '这一安排便于将投资与运维责任置于同一模型边界，但不是法人授权或已签署运营委托。')
    if item_id == 'CH18.01':
        npv = calculated('financial.phase3e.project_npv')
        irr = calculated('financial.phase3e.project_irr')
        years = get('project.evaluation_years')
        if npv is not None and years is not None:
            irr_claim = _project_irr_claim(model)
            irr_note = (f'项目IRR（内部收益率）为{decision_percent(irr)}'
                        if irr is not None and '唯一已认证根' in irr_claim else irr_claim)
            construction = result.get('evidence', {}).get('financial-ledger', {}).get('annual', ())
            initial = (construction[0].get('capex_cash_paid') if construction
                       and calculated('financial.phase3e.project_cash_flow') is not None else None)
            investment = (f'建设期计划资本支出{decision_number(initial, "CNY")}元，' if initial is not None else '')
            delivered = calculated('energy.delivered.year.1')
            energy = f'首年交付预测{decision_number(delivered, "kWh")}kWh；' if delivered is not None else ''
            payback = calculated('financial.phase3e.static_payback')
            recovery = f'静态回收期{decision_number(payback, "year")}年。' if payback is not None else ''
            decision = ('建议暂缓投资决策，先开展专项核验。' if result.get('status') != 'COMPLETE' or
                        result.get('maturity', {}).get('real_project') != 'VERIFIED' else '')
            return (decision + f'目前的{fmt(years)}年合成项目方案具有继续研究的价值：{investment}{energy}'
                    f'按年度期末项目税后现金流计算的净现值（Net Present Value，NPV）为{decision_number(npv, "CNY")}元，'
                    f'{irr_note}；{recovery}这些结果说明的是当前方案及假设下的项目回报，'
                    '并非股东回报或实际投资批准。\n\n'
                    + ('优先取得土地权属、地勘道路排水及集中接网意见，核定工程量和交易价格，'
                       '再更新测算及设备更换资金安排。' if ground else
                       '优先取得屋面权属、结构荷载与防水资料，并用真实厂区负荷和余电接网意见'
                       '复核自用收益及投资边界。'))
    if item_id == 'CH18.03' and ground:
        annual = result.get('evidence', {}).get('financial-ledger', {}).get('annual', ())
        replacement = next((row for row in annual if row.get('period') == 'OPERATING_YEAR_13'), None)
        if replacement and replacement.get('replacement_cash_paid') is not None:
            cashflow = calculated('financial.phase3e.project_cash_flow')
            value = cashflow[13] if isinstance(cashflow, list) and len(cashflow) > 13 else None
            return (f"第13年设备更换预计付款{decision_number(replacement['replacement_cash_paid'], 'CNY')}元"
                    + (f"，该年项目净现金流约{decision_number(value, 'CNY')}元" if value is not None else '')
                    + '；年度净流出不等于某一付款瞬间必然资金不足，但已形成明确的资金安排压力。'
                    '实施前应核对付款计划、可动用现金、准备金或其他合法资金安排；当前没有日期化资金余额，不能宣布付款覆盖已满足。')
    if item_id == 'CH18.03' and not ground:
        return ('当前屋顶装机与自用节费以模拟负荷为条件，下一阶段需以实际逐时用电记录检验白天消纳。'
                '若屋面结构或防水需要加固，应将专项费用更新到投资估算，并重新核对接网余量与余电收入。'
                '在这些输入未闭合前，不能给出真实投资门槛已达成或批准建设的结论。')
    if facts:
        # Keep the evidence attached to its authored engineering implication;
        # four or five label:value pairs separated by semicolons are a table,
        # not a paragraph. Full detail remains in the source workbook.
        lead = facts[0].replace('：', '为', 1) if '：' in facts[0] else facts[0]
        context = facts[1].replace('：', '为', 1) if len(facts) > 1 and '：' in facts[1] else (facts[1] if len(facts) > 1 else '')
        return (lead.rstrip('。') + ('，' + context.rstrip('。') if context else '') + '。' + judgment)
    missing = [FIELD_LABELS[fid] for fid in fields if fid in FIELD_LABELS and get(fid) is None]
    return judgment + ('须核对' + '、'.join(missing[:3]) + '的原件和适用性。' if missing else '')


def build_claim(model: Any, item_id: str, title: str, question: str, reasoning_rule: str,
                field_ids: tuple[str, ...], metric_ids: tuple[str, ...], pv_type: str,
                format_value: Callable[[Any], str], label_metric: Callable[[str], str],
                *, reader_preview: bool = False) -> dict[str, Any]:
    """Bind an independently scoped question to only its own canonical evidence."""
    normalized = model.result["inputs"].get("normalized", {})
    used_sources = model.result["inputs"].get("used_sources", {})
    records = model.result.get("source_snapshot", {}).get("phase2", {}).get("records", ())
    field_ids = category_fields(item_id, field_ids, pv_type, normalized.get('project.has_storage') is True)
    if item_id == 'CH08.06':
        field_ids += ('resource.uncertainty_fraction',)
    if pv_type == 'utility_scale_ground' and item_id == 'CH03.04':
        metric_ids = tuple(mid for mid in metric_ids if not mid.startswith('consumption.'))
    if item_id == 'CH01.05':
        metric_ids += ('financial.phase3e.project_npv',)
    if item_id == 'CH18.01':
        field_ids += ('project.evaluation_years',)
        metric_ids += ('financial.phase3e.project_npv', 'financial.phase3e.project_irr',
                       'energy.delivered.year.1', 'financial.phase3e.static_payback',
                       'financial.phase3e.project_cash_flow')
    if item_id == 'CH17.03':
        metric_ids += ('financial.phase3e.project_npv', 'financial.phase3e.project_irr')
    if item_id in {'CH10.04', 'CH10.05'}:
        metric_ids += ('revenue.year.1', 'consumption.year.1')
    if item_id == 'CH08.03':
        replacement_rows = _source_value(normalized, records, 'assets.replacements')
        if isinstance(replacement_rows, list):
            for row in replacement_rows[:2]:
                year = row.get('fields', {}).get('assets.replacements.year')
                if isinstance(year, int) and year > 1:
                    metric_ids += (f'energy.year.{year}',)
    metric_ids = tuple(dict.fromkeys(metric_ids))
    datasets = _dataset_rows(model.result)
    # Optional corroboration is not a missing prerequisite when the ordinary
    # producer already consumed a bound time series / annual result. Keep these
    # fields in the outline above, but do not turn them into false project gaps.
    consumed = model.result.get('evidence', {}).get('settlement-input-lineage', {})
    def bound_series(fid: str) -> bool:
        row = datasets.get(fid)
        lineage = consumed.get(fid, {})
        return bool(row and row['header'].get('source_id') == lineage.get('source_id')
                    and lineage.get('status') in {'ASSUMED', 'VERIFIED'})
    revenue_row = model.metric('revenue.year.1') or {}
    revenue_ledger = revenue_row.get('details', {}).get('ledger', {}) or {}
    conditional_optional: set[str] = set()
    if (item_id == 'CH10.01' and bound_series('load.series')
            and (model.metric('consumption.year.1') or {}).get('status') == 'CALCULATED'):
        conditional_optional.add('load.monthly_bills')
    if pv_type == 'utility_scale_ground' and bound_series('tariff.market_series'):
        if item_id == 'CH10.04':
            conditional_optional.update(('tariff.ppa_price', 'tariff.revenue_share'))
        if (item_id == 'CH10.05' and revenue_row.get('status') == 'CALCULATED'
                and isinstance(revenue_ledger.get('other_benefit'), (int, float, Decimal))):
            conditional_optional.add('revenue.other_items')
    if (item_id == 'CH08.03' and (model.metric('energy.annual_array') or {}).get('status') == 'CALCULATED'
            and _source_value(normalized, records, 'system.annual_degradation') is not None):
        conditional_optional.add('system.degradation_segments')
    field_ids = tuple(fid for fid in field_ids if fid not in conditional_optional)
    input_records = {fid: [record for record in records
                            if record.get("field_id") == _parent_field(fid)
                            and record.get('source_id')]
                     for fid in field_ids if _has_value(_source_value(normalized, records, fid))}
    metric_rows = [model.metric(mid) for mid in metric_ids]
    observed_metrics = [metric for metric in metric_rows if metric is not None]
    present_fields = [fid for fid in field_ids if fid in input_records or fid in datasets]
    absent_fields = [fid for fid in field_ids if fid not in present_fields]
    blocked_metrics = [mid for mid, metric in zip(metric_ids, metric_rows)
                       if metric is None or metric.get("status") != "CALCULATED"]
    field_sources = ({sid for fid in present_fields for sid in used_sources.get(fid, ())}
                     if isinstance(used_sources, dict) else set())
    sources = sorted({sid for metric in observed_metrics for sid in (metric.get("source_ids") or ())}
                     | {record["source_id"] for matches in input_records.values() for record in matches
                        if record.get("source_id")} | field_sources
                     | {row["header"]["source_id"] for fid, row in datasets.items() if fid in present_fields
                        and row.get("header", {}).get("source_id")})
    field_instance_ids = sorted({record["field_instance_id"] for matches in input_records.values()
                                 for record in matches if record.get("field_instance_id")}
                                | {row["header"]["field_instance_id"] for fid, row in datasets.items()
                                   if fid in present_fields and row.get("header", {}).get("field_instance_id")})
    if item_id in {"APP01.01", "APP01.02"}:
        sources = sorted({record["source_id"] for record in records if record.get("source_id")})
        field_instance_ids = sorted({record["field_instance_id"] for record in records
                                     if record.get("field_instance_id")})
    ground = pv_type == "utility_scale_ground"
    judgment = (APPENDIX_JUDGMENTS[item_id] if item_id.startswith("APP") else
                ITEM_JUDGMENTS[item_id.split(".")[0]][int(item_id.split(".")[1]) - 1])
    if ground:
        judgment = {
            "CH03.02": "本项目按地面集中送出研究，土地边界和送出线路仍需测绘定位。",
            "CH03.04": "集中式项目按全额上网和交易边界测算，交付预测仍不是已结算上网电量。",
            "CH04.04": "地面阵列遮挡与基础承载依赖地勘、排布和实测，不适用屋面荷载鉴定。",
            "CH06.06": "地面专项以土地、地勘及集中送出为先决条件，未配置储能不能代替这些核验。",
            "CH10.02": "集中送出须分别核可交付、实际上网和结算电量，不套用屋顶自用模型。",
            "CH11.02": "地面支架基础须按地勘、冻深和场区地形确定，合成支架类型不能证明桩基可施工。",
            "CH11.03": "地面电站的结构安全取决于地勘、桩基与场区疏散，不采用屋顶荷载判断。",
            "CH12.03": "地面场区的消防、集电线路与施工运行风险须分别审查，不采用屋面疏散结论。",
        }.get(item_id, judgment)
    elif item_id == "CH03.02":
        judgment = "本项目按厂房屋面自用及余电上网研究，实际可用屋面范围和接入边界仍需核实。"
    elif item_id == "CH07.06":
        judgment = "未配置储能不意味着屋面结构、防水和消防专项设计已审查；这些边界仍需独立核实。"
    elif item_id == "CH11.02":
        judgment = "屋面锚固须依结构鉴定与防水构造确定，合成支架类型不足以证明屋面连接安全。"
    if item_id == "CH16.02" and (cashflow := model.metric("financial.phase3e.project_cash_flow")) and cashflow.get("status") == "CALCULATED":
        judgment = "年度项目现金流已按本次预测来源与终期假设计算；它不等于历史银行流水或投资者分红，真实项目收益仍须核验。"
    if item_id == "CH18.01" and (model.result.get("status") == "COMPLETE"
                                 and model.result.get("maturity", {}).get("real_project") == "VERIFIED"):
        judgment = "即使测算与资料核对完成，投资建议仍须经过独立专业审查和决策授权。"
    no_storage = _source_value(normalized, records, 'project.has_storage') is False
    no_debt = _source_value(normalized, records, 'finance.debt_ratio') == 0
    not_applicable = ((ground and _source_value(normalized, records, 'project.pv_type') == 'utility_scale_ground'
                       and item_id in {"CH10.01", "CH10.03"})
                      or (no_storage and item_id == "CH10.06")
                      or (no_debt and item_id in {"CH16.07", "APP07.01"}))
    if not_applicable:
        reason = ("集中式地面项目不采用屋顶负荷及自用节费模型" if ground and item_id in {"CH10.01", "CH10.03"}
                  else "当前配置未设置储能，不存在储能调度或设备专项评价" if no_storage and item_id in {"CH07.06", "CH10.06"}
                  else "当前明确配置为无债务，偿债覆盖率不适用")
        status, state = "NOT_APPLICABLE", "NOT_APPLICABLE"
        claim = ("集中式地面站无需将厂区负荷与发电逐时匹配，售电评价转为集中送出边界。"
                 if ground and item_id == "CH10.01" else
                 "集中式项目不按零售分时电价计算自用节费，交易价格及费用仍需另行核实。"
                 if ground and item_id == "CH10.03" else
                 "明确无债务时本次不计算偿债覆盖倍数，零倍不能表述偿债能力。"
                 if item_id == "CH16.07" else
                 "无债务安排不存在有债务偿还计划，不能据此宣称偿债覆盖达标。"
                 if item_id == "APP07.01" else
                 "本项目未配置储能，充放电调度及收益测算不适用。")
        decision = "保留本项并标注不适用，不代入其他项目类型模型。"
        unresolved = "若配置或融资安排改变，需重开本项。"
        next_action = ("核对集中并网和交易边界，不引入屋顶负荷资料。"
                       if ground and item_id in {"CH10.01", "CH10.03"} else
                       "确认储能配置变更后再单独建立调度与安全证据链。"
                       if no_storage and item_id in {"CH07.06", "CH10.06"} else
                       "核对融资协议及债务比例；如新增债务，重建偿债计划。")
        proof = ('project.pv_type' if ground and item_id in {'CH10.01', 'CH10.03'} else
                 'project.has_storage' if no_storage and item_id == 'CH10.06' else
                 'finance.debt_ratio')
        matched = [row for row in records if row.get('field_id') == proof
                   and row.get('source_id') and row.get('value') == normalized.get(proof)]
        supporting_metric_ids = []
        supporting_field_ids = [proof] if matched else []
        sources = sorted({row['source_id'] for row in matched})
        field_instance_ids = sorted({row['field_instance_id'] for row in matched if row.get('field_instance_id')})
    else:
        supporting_metric_ids = [metric["metric_id"] for metric in observed_metrics
                                 if metric.get("status") == "CALCULATED"]
        supporting_field_ids = present_fields
        facts = [f"{label_metric(mid)}为{format_value(metric['value'])} {_reader_unit(mid, metric.get('unit'))}".rstrip()
                 for mid, metric in zip(metric_ids, metric_rows)
                 if metric is not None and metric.get("status") == "CALCULATED"][:2]
        d3 = [f"{('资源' if fid.startswith('resource.') else '负荷' if fid.startswith('load.') else '市场价格')}时序登记{datasets[fid]['row_count']}条（{('合成假设' if datasets[fid]['header'].get('status') == 'ASSUMED' else '来源待复核')}）"
              for fid in present_fields if fid in datasets]
        if d3:
            facts.extend(d3[:1])
        assumptions = [f"{INPUT_FACT_LABELS[fid]}为{format_value(normalized[fid])} {_reader_unit(fid, input_records[fid][0].get('unit'))}".rstrip()
                       for fid in present_fields if fid in INPUT_FACT_LABELS
                       and isinstance(normalized.get(fid), (int, float, Decimal))
                       and not isinstance(normalized[fid], bool) and input_records.get(fid)]
        facts.extend(assumptions[:max(0, 3 - len(facts))])
        has_direct = bool(facts or present_fields or sources or item_id in {"APP10.01", "APP13.01", "APP13.02"})
        status = ("EVIDENCE_BOUND_CONDITIONAL" if (has_direct and sources and not absent_fields
                  and not blocked_metrics) or item_id == "APP13.01" else "LIMITED_BY_MISSING_EVIDENCE")
        if item_id in {"APP10.01", "APP11.01", "APP13.02"}:
            status = "LIMITED_BY_MISSING_EVIDENCE"
        state = "EVIDENCED" if status == "EVIDENCE_BOUND_CONDITIONAL" else "PENDING_VERIFICATION"
        if item_id == "APP13.01":
            facts = ["本次模型、运行、输入、来源及结果身份均保存在统一结果中"]
        elif item_id in {"APP01.01", "APP01.02"}:
            facts = ["本次结果保留来源登记及字段实例记录，但授权和原始附件位置仍须逐条核对"] if sources else []
        elif item_id == "APP13.02":
            facts = ["当前计算尚未闭合" if model.result.get("status") == "PARTIAL" else "计算状态需逐项核对"]
            if model.result.get("maturity", {}).get("real_project") != "VERIFIED":
                facts.append("真实项目资料未核验")
        elif item_id == "APP10.01":
            findings = model.result.get("findings", [])
            facts = ["现有发现项仍需逐项核对关闭材料"] if findings else []
        elif item_id == "APP11.01" and isinstance(model.result.get("formula_snapshot"), dict):
            facts = ["本次统一结果保留了公式快照身份，完整定义仍须在公式工作表逐条核验"]
        # The judgment is authored for this object; observed values qualify it,
        # rather than a title-prefixed inventory masquerading as a conclusion.
        specific_items = {"CH01.02", "CH08.02", "CH09.02", "CH14.02", "CH16.02", "CH16.04"}
        specific = _specific_project_judgment(model, item_id, format_value) if item_id in specific_items else ''
        claim = (specific if item_id in specific_items
                 else _project_narrative(model, item_id, judgment, field_ids, metric_ids,
                                         format_value, label_metric, reader_preview=reader_preview) if item_id.startswith('CH')
                 else appendix_finding(model, item_id, format_value, _source_value, reader_preview=reader_preview))
        fee_evidence = model.result.get('evidence', {}).get('financial-ledger', {}).get('trading_fee_payment')
        if fee_evidence and item_id in {'CH01.05', 'CH10.04', 'CH15.01', 'CH16.02',
                                        'CH18.01', 'APP05.01', 'APP06.01'}:
            sources = sorted(set(sources) | {fee_evidence['source_id']})
            fee_notes = {
                'CH01.05': '本合成测算按交易费当年发生、当年全额预计支付处理，期初无交易费欠款；'
                           '这一年度预测约定不代表真实合同或实际付款记录。',
                'CH10.04': '交易费另列预计付款，期间由本次合成年度支付假设确定，销售收入仍按毛额列示。',
                'CH15.01': ('交易费与运维费分别列账、分别预测付款，不以运维付款安排推算交易费支付。'
                            if reader_preview else '运维费现金与交易费预计付款分别列账，后者不继承运维付现比例。'),
                'CH16.02': '交易费为合成来源约定的预计支付，不是已付款凭证；税基扣费不等于现金付款。',
                'CH18.01': '上述回报含有独立的交易费同年支付假设，仅对合成年度项目边界成立。',
                'APP05.01': '交易费预计付款另列，不作为运维费第二次扣减。',
                'APP06.01': '交易费计提、预计付款和应付余额须与本附录逐期收支桥相互核对。',
            }
            claim += fee_notes[item_id]
        if blocked_metrics:
            bound = f"{label_metric(blocked_metrics[0])}未形成可引用结果"
        elif absent_fields:
            bound = "原始条件尚未全部进入本项证据链"
        elif not sources and item_id != "APP13.01":
            bound = "缺少可追溯的直接来源"
        else:
            bound = "当前仅有合成或待核实的来源，不代表现场审查"
        decision = ("已计算数据仅供本次方案边界复核，不作为真实项目批准或投资意见。"
                    if status == "EVIDENCE_BOUND_CONDITIONAL" else
                    "本项尚不能形成无条件工程、合规或投资认可。")
        if item_id in {"CH01.05", "CH18.01"} and (model.result.get("status") != "COMPLETE"
                                                  or model.result.get("maturity", {}).get("real_project") != "VERIFIED"):
            blockers = (["权属核验"] if _source_value(normalized, records, 'site.rights_status') not in {'verified', 'VERIFIED', 'approved'} else [])
            blockers += (["正式接网意见"] if _source_value(normalized, records, 'grid.opinion_status') not in {'approved', 'APPROVED', 'verified', 'VERIFIED'} else [])
            cashflow = model.metric("financial.phase3e.project_cash_flow")
            blockers += (["完整现金流"] if cashflow is None or cashflow.get("status") != "CALCULATED" else [])
            decision = "暂缓投资决定；" + "、".join(blockers or ["真实项目的独立核验"]) + "尚未闭合。"
        gaps = []
        if absent_fields:
            gaps.append("缺少直接输入：" + "、".join(absent_fields))
        if blocked_metrics:
            blocked_id = blocked_metrics[0]
            blocked_metric = model.metric(blocked_id)
            gaps.append(label_metric(blocked_id) + "未形成有效计算值（" +
                        str(blocked_metric.get("reason") if blocked_metric else "结果不存在") + "）")
        if not sources:
            gaps.append("无直接来源绑定")
        unresolved = ("；".join(gaps) + "。" if gaps else
                      "真实项目资料与专业审批尚未核验；本项仅在当前输入及计算版本内成立。" if
                      model.result.get("maturity", {}).get("real_project") != "VERIFIED" else
                      "本项依赖当前输入与版本；关键条件变化时须重新核对。")
        next_action = reasoning_rule.rstrip("。") + "。"
    if not_applicable:
        reasoning_rule = reason + "；只有适用前提改变才应重新计算。"
    causal_reasoning = (reasoning_rule if not_applicable else
                        f"{bound}；{next_action}")
    # A single bounded conclusion is preferable to a repeated research-task
    # paragraph. The distinct next action, gaps and decision live in the
    # checklist; the Word body states only what this snapshot can support.
    narrative = [part for part in claim.split('\n\n') if part]
    return {
        "claim_id": f"CLAIM-{item_id}", "canonical_result_hash": model.result["result_hash"],
        "core_question": question,
        "central_claim": claim, "claim_status": status,
        "supporting_metric_ids": supporting_metric_ids, "supporting_input_field_ids": supporting_field_ids,
        "supporting_formula_ids": sorted({metric["formula_id"] for metric in observed_metrics
                                         if metric.get("status") == "CALCULATED" and metric.get("formula_id")})
        if not not_applicable else [],
        "field_instance_ids": field_instance_ids, "source_ids": sources,
        "causal_reasoning": causal_reasoning, "decision": decision,
        "unresolved": unresolved, "next_action": next_action, "state": state,
        "narrative": narrative, "summary": claim,
    }
