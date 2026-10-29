# Phase 3B 正式数值审阅与验收

## 1. 结论、Git与验收边界

**PHASE3B_ENERGY_ENGINE_PASS：本轮已完成原计划的离线工程/资源/温度/损耗/逐年发电链，并由冻结候选v3的完整运行、独立参考及两类25年SYNTHETIC案例验收。** 不等于PHASE3_CALCULATION_ENGINE_PASS，不等于正式四文件、真实项目或WorkBuddy通过。

- 原始HEAD：`5054cc7598ccc4c35a9d3501880f8f15db755106`，分支main。
- 验收候选：`candidate-v3`，41个生产Python模块实际编译通过；最终测试执行前后及当前仓库生产/测试字节与候选hash一致，见phase3b-final-execution-evidence.json。
- 本轮Git提交：本报告、生产代码、测试和证据在本轮最后同一明确范围本地提交中交付。**最终HEAD及本轮准确commit列表在提交后读取，写入持久证据目录的`final-git-receipt.json`并在完成消息给出**；不在尚未生成该提交时虚构SHA或制造自引用提交hash。
- 完整光伏回归：**3506 passed / 0 failed / 0 errors / 6 skipped**，3512个收集节点，3431.48秒。最终JUnit SHA-256：`6b8325bdcffe564c6e42464ba4fec1a1ca6dbd2246ffc2c47ba2f1c2437965c4`。
- 旧产品完整回归含Expert：**145 passed / 0 failed / 0 errors / 5 skipped**，150个节点。JUnit SHA-256：`6cf2b55b6ed8383b7ea806599749c6e2800bd182258585cde739168e27199978`。
- 六个主数值案例与两类跨年时区案例均真实运行。完整原始bundle、逐行中间结果、日志及JUnit已复制并读回校验至：`C:/Users/wangbin/AppData/Local/hermes/attachments/solar-pv-phase3b-evidence-20261029`。不是24小时后可能清理的scratch唯一副本；仓库内两份案例保存小输入/方法/预算/原始manifest/真实结果/receipt/参考证据。

## 2. 真实生产模块

|模块|本轮落地职责|
|---|---|
|calculation/capacity.py|原设备铭牌→DC/AC容量、显式逐台DC分配、面积/GCR/尺寸、组串数/STC电压电流、屋顶/地面分别前置|
|calculation/degradation.py|首年与固定/分段性能滚动、原资产事件与typed恢复/容量/设备范围、停机假设|
|calculation/energy_yield.py|有界资源单遍、逐年重算温度/DC/逐台转换限幅/共享瓶颈/后续损失、月年生命期与唯一结果、逐行证据及失败清理|
|calculation/method_config.py及静态Schema|D2内补显式DC分配和关联原事件的恢复规则；缺失/未审阻断，来源/版本/身份完整|
|cli.py energy子命令|真实离线CLI；JSON与目录路径分别校验，禁止穿越/链接/覆盖，不联网|
|calculation/execution-evidence.json|仅27条真实独立校核的原子公式升级IMPLEMENTED_TESTED，不把注册或函数存在当数值通过|

既有engineering、solar_resource、temperature、losses、input_contract、result_contract及D3被实际消费，不推翻3A设计。无新依赖、HTTP气象客户端、产品工厂或3C业务代码。

## 3. 范围与冻结定义

保留469字段、281公式域、89公式及有效定义版本`solar-pv-formula-definitions/1.0.1`/hash `617a2e9d314c095bd2ec893939c930a2323be6fd7805da12bf6d6fdd70274808`；12份冻结原件、九分类、18章、29sheet、最终四文件与六种产品门禁未改。D1—D3在原批准边界内接线，不改方程含义。

当前执行库存：27 IMPLEMENTED_TESTED、62 NOT_IMPLEMENTED；Phase3总目标82中剩55条属后续3C—3G，另7储能公式属Phase8。矩阵仅27个公式行及对应派生验收状态升级，原expected/需求文本不变；1208行保持，506 PASS、702 NOT_IMPLEMENTED。其他七类只有拒绝/隔离验证，未标项目完成。

