# 九类工程边界、隔离设计与独立验收

> 版本 `solar-pv-categories/1.0.0`。Phase 1冻结，不创建场景源码、schema、模板、fixture或测试文件。**以下九类及其schema/config/methodology/templates/tests/CLI/四文件E2E全部 `NOT_IMPLEMENTED`。** P0/P1/P2仅优先级，不是已实现/已验收状态。没有任一类型可标PASS或对外宣称支持。

## 1. 分类与不可借用的验收顺序

| pv_type（稳定枚举） | 名称 | 优先级/后续阶段 | 独立实现与验收状态 |
|---|---|---|---|
| `industrial_rooftop` | 工商业屋顶分布式 | P0，第一条端到端（Phase 2–5） | NOT_IMPLEMENTED |
| `utility_scale_ground` | 集中式地面 | P0，第二条独立端到端（Phase 6） | NOT_IMPLEMENTED |
| `agri_pv` | 农光互补 | P1，Phase 8独立扩展 | NOT_IMPLEMENTED |
| `fishery_pv` | 渔光互补 | P1，Phase 8独立扩展 | NOT_IMPLEMENTED |
| `pv_storage` | 光储一体 | P1，Phase 8独立扩展；依赖一个已验收的基础光伏类型 | NOT_IMPLEMENTED |
| `public_rooftop` | 公共建筑 | P2，Phase 8独立设计/开发；不得宣传已支持 | NOT_IMPLEMENTED |
| `residential_pv` | 户用 | P2，Phase 8独立设计/开发；不得宣传已支持 | NOT_IMPLEMENTED |
| `pv_carport_bipv` | 车棚/BIPV | P2，Phase 8独立设计/开发；车棚与BIPV子型分别验收 | NOT_IMPLEMENTED |
| `desert_mining` | 荒漠/矿区 | P2，Phase 8独立设计/开发；荒漠与矿区子型分别验收 | NOT_IMPLEMENTED |

先完成工商业屋顶，再完成集中式地面的独立端到端；两类间反向串用测试属于P0门禁。P1/P2每类另立开发审批及真实证据，不能按一张共享测试表一次标全场景PASS。任何尚未实现的分类，包括被选择的复合基座，必须返回 `NOT_IMPLEMENTED` 及后续路线，不做静默P0降级，不生成伪合格报告。

## 2. 共享接口与分类主权

| 可共享层 | 固定接口/参数边界 | 不能共享成默认事实的内容 |
|---|---|---|
| 验证/单位/来源 | 03的点式字段、值provenance信封、来源/冲突/许可、时区与单位系统 | 同一字段名不代表所有类型必填或同含义；禁止kWp/kWac/kWh/kVA互换 |
| 气象适配 | 数据集版本/覆盖/授权/误差、GHI/DNI/DHI/POA、时序 | 不能无依据对立面/水面/矿区用相同损失或默认PR |
| 基础财务 | 时间/币种、NPV/IRR、折现、现金流集合计算；注册公式 | 收入模式、税制、融资和含税/不含税边界由分类/主体/合同明确 |
| 公式注册/质量 | 05注册表ID与符号、量纲、边界、test_id；四态及成熟度 | 不为凑达标调参数；单个公式正确不能证明工程分类可行 |
| 导出/报告样式 | canonical result、18章13附录稳定ID、29个必需sheet、哈希/原子发布 | 分类专项模板/安全提示/附表不能仅改标题；所有章都保留 |
| 权限/隐私/日志 | 本地受限读取、授权、数据最小化、许可审查、脱敏审计 | 文档引擎/本地测试不是OS沙箱；不默认可远传商业附件 |

共享输入接口计划为 `normalized_inputs + provenance_records + source_snapshot + scenario_config`；分类方法学输出 `energy_ledger + engineering_constraints + revenue_items + cost_items + category_issues`，再交共享财务与canonical result组装。每项输出记录类型、工程/计量/税费边界、公式版本和上游字段，拒绝未知字段/错误分类配置，不用一个万能函数+名称替换。

