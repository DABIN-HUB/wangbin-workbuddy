# CALC-SKILL-01｜Decimal Skill 技术候选冻结验收（T01）

状态：**事前合同，不是实现、QA PASS 或平台回执**。`product_id=wangbin-software-consultant`、`product_type=Expert`，候选类型 `Skill`（实验，非正式新产品）；唯一工作树 `F:/ideaWorkSpace/wangbin-workbuddy-software-consultant`，分支 `expert/software-consultant`，基线 `3f0d5a27483839daf782a726694c168b57f439b9`。用户本轮授权见 manager attachment `pasted_content_2026-11-13_01-58-19-463_a77c07.txt`；本轮不称 R6。外显中文 **软件工作量与报价计算器**，英文 **Software Effort and Quote Calculator**，品牌/author **星核实验室 StarCore Lab**，`name=wangbin-estimate-calculator`，`version=0.1.0` 技术候选，不声称 Expert 已接入。

## 来源优先级与现状

- 团队已提交 `F:/ideaWorkSpace/wangbin-workbuddy-team/agent.md`、`team/workflows/skill-development.md`：`team/skill-factory-v1` 本地/精确远端 `6f6040e879be57d5de008d5a410e63c5d50edb79`；blob `53901555742563bb843b94546edda429e029c2bc` / `737925a31da9ae5c92090d13b7607cfc0dea9236`；磁盘与已提交 SHA-256 `67b77d2cdadd80e93386325171e2a9eae16169efe87e3c4186f9ea3825a4b72b` / `5390c3ee68df2ee6cd925705f71fdcbe34be1d42ddad690e258ed3eec6019a75`。另读 `team/policies/{git-policy.md,workspace-policy.md}`、`team/workflows/task-handoff.md`。团队 reports 另有其他任务 dirty，不处理。
- 产品根 `AGENTS.md`（12 行）→ `agent.md`（136 行）→ `docs/development-task-template.md`（35 行）均存在且全文读取；旧根规则/模板的默认禁自动 push，与本次明确授权的开发/质量角色当前产品独立分支普通 push 不同；分析师仍不得 commit/push。冻结 FRD `F:/ideaWorkSpace/wangbin-workbuddy-delivery/experts/wangbin-software-consultant/WorkBuddy-Expert-FRD-v1.0.md`（FRD-1.0、1396 行，SHA-256 `bf1821da43f23e372d8782775617054d39163ac630be3f40c11f4a429cbb682d`）；产品 `docs/{requirements.md,input-output-contract.md,acceptance-cases.md,p01-r5-rate-policy-addendum.md,p01-r7-s29-acceptance.md,p01-r8-s10-s31-acceptance.md}` 均全文读取。旧 86 案与正式 P02 QA 独立保留。
- 原 POC `experiments/decimal-poc/{README.md,estimator.py,test_estimator.py,fixture_synthetic.json}` 四件全文读取，不修改；其 `TIERS=(MVP,Standard,FullA,FullB)` 线性累加，**缺 Standard B**，既有相同 ID 重放去重、不同内容冲突拒绝，`outside_fees` 仅 unknown，CLI `-o` 写输出。原有 25 个聚焦测试在本卡以只读旧源码与外置 S30 原件实际执行：`python -m unittest discover -s packages/experts/wangbin-software-consultant/experiments/decimal-poc -p test_estimator.py -v`，设 `POC_SCRATCH` 为本 profile 已有 scratch，`S30_POC_INPUT`/`S30_POC_RAW` 为下述交付区原件；退出 0，`Ran 25 tests ... OK`，0 skip。仅证明旧四档 POC 回归，**不证明新 Standard B 或模型调用**。R5 原始 `preqa-p02-r5-t_f55d0c99/raw/S30-MULTI-turn3/1/stdout.bin` SHA-256 `18949697dbff9a62cfaf46f31e39f4e569b81b34adb5766fb2d3027e2d6f81fb` 只读核对；`decimal-poc-t_3268574a/s30-transcribed-input.json` 是人工转录而非模型自动抽取。原 stdout 报 Standard A FE/BE/DB/QA 低列 `6/10/5/5`，合计 `26`（高列 `10/17/9/9` 合计 `45`），与原 M1/M2/S1/S2/F1 的独立行低 `30`、高 `52` 不符；原案仍 FAIL，不回填成功或修改原证据。
- WorkBuddy 官方 https://open.workbuddy.cn/docs/skill 的 Skill 根 `SKILL.md` 必需，`references/`、`scripts/` 可选；frontmatter 必填 `name/display_name/display_name_en/description/description_zh/description_en/version/author`，`allowed-tools` 可选，`examples_zh/en` 官方可选但团队**新候选**各恰好三条；正文团队固定五个二级标题（见下）。官方说明脚本由 AI 通过 Bash 工具执行，**文案不能授予 Bash/Python 权限**；平台可运行/安装/上传均 NOT_TESTED。

