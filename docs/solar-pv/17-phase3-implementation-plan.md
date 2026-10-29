# Phase 3 确定性工程与财务引擎实施计划

> 使用executing-plans / test-driven-development / verification-before-completion。用户已授权Phase3A—3G、真实数值测试及各子阶段本地提交；不进入Phase4—8。本计划不代表计算已实现。2026-10-29用户已正式批准18号文件D1/D2/D3推荐方案，同范围不再重复请示，进入3A实施。详见19-phase3-approved-implementation-contract.md；新实质性冲突仍需另行审批。

**Goal:** 同仓库既有solar-pv-engine内实现和专业验收P0屋顶/地面两套独立计算链、Phase3适用公式、完整现金流/指标/重算及唯一结果JSON；交付两个实际运行SYNTHETIC案例，真实发布门禁仍分离。

**Architecture:** 保留Phase2字段/信封/导出与验证链；新增计算层只使用经验证的输入导出。原89公式和281域ID是唯一字典，索引/求根变量不造field_id。共用有量纲核验的原子算法、成本/财务账簿及图；industrial_rooftop和utility_scale_ground独立编排/工程投资/结算约束。新增版本化执行/结果契约，不能复制第二个产品工厂或原始输入目录。

**Tech Stack:** 既有Python >=3.12,<3.15/jsonschema/Decimal/Fraction；任何数值库待方法选择后只在本包声明、隔离环境安装。输入与货币不经float丢精度；工程float方法若需采用，明确误差、收敛与适用域。不修改旧产品依赖、源码、测试、catalog、许可或归档。

**Spec:** 16-phase3-user-task.md原文/manifest；00-original-user-baseline.md、03输入、05公式/扩展/绑定、07分类、08矩阵/验收、10四文件、11路线、12canonical、14/15架构接口。原始任务1003行已归档；以实际文件为准，不因压缩删减。

## 0. 已实核与方法决策入口

- 2026-10-29实际main/clean/HEAD=`6c7081ba32959c3b633f452e43a8826740e79158`；0/1/2完整提交链已读。
- 启动快照：437跟踪文件+72 dist文件，仓库外无.git副本；288保护文件变化0。initial-tracked-hashes在scratch保存，子阶段/最终重新比较。
- 真实启动回归：Phase2 3014 passed/0 failed/5 skipped；旧产品145/0/5，含36项Expert测试；文档20163/20163 PASS。symlink环境skip不计PASS，日志在reports/solar-pv/phase3-startup-*。
- 依据本轮任务与冻结路线，建议89条库存中的82条列本阶段，7条storage扩展明确Phase8；原主表77条没有implementation_stage字面字段，不冒称逐条原有阶段声明。全部保留，启动库存NOT_IMPLEMENTED/NOT_TESTED、executor=null，不能冒充公式通过。
- 需决策D1：按18-phase3-errata-proposals.json所列6项实际矛盾作受控版本化勘误，不改ID/方程/业务意图；保留原始快照，同步有效定义、受影响锁/版本/迁移与回归，不在执行器暗藏相反解释。
- 需决策D2：引入单独版本、严格校验且带来源的计算方法/假设配置（非第二套原始字段），补温度子模型/参数、现金收付及税/债务/股东分配规则和求根控制。469字段和281域含义不改，不把自由文本/应付值猜成数值/已付值。缺配置明确BLOCKED，不补0。
- 需决策D3：全年高粒度输入/结果的显式资源预算与流式规范化/哈希。实测最简8760行负荷（4原子信封/行）数组值36,319,951字节，已超过现32MiB=33,554,432上限，尚不含project/source_snapshot重复。不能静默提全局上限或假造小时曲线；建议保留默认限制，新增显式授权的计算预算和受限流式路径，不删除长期8760/15分钟要求。
- 结果名称建议采用本轮给出的solar-pv-calculation-result/1.0.0；12号契约未固定旧版本字面量，须保留全部必需根/指标/哈希字段，不能因此再建冲突结果结构。
- 温度研究仅访问公开方法文档，不取真实站址/电价。Sandia将模块温度与电池温度分开，系数依构造/安装，不能抄代表值为全项目默认；来源访问与摘要在phase3-method-access.json。具体启用模型须审批/参数充分后另专项验证。

## 1. 通用运行契约（拟新增，不是已有API）

1. 输入入口消费既有solar-pv-input-export/1.0.0。调用ProjectData.from_dict、validate_project、validate_category并复核完整导出：schema/基线、pv_type/scenario_config、normalized_inputs、source_snapshot_id/input_hash与重新export一致；不仅读可篡改摘要。
2. 每个计算节点声明冻结formula_id/输入域ID、实际源field_id/实例/单位/状态、输出边界/时期、方法版本和前置节点。数据缺失/冲突、未批准方法、不适用与未实现分离。没有通用except→0。
3. 每项物理/财务数值必须来自已登记输入、带来源明确假设、已核常数或确定性上游。模型控制/显式假设必须有正式Schema，待D1批准；不能偷塞进组件型号、协议引用等文本字段。
4. 原子公式按281域ID取值，索引集合独立传递；工程/会计period及boundary_id显式，不假设年度总量可直接变8760。
5. 公式产品状态只能在真实专项测试与证据落盘后IMPLEMENTED_TESTED；当前项目NOT_APPLICABLE不升级产品实现。运行缺口另返回BLOCKED_MISSING_INPUT/BLOCKED_METHOD_REVIEW；未实现为NOT_IMPLEMENTED。
6. 结果保留12号契约全部根及metric记录，run_id/created_at独立于可复现result_hash；源/输入/方法/情景更改真实重算，不沿用旧指标。

