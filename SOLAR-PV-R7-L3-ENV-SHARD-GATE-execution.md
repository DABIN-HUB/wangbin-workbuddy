# SOLAR-PV-R7-L3-ENV-SHARD-GATE｜执行回执（环境与机制准入，非发布）

状态：**有限原型与历史审计完成；正式 L3 `NOT_TESTED`，等待两项独立授权**。本文件记录 R7 范围内可合法执行的本地工具开发；不变更冻结财务公式、Phase E/F/G、旧回执或 WorkBuddy 安装。精确最终提交 SHA、远端读回和最终 QA 见本文件末尾的收口记录；本文件所在报告提交本身不得倒填为受测源码。

## 1. 身份、原件和保护

- 开工时本地主工作树 `main`、`origin/main`：`0ad56e30face3193ea8e9d043be87811be6b1b17`；其父修复候选为 `18e988be7bcb1296ce784176f95662bed7aff745`；旧完整 L3 失败候选为 `561d442c281e1c2ab9f161e59eb7bf5a004aecbc`。研发工作树：`F:/ideaWorkSpace/wangbin-workbuddy-r7-env-shard`，分支 `solar/r7-l3-env-shard-gate`，从报告 HEAD 创建。主工作树已有 `?? uv.lock`，不暂存、不覆盖；其余工作树及其他产品不处理。
- R6 原始 XML、日志、回执保存在主工作树忽略目录 `.runtime/solar-pv/R6-production-chain-l3/formal-receipts/solar-pv-r6-561d442-l3-solar/`，来自旧原始 scratch，`copy-manifest.json` 逐项标记本地副本而非远端备份。本次逐字节校验 JUnit SHA-256 `ccd719f0e38a9af3802d3b5d08534a3525f1e8fa7d31c4b3943d99cf0f49a41f`、日志 `84c684e860c54077ef38d12d70f6f0ca07b15866ab91a76bb7a3cef710d595c5`、回执 `9f2cb48ed09132c8a986ffc0d841e20e0e4577e7bfe22d0641818d7c6a924d90`。
- 原失败回执 `pytest_exit=1/gate_exit=1/evidence_error=ambiguous JUnit outcome` **保留原样**；下列新解析结论不回写旧回执。R6 原候选 5089 显式 testcase、5093 suite declared（4 个未单列 subtests）、4848 PASS、121 FAIL、109 ERROR、11 SKIP；其中一个 testcase 有两条 `<failure>`，故 failure element 122，而互异 failure testcase 121。

## 2. P0：逐节点互斥根因

完整 230 行逐一归因表：`reports/solar-pv/r7-failed-node-root-cause.json`，SHA-256 **`93eb549598a61ed0f24fc4f56a028039b6bdeb5a9d5606bff5c66d99cba7bd24`**。每行包括精确参数化 nodeid、旧 testcase 位置/结果、全部 failure/error 标签的异常类型与原消息、各原始栈的 SHA、首/继发异常、日志行号、互斥根因、源码/环境指针、当前修复候选范围及原件 SHA。原始完整栈仍按 testcase 序号存在不可变 JUnit 中；表中不重复公开大段潜在敏感日志。全部 230 个 nodeid 唯一且已归类；JSON 的排序 nodeid 摘要 `a646225e8dd75ce21aed683ef9e93e835a60b1f3c238726ff2546ea05383cf28`。

| 互斥主因 | 旧节点 | 细分及当前判断 |
|---|---:|---|
| `BUNDLE_MEMORY_LIMIT` | 155 | 68 failure + 61 error 直接触发内存检查，另 26 failure 的预期其他错误被内存高水位遮蔽；不能据此认定后者业务逻辑通过。 |
| 同一内存错误经 CLI 包装传播 | 2 | 原 XML 只见 `returncode` 断言；原日志 `output.log:3668,4578` 均有 `{"error":{"code":"BUNDLE_MEMORY_LIMIT","field_id":null}}`。 |
| `REPORT_OMML_CONVERTER_UNAVAILABLE` | 56 | 8 直接 failure、48 fixture/setup error；未证实有本地可执行 Pandoc。 |
| 无债旧方法集缺失可选 `debt.opening_principal` | 15 | `18e988b` 源码差异和定向回归已解决此选项兼容，不改变有债/已有参数的审查。 |
| 旧报告期望语义 | 2 | `18e988b` 已对 `LIMITED_BY_MISSING_EVIDENCE` 和 DSCR 展示做精确专项复核。 |
| **合计** | **230** | 未发现旧原件中的其他独立异常；不等于未来不同环境下不会暴露新失败。 |

