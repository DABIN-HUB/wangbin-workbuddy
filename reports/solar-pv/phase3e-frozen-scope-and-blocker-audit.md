# Phase 3E 原冻结范围与阻断合理性专项审计

**结论 A（范围审计，而非开发放行）**：两案四笔设备更换付款瞬时资金覆盖继续为 `INDETERMINATE`，但未找到原始需求/Phase 1 冻结/正式批准 D1–D3 要求「逐笔银行账户、同日事件排序、付款瞬间可用现金覆盖；否则全部 Phase 3E 停止」的正式门禁。将该专项证明提升为所有项目年度财务评价的前置门禁，属于**部分范围漂移**。这不取消冻结的 **`F-CASH-FUNDING-BALANCE` 期间主体非受限现金平衡、`F-DATED-NPV` 完整有日期现金事件、股东实缴与合法分配/退出、CFADS 协议边界**；这些仍是独立的原需求阻断/条件，不得用默认零或全额分红抹平。`Phase 3E = BLOCKED`、21 条未实现及正式发布门禁均保持原状，等待用户审批分层处理。参见 `00-original-user-baseline.md:121-127`、`05-formulas.json` 各式、`17-phase3-implementation-plan.md:85-95`、`19-phase3-approved-implementation-contract.md:5-10`。

**身份与方式**：`main` / `6823f740b9d34647a13c5cdc874d90a23e0bcd7e`；启动及终检暂存区均空；未运行测试、财务计算或资金余额重算；只增加本报告和同名 JSON。两案例仅 `SYNTHETIC`，任何「可算」均指满足所列冻结输入和计量边界后的数学/条件情景，不是已经算出或验收通过，更不是银行资金充足或真实项目可行性。

## 1. 原文、冻结版本、来源等级

- 原用户总任务 `docs/solar-pv/00-original-user-baseline.md:60,70-80,107-127,189-199`：年度建设/运营、资本开支/更新/税费/营运资金、项目与股东两流；年末 NPV、项目/资本金 IRR、LCOE、DSCR 等。§6 第121行明示「年现金流」，第122行 NPV 为 `y=0…N` 年末时点；第126行债务协议 CFADS。没有描述银行账户级流水、同日付款先后或对全体 Phase 3E 的「瞬时覆盖不明即停」规则。原文第19行允许缺证据时明确 UNKNOWN 和有限草稿，不能伪称完整论证。
- Phase 1 身份 `SOLAR-PV-1.0.0`，2026-10-28 冻结；`00-baseline-manifest.json:2-26` 的原文 SHA-256 与当前原文件字节一致。`03-input-fields.json` 469 原字段，`05-formulas.json` 77 原主表＋`05-formula-extensions.json` 12 共 89，`05-field-bindings.json` 281 域；实际 `Catalog()` 有效定义 `solar-pv-formula-definitions/1.0.1`、定义身份 SHA-256 `617a2e9d314c095bd2ec893939c930a2323be6fd7805da12bf6d6fdd70274808`，仅批准元数据勘误，不改公式数学意图（`19-phase3-approved-implementation-contract.md:14-22`，`definition-errata.json` 的 E03/E05）。本阶段 21 ID 按 `phase3e-review-and-acceptance.md:8-40` 与现存公式对照均存在。
- 可追溯原需求 `08-requirement-traceability.csv:85-91`：`R-S06-L121..127` 均为 Phase 3 原条款；`R-CH16-02..08`（同文件:225-231；`02-report-outline-18-chapters.md:180-186`）是 **Phase 5 报告章节**，只辅助解释口径，不应冒充新增 Phase 3E 门禁。`10-four-file-acceptance.md:96-98` 也是交付物/资金平衡展示，不是付款日银行流水核验条款。
- 后续 `16-phase3-user-task.md:509-557` 明示年度现金流及现金流时间点；`17-phase3-implementation-plan.md:85-95` 列本阶段年度和 dated NPV、股东收付、CFADS。后续开发提示的「实际现金日期」需对应 dated 公式，不能扩张解释为所有项目银行付款日流动性准入。
- `18-phase3-preimplementation-review.md:42-69` 是 D2 的**申请/建议**（包括初始余额、预测收付、债务事件顺序与合成场景）。`19-phase3-approved-implementation-contract.md:5-10,40-46` 才是正式批准：版本化受控方法/显式假设和输入/来源/hash身份，不填零、不把应付当实付、不把合成当真实。实际 D2 `method_config.py:77-118` 及 Schema 包含 `cash.opening_cash`、`equity.distribution_fractions`、`equity.minimum_cash_reserve`、`cfads.method`、折现/IRR/价格域等；**没有批准完整逐笔银行账户系统或付款瞬时门禁**。批准的 D2 配置能力不能冒充核验过的外部真实现金事实。
- `phase3d-review-and-acceptance.md:21-25` 已将 `F-CASH-FUNDING-BALANCE` 明确留给 3E。`phase3e-review-and-acceptance.md:44-62` 初始 B1/B2/B3 为上游真实缺陷，随后 `phase3d-repair-and-acceptance.md:1-39` 定点修复；其第39行以及后续资金覆盖、复核、可表达性专项报告（各自报告第1节/结论）新增更严格的付款瞬时审计准入。**这些晚期报告能证明审计结论/表达能力不足，不能倒推冻结验收标准。**

## 2. 三类计算/证明边界与五问直接答复

1. **逐笔资金覆盖是不是原冻结要求？ NO（所问三件事与全局停机的组合）**。原冻结确实有 **期间主体非受限余额平衡** `F-CASH-FUNDING-BALANCE: CLOSE_y=OPEN_y+CF_E,avail,y+EQ_y−DIV_y`；也有 **逐事件带日期折现** `F-DATED-NPV: Σ(k∈C)`。两者分别要求期初/期末主体现金或完整日期现金事件，并不推出银行账户标识、受限账户全量管理、同日时分秒顺序、某更换付款瞬时可支配额核验，也未发现无法证明则所有 3E 停工的正式条款。`18` 号 D2 申请中的事件顺序针对债务方法，不能扩大成所有收支银行流水规则。逐笔用于 dated NPV 是真的、付款覆盖审计中的「逐笔银行资金流水」是另一个要求。
2. **不建逐笔银行模型能否计算项目流/NPV/IRR/LCOE？ 按公式可条件实现**。项目期间数据与 3C 交付电量有基础，项目流 `F-PROJECT-CASH-FLOW`、税前流、`F-LIFECYCLE-COST` 可依正确归属、税/终期回收/避免双计构造明确合成年度流；`F-NPV`、项目 `F-IRR-PROJECT`、`F-LCOE`、静/动态回收期是派生条件式。价格搜索/最差年亦需明确搜索项/年份集合与完整链。没有一个已经运行的 3E 数值。`F-DATED-NPV` 例外，原式本来需要完整有日期事件；不需要日内账户资金可用排序。详见第3节逐式矩阵。
3. **股东流、CFADS、DSCR 的独立阻断？ YES/有条件**。股东 `F-EQUITY-INVESTOR-CASH-FLOW`、资本金IRR及 `F-CASH-FUNDING-BALANCE` 仍缺实际/可合法支付的逐期 EQ、DIV、EXIT 与可核验的主体期初非受限金额及期间滚动；0 元合成 opening cash 和全额分配比例不证明实际收付或足额分配。`F-CFADS`/`F-DSCR` 两案例已有**合成方法**与年度应还 DS，可作显式情景计算；真实/合同口径的强制更新、储备和调整尚未有合同确认，不能称合同合规或不加说明的真实 DSCR。`F-DATED-NPV` 的日期集合、`F-INVESTMENT-HURDLE-GAP` 的用户目标是另外独立缺口。
4. **整体 BLOCKED 纯属原冻结？ NO**。原启动的 3D B1–B3 是实际专业缺陷、后续授权限定修复；原 B4/B5 的部分方法/率/求根域已由合成配置补齐，股东事实和协议验证仍独立存在。四笔瞬时覆盖 `INDETERMINATE` 保留，但把其未证实+银行事件 Schema 不足当作其它所有年度公式的先决条件，属于后加门槛。3E 仍因未实现 21 式、原冻结中的股东/期间余额/dated/协议等未完成而不能整体 PASS。
5. **最小恢复范围（仅建议待审批）**：明确**将付款瞬时覆盖审计从独立可算的年度财务指标准入中拆出**，保留其 `INDETERMINATE` 和风险记录；在现有 469/89/281/D2 下接已封存 3C/3D 年账、严格按原式处理项目和成本/税/终期口径，优先做合成年度项目公式与独立参考，不默认假现金/股东入账；并列独立阻断 `F-DATED-NPV` 完整有日期事件映射、股东实际或经批准的计划收付与期间非受限平衡、合同 CFADS/DSCR 与客户目标差距。无法在现有契约合法表达的**原式必需事实**必须单独报批准/待核实，不暗改 Schema、不降低验收、不自动解除 BLOCKED。本轮没有执行此建议。

