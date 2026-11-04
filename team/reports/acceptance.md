# 星核实验室 WorkBuddy Skill Factory 初始化验收（未完成）

## A. Hermes 环境与 Setup 0
- CLI `hermes --version`：v0.22.2+1979.g5fc490e；安装 `C:/Users/wangbin/AppData/Local/hermes/hermes-agent`（git），Windows Desktop，`hermes` 可执行文件在该目录的 `.hermes/bin/hermes`。
- `hermes gateway status`：现有手工 Gateway running PID 18768；未重启。`hermes config get kanban`：`dispatch_in_gateway=true`、`notify_in_gateway=true`、调度间隔 60 秒、默认连续失败限制 2；真实 Dispatcher 领取任务 NOT_TESTED。
- `hermes profile list`：原仅 default；现在新增四个 Fresh Profile，`--no-skills`，无主 Profile 记忆/密钥克隆。各 Profile `.env` 仅三行注释，不包含凭证；`auth list` 暴露根 OAuth/环境凭证条目，不能据此断言物理凭证隔离。Model 均为 `gpt-6.1-sol` / `custom:codex-bz`，目前模型无法实际调用。
- `git worktree list --porcelain`：主 `main` 基线 `ba3c40b76b90ef92151d25e6b054e7738e2fa674`、光伏 `solar/phase3e-forward`，主仓库在预检时已有 13 条 `git status --short` 输出（含用户修改），本次未修改/清理主工作区或光伏目录。
- `python -m tooling.products list` 在主仓库目录运行并列出 10 个既有产品。直接 `python tooling/products.py` 因相对导入失败，正确入口是模块执行；现有工厂不可绕过。

预检：HERMES_CLI_AVAILABLE=PASS；BOT_MODE_AVAILABLE=PASS（桌面 Bots 标签可用）；PROFILE_SUPPORT_AVAILABLE=PASS；KANBAN_AVAILABLE=PASS；KANBAN_DISPATCHER_AVAILABLE=NOT_TESTED；GROUP_CHAT_AVAILABLE=PASS（UI 创建）；MODEL_AUTH_AVAILABLE=BLOCKED；GIT_WORKTREE_AVAILABLE=PASS；FACTORY_REUSE_AVAILABLE=PASS；SOLAR_PROTECTION_BASELINE=PASS（仅从主仓库 Git 登记识别）。系统级隔离：SOFT_ISOLATION_ONLY。

## B. Bot 与群聊
| Profile | 角色（SOUL） | Profile 路径 | 模型 | 工具 | 可真实运行 | Desktop 花名册 |
| --- | --- | --- | --- | --- | --- | --- |
| wb-manager | Skill 项目经理 | `C:/Users/wangbin/AppData/Local/hermes/profiles/wb-manager` | gpt-6.1-sol / custom:codex-bz | 文件、终端、Kanban、网页；多余能力已禁用 | BLOCKED: HTTP 401 | 四行之一 |
| wb-analyst | Skill 需求分析师 | `C:/Users/wangbin/AppData/Local/hermes/profiles/wb-analyst` | 同上 | 同上 | NOT_TESTED（共享配置已知 401） | 四行之一 |
| wb-developer | Skill 开发工程师 | `C:/Users/wangbin/AppData/Local/hermes/profiles/wb-developer` | 同上 | 同上 | NOT_TESTED | 四行之一 |
| wb-quality | Skill 测试与打包工程师 | `C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality` | 同上 | 同上 | NOT_TESTED | 四行之一 |

每个 SOUL 路径是对应 Profile 下的 `SOUL.md`，可版本化副本在 `team/bots/<profile>.md`。模型鉴权实测：`hermes -p wb-manager -z ... -t safe` → custom HTTP 401 Invalid API key；Codex OAuth 虽显示 logged in，但三个尝试模型 `gpt-5.5`、`gpt-5.3-codex`、`gpt-5.1-codex` 均被 HTTP 400 拒绝为不支持；gemini 报告无可用 credentials。未复制密钥、未更改 default 模型。

