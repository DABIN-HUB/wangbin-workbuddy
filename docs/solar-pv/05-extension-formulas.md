# 公式扩展：光储、布局、年均、减排与工程核对

本文件与`05-formula-extensions.json`同源；与77条基础注册表合并构成公式目录。当前仅方法设计，全部算法及数值测试PLANNED；不表示Phase8已开发。第07分类文档中的光储文字等式逐一回链本表。所有公式字段通过`05-field-bindings.json`闭合到03输入目录或显式计算账簿，绝不把中间计算状态充作用户已提供数据。

## F-STORAGE-ENERGY-UPDATE 储能时段储能更新

英文全称：Battery stored energy update。

`B_(t+1) = B_t + eta_ch × E_ch,t − E_dis,t / eta_dis − E_sd,t − E_aux,t`

| 符号 | 定义 | 单位 | 字段 |
|---|---|---|---|
| B_(t+1) | 相邻时段末电池内能量 | kWh | storage.state_energy_end |
| B_t | 时段初电池内能量 | kWh | storage.state_energy_begin |
| eta_ch | 充电单向效率 | 1 | storage.charge_efficiency |
| E_ch,t | 充电端输入电量 | kWh/时段 | storage.charge_input |
| E_dis,t | 放电端交付电量 | kWh/时段 | storage.discharge_output |
| eta_dis | 放电单向效率 | 1 | storage.discharge_efficiency |
| E_sd,t | 电池内能量边界自放电损失 | kWh/时段 | storage.self_discharge_energy |
| E_aux,t | 本边界从电池内扣除的辅机电量 | kWh/时段 | storage.internal_auxiliary_energy |

下标/上标/范围：{"t": "按同一时区排序且无重漏的时段索引；t+1为相邻时段末/下一时段初", "y": "评价期运营年，从1开始；构建年时间另登记", "标签": "PV光伏，grid电网，self自用，exp外送，curt限发，ch充电，dis放电，aux辅机，use可用，nom铭牌，min/max上下界；仅本式出现者生效，不是相乘字母"}；上标如出现仅表示指数/边界标签；本条无未定义上标；t∈T；T为实际覆盖、时长/时区一致的有限时段集合。y=1..N，N为project.evaluation_years；本式未出现的集合不参与计算。

计算边界：独立储能模型；充/放电量端口明示，PCS已含效率不重扣；外部供电辅机不能再扣电池内能量。
假设：0<效率≤1；时段连续；充放电互斥；不能用无储能min模型代表光储。
来源：USER-BASELINE相关工程/分类/输出要求与物理代数定义；不是已读标准条款。输出字段：`storage.state_energy_end`。
章节：CH07, CH08, CH10；阶段：Phase 8；未来测试：`T-STORAGE-ENERGY-UPDATE` PLANNED。
验证方式：独立推导/参考算法、单位及相应边界/能量或成本守恒；不以相同引擎生成expected。

## F-STORAGE-SOC 储能荷电状态

英文全称：Battery state of charge。

`SOC_t = B_t / C_use,t`

| 符号 | 定义 | 单位 | 字段 |
|---|---|---|---|
| SOC_t | 按当期可用容量定义的荷电状态 | 1 | storage.soc |
| B_t | 电池内储能 | kWh | storage.state_energy_begin |
| C_use,t | 同一时段退化后的可用能量容量 | kWh | storage.available_capacity |

下标/上标/范围：{"t": "按同一时区排序且无重漏的时段索引；t+1为相邻时段末/下一时段初", "y": "评价期运营年，从1开始；构建年时间另登记", "标签": "PV光伏，grid电网，self自用，exp外送，curt限发，ch充电，dis放电，aux辅机，use可用，nom铭牌，min/max上下界；仅本式出现者生效，不是相乘字母"}；上标如出现仅表示指数/边界标签；本条无未定义上标；t∈T；T为实际覆盖、时长/时区一致的有限时段集合。y=1..N，N为project.evaluation_years；本式未出现的集合不参与计算。

计算边界：当前可用容量分母，非始终不变铭牌容量。
假设：C_use,t>0；SOC_min≤SOC_t≤SOC_max；初始终端SOC独立条件，净耗用须入经济处理。
来源：USER-BASELINE相关工程/分类/输出要求与物理代数定义；不是已读标准条款。输出字段：`storage.soc`。
章节：CH07, CH10；阶段：Phase 8；未来测试：`T-STORAGE-SOC` PLANNED。
验证方式：独立推导/参考算法、单位及相应边界/能量或成本守恒；不以相同引擎生成expected。

