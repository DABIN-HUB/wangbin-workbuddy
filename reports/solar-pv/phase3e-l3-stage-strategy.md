# 后续光伏 L3 门禁与自身耗时优化策略（仅策略及历史剖析）

**适用范围：**从此后的普通光伏开发子阶段起采用分级回归；完整 L3 仅作为**重大集成或发布候选**的最终验收门禁。此策略不追溯撤销已在 `ba3c40b76b90ef92151d25e6b054e7738e2fa674` 启动的 P2-5 光伏 L3，也不改变其当前收口要求。没有删减、跳过或降级现有任何测试；本报告只使用历史证据、现有源码和静态调用链，**未实现夹具优化，也没有实测新的 L3 加速**。逐测试及模块时间、原始哈希与 profiler 引用见 `phase3e-l3-historical-hotspots.json`。

## 1. 新的阶段测试策略

| 工作类别 | 开发及验收门禁 | 完整 L3 的位置 |
|---|---|---|
| 普通局部改动／文档与范围审查 | 快速财务/契约检查、实际受影响模块；只有跨 3B→3C→3D→3E 语义时才选必要真实全链 E2E。记录当次 HEAD、源码/测试/配置哈希、参数、JUnit、失败和跳过；审查报告-only 不为形成报告跑全量。 | **非默认**；局部绿灯不能称发布级完整验收。 |
| 重大集成（跨生产者/输入源/公式契约/结果结构/终期或来源隔离） | 先按上行收敛变更与专项，再冻结最终代码、测试、配置及条件。 | **最终候选**完整光伏 L3＋所需 WorkBuddy/Expert L3 一次；真实 JUnit 和回执逐 ID 核对，不隐藏失败或跳过。 |
| 发布候选 | 冻结同一发布候选身份并复核保护文件和结果来源。 | **必须**完成当前候选完整 L3；已覆盖相同条件的 L2 测试 ID 时，用实际完整 L3 JUnit 证明，不叠加重跑相同完整 L2。旧跨提交 JUnit 仅作历史，不可冒充。 |

`python -m tooling.solar_pv_regression` 现有 `fast`、`affected`、`e2e`、`collect-l2`、`l3-solar`、`l3-workbuddy` 和 `verify` 均保留；**没有修改其选项或隐藏测试**。该入口原本就要求显式 tier，策略调整的是**何时要求执行完整 L3**，不是让 `l3-solar` 只跑一部分。`docs/solar-pv/18-phase3e-regression-orchestration.md:20-29` 是 P2-4B/C 对其当时最终候选的规定；本策略面向**后续**普通子阶段，不把历史门禁重写成未曾执行。禁止为了省时把生产者测试、反篡改、合同校验、完整性断言或独立参考移出发布候选 L3。

## 2. 实际耗时热点与数据口径

历史依据：`reports/solar-pv/phase3e-p2-4b-c-root-certification-evidence/solar-l3.xml`，其 SHA-256 在热点 JSON 中核对；**4184 项，4177 passed、7 skipped、0 failures/errors**。JUnit suite `time=20772.211s`，原回执墙钟 `20772.34s`；4184 个 testcase `time` 合计 `20753.169s`，两者差 `19.042s` 为非 testcase 的框架开销。模块耗时包含 fixture setup/call/teardown，不等于某个业务函数的 profiler 时间。

| 历史六个 Phase 3E 重型模块 | 用例 | testcase 耗时 s | 占该次 L3 JUnit suite |
|---|---:|---:|---:|
| `test_phase3e_terminal_npv` | 3 | 3077.366 | 14.815% |
| `test_phase3e_candidate_replay` | 13 | 2655.339 | 12.783% |
| `test_phase3e_terminal_binding` | 16 | 2313.102 | 11.136% |
| `test_phase3e_break_even_project_session` | 4 | 2235.667 | 10.763% |
| `test_phase3e_break_even_project_npv` | 2 | 2107.992 | 10.148% |
| `test_phase3e_financial_candidate_replay` | 5 | 2101.691 | 10.118% |
| **六模块合计** | **43** | **14491.157** | **69.762%** |

用户给出的约 `69.83%` 为估算口径；按已归档 XML 这六个指定模块的 testcase 时间和 suite 分母重算为 **69.762%**。若按全项目最慢六模块排名，`test_energy_generation_capacity` 的 **2678.712s** 会进入前六，合计 **15068.178s / 72.540%**：这是**不同模块集合**，不得混称。`test_consumption_generation` 另占 **1976.855s**，尚无证明其可合法跨用例复用。

最慢单例依次为 `test_declared_independent_project_has_real_full_chain_root_witness` **2181.945s**，`test_no_disposition_has_independent_decimal_cashflow_and_npv` **2047.952s**，`test_one_candidate_recalculates_original_and_sourced_project_npv` **2037.098s**；它们的时间已包含第一次使用 module fixture 的成本，不能将全额当成可删除重复。

