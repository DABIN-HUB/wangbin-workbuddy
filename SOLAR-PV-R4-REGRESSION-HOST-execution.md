# SOLAR-PV-R4-REGRESSION-HOST｜执行回执（非发布）

> 仅覆盖 `DABIN-HUB/wangbin-workbuddy` 光伏预可研。软件 QA、用户审阅、专业签审、宿主运行和产品发布分别判定；未完成项不计 PASS。本文件记录 R4 当前可核证的事实，不修改任何 R2/R3 原始回执或冻结财务合同。

## 1. Git 身份与 R3 安全同步

- R4 初始本地主仓库：`F:/ideaWorkSpace/wangbin-workbuddy`，`main / 8a33c2fa96f87673c3b95ee3d02314833c1306bf`；R3 末次生产代码提交为 `65046070e9126989156b925694ac2bdf5c43c672`。
- R4 生产源码未改动；最终 Git SHA 以本报告提交后的读回为准。R3 源码提交与 R4 报告提交不能混称。
- 推送前已检查 remote、提交父链、工作树、光伏范围与远端快进关系；当时 `origin/main=4e1b14092acbf8578e582ece39169682052888e7`。已执行普通 `git push origin main` 并重新 fetch 核对目标 `8a33c2fa96f87673c3b95ee3d02314833c1306bf`。本轮再次 `git ls-remote origin refs/heads/main`，返回同一完整 SHA。
- R3 **Git 源码同步 PASS**；平台上传、安装、审核与发布均没有发生。未 force push、merge、rebase、reset；原有未跟踪 `uv.lock` 保持不动。
- R3 忽略目录中的红绿灯与 QA 回执已增量复制到仓库外私有路径 `F:/ideaWorkSpace/solar-pv-r4-private-evidence/r3-runtime-receipts/`：21 个目录、392 个文件、165576 字节逐文件 SHA-256 一致；清单 `F:/ideaWorkSpace/solar-pv-r4-private-evidence/r3-runtime-manifest.json` 的 SHA-256 为 `c6e2a65e15e82cec0532aa02930529d487f1c0135deac7bb45dc9a953b0efbaa`。**这只是同一 F: 磁盘的本地副本，不是独立磁盘或云备份**；原 `.runtime` 和历史 R2 原件均保留。

## 2. 历史 R2 扩展 QA：原始 XML 逐项核查

原始根：`F:/ideaWorkSpace/solar-pv-r1-preservation-20261117/solar-pv-worktree/.runtime/solar-pv/SOLAR-PV-R2-PRESERVE-QA-HOST/`。历史源码头 `0edef90b5a21bced3305015dae53e50c6e392aa1`。直接解析下列 11 份 JUnit XML 的 `<testcase>`：**829 个互异节点，820 PASS / 4 FAIL / 4 ERROR / 1 SKIPPED**；D 批 suite 属性还包含 4 个未单独序列化的 unittest subtests，不计入 829。早期编排器标记 PASSED 或退出 0 不覆盖 XML 失败结论。

