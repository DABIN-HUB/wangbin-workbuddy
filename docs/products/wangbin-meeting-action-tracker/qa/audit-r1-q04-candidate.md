# AUDIT-R1 Q04 独立 QA：0.1.2 精确候选 FAIL

- product_id: `wangbin-meeting-action-tracker`; task_id: `t_674ba6f3`; 分支 `skill/meeting-action-tracker`; 测试前 HEAD `e2b2764b42f9cbc2579c114e36145008cf12d12e`，工作树 clean。开发合同 `168174c3d9b567091fd0de3d15f3ae151a2f6704`，业务源码 `65657b3fb5cd1a5ec342ac7dcbb3a0a642863c8b`。
- 测试对象：`dist/wangbin-meeting-action-tracker-0.1.2-skill-candidate.zip`，独立 SHA-256 `a724a682364cef80eb0a64791f6ea447de463c20f0b14bd05aba87c558ba9ffe`；旧 0.1.1 SHA `5f5f0bc86ca469c89d758010194d8768e27badc96584791495e4b71c8ef745ae` 不变。`ZipFile.testzip()` 无坏项；4 个唯一、安全成员（SKILL.md、manifest.json、references/usage-and-contract.md、scripts/track.py），逐项大小/hash 与 sidecar manifest 及当前产品源码一致。sidecar/candidate catalog 的版本与哈希一致，YAML 身份/双语各三条推荐问题、相对运行入口、封装参考文件及声明的 `openpyxl>=3.1,<4` / `python-docx>=1.1,<2` 路径已静态核对；目标 WorkBuddy 是否安装依赖另列未测。未看到测试文件名/样例常量/expected 载入的显式生产源码特判，静态检查不能证明任意输入可靠。
- `python docs/products/wangbin-meeting-action-tracker/qa/audit_r1_q04_candidate.py`，cwd 产品工作树：exit **0**，真实业务断言 **21/26 符合、5/26 不符**；此脚本 exit0 表示探针成功记录失败，绝非 QA PASS。脚本只从精确 ZIP 干净解压的 `scripts/track.py` 执行正式 CLI，剔除 PYTHONPATH；真实 UTF-8 MD/TXT、CSV、上一轮 XLSX、补证 TXT 和用户更正；每轮单独目录，重新打开四张工作表、记录全部关键行及摘要、退出码、命令、输入/输出 SHA。逐案全量 JSON：`qa/audit-r1-q04-candidate-results.json`，脚本：`qa/audit_r1_q04_candidate.py`。输入旧 CSV 和补证文件前后 hash 一致。程序实测 Python 3.14.9、`openpyxl 3.1.5`、`python-docx 1.2.0`；不是目标 WorkBuddy 环境。
- 开发原有测试：`PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/test_meeting_action_tracker.py tests/test_meeting_action_tracker_audit_r1.py` exit0，42 passed，1 warning；不能抵消独立业务反例。`python -m zipfile -t wangbin-meeting-action-tracker-0.1.2-skill-candidate.zip && sha256sum -c wangbin-meeting-action-tracker-0.1.2-skill-candidate.zip.sha256` 于 dist 运行 exit0（初次误用 `dist/` 路径，在 dist cwd 导致 zipfile FileNotFoundError，但后续 `sha256sum` exit0 掩盖复合命令退出码；已修正 cwd/路径并使用 && 重跑通过）。

## 可独立复现的业务阻断

1. **MTG-F01 否定等义变体错误取消。** 输入旧 CSV T01 接口联调/王工/进行中/已确认期限 2026-11-05，T02 演练培训/待执行；会议 `T01不会取消，仍在进行中。`（JSON `not_cancel_paraphrase`）。预期：T01 进行中、无取消事件。实际 CLI exit0，当前任务 T01 **取消**，本次变化/历史记录 `进行中→取消`，摘要也声称确定取消且把否定原句当来源；T02 仍待执行。代码 `status_claim` 只覆盖部分否定结构，落入裸 `取消` 分支。冻结 R01 正向规则已覆盖 `不取消`，此案是开发未覆盖的等义改写。会产生假取消和错误的逾期结论。
2. **MTG-F01 提议等义变体错误当决议。** 同旧 CSV，会议 `提议取消T01，目前还未拍板。`（`proposal_variant`）。预期：T01 进行中，提议及未决定作为待确认，历史无确定取消。实际 CLI exit0，T01 **取消**、待确认表空、历史确定取消、摘要错误宣称决议。`proposed_status_change` 未覆盖「提议」；且「还未拍板」未作为尚未决定识别。旧基线中的固定「建议取消…尚未形成决定」通过不能代表此案通过。
3. **MTG-F05/MTG-A04 两项相似任务错误合并。** 无旧表；MD 两行：`新增任务：系统接口检查A，由Maya确认负责，截止2027-03-06。` 和 `新增任务：系统接口检查B，由陈琳确认负责，截止2027-03-07。`（`multi_first`）。预期：两个独立 task_id，分别保留 A/Maya/03-06、B/陈琳/03-07，新增历史对应各自来源。实际 CLI exit0，仅 **一个** `MTG-EA20DDFCF7D3F544`，任务内容 **A** 却被第二行的陈琳/03-07 覆盖，摘要共 5 项变化但第二任务无新增事件。根因定位 `apply` 中 `len(recent_new)==1` 的负责人表达回填分支，在第二个明确「新增任务」前沿用上一个任务。基于错误首轮输出重新导入同一记录和重排的后续两案 `multi_repeat`、`multi_reordered` 都未达到两任务幂等及重排不合并的预期，属于同一缺陷链，分别保留实际记录，不把 5 项当 5 个独立根因。

其余用例有独立正向：T01/T02 同句不同状态、明确取消、日期标签与前缀整体平移到 2027-02-28→03-01、缺日期/两个冲突日期保留已确认旧截止、普通中文及英文负责人、无「新增」明示行动项、讨论待确认、报告完成→E-83 证据补录→重放无新增、用户更正→重放、补充同权冲突正反上传顺序、空会议及旧表错误 schema 返回 2 且不产生工作簿。未见变体的全部空间 **NOT_TESTED**；历史 0.1.1 的 7/33 与 26/33 问题记录维持，未篡改。

## 层级与收口

- L1 ZIP/源码成员与路径及静态元数据：PASS（有限静态核对）。L2 旧/开发测试：42 passed；独立业务 L3：**FAIL 21/26**。真实宿主模型三轮 L4：**NOT_TESTED**（本次 L3 已阻断，未把脚本模拟成模型对话）；WorkBuddy 安装/使用 L5、WorkBuddy 依赖实际可得性、第三方及包发布许可：**NOT_TESTED / NOT_VERIFIED**；远端 push **NOT_TESTED**。无上传/部署/发布。
- 结论：此**精确 SHA 只能标本地 QA FAIL**，不得以 42 个旧/开发测试、ZIP 完整性或部分正向代替业务通过。请经理只派本轮第一条有界 QA 返回：开发修复通用否定/提议作用域与新任务唯一归属，保持旧包不变，升级新版本独立 ZIP；另卡独立 QA 重新做所有失败链及全套回归。不得改此 QA 证据或把修复后源码归入旧 SHA。原历史返工不重置；新阶段当前是首次集中修复之后的**第一次 QA 退回**。
