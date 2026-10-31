# Phase 3E 专项收口：冻结依赖与候选版本复核

## 身份、范围与结论

- 起始分支 `main`，HEAD `1be9a32a937a2f6ea378842e7ef81221041fa1fb`；本轮已验证的生产代码及针对性回归提交为 `610e8b3af28897bc4917f4c140c1fd73f1be9104`。本报告与机器证据的提交将成为最终 HEAD；它自身的 SHA 不能预写在其提交内容中，提交回执及交付消息须记录实际最终 SHA。未 push。
- 有效定义 `solar-pv-formula-definitions/1.0.1`，哈希 `617a2e9d314c095bd2ec893939c930a2323be6fd7805da12bf6d6fdd70274808`；Catalog 89 公式、469 字段、281 绑定。未编辑冻结资料、D2 Schema、Phase 3B/3C/3D 代码及两个封存案例。
- **最终门禁仍为 `PHASE3E = PARTIAL/BLOCKED`；不得进入 Phase 3F 或发布。** 候选修复后的两个项目均为 26 期间、21 指标：`CALCULATED 0 / UNDEFINED 1 / BLOCKED_MISSING_INPUT 20 / NOT_APPLICABLE 0`。与此前 `1/1/19` 的差异来自 `F-CFADS` 以前将缺失的合同调整向量隐式补成零；不是通过增加共同资金覆盖门槛阻断。DSCR 中已有正债务服务期，但第 14～25 运营年零分母，整条向量报告 `UNDEFINED/ZERO_DEBT_SERVICE`；正债务服务期另需有效 CFADS，不能声称其比值已核验。
- 机器矩阵 `phase3e-closeout-candidate-evidence.json` 包含每案 21 行冻结表达式、直接操作数、实际状态、原因、来源哈希和 26 期间证明；它基于**原封存 Phase 3D 结果**。CLI 另从案例输入、D2、原 Phase 3C settlement 重新计算 Phase 3D，Phase 3D 的结果哈希和年度账簿相同，但 `run_id` / `created_at` 与封存 JSON 不同，不能把封存结果的 Phase 3E 输出哈希与重算结果直接要求相等；相同重算来源的 API/CLI 逐案哈希一致，见 `phase3e-closeout-cli-verification.json`。

## 21 条公式：直接依赖与两案核查

以下“缺”表示冻结公式的实际直接操作数或可复核上游结果未提供；对两个案例结论相同，不能用另一公式的独立缺口或四笔付款瞬时覆盖状态代替。每案 21 行的冻结式、字段、原文位置、历史/当前状态、阻断原因、来源与修复权限见 `phase3e-closeout-candidate-evidence.json`、`phase3e-closeout-dependency-matrix.json`，实施在 `financial_metrics.py` / `phase3e.py`。表中 `B` = `BLOCKED_MISSING_INPUT`，`U` = `UNDEFINED`。**内核有 21 个可调用入口、若干独立 Decimal 正常值断言，但不是每条都有独立数值比较；项目级 21/21 数值验收不成立。**