| 批次 XML（相对原始根） | XML SHA-256 | XML 结果 |
|---|---|---|
| `qa-a/run.xml` | `c1cce8468524fda43d5dd9c3dea4d8d2901455909fe132948de70a2eff3fa27b` | 598 PASS |
| `heavy-1/B/result.xml` | `cbc6b0a2afc3ce12747124e6f519d1e1320c8275c06b313cea2e1f8a418ef093` | 8 PASS |
| `heavy-1/C/result.xml` | `0806e225acadc70dbb4dad4dc7c83c0afb6848ee990f4c45616ac21ce9da866d` | 20 PASS |
| `qa-d/all-ten.xml` | `9ff6c224952bd323d8e72349b7c78eb0b0e5e9b1980d6cf033a30afd84989d7e` | 143 PASS |
| `qa-e1/run.xml` | `46ae08d13cd71c81c6177d359a8d27572e4d82d453d8a8844e1087634209a8fd` | 17 PASS |
| `heavy-1/E2/result.xml` | `37a19e4607e33774d96170cce39b914e8966d7ca71253d5cc468b9f8e47be840` | 12 PASS / 1 SKIPPED |
| `heavy-1/E3/result.xml` | `5008ced9af716397487ca2b0172ab62c9f04ee2c44cabe9670ac03f81bb84fc1` | 4 PASS / 1 FAIL |
| `heavy-2/F1/result.xml` | `a06f7e179a78df95f2d8030b77c7dbdb11be4b6352f76f14a2f8af57ca12582e` | 16 PASS |
| `heavy-2/F2/result.xml` | `02fb708bd17675dd6e4b5bd342f021061ef93be8b3818839a59b5db4a10bbc2f` | 1 PASS / 2 FAIL |
| `heavy-2/F3/result.xml` | `f036fdbc129120e505bca75b45341b9ecf967fdd8b6e3dfb04f4eed31e70ebf6` | 1 PASS / 1 FAIL |
| `heavy-2/F4/result.xml` | `5bc7608af928db21352fe8e8940709ec1dba5c104bf656fe5e0ad605321f09fb` | 4 ERROR |

原始执行参数及日志：A 批 `qa-a/commands.txt`、`collect.log`、`run.log`、`source-sha.txt`；D 批 `qa-d/all-ten.command.log`、`all-ten.log`、`source-sha.txt`；B/C/E2/E3/F1/F2/F3/F4 每批 `receipt.json` 的命令、源码头、退出码、日志与 JUnit 哈希，以及 `collect.log`、`pytest.log`。E1 的 `collect.log`、`run.log`、已收集/已执行 nodeid 存在，但缺批次独立命令文件与源码 SHA 文件；所有批次均未分流保存独立 stdout 和 stderr。因此**829 XML 节点结果完整，严格原始流及 E1 批次级来源链 PARTIAL**，不捏造缺失字段。

| 历史状态 | 原始 pytest nodeid（均以 `tests/solar-pv/` 开头） | 原始断言、异常或跳过原因 | R4 定点状态 |
|---|---|---|---|
| FAIL E3 | `test_phase3e_financial_candidate_replay.py::test_b2_independent_vat_loss_income_tax_debt_and_cash` | `Decimal('33064.0000') == Decimal('33940.0')` 断言失败 | 当前 1 PASS；修订合成付款来源及独立税基期望，见 E3 XML |
| FAIL F2 | `test_phase3e_terminal_npv.py::test_no_disposition_has_independent_decimal_cashflow_and_npv` | `ContractError: PROJECT_NPV_LEDGER_INCOMPLETE` | 当前 PASS；原案交易费来源绑定后现金向量闭合 |
| FAIL F2 | `test_phase3e_terminal_npv.py::test_rebound_old_candidate_and_unknown_terminal_date_never_publish_npv` | 同上 | 当前 PASS；同一原因 |
| FAIL F3 | `test_phase3e_break_even_project_npv.py::test_one_candidate_recalculates_original_and_sourced_project_npv` | 同上 | 当前 PASS；原案/候选分别绑定付款来源 |
| ERROR F4 | `test_phase3e_break_even_project_session.py::test_declared_independent_project_has_real_full_chain_root_witness` | fixture setup `ContractError: PROJECT_NPV_LEDGER_INCOMPLETE` | 当前 PASS；Session 原案来源接线后的重算路径闭合 |
| ERROR F4 | `test_phase3e_break_even_project_session.py::test_original_price_is_reused_without_neighboring_fake_price` | 同上 | 当前 PASS；同一 fixture/setup 根因 |
| ERROR F4 | `test_phase3e_break_even_project_session.py::test_cannot_certify_unproven_executable_root_or_legacy_interpolation` | 同上 | 当前 PASS；同一 fixture/setup 根因 |
| ERROR F4 | `test_phase3e_break_even_project_session.py::test_in_place_source_or_control_changes_invalidate_original_cache` | 同上 | 当前 PASS；同一 fixture/setup 根因 |
| SKIPPED E2 | `test_phase3e_candidate_replay.py::test_workspace_rejects_real_symlink` | `Windows symlink privilege unavailable: 22`；原始断言未执行 | 环境门禁仍须独立检查 |