AC/DC参数边界：装机DC、逆变AC、变压kVA、计量送出电量分别建模。税费参数边界：金额含税、销项/进项抵扣、实际税金、折旧非现金及主体适用税制独立。收入模型边界：全额售电、企业自用节省、PPA、租赁/分成、家庭/公共主体、储能收益分别选择明确方法。总投资、建设期利息、债务融资与股东现金流不重复。

## 3. 每类独立目录规划（仅路径契约，当前均不存在/NOT_IMPLEMENTED）

以 `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/<pv_type>/` 为计划根，每类必须分别具备 `schemas/`（专项原子字段与拒绝规则）、`config/`（无未经核实真实默认值）、`methodology/`（算法/边界/来源说明）、`templates/`（18章内容与专项图表）。场景测试规划为 `tests/solar-pv/scenarios/<pv_type>/`，不把共享测试通过算作专项通过。包内不复制商用机密附件；后续离线fixture明确SYNTHETIC且需独立参考结果。

| 分类 | schema规划路径 | config规划路径 | methodology规划路径 | template规划路径 | 专项tests规划路径 | 状态 |
|---|---|---|---|---|---|---|
| `industrial_rooftop` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/industrial_rooftop/schemas/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/industrial_rooftop/config/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/industrial_rooftop/methodology/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/industrial_rooftop/templates/` | `tests/solar-pv/scenarios/industrial_rooftop/` | NOT_IMPLEMENTED |
| `utility_scale_ground` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/utility_scale_ground/schemas/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/utility_scale_ground/config/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/utility_scale_ground/methodology/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/utility_scale_ground/templates/` | `tests/solar-pv/scenarios/utility_scale_ground/` | NOT_IMPLEMENTED |
| `agri_pv` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/agri_pv/schemas/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/agri_pv/config/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/agri_pv/methodology/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/agri_pv/templates/` | `tests/solar-pv/scenarios/agri_pv/` | NOT_IMPLEMENTED |
| `fishery_pv` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/fishery_pv/schemas/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/fishery_pv/config/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/fishery_pv/methodology/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/fishery_pv/templates/` | `tests/solar-pv/scenarios/fishery_pv/` | NOT_IMPLEMENTED |
| `pv_storage` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/pv_storage/schemas/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/pv_storage/config/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/pv_storage/methodology/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/pv_storage/templates/` | `tests/solar-pv/scenarios/pv_storage/` | NOT_IMPLEMENTED |
| `public_rooftop` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/public_rooftop/schemas/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/public_rooftop/config/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/public_rooftop/methodology/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/public_rooftop/templates/` | `tests/solar-pv/scenarios/public_rooftop/` | NOT_IMPLEMENTED |
| `residential_pv` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/residential_pv/schemas/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/residential_pv/config/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/residential_pv/methodology/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/residential_pv/templates/` | `tests/solar-pv/scenarios/residential_pv/` | NOT_IMPLEMENTED |
| `pv_carport_bipv` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/pv_carport_bipv/schemas/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/pv_carport_bipv/config/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/pv_carport_bipv/methodology/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/pv_carport_bipv/templates/` | `tests/solar-pv/scenarios/pv_carport_bipv/` | NOT_IMPLEMENTED |
| `desert_mining` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/desert_mining/schemas/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/desert_mining/config/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/desert_mining/methodology/` | `services/solar-pv-engine/src/wangbin_solar_pv/scenarios/desert_mining/templates/` | `tests/solar-pv/scenarios/desert_mining/` | NOT_IMPLEMENTED |

## 4. 九类逐项方法学与独立验收设计

### CAT01 `industrial_rooftop`：工商业屋顶分布式

- **优先级/依赖**：P0，第一条端到端（Phase 2–5）。
- **专项输入**：roof.*、site.rights_*、load.monthly_bills.*、load.series.*、tariff.*、grid.*、capex/opex租金与加固。完整原子字段与来源义务见03，不仅是本段组名。
- **方法学与收益边界**：以产权/结构/荷载/遮挡及剩余屋面年限限定布局；同粒度发电和企业负荷匹配；仅实际可避免的购电费作为自用收益，分时电价、PPA/分成/租赁独立结算。年总量不能产生真实自用率。允许全额上网但需切换明确售电模型，不强行套自用。
- **工程/成本/合规差异**：分布式接入、变压器及上网限制；屋顶荷载、消防、防水、检修及生产协同；加固与屋租独立成本。
- **明确禁止**：禁止把年账单均价当可避免费；禁止无曲线宣称高自用率；不得因不需新土地而省略权属/结构核查。
- **章节和模板**：CH01…CH18及APP01…APP13全部保留；按02第3节该类逐章矩阵展开，不适用只限具体子项并给理由。按10保留19+10个sheet，专项附表可追加不可替代核心sheet。
- **当前状态**：schema/config/methodology/templates/tests/E2E均NOT_IMPLEMENTED；下列测试是未来设计，并非已运行证据。

| 独立未来测试ID | 验收对象及可测断言 | 状态 |
|---|---|---|
| T-CAT-ROOF-ENERGY | 显式虚构1MWp算例，8760/15分钟真实粒度fixture设计；每时段自用+上网+限发守恒，月年一致。 | NOT_IMPLEMENTED |
| T-CAT-ROOF-LOAD-GAP | 只有年电量/城市/面积/预算，无负荷及并网意见：真实自用率UNKNOWN，条件接入且暂缓，不补造。 | NOT_IMPLEMENTED |
| T-CAT-ROOF-PRICE | 峰谷/PPA/租金/分成与不可抵减需量费分开，合同边界无重复收入。 | NOT_IMPLEMENTED |
| T-CAT-ROOF-SAFETY | 结构/产权/消防否决或严重未知优先于高IRR；屋面寿命短于项目期需更换/租期限制。 | NOT_IMPLEMENTED |
| T-CAT-ROOF-FINANCE | 显式25年及用户其他年限，全周期项目/股东现金流独立参考校验与折旧税DSCR。 | NOT_IMPLEMENTED |
| T-CAT-ROOF-EXPORT | 相同屋顶切全额售电时不得保留企业购电节省；无债务附录保留不适用。 | NOT_IMPLEMENTED |

### CAT02 `utility_scale_ground`：集中式地面

- **优先级/依赖**：P0，第二条独立端到端（Phase 6）。
- **专项输入**：site.land_classification、site.boundary_vertices.*、site.terrain_slope、site.geotechnical_reference、grid.upgrade_plan、grid.line_length、tariff.market_series.*、capex.items.*。完整原子字段与来源义务见03，不仅是本段组名。
- **方法学与收益边界**：土地边界、坡度/地勘、排布、道路和基础驱动容量及投资；集中式集电/升压/送出纳入AC交付边界；市场交易售电及限发独立情景。无自用负荷时采用全额售电，不借工商业购电价。
- **工程/成本/合规差异**：土地性质和用地权；支架/道路/排水/防洪/基础，集电线路、升压站、送出工程及集中式接入。
- **明确禁止**：屋顶荷载不能替代地勘/土地合规；禁止沿用工商业自用节省收入；禁止漏送出成本而虚高IRR。
- **章节和模板**：CH01…CH18及APP01…APP13全部保留；按02第3节该类逐章矩阵展开，不适用只限具体子项并给理由。按10保留19+10个sheet，专项附表可追加不可替代核心sheet。
- **当前状态**：schema/config/methodology/templates/tests/E2E均NOT_IMPLEMENTED；下列测试是未来设计，并非已运行证据。

| 独立未来测试ID | 验收对象及可测断言 | 状态 |
|---|---|---|
| T-CAT-GROUND-LAND | 用地性质/边界/坡度/地勘独立输入，非法或未决不以屋顶schema通过。 | NOT_IMPLEMENTED |
| T-CAT-GROUND-EXPORT | 集中式全额交易与极端限发，电量平衡及负电价有依据结算。 | NOT_IMPLEMENTED |
| T-CAT-GROUND-CAPEX | 集电/升压/送出/道路/基础/地租完整，报价有效期及含税口径核查。 | NOT_IMPLEMENTED |
| T-CAT-GROUND-TIME | 用户指定评价期含建设期现金流、延期送出、更换和闰年时数。 | NOT_IMPLEMENTED |
| T-CAT-GROUND-CROSS | 同资源同容量与屋顶对照：售电模型、土地/结构、CAPEX隔离；互传专属字段应拒绝。 | NOT_IMPLEMENTED |
| T-CAT-GROUND-FINANCE | 独立参考项目/股权NPV/IRR/回收期/LCOE/税折旧/DSCR，不使用屋顶golden值改标题。 | NOT_IMPLEMENTED |

### CAT03 `agri_pv`：农光互补

- **优先级/依赖**：P1，Phase 8独立扩展。
- **专项输入**：agri.*、site.land_classification、layout.row_pitch、layout.tilt、capex.items.*及基础地面工程字段。完整原子字段与来源义务见03，不仅是本段组名。
- **方法学与收益边界**：先农业生产与用地合规，再透光率/行距/农机净高和灌溉约束；布局、遮挡发电及高支架基础成本联动；农业收入除有独立合同和明确边界外不进入光伏收益。
- **工程/成本/合规差异**：农业持续生产、耕作通道、透光/产量影响依据、支架基础及灌溉条件；不是地面标题替换。
- **明确禁止**：禁止假定农地产权合规或作物产量不受影响；不得虚构农业增产、补贴或多计农业收益。
- **章节和模板**：CH01…CH18及APP01…APP13全部保留；按02第3节该类逐章矩阵展开，不适用只限具体子项并给理由。按10保留19+10个sheet，专项附表可追加不可替代核心sheet。
- **当前状态**：schema/config/methodology/templates/tests/E2E均NOT_IMPLEMENTED；下列测试是未来设计，并非已运行证据。

| 独立未来测试ID | 验收对象及可测断言 | 状态 |
|---|---|---|
| T-CAT-AGRI-COMPLIANCE | 农业用地不合规或生产证据不足时独立否决/暂缓。 | NOT_IMPLEMENTED |
| T-CAT-AGRI-LIGHT | 行距/透光/农机净空约束改变可用容量及电量；不只改描述文字。 | NOT_IMPLEMENTED |
| T-CAT-AGRI-COST | 高支架/基础/农业保护额外费用进入CAPEX/OPEX且有依据。 | NOT_IMPLEMENTED |
| T-CAT-AGRI-REVENUE | 农业与光伏收入分账；无合同农业收入保持UNKNOWN而非默认增产。 | NOT_IMPLEMENTED |
| T-CAT-AGRI-ISOLATION | 不带农业专项字段的集中式输入不能直接通过农光schema。 | NOT_IMPLEMENTED |
| T-CAT-AGRI-E2E | 独立显式虚构场景，18章13附录和四文件数值、农业生产限制与建议一致。 | NOT_IMPLEMENTED |

### CAT04 `fishery_pv`：渔光互补

- **优先级/依赖**：P1，Phase 8独立扩展。
- **专项输入**：fishery.*、site.rights_*、site.flood_reference、system.mounting_type及基础接入/投资字段。完整原子字段与来源义务见03，不仅是本段组名。
- **方法学与收益边界**：水域权属/养殖与水位水深限制先决；水域基础、防腐、施工和维护可达性对布局成本/损失建模；养殖影响按证据，水面环境效应不得无依据当发电增益。
- **工程/成本/合规差异**：水域使用和养殖权、腐蚀、水上施工/运维、水质和渔业生产；岸上接入工程独立。
- **明确禁止**：禁止用普通地面基础造价覆盖水域施工；禁止以光伏利润抵消水权或水质/生产合规红线。
- **章节和模板**：CH01…CH18及APP01…APP13全部保留；按02第3节该类逐章矩阵展开，不适用只限具体子项并给理由。按10保留19+10个sheet，专项附表可追加不可替代核心sheet。
- **当前状态**：schema/config/methodology/templates/tests/E2E均NOT_IMPLEMENTED；下列测试是未来设计，并非已运行证据。

| 独立未来测试ID | 验收对象及可测断言 | 状态 |
|---|---|---|
| T-CAT-FISHERY-RIGHTS | 水权/养殖权过期冲突及缺证时独立分级与建议。 | NOT_IMPLEMENTED |
| T-CAT-FISHERY-WATER | 水深/水位/防洪改变支架基础与施工条件，未知不假定稳定。 | NOT_IMPLEMENTED |
| T-CAT-FISHERY-CORROSION | 防腐等级、维护与寿命成本关联；缺证不可声称适用认证。 | NOT_IMPLEMENTED |
| T-CAT-FISHERY-PRODUCTION | 水质与养殖影响、收入排他性，无依据不造收益或提升效率。 | NOT_IMPLEMENTED |
| T-CAT-FISHERY-ISOLATION | 普通地面或农光字段不能满足渔光专项schema。 | NOT_IMPLEMENTED |
| T-CAT-FISHERY-E2E | 独立水域虚构案例全期数值/四文件验收及水上安全视觉说明。 | NOT_IMPLEMENTED |

### CAT05 `pv_storage`：光储一体

- **优先级/依赖**：P1，Phase 8独立扩展；依赖一个已验收的基础光伏类型。
- **专项输入**：storage.*全部原子字段、load.series.*、resource.timeseries.*、tariff.market_series/periods、有效调度与并网合同。完整原子字段与来源义务见03，不仅是本段组名。
- **方法学与收益边界**：按storage.base_pv_type组合场址schema，但新增独立能量/SOC/效率/功率/循环与日历衰减、调度和收益模块；AC/DC耦合明确，网充许可/购电、套利、自用节省及合同收益互斥或有依据分账。
- **工程/成本/合规差异**：电池/PCS/耦合、消防隔离、并网双向约束、循环寿命/可用容量/更换和处置；不以光伏PR吸收储能损失。
- **明确禁止**：不得直接使用无储能min(发电,负荷)公式代表系统；禁止同时充放电、免费网充、跨期凭空能量、首尾SOC不同免费消耗、重复售电/自用收益。
- **章节和模板**：CH01…CH18及APP01…APP13全部保留；按02第3节该类逐章矩阵展开，不适用只限具体子项并给理由。按10保留19+10个sheet，专项附表可追加不可替代核心sheet。
- **当前状态**：schema/config/methodology/templates/tests/E2E均NOT_IMPLEMENTED；下列测试是未来设计，并非已运行证据。

| 独立未来测试ID | 验收对象及可测断言 | 状态 |
|---|---|---|
| T-CAT-STORAGE-BALANCE | PV/负荷/电网/电池每节点及全系统能量守恒，充放效率和辅机自放电独立。 | NOT_IMPLEMENTED |
| T-CAT-STORAGE-SOC | 初始/最小/最大/终端SOC及功率×时长边界，跨日年时段连续。 | NOT_IMPLEMENTED |
| T-CAT-STORAGE-GRID | 网充禁止/允许/待核，负电价合同与输入购电成本、上网约束可核验。 | NOT_IMPLEMENTED |
| T-CAT-STORAGE-DEGRADE | 循环与日历衰减后可用容量下降，SOC按当期容量定义，更换恢复及残值现金流一致。 | NOT_IMPLEMENTED |
| T-CAT-STORAGE-REVENUE | 光伏直接自用、储能放电自用/售电、网充成本和其他合同收益不重复；预知未来价格假设披露。 | NOT_IMPLEMENTED |
| T-CAT-STORAGE-E2E | 独立小时/15分钟场景及三种基座输入拒绝/组合测试，四文件含SOC图和逐期分账。 | NOT_IMPLEMENTED |

### CAT06 `public_rooftop`：公共建筑

- **优先级/依赖**：P2，Phase 8独立设计/开发；不得宣传已支持。
- **专项输入**：public.*、roof.*、公共建筑使用时段负荷、公共资产/采购/预算审批及计量合同。完整原子字段与来源义务见03，不仅是本段组名。
- **方法学与收益边界**：公共资产权利与采购预算先决；学校/医院/机关等使用节律驱动时序消纳；税费/资金主体按真实适用规则，不复用企业税负默认。
- **工程/成本/合规差异**：公共人员消防疏散、使用不中断、屋顶结构与检修、公共资产授权。
- **明确禁止**：禁止把公共建筑当普通企业屋顶改名；公共预算审批或授权不能由财务回报替代。
- **章节和模板**：CH01…CH18及APP01…APP13全部保留；按02第3节该类逐章矩阵展开，不适用只限具体子项并给理由。按10保留19+10个sheet，专项附表可追加不可替代核心sheet。
- **当前状态**：schema/config/methodology/templates/tests/E2E均NOT_IMPLEMENTED；下列测试是未来设计，并非已运行证据。

| 独立未来测试ID | 验收对象及可测断言 | 状态 |
|---|---|---|
| T-CAT-PUBLIC-ASSET | 缺公共资产授权或采购核验时暂缓/否决。 | NOT_IMPLEMENTED |
| T-CAT-PUBLIC-LOAD | 寒暑假/昼夜等实际曲线与企业模板不同；无曲线不造消纳。 | NOT_IMPLEMENTED |
| T-CAT-PUBLIC-FIRE | 公共人员消防疏散重大未决独立阻断。 | NOT_IMPLEMENTED |
| T-CAT-PUBLIC-TAX | 资金主体税制/预算/融资规则实际适用而非企业默认。 | NOT_IMPLEMENTED |
| T-CAT-PUBLIC-ISOLATION | 工业屋顶schema通过不代表公共建筑通过。 | NOT_IMPLEMENTED |
| T-CAT-PUBLIC-E2E | 独立公共建筑虚构场景、18章13附录、全四文件和授权资料追溯。 | NOT_IMPLEMENTED |

### CAT07 `residential_pv`：户用

- **优先级/依赖**：P2，Phase 8独立设计/开发；不得宣传已支持。
- **专项输入**：residential.*、适用户用产权/荷载与低压接入、家庭负荷与零售售电合同。完整原子字段与来源义务见03，不仅是本段组名。
- **方法学与收益边界**：产权/共有人同意、户用合同及低压接入先决；家庭时序用电、当地适用零售/上网价格独立；家庭税务/贷款/分期按主体实际处理。
- **工程/成本/合规差异**：屋面、居民安全、低压保护/接入、消费者合同与维保；不用工业PPA默认。
- **明确禁止**：禁止默认企业可避免费/税制/三班负荷适用于居民；不得承诺收益或补贴。
- **章节和模板**：CH01…CH18及APP01…APP13全部保留；按02第3节该类逐章矩阵展开，不适用只限具体子项并给理由。按10保留19+10个sheet，专项附表可追加不可替代核心sheet。
- **当前状态**：schema/config/methodology/templates/tests/E2E均NOT_IMPLEMENTED；下列测试是未来设计，并非已运行证据。

| 独立未来测试ID | 验收对象及可测断言 | 状态 |
|---|---|---|
| T-CAT-HOME-RIGHTS | 共有人同意/房屋权利欠缺及合同风险独立判定。 | NOT_IMPLEMENTED |
| T-CAT-HOME-GRID | 低压接入保护与许可缺失条件处理。 | NOT_IMPLEMENTED |
| T-CAT-HOME-LOAD | 家庭白天低负荷/周末差异真实匹配及年电量不足降级。 | NOT_IMPLEMENTED |
| T-CAT-HOME-CONTRACT | 租赁/贷款/安装/售电合同收益与消费者风险不重计。 | NOT_IMPLEMENTED |
| T-CAT-HOME-ISOLATION | 企业税率/工业分时电价/负荷模板不得泄漏到户用。 | NOT_IMPLEMENTED |
| T-CAT-HOME-E2E | 独立户用虚构案例项目/家庭资金现金流、四文件及隐私审查。 | NOT_IMPLEMENTED |

### CAT08 `pv_carport_bipv`：车棚/BIPV

- **优先级/依赖**：P2，Phase 8独立设计/开发；车棚与BIPV子型分别验收。
- **专项输入**：carport_bipv.*、屋顶/立面或地面适用基座字段、建筑荷载/净空/认证/围护和充电负荷。完整原子字段与来源义务见03，不仅是本段组名。
- **方法学与收益边界**：子型决定围护功能、发电平面与损失；车棚净空排水和充电负荷分账；BIPV增量成本仅对可证实替代建材扣减，建筑功能与电力功能分别说明。
- **工程/成本/合规差异**：建筑防水、防火、抗风、认证与联合验收；立面不能套固定屋顶倾角；车棚不必与屋面同权属。
- **明确禁止**：不能把组件当已认证建材；不能同时全额计建材替代收益又重复扣成本；不能把充电收入全归光伏。
- **章节和模板**：CH01…CH18及APP01…APP13全部保留；按02第3节该类逐章矩阵展开，不适用只限具体子项并给理由。按10保留19+10个sheet，专项附表可追加不可替代核心sheet。
- **当前状态**：schema/config/methodology/templates/tests/E2E均NOT_IMPLEMENTED；下列测试是未来设计，并非已运行证据。

| 独立未来测试ID | 验收对象及可测断言 | 状态 |
|---|---|---|
| T-CAT-BIPV-SUBTYPE | 车棚/屋面BIPV/立面BIPV各schema分支，子型未知不得同一模型。 | NOT_IMPLEMENTED |
| T-CAT-BIPV-BUILDING | 防水耐火抗风/认证重大未知或不合格阻断。 | NOT_IMPLEMENTED |
| T-CAT-BIPV-RESOURCE | 立面方位/倾角与遮挡改变POA和电量，非标题替换。 | NOT_IMPLEMENTED |
| T-CAT-BIPV-COST | 全额成本与增量/替代建材边界交叉核验无重复。 | NOT_IMPLEMENTED |
| T-CAT-BIPV-EV | 充电设施实际用电/运营收入/电价计量独立，不把全部收费当PV收益。 | NOT_IMPLEMENTED |
| T-CAT-BIPV-E2E | 三个子型分别四文件、净空/建筑功能专项附表及视觉验收。 | NOT_IMPLEMENTED |

### CAT09 `desert_mining`：荒漠/矿区

- **优先级/依赖**：P2，Phase 8独立设计/开发；荒漠与矿区子型分别验收。
- **专项输入**：desert_mining.*、土地/地勘/气象积尘/送出、生态修复义务及费用。完整原子字段与来源义务见03，不仅是本段组名。
- **方法学与收益边界**：子型决定生态/矿安/采空沉降限制；风沙积尘与清洗水约束进入损失和运维；复垦恢复费用及长送出工程独立；不把修复义务变成未经合同支持的收益。
- **工程/成本/合规差异**：地质沉降、矿区安全、荒漠生态、抗风沙、供水、道路与远距离送出。
- **明确禁止**：普通集中式合格不代表矿区安全/修复合规；无依据不能默认积尘小/水免费/修复无费用。
- **章节和模板**：CH01…CH18及APP01…APP13全部保留；按02第3节该类逐章矩阵展开，不适用只限具体子项并给理由。按10保留19+10个sheet，专项附表可追加不可替代核心sheet。
- **当前状态**：schema/config/methodology/templates/tests/E2E均NOT_IMPLEMENTED；下列测试是未来设计，并非已运行证据。

| 独立未来测试ID | 验收对象及可测断言 | 状态 |
|---|---|---|
| T-CAT-DESERT-SUBTYPE | 荒漠/在产矿/关闭矿分别准入与禁限规则。 | NOT_IMPLEMENTED |
| T-CAT-DESERT-SAFETY | 采空沉降/矿安或生态红线独立否决/暂缓。 | NOT_IMPLEMENTED |
| T-CAT-DESERT-DUST | 风沙/积尘/水约束联动电量损失和清洗OPEX。 | NOT_IMPLEMENTED |
| T-CAT-DESERT-RESTORE | 复垦修复责任及终期费用进入现金流与政策核验。 | NOT_IMPLEMENTED |
| T-CAT-DESERT-EXPORT | 长送出/道路投资损失与限发，不能漏项提高IRR。 | NOT_IMPLEMENTED |
| T-CAT-DESERT-E2E | 荒漠/矿区子型独立场景和四文件，不接受普通地面换标题。 | NOT_IMPLEMENTED |

## 5. 光储不可复用无储能平衡的独立边界

以下是待实现的方法学验收边界，不代表已有计算器或已验证公式；正式公式ID/全部符号与test_id由05统一注册。

1. 时段长度Δt由真实时间戳取得，功率约束转换为 `充/放电量 <= 对应kW上限 × Δt小时`。分别记录PV直用、PV充电、PV上网、PV限发，电网直接供负荷/网充，电池向负荷/向网放电，辅机/自放电与转换损耗，统一kWh/时段。
2. 电池期末储能=期初储能+充电入端电量×单向充电效率−放电出端电量/单向放电效率−自放电及定义在该边界的辅机损耗。不同耦合位置明确PCS/DC损耗是否已包含，不能再用“往返效率”重复扣损。
3. SOC=该时段电池储能/当期可用容量；0<=最小SOC<=初始/终端SOC<=最大SOC<=1。可用容量随日历/循环衰减变，不能用永远不变标称容量隐藏越界；分母为0应失败，不得造SOC。
4. 时段连续、跨日/跨年状态衔接。终端SOC按合同/情景约束，与初始不同时必须披露净耗用及经济处理，不能靠免费耗尽初始电池提高收益。禁止同时充放电，例外需专门物理/合同证据和独立方法审批。
5. PV能量、购电能量、电池能量与用户负荷/售电分别守恒；网充要计购电及税费，禁止将同一kWh同时计PV直接自用和电池放电自用、两次售电或未扣购电的套利。自用率分母/分子说明是否计电池路径，不把网充放电算PV自用。
6. 循环定义、计量口、退化、容量衰减、停机更换、回收处置、消防成本、辅机用电和额外收益合同分别记录。目标调度不得无披露假设完美未来价格/负荷；所谓优化收益需可重现调度输入与算法。
7. 需要独立能量/SOC/调度单元测试、时序集成、退化与现金流勾稽、反例及四文件E2E。缺少时序/许可/已实现基座则NOT_IMPLEMENTED或资料BLOCKED，不提供无储能替代结果冒充配储结果。

## 6. 共同但逐类执行的门禁

| 门禁ID | 每类必须单独执行的内容 | 状态 |
|---|---|---|
| CAT-G01 | 专项schema字段、类型、条件必填、provenance、未知/冲突/拒绝越界；跨类专属输入反向隔离 | NOT_IMPLEMENTED |
| CAT-G02 | 专项工程布局与能量/收益/成本差异；与独立计算程序或手工参考值比较 | NOT_IMPLEMENTED |
| CAT-G03 | 用户指定年限全期项目/股东/税折旧/债务与替换闭合，IRR无根/多根/期内不回本/零偿债分母 | NOT_IMPLEMENTED |
| CAT-G04 | 资料不足、API失败/许可不清/过期政策、错误单位、无负荷和无并网意见安全降级 | NOT_IMPLEMENTED |
| CAT-G05 | 18章100子项、13附录26子项、该类逐章矩阵、公式符号、术语和专项附表实际内容 | NOT_IMPLEMENTED |
| CAT-G06 | 每类四文件实物打开/重算边界/同源/安全/原子发布/视觉一致；不能借其他类别四文件 | NOT_IMPLEMENTED |
| CAT-G07 | 法律/安全否决、严重未决、目标未达、非关键条件和下一阶段四态与L1/L2/L3证据成熟度 | NOT_IMPLEMENTED |
| CAT-G08 | WorkBuddy运行依赖与能力范围按实际实现声明；安装/调用/平台审核独立证据 | NOT_IMPLEMENTED |

失败只影响相应能力及依赖组合；不能为维持总PASS隐去某类失败。工商业屋顶PASS只代表该类已验收配置，不代表地面、农渔、储能、公共、户用、建筑、荒漠矿区可用。每类变更重跑共享回归与该类专项，按影响依赖重验其他类。

## 7. Phase停止点与后续批准

当前只冻结规划。Phase 2先实现工商业输入契约，Phase 3纯离线显式虚构数值与独立参考，Phase 4真实受许可数据适配，Phase 5工业屋顶四文件实物，Phase 6地面独立链路，Phase 7真实WorkBuddy封装/调用，Phase 8分别扩类。任何后续源码、fixture、测试、付费API、远端上传、平台审核或部署需主任务阶段授权，本轮不执行。平台不支持Expert自动调Skill时提供真实能力分离，不能绕过已有禁止skills字段规则或虚构调用链。