## F-STORAGE-CHARGE-LIMIT 储能充电能量上限

英文全称：Battery charge energy limit。

`E_ch,max,t = P_ch,max,t × delta_t`

| 符号 | 定义 | 单位 | 字段 |
|---|---|---|---|
| E_ch,max,t | 输入边界单时段最大充电量 | kWh/时段 | storage.charge_energy_limit |
| P_ch,max,t | 同边界充电功率限制 | kW | storage.charge_power |
| delta_t | 时段实际持续时间 | h | time.interval_hours |

下标/上标/范围：{"t": "按同一时区排序且无重漏的时段索引；t+1为相邻时段末/下一时段初", "y": "评价期运营年，从1开始；构建年时间另登记", "标签": "PV光伏，grid电网，self自用，exp外送，curt限发，ch充电，dis放电，aux辅机，use可用，nom铭牌，min/max上下界；仅本式出现者生效，不是相乘字母"}；上标如出现仅表示指数/边界标签；本条无未定义上标；t∈T；T为实际覆盖、时长/时区一致的有限时段集合。y=1..N，N为project.evaluation_years；本式未出现的集合不参与计算。

计算边界：功率/能量上限同时受SOC可用裕量和变流器边界限制。
假设：实际E_ch不超过本上限及SOC能量裕量；不把kW直接当kWh。
来源：USER-BASELINE相关工程/分类/输出要求与物理代数定义；不是已读标准条款。输出字段：`storage.charge_energy_limit`。
章节：CH07, CH10；阶段：Phase 8；未来测试：`T-STORAGE-CHARGE-LIMIT` PLANNED。
验证方式：独立推导/参考算法、单位及相应边界/能量或成本守恒；不以相同引擎生成expected。

## F-STORAGE-DISCHARGE-LIMIT 储能放电能量上限

英文全称：Battery discharge energy limit。

`E_dis,max,t = P_dis,max,t × delta_t`

| 符号 | 定义 | 单位 | 字段 |
|---|---|---|---|
| E_dis,max,t | 输出边界单时段最大放电量 | kWh/时段 | storage.discharge_energy_limit |
| P_dis,max,t | 输出边界放电功率限制 | kW | storage.discharge_power |
| delta_t | 时段实际持续时间 | h | time.interval_hours |

下标/上标/范围：{"t": "按同一时区排序且无重漏的时段索引；t+1为相邻时段末/下一时段初", "y": "评价期运营年，从1开始；构建年时间另登记", "标签": "PV光伏，grid电网，self自用，exp外送，curt限发，ch充电，dis放电，aux辅机，use可用，nom铭牌，min/max上下界；仅本式出现者生效，不是相乘字母"}；上标如出现仅表示指数/边界标签；本条无未定义上标；t∈T；T为实际覆盖、时长/时区一致的有限时段集合。y=1..N，N为project.evaluation_years；本式未出现的集合不参与计算。

计算边界：与SOC/功率下限和端口效率共同验收。
假设：实际放电不能超过SOC储能和边界上限；不免费耗尽初始SOC。
来源：USER-BASELINE相关工程/分类/输出要求与物理代数定义；不是已读标准条款。输出字段：`storage.discharge_energy_limit`。
章节：CH07, CH10；阶段：Phase 8；未来测试：`T-STORAGE-DISCHARGE-LIMIT` PLANNED。
验证方式：独立推导/参考算法、单位及相应边界/能量或成本守恒；不以相同引擎生成expected。

## F-STORAGE-PV-BALANCE 光储光伏节点守恒

英文全称：PV node energy balance。

`E_pv,t = E_direct,t + E_pv_ch,t + E_pv_exp,t + E_curt,t`

| 符号 | 定义 | 单位 | 字段 |
|---|---|---|---|
| E_pv,t | 光伏交付至耦合节点电量 | kWh/时段 | energy.available_kwh |
| E_direct,t | 直接向负荷交付的PV电量 | kWh/时段 | storage.pv_direct_load |
| E_pv_ch,t | 同节点向充电端交付电量 | kWh/时段 | storage.pv_charge |
| E_pv_exp,t | PV直接外送电量 | kWh/时段 | storage.pv_direct_export |
| E_curt,t | 同节点可用但受约束限发电量 | kWh/时段 | consumption.curtailed_kwh |

