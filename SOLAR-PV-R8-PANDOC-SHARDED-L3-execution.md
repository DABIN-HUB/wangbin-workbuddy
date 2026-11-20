# SOLAR-PV-R8-PANDOC-SHARDED-L3｜执行与停止回执

**日期：2026-11-20（中国标准时间）**　**范围：仅授权 A、B；未进入 Phase E/F/G、合并、发布或平台上传。**

## 判定

| 独立门禁 | 实际状态 | 可复核依据 |
| --- | --- | --- |
| `PANDOC_OMML` | **PASS（仅授权 A）** | 官方 Pandoc 3.14 ZIP/exe 原字节、真实 89 式 DOCX/OMML 和对应专项 JUnit |
| B1 工具与规范 | **已作非发布本地提交** | `477241f5c58d942218c3baacb88a0a904d60fa87`，新增正式入口、独立验证器、负例和版本化合同；正式 `full` 保持硬阻断 |
| B2 独立 QA | **限定范围 PASS；正式准入 BLOCKED** | 最终冻结源码负例 40 PASS，两个文件 47 个 nodeid 独立复核；资源/输入闭包仍未获证 |
| 完整 R8 全集收集与身份核对 | **NOT_TESTED** | 未启动；当前全集 nodeid 准确数未知，不挪用 R6 的 5,089 显式 testcase |
| `L3_SINGLE_PROCESS_R6` | **FAIL（原判不变）** | R6 原始失败 XML：5,089 显式 testcase／5,093 suite 声明；4,848 PASS、121 FAIL 节点、109 ERROR、11 SKIP |
| `L3_SHARDED_R8` | **NOT_TESTED / BLOCKED** | 正式 `full` 在收集前退出 2，不产生输出目录；没有完整分片回执，不能报 `FULL_ALL_PASSED` |
| `L3_WORKBUDDY` / `RELEASE_READY` | **NOT_TESTED / BLOCKED** | 没有另一次 WorkBuddy L3 或平台/发布回执 |

### A：官方 ZIP 私有验收

仅取得授权 URL `https://github.com/jgm/pandoc/releases/download/3.14/pandoc-3.14-windows-x86_64.zip` 的 ZIP，43,614,099 字节，实测 SHA-256 `0144b96e8c7b023fd382ec5ef5bdc475e873f1019d6fa72502492df2c9a94a3b`（与授权给定官方值相同）。验证成员路径/重复/展开大小/类型/CRC 与随包许可证后私有解压；未安装 MSI、修改系统 PATH、覆盖既有程序或更换版本。随包声明 GPL-2.0-or-later 及第三方例外；**不等于产品分发许可审查通过**。

私有 `C:/Users/wangbin/Documents/solar-pv-tools/pandoc-3.14/pandoc.exe` 的实际 SHA-256 为 `81b551129ae36faa420e07223390252547af92e00e2cc570bc57fee61ccbc623`，实际执行 `--version` 输出 `pandoc 3.14`。在 R7 HEAD `92f5dc50aceeed975ba5a55716651aafe2f466bd` 上以真实 Markdown 数学→DOCX→`word/document.xml`／`python-docx` OMML 检查：**89 个互异源码公式 ID、89 个非空可编辑 OMML 对象**，逐项对应。DOCX SHA-256 `c63ff30ddd89b7b23b343f27b914b60fbaf5cf3fa2b3e61a99c7c0feadecc25f`。完整 `tests/solar-pv/test_report_r9_equations.py`：**1 collected / 1 passed / 0 failed / 0 error / 0 skipped**；JUnit SHA-256 `1ab24505723a80b43e29223de87bcc8a6fc4c7e82f2a843007196711dd0a4d4d`。

原件：`C:/Users/wangbin/Documents/solar-pv-tools/r8-pandoc-evidence-20261120T101050-eb6f6632/`，包括官方 ZIP、`actual-89-formulas.docx`、`focused-junit.xml`、日志、`roundtrip-receipt.json`、`final-verification.json` 与 `evidence-manifest.json`。再次读回 **28/28** 个 manifest 成员的大小和 SHA 均匹配；证据准备期间的路径笔误及并行写日志时取哈希的失败尝试亦原样保留，不是 OMML 计算失败。A 不证明正式 F02、PDF 阅读器效果或后续业务门禁。

### B：工具、独立 QA 与实际覆盖

