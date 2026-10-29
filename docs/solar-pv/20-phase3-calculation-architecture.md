# Phase 3A 计算基础架构与有效版本

本文件解释已批准D1/D2/D3的生产接口，不是发电、现金流或报告数值验收报告。Phase3A按用户明确批准的已验证隔离快照本地验收通过，仅提交光伏，明确排除4个用户其他任务文件；实时工作区保护失败不改称PASS。见reports/solar-pv/phase3a-review-and-acceptance.md及phase3a-isolated-acceptance.json。Phase3B—3G未完成。原始冻结文件、469个输入字段、281个公式域和89条公式全部保留。

## 1. 单一基线与六项正式勘误

原始12份文件及`baseline-lock.json`不修改。`Catalog.frozen_formulas/frozen_bindings`是原始版，`Catalog.formulas/bindings`是同一目录的有效定义。有效版本为`solar-pv-formula-definitions/1.0.1`，有效身份摘要为`617a2e9d314c095bd2ec893939c930a2323be6fd7805da12bf6d6fdd70274808`。

`definition-errata.json`逐项记录E01—E06的对象、路径、原值、新值、理由及批准引用；`definition-lock.json`固定基线、原始/有效定义、输入Schema和勘误摘要；`definition_versions.py`内的审阅锁摘要是信任锚。不能重算任意文件内的锁就把未经批准的修改变成有效版本。6项涉及7处元数据路径，不改变数学表达式。

| 项目 | 内容 | 不代表 |
|---|---|---|
| E01/E02 | 净可利用面积、CAPEX分项计算金额的符号角色由输入改输出 | 面积/造价数值已经校核 |
| E03 | 名实折现率根单位及量纲解释与年度有效比率一致 | 折现率已适用于真实项目 |
| E04/E05 | 能量汇总边界、盈亏电价求根符号解释 | 发电/求根算法已经实现 |
| E06 | 能量守恒残差支持血缘改为可达工程/用电证据 | 整条能量守恒链已经通过 |

`definition_compatibility(catalog, version, definition_hash=None)`明确区分：原版1.0.0仅输入兼容，旧计算结果必须显式重算；当前版必须精确匹配版本/hash。未知版本、篡改或漂移拒绝。旧输入/旧结果/hash不被原地改写。所有新计算消费者使用`catalog.definition_identity()`复验当前有效内容，而不是只相信可变属性中的摘要字符串。

## 2. 输入重验与复合身份

`calculation.input_contract.validate_export(exported, catalog)`是小输入计算入口：严格检验Phase2版本、ProjectData形状、分类、完整原子/候选来源、再生成全部导出投影并逐字节比较。兼容producer0.2.0/0.3.0，输入和导出Schema仍分别为`solar-pv-project/1.0.0`与`solar-pv-input-export/1.0.0`。

旧source snapshot的records数组顺序是身份的一部分。canonical JSON排序对象键后，必须从原records数组恢复根与嵌套字段的原遍历顺序，再完整重验；不能改变原input_hash/source_snapshot_id来掩盖往返不一致。

`calculation_identity(validated, methods, catalog, datasets=None, scenario=None)`重新验证可变包装对象、方法Schema及有效定义。旧Phase2的两个身份保留为独立成员；新业务身份同时包含：

- 原Phase2 input/source身份；
- 当前有效公式定义版本及hash；
- 完整方法配置、来源、状态和hash；
- 已验证bundle的layout-independent content hash、原header、原子数组摘要、期间/单位元数据；
- 显式scenario身份。

`datasets`只能是`read_bundle`产生的`TimeSeriesBundle`，不能直接传自称已验证的任意摘要字典。计算身份发布前完整消费并重验各数据集迭代器；关闭/改变的bundle拒绝。块文件名、chunk大小、处理耗时、工作集和私有绝对路径不进入业务身份。复合source snapshot及其digest可复核，不能覆盖旧源快照。

## 3. D2方法配置

独立版本`solar-pv-method-config/1.0.0`，由`method_schema()`及分发的同源JSON Schema严格校验。目前67个受控项，覆盖精度、期间/温度/STC、能量/损耗/衰减、更新、税费/收付、债务/股东分配、IRR、盈亏电价和情景控制。合法的部分配置不代表任何计算分支资料齐备；`MethodConfig.require(id)`在缺失或未审时返回`BLOCKED_METHOD_REVIEW`异常，不生成数值默认。

每项包含类型、单位、中英文含义、版本、适用分类、边界、来源ID/引用、来源类别、证据状态、许可状态及核验人。SYNTHETIC只能是明确ASSUMED，不得标记VERIFIED或进入真实项目默认。保留原始资产、损耗、衰减、价格、利率等字段；方法选择不得覆盖原输入证据，自由文本与受控选择的映射及冲突仍须在实际计算分支显式核查。