| 冻结 ID | 屋顶/地面 | 直接依赖核对、缺口或原因 | 错误全局传播 |
|---|---|---|---|
| F-PROJECT-CASH-FLOW | B/B | 3D 收益、运营现金费用、项目税、资本收付与建设期营运资金占用、末年回收有账簿；项目终期现金 `finance.project_terminal_cash` 无来源。建期无“释放”字段符合 3D 建设行结构，不再误标为额外缺口。 | 无；与股东、dated 事件无关 |
| F-PROJECT-PRETAX-CASH-FLOW | B/B | 项目现金流阻断；所得税付现由 3D 可核，不把股东事件当依赖。 | 无 |
| F-EQUITY-AVAILABLE-CASH-FLOW | B/B | 权益终期现金、融资本息费/权益营运资金逐期证据不完整；非“必须先有实际分红”。 | 无 |
| F-EQUITY-INVESTOR-CASH-FLOW | B/B | 实际股东出资、分配、退出事件缺失；不能把可用现金直接当分红。 | 无 |
| F-CASH-FUNDING-BALANCE | B/B | 缺主体可证明的逐期期初非受限资金、权益可用现金与真实投入/分配；D2 合成 `cash.opening_cash=0` 不证明银行余额。 | 无 |
| F-NPV | B/B | 年度项目现金流缺终期现金来源；项目折现率字段存在。**不要求 dated events 或股东分配。** | 无 |
| F-DATED-NPV | B/B | 有日期的现金额、事件 ID 与年分数缺失；年度 NPV 不可替代。 | 无 |
| F-NOMINAL-REAL-RATE | B/B | 项目名义折现率 `finance.project_discount_rate` 与 `finance.inflation_rate` 存在，但公式直接要求 `finance.real_discount_rate`、`finance.general_inflation`；禁止把名义率冒充实际率。 | 无 |
| F-IRR-PROJECT | B/B | 3D 已有 D2 IRR 搜索域；项目完整现金流仍缺；不要求股东事件或投资目标。 | 无 |
| F-IRR-EQUITY | B/B | 需真实权益投资者现金流；不可用项目现金流冒充。 | 无 |
| F-CUMULATIVE-CASH-FLOW | B/B | 完整项目现金流缺。 | 无 |
| F-STATIC-PAYBACK | B/B | 依赖完整项目现金流确认首个回收期及前期累计值；不能由截断现金流推算。 | 无 |
| F-DISCOUNTED-CUMULATIVE-CASH | B/B | 完整项目现金流缺；折现输入与期间需匹配。 | 无 |
| F-DYNAMIC-PAYBACK | B/B | 折现累计现金流及首次回收期不具备。 | 无 |
| F-LIFECYCLE-COST | B/B | 项目终期回收、完整成本及营运资金期间边界缺；不能把账面余值算现金。 | 无 |
| F-LCOE | B/B | 依赖上一行完整生命周期成本和交付电量/适用折现口径；上游成本阻断。 | 无 |
| F-CFADS | B/B | 两案已提供 `finance.cfads_definition` 与 D2 `cfads.method`，且 3D 有经营付现、权益税、资本付款；**冻结操作数 `debt.cfads_adjustments` 未提供有来源的期间值**，旧代码隐式填 `[0]` 已纠正；不能称合同 CFADS。 | 无；与项目终期、dated 事件无关 |
| F-DSCR | U/U | 3D `debt_service_due` 在运营年 14～25 为零，故整向量零分母未定义；运营年 1～13 的协议 CFADS 尚缺，不能称 DSCR 已计算。 | 无 |
| F-BREAK-EVEN-PRICE | B/B | 需有价格搜索域上的完整价格→现金流→NPV 重算链，不能把线性样本插值称合同级全链重算。 | 无 |
| F-WORST-CASH-YEAR | B/B | 要在完整现金流的明确年份范围取最小值；缺终期期间。 | 无 |
| F-INVESTMENT-HURDLE-GAP | B/B | 用户投资目标 `decision.target_metric` 不存在；不影响普通项目 IRR/NPV。 | 无 |

**校核边界：** `F-WORST-CASH-YEAR` 现返回原年份标签；年度项目现金流与日期事件不等长时拒绝静默截断；带标签的并列年度向量按键对齐；静态/动态回收期不再接受超过财务期限或尚未真正回收的年数；建设行不再误判缺少不存在的营运资金释放事件。`phase3e.py` 曾将不存在的 3D 字段当零、把名义率映射为实际率、把合同调整当零、把所有单位标成 `CNY`，现按实际冻结操作数与 Catalog 单位记录。已提供 D2 方法身份不等于合同调整量有来源。历史 `phase3e-numerical-verification.json` 所列 21 项“NUMERICAL_VERIFICATION_PASS”不是 21 项独立数值比对或项目验收，本报告不沿用该判断。

