# Phase 3 最终阶段报告——发布候选，**不是正式上架**

> 本文保留 Git 安全收尾前的历史验收快照。以下旧 wheel SHA-256 **已经失效**，不得用于任何发布清单；本轮重新构建的 1.2.0 候选、真实双平台回归及更新后的九项门禁见 `git-review.md`。旧测试输出原样保留，不冒充新产物的证据。

项目 `F:/ideaWorkSpace/wangbin-workbuddy`；候选 `1.2.0`；Windows 10 / Python 3.12.0 与 Linux Docker / Python 3.12.15 实测。Git 分支 `main`，历史提交数 0，本轮未 commit、push、reset、切换分支、发布 PyPI/Release、上传 WorkBuddy 资产、提交审核或设置收费。Phase 2 的 1.1.0 产物与 `28 PASS / 0 FAIL / 1 SKIP` 历史报告保留，Phase 1 的 T15 通用转换仍为 SKIP。

## 本轮生产变更

- 引擎 `process_runner.py`：每文件独立解析进程，父进程 wall-clock 超时终止并清理；POSIX CPU/地址空间 rlimit；默认地址空间限额由 1 GiB 调至 2 GiB。安全复核发现旧的跨进程 pickle 会暴露父进程，最终 wheel 已改为长度受限 JSON IPC 并重新实测；**进程仍不是安全沙箱**。Windows 的 CPU/内存硬限尚无实现；Python 最低版本收紧至 3.12。
- `spreadsheets.py`：临时 XLSX/CSV 写入、重新打开校验、原子替换以及异常清理，继续公式文本转义；仍在主进程运行，不宣称强资源隔离。
- wheel / Connector / Skill 升至 1.2.0；Connector `init` 固定版本、非交互、仅从 wheel 安装，但公开 `wangbin-document-cli==1.2.0` 尚不存在，平台安装不能成功闭环。
- 准备 `.github/workflows/phase3-cross-platform.yml` 和需本人手动授权的受保护 PyPI Trusted Publishing 工作流，**均未触发**；生成六份 Phase 3 报告与独立 1.2.0 候选。

## Git 收尾之前的历史候选证据（旧哈希已失效）

运行：`uv build --wheel services/document-engine --out-dir dist --python .venv/Scripts/python.exe -q`；`.venv/Scripts/python.exe -m tooling.phase3_packager`；解开并检查 wheel 源码/名称/版本元数据、Skill 和 Connector ZIP 白名单成员、逐成员 SHA-256，并对照 1.1.0 三个历史文件的 SHA-256，写入 `dist/wangbin-document-cli-1.2.0-candidate-manifest.json` 与三个 `.sha256`。此打包器的 `status=PASS`、`status_scope=package_structure_only` **仅表示包结构验证成功**，不是分发/平台安全结论。

| 文件（`dist/` 下） | SHA-256 |
|---|---|
| `wangbin_document_cli-1.2.0-py3-none-any.whl` | `c47d4536ee8167ec35fdb3679e2289c582eaa5a8d45da37d6a5e2681520cd97e` |
| `wangbin-document-assistant-1.2.0-skill-candidate.zip` | `38133ee51a91db38091032c60ecb4b84db9e3c63e9953307575b13b7a649de2f` |
| `wangbin-document-cli-1.2.0-connector-candidate.zip` | `be64b3b619382cbc74686fef6bd64a402f15f380487bde61e41620df66feb0e7` |

1.1.0 wheel/Skill/Connector 原有 SHA-256 仍分别为 `51071474a8668d5c4ba153896a5cde4d4233881f6042d7b16f305259fda702f9`、`c96a8644047146c595a2267769aadf8b7e6d6532615be4343d34014efb33678c`、`e04486c39f804307b98d33eabe5a477c6336910708c260ead8703b7fee305fbf`。`dist/` 被 `.gitignore` 忽略；本地文件存在不能等同已提交/远程发布。

验证：**最终 IPC 安全修正后的 wheel** 在 Windows 新隔离 venv 本地安装、`pip check`、`version/doctor/status` 及七格式处理、中文空格方括号路径和 Excel 重新打开，退出 0；Windows symlink 无创建权限，单项 `NOT_TESTED`。Linux Docker 重新安装同一最终 wheel 并真实执行 version/doctor/status、七格式、去重、损坏 PDF、symlink、越界、ZIP 高压缩比与解析超时/无活动子进程 **16 项**，退出 0；第一次 1 GiB 默认 Linux 全链退出 1，修正 2 GiB 后重构建复验。最终源码的现有仓库回归 `.venv/Scripts/python.exe -m pytest -q`：`23 passed, 1 skipped`（Windows symlink）；`validate_project(Path.cwd())` 早前：14 checks、无 findings。macOS CI 未运行。

最终候选日志：`C:/Users/wangbin/AppData/Local/hermes/cache/scratch/phase3-windows-audit-final.log`、`phase3-pytest-audit.log`、`wangbin-phase3-linux/audit-final-complete.log`；这些日志属于本机短期 scratch，不是平台安装日志。命令和详细失败/修复见 `phase3-clean-install.md`、`phase3-linux-tests.md`、`phase3-security.md`。