### 审查结果的细微边界

- 年度增量项目经济利益 `B_op` 可包含有权享有的自用购电避免支出，**该项不是销售回款或主体银行现金存量**；项目税/融资后税必须分别取 3D 列，折旧不作为现金 OPEX 重扣。年度现金流负值可以数学上参与 NPV/IRR，并不因此证明某一天已经完成付款。
- `F-CASH-FUNDING-BALANCE` **不是**可删去的额外审计公式：它明说 `CLOSE_y`/`OPEN_y` 是项目主体期末/期初**非受限现金余额**，且资金缺口不能藏在负现金里；缺 EQ/DIV 及期间现金不可给有效余额。不过其数学下标 `y` 是财务期而非同日银行交易序号（`05-formulas.json` 该式定义/边界）。
- `F-DATED-NPV` 要 `C` 为完整现金事件集合及每个 `τ_k` 年分数，3D 年度行加两笔已知更换日期不构成完整事件集合。不能简单把 dated 当年末 NPV 的同义词；没有足够事件时返回有原因的未定状态，独立年度 NPV 不随之停工。

## 3. 21 条冻结公式逐项依赖矩阵

矩阵状态：`条件` 表示**尚未计算/验收**但原式可在合成年度契约下满足所列条件；`缺股东`、`缺日期`、`缺期间现金`、`缺目标` 均是局部真阻断；`合同情景` 不等于真实合同认可。所有项目/股东分支分别标注。`期`=现金收付期间/日期要求；`逐`=完整逐笔现金事件；`主余额`=主体**期间**非受限余额；`银行`=银行账户级余额；`瞬`=付款瞬间覆盖证明。`Y` 表示要求，`N` 不要求。逐式完整变量、下标及来源紧跟在表后；JSON 保存原始每符号定义/集合/边界/281绑定。

| 需求 | ID / 冻结名 | 数学式（05原式） | 期/逐/主余额/银行/瞬 | 两案数学输入状态 |
|---|---|---|---|---|
| R-S06-L121 | `F-PROJECT-CASH-FLOW` 项目投资无杠杆净现金流 | `CF_P,y = B_op,y − O_y − T_P,y − K_P,y − ΔW_P,y + S_P,y` | Y/N/N/N/N | `CONDITIONAL_ANNUAL` |
| R-S06-L121 | `F-PROJECT-PRETAX-CASH-FLOW` 项目所得税前现金流 | `CF_P,pre,y = CF_P,y + T_inc,cash,P,y` | Y/N/N/N/N | `DEPENDENT_PROJECT` |
| R-S06-L121 | `F-EQUITY-AVAILABLE-CASH-FLOW` 股权可分配增量现金流 | `CF_E,avail,y = B_op,y − O_y − T_E,y − K_E,y − ΔW_E,y + S_E,y + DD_y − PRN_y − INT_y − FF_y` | Y/N/N/N/N | `CONDITIONAL_ANNUAL` |
| R-S06-L121 | `F-EQUITY-INVESTOR-CASH-FLOW` 股东实际投入分配现金流 | `CF_E,y = DIV_y + EXIT_y − EQ_y` | Y/N/N/N/N | `BLOCKED_EQUITY_FACTS` |
| R-S06-L121 | `F-CASH-FUNDING-BALANCE` 融资与现金账户平衡 | `CLOSE_y = OPEN_y + CF_E,avail,y + EQ_y − DIV_y` | Y/N/Y/N/N | `BLOCKED_PERIOD_ENTITY_BALANCE` |
| R-S06-L122 | `F-NPV` 同口径净现值 | `NPV_b = Σ(y=0…N) CF_b,y / (1 + r_b)^y` | Y/N/N/N/N | `PROJECT_CONDITIONAL_EQUITY_BLOCKED` |
| R-S06-L122 | `F-DATED-NPV` 非整年时点净现值 | `NPV_b = Σ(k∈C) CF_b,k / (1 + r_b)^τ_k` | Y/Y/N/N/N | `BLOCKED_DATED_EVENTS` |
| R-S06-L122 | `F-NOMINAL-REAL-RATE` 名义与实际折现率桥 | `r_nom = (1 + r_real) × (1 + π) − 1` | N/N/N/N/N | `CONDITIONAL_RATE_CONVERSION` |
| R-S06-L123 | `F-IRR-PROJECT` 项目投资内部收益率根集 | `R_P = {r∈D : Σ(y=0…N) CF_P,y/(1+r)^y = 0}` | Y/N/N/N/N | `DEPENDENT_PROJECT` |
| R-S06-L123 | `F-IRR-EQUITY` 资本金内部收益率根集 | `R_E = {r∈D : Σ(y=0…N) CF_E,y/(1+r)^y = 0}` | Y/N/N/N/N | `BLOCKED_EQUITY_FACTS` |
| R-S06-L124 | `F-CUMULATIVE-CASH-FLOW` 静态累计现金流 | `A_b,n = Σ(y=0…n) CF_b,y` | Y/N/N/N/N | `PROJECT_CONDITIONAL_EQUITY_BLOCKED` |
| R-S06-L124 | `F-STATIC-PAYBACK` 静态首次回收期 | `PB_static,b = n − 1 + (−A_b,n−1) / CF_b,n` | Y/N/N/N/N | `PROJECT_CONDITIONAL_EQUITY_BLOCKED` |
| R-S06-L124 | `F-DISCOUNTED-CUMULATIVE-CASH` 动态累计现金流 | `A_disc,b,n = Σ(y=0…n) CF_b,y / (1+r_b)^y` | Y/N/N/N/N | `PROJECT_CONDITIONAL_EQUITY_BLOCKED` |
| R-S06-L124 | `F-DYNAMIC-PAYBACK` 动态首次回收期 | `PB_dynamic,b = n − 1 + (−A_disc,b,n−1)/(CF_b,n/(1+r_b)^n)` | Y/N/N/N/N | `PROJECT_CONDITIONAL_EQUITY_BLOCKED` |
| R-S06-L125 | `F-LIFECYCLE-COST` 无杠杆生命周期净成本 | `Cost_P,y = K_P,y + O_y + T_cost,P,y + ΔW_P,y − S_P,y − SUB_P,y` | Y/N/N/N/N | `CONDITIONAL_ANNUAL` |
| R-S06-L125 | `F-LCOE` 平准化度电成本 | `LCOE = Σ(y=0…N) Cost_P,y/(1+r_L)^y / Σ(y=0…N) E_delivered,y/(1+r_L)^y` | Y/N/N/N/N | `DEPENDENT_PROJECT` |
| R-S06-L126 | `F-CFADS` 可用于偿债的现金流 | `CFADS_y = B_op,y − O_y − T_E,y − ΔW_ds,y − K_mand,y + A_ds,y` | Y/N/N/N/N | `CONDITIONAL_PROTOCOL` |
| R-S06-L126 | `F-DSCR` 偿债备付率 | `DSCR_y = CFADS_y / DS_y` | Y/N/N/N/N | `CONDITIONAL_PROTOCOL` |
| R-S06-L127 | `F-BREAK-EVEN-PRICE` 净现值为零的盈亏平衡电价 | `P_star = {p∈P : NPV_b(CF_b(p), r_b) = 0}` | Y/N/N/N/N | `DEPENDENT_FULL_CHAIN` |
| R-S06-L127 | `F-WORST-CASH-YEAR` 最差现金流年份集合 | `Y_worst,b = argmin(y∈Y) CF_b,y` | Y/N/N/N/N | `PROJECT_CONDITIONAL_EQUITY_BLOCKED` |
| R-S06-L127 | `F-INVESTMENT-HURDLE-GAP` 投资门槛差距 | `G_M = M_calc − M_target` | N/N/N/N/N | `BLOCKED_TARGETS_FOR_CASES` |

**每式完整变量、下标、3C/3D 血缘、方法与缺数处理（原式引冻结主表，已批准的 E03 单位和 E05 下标以有效定义为准，不新增公式）：**