R7 原型与旧 `l3-solar`／`verify` 保留原有语义。B1 仅提交四个路径：`tooling/solar_pv_l3_sharded.py`、`tooling/solar_pv_l3_sharded_verify.py`、`tests/solar-pv/test_solar_pv_l3_sharded.py`、`docs/solar-pv/32-r8-l3-sharded-acceptance.md`；冻结 B1 HEAD `477241f5c58d942218c3baacb88a0a904d60fa87`。新命令的 `full` 及独立原件验证器使用 `solar-pv-l3-sharded/1`；按文件串行、一次收集、每片独立 JUnit/日志/退出/前后身份/资源声明、不中断续跑。`full` 当前**有意在收集及输出目录创建前拒绝**，没有旁路或把旧回执改成绿色。

初次独立 B2 审查在旧未提交字节上发现：未知 JUnit 属性／`status="failed"`、伪造单进程/微小资源数、超时后结束时间可被误收；对应负例后已修补验证器属性白名单、资源数值/进程数量关系和时间界限。历史测试读取的两份忽略文件最初未在隔离树；只从主工作树原字节复制到隔离树的忽略目录，并独立校验 SHA-256 `d48b0bfad84b303d7f7978d6c9e53f78aba424541992f509240df8a09928bae1` 与 `976ce58137f5aee380de765584df59d78d4777e993cc9f1ddd7dc912d616df6a`；正式调度器和独立验证器均绑定**这两份已知原件**。不提交该私有原件，不将其哈希当作全输入闭包的证明。

最终冻结 HEAD 的独立复核：攻击性工具测试 **40 collected / 40 passed / 0 failed/error/skipped**，JUnit SHA-256 `a99902d66de5171325189e80adfc9ef682b930254d3c4a33e210d11eaa978c51`，路径 `C:/Users/wangbin/Documents/solar-pv-tools/r8-b2-final-qa-20261120-110525-attacker-v2/`。在原件副本上的七种独立改写负例（未知属性、假失败状态、隐藏 property 属性、单进程、极小峰值、超期、fixture 字节变化）**7/7 被拒绝**；私有目录 `.../r8-b2-final-qa-20261120-110525-negative-probes-v3/`。这些合成负例不是 OS 资源限制的物理证明。

同一冻结 HEAD 的独立真实小样选中 `test_method_configuration.py` 和 `test_phase3e_irr_roots.py`，仅两文件：**47 个唯一有序 nodeid**，两片 **30/17**；JUnit 显式/声明数匹配、FAIL/ERROR/SKIP 均为 0；收集摘要 `a08dce1e7d602c960a8966099cd203fc088e0b2f3a35a50e2f13c1deb64b62cb`。独立 CLI 重读原始日志、XML、回执和受控身份并返回 `SMOKE_ONLY`，不是全集。原件目录 `C:/Users/wangbin/Documents/solar-pv-tools/r8-b2-final-qa-20261120-110525-smoke-v2/`；`summary.json` SHA-256 `4f70560ccc8b5ab9076db120e680f926f343913335543a2103c47f569602a55e`，两片 XML SHA-256 分别为 `2fbefe8b9e00aa57e43b5bfe9b59a76e75eb1c5c50ab6e89eb1cd3f2eb02c27a`、`342924bcd58298543433709504c3f66384fc25c33404def023b0ac3c56b8ecbb`。输入清单 583 项，清单摘要 `94287c745a6e2bc3c84fc95b8498364e745a7300f03214341f147c0efd7ea96f`，另绑定两份已知忽略 fixture。首次小样 `...-smoke/` 因 shard-001 的 `process lost/denied during sample` **失败并保留**；新目录 `...-smoke-v2/` 重跑同一冻结 HEAD 后才获限定范围 PASS，不消去首次失败。正式资源可信性仍不因此得证。

**全集计数与旧 230 节点：**当前正式全集没有收集，因此全集 nodeid 数、逐片状态和实际全集 SKIP 数均为**未知／未测**。R6 原始 JUnit 的 230 个互异失败/错误节点按原件矩阵：内存 155、内存经 CLI 包装传播 2、OMML 56、无债兼容 15、历史报告语义 2；旧 `18e988be7bcb1296ce784176f95662bed7aff745` 候选仅 17 个精确同名节点另有定向 PASS，其余 213 在该候选未复验。R8 47 节点小样与旧 230 **交集为 0**；不得将 17 个旧定向 PASS 或 A 的 89 式通过折算成当前 230 节点已关闭。尚无 R8 全集收集 ID，改名/分裂/删除的旧 ID 数也未知。

