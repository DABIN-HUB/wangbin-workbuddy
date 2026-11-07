# AUDIT-R1 Q02 B — 0.1.2 原 ZIP 独立反例基线

- product_id: `wangbin-project-acceptance-check`; task_id: `t_c08511ed`; branch: `skill/project-acceptance-check`; base_commit: `79f742463ae487f3aede074c3233adb111977147`。
- 原版 `dist/wangbin-project-acceptance-check-0.1.2-skill-candidate.zip` SHA-256 **5117bd7202cd6a322c3aae8246dad79edeb4cd9a876cbcae800ee78ad2a9df57**（与授权基线相等）。`python -m zipfile -t` 返回 0 `Done testing`；9 个路径安全且不重复的成员，逐成员 SHA 在 JSON 中。无重打包/更改旧 ZIP。干净解压至本 QA profile scratch；脚本来自解压包，CLI 子进程去掉 `PYTHONPATH`。此前原 0.1.2 在既有用例的局部 QA PASS 保留，不追溯改写；新增反例说明它**不是**无保留可靠候选。
- 冻结依据：原 V2 附件19 §15.2–15.9，审查修复指令 §07、§12–13、§18。实际完整命令、虚构输入和 SHA、退出码、stdout/stderr、快照里的要求/条件/缺口/来源、重开六表 XLSX 与 DOCX 文本和实际输出 SHA，见 `audit-r1-012-baseline-results.json`；可重跑探针 `audit-r1-012-baseline-probe.py`。所有 20 案 CLI 退出 **0**，说明退出码本身不能用来判断业务正确。

## 独立预期／实际（从完整真实文件 CLI；不是替身）

| 缺陷与案 | 输入摘要 / 预期 | 原 ZIP 实际 / 结论 |
|---|---|---|
| ACC-F01 `F01-login-10`, `-9999` | R01 同场景至少 10000 个并发登录，实测最大 10 / 9999：数量不符，应 `NONCONFORMING` | 两者 `EVIDENCE_FOUND`，且 XLSX/报告沿用该支持状态；**FAIL**。|
| ACC-F01 `-12000`, `-10000`, `-10001` | 同场景 12000 / 10000 / 10001，应有支持 | 均 `EVIDENCE_FOUND`；仅结论碰巧符合，旧代码未比较指标，**正向子项 PASS，验证机制 FAIL**。|
| ACC-F01 `-unrelated` | R01 只写数据库备份，不应支持登录并发 | `EVIDENCE_FOUND`；**FAIL**。|
| ACC-F01 `-no-quantity`, `-unit-mismatch` | 缺实测数量或写 12000 次每日登录，不可冒充并发人数，需保持不可比 | 均 `EVIDENCE_FOUND`；**FAIL**。|
| ACC-F02 `F02-ubuntu`, `-linux` | 分别要求 Windows Server 2022、Debian 12，仅提交 Ubuntu 部署步骤：目标环境未得支持，不能反推系统不能运行 | 均 `EVIDENCE_FOUND`；**FAIL**。|
| ACC-F02 `-only-ubuntu` | 明说仅覆盖 Ubuntu 且没有 Windows Server 2022 步骤：所交部署文档不满足目标要求 | `NO_EVIDENCE_FOUND`，没有准确不符合项；**FAIL**（不得推断软件未开发）。|
| ACC-F02 `-win-full`, `-win-2025` | 提交指定 OS/版本、安装/配置/启动/验证步骤：可得到文本支持 | 均 `EVIDENCE_FOUND`；**正向子项 PASS**，不能说明环境语义检查已正确。|
| ACC-F03 `F03-zero` | 全部登录测试 100 项成功 100、失败次数 0：不能因“失败”二字判坏 | `NONCONFORMING` 且生成不符合发现；**FAIL**。|
| ACC-F03 `-one` | 100 项成功 99、失败 1：不能全通过 | `NONCONFORMING`；**正向负例子项 PASS**。|
| ACC-F03 `-unspecified` | 只写“未发现失败”，缺测试范围：不可泛化为全部通过，须待确认覆盖 | `NONCONFORMING`；**FAIL**（不是确证失败）。|
| ACC-F04 `F04-compound` | 两项交付：只给接口，缺部署，不得整体满足 | 两个子条件，`PARTIAL_EVIDENCE`；**此子项 PASS**。|
| ACC-F04 `F04-claim` | “开发完成”自述不等于接口材料 | `NO_EVIDENCE_FOUND`；**此子项 PASS**。|
| ACC-F04 `F04-conflict` | 同编号一个全部测试通过，一个 99/100 且失败 1：两份来源并存，`CONFLICT` | `CONFLICT`、两份来源均保留；**此子项 PASS**。注意若把“失败0项”写在正向材料中旧版也会错判为双负例，已由 F03-zero 另案实证。|
| ACC-F04 `F04-two-docs` | 同编号接口+部署分别提供两份：两项都获得文本支持 | `EVIDENCE_FOUND`；**此子项 PASS**，不据此推断所有复合规则可用。|

输入刺激中特别保留了证据正文的 `R01 `（非 `R01：`）：后者会被旧文件读取器拆入证据自己的 `number`，而比较器只查看证据正文或 `reference`，导致假性的 `PENDING_CONFIRMATION`。探针首次运行曾触发此输入结构差异；已将**探针输入**更正并重跑**原封未动**的 ZIP，最终证据只采用表中的二次实际运行。此差异应作为编号解析兼容变体给分析师审视，不能拿未关联的首次结果冒充数值判断通过。

L1 静态定位（原 ZIP `scripts/check_acceptance.py`）：`conditions` 的复合部署模式固定 `Windows Server 2019`；`evaluate_condition` 把明确编号当候选后没有登录数量/单位/场景语义比较，环境分支专门检测 `Windows Server 2019`，把包含 `失败` 的任何文案记负面；`analyze` 汇总为追踪结论。以上根因与真实文件 L3 输出互证，但 **L2 NOT_TESTED**（本卡没有独立函数替身/单测）；**L4 真宿主对话 NOT_TESTED；L5 WorkBuddy 安装、运行、审核 NOT_TESTED**。其他 V2 边界、全部安全组合与许可证/权属 NOT_VERIFIED；没有发布或上传。

复现：在本产品工作树运行 `python docs/qa/audit-r1-012-baseline-probe.py`（实际 exit 0，仅表示探针完整执行，不表示 20 案业务全 PASS）。对单案，从 JSON `cases[].command` 取准确命令、`input` 中创建 scope.md 和证据文件，在受限临时目录先创建 output 文件夹；命令中的临时路径来自本轮独立 scratch，重跑会变，不要直接复制已清理的路径。每个案的 `actual.requirements[].results`、`xlsx['要求追踪']`、`docx` 回读支撑上述结论。后续修复必须重测明确正反/边界/缺失/改写，而不是把所有状态变成待确认。

**阶段门禁**：原 0.1.2 对 ACC-F01/F02/F03 的上述明确反例 FAIL，不可放行为本轮新版；旧版本原 QA 结论仍保留在原记录。此卡只负责基线，下一张预建分析师卡冻结补充合同，再由开发与独立新版 QA 接力；不修改业务代码、许可证或历史证据。当前阻断项：旧 ZIP 本轮审查业务门禁 FAIL；新版复验 NOT_TESTED。
