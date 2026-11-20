# SOLAR-PV-R9-L3-ADMISSION-CLOSURE｜执行与阻断回执

**日期：2026-11-20（中国标准时间）｜状态：`BLOCKED_NOT_TESTED`（正式全集）｜非发布 WIP。** 本回执只记录实际完成的资源/依赖诊断和限定独立 QA；不把候选工具、限定通过或 Git 推送写成正式 L3 准入。完整授权与逐级门禁见 `docs/solar-pv/33-r9-l3-admission-closure.md`。

## 1. 源码关系与保全

R7 工具 `92f5dc50aceeed975ba5a55716651aafe2f466bd` → R8 **B1 工具源码** `477241f5c58d942218c3baacb88a0a904d60fa87` → R8 **报告/隔离 HEAD** `e7b86f557931561e00105b067f7e370df1c43a28` → R9 **被测工具源码和合同的非发布提交** `f935c16a2e18f415fbe829a121b97690a320b140`（父提交为 R8 报告 HEAD）。R8 报告 SHA 不能充当 B1 被测源码 SHA。R9 独立工作树 `F:/ideaWorkSpace/wangbin-workbuddy-r9-l3-admission`、分支 `solar/r9-l3-admission`；仅该分支普通推送后的远端 SHA 已读回为 `f935c16a2e18f415fbe829a121b97690a320b140`。报告提交将另生 HEAD；最终本地/远端分支 SHA 须以本报告提交后的独立读回为准，不用报告自身递归声称其 SHA。主工作树及远端 `main` 均读回 `0ad56e30face3193ea8e9d043be87811be6b1b17`；主树受保护的未跟踪 `uv.lock` 未改，R9 工作树无此文件。未 force push、merge、rebase、覆盖历史或碰 Phase E/F/G。

R8 Pandoc 私有 `C:/Users/wangbin/Documents/solar-pv-tools/pandoc-3.14/pandoc.exe` 再读回 SHA-256 `81b551129ae36faa420e07223390252547af92e00e2cc570bc57fee61ccbc623`，版本 3.14、历史真实 89/89 OMML 专项与 28/28 私有 manifest 字节复核保留；没有重新下载/安装/改 PATH，也未用它们替代正式 F02/PDF 或 R9 全集。本轮没有正式 shard，因此没有新的 Pandoc 子进程绑定回执。

## 2. Windows 工作集门禁与原生进程证据

原应用 `Meter` 的 Windows `GetProcessMemoryInfo` 读取当前 `WorkingSetSize` 和生命周期内核 `PeakWorkingSetSize`，检查原上限 **536870912 字节（512 MiB）**；不能把当前值、历史峰值、private commit、Job 限额或并发物理占用等同。R9 的 `tooling/solar_pv_windows_observer.py` 在隔离探针中暂停创建目标、入 Job 后恢复，尝试按 PID＋创建时间保留句柄、读取原生计数和父子关系；原 512 MiB Job process/job **private-commit** 限额单列保留。`tooling/solar_pv_windows_observer_verify.py` 可复算结构/身份/事件与峰值、拒绝篡改与伪称 PASS；它**明确不作 OS 原生无损证明**，正式始终 `BLOCKED` / `native_attestation=false`。这两份诊断代码未接入正式 `full`，不能赋予正式准入。

独立 QA 的真实共享 section 反例：在 512 MiB process/job private-commit 限额下，Job 内 Python 子进程映射 **545259520 字节（520 MiB）**，原生实时 `PeakWorkingSetSize=559345664` 字节、`WorkingSetSize=559316992` 字节，而 `PeakJobMemoryUsed=9334784` 字节。原件 `C:/Users/wangbin/Documents/solar-pv-tools/r9-b2-independent-qa-ce3827d77c814b858171006cef134c19/shared-section-result.json`，SHA-256 `7a1f263227284185f27c0f2f90de2fe69fcf2e1751c9e1c83d32dfe52f848d19`；这是资源隔离反例，不是修改业务 Meter，也不能据此推断具体业务测试调用 Meter 时的结果。正式 Job 完成端口普通通知不保证无遗漏，退出后内存查询不足以证明每个短命子孙的全生命周期峰值；未获得无损事件/退出前屏障，也没有可靠的同时物理占用证据。**`WINDOWS_WORKING_SET_OBSERVER=BLOCKED`、`PROCESS_TREE_COMPLETENESS=BLOCKED`、`MEMORY_LIMIT_512_MIB=BLOCKED`；所有实际测试解释器/子孙被监控：未证明。** 不提升限额、不以 private commit 替代 working set。

## 3. 解释器、依赖及动态输入（不完整清单）

