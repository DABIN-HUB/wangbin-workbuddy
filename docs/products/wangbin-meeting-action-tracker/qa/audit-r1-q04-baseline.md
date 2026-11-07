# AUDIT-R1 Q04 独立历史基线（0.1.1，L3 FAIL）

- product_id=`wangbin-meeting-action-tracker`; task_id=`t_5a7e06e6`; branch=`skill/meeting-action-tracker`; workspace=`F:/ideaWorkSpace/wangbin-workbuddy-meeting-action-tracker`; base_commit=`940b0e27678e4e412ef75b712974b0a008f263f2`。本报告是**另一次**审查新增用例的 QA 记录，不改写旧 `independent-qa-0.1.1.md` 的当时 47/47 PASS（当时覆盖集不同）。
- 原版 ZIP `dist/wangbin-meeting-action-tracker-0.1.1-skill-candidate.zip` SHA-256 `5f5f0bc86ca469c89d758010194d8768e27badc96584791495e4b71c8ef745ae`；sidecar `sha256sum -c` OK；`python -m zipfile -t` Done testing；成员仅 `SKILL.md`、`manifest.json`、`scripts/track.py`，无重名或穿越；包内脚本与当前源码字节 SHA-256 相同 `95a253c224fd2c16c41c452ec2053d6223572cf6ff8c2a5737f703c1a1f16a7d`。外置 manifest 三成员摘要及版本 `0.1.1`，本地完整性 PASS，不表示业务/平台 PASS。
- `python docs/products/wangbin-meeting-action-tracker/qa/audit_r1_q04_baseline.py` → **exit 0（探针正常运行，不是业务 PASS）**，真实 TXT/MD + 旧 CSV（T01 接口联调/王工/进行中/已确认截止 2026-11-05，T02 准备演练培训/李工/待执行）逐案实际 CLI；每案命令、exit/stdout/stderr、会议原文及 SHA、旧 CSV 字节、四表重新打开的所有业务行/来源、输出 SHA 记录在 `audit-r1-q04-baseline-results.json`。使用 wb-quality profile scratch 干净解压原 ZIP，清理 `PYTHONPATH`，不从工作树加载脚本。所有 33 案 CLI exit 0，四表可重新打开，**7/33 符合独立业务预期，26/33 不符**；旧 CSV 输入 SHA 前后相同。运行环境 Python 3.14.9/openpyxl 3.1.5；依赖 python-docx 实际参与包导入，版本未核。临时夹具/工作簿执行后清理，JSON 保留完整可复现输入/参数/重开结果/哈希；重跑将生成新的临时路径与 XLSX 哈希，不能依赖已清理路径重开。

## 代表性失败（输入 → 正确预期 → 真实输出；全部 CLI exit 0）

