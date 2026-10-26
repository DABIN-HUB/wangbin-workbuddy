# Phase 3 Git 工作区与安全收尾审查（1.2.0）

> 审查对象：`F:/ideaWorkSpace/wangbin-workbuddy`，`main`、零次提交。**没有执行 git add、commit、push、reset、checkout、switch、WorkBuddy 上传或公开发布。** 本报告只对本轮重新构建的候选负责；`reports/phase3-*.md` 的旧结果作为历史快照保留，旧 wheel 哈希不得用于发布。

## 1. Git 与可重建性

- 实际执行 `git status`、`git diff`、`git diff --cached`、`git ls-files --others --exclude-standard`，另执行 `git status --ignored --short`、`git check-ignore`、`git diff --check`、`git rev-list --all --count`。首次审查时工作树无已跟踪文件、无暂存差异、无未暂存差异，**129 个可加入的未跟踪文件**（新增本报告及提交方案后为 131，最终状态以临提交前复核为准）。`main` 无提交历史；禁止的 Git 命令均未运行。
- 首次审查 129 项分布：`.github` 2，`.gitignore` 1，`README.md` 1，`docs` 15，`packages` 26，`pyproject.toml` 1，`reports` 25，`requirements-dev.txt` 1，`requirements.txt` 1，`services` 16，`tests` 22，`tooling` 18。测试源码、14 个真实格式/异常夹具、服务源码、CLI、模板、构建器与历史报告都在 Git 可加入范围，**没有发现被误忽略的重要源码**。目录命名和中文/方括号/空格夹具均为合法路径；可加入文件中没有符号链接或末尾空格/点的名称。
- `.gitignore` 显式忽略 `.venv/`、`.phase3-ci-venv/`、`dist/`、`output/`、缓存、egg-info、构建目录、`.runtime/`、日志、`reports/raw/`、生成夹具与 IDE 文件。忽略列表中有 `.venv/`（约 6976 个条目）、`dist/`（18 个条目、含 Phase 1/2 旧包及先前 1.2.0 构建）、缓存/构建文件与 `output/`；这些**不适合首次提交**。`output/` 可能包含用户生成数据，未读取或加入。没有在可加入文件中发现大于或等于 1 MiB 的文件；首次审查可加入内容总计 417560 字节。未发现应公开的二进制大产物。
- 静态凭据/URL-userinfo/私钥/非示例邮箱扫描覆盖所有 129 个可加入文本文件，返回零命中。初审在可选 Expert 模板的 `author.email` 发现非示例邮箱，已替换成 `contact@example.com` 并再次扫描为零。**扫描并不证明不存在任何秘密**；用户在提交前仍须人工检查暂存差异与 `reports/` 中的机器路径/业务数据。报告/摘要中的真实凭据只允许写 `[REDACTED]`；本次没有收集账号密码或读取忽略的用户输出。
- `dist/` 里 1.0.0/1.1.0/过期 1.2.0 产物是**本机历史文件**，不能加入首次提交或与新候选混用；Phase 2 1.1.0 三个历史二进制在本机均经预设 SHA-256 比对保持不变，历史报告 `reports/phase2-*` 保留并建议加入 Git。历史二进制不在 Git 内，离开本机无法逐字节恢复**原** 1.1.0 发布包：这是历史归档局限，不是当前 1.2.0 的源码重建前提；若要求远端保留原包，应由本人另外选择受控私有归档，不要把它当作 1.2.0 候选。
- 从所有可加入源码复制到 Hermes scratch 下的**无 `dist/`、无 `.venv/` 的干净目录**，用 `uv build --wheel services/document-engine --out-dir dist --python <Python-3.12> -q` 构建 wheel，再运行 `<Python-3.12> -m tooling.phase3_packager`；真实结果 `status=PASS / status_scope=package_structure_only`、`phase2_artifacts_available=false`，且 Wheel/Skill ZIP/Connector ZIP 均从源码生成。回到本机有旧包的 `dist/`，打包器核验旧包三项 SHA-256 并生成新清单，`phase2_artifacts_preserved=true`；三个新候选的 `.sha256` 经 `sha256sum -c` 全部 OK。**首次提交不依赖被忽略的历史/新 `dist/`**。构建源码包括 `services/document-engine/`、`packages/`、`tooling/`、根元数据/依赖；不要将根工程工具包 `version=1.0.0` 与独立 CLI 分发包 `version=1.2.0` 混为一个包。