上述异常原始堆栈在各 XML 对应 `<failure>`/`<error>` 文本中；F2/F3/F4 汇聚于旧 `phase3e.py` 的 `PROJECT_NPV_LEDGER_INCOMPLETE` 检查。本轮在当前 R3 HEAD 分别复跑原八个 nodeid：**8 PASS / 0 FAIL / 0 ERROR / 0 SKIP**。`0edef90..8a33c2` 源码 diff 可见 E3 旧参考税基没有扣除明确 `876` 交易费；现行测试在独立 `87600 × 0.01` 预设上扣一次交易费，并断言费用计提、支付、应付账款为零。F2/F3/F4 的旧 fixture 未向需现金闭合的入口提供原案/候选分别绑定的合成付款来源；当前真实入口携带各角色来源后恢复通过，无需再重复修改生产计算或冻结公式。当前专项由执行者复核原始 JUnit，不冒称为另一个独立 QA 角色的全套验收。

## 3. 当前收集集合与实际回归

在 R4 初始 HEAD `8a33c2fa…`、当前 Python/pytest 环境，执行 `python -m pytest --collect-only -q -p no:cacheprovider tests/solar-pv`，退出 0。`5071 tests collected`，逐行提取 5071 个唯一当前 nodeid；将原始 JUnit `classname` 的 pytest/unittest 类路径规范化后，**旧 829 项在当前集合中全部逐 ID 存在**，无历史节点删除、改名或不再适用，新增 4242 个当前节点。集合差异文件及逐节点 `NOT_TESTED` 基线保存在 `.runtime/solar-pv/R4-current-node-collection-01/`：

- `r2-829-nodeids.txt` SHA-256 `a6e575ee960fe4c3b910a6a90f8a26033cf7355bbab8a55ea65e8af7c6f6e27c`；
- `r4-5071-nodeids.txt` SHA-256 `69e9d5873b9bbbaceb2aabb03a81c1191e043c5bb9f6809c0fb14ad687cf2cd0`；
- `r4-4242-added-nodeids.txt` SHA-256 `d307e123778e3bf089440ea059d055048975f55cb3f600f41a0497a384bf70f4`；
- `r4-coverage-baseline.json` SHA-256 `fbaf086b3c5f3f8ffca43eb7ca36948629c15afc88a752ef8b5a2137fddc75bb`。

八个旧失败/错误在 `.runtime/solar-pv/R4-eight-old-nodes-01/` **定向串行执行完成**，以下四批均绑定 `8a33c2fa96f87673c3b95ee3d02314833c1306bf`；每批保留原 nodeid、命令、源码头、UTC 起止、退出码、原始合并日志、JUnit 和 sidecar 哈希，且逐份读回校验日志和 XML 哈希一致：

| 批次 | 起止 UTC（2026-11-18） | 退出 | 新 JUnit 节点 | XML SHA-256 |
|---|---|---:|---|---|
| E3 | 01:02:59–01:51:33 | 0 | 1 PASS / 0 FAIL/ERROR/SKIP | `5d5e164f951a53ecdbd278b4e1bba9dc3392438f4510f9a12dd02f86ba65ac4b` |
| F2 | 01:51:33–02:51:40 | 0 | 2 PASS / 0 FAIL/ERROR/SKIP | `5c4ec4c7838b1b31d6780a5ae195c2abe71fb7031c9e53fc8aa616ba39ffa8c5` |
| F3 | 02:51:40–03:32:37 | 0 | 1 PASS / 0 FAIL/ERROR/SKIP | `9066ab43478db8708f3f222399341fe6571ac43c4c014ecd9dee3d3167250035` |
| F4 | 03:32:37–04:24:53 | 0 | 4 PASS / 0 FAIL/ERROR/SKIP | `a8ce610f0e137d8db65997506927f97258449af3e498a9f629ee2d0021bbf531` |