| ID / 缺陷 | 关键输入（完整字节见结果 JSON） | expected | actual | 层级 |
|---|---|---|---|---|
| `f01_not_cancel_spaced` MTG-F01 | `T01 不取消，继续进行中。` | T01 进行中，无取消事件 | T01=`取消`，事件类型=`取消`，来源是该否定句 | L3 FAIL |
| `f01_not_completed_spaced` MTG-F01 | `T01 不是已完成，仍在进行中。` | T01 进行中，无完成事件 | T01=`报告完成`，来源是否定句 | L3 FAIL |
| `f01_prior_spaced` MTG-F01 | `取消此前取消 T01 的决定，T01 继续执行。` | T01 保持进行中或不能可靠确定则待确认；不得取消 | T01=`取消`，记录取消事件 | L3 FAIL |
| `f01_scoped_spaced` MTG-F01 | `T01 未完成，但 T02 已经完成。` | T01 保持进行中、T02=`报告完成` | 两者原值保留，只生成“多个任务 ID”待确认，漏掉 T02 的确定进展 | L3 FAIL |
| `f01_decide` MTG-F01 | `明确决定取消T01。` | T01 取消并记来源 | T01 进行中、任务关联待确认；插入空格的 `f01_decide_spaced` 是正向对照 PASS | L3 FAIL |
| `f02_zhang` MTG-F02 | `新增任务：接口测试，由张三确认负责，截止2026-11-10。` | 新任务负责人张三已确认，期限正确 | 新任务/期限存在，但负责人及负责人确认状态均空，待确认表也无提示 | L3 FAIL |
| `f02_zhao`/`f02_xiao`/`f02_alex` MTG-F02 | 等量替换负责人赵敏/小王/Alex | 各自确认为负责人 | 全部负责人空，且无待确认项；李工 `f02_li` 正向 PASS | L3 FAIL |
| `f02_tentative` MTG-F02 | `建议由张三负责，尚未确认` | 张三候选、未确认并可追溯 | 负责人空、待确认表空，建议人选丢失 | L3 FAIL |
| `f03_label_spaced` MTG-F03 | `会议日期：2026-11-06。T01 截止明天。` | T01 已确认期限 2026-11-07 | 原截止 2026-11-05 未变，标“缺会议日”待确认 | L3 FAIL |
| `f03_prefix_spaced` MTG-F03 | `2026-11-06项目例会。T01 截止明天。` | 同为 2026-11-07 | 原截止不变，标“缺会议日”（日期和例会之间未加空格，正是要求的前缀变体） | L3 FAIL |
| `f03_missing_spaced`/`f03_conflict_spaced` MTG-F03/F05 | 无会议日期/两个不同会议日期，旧 T01 有已确认期限 | 不猜新期限，保留旧 2026-11-05 的确认状态并标新建议待确认 | 虽未猜新期限，但**把旧确认状态改成待确认**；未分别解释冲突的两个日期 | L3 FAIL |
| `f04_direct` MTG-F04 | 无旧表 `张三负责接口测试，截止2026-11-10。` | 首版建行动项、张三及截止日 | 当前任务表 0 行，仅待确认“无法唯一定位旧任务”；摘要无新任务 | L3 FAIL |
| `f05_correction` MTG-F05 | 旧 CSV + `--correction 将T01截止日更正为2026-11-10` 与 `--correction T01明确改由赵敏确认负责` | T01 新期限/负责人、历史原/新值，T02 不动 | T01 原截止 2026-11-05/王工未变、状态历史空，两条更正均误判“无法唯一定位旧任务”；T02 保留 | L3 FAIL |

其余包括严格无空格的 `T01不取消`/`T01不是已完成`/`建议取消T01`/`取消此前取消T01的决定`/`T01未完成，但T02已经完成`、以及 `T01已经完成`，存在未关联/漏更新（不能把表面状态未变当语义通过）。正向局部对照：空格分隔的明确取消、空格分隔的建议取消、李工负责人、无动作讨论候选、未提及 T02 保留、正常首版新增与原文重复输入幂等。这 7 项仅证明对应受限输入，不能抵消反例。所有四表是结构可重开，不等于四表内容正确。

## L1 / L2 / 覆盖边界

- L1 源码与 ZIP 同字节：`scripts/track.py` 的 `locate` 使用 `(?<![\\w-])T01(?![\\w-])`，Python Unicode `\\w` 包括紧贴任务号的汉字，导致中文连写 ID 无法关联；`apply` 的 `已完成|完成了`、`取消` 分支不解析肯否/作用对象/之前决定；`owner` 候选姓名尾缀限“工|人|经理”；日期正则仅识别日期在“会议/例会”之前且有限字符，标签前置日期不命中；新任务只在“新增”前缀产生。`--correction` 共用同一定位缺陷；相关代码见包内脚本 `locate`/`apply`/`reconcile`，这只是根因定位，不冒充动态证明。
- L2 `python -m pytest -q tests/test_meeting_action_tracker.py` → exit 0、20 passed/1 warning（历史用例并未覆盖上述新反例）；本任务未新增函数替身测试，新增 L2=NOT_TESTED。本次 L3 独立数据/正式 CLI 直接判业务 FAIL。
- 新版候选 QA、真实宿主自然语言/多轮 L4、WorkBuddy 安装/运行/审核 L5、许可证/依赖分发/相似性/发布 = **NOT_TESTED**。本次 33 案不是穷尽性覆盖；补充材料入口对否定作用、其他姓名表达、跨轮补证、恶意压缩文件、Windows 实际 symlink/junction 均 NOT_TESTED。不能用本基线代替后续新 ZIP 独立复验。

**门禁**：0.1.1 当前业务基线 FAIL，应进入分析/修复链；禁止称当前可发布。原 ZIP、许可证、生产源码和历史 QA 记录未修改。本次只提交 QA 探针、独立结果、报告。`blocked_reason`=旧版本 MTG-F01–F05 真实业务反例；新版本未产生、复验 NOT_TESTED。