# 光伏预可研18章与13附录稳定内容契约

> 版本 `solar-pv-outline/1.0.0`；范围：Phase 1需求冻结。依据完整提示词第1–8节，而非已核实的规范全文。**报告模板、机器章节检查、计算、渲染、测试及四文件交付均为 `NOT_IMPLEMENTED`。** 本文仅冻结验收设计，不生成报告实例、不伪造页码/公式结果。

## 1. 不可删章与机器检查规则

1. 正文一级ID严格为 `CH01`…`CH18`，顺序固定、每ID出现一次；显示01…18及中文章名。附录严格为 `APP01`…`APP13`，每ID一次。子项用 `CHxx.nn`/`APPxx.nn`，新增只能向末尾追加，废弃保留说明，不可复用或重排既有ID。
2. 每子项必须生成语义内容块：`content_id,chapter_id,pv_type,applicability,content_state,field_instance_ids,source_ids,formula_ids,table_ids,figure_ids,claim_ids,reason,review_state`。`applicability`为APPLICABLE/CONDITIONAL/NOT_APPLICABLE；`content_state`为EVIDENCED/ASSUMPTION/UNKNOWN/PENDING_VERIFICATION/CONFLICT。这不同于实现状态NOT_IMPLEMENTED。
3. 数据不足不删章、不填零，写明缺口及影响；确实不适用需具体原因、类型/触发规则与复核依据。比如无债务只让CH16偿债子项与APP07说明不适用，CH16及APP07仍保留。未实现类型返回NOT_IMPLEMENTED，不得生成冒充合格的四文件。
4. 每个数值/图/表/公式及重要文字结论都要 `claim_id -> field_instance/source -> formula/result -> chapter/item -> file/sheet/cell/paragraph` 路径。报告数值来自canonical result，不在模板或LLM中重算。公式ID与05注册表最终统一，本轮不自创冲突算法编号；正文出现任何公式则必须完整注册并逐符号解释。
5. 每公式下面独立符号表：字符、大小写/希腊字母、下标/上标、集合/求和范围、定义、单位、输入来源、物理边界、假设、来源和验证test_id。英文专业词首次为“中文全称（英文全称，缩写）”，附录全词典；术语/公式校验不能只做标题匹配。
6. DOCX/PDF完整L2/L3必须18章13附录；L1草稿也保留，未知内容写待核实。章节存在检查与语义/数值检查分开；不能空标题或一段万能文字宣称覆盖。未来每个子项独立验收ID，状态均NOT_IMPLEMENTED。

## 2. 逐章、逐子项验收基线

下表field_id定义见03，数组须展开item原子字段。测试ID为设计的未来测试，不代表已存在测试文件或已有运行结果。每章同时应用第3节九分类适用矩阵及07专项边界。

### CH01 执行摘要与初步结论

| 稳定子项ID | 内容 | 最低输入/证据字段 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|---|
| CH01.01 | 项目识别及方案版本 | `project.name`、`project.pv_type`、`site.address` | 项目/位置/类型/方案/评价基准日可定位；与封面版本相同。 | T-OUTLINE-CH01-01 | NOT_IMPLEMENTED |
| CH01.02 | DC/AC及发电指标 | `system.dc_capacity`、`system.ac_capacity`、`project.evaluation_years` | 列DC、AC、容配比、首年及评价期年均电量，注明能量边界；未知不填0。 | T-OUTLINE-CH01-02 | NOT_IMPLEMENTED |
| CH01.03 | 投资及财务指标 | `capex.items`、`finance.project_discount_rate`、`finance.equity_discount_rate` | 列总投资、单位投资、项目IRR、资本金IRR、NPV、静动态回收期、LCOE；每指标同边界来源可追溯。 | T-OUTLINE-CH01-03 | NOT_IMPLEMENTED |
| CH01.04 | 消纳售电与资料成熟度 | `project.sales_mode`、`load.series`、`tariff.periods` | 列自用/售电/限发比例及L1/L2/L3与各证据轴；无负荷真实自用率UNKNOWN。 | T-OUTLINE-CH01-04 | NOT_IMPLEMENTED |
| CH01.05 | 阻断风险和四态建议 | `risk.items`、`targets.project_irr`、`targets.payback_years` | 先否决/严重未决，再技术商业财务及成熟度；四态唯一且与CH18一致，不以高IRR覆盖红线。 | T-OUTLINE-CH01-05 | NOT_IMPLEMENTED |

### CH02 总论与编制依据

| 稳定子项ID | 内容 | 最低输入/证据字段 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|---|
| CH02.01 | 项目背景与目的 | `project.owner`、`project.developer` | 说明发起背景、预可研目标、正式可研前边界，不冒充工程资质意见。 | T-OUTLINE-CH02-01 | NOT_IMPLEMENTED |
| CH02.02 | 评价范围与价格现金流口径 | `project.evaluation_date`、`project.evaluation_years`、`project.currency`、`project.price_basis`、`project.cashflow_tax_basis` | 明确基期、评价期、币种、名义/实际、税前/税后、投资/资本金和建设期。 | T-OUTLINE-CH02-02 | NOT_IMPLEMENTED |
| CH02.03 | 标准与政策适用 | `policy.applicability` | 标准/政策逐份核验地区、类型、生效日、版本和原文位置；未核实不称现行。 | T-OUTLINE-CH02-03 | NOT_IMPLEMENTED |
| CH02.04 | 资料目录与数据年份 | `attachments.register`、`resource.period_start`、`resource.period_end` | 区分真实项目全文、摘要、示例、标准、技术手册、统计成本，不混称真实工程案例。 | T-OUTLINE-CH02-04 | NOT_IMPLEMENTED |
| CH02.05 | 假设、版本及免责 | `scenarios.options`、`risk.items` | 列示假设/UNKNOWN/CONFLICT、适用限制、审核状态及model/run/input/source/result五标识。 | T-OUTLINE-CH02-05 | NOT_IMPLEMENTED |

### CH03 工程概况及建设必要性

