# 专业公式注册表（Phase 1 方法冻结）

> 主任务整合：本表77条与`05-formula-extensions.json`/`05-extension-formulas.md`的12条合并为89条注册方法；公式域字段通过`05-field-bindings.json`闭合到03输入、明示定义常量或计算账簿，不再将并行整理时的“待映射”当最终接口。所有数值验收仍PLANNED。光储文字等式、布局、年均和减排等扩展同样逐符号登记；07不得在未注册模型中隐式算数。

- 配套机器文件：`05-formulas.json`；配套术语：`06-glossary-zh-en.md`、`06-glossary.json`。
- 方法版本：`METHOD-CONTRACT-v1`；文档日期：2026-10-28。
- **仅冻结定义、边界、输入输出和后续验证要求；引擎 NOT_IMPLEMENTED，全部公式测试 PLANNED，不宣称数值 PASS。**
- 已通读完整附件（213 行）；`USER-BASELINE §6` 是附件需求引用，不是外部行业标准 source_id。
- `NB/T 32044-2018`、`NB/T 32043-2018` 和适用税制/融资协议的全文条款尚未在本子任务核对，统一标注“待标准全文核对”。不得把推导方法写成已核实标准条文。

## 1. 全局计算与记号契约

1. 每个公式独立记录所有完整变量、上下标含义、集合和范围、单位、边界、假设、优先级、来源、符号化算例、验证方式、test_id、章节和字段。括号是分组/函数调用，逗号是索引分隔，Σ 为有限求和，Π 为有限连乘，argmin 返回所有并列最小值位置。
2. 物理标签 DC/AC、POA、STC、inv 等不是额外相乘字母。kWp 参与数值算术按 kW 数值规范化，但峰值和直流标签必须保留。比率以小数存储，不把百分数展示值直接代入。
3. 年度有效折现率和衰减率是无量纲年度比例；指数是年度步数。合同单利采用年化倒时间率乘合同年分数。名义/实际、税前/税后、含税/不含增值税是独立属性。
4. 基期为财务时点 0，运营年从 1 起；多建设年、部分年度和日期收付不能静默压缩。时间轴同时声明时区、间隔、覆盖、计量点和闰年规则。
5. 关键输入 UNKNOWN/CONFLICT 向结果传播；有依据才可声明 NOT_APPLICABLE。无负荷无法给真实自用率，无并网意见只给条件情景，无税制依据不能冒充确定税后结果。
6. `formula_id` 永久稳定。公式域 `input_field_ids` 通过 `05-field-bindings.json` 显式映射到03输入、定义常量或C层计算账簿；该分层避免把内部状态当成长表单。`CH01`—`CH18` 与细纲统一；机器引用闭合只证明冻结索引完整，不证明运行时数据转换或计算正确。
7. 每条 `sample_case` 都是符号化规格，状态 PLANNED；没有现场数值、虚构工程案例或已通过测试证据。`T-*` 是未来测试 ID，不代表测试已经实现。

## 2. 方法优先级与互斥规则

- 可靠同粒度逐时物理模型优先于年度 PR 简式；资料不足才采用简化法并降低成熟度。不能把累计年量倒生成所谓真实逐时数据。
- 已含损失的模拟输出、PVOUT 与 PR 简式不得叠用。每项损失需登记计入节点、模拟是否包含、证据与适用边界；温度/逆变等已显式计算时不再计入笼统系统损失。
- `F-FIRST-YEAR-ENERGY` 与 `F-INITIAL-DEGRADATION` 对同一输出只允许经方法选择形成无循环链；首年 PR 已含初始衰减时不得再乘初始损失。逐时年度汇总与年度比例衰减是互斥/校核路线，不是让相同电量再缩放一遍。
- 设备与损失顺序：阵列面资源→遮挡/污损/雪有效辐照→温度与组件→失配/直流线→逆变转换与单机限幅→交流线→变压器→送出及站用→明确计量点可用电量→自用/上网/限发。可利用率若已经在时序停机模拟中扣除，不再乘一次。
- 屋顶自持收益与第三方 PPA 收入互斥；第三方不能再取得用电方全部避免购电收益。地面全额售电不复用工商业自用收益；站用电仍独立核算。
- 直接现金收付法与权责发生额加营运资金桥二选一；应收、税、资本应付已经在其他桥计过，不得再以总 ΔNWC 重扣。
- 项目无杠杆流排除借款提款、债务本息及融资费，并使用无杠杆税负；资本金实际流按股东出资、分配和退出，使用融资后税负及合法税盾。建设期资本化利息只做一次现金/非现金桥，不在资产付款与付现利息双扣。
- LCOE 本次冻结的默认节点为项目无杠杆、所得税前、同边界可利用交付电量；含税处理、其他税费和补贴抵减另标。融资后/股权/税后 LCOE 须新建明确方法，不能换标题冒用本节点。
- 法规、合同及正式设备/资源模型的适用定义优先于本方法假设；发生冲突先暂停有关结论、记录 CONFLICT，再升方法版本复审，不静默覆盖。

## 3. 外部核验范围与未决项

实际通过 curl 读取了 PVWatts 官方 `System Losses` HTML 正文，支持“未显式建模损失用复合方式处理、温度及逆变转换不能重复包含”的有限核验。JSON 中保留实际 URL、获取方式、短句证据及许可待审状态。不采纳页面默认损失率、逆变效率或任何站址值。

`web_extract` 因当前检索后端仅支持搜索而失败；另一候选 SAM 页面没有取得正文，不将其登记为已读来源。本文没有声称复现 PVWatts 全模型，也没有将其说明替代中国标准、法定税制或贷款协议。所有派生税费、债务、现金桥为方法约定，必须由适用全文及专业复核确认。

## 4. 最低 16 组覆盖索引

| 附件组 | 方法范围 | 独立 formula_id |
|---|---|---|
| 1 | 装机、容配比及单位边界 | `F-DC-CAPACITY`, `F-AC-CAPACITY`, `F-DC-AC-RATIO`, `F-UNIT-KW-MW`, `F-UNIT-KWH-MWH`, `F-UNIT-IRRADIANCE-W-KW`, `F-UNIT-COST-WP-KWP`, `F-UNIT-DC-CAPACITY`, `F-UNIT-AC-CAPACITY` |
| 2 | 辐照量与首年简式 | `F-POA-IRRADIATION`, `F-FIRST-YEAR-ENERGY` |
| 3 | 逐时损失、发电与汇总 | `F-LOSS-COMPOSITE`, `F-DC-TIME-POWER`, `F-AC-INVERTER-POWER`, `F-AVAILABLE-ENERGY`, `F-ENERGY-AGGREGATION` |
| 4 | 初始及后续/分段衰减 | `F-INITIAL-DEGRADATION`, `F-ANNUAL-DEGRADATION`, `F-PIECEWISE-DEGRADATION` |
| 5 | 等效小时、容量因子与 PR | `F-EQUIVALENT-HOURS`, `F-CAPACITY-FACTOR`, `F-PR-OBSERVED` |
| 6 | 自用、上网、限发与能量平衡 | `F-EXPORT-LIMIT-ENERGY`, `F-SELF-CONSUMPTION`, `F-EXPORTED-ENERGY`, `F-CURTAILED-ENERGY`, `F-ENERGY-BALANCE`, `F-DELIVERED-ENERGY`, `F-SELF-CONSUMPTION-RATIO`, `F-LOAD-COVERAGE-RATIO` |
| 7 | 自持/PPA 收益、税价与收款 | `F-ENERGY-REVENUE`, `F-PPA-REVENUE`, `F-TAX-EXCLUSIVE-AMOUNT`, `F-CASH-RECEIPTS` |
| 8 | 投资、运营费用与计划 | `F-CAPEX-TOTAL`, `F-UNIT-INVESTMENT`, `F-ANNUAL-OPEX`, `F-OPEX-ESCALATION` |
| 9 | 折旧、税务与现金桥 | `F-STRAIGHT-LINE-DEPRECIATION`, `F-ASSET-BOOK-VALUE`, `F-TAXABLE-INCOME-PROJECT`, `F-TAXABLE-INCOME-EQUITY`, `F-INCOME-TAX-ACCRUAL`, `F-TAX-LOSS-BALANCE`, `F-TAX-CASH-BRIDGE`, `F-VAT-CREDIT-BALANCE`, `F-OTHER-CASH-TAXES`, `F-CASH-TAX-TOTAL` |
| 10 | 项目/股权现金流及债务平衡 | `F-PROJECT-CASH-FLOW`, `F-PROJECT-PRETAX-CASH-FLOW`, `F-EQUITY-AVAILABLE-CASH-FLOW`, `F-EQUITY-INVESTOR-CASH-FLOW`, `F-CASH-FUNDING-BALANCE`, `F-DEBT-BALANCE`, `F-DEBT-INTEREST`, `F-INTEREST-BALANCE` |
| 11 | 净现值、日期及折现口径 | `F-NPV`, `F-DATED-NPV`, `F-NOMINAL-REAL-RATE` |
| 12 | 项目与资本金 IRR 根集 | `F-IRR-PROJECT`, `F-IRR-EQUITY` |
| 13 | 静态与动态回收期 | `F-CUMULATIVE-CASH-FLOW`, `F-STATIC-PAYBACK`, `F-DISCOUNTED-CUMULATIVE-CASH`, `F-DYNAMIC-PAYBACK` |
| 14 | 生命周期成本与 LCOE | `F-LIFECYCLE-COST`, `F-LCOE` |
| 15 | CFADS、债务服务与 DSCR | `F-CFADS`, `F-DEBT-SERVICE`, `F-DSCR` |
| 16 | 盈亏平衡、敏感性、风险与对账 | `F-BREAK-EVEN-PRICE`, `F-SINGLE-FACTOR-SENSITIVITY`, `F-SENSITIVITY-ELASTICITY`, `F-SCENARIO-METRIC`, `F-WORST-CASH-YEAR`, `F-CAPEX-PAYMENT-BALANCE`, `F-INVESTMENT-HURDLE-GAP` |

## 5. 损失与财务异常状态冻结

### 5.1 损失台账最低元数据

每个损失项至少记录 `loss_id`、物理段、损失率/时序来源、含否标记、上下游计量点、适用期、设备组、模型版本、与 PR/PVOUT/外部输出的包含关系。遮挡、污损、雪、温度、失配、直流线、逆变转换、单机限幅、交流线、可利用率、变压器、送出和限发不得遗漏。限幅与外部限发分离，站用进口不伪装成负发电量。变压器空载/负载效应不能无条件化为统一比例。

### 5.2 根、回收期与分母异常

| 情况 | 必须输出 | 禁止行为 |
|---|---|---|
| IRR 无符号变化且非全零 | `NO_SIGN_CHANGE` | 虚构收益率 |
| 全零现金流 | `INDETERMINATE` | 任选 0% 作唯一 IRR |
| 指定域内无根 | `NO_ROOT`，附搜索域与完整性说明 | 把局部迭代失败当全域无根 |
| 多个有效实根 | `MULTIPLE_ROOTS`，保留根集 | 任挑有利根 |
| 未收敛或未穷尽域 | `NOT_CONVERGED` / `ROOT_ENUMERATION_INCOMPLETE` | 冒称唯一实根 |
| 评价期累计未负转非负 | `NOT_RECOVERED_WITHIN_HORIZON` / 期内未回收 | 把末年编号当回收期 |
| 无债务 | `NOT_APPLICABLE` | 给 DSCR 0 或无限 |
| 有债务但服务期分母为零 | `ZERO_DEBT_SERVICE` | 强行给 DSCR |
| 折现交付电量为零 | `ZERO_DELIVERY` | 强行给 LCOE |
| 比率基准或参考容量为零 | `UNDEFINED` 或参数错误 | 擅自分母置 1 |

负电价在有证据时允许进入结算；负 CFADS、负收入或负合法 IRR 应如实保留，不以零截断掩盖风险。IRR 的求根域、精度、枚举策略尚需 Phase 3 实现与独立参考验证；本文件没有算法代码或测试实现。

### 5.3 敏感性与情景因素目录

| 因素 | 扰动入口 | 必须随动的内生计算 | 边界 |
|---|---|---|---|
| 投资 | CAPEX 分项/付款计划 | 资本化、税/折旧、融资、现金流 | 不倒改现实报价 |
| 售电/避免购电/PPA 价格 | 对应合法价格序列 | 收入、税、现金流 | 各模式权属隔离 |
| 发电量/资源 | 资源或设备性能的明确情景 | 逐时消纳、限发、收益、税 | 不简单比例修改最终 IRR |
| 设备可利用率 | 停机时序或互斥等效率 | 发电与收入 | 已模拟停机不再扣率 |
| 自用率 | 合理负荷/发电时序情景；无负荷仅显式假设 | 自用/上网/限发、电价加权及现金流 | 自用率是派生量，不能违反能量平衡强改 |
| 限发 | 上网约束/调度情景 | 可交付电量、收入、LCOE | 技术损失与弃光不重叠 |
| 运维 | OPEX 分类计划及合同递增 | 税、CFADS、现金流 | 折旧/资本更换不重计 |
| 利率 | 贷款合同分段利率 | 利息、资本化、税盾、债务/股权流 | 不影响冻结经营参数下的无杠杆项目流 |

悲观/基准/乐观采用完整模型重算，记录全部联合扰动；不得虚构概率。盈亏平衡电价只对指定价格项求根；目标 IRR/回收期只是门槛，不是修改真实资源、成本或收入的理由。

## 6. 独立公式条目

以下条目与 JSON 同一内存源生成。输出及输入字段中的可复用函数模板，必须在正式计算图中绑定到明确口径后才能运行；不得产生循环依赖。

### F-DC-CAPACITY · 直流装机容量

- 英文全称：DC nameplate capacity；首次释义：直流装机容量（DC nameplate capacity）。
- 最低清单组：1；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
P_{DC}=N_{mod}P_{mod}
$$

- 文本式：`P_DC = N_mod × P_mod`
- 输出：`capacity.dc_kwp`；量纲/单位：kWp。
- 输入：`equipment.module_count`, `equipment.module_power_kwp`。
- 章节：`CH01`, `CH06`, `CH07`；未来测试：`T-DC-CAPACITY`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| P_DC | 组件阵列在标准测试条件下的额定直流容量 | kWp | `capacity.dc_kwp` |
| N_mod | 同一规格组件的整数块数 | 块 | `equipment.module_count` |
| P_mod | 该规格单块组件额定峰值功率 | kWp/块 | `equipment.module_power_kwp` |

**下标、上标及集合范围：**

- 下标/范围 `说明`：下标仅是变量名称中给出的物理/会计边界标签；具体含义见本条每一完整符号定义，不是乘法。无迭代索引。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 组件铭牌端，不是逆变器交流输出或并网许可容量。混用组件规格须逐类求和。 输出单位为 kWp；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- P_mod > 0；N_mod 非负整数；额定功率不等于所有时刻实际输出。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第1组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `P_DC = N_mod × P_mod`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 独立人工清单复核；块数整数/负值拒绝、功率单位转换和混合规格聚合用例均 PLANNED。

**逐个下标词素：** DC=直流侧组件额定容量/功率；mod=光伏组件。

**术语键：** `TERM-F-DC-CAPACITY`, `TERM-DC`。

### F-AC-CAPACITY · 逆变器交流额定容量

- 英文全称：AC inverter nameplate capacity；首次释义：逆变器交流额定容量（AC inverter nameplate capacity）。
- 最低清单组：1；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
P_{AC}=\sum_{j\in\mathcal J}P_{inv,j}
$$

- 文本式：`P_AC = Σ(j∈J) P_inv,j`
- 输出：`capacity.ac_kw`；量纲/单位：kWac。
- 输入：`equipment.inverters.rated_ac_kw`, `equipment.inverters.ids`。
- 章节：`CH01`, `CH06`, `CH07`, `CH09`；未来测试：`T-AC-CAPACITY`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| P_AC | 全部逆变器额定有功交流容量之和 | kWac | `capacity.ac_kw` |
| P_inv,j | 第 j 台逆变器额定交流有功功率 | kWac | `equipment.inverters.rated_ac_kw` |
| j | 逆变器序号 | 1 | index_or_constant |
| J | 本方案安装的逆变器有限集合 | 集合 | `equipment.inverters.ids` |

**下标、上标及集合范围：**

- 下标/范围 `j∈J`：j 遍历本方案所有逆变器且只计一次；Σ 全集合求和；inv=逆变器；AC=交流。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 集合/求和或连乘 `j∈J`：j 遍历本方案所有逆变器且只计一次；Σ 全集合求和；inv=逆变器；AC=交流。

**边界与量纲：** 逆变器交流端；变压器 kVA、并网点 kW 和无功约束不能直接等同该值。 输出单位为 kWac；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 逐台设备清单明确；需另外校验出线和变压器容量，不在此推导并网资格。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第1组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `P_AC = Σ(j∈J) P_inv,j`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 逐台求和独立复核，kVA 不经功率因数不得代入；空集合和未知额定值分开处理。

**逐个下标词素：** AC=交流侧额定容量/功率；inv=逆变器设备/转换环节；j=逆变器逐台索引。

**术语键：** `TERM-F-AC-CAPACITY`, `TERM-AC`。

### F-DC-AC-RATIO · 直交流容配比

- 英文全称：DC-to-AC ratio；首次释义：直交流容配比（DC-to-AC ratio）。
- 最低清单组：1；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
R_{DC/AC}=P_{DC}/P_{AC}
$$

- 文本式：`R_DC_AC = P_DC / P_AC`
- 输出：`capacity.dc_ac_ratio`；量纲/单位：1。
- 输入：`capacity.dc_kwp`, `capacity.ac_kw`。
- 章节：`CH01`, `CH06`, `CH07`；未来测试：`T-DC-AC-RATIO`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| R_DC_AC | 直流额定容量除以逆变器交流额定容量 | 1 | `capacity.dc_ac_ratio` |
| P_DC | 标准测试条件组件峰值容量，数值以 kW 表示 | kWp | `capacity.dc_kwp` |
| P_AC | 逆变器额定交流有功容量 | kWac | `capacity.ac_kw` |

**下标、上标及集合范围：**

- 下标/范围 `说明`：下标仅是变量名称中给出的物理/会计边界标签；具体含义见本条每一完整符号定义，不是乘法。无迭代索引。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 比较额定功率数值，保留 DC/AC 标签；不是实时效率，也不是并网容量比。 输出单位为 1；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- P_AC > 0；任何推荐范围不得无来源当统一标准。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第1组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `R_DC_AC = P_DC / P_AC`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 分母零拒绝；交换分子分母不等价，结果与铭牌清单交叉核验。

**逐个下标词素：** DC=直流侧组件额定容量/功率；AC=交流侧额定容量/功率。

**术语键：** `TERM-F-DC-AC-RATIO`, `TERM-DC`, `TERM-AC`。

### F-POA-IRRADIATION · 阵列面辐照量积分

- 英文全称：POA irradiation integration；首次释义：阵列面辐照量积分（POA irradiation integration）。
- 最低清单组：2；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
H_{POA,y}=\sum_{t\in\mathcal T_y}G_{POA,t}\Delta t_t
$$

- 文本式：`H_POA,y = Σ(t∈T_y) G_POA,t × Δt_t`
- 输出：`resource.poa_irradiation_kwh_m2`；量纲/单位：kWh/m²。
- 输入：`resource.poa_irradiance_kw_m2`, `time.interval_hours`, `time.resource_intervals`。
- 章节：`CH05`, `CH08`；未来测试：`T-POA-IRRADIATION`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| H_POA,y | 第 y 年阵列面累计辐照量 | kWh/m² | `resource.poa_irradiation_kwh_m2` |
| G_POA,t | 时段 t 的阵列面平均辐照度，输入需先规范为 kW/m² | kW/m² | `resource.poa_irradiance_kw_m2` |
| Δt_t | 时段 t 实际持续小时数 | h | `time.interval_hours` |
| t | 时间段索引 | 1 | index_or_constant |
| y | 资源年序号，不必等于财务年 | 1 | index_or_constant |
| T_y | 资源年 y 的无重叠完整时间段集合 | 集合 | `time.resource_intervals` |

**下标、上标及集合范围：**

- 下标/范围 `t∈T_y`：Σ 对年 y 的全部时段求和；POA=组件平面；下标 y=资源年，t=时段。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 集合/求和或连乘 `t∈T_y`：Σ 对年 y 的全部时段求和；POA=组件平面；下标 y=资源年，t=时段。

**边界与量纲：** 同一阵列朝向、时间标准、已说明遮挡前后边界；GHI/DNI/DHI 不直接当 POA。 输出单位为 kWh/m²；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- G 是区间均值；瞬时样点须另定积分方法；缺测不自动补零。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第2组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `H_POA,y = Σ(t∈T_y) G_POA,t × Δt_t`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 时长完整性、重复时段/时区/闰年、W 与 kW 换算及辐照度与辐照量混用检查。

**逐个下标词素：** POA=组件阵列平面；y=财务或运营年度索引，必须按本条时间定义区分；t=同一时间粒度的时段索引。

**术语键：** `TERM-F-POA-IRRADIATION`, `TERM-POA`。

### F-FIRST-YEAR-ENERGY · 首年性能比简化发电量

- 英文全称：First-year PR-based energy；首次释义：首年性能比简化发电量（First-year PR-based energy）。
- 最低清单组：2；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
E_1=P_{DC}(H_{POA}/G_{STC})PR
$$

- 文本式：`E_1 = P_DC × (H_POA / G_STC) × PR`
- 输出：`energy.first_year_ac_kwh`；量纲/单位：kWh。
- 输入：`capacity.dc_kwp`, `resource.poa_irradiation_kwh_m2`, `constants.stc_irradiance_kw_m2`, `energy.pr_assumed`。
- 章节：`CH01`, `CH08`；未来测试：`T-FIRST-YEAR-ENERGY`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| E_1 | 首个完整运营年的交流电量 | kWh | `energy.first_year_ac_kwh` |
| P_DC | 组件阵列直流额定容量，以 kW 的数值参与运算 | kWp | `capacity.dc_kwp` |
| H_POA | 同年同阵列面累计辐照量 | kWh/m² | `resource.poa_irradiation_kwh_m2` |
| G_STC | 标准测试条件参考辐照度，固定定义为 1 kW/m² | kW/m² | `constants.stc_irradiance_kw_m2` |
| PR | 与输出计量点、首年初始损失和限发边界一致的性能比 | 1 | `energy.pr_assumed` |

**下标、上标及集合范围：**

- 下标/范围 `说明`：下标仅是变量名称中给出的物理/会计边界标签；具体含义见本条每一完整符号定义，不是乘法。无迭代索引。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** PR 假设法仅用于资料不足的简化估算；明确输出在逆变器端或并网点、限发前或后。 输出单位为 kWh；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 量纲 kW × ((kWh/m²)/(kW/m²)) = kWh；PR 不能重复叠加已包含的损失；首年初始衰减须登记。