本轮新节点覆盖矩阵 `.runtime/solar-pv/R4-current-node-collection-01/r4-targeted-coverage.json` SHA-256 `49661bdce4327f4dafbea33d8a6304f98c59dabee9dbc65c044254ecdf55f591`：旧 829 项中当前 8 项已复测通过，余 821 项未在本次八节点批次执行；新增 4242 项亦未纳入此批。**整个当前 5071 集合与旧 829 集合均无新源码全量 JUnit，REGRESSION_TESTS=PARTIAL/NOT_PASSED**，不能由收集退出 0 或历史 135 项限定回执推断全套 PASS。R3 135 项限定回执参见 `SOLAR-PV-R3-MAIN-NPV-CLOSEOUT-execution.md:72-88`；其源码头分批不同，不与本批新运行混算。

## 4. SYNTHETIC 25 年日期来源

`docs/solar-pv/32-dated-cash-event-source.md` 要求独立原始 UTF-8 日期事件 CSV、carrier、来源授权、评价日期及日计数、原始 SHA-256、建设期和运营 1–25 年逐期事件、终期日期事件、账簿逐期精确核对。当前发现的日期 CSV 仅有短运行案例（三条现金事件：建设期、运营第 1、2 年），两案另有 25 年**年度交易费付款合成假设**，不是日期事件源或实际付款凭证。既有两案 canonical 的 `F-DATED-NPV=BLOCKED_MISSING_INPUT`，年度 `F-NPV=CALCULATED`，不得相互替代。

本轮未得到独立于生产年度净现金流、可事先冻结且满足逐期精确核对的两案完整 25 年日期事件金额与日期来源。没有逆向从年度结果构造事件，也没有为追绿而调金额或改变现金计算；**屋顶/地面正例及生产 run_project/CLI = BLOCKED_SOURCE_REQUIRED / NOT_TESTED**。保持 `SYNTHETIC` 范围和真实工程门禁。

## 5. WorkBuddy CH08 原生宿主预检

仓库候选（**不是已安装版本**）：Skill `wangbin-solar-pv-prestudy` / `0.1.3`、Connector `wangbin-solar-pv-cli` / `0.1.2`。已只读检查 `SKILL.md`、`references/host-orchestration.md`、`manifest.json`、`cli.json`、`connector_runtime.py`、`run_ai_chapter.py` 和 `host_session.py`；存在静态 `prepare-r2` 协议。候选 manifest 要求引擎 `wangbin-solar-pv-input==0.3.1`，当前仓库引擎源码声明为 `0.3.2`，需要后续实际包身份确认，不假设兼容。

只读进程检查发现 `WorkBuddy.exe` 与 `WorkBuddyAI.exe`，其程序文件版本分别为 `5.11.3`、`5.9.4`；**没有找到可见客户端窗口**，故未读取客户端 About 或真实 Skill/Connector 详情。两套客户端随附 Python 均返回 `3.13.14`，但这不是已核验的 Connector 托管解释器；随附解释器中目标引擎、文档引擎及相关依赖未找到。**实际已安装 Skill ID/版本/启用状态、Connector ID/版本/运行状态、托管 Python/wheel 来源及 `prepare-r2` 宿主执行均为未核验或 BLOCKED**。

未发送任何模型请求，未使用 Hermes 正文、旧 Word、Python 模板、协议 fixture 或假调用 ID 冒充新宿主输出；屋顶 CH08 和地面 CH08 都是 `NOT_SENT / NOT_TESTED`，CH10/CH16 不解锁。只读预检不是用户对真实模型/附件处理的授权；后续需指定正常可见的目标客户端和已安装候选身份，分别批准有效 canonical、来源/模型/预算、独立新 run 的真实 `prepare-r2`、必要的安装/附件/模型处理。手动 CH08 写作仅在另有明确授权时作为**宿主写作**验证；自动 `prepare-r2→生成→publish→accept→resume→文件读取` 是另一门禁。

## 6. Phase D、F02/F04 与发布门禁

