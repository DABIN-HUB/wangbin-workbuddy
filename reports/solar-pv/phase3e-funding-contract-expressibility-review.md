# Phase 3E 前置资金契约可表达性专项审查（静态、只读）

**结论：现有冻结原始输入＋已批准 D2 方法配置不能完整、结构化、可校验地表达“付款瞬间项目主体可支配的非受限资金”。** 它能表达部分金额、合成情景方法、个别付款**日期**及其来源/哈希；不能把法律主体、账户、付款前逐笔到账与支出、同日顺序、实际股东往来和资金限制闭合成经校验的事件序列。**Phase 3E 仍 `BLOCKED`；历史四笔付款的 `INDETERMINATE` 不变。** 本审查没有重算任何付款前后余额或四笔覆盖率，也没有计算 Phase 3E 指标。

## 1. 审查范围、实际身份与依据

- 实际分支 `main`，HEAD `6823f740b9d34647a13c5cdc874d90a23e0bcd7e`；启动暂存区为空。冻结基线 `SOLAR-PV-1.0.0`；原始目录 `solar-pv-input-catalog/1.0.0`（469 字段）、`05-formulas.json` 原主表 77 条＋扩展 12 条共 89 条、281 绑定域；现行有效公式定义 `solar-pv-formula-definitions/1.0.1`，其身份 `617a2e9d314c095bd2ec893939c930a2323be6fd7805da12bf6d6fdd70274808`。目录与运行时 Phase 2 输入 Schema 不可混为一个文件。[`docs/solar-pv/README.md:1-3,26-30,43`; `docs/solar-pv/19-phase3-approved-implementation-contract.md:14-22`]
- 现行运行时契约：`services/solar-pv-engine/schemas/project-input.schema.json`（`urn:wangbin:solar-pv:project:1.0.0`）；导出 `solar-pv-input-export/1.0.0`；D2 `services/solar-pv-engine/src/wangbin_solar_pv/calculation/schema/method-config.schema.json`（`solar-pv-method-config/1.0.0`）；结果 `.../schema/calculation-result.schema.json`（`solar-pv-calculation-result/1.0.0`）。具体约束与消费行为以相邻 `method_config.py`、`input_contract.py`、`financial_ledger.py`、`result_contract.py` 为准。[`19-phase3-approved-implementation-contract.md:40-46`; `services/solar-pv-engine/src/wangbin_solar_pv/calculation/method_config.py:139-161`]
- 只读检查了指定 `README.md`、`03-input-fields.json`、`05-formulas.json`、`05-field-bindings.json`、`07-category-boundaries.md`、`08-requirement-traceability.csv`、`17/18/19` 号计划/审查/批准文件、Phase 3D 修复验收、Phase 3E 启动审计及前两轮资金审计；另核查 Phase 2 Schema/规范化/来源快照、D2 Schema/实现、Phase 3D 账簿/结果 Schema、两案修复后 `input.json`、`methods.json`、`result.json`、`result.sha256`、独立参考/验收和上游 Phase 3C `settlement.json`。机器证据 `phase3e-funding-contract-expressibility-evidence.json` 保存关键原字节 SHA-256、案例身份与结构化矩阵。旧 `README.md`、`07-category-boundaries.md` 的历史阶段状态不是当前 3D/3E 的实时验收结论；以后续报告及源码现状判定。[`reports/solar-pv/phase3d-repair-and-acceptance.md:3-11`; `reports/solar-pv/phase3e-funding-coverage-recheck.md:1-20`]
- 冻结需求血缘：`R-S06-L119` 投资分项、`R-S06-L121` 项目/股东独立现金流和资本开支/营运资金/融资/税、`R-S06-L122` 年末 NPV 与多时点日期、`R-S06-L123` 项目/股权 IRR、`R-S06-L126` CFADS/债务服务；`R-CH16-02`、`R-CH16-03`、`R-CH16-04` 属 Phase 5 报告章节约束，不伪称新的 Phase 3E 需求。冻结 `F-CASH-FUNDING-BALANCE` 定义 `OPEN_y` 为项目主体期初非受限现金；`F-EQUITY-INVESTOR-CASH-FLOW` 使用股东出资/分配/退出；`F-DATED-NPV` 有现金事件集合及年分数。**公式域需求存在不等于已有可入账原始事件接口。**[`docs/solar-pv/08-requirement-traceability.csv` 的上述实际 ID；`docs/solar-pv/05-formulas.json:5729-5766`; `docs/solar-pv/05-field-bindings.json:504-523,2230-2343`; `docs/solar-pv/17-phase3-implementation-plan.md:85-95`]