新方法/结果Python API只接受Decimal或整数数值；二进制float明确拒绝，JSON数值使用旧严格解码器的Decimal路径。这避免科学计数法float在JSON往返后改变hash。另明确拒绝会编码为整数token `-0`的Decimal负零：旧解码器将该token读成整数0，不能稳定保留身份。`-0.0`和`-0E+3`等能够稳定往返的十进制token保留。该约束不改Phase2旧序列化默认，也不把已有来源或金额静默转换后伪称原身份不变。

未来3B—3G必须逐分支接线：不能因配置Schema存在就宣称温度模型/税制/现金支付/债务账簿已实现，不能把应付等同已付，不能以缺失金额补零。来源不明确的真实税费/融资方法保持阻断。原始现金流时点及方法选择、折旧方法和资产合同之间的兼容必须明确核查，不能建立互相冲突的第二套参数体系。

## 4. D3有界时序

格式`solar-pv-timeseries-bundle/1.0.0`，保留原32MiB默认接口。API为`BundleBudget`、`write_bundle`、`read_bundle`、`TimeSeriesBundle`和`canonical_array_hash`。资源、负荷及市场电价的原始逐原子信封保留；header只去掉大数组`value/original_value`，不以假空数组表示已知观测。

header要求半开区间start/end、IANA时区、明确粒度及coverage=1。逐原子Schema/来源、时间顺序/连续性/重复/缺口、UTC与站址本地时间/DST、单位、负价规则、实例ID和上游引用均验证。计算消费者仍须再次核查跨资源/负荷/电价时间对齐，不能据单数据集已验证推断彼此对齐。

| 预算 | 代码硬上限 |
|---|---|
| 输入字节 | 2GiB |
| 私有磁盘（含索引预留） | 4GiB |
| 行数 | 1,000,000 |
| 处理墙钟 | 3,600秒 |
| 进程内存 | 2GiB |
| 单行/块/manifest | 1MiB / 4MiB / 8MiB |

以上是可配置预算的硬上限，不是最低资源预留。检查点协作式执行，不能抢占阻塞的调用者迭代器/native调用，返回后超时拒绝；不是OS沙箱。内存检查使用Windows实际工作集及进程生命周期峰值，不能解释为本操作独占分配。

独占创建私有目录，manifest最后原子无覆盖发布。失败不留下看似完整的manifest；拒绝穿越/链接/junction/hardlink及额外/遗漏/改变的块。Windows无symlink权限的跳过单独报告，不能与已执行junction/hardlink混同。

canonical数组摘要流式处理真实`[`、逗号、行token、`]`，与旧digest(list(rows))一致；新格式保留数值token拼写。content hash不依赖chunk布局。8760/35040容量读写/逐原子全验/确定性求和的真实证据单独保留；求和负载不是全年发电或财务数值验收，3B/C/G仍需实际计算。

## 5. 显式图与公式库存

`CalculationNode`记录formula_id、原字段依赖、前置节点、期间、边界、方法选择与方法参数；`CalculationGraph`验证引用/循环、产生确定性拓扑及真实受影响节点集合。不从共享字典中最后覆盖的同名输出推测方法/期间。

`execution_inventory(catalog)`保留89条完整有效公式定义、版本、输入/输出域、符号/单位/条件/来源/章节、拟模块及真实证据状态。当前拟模块分配：engineering27、consumption9、costs20、financial_metrics23、scenarios3、Phase8 storage7。这是实施分工，不是89条已执行。

当前真实数值实现验收为0。82条Phase3适用项仍NOT_IMPLEMENTED；7条储能保留Phase8，不伪装NOT_APPLICABLE或通过。`run_formula`对无内核返回NOT_IMPLEMENTED而不是0。只有已接线内核和匹配当前有效定义的数值证据同时存在才能登记IMPLEMENTED_TESTED；完整专业证据在3B—3G逐条形成。

## 6. 唯一结果与血缘

版本`solar-pv-calculation-result/1.0.0`，保留12号契约全部根字段和metric必需字段。结果hash排除自身、run_id、created_at、artifact_manifest；包含业务、模型、定义、源、方法、边界、场景及结果。新运行不能只换run_id冒充重算。

结果验证检查版本/hash/基线/有效定义、唯一metric ID、公式/原字段/上游metric/domain引用，以及边界、来源、证据、方法参数引用。只要存在CALCULATED指标，包含PARTIAL根状态，也必须核验输入/来源复合身份。无数值状态使用null和明确原因。result sealing只计算摘要，不是数值真实性或专业验收证明。

maturity内嵌Schema禁止本阶段把real_project、four_files或platform升级PASS；构造函数与校验器都不能提前放开门禁。未来renderer统一消费本结果，不能另造数值、补未知数或调整输出迎合目标。本阶段不提供正式DOCX/PDF/XLSX或平台发布能力。

## 7. 验证与后续

所有真实RED/GREEN、容量、内存、吞吐、输入/旧结果兼容、私有wheel安装、保护与回归证据归档到Phase3A验收记录。原审批前startup-state/inventory仍作为历史保留，不静默改写。3A完成只表示基础契约闭环，不表示PHASE3_CALCULATION_ENGINE_PASS。后续按17计划逐阶段实现、验证与本地提交；3G完整验收后停止，不自动进入Phase4。