## 11 项门禁（仅 PASS / FAIL / BLOCKED / NOT_TESTED）

| 门禁 | 状态 | 原因 |
|---|---|---|
| DISTRIBUTION_SOURCE_PASS | **BLOCKED** | PyPI 包级与 1.2.0 版本 API 均 HTTP 404；未授权公开发布，无 WorkBuddy 可达来源。 |
| CLEAN_INSTALL_PASS | **PASS** | 本地最终 wheel 的全新 Windows Python 3.12 venv 安装 + `pip check`；限定本地，不代表平台。 |
| WINDOWS_RUNTIME_PASS | **PASS** | Windows 3.12 七格式、Excel 输出和复杂路径实测；symlink 单项未测试且安全门禁不通过。 |
| LINUX_RUNTIME_PASS | **PASS** | Python 3.12.15 Docker 最终 wheel 安装/CLI + 16 项真实运行断言。 |
| MACOS_RUNTIME_PASS | **NOT_TESTED** | 无真实 macOS；CI 工作流尚未在远端运行。 |
| SECURITY_PASS | **BLOCKED** | 虽移除 IPC pickle，但解析进程非安全沙箱；仍有 TOCTOU、进程树/Windows 硬 CPU/内存、XLSX 主进程资源、并发总量及 Windows symlink 缺口。 |
| CONNECTOR_SCHEMA_PASS | **PASS** | 本地校验器和打包器验证字段、资源结构及平台命令存在；平台实际 ZIP 解析仍需私有验收。 |
| SKILL_INTEGRATION_PASS | **BLOCKED** | CLI 名称/参数/JSON/三场景静态核对通过，但无 WorkBuddy 内真实 Skill→CLI/模型摘要证据。 |
| WORKBUDDY_INSTALL_PASS | **BLOCKED** | 无可访问 1.2.0 包和实际 Connector 安装记录。 |
| WORKBUDDY_E2E_PASS | **BLOCKED** | 无平台对话、真实文件处理或新 Excel 附件交付记录。 |
| PUBLISH_READY | **BLOCKED** | 公开来源、macOS、安全门禁、平台安装与真实 E2E 未关闭；不在本轮授权正式上架。 |

## 我本人下一步要做什么

1. 根据 `phase3-distribution-analysis.md` 人工确定受本人控制的包名/可信源；检查许可证全文及捆绑二进制再分发义务。**不要在聊天发送发布凭据。** 安全剩余风险需先决定是修复还是明确收窄产品适用范围；不能把 `SECURITY_PASS=BLOCKED` 偷改 PASS。
2. 如果同意发布，**由本人**按审核过的 wheel/hash 发布到可信包索引（推荐 PyPI；本轮代理没有执行）；随后在全新 WorkBuddy 托管 Python / 客户端网络中验证固定版本、依赖和 `init` 时限。
3. 将工作流提交到自己的仓库并在**真正的 macOS** runner 运行；保存日志/OS/Python/产物哈希。Linux Docker 不替代 macOS。
4. 在 https://open.workbuddy.cn/ 本人登录核实开发者权限与私有草稿/试传入口，严格按 `phase3-workbuddy-acceptance.md` 做 ZIP 解析、Connector 安装与 A/B/C 场景验收。若只能公开提审，则停止，不执行提交审核或收费配置。

距离 WorkBuddy 正式上架至少仍差：可信包分发与实际新客户端安装、macOS 真机证据、安全限制收尾、平台私有安装和真实对话/附件验收，以及随后单独授权的公开提审。没有真实模型调用不报告 AI 摘要。

## 后续 Git 安全收尾最新候选（覆盖旧哈希，不改写历史输出）

此次收尾从无 `dist/`、无虚拟环境的 131 个可加入源码/文档（构建时尚未写两份 Git 报告，故实际复制 129 项）重新构建 1.2.0 wheel 与两 ZIP；本地拥有的三个 1.1.0 历史二进制仍通过原 SHA-256 校验。**唯一可用于本次本地候选核对的最新哈希**：wheel `999251868e5d9679860eb8f0c753fc3358dccf0b96dce05edea01a2501cae4aa`，Skill ZIP `38133ee51a91db38091032c60ecb4b84db9e3c63e9953307575b13b7a649de2f`，Connector ZIP `be64b3b619382cbc74686fef6bd64a402f15f380487bde61e41620df66feb0e7`。三个 sidecar 均 `sha256sum -c` 通过；旧表格中 `c47d4536...` **不可再用于发布**。

Windows 10 / Python 3.12.0 最终 wheel 隔离安装并复跑：CLI version/doctor/status、七格式/复杂路径/Excel/越界通过；源码 31 passed, 1 skipped（Windows symlink 权限不足）。Linux Docker / Python 3.12.15 从同一 wheel 安装并通过 16 项运行验收，源码 32 passed。详见 `phase3-clean-install.md`、`phase3-linux-tests.md`；后续全部九项门禁、八类安全风险和首次提交方案见 `git-review.md`、`git-commit-plan.md`。**SECURITY_PASS=BLOCKED、PUBLISH_READY=BLOCKED**；无公开分发、WorkBuddy 平台或 macOS 实测。