### `F-PROJECT-CASH-FLOW` — 项目投资无杠杆净现金流
- 原式：`CF_P,y = B_op,y − O_y − T_P,y − K_P,y − ΔW_P,y + S_P,y`。来源 `docs/solar-pv/05-formulas.json:5209`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L121，原文见 `00-original-user-baseline.md:121`（第121–127行）。
- 全部变量（原条目中文释义）：`CF_P,y`＝项目投资视角税后无杠杆增量净现金流；`B_op,y`＝增量经营现金利益：到账经营收入加确认的自用避免支出，不含融资；`O_y`＝现金经营支出，不含折旧、已在自用避免支出扣除项和单列税；`T_P,y`＝无杠杆现金税负：项目所得税、其他税费和适配税价桥后的增值税净缴退；`K_P,y`＝当年工程资本付款及资本化更新替换，不含融资资金流和资本化借款利息；`ΔW_P,y`＝经营营运资金净增加，不含已按现金收入/支出桥扣过部分和单列税务资产负债；`S_P,y`＝期末处置净现金和未在 ΔW 中回收的残余资金，税务影响进 T。
- 下标/范围（原条目）：`P`＝无杠杆项目；y 为财务时点索引，0 为基期，含所有建设/运营/退出期；op=经营，Δ=期末减期初，W=营运资金。；`逐个下标词素`＝P=项目无杠杆口径；y=财务或运营年度索引，必须按本条时间定义区分；op=运营经营利益。
- 计量边界：建设期、运营期、替换和退出全时点；绝不含贷款提款、本息、融资费或股东出入资。；原式输入域：`finance.project_operating_cash_benefit`, `opex.cash_annual`, `tax.project_cash_total`, `capex.unlevered_cash_annual`, `working_capital.project_net_change`, `finance.project_terminal_cash`。3C：年度经营利益（屋顶自用单列；地面外售）；3D：项目税/建设及更换付现/OPEX/营运资金/处置；必须明确的既有方法/边界：cash.method、time.cashflow_timing、项目税及残值口径。
- 分类 `CONDITIONAL_ANNUAL`：可按期间形成项目情景；期末残值必须区分账面残值与实际处置现金，屋顶自用节省不得冒充银行到账。 不因缺付款瞬时资金证明而停止；本行其它冻结条件仍须满足。

### `F-PROJECT-PRETAX-CASH-FLOW` — 项目所得税前现金流
- 原式：`CF_P,pre,y = CF_P,y + T_inc,cash,P,y`。来源 `docs/solar-pv/05-formulas.json:5348`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L121，原文见 `00-original-user-baseline.md:121`（第121–127行）。
- 全部变量（原条目中文释义）：`CF_P,pre,y`＝仅加回项目所得税的税前无杠杆现金流；`CF_P,y`＝所得税后无杠杆项目现金流；`T_inc,cash,P,y`＝同一项目口径实际/模拟所得税现金缴纳净额。
- 下标/范围（原条目）：`P`＝项目；pre=所得税前；inc,cash=现金所得税；y=财务时点。；`逐个下标词素`＝P=项目无杠杆口径；pre=初始衰减前或所得税前，按完整符号区分；y=财务或运营年度索引，必须按本条时间定义区分；inc=所得税而非其他现金税费；cash=实际或预测现金收付而非权责计提。
- 计量边界：所得税前不等于不含增值税/全部免税；保留合法其他现金税费和税价桥。；原式输入域：`finance.project_cash_flow`, `tax.project_income_cash_paid`。3C：同上；3D：项目所得税实付与项目税后流；必须明确的既有方法/边界：项目所得税口径。
- 分类 `DEPENDENT_PROJECT`：在正确项目税后流和同口径所得税实付具备后可算。 不因缺付款瞬时资金证明而停止；本行其它冻结条件仍须满足。

### `F-EQUITY-AVAILABLE-CASH-FLOW` — 股权可分配增量现金流
- 原式：`CF_E,avail,y = B_op,y − O_y − T_E,y − K_E,y − ΔW_E,y + S_E,y + DD_y − PRN_y − INT_y − FF_y`。来源 `docs/solar-pv/05-formulas.json:5450`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L121，原文见 `00-original-user-baseline.md:121`（第121–127行）。
- 全部变量（原条目中文释义）：`CF_E,avail,y`＝融资后可供股权的现金余缺，负值表示需股东追加资金；`B_op,y`＝经营现金利益，不含融资；`O_y`＝现金运营支出；`T_E,y`＝考虑合法利息税盾的实际主体现金税总额，税价桥口径与项目流一致；`K_E,y`＝实际资产付款及更换，融资利息和融资费用已单列 INT/FF 因此不在此扣；`ΔW_E,y`＝未在其他现金项扣过的经营营运资金和约定受限储备净增；`S_E,y`＝处置及未在 ΔW 中回收的终期现金；`DD_y`＝债务现金提款，非资本化利息记账增加；`PRN_y`＝本期实际付现归还本金；`INT_y`＝本期实际付现债务利息，含建设期支付部分；`FF_y`＝付现融资费用，未在资产付款/利息中重复计入。
- 下标/范围（原条目）：`E`＝股权口径；avail=可分配余缺；DD=提款，PRN=本金，INT=利息，FF=融资费；y=完整财务时点。；`逐个下标词素`＝E=股权/融资主体口径，ε_E 则标能量残差；avail=可供股权分配的现金余缺；y=财务或运营年度索引，必须按本条时间定义区分；op=运营经营利益。
- 计量边界：明确包含融资并使用融资后税负；项目流不能原样加融资后忽略利息税盾。；原式输入域：`finance.project_operating_cash_benefit`, `opex.cash_annual`, `tax.equity_cash_total`, `capex.equity_asset_cash_annual`, `working_capital.equity_net_change`, `finance.equity_terminal_cash`, `debt.cash_drawdown`, `debt.principal_paid`, `debt.interest_paid`, `debt.finance_fees_paid`。3C：年度经营利益；3D：融资后税、CAPEX/OPEX、提款及实付本息/费、营运/储备/终期；必须明确的既有方法/边界：现金桥、储备/分配约束、债务付现。
- 分类 `CONDITIONAL_ANNUAL`：合成期间余缺可研究；实体受限储备/终期收益须明确，不能把本项自动视作实际分红。 不因缺付款瞬时资金证明而停止；本行其它冻结条件仍须满足。

### `F-EQUITY-INVESTOR-CASH-FLOW` — 股东实际投入分配现金流
- 原式：`CF_E,y = DIV_y + EXIT_y − EQ_y`。来源 `docs/solar-pv/05-formulas.json:5618`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L121，原文见 `00-original-user-baseline.md:121`（第121–127行）。
- 全部变量（原条目中文释义）：`CF_E,y`＝投资者视角净现金流，用于实际资本金 IRR；`DIV_y`＝当期实际或计划可合法支付的股东分配；`EXIT_y`＝未含在分配中的投资者退出或终期清算回款；`EQ_y`＝本期股东实际出资及追加资金。
- 下标/范围（原条目）：`E`＝股东投资者；DIV=分配，EXIT=退出，EQ=实缴出资；y=财务时点。；`逐个下标词素`＝E=股权/融资主体口径，ε_E 则标能量残差；y=财务或运营年度索引，必须按本条时间定义区分。
- 计量边界：分红限制、储备账户、资金滞留需反映实际收付；CF_E,avail 只有立即全额弥补/分配且无滞留时才与此相等。；原式输入域：`equity.distributions`, `equity.exit_receipts`, `equity.contributions`。3C：无直接需要；依赖股东现金；3D：3D无实际股东出资、分配、退出逐期账；必须明确的既有方法/边界：equity.distribution_fractions与minimum_cash_reserve仅为策略。
- 分类 `BLOCKED_EQUITY_FACTS`：出资/合法可付分配/退出需有效期间事实；比例为1及0储备不等于已向股东支付。 原公式无法产生完整有效数值，必须带原因保留未定。

### `F-CASH-FUNDING-BALANCE` — 融资与现金账户平衡
- 原式：`CLOSE_y = OPEN_y + CF_E,avail,y + EQ_y − DIV_y`。来源 `docs/solar-pv/05-formulas.json:5729`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L121，原文见 `00-original-user-baseline.md:121`（第121–127行）。
- 全部变量（原条目中文释义）：`CLOSE_y`＝项目主体期末非受限现金余额；`OPEN_y`＝项目主体期初非受限现金余额；`CF_E,avail,y`＝已计经营、税、资本支出、提款、本息及融资费用的股权可用余缺；`EQ_y`＝股东实际出资及追加；`DIV_y`＝主体支付的股东分配，终期清算支付也应归入对应账户用途。
- 下标/范围（原条目）：`y`＝所有建设/运营财务时点；OPEN/CLOSE=期初/末现金；E,avail=可供股权余缺。；`逐个下标词素`＝y=财务或运营年度索引，必须按本条时间定义区分；E=股权/融资主体口径，ε_E 则标能量残差；avail=可供股权分配的现金余缺。
- 计量边界：本条验证主体现金账户；独立第三方支付的股权转让 EXIT 不经过主体账户；终期资产处置已在 CF_E,avail 中。；原式输入域：`checks.cash_opening`, `finance.equity_available_cash_flow`, `equity.contributions`, `equity.distributions`。3C：无直接需要；以上融资后可用流；3D：3D无主体非受限期初/末现金滚动、股东实际往来；必须明确的既有方法/边界：cash.opening_cash、equity.minimum_cash_reserve。
- 分类 `BLOCKED_PERIOD_ENTITY_BALANCE`：合成期初现金0已配置，但不是核验非受限现金；需要期间OPEN、EQ、DIV及非负/缺口状态，不要求付款瞬时银行账户排序。 原公式无法产生完整有效数值，必须带原因保留未定。

