# MCP 连接器模板

这是一个结构模板，不是可直接连接的生产 MCP Server。官方要求一个连接器只配置一个 MCP Server；示例凭证使用 `${SERVICE_TOKEN}` 占位符，不得替换为真实密钥后提交仓库。

开发或修改 Connector 时，先读仓库根目录 `AGENTS.md`，再完整读取 `agent.md` 和本产品专属冻结合同；执行 `docs/development-task-template.md` 中的测试、清理、dist 保护、显式暂存、本地提交及最终 Git 状态检查。本段只约束仓库开发，不会被平台自动注入 Connector 运行时；禁止自动 push 或发布。
