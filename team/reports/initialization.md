# 初始化状态（实证快照）
Hermes v0.22.2+1979.g5fc490e；Windows Desktop，CLI 位于 C:/Users/wangbin/AppData/Local/hermes/hermes-agent/.hermes/bin/hermes；Gateway PID 18768，未重启。主仓库基线 ba3c40b76b90ef92151d25e6b054e7738e2fa674 且原有未提交文件；光伏登记路径 F:/ideaWorkSpace/wangbin-workbuddy-dev、分支 solar/phase3e-forward，未访问其业务内容。

四个 Fresh Profile 已由 hermes profile create --no-skills 创建，SOUL 与 config 各自存储，无 API 凭证复制；Desktop Bots 列表可见四行。群聊“星核实验室 · WorkBuddy Skill 开发团队”通过 Desktop UI 创建并选择四个成员；消息回复未验证。独立 Board wb-skill-factory 创建，初始空任务；Gateway dispatcher 配置 dispatch_in_gateway=true，但无 Worker 实跑证据。模型：默认 custom:codex-bz 会话 HTTP 401 Invalid API key；openai-codex 账号对尝试的 gpt-5.5 / gpt-5.3-codex / gpt-5.1-codex 返回 400 unsupported；gemini 试用报告无可用凭证。不得宣称模型可用、调度通过或 TEAM_READY=PASS。

状态：HERMES_CLI_AVAILABLE=PASS；BOT_MODE_AVAILABLE=PASS（界面可见）；PROFILE_SUPPORT_AVAILABLE=PASS；KANBAN_AVAILABLE=PASS；KANBAN_DISPATCHER_AVAILABLE=NOT_TESTED；GROUP_CHAT_AVAILABLE=PASS（创建，消息未测）；MODEL_AUTH_AVAILABLE=BLOCKED；GIT_WORKTREE_AVAILABLE=PASS；FACTORY_REUSE_AVAILABLE=PASS（python -m tooling.products list）；SOLAR_PROTECTION_BASELINE=PASS（仅登记识别）；OS 隔离=SOFT_ISOLATION_ONLY。