## 2. 精度与错误规范（3A须进一步冻结）

- 所有输入先按Phase2严格JSON/Decimal读取，bool/字符串不得伪作数字，拒绝NaN/Inf。不以二进制float重新解释原始报价。
- 财务优先Decimal本地context：根据输入有效位、周期和guard digits设精度，不无声明截断高精度输入；中间不保留两位。必须输出precision/rounding/tolerance记录。
- 求根需要明确经济域、完整性/多根检测、残差、收敛、次数和资源上限。无根/多根/不收敛/零多项式分别返回原因，不取有利根。
- 工程浮点若采用：每模型独立abs/rel容差和稳定性校核。最终展示舍入与引擎原值分开，不能修改结果迎合目标。
- 投资/寿命/容量非法按冻结字段拒绝；负电价不无条件截0；无债务DSCR为不适用，零分母与零电量LCOE为非数值状态。

## Phase 3A：计算架构/映射/结果契约

拟新增：计算公共类型、输入导出完整性验证、precision/errors、execution_registry、result_contract及schemas/calculation-result.schema.json；不提前登记空壳执行器为成功。

- [x] 完成两路只读审计并由主任务复核差异，保存18-phase3-preimplementation-review.md；D1—D3已于2026-10-29获用户正式批准，授权与并行接口记录见19号文档。
- [x] 逐89公式保存完整方法/符号/单位/源/条件/前后依赖、拟模块、82本阶段/7后续及真实状态；定义执行登记和测试证据协议。当前有效映射见reports/solar-pv/phase3a-effective-execution-mapping.json；注册不等数值实现。
- [x] 先写RED：输入hash/snapshot/scenario/基线/字段/状态篡改拒绝；结果根和metric类型；JSON往返/未来版本拒绝；run/time不影响result_hash，业务变化必改变hash。追加独立审阅4项回归及Decimal整数负零RED→GREEN，并由最终源码全量验收覆盖。
- [x] 实现有效输入与结果Schema/验证/hash，明确BLOCKED结果不伪造指标，保留89公式真实状态。架构和边界见20-phase3-calculation-architecture.md。
- [x] 编译33个生产模块、完整最终源码3277/0/6、旧回归145/0/5通过。用户确认4个旧文件来自其他任务并批准隔离快照验收及仅提交光伏；隔离快照288保护文件哈希未变、基线复跑exit0，4处明确排除且不回滚。报告见phase3a-review-and-acceptance.md及phase3a-isolated-acceptance.json；准确提交SHA由Git读回。

## Phase 3B：工程与发电

**2026-10-29正式数值验收：PHASE3B_ENERGY_ENGINE_PASS。** v3完整光伏3506/0/6，旧产品含Expert145/0/5；27条公式、两类1MWp/25年SYNTHETIC案例及8760/8784/35040/35136完整计算、跨年DST/净UTC偏移均通过。报告见reports/solar-pv/phase3b-review-and-acceptance.md；4个用户文件不动，隔离快照保护PASS而实时工作区4处授权差异不改称clean。仅能源通过，3C未启动，本轮验收后停止。

拟模块：capacity、solar_resource、losses、energy_yield；共用原子物理算法，分类边界分别调用。

- [x] 先RED独立手算：组件Wp→kWp×块数、每台逆变器转换/限幅后求和、容配比/变压器有功上限、面积排除，既有设计目标不覆盖计算值。
- [x] POA时序积分与明确月度POA输入，拒绝GHI当POA；月合年/年合生命周期、实际时长/闰年/重复缺口。
- [x] 严格损失边界台账，已含PR/温度/限幅/可用率/初始衰减不可重复；顺序、物理接口和上游已扣项独立测试。
- [x] 已批准温度模型+设备参数才允许ambient→cell；没有则方法阻断，不复制ambient。首年初始衰减与后续/分段/更换恢复分别建模。
- [x] 逐公式正常/边界/异常/单位/不适用/缺数及独立参考；编译、回归、保护审查后本地commit。准确最后SHA由同批次Git回执及完成消息记录，不在提交生成前虚构。

## Phase 3C：消纳与收入

拟模块：consumption、tariffs、revenue；industrial_rooftop与utility_scale_ground独立路由。

- [ ] RED时间对齐：同tz/起止/区间长，功率转能量仅一次；缺时段不插0，不平均月度造小时。
- [ ] min自用、余电/上限/弃光和能量恒等式；无时序真实自用率未知，典型曲线须明确假设及映射方法。
- [ ] 单一/分时/合同/PPA折扣/市场序列、计量边界、生效区间/币种/价年/税含；交易及不可避免费项不重复。
- [ ] 地面全售电无屋顶负荷/租赁自用收入；并网限制按时长转换，未确定接入保持条件情景。
- [ ] 两类独立数值/负价/负荷边界测试、回归/审查/本地commit。

