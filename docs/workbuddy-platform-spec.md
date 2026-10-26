# WorkBuddy 平台规范核实记录

- **核实日期**：2026-10-26（中国标准时间）
- **项目**：wangbin AI 万能文档助手
- **产品版本**：1.0.0
- **核实方式**：官方文档页面直连 HTML 读取（HTTP 200）并用官方站点搜索结果交叉检查。`web_extract` 在当前环境无法使用，因此没有把提取失败误判为规范不存在。
- **原则**：下面只把官方页面明确写出的内容记为 `PASS`；未写明、无法在无账号环境验证或依赖人工审核的事项记为 `BLOCKED`/`NOT_TESTED`。

## 状态定义

- `PASS`：官方文档已明确，并已记录对应实现或验证方式。
- `FAIL`：已确认实现不符合官方要求。
- `BLOCKED`：需要登录、人工认证、平台审核、真实运行时或官方未明确说明，当前不能确认。
- `NOT_TESTED`：本地尚未执行对应验证，不代表平台失败。

## 官方来源与要求

| 主题 | 官方原始链接 | 核实结果 | 关键事实 | 当前实现/影响 |
|---|---|---:|---|---|
| Skill 展示与安装 | https://open.workbuddy.cn/docs/skill | PASS | Skill 位于 WorkBuddy 市场；用户可安装后在对话中调用。 | `packages/skills/wangbin-document-assistant/` 按官方 Skill 结构准备。 |
| Skill 基础目录 | https://open.workbuddy.cn/docs/skill | PASS | `SKILL.md` 必须；`references/`、`scripts/`、`templates/` 可选。 | 候选 Skill 保留这三个可选目录，并只引用包内相对路径。 |
| Skill frontmatter | https://open.workbuddy.cn/docs/skill | PASS | 使用 YAML frontmatter + Markdown；必填字段为 `name`、`display_name`、`display_name_en`、`description`、`description_zh`、`description_en`、`version`、`author`；`examples_zh`、`examples_en`、`allowed-tools` 可选。 | `SKILL.md` 只使用上述已核实字段，不加入猜测字段。 |
| Skill 资源引用 | https://open.workbuddy.cn/docs/skill | PASS | `references` 可由 `@references/xxx.md` 引用；脚本由 AI 通过 Bash 调用。 | `SKILL.md` 明确调用命令、输入输出、失败状态和相对路径。 |
| Skill ZIP 解析 | https://open.workbuddy.cn/docs/skill | BLOCKED | 文档说明提交 ZIP 后可能解析失败，并要求检查基础结构，但没有在可读取正文中明确“ZIP 根目录必须直接是资源目录”还是允许额外包裹目录。 | 打包器保留单一候选资源根目录并执行本地结构校验；准确上传根层级待平台无账号试传或官方进一步说明后确认。 |
| Expert 基础目录 | https://open.workbuddy.cn/docs/expert | PASS | `.codebuddy-plugin/plugin.json`、`avatars/`、`agents/`、`README.md`；plugin.json 为核心配置。 | `packages/experts/wangbin-expert-template/` 使用官方目录。 |
| Expert plugin.json | https://open.workbuddy.cn/docs/expert | PASS | `name`、`expertType`、`version`、`description`、`author`、`agents`、`agentName` 及展示字段有明确说明；展示字段包括 `displayName`、`profession`、`displayDescription`、`avatar`、`categoryId`、`defaultInitPrompt`、`plugin`、固定 3 个 `tags`、固定 3 个 `quickPrompts`。 | 模板使用 `expertType=agent`、`categoryId=04-DataAI`，并校验固定 3 个标签/快捷提示。 |
| Expert Agent frontmatter | https://open.workbuddy.cn/docs/expert | PASS | Agent Markdown 需要 YAML frontmatter；`name`、`description`、`displayName`、`profession` 必填；`maxTurns`、`skills` 可选；开发者不可自行添加 tools。 | 模板不声明自定义工具权限，能力边界写入正文。 |
| Expert 图像 | https://open.workbuddy.cn/docs/expert | PASS | PNG 推荐或 JPG；512×512；单张不超过 500KB；头像需符合定位。 | 本地生成简单原创图标，发布包不使用第三方 Logo。 |
| Connector 方式选择 | https://open.workbuddy.cn/docs/connector | PASS | 只能在 MCP + Skill 与 CLI + Skill 中二选一，不能混用；已有 API 优先 MCP，已有稳定跨平台 CLI 才选 CLI。 | 本阶段只做两种未来模板，不声明一个连接器同时支持两种方式。首个产品本身先作为 Skill 候选，不接真实连接器。 |
| MCP Connector 目录 | https://open.workbuddy.cn/docs/connector | PASS | 必须包含 `connector-meta.json`、`mcp.json`、`icon.svg`；`skills/` 可选。一个连接器只能配置一个 MCP Server。 | MCP 模板提供单 Server 示例，所有凭证使用变量占位。 |
| CLI Connector 目录 | https://open.workbuddy.cn/docs/connector | PASS | 必须包含 `connector-meta.json`（`type=cli`）、`cli.json`、`icon.svg`；`skills/{skill-name}/SKILL.md` 强烈推荐。 | CLI 模板提供 macOS/Linux/Windows 命令示例，未连接真实服务。 |
| Connector CLI 运行时 | https://open.workbuddy.cn/docs/connector | PASS | 可在 `cli.json` 声明 Node/Python runtime；Python 运行时自 WorkBuddy 5.0.0 起支持；不要依赖用户系统 Python 或写死绝对路径。 | 文档明确说明候选本地引擎不等于平台 CLI 运行时已验证；若后续包装为 CLI Connector，应声明 `runtime.type=python`。 |
| Connector 凭证 | https://open.workbuddy.cn/docs/connector | PASS | 不得硬编码 Token/密钥；MCP Token 模式使用 `token-schema.json` 和 `${VAR}`；敏感字段必须 password；日志不得输出完整凭证。 | 模板只使用 `${SERVICE_TOKEN}` 等占位符，仓库扫描拒绝真实凭证。 |
| MCP 远程要求 | https://open.workbuddy.cn/docs/connector | PASS | 远程 MCP 使用 HTTPS、SSE 或 streamableHttp；工具描述、返回错误和超时需清晰；建议单次请求 30 秒内响应。 | 本阶段不启动远程服务；模板中的 URL 是明显示例且不作为可运行服务声明。 |
| Connector 兼容版本 | https://open.workbuddy.cn/docs/connector | PASS | 使用带最低版本的字段时，应在 `connector-meta.json` 声明 `minWorkbuddyVersion`；不同字段有明确最低版本。 | 模板不使用超出基础版本的字段，或按规则补齐最低版本。 |
| 个人认证 | https://open.workbuddy.cn/docs/onboarding | PASS | 个人认证需中国大陆二代身份证、实名手机号、邮箱和人脸识别；一个身份证全平台只能认证一个个人主体；每账号最多一个个人主体。 | 项目未执行实名或人脸认证；资格的官方条件已知，当前账号主体状态为 `BLOCKED`。 |
| 开发者资料 | https://open.workbuddy.cn/docs/developer-profile | PASS | 开发者头像、昵称、20–120 字简介和至少一种联系方式等有明确要求；公开信息需真实、合规。 | 只生成市场文案，不填平台资料；头像/昵称/联系信息发布前需人工配置。 |
| 开发者公约 | https://open.workbuddy.cn/docs/developer-agreement | PASS | 资产须真实可用，须说明运行条件、测试方式、依赖、收费、权限和数据用途；不得伪造功能/结果、越权读文件、泄露凭证、隐藏恶意依赖或未经授权外传数据；第三方代码、数据、品牌需有合法依据并遵守许可证。 | 报告、README、Skill 和安全文档披露限制；本地引擎只读、输出隔离、不执行宏/脚本，不外传文件。 |
| 付费资产 | https://open.workbuddy.cn/docs/monetization | PASS | 可发布免费或付费 Skill/Expert；付费方式为一次性买断或按月订阅；付费资格需要入驻资料审核和微信签约；当前付费能力有内测限制。 | 本阶段不设置售价、不签约、不发布付费资产；市场文案按免费候选处理。 |
| 发布与审核 | https://open.workbuddy.cn/docs/skill、https://open.workbuddy.cn/docs/expert、https://open.workbuddy.cn/docs/connector | BLOCKED | 文档要求上传 ZIP/提交审核，但真实解析、审核反馈和版本发布需要平台账号与人工操作。 | `WORKBUDDY_RUNTIME_PASS`、平台安装验证、平台功能验证和 `PUBLISH_READY` 保持 BLOCKED/NOT_TESTED。 |
| 版本更新 | https://open.workbuddy.cn/docs/buddy-app、https://open.workbuddy.cn/docs/connector | PASS | Buddy 应用更新需重新提交审核；Connector 更新需重新提交审核；Skill/Expert 的具体版本替换流程未在本次读取范围内明确。 | 已确认的更新规则写入发布指南；Skill/Expert 版本更新细节若未明确继续标记 BLOCKED。 |
| 许可证 | https://open.workbuddy.cn/docs/developer-agreement | PASS | 使用第三方代码、模型、数据或接口必须有合法依据并遵守开源许可证。 | 生成依赖清单和第三方声明；最终许可证相容性依赖实际安装包元数据。 |
| 外部 API/数据 | https://open.workbuddy.cn/docs/developer-agreement、https://open.workbuddy.cn/docs/connector | PASS | 访问用户数据需说明数据类别、用途、接收方和保留安排；连接器遵循最小权限和认证。 | 首个产品默认本地处理，不向外部服务发送文档；模型摘要仅作为平台侧后续能力，不在本地假造调用。 |
| Windows/macOS/Linux | https://open.workbuddy.cn/docs/connector | PASS（CLI 规则） | CLI Connector 至少支持 macOS 和 Linux，建议 Windows；WorkBuddy 可托管声明的 Python/Node runtime。 | 本地引擎在 Windows 真实执行；macOS/Linux 跨平台只做代码级路径与命令设计，未在三平台实机运行，记为 NOT_TESTED。 |
| 平台运行时 | 官方 Skill/Connector 文档 | BLOCKED | Skill 的 Bash 脚本可调用方式已明确，但 Skill 包中 Python 依赖如何安装/托管未在 Skill 页面明确；Connector 的 Python runtime 仅适用于 Connector。 | 本地 Python 引擎 PASS 不等于 Skill 在 WorkBuddy 中可运行；需要平台账号和实际安装调用验证。 |
| 平台测试环境 | 官方页面与当前环境 | BLOCKED | 当前没有已授权 WorkBuddy 开发者账号、安装沙箱或平台测试凭证。 | 不执行登录、实名认证、上传、审核、发布或付费操作。 |