**方法优先级：**
1. 可靠且边界清楚的逐时物理模型优先。
2. 仅有年累计辐照量时才采用本简式，降低成熟度；不能用年量倒造逐时真实数据。

**来源：**
- USER-BASELINE §6 第2组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `E_1 = P_DC × (H_POA / G_STC) × PR`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 与独立符号推导核对；PR 损失覆盖集合重复校验；与可靠逐时结果同边界交叉比较。

**逐个下标词素：** 1=首运营年或扰动后情景 1，具体按完整符号区分；DC=直流侧组件额定容量/功率；POA=组件阵列平面；STC=标准测试条件基准。

**术语键：** `TERM-F-FIRST-YEAR-ENERGY`, `TERM-PR`, `TERM-STC`。

### F-LOSS-COMPOSITE · 独立损失复合系数

- 英文全称：Multiplicative loss retention；首次释义：独立损失复合系数（Multiplicative loss retention）。
- 最低清单组：3；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
K_{loss}=\prod_{k\in\mathcal K}(1-l_k)
$$

- 文本式：`K_loss = Π(k∈K) (1 − l_k)`
- 输出：`losses.retention_factor`；量纲/单位：1。
- 输入：`losses.independent_rates`, `losses.active_ids`。
- 章节：`CH07`, `CH08`；未来测试：`T-LOSS-COMPOSITE`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| K_loss | 选定独立损失项的剩余比例 | 1 | `losses.retention_factor` |
| l_k | 第 k 个尚未在其他环节扣除的独立损失率，按小数 | 1 | `losses.independent_rates` |
| k | 损失类型序号 | 1 | index_or_constant |
| K | 实际采用且互斥的损失项有限集合 | 集合 | `losses.active_ids` |

**下标、上标及集合范围：**

- 下标/范围 `k∈K`：Π 对登记的损失集合逐项连乘；loss=剩余系数标签。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 集合/求和或连乘 `k∈K`：Π 对登记的损失集合逐项连乘；loss=剩余系数标签。

**边界与量纲：** 仅用于独立、同一基准边界的比例损失；不能替代遮挡、温度、限幅的逐时耦合模型。 输出单位为 1；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 每项 0≤l_k≤1；须有 included_in_simulation 标识；设备停机由时序模拟则不再乘可利用率。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第3组：方法与防重复扣损约束，具体链条为项目方法约定；待标准全文核对。
- PVWatts System Losses：实际已读正文，仅支持未显式建模损失相乘及温度、逆变不应重复纳入系统损失；不采纳页面默认值；定位及实际 URL 见 JSON 的 source_reference。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `K_loss = Π(k∈K) (1 − l_k)`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 重叠损失拒绝；逐项相乘不得改为求和；全零/全损失符号边界用例。

**逐个下标词素：** loss=独立损失复合剩余系数；k=损失/费用类别或现金事件索引，见本条集合。

**术语键：** `TERM-F-LOSS-COMPOSITE`。

### F-DC-TIME-POWER · 时段直流功率近似

- 英文全称：Time-step DC power approximation；首次释义：时段直流功率近似（Time-step DC power approximation）。
- 最低清单组：3；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
P_{DC,t}=\max[0,P_{DC}(G_{eff,t}/G_{STC})(1+\gamma(T_{cell,t}-T_{STC}))K_{DC,t}]
$$

- 文本式：`P_DC,t = max(0, P_DC × G_eff,t/G_STC × (1 + γ×(T_cell,t−T_STC)) × K_DC,t)`
- 输出：`energy.dc_power_kw`；量纲/单位：kW。
- 输入：`capacity.dc_kwp`, `resource.effective_poa_kw_m2`, `constants.stc_irradiance_kw_m2`, `equipment.power_temperature_coefficient`, `resource.cell_temperature_c`, `constants.stc_cell_temperature_c`, `losses.dc_retention`。
- 章节：`CH07`, `CH08`；未来测试：`T-DC-TIME-POWER`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| P_DC,t | 时段平均直流输出功率 | kW | `energy.dc_power_kw` |
| P_DC | 组件直流额定容量数值 | kWp | `capacity.dc_kwp` |
| G_eff,t | 遮挡、灰尘和雪处理后的有效阵列面辐照度 | kW/m² | `resource.effective_poa_kw_m2` |
| G_STC | 标准参考辐照度 | kW/m² | `constants.stc_irradiance_kw_m2` |
| γ | 组件功率相对温度系数，可为负 | 1/°C | `equipment.power_temperature_coefficient` |
| T_cell,t | 电池片工作温度，不是直接用环境温度 | °C | `resource.cell_temperature_c` |
| T_STC | 标准测试条件电池温度 | °C | `constants.stc_cell_temperature_c` |
| K_DC,t | 尚未计入其他模型的失配和直流线损剩余比例 | 1 | `losses.dc_retention` |

**下标、上标及集合范围：**

- 下标/范围 `t`：与负荷同粒度时段；DC=直流，eff=有效，STC=标准测试，cell=电池片。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 用于明确版本的线性温度近似；不是宣称复现 PVWatts 全算法。 输出单位为 kW；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- γ 需组件依据；组件温度子模型须另行评审；有效辐照度已经扣除的损失不再扣；负温度修正导致不合理输出需标适用域错误而非掩盖。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第3组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `P_DC,t = max(0, P_DC × G_eff,t/G_STC × (1 + γ×(T_cell,t−T_STC)) × K_DC,t)`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 独立温度修正式参考、零辐照边界、℃/K 差值一致、温度系数百分数输入检查。

**逐个下标词素：** DC=直流侧组件额定容量/功率；t=同一时间粒度的时段索引；eff=有效阵列面辐照度；STC=标准测试条件基准；cell=电池片温度。

**术语键：** `TERM-F-DC-TIME-POWER`, `TERM-STC`。

### F-AC-INVERTER-POWER · 逆变转换与限幅

- 英文全称：Inverter conversion and clipping；首次释义：逆变转换与限幅（Inverter conversion and clipping）。
- 最低清单组：3；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
P_{AC,t}=\min[P_{AC},\max(0,\eta_{inv,t}P_{DC,t})]
$$

- 文本式：`P_AC,t = min(P_AC, max(0, η_inv,t × P_DC,t))`
- 输出：`energy.inverter_ac_power_kw`；量纲/单位：kW。
- 输入：`capacity.ac_kw`, `losses.inverter_efficiency`, `energy.dc_power_kw`。
- 章节：`CH07`, `CH08`；未来测试：`T-AC-INVERTER-POWER`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| P_AC,t | 逆变器交流输出平均功率 | kW | `energy.inverter_ac_power_kw` |
| P_AC | 同一逆变器聚合组额定交流有功容量 | kWac | `capacity.ac_kw` |
| η_inv,t | 工况相关转换效率 | 1 | `losses.inverter_efficiency` |
| P_DC,t | 该组时段直流输入功率 | kW | `energy.dc_power_kw` |

**下标、上标及集合范围：**

- 下标/范围 `t`：时段；inv=逆变器，AC=交流，DC=直流。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 每台/同质组先转换限幅再相加；不同设备不得只用总容量掩盖单机限幅。 输出单位为 kW；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 效率 0≤η≤1；时段平均限幅只是近似，不保证捕获区间内尖峰；自耗如需单列不能重复扣。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第3组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `P_AC,t = min(P_AC, max(0, η_inv,t × P_DC,t))`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** AC 不超过额定、转换损失非负；先单机限幅后聚合与简单总限幅差异用例。

**逐个下标词素：** AC=交流侧额定容量/功率；t=同一时间粒度的时段索引；inv=逆变器设备/转换环节；DC=直流侧组件额定容量/功率。

**术语键：** `TERM-F-AC-INVERTER-POWER`。

### F-AVAILABLE-ENERGY · 计量点限发前可用电量

- 英文全称：Pre-curtailment available energy；首次释义：计量点限发前可用电量（Pre-curtailment available energy）。
- 最低清单组：3；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
E_{available,t}=\max[0,(P_{AC,t}K_{AC,t}K_{tr,t}K_{line,t}-P_{aux,t})\Delta t_t A_t]
$$

- 文本式：`E_available,t = max(0, (P_AC,t × K_AC,t × K_tr,t × K_line,t − P_aux,t) × Δt_t × A_t)`
- 输出：`energy.available_kwh`；量纲/单位：kWh/时段。
- 输入：`energy.inverter_ac_power_kw`, `losses.ac_retention`, `losses.transformer_retention`, `losses.export_line_retention`, `energy.auxiliary_kw`, `time.interval_hours`, `losses.availability`。
- 章节：`CH08`, `CH09`, `CH10`；未来测试：`T-AVAILABLE-ENERGY`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| E_available,t | 同一计量点时段内限发前可用交流电量 | kWh/时段 | `energy.available_kwh` |
| P_AC,t | 逆变器端交流功率 | kW | `energy.inverter_ac_power_kw` |
| K_AC,t | 交流线损剩余比例 | 1 | `losses.ac_retention` |
| K_tr,t | 变压器损失剩余比例 | 1 | `losses.transformer_retention` |
| K_line,t | 送出线路损失剩余比例 | 1 | `losses.export_line_retention` |
| P_aux,t | 尚未扣除的站用功率 | kW | `energy.auxiliary_kw` |
| Δt_t | 时段持续小时数 | h | `time.interval_hours` |
| A_t | 未在功率输出中模拟的设备可用状态或等效可用比例 | 1 | `losses.availability` |

**下标、上标及集合范围：**

- 下标/范围 `t`：时段；AC=交流，tr=变压器，line=送出线，aux=站用，available=限发前。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 逆变器→交流线→变压器→送出线→明确计量点，限发另由消纳平衡扣；屋顶若计量点不同需禁用不适用段。 输出单位为 kWh/时段；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 变压器空载/负载损耗若不可用常数率逼近则采用独立物理子模型；已模拟停机则 A_t=1。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第3组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `E_available,t = max(0, (P_AC,t × K_AC,t × K_tr,t × K_line,t − P_aux,t) × Δt_t × A_t)`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 逐段能量台账对账；PR/系统损失/可利用率重复扣除检查；站用电进口另列，不通过负发电量混入。

**逐个下标词素：** available=限发前可用电量；t=同一时间粒度的时段索引；AC=交流侧额定容量/功率；tr=变压器环节；line=送出线路损失；aux=站内辅助用电。

**术语键：** `TERM-F-AVAILABLE-ENERGY`。

### F-ENERGY-AGGREGATION · 月年度电量汇总

- 英文全称：Monthly and annual energy aggregation；首次释义：月年度电量汇总（Monthly and annual energy aggregation）。
- 最低清单组：3；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
E_{b,p}=\sum_{t\in\mathcal T_p}E_{b,t}
$$

- 文本式：`E_b,p = Σ(t∈T_p) E_b,t`
- 输出：`energy.period_totals_kwh`；量纲/单位：kWh。
- 输入：`energy.boundary_interval_kwh`, `energy.boundary_id`, `time.aggregation_period`, `time.period_interval_ids`。
- 章节：`CH05`, `CH08`, `CH10`；未来测试：`T-ENERGY-AGGREGATION`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| E_b,p | 边界 b、汇总期 p 的电量 | kWh | `energy.period_totals_kwh` |
| E_b,t | 边界 b 的时段电量 | kWh/时段 | `energy.boundary_interval_kwh` |
| b | 已登记的可用、自用、上网、限发或交付边界标签 | 标签 | `energy.boundary_id` |
| p | 月、资源年或运营年的汇总期 | 期间 | `time.aggregation_period` |
| T_p | 归属该期的完整时段有限集合 | 集合 | `time.period_interval_ids` |
| t | 时段索引 | 1 | index_or_constant |

**下标、上标及集合范围：**

- 下标/范围 `t∈T_p`：Σ 对汇总期全部时段求和；b=同一物理边界；p=选定月或年。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 集合/求和或连乘 `t∈T_p`：Σ 对汇总期全部时段求和；b=同一物理边界；p=选定月或年。

**边界与量纲：** 不混合限发前/后和 DC/AC 边界；账期与自然年不能静默合并。 输出单位为 kWh；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 原始时段无重叠，缺测保持缺失状态。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第3组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `E_b,p = Σ(t∈T_p) E_b,t`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 月总之和与同一运营年总量一致，跨年投产/闰年/缺测均列 PLANNED。

**逐个下标词素：** b=互斥的项目/股权及税前后完整口径索引；p=月/年汇总期间索引；t=同一时间粒度的时段索引。

**术语键：** `TERM-F-ENERGY-AGGREGATION`。

### F-INITIAL-DEGRADATION · 首年初始衰减

- 英文全称：Initial first-year degradation；首次释义：首年初始衰减（Initial first-year degradation）。
- 最低清单组：4；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
E_1=E_{1,pre}(1-d_{init})
$$

- 文本式：`E_1 = E_1,pre × (1 − d_init)`
- 输出：`energy.first_year_ac_kwh`；量纲/单位：kWh。
- 输入：`energy.first_year_pre_initial_kwh`, `degradation.initial_fraction`。
- 章节：`CH07`, `CH08`；未来测试：`T-INITIAL-DEGRADATION`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| E_1 | 已计初始衰减的首年同边界电量 | kWh | `energy.first_year_ac_kwh` |
| E_1,pre | 未计初始衰减的首年同边界电量 | kWh | `energy.first_year_pre_initial_kwh` |
| d_init | 首年初始性能损失比例 | 1 | `degradation.initial_fraction` |

**下标、上标及集合范围：**

- 下标/范围 `1`：首个完整运营年；pre=初始损失前；init=初始衰减。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 只适用于首年初始损失尚未由组件模型/PR/损失表包含的情况。 输出单位为 kWh；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 不得与简式结果的已含初始损失再乘；相同 output 属互斥方法节点，必须记 selected_method。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第4组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `E_1 = E_1,pre × (1 − d_init)`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 已含初始衰减时拒绝再应用；与损失覆盖台账核对。

**逐个下标词素：** 1=首运营年或扰动后情景 1，具体按完整符号区分；pre=初始衰减前或所得税前，按完整符号区分；init=首年初始性能损失。

**术语键：** `TERM-F-INITIAL-DEGRADATION`。

### F-ANNUAL-DEGRADATION · 后续恒定衰减

- 英文全称：Constant annual degradation；首次释义：后续恒定衰减（Constant annual degradation）。
- 最低清单组：4；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
E_y=E_1(1-d)^{y-1}
$$

- 文本式：`E_y = E_1 × (1 − d)^(y − 1)`
- 输出：`energy.annual_kwh`；量纲/单位：kWh。
- 输入：`energy.first_year_ac_kwh`, `degradation.annual_fraction`, `time.operating_year`。
- 章节：`CH08`, `CH16`；未来测试：`T-ANNUAL-DEGRADATION`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| E_y | 第 y 个运营年同边界电量 | kWh | `energy.annual_kwh` |
| E_1 | 已计初始衰减的首年电量 | kWh | `energy.first_year_ac_kwh` |
| d | 每完整运营年的相对衰减比例 | 1（每个年度步长的比例） | `degradation.annual_fraction` |
| y | 从 1 起的完整运营年整数序号 | 1 | `time.operating_year` |

**下标、上标及集合范围：**

- 下标/范围 `y`：运营年 1…N_op，非建设财务年；1=首年。
- 上标/幂 `y−1`：从首年以后经历的完整年度衰减次数；不是变量名称上标。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 天气、限发、自用、设备状态保持可比时才可整年比例缩放；财务基期不是 y=1。 输出单位为 kWh；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 0≤d<1；d 是每年比例，幂中 y−1 是无量纲年度步数；更换、扩容、分段衰减需逐年重算。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第4组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `E_y = E_1 × (1 − d)^(y − 1)`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** y=1 复得首年；无衰减、长期单调性；更换后不许无条件沿用旧曲线。

**逐个下标词素：** y=财务或运营年度索引，必须按本条时间定义区分；1=首运营年或扰动后情景 1，具体按完整符号区分。

**术语键：** `TERM-F-ANNUAL-DEGRADATION`。

### F-PIECEWISE-DEGRADATION · 分段衰减性能系数

- 英文全称：Piecewise degradation retention；首次释义：分段衰减性能系数（Piecewise degradation retention）。
- 最低清单组：4；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
q_y=q_{y-1}(1-d_y)+u_y
$$

- 文本式：`q_y = q_(y−1) × (1 − d_y) + u_y`
- 输出：`degradation.annual_retention`；量纲/单位：1。
- 输入：`degradation.previous_retention`, `degradation.yearly_fraction`, `degradation.replacement_uplift`。
- 章节：`CH08`, `CH15`, `CH16`；未来测试：`T-PIECEWISE-DEGRADATION`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| q_y | 相对铭牌基准的当年性能系数 | 1 | `degradation.annual_retention` |
| q_(y−1) | 上一运营年末性能系数 | 1 | `degradation.previous_retention` |
| d_y | 当年度分段衰减比例 | 1（每个年度步长的比例） | `degradation.yearly_fraction` |
| u_y | 设备更换带来的净性能修复量，占同一原始基准容量比例 | 1 | `degradation.replacement_uplift` |

**下标、上标及集合范围：**