## Phase 3D：投资/运营/折旧/税/融资

拟模块：capex、opex、depreciation、tax、financing、accounting_ledger。

- [ ] RED数量×单价与显式报价/定额、互斥分项/总计/占比/单位投资；不同价年/税含拒绝相加，报价与预算分离。
- [ ] OPEX逐年项/增长、更新资本支出/停机/残值；替换不重复放运维和CAPEX。
- [ ] 直线折旧、投运时点/部分年/处置/残值与资产账面余额；非现金折旧不二扣现金。
- [ ] 明确税制/亏损结转/所得税权责到付现、VAT/附加税及项目/权益税基；无依据阻断，不把税率当完整税模型。
- [ ] 贷款0息、等本/年金/到期/自定义、建设期利息/资本化/未付、本金/费用/合同年分数；应付/已付分别建账，不以同字段冒充。
- [ ] 独立小额手算+余额/守恒/税前后边界测试、回归保护审查、本地commit。

## Phase 3E：现金流与财务指标

拟模块：cashflow、financial_metrics、root_finding。

- [ ] 明确建设/投产/运营期、年0与实际现金日期，项目不混债务、权益区分可分配现金和股东投入/分红/退出。
- [ ] NPV/dated NPV、名实折现一致、年度/累计/最差年、静态动态回收及起点；期内未回收不造数。
- [ ] IRR所有有效候选及重复根/无根/负收益率/全零退化/不收敛；不靠单次Newton或一个变号区间冒充完整根集。
- [ ] LCOE交付边界/零电量、CFADS/应还DS/DSCR、盈亏电价的搜索域和全链重算；缺配置不默认阈值。
- [ ] 两种不同独立核验：小额手算/有出处参考与另算法/数值不变量；测试不调用生产实现生成expected。
- [ ] 明确可手算参考：NPV单年-100/+110@10%=0，IRR多根-100/+230/-132应枚举10%/20%，零息本金、折旧/残值、LCOE按同边界折现；这些是待真实执行的参考，不是已通过。
- [ ] 全边界测试/回归/保护审查后本地commit。

## Phase 3F：多方案与敏感性

拟模块：scenario_runner、sensitivity、calculation_graph。

- [ ] 基准/悲观/乐观配置均显式，扰动幅度不固定默认；8类参数全部覆盖：投资/电量/价格/自用/弃光/运维/贷款率/折现率。
- [ ] 数组字段按原field_id+实际row_id选取，输入量与模型控制区分；原始项目/候选不原地修改。
- [ ] 扰动在clone输入和经验证模型配置上生效，重新hash/新run，按依赖重算收入/税/现金流/IRR/NPV，不乘最终指标系数。
- [ ] 相关性矛盾/超范围/错类拒绝；负价性质用正确符号前提，不虚构概率。
- [ ] 比较边界一致与独立重算等价测试、回归/审查/commit。

## Phase 3G：完整验收与停止

- [ ] 分别真实运行完整SYNTHETIC工商业/地面项目并落可复核输入/结果JSON；逐年现金流、NPV/IRR/回收期/LCOE/情景真实值来自程序，不手写“期望输出”充数。
- [ ] 逐82适用公式实际执行/专项分支证据，7后续保留NOT_IMPLEMENTED；项目不适用和产品实现分开，方法缺口不能藏在不适用中。
- [ ] 输入→公式→中间→最终→章节/sheet可遍历，价格修改重算、结果hash排除run/time、保留源快照和公式版本。
- [ ] Phase2完整回归+旧产品含Expert回归在隔离副本执行；不删除慢用例/修改旧断言。编译/CLI/基线/保护/凭据/差异检查留真实证据。
- [ ] 只升级真正数值验收闭合的矩阵记录，18章/29sheet/四文件/真实数据/平台仍未通过。
- [ ] 写phase3-review-and-acceptance.md，含起止HEAD/所有SHA、公式真实统计、两案例数值/完整假设、未关问题/Phase4接口；核心正确性缺口则PARTIAL/BLOCKED，不能宣称PHASE3_CALCULATION_ENGINE_PASS。
- [ ] 本地commit并读回SHA/clean；不push，立即停止，不进入Phase4。

## 当前状态

Phase3A基础契约按用户明确授权的已验证隔离快照本地验收通过：final3完整最终源码3277 passed/0 failed/6 skipped、旧回归145/0/5、33个生产模块编译及实际wheel源码一致，独立审阅5项关闭。复核源码无漂移、隔离快照288保护文件哈希不变且基线exit0。实时工作区4个旧文件已由用户确认来自其他任务，本次仅提交光伏、明确排除4处且不回滚；不把实时工作区保护失败改称PASS。授权及复核见reports/solar-pv/phase3a-isolated-acceptance.json与验收报告。3B仍仅21号只读准备，未新增数学实现；仍为0条公式数值验收、两完整项目未完成，四文件/真实项目/平台不提前PASS。
