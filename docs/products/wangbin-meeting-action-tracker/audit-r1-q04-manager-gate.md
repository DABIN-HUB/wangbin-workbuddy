# AUDIT-R1 Q04 本地候选经理门禁与缺陷矩阵

- `product_id=wangbin-meeting-action-tracker`; `task_id=t_ec1150c3`; `workspace=F:/ideaWorkSpace/wangbin-workbuddy-meeting-action-tracker`; `branch=skill/meeting-action-tracker`; `idempotency_key=six-skills-audit-fix-r1:wangbin-meeting-action-tracker:0.1.1:MTG-F01-F05:manager-gate`。
- 权威修复授权：`C:/Users/wangbin/AppData/Local/hermes/composer-pastes/pasted_content_2026-11-07_00-32-22-639_d8751e.txt` §09、§12–20；V2 冻结规则 `requirements.md` §MTG-01–09 及其审查增补，`input-output-contract.md`、`acceptance-cases.md`。矩阵中“关闭”只表示列出的本地 L3 用例通过，不代表开放域自然语言、平台或许可通过。
- 历史：原 0.1.1 不同覆盖集 47/47 PASS 保留；本轮独立旧包基线 `qa/audit-r1-q04-baseline.md` 为 7/33 符合、26/33 失败。新阶段初版 0.1.2 QA `t_674ba6f3` **21/26 FAIL**，一次定点返工后 0.1.3 QA `t_5a9f3668` **34/35 FAIL**；第二次且最后一次定点返工后 0.1.4 独立 QA `t_1f081465` **42/42 PASS**（此前35案全过+独立变体7案）。旧失败版本的判定和 ZIP 一概保留，不能用最后一次 PASS 改写历史。

| 缺陷 / V2 冻结规则 | 0.1.1 基线真实输入 → 实际 L3 结果 | 正确预期 | 根因与修复位置 | 0.1.4 独立用例 / 实际输出证据 / 本地结论 |
|---|---|---|---|---|
| MTG-F01 / MTG-01、03–05、08 | 旧 T01 进行中；`T01 不取消，继续进行中。` → T01 错取消；`T01 不是已完成，仍在进行中。` → 错报完成；`明确决定取消T01。` 连写又漏定位。0.1.2 还把 `T01不会取消，仍在进行中。` 和 `提议取消T01，目前还未拍板。` 当确定取消；0.1.3 把 `T01的取消事项仍在讨论，尚无最终决定。` 确定取消。 | 否定/提议/未决保持原状态且必要时待确认；明确当期取消应真实迁移；否定范围只限对应任务。 | 旧 `locate` 的 Unicode 邻接与 `apply/status_claim` 关键词作用域不足。首次修复 `t_d3023ec6`、返工 `t_d82ecc21`，末轮 `t_f19037b8` 修 `packages/skills/wangbin-meeting-action-tracker/scripts/track.py` 的未决讨论、否定、任务子句识别；测试 `tests/test_meeting_action_tracker_audit_r1.py`。 | `qa/audit-r1-q04-rerun-014-results.json`：35案复跑及独立 `unresolved_synonym`、`unresolved_continuing`、`unresolved_exact_variant`、`scoped_mixed`、否定、提议、正式表决；正式解压 CLI 及四表回读 T01 保持进行中/仅待确认，T02 的独立完成不受牵连，正式表决使 T01 取消并留来源；范围内 PASS。复杂跨句语义仍有残余风险。 |
| MTG-F02 / MTG-01、05 | `新增任务：接口测试，由张三确认负责，截止2026-11-10。` → 旧包生成任务和日期却丢负责人；赵敏、小王、Alex 变体亦丢，李工可识别。 | 已明确分配则保留姓名、期限和来源；候选建议不得冒充本人接受。 | 旧 `owner` 姓名尾缀约束；首次开发 `65657b3fb5cd1a5ec342ac7dcbb3a0a642863c8b` 修 `scripts/track.py`、冻结合同补全，0.1.4 源码继承。 | `qa/audit-r1-q04-rerun-014-results.json` 复跑原 35 案中姓名/分配对照；四表/摘要回读、负责人及确认状态符合 QA 独立断言；范围内 PASS。 |
| MTG-F03 / MTG-06、07 | `会议日期：2026-11-06。T01 截止明天。` 与 `2026-11-06项目例会。T01 截止明天。` → 旧包未解析 11-07；无会议日或双会议日时甚至改旧已确认期限状态。 | 唯一明确会议日换算为 2026-11-07；无/冲突基准保留旧期限及已确认属性并单列待确认，不使用机器日期。 | 旧会议日提取依赖词序；初版开发 `65657b3fb5cd1a5ec342ac7dcbb3a0a642863c8b` 改 `scripts/track.py`，0.1.4 继承。 | 最终 JSON 复跑原日期、无/冲突基准和日期平移对照；正式 CLI 输出 XLSX 四表与摘要符合独立断言；范围内 PASS。 |
| MTG-F04 / MTG-02、04 | 无旧表 `张三负责接口测试，截止2026-11-10。` → 旧包任务表空，却报“无法唯一定位旧任务”。 | 明确无“新增”前缀行动项仍建稳定 ID；纯讨论不变成确定行动。 | 旧新任务识别依赖“新增”；初版开发 `65657b3fb5cd1a5ec342ac7dcbb3a0a642863c8b` 改 `scripts/track.py`，0.1.4 继承。 | 最终 JSON 复跑无前缀行动项/纯讨论/明显新增的独立案，四表重新打开；范围内 PASS。 |
| MTG-F05 / MTG-02–05、08、09 | 旧包 `--correction` 对 T01 期限/负责人改动漏定位；0.1.2 无旧表 A/Maya/03-06、B/陈琳/03-07 两项错误合并为一项，重导入和调序衍生失败。 | 各独立新任务不合并；重导入无重复任务/事件；更正只更新对应 ID，历史、四表和摘要一致。 | 初版纠正任务定位和跨轮事件；返工 `t_d82ecc21` 修 `scripts/track.py` 的 `recent_new` 错误回填，末轮保留。 | 最终 JSON 复跑双任务、重导入、调序、更正/补证与四表摘要；对应两个独立任务、其他任务不被覆写，逐案业务断言符合；范围内 PASS。 |