### `F-NPV` — 同口径净现值
- 原式：`NPV_b = Σ(y=0…N) CF_b,y / (1 + r_b)^y`。来源 `docs/solar-pv/05-formulas.json:6243`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L122，原文见 `00-original-user-baseline.md:122`（第121–127行）。
- 全部变量（原条目中文释义）：`NPV_b`＝口径 b 的年末现金流净现值；`CF_b,y`＝已选项目税前/税后或股东实际现金流，口径不混合；`r_b`＝与口径 b 匹配的每年折现率；`b`＝项目税前、项目税后、股东实际收付中的一个完整口径标签；`y`＝从基期 0 起的财务年度整数时点；`N`＝最后一个财务年度时点，含建设及终期。
- 下标/范围（原条目）：`Σ y=0…N`＝有限求和含基期与末期；b=唯一口径；y=0 为评价基准日。；`逐个下标词素`＝b=互斥的项目/股权及税前后完整口径索引；y=财务或运营年度索引，必须按本条时间定义区分。
- 计量边界：同币种、同基准日、同税口径和名义/实际价格；多建设年均保留现金流，不把全部投资挤到首运营年。；原式输入域：`finance.selected_cash_flow`, `finance.selected_discount_rate`, `finance.cash_flow_basis`, `time.financial_end_year`。3C：依所选项目/权益流；3D：已选完整期间流；权益分支缺股东收付；必须明确的既有方法/边界：选定折现率及税/价格/年末时点。
- 分类 `PROJECT_CONDITIONAL_EQUITY_BLOCKED`：项目年末NPV依项目流可算；实际股东NPV随股东收付受阻。 不因缺付款瞬时资金证明而停止；本行其它冻结条件仍须满足。

### `F-DATED-NPV` — 非整年时点净现值
- 原式：`NPV_b = Σ(k∈C) CF_b,k / (1 + r_b)^τ_k`。来源 `docs/solar-pv/05-formulas.json:6375`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L122，原文见 `00-original-user-baseline.md:122`（第121–127行）。
- 全部变量（原条目中文释义）：`NPV_b`＝按实际支付时点折现的净现值；`CF_b,k`＝第 k 个实际现金事件的金额；`r_b`＝同口径年化折现率；`τ_k`＝事件日至基准日的合同年分数，可为非整数；`k`＝现金事件索引；`C`＝完整评价现金事件集合，含基期和终期；`b`＝唯一现金流口径。
- 下标/范围（原条目）：`k∈C`＝Σ 遍历所有现金事件，不漏基期；τ_k 为按明确日计数规则计算的无量纲年分数。；`逐个下标词素`＝b=互斥的项目/股权及税前后完整口径索引；k=损失/费用类别或现金事件索引，见本条集合。
- 计量边界：建设跨年、分期出资优先采用；日计数采用的年分数规则须写入方法版本，不默认日历除数。；原式输入域：`finance.dated_cash_flows`, `finance.selected_discount_rate`, `finance.cash_event_year_fraction`, `finance.cash_event_ids`, `finance.cash_flow_basis`。3C：依所选现金事件口径；3D：完整带日期的项目/股权现金事件集合未由3D生成；必须明确的既有方法/边界：time.day_count、共同基准日、选定折现率。
- 分类 `BLOCKED_DATED_EVENTS`：原式按事件k及τk，完整日期事件是真独立必需；没有强制同日银行先后顺序或付款日资金覆盖。 原公式无法产生完整有效数值，必须带原因保留未定。

### `F-NOMINAL-REAL-RATE` — 名义与实际折现率桥
- 原式：`r_nom = (1 + r_real) × (1 + π) − 1`。来源 `docs/solar-pv/05-formulas.json:6514`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L122，原文见 `00-original-user-baseline.md:122`（第121–127行）。
- 全部变量（原条目中文释义）：`r_nom`＝名义年折现率；`r_real`＝不含一般通胀的实际年折现率；`π`＝与币种和评价期对应的一般年通胀率假设。
- 下标/范围（原条目）：`nom`＝名义；real=实际；π 为同年度步长通胀。；`逐个下标词素`＝nom=名义币值/名义折现率；real=实际购买力价格/折现率。
- 计量边界：仅作同一税/风险/币种口径下的通胀转换；不能拿资产特定电价变化替代一般通胀。有效定义 E03 单位为无量纲年度比例 `1`，不是连续时间 `1/年`；原式输入域：`finance.real_discount_rate`, `finance.general_inflation`。3C：无；3D：无；必须明确的既有方法/边界：名义/实际一致的通胀与实率假设。
- 分类 `CONDITIONAL_RATE_CONVERSION`：两案有名义项目折现与通胀假设，未见独立真实率；不用此桥也能按现有一致名义口径算项目NPV。 不因缺付款瞬时资金证明而停止；本行其它冻结条件仍须满足。

### `F-IRR-PROJECT` — 项目投资内部收益率根集
- 原式：`R_P = {r∈D : Σ(y=0…N) CF_P,y/(1+r)^y = 0}`。来源 `docs/solar-pv/05-formulas.json:6617`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L123，原文见 `00-original-user-baseline.md:123`（第121–127行）。
- 全部变量（原条目中文释义）：`R_P`＝项目投资 IRR 的全部可识别实根集合，不是任意单根百分比；`r`＝待求每年收益率；`D`＝事前声明的实数搜索域，必须位于 r>−1；域外根不声称不存在；`CF_P,y`＝同口径项目投资无杠杆现金流，明确税前或税后，不含融资；`y`＝财务年度时点；`N`＝最后评价时点。
- 下标/范围（原条目）：`Σ y=0…N`＝对基期到终期项目流求和；P=无杠杆项目。；`r∈D`＝集合构造：所有使 NPV 为零的域内实率；集合可能为空/单根/多根/连续。；`逐个下标词素`＝P=项目无杠杆口径；y=财务或运营年度索引，必须按本条时间定义区分。
- 计量边界：无债务流；税前与税后分别调用并分别输出，不以同字段覆盖；非整年时点改用同口径 dated-NPV 求根版本。；原式输入域：`finance.irr_search_domain`, `finance.project_irr_cash_flow`, `time.financial_end_year`。3C：项目年度经营利益；3D：完整无杠杆项目现金流；必须明确的既有方法/边界：irr.minimum_rate/maximum_rate/root_tolerance/method/maximum_degree。
- 分类 `DEPENDENT_PROJECT`：项目年度向量及搜索域有情景基础；必须处理无根/多根/未穷尽。 不因缺付款瞬时资金证明而停止；本行其它冻结条件仍须满足。

### `F-IRR-EQUITY` — 资本金内部收益率根集
- 原式：`R_E = {r∈D : Σ(y=0…N) CF_E,y/(1+r)^y = 0}`。来源 `docs/solar-pv/05-formulas.json:6755`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L123，原文见 `00-original-user-baseline.md:123`（第121–127行）。
- 全部变量（原条目中文释义）：`R_E`＝投资者资本金 IRR 实根集合；`r`＝待求年化股权收益率；`D`＝事前声明并记录的 r>−1 实数搜索域；`CF_E,y`＝真实股东出资为负、分配和退出为正的投资者现金流；`y`＝财务时点；`N`＝终期评价时点。
- 下标/范围（原条目）：`Σ y=0…N`＝股东全部真实/计划收付时点；E=股东口径。；`r∈D`＝域内全部满足 NPV=0 的实率构成集合。；`逐个下标词素`＝E=股权/融资主体口径，ε_E 则标能量残差；y=财务或运营年度索引，必须按本条时间定义区分。
- 计量边界：必须计融资及分红限制，不能用项目现金流或单纯会计利润代替；日期不齐改 dated-NPV。；原式输入域：`finance.irr_search_domain`, `finance.equity_investor_cash_flow`, `time.financial_end_year`。3C：股东分配/退出无3C源；3D：股东实缴与合法分配/退出缺失；必须明确的既有方法/边界：同项目IRR有界求根配置。
- 分类 `BLOCKED_EQUITY_FACTS`：股东现金流缺失；不能以股权可用流或利润顶替。 原公式无法产生完整有效数值，必须带原因保留未定。