## 技术实现范围与可观察产品价值

非改提示词：把原有人工转录后才能运行的确定性 POC 变成独立可解压的 Skill 来源、严格结构化输入/输出、范围条件分支、错误拒算及可审计回执；自然语言→工作包抽取合理性与工具实际调用另行模型证据验证。只用 Python 标准库 `decimal.Decimal`，不增服务、网络、MCP、数据库和通用报价规则引擎。脚本不判定真实需求完整、估时合理或财务接口实际开放。用户自然语言使用，不能强迫普通用户亲填 JSON/CLI。详细字段、方案集合及公式以同目录 `skill-preview/wangbin-estimate-calculator/references/input-output-contract.md` 为实现合同；所有新增方案成员不得把已撤销旧包计入当前快照。

## 技术验收矩阵（事前固定；全为 NOT_TESTED）

| ID / 门禁 | 输入与正向可观察断言 | 负例及 FAIL 条件 |
|---|---|---|
| A01 `STANDARD_B_BRANCH` | 合成集合 M={M1,M2}，S={S1,S2,F1}，I={I1}，F={C1}；MVP=M，Standard A=M∪S，Standard B=M∪S∪I，Full A=M∪S∪F，Full B=M∪S∪F∪I。每个方案 `ids` 恰是去重集合、角色/行/B/R/E 与条件价格逐一可复核；无接口授权时 B 为明示条件示意 | Standard B 不存在；把 I 提前算到 Standard A/Full A；Full B 加两次 I；只按序列线性前缀累加；声称接口已开放 |
| A02 `DECIMAL_CORE_REGRESSION` | 原四文件和旧断言不改；现有原 25 测试再次实际运行且 25/25 PASS（包括需要外置 S30 原件的用例，记录环境/路径/退出码）；新标准分支独立测试 | 改旧断言/fixture 凑绿；SKIP S30 却报告 25 PASS；用 25 旧测证明新分支 |
| A03 输入一致性 | ID 全局唯一；相同 ID 完全同一身份/来源/版本/角色数可幂等重放且仅计一次，任何同 ID 不同内容冲突非零；每包来源、范围版本、功能、FE/BE/DB/QA 低高 Decimal 字符串均完整，0≤低≤高 | 同 ID 跨分支有冲突仍算两次；范围变更沿用旧行版本；缺项、负数、NaN、Infinity、非数字、额外字段或角色缺失→非零，不把 UNKNOWN 填 0；不适用的显式 0 仅在来源说明其无此角色且经确认时成立 |
| A04 数值/价格 | 每行四角色综合行；每方案逐角色汇总等于 B；独立 rL/rH，R=B×r，E=B+R；fixed 优先于批准的示意 1000/1500，明确拒价或只要人天时人民币为空；第三方未知时完整项目总价 `null`；打印单位、来源、示意/条件状态 | 浮点运算/中途舍入掩盖差异，错用默认价、拒价仍出人民币、把未知第三方/部署/维护填零或人工费冒充完整总价 |
| A05 `SKILL_SOURCE_VALIDATION` | YAML 安全解析、上述必填字段均非空，`description=description_zh`；中英各三条自然语言示例（中文 8–120 字、英文 12–180 字），规范化后互不重复，无脚本命令/内部路径/无据保证；正文按顺序且仅使用 `## Preparation / 准备`、`## Usage / 使用`、`## Processing / 处理`、`## Outputs / 输出`、`## Limits / 限制`，各有真实内容，引用本合同及脚本命令/输入/输出/异常/限制/「试试这样问」 | 把 Skill 本地结构检测当平台运行；无权限仍声称脚本已被 WorkBuddy 执行；示例占位、跨语重复、YAML 不可安全解析却 PASS；人工语义未核写 PASS |
| A06 CLI/安全 | 明确一个输入文件及新输出路径；合法 JSON 成功退出 0、UTF-8 结果按完整 schema 读回；非法 JSON/字段/同 ID 冲突/源文件不可读/目标不可写/覆盖已有输出均非零，stderr 诊断不包含敏感用户正文，不产生部分成功报价 | stdout/stderr/退出码不符；覆盖输入、原始 R5/旧 QA 输出、已存在路径；读未指定文件、访问网络、执行用户文本为 shell/Python；符号链接/越界路径绕过限定。沿用 POC 错误退出 2 可优先，成功仅 0，具体 CLI 改动由 Developer 受限实现并测 |
| A07 S30 原件诊断 | 保留原 stdout/hash/原 FAIL 与人工转录身份；复核原表 Standard A 报列低26/高45 vs 行低30/高52，拒绝 `reported` 不匹配；新双分支用**另行冻结的合成输入**覆盖 B/E/价态，不把原 S30 伪称已含 Standard B | 修改原证据或把新演示计算当原模型回答正确；只核表头数字不核行/列/档位 |
| A08 `SKILL_ZIP_INTEGRITY`/`SKILL_CLI_STANDALONE` | 候选 ZIP 根目录 `wangbin-estimate-calculator/`，至少 `SKILL.md`, `scripts/estimator.py`, `references/input-output-contract.md`，实际成员逐件 SHA 与来源一致、CRC 全通过、manifest/SHA sidecar 读回；从 ZIP 干净解压仅用包内脚本和标准库运行正反例，路径/权限/异常真实验证 | 引用实验目录或仓库外源码、生成物/缓存/客户原件入包，只有 CRC 没有独立执行；若附 LICENSE 先核来源/分发权，**原 Expert LICENSE 不改**；ZIP 不当 Expert 安装包、不进 Git |
| A09 旧边界/回滚 | 不改正式 Agent、plugin.json、`tooling/expert_rules.py`、`tooling/phase5_expert_packager.py`、FRD/旧场景/旧证据；对输入和工具错误保持失败、原证据不覆盖；若技术路线需改受保护项即停下并报告 | 把 Hermes 工具可用推成原生 Expert 已接入；删除旧失败、启动正式 P02 QA/MES/R6 或 WorkBuddy 上传发布 |

