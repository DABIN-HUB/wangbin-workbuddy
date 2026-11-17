# SOLAR-PV-R3-MAIN-NPV-CLOSEOUT execution report

- 任务编号：`SOLAR-PV-R3-MAIN-NPV-CLOSEOUT`
- 范围：仅 `DABIN-HUB/wangbin-workbuddy` 光伏预可研计算与报告消费链
- 执行时间：2026-11-17（UTC 记录见各回执目录）
- 初始审阅基线：`main / 4e1b14092acbf8578e582ece39169682052888e7`
- 最终本地源码：`main / 65046070e9126989156b925694ac2bdf5c43c672`
- `origin/main`：仍为 `4e1b14092acbf8578e582ece39169682052888e7`
- 同步状态：已完成本地提交，**未 push**；未执行 force push、merge、rebase、reset 或发布
- 工作区保护：未修改未跟踪的 `uv.lock`；未导入旧 bundle，未清理历史 R2/R4–R13 原件

## 1. 本轮本地提交

按独立修复批次提交，均为本地 `main` 提交：

1. `67d161cf` — `fix(solar): preserve exact dated cash ledger sums`
2. `c551707` — `fix(solar): pin project session publication identity`
3. `056185a2` — `fix(solar): distinguish no-debt DSCR applicability`
4. `6504607` — `fix(solar): keep DSCR report state debt-aware`

最终工作区除受保护的未跟踪 `uv.lock` 外无未提交修改；`git diff --check` 通过。

## 2. 已完成的生产代码修复

### 2.1 日期现金事件精度

`calculation/dated_cash_events.py` 不再使用固定 85 位 `Decimal` 上下文对期间事件直接求和。现在根据实际输入 Decimal 的小数尺度统一缩放为整数系数后精确求和，再还原 Decimal。

保留并验证了以下边界：

- `A = Decimal("9" * 79)`、`epsilon = Decimal("0." + "0" * 77 + "1")`、`-A` 的抵消残差 `1E-78`；
- 正负抵消和多种事件排列；
- 原有 `0.01` 金额路径；
- 正确账簿对账通过、精确残差不为零时拒绝；
- 未放宽容差、未按分取整、未删除小额事件、未补差额、未修改 NPV/IRR 公式。

红灯与绿灯均保留：

- `.runtime/solar-pv/R3-dated-precision-red/`：固定精度实现退出码 `1`，证明原缺陷；JUnit SHA-256 `33475e6b3bf3925334fd6a2890220eac538e07001e2f5001edfd76e02dbf49d4`。
- `.runtime/solar-pv/R3-dated-precision-green/`：退出码 `0`；JUnit SHA-256 `f950a5e793a626aa49a0223bc5b48d26758c58d2e090e6e3dfc9f285e20ca5fb`。
- `.runtime/solar-pv/R3-dated-full/`：退出码 `0`；JUnit SHA-256 `bdda8f34561f92749fc811c2cae292bb218298ef7557d6eaae007ed6803452ea`。

红绿灯回执的历史源码头记录为 `4e1b140`；之后的最终日期专项回归在 `056185a2` 上重新执行，日期生产代码从 `056185a2` 到最终 `6504607` 未变化。

### 2.2 原案/候选交易费来源隔离与 NPV/session

已保留并复验此前的原案/候选交易费来源字节透传：

- 原案与候选来源分别从入口进入 NPV、Session、3D 账簿、终期重算和 3E；
- 不自动从另一角色继承来源，不把缺失付款来源当作零；
- Session 原案来源身份进入缓存指纹；
- Session 现在比较内存中的原案 3C/3D/3E 结果与已发布 `result.json` 内容，防止公开对象被原地修改后重新封存出磁盘不存在的结果哈希；
- `_EXECUTOR_FILES` 已纳入 `trading_fee_payment.py` 与 `schema/trading-fee-payment.schema.json`；
- 原价复用、候选来源缺失/错配、缓存篡改和依赖指纹负例均保留阻断行为。

### 2.3 DSCR 状态与报告消费

读取并依据有效 Catalog `solar-pv-formula-definitions/1.0.1` 的 `F-DSCR` 定义：

- 明确无融资且证据一致：`NOT_APPLICABLE / NO_DEBT`；
- 有债务但某偿债期分母为零：仍为 `UNDEFINED / ZERO_DEBT_SERVICE`；
- CFADS 缺失独立保持阻断，不因 DSCR 不适用补零。

`phase3e.py` 的 `NOT_APPLICABLE` 判定要求债务比例为零、`NO_DEBT_DECLARED`、债务计划为空、期初本金/应付利息为零，以及债务向量和账簿债务字段均为零；不能仅凭零分母得出无债务结论。

`report_export.py` 不再仅凭债务比例为零就把有显式计划或期初债务的结果解释为无债务；报告状态回归已覆盖无债务和“零比例但有债务计划”的矛盾输入。

仍保留的边界事项：`financial_ledger.py` 中已有债务比例与显式计划组合的上游处置规则仍需独立合同裁定；本轮没有擅自改写冻结账簿定义，也没有重写旧 R2 canonical/manifest。旧 R2 canonical 中的 `UNDEFINED/ZERO_DEBT_SERVICE` 是历史结果身份，未被本轮覆盖；新 `calculate_phase3e` 合成结果使用新运行身份。

