# R8 B1 — 光伏 L3 按测试文件串行分片契约（版本 1）

**范围**：仅新增 `L3_SHARDED_*` 证据链；R7 原型原参数、`l3-solar` 单进程与原 `verify` 不变。R6 单进程 FAIL 不继承本链结果。此文件是 B1 工具合同，不是 B2 独立 QA 准入或全量执行回执。

## 入口、身份、边界

- `python -m tooling.solar_pv_l3_sharded full --out <仓库外全新私有目录> --pandoc C:/Users/wangbin/Documents/solar-pv-tools/pandoc-3.14/pandoc.exe --timeout 7200`。开发小样增加两个或三个完整文件的 `--smoke-select tests/solar-pv/test_x.py`，只能返回 `SMOKE_ONLY`，不等于正式全量；无此参数才取 `tests/solar-pv` 全集。默认每个子进程 7200 秒，允许 10..14400 秒；不会为了超时拆分文件、重试、降低覆盖或改变测试 fixture 作用域。
- 输出目录必须尚不存在且在仓库外；每片独立 `workspace-tmp`（TMPDIR/TMP/TEMP）和 `pytest-basetemp`，独立 `stdout.log`、`stderr.log`、`junit.xml`、`receipt.json`。先一次真实 `--collect-only`，然后按文件名排序，每文件一个新进程，前一片证据验证后才启动后一片。集合的有序 nodeid 与 `SHA256(UTF8("\\n".join(ids)))` 存入 `summary.json`。
- 固定本机 HEAD、R7 受控源码／测试／工具／产品／文档／配置真实字节，以及 Git 跟踪的 `reports/solar-pv` 证据 fixture 全部字节摘要。解释器绝对路径、版本、pytest、安装包名称/版本集合摘要、环境条件（含路径、时区及 pytest 插件相关环境）逐进程检查；拒绝继承的 `PYTEST_ADDOPTS`、`PYTEST_PLUGINS`、`PYTHONPATH`。Pandoc 要求绝对 regular exe、exe SHA-256 `81b551129ae36faa420e07223390252547af92e00e2cc570bc57fee61ccbc623` 与 `pandoc 3.14`，仅注入子进程的 `WANGBIN_SOLAR_PV_PANDOC`。ZIP 的公开 SHA 不替代 exe SHA。子进程的环境与 Python 导入路径被明确设定，不修改系统 PATH。预期源代码工作树只在全部修改完成后冻结；未提交 HEAD 不单独代表不可变源码。
- Windows 使用 Job Object 的 **job+process private-commit 硬上限 512 MiB**，先 `CREATE_SUSPENDED`，加入 Job 后才恢复线程；Job 关句柄终止未退出子树。另用已存在的 psutil `7.2.2` 逐进程 PID/创建时间记录工作集当前和生命周期 `peak_wset`，合计所有已观测进程 lifetime peak（保守上界）；以 Job 的 `total_processes` 核对观测数，拒绝没观测到真正 Python 子进程、峰值超限、访问失败、未退出的孙进程、无法创建/分配 Job 或超时。**硬 Job 限额约束 private commit，不等于物理工作集；采样不能独立证明未观测到的共享映射工作集瞬态峰值。**这项 OS 峰值等价性和安装包 wheel 字节身份未得到独立 B2 证明前，正式全量仍 **BLOCKED**，不能仅据工具输出自称 512 MiB 已审定。

## 证据 schema 与 fail-closed