本专项审查要求的账户/银行证明和付款瞬间资金覆盖是为了回答此前资金门禁；不能把它们冒充冻结文件已逐字要求新增的 469 字段。下文只分析可表达性和必要兼容方向，不自行扩展产品范围。`EXPRESSIBLE` 仅用于一个**确切的已有子要素**满足类型/单位/来源/约束，不表示整个资金事实 PASS；`PARTIALLY_EXPRESSIBLE`、`NOT_EXPRESSIBLE` 按完整可审计事实判定。此处没有把任一付款资金证明核心要素标记 `NOT_REQUIRED`；年度项目收益的计算与瞬时银行流动性证明是不同的任务。[`docs/solar-pv/18-phase3-preimplementation-review.md:42-69`; `reports/solar-pv/phase3e-funding-coverage-review.md:18-25,71-79`]

## 2. 逐要素差异矩阵

`屋/地` 分别指 `industrial_rooftop` / `utility_scale_ground`；“案例有”仅是合成输入，不是银行证据；“哈希覆盖”仅表示**已经入契约的内容**参与身份。所有路径均为实际字段、方法参数或冻结公式域，而非建议新增字段。

| 数据要素 | 冻结要求依据 | 现有字段或配置路径／类型和单位 | 表达能力 | 当前案例数据（屋/地） | 计算链支持 | 阻断原因／类别 |
|---|---|---|---|---|---|---|
| 期初非受限现金 | `R-S06-L121`; `F-CASH-FUNDING-BALANCE` | D2 `cash.opening_cash`: number≥0、unit=`currency`；`project.currency`: ISO 风格三字母；公式域 `checks.cash_opening`: 元 | **PARTIALLY_EXPRESSIBLE** | 均 `0 CNY`，`SYNTHETIC/ASSUMED`，非验真银行存量 | 参数随方法入复合哈希；3D 未读取它、3E 未实现 | 法人/账户标识、准确时刻、非受限金额及证明状态未作为一份受控余额绑定；**DATA_MISSING＋契约缺口＋消费缺口** |
| 归属主体、账户、资金类别 | `R-S06-L121`; `F-CASH-FUNDING-BALANCE` | `project.ownership_mode`: 枚举模式；`project.project_id`；`finance.debt_schedule.drawdown`: number/currency；`finance.working_capital`: number/currency | **PARTIALLY_EXPRESSIBLE** | 屋顶 `owner_invested` 未核；地面未填所有权模式；均非具体法人/银行账户 | 3D 能分债务提款、应收、年度收益与营运资金；不区分账户现金存量 | 所有权模式/项目 ID ≠ 收付法律实体/账户；额度/应收/预测收入 ≠ 已到账；**契约缺口** |
| 单笔付款日期、投资额及资产关联 | `R-S06-L119`, `R-S06-L121`; `F-CAPEX-PAYMENT-BALANCE` | `capex.items.row_id`, `.asset_id`, `.amount`(number/currency), `.currency`(三字母), `.payment_date`(format=`date`)，`assets.replacements.row_id` | **EXPRESSIBLE（仅该子要素的合成日期/金额/关联）** | 两案 2037-06-01／2040-06-01 两行，金额 190,000／720,000 CNY；原子 `UNVERIFIED`，源 `SYNTHETIC-phase3d-repair` | 3D 用 `payment_date` 核对并按年度归集付现/应付，含关联；来源入 Phase 2 快照及哈希 | 不是准确银行扣款时间；不能由此推出此前余额；**其他收付事件仍有契约缺口** |
| 通用逐笔收付事件及时间 | `R-S06-L121`, `R-S06-L122`; `F-CASH-RECEIPTS`, `F-DATED-NPV` | `finance.debt_schedule.date`(date)及 `.drawdown/.principal/.interest/.fees`(currency)；公式域 `finance.cash_event_ids`, `finance.dated_cash_flows`；D2 收付比例为 1 的数组 | **PARTIALLY_EXPRESSIBLE** | 两案 `finance.debt_schedule=[]`；收款/OPEX/税/本息仅年度合成预测，未有逐笔日期 | 3D 债务日期/投资付款日期归年度；没有带主体、账户、状态、来源和所有收入/支出类型的通用流水生产者 | 事件 ID、计划/实际时刻、方向、账户、已付/应付/预测、关联业务、限制状态不能一体校验；**DATA_MISSING＋契约/生产者缺口** |
| 同日现金顺序与付款前后余额 | `R-S06-L121`, `R-S06-L122`; `F-DATED-NPV`, `F-CASH-FUNDING-BALANCE` | `.payment_date`、`finance.debt_schedule.date` 仅 `date`；D2 `time.cashflow_timing` 为 `YEAR_END/ DATED`，`time.day_count` 为日计数；`site.timezone` 为站址文本 | **NOT_EXPRESSIBLE** | 两案 `YEAR_END`；无同日实际到账/付款事件时分秒、顺序或付款前余额 | `financial_ledger._year()` 折为期间、年度行；3E 未实现，不能在排序不确定时合法返回具体瞬时余额 | 没有事件时间戳精度、账户时区绑定、同刻稳定排序/受控优先级、付款生效与到账区别；**契约缺口而非仅“DATED 未启用”** |
| 股东实际出资 | `R-S06-L121`, `R-S06-L123`; `F-EQUITY-INVESTOR-CASH-FLOW`, `F-CASH-FUNDING-BALANCE` | 仅公式域 `equity.contributions`(元，`CALCULATION_LEDGER_STATE`)；支持映射列 `finance.debt_ratio`、`finance.debt_schedule`、`project.ownership_mode` 等 | **NOT_EXPRESSIBLE（实际事件）** | 均无股东、实付金额/时间/收款主体记录 | 3D 没有实际出资生产者，3E 未实现 | `debt_ratio` 与投资差额不能倒推出到账股本；无现成经 Schema 校验的股东交易入口；**DATA_MISSING＋契约缺口** |
| 股东分配、留存及退出 | `R-S06-L121`, `R-S06-L123`; `F-EQUITY-INVESTOR-CASH-FLOW` | D2 `equity.distribution_fractions`(逐期 0..1 比例)、`equity.minimum_cash_reserve`(number/currency)；公式域 `equity.distributions`, `equity.exit_receipts`(元) | **PARTIALLY_EXPRESSIBLE（策略）；实际分红事件 NOT_EXPRESSIBLE** | 均为 25 期比例 1、最低留存 0，`SYNTHETIC/ASSUMED`；没有股东实收记录 | D2 参数入方法哈希但 3D 不消费为分配/留存，3E 未实现 | 策略不是实际付款；无收款股东、金额/时间、可分配额及存量账；**DATA_MISSING＋契约/消费缺口** |
| 受限资金 | `R-S06-L121`, `R-S06-L126`; `F-EQUITY-AVAILABLE-CASH-FLOW` 的 `working_capital.equity_net_change`、`F-CASH-FUNDING-BALANCE` 的非受限余额 | D2 `equity.minimum_cash_reserve`(number≥0/currency)仅最低储备**政策**；公式域 `checks.cash_opening`(非受限元) | **PARTIALLY_EXPRESSIBLE（最低储备规则）；实际受限余额 NOT_EXPRESSIBLE** | 均储备假设 0，无受限账户、限制/解限凭证 | 3D 未消费储备规则，无限制状态/释放事件 | 无受限原因、归属主体、金额、有效/解除时刻及更换能否使用的结构化判断；**DATA_MISSING＋契约缺口** |
| 资金事件来源、身份及哈希 | `R-S06-L121`, `R-S06-L122`; `F-DATED-NPV`, `F-CASH-FUNDING-BALANCE` | Phase 2 信封 `field_instance_id`, `source_id`, `status`, `unit`, 来源/生效期；导出 `input_hash`, `source_snapshot_id`；D2 `source_kind/status/source_reference`；计算 `method_config_hash`, `result_hash` | **PARTIALLY_EXPRESSIBLE** | 现有原子/方法与更换日期在快照/复合哈希中；缺失实体/事件/限制为未知而非 0 | 现有输入、方法、3C 身份、3D 年账封存可追；不存在应纳入哈希的逐笔完整事件 | 哈希能防现有负载漂移，不能证明来源真实或绑定契约无法表达的事实；**契约＋消费缺口** |