下标/上标/范围：{"t": "按同一时区排序且无重漏的时段索引；t+1为相邻时段末/下一时段初", "y": "评价期运营年，从1开始；构建年时间另登记", "标签": "PV光伏，grid电网，self自用，exp外送，curt限发，ch充电，dis放电，aux辅机，use可用，nom铭牌，min/max上下界；仅本式出现者生效，不是相乘字母"}；上标如出现仅表示指数/边界标签；本条无未定义上标；t∈T；T为实际覆盖、时长/时区一致的有限时段集合。y=1..N，N为project.evaluation_years；本式未出现的集合不参与计算。

计算边界：光伏至储能耦合点，同节点电量，额外变换损耗须在节点台账独立列出。
假设：各路径非负，不把网充放电当PV直接自用；检查残差=左−右。
来源：USER-BASELINE相关工程/分类/输出要求与物理代数定义；不是已读标准条款。输出字段：`checks.storage_pv_balance`。
章节：CH08, CH10；阶段：Phase 8；未来测试：`T-STORAGE-PV-BALANCE` PLANNED。
验证方式：独立推导/参考算法、单位及相应边界/能量或成本守恒；不以相同引擎生成expected。

## F-STORAGE-LOAD-BALANCE 光储负荷节点守恒

英文全称：Load node energy balance。

`L_t = E_direct,t + E_bat_load,t + E_grid_load,t`

| 符号 | 定义 | 单位 | 字段 |
|---|---|---|---|
| L_t | 该节点负荷电量 | kWh/时段 | load.interval_kwh |
| E_direct,t | PV直接供负荷电量 | kWh/时段 | storage.pv_direct_load |
| E_bat_load,t | 储能输出端供负荷电量 | kWh/时段 | storage.battery_to_load |
| E_grid_load,t | 电网直接购电供负荷电量 | kWh/时段 | storage.grid_to_load |

下标/上标/范围：{"t": "按同一时区排序且无重漏的时段索引；t+1为相邻时段末/下一时段初", "y": "评价期运营年，从1开始；构建年时间另登记", "标签": "PV光伏，grid电网，self自用，exp外送，curt限发，ch充电，dis放电，aux辅机，use可用，nom铭牌，min/max上下界；仅本式出现者生效，不是相乘字母"}；上标如出现仅表示指数/边界标签；本条无未定义上标；t∈T；T为实际覆盖、时长/时区一致的有限时段集合。y=1..N，N为project.evaluation_years；本式未出现的集合不参与计算。

计算边界：负荷节点单独计量，若系统不可满足负荷需另列未供电项而非强制伪平衡。
假设：检查残差左−右，电网购电有真实成本；直接PV与电池输出不重计自用。
来源：USER-BASELINE相关工程/分类/输出要求与物理代数定义；不是已读标准条款。输出字段：`checks.storage_load_balance`。
章节：CH10；阶段：Phase 8；未来测试：`T-STORAGE-LOAD-BALANCE` PLANNED。
验证方式：独立推导/参考算法、单位及相应边界/能量或成本守恒；不以相同引擎生成expected。

## F-STORAGE-CYCLE-COUNT 等效完整循环计数

英文全称：Equivalent full cycle count。

`n_eq = sum_t(E_dis,internal,t) / C_ref`

| 符号 | 定义 | 单位 | 字段 |
|---|---|---|---|
| n_eq | 本定义的累计等效完整循环数 | 次 | storage.equivalent_cycles |
| E_dis,internal,t | 电池内边界放电消耗能量 | kWh/时段 | storage.internal_discharge_energy |
| C_ref | 设备协议声明的循环参考可用容量 | kWh | storage.cycle_reference_capacity |

下标/上标/范围：{"t": "按同一时区排序且无重漏的时段索引；t+1为相邻时段末/下一时段初", "y": "评价期运营年，从1开始；构建年时间另登记", "标签": "PV光伏，grid电网，self自用，exp外送，curt限发，ch充电，dis放电，aux辅机，use可用，nom铭牌，min/max上下界；仅本式出现者生效，不是相乘字母"}；上标如出现仅表示指数/边界标签；本条无未定义上标；t∈T；T为实际覆盖、时长/时区一致的有限时段集合。y=1..N，N为project.evaluation_years；本式未出现的集合不参与计算。

计算边界：仅当设备循环协议采用累计放电量定义时使用；其他吞吐/雨流计数须另注册，不混成统一事实。
假设：参考容量>0，厂家依据与SOC深度条件明确；退化映射须正式曲线，不给无依据统一年衰减。
来源：USER-BASELINE相关工程/分类/输出要求与物理代数定义；不是已读标准条款。输出字段：`storage.equivalent_cycles`。
章节：CH07, CH15；阶段：Phase 8；未来测试：`T-STORAGE-CYCLE-COUNT` PLANNED。
验证方式：独立推导/参考算法、单位及相应边界/能量或成本守恒；不以相同引擎生成expected。

