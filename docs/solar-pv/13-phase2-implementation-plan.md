# 光伏 Phase 2 输入契约实施计划

> 执行技能：superpowers:executing-plans / test-driven-development / verification-before-completion。用户已批准本阶段范围与新增测试；仅Phase2A—2E，不进入Phase3。所有步骤依赖冻结原文及目录，不重定义字段/公式ID。

**Goal:** 交付可运行且严格可追溯的469字段输入契约、归一化、九类隔离、资料成熟度、受限解析、多轮CLI及89公式输入查询。

**Architecture:** 新增仓库内 `services/solar-pv-engine/` 独立Python包。字段与公式从已冻结docs读取，以版本和SHA-256锁定；JSON Schema 2020-12描述全部字段/逐值信封，Python语义规则负责跨字段、来源、时序与分级。共享数据层不计算光伏/财务结果，分类契约独立。命令行消费JSON，不依赖WorkBuddy和远端服务。

**Tech Stack:** Python >=3.12,<3.15；jsonschema 4.26.0（显式FormatChecker及严格数字类型）；Decimal/Fraction精确单位换算；复用既有wangbin_document_engine的SecurityPolicy/受限转换和openpyxl只读能力；pytest与python-docx沿用现有声明。必要新依赖只在新包声明，在scratch验证环境安装，不改旧产品运行环境。

**Spec:** `00-original-user-baseline.md`、`03-input-fields.json`、`05-formulas.json`及extensions、`05-field-bindings.json`、`07-category-boundaries.md`、用户本轮Phase2任务附件；新附件全文和哈希另归档。

## 全局边界与现状复核

- 2026-10-28实际初始HEAD=`b475c5e5b3d107625acb8e531a623d142060a194`；main；工作区干净。保护288旧文件hash变化0，基线校验19209/19209通过。
- 实际目录469字段（446标量、22对象数组、1标量数组）、89公式、281公式域绑定、九分类与上轮一致，没有字段删减差异。目录不是运行时Schema。
- 旧测试会写reports/dist，只在scratch快照跑旧回归；复制273跟踪文件及72 dist文件共345文件，不复制凭据/.git/用户运行资料。
- document-engine不是报告生成器或OS沙箱；financial_xlsx是拒绝公式的XLSX->CSV工具。读取调用可复用但不执行转换导出，不新增第二套注册/打包工厂。
- 不修改旧源码/旧测试/catalog/metrics/许可证/历史ZIP或wheel。允许修改本项目README与追踪矩阵，只对真正验证的窄范围条款关闭；原文、目录和公式定义保持冻结。
- 数值使用明确单位，拒绝物理边界跨用；无默认站址/电价/容量/年限；未知为null，缺口与冲突不可转0。目标回收期仅约束，用户交互不能写C层结果。
- 九类仅输入契约能力分别验收；所有分类业务计算保持NOT_IMPLEMENTED。资料L2/L3是输入证据评估，不表示四文件/投资建议/平台门禁通过。
- 完整信封保存原始/规范值、原始/目标单位、U/D/C/AI及六类来源、证据/适用期/许可/复核与C血缘。UNKNOWN可序列化；VERIFIED必须有证据及复核，不自动核实用户陈述。

## 数据接口约定

- `Catalog(baseline_dir=None)`：锁定并读取冻结目录；`fields`按稳定field_id查询，`metadata(field_id)`给出15类元数据及公式映射，`project_schema()`返回完整Schema。
- `ProjectData.new(project_id,pv_type,catalog)` / `from_dict(data,catalog)` / `to_dict()`：版本化项目，`values`仅放非repeat_group字段，包含所有允许的字段信封。对象数组为`value=[{row_id,fields:{完整子field_id:信封}}]`；标量数组逐元素信封，空数组与null有不同含义。顶层仅允许契约属性。
- `make_record(catalog,field_id,value,source_kind,...)->dict` / `normalize_record(...)`：保留original_value/original_unit；`value/unit`为规范结果。字符串不能隐式转数值；CLI/解析器仅在显式数值语法与单位下做有记录的转换。
- `validate_project(project,catalog)->list[Issue]`：不丢弃原数据；严格类型/范围/元数据/单位/数组/关联/时间/分类校验；Issue只给code、field_id、实例和原因，不输出敏感原文。
- `evaluate_completeness(project,catalog)->dict`：逐字段及证据轴判定，含L1/L2/L3/未满足L1、已具备/缺失/冲突/假设/条件未知/下一问与能否进入计算；不使用填表百分比。
- `parse_attachment(path,input_root,...)->dict`：授权目录、受限稳定快照、真格式/活动内容拒绝；输出脱敏attachment_id/hash、带可靠定位的提取片段和候选，不自动覆盖/核实。扫描/图片无文本为NEEDS_OCR或PARTIAL，不等于无数据。
- `IntakeSession`增量接受用户来源候选，按submission_id及摘要幂等、修改保留旧候选及理由、冲突显式确认；每轮最多5个按阻断排序的问题；项目规范JSON可供Phase3输入。
- `FormulaBindings.describe(formula_id,project=None)`：89公式、每符号/下标/类型/单位/来源/条件/缺口；中间账簿明确NOT_COMPUTED，不能用支持输入可得推断公式已能执行。

