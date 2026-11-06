"""Per-item editorial claim bindings for the frozen solar-PV report outline.

Only canonical normalized inputs and canonical metrics may support a claim. An
editorial fixture is never an evidence source. Missing results remain missing.
"""
from __future__ import annotations

from functools import lru_cache
from decimal import Decimal
import json
from pathlib import Path
from typing import Any, Callable

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
        'project.ownership_mode site.rights_holder site.rights_document_id',  # CH03.03
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
    'APP08.02': '阈值与属性验收',
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
    "APP01.01": ("本次使用的资料是否逐份有身份、授权和可读位置？", "核验来源登记、附件位置与授权，不把来源编号当作已读全文。", (), ()),
    "APP01.02": ("关键输入能否回溯到字段实例与原始来源？", "逐项核对输入血缘，缺少实例位置时保留追溯缺口。", (), ()),
    "APP02.01": ("12个月气象资料的分量、覆盖和单位能否核查？", "取得资源原始月表及授权；月发电量不能倒推辐照分量。", ("resource.monthly", "resource.period_start", "resource.period_end"), ()),
    "APP02.02": ("月度发电、消纳与交付电量能否同边界对账？", "核对时区、月度能量和结算边界，不由发电量代替交付。", ("load.series",), ("energy.monthly.year.1", "energy.year.1", "energy.delivered.year.1")),
    "APP03.01": ("设备和布局的原子参数是否有可核验型号？", "取得组件、逆变器和支架数据表并逐字段复核。", ("system.module_model", "system.inverter_model", "layout.row_pitch"), ("dc_capacity", "ac_capacity")),
    "APP03.02": ("每项损失与退化是否只计入一次？", "核查损失顺序、已含标志与衰减时点。", ("system.losses", "system.annual_degradation"), ("energy.annual_array",)),
    "APP04.01": ("费用清单是否覆盖设备、土建、预备与专项投资？", "逐项核实工程量、数量单价、税与分类专项范围。", ("capex.items", "capex.includes_land", "capex.includes_storage"), ("financial.capex.total",)),
    "APP04.02": ("报价、付款与投资总额能否勾稽？", "补充报价有效期及付款时点，避免应付替代实付。", ("capex.items", "finance.debt_schedule"), ("financial.capex.total",)),
    "APP05.01": ("年度现金运维与更换、非现金折旧是否分账？", "核对全期运维、更换与残值计划，折旧不作为现金支出。", ("opex.items", "assets.depreciation", "assets.replacements"), ("financial.opex.cash_lifecycle",)),
    "APP05.02": ("适用税制与实际税金能否逐年衔接？", "取得税制与现金支付依据，对账应计、应付及实付。", ("tax.regime_reference", "tax.vat_recovery_timing"), ("financial.tax.cash_lifecycle",)),
    "APP06.01": ("建设至终期的项目投资现金事件是否闭合？", "取得有日期的投资、税、营运资金和终期收付记录。", ("finance.working_capital",), ("financial.phase3e.project_cash_flow",)),
    "APP06.02": ("资本金全期现金流是否独立包含提款和偿债？", "核实股东出资、提款、本息和分配，不能沿用项目现金流。", ("finance.debt_schedule",), ("financial.phase3e.equity-investor-cash-flow",)),
    "APP07.01": ("有债务时偿债计划与可偿债现金是否逐期匹配？", "取得合同还本付息日程与CFADS定义后计算覆盖倍数。", ("finance.debt_schedule", "finance.cfads_definition"), ("financial.phase3e.dscr",)),
    "APP07.02": ("无债务与偿债零分母是否被正确区分？", "核查债务比例与每期偿债额，零分母不得填零倍。", ("finance.debt_ratio", "finance.debt_schedule"), ("financial.phase3e.dscr",)),
    "APP08.01": ("单因素和组合情景是否分别独立运行？", "提供各因素变化、控制变量及运行身份后比较结果。", ("scenarios.options",), ()),
    "APP08.02": ("阈值与反向约束是否经独立数值验收？", "补充门槛目标、重算结果和方向性复核。", ("targets.project_irr", "targets.payback_years"), ("financial.phase3e.break-even-price",)),
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
  '反向约束须检验来源授权、计量边界和项目类型，单次结果不是验收。'),
 'CH18': (
  '当前只能暂缓实质投资决定，先关闭独立否决条件。',
  '权利、结构或地勘及电网意见可各自否决推进，局部财务数值不能覆盖。',
  '进入下一阶段须先取得权属、工程及接入证据，再检验现金流门槛。',
  '待核事项须按场址、资源、售电及财务分别取证，版本更新不等于关闭。',
  '决策里程碑以具名审批和专业复核为前提，评价日期不是开工承诺。'),
}
APPENDIX_JUDGMENTS = {
 'APP01.01': '来源编号只是索引，原件位置、授权和可读性仍须逐份核查。',
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
 'APP08.02': '盈亏门槛需目标口径、重算及方向验收，展示值不证明约束。',
 'APP09.01': '政策须定位文号、地区及有效期，适用意向不是现行证明。',
 'APP09.02': '政策冲突须逐条审查，未核验文本不能形成合法性意见。',
 'APP10.01': '阻断事项须关联关闭材料和责任，发现项存在不等于解除。',
 'APP10.02': '推进门槛须映射权属、工程、接网及现金流证据，不由日期满足。',
 'APP11.01': '公式快照只是定义索引，适用边界仍须逐条核对。',
 'APP11.02': '符号须解释单位、下标及求和边界，编号不定义变量。',
 'APP12.01': '缩写须对应中英全称和首次出现位置，避免同名异义。',
 'APP12.02': '功率、能量及辐照单位不可互换，单位投资须说明装机分母。',
 'APP13.01': '配套文件须指向同次模型、运行、输入、来源及结果，不能拼接历史快照。',
 'APP13.02': '结构生成、计算成熟度、真实来源及页面审阅是不同门禁。',
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


def _has_value(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}

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
    return {"degree": "°", "m2": "㎡", "year": "年", "piece": "件", "1": ""}.get(unit or "", unit or "")


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


def _specific_project_judgment(model: Any, item_id: str, format_value: Callable[[Any], str]) -> str:
    """Write six bounded conclusions from this run's Phase 2, ledger and metrics."""
    result = model.result
    n = result["inputs"].get("normalized", {})
    records = result.get("source_snapshot", {}).get("phase2", {}).get("records", ())
    bound = {row.get("field_id"): row.get("value") for row in records if row.get("source_id")
             and row.get("status") not in {"REJECTED", "INVALID"}}
    category = result.get("pv_type")
    ground = category == "utility_scale_ground"

    def inp(fid):
        # The Phase 2 record must identify the *same* value, not merely a field
        # name; list-child source metadata is flattened only for comparison.
        source = bound.get(fid)
        if fid == "capex.items" and isinstance(source, list):
            source = [{"row_id": row.get("row_id"), "fields": {
                key: atom.get("value") if isinstance(atom, dict) and "value" in atom else atom
                for key, atom in row.get("fields", {}).items()}}
                      for row in source if isinstance(row, dict)]
        return n.get(fid) if source is not None and source == n.get(fid) else None

    def metric(mid):
        row = model.metric(mid)
        return row.get("value") if row and row.get("status") == "CALCULATED" else None

    def money(number):
        return f"{format_value(number)}元"

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
        energy = f"；首年合成资源下预测发电{format_value(year1)}kWh" if year1 is not None else "；首年发电结果尚未形成"
        return (f"本次方案按{format_value(dc)}kWp直流组件和{format_value(ac)}kW交流逆变器配置，"
                f"以{format_value(years)}年作为测算期{energy}。这只是设备铭牌与模型发电边界，"
                f"并非获批装机或保底上网电量；{location}。")
    if item_id == "CH08.02":
        months = metric("energy.monthly.year.1")
        if not isinstance(months, list) or len(months) != 12 or year1 is None:
            return "首年月度与年度发电未同时形成可对账结果，暂不推断季节发电。"
        reconciled = abs(sum(Decimal(str(x)) for x in months) - Decimal(str(year1))) < Decimal("0.01")
        reconciliation = ("与年度发电指标一致" if reconciled else "与年度发电指标不符，需先查清口径")
        depreciation = inp("system.annual_degradation")
        tail = (f"后续年份按{pct(depreciation)}年衰减另行重算" if depreciation is not None
                else "后续年份衰减假设尚需核对")
        boundary = "屋顶自用与余电上网" if not ground else "地面集中送出与结算"
        return (f"首年合成资源计算的12个月发电量中，1月为{format_value(months[0])}kWh、"
                f"12月为{format_value(months[-1])}kWh；逐月汇总{reconciliation}，对应年度"
                f"{format_value(year1)}kWh。月份的发电序列不是辐照实测，也不能直接作为{boundary}电量；"
                f"{tail}，仍需真实资源、损失和计量边界核验。")
    if item_id == "CH09.02":
        transformer, available, export = (inp("grid.transformer_capacity"),
                                         inp("grid.available_capacity"), inp("grid.export_power_limit"))
        if ac is None or transformer is None or available is None:
            return "变压器、可用接入余量与交流铭牌尚未同时绑定，不能作出并网可行结论。"
        constraint = (f"可用接入余量低于{format_value(ac)}kW交流铭牌，不能以变压器额定容量直接认定可全额送出"
                      if Decimal(str(available)) < Decimal(str(ac)) else
                      "可用接入余量不低于交流铭牌，但仍不等于核准可送出功率")
        export_text = f"；送出限值假设另为{format_value(export)}kW" if export is not None else ""
        point = "屋顶自用后的余电" if not ground else "地面电站集中上网的全部电量"
        opinion = inp("grid.opinion_status")
        opinion_text = "待取得" if opinion == "pending" else (str(opinion) if opinion else "待核")
        factor = inp("grid.power_factor")
        factor_text = (f"本次功率因数{format_value(factor)}仍是合成假设" if factor is not None
                       else "功率因数未提供，不将kVA强行折算为可接入kW")
        return (f"{format_value(transformer)}kVA变压器是设备视在容量，不能直接与kW有功功率比较；"
                f"{factor_text}。本次填报可用接入余量{format_value(available)}kWac，{constraint}{export_text}。"
                f"{point}还受保护、线路与计量边界约束；正式接网意见{opinion_text}，"
                "仅属合成条件，正式电网接入与送出限值待批复，不视为已获接入许可。")
    if item_id == "CH14.02":
        items = inp("capex.items")
        rows = [r.get("fields", {}) for r in items if isinstance(r, dict)] if isinstance(items, list) else []
        initial = [r for r in rows if str(r.get("capex.items.payment_date", ""))[:4] <= str(result.get("evaluation_date", ""))[:4]]
        later = [r for r in rows if r not in initial]
        equipment = {"modules": ("组件", "块"), "inverters": ("逆变器", "台"),
                     "mounting": ("支架", "项"), "cables": ("电缆", "项"),
                     "transformer": ("变压器", "台"), "electrical": ("电气设备", "项"),
                     "storage": ("储能设备", "套")}
        listed = [r for r in initial if r.get("capex.items.category") in equipment]
        if not listed:
            return "本次未取得可绑定的设备分项数量、单价和税口径，设备费用不能由总额倒推。"
        largest = max(listed, key=lambda r: Decimal(str(r.get("capex.items.amount", 0))))
        descriptions = [f"{equipment[r['capex.items.category']][0]}{format_value(r['capex.items.quantity'])}"
                        f"{equipment[r['capex.items.category']][1]}×{money(r['capex.items.unit_price'])}/"
                        f"{equipment[r['capex.items.category']][1]}={money(r['capex.items.amount'])}"
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
        civil_text = (f"，其中土建施工{money(civil[0]['capex.items.amount'])}另列，不能充作设备费"
                      if civil and civil[0].get("capex.items.amount") is not None else "")
        return (f"本次设备清单以{equipment[largest['capex.items.category']][0]}"
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
        opex, tax = first.get("opex_cash_paid"), first.get("cash_tax_total_project")
        if any(v is None for v in (start, wc, receipts, opex, tax)):
            return "项目现金流虽有结果，但缺少与之配套的投资、营运资金或首年收支账簿，不能作分项解释。"
        benefit = (f"合成的余电预计回款{money(receipts)}与自用节费{money(savings)}"
                   if not ground and savings is not None else f"预计上网回款{money(receipts)}")
        replacements = [r for r in ledger[1:] if r.get("replacement_cash_paid")]
        renewal = (f"；第{replacements[0]['period'].removeprefix('OPERATING_YEAR_')}年计划更换支出"
                   f"{money(replacements[0]['replacement_cash_paid'])}"
                   if replacements and str(replacements[0].get("period", "")).startswith("OPERATING_YEAR_") else "")
        return (f"项目税后年度现金流建设期为{money(flow[0])}，由建设期计划资本支出{money(start)}"
                f"和营运资金投入{money(wc)}构成；运营首年{benefit}，"
                f"扣运维现金{money(opex)}与项目现金税费{money(tax)}后，"
                f"对应首年净流入{money(flow[1])}{renewal}，已在后续年度扣除而非重复计入初始投资。"
                "本项是合成年度项目收支预测，不是实际银行流水、已收回款或投资者分红；"
                "股东出资及分配事件未闭合，不能由项目净流量替代。")
    if item_id == "CH16.04":
        npv, irr = metric("financial.phase3e.project_npv"), metric("financial.phase3e.project_irr")
        static, dynamic = metric("financial.phase3e.static_payback"), metric("financial.phase3e.dynamic_payback")
        discount = inp("finance.project_discount_rate")
        flow = metric("financial.phase3e.project_cash_flow")
        if (any(x is None for x in (npv, irr, static, dynamic, discount, years))
                or not isinstance(flow, list)
                or inp("project.price_basis") != "nominal"
                or inp("project.cashflow_tax_basis") != "post_tax"
                or inp("finance.cashflow_timing") != "PERIOD_END"):
            return "项目税后NPV、IRR、回收期与折现率尚未在同一计算边界闭合，不可替代为投资者收益。"
        outcome = ("在本次假设下NPV为正且IRR高于折现率，模型项目回报超过折现假设"
                   if npv > 0 and Decimal(str(irr)) > Decimal(str(discount)) else
                   "本次测算未同时满足NPV为正及IRR高于折现率的条件")
        return (f"按合成的{format_value(years)}年项目税后、名义价格及年度期末现金流，"
                f"使用{pct(discount)}项目折现率得到年度NPV{money(npv)}、IRR{pct(irr)}；"
                f"静态回收期{format_value(static)}年、动态回收期{format_value(dynamic)}年，{outcome}。"
                "这不是逐笔日期NPV或实际投资者出资—分红回报：未提供股东现金事件及真实银行流水，"
                "也未获得现场审批、签署交易与专业复核，不能据此批准投资。")
    return ""


def build_claim(model: Any, item_id: str, title: str, question: str, reasoning_rule: str,
                field_ids: tuple[str, ...], metric_ids: tuple[str, ...], pv_type: str,
                format_value: Callable[[Any], str], label_metric: Callable[[str], str]) -> dict[str, Any]:
    """Bind an independently scoped question to only its own canonical evidence."""
    normalized = model.result["inputs"].get("normalized", {})
    used_sources = model.result["inputs"].get("used_sources", {})
    records = model.result.get("source_snapshot", {}).get("phase2", {}).get("records", ())
    datasets = _dataset_rows(model.result)
    input_records = {fid: [record for record in records
                            if record.get("field_id") == fid and record.get("value") == normalized.get(fid)]
                     for fid in field_ids if _has_value(normalized.get(fid))}
    metric_rows = [model.metric(mid) for mid in metric_ids]
    observed_metrics = [metric for metric in metric_rows if metric is not None]
    present_fields = [fid for fid in field_ids if _has_value(normalized.get(fid)) or fid in datasets]
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
            "CH03.04": "集中式项目按全额上网和交易边界测算，交付预测仍不是已结算上网电量。",
            "CH04.04": "地面阵列遮挡与基础承载依赖地勘、排布和实测，不适用屋面荷载鉴定。",
            "CH06.06": "地面专项以土地、地勘及集中送出为先决条件，未配置储能不能代替这些核验。",
            "CH10.02": "集中送出须分别核可交付、实际上网和结算电量，不套用屋顶自用模型。",
            "CH11.02": "地面支架基础须按地勘、冻深和场区地形确定，合成支架类型不能证明桩基可施工。",
            "CH11.03": "地面电站的结构安全取决于地勘、桩基与场区疏散，不采用屋顶荷载判断。",
            "CH12.03": "地面场区的消防、集电线路与施工运行风险须分别审查，不采用屋面疏散结论。",
        }.get(item_id, judgment)
    elif item_id == "CH07.06":
        judgment = "未配置储能不意味着屋面结构、防水和消防专项设计已审查；这些边界仍需独立核实。"
    elif item_id == "CH11.02":
        judgment = "屋面锚固须依结构鉴定与防水构造确定，合成支架类型不足以证明屋面连接安全。"
    if item_id == "CH16.02" and (cashflow := model.metric("financial.phase3e.project_cash_flow")) and cashflow.get("status") == "CALCULATED":
        judgment = "年度项目现金流已按本次预测来源与终期假设计算；它不等于历史银行流水或投资者分红，真实项目收益仍须核验。"
    if item_id == "CH18.01" and (model.result.get("status") == "COMPLETE"
                                 and model.result.get("maturity", {}).get("real_project") == "VERIFIED"):
        judgment = "即使计算与来源门禁完成，投资建议仍须经过独立专业审查和决策授权。"
    no_storage = normalized.get("project.has_storage") is False
    no_debt = normalized.get("finance.debt_ratio") == 0
    not_applicable = ((ground and item_id in {"CH10.01", "CH10.03"})
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
        supporting_metric_ids, supporting_field_ids, sources, field_instance_ids = [], [], [], []
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
        specific = _specific_project_judgment(model, item_id, format_value)
        claim = (specific if item_id in {"CH01.02", "CH08.02", "CH09.02", "CH14.02", "CH16.02", "CH16.04"}
                 else judgment + ("本次测算显示：" + "；".join(facts) + "。" if facts else ""))
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
            blockers = (["权属"] if not _has_value(normalized.get("site.rights_status")) else [])
            blockers += (["接网意见"] if not _has_value(normalized.get("grid.opinion_status")) else [])
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
        gaps.append("合成或未验证资料不构成真实项目第三方证明")
        unresolved = "；".join(gaps) + "。"
        next_action = reasoning_rule.rstrip("。") + "。"
    if not_applicable:
        reasoning_rule = reason + "；只有适用前提改变才应重新计算。"
    causal_reasoning = (reasoning_rule if not_applicable else
                        f"{bound}；{next_action}")
    # A single bounded conclusion is preferable to a repeated research-task
    # paragraph. The distinct next action, gaps and decision live in the
    # checklist; the Word body states only what this snapshot can support.
    narrative = [claim]
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
        "narrative": narrative, "summary": "".join(narrative),
    }