## F-USABLE-AREA 可利用面积核算

英文全称：Usable area accounting。

`A_use = A_total − sum_i(A_excl,i)`

| 符号 | 定义 | 单位 | 字段 |
|---|---|---|---|
| A_use | 净可利用面积 | m² | site.usable_area |
| A_total | 同一边界总面积 | m² | site.total_area |
| A_excl,i | 互不重叠排除区域面积，i为有效排除区ID | m² | site.exclusion_area |

下标/上标/范围：{"t": "按同一时区排序且无重漏的时段索引；t+1为相邻时段末/下一时段初", "y": "评价期运营年，从1开始；构建年时间另登记", "标签": "PV光伏，grid电网，self自用，exp外送，curt限发，ch充电，dis放电，aux辅机，use可用，nom铭牌，min/max上下界；仅本式出现者生效，不是相乘字母"}；上标如出现仅表示指数/边界标签；本条无未定义上标；t∈T；T为实际覆盖、时长/时区一致的有限时段集合。y=1..N，N为project.evaluation_years；本式未出现的集合不参与计算。

计算边界：边界坐标系/投影与面积同一，排除区先做空间并集去重后计算。
假设：各区非负；排除区重叠不能重复扣；城市/照片不能替代可靠面积证据。
来源：USER-BASELINE相关工程/分类/输出要求与物理代数定义；不是已读标准条款。输出字段：`site.usable_area`。
章节：CH04, CH06；阶段：Phase 3；未来测试：`T-USABLE-AREA` PLANNED。
验证方式：独立推导/参考算法、单位及相应边界/能量或成本守恒；不以相同引擎生成expected。

## F-AVERAGE-ANNUAL-ENERGY 评价期年均电量

英文全称：Average annual energy。

`E_mean = sum_(y=1..N)(E_y) / N`

| 符号 | 定义 | 单位 | 字段 |
|---|---|---|---|
| E_mean | 评价范围同边界年均电量 | kWh/年 | energy.mean_annual_kwh |
| E_y | 第y运营年交流电量 | kWh | energy.annual_kwh |
| N | 明确的完整运营年数量 | 年 | time.operating_year_count |
| y | 从1至N的运营年索引 | 1 | 索引/记号 |

下标/上标/范围：{"t": "按同一时区排序且无重漏的时段索引；t+1为相邻时段末/下一时段初", "y": "评价期运营年，从1开始；构建年时间另登记", "标签": "PV光伏，grid电网，self自用，exp外送，curt限发，ch充电，dis放电，aux辅机，use可用，nom铭牌，min/max上下界；仅本式出现者生效，不是相乘字母"}；上标如出现仅表示指数/边界标签；本条无未定义上标；t∈T；T为实际覆盖、时长/时区一致的有限时段集合。y=1..N，N为project.evaluation_years；本式未出现的集合不参与计算。

计算边界：完整运营年算术均值；含不足年采用时长加权并另注册方法，不以建设年补0混淆。
假设：N>0；年均不得与首年电量混称。
来源：USER-BASELINE相关工程/分类/输出要求与物理代数定义；不是已读标准条款。输出字段：`energy.mean_annual_kwh`。
章节：CH01, CH08；阶段：Phase 3；未来测试：`T-AVERAGE-ANNUAL-ENERGY` PLANNED。
验证方式：独立推导/参考算法、单位及相应边界/能量或成本守恒；不以相同引擎生成expected。

## F-EMISSIONS-AVOIDED 有边界的减排估算

英文全称：Boundary specific avoided emissions。

`M_avoided,y = E_eligible,y × EF_grid,y`

| 符号 | 定义 | 单位 | 字段 |
|---|---|---|---|
| M_avoided,y | 声明反事实边界的避免排放估算 | tCO2e | environment.avoided_emissions |
| E_eligible,y | 该因子适用的电量，不默认全部理论发电量 | kWh | environment.eligible_energy |
| EF_grid,y | 同地区同年份边界电网因子 | tCO2e/kWh | environment.grid_emission_factor |