**独立复核确认的未关闭内核缺陷（保持 BLOCKED）：** `F-IRR-PROJECT`、`F-IRR-EQUITY` 目前通过网格异号寻找根，偶重根可能漏报（现金流 `[1,-2,1]` 在含 0 的搜索域内将 `r=0` 误报 `NO_ROOT`）；全零现金流的现有 `ALL_ZERO_CASH_FLOW` 也未完全匹配冻结的不可判定语义。`F-BREAK-EVEN-PRICE` 内核仍依赖样本间线性插值，不能代表冻结要求的价格变化后全链重算；价格残差与电价容差混用，例如价格 0/10 对应 `-1e-20`/`9e-20` 时可能提前在 5 停止，真实零点为 1。两端零现金流的连续根域也没有完整表示。修复上述根枚举、价格全链关键方法或结果契约语义需重新确认冻结边界，**本轮未擅改这些关键方法或 Schema，不得声明全部 21 内核数值通过**。`F-CFADS` 的项目营运资金与全部资本支出也不能仅凭账簿认定与协议储备及强制资本支出同义，仍需有来源的合同口径。权益可用现金不直接要求分红，当前笼统的终期阻断原因不能被解读为“缺分红”；DSCR 年 1～13 有正分母但 CFADS 未核验。

四笔设备更换付款（两案的 `2037-06-01` 各 190,000 元、`2040-06-01` 各 720,000 元）保持 `INDETERMINATE`，本轮不重做资金瞬时覆盖；不作为其他公式的共同门禁。需要用户提供终期可验证现金回收、股东实际收付、日期事件、主体非受限期初/结余、明确实际折现/通胀口径、用户投资目标及有来源的偿债协议 CFADS 调整/全链价格输入；未把缺口自动变为新产品需求。

## 候选运行与回归