矩阵里的 `EXPRESSIBLE` 不表示该付款已发生、当日资金可用或四笔覆盖已知。`finance.working_capital` 是单项营运资金占用（3D 建设期增加、终期回收），不是银行余额；`finance.cashflow_timing` 在两案是文本 `PERIOD_END`，不能代替现金事件。日期字段和自由文本不能作为计算引擎可校验的账户限制。依据：`03-input-fields.json` 的对应字段定义、`05-field-bindings.json:504-523,2230-2343`、`method_config.py:77-108`、`financial_ledger.py:83-114,193-218,240-257`。

## 3. 两案数据完整性及时间排序能力

| 观察项 | 工商业屋顶 | 集中式地面 | 数据性质／限制 |
|---|---|---|---|
| Phase 2 原子数、3D 年度期数 | 98 / 26 | 89 / 26 | 已封存合成输入/结果，非银行流水 |
| 期初现金与最低储备 | `0 / 0 CNY` | `0 / 0 CNY` | D2 `SYNTHETIC/ASSUMED`，不是经核验的非受限账户余额/无冻结证明 |
| 出资／分配 | 无实际出资/实分/退出；分配比例 25 期均 1 | 同左 | 比例不能变成股东已收到的款，也不能假定所有历史结余留存 |
| 贷款与现金预测 | 原债务明细数组为空；合成 CAPEX 比例提款；年度收/付比例 | 同左 | 未提供实际到账/到期时刻；应收与债务额度不能用作资金存量 |
| 设备更换付款假设 | 2037-06-01、2040-06-01，分别 190,000/720,000 CNY | 同左 | 投资行 `UNVERIFIED`、有合成来源、只有日期；不重算覆盖 |
| 其他方法 | `YEAR_END`，`ACT_365F`；项目/股东折现、IRR/盈亏价搜索域、CFADS 方法已有值 | 同左 | D2 合成配置完整性≠实际流水/资金充足证明 |
| 法人、账户、限制、同日顺序 | 未提供 | 未提供 | 用 `null/缺失` 表示，不默认无事件/无限制 |