- 下标/范围 `y`：从第二完整运营年开始递推；y−1 为前一年；q_1 为已知初始条件。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 只更新性能，不替代年度天气/停机/限发重算；设备增容需修改容量而非伪装修复。 输出单位为 1；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- q_1 来源单列；更换范围与报废范围有凭据；物理合理上界需按设备确定。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第4组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `q_y = q_(y−1) × (1 − d_y) + u_y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 分段时间连接、更换不双计、q_y 与年度容量/停机模型一致性。

**逐个下标词素：** y=财务或运营年度索引，必须按本条时间定义区分；1=首运营年或扰动后情景 1，具体按完整符号区分。

**术语键：** `TERM-F-PIECEWISE-DEGRADATION`。

### F-EQUIVALENT-HOURS · 等效利用小时

- 英文全称：Equivalent full-load hours；首次释义：等效利用小时（Equivalent full-load hours）。
- 最低清单组：5；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
h_{eq,y}=E_y/P_{ref}
$$

- 文本式：`h_eq,y = E_y / P_ref`
- 输出：`energy.equivalent_hours`；量纲/单位：h。
- 输入：`energy.annual_kwh`, `energy.reference_capacity_kw`。
- 章节：`CH01`, `CH08`；未来测试：`T-EQUIVALENT-HOURS`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| h_eq,y | 年度等效满功率小时 | h | `energy.equivalent_hours` |
| E_y | 选定计量点年度交流电量 | kWh | `energy.annual_kwh` |
| P_ref | 与指标标签一致的 DC 或 AC 参考容量 | kW | `energy.reference_capacity_kw` |

**下标、上标及集合范围：**

- 下标/范围 `eq`：等效标签；y=指定运营年；ref=明确 DC/AC 参考容量。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 必须同时输出 reference_capacity_basis=DC/AC 和计量点，不能跨口径对标。 输出单位为 h；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- P_ref > 0；不将小时数理解为实际日照时长。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第5组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `h_eq,y = E_y / P_ref`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 独立 kWh/kW 量纲校验，DC/AC 分母互换应改变结果且标签同步。

**逐个下标词素：** eq=等效满发小时；y=财务或运营年度索引，必须按本条时间定义区分；ref=DC 或 AC 已明确的参考容量。

**术语键：** `TERM-F-EQUIVALENT-HOURS`。

### F-CAPACITY-FACTOR · 容量因子

- 英文全称：Capacity factor；首次释义：容量因子（Capacity factor）。
- 最低清单组：5；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
CF_{cap,y}=E_y/(P_{ref}H_y)
$$

- 文本式：`CF_cap,y = E_y / (P_ref × H_y)`
- 输出：`energy.capacity_factor`；量纲/单位：1。
- 输入：`energy.annual_kwh`, `energy.reference_capacity_kw`, `time.year_hours`。
- 章节：`CH01`, `CH08`；未来测试：`T-CAPACITY-FACTOR`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| CF_cap,y | 指定年度和容量口径的容量因子，不是现金流 | 1 | `energy.capacity_factor` |
| E_y | 选定边界年度交流电量 | kWh | `energy.annual_kwh` |
| P_ref | 标签明确的 DC/AC 参考容量 | kW | `energy.reference_capacity_kw` |
| H_y | 该评价年度的实际覆盖小时数 | h | `time.year_hours` |

**下标、上标及集合范围：**

- 下标/范围 `cap`：容量指标标签；y=运营年；ref=参考装机。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 完整普通年、闰年、首尾不完整运营年分别用实际时段覆盖；不能一律硬编码小时数。 输出单位为 1；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- CF_cap 与财务 CF 变量分开；不完整年需显著标注。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第5组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `CF_cap,y = E_y / (P_ref × H_y)`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 与等效小时/H_y 一致，闰年和时区时间轴核验。

**逐个下标词素：** cap=容量因子，避免与现金流 CF 混淆；y=财务或运营年度索引，必须按本条时间定义区分；ref=DC 或 AC 已明确的参考容量。

**术语键：** `TERM-CAPACITY-FACTOR`。

### F-PR-OBSERVED · 同边界性能比校核

- 英文全称：Boundary-consistent performance ratio；首次释义：同边界性能比校核（Boundary-consistent performance ratio）。
- 最低清单组：5；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
PR_y=\frac{E_y/P_{DC}}{H_{POA,y}/G_{STC}}
$$

- 文本式：`PR_y = (E_y/P_DC) / (H_POA,y/G_STC)`
- 输出：`energy.pr_observed`；量纲/单位：1。
- 输入：`energy.annual_kwh`, `capacity.dc_kwp`, `resource.poa_irradiation_kwh_m2`, `constants.stc_irradiance_kw_m2`。
- 章节：`CH08`；未来测试：`T-PR-OBSERVED`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| PR_y | 同年同容量同计量点的性能比 | 1 | `energy.pr_observed` |
| E_y | 选定计量点年度交流电量 | kWh | `energy.annual_kwh` |
| P_DC | 同期可比直流额定容量 | kWp | `capacity.dc_kwp` |
| H_POA,y | 同年阵列面累计辐照量 | kWh/m² | `resource.poa_irradiation_kwh_m2` |
| G_STC | 标准参考辐照度 | kW/m² | `constants.stc_irradiance_kw_m2` |

**下标、上标及集合范围：**

- 下标/范围 `y`：同一运营年；POA=阵列平面；STC=标准测试；DC=直流。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 性能比不是逆变器效率；限发/停机含否需标签；不与 PR 假设法形成循环输入。 输出单位为 1；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 有效 POA 和 P_DC 均大于零；扩容年度要分段。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第5组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `PR_y = (E_y/P_DC) / (H_POA,y/G_STC)`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 简式符号回代仅查代数不算独立验证；最终需独立能量参考。

**逐个下标词素：** y=财务或运营年度索引，必须按本条时间定义区分；DC=直流侧组件额定容量/功率；POA=组件阵列平面；STC=标准测试条件基准。

**术语键：** `TERM-F-PR-OBSERVED`, `TERM-PR`。

### F-EXPORT-LIMIT-ENERGY · 上网功率限制换算电量

- 英文全称：Export power-to-energy limit；首次释义：上网功率限制换算电量（Export power-to-energy limit）。
- 最低清单组：6；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
X_t=P_{lim,t}\Delta t_t
$$

- 文本式：`X_t = P_lim,t × Δt_t`
- 输出：`grid.export_limit_kwh`；量纲/单位：kWh/时段。
- 输入：`grid.export_limit_kw`, `time.interval_hours`。
- 章节：`CH09`, `CH10`；未来测试：`T-EXPORT-LIMIT-ENERGY`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| X_t | 该时段允许的最大上网电量 | kWh/时段 | `grid.export_limit_kwh` |
| P_lim,t | 时段有效上网有功功率限额 | kW | `grid.export_limit_kw` |
| Δt_t | 同一时段时长 | h | `time.interval_hours` |

**下标、上标及集合范围：**

- 下标/范围 `t`：与发电和负荷完全同一时段；lim=功率限制。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 功率限额在区间内有效且恒定/以保守等效值表示；合同直接给电量上限时直接使用不再乘时长。 输出单位为 kWh/时段；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 限额非负；缺失限额不等于无限制；需标已核验/情景。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第6组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `X_t = P_lim,t × Δt_t`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** kW 与 kWh 混用拒绝，时长改变时限额按比例变化。

**逐个下标词素：** t=同一时间粒度的时段索引；lim=上网有功功率限制。

**术语键：** `TERM-F-EXPORT-LIMIT-ENERGY`。

### F-SELF-CONSUMPTION · 时段自用电量

- 英文全称：Interval self-consumption；首次释义：时段自用电量（Interval self-consumption）。
- 最低清单组：6；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
E_{self,t}=\min(E_{available,t},L_t)
$$

- 文本式：`E_self,t = min(E_available,t, L_t)`
- 输出：`consumption.self_kwh`；量纲/单位：kWh/时段。
- 输入：`energy.available_kwh`, `load.interval_kwh`。
- 章节：`CH08`, `CH10`；未来测试：`T-SELF-CONSUMPTION`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| E_self,t | 该时段物理匹配的自用电量 | kWh/时段 | `consumption.self_kwh` |
| E_available,t | 同计量点限发前可用电量 | kWh/时段 | `energy.available_kwh` |
| L_t | 同计量点可由光伏供给的负荷电量 | kWh/时段 | `load.interval_kwh` |

**下标、上标及集合范围：**

- 下标/范围 `t`：相同时区、时间戳和时长的区间；self=自用，available=限发前。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 非负、同区间 kWh；E_available 是同计量边界限发前电量，L 是同点可抵减负荷；本公式不充分描述含储能/跨区间净计量/不同电表边界。 输出单位为 kWh/时段；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 年总负荷不能代替同粒度负荷；第三方投资收入归属由合同独立决定。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第6组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `E_self,t = min(E_available,t, L_t)`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 自用不超过发电或负荷；缺负荷返回 UNKNOWN，不以年总量虚构自用率。

**逐个下标词素：** self=同边界时段自用电量；t=同一时间粒度的时段索引；available=限发前可用电量。

**术语键：** `TERM-F-SELF-CONSUMPTION`。

### F-EXPORTED-ENERGY · 时段上网电量

- 英文全称：Interval exported energy；首次释义：时段上网电量（Interval exported energy）。
- 最低清单组：6；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
E_{export,t}=\min[\max(E_{available,t}-E_{self,t},0),X_t]
$$

- 文本式：`E_export,t = min(max(E_available,t − E_self,t, 0), X_t)`
- 输出：`consumption.export_kwh`；量纲/单位：kWh/时段。
- 输入：`energy.available_kwh`, `consumption.self_kwh`, `grid.export_limit_kwh`。
- 章节：`CH09`, `CH10`；未来测试：`T-EXPORTED-ENERGY`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| E_export,t | 计量点实际可上网电量 | kWh/时段 | `consumption.export_kwh` |
| E_available,t | 同点限发前电量 | kWh/时段 | `energy.available_kwh` |
| E_self,t | 同点自用电量 | kWh/时段 | `consumption.self_kwh` |
| X_t | 同区间上网电量上限 | kWh/时段 | `grid.export_limit_kwh` |

**下标、上标及集合范围：**

- 下标/范围 `t`：时段；export=上网，self=自用。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 非负、同区间 kWh；E_available 是同计量边界限发前电量，L 是同点可抵减负荷；本公式不充分描述含储能/跨区间净计量/不同电表边界。 输出单位为 kWh/时段；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 全额上网方案设商业自用边界为零但站用电仍需扣除；未获并网确认仅可作为情景。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第6组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `E_export,t = min(max(E_available,t − E_self,t, 0), X_t)`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 上网不超过剩余发电和时段限额；屋顶自用模式与全额上网分类隔离。

**逐个下标词素：** export=上网/送出计量边界；t=同一时间粒度的时段索引；available=限发前可用电量；self=同边界时段自用电量。

**术语键：** `TERM-F-EXPORTED-ENERGY`。

### F-CURTAILED-ENERGY · 时段弃光限发电量

- 英文全称：Interval curtailed energy；首次释义：时段弃光限发电量（Interval curtailed energy）。
- 最低清单组：6；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
E_{curt,t}=E_{available,t}-E_{self,t}-E_{export,t}
$$

- 文本式：`E_curt,t = E_available,t − E_self,t − E_export,t`
- 输出：`consumption.curtailed_kwh`；量纲/单位：kWh/时段。
- 输入：`energy.available_kwh`, `consumption.self_kwh`, `consumption.export_kwh`。
- 章节：`CH08`, `CH09`, `CH10`；未来测试：`T-CURTAILED-ENERGY`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| E_curt,t | 因本时段消纳或送出约束未交付的电量 | kWh/时段 | `consumption.curtailed_kwh` |
| E_available,t | 同计量点限发前可用电量 | kWh/时段 | `energy.available_kwh` |
| E_self,t | 同点自用电量 | kWh/时段 | `consumption.self_kwh` |
| E_export,t | 同点上网电量 | kWh/时段 | `consumption.export_kwh` |

**下标、上标及集合范围：**

- 下标/范围 `t`：同时间段；curt=弃光限发。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 非负、同区间 kWh；E_available 是同计量边界限发前电量，L 是同点可抵减负荷；本公式不充分描述含储能/跨区间净计量/不同电表边界。 输出单位为 kWh/时段；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 技术损失已在 available 前处理，不能全算弃光；负弃光是错误而非静默归零。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第6组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `E_curt,t = E_available,t − E_self,t − E_export,t`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 极端零上网/零负荷/足额消纳；非负能量守恒。

**逐个下标词素：** curt=弃光限发；t=同一时间粒度的时段索引；available=限发前可用电量；self=同边界时段自用电量；export=上网/送出计量边界。

**术语键：** `TERM-F-CURTAILED-ENERGY`。

### F-ENERGY-BALANCE · 时段电量平衡残差

- 英文全称：Interval energy balance residual；首次释义：时段电量平衡残差（Interval energy balance residual）。
- 最低清单组：6；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
\epsilon_{E,t}=E_{available,t}-E_{self,t}-E_{export,t}-E_{curt,t}
$$

- 文本式：`ε_E,t = E_available,t − E_self,t − E_export,t − E_curt,t`
- 输出：`checks.energy_balance_residual`；量纲/单位：kWh/时段。
- 输入：`energy.available_kwh`, `consumption.self_kwh`, `consumption.export_kwh`, `consumption.curtailed_kwh`。
- 章节：`CH08`, `CH10`, `CH17`；未来测试：`T-ENERGY-BALANCE`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| ε_E,t | 电量守恒残差，应在声明的容差内为零 | kWh/时段 | `checks.energy_balance_residual` |
| E_available,t | 限发前可用电量 | kWh/时段 | `energy.available_kwh` |
| E_self,t | 自用电量 | kWh/时段 | `consumption.self_kwh` |
| E_export,t | 上网电量 | kWh/时段 | `consumption.export_kwh` |
| E_curt,t | 限发电量 | kWh/时段 | `consumption.curtailed_kwh` |

**下标、上标及集合范围：**

- 下标/范围 `E`：能量残差标签；t=时段；ε=残差。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 非负、同区间 kWh；E_available 是同计量边界限发前电量，L 是同点可抵减负荷；本公式不充分描述含储能/跨区间净计量/不同电表边界。 输出单位为 kWh/时段；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 未来引擎需配置绝对与相对容差；本阶段不伪造容差测试成功。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第6组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `ε_E,t = E_available,t − E_self,t − E_export,t − E_curt,t`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 全部分项非负且残差闭合；不能只检查公式字符串。

**逐个下标词素：** E=股权/融资主体口径，ε_E 则标能量残差；t=同一时间粒度的时段索引；available=限发前可用电量；self=同边界时段自用电量；export=上网/送出计量边界；curt=弃光限发。

**术语键：** `TERM-F-ENERGY-BALANCE`。

### F-DELIVERED-ENERGY · 可利用交付电量

- 英文全称：Delivered usable energy；首次释义：可利用交付电量（Delivered usable energy）。
- 最低清单组：6；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
E_{delivered,y}=\sum_{t\in\mathcal T_y}(E_{self,t}+E_{export,t})
$$

- 文本式：`E_delivered,y = Σ(t∈T_y) (E_self,t + E_export,t)`
- 输出：`energy.delivered_annual_kwh`；量纲/单位：kWh。
- 输入：`consumption.self_kwh`, `consumption.export_kwh`, `time.operating_interval_ids`。
- 章节：`CH01`, `CH08`, `CH10`, `CH16`；未来测试：`T-DELIVERED-ENERGY`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| E_delivered,y | 第 y 年同项目边界可利用交付电量 | kWh | `energy.delivered_annual_kwh` |
| E_self,t | 合法计量边界内的自用电量 | kWh/时段 | `consumption.self_kwh` |
| E_export,t | 同边界实际上网电量 | kWh/时段 | `consumption.export_kwh` |
| t | 时段索引 | 1 | index_or_constant |
| y | 运营年索引 | 1 | index_or_constant |
| T_y | 第 y 个运营年的完整时段集合 | 集合 | `time.operating_interval_ids` |

**下标、上标及集合范围：**

- 下标/范围 `t∈T_y`：Σ 遍历年 y 的所有时段；delivered=交付，不含弃光。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 集合/求和或连乘 `t∈T_y`：Σ 遍历年 y 的所有时段；delivered=交付，不含弃光。

**边界与量纲：** 用于 LCOE 的可利用边界；剔除弃光，不得用理论直流电量替代。 输出单位为 kWh；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 若只评价售电边界则仅纳入售电且成本也同边界；缺项不能当零。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第6组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `E_delivered,y = Σ(t∈T_y) (E_self,t + E_export,t)`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 交付加限发等于可用年度量；与时段汇总独立复核。

**逐个下标词素：** delivered=同计量点可利用交付量，不含弃光；y=财务或运营年度索引，必须按本条时间定义区分；self=同边界时段自用电量；t=同一时间粒度的时段索引；export=上网/送出计量边界。

**术语键：** `TERM-F-DELIVERED-ENERGY`。

### F-SELF-CONSUMPTION-RATIO · 发电侧自用率

- 英文全称：Generation-side self-consumption ratio；首次释义：发电侧自用率（Generation-side self-consumption ratio）。
- 最低清单组：6；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
S_y=\frac{\sum_{t\in\mathcal T_y}E_{self,t}}{E_{delivered,y}}
$$

- 文本式：`S_y = Σ(t∈T_y) E_self,t / E_delivered,y`
- 输出：`consumption.self_ratio`；量纲/单位：1。
- 输入：`consumption.self_kwh`, `energy.delivered_annual_kwh`, `time.operating_interval_ids`。
- 章节：`CH01`, `CH10`；未来测试：`T-SELF-CONSUMPTION-RATIO`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| S_y | 以实际交付电量为分母的自用比例 | 1 | `consumption.self_ratio` |
| E_self,t | 时段自用电量 | kWh/时段 | `consumption.self_kwh` |
| E_delivered,y | 同年自用加上网电量，不含弃光 | kWh | `energy.delivered_annual_kwh` |
| t | 时段索引 | 1 | index_or_constant |
| T_y | 运营年 y 的时段集合 | 集合 | `time.operating_interval_ids` |
| y | 运营年 | 1 | index_or_constant |

**下标、上标及集合范围：**

- 下标/范围 `t∈T_y`：Σ 遍历年 y；S=发电侧自用率。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 集合/求和或连乘 `t∈T_y`：Σ 遍历年 y；S=发电侧自用率。

**边界与量纲：** 明确分母为交付电量；另需限发前自用比例时须新 ID，不能混称；不是负荷自给率。 输出单位为 1；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 分母零返回 UNDEFINED；缺逐时负荷只可用显式假设情景，不是实际自用率。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第6组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `S_y = Σ(t∈T_y) E_self,t / E_delivered,y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 比率范围、分母零、无负荷 UNKNOWN；与负荷自给率区分。

**逐个下标词素：** y=财务或运营年度索引，必须按本条时间定义区分；self=同边界时段自用电量；t=同一时间粒度的时段索引；delivered=同计量点可利用交付量，不含弃光。

**术语键：** `TERM-F-SELF-CONSUMPTION-RATIO`。

### F-LOAD-COVERAGE-RATIO · 负荷侧自给率

- 英文全称：Load coverage ratio；首次释义：负荷侧自给率（Load coverage ratio）。
- 最低清单组：6；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
A_y=\frac{\sum_{t\in\mathcal T_y}E_{self,t}}{\sum_{t\in\mathcal T_y}L_t}
$$

- 文本式：`A_y = Σ(t∈T_y) E_self,t / Σ(t∈T_y) L_t`
- 输出：`consumption.load_coverage_ratio`；量纲/单位：1。
- 输入：`consumption.self_kwh`, `load.interval_kwh`, `time.operating_interval_ids`。
- 章节：`CH10`；未来测试：`T-LOAD-COVERAGE-RATIO`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| A_y | 被光伏自用覆盖的总负荷比例 | 1 | `consumption.load_coverage_ratio` |
| E_self,t | 时段自用电量 | kWh/时段 | `consumption.self_kwh` |
| L_t | 时段负荷 | kWh/时段 | `load.interval_kwh` |
| t | 时段索引 | 1 | index_or_constant |
| T_y | 运营年 y 同一覆盖时段集合 | 集合 | `time.operating_interval_ids` |
| y | 运营年 | 1 | index_or_constant |

**下标、上标及集合范围：**

- 下标/范围 `t∈T_y`：分子分母均对同年全部时段求和；A=负荷覆盖标签，非可用率 A_t。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 集合/求和或连乘 `t∈T_y`：分子分母均对同年全部时段求和；A=负荷覆盖标签，非可用率 A_t。

**边界与量纲：** 同一负荷表边界；不与发电侧自用率混用。 输出单位为 1；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 总负荷为零时 UNDEFINED；负荷覆盖完整。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第6组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `A_y = Σ(t∈T_y) E_self,t / Σ(t∈T_y) L_t`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 分母与自用率不同的对照、负荷覆盖率不超过一。

**逐个下标词素：** y=财务或运营年度索引，必须按本条时间定义区分；self=同边界时段自用电量；t=同一时间粒度的时段索引。

**术语键：** `TERM-F-LOAD-COVERAGE-RATIO`。

### F-ENERGY-REVENUE · 自持项目电量经济收益

- 英文全称：Owner-operated energy benefit；首次释义：自持项目电量经济收益（Owner-operated energy benefit）。
- 最低清单组：7；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
R_y=\sum_{t\in\mathcal T_y}(E_{self,t}p_{avoid,t}+E_{export,t}p_{sell,t})+R_{other,y}
$$

- 文本式：`R_y = Σ(t∈T_y)(E_self,t×p_avoid,t + E_export,t×p_sell,t) + R_other,y`
- 输出：`revenue.annual_benefit`；量纲/单位：元。
- 输入：`consumption.self_kwh`, `tariff.avoidable_price`, `consumption.export_kwh`, `tariff.export_price`, `revenue.other_benefit`, `time.settlement_interval_ids`。
- 章节：`CH10`, `CH16`；未来测试：`T-ENERGY-REVENUE`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| R_y | 自持项目年度经济收益，按同一税价口径 | 元 | `revenue.annual_benefit` |
| E_self,t | 自用电量 | kWh/时段 | `consumption.self_kwh` |
| p_avoid,t | 确实可避免的边际购电单价，不含不可减少固定费 | 元/kWh | `tariff.avoidable_price` |
| E_export,t | 可结算上网电量 | kWh/时段 | `consumption.export_kwh` |
| p_sell,t | 合同/交易规则的售电结算单价，可在有依据时为负 | 元/kWh | `tariff.export_price` |
| R_other,y | 有来源且未重计的其他年度收益 | 元 | `revenue.other_benefit` |
| t | 结算时段索引 | 1 | index_or_constant |
| T_y | 该运营年合法结算时段集合 | 集合 | `time.settlement_interval_ids` |
| y | 运营年 | 1 | index_or_constant |

**下标、上标及集合范围：**

- 下标/范围 `t∈T_y`：Σ 对年 y 结算时段求和；avoid=可避免购电，sell=售电，other=其他。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 集合/求和或连乘 `t∈T_y`：Σ 对年 y 结算时段求和；avoid=可避免购电，sell=售电，other=其他。

**边界与量纲：** 自持自用节省属于项目经济收益但不是另一笔到账销售现金；进现金流时用避免支出法或增量收益法二选一。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 税价/计量周期一致；需求电费减免有独立账单模型才可计；外售需计结算偏差。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第7组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `R_y = Σ(t∈T_y)(E_self,t×p_avoid,t + E_export,t×p_sell,t) + R_other,y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 自用与外售逐项复算；不变电价下发电下降不应增加电量收益；合法负电价不得静默归零。

**逐个下标词素：** y=财务或运营年度索引，必须按本条时间定义区分；self=同边界时段自用电量；t=同一时间粒度的时段索引；avoid=实际可避免的购电成本；export=上网/送出计量边界；sell=售电结算价；other=未在其他项目计入的其他收益/税费。

**术语键：** `TERM-F-ENERGY-REVENUE`。

### F-PPA-REVENUE · 第三方购售电合同收入

- 英文全称：Third-party PPA revenue；首次释义：第三方购售电合同收入（Third-party PPA revenue）。
- 最低清单组：7；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
R_{PPA,y}=\sum_{t\in\mathcal T_y}(E_{host,t}p_{PPA,t}+E_{export,t}p_{sell,t})+R_{other,y}
$$

- 文本式：`R_PPA,y = Σ(t∈T_y)(E_host,t×p_PPA,t + E_export,t×p_sell,t) + R_other,y`
- 输出：`revenue.ppa_benefit`；量纲/单位：元。
- 输入：`consumption.host_delivery_kwh`, `tariff.ppa_price`, `consumption.export_kwh`, `tariff.export_price`, `revenue.other_benefit`, `time.settlement_interval_ids`。
- 章节：`CH03`, `CH10`, `CH16`；未来测试：`T-PPA-REVENUE`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| R_PPA,y | 第三方投资方年度合同经济收入 | 元 | `revenue.ppa_benefit` |
| E_host,t | 向场所业主交付并按 PPA 计价的电量 | kWh/时段 | `consumption.host_delivery_kwh` |
| p_PPA,t | 合同约定的对业主售电单价 | 元/kWh | `tariff.ppa_price` |
| E_export,t | 投资方有权结算的上网电量 | kWh/时段 | `consumption.export_kwh` |
| p_sell,t | 上网结算价 | 元/kWh | `tariff.export_price` |
| R_other,y | 第三方投资方有权获得的其他收益 | 元 | `revenue.other_benefit` |
| t | 时段索引 | 1 | index_or_constant |
| T_y | 运营年 y 的结算时段集合 | 集合 | `time.settlement_interval_ids` |
| y | 运营年 | 1 | index_or_constant |

**下标、上标及集合范围：**

- 下标/范围 `t∈T_y`：Σ 对运营年全部合同结算时段；host=场所用电方；PPA=购售电协议。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 集合/求和或连乘 `t∈T_y`：Σ 对运营年全部合同结算时段；host=场所用电方；PPA=购售电协议。

**边界与量纲：** 从投资方视角；不得再加用电方避免购电收益。租金/收益分成/交易费另入相应费用。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 合同权属清晰；合同单价含税状态与各收入分项单独标注。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第7组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `R_PPA,y = Σ(t∈T_y)(E_host,t×p_PPA,t + E_export,t×p_sell,t) + R_other,y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** PPA 与自持方法互斥，投资方/用电方收益不串用，租金不重记。

**逐个下标词素：** PPA=购售电合同收入或单价；y=财务或运营年度索引，必须按本条时间定义区分；host=购售电合同的场所用电方；t=同一时间粒度的时段索引；export=上网/送出计量边界；sell=售电结算价；other=未在其他项目计入的其他收益/税费。

**术语键：** `TERM-F-PPA-REVENUE`, `TERM-PPA`。

### F-TAX-EXCLUSIVE-AMOUNT · 含税金额剥离

- 英文全称：Tax-inclusive amount separation；首次释义：含税金额剥离（Tax-inclusive amount separation）。
- 最低清单组：7；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
A_{net}=A_{gross}/(1+v)
$$

- 文本式：`A_net = A_gross / (1 + v)`
- 输出：`tax.exclusive_amount`；量纲/单位：与输入同金额单位。
- 输入：`tax.inclusive_amount`, `tax.vat_rate`。
- 章节：`CH10`, `CH14`, `CH15`, `CH16`；未来测试：`T-TAX-EXCLUSIVE-AMOUNT`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| A_net | 不含增值税的单项金额或单价 | 与输入同金额单位 | `tax.exclusive_amount` |
| A_gross | 同项含税金额或单价 | 元或元/kWh | `tax.inclusive_amount` |
| v | 该项该生效期适用的增值税税率 | 1 | `tax.vat_rate` |

**下标、上标及集合范围：**

- 下标/范围 `net`：不含增值税；gross=含增值税；v 为小数税率。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 逐笔按项目/货物/服务适用税率处理，不用统一税率剥离混合成本；免税规则需人工确认。 输出单位为 与输入同金额单位；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- v 有有效性及地域证据；不预设现行税率；税前/税后与含税/不含增值税不是一回事。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第7组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `A_net = A_gross / (1 + v)`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 含税回构、混合税率分项、未知税制拒绝给确定税后结果。

**逐个下标词素：** net=不含增值税金额/收入，非净利润的泛称；gross=含增值税金额或单价。

**术语键：** `TERM-F-TAX-EXCLUSIVE-AMOUNT`。