## 设计结论

1. **本地实现路径**：独立 Python 文档引擎 + MarkItDown + 本地 CLI，真实处理七类文件。
2. **WorkBuddy Skill 候选路径**：按官方 `SKILL.md` frontmatter 和资源目录制作；脚本调用协议清晰，但不宣称平台脚本运行时已经满足 Python 依赖。
3. **未来 Connector 路径**：若需要在 WorkBuddy 中稳定托管 Python 依赖，应把文档引擎包装成单独的 CLI Connector，使用官方 `cli.json` 的 Python runtime 规则；不能把 MCP 与 CLI 混在同一个连接器包中。
4. **Docling**：当前官方平台规范不要求 Docling；只有 MarkItDown 对目标格式的真实测试出现不可接受失败时才评估。
5. **候选 ZIP 根层级**：官方页面明确资源结构，但未明确上传 ZIP 根目录层级。打包器会产生一个可审计的单一资源根目录并把此项列为 BLOCKED，待平台试传或官方答复确认。

## 当前平台门禁

| 门禁 | 状态 | 原因 |
|---|---:|---|
| `PLATFORM_SPEC_PASS` | PASS（规范核实层面） | Skill/Expert/Connector/认证/公约等官方规则已读取并记录；ZIP 根层级和平台运行时仍单独 BLOCKED。 |
| `SKILL_SCHEMA_PASS` | PASS（本地结构层面） | 采用官方已确认 frontmatter 和目录；平台上传解析未测试。 |
| `OPEN_SOURCE_LICENSE_PASS` | 待本地依赖扫描 | 需安装实际依赖后生成清单并检查许可证。 |
| `DOCUMENT_ENGINE_PASS` | 待执行 | 需真实处理七类文件。 |
| `SECURITY_PASS` | 待执行 | 需运行安全测试。 |
| `INTEGRATION_TEST_PASS` | 待执行 | 需运行统一 CLI。 |
| `PACKAGE_VALIDATION_PASS` | 待执行 | 需生成并重读候选 ZIP。 |
| `WORKBUDDY_RUNTIME_PASS` | BLOCKED | 无授权平台运行环境。 |
| `PUBLISH_READY` | BLOCKED | 平台安装/运行、主体资格和 ZIP 根层级未完成真实验证；本轮只交付本地合格候选包。 |

