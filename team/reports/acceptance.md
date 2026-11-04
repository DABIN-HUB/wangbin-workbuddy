# 星核实验室 WorkBuddy Skill Factory 验收记录

> **当前结论（2026-11-04 23:14 本地核查）：`TEAM_READY=PARTIAL`。** 下文 A–E 及多次 401 是各轮历史快照，不代表当前模型或任务状态；最新证据见文末“完整虚构产品联调”。Kanban 七卡均 done，本地候选可核验，但群聊定向路由及经理自动唤醒没有通过证据，许可证与 WorkBuddy 平台验收未完成。不得据此发布正式产品。

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

## 2026-11-04 继续恢复尝试

重新读取并实际调用四个现有 Profile，未创建或重建任何对象：

| Profile | 当前路由 | 实际结果 | 退出状态 |
|---|---|---|---|
| `wb-manager` | `gpt-6-sol` / `custom:codex-bz` / `codex_responses` | `HTTP 401: Invalid API key`，未返回 `MANAGER_READY` | 1 |
| `wb-analyst` | `gpt-6-sol` / `custom:codex-bz` / `codex_responses` | `HTTP 401: Invalid API key`，未返回 `ANALYST_READY` | 1 |
| `wb-developer` | `gpt-6-sol` / `custom:codex-bz` / `codex_responses` | `HTTP 401: Invalid API key`，未返回 `DEVELOPER_READY` | 1 |
| `wb-quality` | `gpt-6-sol` / `custom:codex-bz` / `codex_responses` | `HTTP 401: Invalid API key`，未返回 `QUALITY_READY` | 1 |

复核时 Gateway 仍为 PID 18768，`wb-skill-factory` Board 仍为空且各状态计数为 0，团队工作树无未提交改动。四个模型调用仍未全部通过，后续 SOUL 生效、群聊消息、Dispatcher 领取、T00–T05、QA 返工和 ZIP 打包继续保持 NOT_TESTED；`TEAM_READY=PARTIAL`。

## 2026-11-04 再次请求的模型复测

应用户要求再次分别执行四个当前 Profile 的 `config get model.default`、`config get model.provider` 和低成本 `chat -q '请仅回复：<ROLE>_READY' -Q`。四个当前配置仍是 `gpt-6-sol` / `custom:codex-bz`。`wb-manager`、`wb-analyst`、`wb-developer`、`wb-quality` 均返回 `HTTP 401: Invalid API key`，各自模型请求退出状态均为 1，无任一 `*_READY` 正常回复。未改动配置或凭证。四个模型均未通过，T00–T05、群聊消息、QA 返工及 ZIP 验收继续 NOT_TESTED；`TEAM_READY=PARTIAL`。

## 再次请求：三名 Bot 已恢复，分析师仍阻断

分别执行四个 Profile 当前配置读取以及 `hermes -p <profile> chat -q '请只回复 <ROLE>_READY' -Q`，检查模型输出和内层退出状态：

| Profile | 当前配置模型/提供商 | 本次真实输出 | 退出状态 |
| --- | --- | --- | --- |
| wb-manager | `gpt-6-sol` / `codex-bz` | `MANAGER_READY` | 0 |
| wb-analyst | `gpt-6-sol` / `codex-bz` | `HTTP 401: Invalid API key`，无预期回复 | 1 |
| wb-developer | `gpt-6-sol` / `codex-bz` | `DEVELOPER_READY` | 0 |
| wb-quality | `gpt-6-sol` / `codex-bz` | `QUALITY_READY` | 0 |

`hermes -p ... config get providers.codex-bz.key_env` 和仅打印 `.env` **键名**的检查显示：经理、开发、质量各自 `.env` 配有 `HERMES_CUSTOM_CODEX_BZ_API_KEY`，配置 `key_env` 同名；分析师 `.env` 没有凭证键，配置仍指向旧的 `HERMES_CUSTOM_172_16_5_65_API_KEY`。分析师 Gateway 错误日志明确记录运行时该变量为空，发送了占位凭证并收到 401。当前工具进程中的环境变量非空，但不能据此推断已运行 Gateway 的进程环境相同。未读取、输出或复制任何凭证值。

受既有“不得擅自复制 API Key”约束，未向分析师复制其他 Bot 凭证，未自行切换模型、重新登录或重启 Gateway。用户需自行在分析师 Profile 配置可用授权，并确认 `key_env` 与所配置凭证一致；随后重试分析师真实对话。四名 Bot 未全部通过之前，群聊定向消息、SOUL 注入、Kanban Dispatcher、T00–T05、独立 QA、自动返工、ZIP 和 SHA-256 仍为 NOT_TESTED。`TEAM_READY=PARTIAL`。

## 2026-11-04 完整虚构产品联调（取代上方历史状态）

用户恢复认证后，四个现有 Profile 的真实 `hermes -p <profile> chat -q '请只回复 <ROLE>_READY' -Q` 分别返回 `MANAGER_READY`、`ANALYST_READY`、`DEVELOPER_READY`、`QUALITY_READY`，四次退出码均为 0；没有重建 Profile/群聊/Board、切换模型、复制或展示凭证，也没有重启 Gateway。角色问答实际执行，QA 明确拒绝凭开发声明放行与擅自修改许可证；这不等同于 UI 花名册托管标记或群聊路由验证。

经理在既有 `wb-skill-factory` 派发虚构产品 `wangbin-team-smoke-test`。`hermes kanban --board wb-skill-factory list/stats` 于 23:14 回读七卡全部 `done`、其余状态均为 0；Gateway 当时仍 running，PID 18768。六阶段及返工卡记录：

