# Phase 3E-P2-5：已证财务指标受限验收

**结论：PARTIAL，不是 Phase 3E PASS。** 冻结 Catalog 中 Phase 3E 共 **21** 条公式（总 Catalog 89 条），当前有来源的 **SYNTHETIC、NO_DISPOSITION、项目税后、年末折现**三次执行均为 **7 CALCULATED / 12 BLOCKED_MISSING_INPUT / 2 NOT_IMPLEMENTED**。其中本轮由占位接通 **4** 条；历史同类候选为 3 / 12 / 6。这里的 CALCULATED 只表示所列合成项目执行和数值核验成立，**不代表两个封存 25 年项目或真实项目通过**。冻结式与正式状态枚举未修改。逐字段冻结输入、历史状态和测试入口见 `phase3e-p2-5-formula-audit.json`；当前逐式状态、回执与独立参考见 `phase3e-p2-5-evidence.json`、`phase3e-p2-5-decimal-reconciliation.json`；逐项**实际数值、3D 来源字段、独立计算式及精确相等比较**见 `phase3e-p2-5-value-ledger.json`。

## 1. 执行身份与局部验收

- 基线 `87f4aa15344e9ae40367c673e5aaed18ea6f865e`；P2-5A 审计提交 `67257bb3153df8b79faf30b65d9edbc05e8c853d`；P2-5B 生产接线提交 `ba3c40b76b90ef92151d25e6b054e7738e2fa674`。**没有修改测试文件、冻结公式、封存案例、P2-4 根集定义、终期 EVENTS 或正式状态枚举。**
- `phase3e.py:219-338` 在 3E 绑定明确来源的 NO_DISPOSITION 终期、重算 3D 账簿，生成含建设第 0 期的项目税后与税前现金，并对选定的项目税后向量按同口径来源折现率计算 NPV；税前仅加回**项目所得税现金**，不是 VAT/其他税。新增 `phase3e.py:339-395` 复用冻结内核接通项目累计、折现累计、静态与动态回收期；全期前缀和证明**首次**负转非负，后续重新转负的年度保存在现有 details。无有效交叉保持 `UNDEFINED` 且 `value=null`，不得捏造回收期。动态内核接收未折现当年现金，避免双重折现；折现累计末值必须与同口径 NPV 完全对账。
- 独立参考未调用 3E 内核生成 expected：由三份 3D 年账簿、合成价 `0.4 / 0.6 / 0.8 元/kWh`、实际自用避免支出和现金税源计算；按 3D 既有 **28 位**税/VAT 精度与 3E **80 位** Decimal 精度重算项目现金、所得税加回、逐年前缀和、折现前缀和、两类回收期和 NPV。三组七条项目指标的 **21 组实际值与参考值精确相等**；已将每组真实观察值、最小必要 3D 年账簿字段、参考式及原始结果字节哈希一并封入 `phase3e-p2-5-value-ledger.json`，可在不重新运行重型链的条件下复核数字。三份不同结果哈希；当前输出均 `PARTIAL` 且 `real_project=NOT_VERIFIED`。这是**有来源合成候选的真实链执行**，不是单点理想模型代替真实项目；大型原始 3D/3E 结果 JSON 未重复入库，归档的是字段级摘录和原始文件哈希，不能把摘录误称完整原件。
- 每份执行输出 `validate_result` 通过并带 3D `result_hash` 来源绑定；受影响 E2E 对 `0.6` 候选另做 JSON 往返及封存 `result_hash` 不变验证；上述数值复算和三份源/结果字节 SHA-256 归档在 Decimal 对账 JSON。输出的 `F-BREAK-EVEN-PRICE` 在三案均 `BLOCKED_MISSING_INPUT`、`value=null`；项目现金及 NPV 计算不构成完整价格根集认证。

## 2. 21 条冻结公式的实际执行结论

下列状态均取本轮三次同口径 SYNTHETIC 项目实际输出；输入字段、冻结方程、单条原子测试 ID 在机器矩阵。原子测试覆盖**不等于**所有公式已取得真实项目财务来源；共享 normal-case 测试多数只断言状态，不能被写成逐条独立数值通过。