## 3. 最终限定 QA 回执

所有回执均保存源码头、起止 UTC、退出码、JUnit XML 和 XML SHA-256。XML 节点数按 `<testcase>` 统计，不把编排器输出或 subtest 文本冒充 XML 节点。

| 批次 | 回执目录 | 源码头 | XML 节点 | 结果 | 起止 UTC | JUnit SHA-256 |
|---|---|---|---:|---|---|---|
| 日期精度 | `R3-final-qa-dated` | `056185a2` | 20 | 20 PASS，0 FAIL/ERROR/SKIP，退出 0 | 11:53:53–11:53:55 | `df728313769a15758721909f8362ee07b18dafc2b2c209c092b02728edc48fb2` |
| DSCR 计算状态 | `R3-final-qa-dscr` | `056185a2` | 19 | 19 PASS，0 FAIL/ERROR/SKIP，退出 0 | 11:53:56–11:54:12 | `140c7c46fab0e2cc5bccd5f733ac8df2146761c11a8d46552c782e54e329920a` |
| Session 新增负例 | `R3-final-qa-session-negative` | `056185a2` | 7 | 7 PASS，0 FAIL/ERROR/SKIP，退出 0 | 11:54:12–11:54:15 | `911ef787e7788b041e6059b4e81baec00105ade0a559bc30dcedd44c30c2fed7` |
| 报告 DSCR 消费 | `R3-final-qa-report-dscr-final` | `6504607` | 26 | 26 PASS，0 FAIL/ERROR/SKIP，退出 0 | 12:05:56–12:06:33 | `a2eccafe463544dbcdc169594d59c603be16b2c4b670a5b00303b7a9680b3d62` |
| 交易费来源/转发 | `R3-final-qa-fee-source` | `6504607` | 41 | 41 PASS，0 FAIL/ERROR/SKIP，另 4 个 subtest PASS，退出 0 | 12:06:56–12:10:08 | `efb295cee0579a3094bcce6b361e9aeef331be0dcf8b1c985bc3d7739648b1a0` |
| Terminal NPV | `R3-final-qa-terminal-npv` | `056185a2` | 3 | 3 PASS，0 FAIL/ERROR/SKIP，退出 0 | 11:53:29–13:10:42 | `5d345c0a11c21ae5613e2e3cdb291cbb184c27ec5fd555e0065a2152695f5fee` |
| One-price project NPV | `R3-final-qa-one-price-npv` | `056185a2` | 2 | 2 PASS，0 FAIL/ERROR/SKIP，退出 0 | 11:53:31–12:53:07 | `da4a55d806f9f3f9423f32873af5d81ee65cfb32d206bd99ec6f2480e0136682` |
| Financial candidate replay | `R3-final-qa-financial-replay` | `056185a2` | 6 | 6 PASS，0 FAIL/ERROR/SKIP，退出 0 | 11:53:30–13:02:01 | `254db5f8d3e42d040f0526d73503c587f584aca35195a2a5b5f82c0df6fd0610` |
| Project NPV Session 全量 | `R3-final-qa-session` | `056185a2` | 11 | 11 PASS，0 FAIL/ERROR/SKIP，退出 0 | 11:53:31–13:05:29 | `93be118ba7a112d708717eca4ee1137915d5d09a34f2885b54fcf4495fb80379` |

`056185a2` 到 `6504607` 之间只修改了 DSCR 报告消费文件和对应报告回归文件；日期、NPV、Session、交易费来源及 replay 生产目标文件均无差异，因此绑定 `056185a2` 的长批 QA 对这些目标仍是同一源码内容。最终 `6504607` 上另外执行的报告和交易费来源专项已覆盖新增报告消费修改。

## 4. 未完成与不得升级的结论

以下结论保持原门禁，不因本轮限定 QA 变绿而升级：

- 日期来源、交易费来源和 sourced project NPV 仍限于 `SYNTHETIC`；真实工程资料缺失，真实工程日期来源验收仍 `BLOCKED`。
- F04 仍为 `DRAFT_PARTIAL`；非正式 PDF 抽查不足以升级为正式 F02。
- `BLOCKED_ROOT_SET_COMPLETENESS_UNPROVEN` 仍保留；根见证不等于完整根集合证明；本轮没有新增根求解器，也没有完成保本电价认证。
- 用户 40 项审阅仍为 `PENDING`；专业签审、宿主模型、Skill→Connector、文件回传闭环无新回执。
- 不把合成正例、局部测试通过、编排器退出 0、PDF 检查或自动核对升级为真实工程、人工签审、正式交付或产品发布 PASS。
- 历史 R2 扩展 QA 的独立结果仍保持：829 个 XML 节点中 820 PASS、4 FAIL、4 ERROR、1 SKIPPED；本轮新回执没有覆盖或改写历史 XML。
- 本轮没有安装、替换、上传、模型调用、平台上架或发布授权。

## 5. 交付与停止状态

软件整改和限定回归已在本地 `main` 收口，最终 SHA 为 `65046070e9126989156b925694ac2bdf5c43c672`。代码仍只在本地，未推送；产品发布状态仍为未发布，下一步若要推送或解除人工/真实工程门禁，必须取得新的明确授权和相应外部回执。