| 阶段 / 卡 | 真实交付与证据 |
|---|---|
| T00 `t_a9dcd8e6` | 独立 worktree 基线核对；无业务改动。 |
| T01 `t_e044639f` | 分析师交付 `requirements.md`、`input-output-contract.md`、`acceptance-cases.md`；后续由开发提交。 |
| T02 `t_3e7d4971` | 在 `skill/team-smoke-test` 完成虚构 CSV 对账 Skill、示例与专项验证，本地提交 `d08dc3e84c8474157452099a4d7227c5fc5d2e66`。 |
| T03 `t_5458c076` | 独立 QA 第一轮发现 DEL U+007F / C1 U+0085 开头 ID 被错误接受，记录负向探针并 blocked；修复后独立复验：原探针 17/17、补充探针 12/12、目标专项 23 passed。缺陷与复验报告均作为卡片附件。 |
| 返工 `t_9da85b1e` | 经理另建开发卡，修复目标脚本并补专项用例；本地提交 `e65dad32e953531553c2ed8969a5b60fbcd2a7c4`。开发期间额外扩大运行范围（排除 solar-pv）得到 130 passed、5 skipped、2 个基线/环境失败；**不得称全仓库回归通过**。经理核验后解除 T03 阻断，QA 才重新领取。 |
| T04 `t_d5bcf4e6` | 独立质量角色实际使用现有工厂 `package/verify/validate/test`，目标专项 23 passed，verify/validate/test 及 ZIP 完整性通过；T04 报告、ZIP、sidecar、manifest 已附到卡。工厂 `release-check` 实际退出 1 / BLOCKED。 |
| T05 `t_bdddb571` | 经理检查现有包并交付清单；原清单是当时快照，补充清单逐卡核对 T00–T03、修复、当前 Git 和 ZIP，均已附卡；以补充清单纠正原清单的 NOT_VERIFIED 与旧工作树状态。 |

本地候选：`F:/ideaWorkSpace/wangbin-workbuddy-team-smoke-test/dist/wangbin-team-smoke-test-0.1.0-skill-candidate.zip`，5 个 ZIP 成员，SHA-256 `2b8556004e014f912287de84da5430a356feb3074f1f2fca3a8000de5464b72a`。现场重新运行 `python -m tooling.products verify --id wangbin-team-smoke-test` 退出 0，返回 `status: PASS` 和相同哈希；`sha256sum` 与工厂 sidecar、已附卡 ZIP 对照一致。工厂写入的仅目标 catalog 候选元数据及 validation 报告已单独本地提交 `be2831ce47c686e892ac555167d92946dbf16b6e`；提交后产品工作树 `git status --porcelain=v1` 无输出。产物为**本地候选**，不是 WorkBuddy 发布件；未覆盖旧 ZIP 或历史验收材料。

| 最新门禁 | 状态与边界 |
|---|---|
| `MODEL_CALLS_PASS` / `SOUL_RUNTIME_CHECK` | PASS / PARTIAL（四角色真实模型回复；QA 的角色约束回复可核，其他角色问答虽执行但完整输出未保留），不代表物理凭证隔离。 |
| `KANBAN_BOARD_PASS` / `DISPATCHER_PASS` / `TASK_HANDOFF_PASS` | PASS（真实 Worker 领取、产物、逐卡完成与七卡回读），不等于通知唤醒。 |
| `QA_INDEPENDENCE_PASS` / `DEFECT_REWORK_PASS` | PASS（真实缺陷→blocked→单独修复提交→经理解除阻断→QA 独立复验）；自动通知触发经理的链路另记 NOT_VERIFIED。 |
| `PACKAGE_VALIDATION_PASS` / `DELIVERY_REPORT_PASS` | PASS（限本地候选及 T04/T05 证据，不含平台）。 |
| `GROUP_CHAT_PASS` / Bot Mode 托管花名册 | PARTIAL / NOT_VERIFIED：群聊已存在，但未保存可核查的 `@wb-manager` 发送回执、定向响应及其余 Bot 静默证据；不能以经理 CLI 派单冒充群聊成功。托管标记和展示标题未核实。 |
| `AUTO_MANAGER_WAKEUP_PASS` | NOT_VERIFIED：T03 无订阅，未能观察到通知主动唤醒经理；后续人工推进不算自动唤醒。 |
| `WORKTREE_ISOLATION_PASS` | PASS（Git worktree 与操作路径软隔离），不代表 NTFS/OS 强隔离；主仓库/光伏工作树未被本轮操作目标化。 |
| `LICENSE` / `PLATFORM_ACCEPTANCE` / `INDEPENDENT_VALUE` | BLOCKED（目标 LICENSE/授权缺失） / NOT_TESTED（WorkBuddy 安装、对话、审核） / REVIEW_REQUIRED（反重复及独立价值人工审核）。未擅自改既有 PROPRIETARY 许可。 |

**最终 `TEAM_READY=PARTIAL`**：四角色和本地研发→QA→返工→候选打包链路已运行，但群聊定向消息、经理通知唤醒、正式许可与平台门禁未闭环。只有在支持的 Desktop 群聊中实际发出无副作用 `@wb-manager` 消息并核查路由/静默、为经理订阅真实 QA 阻断通知并实测唤醒、由授权人提供许可证且完成平台/独立性审核后，才能重新评估 PASS；本轮未 push、merge、上传或发布。