地面案例 `project.ownership_mode` 缺项，屋顶虽填 `owner_invested` 仍不构成某具体法人或账户身份。两份 `result.sha256` 分别与 `result.json.result_hash` 相同；原输入哈希、D2 方法哈希和结果哈希及原文件字节 SHA-256 分别记录在机器证据，**原字节 SHA-256 与 canonical 结果哈希不混用**。旧两轮资金审计的结论仅作背景，未用它们的年累计数倒推余额。[`reports/solar-pv/phase3d-repaired-cases/{industrial_rooftop,utility_scale_ground}/input.json,methods.json,result.json,result.sha256`; `reports/solar-pv/phase3e-funding-coverage-recheck.md:59-72`]

可表达的精度分层：投资/贷款日 `format: date`；项目估值日亦为 `date`；`site.timezone` 有站址字符串，但不是资金事件的强制时区；D2 的 `DATED` 是折现口径选择而不是逐笔事件/同日排序。Phase 3D `_capex` 保留关联并把日期归入年度金额；`_debt` 把贷款计划日期归年度；所得税、OPEX、收入用逐年比例生成年度行。结果证据 `financial-ledger.annual` 是 26 期年度记录，`phase3e_cashflow=None`、`deferred-financial-domains` 中现金流/NPV/IRR 未实现；无银行账户、事件序号、付款前后余额。**即便把 D2 改选 `DATED`，也不能合法默认“同日收入都先到账”。**[`financial_ledger.py:44-52,83-114,159-169,193-218,240-257`; `method_config.py:44-46`; `result.json` 的 `evidence`]

## 4. 输入→结果集成链与缺口归类