### `F-CUMULATIVE-CASH-FLOW` — 静态累计现金流
- 原式：`A_b,n = Σ(y=0…n) CF_b,y`。来源 `docs/solar-pv/05-formulas.json:6892`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L124，原文见 `00-original-user-baseline.md:124`（第121–127行）。
- 全部变量（原条目中文释义）：`A_b,n`＝截至时点 n 的未折现累计净现金流；`CF_b,y`＝同一口径各期净现金流；`y`＝自基期起财务年度时点；`n`＝被评估的累计终点，0…N；`b`＝项目/股权及税前后唯一口径。
- 下标/范围（原条目）：`Σ y=0…n`＝含基期至累计终点 n；A 为累计值标签。；`逐个下标词素`＝b=互斥的项目/股权及税前后完整口径索引；n=累计终点或首次回收年度索引；y=财务或运营年度索引，必须按本条时间定义区分。
- 计量边界：从首次纳入评价的建设出资基期起算，不从投产时重置亏损；如使用运营回收期必须另标起点。；原式输入域：`finance.selected_cash_flow`, `time.cumulative_end_year`, `finance.cash_flow_basis`。3C：项目已选流；3D：项目/权益同口径年流；权益分支缺失；必须明确的既有方法/边界：完整评价期及基期。
- 分类 `PROJECT_CONDITIONAL_EQUITY_BLOCKED`：项目期内累计可算；权益累计依真实/获批计划收付。 不因缺付款瞬时资金证明而停止；本行其它冻结条件仍须满足。

### `F-STATIC-PAYBACK` — 静态首次回收期
- 原式：`PB_static,b = n − 1 + (−A_b,n−1) / CF_b,n`。来源 `docs/solar-pv/05-formulas.json:7015`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L124，原文见 `00-original-user-baseline.md:124`（第121–127行）。
- 全部变量（原条目中文释义）：`PB_static,b`＝自评价基期起静态首次回收的年数；`n`＝第一个使累计净流由负转非负的年度终点；`A_b,n−1`＝此前一年末负累计净现金流；`CF_b,n`＝首次回收年度的正净现金流；`b`＝项目/股权唯一口径；`N`＝评价期最后一个财务年度时点，限制首次交叉搜索范围。
- 下标/范围（原条目）：`n`＝在 {1,…,N} 内满足首次负转非负的最小年度索引；static=未折现。；`范围`＝N 是评价末期，查找过程必须涵盖全部现金流，N 见时间字段 time.financial_end_year。；`逐个下标词素`＝static=未折现回收期；b=互斥的项目/股权及税前后完整口径索引；n=累计终点或首次回收年度索引；1=首运营年或扰动后情景 1，具体按完整符号区分；`时间偏移`＝y−1/n−1 表示该财务年/索引前一年度期末，即本年期初；−1 是索引偏移而非新符号。。
- 计量边界：仅当 n≥1、A_(n−1)<0、A_n≥0、CF_n>0；区间内线性流入是假设而非真实日期。；原式输入域：`finance.first_recovery_year`, `finance.pre_recovery_cumulative_cash`, `finance.recovery_year_cash_flow`, `finance.cash_flow_basis`, `time.financial_end_year`。3C：项目已选流；3D：未折现累计及首次交叉；必须明确的既有方法/边界：评价基期与区间内线性插值说明。
- 分类 `PROJECT_CONDITIONAL_EQUITY_BLOCKED`：无首次交叉应返回期内未回收，非付款日资金证明。 不因缺付款瞬时资金证明而停止；本行其它冻结条件仍须满足。

### `F-DISCOUNTED-CUMULATIVE-CASH` — 动态累计现金流
- 原式：`A_disc,b,n = Σ(y=0…n) CF_b,y / (1+r_b)^y`。来源 `docs/solar-pv/05-formulas.json:7150`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L124，原文见 `00-original-user-baseline.md:124`（第121–127行）。
- 全部变量（原条目中文释义）：`A_disc,b,n`＝截至 n 的折现累计净现金流；`CF_b,y`＝同口径财务净现金流；`r_b`＝同口径年度折现率；`y`＝财务年度时点；`n`＝累计终点索引；`b`＝唯一现金流口径。
- 下标/范围（原条目）：`Σ y=0…n`＝从基期到累计终点全部年度流求和。；`逐个下标词素`＝disc=已经折现的累计值；b=互斥的项目/股权及税前后完整口径索引；n=累计终点或首次回收年度索引；y=财务或运营年度索引，必须按本条时间定义区分。
- 计量边界：与 NPV 同基准日、同年末假设；不能静态累计配动态年度流。；原式输入域：`finance.selected_cash_flow`, `finance.selected_discount_rate`, `time.cumulative_end_year`, `finance.cash_flow_basis`。3C：项目已选流；3D：同口径期间现金流；必须明确的既有方法/边界：匹配折现率、年末时点。
- 分类 `PROJECT_CONDITIONAL_EQUITY_BLOCKED`：项目折现累计依流和率；权益依股东流。 不因缺付款瞬时资金证明而停止；本行其它冻结条件仍须满足。

### `F-DYNAMIC-PAYBACK` — 动态首次回收期
- 原式：`PB_dynamic,b = n − 1 + (−A_disc,b,n−1)/(CF_b,n/(1+r_b)^n)`。来源 `docs/solar-pv/05-formulas.json:7281`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L124，原文见 `00-original-user-baseline.md:124`（第121–127行）。
- 全部变量（原条目中文释义）：`PB_dynamic,b`＝自基期起动态首次回收期；`n`＝折现累计首次负转非负的年度终点；`A_disc,b,n−1`＝前一年末负折现累计净流；`CF_b,n`＝回收年度未折现净现金流；`r_b`＝同口径年折现率；`b`＝唯一现金流口径；`N`＝评价期最后一个财务年度时点，限制首次交叉搜索范围。
- 下标/范围（原条目）：`n`＝范围 1…N 中折现累计首次负转非负最小索引；N 为已定义的评价末期。；`逐个下标词素`＝dynamic=折现回收期；b=互斥的项目/股权及税前后完整口径索引；disc=已经折现的累计值；n=累计终点或首次回收年度索引；1=首运营年或扰动后情景 1，具体按完整符号区分；`时间偏移`＝y−1/n−1 表示该财务年/索引前一年度期末，即本年期初；−1 是索引偏移而非新符号。。
- 计量边界：与静态回收期同起点；线性插值基于年度折现值，只是近似，不代表精确日历回收日。；原式输入域：`finance.first_discounted_recovery_year`, `finance.pre_discounted_recovery_cumulative`, `finance.discounted_recovery_year_cash_flow`, `finance.selected_discount_rate`, `finance.cash_flow_basis`, `time.financial_end_year`。3C：项目已选流；3D：折现累计与首次交叉；必须明确的既有方法/边界：匹配折现率/年内插值。
- 分类 `PROJECT_CONDITIONAL_EQUITY_BLOCKED`：未交叉输出未回收，不能当实际到款日。 不因缺付款瞬时资金证明而停止；本行其它冻结条件仍须满足。

### `F-LIFECYCLE-COST` — 无杠杆生命周期净成本
- 原式：`Cost_P,y = K_P,y + O_y + T_cost,P,y + ΔW_P,y − S_P,y − SUB_P,y`。来源 `docs/solar-pv/05-formulas.json:7418`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L125，原文见 `00-original-user-baseline.md:125`（第121–127行）。
- 全部变量（原条目中文释义）：`Cost_P,y`＝选定税费/补贴边界的项目生命周期净成本；`K_P,y`＝无杠杆工程及资本更换现金支出；`O_y`＝现金运营支出，不含折旧；`T_cost,P,y`＝选定成本税费，税前 LCOE 不含所得税；税后模型需独立收入税基；`ΔW_P,y`＝未重计的营运资金净增；`S_P,y`＝净残值回收及未在 ΔW 中回收的营运资金；`SUB_P,y`＝明确选择为成本抵减且未计收入的有依据补贴。
- 下标/范围（原条目）：`P`＝无杠杆项目；y=建设至退出时点；cost=成本税费，SUB=补贴抵减。；`逐个下标词素`＝P=项目无杠杆口径；y=财务或运营年度索引，必须按本条时间定义区分；cost=LCOE 成本范围。
- 计量边界：默认方法冻结为项目无杠杆税前所得税 LCOE，保留适用其他税；融资本息不混入再用含融资成本折现率双计；补贴抵成本/收益二选一。；原式输入域：`capex.unlevered_cash_annual`, `opex.cash_annual`, `lcoe.cost_taxes`, `working_capital.project_net_change`, `finance.project_terminal_cash`, `lcoe.cost_subsidy_offset`。3C：可交付电量另供LCOE；3D：无杠杆CAPEX/更换、OPEX、适用成本税、营运与处置现金；必须明确的既有方法/边界：冻结无杠杆税前所得税成本/补贴抵减边界。
- 分类 `CONDITIONAL_ANNUAL`：须核定残值是否可回收、补贴是否有依据且不双计；可按明确合成期间边界计算。 不因缺付款瞬时资金证明而停止；本行其它冻结条件仍须满足。

