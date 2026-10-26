# wangbin WorkBuddy Phase 1 设计说明

## 目标

在 `F:/ideaWorkSpace/wangbin-workbuddy` 中建立可持续维护的 WorkBuddy 资产工程，并交付第一个真实可运行的本地候选产品：`wangbin AI 万能文档助手`（英文名：`wangbin AI Document Assistant`，Skill ID：`wangbin-document-assistant`，版本：`1.0.0`）。本阶段完成官方规范核实、独立文档处理引擎、统一校验/测试/打包工具、测试证据和发布候选 ZIP；不登录平台、不上架、不收费、不部署生产环境。

## 范围与非目标

### 本阶段范围

- 核实 WorkBuddy 官方文档；每项平台规则记录原始 URL、核实日期和状态。
- 交付可在本地 Windows 10 上运行的 Python 文档处理引擎。
- 使用 MarkItDown 作为首选解析组件，只有真实能力不足时才评估 Docling。
- 支持 PDF、DOCX、XLSX、PPTX、HTML、TXT、Markdown 的实际读取。
- 实现单文档解析、多文档批处理、Excel 去重/导出、结构化结果、错误隔离和安全限制。
- 建立 Skill、Expert、Connector 的本地模板及结构校验。
- 提供 `validate`、`test`、`package`、`release-check` 命令。
- 生成真实测试夹具、机器可读 JSON 报告、人类可读 Markdown 报告和发布候选 ZIP。

### 非目标

- 不伪造 WorkBuddy 平台专有字段、运行时能力或审核结果。
- 不接入真实模型、企业系统、MCP 服务或外部收费 API；摘要功能只提供可供模型使用的结构化原文输入和明确的本地限制。
- 不默认使用 Docling，不引入浏览器自动化服务，不执行宏、脚本或危险公式。
- 不修改其他项目，不执行 Git commit、push、reset 或分支切换。
- 不自动登录 WorkBuddy、提交审核、发布资产、设置售价或开通变现。

## 设计原则

1. **平台结构与开发结构分离**：本地工程允许有测试、工具和报告，但上传候选包只包含经过明确规则筛选的资源。
2. **事实优先**：官方文档未确认的约束使用 `BLOCKED` 或 `待确认`，不将本地约定写成平台规则。
3. **真实执行**：文档引擎必须调用真实解析库处理真实文件；测试不得用 Mock 替代引擎验证。
4. **最小依赖**：优先 MarkItDown 和 Python 标准库；只有实现目标必须时才增加依赖。
5. **默认拒绝危险输入**：只读输入、限定根目录、限制文件大小/数量/展开大小、隔离输出目录、清理临时资源。
6. **可审计输出**：每个文件都有状态、格式、大小、耗时、提取文本和异常信息；报告记录实际命令和环境。

## 方案比较

### 方案 A：纯 WorkBuddy Skill

优点是发布包小、平台集成简单；缺点是官方运行时是否提供 Python、MarkItDown 及 Office 依赖尚未确认，无法保证七类文档真实处理。仅适合作为最终平台适配层，不能作为本地引擎实现方案。

### 方案 B：Skill + 本地/独立 CLI 文档引擎（采用）

文档处理逻辑独立于平台，CLI 可在本地真实运行，Skill 通过清晰的任务协议调用处理能力。它能先交付本地合格候选包，并把平台运行时兼容性单独列为门禁；如果平台不允许 Python，可在后续不改业务逻辑的情况下替换为 MCP 或平台内置工具适配器。

### 方案 C：Skill + MCP 文档服务

可隔离依赖并适配无法执行 Python 的平台运行时，但需要额外服务生命周期、认证、网络和数据传输审核，当前官方规则尚未确认，超出 Phase 1 的必要范围。

## 组件边界

### 文档引擎

路径：`services/document-engine/`

职责：

- `DocumentEngine.parse_file(path, options) -> DocumentResult`
- `DocumentEngine.parse_many(paths, options) -> BatchResult`
- `SpreadsheetService.deduplicate(...) -> ExportResult`
- `SecurityPolicy` 负责路径、大小、数量、时间、展开大小和输出约束。
- `MarkItDownAdapter` 负责真实格式解析；解析库异常转换为结构化失败，不中断批处理。
- `ResultSerializer` 负责 JSON/Markdown 结果和脱敏错误。

引擎不负责识别自然语言，不负责模型调用，不负责 WorkBuddy 登录。

### 统一工程工具

路径：`tooling/`

- `validator`：检查工程结构、JSON/YAML、版本、资源引用、依赖许可证清单和凭证泄漏。
- `test_runner`：以真实命令运行项目测试，并保存命令、退出码和摘要。
- `packager`：按候选包清单建立临时目录，生成 ZIP，拒绝路径穿越和意外文件。
- `release_check`：串联验证、真实测试和包结构校验，生成门禁报告。
- `generator`：生成 Skill、Expert、Connector 的本地模板，模板只使用已确认的字段。