## 4. 本阶段27条公式与专业参考

逐符号/上下标/集合/量纲/条件/来源/输入绑定/预期/实际/误差/测试ID/需求ID完整内容见`phase3b-formula-numerical-verification.json`；机器横表见`phase3b-formula-implementation-matrix.csv`。预期来自已有独立字面值/有理手算，不调用生产函数生成expected。最终JUnit逐条包含其所有登记测试ID。

|formula_id|输出单位|独立锚实际值|绝对误差|结论|
|---|---|---|---|---|
|`F-DC-CAPACITY`|kWp|660.000|0.000|PASS|
|`F-AC-CAPACITY`|kWac|350|0|PASS|
|`F-DC-AC-RATIO`|1|1.8857142857142857142857142857142857142857142857142857142857142857142857142857143|0E-79|PASS|
|`F-POA-IRRADIATION`|kWh/m²|0.500|0.000|PASS|
|`F-FIRST-YEAR-ENERGY`|kWh|264.00|0.00|PASS|
|`F-LOSS-COMPOSITE`|1|0.855|0.000|PASS|
|`F-DC-TIME-POWER`|kW|415.3248000|0E-7|PASS|
|`F-AC-INVERTER-POWER`|kW|250|0|PASS|
|`F-AVAILABLE-ENERGY`|kWh/时段|65.9074180250|0E-10|PASS|
|`F-ENERGY-AGGREGATION`|kWh|6.6|0.0|PASS|
|`F-INITIAL-DEGRADATION`|kWh|970.00|0.00|PASS|
|`F-ANNUAL-DEGRADATION`|kWh|922.36816000|0E-8|PASS|
|`F-PIECEWISE-DEGRADATION`|1|0.9610|0.0000|PASS|
|`F-EQUIVALENT-HOURS`|h|4380|0|PASS|
|`F-CAPACITY-FACTOR`|1|0.5|0.0|PASS|
|`F-PR-OBSERVED`|1|0.008|0.000|PASS|
|`F-EXPORT-LIMIT-ENERGY`|kWh/时段|25.00|0.00|PASS|
|`F-UNIT-KW-MW`|MW|1.25|0.00|PASS|
|`F-UNIT-KWH-MWH`|MWh|2.5|0.0|PASS|
|`F-UNIT-IRRADIANCE-W-KW`|kW/m²|0.8|0.0|PASS|
|`F-UNIT-COST-WP-KWP`|元/kWp|1250.00|0.00|PASS|
|`F-UNIT-DC-CAPACITY`|MWp|0.66|0.00|PASS|
|`F-UNIT-AC-CAPACITY`|MWac|0.35|0.00|PASS|
|`F-USABLE-AREA`|m²|800|0|PASS|
|`F-AVERAGE-ANNUAL-ENERGY`|kWh/年|1000|0|PASS|
|`F-EMISSIONS-AVOIDED`|tCO2e|0.5000|0.0000|PASS|
|`F-TRANSFORMER-ACTIVE-LIMIT`|kW|900.0|0.0|PASS|

温度采用显式Sandia两步结构，单独校核module与cell、零POA、低温增益、高温、风速、参数及来源。公开方法/设备应用的真实商业许可及适用性仍另审，不冒充实际设备认证。

## 5. 尚未实现/阻断公式清单

**无本轮27条原子公式尚未实现或数值失败。** 以下均保留原ID及NOT_IMPLEMENTED，不提前计入Phase3B：

