# CLI 连接器模板

WorkBuddy 的 CLI 连接器必须提供非交互式安装，以及 `auth`、`status`、`unAuth` 命令。这里的包名和认证域名是模板占位值，不代表真实服务，提交前必须替换并完成跨平台、重启恢复和凭证清理验证。

开发或修改 Connector 时，先读仓库根目录 `AGENTS.md`，再完整读取 `agent.md` 和本产品专属冻结合同；执行 `docs/development-task-template.md` 中的测试、清理、dist 保护、显式暂存、本地提交及最终 Git 状态检查。本段只约束仓库开发，不会被平台自动注入 Connector 运行时；禁止自动 push 或发布。
