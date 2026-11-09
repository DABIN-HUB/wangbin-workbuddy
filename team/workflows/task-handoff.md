# 交接格式与检查
完成卡必须包括 product_id / product_type / task_id / workspace / branch / base_commit / result_commit / changed_files / artifacts / verification_commands / verification_results / blocked_reason / residual_risks。目录与哈希必须是真实值；没有改变提交时 result_commit 写 NOT_APPLICABLE。命令与退出码照实记录，未执行项 NOT_TESTED。下游读取 parent handoff 前验证相应文件与提交存在；同一产品只允许一个业务写入者。每次失败保留证据与阻塞理由，不重放不确定的写操作。

## Manager Checkpoint（阶段事实索引，不是任务数据库）
在已有 `F:/ideaWorkSpace/wangbin-workbuddy-delivery/reports/` 下，以 `manager-checkpoint-<product_id>-<阶段>.md` 留简短快照；不创建新的产品工作树，不保存密钥/个人数据或大段原始日志。至少记录：product_id、product_type、唯一正式目录、分支及完整本地 HEAD、精确远端 HEAD 和同步状态、冻结需求版本与路径、已完成任务 ID、Running/Ready/Todo/Blocked（及 Review）任务 ID 与依赖、最近的真实独立 QA 结论与证据、候选 ZIP 路径及 SHA-256（无则 NOT_APPLICABLE）、未决问题、授权/禁止操作、**下一步唯一动作**、北京时间交接时间及原始依据路径/任务 ID。不可用或未知的值写 NOT_VERIFIED，不从旧聊天猜测。

安全轮换仅在产品 T05、跨产品切换或复杂返工收口且没有未交接的开发、QA、Git push 时进行；不按定时器中断任务。确认 `wb-manager` 的当前实际会话与 Gateway/Dispatcher 状态；旧会话完成 Checkpoint 并停止对同一批任务派单后，在同一个 Profile 的 Hermes 支持界面执行 `/new`（若 CLI `hermes -p wb-manager chat -q` 启动经核实会创建新会话，也可用于独立受控接班验证；`/new` 不是 shell 命令）。不删除旧会话，不修改 Hermes 私有数据库/伪造 Gateway 路由；有运行中任务时只能只读观察，不强制结束。

新会话依次完整读取仓库根 `agent.md`、本 Checkpoint、当前 `wb-skill-factory` 的 Running/Ready/Todo/Blocked/Review 状态及必要的 Done 摘要、相关产品 Git HEAD/远端；逐项标记快照与实时状态差异，仅接续现有未完成卡（按 idempotency_key 查重），核实 Dispatcher 和真正的通知订阅。QA 独立检查读取证据、角色/会话 ID、任务依赖和交接前后任务数量；没有观察到新会话真实模型调用与接班时写 `SESSION_HANDOFF_NOT_VERIFIED`。通知订阅存在不证明事件唤醒新会话；未观察到投递、模型调用和处理链时分别写 NOT_VERIFIED。