独立 SYNTHETIC profiler (`phase3e-p2-4b-c-root-certification-evidence.json:performance`，原始 `performance-before.json`/`performance-after.json`) 的**旧单候选实测** `842.3394485s`，其中整体 Phase2→D3→3C→3D replay `418.436905s`，终期绑定及 3D 重算 `126.266281s`，原始 3E `114.742210s`、候选 3E `128.241907s`。前两者存在嵌套/交叉，**不得简单相加**。新会话打开/首候选/第二候选实测 `337.065824 / 582.469237 / 576.059817s`，双候选合计 `1587.252344s`。把旧**一次**调用线性外推两次的 `1684.678897s` 与之相减得到 `97.426553s`，**仅是历史对照投影，不是两次旧版实跑，更不是本次 L3 加速**。该 profiler 衡量同项目 0.4 原价、两次 0.6 候选；不能用作不同项目或价格的财务复用许可证。

## 3. 按风险排序的最小 L3 自身优化候选（**待单独授权实施**）

1. **第一优先：消除 `npv_case` 跨两个模块的重复准备。** `test_phase3e_terminal_npv.py:26-31` 构建一套 Phase2→D3→3B 案例并预跑 0.6/0.8 两个候选；`test_phase3e_break_even_project_npv.py:7,16,66` 通过导入同名 module fixture 又重新准备相同一套。可将该**同一输入身份**的准备提升为共享、受控的 session fixture，两个消费者仍用各自专属输出目录、每次按来源/模型/方法/D3/3B/终期证据哈希复核，必要时用私有快照而非共享可写对象。保留项目 NPV 公开入口的**独立原始＋候选完整重算**及 `(replay=1,3C=2,3D=2,3E=2)` 断言；不能把已有财务结果塞进公开入口或用相同数值但不同来源的项目偷换。预计可免**一套重复准备及两次预备候选**，但**可省秒数尚未实测**，复制/验签成本也可能抵消收益。直接仅改装饰器 `scope="session"` 不保证跨模块共享，须在受控 fixture 定义处设计一次性的只读共享，并保留模块私有运行命名。
2. **第二优先：财务准备链的重复 0.6 原价重放。** `test_phase3e_financial_candidate_replay.py:173-194` 与 `test_phase3e_terminal_binding.py:9,76-87` 各建 `financial_case` 并执行 `financial-first`。只有在确认同项目 ID、经济来源、有效定义、方法 hash、原价、D3 内容和 3B hash 均逐项一致，且输出目录隔离之后，才考虑复用**不可变物理或原始准备输入**；现有相同 run_name 会导致共享目录冲突。**绝不复用不同项目或不同候选电价的 3C/3D/3E 财务结果。**这项也仅有静态重复数量，无可引用的 L3 节省时间。
3. **保留独立性，不优先改动：** `test_phase3e_break_even_project_session.py:24-52` 使用另一 `project_id` 和 `180000 元` OPEX，评估 `0/2/4567÷7300` 并篡改 sidecar 检查缓存失效；不得共享其他项目的原始 3D/3E 或缓存。`test_phase3e_candidate_replay.py:29-83` 的物理资源/原价案例与上述财务案例契约不同；不能凭资源行相同就跨项目拷贝整个 D3 bundle（其 hash 绑定 base export）。`test_energy_generation_capacity.py:25-75,86-125` 运行独立物理参考与 API/CLI 双入口，其 2678.712s 不属于前述六模块的财务候选浪费；先做单独 profiler，不以删独立参考、CLI 或降低物理容量换加速。

**复用安全条件：**任何共享快照仅限本次 pytest 进程和匹配身份（project/type、Phase2 导出/来源、D2 方法、D3 原始数据内容、3B 生成结果、source bytes、有效定义/执行条件）。共享前后验证不可变字节及边界，私有候选目录和生成结果，失配即拒绝而不是重新签一个污染的 hash。不得 hardlink/junction 同一可写测试目录；篡改、路径遍历、来源漂移、无效原价、独立产线测试必须保留独立根，不能因共享 fixture 绕过入口门禁或隐藏失败/跳过。会话内部已证明的原价只读复用边界不扩大为跨项目缓存。

## 4. 实施与计量的停机条件

本轮**只提出** fixture 方案，不修改任何 `tests/solar-pv`、`conftest.py` 或生产计算：当前还在执行先前已启动的 P2-5 L3，修改它的受控源码/测试/配置会使该回执失效；也没有授权为省时改写测试语义。若另行批准测试夹具优化，应先为拟共享 fixture 留下明确身份与隔离审查，在同一环境对**相关两个模块**做优化前后专项计时，记录每次 Phase2/D3/3B/3C/3D/3E 真实调用次数、结果 hash、JUnit node ID/参数、通过/失败/跳过、运行目录和安全反例。开发时运行 fast/契约及受影响 E2E；**本轮不为验证编排再启动完整 L3**。预计消除的操作数（上节）和专项目标时间属于**假设**，在前后实测之前不宣布 L3 缩短了多少秒/百分比；下一次重大集成或发布候选 L3 才检验全量真实收益和未被干扰的参数覆盖。

当前已运行中的 P2-5 L3 与本策略相互隔离：仅把本报告和热点 JSON 写在不属于该运行可执行身份清单的 `reports/solar-pv/`；未改 `services/`、`tests/`、`tooling/`、`docs/solar-pv/`、`products/` 或用户六份既有差异文件，未另启全量回归，也不在该回执完成前制造新 HEAD。**本轮无已实现性能优化及对应专项实测，不作性能 commit；**本策略可供后续子阶段按需审查，不 push、部署或发布。