- CH08 已有结构/引用闭合记录，`professional_semantics=NOT_TESTED`；不是本轮真实 WorkBuddy 新正文或专业签审。数值、段落 claims 与来源的完整同运行身份复核须等真实 CH08 可见内容。
- R3 两案 canonical 总状态仍 `PARTIAL`，F04 在两案 manifest 均为 `DRAFT_PARTIAL`；缺失指标不可补零或以年度合成付款假设当作实付。
- 两份历史称为“50 页”的非正式 PDF **当前文件实际各 55 页**。只读 PDF 文本/书签清点：每份 55 页、205 条 PDF 书签、无完全空白文本页；PDF 搜索/复制中的公式与全页视觉尚未完成审核，**F02 正式验收 BLOCKED**。屋顶 PDF SHA-256 `81a069d121b455b072e8def982738d73e8d0f6f0ff922e75995b9a8f4239ab94`，地面 `6ae28fa0603633cc49bb53b8c0177b741795301fddd16b9d58435396ec29bafa`。已有历史回执对 WPS 公式复制/搜索记为阻断；本轮没有把简单 U+FFFD 计数或 PDF 文件存在当作通过。
- 本轮只读核对了两案 manifest 与 canonical 的五项身份：`model_version`、`run_id`、`input_hash`、`source_snapshot_id`、`result_hash` 均一致；F01 DOCX、F03 XLSX、F04 来源工作簿及 F02 PDF 的实际 SHA-256 与各自 manifest 条目一致，F04 条目的五项身份也一致。DOCX/F03/F04 的 OOXML 中均可找到五项原值。**但两案 PDF 第 55 页的 `input_hash`、`source_snapshot_id`、`result_hash` 均因提取文本跨行，原长字符串不能直接全文匹配或被 PyMuPDF `search_for` 命中；删除提取文本中的空白才恢复完整哈希。**这只是文本层身份抽查及一个明确的复制/全文搜索缺口，不能代替公式复制、逐页视觉与数据语义验收。manifest 仍写明 `VISUAL_REVIEW=NOT_TESTED`、`DOCUMENT_CONTENT_REVIEW=NOT_REVIEWED`、`FOUR_FILE_GATE=NOT_FORMAL_ACCEPTANCE`；四件套正式门禁未通过。
- 40 项用户审阅仍 `PENDING`；工程原始资料、合同裁定、专业签审、正式 F02、四件套、平台发布均未闭合。`BLOCKED_ROOT_SET_COMPLETENESS_UNPROVEN` 仍有效，根见证不是全部根的认证；`financial_ledger.py` 中零债务比例与非零计划/期初证据矛盾的上游裁定仍待明确，不擅改冻结规则。

## 7. 仓库卫生、本地候选与最终读回

`python tooling/solar_pv_workspace_hygiene.py --check` 退出 0；当时 1299 个跟踪文件/614933171 本地字节，641 个报告文件/589424330 字节，唯一未跟踪文件 `uv.lock`（受保护、未修改）。本轮没有核实可净删的跟踪光伏原件，净删除 0、释放空间 0；R2/R3 原始证据保持原样。`dist/` 受 `.gitignore` 忽略，候选 Skill `0.1.3` 和 Connector `0.1.2` ZIP 及 SHA-256 sidecar 对照一致、ZIP CRC 检查无错误；只证明本地包完整性，不证明平台运行。`dist/` 另存两份有明确身份的历史 0.1.3 ZIP，本轮不盲删。

最终源码/报告 SHA、暂存区与工作区状态必须以本报告提交后的只读验收回执补充；报告提交不允许回填成生产源码 SHA。**本任务最终总门禁不是全部完成**：R3 Git 同步已通过；旧 R2 结果可追溯，当前软件扩展 QA 未证明；两案日期来源和真实 CH08 宿主写作阻断；F02/F04、人工审阅、专业签审及平台发布分别待办。下一轮须先读取每批原始 JUnit 并完成未测集合、取得独立日期来源与明确 WorkBuddy 授权，再分别申请后续门禁；不推进 Phase E/F/G。
