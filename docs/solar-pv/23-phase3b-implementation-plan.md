# Phase 3B Energy Engine Implementation Plan

> **For agentic workers:** 使用executing-plans / 分工独占文件，主任务复核每项真实证据后才提交。子任务不得暂存或提交。

**Goal:** 完成本阶段确定性容量、资源、温度、损失、限幅、衰减和逐年发电计算；只在专业数值和真实全年计算全部闭环时标记PHASE3B_ENERGY_ENGINE_PASS。

**Architecture:** 复用Phase2完整导出重验与D3 bundle，冻结281域的纯Decimal原子核与项目适配分离；物理时间轴以UTC区间连续性及站址IANA本地日历聚合。区间计算有界流式，逐年先应用性能变化再重算逆变器限幅，不缩放已经限幅的年总量。唯一结果仍用Phase3A契约，逐条中间证据与结果数据内容摘要关联，最终manifest最后发布。

**Tech Stack:** 现有Python>=3.12,<3.15、Decimal/Fraction、jsonschema、ZoneInfo和D3资源预算；不新增依赖、不建立产品工厂。

**Spec:** 22-phase3b-user-task.md（用户本轮原文）、17/18/19/20/21、15输入接口、冻结03/05/06/07/08/12、Phase3A验收报告。

## Global Constraints

- 起始HEAD a84451fa0a09ce65c6e1e8c67c853d65c4e8c1ca，实际核验两个3A提交。四个其他任务文件路径/状态/原字节SHA256见reports/solar-pv/phase3b-startup-state.json；不写、不暂存、不提交、不回滚，不声称整体clean。
- 原469输入、281域、89公式、方程、12份冻结原文件、九分类全部保留；本阶段工程27条，剩余公式不伪造已实现。
- 不读写凭据，不输出用户原始资料；案例全为来源/状态明确的SYNTHETIC，不联网抓真实气象。
- 缺值/未审方法/来源失效不补零，错误单位不猜，已有POA不再转置，GHI不能当POA。原始事实参数不藏进型号/拓扑/协议等自由文本。
- D2/D3同批准范围不重复请示；若实际接入暴露新的实质数学/关键数据契约冲突，先写具体差异并暂停该冲突分支，不以假设或默认绕过。
- 专业参考使用明确输入/公式/符号单位、独立手算或有理算法/公开方法，不调用生产函数生成expected。
- 本轮明确授权测试。旧产品代码、测试断言、catalog、历史归档不改；pytest的basetemp、log、XML和大表仅置于独占Hermes scratch目录，不并发复用。
- 不push、不上传、不发布、不部署；3B完成后停止，不进入3C。财务、正式四文件、真实项目和平台仍独立BLOCKED。

## 3B-1 接口、矩阵和保护基线

- [x] 全文读取本轮379行任务，核验3A两个真实Git提交和本地index。
- [x] 记录4个保留改动的路径/状态/内容哈希，核对288保护集合仅该4处有授权差异；启动记录和原文保存。
- [x] 读取当前有效Catalog的27条完整数学/符号/单位/条件及绑定，形成formula_id→输入域→原字段→专项参考→状态矩阵；未运行项保持NOT_TESTED。
- [x] 跟踪温度、时序、更新等真实方法接口，独立检查现有严格配置能否完整承载物理分支；发现契约冲突记录而不偷塞文本。

## 3B-2 原子容量/资源/温度

**Files:** 新增calculation/engineering.py、temperature.py、capacity.py、solar_resource.py及相应新测试；不改冻结原文件。

**Interfaces:** engineering.FORMULA_IDS及evaluate(formula_id,values,options=None)接入现有registry；values仅冻结域ID；temperature.cell_temperature及prepare_temperature消费已严格重验D2配置，返回明确状态/中间温度/方法来源。项目适配只消费ValidatedInput，不直接读未经校验用户输入。

- [x] 工程核每条先RED：显式正常/边界/非法/缺值/不适用、精确单位及索引集合；全运算受本地Decimal precision控制；27条已实际专项执行。
- [x] 容量从模块Wp×块数、逆变器有限集合求和；DC/AC标签不合并。面积/尺寸/间距/串并联电压电流检查缺关键参数时保留缺口，不能以固定面积功率密度顶替。（原子容量核已通过，项目适配未闭合）
- [x] 资源月度累计与区间均值积分分开；时间覆盖/时区/闰年/计量边界明确，GHI/DNI/DHI保留来源，不在无方法时转POA；资源专项9项通过。
- [x] Sandia模块温度与电池温度分两步，系数、风速、参考量、适用域/安装来源显式；零辐照、极冷极热、错误系数和来源失效专项20项通过；公开方法许可仍REQUIRES_REVIEW。
- [x] 快速专项/编译/代码检查与四文件哈希复核通过后显式范围本地commit，并读回SHA和提交路径。