| 环节 | 实际入口/约束 | 对所需资金事实的结论 |
|---|---|---|
| 原始 469 字段 | `03-input-fields.json`＋`project-input.schema.json` 的 `values.additionalProperties=false`，原子信封类型/单位/状态/来源；`capex.items.payment_date` 与 `finance.debt_schedule.date` 限制为 `date` | 可以输入有来源的更换付款日、金额及贷款计划；不能借文本或未知额外键输入完整账户/逐笔事件 |
| Phase 2 规范化与快照 | `IntakeSession.export()` 的 `normalized_inputs`、`provenance_records`、`source_snapshot`、`input_hash`；`validate_export()` 由项目和来源记录**重新导出并逐字比较** | 已有字段/来源可传递、不可偷换值；原本不存在的资金事件不会在规范化中生成 |
| D2 方法 | `method_schema()` 注册参数的值、类型、单位、来源/状态；`parameters.additionalProperties=false`、无数值默认；`MethodConfig.from_dict` 校验 | 仅期初金额标量、年度比例、最低现金储备和时间选择；没有股东逐笔出资、账户受限或同日先后规则 |
| 复合输入身份 | `calculation_identity()` 复验 Phase 2，`source_snapshot` 组合 `phase2`、`methods`、`formula_definition`，复合 `input_hash` 另含方法哈希与数据集 | **已登记的**付款日期与 D2 标量确实入哈希，不能把未获准字段直接附加到结果来假装完整输入 |
| Phase 3D 年度账簿 | `calculate_financial_ledger()` 读取投资日期/金额并对年应付付现、年度融资税款收支进行计算；继承 Phase 3C 身份 | 消费部分已存在日期及年度预测；**没有消费** `cash.opening_cash`、`equity.distribution_fractions`、`equity.minimum_cash_reserve` 来计算现金余额/实际分配；这与“案例缺数据”是独立的消费缺口，且 3D 本身不是 3E |
| Phase 3E 与结果 | 冻结 `F-CASH-FUNDING-BALANCE`/`F-DATED-NPV` 等仅有公式域；现行 `result_contract.py` 会对已计算结果检查哈希、定义版本、来源及引用，`result_hash` 排除 `run_id/created_at/artifact_manifest` | 目前没有 Phase 3E 生产现金流及事件消费接口。结果 Schema 的 `evidence`/`details` 可存对象，**不等于获批的资金事件输入 Schema 或排序算法**；不能凭未实现路径报告已计算瞬时余额 |

证据位置：`intake.py:282-295`、`provenance.py:172-180`、`input_contract.py:31-76,80-132`、`method_config.py:139-161,180-185`、`financial_ledger.py:193-265`、`result_contract.py:18-20,62-64,87-149`。现行 `result.schema.json` 是 `calculation-result.schema.json`，不是另一个已存在的现金事件结果 Schema。

**三类问题分别成立而不能合并为“缺字段”：**

1. **DATA_MISSING**：既有字段允许提交有来源的 CAPEX 日期/金额、债务合同计划、币种、D2 期初现金*数字*与年度预测规则；两个案例缺银行核验的初始资金证据、实际逐笔收付、股东/限制合同。可在现有入口补充**它们本来能合法表达的事实**，并重建对应输入/方法/结果身份，但不能补写未知值或把所有缺口塞入这些标量。
2. **执行链消费缺口**：已有 D2 `cash.opening_cash`、`equity.distribution_fractions`、`equity.minimum_cash_reserve` 随配置入哈希，但 Phase 3D 没有使用它们计算项目非受限现金或分配；Phase 3E 现金流/余额尚未实现。只在**已有字段足以表达的范围**，经用户另行确认属于冻结计划必要实施/缺陷修复，最小位置是既定的 Phase 3E 现金流消费者和必要的 3D→3E 映射；不能在本轮改代码，也不能用这些标量代替缺失事件。
3. **真正契约缺口**：现有原子字段及 D2 Schema 不支持带具体法律主体、账户、精确时点与稳定排序的全类收付事件；未支持实际股东出资/分红与解除限制的受控事实。冻结公式域虽然声明年金额与非受限余额，不是可校验的数据提交接口。此缺口**不能仅通过再补两个案例数据解决**。如果专项资金门禁必须证明确切付款瞬间的余额，须先提交兼容性设计供用户**单独批准**；这不是本报告对 469 字段、D2 Schema 或金融业务功能的擅自扩展。