| 稳定子项ID | 内容 | 最低输入/证据字段 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|---|
| CH03.01 | 业主与投资运营主体 | `project.owner`、`project.investor`、`project.operator` | 主体和投资/建设/运营角色明确，未核实信息不虚构。 | T-OUTLINE-CH03-01 | NOT_IMPLEMENTED |
| CH03.02 | 站址及工程分类 | `project.pv_type`、`site.address`、`site.latitude`、`site.longitude` | 定位到具体屋顶/地块；九类名称不可仅改标题而共用不适用模型。 | T-OUTLINE-CH03-02 | NOT_IMPLEMENTED |
| CH03.03 | 建设及权属模式 | `project.ownership_mode`、`site.rights_holder`、`site.rights_document_id` | 自投/租赁/PPA/收益分成与权属期限对齐，不把用户陈述等同权利确认。 | T-OUTLINE-CH03-03 | NOT_IMPLEMENTED |
| CH03.04 | 用能及售电模式 | `project.sales_mode`、`load.monthly_bills`、`tariff.contract_id` | 需求/计量边界/全额或余电/PPA描述与CH10计算一致。 | T-OUTLINE-CH03-04 | NOT_IMPLEMENTED |
| CH03.05 | 规模目标与建设必要性 | `system.dc_capacity`、`targets.budget_ceiling`、`targets.project_irr` | 解释目标、必要性及可核实依据；用户目标不是实际收益保证。 | T-OUTLINE-CH03-05 | NOT_IMPLEMENTED |

### CH04 选址及建设条件

| 稳定子项ID | 内容 | 最低输入/证据字段 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|---|
| CH04.01 | 位置坐标与边界 | `site.address`、`site.latitude`、`site.longitude`、`site.crs`、`site.boundary_vertices` | 地址、坐标系、边界闭合/面积可核查；城市级信息只能写站址待定。 | T-OUTLINE-CH04-01 | NOT_IMPLEMENTED |
| CH04.02 | 地形海拔与面积核算 | `site.elevation`、`site.terrain_slope`、`site.total_area`、`site.usable_area`、`site.exclusion_area` | 总/可用/排除面积闭合，退界与消防通道等扣减有依据。 | T-OUTLINE-CH04-02 | NOT_IMPLEMENTED |
| CH04.03 | 土地屋顶权属与期限 | `site.rights_holder`、`site.land_classification`、`site.rights_status`、`site.rights_expiry` | 按分类核验土地/屋顶/水域/公共资产；争议/禁止/未核实分别列。 | T-OUTLINE-CH04-03 | NOT_IMPLEMENTED |
| CH04.04 | 遮挡与结构安全 | `site.shading_fraction`、`roof.allowable_additional_load`、`roof.design_added_load`、`roof.remaining_life` | 遮挡、荷载、屋面寿命按适用类别核查；无鉴定不写安全合格。 | T-OUTLINE-CH04-04 | NOT_IMPLEMENTED |
| CH04.05 | 交通生态灾害限制 | `site.transport_access`、`site.ecology_reference`、`site.disaster_reference`、`site.local_restrictions` | 列物流、生态/灾害/限建和专项核查；未知与不适用有独立理由。 | T-OUTLINE-CH04-05 | NOT_IMPLEMENTED |
| CH04.06 | 专项建设条件与缺口 | `site.geotechnical_reference`、`site.flood_reference`、`risk.items` | 地勘、防洪、屋顶防水等按类别展开；限制与CH06/11方案相互引用。 | T-OUTLINE-CH04-06 | NOT_IMPLEMENTED |

### CH05 太阳能资源与气象

| 稳定子项ID | 内容 | 最低输入/证据字段 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|---|
| CH05.01 | 数据集元信息与授权 | `resource.dataset_id`、`resource.version`、`resource.provider`、`resource.license_id` | 保存实际获取状态、版本、许可、地区、时段、分辨率和来源ID，不以链接代全文。 | T-OUTLINE-CH05-01 | NOT_IMPLEMENTED |
| CH05.02 | 辐照分量与单位 | `resource.monthly.ghi`、`resource.monthly.dni`、`resource.monthly.dhi`、`resource.monthly.poa` | GHI/DNI/DHI/GTI或POA逐项定义，辐照度/量分开；不将PVOUT当实测项目发电。 | T-OUTLINE-CH05-02 | NOT_IMPLEMENTED |
| CH05.03 | 温度风速与12个月 | `resource.monthly.ambient_temperature`、`resource.monthly.wind_speed`、`resource.monthly.month` | 12个月连续不重漏，温度/风单位、年合计/平均加权口径清楚。 | T-OUTLINE-CH05-03 | NOT_IMPLEMENTED |
| CH05.04 | 逐年差异与典型气象年 | `resource.annual_comparison`、`resource.is_tmy`、`resource.tmy_method` | 说明年份跨度、TMY构造及年度差异，闰年/DST处理可追溯。 | T-OUTLINE-CH05-04 | NOT_IMPLEMENTED |
| CH05.05 | 平面转置与气象适配 | `resource.model_method`、`resource.poa_boundary`、`layout.tilt`、`layout.azimuth` | 平面方向、模型假设、数据质量适配，禁止未经支持的直接转换。 | T-OUTLINE-CH05-05 | NOT_IMPLEMENTED |
| CH05.06 | 误差与交叉验证降级 | `resource.uncertainty_fraction`、`resource.uncertainty_basis`、`resource.timeseries` | 交叉验证用同边界可比数据；接口失败/覆盖不足/许可缺失明确降级，不造真实数据。 | T-OUTLINE-CH05-06 | NOT_IMPLEMENTED |

### CH06 工程任务、规模与方案比选