## 2. 最新候选、版本与真实回归

| 产物（`dist/`，本地且不入 Git） | SHA-256 |
|---|---|
| `wangbin_document_cli-1.2.0-py3-none-any.whl` | `999251868e5d9679860eb8f0c753fc3358dccf0b96dce05edea01a2501cae4aa` |
| `wangbin-document-assistant-1.2.0-skill-candidate.zip` | `38133ee51a91db38091032c60ecb4b84db9e3c63e9953307575b13b7a649de2f` |
| `wangbin-document-cli-1.2.0-connector-candidate.zip` | `be64b3b619382cbc74686fef6bd64a402f15f380487bde61e41620df66feb0e7` |

Wheel 的 `services/document-engine/pyproject.toml`、CLI `version`、Connector 元信息及 `init`、两个 Skill 的候选描述均为 `1.2.0`；直接依赖 `markitdown[pdf,docx,xlsx,pptx]==0.1.9`、`openpyxl==3.1.5` 与 wheel 元数据对应，根 `requirements.txt` 另含工具链 `PyYAML==6.0.3`。根工程包 `1.0.0` 是单独的 toolkit，不是用户安装的 CLI wheel。`dist/wangbin-document-cli-1.2.0-candidate-manifest.json` 的 `PASS` **仅指包结构与源码成员**，不代表安全/分发/平台验收。

- Windows 10 / CPython 3.12.0：隔离 venv 对最新 wheel `--force-reinstall --no-deps`（隔离环境的依赖此前已安装）、`pip check` 为 `No broken requirements found.`，实际安装 CLI `version=1.2.0`、`doctor=ready`、`status=LOCAL_READY`。旧的隔离验收脚本对本 wheel 实跑七格式、中文/空格/方括号路径、XLSX 去重重新打开和越界，共 10 项通过；symlink 单项因 Windows 建立权限不足为 `NOT_TESTED`，不能算通过。完整仓库 `pytest -q`：**31 passed, 1 skipped**，退出码 0。日志（scratch 临时文件）：`C:/Users/wangbin/AppData/Local/hermes/cache/scratch/wb-phase3-windows-release.json`。
- Linux Docker `python:3.12-slim` / Python 3.12.15：从同一 wheel 安装、`pip check` 无损坏依赖；`PYTHONPATH` 清空后的真实 CLI 16 项（version/doctor/status、七格式、去重、异常输入、symlink、越界、ZIP 比率、超时/子进程观察）**全部通过**、退出码 0。将源码只读挂载后复制到容器内可写目录，`python -m pytest -q -p no:cacheprovider`：**32 passed**、退出码 0。先前因少装 PyYAML 的收集错误、只读挂载上 `test_tooling` 写报告失败均如实记录在 `phase3-linux-tests.md`，没有删测；最终容器 `--rm`。日志：`C:/Users/wangbin/AppData/Local/hermes/cache/scratch/wb-phase3-linux-release.json`。
- macOS 没有真机或 CI 实测，Linux Docker 不能替代。WorkBuddy 托管 Python/Connector/Skill/模型调用没有执行，平台门禁仍阻断。

## 3. 八类安全风险分级（最新源码；**普通子进程不是安全沙箱**）

