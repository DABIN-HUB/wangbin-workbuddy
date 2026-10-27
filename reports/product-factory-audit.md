# 产品工厂实施前能力审计（2026-10-27）

## Git 与保护基线

开始时 `main`、`HEAD=ed30c1a68536e84ecd1219468133b7d72965e9c9`，`git status --short --untracked-files=all` 为空。`dist/` 与 `.venv/` 被忽略，不能仅凭 Git 状态断言候选不存在。独立 Expert ZIP `dist/wangbin-software-consultant-1.0.0-expert-candidate.zip` 实测 SHA-256 为 `577f3089d2f4707178f44ba1e5c395a99853bb9558f3e8c0e752a0e6ba2e30de`；本轮不改其源码或 ZIP。

## 产品与证据状态

| 资产 | 已存在功能 | 当前可核实结论 |
|---|---|---|
| `wangbin-document-assistant` Skill 1.0.0 | 引擎任务路由及文档输入协议；参见 `packages/skills/wangbin-document-assistant/SKILL.md:1-67` | 本地候选；Skill 自动安装 Python 依赖与平台调用未经证明；`README.md:41-57` |
| `wangbin-document-cli` CLI Connector 1.2.0 | 跨平台 CLI 配置、独立 wheel/候选 ZIP；参见 `README.md:59-69` | 可信索引分发、平台安装及运行仍 BLOCKED；`reports/phase3-final-summary.md:34-44` |
| `wangbin-software-consultant` Expert 1.0.0 | 无额外工具依赖的需求/报价指导；`packages/experts/wangbin-software-consultant/README.md` | 用户报告已提交审核，记 `USER_REPORTED_SUBMITTED`；仓库最后一次有记录的平台上传返回中文名称超限，修正版是否重新上传、审批结果尚缺平台回执；`reports/phase8-platform-name-fix.md:8-20,157-170`。绝不标 APPROVED |
| 既有 Expert、CLI/MCP Connector 模板 | 目录/字段示例 | 模板不是已发布产品；`packages/experts/wangbin-expert-template/`、`packages/connectors/*-template/` |
| 五个新候选 | 用户提出的领域需求 | 仅登记为 BACKLOG，招标分析 Skill 本轮进入 DEVELOPING；不虚构平台数据 |

`reports/git-review.md` 等早期报告以当时的未提交工作树为前提，不是当前 Git 状态；旧 `docs/publishing-guide.md` 中“未上传”也已被 Phase 8 的一次失败上传覆盖。软件顾问用户新陈述记录为独立证据，不将仓库的旧失败回执推断为当前平台最终审核状态。

## 能力复用与缺口

- `tooling/cli.py:17-54` 已有 `validate/test/package/release-check`，仅面向早期单一文档助手；新增命令应在独立入口，旧命令不变。
- `tooling/generators.py:8-35` 已能生成基础 Skill；Expert/Connector 模板可作为单一来源，初始化时需处理 ID、目录、包名、发布路径冲突，不覆盖原文件。
- `tooling/validators/project_validator.py:34-160` 涵盖基础结构、前言与 MCP/CLI 类别；`tooling/validators/secret_scanner.py` 只检查部分凭证模式，不能代替人工隐私与授权审查。
- `tooling/phase5_expert_packager.py:34-83` 比 `project_validator.py:60-85` 严格得多，包含中文展示名 ≤15、双语字段、三个标签/提示词、Agent 一致性、PNG 512×512/500KB、无运行时依赖等。抽取通用严格规则时保留 Expert 专有 ID/版本/类目及字节级 ZIP 验证；不得降级为现有通用宽松校验。
- `tooling/phase5_expert_packager.py:94-121` 已有稳定 ZIP 时间戳/权限/成员顺序及逐字节读回；可复用算法，但不能改其现有候选结果。
- 引擎 `services/document-engine/src/wangbin_document_engine/models.py:17-30` 返回提取文本/质量提示，但无页码、文档单元格坐标；招标分析证据应基于确切文本引文与文本行，不造页码。扫描件和复杂表格需待人工核对。

## 安全、许可证与平台限制

`reports/phase4-threat-model.md:7-16` 指出 Windows CPU/内存硬隔离、后代进程回收、同用户权限与数据流仍有高风险，旧 CLI 不可宣称已适用于公开不可信文档。`docs/third-party-notices.md:20-29` 提醒依赖的许可证元数据并非再分发法律审查完成。既有 `tooling/release_check.py:46` 将局部验证+测试视作 `SECURITY_PASS` 是旧 Phase 1 报告语义；不能用于新产品的整体安全发布判定，新的门禁必须保持保守。

官方页面 `https://open.workbuddy.cn/docs/skill`、`/expert`、`/connector` 和 `/developer-agreement` 本轮通过 HTTP 200 读取（标题分别为“技能”“专家”“连接器”“WorkBuddy 开放平台开发者公约（试行）”），仓库已整理字段和平台未验证边界于 `docs/workbuddy-platform-spec.md`。公开文档不能证明当前账户审核、安装、对话或支付资格。平台真实安装与调用必须由账号所有者在授权入口完成并保留脱敏回执。