CLI 入口：

```text
python -m tooling validate
python -m tooling test
python -m tooling package
python -m tooling release-check
```

### Skill 产品

路径：`packages/skills/wangbin-document-assistant/`

包含：

- 产品说明和自然语言触发场景。
- 任务协议、输入/输出约束、失败处理和隐私说明。
- 仅使用官方已确认字段的元数据；未确认字段放在本地候选说明，不伪装为平台规范。
- `scripts/` 中仅放可审计的调用适配脚本，不保存密钥。
- `references/` 和 `templates/` 作为可复用文档资源。

### Expert 与 Connector 模板

路径：

```text
packages/experts/wangbin-expert-template/
packages/connectors/wangbin-connector-template/
```

本阶段实现身份/能力/场景/输入输出/权限/认证占位协议和结构校验，不连接真实系统，不放入真实凭证。模板中的平台专有字段只有在官方文档确认后才进入候选包。

## 数据流

1. 用户或测试命令传入文件路径和任务选项。
2. 安全策略解析绝对路径，校验路径必须位于允许的输入根目录，拒绝符号链接和目录越界。
3. 对 Office ZIP 容器执行条目数、压缩后总大小和单条目大小检查；超限立即失败。
4. MarkItDown 适配器读取文件，不执行宏、脚本或外部网络资源。
5. 引擎生成 `DocumentResult`，包含格式、元数据、标题/章节（能可靠提取时）、文本、质量提示、异常信息和耗时。
6. 批处理按文件隔离异常，继续处理其他文件，并生成每文件状态。
7. 导出器写入独立输出目录，不覆盖输入；CSV/XLSX 输出对 `=`, `+`, `-`, `@` 开头的单元格做公式注入防护。
8. 报告和 ZIP 打包器只读取工程白名单中的文件，生成哈希和清单。

## 错误处理

- 单文件错误返回失败结果，包含稳定的错误类别和脱敏信息。
- 多文件任务中单个文件失败不影响其他文件；批次状态为 `partial_failure`。
- 文件不存在、路径越界、类型不匹配、文件过大、容器展开过大、解析异常和导出校验失败使用不同错误码。
- 临时目录使用上下文清理；进程异常后由 release/test 目录清理步骤清除已知临时目录。
- 不将完整本地路径、用户名、文档内容或凭证写入报告；报告中路径使用相对路径或 `[REDACTED]`。

## 测试和验收

测试位于 `tests/`，用户已明确要求真实测试，因此本阶段生成真实夹具而非 Mock。至少覆盖 PDF、DOCX、XLSX、PPTX、HTML、TXT、Markdown 的实际读取，批处理、空文件、损坏文件、错误扩展名、大小限制、中文/特殊文件名、不存在文件、转换完整性、Excel 去重、部分失败、路径安全、元数据和 ZIP 结构。

测试报告必须列出每个测试 ID 的 `PASS`/`FAIL`/`SKIP`、实际命令、退出码和脱敏错误。平台未登录或无授权时，平台安装和平台运行测试为 `BLOCKED` 或 `NOT_TESTED`，不能与本地测试合并。

## 验收门禁定义

- `PLATFORM_SPEC_PASS`：官方要求已逐项核实；无法读取或确认的项目为 `BLOCKED`。
- `SKILL_SCHEMA_PASS`：仅对已确认字段和本地候选结构通过；平台未确认字段不宣称通过。
- `OPEN_SOURCE_LICENSE_PASS`：依赖许可证可追溯且与发布方式相容。
- `DOCUMENT_ENGINE_PASS`：七类真实文件均完成读取和结果校验。
- `SECURITY_PASS`：安全策略和对应真实测试通过。
- `INTEGRATION_TEST_PASS`：统一 CLI 端到端执行成功。
- `PACKAGE_VALIDATION_PASS`：候选 ZIP 清单、结构和哈希校验成功。
- `WORKBUDDY_RUNTIME_PASS`：只有在授权的真实 WorkBuddy 环境安装并执行验证后才能通过；否则为 `BLOCKED` 或 `NOT_TESTED`。
- `PUBLISH_READY`：不得只由本地测试决定；平台运行时或资格未确认时为 `BLOCKED`。

## Phase 1 交付物

- `docs/workbuddy-platform-spec.md`
- `docs/architecture.md`
- `docs/development-guide.md`
- `docs/publishing-guide.md`
- `docs/security-guide.md`
- `docs/product-roadmap.md`
- 可运行的 `services/document-engine/`
- 可运行的 `tooling/`
- 首个 Skill、Expert、Connector 模板
- 真实测试夹具和测试报告
- `dist/` 下的发布候选 ZIP、SHA-256 和包清单
- 最终 Git 状态和未解决问题说明