| 冻结公式 ID | 本轮实际状态 | 来源、独立依据或未满足的硬条件 |
|---|---|---|
| F-PROJECT-CASH-FLOW | CALCULATED | 3D 项目经营/现金 OPEX/项目现金税/无杠杆投资/营运资金，另经 3E 终期 NO_DISPOSITION 来源绑定；3D 年账簿独立复算。 |
| F-PROJECT-PRETAX-CASH-FLOW | CALCULATED | 同一期项目税后现金仅加回 3D 已缴项目所得税；未加回 VAT；独立 Decimal 复算。 |
| F-EQUITY-AVAILABLE-CASH-FLOW | BLOCKED_MISSING_INPUT | 缺权益终期现金及融资后储备、债务收付的完整同口径来源；项目现金不能充当股东现金。 |
| F-EQUITY-INVESTOR-CASH-FLOW | BLOCKED_MISSING_INPUT | 缺逐期真实出资、合法分配、退出事件；可用现金不是已分红。 |
| F-CASH-FUNDING-BALANCE | BLOCKED_MISSING_INPUT | 缺主体非受限期初余额及实际出资/分配和跨期滚动来源。 |
| F-NPV | CALCULATED | 项目**税后**全期流、同口径项目折现率及年末时点；独立 Decimal 与折现累计末值对账；**税前 NPV/权益 NPV 未由此签收**。 |
| F-DATED-NPV | BLOCKED_MISSING_INPUT | 缺全量带日期、事件 ID、现金额、日计数适用性及不重不漏证明；年账不能代替事件集合。 |
| F-NOMINAL-REAL-RATE | BLOCKED_MISSING_INPUT | 缺同风险/税/币种的实际折现率与一般通胀率；电价涨幅不可替代通胀。 |
| F-IRR-PROJECT | NOT_IMPLEMENTED | 项目流已具备，但当前 D2 源快照**没有 irr 搜索域/精度来源**；不得默设区间或从 NPV 倒推出唯一根。旧占位的“项目流未接通/范围外”理由已过时，须单列输入与根集验收依赖。 |
| F-IRR-EQUITY | BLOCKED_MISSING_INPUT | 缺投资者真实现金收付向量；不能以权益可用流或项目流代替。 |
| F-CUMULATIVE-CASH-FLOW | CALCULATED | **本轮接通**，项目税后全期含建设 0 期，独立逐期 Decimal 前缀和相等。 |
| F-STATIC-PAYBACK | CALCULATED | **本轮接通**，全期累计首次负转非负、对应未折现年现金；独立 Decimal 插值相等，details 披露随后再转负年度。 |
| F-DISCOUNTED-CUMULATIVE-CASH | CALCULATED | **本轮接通**，与项目 NPV 相同基准日、现金流和折现率；独立 Decimal 前缀和、末值与 NPV 一致。 |
| F-DYNAMIC-PAYBACK | CALCULATED | **本轮接通**，首次折现累计回正，当前年度原始现金仅在内核折现一次；独立 Decimal 插值相等。 |
| F-LIFECYCLE-COST | BLOCKED_MISSING_INPUT | 缺经核定的非所得税成本税、补贴抵减及终期成本/现金不重计边界，不能把项目 NPV 成本替代。 |
| F-LCOE | BLOCKED_MISSING_INPUT | 上游生命周期成本不成立；另需同一计量边界已交付 kWh 及成本折现口径，不得用理论发电量。 |
| F-CFADS | BLOCKED_MISSING_INPUT | 缺协议 CFADS 方法、带来源的调整向量/储备/强制 CAPEX；不得补零。 |
| F-DSCR | BLOCKED_MISSING_INPUT | 上游 CFADS 未成立；服务期零债务服务时须遵循既有 `UNDEFINED/ZERO_DEBT_SERVICE`，不输出无穷数值。 |
| F-BREAK-EVEN-PRICE | BLOCKED_MISSING_INPUT | 正式 `value=null`；P2-4 全链单点与理想有理模型**不是**连续闭域全分支完整根集认证。EVENTS 终期缺交易级排重及税务依据继续阻断；`1 元` 残差不是获批阈值。 |
| F-WORST-CASH-YEAR | NOT_IMPLEMENTED | 缺事前比较年范围；现有内核返回年份字符串，而正式 value 仅容数值/数值数组，还需同列最小金额。旧“项目流未接通”理由已过时，不可伪造数值年份。 |
| F-INVESTMENT-HURDLE-GAP | BLOCKED_MISSING_INPUT | 缺用户同口径目标及达标方向，不得从计算值反填目标。 |