| 风险 | 触发条件及影响 | 级别 | 当前实现、建议及对应真实回归 | 阻断发布 |
|---|---|---|---|---|
| 1. TOCTOU 输入/输出路径 | 攻击者可同时替换用户文件、路径组件或输出目录；可能越界读取或覆盖文件。 | 高 | 输入先校验，再从打开的 FD 比较文件标识、复制到私有临时文件、重验快照/Office ZIP；导出通过同目录硬链接原子无覆盖发布，冲突返回 `OUTPUT_CONFLICT`。`test_parser_uses_private_input_snapshot_and_cleans_it`、`test_publish_new_file_never_overwrites_existing_user_output`、旧 symlink/越界测试；Windows symlink 无权限未测。建议在允许敌对并发文件系统的部署中使用基于目录句柄/平台重解析点的完整路径约束并复验，避免 Windows 父目录 junction 换入、原地同尺寸内容修改和输出父目录竞争。 | **是**，敌对可写目录仍不闭环。 |
| 2. Windows 解析子进程资源 | 恶意文档让解析库无限 CPU/内存、衍生其他进程，影响同账户/机器。 | 高 | Windows 有父进程超时并终止**直接子进程**，没有 Job Object CPU/内存/进程树硬限。`test_timeout_reaps_parser_process_and_releases_capacity` 在 Windows/Linux 实跑；建议 Job Object 或 OS/容器级专用低权限隔离并分别验证硬限及树回收。 | **是**。 |
| 3. Excel 主进程负载 | 高密 XLSX/sharedStrings、压缩放大或高成本单元格在 `load_workbook` 内扩张，导致主 CLI 耗尽 CPU/内存；写出也可能阻塞。 | 高 | 只读迭代/只写输出、最多 100000 行/500000 单元格、文本和导出最多 50 MiB、迭代时间检查；超过明确报 `SPREADSHEET_ROW_LIMIT` / `SPREADSHEET_CELL_LIMIT` / `EXPORT_TOO_LARGE`。`test_spreadsheet_limits_fail_without_output`、`test_spreadsheet_cell_limit_applies_to_inspection_and_export`、`test_export_size_limit_cleans_temporary_file`、旧 XLSX/CSV 回归及实际 wheel 去重。**这些是协作式限制，不约束初始加载、共享字符串内存、保存时 CPU/内存，也不保证强制超时。** 建议将 Excel 全操作迁移到有 OS 硬限的独立进程或只接受可信 XLSX。 | **是**，对不可信 XLSX。 |
| 4. 多进程并发 | 多 CLI 并行解析/导出，累积资源耗尽。 | 中高 | 每用户/同一系统临时目录的 2 个 OS 文件锁槽共享解析与 Excel，第三个任务立即报 `RESOURCE_BUSY`；进程退出由 OS 释放锁。`test_capacity_is_enforced_across_cli_processes` 实际跨进程 Windows/Linux 验证。不同系统账号/容器不共享容量，锁目录遭同账户破坏、单槽资源预算与部署全局上限未解决；建议部署层再限额。 | 对单机同账户容量局部缓解；多租户/全局**是**。 |
| 5. 异常终止与后代 | 工作进程超时/崩溃、启动/IPC 中断或衍生子孙；可能孤儿进程、资源残留。 | 高 | `multiprocessing.spawn`、父进程超时 `terminate`/必要时 `kill`/`join`；JSON IPC `recv_bytes(maxlength=32 MiB)`，原 pickle 反序列化通路关闭。`test_timeout_reaps_parser_process_and_releases_capacity`、Linux 16 项的超时/无活动直接子进程；启动阶段、子孙进程、恶意 IPC/大结果未完成专用压力验收，异常强杀后代未可靠保证。建议进程树/Job Object 回收与错误路径动态实测。 | **是**。 |
| 6. 用户文件权限边界 | 用户选宽泛 `input_root` 或解析库被利用，继承当前用户权限读取其他文件；输出目录若同用户可被恶意替换。 | 高 | 校验根/符号链接/扩展名/ZIP 并从源 FD 建立私有快照，但解析器仍与用户同权限；快照不构成权限沙箱。旧 `test_path_traversal_is_rejected`、Linux symlink/越界探针、Windows 越界探针。建议专用最小权限身份，仅显式输入/输出目录授权，禁止同账户访问敏感资料。 | **是**，不可信多用户部署。 |
| 7. 临时文件与缓存清理 | 解析/Excel 抛异常、超限、进程崩溃，私有文档残留临时目录；用户资料可外泄或填满磁盘。 | 中高 | 快照采用上下文自动清理；Excel 同目录临时文件在失败时删除，部分写出的 openpyxl scratch 也清理；OS 锁文件只含一个零字节、无文档。`test_export_size_limit_cleans_temporary_file`、`test_rejection_cleans_openpyxl_scratch`、旧异常导出实测。SIGKILL/系统崩溃、openpyxl 内部其他临时路径、系统临时目录 ACL/保留期限尚未证实；建议专用加密/受限 scratch、启动回收策略与真实崩溃恢复测试。 | 对敏感用户文件部署**是**。 |
| 8. 不可信解析库安全边界 | 攻击者构造 PDF/Office 输入利用 MarkItDown/第三方库漏洞，可能在用户权限下执行任意操作。 | 严重 | Office ZIP 预检、独立解析子进程、POSIX 尝试 `RLIMIT_CPU`/`RLIMIT_AS`、32 MiB JSON IPC；真实七格式、损坏输入、ZIP bomb、超时在双平台通过。**JSON IPC 只关闭原 pickle 攻击通路，普通子进程不是安全沙箱**；仍可访问用户其他文件，Windows 无硬限、Linux 也无系统调用/文件权限隔离。建议更新/审计依赖，采用低权限 OS 容器/沙箱与进程树回收，做敌对输入专项验证。 | **是**。 |