- 顶层 `solar-pv-l3-sharded/1`：`mode`、`verdict`、`identity`、`conditions`、`pandoc`、`files`、`collected_ids`、`collection_sha256`、`shards`、`process_timeout_seconds`。进程 `solar-pv-l3-sharded-process/1`：`kind`、完整 `command`、`scratch`、开始结束 UTC、`exit_code`、`timed_out`、前后 `identity/conditions`、Pandoc、`resource`、stdout/stderr/JUnit 原始 SHA-256。失败进程依旧写原始回执；顶层 `INCOMPLETE` 和 `error`，退出 2。原始回执只创建一次，不原地修复/覆盖。
- 完整收集拒绝空、重复、超范围、不合法或参数后缀变化 ID，拒绝 `deselected`、报告数与列表不符、被漏掉的测试文件。JUnit 顶层/每 suite 精确计数、每个 testcase 必须映射唯一标准 nodeid；额外、遗漏、重复、参数化差异、非零进程退出、无 JUnit、fail/error/任何 skip、未表示 subtest、混合 failure/error、嵌套结果标签一律拒绝。按文件精确匹配收集与执行，聚合后必须精确覆盖全集；不能以成功汇总标签代替 raw JUnit。
- 独立 CLI：`python -m tooling.solar_pv_l3_sharded_verify --evidence <目录>`，重读原始 bytes/hash、命令、身份、日志、全集、每片 XML 与过程资源声明；默认与当前 checkout 字节及 Pandoc exe 重比。`--archived-only` 只做内部一致性检查，**绝不**给 full 当前源码门禁通过；历史混 SHA 回执不能恢复。验证器独立实现 XML 与现场身份读取，**不调用调度器或原型 parser**。摘要不带公钥签名，任何持有整个私有证据目录写权限的人可同时伪造日志与摘要；本链须用受控不可变原始回执及独立 QA 做可信来源保护，不宣称抵抗整体重写。
- **无续跑**：任何中断、失败或超时保留目录为 `INCOMPLETE`；新执行只能在新的空目录、同一冻结候选重新收集并完整执行，禁止跨 HEAD/条件拼接和改旧 receipt。正式 B2 独立 QA 未对最终冻结字节快照、真实 Job Object 限额／解释器子进程、Pandoc 和 fixture 不变性验收之前，不得运行 full；B3/B4、WorkBuddy、发布、F02/PDF/专业签审保持 `NOT_TESTED/BLOCKED`。
- 本版本的 **`full` CLI 在收集前硬拒绝**（即使提供已验证 Pandoc），直到在本轮已授权 B 范围内有可审计的源码升级解决上述 B2 可证明性阻断，且最终冻结源码独立 QA 通过；当前仅可执行 `--smoke-select` 开发样本。不得移除此拒绝以便先跑全量。工具的保守拒绝不是完整 L3 的通过，也不会重写任何历史回执。
- B2 初次独立审查发现：JUnit 可携带未审定的 `status="failed"` 或未知 suite/property 属性仍被当作 PASS；资源回执可声明只见一个进程或不可信微小峰值，结束时刻也可超出所记期限。这些**可修复的验证器缺口**已补上白名单、最小进程数量、数值一致性与时限校验，仍须对最终冻结源码再次独立负例复验。数值下界只是异常回执拒绝规则，**不能**代替 512 MiB 物理工作集硬门禁或可信进程逐 PID 原始观测。
- B2 同时发现 `tests/solar-pv/test_ai_host_input_view.py` 引用已忽略的 `.runtime/solar-pv/r2-client-552-20261113-132354/workspaces/.../CH08-1-request.json`，初审时隔离工作树缺这两份原件；后来仅从主工作树原字节复制到隔离树相同忽略路径，两个副本哈希分别为 `d48b0bfad84b303d7f7978d6c9e53f78aba424541992f509240df8a09928bae1`、`976ce58137f5aee380de765584df59d78d4777e993cc9f1ddd7dc912d616df6a`。正式工具与独立验证器现在均对**这两份已知文件**作逐字节绑定，不能因此推断所有动态/忽略输入已构成完整闭包。已安装依赖只绑定包名/版本、不绑定 wheel 或安装后文件字节。正式全集前须独立盘点并绑定其余全部外部/忽略输入、解释器与依赖字节，并证明资源门禁；不能修改测试断言或虚构原始资料来规避缺口。

## B1 开发验证与明确余项

`tests/solar-pv/test_solar_pv_l3_sharded.py` 是攻击性工具测试（合成证据明确不是运行实测）：篡改集合、重复/缺节点、参数化漂移、伪造顶层 PASS、改日志/回执/JUnit、重哈希 deselect/隐藏失败/skip、混合 outcome、超限、超时、环境漂移、中断等。B2 必须用另一执行角色在**全部源码冻结后**复测小样并直接运行独立 CLI，补充 Job Object 真实限额拒绝、安装 wheel 字节清单与未跟踪/被忽略动态 fixture 的输入闭包；本开发角色的绿灯不等于 B2。无 B2 结论/源提交、无资源门禁确定性证明，`L3_SHARDED_R8=NOT_TESTED/BLOCKED`，不可启动全量；后续所有正式证据必须绑定新的不可变提交 SHA。