- **consumption**：`F-SELF-CONSUMPTION`、`F-EXPORTED-ENERGY`、`F-CURTAILED-ENERGY`、`F-ENERGY-BALANCE`、`F-DELIVERED-ENERGY`、`F-SELF-CONSUMPTION-RATIO`、`F-LOAD-COVERAGE-RATIO`、`F-ENERGY-REVENUE`、`F-PPA-REVENUE`
- **costs**：`F-TAX-EXCLUSIVE-AMOUNT`、`F-CAPEX-TOTAL`、`F-UNIT-INVESTMENT`、`F-ANNUAL-OPEX`、`F-OPEX-ESCALATION`、`F-STRAIGHT-LINE-DEPRECIATION`、`F-ASSET-BOOK-VALUE`、`F-TAXABLE-INCOME-PROJECT`、`F-TAXABLE-INCOME-EQUITY`、`F-INCOME-TAX-ACCRUAL`、`F-TAX-LOSS-BALANCE`、`F-TAX-CASH-BRIDGE`、`F-VAT-CREDIT-BALANCE`、`F-OTHER-CASH-TAXES`、`F-DEBT-BALANCE`、`F-DEBT-INTEREST`、`F-INTEREST-BALANCE`、`F-CAPEX-PAYMENT-BALANCE`、`F-CASH-TAX-TOTAL`、`F-CAPEX-ITEM-AMOUNT`
- **financial_metrics**：`F-CASH-RECEIPTS`、`F-PROJECT-CASH-FLOW`、`F-PROJECT-PRETAX-CASH-FLOW`、`F-EQUITY-AVAILABLE-CASH-FLOW`、`F-EQUITY-INVESTOR-CASH-FLOW`、`F-CASH-FUNDING-BALANCE`、`F-NPV`、`F-DATED-NPV`、`F-NOMINAL-REAL-RATE`、`F-IRR-PROJECT`、`F-IRR-EQUITY`、`F-CUMULATIVE-CASH-FLOW`、`F-STATIC-PAYBACK`、`F-DISCOUNTED-CUMULATIVE-CASH`、`F-DYNAMIC-PAYBACK`、`F-LIFECYCLE-COST`、`F-LCOE`、`F-CFADS`、`F-DEBT-SERVICE`、`F-DSCR`、`F-BREAK-EVEN-PRICE`、`F-WORST-CASH-YEAR`、`F-INVESTMENT-HURDLE-GAP`
- **scenarios**：`F-SINGLE-FACTOR-SENSITIVITY`、`F-SENSITIVITY-ELASTICITY`、`F-SCENARIO-METRIC`
- **storage (Phase8)**：`F-STORAGE-ENERGY-UPDATE`、`F-STORAGE-SOC`、`F-STORAGE-CHARGE-LIMIT`、`F-STORAGE-DISCHARGE-LIMIT`、`F-STORAGE-PV-BALANCE`、`F-STORAGE-LOAD-BALANCE`、`F-STORAGE-CYCLE-COUNT`

其中消纳平衡类F-CURTAILED-ENERGY等仍留3C；本轮只计算明确物理发电边界下的并网限额/限发损失，不伪造负荷匹配、自用、收入或财务成功。

## 6. 逐年重算、恢复与停机

每个资源区间、每个运营年均先更新DC性能，再按每台逆变器的明确DC分配转换、限幅并求和，之后重算共享变压器上限、AC/变压器/送出损失、站用、可用率、交付上限及限发。没有对已限幅的首年交付量简单乘衰减率。

首年初衰与上游PR包含标志互斥；分段率有完整无重叠覆盖。恢复规则关联原事件row_id/asset_id/年/天数，明确恢复目标与容量比例；performance_ceiling只作上限，不能生成目标。

缺日期只使用已声明的年初恢复/均匀等效停机场景。正常和停运两种状态**分别**重算所有瓶颈后时间加权；组件仅对未更换部分保留老化性能，逆变器停运必须有具体设备ID且容量比例一致。饱和反例实证：部分停运后仍限幅时不能错误扣减饱和输出，共享变压器瓶颈也同样重算。月度PR不足以作此重算时返回BLOCKED，不伪装真实时点。

## 7. 普通/闰年完整大时序实测