| 稳定子项ID | 内容 | 最低输入/证据字段 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|---|
| CH06.01 | 任务与可利用面积 | `site.usable_area`、`layout.fire_setback`、`layout.ground_coverage_ratio` | 容量受有效面积、退界、通道及生产/建筑约束，不只理论铺满。 | T-OUTLINE-CH06-01 | NOT_IMPLEMENTED |
| CH06.02 | 组件排列与数量 | `system.module_count`、`system.module_length`、`system.module_width`、`layout.row_pitch` | 块数与布局可行性对应，子型差异/无法确定时说明。 | T-OUTLINE-CH06-02 | NOT_IMPLEMENTED |
| CH06.03 | DC/AC规模与比例 | `system.dc_capacity`、`system.ac_capacity`、`system.dc_ac_ratio` | DC=块数×组件功率，AC=台数×额定输出；比例及接入约束核对。 | T-OUTLINE-CH06-03 | NOT_IMPLEMENTED |
| CH06.04 | 基准与可行替代方案 | `scenarios.options` | 至少一基准一有约束依据的可行替代；不可只换标题或比较不可建方案。 | T-OUTLINE-CH06-04 | NOT_IMPLEMENTED |
| CH06.05 | 比选口径与选择理由 | `targets.budget_ceiling`、`grid.available_capacity`、`risk.items` | 相同边界比较技术/投资/收益/风险；门槛缺失不宣称最优。 | T-OUTLINE-CH06-05 | NOT_IMPLEMENTED |
| CH06.06 | 分类专项方案 | `storage.base_pv_type`、`storage.energy_capacity`、`agri.minimum_light_transmission` | 储能容量/耦合/时序或农渔/建筑等按实际类型展开；未实现分类NOT_IMPLEMENTED，不套P0。 | T-OUTLINE-CH06-06 | NOT_IMPLEMENTED |

### CH07 光伏系统初步设计

| 稳定子项ID | 内容 | 最低输入/证据字段 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|---|
| CH07.01 | 组件与逆变器选择 | `system.module_model`、`system.module_power`、`system.module_efficiency`、`system.inverter_model`、`system.inverter_unit_ac` | 设备规格、版本、来源和适用理由；无实价/认证证据不得声称已核实。 | T-OUTLINE-CH07-01 | NOT_IMPLEMENTED |
| CH07.02 | 支架及几何参数 | `system.mounting_type`、`layout.azimuth`、`layout.tilt`、`layout.row_pitch` | 角度基准、间距、支架和土建条件相容，含农机/水域/建筑子型差异。 | T-OUTLINE-CH07-02 | NOT_IMPLEMENTED |
| CH07.03 | 串并联与电压电流校核 | `system.modules_per_string`、`system.parallel_strings`、`system.module_voc`、`system.inverter_max_dc_voltage`、`system.inverter_max_input_current` | 数量、温度极值、MPPT及输入电流边界明确；不能以简图代校核。 | T-OUTLINE-CH07-03 | NOT_IMPLEMENTED |
| CH07.04 | 损失分项与物理顺序 | `system.losses` | 每损失有数值/模型、单位、顺序、已含标志；PR与模拟输出不重复扣损。 | T-OUTLINE-CH07-04 | NOT_IMPLEMENTED |
| CH07.05 | 系统结构及接口 | `system.topology`、`system.capacity_boundary`、`grid.connection_point` | DC/AC/变压器/计量/送出边界图和适用理由，不伪造设计批准。 | T-OUTLINE-CH07-05 | NOT_IMPLEMENTED |
| CH07.06 | 储能或分类专项设计 | `storage.coupling`、`storage.soc_min`、`storage.soc_max`、`storage.fire_safety_reference` | 配储独立SOC/效率/安全；非储能保留本项并说明不适用及依据。 | T-OUTLINE-CH07-06 | NOT_IMPLEMENTED |

### CH08 发电量预测与效率评价

| 稳定子项ID | 内容 | 最低输入/证据字段 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|---|
| CH08.01 | 预测方法及能量边界 | `resource.model_method`、`resource.poa_boundary`、`system.capacity_boundary` | 优先可靠逐时模型；简化POA×DC×PR需说明适用边界和损失。 | T-OUTLINE-CH08-01 | NOT_IMPLEMENTED |
| CH08.02 | 月度与首年电量 | `resource.monthly`、`system.losses`、`system.first_year_degradation` | 12月汇总等于首年同边界电量；月年、图表、Excel全数值一致。 | T-OUTLINE-CH08-02 | NOT_IMPLEMENTED |
| CH08.03 | 逐年衰减和更换 | `system.degradation_segments`、`system.annual_degradation`、`assets.replacements` | 用户评价期全周期逐年列，首年与后续衰减/更换停机不重复。 | T-OUTLINE-CH08-03 | NOT_IMPLEMENTED |
| CH08.04 | PR、等效小时和容量因子 | `system.dc_capacity`、`system.ac_capacity`、`system.losses` | 容量参考DC或AC明确；容量因子年时数按实际闰年/年度定义。 | T-OUTLINE-CH08-04 | NOT_IMPLEMENTED |
| CH08.05 | 不可利用与限发校核 | `system.unavailability`、`grid.curtailment_assumption` | 送出/可利用/限发边界独立，避免损失重复，非负能量平衡。 | T-OUTLINE-CH08-05 | NOT_IMPLEMENTED |
| CH08.06 | 不确定性与结果限制 | `resource.uncertainty_basis`、`risk.items` | 不得将示例模拟冒充真实发电；跨项目实绩只作有来源同口径交叉核验。 | T-OUTLINE-CH08-06 | NOT_IMPLEMENTED |

### CH09 电气系统与电网接入

| 稳定子项ID | 内容 | 最低输入/证据字段 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|---|
| CH09.01 | 接入点与电压 | `grid.connection_point`、`grid.connection_voltage`、`grid.metering_boundary` | 接入方案及计量位置可定位，未得正式意见标条件。 | T-OUTLINE-CH09-01 | NOT_IMPLEMENTED |
| CH09.02 | 变压器线路与容量约束 | `grid.transformer_capacity`、`grid.power_factor`、`grid.available_capacity`、`grid.line_length` | kVA/kW换算有功率因数；线路/容量与AC规模相容。 | T-OUTLINE-CH09-02 | NOT_IMPLEMENTED |
| CH09.03 | 升压保护及送出工程 | `grid.upgrade_plan`、`grid.protection_plan`、`capex.items` | 集中式集电/升压/送出与屋顶分布式差异真实展开，造价边界不漏计。 | T-OUTLINE-CH09-03 | NOT_IMPLEMENTED |
| CH09.04 | 并网与交易核验 | `grid.opinion_status`、`grid.opinion_attachment_id`、`grid.opinion_valid_until`、`grid.transaction_opinion` | 未得/过期/拒绝与有效意见区分；不得写具备并网资格。 | T-OUTLINE-CH09-04 | NOT_IMPLEMENTED |
| CH09.05 | 限发与尚待电网确认 | `grid.export_power_limit`、`grid.curtailment_basis`、`risk.items` | 限制按时段功率/电量换算；列需电网确认的容量、接入和限制事项。 | T-OUTLINE-CH09-05 | NOT_IMPLEMENTED |

