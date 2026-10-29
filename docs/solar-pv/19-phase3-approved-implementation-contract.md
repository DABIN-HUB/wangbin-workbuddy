# Phase 3 D1/D2/D3 已批准实施接口

日期2026-10-29。用户在审核17/18号文档后正式批准D1/D2/D3，要求同一范围不重复审批，继续3A—3G；新实质性数学/数据/架构冲突仍先报告。本文件记录具体执行约定，不代表数值验收已通过。

## 授权边界

- D1：6项版本化勘误，原始冻结快照/ID/业务含义/方程保留；有效版本明确，受影响引用/Schema/锁/哈希/兼容/迁移及6组RED→GREEN同步；不得隐藏修正或把勘误当数值PASS。
- D2：独立版本、严格Schema的方法/显式假设配置，每个参数有类型、单位、来源、状态、版本、分类、边界及中英文解释。纳入计算身份/来源/hash；不把缺值填0、应付当已付，不把SYNTHETIC当真实默认，不创建冲突原始字段。
- D3：旧接口32MiB默认保持；独立版本大时序，显式预算/硬上限、原子发布、有界分块/流式校验与canonical hash一致性；8760小时完整计算及35040个15分钟容量/内存/吞吐/边界真实验证，逐原子证据保留。
- 89公式全部跟踪，82本阶段，7储能留Phase8；两类P0独立完整SYNTHETIC案例；旧产品不改、不push/上传/发布/部署，不进Phase4。

## 并行工作边界与固定API（新设计）

### D1：有效定义（同一Catalog，保留原版）

子任务独占`definition_versions.py`、`definition-errata.json`、`definition-lock.json`与6项/兼容测试，可精确修改catalog.py和formula_bindings.py以公开有效定义版本；不能改原始03/05文件、baseline-lock.json、旧测试或其他模块。

- Catalog的fields及baseline_hashes仍代表原469输入与12冻结原文件，保证旧ProjectData与solar-pv-input-export/1.0.0可重验；不静默改用户旧hash。
- Catalog保留frozen_formulas/frozen_bindings；formulas/bindings是统一、明确版本的有效定义，所有执行消费者使用同一有效Catalog，不维护相反数值解释。
- Catalog新增definition_version（建议solar-pv-formula-definitions/1.0.1）、definition_hash及definition_manifest；后两者包括原基线与精确6项批准patch。所有公式查询/执行快照公开该身份。
- `definition_compatibility(catalog, version, definition_hash=None) -> dict`：已知原版仅输入兼容、旧公式结果需重算；当前版本/hash严格匹配，未来/未知或篡改拒绝。不得改旧结果hash宣称迁移成功。
- 如果原输入Schema未因元数据改变而变化，须实际比对说明；新增errata/definition lock自身也有严格Schema/哈希校验。任何Catalog读取不能以文件存在就信任任意patch。

### D3：有界bundle（独立格式，不修改旧序列化默认）

子任务独占`timeseries_bundle.py`/私有辅助及新测试；不要改serialization.py/validation.py/local_files.py/catalog.py或父计算模块。可用现有StrictValidator与validate_record进行严格语义校验；性能确需通用验证器改动先回报父任务，不能偷偷跳过。

固定API：

- `BundleBudget` dataclass：max_input_bytes、max_disk_bytes、max_rows、max_seconds、max_memory_bytes，必须正数且不超过代码硬上限；默认私有预算也受限，不改旧32MiB。
- `write_bundle(path, *, base_export, datasets, catalog, budget, rows_per_chunk=256) -> dict`：datasets为`{field_id: {"header":原来源元数据,"rows":Iterable[完整原始row]}}`。只允许resource.timeseries/load.series/tariff.market_series，row结构仍`{row_id,fields:{完整field_id:原信封}}`；原子信封原样保留，header不能假装空数组事实。base_export由Phase2完整重验，不能替换其中已有的同名数据集。
- `read_bundle(path, *, catalog, budget) -> TimeSeriesBundle`：根/版本/安全路径/文件hash/字节/数量/完整标志验证，失败不发布有效结果。
- `TimeSeriesBundle.base_export`；`.manifest`；`.dataset_ids`；`.rows(field_id)`有界Iterator；`.content_hash`（不依赖分块大小/文件名）；`.stats`；`.close()`及context manager。
- `canonical_array_hash(rows) -> str`：与旧serialization.digest(list(rows))逐字节一致，不把JSONL/块摘要误称原数组摘要；必须小数据独立等价测试。
- schema_version=solar-pv-timeseries-bundle/1.0.0，manifest最后原子发布且不覆盖既有输出。所有相对文件位于manifest同私有目录，拒绝穿越/链接/重复/遗漏/额外未声明块，禁止网络。
- 整个序列强制单调连续、重复/缺口/tz偏移/DST/区间长度/时区、跨资源-负荷起止和粒度对齐在消费端再次核查；按现有单位和字段规则逐原子验证，不能仅check字段存在。
- 附件路径只本地授权目录，错误不泄露商业原值/绝对路径。可用Windows进程工作集实测检查内存预算，资源/墙钟失败明确异常，不宣称修复OS沙箱。
- 独立tests提供8760/35040真实读写/全表验证及简单确定性求和负载，性能指标从实际测量生成；发电/负荷数值集成由3B/C再验。

### 父任务：方法/计算/结果

- 公开项目计算入口只接受经Phase2重新验证的export或已验证bundle及受控方法配置；纯数学内部kernels只消费冻结281域ID。
- 新目录`src/wangbin_solar_pv/calculation/`：common/errors/precision、method_config、input_contract、execution_registry、result_contract，然后按17计划新增工程/消纳/成本/财务/情景模块；不新建产品工厂。
- 新方法配置版本solar-pv-method-config/1.0.0；原输入hash与源快照身份保留，计算复合input_hash显式覆盖原身份、定义版本、方法参数/来源和数据集canonical hash；结果快照解释组合关系，不改写原摘要。
- 原子内核约定`evaluate(formula_id, values, options=None) -> {status, value, reason, details}`，values键为冻结formula_field_id（索引集合可由同域已定义集合输入提供）。status为CALCULATED/NOT_APPLICABLE/UNDEFINED/BLOCKED_MISSING_INPUT/BLOCKED_METHOD_REVIEW；缺值不变0。产品IMPLEMENTED_TESTED由真实测试证据登记，不靠函数存在。
- 结果严格采用12号全部根和metric记录，schema_version=solar-pv-calculation-result/1.0.0；result_hash排除run_id/created_at/artifact_manifest及自身，包含全部数值内容/模型/输入/来源/公式/方法/分类/场景；trace保留指标/时期/边界/源与章节/sheet关联。

## 提交顺序

D1与D3在3A内独立并行开发但不自行stage/commit；父任务统一复核、联合测试/编译/保护/源码扫描后提交3A。3B—3G依次按真实交付提交，不能把准备性文件当计算完成；当前不产生任何伪正式报告。