下标/上标/范围：{"t": "按同一时区排序且无重漏的时段索引；t+1为相邻时段末/下一时段初", "y": "评价期运营年，从1开始；构建年时间另登记", "标签": "PV光伏，grid电网，self自用，exp外送，curt限发，ch充电，dis放电，aux辅机，use可用，nom铭牌，min/max上下界；仅本式出现者生效，不是相乘字母"}；上标如出现仅表示指数/边界标签；本条无未定义上标；t∈T；T为实际覆盖、时长/时区一致的有限时段集合。y=1..N，N为project.evaluation_years；本式未出现的集合不参与计算。

计算边界：仅适用因子匹配时估算，生命周期/运行边际/平均排放因子不可混用；储能网充影响单独。
假设：因子及有效期必须来源；不是碳资产认证，不默认产生碳现金收益。
来源：USER-BASELINE相关工程/分类/输出要求与物理代数定义；不是已读标准条款。输出字段：`environment.avoided_emissions`。
章节：CH12；阶段：Phase 3；未来测试：`T-EMISSIONS-AVOIDED` PLANNED。
验证方式：独立推导/参考算法、单位及相应边界/能量或成本守恒；不以相同引擎生成expected。

## F-TRANSFORMER-ACTIVE-LIMIT 变压器有功容量校核

英文全称：Transformer active power limit。

`P_tr = S_tr × PF`

| 符号 | 定义 | 单位 | 字段 |
|---|---|---|---|
| P_tr | 在声明工况功率因数下的有功容量上限 | kW | grid.transformer_active_limit |
| S_tr | 变压器额定视在容量 | kVA | grid.transformer_capacity |
| PF | 同工况功率因数 | 1 | grid.power_factor |

下标/上标/范围：{"t": "按同一时区排序且无重漏的时段索引；t+1为相邻时段末/下一时段初", "y": "评价期运营年，从1开始；构建年时间另登记", "标签": "PV光伏，grid电网，self自用，exp外送，curt限发，ch充电，dis放电，aux辅机，use可用，nom铭牌，min/max上下界；仅本式出现者生效，不是相乘字母"}；上标如出现仅表示指数/边界标签；本条无未定义上标；t∈T；T为实际覆盖、时长/时区一致的有限时段集合。y=1..N，N为project.evaluation_years；本式未出现的集合不参与计算。

计算边界：只是有功换算；可用接入还需负荷占用/电网限制/无功和温升核查，不能因此认定许可。
假设：0<PF≤1；不能用直流kWp直接与kVA比较。
来源：USER-BASELINE相关工程/分类/输出要求与物理代数定义；不是已读标准条款。输出字段：`grid.transformer_active_limit`。
章节：CH09；阶段：Phase 3；未来测试：`T-TRANSFORMER-ACTIVE-LIMIT` PLANNED。
验证方式：独立推导/参考算法、单位及相应边界/能量或成本守恒；不以相同引擎生成expected。

## F-CAPEX-ITEM-AMOUNT 投资分项金额

英文全称：Capital cost item amount。

`C_i = q_i × u_i`

| 符号 | 定义 | 单位 | 字段 |
|---|---|---|---|
| C_i | 同币种同税边界第i成本项金额 | 元 | capex.items.amount |
| q_i | 第i项工程量/设备数量 | 按quantity_unit | capex.items.quantity |
| u_i | 匹配工程量单位的单价 | 元/quantity_unit | capex.items.unit_price |
| i | 成本明细行ID，非乘法符号 | 1 | 索引/记号 |

下标/上标/范围：{"t": "按同一时区排序且无重漏的时段索引；t+1为相邻时段末/下一时段初", "y": "评价期运营年，从1开始；构建年时间另登记", "标签": "PV光伏，grid电网，self自用，exp外送，curt限发，ch充电，dis放电，aux辅机，use可用，nom铭牌，min/max上下界；仅本式出现者生效，不是相乘字母"}；上标如出现仅表示指数/边界标签；本条无未定义上标；t∈T；T为实际覆盖、时长/时区一致的有限时段集合。y=1..N，N为project.evaluation_years；本式未出现的集合不参与计算。

计算边界：数量、单价、金额税与币种一致再比较；总包固定金额可独立提供而不是伪造工程量。
假设：复核差额并保留约定舍入；无报价不能从预算推为真实分项价。
来源：USER-BASELINE相关工程/分类/输出要求与物理代数定义；不是已读标准条款。输出字段：`capex.items.amount`。
章节：CH14；阶段：Phase 3；未来测试：`T-CAPEX-ITEM-AMOUNT` PLANNED。
验证方式：独立推导/参考算法、单位及相应边界/能量或成本守恒；不以相同引擎生成expected。