## 官方链接汇总

- https://open.workbuddy.cn/docs
- https://open.workbuddy.cn/docs/skill
- https://open.workbuddy.cn/docs/expert
- https://open.workbuddy.cn/docs/expert-team
- https://open.workbuddy.cn/docs/connector
- https://open.workbuddy.cn/docs/onboarding
- https://open.workbuddy.cn/docs/developer-profile
- https://open.workbuddy.cn/docs/monetization
- https://open.workbuddy.cn/docs/developer-agreement
- https://open.workbuddy.cn/docs/buddy-app
- https://open.workbuddy.cn/docs/third-party-app
- https://open.workbuddy.cn/docs/openapi
- https://open.workbuddy.cn/docs/service-categories-enterprise

## Phase 2 重新核对（2026-10-26）

- https://open.workbuddy.cn/docs/skill：脚本由 AI 通过 Bash 执行，但**未确认**普通 Skill 的 Python 依赖自动安装/托管；官网展示 `{skill-name}/SKILL.md` 示例，但没有明确上传 ZIP 外层根解析行为。旧版 1.0.0 Skill 依赖 `WANGBIN_ENGINE_SRC` 或已有本地引擎，不能作为普通用户可运行交付。
- https://open.workbuddy.cn/docs/connector：CLI Connector 必含 `connector-meta.json`、`cli.json`、`icon.svg`，`skills/{name}/SKILL.md` 强烈推荐。`init.{darwin,linux,win32}` 必填，`auth` 按需；仅**有认证时** `unAuth`、`status` 是条件必填。`statusMatch`/`statusMatchJson` 二选一。Python `runtime.type=python` 自 WorkBuddy 5.0.0 支持，托管隔离 venv；建议 `python -m pip install <package>`。本地无外部账号模式在 `cli.json` 不声明 `auth`/`unAuth`，只保留真实只读 `status`；CLI 本身的诊断命令仍提供 `auth`/`logout`。无账号模式能否在平台被视为已连接：**BLOCKED**。
- https://open.workbuddy.cn/docs/connector：没有可确认的打包 wheel 到 Connector ZIP 后供 `init` 使用的标准相对路径变量；不能猜测工作目录。本轮版本化 `pip install wangbin-document-cli==1.1.0` 的 CLI 包仅存在本地 wheel；公开索引查询 HTTP 404，平台获取与真机安装：**BLOCKED**。
- https://open.workbuddy.cn/docs/connector：CLI 至少支持 macOS、Linux，Windows 为建议支持；Windows 本地实测已完成，macOS/Linux 当前 `NOT_TESTED`。Connector 发布须提交审核，未获授权不执行。
- 上述追加不改变本文件 Phase 1 原始门禁记录；Phase 2 的实测与未关闭门禁在 `reports/phase2-acceptance.md` 分别列明。