### F-CASH-RECEIPTS · 权责收益到收款口径

- 英文全称：Accrual-to-cash receipts bridge；首次释义：权责收益到收款口径（Accrual-to-cash receipts bridge）。
- 最低清单组：7；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
R_{cash,y}=R_{invoice,gross,y}+R_{other,cash,y}-\Delta AR_y+\Delta ADV_y
$$

- 文本式：`R_cash,y = R_invoice,gross,y + R_other,cash,y − ΔAR_y + ΔADV_y`
- 输出：`revenue.cash_receipts`；量纲/单位：元。
- 输入：`revenue.invoiced_gross`, `revenue.other_cash`, `working_capital.receivables_change`, `working_capital.advances_change`。
- 章节：`CH15`, `CH16`；未来测试：`T-CASH-RECEIPTS`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| R_cash,y | 实际或预测年度销售现金到账总额 | 元 | `revenue.cash_receipts` |
| R_invoice,gross,y | 本年确认的含税应收售电/服务款，不含自用节省 | 元 | `revenue.invoiced_gross` |
| R_other,cash,y | 未含在发票应收款的其他现金收入 | 元 | `revenue.other_cash` |
| ΔAR_y | 期末减期初经营应收款增加额，含对应税项 | 元 | `working_capital.receivables_change` |
| ΔADV_y | 期末减期初经营预收款增加额 | 元 | `working_capital.advances_change` |

**下标、上标及集合范围：**

- 下标/范围 `y`：财务年；cash=现金，invoice=已确认应收，gross=含税，AR=应收，ADV=预收；Δ=期末减期初。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 用于现金到账核对，不与已扣全部 ΔNWC 的现金流再同时扣应收；模型选择权责+营运资金桥或直接现金法二选一。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 增量自用节省以反事实减少购电支出呈现或等价增量收益桥，非伪造发票；必须声明 selected_cash_basis。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第7组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `R_cash,y = R_invoice,gross,y + R_other,cash,y − ΔAR_y + ΔADV_y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 应收跨年与增值税桥、现金法与权责法同输入等价核对。

**逐个下标词素：** cash=实际或预测现金收付而非权责计提；y=财务或运营年度索引，必须按本条时间定义区分；invoice=本期确认发票应收权责金额；gross=含增值税金额或单价；other=未在其他项目计入的其他收益/税费。

**术语键：** `TERM-F-CASH-RECEIPTS`。

### F-CAPEX-TOTAL · 分类投资估算总额

- 英文全称：Categorized CAPEX total；首次释义：分类投资估算总额（Categorized CAPEX total）。
- 最低清单组：8；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
CAPEX=\sum_{i\in\mathcal I}C_i
$$

- 文本式：`CAPEX = Σ(i∈I) C_i`
- 输出：`capex.total`；量纲/单位：元。
- 输入：`capex.items.amount`, `capex.item_ids`。
- 章节：`CH06`, `CH14`, `CH16`；未来测试：`T-CAPEX-TOTAL`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| CAPEX | 投资估算总额，边界由清单标识 | 元 | `capex.total` |
| C_i | 第 i 类可追溯投资金额 | 元 | `capex.items.amount` |
| i | 成本类别索引 | 1 | index_or_constant |
| I | 互斥且完整的分类清单 | 集合 | `capex.item_ids` |

**下标、上标及集合范围：**

- 下标/范围 `i∈I`：Σ 对方案成本清单所有互斥分类求和；I 的成员须记录税价与建期利息标志。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 集合/求和或连乘 `i∈I`：Σ 对方案成本清单所有互斥分类求和；I 的成员须记录税价与建期利息标志。

**边界与量纲：** 组件、逆变器、支架、电缆、变配电、送出、土建、屋顶加固、施工、运输、设计、开发、管理、预备费、建设期利息逐项纳入/剔除及理由；储能/土地同样显式标识。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 含税估算总额、可折旧资产基数、无杠杆现金流资本支出三者不能直接等同；融资利息标识独立。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第8组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `CAPEX = Σ(i∈I) C_i`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 清单合计与年度付款计划回勾；遗漏/重复、建设期利息重计检查。

**逐个下标词素：** i=投资成本类别索引。

**术语键：** `TERM-F-CAPEX-TOTAL`, `TERM-CAPEX`。

### F-UNIT-INVESTMENT · 单位装机投资

- 英文全称：Specific capital investment；首次释义：单位装机投资（Specific capital investment）。
- 最低清单组：8；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
c_{DC}=CAPEX/P_{DC}
$$

- 文本式：`c_DC = CAPEX / P_DC`
- 输出：`capex.unit_dc`；量纲/单位：元/kWp。
- 输入：`capex.total`, `capacity.dc_kwp`。
- 章节：`CH01`, `CH14`；未来测试：`T-UNIT-INVESTMENT`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| c_DC | 按直流容量计的单位投资 | 元/kWp | `capex.unit_dc` |
| CAPEX | 已说明含税、土地、储能和融资边界的投资估算 | 元 | `capex.total` |
| P_DC | 直流峰值装机容量 | kWp | `capacity.dc_kwp` |

**下标、上标及集合范围：**

- 下标/范围 `DC`：直流容量口径。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 不可将元/kWp 标作元/Wp；对标必须说明地区、时间和范围。 输出单位为 元/kWp；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- P_DC > 0；按 AC 的单位投资另用不同字段。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第8组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `c_DC = CAPEX / P_DC`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 单位换算以及含税边界标签完整性。

**逐个下标词素：** DC=直流侧组件额定容量/功率。

**术语键：** `TERM-SPECIFIC-INVESTMENT`。

### F-ANNUAL-OPEX · 年度现金运营费用计划

- 英文全称：Annual cash OPEX schedule；首次释义：年度现金运营费用计划（Annual cash OPEX schedule）。
- 最低清单组：8；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
O_y=\sum_{k\in\mathcal O_y}O_{k,y}
$$

- 文本式：`O_y = Σ(k∈𝒪_y) O_k,y`
- 输出：`opex.cash_annual`；量纲/单位：元。
- 输入：`opex.items.cash_amount`, `opex.item_ids`。
- 章节：`CH15`, `CH16`；未来测试：`T-ANNUAL-OPEX`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| O_y | 当年现金运营费用合计 | 元 | `opex.cash_annual` |
| O_k,y | 当年分类现金费用，维修、清洗、保险、运维、租金等 | 元 | `opex.items.cash_amount` |
| k | 费用分类索引 | 1 | index_or_constant |
| y | 财务年 | 1 | index_or_constant |
| 𝒪_y | 本年费用分类集合，用符号 O_y 的花体集合形式区分金额 | 集合 | `opex.item_ids` |

**下标、上标及集合范围：**

- 下标/范围 `k∈𝒪_y`：Σ 对本年已登记运营费用分类求和；𝒪_y 与金额 O_y 不同；k=费用类别。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 集合/求和或连乘 `k∈𝒪_y`：Σ 对本年已登记运营费用分类求和；𝒪_y 与金额 O_y 不同；k=费用类别。

**边界与量纲：** 折旧非现金；所得税、增值税、债务本息、资本化更换不在此重复；费用化维修与资本化替换需互斥。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 税价状态与现金流桥一致；未知成本不默认为零。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第8组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `O_y = Σ(k∈O_y) O_k,y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 分类合计、更换资本化与运维不重复、年度付款与应付桥一致性。

**逐个下标词素：** y=财务或运营年度索引，必须按本条时间定义区分；k=损失/费用类别或现金事件索引，见本条集合。

**术语键：** `TERM-F-ANNUAL-OPEX`, `TERM-OPEX`。

### F-OPEX-ESCALATION · 单项运营费用递增

- 英文全称：OPEX escalation schedule；首次释义：单项运营费用递增（OPEX escalation schedule）。
- 最低清单组：8；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
O_{k,y}=O_{k,base}\prod_{a=1}^{y}(1+\pi_{k,a})
$$

- 文本式：`O_k,y = O_k,base × Π(a=1…y)(1 + π_k,a)`
- 输出：`opex.items.escalated_amount`；量纲/单位：元。
- 输入：`opex.items.base_amount`, `opex.items.escalation_rates`, `time.escalation_year`。
- 章节：`CH15`, `CH17`；未来测试：`T-OPEX-ESCALATION`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| O_k,y | 第 k 项第 y 财务年的费用 | 元 | `opex.items.escalated_amount` |
| O_k,base | 基准时点第 k 项费用 | 元 | `opex.items.base_amount` |
| π_k,a | 第 a 年适用于第 k 项的价格递增率 | 1（每个年度步长的比例） | `opex.items.escalation_rates` |
| k | 费用类别 | 1 | index_or_constant |
| a | 递增年度索引 | 1 | index_or_constant |
| y | 从基准到评价年的完整年度步数 | 1 | `time.escalation_year` |

**下标、上标及集合范围：**

- 下标/范围 `Π a=1…y`：对从基准后的第 1 个到第 y 个年度连乘；base=基准，k=费用类别。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 集合/求和或连乘 `Π a=1…y`：对从基准后的第 1 个到第 y 个年度连乘；base=基准，k=费用类别。

**边界与量纲：** 仅适用合同按年度递增的项目；租赁阶梯、一次性更换独立排期，不能同一项重复通胀。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 名义现金流用名义费用；实际现金流不再套一般通胀。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第8组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `O_k,y = O_k,base × Π(a=1…y)(1 + π_k,a)`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 逐年递推和连乘一致、y=0 空乘积为 1、负合法通胀大于 −1。

**逐个下标词素：** k=损失/费用类别或现金事件索引，见本条集合；y=财务或运营年度索引，必须按本条时间定义区分；base=评价或价格基准时点；a=资产/资产类别索引；递增连乘中为年度索引。

**术语键：** `TERM-F-OPEX-ESCALATION`。

### F-STRAIGHT-LINE-DEPRECIATION · 分类直线折旧

- 英文全称：Asset-class straight-line depreciation；首次释义：分类直线折旧（Asset-class straight-line depreciation）。
- 最低清单组：9；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
D_{a,y}=(V_{dep,a}-V_{res,a})/N_{dep,a}
$$

- 文本式：`D_a,y = (V_dep,a − V_res,a) / N_dep,a`
- 输出：`depreciation.asset_annual`；量纲/单位：元/财务年。
- 输入：`depreciation.asset_basis`, `depreciation.asset_residual`, `depreciation.asset_life_years`。
- 章节：`CH15`, `CH16`；未来测试：`T-STRAIGHT-LINE-DEPRECIATION`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| D_a,y | 资产类别 a 在符合计提条件财务年 y 的年度折旧额 | 元/财务年 | `depreciation.asset_annual` |
| V_dep,a | 该资产依法/按会计政策确认的折旧原值，含不可抵扣税而非全部投资 | 元 | `depreciation.asset_basis` |
| V_res,a | 该资产预计计税/会计残值，政策分开建账 | 元 | `depreciation.asset_residual` |
| N_dep,a | 该资产适用折旧年限 | 年 | `depreciation.asset_life_years` |
| a | 资产类别索引 | 1 | index_or_constant |
| y | 符合折旧条件的财务年 | 1 | index_or_constant |

**下标、上标及集合范围：**

- 下标/范围 `a`：资产类别；y=财务年；dep=折旧基础或年限标签，res=残值。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 完整年度直线法；投产当年按生效规则折算，更换资产新增账簿；税折旧与账面折旧分字段。 输出单位为 元/财务年；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- V_dep≥V_res≥0；N_dep>0；累计折旧不超原值减残值；不得将折旧再作现金 OPEX。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第9、10、16组（附件 hermes-完整提示词.md）：由折旧、税务现金口径及平衡要求推导的方法约定；不代表现行法定税率或条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `D_a,y = (V_dep,a − V_res,a) / N_dep,a`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 逐资产折旧表与净值对账，期满停止、部分年度、更换和残值边界；税法未核验则税后结果待核实。

**逐个下标词素：** a=资产/资产类别索引；递增连乘中为年度索引；y=财务或运营年度索引，必须按本条时间定义区分；dep=折旧基础、折旧年限等资产折旧属性；res=资产预计折旧残值。

**术语键：** `TERM-F-STRAIGHT-LINE-DEPRECIATION`。

### F-ASSET-BOOK-VALUE · 资产净值滚动

- 英文全称：Asset net book value roll-forward；首次释义：资产净值滚动（Asset net book value roll-forward）。
- 最低清单组：9；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
BV_{a,y}=BV_{a,y-1}+ADD_{a,y}-D_{a,y}-DISP_{a,y}
$$

- 文本式：`BV_a,y = BV_a,y−1 + ADD_a,y − D_a,y − DISP_a,y`
- 输出：`assets.closing_book_value`；量纲/单位：元。
- 输入：`assets.opening_book_value`, `assets.capitalized_additions`, `depreciation.asset_annual`, `assets.disposal_book_value`。
- 章节：`CH15`, `CH16`；未来测试：`T-ASSET-BOOK-VALUE`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| BV_a,y | 财务年末资产账面/计税净值，账簿类型明确 | 元 | `assets.closing_book_value` |
| BV_a,y−1 | 该年期初同一账簿资产净值 | 元 | `assets.opening_book_value` |
| ADD_a,y | 本年转入该账簿的资产新增原值 | 元 | `assets.capitalized_additions` |
| D_a,y | 本年该账簿折旧额 | 元 | `depreciation.asset_annual` |
| DISP_a,y | 报废/处置转出的资产净值，不是现金收入 | 元 | `assets.disposal_book_value` |
| a | 资产或资产类别 | 1 | index_or_constant |
| y | 财务年索引 | 1 | index_or_constant |

**下标、上标及集合范围：**

- 下标/范围 `a`：资产标识；y−1=上一财务年末；ADD=新增，DISP=处置净值，BV=净值。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 资产处置收入另进入现金流，处置损益另入税基；账面和税务滚动不混用。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 年内新增/处置折旧按实际适用规则计算；净值不能低于合法剩余值。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第9、10、16组（附件 hermes-完整提示词.md）：由折旧、税务现金口径及平衡要求推导的方法约定；不代表现行法定税率或条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `BV_a,y = BV_a,y−1 + ADD_a,y − D_a,y − DISP_a,y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 期初+新增−折旧−处置=期末；资本支出不等于当期转固时的桥接。

**逐个下标词素：** a=资产/资产类别索引；递增连乘中为年度索引；y=财务或运营年度索引，必须按本条时间定义区分；1=首运营年或扰动后情景 1，具体按完整符号区分。

**术语键：** `TERM-F-ASSET-BOOK-VALUE`。

### F-TAXABLE-INCOME-PROJECT · 项目无杠杆应税利润基数

- 英文全称：Unlevered project taxable income base；首次释义：项目无杠杆应税利润基数（Unlevered project taxable income base）。
- 最低清单组：9；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
B_{P,y}=R_{net,y}-O_{ded,y}-D_{tax,y}-A_{tax,y}+G_{tax,y}
$$

- 文本式：`B_P,y = R_net,y − O_ded,y − D_tax,y − A_tax,y + G_tax,y`
- 输出：`tax.project_base_pre_losses`；量纲/单位：元。
- 输入：`revenue.taxable_net`, `tax.deductible_opex`, `depreciation.tax_annual`, `tax.other_deductions`, `tax.other_adjustments`。
- 章节：`CH15`, `CH16`；未来测试：`T-TAXABLE-INCOME-PROJECT`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| B_P,y | 不计融资利息的项目应税利润初始基数，未扣亏损结转 | 元 | `tax.project_base_pre_losses` |
| R_net,y | 项目增量不含增值税应税收入/利益，按适用规则调整 | 元 | `revenue.taxable_net` |
| O_ded,y | 依法允许扣除的当期经营费用 | 元 | `tax.deductible_opex` |
| D_tax,y | 本年允许税前扣除的折旧 | 元 | `depreciation.tax_annual` |
| A_tax,y | 本年可扣除摊销及其他非利息扣减 | 元 | `tax.other_deductions` |
| G_tax,y | 处置收益及其他应税调整净额，可正可负 | 元 | `tax.other_adjustments` |

**下标、上标及集合范围：**

- 下标/范围 `P`：项目无杠杆；y=财务年；net=不含增值税，ded=可扣，tax=税务账。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 这是无杠杆项目评估的税基，不是主体实际申报；自用节省税务影响需反事实税基明确。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 不扣债务利息，避免无杠杆项目 IRR 混入税盾；费用可扣性/递延按核实政策。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第9、10、16组（附件 hermes-完整提示词.md）：由折旧、税务现金口径及平衡要求推导的方法约定；不代表现行法定税率或条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `B_P,y = R_net,y − O_ded,y − D_tax,y − A_tax,y + G_tax,y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 融资比例改变但经营条件不变时该税基不应变；折旧只税盾不重复付现。

**逐个下标词素：** P=项目无杠杆口径；y=财务或运营年度索引，必须按本条时间定义区分；net=不含增值税金额/收入，非净利润的泛称；ded=依法允许税前扣除；tax=税务账簿/计税口径。

**术语键：** `TERM-F-TAXABLE-INCOME-PROJECT`。

### F-TAXABLE-INCOME-EQUITY · 融资后主体应税利润基数

- 英文全称：Levered entity taxable income base；首次释义：融资后主体应税利润基数（Levered entity taxable income base）。
- 最低清单组：9；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
B_{E,y}=B_{P,y}-I_{ded,y}-F_{ded,y}
$$

- 文本式：`B_E,y = B_P,y − I_ded,y − F_ded,y`
- 输出：`tax.equity_base_pre_losses`；量纲/单位：元。
- 输入：`tax.project_base_pre_losses`, `tax.deductible_interest`, `tax.deductible_finance_fees`。
- 章节：`CH15`, `CH16`；未来测试：`T-TAXABLE-INCOME-EQUITY`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| B_E,y | 融资后主体应税利润初始基数 | 元 | `tax.equity_base_pre_losses` |
| B_P,y | 同经营边界无杠杆税基 | 元 | `tax.project_base_pre_losses` |
| I_ded,y | 本年税法允许扣除的债务利息，非必等于现金利息 | 元 | `tax.deductible_interest` |
| F_ded,y | 本年允许税前扣除的融资费用 | 元 | `tax.deductible_finance_fees` |

**下标、上标及集合范围：**

- 下标/范围 `E`：融资后主体/股权口径；P=无杠杆项目口径；ded=可扣除；y=财务年。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 资本化利息与费用按实际税务口径处理，不能既进折旧又全额当期扣除。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 主体税率、扣除限制与有效期需证据；未知税制不推断。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第9、10、16组（附件 hermes-完整提示词.md）：由折旧、税务现金口径及平衡要求推导的方法约定；不代表现行法定税率或条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `B_E,y = B_P,y − I_ded,y − F_ded,y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 融资税盾与资本化利息不重复；无融资时与项目税基一致。

**逐个下标词素：** E=股权/融资主体口径，ε_E 则标能量残差；y=财务或运营年度索引，必须按本条时间定义区分；P=项目无杠杆口径；ded=依法允许税前扣除。

**术语键：** `TERM-F-TAXABLE-INCOME-EQUITY`。

### F-INCOME-TAX-ACCRUAL · 所得税计提与亏损使用

- 英文全称：Income tax charge and loss utilization；首次释义：所得税计提与亏损使用（Income tax charge and loss utilization）。
- 最低清单组：9；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
T_{inc,b,y}=\tau_{b,y}\max(0,B_{b,y}-U_{b,y})
$$

- 文本式：`T_inc,b,y = τ_b,y × max(0, B_b,y − U_b,y)`
- 输出：`tax.income_charge`；量纲/单位：元。
- 输入：`tax.income_rate`, `tax.selected_base_pre_losses`, `tax.losses_used`, `finance.tax_basis`。
- 章节：`CH15`, `CH16`；未来测试：`T-INCOME-TAX-ACCRUAL`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| T_inc,b,y | 本年按已核验规则计提的所得税 | 元 | `tax.income_charge` |
| τ_b,y | 该主体/口径当年有效所得税率，优惠须有适用性证据 | 1 | `tax.income_rate` |
| B_b,y | 未扣结转亏损的应税利润基数 | 元 | `tax.selected_base_pre_losses` |
| U_b,y | 本年依法允许使用的历史亏损额 | 元 | `tax.losses_used` |
| b | P 无杠杆项目或 E 融资主体的互斥口径 | 枚举 | `finance.tax_basis` |
| y | 财务年 | 1 | index_or_constant |

**下标、上标及集合范围：**

- 下标/范围 `b`：P/E 口径标签，必须分开运行；y=财务年；inc=所得税。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 计提不是现金缴纳；亏损使用需逐批年份、期限、限额和政策适用台账，不把负税基直接作退税。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 0≤U≤max(B,0) 且不超可用历史亏损；税率未知则结果 PENDING_VERIFICATION。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第9、10、16组（附件 hermes-完整提示词.md）：由折旧、税务现金口径及平衡要求推导的方法约定；不代表现行法定税率或条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `T_inc,b,y = τ_b,y × max(0, B_b,y − U_b,y)`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 亏损结转/到期、优惠终止、零税基、税率变更均单列未来用例。

**逐个下标词素：** inc=所得税而非其他现金税费；b=互斥的项目/股权及税前后完整口径索引；y=财务或运营年度索引，必须按本条时间定义区分。

**术语键：** `TERM-F-INCOME-TAX-ACCRUAL`。

### F-TAX-LOSS-BALANCE · 税务亏损余额校验

- 英文全称：Tax loss carryforward balance；首次释义：税务亏损余额校验（Tax loss carryforward balance）。
- 最低清单组：9；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
L_{b,y}=L_{b,y-1}+\max(-B_{b,y},0)-U_{b,y}-X_{b,y}
$$

- 文本式：`L_b,y = L_b,y−1 + max(−B_b,y,0) − U_b,y − X_b,y`
- 输出：`tax.losses_closing`；量纲/单位：元。
- 输入：`tax.losses_opening`, `tax.selected_base_pre_losses`, `tax.losses_used`, `tax.losses_expired`, `finance.tax_basis`。
- 章节：`CH15`, `CH16`；未来测试：`T-TAX-LOSS-BALANCE`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| L_b,y | 本年末可用税务亏损余额 | 元 | `tax.losses_closing` |
| L_b,y−1 | 本年初亏损余额，含逐批期限台账 | 元 | `tax.losses_opening` |
| B_b,y | 本年应税利润初始基数 | 元 | `tax.selected_base_pre_losses` |
| U_b,y | 本年实际使用的历史亏损 | 元 | `tax.losses_used` |
| X_b,y | 本年过期/不得再结转的亏损额 | 元 | `tax.losses_expired` |
| b | P/E 税务评估口径 | 枚举 | `finance.tax_basis` |
| y | 财务年 | 1 | index_or_constant |

**下标、上标及集合范围：**

- 下标/范围 `b`：独立税务口径；y−1=上年末；X=过期额标签。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 公式是聚合平衡，不能替代逐批到期和法定抵扣限制判断。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 亏损不跨主体/口径乱转；法规未确认时仅假设方案。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第9、10、16组（附件 hermes-完整提示词.md）：由折旧、税务现金口径及平衡要求推导的方法约定；不代表现行法定税率或条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `L_b,y = L_b,y−1 + max(−B_b,y,0) − U_b,y − X_b,y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 逐批余额之和对聚合式，过期额不重减，余额非负。