## Phase 2A：基线、结构及Schema

文件：新增本计划、任务原文归档/manifest、`services/solar-pv-engine/pyproject.toml`、`src/wangbin_solar_pv/{__init__,errors,serialization,catalog,schemas,models}.py`、`baseline-lock.json`、`tests/solar-pv/conftest.py`和`test_catalog_schema.py`。

- [ ] 保存原文/初始快照和保护证据；记录已有组件调用链与复用限制。
- [ ] 先写覆盖全部469字段、22对象数组/标量数组、拒绝未知字段/重复JSON键/未来版本、序列化精度与目录漂移的测试，实际观察RED。
- [ ] 实现有版本与hash引用的目录、完整Schema和可序列化项目模型；不执行公式。
- [ ] 执行上述测试、静态编译、diff/敏感模式/保护检查；只暂存本阶段文件本地提交。

## Phase 2B：值、来源及归一化

文件：新增`units.py`、`provenance.py`、`validation.py`及对应`tests/solar-pv/test_units.py`、`test_provenance_validation.py`。

- [ ] 单位测试先RED：每类正确、逆向、边界/异常，DC/AC/功率电量隔离，金额/价格年基准/含税不可直接合并，摄氏/K/风速、日期/时刻/时区/坐标、非有限与精度。
- [ ] 采用显式单位表与精确有理因子，不能精确十进制表示的结果返回明确精度/舍入政策或拒绝，不静默截断；原始数值保留。
- [ ] 信封来源六类与U/D/C/AI映射，未知/假设/VERIFIED边界及逐原子血缘；capex计算金额必须引用数量、单价、公式版本和run，真实报价不被替换。
- [ ] 校验数组行ID、task依赖/循环、合法日内时间和分段/数值范围；验证后审查并本地提交。

## Phase 2C：分类与成熟度

文件：新增`categories.py`、九类`scenarios/<pv_type>/contract.json`、`completeness.py`、条件规则配置与`tests/solar-pv/test_categories_completeness.py`。

- [ ] 先写屋顶/地面双向拒绝、七类型识别、storage非递归基座、条件为UNKNOWN不能当false、L1/L2/L3正反例。
- [ ] 从冻结required_level与IN-C01..13生成适用义务；子字段仅在父数组适用/存在时约束。明确无债不索要债务资料，纯售电不索要负荷，未知容量可继续收集但不造结果。
- [ ] 对工程/权属/资源/商业/财务/追溯轴分别评估，等级取最低；关键未知/冲突阻止升级。输入成熟度不检查尚未实现的文件生成来制造循环依赖，而单独报告后续输出门禁。
- [ ] 验证后审查并本地提交。

## Phase 2D：解析与多轮收集

文件：新增`parsers.py`/解析安全辅助、`intake.py`、`cli.py`、`__main__.py`、仓库直跑入口、六格式和CLI测试。

- [ ] 先写六格式真实虚构文档、单元格/页/文本定位、无OCR/复杂内容降级、重复提交/修改/冲突确认测试。
- [ ] 受限读取CSV/TXT/MD；DOCX/XLSX在同一稳定快照上检查宏/外链/嵌入和XML实体，拒绝公式不执行。PDF既有解析能力提供不了页码时明确UNKNOWN，不猜页码。
- [ ] 路径越界、符号/硬链接、ZIP压缩炸弹、重复成员、异常编码、超大输入、活动内容和超时测试；Windows硬资源隔离仍未解决，公开不可信服务保持阻断。
- [ ] CLI JSON命令覆盖创建/补充/修订/确认/状态/导出与附件候选，不作远端网络调用；真实命令和多轮输出留脱敏证据；验证后本地提交。

## Phase 2E：绑定、全验收与停止

文件：新增`formula_bindings.py`与89公式查询测试；更新`08-requirement-traceability.csv`、README，新增`14-phase2-architecture.md`、Phase3接口说明、`reports/solar-pv/phase2-review-and-acceptance.md`、各子阶段/最终日志及机器结果。

- [ ] 所有89公式与281域字段逐条查询检查；区分输入、常量、计算账簿和输出；缺失变量准确列出，中间状态仍NOT_COMPUTED。
- [ ] 执行A—N测试组，独立检查边界/负向/隐私/兼容性，不以19209文档检查冒充功能测试。
- [ ] 在scratch快照用已安装历史CLI的独立解释器运行完整旧回归；复算所有288保护文件及全部初始跟踪文件，只有本阶段允许docs文件可变化。
- [ ] 更新真正闭合的输入契约矩阵记录；公式数值/分类E2E/四文件/真实数据/平台全部保持原未通过状态。重跑只读基线检查及预期BLOCKED发布检查。
- [ ] 形成实际计数/命令/JUnit/源码hash/提交记录的独立验收报告，审查后本地提交读回SHA和状态；不push；停止Phase2。

## 文档依据（工具/格式，不是新增站址数据源）

jsonschema官方4.26.0 validate文档、JSON Schema 2020-12 validation规范、Python decimal文档已实际访问；格式校验显式启用，数值与序列化禁止非有限值。仅引用API/格式设计，不引入用户附件上传或新的外部气象/电价抓取。