## Phase 3 重新核对（2026-10-26）

- 再次读取 `https://open.workbuddy.cn/docs/connector`：CLI + Skill 目录、`runtime.type=python`、`init.{darwin,linux,win32}`、命令退出码和 JSON 输出要求保持不变。官方明确 Python 自 WorkBuddy 5.0.0 支持，WorkBuddy 托管虚拟环境并隔离 pip/cache；建议 `python -m pip install <package>`，禁止 `pip install --user`，不得依赖用户系统 Python。
- 官方字段表确认：`auth` 按需；有认证时 `unAuth.{platform}` 和认证状态 `status.{platform}` 必填；`statusMatch`/`statusMatchJson` 二选一。由于本产品无外部账号，`cli.json` 不添加伪造 OAuth/Token 配置；CLI 本身的 `auth`/`logout` 只返回无远程会话说明。平台是否接受无账号 Connector 的连接状态仍需真机验证，保持 `BLOCKED`。
- 官方命令时限：`init` 最长 5 分钟且应非交互；有认证时 `auth` 10 秒、`status` 10 秒、`unAuth` 30 秒；本产品不声明认证命令，因此不把这些认证轮询规则外推为本地运行通过。
- 官方 Skill 页面仍只确认 `SKILL.md`、`references/`、`scripts/`、`templates/` 结构和 Bash 调用；未确认普通 Skill 自动托管 Python/MarkItDown，也未明确 ZIP 外层根目录解析。独立 Skill 仍仅作为 CLI 工作流说明。
- Phase 3 采用 1.2.0：`init` 增加 `--no-input` 和 `--disable-pip-version-check`，保持 `--only-binary=:all:` 和固定版本。公开 PyPI 查询仍为 HTTP 404；没有执行注册、上传或 GitHub Release，因此分发来源和 WorkBuddy 安装继续 `BLOCKED`。