### CH10 电力消纳与电价售电方案

| 稳定子项ID | 内容 | 最低输入/证据字段 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|---|
| CH10.01 | 负荷资料与同粒度匹配 | `load.monthly_bills`、`load.series`、`load.timezone` | 负荷/发电/价格同时间粒度、时区和边界；账单和覆盖率校验；无曲线不得真实自用率。 | T-OUTLINE-CH10-01 | NOT_IMPLEMENTED |
| CH10.02 | 自用、上网与限发平衡 | `project.sales_mode`、`grid.export_power_limit`、`load.series` | 无储能时逐时自用+上网+限发=可用电；非负且全年同界加总。 | T-OUTLINE-CH10-02 | NOT_IMPLEMENTED |
| CH10.03 | 分时电价与可避免费用 | `tariff.periods`、`tariff.non_avoidable_charges` | 峰平谷、实际可避免费/不可抵减固定费、含税和适用期明确；不能以总账单均价替代。 | T-OUTLINE-CH10-03 | NOT_IMPLEMENTED |
| CH10.04 | 合同与交易结算模式 | `tariff.contract_id`、`tariff.ppa_price`、`tariff.revenue_share`、`tariff.transaction_fee` | 全额/余电、PPA、租赁、分成、交易费和限制条款逐项，不重复收益。 | T-OUTLINE-CH10-04 | NOT_IMPLEMENTED |
| CH10.05 | 逐时市场价与其他收益 | `tariff.market_series`、`revenue.other_items` | 负电价按有依据条款；其他收入须合同与排他边界，不造补贴。 | T-OUTLINE-CH10-05 | NOT_IMPLEMENTED |
| CH10.06 | 储能调度独立边界 | `storage.dispatch`、`storage.charge_efficiency`、`storage.discharge_efficiency`、`storage.grid_charging` | 光伏/网充/负荷/上网/电池分账、SOC功率终端约束、双向损耗和收益不重复。 | T-OUTLINE-CH10-06 | NOT_IMPLEMENTED |

### CH11 总平面与土建施工条件

| 稳定子项ID | 内容 | 最低输入/证据字段 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|---|
| CH11.01 | 总平面与功能分区 | `site.boundary_vertices`、`layout.row_pitch`、`layout.fire_setback` | 布局有图题/边界、通道与检修区域，不将概念草图称施工图。 | T-OUTLINE-CH11-01 | NOT_IMPLEMENTED |
| CH11.02 | 地基与支架基础 | `site.geotechnical_reference`、`system.mounting_type`、`fishery.foundation_method` | 按屋顶/土地/水域/矿区展开专项；无地勘不可证实承载。 | T-OUTLINE-CH11-02 | NOT_IMPLEMENTED |
| CH11.03 | 结构承载与安全疏散 | `roof.structure_report_id`、`roof.design_added_load`、`roof.fire_access_reference` | 结构/荷载/消防路径核验，未知明确待检，不删章。 | T-OUTLINE-CH11-03 | NOT_IMPLEMENTED |
| CH11.04 | 施工物流道路与排水 | `site.transport_access`、`site.flood_reference`、`roof.waterproof_plan` | 施工/运输/道路/防洪排水/防水及生产干扰成本边界。 | T-OUTLINE-CH11-04 | NOT_IMPLEMENTED |
| CH11.05 | 专项勘察及工程量缺口 | `risk.items`、`capex.items` | 列测绘、地勘、结构鉴定等需求与估算影响、责任方及后续设计依赖。 | T-OUTLINE-CH11-05 | NOT_IMPLEMENTED |

### CH12 环境、生态、安全及社会影响

| 稳定子项ID | 内容 | 最低输入/证据字段 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|---|
| CH12.01 | 节能减排与因子 | `environment.grid_emission_factor`、`environment.factor_period` | 排放因子来源、年度、区域、边界和单位齐全，不杜撰碳收益。 | T-OUTLINE-CH12-01 | NOT_IMPLEMENTED |
| CH12.02 | 环境生态与水土保持 | `site.ecology_reference`、`environment.approval_reference` | 按类型核查生态/水域/农作/复垦/水保适用性；不冒充审批通过。 | T-OUTLINE-CH12-02 | NOT_IMPLEMENTED |
| CH12.03 | 消防与施工运行安全 | `environment.fire_reference`、`roof.fire_access_reference`、`storage.fire_safety_reference` | 屋顶高处、电气、公共人员、储能消防等按类型独立，不以通用文字盖过风险。 | T-OUTLINE-CH12-03 | NOT_IMPLEMENTED |
| CH12.04 | 社会影响与利益主体 | `site.rights_holder`、`public.asset_authorization`、`residential.property_consent` | 涉及公众、农业、养殖、住户及公共资产影响，必要同意/权利待核。 | T-OUTLINE-CH12-04 | NOT_IMPLEMENTED |
| CH12.05 | 专项评估与合规阻断 | `policy.applicability`、`risk.items` | 必须依法核验的审批/专项清单及证据状态；红线独立约束结论。 | T-OUTLINE-CH12-05 | NOT_IMPLEMENTED |

### CH13 实施组织与建设计划