Desktop Bots 标签四行均显示 `wb-*`。通过 Desktop New Group Chat 勾选四人（未选 Hermes/default），输入名称并创建，标签显示 `星核实验室 · WorkBuddy Skill 开发团队`；群聊消息测试因模型鉴权 BLOCKED。CLI 创建的 Profile 会被列表展示，但是否具有 Bot Mode 托管标记 `ui_meta` 和永久 Bot Chat 没有实证；不可把列表可见等同于完全托管 Bot。UI 角色展示名称目前仍为 Profile ID；Edit Profile 右键操作被许可门禁拒绝且未重试。四位展示标题与花名册托管状态需在得到明确许可后由用户在 Desktop Edit Profile 核验/设置。

## C. Kanban 与流程
`hermes kanban boards create wb-skill-factory --name 'StarCore Lab - WorkBuddy Skill Factory'` 创建独立空 Board；`hermes kanban boards list` 可重读；`hermes kanban --board wb-skill-factory diagnostics` 无活跃诊断。未修改 default Board、全局 Gateway 配置或默认活动 Board。六阶段 T00→T05 模板、独立 QA 缺陷返工、幂等键、证据字段和限制见 `team/workflows/`。模型不可用，因此未创建会被 Dispatcher 自动执行的虚构卡，也未模拟经理真实派单；调度、通知唤醒、自动返工及持久化运行证据均 NOT_TESTED。

## D. Git/worktree
- 团队配置：`F:/ideaWorkSpace/wangbin-workbuddy-team`，`team/skill-factory-v1`，本地提交 `26002233c884f2e54f875428dbf846c08919b69e`（19 个规则/模板/报告文件；后续报告文件另有提交）。
- 虚构联调预备：`F:/ideaWorkSpace/wangbin-workbuddy-team-smoke-test`，`skill/team-smoke-test`，基线 `ba3c40b76b90ef92151d25e6b054e7738e2fa674`；尚无业务代码/提交/ZIP。未访问光伏业务目录，未 push/merge/upload/删除其他 worktree。

## E. Setup 6 实测状态
| 联调项 | 实际动作/命令 | 结果 | 状态 |
| --- | --- | --- | --- |
| 经理接收任务 | 群聊存在；因模型鉴权未发送任务 | 无 Kanban 链 | BLOCKED |
| 需求分析 | 无 Worker 领取 | 无规格产物 | NOT_TESTED |
| 代码开发 | 仅建立独立 smoke worktree | 无代码/测试/commit | NOT_TESTED |
| 故意缺陷检测 | 未写预置业务错误 | 无实际 QA 证据 | NOT_TESTED |
| 自动缺陷返工 | 未运行卡片 | 无修复任务 | NOT_TESTED |
| 重新验收 | 未运行 | 无结果 | NOT_TESTED |
| 候选打包 | 未运行 `python -m tooling.products package` | ZIP 与 SHA-256 不存在 | NOT_TESTED |
| 最终交付 | 本报告由初始化执行者写；不是 wb-manager Worker 的报告 | 不构成 T05 通过 | NOT_TESTED |
| 隔离 | Git 登记确认四目录，团队/联调工作树独立；没有访问光伏业务文件 | 配置/操作软隔离；OS 强隔离未建立 | PASS（软隔离） |
| 任务持久化 | Board 可重读且为空；未重启 Gateway | 运行历史持久化未测 | NOT_TESTED |

状态：PROFILES_READY=PARTIAL；SOUL_CONFIG_PASS=PARTIAL（文件存在，实际会话注入未测）；BOT_ROSTER_PASS=PARTIAL（列表可见，托管标记未测）；GROUP_CHAT_PASS=PARTIAL；KANBAN_BOARD_PASS=PASS；DISPATCHER_PASS=NOT_TESTED；TASK_HANDOFF_PASS=NOT_TESTED；AUTO_REWORK_PASS=NOT_TESTED；WORKTREE_ISOLATION_PASS=PASS（软隔离）；GIT_COMMIT_PASS=PASS（团队配置）；QA_INDEPENDENCE_PASS=NOT_TESTED；PACKAGE_VALIDATION_PASS=NOT_TESTED；DELIVERY_REPORT_PASS=NOT_TESTED。**TEAM_READY=PARTIAL**，不能承接正式 Skill 的自动闭环。