只读 `tooling/solar_pv_dependency_closure.py` 记录解释器路径/文件 SHA、实现/架构、加载模块、`sys.path`、安装文件/RECORD、native 文件，并在有准确原 wheel 时核对 wheel 内安装映射；对缺失或不明确者失败关闭。已核对的原始 `C:/Users/wangbin/Documents/solar-pv-tools/r9-native-reviewed-20261120/dependency-closure-blocked-original.json`（SHA-256 `07760fe881ed2f40b8cb31aacab86f2314af6191320dd1206aa29a5af2365be7`）枚举 **157** 项 installed distributions，**157** 项未闭合：`LOCK_PACKAGE_UNAVAILABLE` **127**、`WHEEL_UNAVAILABLE` **30**。这不是 157 项已获官方 wheel 的证明；没有升级依赖、改共享解释器或改锁文件。当前 R9 树刻意没有受保护的 `uv.lock`，新执行 `dependency-missing-lock-v8.json`（SHA-256 `47f8deed2d30c839418db009efbea7d5e58f0798a44dbf6c2f76d94867ebbd2e`）只得到 `BLOCKED / LOCK_UNAVAILABLE`、157 项安装清单；主树 `uv.lock` 未复制。对主树锁定文件的后续一次只读离线缓存审计尝试在 **240 秒超时**、未写出指定回执，不计作新闭包结论或成功。探针现拒绝多重 stdout 标记、非零退出、启动噪声和空依赖清单，隔离继承 `PYTHONPATH`；这仍不是受污染解释器或将来测试进程的密码学远程证明。**`PYTHON_DEPENDENCY_BYTES=BLOCKED`。**

仅两份历史忽略请求 fixture 原字节复制到 R9 忽略目录：工业屋顶 SHA-256 `d48b0bfad84b303d7f7978d6c9e53f78aba424541992f509240df8a09928bae1`、地面 SHA-256 `976ce58137f5aee380de765584df59d78d4777e993cc9f1ddd7dc912d616df6a`，不是动态输入全集。`C:/Users/wangbin/Documents/solar-pv-tools/r9-l3-admission-input-feasibility.json` 记录 Windows Kernel-File Analytic 未启用、当前身份非管理员、`auditpol` 权限错误 `0x00000522`、Security 日志访问被拒；没有改审计策略，也没有无损 PID＋创建时间关联的运行时读轨迹。静态检查另见报告、公式、测试中的读路径；未辨识全部实际输入/输出、前后 SHA 和变更事件。敏感环境值一律不记录明文，发现凭据须 `[REDACTED]`。**完整动态输入 manifest：未生成；`DYNAMIC_INPUT_CLOSURE=BLOCKED`。**

## 4. 独立 QA 与限定证据

修复首轮 QA 的 wheel 安装目标误映射、资源伪造/父子结构误报，及次轮 QA 的探针 stdout/非零退出误收、根进程自指父 PID 后，最终独立 QA 对已提交六个 R9 文件和原 R8 工具/测试的同一工作区字节复跑：Windows observer **9/9**、依赖审计 **10/10**、原 R8 分片攻击测试 **40/40**；合计 **59 个互异 testcase、0 FAIL、0 ERROR、0 SKIP**。独立 JUnit `C:/Users/wangbin/Documents/solar-pv-tools/r9-final-qa-20261120-132833-9402/scoped.xml` SHA-256 `43500ea7aaf636e30865afb3c0ae1c1f79f6ddf2af4014c7975a265f71efd49f`；日志 SHA-256 `48fd573ec474f32e5dc490bc6dbcfaea69137af7a833b4dcb59a4bb8ee84a3a7`，源码前后哈希见同目录 `source-pre.sha256` / `source-final.sha256`，复读一致。`adversarial-results.json` SHA-256 `a3c9103bc08dbe68ce45bf5e637d5c1af056fe2c91916101b196f2ec8590e550`：私人 `sitecustomize` 注入伪标记直接子进程退出 17，但审计取得真实身份/157 distributions 并仍为依赖 `BLOCKED`；root 自指父 PID、退出后超限及伪称 PASS 重哈希回执均拒绝；协调伪低峰结构可自洽却仍只得 `BLOCKED`、CLI 退出 2、`native_attestation=false`。原真实资源回执 `tree-512miB-v2.json` SHA-256 `374e8d44eee336fd51f861db446115eefa580a5e7d7f4b86eabb8e3ab7efa5b1`。这些有限探针和合成攻击不构成 OS 无损证明或重型业务文件验证。**`SHARD_TOOL_SECURITY=PASS（仅限定攻击套件）`；`INDEPENDENT_QA=PASS（仅限定专项）`，两者的正式准入尚为 BLOCKED。**

## 5. 十项准入、全集与发布

