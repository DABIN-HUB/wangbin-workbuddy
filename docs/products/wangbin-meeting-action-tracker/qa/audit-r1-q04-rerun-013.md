# AUDIT-R1 Q04 0.1.3 独立 ZIP 复验：FAIL

- product_id `wangbin-meeting-action-tracker`；task_id `t_5a9f3668`；workspace `F:/ideaWorkSpace/wangbin-workbuddy-meeting-action-tracker`；branch `skill/meeting-action-tracker`；测试前源码 commit `5d284a7ef71aea55667b1e322ea3d898372c1c06`，起始 clean。
- 精确未占用新版候选 `dist/wangbin-meeting-action-tracker-0.1.3-skill-candidate.zip`，SHA-256 `7a336890accd132e69deff91a60b4e4cd30b7d7ce144862f778fa6e5023b2a6d`。旧 0.1.1 SHA `5f5f0bc86ca469c89d758010194d8768e27badc96584791495e4b71c8ef745ae`、旧 0.1.2 SHA `a724a682364cef80eb0a64791f6ea447de463c20f0b14bd05aba87c558ba9ffe` 均保持不变；后者历史独立 QA 为 21/26 FAIL，绝不改写为通过。新版 ZIP/侧车清单 SHA、四个唯一安全成员的大小/哈希与当前 packages/skills 源码逐项相等；`ZipFile.testzip()`、`python -m zipfile -t` 均通过；工厂 `validate`、`verify` 当前 active 0.1.3 PASS。`products/catalog.json` active_version 0.1.3 仅代表本地候选指针，版本记录候选路径和 SHA 对应；SKILL YAML name/version 0.1.3、中英显示名与各三条推荐问题、相对脚本和随包参考文件、manifest 中 Python 3.11+ 与 `openpyxl>=3.1,<4`、`python-docx>=1.1,<2` 已核对。包中不携带依赖，目标环境依赖可得性仍未验证。
- 执行 `PYTHONDONTWRITEBYTECODE=1 python docs/products/wangbin-meeting-action-tracker/qa/audit_r1_q04_rerun_013.py`，cwd 产品工作树，**probe exit 0 但业务断言 34/35 符合、1/35 不符**；原冻结 26 案在此 ZIP 上为 26/26，独立新设计 9 案为 8/9。逐案真实输入、完整命令/工作目录、CLI 退出码、stdout/stderr、输入/输出 SHA、四表完整数据、摘要及断言结果见 `qa/audit-r1-q04-rerun-013-results.json`。探针将 ZIP 解压于 wb-quality 专属 scratch，删除 PYTHONPATH，用解压脚本正式 CLI 跑真实 MD/TXT/旧 CSV、上一轮 XLSX、补证 TXT、用户更正；每轮重开四表，错误输入核退出码和无工作簿，旧 CSV/证据哈希前后不变。Python 3.14.9、openpyxl 3.1.5、python-docx 1.2.0 是本机执行环境，不代表 WorkBuddy。

## 新独立反例，阻断本地业务门禁

- 案例 `proposal_deliberation`：旧 CSV T01 接口联调/王工/进行中、已确认截止 2026-11-05；T02 演练培训/李工/待执行。MD 会议内容 **`T01的取消事项仍在讨论，尚无最终决定。`**，用解压后 `scripts/track.py --meeting-file <meeting.md> --project-name 蓝桥演练 --output-dir <empty-out> --previous-tasks <old.csv>`；实际 CLI exit **0**。
- 预期：没有明确取消决议，T01 保持进行中，历史与本次变化不能出现确定取消；未决取消应列为待确认，T02 状态不变。实际：T01 **取消**，`本次新增与变化`及`状态历史`分别记录一次已确认 `进行中→取消`（event_id `EV-f5e760182c5417b2d5ef`），`待确认事项` **0 行**；Markdown 摘要声称“确定变化：T01 取消”，且将未决原句当确定来源。错误使任务被虚假关闭、逾期标成“否”。对照 `positive_cancel_later` 的确切决定与 `negation_modal` 的否定、`proposal_variant` 的另一提议语序已分别通过，故不能用全部取消都待确认掩盖此缺陷。
- 可复现：直接运行上述 probe 后查看 JSON `cases` 中该 id（最终断言 false），或按记录的命令对该真实输入运行 ZIP 解压脚本，再打开 XLSX 的四表和 MD 摘要。初始尝试 34/35 与加强待确认断言后的复跑同为 34/35；后一报告为保留证据。源码 `proposed_status_change` 仅涵盖特定提议和“未/还未…决定”结构，`status_claim` 对裸“取消”形成肯定状态；这是静态定位，不代替实际 CLI 证据。修复需基于整句未决语义及范围，主纪要/补证/用户更正一致；不得修改旧证据或测试预期迁就错误。

## 层级与剩余风险

- L1 **PASS**：完整性、版本/路径/manifest/catalog 静态对应；不能推断平台安装成功。L2 **PASS**：`PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider --basetemp="$TMPDIR/q04-rerun-013-pytest" tests/test_meeting_action_tracker.py tests/test_meeting_action_tracker_audit_r1.py`，exit0，59 passed、1 第三方弃用警告。L3 **FAIL 34/35**，CLI exit0 并不消除业务假取消。L4 真正模型多轮 **NOT_TESTED**；L5 WorkBuddy 安装/实际使用 **NOT_TESTED**；隔离目标环境依赖安装/可得性、第三方许可证及目标平台授权 **NOT_VERIFIED**；相似性平台审核 **NOT_TESTED**；普通 push **NOT_TESTED（QA 失败禁止）**，没有上传/发布。
- 本次属于原 0.1.2 首次新阶段 QA 退回之后的 0.1.3 复验 FAIL；按照本阶段最多两轮由 QA 退回导致的修复/复验，**尚余第二次 QA-return 一轮**。已通知经理卡 `t_ec1150c3`：请仅建立必要的唯一后续定点修复→另卡 QA 链，未闭环前不能放行此 SHA；不用老包测试 PASS 或工厂 PASS 替代独立业务结论。生产源码、包、catalog、历史报告均未改动，本次仅提交 QA 探针/逐案 JSON/本报告。
