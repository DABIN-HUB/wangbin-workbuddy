# Phase 4 — 最小可发布功能边界

**结论：现有 1.2.0 文件解析 CLI/Connector 没有可负责任宣称已安全且已可分发的公开发布子集。** 本轮不新增功能、不降低测试标准，也没有悄悄删除某一格式。`security.py` 仍允许 PDF/DOCX/XLSX/PPTX/HTML/TXT/Markdown，`main.py` 仍公开 `parse`、`batch`、`deduplicate`；内嵌 Skill、Connector 市场文案仍描述七类文件与 Excel 去重。因此任何声称“1.2.0 已仅支持简单格式/已关闭 Excel”的介绍都不真实。只收窄宣传不能阻断实际调用，也不能把 `SECURITY_PASS` 转为 PASS。

| 候选边界 | 实际代码/打包状态 | 公开发布判断 |
|---|---|---|
| 现有全格式 CLI + Excel | 1.2.0 wheel、Skill ZIP、Connector ZIP 可本地构建/安装；Windows 解析资源、Excel 主进程、权限及库漏洞未被强隔离，公开包不存在。 | **BLOCKED**。 |
| 禁用 XLSX 或 PDF 等高风险格式后的裁剪版 | **未实施**，而且 DOCX/PPTX/HTML 等仍存在不可信解析、同用户权限问题；简单 TXT/Markdown 当前也经通用 MarkItDown 子进程，不能把它们当成无解析器的纯文本专线。 | **NOT_IMPLEMENTED/BLOCKED**；不能把理论裁剪版冒充现成 MVP。 |
| 不处理文件的纯提示词 Skill/专家（如基于用户在聊天中粘贴的文字整理要点、待办，标注事实与推断） | WorkBuddy 文档有独立 Skill/专家市场和无依赖专家形态；但现有独立 Skill `1.0.0` 明确调用 `scripts/run_document_engine.py`，现有专家也声明预加载它并承诺读取 PDF/XLSX；**现有资产不符合纯提示词边界**。 | **后续更简单的首款产品方向**，不作为本轮现成可发布物；需独立审核文案/提示词、平台私有验收及内容/隐私边界。不能宣称平台模型已摘要或文件已处理。 |

若以后选择缩减格式作为**单独授权的实现阶段**，必须同步：①在 `SecurityPolicy.SUPPORTED_EXTENSIONS` 和 `main.py` 命令/参数入口实拒相关文件，并核查 `DocumentEngine.parse_file/parse_many`、`SpreadsheetService.inspect/deduplicate` 与可直接 import 的路径；②改内嵌/独立 Skill、Expert 依赖与调用示例、Connector 市场描述和 README/发布说明；③在用户明确授权编写测试后新增真实拒绝/允许路径回归（Windows/Linux/macOS 需要相应运行验证），不删除原有安全验收或降低其阈值；④升版、从源码重建三产物、重算 SHA-256，并只让新版本进入候选审核。**上述不是声称已完成的改造清单。** 当前维持 1.2.0 不变，故既不修改现有测试，也不假造禁用测试结果。

更简首品若选择“粘贴文本→来源明确的待办清单/文书草稿”：必须用新的无脚本、无文件解析、无 Connector 依赖的 Skill/专家资产，市场说明写明用户粘贴文本和模型不保证准确；不得复制当前同名 Skill/专家后仅把文案换成纯文本。官方 [Skill](https://open.workbuddy.cn/docs/skill) 与 [专家](https://open.workbuddy.cn/docs/expert) 描述资产结构/市场入口，不构成个人主体审核通过证明。开发者公约要求如实描述运行条件与权限、核心流程可用，见 [公约](https://open.workbuddy.cn/docs/developer-agreement)。

本阶段实际可交付的最小范围 = 1.2.0 **研究/本地候选** + 七份风险/验收报告；**没有被证实可公开发布的文件处理产品**。