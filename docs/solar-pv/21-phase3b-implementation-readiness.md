# Phase 3B 工程与发电实施准备（只读，不是实现验收）

## 状态与依据

Phase3A最终源码已在仓库外冻结快照中完成全量回归3277/0/6，基础契约验收记录已保存；本文件只保存后续已批准3B的准备，3A本地提交后才进行生产变更，不登记数值通过。基线为19号批准边界、20号架构、有效Catalog和17号计划。只读任务deleg_757ae2a1的建议经过父任务核查，不能把子任务自述当成已验证事实。

engineering库存27条，当前全部NOT_IMPLEMENTED/executor=null。完整有效定义、符号、单位、条件、原字段绑定与拟模块见reports/solar-pv/phase3a-effective-execution-mapping.json。两个类别独立编排，原89公式、469字段、281域不改。

## 1. 对四项所谓新增审批阻断的核查

| 观察项 | 实读事实与处理 | 当前是否需改冻结契约 |
|---|---|---|
| 异构逆变器聚合限幅 | F-AC-INVERTER-POWER原符号已写“同一逆变器聚合组额定交流有功容量”“该组时段直流输入功率”；原边界已要求每台/同质组先限幅再求和。按组实例化同一标量公式，再明确汇总，不修改原方程。 | 不因该标量式本身申请改公式。实际逐组容量、效率和DC分配必须有可验证来源；缺失时阻断，不猜测均匀分配。若后续确需新增关键用户数据契约，另提交具体差异。 |
| PF=0 | 原字段数值Schema下界0，但quality.py:43–45已有POWER_FACTOR_NOT_POSITIVE且说明禁止换算；公式原假设0<PF≤1。 | 保留旧Schema/原输入，计算入口和kernel执行原有严格正前置条件；不将0视为正常计算，也不为此改字段。 |
| kgCO2e/kWh与tCO2e/kWh | 原始字段保持kg单位；公式域绑定明示NORMALIZED_INPUT_OR_EXPLICIT_TRANSFORM且目标t单位。units.py已有同维度精确kg/t换算。 | 使用现有公开convert_unit，在适配层记录source/target/rule/exact/原实例及证据；公式仍做原乘法。不是在kernel中偷偷除1000，也不改同名原字段。 |
| 月度累计POA与时序积分 | 输出域的绑定类型本就CALCULATED_OR_VALIDATED_LEDGER_OUTPUT；F-POA-IRRADIATION只定义区间平均辐照度乘实际时长。 | 月度已给累计量按显式来源分支进入验证账簿；时序分支实际执行原积分式。直接接受月度累计不能冒充执行了时序积分公式，也不能插值造小时。 |

这些处置复用已冻结的符号、前置条件、单位桥和已批准的方法/期间/边界区分，不新增D1勘误，不自行批准实质性数学或关键数据架构变化。全量3A失败的历史Git夹具问题属于验证环境，不涉及本表的数学判断。

## 2. 原子核与编排接口约束（拟实施）

- 与execution_registry.run_formula(formula_id, values, options, catalog=...)接线；值按冻结公式域ID，原始字段只在已验证适配入口读取。不得直接绕过Phase2读取原用户值。
- 通过common.number/integer/required与显式local Decimal context控制精度、范围、缺值；禁止float/数字字符串/NaN/Inf及缺金额补零。数学零必须由已知输入计算或显式声明，不是未知默认。
- options拟承载期间、物理边界、受控方法选择/参数ID、数值精度、索引集合及单台/同质组上下文；具体类型在3B落地并严格校验，不声称目前已有KernelOptions类。
- 每个j/k/t/y实例保持稳定row_id/期间/边界和逐原子来源。相同域名可以属于不同明确节点上下文，不能只以共享字典最后赋值选择模型。
- 原子结果使用common.calculated/nonvalue已有结构；调用者将ContractError转为明确阻断，不通用except→0。NOT_APPLICABLE、UNDEFINED、BLOCKED_MISSING_INPUT、BLOCKED_METHOD_REVIEW和NOT_IMPLEMENTED区分。
- 单位变化复用convert_unit，只传精确数值，记录原单位、目标单位、rule_id、exact及显式舍入策略。不能借普通power维度转换抹掉DC/AC/nameplate边界。
- 单个项目缺某方法不意味着产品公式不适用；产品IMPLEMENTED_TESTED必须有独立数值锚和边界证据，注册仍不算实现。