- 原封存 Phase 3D 结果 API（`validate_result` 成功）：屋顶哈希 `5b00f6f1ab1bd7df8fb27ca068d41c80bdac9a1b50668e2b159f12f0a3ef8dbe`；地面 `ee6f20a1812f6db694762b6eaf3674b7dd6237db67ebe418638982c956695673`。两案各 20 B / 1 U、0 数值成功；与 `phase3e-closeout-candidate-evidence.json` 一致。
- 两案例真实 CLI：`python services/solar-pv-engine/solar_pv.py --workspace <scratch> phase3e --input <case>/input.json --methods <case>/methods.json --settlement <case>/settlement.json --output <case>/final-v2`，两次退出码 0；屋顶重算哈希 `332a952e523758a9806f6ed0bb42bcda197adad2c2561bab68c19d15c7e5bf60`、地面 `a95974ebac355493eba5b5674462ce45ad87dbe7d7de8bad96ff1a451519723d`。各自 sidecar = JSON 内哈希；用**同一**输入、方法及 settlement 重算 API 时哈希逐案相等。原封存 API 与 CLI 重算因运行元数据不同而哈希不等，不应称两者一致。
- 定向内核 `python -m pytest tests/solar-pv/test_phase3e_financial_metrics.py -q`：17 passed；`python -m compileall -q services/solar-pv-engine/src/wangbin_solar_pv` 返回 0；三个本轮文件的 `git diff --check` 返回 0。内核定向回归通过不等于上节未闭合的数值门禁通过。完整光伏回归的候选版总数在下节待机器结果核定。
- **最终光伏完整回归**：`python -m pytest tests/solar-pv -q --junitxml=C:/Users/wangbin/AppData/Local/hermes/cache/scratch/phase3e-solar-final.xml` 单次完整运行，退出码 **0**。JUnit 起点 `2026-10-31T10:34:37.723518+08:00`，以其 `5428.500 s` 计算的结束约为 `2026-10-31T12:05:06.223518+08:00`；收集并执行 **4092 个不同测试 ID**，集合完全一致、重复 0、漏测 0、额外 0；**4086 passed / 0 failed / 0 errors / 6 skipped**。历史单次 420 秒工具超时及本轮因源码继续修复而终止的两次预备运行均未计入。所有 6 项跳过均因 Windows 符号链接权限：`test_cli.py` 的 file/ancestor/workspace 各一、`test_parser_security.py` 的 file/root 各一、`test_timeseries_bundle_security.py` 的 symlink_bundle 一项；完整 ID/理由见机器证据。全年 8760/8784 小时及 35040/35136 时段的大时序测试没有缩小或排除。持久化文件：`phase3e-closeout-solar-junit.xml`、`phase3e-closeout-solar-test-ids.txt`、`phase3e-closeout-regression.json`。
- **最终旧 WorkBuddy/Expert 回归**：`python -m pytest tests --ignore=tests/solar-pv -q --junitxml=C:/Users/wangbin/AppData/Local/hermes/cache/scratch/phase3e-workbuddy-final.xml`，退出码 **0**，114 个收集 ID 与 JUnit 114 项一致、无重复/漏测；**109 passed / 0 failed / 0 errors / 5 skipped**。5 项均因本机 Windows 符号链接不可创建，分别在 inventory、product_factory（两项）、security、tender_analyzer 测试中；不计入通过。持久化文件：`phase3e-closeout-workbuddy-junit.xml`、`phase3e-closeout-workbuddy-test-ids.txt`、同一汇总 JSON。
- 两次完整回归对应的生产源码 SHA-256 分别为 `financial_metrics.py`=`ab9820b15b0693e88aa7a76861fe00419c96703a820c548d2bb6a9faee7225c6`、`phase3e.py`=`220c6e187d46cf9f47b4f15bd8dc85b69a6527771634256921a61cde67d9c94b`；定向测试源码 SHA-256 为 `f0e62688bce795f33fce989be1b914f76c97aab104e1ccd5c50954842c95aeb8`。相同文件的 `compileall` 退出 0、三文件 `git diff --check` 退出 0。扫描 12 个本轮代码、测试、报告及证据文件，凭据赋值模式命中 0；不将模式扫描当作绝对安全保证。
- **保护基线与 Git**：288 个文件 286 匹配，`reports/validate.json` 与 `reports/validate.md` 两个原有偏差，0 缺失。六个既有差异文件的审查前 SHA-256：`SKILL.md`=`8a5ee4eb54a4f6a08d3ab7cccf792c12d5f01ab3fb4ab0de8dc926149087a945`；`manifest.json`=`0a9459ab33f0f3bbc1c538535b994218e6ad92792901a39c3e4e94eaf777762b`；`products/catalog.json`=`d74f3fa9f00184ee64f8452862958c3ef11f7848378ed42657e4b5fbc91def27`；`reports/workbuddy-upload-list.md`=`6d0df16f21a4cf7a3a87eef1b90fb2f7d26fd1457f124066707281f9ff0ec586`；`reports/validate.json`=`42765dae553254369311f3d4e7d2d3ab6f3cf0f8858a1c0e587debfea809d1ba`；`reports/validate.md`=`2c3f7cd41671f2af1cd9f5688ae4e3779d92390260cdb43299457bcedb2060e3`。代码提交仅显式暂存两生产文件与一项针对性回归；六文件未暂存、未修改。证据提交后再次检查其 SHA 和 Git 范围。

**最终结论：** 当前回归集合虽然完全通过，项目冻结必需输入仍缺、IRR 根枚举与盈亏电价全链方法的独立数值验收未关闭、合同 CFADS 口径未证实，因此 **`PHASE3E = PARTIAL/BLOCKED`**，不具备进入 Phase 3F 条件；不是将四笔付款 `INDETERMINATE` 外加为所有公式的门禁。后续需用户确认原冻结所需的有来源终期现金、股东收付和日期事件、主体非受限期间资金、实际率/通胀、投资目标与合同级 CFADS 口径，以及关键方法的冻结范围核准。不得以缺失自动置零、补造合同或提高 CALCULATED 数量替代验收。

**后续权限边界：** 本轮仅本地提交允许范围文件；不 push、不部署、不上传、不修改资金、公式、字段、绑定、方法 Schema 或其他阶段。最终 HEAD 与新增证据提交以真实 Git 回执为准。