**逐个下标词素：** b=互斥的项目/股权及税前后完整口径索引；y=财务或运营年度索引，必须按本条时间定义区分；1=首运营年或扰动后情景 1，具体按完整符号区分。

**术语键：** `TERM-F-TAX-LOSS-BALANCE`。

### F-TAX-CASH-BRIDGE · 所得税计提到现金桥

- 英文全称：Income tax cash bridge；首次释义：所得税计提到现金桥（Income tax cash bridge）。
- 最低清单组：9；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
T_{cash,b,y}=T_{inc,b,y}+TP_{b,y-1}-TP_{b,y}+PRE_{b,y}-PRE_{b,y-1}
$$

- 文本式：`T_cash,b,y = T_inc,b,y + TP_b,y−1 − TP_b,y + PRE_b,y − PRE_b,y−1`
- 输出：`tax.income_cash_paid`；量纲/单位：元。
- 输入：`tax.income_charge`, `tax.income_payable_opening`, `tax.income_payable_closing`, `tax.income_prepaid_closing`, `tax.income_prepaid_opening`, `finance.tax_basis`。
- 章节：`CH15`, `CH16`；未来测试：`T-TAX-CASH-BRIDGE`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| T_cash,b,y | 该年所得税现金净支出，合法退税可为负 | 元 | `tax.income_cash_paid` |
| T_inc,b,y | 当年计提的所得税 | 元 | `tax.income_charge` |
| TP_b,y−1 | 期初应交所得税负债 | 元 | `tax.income_payable_opening` |
| TP_b,y | 期末应交所得税负债 | 元 | `tax.income_payable_closing` |
| PRE_b,y | 期末预缴/可退所得税资产 | 元 | `tax.income_prepaid_closing` |
| PRE_b,y−1 | 期初预缴/可退所得税资产 | 元 | `tax.income_prepaid_opening` |
| b | P/E 口径 | 枚举 | `finance.tax_basis` |
| y | 财务年 | 1 | index_or_constant |

**下标、上标及集合范围：**

- 下标/范围 `b`：项目/融资主体口径；TP=应交税负债，PRE=预缴资产；y−1=期初。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 现金流用本条现金税，不用计提税替代；若营运资金中已含同税资产负债则剔除避免双计。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 欠税/预缴变化合法且有计划；P 口径假想无杠杆税缴纳时点须声明。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第9、10、16组（附件 hermes-完整提示词.md）：由折旧、税务现金口径及平衡要求推导的方法约定；不代表现行法定税率或条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `T_cash,b,y = T_inc,b,y + TP_b,y−1 − TP_b,y + PRE_b,y − PRE_b,y−1`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 税费资产负债期初期末对账；计提/缴纳错期和退税用例。

**逐个下标词素：** cash=实际或预测现金收付而非权责计提；b=互斥的项目/股权及税前后完整口径索引；y=财务或运营年度索引，必须按本条时间定义区分；inc=所得税而非其他现金税费；1=首运营年或扰动后情景 1，具体按完整符号区分。

**术语键：** `TERM-F-TAX-CASH-BRIDGE`。

### F-VAT-CREDIT-BALANCE · 增值税留抵平衡

- 英文全称：VAT input-credit balance；首次释义：增值税留抵平衡（VAT input-credit balance）。
- 最低清单组：9；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
VC_y=VC_{y-1}+VI_y-VO_y+VP_y-VR_y
$$

- 文本式：`VC_y = VC_y−1 + VI_y − VO_y + VP_y − VR_y`
- 输出：`tax.vat_credit_closing`；量纲/单位：元。
- 输入：`tax.vat_credit_opening`, `tax.vat_input_eligible`, `tax.vat_output`, `tax.vat_cash_paid`, `tax.vat_cash_refund`。
- 章节：`CH14`, `CH15`, `CH16`；未来测试：`T-VAT-CREDIT-BALANCE`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| VC_y | 期末可用留抵余额 | 元 | `tax.vat_credit_closing` |
| VC_y−1 | 期初可用留抵余额 | 元 | `tax.vat_credit_opening` |
| VI_y | 本期合法可抵扣进项税额 | 元 | `tax.vat_input_eligible` |
| VO_y | 本期销项税额 | 元 | `tax.vat_output` |
| VP_y | 本期实际缴纳的增值税 | 元 | `tax.vat_cash_paid` |
| VR_y | 本期取得的合法留抵退税 | 元 | `tax.vat_cash_refund` |

**下标、上标及集合范围：**

- 下标/范围 `y`：纳税明细汇总财务年；VC=留抵，VI=进项，VO=销项，VP=缴纳，VR=退税。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 简化连续期对账，须先以法定纳税期建明细再汇总年度；不可抵扣进项进入资产或费用，不进 VI。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 实际税制适用性/抵扣时点和退税资格须核验；若应交未交须增加 VAT 应付账而不是强行令留抵负数。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第9、10、16组（附件 hermes-完整提示词.md）：由折旧、税务现金口径及平衡要求推导的方法约定；不代表现行法定税率或条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `VC_y = VC_y−1 + VI_y − VO_y + VP_y − VR_y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 可抵扣与不可抵扣分离；已退税余额扣减；与实际现金流中销/进项和净缴退税桥对应。

**逐个下标词素：** y=财务或运营年度索引，必须按本条时间定义区分；1=首运营年或扰动后情景 1，具体按完整符号区分。

**术语键：** `TERM-F-VAT-CREDIT-BALANCE`, `TERM-VAT`。

### F-OTHER-CASH-TAXES · 其他现金税费合计

- 英文全称：Other cash taxes and levies；首次释义：其他现金税费合计（Other cash taxes and levies）。
- 最低清单组：9；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
T_{other,b,y}=\sum_{k\in\mathcal Q_{b,y}}T_{k,b,y}
$$

- 文本式：`T_other,b,y = Σ(k∈Q_b,y) T_k,b,y`
- 输出：`tax.other_cash_total`；量纲/单位：元。
- 输入：`tax.other_items_cash`, `tax.other_item_ids`, `finance.tax_basis`。
- 章节：`CH15`, `CH16`；未来测试：`T-OTHER-CASH-TAXES`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| T_other,b,y | 除已单列所得税及增值税净缴退税以外的现金税费 | 元 | `tax.other_cash_total` |
| T_k,b,y | 依法适用的第 k 项现金税费，如有依据的附加/土地等 | 元 | `tax.other_items_cash` |
| Q_b,y | 适用于该主体年度的税费集合 | 集合 | `tax.other_item_ids` |
| k | 税费项索引 | 1 | index_or_constant |
| b | P/E 口径 | 枚举 | `finance.tax_basis` |
| y | 财务年 | 1 | index_or_constant |

**下标、上标及集合范围：**

- 下标/范围 `k∈Q_b,y`：Σ 对该口径该年适用且互斥税费项求和；other=其他税费。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 集合/求和或连乘 `k∈Q_b,y`：Σ 对该口径该年适用且互斥税费项求和；other=其他税费。

**边界与量纲：** 本条只合计，不杜撰统一税种/税率；不得再纳入 OPEX 或税务桥重复扣除。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 税种依据、地域、有效期和缴纳时点逐项记录；UNKNOWN 不视为免税。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第9、10、16组（附件 hermes-完整提示词.md）：由折旧、税务现金口径及平衡要求推导的方法约定；不代表现行法定税率或条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `T_other,b,y = Σ(k∈Q_b,y) T_k,b,y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 税费分类完整性、重复计提、税前成本可扣性和现金年度回勾。

**逐个下标词素：** other=未在其他项目计入的其他收益/税费；b=互斥的项目/股权及税前后完整口径索引；y=财务或运营年度索引，必须按本条时间定义区分；k=损失/费用类别或现金事件索引，见本条集合。

**术语键：** `TERM-F-OTHER-CASH-TAXES`。

### F-PROJECT-CASH-FLOW · 项目投资无杠杆净现金流

- 英文全称：Unlevered project investment cash flow；首次释义：项目投资无杠杆净现金流（Unlevered project investment cash flow）。
- 最低清单组：10；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
CF_{P,y}=B_{op,y}-O_y-T_{P,y}-K_{P,y}-\Delta W_{P,y}+S_{P,y}
$$

- 文本式：`CF_P,y = B_op,y − O_y − T_P,y − K_P,y − ΔW_P,y + S_P,y`
- 输出：`finance.project_cash_flow`；量纲/单位：元。
- 输入：`finance.project_operating_cash_benefit`, `opex.cash_annual`, `tax.project_cash_total`, `capex.unlevered_cash_annual`, `working_capital.project_net_change`, `finance.project_terminal_cash`。
- 章节：`CH01`, `CH14`, `CH15`, `CH16`；未来测试：`T-PROJECT-CASH-FLOW`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| CF_P,y | 项目投资视角税后无杠杆增量净现金流 | 元 | `finance.project_cash_flow` |
| B_op,y | 增量经营现金利益：到账经营收入加确认的自用避免支出，不含融资 | 元 | `finance.project_operating_cash_benefit` |
| O_y | 现金经营支出，不含折旧、已在自用避免支出扣除项和单列税 | 元 | `opex.cash_annual` |
| T_P,y | 无杠杆现金税负：项目所得税、其他税费和适配税价桥后的增值税净缴退 | 元 | `tax.project_cash_total` |
| K_P,y | 当年工程资本付款及资本化更新替换，不含融资资金流和资本化借款利息 | 元 | `capex.unlevered_cash_annual` |
| ΔW_P,y | 经营营运资金净增加，不含已按现金收入/支出桥扣过部分和单列税务资产负债 | 元 | `working_capital.project_net_change` |
| S_P,y | 期末处置净现金和未在 ΔW 中回收的残余资金，税务影响进 T | 元 | `finance.project_terminal_cash` |

**下标、上标及集合范围：**

- 下标/范围 `P`：无杠杆项目；y 为财务时点索引，0 为基期，含所有建设/运营/退出期；op=经营，Δ=期末减期初，W=营运资金。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 建设期、运营期、替换和退出全时点；绝不含贷款提款、本息、融资费或股东出入资。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 直接现金法时 ΔW 只剩未计入收付桥的营运资金；权责法需完整营运资金调整，二者不能叠用。
- 自用节省必须与反事实基线一致，不可把原购电费用和全部节省同时重复扣减/增加。
- 税前项目流由税后流加回明确所得税项形成另一字段/ID，不能把所有增值税都混称所得税。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第10组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `CF_P,y = B_op,y − O_y − T_P,y − K_P,y − ΔW_P,y + S_P,y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 逐项现金流桥、融资比例不改变无杠杆流、折旧仅经税盾影响，建设期利息不重复计入。

**逐个下标词素：** P=项目无杠杆口径；y=财务或运营年度索引，必须按本条时间定义区分；op=运营经营利益。

**术语键：** `TERM-F-PROJECT-CASH-FLOW`。

### F-PROJECT-PRETAX-CASH-FLOW · 项目所得税前现金流

- 英文全称：Project pre-income-tax cash flow；首次释义：项目所得税前现金流（Project pre-income-tax cash flow）。
- 最低清单组：10；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
CF_{P,pre,y}=CF_{P,y}+T_{inc,cash,P,y}
$$

- 文本式：`CF_P,pre,y = CF_P,y + T_inc,cash,P,y`
- 输出：`finance.project_pretax_cash_flow`；量纲/单位：元。
- 输入：`finance.project_cash_flow`, `tax.project_income_cash_paid`。
- 章节：`CH16`；未来测试：`T-PROJECT-PRETAX-CASH-FLOW`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| CF_P,pre,y | 仅加回项目所得税的税前无杠杆现金流 | 元 | `finance.project_pretax_cash_flow` |
| CF_P,y | 所得税后无杠杆项目现金流 | 元 | `finance.project_cash_flow` |
| T_inc,cash,P,y | 同一项目口径实际/模拟所得税现金缴纳净额 | 元 | `tax.project_income_cash_paid` |

**下标、上标及集合范围：**

- 下标/范围 `P`：项目；pre=所得税前；inc,cash=现金所得税；y=财务时点。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 所得税前不等于不含增值税/全部免税；保留合法其他现金税费和税价桥。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 若另需全部税前口径必须新命名，不能替换本式。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第10组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `CF_P,pre,y = CF_P,y + T_inc,cash,P,y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 税前税后流之差等于现金所得税；税盾边界独立复核。

**逐个下标词素：** P=项目无杠杆口径；pre=初始衰减前或所得税前，按完整符号区分；y=财务或运营年度索引，必须按本条时间定义区分；inc=所得税而非其他现金税费；cash=实际或预测现金收付而非权责计提。

**术语键：** `TERM-F-PROJECT-PRETAX-CASH-FLOW`。

### F-EQUITY-AVAILABLE-CASH-FLOW · 股权可分配增量现金流

- 英文全称：Cash flow available to equity；首次释义：股权可分配增量现金流（Cash flow available to equity）。
- 最低清单组：10；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
CF_{E,avail,y}=B_{op,y}-O_y-T_{E,y}-K_{E,y}-\Delta W_{E,y}+S_{E,y}+DD_y-PRN_y-INT_y-FF_y
$$

- 文本式：`CF_E,avail,y = B_op,y − O_y − T_E,y − K_E,y − ΔW_E,y + S_E,y + DD_y − PRN_y − INT_y − FF_y`
- 输出：`finance.equity_available_cash_flow`；量纲/单位：元。
- 输入：`finance.project_operating_cash_benefit`, `opex.cash_annual`, `tax.equity_cash_total`, `capex.equity_asset_cash_annual`, `working_capital.equity_net_change`, `finance.equity_terminal_cash`, `debt.cash_drawdown`, `debt.principal_paid`, `debt.interest_paid`, `debt.finance_fees_paid`。
- 章节：`CH15`, `CH16`；未来测试：`T-EQUITY-AVAILABLE-CASH-FLOW`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| CF_E,avail,y | 融资后可供股权的现金余缺，负值表示需股东追加资金 | 元 | `finance.equity_available_cash_flow` |
| B_op,y | 经营现金利益，不含融资 | 元 | `finance.project_operating_cash_benefit` |
| O_y | 现金运营支出 | 元 | `opex.cash_annual` |
| T_E,y | 考虑合法利息税盾的实际主体现金税总额，税价桥口径与项目流一致 | 元 | `tax.equity_cash_total` |
| K_E,y | 实际资产付款及更换，融资利息和融资费用已单列 INT/FF 因此不在此扣 | 元 | `capex.equity_asset_cash_annual` |
| ΔW_E,y | 未在其他现金项扣过的经营营运资金和约定受限储备净增 | 元 | `working_capital.equity_net_change` |
| S_E,y | 处置及未在 ΔW 中回收的终期现金 | 元 | `finance.equity_terminal_cash` |
| DD_y | 债务现金提款，非资本化利息记账增加 | 元 | `debt.cash_drawdown` |
| PRN_y | 本期实际付现归还本金 | 元 | `debt.principal_paid` |
| INT_y | 本期实际付现债务利息，含建设期支付部分 | 元 | `debt.interest_paid` |
| FF_y | 付现融资费用，未在资产付款/利息中重复计入 | 元 | `debt.finance_fees_paid` |

**下标、上标及集合范围：**

- 下标/范围 `E`：股权口径；avail=可分配余缺；DD=提款，PRN=本金，INT=利息，FF=融资费；y=完整财务时点。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 明确包含融资并使用融资后税负；项目流不能原样加融资后忽略利息税盾。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 资本化但未支付利息只滚入债务余额，不再作为 INT 现金支出；资本化费用同理。
- 本条是可供股权现金流，受限分红制度下不一定等于投资者实际收付。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第10组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `CF_E,avail,y = B_op,y − O_y − T_E,y − K_E,y − ΔW_E,y + S_E,y + DD_y − PRN_y − INT_y − FF_y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 贷款、资本化利息、现金税和更换均逐期复核；与项目流差异桥及资金闭合联检。

**逐个下标词素：** E=股权/融资主体口径，ε_E 则标能量残差；avail=可供股权分配的现金余缺；y=财务或运营年度索引，必须按本条时间定义区分；op=运营经营利益。

**术语键：** `TERM-F-EQUITY-AVAILABLE-CASH-FLOW`。

### F-EQUITY-INVESTOR-CASH-FLOW · 股东实际投入分配现金流

- 英文全称：Equity investor cash flow；首次释义：股东实际投入分配现金流（Equity investor cash flow）。
- 最低清单组：10；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
CF_{E,y}=DIV_y+EXIT_y-EQ_y
$$

- 文本式：`CF_E,y = DIV_y + EXIT_y − EQ_y`
- 输出：`finance.equity_investor_cash_flow`；量纲/单位：元。
- 输入：`equity.distributions`, `equity.exit_receipts`, `equity.contributions`。
- 章节：`CH01`, `CH16`；未来测试：`T-EQUITY-INVESTOR-CASH-FLOW`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| CF_E,y | 投资者视角净现金流，用于实际资本金 IRR | 元 | `finance.equity_investor_cash_flow` |
| DIV_y | 当期实际或计划可合法支付的股东分配 | 元 | `equity.distributions` |
| EXIT_y | 未含在分配中的投资者退出或终期清算回款 | 元 | `equity.exit_receipts` |
| EQ_y | 本期股东实际出资及追加资金 | 元 | `equity.contributions` |

**下标、上标及集合范围：**

- 下标/范围 `E`：股东投资者；DIV=分配，EXIT=退出，EQ=实缴出资；y=财务时点。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 分红限制、储备账户、资金滞留需反映实际收付；CF_E,avail 只有立即全额弥补/分配且无滞留时才与此相等。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 初始及追加出资均负流；不得将累计正项目现金流直接当资本金 IRR 输入。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第10组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `CF_E,y = DIV_y + EXIT_y − EQ_y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 出资计划与资金来源用途对账；受限分红造成 IRR 时点差异；重复退出收入检查。

**逐个下标词素：** E=股权/融资主体口径，ε_E 则标能量残差；y=财务或运营年度索引，必须按本条时间定义区分。

**术语键：** `TERM-F-EQUITY-INVESTOR-CASH-FLOW`。

### F-CASH-FUNDING-BALANCE · 融资与现金账户平衡

- 英文全称：Sources-and-uses cash balance；首次释义：融资与现金账户平衡（Sources-and-uses cash balance）。
- 最低清单组：10；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
CLOSE_y=OPEN_y+CF_{E,avail,y}+EQ_y-DIV_y
$$

- 文本式：`CLOSE_y = OPEN_y + CF_E,avail,y + EQ_y − DIV_y`
- 输出：`checks.cash_closing`；量纲/单位：元。
- 输入：`checks.cash_opening`, `finance.equity_available_cash_flow`, `equity.contributions`, `equity.distributions`。
- 章节：`CH14`, `CH16`, `CH17`；未来测试：`T-CASH-FUNDING-BALANCE`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| CLOSE_y | 项目主体期末非受限现金余额 | 元 | `checks.cash_closing` |
| OPEN_y | 项目主体期初非受限现金余额 | 元 | `checks.cash_opening` |
| CF_E,avail,y | 已计经营、税、资本支出、提款、本息及融资费用的股权可用余缺 | 元 | `finance.equity_available_cash_flow` |
| EQ_y | 股东实际出资及追加 | 元 | `equity.contributions` |
| DIV_y | 主体支付的股东分配，终期清算支付也应归入对应账户用途 | 元 | `equity.distributions` |

**下标、上标及集合范围：**

- 下标/范围 `y`：所有建设/运营财务时点；OPEN/CLOSE=期初/末现金；E,avail=可供股权余缺。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 本条验证主体现金账户；独立第三方支付的股权转让 EXIT 不经过主体账户；终期资产处置已在 CF_E,avail 中。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 资金缺口不能用负现金隐藏；需标 ADDITIONAL_EQUITY_REQUIRED 或融资缺口。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第10组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `CLOSE_y = OPEN_y + CF_E,avail,y + EQ_y − DIV_y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 每期来源=用途+现金增加；建设期超预算、还本期负现金、终期清算不重复。

**逐个下标词素：** y=财务或运营年度索引，必须按本条时间定义区分；E=股权/融资主体口径，ε_E 则标能量残差；avail=可供股权分配的现金余缺。

**术语键：** `TERM-F-CASH-FUNDING-BALANCE`。

### F-DEBT-BALANCE · 债务本金余额滚动

- 英文全称：Debt principal balance roll-forward；首次释义：债务本金余额滚动（Debt principal balance roll-forward）。
- 最低清单组：10；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
B_{D,y}=B_{D,y-1}+DD_y+IC_y+FC_y-PRN_y-WO_y
$$

- 文本式：`B_D,y = B_D,y−1 + DD_y + IC_y + FC_y − PRN_y − WO_y`
- 输出：`debt.closing_balance`；量纲/单位：元。
- 输入：`debt.opening_balance`, `debt.cash_drawdown`, `debt.capitalized_unpaid_interest`, `debt.capitalized_unpaid_fees`, `debt.principal_paid`, `debt.documented_writeoff`。
- 章节：`CH16`；未来测试：`T-DEBT-BALANCE`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| B_D,y | 期末贷款本金余额 | 元 | `debt.closing_balance` |
| B_D,y−1 | 期初贷款本金余额 | 元 | `debt.opening_balance` |
| DD_y | 实际现金提款 | 元 | `debt.cash_drawdown` |
| IC_y | 按合同资本化转本金但未付现的利息 | 元 | `debt.capitalized_unpaid_interest` |
| FC_y | 按合同转为本金但未付现的融资费用 | 元 | `debt.capitalized_unpaid_fees` |
| PRN_y | 本期实际归还本金 | 元 | `debt.principal_paid` |
| WO_y | 有法律凭据的本金豁免/其他非现金核销，默认不假设存在 | 元 | `debt.documented_writeoff` |

**下标、上标及集合范围：**

- 下标/范围 `D`：债务标签；y−1=期初；IC/FC=转本金的未付现利息/费用，WO=合法核销。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 逐贷款、逐币种、逐合同先算再汇总；本金与应付未资本化利息分账。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 债务余额非负；期末有气球本金或未偿还必须披露，不能默认抹零。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第10组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `B_D,y = B_D,y−1 + DD_y + IC_y + FC_y − PRN_y − WO_y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 累计提款+资本化−还本−核销等于余额；终期未偿、宽限期及分笔融资。

**逐个下标词素：** D=债务本金口径；y=财务或运营年度索引，必须按本条时间定义区分；1=首运营年或扰动后情景 1，具体按完整符号区分。