`18e988b` 的 101 项定向 JUnit 与旧 230 行精确 ID 交集 **17 行 PASS（15+2）**，其余 **213 行 NOT_TESTED**，不可把 101 记作旧失败关闭数。11 个旧 SKIP 逐项如下，均非 PASS：

| nodeid（省略共同前缀 `tests/solar-pv/`） | 原因 |
|---|---|
| `test_cli.py::test_real_symlinks_are_rejected_in_all_path_positions[file]` | Windows symlink privilege unavailable: 22 |
| `test_cli.py::test_real_symlinks_are_rejected_in_all_path_positions[ancestor]` | 同上 |
| `test_cli.py::test_real_symlinks_are_rejected_in_all_path_positions[workspace]` | 同上 |
| `test_parser_security.py::test_symlinks_and_linked_root_are_rejected_or_explicitly_skipped[file]` | Windows symlink privilege unavailable: OSError |
| `test_parser_security.py::test_symlinks_and_linked_root_are_rejected_or_explicitly_skipped[root]` | 同上 |
| `test_report_claims_analysis.py::test_ch10_roof_separates_load_savings_export_and_receipts[utility_scale_ground]` | roof-only |
| `test_report_claims_analysis.py::test_ground_uses_market_price_series_and_curtailment_without_rooftop_load[industrial_rooftop]` | ground-only |
| `test_report_claims_analysis.py::test_supplied_market_series_with_blocked_revenue_is_not_called_absent[industrial_rooftop]` | ground-only |
| `test_report_claims_analysis.py::test_ground_curtailment_narrative_changes_with_bound_input[industrial_rooftop]` | ground-only |
| `test_report_r3_narrative.py::test_ground_price_status_and_roof_load_rebind[utility_scale_ground]` | roof only |
| `test_report_r3_narrative.py::test_changed_or_unbound_source_does_not_keep_roof_load_comparison[utility_scale_ground]` | roof only |

## 3. P1：Pandoc 的拟批准来源与真实环境

本进程 `PATH` 和 `WANGBIN_SOLAR_PV_PANDOC` 均未定位 Pandoc；只读检查了 `C:/Program Files/Pandoc`、用户本地 Programs、`D:/dowloads` 与主工作树光伏受控运行目录，均未发现 `pandoc.exe`。这不是全盘未安装的证明；**本轮没有实测 exe 字节、版本或 OMML 成功输出**。