## 3. 27条原子域映射

| formula_id | 输入域 | 输出域 |
|---|---|---|
| `F-DC-CAPACITY` | `equipment.module_count`, `equipment.module_power_kwp` | `capacity.dc_kwp` |
| `F-AC-CAPACITY` | `equipment.inverters.rated_ac_kw`, `equipment.inverters.ids` | `capacity.ac_kw` |
| `F-DC-AC-RATIO` | `capacity.dc_kwp`, `capacity.ac_kw` | `capacity.dc_ac_ratio` |
| `F-POA-IRRADIATION` | `resource.poa_irradiance_kw_m2`, `time.interval_hours`, `time.resource_intervals` | `resource.poa_irradiation_kwh_m2` |
| `F-FIRST-YEAR-ENERGY` | `capacity.dc_kwp`, `resource.poa_irradiation_kwh_m2`, `constants.stc_irradiance_kw_m2`, `energy.pr_assumed` | `energy.first_year_ac_kwh` |
| `F-LOSS-COMPOSITE` | `losses.independent_rates`, `losses.active_ids` | `losses.retention_factor` |
| `F-DC-TIME-POWER` | `capacity.dc_kwp`, `resource.effective_poa_kw_m2`, `constants.stc_irradiance_kw_m2`, `equipment.power_temperature_coefficient`, `resource.cell_temperature_c`, `constants.stc_cell_temperature_c`, `losses.dc_retention` | `energy.dc_power_kw` |
| `F-AC-INVERTER-POWER` | `capacity.ac_kw`, `losses.inverter_efficiency`, `energy.dc_power_kw` | `energy.inverter_ac_power_kw` |
| `F-AVAILABLE-ENERGY` | `energy.inverter_ac_power_kw`, `losses.ac_retention`, `losses.transformer_retention`, `losses.export_line_retention`, `energy.auxiliary_kw`, `time.interval_hours`, `losses.availability` | `energy.available_kwh` |
| `F-ENERGY-AGGREGATION` | `energy.boundary_interval_kwh`, `energy.boundary_id`, `time.aggregation_period`, `time.period_interval_ids` | `energy.period_totals_kwh` |
| `F-INITIAL-DEGRADATION` | `energy.first_year_pre_initial_kwh`, `degradation.initial_fraction` | `energy.first_year_ac_kwh` |
| `F-ANNUAL-DEGRADATION` | `energy.first_year_ac_kwh`, `degradation.annual_fraction`, `time.operating_year` | `energy.annual_kwh` |
| `F-PIECEWISE-DEGRADATION` | `degradation.previous_retention`, `degradation.yearly_fraction`, `degradation.replacement_uplift` | `degradation.annual_retention` |
| `F-EQUIVALENT-HOURS` | `energy.annual_kwh`, `energy.reference_capacity_kw` | `energy.equivalent_hours` |
| `F-CAPACITY-FACTOR` | `energy.annual_kwh`, `energy.reference_capacity_kw`, `time.year_hours` | `energy.capacity_factor` |
| `F-PR-OBSERVED` | `energy.annual_kwh`, `capacity.dc_kwp`, `resource.poa_irradiation_kwh_m2`, `constants.stc_irradiance_kw_m2` | `energy.pr_observed` |
| `F-EXPORT-LIMIT-ENERGY` | `grid.export_limit_kw`, `time.interval_hours` | `grid.export_limit_kwh` |
| `F-UNIT-KW-MW` | `units.power_kw`, `constants.kilo_scale` | `units.power_mw` |
| `F-UNIT-KWH-MWH` | `units.energy_kwh`, `constants.kilo_scale` | `units.energy_mwh` |
| `F-UNIT-IRRADIANCE-W-KW` | `units.irradiance_w_m2`, `constants.kilo_scale` | `units.irradiance_kw_m2` |
| `F-UNIT-COST-WP-KWP` | `units.cost_per_wp`, `constants.kilo_scale` | `units.cost_per_kwp` |
| `F-UNIT-DC-CAPACITY` | `capacity.dc_kwp`, `constants.kilo_scale` | `units.dc_mwp` |
| `F-UNIT-AC-CAPACITY` | `capacity.ac_kw`, `constants.kilo_scale` | `units.ac_mw` |
| `F-USABLE-AREA` | `site.total_area`, `site.exclusion_area` | `site.usable_area` |
| `F-AVERAGE-ANNUAL-ENERGY` | `energy.annual_kwh`, `time.operating_year_count` | `energy.mean_annual_kwh` |
| `F-EMISSIONS-AVOIDED` | `environment.eligible_energy`, `environment.grid_emission_factor` | `environment.avoided_emissions` |
| `F-TRANSFORMER-ACTIVE-LIMIT` | `grid.transformer_capacity`, `grid.power_factor` | `grid.transformer_active_limit` |