**术语键：** `TERM-F-DEBT-BALANCE`。

### F-DEBT-INTEREST · 债务利息计提

- 英文全称：Debt interest accrual；首次释义：债务利息计提（Debt interest accrual）。
- 最低清单组：10；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
I_y=\sum_{s\in\mathcal S_y}B_{D,s}i_s\delta_s
$$

- 文本式：`I_y = Σ(s∈S_y) B_D,s × i_s × δ_s`
- 输出：`debt.interest_accrued`；量纲/单位：元。
- 输入：`debt.interest_principal_base`, `debt.annual_interest_rate`, `debt.daycount_year_fraction`, `debt.interest_subperiod_ids`。
- 章节：`CH16`, `CH17`；未来测试：`T-DEBT-INTEREST`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| I_y | 财务年度利息计提额，不必等于付现利息 | 元 | `debt.interest_accrued` |
| B_D,s | 合同计息子期间实际本金基数 | 元 | `debt.interest_principal_base` |
| i_s | 合同该子期间年化利率 | 1/年 | `debt.annual_interest_rate` |
| δ_s | 按合同日计数法计算的年分数 | 年 | `debt.daycount_year_fraction` |
| s | 年内计息子期间索引 | 1 | index_or_constant |
| S_y | 该财务年全部无重叠计息子期间集合 | 集合 | `debt.interest_subperiod_ids` |
| y | 财务年 | 1 | index_or_constant |

**下标、上标及集合范围：**

- 下标/范围 `s∈S_y`：Σ 年内各计息段；D=债务；δ_s=合同年分数，不是小时。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 集合/求和或连乘 `s∈S_y`：Σ 年内各计息段；D=债务；δ_s=合同年分数，不是小时。

**边界与量纲：** 提款/还本/利率变化处切分，利息计提、付现、资本化及应付余额需桥接；不擅自定年初或平均余额。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 日计数、复利/罚息由合同独立评审；本式是分段单利累计。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第10组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `I_y = Σ(s∈S_y) B_D,s × i_s × δ_s`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 合同日计数独立复核，年内提款、利率重置和宽限期不漏息。

**逐个下标词素：** y=财务或运营年度索引，必须按本条时间定义区分；D=债务本金口径；s=计息子期间或命名情景索引，见本条集合。

**术语键：** `TERM-F-DEBT-INTEREST`。

### F-INTEREST-BALANCE · 应付利息平衡

- 英文全称：Interest payable balance；首次释义：应付利息平衡（Interest payable balance）。
- 最低清单组：10；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
IP_y=IP_{y-1}+I_y-INT_y-IC_y
$$

- 文本式：`IP_y = IP_y−1 + I_y − INT_y − IC_y`
- 输出：`debt.interest_payable_closing`；量纲/单位：元。
- 输入：`debt.interest_payable_opening`, `debt.interest_accrued`, `debt.interest_paid`, `debt.capitalized_unpaid_interest`。
- 章节：`CH14`, `CH15`, `CH16`；未来测试：`T-INTEREST-BALANCE`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| IP_y | 期末未付且未资本化的应付利息 | 元 | `debt.interest_payable_closing` |
| IP_y−1 | 期初应付利息 | 元 | `debt.interest_payable_opening` |
| I_y | 本期利息计提 | 元 | `debt.interest_accrued` |
| INT_y | 现金支付利息 | 元 | `debt.interest_paid` |
| IC_y | 转入贷款本金的利息 | 元 | `debt.capitalized_unpaid_interest` |

**下标、上标及集合范围：**

- 下标/范围 `IP`：应付利息；I=计提，INT=付现，IC=转本；y−1=期初。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 同一贷款同一计息期间；资本化利息不能又当付现，再当资本支出重复扣。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 如发生豁免、汇兑、罚息需独立调整节点并版本化，本基础式不能静默吞并。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第10组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `IP_y = IP_y−1 + I_y − INT_y − IC_y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 与借款本金余额和建设期投资估算的三方桥。

**逐个下标词素：** y=财务或运营年度索引，必须按本条时间定义区分；1=首运营年或扰动后情景 1，具体按完整符号区分。

**术语键：** `TERM-F-INTEREST-BALANCE`。

### F-NPV · 同口径净现值

- 英文全称：Net present value；首次释义：同口径净现值（Net present value）。
- 最低清单组：11；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
NPV_b(r_b)=\sum_{y=0}^{N}CF_{b,y}/(1+r_b)^y
$$

- 文本式：`NPV_b = Σ(y=0…N) CF_b,y / (1 + r_b)^y`
- 输出：`finance.npv`；量纲/单位：元。
- 输入：`finance.selected_cash_flow`, `finance.selected_discount_rate`, `finance.cash_flow_basis`, `time.financial_end_year`。
- 章节：`CH01`, `CH16`, `CH17`；未来测试：`T-NPV`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| NPV_b | 口径 b 的年末现金流净现值 | 元 | `finance.npv` |
| CF_b,y | 已选项目税前/税后或股东实际现金流，口径不混合 | 元 | `finance.selected_cash_flow` |
| r_b | 与口径 b 匹配的每年折现率 | 1（每年度有效比例，非连续时间倒数单位） | `finance.selected_discount_rate` |
| b | 项目税前、项目税后、股东实际收付中的一个完整口径标签 | 枚举 | `finance.cash_flow_basis` |
| y | 从基期 0 起的财务年度整数时点 | 1 | index_or_constant |
| N | 最后一个财务年度时点，含建设及终期 | 1 | `time.financial_end_year` |

**下标、上标及集合范围：**

- 下标/范围 `Σ y=0…N`：有限求和含基期与末期；b=唯一口径；y=0 为评价基准日。
- 上标/幂 `y`：距基期的年度步数，用作折现幂指数。
- 集合/求和或连乘 `Σ y=0…N`：有限求和含基期与末期；b=唯一口径；y=0 为评价基准日。

**边界与量纲：** 同币种、同基准日、同税口径和名义/实际价格；多建设年均保留现金流，不把全部投资挤到首运营年。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- r_b > −1；年末假定必须声明；项目 r 不直接代股东 r；缺折现率只可报情景。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第11组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `NPV_b = Σ(y=0…N) CF_b,y / (1 + r_b)^y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 独立折现表核对；r=0 等于总净流；固定其他因素提高投资不应增加 NPV。

**逐个下标词素：** b=互斥的项目/股权及税前后完整口径索引；y=财务或运营年度索引，必须按本条时间定义区分。

**术语键：** `TERM-NPV`。

### F-DATED-NPV · 非整年时点净现值

- 英文全称：Dated net present value；首次释义：非整年时点净现值（Dated net present value）。
- 最低清单组：11；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
NPV_b=\sum_{k\in\mathcal C}CF_{b,k}/(1+r_b)^{\tau_k}
$$

- 文本式：`NPV_b = Σ(k∈C) CF_b,k / (1 + r_b)^τ_k`
- 输出：`finance.dated_npv`；量纲/单位：元。
- 输入：`finance.dated_cash_flows`, `finance.selected_discount_rate`, `finance.cash_event_year_fraction`, `finance.cash_event_ids`, `finance.cash_flow_basis`。
- 章节：`CH16`；未来测试：`T-DATED-NPV`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| NPV_b | 按实际支付时点折现的净现值 | 元 | `finance.dated_npv` |
| CF_b,k | 第 k 个实际现金事件的金额 | 元 | `finance.dated_cash_flows` |
| r_b | 同口径年化折现率 | 1（每年度有效比例，非连续时间倒数单位） | `finance.selected_discount_rate` |
| τ_k | 事件日至基准日的合同年分数，可为非整数 | 年/年 | `finance.cash_event_year_fraction` |
| k | 现金事件索引 | 1 | index_or_constant |
| C | 完整评价现金事件集合，含基期和终期 | 集合 | `finance.cash_event_ids` |
| b | 唯一现金流口径 | 枚举 | `finance.cash_flow_basis` |

**下标、上标及集合范围：**

- 下标/范围 `k∈C`：Σ 遍历所有现金事件，不漏基期；τ_k 为按明确日计数规则计算的无量纲年分数。
- 上标/幂 `τ_k`：年化折现指数；具体日计数与日历基准为输入方法参数。
- 集合/求和或连乘 `k∈C`：Σ 遍历所有现金事件，不漏基期；τ_k 为按明确日计数规则计算的无量纲年分数。

**边界与量纲：** 建设跨年、分期出资优先采用；日计数采用的年分数规则须写入方法版本，不默认日历除数。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- τ 的计算基准所有事件一致；r>−1；不能和年末 NPV 无说明比较。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第11组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `NPV_b = Σ(k∈C) CF_b,k / (1 + r_b)^τ_k`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 与事件级独立折现表核对，同年末事件退化为年度 NPV。

**逐个下标词素：** b=互斥的项目/股权及税前后完整口径索引；k=损失/费用类别或现金事件索引，见本条集合。

**术语键：** `TERM-F-DATED-NPV`, `TERM-NPV`。

### F-NOMINAL-REAL-RATE · 名义与实际折现率桥

- 英文全称：Nominal-real discount rate relation；首次释义：名义与实际折现率桥（Nominal-real discount rate relation）。
- 最低清单组：11；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
1+r_{nom}=(1+r_{real})(1+\pi)
$$

- 文本式：`r_nom = (1 + r_real) × (1 + π) − 1`
- 输出：`finance.nominal_discount_rate`；量纲/单位：1/年。
- 输入：`finance.real_discount_rate`, `finance.general_inflation`。
- 章节：`CH15`, `CH16`；未来测试：`T-NOMINAL-REAL-RATE`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| r_nom | 名义年折现率 | 1（每年度有效比例，非连续时间倒数单位） | `finance.nominal_discount_rate` |
| r_real | 不含一般通胀的实际年折现率 | 1（每年度有效比例，非连续时间倒数单位） | `finance.real_discount_rate` |
| π | 与币种和评价期对应的一般年通胀率假设 | 1（每年度有效比例，非连续时间倒数单位） | `finance.general_inflation` |

**下标、上标及集合范围：**

- 下标/范围 `nom`：名义；real=实际；π 为同年度步长通胀。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 仅作同一税/风险/币种口径下的通胀转换；不能拿资产特定电价变化替代一般通胀。 输出单位为 1/年；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 各率均大于 −1；变动通胀需分期转换；不声称市场真实折现率。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第11组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `r_nom = (1 + r_real) × (1 + π) − 1`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 名义现金流与实际现金流折现一致性，避免名义费用配实际利率。

**逐个下标词素：** nom=名义币值/名义折现率；real=实际购买力价格/折现率。

**术语键：** `TERM-F-NOMINAL-REAL-RATE`。

### F-IRR-PROJECT · 项目投资内部收益率根集

- 英文全称：Project investment IRR root set；首次释义：项目投资内部收益率根集（Project investment IRR root set）。
- 最低清单组：12；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
\mathcal R_P=\{r\in\mathcal D:\sum_{y=0}^{N}CF_{P,y}(1+r)^{-y}=0\}
$$

- 文本式：`R_P = {r∈D : Σ(y=0…N) CF_P,y/(1+r)^y = 0}`
- 输出：`finance.project_irr_root_set`；量纲/单位：集合（元素为每年比例）。
- 输入：`finance.irr_search_domain`, `finance.project_irr_cash_flow`, `time.financial_end_year`。
- 章节：`CH01`, `CH16`, `CH17`；未来测试：`T-IRR-PROJECT`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| R_P | 项目投资 IRR 的全部可识别实根集合，不是任意单根百分比 | 集合 | `finance.project_irr_root_set` |
| r | 待求每年收益率 | 1（每年度有效比例，非连续时间倒数单位） | index_or_constant |
| D | 事前声明的实数搜索域，必须位于 r>−1；域外根不声称不存在 | 集合 | `finance.irr_search_domain` |
| CF_P,y | 同口径项目投资无杠杆现金流，明确税前或税后，不含融资 | 元 | `finance.project_irr_cash_flow` |
| y | 财务年度时点 | 1 | index_or_constant |
| N | 最后评价时点 | 1 | `time.financial_end_year` |

**下标、上标及集合范围：**

- 下标/范围 `Σ y=0…N`：对基期到终期项目流求和；P=无杠杆项目。
- 下标/范围 `r∈D`：集合构造：所有使 NPV 为零的域内实率；集合可能为空/单根/多根/连续。
- 上标/幂 `−y`：年末折现的负幂；r>−1 保持实数折现意义。
- 集合/求和或连乘 `Σ y=0…N`：对基期到终期项目流求和；P=无杠杆项目。
- 集合/求和或连乘 `r∈D`：集合构造：所有使 NPV 为零的域内实率；集合可能为空/单根/多根/连续。

**边界与量纲：** 无债务流；税前与税后分别调用并分别输出，不以同字段覆盖；非整年时点改用同口径 dated-NPV 求根版本。 输出单位为 集合（元素为每年比例）；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 未来算法必须报告域、区间隔离、收敛容差、根数和未穷尽标识；不能只跑一次局部求根。
- 无正负符号变化（除全零）报 NO_SIGN_CHANGE；全零报 INDETERMINATE；无根报 NO_ROOT；多根报 MULTIPLE_ROOTS；唯一根才返回数值，且注明域内唯一/是否全域证明。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第12组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `R_P = {r∈D : Σ(y=0…N) CF_P,y/(1+r)^y = 0}`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 独立多项式或高精度参考；无根、多根、重根、全零、不收敛、负合法 IRR 和域外根 PLANNED。

**逐个下标词素：** P=项目无杠杆口径；y=财务或运营年度索引，必须按本条时间定义区分。

**术语键：** `TERM-F-IRR-PROJECT`, `TERM-IRR`。

### F-IRR-EQUITY · 资本金内部收益率根集

- 英文全称：Equity investor IRR root set；首次释义：资本金内部收益率根集（Equity investor IRR root set）。
- 最低清单组：12；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
\mathcal R_E=\{r\in\mathcal D:\sum_{y=0}^{N}CF_{E,y}(1+r)^{-y}=0\}
$$

- 文本式：`R_E = {r∈D : Σ(y=0…N) CF_E,y/(1+r)^y = 0}`
- 输出：`finance.equity_irr_root_set`；量纲/单位：集合（元素为每年比例）。
- 输入：`finance.irr_search_domain`, `finance.equity_investor_cash_flow`, `time.financial_end_year`。
- 章节：`CH01`, `CH16`, `CH17`；未来测试：`T-IRR-EQUITY`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| R_E | 投资者资本金 IRR 实根集合 | 集合 | `finance.equity_irr_root_set` |
| r | 待求年化股权收益率 | 1（每年度有效比例，非连续时间倒数单位） | index_or_constant |
| D | 事前声明并记录的 r>−1 实数搜索域 | 集合 | `finance.irr_search_domain` |
| CF_E,y | 真实股东出资为负、分配和退出为正的投资者现金流 | 元 | `finance.equity_investor_cash_flow` |
| y | 财务时点 | 1 | index_or_constant |
| N | 终期评价时点 | 1 | `time.financial_end_year` |

**下标、上标及集合范围：**

- 下标/范围 `Σ y=0…N`：股东全部真实/计划收付时点；E=股东口径。
- 下标/范围 `r∈D`：域内全部满足 NPV=0 的实率构成集合。
- 上标/幂 `−y`：折现负幂。
- 集合/求和或连乘 `Σ y=0…N`：股东全部真实/计划收付时点；E=股东口径。
- 集合/求和或连乘 `r∈D`：域内全部满足 NPV=0 的实率构成集合。

**边界与量纲：** 必须计融资及分红限制，不能用项目现金流或单纯会计利润代替；日期不齐改 dated-NPV。 输出单位为 集合（元素为每年比例）；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 与项目 IRR 使用完全相同的无根/多根/全零/未收敛状态规则；资本金为零不能虚构无限回报。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第12组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `R_E = {r∈D : Σ(y=0…N) CF_E,y/(1+r)^y = 0}`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 独立参考验证；融资比例改变可影响股权但不应改变无杠杆项目 IRR；多次追加可能产生多根。

**逐个下标词素：** E=股权/融资主体口径，ε_E 则标能量残差；y=财务或运营年度索引，必须按本条时间定义区分。

**术语键：** `TERM-F-IRR-EQUITY`, `TERM-IRR`。

### F-CUMULATIVE-CASH-FLOW · 静态累计现金流

- 英文全称：Undiscounted cumulative cash flow；首次释义：静态累计现金流（Undiscounted cumulative cash flow）。
- 最低清单组：13；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
A_{b,n}=\sum_{y=0}^{n}CF_{b,y}
$$

- 文本式：`A_b,n = Σ(y=0…n) CF_b,y`
- 输出：`finance.cumulative_cash_flow`；量纲/单位：元。
- 输入：`finance.selected_cash_flow`, `time.cumulative_end_year`, `finance.cash_flow_basis`。
- 章节：`CH01`, `CH16`；未来测试：`T-CUMULATIVE-CASH-FLOW`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| A_b,n | 截至时点 n 的未折现累计净现金流 | 元 | `finance.cumulative_cash_flow` |
| CF_b,y | 同一口径各期净现金流 | 元 | `finance.selected_cash_flow` |
| y | 自基期起财务年度时点 | 1 | index_or_constant |
| n | 被评估的累计终点，0…N | 1 | `time.cumulative_end_year` |
| b | 项目/股权及税前后唯一口径 | 枚举 | `finance.cash_flow_basis` |

**下标、上标及集合范围：**

- 下标/范围 `Σ y=0…n`：含基期至累计终点 n；A 为累计值标签。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 集合/求和或连乘 `Σ y=0…n`：含基期至累计终点 n；A 为累计值标签。

**边界与量纲：** 从首次纳入评价的建设出资基期起算，不从投产时重置亏损；如使用运营回收期必须另标起点。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 未知现金流不参与确定回收期；基期无负投入需返回 NOT_APPLICABLE 或说明即时回收。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第13组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `A_b,n = Σ(y=0…n) CF_b,y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 独立累计表；后期替换再次转负要另披露，不能以首次回收掩盖。

**逐个下标词素：** b=互斥的项目/股权及税前后完整口径索引；n=累计终点或首次回收年度索引；y=财务或运营年度索引，必须按本条时间定义区分。

**术语键：** `TERM-F-CUMULATIVE-CASH-FLOW`。

### F-STATIC-PAYBACK · 静态首次回收期

- 英文全称：Static first payback period；首次释义：静态首次回收期（Static first payback period）。
- 最低清单组：13；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
PB_{static,b}=n-1+\frac{-A_{b,n-1}}{CF_{b,n}}
$$

- 文本式：`PB_static,b = n − 1 + (−A_b,n−1) / CF_b,n`
- 输出：`finance.static_payback_years`；量纲/单位：年。
- 输入：`finance.first_recovery_year`, `finance.pre_recovery_cumulative_cash`, `finance.recovery_year_cash_flow`, `finance.cash_flow_basis`, `time.financial_end_year`。
- 章节：`CH01`, `CH16`；未来测试：`T-STATIC-PAYBACK`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| PB_static,b | 自评价基期起静态首次回收的年数 | 年 | `finance.static_payback_years` |
| n | 第一个使累计净流由负转非负的年度终点 | 1 | `finance.first_recovery_year` |
| A_b,n−1 | 此前一年末负累计净现金流 | 元 | `finance.pre_recovery_cumulative_cash` |
| CF_b,n | 首次回收年度的正净现金流 | 元 | `finance.recovery_year_cash_flow` |
| b | 项目/股权唯一口径 | 枚举 | `finance.cash_flow_basis` |
| N | 评价期最后一个财务年度时点，限制首次交叉搜索范围 | 1 | `time.financial_end_year` |

**下标、上标及集合范围：**

- 下标/范围 `n`：在 {1,…,N} 内满足首次负转非负的最小年度索引；static=未折现。
- 下标/范围 `范围`：N 是评价末期，查找过程必须涵盖全部现金流，N 见时间字段 time.financial_end_year。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 集合/求和或连乘 `范围`：N 是评价末期，查找过程必须涵盖全部现金流，N 见时间字段 time.financial_end_year。

**边界与量纲：** 仅当 n≥1、A_(n−1)<0、A_n≥0、CF_n>0；区间内线性流入是假设而非真实日期。 输出单位为 年；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 查全部评价期无满足条件则 NOT_RECOVERED_WITHIN_HORIZON，展示期内未回收；分母零不插值。
- 非整年现金事件优先日期级回收；回收后再负需风险披露。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第13组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `PB_static,b = n − 1 + (−A_b,n−1) / CF_b,n`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 首次交叉而非最后交叉、期内未回收、精确整年回收、基期为零和建设多期。

**逐个下标词素：** static=未折现回收期；b=互斥的项目/股权及税前后完整口径索引；n=累计终点或首次回收年度索引；1=首运营年或扰动后情景 1，具体按完整符号区分。

**术语键：** `TERM-F-STATIC-PAYBACK`。

### F-DISCOUNTED-CUMULATIVE-CASH · 动态累计现金流

- 英文全称：Discounted cumulative cash flow；首次释义：动态累计现金流（Discounted cumulative cash flow）。
- 最低清单组：13；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
A^d_{b,n}=\sum_{y=0}^{n}CF_{b,y}/(1+r_b)^y
$$

- 文本式：`A_disc,b,n = Σ(y=0…n) CF_b,y / (1+r_b)^y`
- 输出：`finance.discounted_cumulative_cash`；量纲/单位：元。
- 输入：`finance.selected_cash_flow`, `finance.selected_discount_rate`, `time.cumulative_end_year`, `finance.cash_flow_basis`。
- 章节：`CH16`；未来测试：`T-DISCOUNTED-CUMULATIVE-CASH`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| A_disc,b,n | 截至 n 的折现累计净现金流 | 元 | `finance.discounted_cumulative_cash` |
| CF_b,y | 同口径财务净现金流 | 元 | `finance.selected_cash_flow` |
| r_b | 同口径年度折现率 | 1（每年度有效比例，非连续时间倒数单位） | `finance.selected_discount_rate` |
| y | 财务年度时点 | 1 | index_or_constant |
| n | 累计终点索引 | 1 | `time.cumulative_end_year` |
| b | 唯一现金流口径 | 枚举 | `finance.cash_flow_basis` |

**下标、上标及集合范围：**

- 下标/范围 `Σ y=0…n`：从基期到累计终点全部年度流求和。
- 上标/幂 `d`：仅是 discounted 折现标签，不是幂。
- 上标/幂 `y`：(1+r_b) 的年度折现幂。
- 集合/求和或连乘 `Σ y=0…n`：从基期到累计终点全部年度流求和。

**边界与量纲：** 与 NPV 同基准日、同年末假设；不能静态累计配动态年度流。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- r>−1；日期级模型另用年分数。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第13组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `A_disc,b,n = Σ(y=0…n) CF_b,y / (1+r_b)^y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 末期累计等于 NPV；零折现率退化为静态累计。