## 模型链路专用验收（Developer 试验、Quality 独立复核；本卡未运行）

五组各**两次独立清洁会话**，记录 run/session ID、模型/提供方及参数、源码与 Skill ZIP SHA、每轮用户原文与前一轮实际状态（S30 不拼接不同会话），在执行前冻结输入/预期/禁止项及 SHA。①单轮给定人天、缓冲、价：模型提取带来源的工作包，实际工具命令/输入文件身份/退出 0/回执，逐字段对齐 FE/BE/DB/QA/B/R/E/C。②真正三轮 S30 采购库存→多仓审批财务对接→五档条件方案，记录每轮版本/撤销/条件接口与去重，原原始 FAIL 保留。③明确只要人天不要人民币：依然调用计算器核 B/R/E，回复不出现人民币。④重复 ID/角色列冲突/必填缺失：工具非零，模型不得绕开错误给定价。⑤工具不可用或输入不可确认：如实告知未验证计算，不用模型口算冒称工具结果。所有模型生成的估时标 `ASSUMED`，用户确认数据才标 `CONFIRMED`；用户没给缓冲/价且无法形成有依据假设，先说明不能得数值 E/C，不暗设零。

**证据分类**：只有模型**自己选择**执行工具的真实记录 + 完整命令与输入文件身份 + 真实退出码 + 工具回执 + 输入/输出 SHA-256 + 最终自然语言答复 + 数值逐字段复核同时齐备，才标 `REAL_MODEL_TOOL_INVOCATION` 并据此评估 `MODEL_TOOL_INVOCATION`/`MODEL_INPUT_EXTRACTION`/`MODEL_OUTPUT_RECONCILIATION`/`MODEL_FAILURE_BEHAVIOR`。测试程序先调用 Python 再复制结果给模型仅标 `ORCHESTRATED_TEST`，可以验证复述但不能给 MODEL_TOOL_INVOCATION PASS；缺少模型自主工具记录即 `NOT_TESTED`，观察到有工具却绕开/造价则按对应断言 FAIL。退出 0 不能证明工作包真实完整或估时合理；工具不可用案应保存实际失败而不是制造假的成功记录。Hermes 本地通过与 WorkBuddy 原生安装、Expert 调用、审核发布分开，后三者无真实回执均 `NOT_TESTED`。

## 后续角色与停止门

分析师本卡只新增本合同及引用合同，**不改源码/旧文档、不 commit/push**；授权 Developer 接棒先逐字审核这两份合同与冻结来源，在当前唯一分支用精确路径单独 `docs(wangbin-software-consultant): ...` 提交，再实现/测试/构建及另次精准提交；检查 `git status`、`diff --cached --stat/--check/--name-status`、敏感内容、忽略 dist、远端当前 HEAD 与待推历史，获长期授权仅当前独立分支普通 fast-forward push，回读精确远端 SHA。Quality 独立冻结用例并验证最终 ZIP，不能将本技术 QA 称为 P02 正式独立业务 QA。禁止 merge/rebase/force push/main 历史改写、上传/安装/发布。清理只限本轮产生且可确认的临时物；当前有效 dist 与旧失败证据受保护，未知不删。正式 Expert/Skill 平台集成、许可证/相似性、P02 Manager/MES 门禁保持 `NOT_TESTED`/既有 BLOCKED，不能从本文升级结论。