### `F-LCOE` — 平准化度电成本
- 原式：`LCOE = Σ(y=0…N) Cost_P,y/(1+r_L)^y / Σ(y=0…N) E_delivered,y/(1+r_L)^y`。来源 `docs/solar-pv/05-formulas.json:7555`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L125，原文见 `00-original-user-baseline.md:125`（第121–127行）。
- 全部变量（原条目中文释义）：`LCOE`＝声明成本与交付边界的平准化度电成本；`Cost_P,y`＝本条选定无杠杆税前所得税生命周期净成本；`E_delivered,y`＝同项目计量点可利用交付电量，建设无发电期显式为零；`r_L`＝与成本币种/名义实际口径相容的 LCOE 年折现率；`y`＝建设基期至退出的财务年度时点；`N`＝末期评价年度。
- 下标/范围（原条目）：`Σ y=0…N`＝分子分母分别对全部财务年求和；L=度电成本折现率标签。；`逐个下标词素`＝P=项目无杠杆口径；y=财务或运营年度索引，必须按本条时间定义区分；delivered=同计量点可利用交付量，不含弃光；L=度电成本折现口径。
- 计量边界：分子/分母同年、同期间、同项目边界；弃光不算交付；按售电量计则成本必须切换为同售电边界。；原式输入域：`lcoe.project_cost_annual`, `energy.delivered_annual_kwh`, `lcoe.discount_rate`, `time.financial_end_year`。3C：3B/3C同口径逐年交付电量；3D：F-LIFECYCLE-COST年度成本；必须明确的既有方法/边界：finance.project_discount_rate经绑定选同名义口径r_L。
- 分类 `DEPENDENT_PROJECT`：年度成本与交付量、明确折现率具备后可算；不能用理论发电量分母。 不因缺付款瞬时资金证明而停止；本行其它冻结条件仍须满足。

### `F-CFADS` — 可用于偿债的现金流
- 原式：`CFADS_y = B_op,y − O_y − T_E,y − ΔW_ds,y − K_mand,y + A_ds,y`。来源 `docs/solar-pv/05-formulas.json:7686`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L126，原文见 `00-original-user-baseline.md:126`（第121–127行）。
- 全部变量（原条目中文释义）：`CFADS_y`＝按融资协议可用于偿债的当期现金流；`B_op,y`＝经营现金利益，不含融资；`O_y`＝协议口径现金运营支出；`T_E,y`＝协议口径实际现金税，不重复税价桥；`ΔW_ds,y`＝协议要求的未重计营运资金或储备净增；`K_mand,y`＝协议要求在偿债前扣除的维护性资本开支；`A_ds,y`＝有合同依据的其他 CFADS 调整，可正可负。
- 下标/范围（原条目）：`y`＝与债务应付服务完全同周期；ds=偿债协议调整；mand=强制维护资本支出。；`逐个下标词素`＝y=财务或运营年度索引，必须按本条时间定义区分；op=运营经营利益；E=股权/融资主体口径，ε_E 则标能量残差；ds=融资协议偿债现金口径；mand=协议要求优先扣除的维护性资本支出。
- 计量边界：债务服务前现金；不得在分子再扣同笔利息本金，也不把提款、股东出资当经营偿债能力。；原式输入域：`finance.project_operating_cash_benefit`, `opex.cash_annual`, `tax.equity_cash_total`, `debt.cfads_working_capital_change`, `debt.cfads_mandatory_capex`, `debt.cfads_adjustments`。3C：年度经营利益；3D：融资后现金税、OPEX、协议营运/储备、强制更换、调整；必须明确的既有方法/边界：cfads.method及协议或显式SYNTHETIC情景。
- 分类 `CONDITIONAL_PROTOCOL`：合成方法已配置，可计算标注情景；真实协议CFADS/调整未获验证，不可宣布合同值。 不因缺付款瞬时资金证明而停止；本行其它冻结条件仍须满足。

### `F-DSCR` — 偿债备付率
- 原式：`DSCR_y = CFADS_y / DS_y`。来源 `docs/solar-pv/05-formulas.json:7930`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L126，原文见 `00-original-user-baseline.md:126`（第121–127行）。
- 全部变量（原条目中文释义）：`DSCR_y`＝当期可供偿债现金除以合同债务服务；`CFADS_y`＝同周期协议口径可用于偿债现金；`DS_y`＝同周期合同应付本金、利息及协议费用合计。
- 下标/范围（原条目）：`y`＝与服务完全相同周期；DS=应付债务服务；DSCR=比值。；`逐个下标词素`＝y=财务或运营年度索引，必须按本条时间定义区分。
- 计量边界：无融资返回 NOT_APPLICABLE；存在债务但宽限期服务为零返回 ZERO_DEBT_SERVICE 不输出无限或伪造数值。；原式输入域：`debt.cfads`, `debt.service_due`。3C：无直接需要；来自CFADS；3D：同期合同应还本金/利息/费；必须明确的既有方法/边界：cfads.method及债务合同服务期。
- 分类 `CONDITIONAL_PROTOCOL`：应还DS已在3D，CFADS协议口径未验真；情景可算，合同DSCR未证实，DS=0要状态。 不因缺付款瞬时资金证明而停止；本行其它冻结条件仍须满足。

### `F-BREAK-EVEN-PRICE` — 净现值为零的盈亏平衡电价
- 原式：`P_star = {p∈P : NPV_b(CF_b(p), r_b) = 0}`。来源 `docs/solar-pv/05-formulas.json:8034`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L127，原文见 `00-original-user-baseline.md:127`（第121–127行）。
- 全部变量（原条目中文释义）：`P_star`＝满足 NPV=0 的电价根集合；`p`＝待求结算电价，只调整预先指定的电价项；`P`＝有业务依据且事前声明的允许电价域，可含合法负价；`NPV_b`＝同一税/融资口径的净现值函数；`CF_b(p)`＝固定其他外生输入、电价为 p 时完整重算的现金流向量；`r_b`＝同一口径折现率；`b`＝项目或股权的唯一口径。
- 下标/范围（有效定义 E05）：`p∈P`＝域内全部使 NPV=0 的电价构成集合；`逐个下标词素`＝star=盈亏平衡根集合标签，相当于上标 *，不是乘方；b=互斥的项目/股权及税前后完整口径索引；p=待求结算电价，只调整事前指定电价项，在允许价格域P内求全部有效根。
- 计量边界：冻结“使 NPV=0”的定义，不混称会计利润盈亏平衡；分时电价可对指定倍率求根但需新输出字段。；原式输入域：`sensitivity.price_search_domain`, `finance.npv`, `sensitivity.price_cash_flow_vector`, `finance.selected_discount_rate`, `finance.cash_flow_basis`。3C：价格变动时3C全部重算；3D：3D税/资本/经营与3E项目/股东全链重算；必须明确的既有方法/边界：break_even.*域、指定可调整价格项、折现口径。
- 分类 `DEPENDENT_FULL_CHAIN`：搜索域有合成配置；必须明确变动的是哪一价格，并逐候选整链重算，非直接变更NPV终值。 不因缺付款瞬时资金证明而停止；本行其它冻结条件仍须满足。

### `F-WORST-CASH-YEAR` — 最差现金流年份集合
- 原式：`Y_worst,b = argmin(y∈Y) CF_b,y`。来源 `docs/solar-pv/05-formulas.json:8530`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L127，原文见 `00-original-user-baseline.md:127`（第121–127行）。
- 全部变量（原条目中文释义）：`Y_worst,b`＝达到最小净现金流的全部年份，允许并列；`CF_b,y`＝选定口径当年净现金流；`Y`＝被比较的有效年份集合，需明确仅运营期或含建设期；`y`＝年份索引；`b`＝项目/股权及税前后口径。
- 下标/范围（原条目）：`argmin y∈Y`＝在声明范围内寻找全部最小值年份；不武断取第一个。；`逐个下标词素`＝worst=给定年份集合中最差净现金流的全部位置；b=互斥的项目/股权及税前后完整口径索引；y=财务或运营年度索引，必须按本条时间定义区分。
- 计量边界：必须同时列最小现金额和比较范围；含建设期与运营最差年各自输出，不能借大建设负数掩盖运营缺口。；原式输入域：`finance.selected_cash_flow`, `risk.cash_year_scope`, `finance.cash_flow_basis`。3C：所选项目/股东期间流；3D：完整对应各期现金流；必须明确的既有方法/边界：风险比较范围必须明确运营或建设。
- 分类 `PROJECT_CONDITIONAL_EQUITY_BLOCKED`：项目最差年按明确范围可算；股东需真实/获批计划流。 不因缺付款瞬时资金证明而停止；本行其它冻结条件仍须满足。