### 未解除的硬阻断与可执行下一门

1. **512 MiB 原门禁未证明**：Job Object 对子进程树施加 512 MiB private-commit 硬限额，但它不等同于每个实际计算解释器的全部瞬态物理 working set；`psutil` 采样与总进程数不能独立复算每个 PID/创建时间的全生命周期峰值。小样曾出现一次采样进程丢失并按设计失败。正式运行前须按合同形成可信的物理工作集当前/生命周期 OS 峰值与完整进程树证据，再独立负例复核；不能把启动器 4 MiB 或两片小样冒充全套证明。
2. **输入身份闭包未证明**：受控 Git 文件、已跟踪 `reports/solar-pv` 和上述两份已知忽略 fixture 已绑定；所有其余被忽略/动态输入、解释器及已安装 wheel/文件的真实字节尚未逐项闭合。包名/版本摘要不是 wheel 字节身份；父目录链接拒绝和已知 fixture 校验只是局部修复。
3. **正式候选环境预检与 B2 全准入尚未完成**：本次只是最终源码的工具负例/两文件小样；不以机器容量快照代替重型单文件资源、全节点身份或正式环境验证。当前 `full` 无 `--smoke-select` 退出 2，`formal full BLOCKED: B2 OS working-set/wheel-byte admission not established`，**未创建输出目录、未运行全量 collect-only，也未执行一次正式完整 L3**。
4. **业务和发布阻断不变**：真实工程日期与来源、IRR 完整根集合、F04、正式 F02、40 项人工审阅、专业签审、WorkBuddy 宿主双案验收及独立 WorkBuddy L3/平台发布，均无本轮正式解除证据；Phase E/F/G 未进入，`RELEASE_READY=BLOCKED`。

后续在**本轮 B 授权范围内**，先解决上述 OS 资源证明和安装依赖/动态输入闭包，修复并独立复测，再对新冻结候选做正式全量收集、环境预检及一次完整串行执行；任何失败或漂移保留原件，不能跨源码 SHA 拼接绿色回执。完整门禁未开之前，不安排全集或发布。

### 保全、仓库与卫生

- R7 本地提交 `92f5dc50aceeed975ba5a55716651aafe2f466bd` 已通过独立 `git bundle verify` 保存在 `C:/Users/wangbin/Documents/solar-pv-tools/r8-preservation/r7-pre-r8-all.bundle`，且用恢复探针核对相同 HEAD；R7 运行证据在 `.../r8-preservation/r7-evidence-copy/`，逐文件哈希索引 `r7-evidence-preservation-manifest.json`。**同机副本不是异盘/云备份**；本轮未重建或覆盖 R6/R7 历史回执。
- B1 代码/规范本地非发布提交 **`477241f5c58d942218c3baacb88a0a904d60fa87`**（父 R7 HEAD 如上）。主工作树 `F:/ideaWorkSpace/wangbin-workbuddy` 的 `main` 和只读查询的远端 `origin/main` 均为 **`0ad56e30face3193ea8e9d043be87811be6b1b17`**；主工作树仍有受保护未跟踪 `uv.lock`，未触碰。分支**未 push**，无 force push/merge/rebase。
- 隔离树本轮源码提交仅四个允许路径，未净删除已跟踪文件；`python tooling/solar_pv_workspace_hygiene.py --check` 为只读，旧报告输出未按文件名扫除。隔离树未发现本轮可验证的本地 `dist` 候选，因此 `DIST_LOCAL_VALID=BLOCKED/NOT_ASSESSED`，不伪称 ZIP 候选已验收；未动其他产品包。B1 提交后暂存/未跟踪状态为清洁。报告作为单独根目录文件提交后，其最终 HEAD/状态须以本地最终状态回执及交付消息读回；该报告**不是** B1 小样源码身份的一部分。

**最终交付结论：**A 限定通过，B 工具与小样限定通过；B2 正式准入、全量覆盖、`L3_SHARDED`、WorkBuddy 与发布全部如实阻断。不得将本地提交或私有 Pandoc 样件宣称为正式光伏交付/平台审核。