全部为完整原子信封的SYNTHETIC资源，先写D3、完整验证，再真实温度/DC/逆变器/损失/3运营年重算与逐行落盘；不是仅读取或求和负载。小JSON仍32MiB，所有输入文件规模均超该默认限制而使用已批准D3。

|输入行数|实际输入bytes|写入秒|完整读取验证+发电秒|Windows OS生命周期峰值MiB|输入+结果最终bytes|首年输出kWh|
|---|---|---|---|---|---|---|
|8760|65620138|44.578|96.859|431.86|100734033|3425598.000000|
|8784|65779888|42.921|88.985|436.74|103201429|2608848.000000|
|35040|260224518|167.172|343.766|436.74|408413963|2601720.000000|
|35136|260953209|167.531|351.110|436.74|400693915|3434983.200000|

表中内存是同一pytest进程在检查点观察到的Windows生命周期高水位，不是每个操作独占内存；完整CLI另实跑与API相同result_hash。磁盘为实际输入文件+输出文件并含receipt自身，不是估计数组长度。receipt的时间/内存采样终点明确为结果数据fsync后、receipt fsync前；完整调用耗时由外部测试另量。

预算每次显式设置并受D3硬上限校验，内存/墙钟/行数/输入/磁盘检查为**应用合作式限额，不是Windows OS硬隔离**。超限、中断、重复、缺口、缺数、错误单位/粒度、源过期、块篡改、不能覆盖和清理失败路径均由最终完整suite覆盖。两种真实时间轴跨年还验证：America/New_York资源年实际8784/8760小时；Asia/Almaty资源年实际8785/8760小时。完整性按站址年界转UTC的真实经过时长，不固定日历天数×24。

## 8. 案例输入、方法和真实性

两个案例均1MWp DC（2000块×500Wp）、800kWac（2台×400kWac）、DC/AC=1.25；可用面积9000m²、组件面积4000m²、显式GCR=0.5对应占地8000m²。屋顶独立检查荷载/剩余寿命/结构消防防水引用；地面不读取屋顶字段，独立检查土地/地勘/洪水与固定支架，严格PF>0及全售电边界。

合成资源年2025，Asia/Shanghai，每天06:00—18:00为1000W/m²，其他时段0；温度/风速及Sandia参数均明确SYNTHETIC，不是实测、TMY或行业推荐。25运营年按显式代表年重复情景；初衰2%、后续10%是压力测试输入，不作真实项目默认。第12年均匀替换50%组件、明确恢复目标0.99、上限1.00、等效停机10天；恢复量不是把上限当默认。

原始输入、方法、预算、真实结果、原始资源manifest、receipt与独立参考保存于`phase3b-cases/industrial_rooftop/`和`phase3b-cases/utility_scale_ground/`。大原子表及中间轨迹在持久目录，文件bytes/SHA及内容摘要详见final-execution-evidence。

## 9. 两类首年12个月实际结果（kWh）

|月|工商业屋顶可用、消纳前|地面可交付|
|---|---|---|
|1|290941.200000|220968.000000|
|2|262785.600000|199584.000000|
|3|290941.200000|220968.000000|
|4|281556.000000|213840.000000|
|5|290941.200000|220968.000000|
|6|281556.000000|213840.000000|
|7|290941.200000|220968.000000|
|8|290941.200000|220968.000000|
|9|281556.000000|213840.000000|
|10|290941.200000|220968.000000|
|11|281556.000000|213840.000000|
|12|290941.200000|220968.000000|

|指标|工商业屋顶|地面集中式|
|---|---|---|
|首年kWh|3425598.0000|2601720.0000000000|
|首年DC参考等效小时h|3425.598|2601.720000000|
|25年累计kWh|43420022.9522111451649045594923057121594242955301786308387673|40535082.2639562239686459259301394000369923760647323144972845|

这些仅是上述合成压力情景的计算结果，不能用作真实站址预可研投资结论。

## 10. 完整25年实际发电数组（kWh）