**逐个下标词素：** disc=已经折现的累计值；b=互斥的项目/股权及税前后完整口径索引；n=累计终点或首次回收年度索引；y=财务或运营年度索引，必须按本条时间定义区分。

**术语键：** `TERM-F-DISCOUNTED-CUMULATIVE-CASH`。

### F-DYNAMIC-PAYBACK · 动态首次回收期

- 英文全称：Discounted first payback period；首次释义：动态首次回收期（Discounted first payback period）。
- 最低清单组：13；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
PB_{dynamic,b}=n-1+\frac{-A^d_{b,n-1}}{CF_{b,n}/(1+r_b)^n}
$$

- 文本式：`PB_dynamic,b = n − 1 + (−A_disc,b,n−1)/(CF_b,n/(1+r_b)^n)`
- 输出：`finance.dynamic_payback_years`；量纲/单位：年。
- 输入：`finance.first_discounted_recovery_year`, `finance.pre_discounted_recovery_cumulative`, `finance.discounted_recovery_year_cash_flow`, `finance.selected_discount_rate`, `finance.cash_flow_basis`, `time.financial_end_year`。
- 章节：`CH01`, `CH16`；未来测试：`T-DYNAMIC-PAYBACK`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| PB_dynamic,b | 自基期起动态首次回收期 | 年 | `finance.dynamic_payback_years` |
| n | 折现累计首次负转非负的年度终点 | 1 | `finance.first_discounted_recovery_year` |
| A_disc,b,n−1 | 前一年末负折现累计净流 | 元 | `finance.pre_discounted_recovery_cumulative` |
| CF_b,n | 回收年度未折现净现金流 | 元 | `finance.discounted_recovery_year_cash_flow` |
| r_b | 同口径年折现率 | 1（每年度有效比例，非连续时间倒数单位） | `finance.selected_discount_rate` |
| b | 唯一现金流口径 | 枚举 | `finance.cash_flow_basis` |
| N | 评价期最后一个财务年度时点，限制首次交叉搜索范围 | 1 | `time.financial_end_year` |

**下标、上标及集合范围：**

- 下标/范围 `n`：范围 1…N 中折现累计首次负转非负最小索引；N 为已定义的评价末期。
- 上标/幂 `d`：折现标签，非乘方。
- 上标/幂 `n`：对本年度净流的折现幂。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 与静态回收期同起点；线性插值基于年度折现值，只是近似，不代表精确日历回收日。 输出单位为 年；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 前期累计<0、本年折现净流>0；未交叉返回期内未回收。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第13组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `PB_dynamic,b = n − 1 + (−A_disc,b,n−1)/(CF_b,n/(1+r_b)^n)`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 零折现率一致、正折现下常规现金流动态不早于静态（限常规边界），再负风险披露。

**逐个下标词素：** dynamic=折现回收期；b=互斥的项目/股权及税前后完整口径索引；disc=已经折现的累计值；n=累计终点或首次回收年度索引；1=首运营年或扰动后情景 1，具体按完整符号区分。

**术语键：** `TERM-F-DYNAMIC-PAYBACK`。

### F-LIFECYCLE-COST · 无杠杆生命周期净成本

- 英文全称：Unlevered lifecycle net cost；首次释义：无杠杆生命周期净成本（Unlevered lifecycle net cost）。
- 最低清单组：14；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
Cost_{P,y}=K_{P,y}+O_y+T_{cost,P,y}+\Delta W_{P,y}-S_{P,y}-SUB_{P,y}
$$

- 文本式：`Cost_P,y = K_P,y + O_y + T_cost,P,y + ΔW_P,y − S_P,y − SUB_P,y`
- 输出：`lcoe.project_cost_annual`；量纲/单位：元。
- 输入：`capex.unlevered_cash_annual`, `opex.cash_annual`, `lcoe.cost_taxes`, `working_capital.project_net_change`, `finance.project_terminal_cash`, `lcoe.cost_subsidy_offset`。
- 章节：`CH14`, `CH15`, `CH16`；未来测试：`T-LIFECYCLE-COST`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| Cost_P,y | 选定税费/补贴边界的项目生命周期净成本 | 元 | `lcoe.project_cost_annual` |
| K_P,y | 无杠杆工程及资本更换现金支出 | 元 | `capex.unlevered_cash_annual` |
| O_y | 现金运营支出，不含折旧 | 元 | `opex.cash_annual` |
| T_cost,P,y | 选定成本税费，税前 LCOE 不含所得税；税后模型需独立收入税基 | 元 | `lcoe.cost_taxes` |
| ΔW_P,y | 未重计的营运资金净增 | 元 | `working_capital.project_net_change` |
| S_P,y | 净残值回收及未在 ΔW 中回收的营运资金 | 元 | `finance.project_terminal_cash` |
| SUB_P,y | 明确选择为成本抵减且未计收入的有依据补贴 | 元 | `lcoe.cost_subsidy_offset` |

**下标、上标及集合范围：**

- 下标/范围 `P`：无杠杆项目；y=建设至退出时点；cost=成本税费，SUB=补贴抵减。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 默认方法冻结为项目无杠杆税前所得税 LCOE，保留适用其他税；融资本息不混入再用含融资成本折现率双计；补贴抵成本/收益二选一。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 不扣正常售电收入或自用节省，否则变成净收益指标而非度电成本。
- 如需股权/融资后/税后 LCOE 必须另建命名方法，冻结成本范围并处理税基与电价循环，不能直接沿用本字段。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第14组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `Cost_P,y = K_P,y + O_y + T_cost,P,y + ΔW_P,y − S_P,y − SUB_P,y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 逐项成本表对 CAPEX/OPEX/残值；折旧不作为付现成本；补贴不重记。

**逐个下标词素：** P=项目无杠杆口径；y=财务或运营年度索引，必须按本条时间定义区分；cost=LCOE 成本范围。

**术语键：** `TERM-F-LIFECYCLE-COST`。

### F-LCOE · 平准化度电成本

- 英文全称：Levelized cost of energy；首次释义：平准化度电成本（Levelized cost of energy）。
- 最低清单组：14；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
LCOE=\frac{\sum_{y=0}^{N}Cost_{P,y}/(1+r_L)^y}{\sum_{y=0}^{N}E_{delivered,y}/(1+r_L)^y}
$$

- 文本式：`LCOE = Σ(y=0…N) Cost_P,y/(1+r_L)^y / Σ(y=0…N) E_delivered,y/(1+r_L)^y`
- 输出：`finance.lcoe`；量纲/单位：元/kWh。
- 输入：`lcoe.project_cost_annual`, `energy.delivered_annual_kwh`, `lcoe.discount_rate`, `time.financial_end_year`。
- 章节：`CH01`, `CH16`；未来测试：`T-LCOE`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| LCOE | 声明成本与交付边界的平准化度电成本 | 元/kWh | `finance.lcoe` |
| Cost_P,y | 本条选定无杠杆税前所得税生命周期净成本 | 元 | `lcoe.project_cost_annual` |
| E_delivered,y | 同项目计量点可利用交付电量，建设无发电期显式为零 | kWh | `energy.delivered_annual_kwh` |
| r_L | 与成本币种/名义实际口径相容的 LCOE 年折现率 | 1（每年度有效比例，非连续时间倒数单位） | `lcoe.discount_rate` |
| y | 建设基期至退出的财务年度时点 | 1 | index_or_constant |
| N | 末期评价年度 | 1 | `time.financial_end_year` |

**下标、上标及集合范围：**

- 下标/范围 `Σ y=0…N`：分子分母分别对全部财务年求和；L=度电成本折现率标签。
- 上标/幂 `y`：距基期年度步数。
- 集合/求和或连乘 `Σ y=0…N`：分子分母分别对全部财务年求和；L=度电成本折现率标签。

**边界与量纲：** 分子/分母同年、同期间、同项目边界；弃光不算交付；按售电量计则成本必须切换为同售电边界。 输出单位为 元/kWh；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 折现交付量>0 否则 ZERO_DELIVERY，不返回零/无穷假数值；成本定义写入方法版本，公开对标需同口径。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第14组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `LCOE = Σ(y=0…N) Cost_P,y/(1+r_L)^y / Σ(y=0…N) E_delivered,y/(1+r_L)^y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 独立折现成本/电量表复核；零电量、设备更换和残值；电量下降不应在其他条件不变时降低 LCOE。

**逐个下标词素：** P=项目无杠杆口径；y=财务或运营年度索引，必须按本条时间定义区分；delivered=同计量点可利用交付量，不含弃光；L=度电成本折现口径。

**术语键：** `TERM-LCOE`。

### F-CFADS · 可用于偿债的现金流

- 英文全称：Cash flow available for debt service；首次释义：可用于偿债的现金流（Cash flow available for debt service）。
- 最低清单组：15；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
CFADS_y=B_{op,y}-O_y-T_{E,y}-\Delta W_{ds,y}-K_{mand,y}+A_{ds,y}
$$

- 文本式：`CFADS_y = B_op,y − O_y − T_E,y − ΔW_ds,y − K_mand,y + A_ds,y`
- 输出：`debt.cfads`；量纲/单位：元。
- 输入：`finance.project_operating_cash_benefit`, `opex.cash_annual`, `tax.equity_cash_total`, `debt.cfads_working_capital_change`, `debt.cfads_mandatory_capex`, `debt.cfads_adjustments`。
- 章节：`CH16`；未来测试：`T-CFADS`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| CFADS_y | 按融资协议可用于偿债的当期现金流 | 元 | `debt.cfads` |
| B_op,y | 经营现金利益，不含融资 | 元 | `finance.project_operating_cash_benefit` |
| O_y | 协议口径现金运营支出 | 元 | `opex.cash_annual` |
| T_E,y | 协议口径实际现金税，不重复税价桥 | 元 | `tax.equity_cash_total` |
| ΔW_ds,y | 协议要求的未重计营运资金或储备净增 | 元 | `debt.cfads_working_capital_change` |
| K_mand,y | 协议要求在偿债前扣除的维护性资本开支 | 元 | `debt.cfads_mandatory_capex` |
| A_ds,y | 有合同依据的其他 CFADS 调整，可正可负 | 元 | `debt.cfads_adjustments` |

**下标、上标及集合范围：**

- 下标/范围 `y`：与债务应付服务完全同周期；ds=偿债协议调整；mand=强制维护资本支出。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 债务服务前现金；不得在分子再扣同笔利息本金，也不把提款、股东出资当经营偿债能力。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 协议尚缺则只能显式情景；融资后现金税含合法利息税盾，不等于重复扣利息本身。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第15组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `CFADS_y = B_op,y − O_y − T_E,y − ΔW_ds,y − K_mand,y + A_ds,y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 与融资协议定义逐项核对；经营流→CFADS→本息→股权余缺现金瀑布。

**逐个下标词素：** y=财务或运营年度索引，必须按本条时间定义区分；op=运营经营利益；E=股权/融资主体口径，ε_E 则标能量残差；ds=融资协议偿债现金口径；mand=协议要求优先扣除的维护性资本支出。

**术语键：** `TERM-CFADS`。

### F-DEBT-SERVICE · 应付债务服务

- 英文全称：Scheduled debt service；首次释义：应付债务服务（Scheduled debt service）。
- 最低清单组：15；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
DS_y=PRN_{due,y}+INT_{due,y}+F_{due,y}
$$

- 文本式：`DS_y = PRN_due,y + INT_due,y + F_due,y`
- 输出：`debt.service_due`；量纲/单位：元。
- 输入：`debt.principal_due`, `debt.interest_due`, `debt.service_fees_due`。
- 章节：`CH16`；未来测试：`T-DEBT-SERVICE`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| DS_y | 当期合同应还的债务服务，而非因拖欠变少的实际支付 | 元 | `debt.service_due` |
| PRN_due,y | 本期应还本金 | 元 | `debt.principal_due` |
| INT_due,y | 本期应付利息 | 元 | `debt.interest_due` |
| F_due,y | 融资协议纳入服务口径的应付费用 | 元 | `debt.service_fees_due` |

**下标、上标及集合范围：**

- 下标/范围 `due`：本期合同应付，不是 paid 实付；y=债务服务期。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** DSCR 用应付口径；现金流用实付口径，逾期二者差异单独披露；不同债务协议先独立。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 资本化利息若协议不要求当期付现，不自动纳入服务；合同优先。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第15组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `DS_y = PRN_due,y + INT_due,y + F_due,y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 到期本息计划与余额回勾，应付/实付分开以避免违约反而提高 DSCR。

**逐个下标词素：** y=财务或运营年度索引，必须按本条时间定义区分；due=合同当期应付，不是实际已付。

**术语键：** `TERM-F-DEBT-SERVICE`。

### F-DSCR · 偿债备付率

- 英文全称：Debt service coverage ratio；首次释义：偿债备付率（Debt service coverage ratio）。
- 最低清单组：15；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
DSCR_y=CFADS_y/DS_y
$$

- 文本式：`DSCR_y = CFADS_y / DS_y`
- 输出：`debt.dscr`；量纲/单位：1。
- 输入：`debt.cfads`, `debt.service_due`。
- 章节：`CH01`, `CH16`, `CH17`；未来测试：`T-DSCR`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| DSCR_y | 当期可供偿债现金除以合同债务服务 | 1 | `debt.dscr` |
| CFADS_y | 同周期协议口径可用于偿债现金 | 元 | `debt.cfads` |
| DS_y | 同周期合同应付本金、利息及协议费用合计 | 元 | `debt.service_due` |

**下标、上标及集合范围：**

- 下标/范围 `y`：与服务完全相同周期；DS=应付债务服务；DSCR=比值。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 无融资返回 NOT_APPLICABLE；存在债务但宽限期服务为零返回 ZERO_DEBT_SERVICE 不输出无限或伪造数值。 输出单位为 1；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- CFADS 可负且应如实反映；最小 DSCR 只对 DS>0 期间求，不用无效期覆盖。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第15组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `DSCR_y = CFADS_y / DS_y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 无融资/零服务/负 CFADS/气球本金/应付实付差异均 PLANNED；合同门槛不臆造。

**逐个下标词素：** y=财务或运营年度索引，必须按本条时间定义区分。

**术语键：** `TERM-DSCR`。

### F-BREAK-EVEN-PRICE · 净现值为零的盈亏平衡电价

- 英文全称：NPV break-even tariff；首次释义：净现值为零的盈亏平衡电价（NPV break-even tariff）。
- 最低清单组：16；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
\mathcal P^*=\{p\in\mathcal P:NPV_b(CF_b(p),r_b)=0\}
$$

- 文本式：`P_star = {p∈P : NPV_b(CF_b(p), r_b) = 0}`
- 输出：`sensitivity.break_even_price_roots`；量纲/单位：集合（元素元/kWh）。
- 输入：`sensitivity.price_search_domain`, `finance.npv`, `sensitivity.price_cash_flow_vector`, `finance.selected_discount_rate`, `finance.cash_flow_basis`。
- 章节：`CH16`, `CH17`；未来测试：`T-BREAK-EVEN-PRICE`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| P_star | 满足 NPV=0 的电价根集合 | 集合 | `sensitivity.break_even_price_roots` |
| p | 待求结算电价，只调整预先指定的电价项 | 元/kWh | index_or_constant |
| P | 有业务依据且事前声明的允许电价域，可含合法负价 | 集合 | `sensitivity.price_search_domain` |
| NPV_b | 同一税/融资口径的净现值函数 | 元 | `finance.npv` |
| CF_b(p) | 固定其他外生输入、电价为 p 时完整重算的现金流向量 | 元/期 | `sensitivity.price_cash_flow_vector` |
| r_b | 同一口径折现率 | 1（每年度有效比例，非连续时间倒数单位） | `finance.selected_discount_rate` |
| b | 项目或股权的唯一口径 | 枚举 | `finance.cash_flow_basis` |

**下标、上标及集合范围：**

- 下标/范围 `p∈P`：域内全部使 NPV=0 的电价构成集合。
- 上标/幂 `*`：盈亏平衡候选根集合标签，不是乘方。
- 集合/求和或连乘 `p∈P`：域内全部使 NPV=0 的电价构成集合。

**边界与量纲：** 冻结“使 NPV=0”的定义，不混称会计利润盈亏平衡；分时电价可对指定倍率求根但需新输出字段。 输出单位为 集合（元素元/kWh）；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 税/消纳/债务约束可能非线性；价格域内无根、多根、未收敛、零交付返回明确原因；不能改现实成本迎合目标。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第16组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `P_star = {p∈P : NPV_b(CF_b(p), r_b) = 0}`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 单调线性特例独立代数、税盾分段、多根和域约束；替代全部收入电价不合法。

**逐个下标词素：** star=盈亏平衡根集合标签，相当于上标 *，不是乘方；b=互斥的项目/股权及税前后完整口径索引；p=月/年汇总期间索引。

**术语键：** `TERM-F-BREAK-EVEN-PRICE`。

### F-SINGLE-FACTOR-SENSITIVITY · 单因素绝对与相对敏感性

- 英文全称：One-factor absolute and relative sensitivity；首次释义：单因素绝对与相对敏感性（One-factor absolute and relative sensitivity）。
- 最低清单组：16；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
\Delta M_x=M(x_0+\Delta x;z_0)-M(x_0;z_0)
$$

- 文本式：`ΔM_x = M(x_0 + Δx; z_0) − M(x_0; z_0)`
- 输出：`sensitivity.metric_absolute_change`；量纲/单位：与 M 同单位。
- 输入：`sensitivity.metric_definition`, `sensitivity.factor_base_value`, `sensitivity.factor_delta`, `sensitivity.frozen_other_inputs`。
- 章节：`CH17`；未来测试：`T-SINGLE-FACTOR-SENSITIVITY`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| ΔM_x | 仅扰动 x 后指标 M 的绝对变化 | 与 M 同单位 | `sensitivity.metric_absolute_change` |
| M | 完整模型输出函数，只能返回有效数值指标 | 元或比例或年或元/kWh | `sensitivity.metric_definition` |
| x_0 | 该因素基准输入 | 该因素原单位 | `sensitivity.factor_base_value` |
| Δx | 单因素扰动额，非伪造真实输入 | 该因素原单位 | `sensitivity.factor_delta` |
| z_0 | 其余外生输入冻结的完整基准向量 | 混合单位逐字段 | `sensitivity.frozen_other_inputs` |

**下标、上标及集合范围：**

- 下标/范围 `x`：唯一扰动因素标签；0=基准情景；z=其余外生输入；Δ=扰动或差值。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** CAPEX、电价、发电量、可利用率、自用率、限发、OPEX、利率分别列情景，所有内生税/债务/现金流需重算。 输出单位为 与 M 同单位；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 自用率有物理负荷约束，不能独立改比率且不守恒；无真实负荷则仅显式假设情景。
- NPV 与 IRR 等指标可选；IRR 无根/多根不作数值差分。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第16组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `ΔM_x = M(x_0 + Δx; z_0) − M(x_0; z_0)`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 固定其他外生量的变形测试；不将结果目标当输入调优现实参数。

**逐个下标词素：** x=被扰动的唯一因素；0=基准情景或财务基期 0，具体按完整符号区分。

**术语键：** `TERM-F-SINGLE-FACTOR-SENSITIVITY`。

### F-SENSITIVITY-ELASTICITY · 归一化敏感性系数

- 英文全称：Normalized sensitivity elasticity；首次释义：归一化敏感性系数（Normalized sensitivity elasticity）。
- 最低清单组：16；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
S_{M,x}=\frac{(M_1-M_0)/M_0}{(x_1-x_0)/x_0}
$$

- 文本式：`S_M,x = ((M_1−M_0)/M_0) / ((x_1−x_0)/x_0)`
- 输出：`sensitivity.elasticity`；量纲/单位：1。
- 输入：`sensitivity.metric_base`, `sensitivity.metric_perturbed`, `sensitivity.factor_base_value`, `sensitivity.factor_perturbed_value`。
- 章节：`CH17`；未来测试：`T-SENSITIVITY-ELASTICITY`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| S_M,x | 基准归一化敏感性系数 | 1 | `sensitivity.elasticity` |
| M_0 | 基准有效指标值 | 指标原单位 | `sensitivity.metric_base` |
| M_1 | 扰动后有效指标值 | 指标原单位 | `sensitivity.metric_perturbed` |
| x_0 | 基准因素值 | 因素原单位 | `sensitivity.factor_base_value` |
| x_1 | 扰动因素值 | 因素原单位 | `sensitivity.factor_perturbed_value` |

**下标、上标及集合范围：**

- 下标/范围 `0`：基准；1=扰动后；M=目标指标；x=唯一因素。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 仅适用于 M_0≠0、x_0≠0、x_1≠x_0；基准 NPV 为零时应报 UNDEFINED 并展示绝对变化，不做夸大比率。 输出单位为 1；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 报告差分区间和单侧/双侧方法；非线性系数仅局部，不能当全域导数。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第16组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `S_M,x = ((M_1−M_0)/M_0) / ((x_1−x_0)/x_0)`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 零基准/零扰动、负基准符号及不同扰动幅度；与单因素结果回勾。

**逐个下标词素：** M=所考察财务/技术指标；x=被扰动的唯一因素；0=基准情景或财务基期 0，具体按完整符号区分；1=首运营年或扰动后情景 1，具体按完整符号区分。

**术语键：** `TERM-F-SENSITIVITY-ELASTICITY`。

### F-SCENARIO-METRIC · 联合情景全模型重算

- 英文全称：Joint scenario model recalculation；首次释义：联合情景全模型重算（Joint scenario model recalculation）。
- 最低清单组：16；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
M_s=f(x_s,z_s)
$$

- 文本式：`M_s = f(x_s, z_s)`
- 输出：`sensitivity.scenario_metrics`；量纲/单位：逐指标原单位。
- 输入：`model.selected_method_version`, `sensitivity.scenario_inputs`, `sensitivity.scenario_fixed_inputs`, `sensitivity.scenario_id`。
- 章节：`CH06`, `CH17`, `CH18`；未来测试：`T-SCENARIO-METRIC`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| M_s | 情景 s 的完整有效指标向量 | 逐指标原单位 | `sensitivity.scenario_metrics` |
| f | 已版本化确定性完整计算模型映射，不是生成式数值 | 函数 | `model.selected_method_version` |
| x_s | 情景 s 中明确扰动的全部外生因素向量 | 混合单位逐字段 | `sensitivity.scenario_inputs` |
| z_s | 情景 s 维持基准的其余外生参数 | 混合单位逐字段 | `sensitivity.scenario_fixed_inputs` |
| s | 悲观、基准、乐观或合同定义情景标识 | 枚举 | `sensitivity.scenario_id` |

**下标、上标及集合范围：**

- 下标/范围 `s`：命名情景，集合由审定情景表给出；f=方法映射非物理标量。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 联合情景不同于单因素敏感性；同一参数不能在 x_s 和 z_s 同时出现且值不同。 输出单位为 逐指标原单位；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 不虚构成功概率或置信度；输入可行性/能量守恒/税务债务平衡全部重检。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第16组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `M_s = f(x_s, z_s)`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 每情景独立完整流水线和证据哈希，不只比例缩放最终 IRR；分类隔离。

**逐个下标词素：** s=计息子期间或命名情景索引，见本条集合。

**术语键：** `TERM-F-SCENARIO-METRIC`。

### F-WORST-CASH-YEAR · 最差现金流年份集合

- 英文全称：Worst cash-flow year set；首次释义：最差现金流年份集合（Worst cash-flow year set）。
- 最低清单组：16；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
\mathcal Y_{worst,b}=\operatorname{argmin}_{y\in\mathcal Y} CF_{b,y}
$$

- 文本式：`Y_worst,b = argmin(y∈Y) CF_b,y`
- 输出：`risk.worst_cash_years`；量纲/单位：集合（年份标签）。
- 输入：`finance.selected_cash_flow`, `risk.cash_year_scope`, `finance.cash_flow_basis`。
- 章节：`CH16`, `CH17`；未来测试：`T-WORST-CASH-YEAR`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| Y_worst,b | 达到最小净现金流的全部年份，允许并列 | 集合 | `risk.worst_cash_years` |
| CF_b,y | 选定口径当年净现金流 | 元 | `finance.selected_cash_flow` |
| Y | 被比较的有效年份集合，需明确仅运营期或含建设期 | 集合 | `risk.cash_year_scope` |
| y | 年份索引 | 1 | index_or_constant |
| b | 项目/股权及税前后口径 | 枚举 | `finance.cash_flow_basis` |

**下标、上标及集合范围：**

- 下标/范围 `argmin y∈Y`：在声明范围内寻找全部最小值年份；不武断取第一个。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 集合/求和或连乘 `argmin y∈Y`：在声明范围内寻找全部最小值年份；不武断取第一个。

**边界与量纲：** 必须同时列最小现金额和比较范围；含建设期与运营最差年各自输出，不能借大建设负数掩盖运营缺口。 输出单位为 集合（年份标签）；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 空集合或有缺失无法断言完整最差年；最差现金流不是最大会计亏损。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第16组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `Y_worst,b = argmin(y∈Y) CF_b,y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 并列、全非负、缺失、空集合和运营/建设范围分开。