### `F-INVESTMENT-HURDLE-GAP` — 投资门槛差距
- 原式：`G_M = M_calc − M_target`。来源 `docs/solar-pv/05-formulas.json:8792`，SHA-256 `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331`；需求 R-S06-L127，原文见 `00-original-user-baseline.md:127`（第121–127行）。
- 全部变量（原条目中文释义）：`G_M`＝测算值减用户门槛的原始差距；`M_calc`＝有效的确定性测算指标，不得倒改输入迎合目标；`M_target`＝用户目标，如 IRR 下限或回收期上限。
- 下标/范围（原条目）：`M`＝被比较指标；calc=测算，target=用户目标。；`逐个下标词素`＝M=所考察财务/技术指标；calc=确定性测算结果；target=用户目标阈值而非实际测算输入。
- 计量边界：IRR 下限差距≥0 倾向满足；回收期上限差距≤0 才满足，方向由指标定义而非本式自动推断。；原式输入域：`decision.calculated_metric`, `decision.target_metric`。3C：无直接需要；3D：有效已算指标；必须明确的既有方法/边界：targets.*有来源门槛且与指标同口径。
- 分类 `BLOCKED_TARGETS_FOR_CASES`：两案目标门槛未提供；可不伪造目标并标缺失，不阻断独立项目指标计算。 原公式无法产生完整有效数值，必须带原因保留未定。

## 4. 两案已封存 Phase 3D 数据：15 项检查

两项目 `result.json` 均为 `CALCULATED_SYNTHETIC`，各 26 行（CONSTRUCTION＋25个运营期），`phase3e_cashflow` 均为 `null`；未计算任一 3E 指标。第12、15年更换付现各为 190,000/720,000 元，3D 应收/应付、项目与融资后税、债务应还均存在。`cash.opening_cash=0`、`equity.distribution_fractions` 全1、最低储备0皆为明确**合成**方法假设；3D 代码 `financial_ledger.py:193-265` 未消费它们生成实际股东交易或非受限余额。该 0 不是经验证银行可用存款，也不能与 `finance.working_capital` 混淆。

| 条目 | 分类（两案相同） | 证据与限制 |
|---|---|---|
| 期间划分 | 已存在且可按冻结口径使用 | 两案26期，CONSTRUCTION+25运营年 |
| Phase 3C收益 | 已存在但仍需核对计算口径 | 屋顶避免支出是经济利益、非主体银行收款 |
| CAPEX支付计划 | 已存在且可按冻结口径使用 | 3D建设与替换付现；合成日期非实际扣款时刻 |
| 资产更换支出 | 已存在且可按冻结口径使用 | 年12/15分别190000/720000，已列3D账 |
| OPEX付现 | 已存在且可按冻结口径使用 | 3D逐年opex_cash_paid |
| 税费预测实付 | 已存在且可按冻结口径使用 | 3D独立project/equity税费列；只作SYNTHETIC预测 |
| 贷款提款 | 已存在且可按冻结口径使用 | 3D period债务提款；无证明替换期另行提款 |
| 本息支付 | 已存在且可按冻结口径使用 | 逐期实付与应还分开 |
| 营运资金变化 | 已存在但仍需核对计算口径 | 建设期占用及终期回收须按未重复扣除边界映射 |
| 应收应付/账簿余额 | 已存在且可按冻结口径使用 | 应收/资本应付/所得税/债务本金；非现金存量 |
| 期初资本金/股东分配 | 原冻结必需但缺失 | 有期初现金合成0及比例1/储备0；没有逐期股东出资、可合法支付分配、退出和非受限主体余额 |
| 折现率 | 已存在但仍需核对计算口径 | 两案合成project/equity 0.08；LCOE等需明确名实/税口径 |
| IRR搜索域 | 已存在且可按冻结口径使用 | 合成界[-0.5,1]及有界求根控制，域外不作不存在证明 |
| 盈亏电价搜索域 | 已存在但仍需核对计算口径 | 合成[0,2]；待指定变动电价项并全链重算 |
| CFADS计算配置 | 已存在但仍需核对计算口径 | 合成method存在；合同协议边界/调整尚未核实 |

- `industrial_rooftop`：`input.json` SHA-256 `7b08b2b12e9b8a57b4848a73b9c3b68d8881f9305cd796e773a16b3699ba743f`；`methods.json` `3b33541d440b847187cc1886e27789a167a91cdab5e410b89aed22e3f303d8f5`；`result.json` 文件字节 `53d3c0cded618566bbce1d8e51fa4e0be91d84609f7bf907010a93cf3acb182e`；**canonical** `result_hash` `5e2868121e4c80119a47157348b9afba685a172d4575a9d71c840dbbb68278d7`。两种哈希不可混为同一值。上游 3C 结果 hash `7eee9f80f9633a4e93905f2df7bafa9896658020c67069b5276e16f259534a50`。
- `utility_scale_ground`：`input.json` SHA-256 `dce65dc6808321a1267d9deb03737f2eeeddd7ac942cd96f2af5783d879a583f`；`methods.json` `a3d04cd0f14d7c6678ef739dc494c16357a8e766a792a7d0c5f7d6b85c90c5f8`；`result.json` 文件字节 `99e7b2ae90a28dc07e6c6effbc9bdca9e0aa1c8226efcd10b357e988b4dfd9bb`；**canonical** `result_hash` `d2a4ded9e50d16ebd1fe858d06c987daa4a230b3560ddca7be9974f8c358c4f7`。两种哈希不可混为同一值。上游 3C 结果 hash `6f070c327912973efd79f5cb50a705d4422990132aa28701b1e6fe2a5e6ae616`。

## 5. 阻断血缘与范围漂移时间链

| 链路 | 性质/已授权事实 | 本次边界判断 |
|---|---|---|
| Phase 3E 年度/dated现金流计划 | 原需求 `R-S06-L121..127`；17号计划:85-95，21式 | 项目/股东分别实现；数值验收尚未开始 |
| 3D 原 B1/B2/B3 | 3E 启动报告:44-54：自用应收重复、更换付现漏记、项目/权益税混用 | 属冻结公式的真实上游缺陷；用户批准后 3D 限定修复已完成，不能继续称这三项未修 |
| 3D 合成方法修复 | `phase3d-repair-and-acceptance.md:35-39` 明确折现/IRR/电价/CFADS/分配比例来源与假设 | 解决原 B5 与 B4 的**配置缺项**；没有解决实际股东资金或真实贷款协议 |
| 四笔资金覆盖审计 | `phase3e-funding-coverage-review.md:64-79`；`phase3e-funding-coverage-recheck.md:59-74` | 分别为 2037-06-01 / 2040-06-01 两案各 190,000 / 720,000 CNY；仅 `INDETERMINATE`，并非已证明缺口；不是原全局门禁 |
| 资金契约可表达性审查 | `phase3e-funding-contract-expressibility-review.md:14-30,61-72`：当前契约不足以证明瞬时资金 | 若另批该证明确须扩接口；不由「表达不足」反证原式必须做逐笔银行管理 |
| 后来拟扩逐笔事件 Schema | 无本轮明确批准；D2批准的是受控方法及哈希 | 把拟扩 Schema 作为所有年度财务指标的先决条件即范围漂移；仅原 `F-DATED-NPV` 的完整日期事件/股东与期间平衡仍须分别保持阻断 |

**来源类别**：原用户要求/Phase1冻结为 `00-original-user-baseline.md`、`05-formulas.json`、矩阵；已正式批准的必要变更仅 `19-phase3-approved-implementation-contract.md` D1–D3 及获授权 3D 修复；`16/17` 是后续任务与实施计划，不可自动改写冻结验收；Phase 3E 启动、资金覆盖/复核/表达性报告是实施与 Hermes 专项审计的结论，而非新的用户批准需求。现有实现与有效验收同样不可混淆。**未发现两份正式冻结文件在瞬时银行覆盖门禁上直接互相矛盾；故选 A，不选 C**。D2 申请中「初始余额/事件顺序」与现行受控 Schema 的粒度差异属于实现能力/批准具体范围的审查点，不据此推定隐含银行全流水门禁。

## 6. 最小后续决定、不得解除的阻断

