# 独立 QA 入口与当前状态

**INDEPENDENT_QA=NOT_RUN / PENDING_INDEPENDENT_QA**。作者仅执行候选生成、冻结输入重建比较、AST/文档/卫生/范围自检；没有签署独立 QA。
这是有实际输入、范围与待验项的审核索引，不是模拟 QA 结果。真正审查完成后，唯一writer须原字节复制审查员结论并明确其冻结快照范围，再做新payload限定复审。

## 输入与冻结边界

- RUN/developer-freeze-index.json：源码/新文档/脚本/允许证据逐路径size/SHA、来源映射、脱敏身份；独立 QA 必须先核此索引 SHA及每件实际字节。
- RUN/frozen-inputs.json：本地原元数据胶囊，177件，SHA `171656d7edd77345ba25edc333c2450db000dbbc38fdd30242531ecbad19f5e9`。仅本地，含公开联系字段，不可直接共享。
- 重新读取 source-research/official-metadata/raw 和 pep658/raw 与响应索引、全部旧12图/绑定、license-identity 原来源文本、document 原件；不能只复述 RESULT。
- 共享 raw不入payload：source-research/sharing-index.final.json 是185件脱敏/最小派生allowlist；原/派生SHA分别记录，PEP658索引期望摘要未核。

## 独立复核必测

1. 从十二旧图分别抽42名称/43精确版本，校核官方对应与tzdata差异。
2. 由真实Requires-Dist重新求marker/extras固定点，保留magika澄清；核全部传递依赖及Python范围。
3. 逐115文件核官方 URL/SHA/文件名/name/version/tag/ABI/platform/OS最低条件；拒绝yanked/t-GIL/musl混入。
4. 区分官方记录摘要与实际本地wheel摘要（后者0），核所有license/source/READY/closure状态不升级。
5. 复核三项精确文本缺口、全部42再分发BLOCKED、双document identity与外置12/optional11/历史重放限制。
6. 负向真实变异：同名不同version、同version不同SHA、错误Python/ABI/platform、Requires-Python、删传递node或边、错marker/extras、未取得却claimed hash pass、unknown license却PASS、unknown officialsource却READY、缺件却closurePASS；独立保存变异输入、运行回执与拒绝诊断，不能预填expected结果。
7. 核无下载/安装/生产改动/Skill变更；核task允许树隐私/秘密与提交blob字节；审新payload exact成员集。

脚本命令：以现有绝对 .venv/Scripts/python.exe -I -B 调用 scripts/locktool.py validate --inputs <frozen-inputs> --candidate <完整候选>；须经 RUN/record_command.py 以 quality 独名保存 exact inputs/stdout/stderr/退出码。单条<=120秒，质量角色预算200秒，任务总1200秒含失败。

开发者自检日志：RUN/commands/developer-*；最终已完成时间/失败/保护读回另存 developer-final-state.json。作者自检不计独立检查数量。
没有新源码审阅ZIP；独立QA完成且payload限定复审通过前不封包。
