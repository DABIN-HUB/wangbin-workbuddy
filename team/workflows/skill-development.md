# 六阶段 Kanban 模板
所有卡：board=wb-skill-factory，tenant/product_id=产品 ID，workspace=产品 worktree 的绝对路径，`idempotency_key=产品ID:阶段`，max_runtime=30m（复杂阶段需人工调整），max_retries=1，local-only；每卡写明验收条件，下一阶段依赖上一阶段。
每个产品必须另有一个 `wb-manager` T05 收尾根卡（幂等键 `产品ID:T05`），并把所有必要的开发、QA、修复、复验、打包和推送卡直接或间接依赖到该收尾卡；收尾卡只能核对真实物证、保存报告和汇报，不实现业务代码。
创建后不得依赖用户再次提醒：Ready 由 Gateway Dispatcher 自动领取，Todo 在父任务 Done 后自动晋级，Blocked 通过 `auto_subscribe_on_create`/`notify_in_gateway` 发送 terminal-event；经理收到事件后必须读取卡片、核验失败证据，按 `产品ID:fix:轮次` 幂等创建独立修复卡，并在最多两轮后保持 BLOCKED。
- T00 wb-developer：检查 ID/路径/分支/登记与基线，安全创建独立 worktree，报告可写性与原始状态。
- T01 wb-analyst：交付 requirements.md、input-output-contract.md、acceptance-cases.md，冻结 MVP；依赖 T00。
- T02 wb-developer：实现业务代码、SKILL.md、示例及专项测试，真实运行并本地 commit；必要检查通过后允许自动 push 到该产品远程分支；依赖 T01。
- T03 wb-quality：独立业务准确性、边界、安全和许可核查；依赖 T02，失败走 qa-rework.md。
- T04 wb-quality：现有工厂的实际 ZIP 构建、SHA-256、版本、成员、回归和发布限制；必要验收证据提交后允许自动 push 到该产品远程分支；依赖 T03。
- T05 wb-manager：对照真实任务记录、提交哈希、包、测试和平台未测项完成交付；依赖 T04。
不能靠群聊或普通 CLI 输出代替 Worker 的 kanban_complete/kanban_block。经理需在工作前确认模型与 Dispatcher 可用，并在收尾卡保存最终报告路径、看板状态和通知送达状态。
每次新模板变更必须先用隔离的虚构任务验证：依赖晋级、Ready 领取、Blocked 事件、经理唤醒、独立修复/QA 续跑和 T05 收尾；任一步无真实事件、run 或评论证据均标记 NOT_VERIFIED。