| 稳定子项ID | 内容 | 最低输入/证据字段 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|---|
| CH13.01 | 开发前提与组织分工 | `project.developer`、`project.operator`、`schedule.tasks` | 产权/土地/接入咨询前提和责任方明确，计划不是实际批准。 | T-OUTLINE-CH13-01 | NOT_IMPLEMENTED |
| CH13.02 | 初设采购施工调试验收 | `schedule.tasks`、`schedule.construction_start`、`schedule.commissioning_date` | 阶段任务、起止时间、招采和验收接口完整。 | T-OUTLINE-CH13-02 | NOT_IMPLEMENTED |
| CH13.03 | 依赖关系与关键路径 | `schedule.tasks.predecessor_ids`、`schedule.tasks.critical_path` | 任务依赖无循环，关键路径与建设期支出/投运现金流相容。 | T-OUTLINE-CH13-03 | NOT_IMPLEMENTED |
| CH13.04 | 建设风险与缓释 | `risk.items`、`site.transport_access` | 季节/供货/生产协调/送出延期等按类型，进度情景不承诺成功概率。 | T-OUTLINE-CH13-04 | NOT_IMPLEMENTED |
| CH13.05 | 里程碑与进入下一阶段条件 | `targets.risk_preference`、`risk.items` | 每里程碑证据、责任方和停止条件，与CH18后续工作一致。 | T-OUTLINE-CH13-05 | NOT_IMPLEMENTED |

### CH14 工程投资估算 CAPEX

| 稳定子项ID | 内容 | 最低输入/证据字段 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|---|
| CH14.01 | 估算依据与边界 | `capex.estimate_basis`、`capex.user_budget`、`project.currency` | 价格年份、地区、汇率、有效报价/预算/估算状态分开，用户预算不是真实成本。 | T-OUTLINE-CH14-01 | NOT_IMPLEMENTED |
| CH14.02 | 设备材料投资 | `capex.items` | 组件、逆变、支架、电缆、变配电与储能单列；数量×价及汇总可复核。 | T-OUTLINE-CH14-02 | NOT_IMPLEMENTED |
| CH14.03 | 工程建设与场址专项 | `capex.items.category`、`site.geotechnical_reference` | 并网送出、土建、屋顶加固、施工、运输、土地/屋顶费用不漏不重。 | T-OUTLINE-CH14-03 | NOT_IMPLEMENTED |
| CH14.04 | 前期与管理及预备费 | `capex.items.category`、`capex.contingency_rate` | 设计、开发、管理、预备费及适用基数明确；报价日期/许可可追溯。 | T-OUTLINE-CH14-04 | NOT_IMPLEMENTED |
| CH14.05 | 建设期利息与资金进度 | `capex.includes_construction_interest`、`finance.debt_schedule`、`schedule.tasks` | 建期利息与融资支出一致，项目与股东口径不重复融资。 | T-OUTLINE-CH14-05 | NOT_IMPLEMENTED |
| CH14.06 | 税口径与单位投资校核 | `capex.items.tax_included`、`capex.items.vat_rate`、`capex.includes_storage`、`capex.includes_land` | 含税/不含税/可抵扣税独立，是否含储能/租地明示；总额和元/Wp/元/kWp换算。 | T-OUTLINE-CH14-06 | NOT_IMPLEMENTED |

### CH15 运营费用 OPEX 与折旧税费

| 稳定子项ID | 内容 | 最低输入/证据字段 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|---|
| CH15.01 | 年度运营费 | `opex.items` | 维修、清洗、保险、运维、地租/屋顶租金按合同基年及通胀列年度计划。 | T-OUTLINE-CH15-01 | NOT_IMPLEMENTED |
| CH15.02 | 资产分类折旧与残值 | `assets.depreciation` | 分类原值、残值、年限、方法和税法依据，累计折旧不超可折旧额。 | T-OUTLINE-CH15-02 | NOT_IMPLEMENTED |
| CH15.03 | 更换与寿命计划 | `assets.replacements`、`storage.replacement_rule` | 组件/逆变/电池更换与停机/性能恢复有独立年计划，资本开支不重复OPEX。 | T-OUTLINE-CH15-03 | NOT_IMPLEMENTED |
| CH15.04 | 税制与实际现金税金 | `tax.regime_reference`、`tax.corporate_income_rate`、`tax.vat_recovery_timing`、`tax.surcharge_basis` | 法定适用税率/优惠/期限/抵扣/结转有证据；不杜撰统一税制。 | T-OUTLINE-CH15-04 | NOT_IMPLEMENTED |
| CH15.05 | 非现金与年度汇总校核 | `opex.items`、`assets.depreciation`、`assets.replacements` | 折旧影响应税所得但不再作为经营现金支出；税表与项目股东现金流勾稽。 | T-OUTLINE-CH15-05 | NOT_IMPLEMENTED |

### CH16 财务效益与投资回报

| 稳定子项ID | 内容 | 最低输入/证据字段 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|---|
| CH16.01 | 收入与残值 | `tariff.periods`、`tariff.market_series`、`revenue.other_items`、`assets.depreciation.residual_value` | 发电自用/市场售电/其他合同收益及残值边界相同，租金/PPA/分成不重复。 | T-OUTLINE-CH16-01 | NOT_IMPLEMENTED |
| CH16.02 | 项目投资现金流 | `capex.items`、`opex.items`、`tax.regime_reference`、`finance.working_capital` | 建设/运营全期收入、现金费、税、CAPEX、营运变化、残值；不混债务资金流。 | T-OUTLINE-CH16-02 | NOT_IMPLEMENTED |
| CH16.03 | 股东现金流与融资偿债 | `finance.debt_schedule`、`finance.debt_ratio`、`finance.loan_rate` | 包含借入/还本/付息/债务费及股东投入，余额与本金/利息核对。 | T-OUTLINE-CH16-03 | NOT_IMPLEMENTED |
| CH16.04 | NPV与IRR | `finance.project_discount_rate`、`finance.equity_discount_rate`、`project.price_basis` | 项目/资本金独立且折现边界匹配；IRR无根/多根/无符号变化输出不可计算原因。 | T-OUTLINE-CH16-04 | NOT_IMPLEMENTED |
| CH16.05 | 静态动态回收期 | `targets.payback_years`、`targets.payback_basis` | 首次累计转正、相邻年插值及起点定义；期内未回收不强给年份。 | T-OUTLINE-CH16-05 | NOT_IMPLEMENTED |
| CH16.06 | LCOE与可交付电量 | `system.capacity_boundary`、`grid.export_power_limit`、`project.cashflow_tax_basis` | 同边界生命周期成本/折现送出电量；不以理论发电分母替代实际交付。 | T-OUTLINE-CH16-06 | NOT_IMPLEMENTED |
| CH16.07 | DSCR与债务条件 | `finance.cfads_definition`、`finance.debt_schedule.dscr_covenant` | CFADS和偿债本息费按协议；无债务不适用；零分母不可计算并说明。 | T-OUTLINE-CH16-07 | NOT_IMPLEMENTED |
| CH16.08 | 盈亏平衡与目标差距 | `targets.project_irr`、`targets.equity_irr`、`targets.budget_ceiling` | 盈亏平衡价/现金流最差年/投资与债务校验；目标为约束，不能调数据迎合。 | T-OUTLINE-CH16-08 | NOT_IMPLEMENTED |