| 正式前置项 | 实际判定 |
| --- | --- |
| `PANDOC_OMML` | 历史 89/89 PASS（限原专项） |
| `WINDOWS_WORKING_SET_OBSERVER`、`PROCESS_TREE_COMPLETENESS`、`MEMORY_LIMIT_512_MIB` | BLOCKED，缺进程无遗漏和全生命周期工作集证据，真实物理反例保全 |
| `PYTHON_DEPENDENCY_BYTES`、`DYNAMIC_INPUT_CLOSURE` | BLOCKED，157 项依赖未闭合；动态读输入 manifest 不存在 |
| `SHARD_TOOL_SECURITY`、`INDEPENDENT_QA` | 限定范围 PASS；正式完整环境准入 BLOCKED |
| `HEAVY_SINGLE_FILE_RESOURCE_TEST` | BLOCKED_NOT_TESTED，前置资源闭包未满足，未运行 |
| `FINAL_SOURCE_IDENTITY` | R9 工具源码提交 `f935c16a2e18f415fbe829a121b97690a320b140` 已冻结、限定 QA 哈希已绑定；完整依赖/动态输入/正式 shard 身份未闭合，正式 BLOCKED |

`python -m tooling.solar_pv_l3_sharded full --out <全新私有目录> --pandoc <上述已核验私有绝对 EXE>` 在此源码提交上**收集前退出 2**：`formal full BLOCKED: B2 OS working-set/wheel-byte admission not established`；输出目录不存在。未绕过此挡板。因此正式全集 nodeid 数 **未知/未收集**，nodeid 清单 SHA **不存在**；参数化节点/唯一分片归属/每节点恰好一次 **未检验**；分片分配与实际执行矩阵 **不存在**，每片 JUnit/日志/资源/身份 SHA **不存在**，全量 JUnit/日志 SHA **不存在**；全集 FAIL/ERROR/SKIP 的实际节点名单和数量 **未知/未测**，不能填 0，也不以 R6 旧 5,089 个显式 testcase 或 R8 两文件 47 节点代填。`L3_SHARDED_R9=BLOCKED_NOT_TESTED`，不是 PASS；R6 单进程失败及 R7/R8 历史判定均未改变。

**对本任务七个结论问题的答复：**512 MiB 原工作集门禁未证明；所有子进程覆盖未证明；依赖及动态输入未完整闭合；正式全集实际收集数未知（未收集）；每节点恰好执行一次未证明（未执行）；完整 L3 未通过且未运行；**仍禁止发布**。不进入 Phase E/F/G；真实工程日期、IRR 全根、F04、正式 F02/PDF、40 项人工审阅、专业签审、WorkBuddy 双案/独立 L3、许可证与发布均是独立阻断。

## 6. 本轮卫生与下一准入

隔离工作树初审 **1310 个已跟踪文件 / 615847770 字节，6 个待纳入的有用文件 / 115558 字节**；六文件均仅以显式路径暂存并作非发布 WIP 源码提交，未净删除历史跟踪文件或伪造释放空间；已有 115 条历史已跟踪生成日志待独立追溯，不在本轮范围删。随后本回执为必要合同文件而单独提交；每一步 `git diff --check`、状态、暂存路径读回；工作树不存在无用途未跟踪文件。R9 树 `dist_candidates=[]`、`git ls-files -- dist` 为空、`.gitignore` 已忽略 `dist/`；本轮无本地可用候选 ZIP，不宣称 `DIST_LOCAL_VALID=PASS`（实际 `BLOCKED/NOT_ASSESSED`）；历史保护的 R2 请求原件在忽略目录保留。其他产品和主工作树未清理。质量状态：`TRACKED_ARTIFACT_CLEANUP=NOT_APPLICABLE（净删除 0）`、`UNTRACKED_HYGIENE=PASS`、`SOURCE_AND_TEST_PROTECTION=PASS`、`REGRESSION_TESTS=PASS（仅 59/59 限定，全集 NOT_TESTED）`、`ARTIFACT_QA=BLOCKED`、`PLATFORM_AND_RELEASE=BLOCKED`。

下一准入必须先在不修改财务/512 MiB/节点/锁文件的前提下建立**真正无遗漏的子孙进程生命周期工作集证据与事件丢失证明**，再获得确切 wheel 与安装文件字节及实际无损动态读输入闭包，进行独立复核和重型单文件探针；任一项不能满足继续 `BLOCKED_NOT_TESTED`。条件齐备后才允许在同一冻结身份上正式 collect-only 和串行全集，任何失败保留原件、不自动重试、不跨 SHA 拼接。普通分支 push 不代表发布或本阶段正式验收。最终报告提交/远端 HEAD 的精确读回另存于私有 `C:/Users/wangbin/Documents/solar-pv-tools/r9-native-reviewed-20261120/r9-final-git-state.json` 并在交付消息列明。
