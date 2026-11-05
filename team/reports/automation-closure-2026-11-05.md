# wb-skill-factory 自动推进收尾核验

- Board: `wb-skill-factory`
- Date: 2026-11-05
- Scope: 清理过期依赖链、核对 Gateway/Dispatcher/通知配置、更新后续 Skill 编排模板。

## 看板核验

本轮开始时 Dashboard 所见 4 张 Todo 为历史 `wangbin-supplier-reconciliation` 替代链：

- `t_1339aa1a`：FIX-1，父 `t_18e342ea`，wb-developer；无 Worker run，等待被阻断父卡。
- `t_84b98a36`：M，父 `t_18e342ea`，wb-manager；无 Worker run，等待被阻断父卡。
- `t_c96ff182`：Q2，父 `t_1339aa1a`，wb-quality；无 Worker run，等待父卡。
- `t_bd947992`：M2，父 `t_c96ff182`，wb-manager；无 Worker run，等待父卡。

四卡均已有 superseded 评论，实际交付链为 `t_cb55636d` → `t_f4a26e1d` → `t_9d85cdb2`，因此按官方 CLI 归档而非强制 Done 或删除。原阻断 `t_18e342ea` 也已归档；历史评论、事件和证据保留。

最终现场统计：`todo=0, ready=0, running=0, blocked=0, review=0, triage=0, done=22`。

## 调度核验

- Gateway：running，PID 18768，手工进程而非 Windows 服务；未重启。
- Dispatcher：Gateway 内置 dispatcher 真实运行，历史日志存在多次 `spawned` 与 `reaped` 记录。
- 配置已显式设置：`dispatch_in_gateway=true`、`notify_in_gateway=true`、`auto_subscribe_on_create=true`、`auto_decompose=true`、`orchestrator_profile=wb-manager`、`default_assignee=wb-manager`、`failure_limit=2`、`dispatch_interval_seconds=60`。
- `hermes config check`：exit 0；`hermes --profile wb-manager config get kanban` 返回上述值。
- 四个 Bot 均具备 Kanban 工具权限；Gateway 当前服务 wb-analyst、wb-developer、wb-manager、wb-quality。

## 隔离控制验证

控制卡 `t_353c1ce2`（tenant=`wb-skill-factory-automation-test`）真实经历：创建为 Ready → Gateway Dispatcher 领取并 spawn `wb-quality` → Worker run 28 使用 `kanban_block`，返回 `AUTO_WAKE_RECHECK_BLOCK`，exit 0 → 订阅存在 `notify+wake`。

但是截至本报告核验，没有观察到 `wb-manager` 的自动唤醒 run，也没有 `AUTO_WAKE_RECHECK_HANDLED` 评论；因此经理自动唤醒、自动建修复卡、修复后 QA 续跑及最终 T05 自动收尾均保持 `NOT_VERIFIED`。控制卡随后已归档，未修改源码、未创建修复卡。

## 模板变更

- `team/workflows/skill-development.md`：要求每个产品创建 wb-manager T05 收尾卡、完整依赖链、幂等修复卡和隔离自动化验收。
- `team/bots/wb-manager.md`：规定收到 Blocked terminal-event 后查重、核证、最多两轮独立修复，并记录通知送达状态。

平台/许可证/发布仍按真实证据保持 NOT_TESTED/BLOCKED；本报告不代表 WorkBuddy 平台发布通过。