|运营年|工商业屋顶|地面集中式|
|---|---|---|
|1|3425598.000000|2601720.000000|
|2|3294541.137863|2601720.000000|
|3|2964219.784076|2601720.000000|
|4|2666930.565669|2587549.205985|
|5|2399370.269102|2327935.717787|
|6|2158566.002192|2094283.578408|
|7|1941842.161973|1883996.652967|
|8|1746790.705775|1694738.420071|
|9|1571244.395198|1524406.010464|
|10|1413252.715678|1371106.841817|
|11|1271060.204110|1233137.590035|
|12|2370261.348639|2299691.361371|
|13|2178079.203891|2113217.218504|
|14|1959404.043502|1901036.929054|
|15|1762596.399152|1710074.668548|
|16|1585469.519237|1538208.634093|
|17|1426055.327313|1383529.203084|
|18|1282582.554582|1244317.715176|
|19|1153457.059124|1119027.376058|
|20|1037244.113211|1006266.070852|
|21|932652.461890|904780.896167|
|22|838519.975701|813444.238950|
|23|753800.738131|731241.247455|
|24|677553.424318|657258.555110|
|25|608930.841886|590674.131999|

第12年恢复是明确同容量更换情景。表格只显示6位小数；唯一JSON保留引擎原精度，无显示舍入反写。

## 11. 首年损耗账簿与守恒（kWh）

|项|工商业屋顶|地面集中式|
|---|---|---|
|首年初衰|87600.000000|87600.000000|
|遮挡|42924.000000|42924.000000|
|积灰|42494.760000|42494.760000|
|积雪（显式零情景）|0.000000|0.000000|
|温度|308214.196814|308214.196814|
|失配|38987.670432|38987.670432|
|DC线路|38597.793728|38597.793728|
|逆变转换|76423.631581|76423.631581|
|逆变器限幅|240757.947446|240757.947446|
|AC线路|35040.000000|35040.000000|
|变压器|0.000000|34689.600000|
|送出线|0.000000|34342.704000|
|站用（仅可用PV扣除边界）|8760.000000|8760.000000|
|可利用率|34602.000000|33911.676960|
|变压器有功上限|0.000000|0.000000|
|并网/可用容量上限|0.000000|729256.019040|
|限发|0.000000|26280.000000|
|更换停运（首年无事件）|0.000000|0.000000|

损失按DC/逆变器/AC/交付侧隔离，温度可为低温增益负损失，不能简单叠加比例；已包含上游损失不重复扣。每条轨迹有各组DC/AC/削峰和完整损失，实际检查理想能量=损失合计+输出（月年合计同样守恒）。屋顶不拿上网限额限制全部可供自用电量，不在3B计算负荷匹配。

## 12. 独立数值误差、公式与中间血缘

项目参考使用独立Fraction链及独立libm exp温度因子，不调用生产函数生成expected；25年参考另独立滚动性能和两个停运状态。六个主案例观测到的最大年度绝对误差为**7.568136480415825250553412470E-11kWh**，小于1E-8kWh的独立参考断言；内部Decimal精度60位、各核/守恒容差另由D2记录。

血缘为原field/instance/source→规范输入→D2及hash→有效公式ID/version→温度/DC/每台逆变器/损失→月/年/生命周期→result_hash。逐行轨迹按canonical数组token流式hash，原块hash与全部轨迹行在持久化时再次核对。不是仅声明有hash字段。

## 13. 统一结果与复现

继续既有solar-pv-calculation-result/1.0.0；project_id、pv_type、input_hash、source_snapshot_id、method_config_hash（inputs及身份payload内）、scenario_id、run_id、result_hash、formula/version、period/boundary、来源/证据/限制均保留。序列化、反序列化、validate_result真实通过。

API输入和方法经过canonical JSON文件往返后，数值及result_hash相同；run_id/created_at变化不改业务hash；方法变化会重算并改变输入/来源/结果身份，Phase2原hash不被重写。两案例result_hash分别：