## 3B-3 损失、发电、衰减和更新

**Files:** 新增calculation/losses.py、degradation.py、energy_yield.py及新专项测试。

- [x] 逐loss ID、原sequence、物理边界、来源和included_in_source建立覆盖台账；乘积损失与各步前后能量守恒独立校核；损失原子账簿专项通过。
- [x] 同质组或单机先转换限幅后求和；缺异构DC分配时不猜平均。年度/月度数据不伪造精准限幅。
- [x] 明确站用、AC/变压器/送出、并网限额与弃光的适用边界。屋顶可用电量交给3C后才分自用/上网，不能把上网限额错误限制全部自用可用电量；地面全售电可单独计算交付侧物理限额。
- [x] D2缺口审查确认`energy.auxiliary_kw`可作为已批准D2内的最小typed显式假设：非负kW、无默认、缺失阻断、纳入方法hash；不把数字塞进`system.topology`或比例型`system.losses`。更换恢复上限不能单独推导恢复量，日期缺失的停机仅可作为明确披露的等效情景。
- [x] 首年初衰与PR包含标记互斥；固定率/分段率、更新恢复上限与事件明确。每年性能先改变DC，再重算每时段AC限幅，不缩放已限幅电量；没有明确恢复/时间规则就阻断。
- [x] 独立参考及正常/异常/边界/不适用、物理守恒通过后范围提交。

## 3B-4 真实全年有界计算

**Files:** 新增有界执行与结果输出辅助模块及test_energy_timeseries_capacity.py，复用既有D3不全局提限。

- [x] 精确UTC半开区间；8760/8784小时及35040/35136个15分钟分别真实生成→完整写入→逐原子读验→温度/DC/限幅/损失/积分/逐年重算；逐行输出证据有界落盘，不多份复制大数组。
- [x] 连续/重复/缺口/缺值/错误单位/春跳秋折/粒度变化/超限/中途失败专项；结果manifest最后发布，中途失败不留可被当成有效完整结果的产物。
- [x] 保存真实输入字节、行数、原子数、峰值工作集/OS峰值、磁盘、时长和验证状态；检查预算/源文件运行前后哈希。不把合作式逻辑限额当OS沙箱，其他平台强制隔离保持未验。
- [x] 快速与容量证据冻结后范围提交。

## 3B-5 分类入口与唯一结果

- [x] 工商业屋顶与集中式地面分别入口，复用物理核但独立分类校验、专项条件、输出边界；其余7类保持未实现。
- [x] 入口重验Phase2导出、D2、真实bundle内容身份。指标有输入field/instance/source、方法参数、公式版本、上游、期间和物理边界；中间区间输出摘要进入结果业务内容，私有路径/耗时不进入业务hash。
- [x] validate_result/serialize_result/deserialize_result实跑；重复run仅run_id/created_at变化，result_hash一致；输入/源/方法变化必须重算并改变身份。尚未实现的消纳和财务null+NOT_IMPLEMENTED，不能标CALCULATED。
- [x] 保存两类可复核SYNTHETIC能源案例，交接3C的可用能量和对齐接口，不实现3C；验收后范围提交。

## 3B-6 完整专业验收、回归与停止

- [x] 每条真正执行公式的独立参考输入/式/单位/expected/来源/actual/误差/判定写入数值证据；只有已实际专项校核才写execution-evidence并升级库存，不把注册当实现。
- [x] 独立只读审阅，实际复现和关闭问题；修复后重新冻结最终候选，再跑Phase2/3完整回归、旧145项含Expert回归（仓库外隔离副本，带真实固定历史fixture对象库）。旧断言不削弱。
- [x] 复核288原保护文件：除授权4处外全部不变；4处与启动哈希相同。提交前后只核本轮允许路径、Git blob与清单SHA（注意ignored日志和CRLF），保留所有真实失败、SKIP和 superseded 证据。
- [x] 更新README/17顶层状态及本计划历史，生成reports/solar-pv/phase3b-review-and-acceptance.md，逐项报告公式数/实际案例/全年指标/全部SHA/未关问题/3C依赖。仅所有核心正确性要求闭合才PHASE3B_ENERGY_ENGINE_PASS，否则PARTIAL/BLOCKED。
- [x] 最终本地commit、读回SHA与四文件哈希，明确工作区仍有用户4处改动；停止，不自动进入3C。