## 4. 资源、损失与年度链

1. 月度数据来自已验证base_export的resource.monthly，不能误当D3独立dataset。逐年/逐月累计含期间、阵列朝向和遮挡边界，不从月度造小时。月度直接来源状态和实际积分状态分别记录。
2. D3当前dataset为resource.timeseries/load.series/tariff.market_series。逐行严格读取，经hash/原子来源重验并保留完整时间轴；跨数据集对齐仍由消费者验证。辐照度W→kW和分钟→小时各一次。
3. G_POA必须是区间均值；只有瞬时样点但无积分方法则方法阻断，GHI/DNI/DHI不能替换POA。年度小时数由实际期间决定，不能对闰年固定8760。
4. ambient→cell必须调用受控thermal.method及明确安装参数/来源，不将ambient直接当cell。工程中间精度由配置控制，不按显示金额位数截断。
5. 建立有来源的损失覆盖台账：DC、AC、变压器、线路、自耗、可利用率、温度、限幅、初始衰减及PR包含范围分别核查。已在上游包含者不得重复扣除。
6. F-FIRST-YEAR-ENERGY与F-INITIAL-DEGRADATION有同名输出，按选定方法/节点上下文互斥，不能都覆盖。固定年度与分段衰减同理；设备更换后需要明确性能恢复、停机/容量重算，不简单整体年系数缩放。
7. 缺限发上限不默认为无限；变压器有功换算不代表并网许可；排放估算不代表碳认证/碳现金收入。

## 5. 独立小锚（尚未运行生产核）

以下由父任务在工具中以Decimal独立计算，仅用于后续测试expected，不是生产内核结果，不是完整合成项目，不增加公式通过计数。

| 目的 | 明确SYNTHETIC输入 | 独立结果 |
|---|---|---|
| DC容量 | 1200块×0.550kWp/块 | 660.000kWp |
| 区间POA积分 | [0.8,0.6,0.4,0.2]kW/m²，各0.25h | 0.500kWh/m² |
| 温度/DC功率 | 660×0.8×(1−0.004×20)×0.855 | 415.3248000kW |
| 逐组限幅 | min(200,0.98×250)+min(150,0.97×100) | 297.00kW；不能替换为总量min(350,0.98×350)=343.00kW |
| 可用电量 | (297×0.99×0.98×0.97−2)×0.25×0.95 | 65.9074180250kWh |
| 排放单位桥 | 1000kWh×convert_unit(0.5kgCO2e/kWh→tCO2e/kWh) | 0.5000tCO2e；转换exact=True，rule_id=unit/v1:kgCO2e/kWh->tCO2e/kWh |
| 变压器有功 | 1000kVA×0.9 | 900.0kW，不是接入批准 |

3B实施必须补齐27条的正常/边界/非法/缺数/适用性、单位/来源/精度、独立数值校核，并真实接入月度/时序消费者。Phase3A提交及核验完成后才开始生产变更；不进入3C或报告阶段来掩盖3B缺口。