### CH17 敏感性、情景与风险

| 稳定子项ID | 内容 | 最低输入/证据字段 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|---|
| CH17.01 | 单因素敏感性 | `scenarios.options`、`capex.items`、`tariff.periods`、`resource.uncertainty_fraction` | 投资、电价、发电、利用率/自用率、限发、运维、利率逐项独立；其他保持不变。 | T-OUTLINE-CH17-01 | NOT_IMPLEMENTED |
| CH17.02 | 悲观基准乐观组合 | `scenarios.options` | 组合假设有来源和相关性说明；不是自造发生概率。 | T-OUTLINE-CH17-02 | NOT_IMPLEMENTED |
| CH17.03 | 阈值与稳健性 | `targets.project_irr`、`targets.equity_irr`、`targets.payback_years` | 门槛临界值/失效边界/无法求解原因，保守条件和备选方案相容。 | T-OUTLINE-CH17-03 | NOT_IMPLEMENTED |
| CH17.04 | 风险清单与证据状态 | `risk.items`、`policy.applicability` | 法律、技术、接入、资源、商业、税/融资及类型专项，已证实与待核实分离。 | T-OUTLINE-CH17-04 | NOT_IMPLEMENTED |
| CH17.05 | 属性及反向约束校核 | `scenarios.options` | 其他不变投资升高不得使项目NPV升高；同价电量下降不得增收入；实际数值校验而非只对字符串。 | T-OUTLINE-CH17-05 | NOT_IMPLEMENTED |

### CH18 综合结论及后续工作

| 稳定子项ID | 内容 | 最低输入/证据字段 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|---|
| CH18.01 | 四态唯一建议 | `risk.items`、`targets.project_irr`、`targets.payback_years` | 仅建议进入下一阶段/有条件推进/暂缓决策/不建议按当前方案推进，CH01一致。 | T-OUTLINE-CH18-01 | NOT_IMPLEMENTED |
| CH18.02 | 结论证据及独立否决 | `site.rights_status`、`grid.opinion_status`、`risk.items` | 先法律/产权/结构消防/关键接入；重大未决暂缓，已证实红线不被高IRR抵消。 | T-OUTLINE-CH18-02 | NOT_IMPLEMENTED |
| CH18.03 | 推进条件与触发阈值 | `targets.risk_preference`、`scenarios.options` | 条件可核验、责任人/期限明确；条件不成即退回暂缓或不建议。 | T-OUTLINE-CH18-03 | NOT_IMPLEMENTED |
| CH18.04 | 资料缺口与专项核查 | `risk.items`、`attachments.register` | 缺口逐项ID、影响、责任方、核查方式及关闭证据，禁止只写泛化建议。 | T-OUTLINE-CH18-04 | NOT_IMPLEMENTED |
| CH18.05 | 决策里程碑及免责 | `schedule.tasks`、`project.evaluation_date` | 下一阶段/有效期/需资质机构的事项明确；预可研不替代正式审批、设计或鉴定。 | T-OUTLINE-CH18-05 | NOT_IMPLEMENTED |

## 3. 九分类逐章适用矩阵（18×9，不可删章）

每单元均为**保留本章并按该指令展开**，不存在省略整个章节的N/A。适用细项可按证据写不适用/待核实；PV储能同时采用基础工程类型的场址条件，但能量/SOC/现金流模块独立。P0/P1/P2不是实现进度；当前九类均NOT_IMPLEMENTED。