1. 待用户确认：是否批准把 **付款瞬时覆盖风险单独保留，不阻断独立年度项目公式的开发**；此决定不改变四笔 INDETERMINATE、21式验收标准或正式 Phase 3E 当前 BLOCKED。
2. 如继续既有 Phase 3E，仅用已封存年度 3C/3D 成本收益税融资结果与已批准现有方法；先审正确现金计量边界、残值/回收与税，不把股东分配比例当实际付款；各公式只对完整输入给结果，否则保留 `BLOCKED_MISSING_INPUT`/`BLOCKED_METHOD_REVIEW`/`UNDEFINED` 原状态。
3. 不得自动解除的**原需求局部阻断**：`F-CASH-FUNDING-BALANCE` 期间主体非受限期初/末与 EQ/DIV 非负/缺口处理；股东实缴/合法分配/退出及权益 NPV/IRR；`F-DATED-NPV` 全量日期事件；协议口径 CFADS/DSCR 真实陈述；未提供目标的 `F-INVESTMENT-HURDLE-GAP`。若无现成结构入口合法表达这些原式必需事实，须专门请求用户批准兼容处理；不能默默新增银行/股东 Schema，也不能以取消公式解阻断。
4. 本次**只读审计与两份新交付**，没有计算 3E、测试、修改冻结要求/生产代码/Schema/案例、commit、push、部署、上传或发布；不得说 3E PASS 或全部 21 式现可给数值。审批前保持当前状态。

## 7. 证据身份与工作区保护

| 已读来源（原字节） | SHA-256 |
|---|---|
| `docs/solar-pv/00-original-user-baseline.md` | `4af609040ca4e800b16d561b86a8a33c54226d175581b54aa00110158c5d09f2` |
| `docs/solar-pv/00-baseline-manifest.json` | `33845de976ec13345320b79ff7045e86a39bf2194a427b5cd28169238d1defec` |
| `docs/solar-pv/README.md` | `95e8f4625bc66d3cde733619ba5d76b8d5cba438257740d4cb7dcd0c9151b853` |
| `docs/solar-pv/02-report-outline-18-chapters.md` | `b78456f1ac59be371f15076e0a17cdcfa89249d68b584afa57feaf2db8654125` |
| `docs/solar-pv/03-input-data-dictionary.md` | `fcc1eac5641f941adbd6fd4fab216050344b2ae4e0590d8e9549682117ab8148` |
| `docs/solar-pv/03-input-fields.json` | `393140cc57b5934041c3fece2c9c185c03c7876afaa3403ce317d795d6112a1b` |
| `docs/solar-pv/05-formulas.json` | `d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331` |
| `docs/solar-pv/05-formula-extensions.json` | `14bb789c908f4f883910fd517fd2cf55cf0719739f9fdd84e4dc61b111252007` |
| `docs/solar-pv/05-field-bindings.json` | `4ef6171f063f402963d61edc9647c7565c9ec9338099f62424a77e3507521533` |
| `docs/solar-pv/07-category-boundaries.md` | `ee935418c0a7ef55544f6f97fddf71bcb62f6b906d0c19256b871f8d02b086a8` |
| `docs/solar-pv/08-requirement-traceability.csv` | `80678b46ed84e1935fbca04fcb10662e01dc8af4c0d1f616743c5855498203b4` |
| `docs/solar-pv/08-acceptance-design.md` | `0c8e0db8619bc1d1b060a277923d261ebe0f01f5fa4e666d764e92b4c568acb3` |
| `docs/solar-pv/10-four-file-acceptance.md` | `50ebfe4e942bd1f33ed975b4d10eb67a044ea7cf31de7b8577384139c32a909c` |
| `docs/solar-pv/11-phased-roadmap.md` | `2e45d757c5f4fc9fdac5b7ae5a03f5f95fd8c05ae09de8a65b58be062d5bd614` |
| `docs/solar-pv/12-canonical-result-contract.md` | `d45a819d8a7903e5c4b3493823219a896747540424280018507471bd0df994db` |
| `docs/solar-pv/16-phase3-user-task.md` | `c1fdd047f8d493678642e1609c5b7da2492dae5ef0e28ac2966cd1f59bdb3349` |
| `docs/solar-pv/17-phase3-implementation-plan.md` | `94ec602f8c118905e0bf5fbe97c2e9cf91d3446165debe1f408cbcbe4bac6d08` |
| `docs/solar-pv/18-phase3-preimplementation-review.md` | `1f0ceb81dfe925a8501879252b9ebe5a71d35774fc71b390c3338b9464cd2868` |
| `docs/solar-pv/19-phase3-approved-implementation-contract.md` | `68f2551dce001360972fe94dd562539e967dc1891ae17bc9fb98898ccc4495b4` |
| `reports/solar-pv/phase3d-review-and-acceptance.md` | `0d01fbfd7a50158fca79a70cdb009492653c9fbae8bc6991b17a4379d7d88962` |
| `reports/solar-pv/phase3d-repair-and-acceptance.md` | `1a4e892596befef1392eb4723fcda36ddebe66595805c149477db314ed0b6317` |
| `reports/solar-pv/phase3e-review-and-acceptance.md` | `43b2c1af1d4a804329449fc38a423c29721782b6877d299ce2bfeac8f886844d` |
| `reports/solar-pv/phase3e-funding-coverage-review.md` | `af2c785901bf490bfe9de4a82ec65c82376b72a1dbc66bede9dbe8580b3cb5be` |
| `reports/solar-pv/phase3e-funding-coverage-recheck.md` | `526c1816f873ce8c55832684bd9aa07ad7d075123e56842dbdb4366e97ce19f3` |
| `reports/solar-pv/phase3e-funding-contract-expressibility-review.md` | `247381b643839fcd931024c1ae2e0a91ba58574ed621d6152d0683dd3d0469b3` |
| `services/solar-pv-engine/src/wangbin_solar_pv/calculation/method_config.py` | `3beccfc6ab03a9d6c21d020819eb2d30422e83daa4245e7167ab7428e17c6001` |
| `services/solar-pv-engine/src/wangbin_solar_pv/calculation/financial_ledger.py` | `41e9d5b85ecb1b730554fcdf20932fc69b2f15fe2a2ddfb46ead20d49088fce6` |
| `services/solar-pv-engine/src/wangbin_solar_pv/calculation/schema/method-config.schema.json` | `f8d8aa861269bc44af0eb302e56457f6d5b7edac9f2b7f5903dc6440df8eae14` |
| `services/solar-pv-engine/src/wangbin_solar_pv/calculation/schema/calculation-result.schema.json` | `f9f188a924e1c040697a09d7a97d88800bcee8756a453f7a2efe56ca2fc55fe6` |
| `services/solar-pv-engine/schemas/project-input.schema.json` | `1de2bf35f96b75ea6ffd510dd07f8ea9f52a0f26616e174280346c5127363e27` |
| `services/solar-pv-engine/src/wangbin_solar_pv/definition_versions.py` | `9d50c04fb815fe1160ff43ec1fb7141492bf0acaa8ae264b0480e47fd68b5b43` |
| `services/solar-pv-engine/src/wangbin_solar_pv/definition-lock.json` | `728ccb42a5d5f78cc9252f61070dd5eb2c1a426b8e727423d113bb2f79d170b6` |
| `services/solar-pv-engine/src/wangbin_solar_pv/definition-errata.json` | `bee7fc4e737a3f8e40befa272a842ce1ad0454b8437590089e090e32031b15e0` |

**六个用户既有差异文件的启动/结束 SHA-256（每项不变）：**
- `packages/skills/wangbin-receivable-analyzer/SKILL.md`：`8a5ee4eb54a4f6a08d3ab7cccf792c12d5f01ab3fb4ab0de8dc926149087a945`。
- `packages/skills/wangbin-receivable-analyzer/manifest.json`：`0a9459ab33f0f3bbc1c538535b994218e6ad92792901a39c3e4e94eaf777762b`。
- `products/catalog.json`：`d74f3fa9f00184ee64f8452862958c3ef11f7848378ed42657e4b5fbc91def27`。
- `reports/workbuddy-upload-list.md`：`6d0df16f21a4cf7a3a87eef1b90fb2f7d26fd1457f124066707281f9ff0ec586`。
- `reports/validate.json`：`42765dae553254369311f3d4e7d2d3ab6f3cf0f8858a1c0e587debfea809d1ba`。
- `reports/validate.md`：`2c3f7cd41671f2af1cd9f5688ae4e3779d92390260cdb43299457bcedb2060e3`。
**288 保护文件**：以 `reports/solar-pv/phase3c-startup-state.json`（SHA-256 `26fdade64ab3f1f23a51850afa3ce068f3ebfc026b22f30e3a06e31a76732a4d`）逐件复核：286 与旧基线匹配，原有差异仅 `reports/validate.json`、`reports/validate.md` 2 项，本轮新增差异 0、缺失 0；这**不是**工作区 clean。终检逐项读取 SHA-256，与机器证据所记起止值一致。
**处理状态**：当前 HEAD 不动、暂存区空；六既有文件、历史审计报告和封存案例均不覆盖。此处源路径/行号/原字节哈希可在同名 JSON 中按每条公式及两个案例复核。无凭据值随报告输出，敏感值若需引用均记 `[REDACTED]`。