**逐个下标词素：** worst=给定年份集合中最差净现金流的全部位置；b=互斥的项目/股权及税前后完整口径索引；y=财务或运营年度索引，必须按本条时间定义区分。

**术语键：** `TERM-F-WORST-CASH-YEAR`。

### F-CAPEX-PAYMENT-BALANCE · 投资估算付款平衡

- 英文全称：CAPEX payment reconciliation；首次释义：投资估算付款平衡（CAPEX payment reconciliation）。
- 最低清单组：16；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
\epsilon_K=\sum_{y\in\mathcal Y_K}K_y+AP_{end}-AP_{start}-CAPEX_{payable}
$$

- 文本式：`ε_K = Σ(y∈Y_K) K_y + AP_end − AP_start − CAPEX_payable`
- 输出：`checks.capex_payment_residual`；量纲/单位：元。
- 输入：`capex.scope_cash_payments`, `capex.payable_net_closing`, `capex.payable_net_opening`, `capex.scope_accrued_amount`, `capex.scope_year_ids`。
- 章节：`CH14`, `CH16`；未来测试：`T-CAPEX-PAYMENT-BALANCE`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| ε_K | 投资范围内现金付款与权责确认金额桥的残差 | 元 | `checks.capex_payment_residual` |
| K_y | 本范围当年资本付款，不含重复融资现金项 | 元 | `capex.scope_cash_payments` |
| AP_end | 期末资本应付款减预付款净额 | 元 | `capex.payable_net_closing` |
| AP_start | 期初资本应付款减预付款净额 | 元 | `capex.payable_net_opening` |
| CAPEX_payable | 同范围同税价确认的累计资产采购和服务金额，已剥离非付现/融资项 | 元 | `capex.scope_accrued_amount` |
| Y_K | 该投资范围完整付款评价期 | 集合 | `capex.scope_year_ids` |
| y | 财务时点索引 | 1 | index_or_constant |

**下标、上标及集合范围：**

- 下标/范围 `Σ y∈Y_K`：对同一投资范围完整付款期求和；AP=资本应付减预付；end/start=期末/初。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 集合/求和或连乘 `Σ y∈Y_K`：对同一投资范围完整付款期求和；AP=资本应付减预付；end/start=期末/初。

**边界与量纲：** 用相同含税/不含税和资本化利息范围；不能把未付合同总额与无杠杆现金流无桥对账。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 非现金转固、资本化利息、汇兑和范围差额先单列桥项；本式不把它们藏在零残差。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第16组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `ε_K = Σ(y∈Y_K) K_y + AP_end − AP_start − CAPEX_payable`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 资本付款+应付款净增=同范围确认金额；逐项工程量/报价清单回勾。

**逐个下标词素：** K=资本开支或其付款范围；y=财务或运营年度索引，必须按本条时间定义区分；end=评价范围期末；start=评价范围期初；payable=与资本付款相对应权责确认金额。

**术语键：** `TERM-F-CAPEX-PAYMENT-BALANCE`。

### F-INVESTMENT-HURDLE-GAP · 投资门槛差距

- 英文全称：Investment hurdle gap；首次释义：投资门槛差距（Investment hurdle gap）。
- 最低清单组：16；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
G_M=M_{calc}-M_{target}
$$

- 文本式：`G_M = M_calc − M_target`
- 输出：`decision.metric_gap`；量纲/单位：与 M 同单位。
- 输入：`decision.calculated_metric`, `decision.target_metric`。
- 章节：`CH01`, `CH16`, `CH17`, `CH18`；未来测试：`T-INVESTMENT-HURDLE-GAP`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| G_M | 测算值减用户门槛的原始差距 | 与 M 同单位 | `decision.metric_gap` |
| M_calc | 有效的确定性测算指标，不得倒改输入迎合目标 | 原指标单位 | `decision.calculated_metric` |
| M_target | 用户目标，如 IRR 下限或回收期上限 | 原指标单位 | `decision.target_metric` |

**下标、上标及集合范围：**

- 下标/范围 `M`：被比较指标；calc=测算，target=用户目标。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** IRR 下限差距≥0 倾向满足；回收期上限差距≤0 才满足，方向由指标定义而非本式自动推断。 输出单位为 与 M 同单位；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 指标必须同税/融资/时点口径；多根 IRR 或期内未回收不能硬转数值比较；合规阻断不被财务达标抵消。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第16组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。
- 项目方法冻结约定 METHOD-CONTRACT-v1：在附件最低公式基础上补充会计桥、边界与异常状态；不构成现行税法/融资协议结论；待适用标准、合同和税制全文复核。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `G_M = M_calc − M_target`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 下限/上限方向、口径不一致、不可计算状态传播。

**逐个下标词素：** M=所考察财务/技术指标；calc=确定性测算结果；target=用户目标阈值而非实际测算输入。

**术语键：** `TERM-F-INVESTMENT-HURDLE-GAP`。

### F-CASH-TAX-TOTAL · 同口径现金税费总额

- 英文全称：Boundary-consistent total cash taxes；首次释义：同口径现金税费总额（Boundary-consistent total cash taxes）。
- 最低清单组：9；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
T_{b,y}=T_{inc,cash,b,y}+T_{other,b,y}+VP_{b,y}-VR_{b,y}+ADJ_{vat,b,y}
$$

- 文本式：`T_b,y = T_inc,cash,b,y + T_other,b,y + VP_b,y − VR_b,y + ADJ_vat,b,y`
- 输出：`tax.cash_total_selected`；量纲/单位：元。
- 输入：`tax.income_cash_paid`, `tax.other_cash_total`, `tax.vat_cash_paid`, `tax.vat_cash_refund`, `tax.vat_cash_basis_adjustment`, `finance.tax_basis`。
- 章节：`CH15`, `CH16`；未来测试：`T-CASH-TAX-TOTAL`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| T_b,y | 选定项目/主体口径现金税净额 | 元 | `tax.cash_total_selected` |
| T_inc,cash,b,y | 同口径现金所得税 | 元 | `tax.income_cash_paid` |
| T_other,b,y | 未在经营费用/资产中重复的其他现金税费 | 元 | `tax.other_cash_total` |
| VP_b,y | 本期增值税实际缴纳额 | 元 | `tax.vat_cash_paid` |
| VR_b,y | 本期增值税实际退税额 | 元 | `tax.vat_cash_refund` |
| ADJ_vat,b,y | 如收付采用不含税口径，用于补回销项/进项收付的桥接净额；含税全现金口径时为零 | 元 | `tax.vat_cash_basis_adjustment` |
| b | P 无杠杆项目或 E 融资主体 | 枚举 | `finance.tax_basis` |
| y | 财务年 | 1 | index_or_constant |

**下标、上标及集合范围：**

- 下标/范围 `b`：项目/融资主体互斥口径；y=财务年；vat=增值税；ADJ=税价桥调整。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 含税收付时净缴退税直接入流；不含税收付时必须显式记录 VAT 桥，不能既除税又全扣净缴税漏掉税收付。输出按 b 投影到 tax.project_cash_total 或 tax.equity_cash_total。 输出单位为 元；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 只有税价桥完备才允许税后财务指标；实际负税净额须有合法退税依据。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第9、10、16组（附件 hermes-完整提示词.md）：由折旧、税务现金口径及平衡要求推导的方法约定；不代表现行法定税率或条款；待标准全文核对。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `T_b,y = T_inc,cash,b,y + T_other,b,y + VP_b,y − VR_b,y + ADJ_vat,b,y`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 含税现金法与不含税+税价桥独立对账；应收/应付 VAT 时点对齐。

**逐个下标词素：** b=互斥的项目/股权及税前后完整口径索引；y=财务或运营年度索引，必须按本条时间定义区分；inc=所得税而非其他现金税费；cash=实际或预测现金收付而非权责计提；other=未在其他项目计入的其他收益/税费；vat=增值税现金桥。

**术语键：** `TERM-F-CASH-TAX-TOTAL`, `TERM-VAT`。

### F-UNIT-KW-MW · 功率千瓦至兆瓦换算

- 英文全称：Kilowatt to megawatt conversion；首次释义：功率千瓦至兆瓦换算（Kilowatt to megawatt conversion）。
- 最低清单组：1；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
P_MW=P_kW/s
$$

- 文本式：`P_MW = P_kW / s`
- 输出：`units.power_mw`；量纲/单位：MW。
- 输入：`units.power_kw`, `constants.kilo_scale`。
- 章节：`CH06`, `CH08`, `CH14`；未来测试：`T-UNIT-KW-MW`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| P_MW | 规范化后的同一物理量或单位成本 | MW | `units.power_mw` |
| P_kW | 待转换原值，保持 DC/AC 或峰值标签 | kW | `units.power_kw` |
| s | 十进制千倍单位换算系数，定义值 1000，非经验参数 | 1 | `constants.kilo_scale` |

**下标、上标及集合范围：**

- 下标/范围 `单位后缀`：k/M 为千/兆前缀，W 为瓦，h 为小时，p 为额定峰值标签；不把单位后缀当乘法变量。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 仅变换单位数值，保留物理维度、DC/AC、峰值和税价标签；kW 与 kWh 不互换。 输出单位为 MW；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 十进制前缀定义；功率转电量另须时间积分，不能应用本换算。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第1组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `P_MW = P_kW / s`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 逆转换一致性、元/Wp 与元/kWp 的方向校验；本阶段仅文档结构核查，不宣称数值测试。

**逐个下标词素：** MW=兆瓦功率单位后缀；kW=千瓦，辐照度变量中为 kW/m² 单位后缀。

**术语键：** `TERM-F-UNIT-KW-MW`。

### F-UNIT-KWH-MWH · 电量千瓦时至兆瓦时换算

- 英文全称：Kilowatt-hour to megawatt-hour conversion；首次释义：电量千瓦时至兆瓦时换算（Kilowatt-hour to megawatt-hour conversion）。
- 最低清单组：1；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
E_MWh=E_kWh/s
$$

- 文本式：`E_MWh = E_kWh / s`
- 输出：`units.energy_mwh`；量纲/单位：MWh。
- 输入：`units.energy_kwh`, `constants.kilo_scale`。
- 章节：`CH06`, `CH08`, `CH14`；未来测试：`T-UNIT-KWH-MWH`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| E_MWh | 规范化后的同一物理量或单位成本 | MWh | `units.energy_mwh` |
| E_kWh | 待转换原值，保持 DC/AC 或峰值标签 | kWh | `units.energy_kwh` |
| s | 十进制千倍单位换算系数，定义值 1000，非经验参数 | 1 | `constants.kilo_scale` |

**下标、上标及集合范围：**

- 下标/范围 `单位后缀`：k/M 为千/兆前缀，W 为瓦，h 为小时，p 为额定峰值标签；不把单位后缀当乘法变量。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 仅变换单位数值，保留物理维度、DC/AC、峰值和税价标签；kW 与 kWh 不互换。 输出单位为 MWh；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 十进制前缀定义；功率转电量另须时间积分，不能应用本换算。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第1组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `E_MWh = E_kWh / s`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 逆转换一致性、元/Wp 与元/kWp 的方向校验；本阶段仅文档结构核查，不宣称数值测试。

**逐个下标词素：** MWh=兆瓦时电量单位后缀；kWh=千瓦时电量单位后缀。

**术语键：** `TERM-F-UNIT-KWH-MWH`。

### F-UNIT-IRRADIANCE-W-KW · 辐照度瓦至千瓦换算

- 英文全称：Irradiance watt-to-kilowatt conversion；首次释义：辐照度瓦至千瓦换算（Irradiance watt-to-kilowatt conversion）。
- 最低清单组：1；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
G_kW=G_W/s
$$

- 文本式：`G_kW = G_W / s`
- 输出：`units.irradiance_kw_m2`；量纲/单位：kW/m²。
- 输入：`units.irradiance_w_m2`, `constants.kilo_scale`。
- 章节：`CH06`, `CH08`, `CH14`；未来测试：`T-UNIT-IRRADIANCE-W-KW`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| G_kW | 规范化后的同一物理量或单位成本 | kW/m² | `units.irradiance_kw_m2` |
| G_W | 待转换原值，保持 DC/AC 或峰值标签 | W/m² | `units.irradiance_w_m2` |
| s | 十进制千倍单位换算系数，定义值 1000，非经验参数 | 1 | `constants.kilo_scale` |

**下标、上标及集合范围：**

- 下标/范围 `单位后缀`：k/M 为千/兆前缀，W 为瓦，h 为小时，p 为额定峰值标签；不把单位后缀当乘法变量。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 仅变换单位数值，保留物理维度、DC/AC、峰值和税价标签；kW 与 kWh 不互换。 输出单位为 kW/m²；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 十进制前缀定义；功率转电量另须时间积分，不能应用本换算。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第1组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `G_kW = G_W / s`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 逆转换一致性、元/Wp 与元/kWp 的方向校验；本阶段仅文档结构核查，不宣称数值测试。

**逐个下标词素：** kW=千瓦，辐照度变量中为 kW/m² 单位后缀；W=瓦，辐照度变量中为 W/m² 单位后缀。

**术语键：** `TERM-F-UNIT-IRRADIANCE-W-KW`。

### F-UNIT-COST-WP-KWP · 单位投资瓦峰至千瓦峰换算

- 英文全称：Per-watt-peak to per-kilowatt-peak cost conversion；首次释义：单位投资瓦峰至千瓦峰换算（Per-watt-peak to per-kilowatt-peak cost conversion）。
- 最低清单组：1；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
c_kWp=c_Wps
$$

- 文本式：`c_kWp = c_Wp × s`
- 输出：`units.cost_per_kwp`；量纲/单位：元/kWp。
- 输入：`units.cost_per_wp`, `constants.kilo_scale`。
- 章节：`CH06`, `CH08`, `CH14`；未来测试：`T-UNIT-COST-WP-KWP`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| c_kWp | 规范化后的同一物理量或单位成本 | 元/kWp | `units.cost_per_kwp` |
| c_Wp | 待转换原值，保持 DC/AC 或峰值标签 | 元/Wp | `units.cost_per_wp` |
| s | 十进制千倍单位换算系数，定义值 1000，非经验参数 | 1 | `constants.kilo_scale` |

**下标、上标及集合范围：**

- 下标/范围 `单位后缀`：k/M 为千/兆前缀，W 为瓦，h 为小时，p 为额定峰值标签；不把单位后缀当乘法变量。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 仅变换单位数值，保留物理维度、DC/AC、峰值和税价标签；kW 与 kWh 不互换。 输出单位为 元/kWp；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 十进制前缀定义；功率转电量另须时间积分，不能应用本换算。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第1组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `c_kWp = c_Wp × s`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 逆转换一致性、元/Wp 与元/kWp 的方向校验；本阶段仅文档结构核查，不宣称数值测试。

**逐个下标词素：** kWp=千瓦峰值直流容量或其单位投资后缀；Wp=瓦峰值单位投资口径。

**术语键：** `TERM-F-UNIT-COST-WP-KWP`。

### F-UNIT-DC-CAPACITY · 峰值直流装机单位换算

- 英文全称：Peak DC capacity unit conversion；首次释义：峰值直流装机单位换算（Peak DC capacity unit conversion）。
- 最低清单组：1；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
P_MWp=P_kWp/s
$$

- 文本式：`P_MWp = P_kWp / s`
- 输出：`units.dc_mwp`；量纲/单位：MWp。
- 输入：`capacity.dc_kwp`, `constants.kilo_scale`。
- 章节：`CH01`, `CH06`, `CH07`；未来测试：`T-UNIT-DC-CAPACITY`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| P_MWp | 兆瓦级额定容量，保持 DC 标签 | MWp | `units.dc_mwp` |
| P_kWp | 千瓦级额定容量，保持 DC 标签 | kWp | `capacity.dc_kwp` |
| s | 十进制千倍换算系数，定义值 1000 | 1 | `constants.kilo_scale` |

**下标、上标及集合范围：**

- 下标/范围 `单位后缀`：p=额定峰值，ac=交流，k/M=千/兆前缀，均非额外变量。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 这是单位映射，不是 DC→AC 转换模型；MWp 不能直接替代 MWac。 输出单位为 MWp；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 保留峰值 p 或交流 ac 标签；输入需铭牌依据。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第1组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `P_MWp = P_kWp / s`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 反转换一致；与容配比单位换算不变性联检。

**逐个下标词素：** MWp=兆瓦峰值直流容量单位后缀；kWp=千瓦峰值直流容量或其单位投资后缀。

**术语键：** `TERM-F-UNIT-DC-CAPACITY`。

### F-UNIT-AC-CAPACITY · 额定交流容量单位换算

- 英文全称：Rated AC capacity unit conversion；首次释义：额定交流容量单位换算（Rated AC capacity unit conversion）。
- 最低清单组：1；状态：方法冻结待复核，数值验证 **PLANNED**。
- LaTeX：

$$
P_MWac=P_kWac/s
$$

- 文本式：`P_MWac = P_kWac / s`
- 输出：`units.ac_mw`；量纲/单位：MWac。
- 输入：`capacity.ac_kw`, `constants.kilo_scale`。
- 章节：`CH01`, `CH06`, `CH07`；未来测试：`T-UNIT-AC-CAPACITY`（PLANNED）。

| 完整符号 | 逐符号释义 | 单位 | 字段/角色 |
|---|---|---|---|
| P_MWac | 兆瓦级额定容量，保持 AC 标签 | MWac | `units.ac_mw` |
| P_kWac | 千瓦级额定容量，保持 AC 标签 | kWac | `capacity.ac_kw` |
| s | 十进制千倍换算系数，定义值 1000 | 1 | `constants.kilo_scale` |

**下标、上标及集合范围：**

- 下标/范围 `单位后缀`：p=额定峰值，ac=交流，k/M=千/兆前缀，均非额外变量。
- 上标/幂 `说明`：本式无上下标幂运算；上标如有均在完整符号定义中说明。
- 无集合求和或连乘；如出现 min/max，按所列有限标量比较。

**边界与量纲：** 这是单位映射，不是 DC→AC 转换模型；MWp 不能直接替代 MWac。 输出单位为 MWac；每个输入的单位见 every_symbol_definition，同量纲才能相加；比率以小数存储，百分号仅展示。 每年有效折现率/衰减率存为无量纲年度比例；(1+r) 的幂为年度步数或年化分数。合同单利 i_s 则按 1/年 与 δ_s 的年量相乘。kWp 计算数值按 kW 等价缩放但永久保留峰值/DC 标签。

**假设：**
- 保留峰值 p 或交流 ac 标签；输入需铭牌依据。

**方法优先级：**
1. 先核验来源、单位、时点和计量边界；UNKNOWN/CONFLICT 不代入默认零。
2. 本条仅冻结方法；实际合同/适用法规优先，变更需升版本并重审受影响公式。

**来源：**
- USER-BASELINE §6 第1组（附件 hermes-完整提示词.md）：附件要求的定义/代数推导，非声称来自已读行业标准条款；待标准全文核对。

**符号算例（PLANNED）：** 在本条边界和假设成立时，以全部输入符号代入，应满足 `P_MWac = P_kWac / s`。不提供伪造数值；该关系本身不构成独立数值验证。

**验证方式（尚未执行）：** 反转换一致；与容配比单位换算不变性联检。

**逐个下标词素：** MWac=兆瓦交流功率单位后缀；kWac=千瓦交流额定功率单位后缀。

**术语键：** `TERM-F-UNIT-AC-CAPACITY`。

## 7. 后续验证与冻结变更门禁

- Phase 2：统一字段、单位、类型、空值/不适用状态和章节别名；验证公式依赖图无循环，单一物理指标只有一个生效方法。
- Phase 3：逐条实现确定性计算并建立本表 `test_id` 对应真实测试，使用独立手工/程序参考核对数值；单纯代数回代和字符串断言不能替代数值验证。
- 必备未来用例：负/零容量、混合单位、闰年/部分年度、缺负荷、无并网、极端限发、负价、IRR 无根/多根/全零/重根、期内不回收、折旧超限、设备更换、亏损到期、税缴错期、债务服务零、资本化利息、宽限期、气球本金、分红约束、投资与资金平衡。
- 属性/变形测试：固定其他因素增加投资不得提高项目 NPV；相同结算条件下降电量不增加电量收益；每期能量守恒；提款/本金/利息/权益/现金账户闭合；不变经营条件下融资比例不改变无杠杆项目流。
- 任何未通过实现/独立数值核验的公式不得升级为 PASS；Phase 1 文档结构可读不代表产品可运行。
- 本次不实现储能 SOC/效率/充放电及退化引擎；含储能时无储能能量平衡必须阻断或转入独立 NOT_IMPLEMENTED 分类。