拟批准资产：Pandoc **3.14** Windows x86_64 ZIP，官方 [release](https://github.com/jgm/pandoc/releases/tag/3.14) 与 [asset metadata](https://github.com/jgm/pandoc/releases/expanded_assets/3.14)，文件 `pandoc-3.14-windows-x86_64.zip`，发布页 SHA-256 `0144b96e8c7b023fd382ec5ef5bdc475e873f1019d6fa72502492df2c9a94a3b`。这是官方 **ZIP** 摘要，不是 exe 实测哈希，也不把旧文档提到的 3.13 当作当前安装。该版本源码的 [COPYRIGHT](https://github.com/jgm/pandoc/blob/3.14/COPYRIGHT) 声明主体 GPL-2.0-or-later，并列出不同但 GPL 兼容的第三方许可；仅私有隔离使用的拟议方案不代表已完成产品分发的许可证审查。源码 `report_equations.py:74-126` 实际执行 `--from=markdown+tex_math_dollars --to=docx` 并检查真实 `m:oMath`；并非 WPS/PDF 路径。

**授权动作 A（尚未获批）**：允许从上述唯一官方 URL 取得该 ZIP，在用户私有隔离目录 `C:/Users/wangbin/Documents/solar-pv-tools/pandoc-3.14/` 校验官方 ZIP SHA，校验 ZIP 成员安全后解压；单独记录 `pandoc.exe` SHA、绝对路径和 `pandoc.exe --version`，再只对原 89 式目录的合法小样及已有 `tests/solar-pv/test_report_r9_equations.py` 执行真实 Markdown→DOCX→`word/document.xml`/`python-docx` OMML 验收。验证命令的核心分别是 `sha256sum <批准的ZIP>`、`<绝对路径>/pandoc.exe --version` 和 `WANGBIN_SOLAR_PV_PANDOC=<绝对路径> python -B -m pytest -q -p no:cacheprovider tests/solar-pv/test_report_r9_equations.py --basetemp=<新的仓库外QA目录>`；执行时记录 CLI 完整命令/日志/JUnit/hash、ZIP/exe 和前后源身份。验收前无任何转换器节点可写 PASS。回退仅清理经逐文件确认**本轮创建**的上述隔离目录/ZIP/解压件及运行 scratch，不改系统 PATH、MSI 或旧 3.13 资产；失败原始回执必须留存。当前 **未下载、未解压、未安装、未运行新程序**。

## 4. P2/P3：不放宽 512 MiB 的执行机制与 JUnit 解析

`timeseries_private.py:43-69` 在 `Meter` 创建时核对 Windows working set 当前量与进程生命周期峰值，默认 `BundleBudget.max_memory_bytes=512×1024×1024`；R6 单 pytest 进程在第 990 个节点附近开始污染后续结果。未改 `Meter`、预算、冻结方法或测试断言。

在隔离研发工作树新增 `tooling/solar_pv_l3_sharded.py` **受限原型**：只允许 2–3 个预先审过的快测文件（没有全树/OMML 入口），且拒绝未经绑定的 Pandoc 环境变量或 PATH 命中；收集精确参数化 ID 并保存原文/hash；按文件确定性分区；每个文件从相同固定解释器新启动一个串行 Python pytest 子进程，各有独占 TMPDIR、basetemp、JUnit、日志、起止时间、退出码、输入字节/HEAD及解释器/依赖指纹；逐个校验收集/执行 ID、失败/错误/SKIP、重复/缺失、原始 XML/日志 SHA 和身份漂移，另存独立 `solar-pv-sharded-prototype/1` 聚合 JSON，不改旧 `l3-solar` 或 `verify`。任何 SKIP/未单列 subtest 使原型退出非零，即使 XML/pytest 无失败。Windows 直接进程 PID 与可用时的子进程树分别采样 working set/OS peak，区分采样值和真正 `Meter` 检查。不存在已获批全量模式；原型成功的标签仅 `PASSED_PROTOTYPE_ONLY`。

`tooling/solar_pv_regression.py:91-168` 现允许单节点多个**同类** `<failure>`，保留各自 type/message/full text，分别计 testcase/element；mixed error/failure/skip、重复的非 failure outcome、suite 标签总数不符、非法 testcase 直接及嵌套子标签（含 property、system-out）、normalized ID 重复均在**生成成功回执前** fail-closed；新的回执含 `element_counts`，成功/跳过节点仍保留原 `cases` 结构和 `verify` 语义，旧回执不变。旧 R6 原 XML 在新解析器下读回：`counts=4848/11/121/109`（PASS/SKIP/FAIL/ERROR），`element_counts=122/109/11`，`unrepresented_tests=4`，5089 个 normalized ID 唯一。原 `pytest_exit=1` **仍然是失败**。

开发者于未提交研发字节上执行：
- `python -B -m pytest -q -p no:cacheprovider --basetemp=<独立 scratch> tests/solar-pv/test_solar_pv_regression_tool.py`：后审修复后 **7 PASS**、0 FAIL/ERROR/SKIP；anyio/pytest 弃用警告 1 项。
- `python -B -m tooling.solar_pv_l3_sharded --select tests/solar-pv/test_method_configuration.py --select tests/solar-pv/test_phase3e_irr_roots.py --out <独立 scratch> --timeout 180`：后审修复后收集 **47** 个精确 nodeid、2 个独立子进程分别 **30/17 PASS**，0 FAIL/ERROR/SKIP，ID 和字节身份前后一致；原型摘要路径 `C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-r7-shard-prototype-postreview/summary.json`，SHA-256 `55447a9b88a82d7539294656506efb56ba14e9e0da35fe819debbd0ee64cfe0b`。这 47 项并非全集。OS 采样识别出 Windows venv `python.exe` 的约 4 MiB 启动器与实际测试解释器子进程峰值 53,125,120 / 48,439,296 字节；采样本身不代替束内 Meter 限额检查。

文件级分区不能自动证明跨文件 session fixture/共享状态语义相同，更不能因 47 项通过宣称覆盖剩余节点。完整新候选的所有光伏 ID 需在获批后重新收集、每个 ID 恰好分配/执行一次、所有子进程逐回执 QA、与旧单进程语义差异单列；未来确实超出 512 MiB 的分片仍 FAIL。原型未实现完整集合命令/正式聚合验证器，禁止编造可运行的全量命令。

**授权动作 B（尚未获批）**：明确批准**把分进程全集覆盖作为新的可接受光伏 L3 验收方式，并运行全量**（预计数千项、按收集实数不写死 5090）。获批后先完成独立正式规范、全树入口及独立验证器/QA，并在唯一最终 HEAD 上绑定 Pandoc 绝对路径、exe SHA 和版本、Python/依赖/受控源码/配置哈希；仅在全部预检通过后于全新仓库外私有运行目录串行启动完整分片。每片保留 JUnit/日志/退出码/资源样本、任何超时/失败/跳过/未覆盖均不能给绿色；`l3-workbuddy` 另行取得本候选正式回执前仍不宣称三门禁全过。**当前原型故意没有 `--full` 等可执行全集命令**，因此不能以自行拼参数代替用户授权。

## 5. 收口、未测与交付边界

- 独立 QA 第一轮实测工具 6 PASS、两文件 30/17 PASS，指出归一化 ID/非法标签、OMML/PATH、意外 SKIP 等问题；第二轮 7 PASS、30/17 PASS 后发现嵌套 `<property><failure>` 可冒充 PASS。开发者修复后第三轮独立 QA 对**最终源码字节**实测工具 **7 PASS、1 项 anyio/pytest 弃用警告**，非法嵌套 property/system-out/error、未知直接标签、归一化 ID 冲突均拒绝；双 failure 保留两份完整证据；`PYTEST_ADDOPTS=--deselect` 反例非零。全新 scratch 的两文件原型 47 个唯一 ID，**30/17 PASS、零 FAIL/ERROR/SKIP/未单列**，收集/执行 ID、原始日志/JUnit/回执及前后 580 个输入哈希均由独立 QA 校对；`formal_l3_replacement=false`。第三轮证据目录 `C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-r7-independent-qa3-716b7ba6c9e8/`，`prototype/summary.json` SHA `8561a0f3f7929801f9777edfbf100810c35608c7960d54ee4c4cab7e1d87eba1`，`focused-output.log` SHA `d3e3fcd1cb9b1efbc8e4a55655218895a012a07f68d9ee10ee38058706f6250c`；当时报告 HEAD `0ad56e30face3193ea8e9d043be87811be6b1b17`、输入摘要 `71c8f1a78fe9caf8cc4c84ad33ff2f47a824792343ca1206d069bfdea5599a4a`、解析器字节 SHA `2de28520b3dcee879f1b5bd23782253919e6202c33af613e704c11d8f75f2cd1`。这些是**受限工具准入**，不是完整 L3、Pandoc 或发布验收。
- 新完整 L3：**未运行**，当前光伏完整收集参考值仍是旧 `18e988b` 的 5090，不属于本轮新头的被测全集。矩阵旧失败未在新候选重测的 213 个节点保持 NOT_TESTED；其他光伏节点也没有新头的完整 L3 回执。新版出包/隔离安装/真实 WorkBuddy 平台运行：NOT_TESTED；R6 旧 wheel `wangbin_solar_pv_input-0.3.2-py3-none-any.whl` 已按原字节重核 SHA `8767fa19cd5456f6a902018589226bcdfcf2b449a6b36db6a67c33a829c3f168`，只归属 `18e988b` 源码，不能据同版本号冒充新 HEAD 的发布构件。
- F04、正式 F02/PDF、真实工程日期、IRR 根集合证明、40 项用户审阅、专业签审、四件套、Phase E/F/G、许可证/平台/发布门禁：仍 BLOCKED/NOT_TESTED；不以工具回归替代。
- 本轮没有清理已跟踪文件，也没有删除受保护证据/旧 dist。只保留各自独立原型原始回执；非发布。下方最终收口记录将给出本地提交、卫生检查及远端实际状态；**未经新的有效光伏 main 推送授权不 push**。

### 最终收口记录

独立 QA 后本地提交和最终核验的**精确提交 SHA**、提交前后路径/字节、测试回执及远端读回见忽略目录 `.runtime/solar-pv/R7-l3-env-shard-gate/final-state.json`（提交后写入，避免本文件自引用提交 SHA）。主工作树及其受保护未跟踪 `uv.lock` 保持原样；原 R6 wheel ZIP CRC 可读（123 个成员），11 个复制原件的清单哈希逐项匹配。本隔离工作树没有复制主工作树 `dist/`：主工作树本轮只读复核的四份光伏本地候选 ZIP CRC、各自成员哈希/大小、LICENSE、manifest 与 sidecar SHA 均相符且原样留存，**它们不是 R7 新源码候选**；本隔离工作树无 dist 包，不发布/安装。未自动 push；仅在获得独立有效授权且目标 `main` 可安全快进时才考虑普通 push。
