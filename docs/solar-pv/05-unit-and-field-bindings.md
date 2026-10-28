# 公式域字段归一化与账簿绑定复核

Phase1冻结；配套 `05-field-bindings.json` 覆盖281个公式域字段。这里是接口/单位/依赖规则，不是已实现数据适配或计算算法。每个值还必须保留03要求的原单位、来源、处理规则及上下游实例。不能仅因为ID可匹配就宣称数值正确。

## 明确的非恒等映射

| 输入/状态来源 | 公式域目标 | 冻结归一化规则 | 未来验收 |
|---|---|---|---|
| `system.module_power`（单块Wp） | `equipment.module_power_kwp`（kWp/块） | 确认单块铭牌与STC，再按SI千倍进制归一化；不能把Wp原值直接当kWp。混合规格按型号分组。 | T-BOUND-UNITS、T-DC-CAPACITY |
| `system.dc_capacity` kWp、`system.ac_capacity` kWac | `capacity.dc_kwp`、`capacity.ac_kw` | 数值单位对应但永久保留DC/AC与峰值标签；输入目标与设备计算输出分候选，校核不能互相覆盖。 | T-DC-CAPACITY、T-AC-CAPACITY、T-BOUND-TRANSFORMER |
| `system.inverter_unit_ac`、count/model | `equipment.inverters.rated_ac_kw`、ids | 单机/同质设备组清单展开后求和，数量只应用一次；不同单机限幅先算后汇总。不能把单机当总AC容量。 | T-AC-CAPACITY、T-AC-INVERTER-POWER |
| `resource.timeseries.poa` W/m² | `resource.poa_irradiance_kw_m2`及有效POA | 先按SI千倍进制规范为kW/m²；有效POA再按已选损失方法处理；已含遮挡/污损不再扣。年/月辐照量来自真实时段积分，不能把W/m²直接当kWh/m²。 | T-BOUND-UNITS、T-POA-IRRADIATION、T-LOSS-COMPOSITE |
| `load.series.energy`或power＋interval | `load.interval_kwh` | 已有电量仅做同计量口归一化，不再乘时长；功率样本按声明区间平均/积分规则转时段电量。时区、时长、缺测和重复需校验；年度总量不能倒生成8760。 | T-BOUND-LEAP、T-MISSING-LOAD、T-PROP-BALANCE |
| `system.unavailability` | `losses.availability` | 前者是不可利用比例，后者是可利用比例，须取互补；若停机已在时序扣除则不再作为额外乘因子；不作同值别名。 | T-AVAILABLE-ENERGY、T-LOSS-COMPOSITE |
| `resource.timeseries.ambient_temperature`与风/设备模型 | `resource.cell_temperature_c` | degC与°C文字规范不改变数值；环境温度不能直接赋给电池片工作温度。需选择有依据的温度子模型/参数/适用域及独立测试；未核验时该逐时模型BLOCKED，年度PR情景也须明确假设/成熟度。 | T-BOUND-TEMP、T-DC-TIME-POWER |
| `system.temperature_coefficient` | `equipment.power_temperature_coefficient` | 输入为每摄氏度的小数系数；设备若提供百分数则先规范小数并保存原值/单位，禁止重复百分比换算；摄氏温差与开尔文温差同幅，不将绝对温度直接混用。 | T-BOUND-TEMP、T-DC-TIME-POWER |
| `environment.grid_emission_factor` kgCO2e/kWh | 同名公式域 tCO2e/kWh | 同名不代表同单位；显式按SI千倍进制从kg规范到t，保存源单位和因子年度/区域/口径；不将tCO2/MWh和kgCO2e/kWh只改标签。需核温室气体范围是否同为CO2e。 | T-EMISSIONS-AVOIDED、T-BOUND-UNITS |
| `currency`与`currency/year` | 公式域“元”及年度金额 | 公式“元”是选择评价币种的金额记号，仅project.currency=CNY时为人民币元。跨币种须原币、汇率、日期/来源。运营费率型年度金额须按声明年度/部分年/通胀计划转年度现金账，不直接把每年费率当任意时段现金。 | T-ANNUAL-OPEX、T-OPEX-ESCALATION、T-FIN-CASHFLOW |
| `finance.loan_rate`年度比例 | `debt.annual_interest_rate`合同单利 | 必须确定单利/复利、日计数、重定价和宽限定义；不能把有效年度折现率直接当可任意乘年分数的单利率。合同缺失仅情景，不称法定统一利率。 | T-DEBT-INTEREST、T-FIN-DEBT-BALANCE |
| `finance.debt_schedule`计划值 | 应付/付现/资本化各债务账簿 | 模型是预测时需明确预计支付假设；实际已付须真实支付证据。资本化未付利息只增债务账，不重复现金扣除；计划应付与实际付现不是天然同一字段。 | T-DEBT-BALANCE、T-INTEREST-BALANCE、T-FIN-CASHFLOW |
| `finance.working_capital`与合同 | 年度净营运变化 | 总金额不是每年现金流变化值；按期初期末和已采用现金/权责桥生成，已在收入/税/资本应付款桥计入的不能再扣。 | T-PROJECT-CASH-FLOW、T-EQUITY-AVAILABLE-CASH-FLOW |
| 场景changed_field/value文本 | 灵敏度数值输入 | 只解析允许且已在03登记的字段类型/单位，不执行文本代码；记录基准/扰动/冻结其他值，完整模型重算。未给价格搜索域/步长/求根策略时保持待实现，不伪造阈值。 | T-FIN-SENSITIVITY、T-PROP-TARGET |
| `constants.stc_cell_temperature_c` | STC温度 | 属标准/设备定义，不是站址环境值。当前绑定未伪填数值；实施选用方法前以已获手册/适用标准核验，来源缺失保留BLOCKED。 | T-DC-TIME-POWER |

## 计算输出、账簿状态与输入分层

`CALCULATED_OR_VALIDATED_LEDGER_OUTPUT`是公式生产/校核的结果，可能还关联独立用户目标值，但不能由目标覆写。`CALCULATION_LEDGER_STATE`是建设期/税务/应收应付/债务/现金事件/回收点/敏感性等有定义的中间台账，不是让用户首轮输入数百个未知值。它们必须来自已列支持输入、正式合同规则与已注册公式图，阶段实现前仍NOT_IMPLEMENTED。

`input_field_ids`是支持性血缘而非“这些量可直接相加”的表达式。真实计算图在Phase2/3固定索引、账簿期初期末、时序/年度聚合、正负方向、金额/税边界和所选方法；有多生产方法的字段必须互斥选择，尤其首年初始损失与PR不能循环或重复扣减。对外数据状态与计算实现状态分开，任何UNKNOWN/CONFLICT不能静默代0。

当前闭合的是文档引用，不是数值运行链。标准、法定税制、融资协议和温度子模型专业复核待办仍有效；不能因为这里建立别名/单位规则就关闭对应功能测试或产品安全/真实性门禁。