| 章节 | I 工商业屋顶 | G 集中式地面 | A 农光 | F 渔光 | S 光储 | P 公共建筑 | R 户用 | B 车棚/BIPV | D 荒漠/矿区 |
|---|---|---|---|---|---|---|---|---|---|
| CH01 | 分布式收益摘要 | 全额售电摘要 | 农业光伏双约束 | 渔业光伏双约束 | 光伏储能分账摘要 | 公共资产收益摘要 | 户用权益摘要 | 车棚/建筑功能摘要 | 土地复垦与送出摘要 |
| CH02 | 分布式及合同依据 | 用地/市场交易依据 | 农业合规依据 | 水域渔业依据 | 充放电及收益依据 | 公共资产采购依据 | 住户产权低压依据 | 建筑/认证专项依据 | 矿区/生态修复依据 |
| CH03 | 企业用能必要性 | 电源/市场必要性 | 保农业生产必要性 | 保渔业生产必要性 | 独立配储必要性 | 公共建筑使用目的 | 家庭用电与投资 | 建筑替代/停车目的 | 基地开发修复目的 |
| CH04 | 产权荷载遮挡 | 土地边界地勘坡度 | 农地与耕作约束 | 水权水位腐蚀 | 基座加储能安全选址 | 公共权属人员安全 | 产权共有人荷载 | 净空围护结构 | 采空沉降风沙 |
| CH05 | 屋顶资源遮挡 | 地面多年资源 | 透光与行距影响 | 水面环境资源 | PV资源与调度时序 | 公共屋面资源 | 户用遮挡资源 | 立面/车棚平面资源 | 沙尘风与资源 |
| CH06 | 屋顶布局自用比选 | 用地/送出规模比选 | 行距透光农机比选 | 水域基础养殖比选 | 功率/能量/调度比选 | 公共空间布局比选 | 小容量与低压比选 | 车棚/BIPV分子型比选 | 场地/修复/送出比选 |
| CH07 | 屋顶串并支架 | 地面支架集电 | 净高/透光支架 | 防腐水域支架 | 独立电池耦合SOC | 消防检修支架 | 低压保护屋顶 | 围护防水认证 | 抗风沙沉降设计 |
| CH08 | 屋顶损失月年电量 | 地面损失送出电量 | 遮挡/生产限制电量 | 水域损失可用电量 | PV输出与电池损耗分开 | 公共屋面月年电量 | 户用月年电量 | 平面/立面损失电量 | 积尘送出损失电量 |
| CH09 | 分布式接入限制 | 集电升压送出限制 | 农业站接入核查 | 水域站接入核查 | 双向接入与网充许可 | 公共建筑接入 | 低压接入保护 | 建筑负荷/充电接入 | 远距离送出接入 |
| CH10 | 企业同粒度真实负荷 | 市场全额售电/限发 | 农业负荷/售电分界 | 渔业负荷/售电分界 | 逐时SOC能量与收益独立 | 公共使用时段负荷 | 家庭真实时段负荷 | 充电/建筑用电分界 | 市场售电与限发 |
| CH11 | 荷载消防防水 | 道路排水基础施工 | 耕作通道灌溉 | 水上施工检修 | 基座加电池消防布置 | 公共人员疏散 | 住户屋面安全 | 净空防水围护 | 地勘沉降/修复通道 |
| CH12 | 高处作业消防 | 生态水保土地影响 | 农业生产生态 | 水质养殖生态 | 电池消防回收 | 公共人员社会影响 | 消费者与共同产权 | 建筑防火/停车安全 | 荒漠生态矿区安全 |
| CH13 | 屋顶生产协同计划 | 土地送出施工计划 | 农时协同施工 | 养殖期水上施工 | 电池采购联调验收 | 公共采购使用协调 | 住户施工接入计划 | 建筑工程联合验收 | 修复/送出协同计划 |
| CH14 | 屋顶加固租赁专项 | 土地道路升压送出 | 高支架基础农业保护 | 水域基础防腐施工 | 电池PCS消防增量 | 公共资产合规采购 | 户用施工低压投资 | 建材替代增量边界 | 修复道路长线送出 |
| CH15 | 租金清洗运维税 | 地租道路运维税 | 农业保护额外费用 | 水域防腐养殖协调 | 电池衰减更换回收 | 公共维护预算税 | 户用合同税务边界 | 建筑围护维护替换 | 积尘清洗复垦费用 |
| CH16 | 自用/PPA及项目股权 | 市场价及项目股权 | 农业与售电收益隔离 | 养殖与售电收益隔离 | 套利/节省/合同不重计 | 公共主体税融资边界 | 家庭主体税合同边界 | 替代成本与售电不重计 | 修复责任与售电现金流 |
| CH17 | 自用率合同负荷风险 | 市场价限发送出风险 | 透光生产合规风险 | 腐蚀水质权属风险 | SOC效率退化价差风险 | 采购/公共安全风险 | 合同/低压产权风险 | 建筑认证/增量成本风险 | 风沙沉降复垦风险 |
| CH18 | 权属结构并网先决 | 用地送出先决 | 农业合规先决 | 水域渔业合规先决 | 基座及电池安全先决 | 公共授权消防先决 | 产权同意低压先决 | 建筑功能认证先决 | 用地矿安生态先决 |

## 4. 十三项强制附录及稳定子项

### APP01 项目资料索引

| 稳定子项ID | 内容 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|
| APP01.01 | 来源与附件索引 | 每份资料ID、实际可读范围、页/节/单元格、敏感级、授权状态；不输出机密全文。 | T-OUTLINE-APP01-01 | NOT_IMPLEMENTED |
| APP01.02 | 输入血缘索引 | 每个重要输入和claim到字段实例/来源/处理规则，缺失与冲突完整可查。 | T-OUTLINE-APP01-02 | NOT_IMPLEMENTED |

### APP02 12个月气象与发电量

| 稳定子项ID | 内容 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|
| APP02.01 | 月度气象与资源 | 1..12月GHI/DNI/DHI/POA、温度风、数据期与覆盖率，未知保留。 | T-OUTLINE-APP02-01 | NOT_IMPLEMENTED |
| APP02.02 | 月度能量平衡 | 月发电/自用/上网/限发及年汇总、单位、边界和图表勾稽。 | T-OUTLINE-APP02-02 | NOT_IMPLEMENTED |

### APP03 设备及损失参数

| 稳定子项ID | 内容 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|
| APP03.01 | 设备与布局原子参数 | 组件/逆变/支架/几何/串并联及来源版本。 | T-OUTLINE-APP03-01 | NOT_IMPLEMENTED |
| APP03.02 | 损失与衰减链 | 每项顺序、单位、已含标志、模型/时段；不重复PR和损失。 | T-OUTLINE-APP03-02 | NOT_IMPLEMENTED |

### APP04 CAPEX明细

| 稳定子项ID | 内容 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|
| APP04.01 | 逐项含税及分类明细 | 设备/工程/开发/管理/预备费/建设期利息，储能/土地是否包含明示。 | T-OUTLINE-APP04-01 | NOT_IMPLEMENTED |
| APP04.02 | 报价与投资勾稽 | 数量单价金额、报价时点有效性、付款时点/资产/税口径及CH14总额。 | T-OUTLINE-APP04-02 | NOT_IMPLEMENTED |

### APP05 OPEX、折旧、更换与税费

| 稳定子项ID | 内容 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|
| APP05.01 | 运营更换及资产计划 | 评价期逐年运维、租金、通胀、更换、原值残值折旧；折旧不是现金支出。 | T-OUTLINE-APP05-01 | NOT_IMPLEMENTED |
| APP05.02 | 适用税与年度勾稽 | 税制证据/抵扣/结转/优惠，实际税金与财务现金流一致。 | T-OUTLINE-APP05-02 | NOT_IMPLEMENTED |