## 最短恢复路径
1. 用户在 Hermes Desktop 的各 Bot Profile 中选择可用模型与合法认证（避免复制主 Profile 密钥）；逐个运行最小会话，确认四个模型真实回复。不要通过修改全局 Gateway 或拷贝 OAuth token 绕过。
2. 用户在 Desktop Edit Profile 设置四个展示标题、核验每个 `Bot Chat` 永久会话与 `ui_meta` 托管；群聊 @wb-manager 发送一次无副作用测试消息，确认仅经理回复。
3. 在 `wb-skill-factory` 由 wb-manager 一次性创建带依赖的六卡虚构任务链，真实经历 T00→T05、故意缺陷→阻断→修复提交→复验→产品工厂打包/验哈希；检查 Gateway 通知能否主动唤醒经理及任务重新进入界面后的持久化。不通过则保持 PARTIAL。
4. 如需超越软隔离，另行决定受限执行账号/权限方案；本轮未触碰既有 NTFS ACL。

## 2026-11-04 重新验证追加证据

### 第一阶段：四个 Profile 实际模型调用

未创建、删除或重建任何 Profile、群聊或 Board；未修改全局模型配置，未重新登录，未重启 Gateway。逐个执行了以下真实请求，并检查返回文本与退出状态：

```text
hermes -p wb-manager config get model
hermes -p wb-manager chat -q "请仅回复：MANAGER_READY" -Q
hermes -p wb-analyst config get model
hermes -p wb-analyst chat -q "请仅回复：ANALYST_READY" -Q
hermes -p wb-developer config get model
hermes -p wb-developer chat -q "请仅回复：DEVELOPER_READY" -Q
hermes -p wb-quality config get model
hermes -p wb-quality chat -q "请仅回复：QUALITY_READY" -Q
```

四个 Profile 的实际配置一致：

```text
active model: gpt-6-sol
provider: custom:codex-bz
base_url: http://172.16.5.65/v1
api_mode: codex_responses
key_env: HERMES_CUSTOM_172_16_5_65_API_KEY
```

结果：四次请求均返回 `custom rejected your API key` / `HTTP 401: Invalid API key`，每次命令最终退出状态为 `1`，没有生成对应的 `*_READY` 回复。配置已不再使用旧的活动模型 `gpt-6.1-sol`；Provider 元数据中仍保留 `gpt-6.1-sol` 模型条目，并存在 `default_model: gpt-5.5` 元数据，但当前活动路由明确为 `gpt-6-sol`，因此没有擅自清理这些元数据。

诊断边界：

- 认证失败：PASS（四次一致的 HTTP 401）。
- 模型不支持：本轮未触发；之前对其他 Codex OAuth 模型的 400 不支持结果仍保留在历史记录中。
- 网络错误：未发现；对 `http://172.16.5.65/v1` 的无凭证 HEAD 请求返回 HTTP 200，说明端点可达。该请求未发送任何凭证。
- Profile 配置错误：未发现 YAML/版本错误；`hermes -p wb-manager doctor` 显示配置版本 v51、无弃用键，但命令在 120 秒达到超时，不能把完整 doctor 作为通过证据。
- 凭证状态：四个 Profile `.env` 仍只有注释，没有明文凭证；进程环境中存在配置引用的变量名，但提供商拒绝其凭证。未输出任何密钥值、Token 或连接凭证。

结论：当前阻断点是 `custom:codex-bz` 的凭证被提供商拒绝，需要用户或凭证所有者提供有效授权/更新凭证后再复验。没有无需外部授权的 Profile 局部修复，因此未修改配置。

### 第二、三阶段门禁

由于四个 Bot 的真实模型调用未全部通过，按任务要求未启动 SOUL 实际生效验证、群聊消息验证、Kanban Worker、T00–T05、虚构 Skill 代码、QA 缺陷返工、ZIP 打包或 SHA-256 验证。原有群聊、Board、团队工作树、联调工作树和 Gateway 均保持不变。

本次状态：`MODEL_CALLS_PASS=FAIL`；`MODEL_AUTH_STATUS=BLOCKED`；`KANBAN_BOARD_PASS=PASS`；`DISPATCHER_PASS=NOT_TESTED`；`TASK_HANDOFF_PASS=NOT_TESTED`；`AUTO_REWORK_PASS=NOT_TESTED`；`PACKAGE_VALIDATION_PASS=NOT_TESTED`；`TEAM_READY=PARTIAL`。