## 产物与可重核命令

- 初版 0.1.2 `a724a682364cef80eb0a64791f6ea447de463c20f0b14bd05aba87c558ba9ffe`；返工 0.1.3 `7a336890accd132e69deff91a60b4e4cd30b7d7ce144862f778fa6e5023b2a6d`；旧基线 0.1.1 `5f5f0bc86ca469c89d758010194d8768e27badc96584791495e4b71c8ef745ae`；新 0.1.4 ZIP：`F:/ideaWorkSpace/wangbin-workbuddy-meeting-action-tracker/dist/wangbin-meeting-action-tracker-0.1.4-skill-candidate.zip`，SHA-256 `8b45ac776227db6128f6e6c60e2f345604e63fbb52e693b4bd3dadccb2a45193`。
- 0.1.4 sidecars 为同目录 `.zip.sha256`、`.zip.manifest.json`。解压成员且只有四个：`wangbin-meeting-action-tracker/SKILL.md` (`fc7e1201a92745ed933c9008f288336d4bb614adc7d48a077df8983b589b8d7b`)、`manifest.json` (`dfda67d36bfff59c49eeb91339867f2382836761e659ca3adeb4f5ca355007b0`)、`references/usage-and-contract.md` (`0bee61a67af53a7f135ce0574e6239ba954c531d0e2d4af568ee7fe4a1f99e59`)、`scripts/track.py` (`fede566de1bef5f08da37b55a08042dceb4f9e3e04092ca66f21b21b23315ee0`)；实算包成员与源码及 sidecar 的哈希相同。`python -m zipfile -t dist/wangbin-meeting-action-tracker-0.1.4-skill-candidate.zip` exit0，`(cd dist && sha256sum -c wangbin-meeting-action-tracker-0.1.4-skill-candidate.zip.sha256)` exit0。
- 源码提交 `d52c01d31d38b326e373efa359a078d001f44618`、独立 QA-only 提交 `fae694eebf3ab14c91975cb5f1f58fb44e5d603a`，后者只改本产品 `qa/audit_r1_q04_rerun_014.py`、逐案 JSON、报告；`git diff --exit-code d52c01d..fae694e -- packages/skills/wangbin-meeting-action-tracker products/catalog.json` exit0，QA 后源码未变；本报告为包外管理证据，不修改包。catalog 本地 `active_version=0.1.4` 是工厂选择器，不等于 WorkBuddy 激活/发布，旧版本虽包哈希保留但旧版本当前对变更源码的 default verify 并未证明通过。
- 独立 QA `PYTHONDONTWRITEBYTECODE=1 python docs/products/wangbin-meeting-action-tracker/qa/audit_r1_q04_rerun_014.py` exit0 **42/42 逐案符合**（探针 exit0 本身不作业务通过证据）；`PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider --basetemp=<wb-quality-scratch>/q04-rerun-014-tests tests/test_meeting_action_tracker.py tests/test_meeting_action_tracker_audit_r1.py` exit0 **72 passed、1 第三方 warning**；`python -m tooling.products test --id wangbin-meeting-action-tracker` exit0 **20 passed、1 warning**；工厂 `validate` 和 `verify` 对当前 0.1.4 候选 exit0。精确命令/返回码、真实 MD/TXT/CSV/XLSX、四表/摘要行和 SHA 见独立 QA `qa/audit-r1-q04-rerun-014.md`、`qa/audit-r1-q04-rerun-014-results.json`。经理未冒充重新运行独立 QA。

## 分层门禁与剩余事项

| 门禁 | 状态与界限 |
|---|---|
| L1 ZIP/包内源码与侧车 | PASS（此精确 0.1.4 ZIP） |
| L2 专项/工厂测试 | PASS（72/20，上述限定集合） |
| L3 从精确 ZIP 干净解压后正式 CLI、真实文件及四表/摘要回读 | PASS 42/42（仅列举用例） |
| L4 真实宿主模型三轮 | NOT_TESTED |
| L5 WorkBuddy 安装/实际使用/审核 | NOT_TESTED；不得宣传平台可用 |
| 目标依赖可得性/第三方许可证及发布权 | NOT_VERIFIED |
| 跨产品相似性 | NOT_TESTED |
| 上传/提审/发布/合并/部署 | NOT_DONE，均未获授权 |

本地包有 `openpyxl>=3.1,<4`、`python-docx>=1.1,<2` 声明；QA 环境 Python 3.14.9/openpyxl 3.1.5/python-docx 1.2.0，不是目标 WorkBuddy 环境证明。复杂中文跨句、隐含主语的规则分类不由这 42 项穷尽。`GIT_PUSH_PASS` 及远端精确 ref 在实际推送与回读后另记卡片 handoff；即使远端成功也不是 L5 或平台审核。预建 Q05 基线 `t_14b7c2e8` 仅依赖本经理卡，经理完成后自动提升，不再建重复链。
