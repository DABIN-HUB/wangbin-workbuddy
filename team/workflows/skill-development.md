# 六阶段 Kanban 模板
所有卡：board=wb-skill-factory，tenant/product_id=产品 ID，workspace=产品 worktree 的绝对路径，`idempotency_key=产品ID:阶段`，max_runtime=30m（复杂阶段需人工调整），max_retries=1，local-only；每卡写明验收条件，下一阶段依赖上一阶段。
- T00 wb-developer：检查 ID/路径/分支/登记与基线，安全创建独立 worktree，报告可写性与原始状态。
- T01 wb-analyst：交付 requirements.md、input-output-contract.md、acceptance-cases.md，冻结 MVP；依赖 T00。
- T02 wb-developer：实现业务代码、SKILL.md、示例及专项测试，真实运行并本地 commit；依赖 T01。
- T03 wb-quality：独立业务准确性、边界、安全和许可核查；依赖 T02，失败走 qa-rework.md。
- T04 wb-quality：现有工厂的实际 ZIP 构建、SHA-256、版本、成员、回归和发布限制；依赖 T03。
- T05 wb-manager：对照真实任务记录、提交哈希、包、测试和平台未测项完成交付；依赖 T04。
不能靠群聊或普通 CLI 输出代替 Worker 的 kanban_complete/kanban_block。经理需在工作前确认模型与 Dispatcher 可用。