### APP06 全周期项目与资本金现金流

| 稳定子项ID | 内容 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|
| APP06.01 | 项目投资全期现金流 | 建设期至评价末期逐年/日期现金流，不混融资，含营运变化与残值。 | T-OUTLINE-APP06-01 | NOT_IMPLEMENTED |
| APP06.02 | 资本金全期现金流 | 含债务提款/还本/付息/费，投资与资金平衡；与CH16和两现金流sheet一致。 | T-OUTLINE-APP06-02 | NOT_IMPLEMENTED |

### APP07 偿债明细

| 稳定子项ID | 内容 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|
| APP07.01 | 有债务偿债计划 | 期初余额/提款/本金/利息/费用/期末余额/CFADS/DSCR逐期。 | T-OUTLINE-APP07-01 | NOT_IMPLEMENTED |
| APP07.02 | 无债务或零分母说明 | 无债务附录仍保留且写不适用；零偿债额单列不可计算原因。 | T-OUTLINE-APP07-02 | NOT_IMPLEMENTED |

### APP08 敏感性与情景数据

| 稳定子项ID | 内容 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|
| APP08.01 | 单因素与组合底表 | 七类最低变量敏感性和悲观/基准/乐观参数及结果，变化边界保留。 | T-OUTLINE-APP08-01 | NOT_IMPLEMENTED |
| APP08.02 | 阈值与属性验收 | 盈亏平衡、门槛差距、单因素其他条件不变、投资/电量变形方向及独立参考。 | T-OUTLINE-APP08-02 | NOT_IMPLEMENTED |

### APP09 政策适用性

| 稳定子项ID | 内容 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|
| APP09.01 | 政策条款与有效期 | 地区/类型/基准日/文号/版本/原文位置/许可/替代关系。 | T-OUTLINE-APP09-01 | NOT_IMPLEMENTED |
| APP09.02 | 核验与限制意见 | 适用/不适用/待核/过期/冲突，不能由历史文件推断现行许可。 | T-OUTLINE-APP09-02 | NOT_IMPLEMENTED |

### APP10 未完成事项

| 稳定子项ID | 内容 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|
| APP10.01 | 待核与冲突清单 | 每项ID、缺证影响、责任方、到期、关闭证据和阻断级别。 | T-OUTLINE-APP10-01 | NOT_IMPLEMENTED |
| APP10.02 | 推进条件与里程碑 | 与四态建议一致的触发阈值、下一阶段专项及停止/重启条件。 | T-OUTLINE-APP10-02 | NOT_IMPLEMENTED |

### APP11 公式逐符号字典

| 稳定子项ID | 内容 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|
| APP11.01 | 全部公式注册 | 公式ID/中英名/LaTeX/文本/输入输出/来源/边界/假设/优先级/算例/test_id。 | T-OUTLINE-APP11-01 | NOT_IMPLEMENTED |
| APP11.02 | 全部符号逐一解释 | 每字符、下上标、集合/求和范围、单位/量纲、来源、边界与验证；无孤立未释符号。 | T-OUTLINE-APP11-02 | NOT_IMPLEMENTED |

### APP12 全部术语中英词典

| 稳定子项ID | 内容 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|
| APP12.01 | 中英全称缩写 | GHI/DNI/DHI/POA/GTI/PVOUT/PR/DC/AC/STC/CAPEX/OPEX/PPA/NPV/IRR/LCOE/DSCR/CFADS/SOC/EPC/GIS/TMY等。 | T-OUTLINE-APP12-01 | NOT_IMPLEMENTED |
| APP12.02 | 首次释义与单位区分 | 正文第一次中英全称+缩写，术语索引回链；辐照度/量、功率/能量、DC/AC及单位投资严格区分。 | T-OUTLINE-APP12-02 | NOT_IMPLEMENTED |

### APP13 版本与数据质量说明

| 稳定子项ID | 内容 | 可测验收断言 | 未来测试ID | 状态 |
|---|---|---|---|---|
| APP13.01 | 同源版本与哈希 | model_version/run_id/input_hash/source_snapshot_id/result_hash及schema/formula/template版本，与四文件相同。 | T-OUTLINE-APP13-01 | NOT_IMPLEMENTED |
| APP13.02 | 成熟度与审阅边界 | 各证据轴等级、来源质量、假设/冲突、变更/核验记录、导出重算声明与审核状态。 | T-OUTLINE-APP13-02 | NOT_IMPLEMENTED |

## 5. 图表、公式、页码及覆盖导出契约

- 最低图表：站址/边界与布局示意；12月资源与电量；物理能量/损失链；年度项目及股东现金流；敏感性和方案比较。无可靠数据则图位给“缺资料无法绘制+原因”，不能画似真数据。配储另有SOC/功率/电量时序图；容量/入出能量单位明确。
- 图表/公式稳定ID用所属内容块前缀；正文显示编号、题注、单位、数据来源与边界。跨页表重复表头，引用目标存在；目录及页码由真实排版渲染后产生，不编造源报告页码或输出报告页数。
- 机器导出覆盖必须逐子项形成 `requirement_id -> stage -> pv_type -> chapter_id/content_id -> user_input_ids -> data_source_ids -> formula_ids -> output_file/sheet/paragraph -> test_id -> status/evidence`。05/06/08由其他基线统一；本文提供稳定章/子项/附录ID，不以“后续补充”删除用户明确子项。
- 未来测试 `T-OUTLINE-IDS` 验证18章13附录集合/顺序/唯一；`T-OUTLINE-NINE-TYPES`对九类逐子项覆盖；`T-OUTLINE-UNKNOWN`验证未知不删章；`T-OUTLINE-NA-REASON`验证不适用理由；`T-OUTLINE-SYMBOLS`与`T-OUTLINE-GLOSSARY`核对所有符号/术语；全部NOT_IMPLEMENTED。
- 静态目录存在不是语义覆盖；文档齐全不是计算正确，计算正确不是数据真实，四文件正常打开不是平台调用或审核通过。六种门禁和四文件细则见10。