- 屋顶：`d693f292ab886b9d175b44d083e0f9517e599437c171389f5dba617b0fa371dc`
- 地面：`c36bdf22097be277e00433d06583ea5ef8ac1467aa86edc0c7a1be06dd1078f5`

根status仍PARTIAL，因为统一契约还包含未来阶段；能源指标真实CALCULATED、maturity为CALCULATED_SYNTHETIC。consumption/revenue/npv保持null+NOT_IMPLEMENTED；不伪造零收入、零税或现金流。

## 14. Phase2/3A、旧产品与编译回归

- 同一次final3完整光伏suite覆盖Phase2历史24个测试文件组：3014 passed、5 skipped。
- 覆盖Phase3A历史35个文件及共享方法扩展：3279 passed、6 skipped（含基础提交追加的方法回归；不能把该文件组计数误称原始3A的3277条）。这些是全量suite的重叠子集，不相加当独立总数。
- 旧产品完整命令含`packages/experts/wangbin-software-consultant/tests`：145 passed、5 skipped，未漏36项Expert测试。仅跑根tests得到109项的早期子集不作最终旧产品全量。
- 41个生产模块编译；源码CLI完整8760计算与Python API的结果hash相同。未生成正式Word/PDF/Excel或新WorkBuddy候选。
- 光伏6项、旧产品5项symlink skip均单列，junction/hardlink分支另有实际验证；skip不是通过。

## 15. 保护文件、隔离基线与敏感数据

四个用户文件始终不修改、不暂存、不提交；起始SHA-256见final-execution-evidence，开发/冻结/收集及提交前后复核。实时工作区保护检查保留实际exit1，原因恰为这四个用户已确认的改动，不将它改称全局clean或保护PASS。

原288保护集合除上述四个相对历史基线的授权差异外无漂移。隔离候选仅在副本中从原Git blob恢复其历史基线字节，未触碰实际用户文件；288项副本校验、冻结基线exit0；12冻结原件不变。固定历史Git夹具在独立scratch对象库，未重写用户仓库历史。

提交仅用明确光伏路径allowlist，diff检查、源/案例/报告凭据扫描及最终保护检查落盘；不执行reset/restore/checkout/clean/stash，不push/上传/部署/发布。

## 16. 已关闭问题与未关闭风险

独立审阅及实跑发现的停机/限幅不交换、中间计量边界、PF零值入口、receipt磁盘自计量、CLI目录路径、API/CLI引用顺序hash和净UTC偏移年时长问题均已修复，并由最终完整源码验收覆盖；失败和主动中止日志保留，不拼凑PASS。

保留风险/适用性：真实历史资源及国内接口仍Phase4；真实设备参数/结构/冷热组串设计引用和许可必须另核；无未批准的GHI→POA、跟踪器或异构设备分配猜测；日期未知仅作明示等效情景，多事件重叠/未知恢复阻断；月度PR只是明确计量边界的条件情景，不冒充精准削峰或交付；OS强制隔离与symlink权限分支仍未完成。上述风险不能升级为真实项目/公开服务/发布通过。

## 17. Phase3C交接（只交接口，不实施）

详见docs/solar-pv/25-phase3b-runtime-and-phase3c-handoff.md。屋顶交每时段AVAILABLE_PRE_CONSUMPTION可用电量及实际UTC区间；地面交GRID_DELIVERABLE；月/年/25年数组、源/方法/定义/内容hash及中间损失同时保留。未来先做来源和时间/粒度对齐，再执行原冻结消纳/价格/收入模型，不按行号配对或把NOT_IMPLEMENTED当零。

## 18. 发布门禁与停止

**仅PHASE3B_ENERGY_ENGINE_PASS。** PHASE3整体计算、真实来源、完整18章/四文件、目标运行时与WorkBuddy、平台审核和总发布保持BLOCKED/NOT_IMPLEMENTED。真实`verify_baseline.py --release`仍exit1，不改门禁凑通过。

本轮本地提交并读回准确SHA、四文件hash及清单后立即停止，等待用户下一步指令；不自动进入Phase3C。
