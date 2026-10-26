# Phase 3 安全门禁（1.2.0）

> 此表是 Git 安全收尾前的**历史快照**；其中“并发无限”、“os.replace”等实现状态已由后续局部修复更新。最新八类风险的触发条件、测试、剩余风险和发布阻断判定请以 `git-review.md` 为准；旧结果不改写为新结果，`SECURITY_PASS` 仍为 `BLOCKED`。

结论：**SECURITY_PASS=BLOCKED**。已修复/实测部分风险，但不将局部探针扩大为通用隔离承诺。本产品处理来自用户的非可信文档，当前不能宣称达到恶意输入的强沙箱安全级别。

| 风险 | 当前实现和实际证据 | 状态/余留 |
|---|---|---|
| 父进程 IPC 反序列化 | 独立静态安全审计发现旧 `Connection.send/recv` 对来自解析子进程的数据使用 pickle/unpickle，恶意文档若利用解析器即可借此攻击父进程。随即改为 `send_bytes`、`recv_bytes(maxlength=32 MiB)` 与受限 JSON、字段类型/错误码校验；最终 wheel 在 Windows/Linux 真实格式命令上复跑通过。 | 已删除此 IPC pickle 通路；恶意子进程/大输出专用动态攻击验证未完成，不能宣称整体隔离 PASS。 |
| 文件符号链接/路径越界 | `SecurityPolicy.validate_input` 检查组件、根目录和扩展名；Linux Docker 真实 symlink 返回 `SYMLINK_INPUT`/exit 1；Linux/Windows 路径越界返回 `PATH_OUTSIDE_ROOT`/exit 1。 | Linux PASS；Windows symlink 因无创建权限为 NOT_TESTED；路径检查与真正打开之间仍存在 TOCTOU（可被其他进程换入链接）。 |
| 真正解析超时 | 生产 `DocumentEngine` 默认通过 `multiprocessing spawn` 隔离 parser；父进程 `terminate`，必要时 `kill` 并 `join`。Windows 3.12 和 Linux 3.12 的真实 PDF 均在 0.05 秒阈值返回 `PARSER_TIMEOUT`，调用返回后 `active_children()` 与调用前相同。 | 当前单子进程超时 PASS；极端启动阶段、子孙进程、跨进程句柄和大结果传输尚未全部证明。 |
| CPU/内存限制 | Linux/POSIX 子进程尝试 `RLIMIT_CPU` 和 `RLIMIT_AS`；1 GiB 默认导致 Linux 全量链失败，改为 2 GiB 后重构建并运行真实 PDF/DOCX/XLSX/PPTX 等。 | 2 GiB 正常样例 PASS；恶意输入限制回收、macOS 行为未实测；Windows 无 Job Object CPU/内存硬限，BLOCKED。 |
| Office ZIP 展开攻击 | 逐条/累计展开体积、压缩比、条数、路径穿越、加密条目预检。Linux 高压缩比 XLSX 真正返回 `ZIP_COMPRESSION_RATIO`/exit 1。 | 典型样本 PASS；预检与第三方解析库之间 TOCTOU、第三方库内部展开/耗时仍需更强隔离。 |
| Excel 临时文件/输出 | 同目录临时 `.tmp.xlsx`/`.tmp.csv` 写入、可重新打开再 `os.replace`，异常清理。Windows 安装 wheel 后运行公式 Excel：源 SHA-256 不变、新文件重新打开 3 行且危险值不为公式；无效去重 key 返回 `INVALID_KEYS`、无临时文件残留。 | 探针 PASS；导出路径 `SpreadsheetService` 仍在主进程，尚无 CPU/内存/壁钟硬限。 |
| 子进程异常清理 | 正常超时后未见 `multiprocessing.active_children` 孤儿；`process.start()` 失败时现在显式关闭父端/子端管道。 | 大数据传输、不可捕获的中断、工作进程自己衍生后代未覆盖；BLOCKED。 |
| Excel 公式注入 | XLSX/CSV 输出时以文本前缀保护以 `= + - @` 开头的单元格；Windows 真实导出并重新打开验证 `=...`/`@...` 为字符串。 | 探针 PASS，仍需针对具体电子表格软件人工验收。 |
| 并发聚合限制 | `parse_many` 顺序处理并限制单批数量及累计输入大小。 | 多 CLI 进程并发无限；导出不在子进程；没有用户/全局限额、总内存池或队列，BLOCKED。 |

## 实际命令与日志

- Windows 最终 wheel timeout/无活动子进程、公式与输出完整性：`PYTHONNOUSERSITE=1 PYTHONPATH= WANGBIN_ENGINE_SRC= <隔离Python> C:/Users/wangbin/AppData/Local/hermes/cache/scratch/phase3-timeout-probe.py` 及 `phase3-export-security.py`，退出码 0，`children_before=[]`、`children_after=[]`。日志 `C:/Users/wangbin/AppData/Local/hermes/cache/scratch/phase3-windows-audit-final.log`。
- Linux 最终 wheel 容器：`reports/phase3-linux-tests.md` 中的 Docker 安装及验收命令，退出码 0，16 项断言；日志 `C:/Users/wangbin/AppData/Local/hermes/cache/scratch/wangbin-phase3-linux/audit-final-complete.log`。

修复：本轮增加独立解析进程和 POSIX rlimit、从 1 GiB 调整为能处理真实样例的 2 GiB、Excel 原子导出和清理；复核后移除不安全的跨进程 pickle 反序列化，限制响应大小；wheel 最低版本提升到 Python 3.12，避免在未复核 junction API 的 3.11 上运行。Phase 2 的 1.1.0 历史安全结论不被此报告改写。

继续关闭门禁需要：确认**独立子进程并非安全沙箱**；Windows 内存/CPU 的 OS 级进程约束与进程树收割；导出使用同等资源边界及行/列/单元格限额；跨进程并发容量；文件描述符级防 TOCTOU（输出 `os.replace` 仍可能和外部进程竞争）；解析器进程崩溃/恶意 IPC/大结果/强杀子进程树的验证。在这些能力未可靠实现之前保持 BLOCKED。

## 后续 Git 收尾安全变化（不改写上方历史表）

最新 1.2.0 wheel SHA-256 `999251868e5d9679860eb8f0c753fc3358dccf0b96dce05edea01a2501cae4aa`：文件私有快照/重验、跨 CLI 进程两槽容量锁与明确 `RESOURCE_BUSY`、Excel 流式行/单元格/字节限额和原子无覆盖发布已实现；八个新增安全回归分别在 Windows/Linux 真实执行。最终 Windows 源码 31 passed, 1 skipped、Linux 32 passed；安装 wheel 的 Windows 实际验收与 Linux 16 项验收均通过。Windows symlink 未获权限无法实测。剩余高危：Windows Job Object/低权限隔离缺失、Excel 主进程没有 `load_workbook`/保存阶段 OS 级 CPU/内存硬限、工作进程后代不保证清理、目录/输出竞态以及第三方解析器与当前用户同权限。**这些改进不使 `SECURITY_PASS` 由 BLOCKED 变 PASS**；完整触发条件/影响/等级/建议/对应测试见 `git-review.md`。