## 5. 最小必要处理范围及对原冻结阶段的影响（只分析，不实施）

- **原契约内可做但本轮不做**：取得可核对来源的原投资行付款日期/金额/币种/资产关联、原贷款合同日期/计划、明确口径的年度合成收付比例和 D2 期初**金额假设**；按既有 Phase 2 导出/D2 快照的版本与哈希机制处理；继续只用已批准的折现/搜索/CFADS 配置。能说明年度预测账簿及条件性项目经济指标的输入基础，但不得把银行未证明的数据宣称为真实流动性或股东实际回款。数据可得性与引擎消费分别验收。[`19-phase3-approved-implementation-contract.md:7-9,40-46`; `phase3d-repair-and-acceptance.md:35-39`]
- **必须另批而本轮不改**：若用户坚持付款**瞬间**可支配资金门禁，需要在已有 Phase 2/D2/3D→3E 体系选择**最小兼容入口**表达期初项目非受限余额的实体/账户/时点与证明、带来源与计划/实际状态的收付（含股东投入、分配、税/债、投资）、限制及解限、同日确定性顺序；定义校验/拒绝不完整事件与排序不确定行为，并让 Phase 3E 消费且纳入复合输入/快照/结果哈希。此处只是所需信息的**差异方向**，不是新增字段清单、现金管理新业务或融资方案。拟改原目录还是批准独立版本化配置，应由用户选择，不能以“D2 曾批准”推定具体事件 Schema 也已获批。[`18-phase3-preimplementation-review.md:42-69`; `19-phase3-approved-implementation-contract.md:5-9,40-46`]
- 兼容/迁移影响：若扩原 469 目录及 Phase 2 项目 Schema，须另行升受控输入版本、保留旧导出/基线的校验与明确迁移/不支持语义，不能默默改变旧 `input_hash`；若选择独立事件契约，须版本化并纳入原 Phase 2 摘要＋D2/定义身份的组合哈希与来源，旧项目缺记录须保持 `BLOCKED`/不可证明，不得生成 0 值或宣称已有哈希涵盖新事实。新旧结果不可沿用旧 `result_hash`，须在批准后重新生成并审计。是否需要实际数据迁移**取决于获批设计与旧项目是否有合规原始记录**，本轮没有资料可确认迁移规模。[`input_contract.py:70-76,118-132`; `result_contract.py:62-64,141-149`]
- **不修复时**：3D 年度 CAPEX/OPEX/债务/应收/税额账簿可以维持原有已验收边界；项目现金流、NPV 等**年度数学形式**的潜在可计算性与付款时流动性证明分开，不能在未实施 3E 前报数值 PASS。股东实缴/分配的实际 IRR、项目瞬时非受限现金、四笔付款覆盖及依赖它们的原冻结整体准入保持 `BLOCKED`。无需发明一个确定资金短缺或把缺失当作零。[`05-formulas.json` 中 `F-PROJECT-CASH-FLOW`/`F-EQUITY-INVESTOR-CASH-FLOW`/`F-CASH-FUNDING-BALANCE`; `17-phase3-implementation-plan.md:85-95`]

## 6. 工作区保护及停止

起点六文件 SHA-256、288 文件原基线复核及两案例原文件 SHA-256 均在同名机器证据中。288 个保护文件：**286 匹配原基线，2 个仅为原有 `reports/validate.json`、`reports/validate.md` 偏差；新增保护差异 0**。六文件（`packages/skills/wangbin-receivable-analyzer/SKILL.md`、同目录 `manifest.json`、`products/catalog.json`、`reports/workbuddy-upload-list.md`、`reports/validate.json`、`reports/validate.md`）均已有未提交差异，本轮不恢复、不改写、不暂存。起止 SHA-256 与最终 Git 检查记录于机器证据。仅新建本报告和对应 JSON；不改冻结定义/生产代码/测试/两案/旧报告，不生成现金或贷款假设，不执行资金覆盖重算、Phase 3E 计算、测试或自动生成器，不 commit/push/上传/部署/发布。若历史材料需提及任何凭据，一律 `[REDACTED]`。审查在此停止，等待用户单独审批。