**占位核查：**四项原先错误地滞留在 `NOT_IMPLEMENTED` 的项目回报指标已接通并取得当前合成项目数值。剩余两项的旧通用占位理由不准确，但前者确缺已声明 IRR 搜索域，后者缺比较范围和结果表示批准，故**没有合法数值可发布**；仍保留当前实际 `NOT_IMPLEMENTED`，不以报告改写生产状态。所有其余公式的原子内核存在并不等于有项目级来源。两个封存 25 年项目缺终期证明/获证项目折现率/所有权现金及其他所需来源；未更改其输入或结果，**没有**把本轮三组 SYNTHETIC 七项状态套到封存案例。

## 3. 测试、身份与保护门禁

| 门禁 | 本轮事实 | 限制 |
|---|---|---|
| 快速财务/IRR/方法 | 64 passed，0 failed/skipped | 生产接线最终候选上的原子测试；原始 JUnit、回执、日志归档于 `phase3e-p2-5-evidence/fast/`。 |
| 契约专项 | 35 passed，0 failed/skipped | `test_calculation_contracts.py`，原始归档于 `.../contract/`。 |
| 受影响真实链 E2E | 1 passed，0 failed/skipped；三次 3E 执行；2186.197s | `test_phase3e_terminal_npv.py::test_no_disposition_has_independent_decimal_cashflow_and_npv`；它独立验证原三项，本轮四项另由 Decimal 对账脚本逐值核验。原始归档于 `.../e2e/`。E2E 在实施提交**之前**运行，回执 HEAD 不得冒充该提交之后的完整 L3。 |
| 当前候选 L2 收集 | 60 个唯一参数化测试 ID，收集成功；**未运行完整 L2** | 由完成后的当前候选 L3 实际 JUnit 及身份、执行条件核对后才可能证明覆盖。 |
| WorkBuddy/Expert L3 | 109 passed、5 skipped、0 failure/error | 当前候选 HEAD 的真实回执已归档于 `.../l3-workbuddy/`。跳过数未被隐瞒。 |
| 光伏完整 L3 | **运行中；无最终 JUnit 或覆盖结论** | 生产代码改变后的必要最终回归只运行一次；在产出并验证回执以前，不能标记完整 L3 或 L2 覆盖通过。 |

`reports/solar-pv/phase3c-startup-state.json` 的 288 项冻结保护清单已复核：**286 原哈希一致、2 项既存差异 `reports/validate.json`/`reports/validate.md`、0 缺失**；六份用户既有差异文件的 SHA-256 与 P2-4B/C 封存证明全部一致，未暂存、覆盖、清理或提交。L3 运行期间不得改生产、测试、配置或这些用户文件。最终回归完成后还需按 `python -m tooling.solar_pv_regression verify` 真实核对相同 HEAD、受控输入字节、条件和全部 60 个测试 ID，**不得用跨提交旧 JUnit 或仅历史 ID 重叠替代**。

## 4. Phase 3F 依赖判断（未启动）

- **可复用而非已授权启动：** 3D 已证账簿、3E 有来源 NO_DISPOSITION 项目税前/税后现金、同口径项目 NPV、四条回报接线；原价候选回放、来源绑定、序列化及哈希稳定的基础生产者。但本轮只验证了一年期项目税后合成候选，不能推广至全部 25 年配置、权益或 EVENTS。
- **硬依赖：** 3F 的八类扰动必须显式来源、clone 原始输入并独立变更 hash，逐路径重算收入/税/全链现金/IRR/NPV，不得乘最终指标；项目 IRR 先有来源地声明搜索域、数值容差与多根/无根/退化验收；最差年先解决事前范围和正式表示；融资、所有权收付、CFADS/DSCR、LCOE、DATED 现金事件必须分别闭合；EVENTS 交易级排重与税务证据、正式盈亏电价完整根集、两份封存案例输入亦为各自依赖。缺项时不得宣称 Phase 3E PASS 或全面 3F 就绪。
- 本阶段不开发 `scenario_runner`、`sensitivity`、`calculation_graph`，不进入 Phase 3F/3G/4，不 push、部署、发布；完成最终 L3 回执、保护复核及报告收口后停止等待审查。
