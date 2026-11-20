# R9 光伏分进程 L3 正式准入：执行门禁（非验收回执）

本合同仅适用于独立分支 `solar/r9-l3-admission`。基线为 R8 报告 HEAD `e7b86f557931561e00105b067f7e370df1c43a28`，其中 B1 工具源码提交 `477241f5c58d942218c3baacb88a0a904d60fa87`；报告提交不等于被测源码提交。R6 单进程失败、R7/R8 原始回执、财务公式与 512 MiB 默认 `BundleBudget` 均不可被本模式改写。完整授权和优先级见本轮用户提供的《SOLAR-PV-R9｜分进程 L3 正式准入与资源闭包收口》。本文件不授予跳过门禁或推送 main 的权利。

## 逐级准入步骤

1. **保全与只读预检**：读取 `agent.md`、R8 合同/报告，确认隔离分支/工作树/受保护 `uv.lock`、官方私有 Pandoc 3.14 EXE 哈希与原 89/89 回执。R8 历史忽略 fixture 须原字节复制、单独校验，不把这两份副本当作完整输入清单。
2. **Windows 资源语义**：原 `Meter` 的 `GetProcessMemoryInfo` 返回每个当前进程的 `WorkingSetSize` 与内核累积 `PeakWorkingSetSize`；默认检查两者最大值不超过 `512 * 1024**2`。Job Object 的 process/job private-commit 上限与它不是同一指标。实现可查询的 PID＋进程创建时间、实际 Python 解释器及完整子孙进程生命周期原始内核读数；短寿命进程不得仅靠固定间隔采样。事件、权限、句柄、进程数量或读取丢失一律拒绝，并由独立解析器复算。先对父子/孙/瞬态/分配释放/越限/监控失效等真实 Windows 探针负例验收。
3. **环境字节闭包**：冻结实际解释器路径及 SHA、版本/架构、`sys.path`、加载模块与本机 native 扩展/DLL；枚举第三方安装文件逐项 SHA，核对 `.dist-info/RECORD`，再绑定原 wheel 哈希及安装后文件映射。优先查离线缓存；只允许取得锁定的官方精确摘要构件。缺 wheel、文件或映射的项目必须列为未闭合，不得用包名、版本、锁文件摘要替代。
4. **动态读输入闭包**：可靠地按 PID＋创建时间跟踪实际文件读取，将已跟踪源码/报告、已忽略 fixture、外部 Pandoc、依赖及临时输入分别纳入版本化 manifest；对每份实际读入的文件保留路径、类型、大小、SHA、文件身份/时间、读取进程及时间和前后字节。区分运行产物。环境变量只记脱敏/摘要；丢失事件、无法分类、不可读或变更即闭包失败。独立验证器须重读原件，不能信任调度器的 `PASS` 字段。
5. **工具与独立 QA**：保留 R8 原 40 个攻击性验证，增加进程树/资源和输入闭包负例；在最终工具源码冻结提交后由另一执行角色独立复验原字节、小样、资源探针、身份漂移及重型单文件。开发者绿灯不等于独立准入。
6. **十项同时为真才可正式 collect-only**：`PANDOC_OMML`、`WINDOWS_WORKING_SET_OBSERVER`、`PROCESS_TREE_COMPLETENESS`、`MEMORY_LIMIT_512_MIB`、`PYTHON_DEPENDENCY_BYTES`、`DYNAMIC_INPUT_CLOSURE`、`SHARD_TOOL_SECURITY`、`INDEPENDENT_QA`、`HEAVY_SINGLE_FILE_RESOURCE_TEST`、`FINAL_SOURCE_IDENTITY`。所有判定绑定同一最终冻结源码、依赖、外部工具和输入字节。任何未知仍为 `BLOCKED`，不能用历史节点数替代实际收集。
7. **有条件全集**：仅第 6 步全通过后，以相同冻结身份真实收集全部参数化 nodeid；记录有序清单及 SHA、无遗漏/重复的文件分片。每文件独立进程串行执行一次，独立保留原始 JUnit/日志/退出码/资源证据并逐片重验。FAIL、ERROR、非预期 SKIP、超时、丢进程或证据不一致即保留失败原件并停止，不重试拼接。新源码修复必须重新冻结及验收。仅独立复核完全集唯一覆盖、全部通过，才能写 `L3_SHARDED_R9=PASS`；不更改 R6 单进程失败原判。
8. **本地提交/远端核对**：每轮完成独立 QA 后按明确路径选择性暂存，执行卫生、受影响验证、`dist` 保全与本地提交。授权范围仅为独立 R9 普通分支 push，随后精确读回远端 SHA；禁止 force push、merge、rebase、修改 main、覆盖 `uv.lock`，也不能把 push 当发布。

正式报告 `SOLAR-PV-R9-L3-ADMISSION-CLOSURE-execution.md` 须以实际原始证据填写所有通过、失败、未测和阻断；若上游门禁不成立，全集节点数/分片执行矩阵如实记为 **未收集/未执行**，不得预填旧数或模拟结果。WorkBuddy L3、真实工程日期、IRR 完整根证明、F04、F02/PDF、40 项人工审阅、专业签审、Phase E/F/G 及发布均属其他独立门禁。
