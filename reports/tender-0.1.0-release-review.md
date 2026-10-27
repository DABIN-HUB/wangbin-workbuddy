# 招标分析 Skill 0.1.0 发布阻断复核

2026-10-27；只审计原有 `0.1.0`，不重打包或覆盖其 ZIP。此报告的 `PASS` 仅限所述本地检查，不是 WorkBuddy 平台验收。

## 原候选完整性与结构

- `dist/wangbin-tender-analyzer-0.1.0-skill-candidate.zip` SHA-256：`2e68809033301c97b02ec7c7fd59f7b477fcd2f1f86d515d69b5fc7b20146bc7`，与保护基线相同。ZIP 本地 readback/testzip 和对应 manifest 的成员哈希检查通过。
- ZIP 只有 `wangbin-tender-analyzer/` 一个资源根，包含 `wangbin-tender-analyzer/SKILL.md`、`scripts/analyze_tender.py`、示例和模板共六个文件；ZIP 顶层**没有**独立 `SKILL.md`。该结构符合官方示例的 `{skill-name}/SKILL.md`，但官方文档未说明上传时外层目录解析的全部边界，因此平台解析标记 `NOT_TESTED`，不可把本地结构检查记作平台通过。
- `SKILL.md` 有双语名称、描述、版本、作者和 `allowed-tools: Read, Bash`。其中的本地命令依赖仓库 checkout 的相对路径，ZIP 安装后工作目录、解压路径与文件访问权限未验证。

## 许可证、依赖与隐私审查

- 此 ZIP **没有** `LICENSE` 或 `NOTICE`；仓库根目录也没有独立 LICENSE。其他 Expert/文档引擎的 MIT 文件和 `pyproject.toml` 的 MIT 元数据，不自动授予本 Skill 独立分发权。权利人、样例许可范围及是否采用 MIT 均需人工确认，故 `LICENSE_DISTRIBUTION=BLOCKED`。不要为了消除检查阻断而复制不属于该产品的声明。
- `scripts/analyze_tender.py` 直接导入的模块均为 Python 标准库：`argparse`、`json`、`re`、`stat`、`sys`、`pathlib`、`typing`。ZIP 中不含 MarkItDown、openpyxl、PyYAML 或其传递依赖；因此当前 ZIP 没有待安装的第三方 Python 包，但**Python 本身在普通 Skill 运行时的可用性未知**。若以后引入文档引擎，须重新审查第三方许可证及运行时。
- 本地输入为单个不超过 1 MiB 的 UTF-8 TXT/MD，不声明 PDF/DOCX/扫描件能力。限长脱敏短摘录无法保证完全去识别；只可在获授权、受控输出环境下核对原文，不将采购原件上传至未授权远端服务。

## 平台门禁

官方资料：[Skill 规范](https://open.workbuddy.cn/docs/skill)说明 `SKILL.md`、可选 `scripts/` 和通过 Bash 调用脚本；[Connector 规范](https://open.workbuddy.cn/docs/connector)中的 Python 托管能力属于 **Connector**，不能直接推断普通 Skill 自动安装 Python/依赖；[开发者公约](https://open.workbuddy.cn/docs/developer-agreement)要求说明运行条件、依赖、权限、数据用途并依法使用第三方资产。本轮没有可确认的授权 WorkBuddy 私有安装会话；未上传、未安装、未真实调用、未提交审核或发布。

| 门禁 | 状态 | 证据 |
|---|---|---|
| 本地代码/ZIP/哈希 | PASS | 源代码校验、ZIP 六成员与 SHA-256 |
| 独立分发许可证 | BLOCKED | ZIP 无 LICENSE；权利归属和授权范围待确认 |
| 普通 Skill Python 与路径/权限 | UNKNOWN | 官方资料未明确运行时机制，未执行平台调用 |
| WorkBuddy ZIP 解析/安装/真实调用 | NOT_TESTED | 没有可确认的授权私有环境或回执 |
| 审核、公开发布、商业化 | BLOCKED | 不能由本地候选推断或代替人工审核 |

## 安全的后续步骤

取得权利人的许可决定后，若仅补齐发行文件，注册 **0.1.1** 并在该新版本产品目录/ZIP 中包含许可全文，保留原 `0.1.0` 候选和哈希；若更改业务逻辑或平台执行方式，用更合适的新版本，不覆盖已有 ZIP。在官方授权的私有安装入口，用虚构样例记录候选 SHA、ZIP 解析、资源路径、Python 可用性、读文件权限和真实对话结果。如入口实际触发正式审核或公开发布，应先获单独确认并停止当前自动流程。