## 4. 最终九项门禁

| 门禁 | 状态 | 说明 |
|---|---|---|
| GIT_REVIEW_PASS | **PASS** | 首次提交范围、误忽略、历史证据、静态敏感信息与大文件已审查；**尚未实际提交**，提交前再次人工检查暂存区。 |
| SOURCE_REBUILD_PASS | **PASS** | 无 `dist/`、无虚拟环境，从可加入源码实建 wheel + 两 ZIP；Phase 2 本地旧包可选且仍被哈希保护。 |
| SECURITY_PASS | **BLOCKED** | Excel/Windows 硬资源、进程树、OS 低权限、敌对路径竞态和敏感临时目录仍未闭环。 |
| WINDOWS_RUNTIME_PASS | **PASS** | 当前 wheel 实际 Windows 3.12 运行及 31 passed；symlink 专项 NOT_TESTED，不意味着安全通过。 |
| LINUX_RUNTIME_PASS | **PASS** | 当前 wheel Linux 3.12.15 运行 16 项和 32 passed。 |
| PACKAGE_VALIDATION_PASS | **PASS** | 包内容/元数据/成员校验及三份 sidecar 通过；范围仅 `package_structure_only`。 |
| WORKBUDDY_INSTALL_PASS | **BLOCKED** | 没有可达、可信、经本人授权的 1.2.0 安装来源，也无平台托管环境安装证据。 |
| WORKBUDDY_E2E_PASS | **BLOCKED** | 无真实平台 ZIP 解析、Skill→CLI/模型摘要/Excel 附件证据。 |
| PUBLISH_READY | **BLOCKED** | 安全、分发、平台验收未达门槛；macOS 也尚未实测。 |

## 5. WorkBuddy 仍需本人完成

先关闭/明确限制上述安全阻断项并审核第三方许可证/NOTICE，确认可控制包名及公开可信分发；**不得在聊天提供凭据**。有受保护草稿/私有试传入口且本人授权后按 `phase3-workbuddy-acceptance.md` 核对 ZIP 根目录解析、托管 Python `init`/依赖/退出码、三种文件对话、真实模型摘要调用以及 Excel 附件；如平台只允许公开提交审核，停止。本轮没有发布或登录；Linux 不能替代 macOS 实测。
