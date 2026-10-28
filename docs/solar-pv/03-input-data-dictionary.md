# 输入数据字典与分级采集契约

> 基线版本：`solar-pv-input-catalog/1.0.0`。依据完整提示词第1–8节冻结；本文件与 `03-input-fields.json` 一一对应。**文档已定义不等于功能已实现；字段解析器、运行时 JSON Schema、采集交互、数据验证、等级判定与测试均为 `NOT_IMPLEMENTED`。** 本轮不创建源码、fixture 或测试文件，不声明任何现行政策/标准已核实。

## 1. 字段、值、证据的分离

- `03-input-fields.json` 是机器可读的**字段目录**，不是已经可执行的 JSON Schema；未来 Phase 2 才从它实现共享 schema 与九类独立 schema。所有field_id为点式，如 `project.name`、`site.latitude`、`system.dc_capacity`。永不按显示标题重命名既有ID，废弃保留迁移映射。
- 每个字段有 `field_id,type,unit,constraints,required_level,provenance_kinds,validation,substitutable,chapter_ids,pv_types`。`required_level` 分别定义L1/L2/L3，不表示一切字段第一轮必填；条件字段按下文规则触发。顶层额外属性、类型强转、NaN/Infinity不默认放行。
- 数值用有限JSON number/integer；百分比保存0..1，显示百分号。`1`为无量纲，`null`单位表示文字或逻辑项无单位。`currency`以 `project.currency` 解析；币种变化需汇率及日期证据。kWp/MWp、kWac/MWac、kWh、kVA、Wp、元/Wp与元/kWp不得混用。辐照度W/m²与辐照量kWh/m²不能仅改标签。
- `UNKNOWN` 用 `value:null` 加缺失原因，不能把0、空串、`待核实`当有效数值；0是实际数值且需证据。数组空值不是零负荷/零投资。`not_applicable`需理由、核验者和触发条件，不能用来规避未知。
- 数组也是带provenance的值。对象数组每个item有稳定 `row_id`，每个item的**每个原子值**分别保存provenance，不能只给整组一个URL。标量数组如前置task_id列表，每个标量元素保存稳定元素实例ID和独立provenance，不要求给string伪加row_id。目录以 `load.series.timestamp` 等点式ID定义对象item字段；实例以 `field_instance_id` 与row_id/元素实例ID定位，不把数组下标塞进稳定field_id。JSON的array.items.field_ids是对象item结构，标量数组则以items.type明确类型，不是十个大类占位。
- 所有数值事实只来自U/D/C的可核查证据；AI用于资料理解、差异说明和风险解释，不可虚构电价、光照、真实发电、成本、审批、认证或页码。计算值C必须保存计算运行、公式/转换规则与上游实例链。

## 2. 第一轮最小采集与条件必填

第一轮只收集：①项目类型；②具体位置/地址或经纬度；③面积或装机至少其一；④消纳/销售模式；⑤期望回收期或IRR至少其一。项目名可先用非事实的临时会话标签；投资预算可填也可待估。**不要求用户同时知道容量和面积，不要求用户先知道投资额，更不能以目标IRR倒推真实造价或光照。**

若用户仅说城市/面积/预算，接受输入，输出站址未明确的L1草稿/缺口，而非编造坐标或阻断对话；下一轮先问具体地块/屋顶与消纳模式等会改变结论的少量问题。目标未定可以继续采集，但不能声称已满足用户投资门槛。不得第一轮抛出本字典长表单。

| 条件规则ID | 触发与约束 | 未满足处理 | 未来测试ID / 状态 |
|---|---|---|---|
| IN-C01 | `site.address` 或成对latitude+longitude；详细边界L3按类型需要 | 仅城市：站址UNKNOWN，不能输出实测资源/建设可行 | T-IN-FIRST-LOCATION / NOT_IMPLEMENTED |
| IN-C02 | total_area/usable_area/dc_capacity至少其一；容量可由面积显式估算 | 缺失追问；不要求预算；估算范围和方法入账 | T-IN-FIRST-SIZE / NOT_IMPLEMENTED |
| IN-C03 | payback_years/project_irr/equity_irr至少一个作为目标；口径需后补 | 未指定仅给指标，不给达标结论 | T-IN-FIRST-TARGET / NOT_IMPLEMENTED |
| IN-C04 | 自用/余电或PPA等需匹配时序负荷、计量边界和真实可避免费 | 无曲线只能做自用率假设情景，真实自用率UNKNOWN | T-IN-LOAD / NOT_IMPLEMENTED |
| IN-C05 | 全额上网需售电/交易机制；无需自用负荷不等于用屋顶节省模型 | 收入边界缺失则UNKNOWN，非套用工商业自用电价 | T-IN-FULL-EXPORT / NOT_IMPLEMENTED |
| IN-C06 | 有债务时贷款期限、利率、提款还本付息费、CFADS及DSCR定义必需 | 未融资DSCR为不适用；偿债额为0不得除零造数 | T-IN-DEBT / NOT_IMPLEMENTED |
| IN-C07 | 有配储必须选pv_storage及非递归base_pv_type并具备独立SOC与调度 | 未实现或缺时序禁止用无储能min公式冒充 | T-IN-STORAGE / NOT_IMPLEMENTED |
| IN-C08 | 屋顶派生类型需要结构/荷载/剩余寿命/消防与产权；地面派生需要土地/地勘/坡度/送出 | 不适用必须有依据；权属安全严重未决阻止肯定结论 | T-IN-SITE-TYPE / NOT_IMPLEMENTED |
| IN-C09 | 边界顶点需坐标系和有效多边形；时序需时区/时间粒度/覆盖区间 | 无时区、重复/跳时、DST/闰年缺口不静默补零 | T-IN-SPATIAL-TEMPORAL / NOT_IMPLEMENTED |
| IN-C10 | PPA/分成/租赁/其他收益须合同边界及税费；目标/预算不替代报价 | 收益冲突保留CONFLICT；无依据其他收益不计作事实 | T-IN-CONTRACT / NOT_IMPLEMENTED |
| IN-C11 | 负价格只在合法市场/合同结算模型及证据下接受；费用为负另审 | 非法负面积/容量直接拒绝；负电价标核验而非取绝对值 | T-IN-NEGATIVE / NOT_IMPLEMENTED |
| IN-C12 | 所有数组按item字段逐行；每个单元的类型、单位和来源相同义务 | 缺row_id或原子provenance不能升级成熟度 | T-IN-ARRAY-PROVENANCE / NOT_IMPLEMENTED |
| IN-C13 | 固定/分时价格表与市场价格时序按结算方法选择，不强制两种资料同时齐备；避免购电价仅自用收益触发，售电价仅有上网结算触发 | 两类均无可靠价格依据时UNKNOWN；不得以未触发为由豁免真实收入证据 | T-MISSING-TARIFF / NOT_IMPLEMENTED |

未触发IN-C04的纯全额售电项目无需提供用户负荷/账单；明确贷款比例为0且无债务计划/余额时IN-C06不触发，无融资协议/CFADS定义不降低成熟度。触发条件UNKNOWN不是“未触发”。数组item的REQUIRED仅在父容器适用且该item存在时生效，父数组不适用时不制造虚假item；章/附录/sheet仍保留不适用说明。

`tariff.periods`采用本地日内半开时段：起点00:00–23:59，终点同范围或仅日末24:00；跨午夜拆为两条合法日内记录。按生效期、季节、工作日和时区归一后检查覆盖、重叠与缺口，DST用有时区的真实时序匹配，禁止29:59或24:01。起始任务的`predecessor_ids=[]`表示已确认无前置，null表示UNKNOWN；标量列表元素各带provenance/稳定实例ID，不能只给整组来源。

## 3. 全字段provenance值记录

以下键对每个字段、数组容器、每个item原子值均须存在。非适用元数据可null，但应写 `missing_reason` 及原因，不能伪造来源。多个来源保留多个候选记录，正式选取需复核留痕。机密资料仅给附件ID和必要节/单元格，不输出全文或敏感绝对路径。元数据自身不递归套娃，但必须遵循记录类型与受控来源约束。

| 键 | 类型 | 语义与校验 |
|---|---|---|
| `field_id` | string | 引用本字段目录，不随行序改变 |
| `field_instance_id` | string | 同field_id多行用row_id/嵌套路径定位唯一值 |
| `value` | typed-or-null | 严格匹配字段类型；UNKNOWN为null不伪造0 |
| `unit` | string-or-null | 匹配字段单位；无量纲为1，无单位为null |
| `provenance_kind` | U/D/C/AI/null | 未知允许null并说明原因，不默认AI |
| `source_id` | string-or-null | 关联来源索引；C指向上游输入与计算运行 |
| `source_url_or_attachment` | string-or-null | 公共来源URL或脱敏附件ID，不输出敏感绝对路径 |
| `source_section_or_cell` | string-or-null | 页/节/表/单元格/行范围；无法定位说明缺口 |
| `measurement_period` | object-or-null | start/end/timezone/interval/coverage；非观测数据解释不适用 |
| `published_at` | date-or-null | 公开或文件发布日期 |
| `retrieved_at` | datetime-or-null | 带时区获取时间，禁止生成虚假历史时间 |
| `effective_from` | date-or-null | 生效起 |
| `effective_to` | date-or-null | 生效止；无期限也需依据 |
| `geography` | string-or-null | 地区/站址/坐标覆盖 |
| `status` | enum | VERIFIED/UNVERIFIED/ASSUMED/UNKNOWN/CONFLICT |
| `confidence_basis` | string | 证据与质量文字依据；单一置信数字不合格 |
| `reviewer` | string-or-null | 核验人/角色；不能伪造签署 |
| `last_updated` | datetime | 带时区最后变更时间 |
| `missing_reason` | string-or-null | 应有元数据缺失原因；UNKNOWN关键依据不可省 |
| `candidate_ids` | array<string> | 冲突保留候选引用及选用依据 |
| `transformation_rule_ids` | array<string> | 单位/清洗/聚合/计算转换记录 |
| `upstream_instance_ids` | array<string> | C类计算血缘；AI解释引用证据 |
| `license_status` | enum | AUTHORIZED/REQUIRES_REVIEW/DENIED/UNKNOWN |
| `sensitivity` | enum | PUBLIC/INTERNAL/CONFIDENTIAL/RESTRICTED |

### 3.1 来源与状态不能混为一谈

| 来源/状态 | 允许行为 | 禁止行为 |
|---|---|---|
| U 用户提供 | 保存原附件位置/陈述者/时点；核查后才可VERIFIED | 用户说过不等于权属/并网已获证实 |
| D 外部数据 | 实际访问、版本、地区、时段、许可核验；缓存快照 | 只有URL不算获取全文；API失败不构造仿真真实值 |
| C 确定性计算 | 链接输入实例、公式版本、运行及输出边界 | LLM自由算数；用结果倒改输入；丢失上游不确定性 |
| AI 分析解释 | 引证事实、说明假设及待核事项 | 自造价格/成本/光照/批准/成功概率；把分析当测绘或结构鉴定 |
| VERIFIED | 明确证据与核验者、适用性和有效期充分 | confidence=0.9而无依据；核验失效后沿用 |
| UNVERIFIED | 有候选但尚未核实 | 输出“正式许可”“实际发电量”等确定性事实 |
| ASSUMED | 显式可编辑情景，说明方法、区间及级别上限 | 将PR80%、衰减0.5%、25年、运维1%标作统一国家标准 |
| UNKNOWN | value=null、缺口、责任人及后续核验 | 用0、均值或类似项目实绩冒充本项目 |
| CONFLICT | 保留候选及差异，人工核验/有依据选取；下游继承冲突 | 静默取平均、取有利值或覆盖旧证据 |

### 3.2 时间、许可、地域与隐私

政策/电价/税制/报价按评价基准日、站址、类型、生失效日和替代文件判适用；历史成本和跨年案例只作同口径参考。气象观测期不等于发布日期；retrieved_at不等于effective_from。远端上传须明确授权，默认只本地处理；未知许可为REQUIRES_REVIEW。任何付费/新数据源需另行批准。权限、摘要日志、脱敏引用、保存期限及撤销处理另见09安全基线，不能把文档设计当OS沙箱。

## 4. L1/L2/L3证据成熟度门槛（不是排版等级）

等级为下表全部适用轴的最低等级，不按字段填写数量或平均分升级。必需字段UNKNOWN可存储并导出草稿，但不等于等级门槛通过。九类专项轴和共用轴同时满足；详见07。L3仍非正式工程设计、检测、并网审查或行政审批替代。

| 证据轴 | L1 初筛 | L2 预可研 | L3 深度预可研 | 降级/阻断条件 |
|---|---|---|---|---|
| 位置与权属 | 具体位置优先；城市级明确站址待定 | 具体站址/面积依据、权属基本核查、约束清单 | 边界测绘、有效权利文件及可实施面积核对 | 只有城市不能站址可行；已证实禁止建设一票否决 |
| 结构/土地/消防 | 只能列核查项，不宣称安全 | 基本建设条件和结构/用地/消防依据、专项检查计划 | 适用的结构鉴定、荷载/地勘/生态专项核查更充分 | 超荷载、违法用地等重大事实不被高IRR抵消 |
| 资源 | 区域参考/显式示例可做范围 | 可靠且受许可站址资源、12月、版本区间、损失边界 | 更充分时序/多年差异、交叉核验、误差来源 | 接口失败、许可不清不能补造实测；重大资源冲突降级 |
| 方案设备 | 面积或容量估算区间 | DC/AC、布局、至少基准及可行替代、损失链 | 测绘/设备技术与串并联、约束细化更充分 | DC/AC、kW/kWh串用、结构约束未处理不达标 |
| 并网与送出 | 条件情景，意见待核实 | 接入基本假设/容量/电压/送出成本清楚，未许可显式条件 | 接入意见、容量、送出与限制核查更充分 | 无意见不能称具备并网资格；严重关键接入未决暂缓 |
| 消纳与电价 | 年总量只作参考，自用率假设 | 自用项目具可靠同粒度曲线与可避免费；售电项目适用交易价及条款 | 更充分12月账单/合同、时序质量与结算复核 | 无负荷真实自用率UNKNOWN；电价未知收入与IRR不确定 |
| 投资与运营 | 预算/区间假设，不作事实报价 | 分类成本、税含状态、区域价格基年、运维/替换边界 | 有效报价、合同和资产税务依据更充分 | 用目标回报倒推造价禁止；报价失效需重核 |
| 融资/税/现金流 | 可无融资情景；边界写明 | 项目与资本金分开、实际税金、折旧非现金、债务闭合 | 适用协议、税务确认/偿债约定、时点细化 | IRR无根/多根不得给伪百分比；税/融资重大缺口降级 |
| 风险与追溯 | 缺口完整，事实/假设分离 | 全字段provenance、冲突处置、政策适用、风险责任人 | 核验记录/版本及专项闭环更充分 | 重大来源冲突、越权、无许可、伪造数据阻断 |
| 输出与证据 | 可生成醒目标注未决策就绪的有限草稿 | 18章/13附录不删、四文件同源及全部门禁 | 同L2并附更充分核验、审阅记录 | 缺PDF/未缓存公式/视觉未检验均不能四文件PASS |

L2允许少量**有区间、有出处、非关键且不改变决策**的工程假设，但必须逐项说明和敏感性分析；不允许用假设顶替法规、安全、正式并网许可。L3按类型专项成熟度评审，不能仅上传几份附件自动升级。用户目标是最后的门槛，不能反向调整客观数据。

## 5. 四态投资建议的判定顺序

建议只允许四种中文枚举，与技术实现状态NOT_IMPLEMENTED、门禁PASS/FAIL/BLOCKED、证据状态UNKNOWN等互相独立。

| 顺序 | 条件 | 建议 | 必须记录的输出/未来测试 |
|---|---|---|---|
| 1 | 已证实的法律/产权/结构/消防/禁止建设/关键接入拒绝等否决；或充分证据证明当前方案达不到约束且无合理替代 | 不建议按当前方案推进 | 否决证据、条款适用及替代/重启条件；T-DECISION-VETO，NOT_IMPLEMENTED |
| 2 | 权属/结构/消防/关键并网等严重未决或CONFLICT；关键资源/成本/电价/负荷无法确定；IRR不可解释；目标未明确 | 暂缓决策 | 缺口、阻断影响、责任人/核验期限，不能写肯定可行；T-DECISION-UNKNOWN，NOT_IMPLEMENTED |
| 3 | L2及以上、无否决/严重未决；可控且非关键条件尚待闭合，保守情景达门槛；条件关闭前不作投资批准 | 有条件推进 | 条件、可核验阈值、有效期、失败退回/暂缓；T-DECISION-CONDITIONAL，NOT_IMPLEMENTED |
| 4 | L2/L3充分证据、关键条件核实、技术商业财务达明确目标、风险可接受 | 建议进入下一阶段 | 指向正式可研/设计/审批而非已批准开建；T-DECISION-NEXT，NOT_IMPLEMENTED |

财务充分但达不到目标且无可行改进时为“不建议按当前方案推进”；数据不足导致是否达标未知时为“暂缓决策”，不可混淆。恰等于门槛按用户明确的≥或>口径；门槛类型不清先补问。L1不得给肯定投资可行结论，可建议继续补资料，但四态保持“暂缓决策”。重大否决优先于高IRR；不能通过加权评分抵消。无目标或评价期内未回收、IRR无唯一根，按原因与证据独立说明，禁止强行给数。所有规则未来需冲突组合/优先级测试，当前NOT_IMPLEMENTED。

## 6. 原子字段总表

分类代号：I=industrial_rooftop；G=utility_scale_ground；A=agri_pv；F=fishery_pv；S=pv_storage；P=public_rooftop；R=residential_pv；B=pv_carport_bipv；D=desert_mining；ALL=九类。S的屋顶/地面基座字段由storage.base_pv_type组合，不表示无条件套用工商业模型。来源代号U/D/C/AI见第3节。必填列按L1/L2/L3顺序；R=REQUIRED，O=OPTIONAL，C=CONDITIONAL。可替代仅显式假设，默认最高L1；不代表真实证据或关键门禁可替代。

下面表格逐字段列出完整契约；数组后紧接item字段，item行在JSON中有repeat_group。每行共同适用全字段provenance、有限数/日期/单位、有效性与冲突规则，细节以同版本JSON为机器目录。所有行实现与未来测试状态统一 `NOT_IMPLEMENTED`。


### 6.project 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `project.name` 项目名称 | string / — | {"minLength":1,"maxLength":2000} | R/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH01,CH02,CH03 | ALL |
| `project.owner` 项目业主 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH01,CH02,CH03 | ALL |
| `project.investor` 投资主体 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH01,CH02,CH03 | ALL |
| `project.developer` 开发主体 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH01,CH02,CH03 | ALL |
| `project.operator` 运营主体 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH01,CH02,CH03 | ALL |
| `project.contact_reference` 脱敏联系标识 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH01,CH02,CH03 | ALL |
| `project.pv_type` 项目分类 | string / — | {"enum":["industrial_rooftop","utility_scale_ground","agri_pv","fishery_pv","pv_storage","public_rooftop","residential_pv","pv_carport_bipv","desert_mining"]} | R/R/R | U | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH01,CH03 | ALL |
| `project.ownership_mode` 投建营所有权模式 | string / — | {"enum":["owner_invested","third_party","lease","ppa","revenue_share","other"]} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH03,CH10,CH16 | ALL |
| `project.sales_mode` 消纳/销售模式 | string / — | {"enum":["self_use_surplus_export","full_export","off_grid","hybrid","undecided"]} | R/R/R | U | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH03,CH10 | ALL |
| `project.has_storage` 是否配储 | boolean / — | {} | R/R/R | U | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH03,CH06,CH10 | ALL |

### 6.schedule 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `schedule.development_start` 开发开始日 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH13,CH16 | ALL |
| `schedule.construction_start` 开工计划 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH13,CH16 | ALL |
| `schedule.commissioning_date` 投产计划 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH13,CH16 | ALL |

### 6.project 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `project.evaluation_date` 评价基准日 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH13,CH16 | ALL |
| `project.currency` 评价币种 | string / — | {"pattern":"^[A-Z]{3}$","note":"代码与所用币种清单版本一并存档，不能默认为人民币。"} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH14,CH15,CH16 | ALL |
| `project.evaluation_years` 评价期 | integer / year | {"minimum":1,"maximum":100} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 可：用户指定年限；缺省只允许显式示例情景，禁止强制25年。；最高L1 | CH02,CH08,CH15,CH16 | ALL |
| `project.price_basis` 价格口径 | string / — | {"enum":["nominal","real"]} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH14,CH15,CH16 | ALL |
| `project.cashflow_tax_basis` 财务税前税后口径 | string / — | {"enum":["pre_tax","post_tax","both"]} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH16 | ALL |

### 6.targets 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `targets.budget_ceiling` 预算上限 | number / currency | {"minimum":0} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；仅评价目标差距，不进入发电、成本或电价反推；第一轮回收期或项目/资本金IRR至少一个目标可用。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH01,CH16,CH17,CH18 | ALL |
| `targets.payback_years` 期望回收期 | number / year | {"minimum":0} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；仅评价目标差距，不进入发电、成本或电价反推；第一轮回收期或项目/资本金IRR至少一个目标可用。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH01,CH16,CH17,CH18 | ALL |
| `targets.project_irr` 项目IRR门槛 | number / 1 | {"exclusiveMinimum":-1} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；仅评价目标差距，不进入发电、成本或电价反推；第一轮回收期或项目/资本金IRR至少一个目标可用。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH01,CH16,CH17,CH18 | ALL |
| `targets.equity_irr` 资本金IRR门槛 | number / 1 | {"exclusiveMinimum":-1} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；仅评价目标差距，不进入发电、成本或电价反推；第一轮回收期或项目/资本金IRR至少一个目标可用。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH01,CH16,CH17,CH18 | ALL |

### 6.finance 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `finance.project_discount_rate` 项目折现率 | number / 1 | {"exclusiveMinimum":-1} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；与名义/实际、税前/税后、项目现金流及时间基准相容，不能用股东率替换。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH01,CH16,CH17,CH18 | ALL |
| `finance.equity_discount_rate` 股东折现率 | number / 1 | {"exclusiveMinimum":-1} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；只用于股东口径；目标IRR不自动当折现率。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH01,CH16,CH17,CH18 | ALL |

### 6.targets 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `targets.risk_preference` 风险偏好 | string / — | {"enum":["conservative","balanced","aggressive","unspecified"]} | O/R/R | U | 仅评价目标差距，不进入发电、成本或电价反推；第一轮回收期或项目/资本金IRR至少一个目标可用。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH17,CH18 | ALL |
| `targets.payback_basis` 目标回收期起点/静动态口径 | string / — | {"enum":["static_from_investment","dynamic_from_investment","static_from_operation","dynamic_from_operation"]} | C/C/C | U | 仅评价目标差距，不进入发电、成本或电价反推；第一轮回收期或项目/资本金IRR至少一个目标可用。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH16,CH18 | ALL |

### 6.site 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `site.province` 省/州 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH03,CH04,CH05 | ALL |
| `site.city` 市 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH03,CH04,CH05 | ALL |
| `site.district` 区县 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH03,CH04,CH05 | ALL |
| `site.address` 具体地块/屋顶地址 | string / — | {"minLength":1,"maxLength":2000} | C/C/C | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH03,CH04,CH05 | ALL |
| `site.country` 国家或地区 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH03,CH04,CH05 | ALL |
| `site.crs` 坐标参考系 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH03,CH04,CH05 | ALL |
| `site.timezone` IANA时区标识 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH03,CH04,CH05 | ALL |
| `site.latitude` 纬度 | number / degree | {"minimum":-90,"maximum":90} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；纬经度成对，地点/坐标系/时区相容；仅城市不得冒充具体站址。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH03,CH04,CH05 | ALL |
| `site.longitude` 经度 | number / degree | {"minimum":-180,"maximum":180} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；与纬度配对，检查边界落点和反地理编码差异。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH03,CH04,CH05 | ALL |
| `site.elevation` 海拔 | number / m | {"minimum":-500,"maximum":9000} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 可：经授权DEM/地形数据匹配坐标，注明分辨率与误差。；最高L1 | CH04,CH05 | ALL |
| `site.boundary_attachment_id` 边界GIS附件引用 | string / — | {"minLength":1,"maxLength":2000} | O/O/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH11 | ALL |
| `site.boundary_vertices` 闭合多边形顶点 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=site.boundary_vertices.polygon_id,site.boundary_vertices.ring_index,site.boundary_vertices.vertex_index,site.boundary_vertices.latitude,site.boundary_vertices.longitude,site.boundary_vertices.row_id | O/O/R | U,D,C | 环闭合、点序有效、无自交；坐标系相容；边界附件摘要对应。；所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH11 | ALL |
| `site.boundary_vertices.polygon_id` 多边形ID | string / — | {"minLength":1,"maxLength":2000} | O/O/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH11 | ALL |
| `site.boundary_vertices.ring_index` 外环0/内环序号 | integer / — | {"minimum":0} | O/O/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH11 | ALL |
| `site.boundary_vertices.vertex_index` 顶点顺序 | integer / — | {"minimum":0} | O/O/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH11 | ALL |
| `site.boundary_vertices.latitude` 纬度 | number / degree | {"minimum":-90,"maximum":90} | O/O/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH11 | ALL |
| `site.boundary_vertices.longitude` 经度 | number / degree | {"minimum":-180,"maximum":180} | O/O/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH11 | ALL |
| `site.boundary_vertices.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH11 | ALL |
| `site.total_area` 总面积 | number / m2 | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 可：仅有用户面积时形成区间布局情景；可利用面积必须扣除消防、退界、通道及遮挡。；最高L1 | CH04,CH06,CH07,CH11 | ALL |
| `site.usable_area` 可利用面积 | number / m2 | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；0 < 可用面积 <= 总面积-排除面积；多边形/测绘和输入一致，不用预算反推。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 可：仅有用户面积时形成区间布局情景；可利用面积必须扣除消防、退界、通道及遮挡。；最高L1 | CH04,CH06,CH07,CH11 | ALL |
| `site.exclusion_area` 不可用面积 | number / m2 | {"minimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 可：仅有用户面积时形成区间布局情景；可利用面积必须扣除消防、退界、通道及遮挡。；最高L1 | CH04,CH06,CH07,CH11 | ALL |
| `site.terrain_slope` 地形坡度 | number / degree | {"minimum":0,"maximum":90} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH11 | ALL |
| `site.shading_fraction` 遮挡比例 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 可：仅有用户面积时形成区间布局情景；可利用面积必须扣除消防、退界、通道及遮挡。；最高L1 | CH04,CH06,CH07,CH11 | ALL |
| `site.area_basis` 面积测算依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH11,CH12 | ALL |
| `site.rights_holder` 土地/屋顶使用权主体 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH11,CH12 | ALL |
| `site.rights_document_id` 权属材料引用 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH11,CH12 | ALL |
| `site.land_classification` 土地性质 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH11,CH12 | ALL |
| `site.local_restrictions` 地方建设限制 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH11,CH12 | ALL |
| `site.transport_access` 交通及物流条件 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH11,CH12 | ALL |
| `site.geotechnical_reference` 地勘引用 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH11,CH12 | ALL |
| `site.flood_reference` 防洪排水依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH11,CH12 | ALL |
| `site.disaster_reference` 灾害评价依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH11,CH12 | ALL |
| `site.ecology_reference` 生态限制依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH11,CH12 | ALL |
| `site.rights_expiry` 权利到期日 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH15,CH18 | ALL |
| `site.rights_status` 权属核查状态 | string / — | {"enum":["verified","pending","disputed","prohibited"]} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH18 | ALL |

### 6.roof 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `roof.structure_type` 建筑结构类型 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH07,CH11,CH12 | I,P,R,B |
| `roof.material` 屋面材料 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH07,CH11,CH12 | I,P,R,B |
| `roof.age` 现有屋面年限 | number / year | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH07,CH11,CH12 | I,P,R,B |
| `roof.remaining_life` 屋面剩余年限 | number / year | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH07,CH11,CH12 | I,P,R,B |
| `roof.allowable_additional_load` 允许附加荷载 | number / kN/m2 | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH07,CH11,CH12 | I,P,R,B |
| `roof.design_added_load` 方案附加荷载 | number / kN/m2 | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；与允许附加荷载同单位、结构鉴定范围相同；超限为重大/否决风险，不由高收益覆盖。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH07,CH11,CH12 | I,P,R,B |
| `roof.slope` 屋面坡度 | number / degree | {"minimum":0,"maximum":90} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH07,CH11,CH12 | I,P,R,B |
| `roof.azimuth` 屋面方位角 | number / degree | {"minimum":0,"exclusiveMaximum":360} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH07,CH11,CH12 | I,P,R,B |
| `roof.structure_report_id` 结构鉴定引用 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH07,CH11,CH12 | I,P,R,B |
| `roof.fire_access_reference` 消防及疏散依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH07,CH11,CH12 | I,P,R,B |
| `roof.waterproof_plan` 防水与检修方案 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH07,CH11,CH12 | I,P,R,B |

### 6.system 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `system.dc_capacity` 目标/设计DC容量 | number / kWp | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；块数×组件Wp/1000一致；与可用面积和布局相容；DC不是AC。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 可：面积/组件规格/退界及布局算法估算，输出可行容量区间并保留方法、设备版本及约束。；最高L1 | CH06,CH07,CH08,CH11 | ALL |
| `system.ac_capacity` 逆变输出AC容量 | number / kWac | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；逆变台数×单台AC一致；受变压器功率因数和接入约束；不得将kVA等于kW。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 可：面积/组件规格/退界及布局算法估算，输出可行容量区间并保留方法、设备版本及约束。；最高L1 | CH06,CH07,CH08,CH11 | ALL |
| `system.dc_ac_ratio` 容配比 | number / 1 | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；等于DC_kWp/AC_kWac且分母大于0；不得直接强制固定比例。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 可：面积/组件规格/退界及布局算法估算，输出可行容量区间并保留方法、设备版本及约束。；最高L1 | CH06,CH07,CH08,CH11 | ALL |
| `system.module_count` 组件块数 | integer / piece | {"minimum":1} | O/R/R | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 可：面积/组件规格/退界及布局算法估算，输出可行容量区间并保留方法、设备版本及约束。；最高L1 | CH06,CH07,CH08,CH11 | ALL |
| `system.module_power` 组件标称功率 | number / Wp | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `system.module_efficiency` 组件效率 | number / 1 | {"exclusiveMinimum":0,"maximum":1} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `system.module_length` 组件长 | number / m | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `system.module_width` 组件宽 | number / m | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `system.module_mass` 组件质量 | number / kg | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `system.module_voc` 开路电压 | number / V | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `system.module_vmp` 最大功率点电压 | number / V | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `system.module_isc` 短路电流 | number / A | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `system.module_imp` 最大功率点电流 | number / A | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `system.temperature_coefficient` 功率温度系数 | number / 1/degC | {"minimum":-0.02,"maximum":0.02} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `system.inverter_unit_ac` 单台逆变额定交流功率 | number / kWac | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `system.inverter_count` 逆变器台数 | integer / piece | {"minimum":1} | O/R/R | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `system.inverter_efficiency` 逆变转换效率 | number / 1 | {"exclusiveMinimum":0,"maximum":1} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `system.inverter_max_dc_voltage` 逆变DC电压上限 | number / V | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `system.inverter_mppt_min` MPPT电压下限 | number / V | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `system.inverter_mppt_max` MPPT电压上限 | number / V | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `system.inverter_max_input_current` 逆变输入电流上限 | number / A | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `system.modules_per_string` 每串组件数 | integer / piece | {"minimum":1} | O/R/R | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `system.parallel_strings` 并联串数 | integer / piece | {"minimum":1} | O/R/R | U,D,C | 组件串并总数相容；最大输入电流/MPPT范围/温度端电压专项校核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |

### 6.layout 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `layout.tilt` 倾角 | number / degree | {"minimum":0,"maximum":90} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `layout.azimuth` 方位角，北0顺时针 | number / degree | {"minimum":0,"exclusiveMaximum":360} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `layout.row_pitch` 行距 | number / m | {"exclusiveMinimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `layout.ground_coverage_ratio` 场地覆盖率 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |
| `layout.fire_setback` 消防退界宽度 | number / m | {"minimum":0} | O/R/R | U,D,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH11 | ALL |

### 6.system 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `system.module_model` 组件型号 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07 | ALL |
| `system.inverter_model` 逆变器型号 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07 | ALL |
| `system.mounting_type` 支架方式 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07 | ALL |
| `system.topology` 系统拓扑 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07 | ALL |
| `system.capacity_boundary` DC/AC及计量容量边界 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07 | ALL |

### 6.layout 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `layout.string_validation_reference` 串并联与温度电压校核依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH07 | ALL |

### 6.system 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `system.losses` 按物理顺序的损失分项 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=system.losses.kind,system.losses.value,system.losses.sequence,system.losses.boundary,system.losses.included_in_source,system.losses.method,system.losses.period,system.losses.row_id | O/R/R | U,D,C | 按sequence物理处理；included_in_source为真不得再扣；限发和可利用率不得重复。；所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。 | 不可；证据不足保留UNKNOWN | CH07,CH08 | ALL |
| `system.losses.kind` 损失项 | string / — | {"enum":["shading","soiling","snow","temperature","mismatch","dc_cable","inverter","clipping","availability","ac_cable","transformer","export_line","curtailment"]} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH07,CH08 | ALL |
| `system.losses.value` 损失率或模型参数 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH07,CH08 | ALL |
| `system.losses.sequence` 物理顺序 | integer / — | {"minimum":0} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH07,CH08 | ALL |
| `system.losses.boundary` 输入输出物理边界 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH07,CH08 | ALL |
| `system.losses.included_in_source` 是否已在资源/模拟中扣除 | boolean / — | {} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH07,CH08 | ALL |
| `system.losses.method` 相乘/时序/设备曲线方法 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH07,CH08 | ALL |
| `system.losses.period` 适用时段 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH07,CH08 | ALL |
| `system.losses.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH07,CH08 | ALL |
| `system.first_year_degradation` 首年初始衰减 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 可：仅显式情景；不得无依据采用0.5%等默认值。；最高L1 | CH07,CH08 | ALL |
| `system.annual_degradation` 后续年度衰减 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 可：仅显式情景；不得无依据采用0.5%等默认值。；最高L1 | CH07,CH08 | ALL |
| `system.unavailability` 不可利用率 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 可：仅显式情景；不得无依据采用0.5%等默认值。；最高L1 | CH07,CH08 | ALL |
| `system.degradation_segments` 分段衰减计划 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=system.degradation_segments.from_year,system.degradation_segments.to_year,system.degradation_segments.rate,system.degradation_segments.reset_on_replacement,system.degradation_segments.row_id | O/R/R | U,D,C | 分段年序连续不重叠，不越评价期；首年与后续衰减不重计。；所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。 | 不可；证据不足保留UNKNOWN | CH07,CH08 | ALL |
| `system.degradation_segments.from_year` 运营起年 | integer / year | {"minimum":1,"maximum":100} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH07,CH08 | ALL |
| `system.degradation_segments.to_year` 运营止年 | integer / year | {"minimum":1,"maximum":100} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH07,CH08 | ALL |
| `system.degradation_segments.rate` 年度衰减率 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH07,CH08 | ALL |
| `system.degradation_segments.reset_on_replacement` 替换后重置规则 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH07,CH08 | ALL |
| `system.degradation_segments.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH07,CH08 | ALL |

### 6.resource 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `resource.dataset_id` 资源数据集 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH05,CH08 | ALL |
| `resource.version` 数据集版本 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH05,CH08 | ALL |
| `resource.provider` 提供者 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH05,CH08 | ALL |
| `resource.model_method` 资源转置/模拟方法 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH05,CH08 | ALL |
| `resource.license_id` 许可引用 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH05,CH08 | ALL |
| `resource.tmy_method` 典型气象年构造方法 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH05,CH08 | ALL |
| `resource.spatial_resolution` 空间分辨率说明 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH05,CH08 | ALL |
| `resource.time_resolution` 时间分辨率说明 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH05,CH08 | ALL |
| `resource.uncertainty_basis` 不确定性依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH05,CH08 | ALL |
| `resource.poa_boundary` POA/GTI定义及平面 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH05,CH08 | ALL |
| `resource.period_start` 资源起日 | string / — | {"format":"date"} | O/R/R | D,U | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.period_end` 资源止日 | string / — | {"format":"date"} | O/R/R | D,U | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.is_tmy` 是否典型气象年 | boolean / — | {} | O/R/R | D,U | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05 | ALL |
| `resource.uncertainty_fraction` 有依据的不确定性幅度 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | D,U | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH17 | ALL |
| `resource.monthly` 12个月资源 | array / — | 稳定row_id；minItems=0，maxItems=12；item字段=resource.monthly.month,resource.monthly.ghi,resource.monthly.dni,resource.monthly.dhi,resource.monthly.poa,resource.monthly.ambient_temperature,resource.monthly.wind_speed,resource.monthly.days,resource.monthly.coverage,resource.monthly.row_id | O/R/R | U,D,C | 月份1..12不重不漏；年累计来自12月；覆盖率和气候区异常人工复核。；所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.monthly.month` 月份 | integer / — | {"minimum":1,"maximum":12} | O/R/R | D,U,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.monthly.ghi` 水平面总辐照量 | number / kWh/m2 | {"minimum":0} | O/R/R | D,U,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.monthly.dni` 直接法向辐照量 | number / kWh/m2 | {"minimum":0} | O/R/R | D,U,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.monthly.dhi` 水平面散射辐照量 | number / kWh/m2 | {"minimum":0} | O/R/R | D,U,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.monthly.poa` 组件平面辐照量 | number / kWh/m2 | {"minimum":0} | O/R/R | D,U,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.monthly.ambient_temperature` 环境平均温度 | number / degC | {"minimum":-90,"maximum":70} | O/R/R | D,U,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.monthly.wind_speed` 平均风速 | number / m/s | {"minimum":0} | O/R/R | D,U,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.monthly.days` 当月天数 | integer / day | {"minimum":28,"maximum":31} | O/R/R | D,U,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.monthly.coverage` 有效数据覆盖率 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | D,U,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.monthly.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.timeseries` 逐时气象 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=resource.timeseries.timestamp,resource.timeseries.interval_minutes,resource.timeseries.ghi,resource.timeseries.dni,resource.timeseries.dhi,resource.timeseries.poa,resource.timeseries.ambient_temperature,resource.timeseries.wind_speed,resource.timeseries.quality_flag,resource.timeseries.row_id | C/C/C | U,D,C | 时区、闰年及DST；无重复/逆序/隐式补零；W/m2按真实时长积分为kWh/m2。；所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.timeseries.timestamp` 带时区时间戳 | string / — | {"format":"date-time","timezoneRequired":true} | C/C/C | D,U,C | 严格解析ISO-8601带时区时间戳，拒绝无时区或不存在的本地时刻。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.timeseries.interval_minutes` 时段长 | number / minute | {"exclusiveMinimum":0} | C/C/C | D,U,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.timeseries.ghi` 水平面总辐照度 | number / W/m2 | {"minimum":0} | C/C/C | D,U,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.timeseries.dni` 直接法向辐照度 | number / W/m2 | {"minimum":0} | C/C/C | D,U,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.timeseries.dhi` 散射辐照度 | number / W/m2 | {"minimum":0} | C/C/C | D,U,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.timeseries.poa` 阵列平面辐照度 | number / W/m2 | {"minimum":0} | C/C/C | D,U,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.timeseries.ambient_temperature` 环境温度 | number / degC | {"minimum":-90,"maximum":70} | C/C/C | D,U,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.timeseries.wind_speed` 风速 | number / m/s | {"minimum":0} | C/C/C | D,U,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.timeseries.quality_flag` 质量标志 | string / — | {"enum":["valid","missing","imputed","outlier"]} | C/C/C | D,U,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.timeseries.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH08 | ALL |
| `resource.annual_comparison` 逐年气象差异 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=resource.annual_comparison.year,resource.annual_comparison.poa,resource.annual_comparison.coverage,resource.annual_comparison.difference_from_reference,resource.annual_comparison.row_id | O/R/R | U,D,C | 所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。 | 不可；证据不足保留UNKNOWN | CH05,CH17 | ALL |
| `resource.annual_comparison.year` 气象年份 | integer / year | {"minimum":1900,"maximum":2200} | O/R/R | D,U,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH17 | ALL |
| `resource.annual_comparison.poa` 年平面辐照量 | number / kWh/m2 | {"minimum":0} | O/R/R | D,U,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH17 | ALL |
| `resource.annual_comparison.coverage` 覆盖率 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | D,U,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH17 | ALL |
| `resource.annual_comparison.difference_from_reference` 较基准相对差异 | number / 1 | {} | O/R/R | D,U,C | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH17 | ALL |
| `resource.annual_comparison.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH05,CH17 | ALL |

### 6.grid 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `grid.connection_point` 接入点 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH09,CH10,CH14,CH18 | ALL |
| `grid.metering_boundary` 计量边界 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH09,CH10,CH14,CH18 | ALL |
| `grid.opinion_attachment_id` 并网意见附件 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH09,CH10,CH14,CH18 | ALL |
| `grid.permit_reference` 许可引用 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH09,CH10,CH14,CH18 | ALL |
| `grid.transaction_opinion` 交易意见 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH09,CH10,CH14,CH18 | ALL |
| `grid.protection_plan` 保护方案 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH09,CH10,CH14,CH18 | ALL |
| `grid.upgrade_plan` 升压及送出方案 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH09,CH10,CH14,CH18 | ALL |
| `grid.curtailment_basis` 限发依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH09,CH10,CH14,CH18 | ALL |
| `grid.connection_voltage` 接入电压 | number / kV | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH09,CH10,CH14 | ALL |
| `grid.transformer_capacity` 变压器容量 | number / kVA | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH09,CH10,CH14 | ALL |
| `grid.available_capacity` 可接入容量 | number / kWac | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH09,CH10,CH14 | ALL |
| `grid.line_length` 线路长度 | number / km | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH09,CH10,CH14 | ALL |
| `grid.export_power_limit` 上网功率上限 | number / kW | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；上网功率转时段电量必须乘时长；与变压器及合同约束相容。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH09,CH10,CH14 | ALL |
| `grid.power_factor` 设计功率因数 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；严格大于0；变压器kVA与kW换算保留依据。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH09,CH10,CH14 | ALL |
| `grid.opinion_status` 并网意见状态 | string / — | {"enum":["not_requested","pending","conditional","confirmed","rejected","expired"]} | O/R/R | U,D | confirmed须有效正式意见、接入点和容量匹配；UNVERIFIED不得输出具备并网资格。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH09,CH18 | ALL |
| `grid.opinion_valid_until` 意见有效截止日 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH09,CH18 | ALL |
| `grid.curtailment_assumption` 限发情景率 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 可：无正式依据时仅条件情景，不可宣称获准并网。；最高L1 | CH08,CH09,CH10,CH17 | ALL |

### 6.load 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `load.work_schedule` 工作制度 | string / — | {"minLength":1,"maxLength":2000} | O/C/C | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；条件IN-C04，未触发时不降成熟度，UNKNOWN不当作未触发。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.meter_id` 脱敏电表标识 | string / — | {"minLength":1,"maxLength":2000} | O/C/C | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；条件IN-C04，未触发时不降成熟度，UNKNOWN不当作未触发。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.meter_boundary` 用电计量边界 | string / — | {"minLength":1,"maxLength":2000} | O/C/C | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；条件IN-C04，未触发时不降成熟度，UNKNOWN不当作未触发。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.quality_basis` 曲线质量依据 | string / — | {"minLength":1,"maxLength":2000} | O/C/C | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；条件IN-C04，未触发时不降成熟度，UNKNOWN不当作未触发。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.profile_attachment_id` 负荷附件 | string / — | {"minLength":1,"maxLength":2000} | O/C/C | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；条件IN-C04，未触发时不降成熟度，UNKNOWN不当作未触发。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.timezone` 曲线时区 | string / — | {"minLength":1,"maxLength":2000} | O/C/C | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；条件IN-C04，未触发时不降成熟度，UNKNOWN不当作未触发。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.annual_energy` 全年用电量 | number / kWh | {"minimum":0} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；只作总量交叉核验，不能替代负荷曲线确定真实自用率。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.proposed_self_use_ratio` 用户提出自用率 | number / 1 | {"minimum":0,"maximum":1} | O/O/O | U | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；无可靠时序只允许ASSUMED情景；不准作VERIFIED真实消纳。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 可：只能作为无负荷的假设情景，不是真实自用率。；最高L1 | CH10,CH17 | ALL |
| `load.monthly_bills` 近12个月账单 | array / — | 稳定row_id；minItems=0，maxItems=24；item字段=load.monthly_bills.period_start,load.monthly_bills.period_end,load.monthly_bills.energy,load.monthly_bills.energy_charge,load.monthly_bills.demand_charge,load.monthly_bills.capacity_charge,load.monthly_bills.fixed_charge,load.monthly_bills.other_charge,load.monthly_bills.tax_amount,load.monthly_bills.total_charge,load.monthly_bills.attachment_id,load.monthly_bills.row_id | O/C/C | U,D,C | 分项税费加总等于总额；近12个月完整；非可避免费不得计节省。；所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。；条件IN-C04，未触发时不降成熟度，UNKNOWN不当作未触发。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.monthly_bills.period_start` 账期起 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.monthly_bills.period_end` 账期止 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.monthly_bills.energy` 购电电量 | number / kWh | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.monthly_bills.energy_charge` 电量电费 | number / currency | {} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.monthly_bills.demand_charge` 需量费 | number / currency | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.monthly_bills.capacity_charge` 容量费 | number / currency | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.monthly_bills.fixed_charge` 固定费 | number / currency | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.monthly_bills.other_charge` 其他费 | number / currency | {} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.monthly_bills.tax_amount` 税额 | number / currency | {} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.monthly_bills.total_charge` 账单总额 | number / currency | {} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.monthly_bills.attachment_id` 账单引用 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.monthly_bills.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.series` 同时间粒度负荷 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=load.series.timestamp,load.series.interval_minutes,load.series.energy,load.series.power,load.series.quality_flag,load.series.row_id | C/C/C | U,D,C | 与发电和电价同时间粒度及计量边界；功率×时长=电量；8760/8784或15分钟完整性检查。；所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。；条件IN-C04，未触发时不降成熟度，UNKNOWN不当作未触发。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.series.timestamp` 时段开始时间戳 | string / — | {"format":"date-time","timezoneRequired":true} | C/C/C | U,D | 严格解析ISO-8601带时区时间戳，拒绝无时区或不存在的本地时刻。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.series.interval_minutes` 时段长 | number / minute | {"exclusiveMinimum":0} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.series.energy` 时段负荷电量 | number / kWh | {"minimum":0} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.series.power` 时段平均功率 | number / kW | {"minimum":0} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.series.quality_flag` 质量标志 | string / — | {"enum":["valid","missing","estimated","outlier"]} | C/C/C | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |
| `load.series.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10 | ALL |

### 6.tariff 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `tariff.contract_id` 购售电合同引用 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH10,CH16 | ALL |
| `tariff.settlement_mode` 结算模式 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH10,CH16 | ALL |
| `tariff.market_region` 交易地区 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH10,CH16 | ALL |
| `tariff.policy_reference` 电价政策引用 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH10,CH16 | ALL |
| `tariff.negative_price_rule` 负电价条款 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 负电价不一刀切拒绝：仅凭适用合同/规则及明确结算模型接受；其余标冲突待核验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH10,CH16 | ALL |
| `tariff.non_avoidable_charges` 不可抵减费用说明 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 负电价不一刀切拒绝：仅凭适用合同/规则及明确结算模型接受；其余标冲突待核验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH10,CH16 | ALL |
| `tariff.revenue_share_boundary` 分成和购售电边界 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH10,CH16 | ALL |
| `tariff.ppa_price` PPA单价 | number / currency/kWh | {} | C/C/C | U,D | 负电价不一刀切拒绝：仅凭适用合同/规则及明确结算模型接受；其余标冲突待核验。；拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.revenue_share` 收益分成比例 | number / 1 | {"minimum":0,"maximum":1} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.transaction_fee` 每电量交易费 | number / currency/kWh | {"minimum":0} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.periods` 分时电价表 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=tariff.periods.effective_from,tariff.periods.effective_to,tariff.periods.season,tariff.periods.weekday_rule,tariff.periods.start_time,tariff.periods.end_time,tariff.periods.period_label,tariff.periods.avoidable_price,tariff.periods.sale_price,tariff.periods.tax_included,tariff.periods.vat_rate,tariff.periods.policy_id,tariff.periods.row_id | O/C/C | U,D,C | 所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。；条件IN-C13，未触发时不降成熟度，UNKNOWN不当作未触发。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.periods.effective_from` 生效日 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.periods.effective_to` 失效日 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.periods.season` 适用月份/季节 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.periods.weekday_rule` 工作日及节假日规则 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.periods.start_time` 时段起 | string / — | {"pattern":"^(?:[01][0-9]\|2[0-3]):[0-5][0-9]$"} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.periods.end_time` 时段止 | string / — | {"pattern":"^(?:(?:[01][0-9]\|2[0-3]):[0-5][0-9]\|24:00)$"} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.periods.period_label` 峰平谷标识 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.periods.avoidable_price` 实际可避免购电价 | number / currency/kWh | {} | O/C/C | U,D | 负电价不一刀切拒绝：仅凭适用合同/规则及明确结算模型接受；其余标冲突待核验。；拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；条件IN-C04，未触发时不降成熟度，UNKNOWN不当作未触发。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.periods.sale_price` 售电价 | number / currency/kWh | {} | O/R/R | U,D | 负电价不一刀切拒绝：仅凭适用合同/规则及明确结算模型接受；其余标冲突待核验。；拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.periods.tax_included` 是否含税 | boolean / — | {} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.periods.vat_rate` 适用增值税率 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.periods.policy_id` 政策/合同来源ID | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.periods.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.market_series` 逐时市场结算价格 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=tariff.market_series.timestamp,tariff.market_series.interval_minutes,tariff.market_series.sale_price,tariff.market_series.transaction_fee,tariff.market_series.row_id | C/C/C | U,D,C | 所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.market_series.timestamp` 结算时间戳 | string / — | {"format":"date-time","timezoneRequired":true} | C/C/C | U,D | 严格解析ISO-8601带时区时间戳，拒绝无时区或不存在的本地时刻。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.market_series.interval_minutes` 时长 | number / minute | {"exclusiveMinimum":0} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.market_series.sale_price` 售电价 | number / currency/kWh | {} | C/C/C | U,D | 负电价不一刀切拒绝：仅凭适用合同/规则及明确结算模型接受；其余标冲突待核验。；拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.market_series.transaction_fee` 交易费用 | number / currency/kWh | {"minimum":0} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `tariff.market_series.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |

### 6.capex 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `capex.user_budget` 用户预算/待估投资 | number / currency | {"minimum":0} | O/O/O | U | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 可：无报价仅形成区间估算并标记假设，预算不是实际成本。；最高L1 | CH14,CH16 | ALL |
| `capex.estimate_basis` 估算依据与价格基年 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14 | ALL |
| `capex.contingency_rate` 预备费率 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 可：仅显式可编辑情景。；最高L1 | CH14 | ALL |
| `capex.includes_storage` 投资是否含储能 | boolean / — | {} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14 | ALL |
| `capex.includes_land` 投资是否含土地/租赁 | boolean / — | {} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14 | ALL |
| `capex.includes_construction_interest` 是否含建设期利息 | boolean / — | {} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `capex.items` 投资逐项明细 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=capex.items.category,capex.items.description,capex.items.quantity,capex.items.quantity_unit,capex.items.unit_price,capex.items.amount,capex.items.tax_included,capex.items.vat_rate,capex.items.recoverable_vat_share,capex.items.quote_date,capex.items.quote_valid_until,capex.items.quote_attachment_id,capex.items.payment_date,capex.items.currency,capex.items.fx_rate,capex.items.asset_id,capex.items.row_id | O/R/R | U,D,C | 数量×单位价与金额相容；统一币种/含税；税额和资产台账关联；报价有效期复核。；所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `capex.items.category` 投资分类 | string / — | {"enum":["modules","inverters","mounting","cables","transformer_switchgear","grid_export","civil_works","roof_reinforcement","construction","transport","design","development","management","contingency","construction_interest","storage","land","other"]} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `capex.items.description` 项目名称规格 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `capex.items.quantity` 数量 | number / — | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `capex.items.quantity_unit` 数量单位 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `capex.items.unit_price` 单位造价 | number / currency/unit | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `capex.items.amount` 金额 | number / currency | {"minimum":0} | O/R/R | U,D,C | C实例必须引用数量和单价的上游实例、F-CAPEX-ITEM-AMOUNT公式版本与run_id；原报价金额和计算金额保留独立候选，禁止覆盖或伪标U/D。；拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `capex.items.tax_included` 是否含税 | boolean / — | {} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `capex.items.vat_rate` 增值税率 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `capex.items.recoverable_vat_share` 可抵扣税份额 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `capex.items.quote_date` 报价日 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `capex.items.quote_valid_until` 报价有效期 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `capex.items.quote_attachment_id` 报价附件 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `capex.items.payment_date` 支出日期 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `capex.items.currency` 报价币种 | string / — | {"pattern":"^[A-Z]{3}$"} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `capex.items.fx_rate` 评价币种换算率 | number / 1 | {"exclusiveMinimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `capex.items.asset_id` 对应资产ID | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `capex.items.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |

### 6.opex 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `opex.items` 运营费逐项计划 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=opex.items.category,opex.items.base_amount,opex.items.from_year,opex.items.to_year,opex.items.escalation_rate,opex.items.tax_included,opex.items.vat_rate,opex.items.recoverable_vat_share,opex.items.contract_id,opex.items.row_id | O/R/R | U,D,C | 起止年相容，现金运营费不包含折旧；租金不与分成或CAPEX重复。；所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `opex.items.category` 费项 | string / — | {"enum":["maintenance","cleaning","insurance","operations","land_rent","roof_rent","transaction","decommissioning","other"]} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `opex.items.base_amount` 基期年度费用 | number / currency/year | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `opex.items.from_year` 起年 | integer / year | {"minimum":1,"maximum":100} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `opex.items.to_year` 止年 | integer / year | {"minimum":1,"maximum":100} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `opex.items.escalation_rate` 通胀/递增率 | number / 1 | {"exclusiveMinimum":-1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `opex.items.tax_included` 是否含税 | boolean / — | {} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `opex.items.vat_rate` 适用税率 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `opex.items.recoverable_vat_share` 可抵扣税份额 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `opex.items.contract_id` 合同引用 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `opex.items.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |

### 6.assets 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `assets.depreciation` 资产折旧与残值 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=assets.depreciation.asset_id,assets.depreciation.asset_class,assets.depreciation.depreciable_basis,assets.depreciation.depreciation_years,assets.depreciation.method,assets.depreciation.residual_value,assets.depreciation.in_service_date,assets.depreciation.tax_basis_reference,assets.depreciation.row_id | O/R/R | U,D,C | 残值<=原值；累计折旧<=可折旧额；折旧为非现金，不重复扣经营支出。；所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `assets.depreciation.asset_id` 资产ID | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `assets.depreciation.asset_class` 资产分类 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `assets.depreciation.depreciable_basis` 可折旧原值 | number / currency | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `assets.depreciation.depreciation_years` 折旧年限 | integer / year | {"minimum":1,"maximum":100} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `assets.depreciation.method` 折旧方法 | string / — | {"enum":["straight_line","other_requires_methodology"]} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `assets.depreciation.residual_value` 残值 | number / currency | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `assets.depreciation.in_service_date` 启用日期 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `assets.depreciation.tax_basis_reference` 税法依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `assets.depreciation.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `assets.replacements` 设备更换计划 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=assets.replacements.asset_id,assets.replacements.year,assets.replacements.cost,assets.replacements.salvage,assets.replacements.downtime_days,assets.replacements.new_life,assets.replacements.performance_reset,assets.replacements.row_id | O/R/R | U,D,C | 所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。 | 不可；证据不足保留UNKNOWN | CH08,CH15,CH16 | ALL |
| `assets.replacements.asset_id` 被更换资产ID | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH08,CH15,CH16 | ALL |
| `assets.replacements.year` 更换年 | integer / year | {"minimum":1,"maximum":100} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH08,CH15,CH16 | ALL |
| `assets.replacements.cost` 更换开支 | number / currency | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH08,CH15,CH16 | ALL |
| `assets.replacements.salvage` 原设备处置回收 | number / currency | {} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH08,CH15,CH16 | ALL |
| `assets.replacements.downtime_days` 停机天数 | number / day | {"minimum":0,"maximum":366} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH08,CH15,CH16 | ALL |
| `assets.replacements.new_life` 新设备寿命 | number / year | {"exclusiveMinimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH08,CH15,CH16 | ALL |
| `assets.replacements.performance_reset` 性能恢复规则 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH08,CH15,CH16 | ALL |
| `assets.replacements.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH08,CH15,CH16 | ALL |

### 6.tax 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `tax.corporate_income_rate` 所得税率 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH15,CH16 | ALL |
| `tax.vat_output_rate` 销项税率 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH15,CH16 | ALL |
| `tax.surcharge_rate` 附加税率 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH15,CH16 | ALL |
| `tax.loss_carryforward_years` 亏损结转年限 | integer / year | {"minimum":0,"maximum":100} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH15,CH16 | ALL |

### 6.finance 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `finance.debt_ratio` 贷款比例 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；借款与股东出资、投资支出、建期利息口径平衡；0贷款时DSCR为不适用。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH15,CH16 | ALL |
| `finance.loan_rate` 贷款利率 | number / 1 | {"minimum":0} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH15,CH16 | ALL |
| `finance.loan_years` 贷款期限 | integer / year | {"minimum":1,"maximum":100} | C/C/C | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH15,CH16 | ALL |
| `finance.grace_years` 宽限期 | integer / year | {"minimum":0,"maximum":100} | C/C/C | U,D | 宽限期<=贷款期限；付息规则不能默认为免息。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH15,CH16 | ALL |
| `finance.debt_fee` 融资费用 | number / currency | {"minimum":0} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH15,CH16 | ALL |
| `finance.shareholder_cost` 股东资金成本 | number / 1 | {"exclusiveMinimum":-1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH15,CH16 | ALL |
| `finance.working_capital` 初始营运资金 | number / currency | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH15,CH16 | ALL |
| `finance.inflation_rate` 通胀率 | number / 1 | {"exclusiveMinimum":-1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH15,CH16 | ALL |

### 6.tax 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `tax.regime_reference` 法定税制适用依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `tax.incentive_reference` 税惠依据及期限 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `tax.vat_recovery_timing` 税额抵扣与现金支付时点 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `tax.surcharge_basis` 附加税计税基础 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |

### 6.finance 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `finance.loan_agreement_id` 融资协议引用 | string / — | {"minLength":1,"maxLength":2000} | O/C/C | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；条件IN-C06，未触发时不降成熟度，UNKNOWN不当作未触发。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `finance.cfads_definition` CFADS协议定义 | string / — | {"minLength":1,"maxLength":2000} | O/C/C | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；条件IN-C06，未触发时不降成熟度，UNKNOWN不当作未触发。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `finance.cashflow_timing` 年末/实际日期现金流时点 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH15,CH16 | ALL |
| `finance.repayment_method` 还款方法 | string / — | {"enum":["equal_principal","annuity","bullet","custom_schedule"]} | C/C/C | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH16 | ALL |
| `finance.debt_schedule` 债务合同/自定义计划 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=finance.debt_schedule.date,finance.debt_schedule.drawdown,finance.debt_schedule.principal,finance.debt_schedule.interest,finance.debt_schedule.fees,finance.debt_schedule.dscr_covenant,finance.debt_schedule.row_id | C/C/C | U,D,C | 提款-还本=余额变化；到期清偿；利息和手续费按合同；与项目/股权分流。；所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。；条件IN-C06，未触发时不降成熟度，UNKNOWN不当作未触发。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `finance.debt_schedule.date` 资金日期 | string / — | {"format":"date"} | C/C/C | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `finance.debt_schedule.drawdown` 借款提款 | number / currency | {"minimum":0} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `finance.debt_schedule.principal` 应还本金 | number / currency | {"minimum":0} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `finance.debt_schedule.interest` 应付利息 | number / currency | {"minimum":0} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `finance.debt_schedule.fees` 偿债费用 | number / currency | {"minimum":0} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `finance.debt_schedule.dscr_covenant` DSCR最低约定 | number / 1 | {"minimum":0} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |
| `finance.debt_schedule.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH14,CH16 | ALL |

### 6.revenue 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `revenue.other_items` 其他有据收益 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=revenue.other_items.kind,revenue.other_items.year,revenue.other_items.amount,revenue.other_items.contract_id,revenue.other_items.exclusive_boundary,revenue.other_items.row_id | C/C/C | U,D,C | 所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `revenue.other_items.kind` 收益类别 | string / — | {"minLength":1,"maxLength":2000} | C/C/C | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `revenue.other_items.year` 运营年 | integer / year | {"minimum":1,"maximum":100} | C/C/C | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `revenue.other_items.amount` 年度金额 | number / currency | {} | C/C/C | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `revenue.other_items.contract_id` 合同证据 | string / — | {"minLength":1,"maxLength":2000} | C/C/C | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `revenue.other_items.exclusive_boundary` 排他边界避免重复 | string / — | {"minLength":1,"maxLength":2000} | C/C/C | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |
| `revenue.other_items.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH10,CH16 | ALL |

### 6.policy 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `policy.applicability` 政策适用核验 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=policy.applicability.title,policy.applicability.document_number,policy.applicability.authority,policy.applicability.region,policy.applicability.issued_date,policy.applicability.effective_from,policy.applicability.effective_to,policy.applicability.clause,policy.applicability.superseded_by,policy.applicability.applicability_status,policy.applicability.reviewer,policy.applicability.row_id | O/R/R | U,D,C | 按站址、类别、基准日与生失效日判断；过期/替代/冲突不可当现行政策。；所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。 | 不可；证据不足保留UNKNOWN | CH02,CH09,CH10,CH12,CH15,CH18 | ALL |
| `policy.applicability.title` 政策名称 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH09,CH10,CH12,CH15,CH18 | ALL |
| `policy.applicability.document_number` 文号 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH09,CH10,CH12,CH15,CH18 | ALL |
| `policy.applicability.authority` 发布机关 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH09,CH10,CH12,CH15,CH18 | ALL |
| `policy.applicability.region` 适用地区 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH09,CH10,CH12,CH15,CH18 | ALL |
| `policy.applicability.issued_date` 发布日期 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH09,CH10,CH12,CH15,CH18 | ALL |
| `policy.applicability.effective_from` 生效日期 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH09,CH10,CH12,CH15,CH18 | ALL |
| `policy.applicability.effective_to` 失效日期 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH09,CH10,CH12,CH15,CH18 | ALL |
| `policy.applicability.clause` 适用条款 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH09,CH10,CH12,CH15,CH18 | ALL |
| `policy.applicability.superseded_by` 替代政策ID | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH09,CH10,CH12,CH15,CH18 | ALL |
| `policy.applicability.applicability_status` 核验结论 | string / — | {"enum":["applicable","not_applicable","pending","expired","conflict"]} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH09,CH10,CH12,CH15,CH18 | ALL |
| `policy.applicability.reviewer` 核验人 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH09,CH10,CH12,CH15,CH18 | ALL |
| `policy.applicability.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH09,CH10,CH12,CH15,CH18 | ALL |

### 6.attachments 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `attachments.register` 附件登记 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=attachments.register.attachment_id,attachments.register.kind,attachments.register.local_reference,attachments.register.sha256,attachments.register.license_status,attachments.register.remote_upload_consent,attachments.register.sensitivity,attachments.register.retention_until,attachments.register.document_date,attachments.register.row_id | O/R/R | U,D,C | 限制根目录、真实路径与符号链接；类型/压缩比/条目大小/宏与外链审查；不得远传无授权附件。；所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。 | 不可；证据不足保留UNKNOWN | CH02,CH04,CH18 | ALL |
| `attachments.register.attachment_id` 脱敏附件ID | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH04,CH18 | ALL |
| `attachments.register.kind` 附件种类 | string / — | {"enum":["survey","structure","quote","grid","rights","photo","gis","load","bill","contract","other"]} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH04,CH18 | ALL |
| `attachments.register.local_reference` 受控本地引用非公开绝对路径 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH04,CH18 | ALL |
| `attachments.register.sha256` 附件摘要 | string / — | {"pattern":"^[a-f0-9]{64}$"} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH04,CH18 | ALL |
| `attachments.register.license_status` 授权状态 | string / — | {"enum":["authorized","denied","requires_review","unknown"]} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH04,CH18 | ALL |
| `attachments.register.remote_upload_consent` 远端上传明确授权 | boolean / — | {} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH04,CH18 | ALL |
| `attachments.register.sensitivity` 资料敏感等级 | string / — | {"enum":["public","internal","confidential","restricted"]} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH04,CH18 | ALL |
| `attachments.register.retention_until` 保留期限 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH04,CH18 | ALL |
| `attachments.register.document_date` 文件日期 | string / — | {"format":"date"} | O/R/R | U,D | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH04,CH18 | ALL |
| `attachments.register.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH02,CH04,CH18 | ALL |

### 6.risk 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `risk.items` 阻断与待核事项 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=risk.items.risk_id,risk.items.category,risk.items.description,risk.items.severity,risk.items.evidence_state,risk.items.owner,risk.items.deadline,risk.items.trigger,risk.items.mitigation,risk.items.row_id | O/R/R | U,D,C | 所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。 | 不可；证据不足保留UNKNOWN | CH04,CH09,CH11,CH12,CH17,CH18 | ALL |
| `risk.items.risk_id` 风险ID | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH09,CH11,CH12,CH17,CH18 | ALL |
| `risk.items.category` 风险类型 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH09,CH11,CH12,CH17,CH18 | ALL |
| `risk.items.description` 风险事实或待核问题 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH09,CH11,CH12,CH17,CH18 | ALL |
| `risk.items.severity` 严重性 | string / — | {"enum":["veto","major","moderate","minor"]} | O/R/R | U,D,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH09,CH11,CH12,CH17,CH18 | ALL |
| `risk.items.evidence_state` 证据状态 | string / — | {"enum":["confirmed","pending","conflicted","resolved"]} | O/R/R | U,D,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH09,CH11,CH12,CH17,CH18 | ALL |
| `risk.items.owner` 责任主体 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH09,CH11,CH12,CH17,CH18 | ALL |
| `risk.items.deadline` 核查期限 | string / — | {"format":"date"} | O/R/R | U,D,AI | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH09,CH11,CH12,CH17,CH18 | ALL |
| `risk.items.trigger` 触发条件 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH09,CH11,CH12,CH17,CH18 | ALL |
| `risk.items.mitigation` 处置与关闭证据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH09,CH11,CH12,CH17,CH18 | ALL |
| `risk.items.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH04,CH09,CH11,CH12,CH17,CH18 | ALL |

### 6.schedule 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `schedule.tasks` 建设阶段任务 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=schedule.tasks.task_id,schedule.tasks.name,schedule.tasks.predecessor_ids,schedule.tasks.start_date,schedule.tasks.finish_date,schedule.tasks.owner,schedule.tasks.critical_path,schedule.tasks.row_id | O/R/R | U,D,C | 所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。 | 不可；证据不足保留UNKNOWN | CH13 | ALL |
| `schedule.tasks.task_id` 任务ID | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH13 | ALL |
| `schedule.tasks.name` 产权/并网/初设/招采/施工/调试/验收任务 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH13 | ALL |
| `schedule.tasks.predecessor_ids` 前置任务ID清单 | array / — | {"minItems":0,"maxItems":100000,"uniqueItems":true,"items":{"type":"string","minLength":1,"maxLength":2000},"references":"schedule.tasks.task_id","rejectSelfReference":true,"rejectCycles":true,"perScalarItemProvenance":true,"emptyArrayMeaning":"已确认无前置任务；UNKNOWN必须null及原因"} | O/R/R | U,D,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；[]为已确认无前置；null为UNKNOWN；逐标量item带provenance，引用task_id且唯一、无自引用/循环。 | 不可；证据不足保留UNKNOWN | CH13 | ALL |
| `schedule.tasks.start_date` 开始 | string / — | {"format":"date"} | O/R/R | U,D,AI | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH13 | ALL |
| `schedule.tasks.finish_date` 完成 | string / — | {"format":"date"} | O/R/R | U,D,AI | 日历日期真实存在；与评价基准日及对应生效区间交叉校验。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH13 | ALL |
| `schedule.tasks.owner` 责任方 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH13 | ALL |
| `schedule.tasks.critical_path` 是否关键路径 | boolean / — | {} | O/R/R | U,D,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH13 | ALL |
| `schedule.tasks.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH13 | ALL |

### 6.environment 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `environment.grid_emission_factor` 适用电网排放因子 | number / kgCO2e/kWh | {"minimum":0} | O/R/R | D,U | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH12 | ALL |
| `environment.factor_period` 排放因子年份与边界 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH12 | ALL |
| `environment.fire_reference` 消防评估依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH11,CH12 | ALL |
| `environment.approval_reference` 环评/水保/专项审批核验 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH12,CH13,CH18 | ALL |

### 6.agri 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `agri.crop_species` 农业品种 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | A |
| `agri.production_baseline` 农业生产基准 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | A |
| `agri.agricultural_compliance` 农业用地合规证据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | A |
| `agri.minimum_light_transmission` 作物最低透光要求 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | A |
| `agri.design_light_transmission` 设计透光比例 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | A |
| `agri.machine_clearance` 农机净高 | number / m | {"exclusiveMinimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | A |
| `agri.machine_access_width` 农机通道宽 | number / m | {"exclusiveMinimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | A |
| `agri.yield_impact_reference` 产量影响依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | A |
| `agri.irrigation_plan` 灌溉及耕作方案 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | A |

### 6.fishery 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `fishery.water_rights_reference` 水域及养殖权依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | F |
| `fishery.production_baseline` 渔业基线 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | F |
| `fishery.water_depth` 水深 | number / m | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | F |
| `fishery.water_level_variation` 水位变化 | number / m | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | F |
| `fishery.corrosion_class` 腐蚀等级及设计依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | F |
| `fishery.foundation_method` 水域基础施工方式 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | F |
| `fishery.access_plan` 水上施工运维通道 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | F |
| `fishery.water_quality_reference` 水质/养殖生态依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | F |
| `fishery.production_impact_reference` 渔业生产影响依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | F |

### 6.public 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `public.asset_authorization` 公共资产授权 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | P |
| `public.procurement_reference` 公共采购合规依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | P |
| `public.occupancy_schedule` 公共建筑使用时段 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | P |
| `public.fire_evacuation_reference` 公共人员消防疏散核验 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | P |
| `public.budget_approval` 预算审批核验 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | P |

### 6.residential 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `residential.property_consent` 产权及共有人同意 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | R |
| `residential.connection_standard` 低压接入依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | R |
| `residential.retail_tariff_reference` 居民电价依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | R |
| `residential.household_load_reference` 家庭实际负荷依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | R |
| `residential.consumer_contract_reference` 户用合同及消费者风险 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | R |

### 6.carport_bipv 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `carport_bipv.subtype` 车棚或BIPV子型 | string / — | {"enum":["carport","bipv_roof","bipv_facade"]} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | B |
| `carport_bipv.building_function` 建筑围护/停车功能 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | B |
| `carport_bipv.minimum_clearance` 净空高度 | number / m | {"exclusiveMinimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | B |
| `carport_bipv.fire_rating_reference` 耐火与认证依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | B |
| `carport_bipv.waterproof_reference` 防水排水依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | B |
| `carport_bipv.wind_load_reference` 抗风结构依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | B |
| `carport_bipv.replaced_material_cost` 替代建材成本 | number / currency | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；只对有证据的替代建材计算增量，不同时扣全额造价与替代收益。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | B |
| `carport_bipv.incremental_cost_boundary` 增量成本边界 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | B |
| `carport_bipv.ev_load_reference` 充电设施负荷与计量 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | B |

### 6.desert_mining 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `desert_mining.subtype` 荒漠/矿区子型 | string / — | {"enum":["desert","active_mine","closed_mine"]} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | D |
| `desert_mining.restoration_obligation` 生态修复义务依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | D |
| `desert_mining.subsidence_reference` 采空沉降/地质安全依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | D |
| `desert_mining.sand_dust_reference` 风沙及积尘依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | D |
| `desert_mining.water_supply` 清洗供水约束 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | D |
| `desert_mining.soil_reference` 地质土壤依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | D |
| `desert_mining.transmission_reference` 长距离送出方案 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | D |
| `desert_mining.land_rehabilitation_cost` 复垦修复成本 | number / currency | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH06,CH07,CH10,CH11,CH12,CH14,CH15,CH17,CH18 | D |

### 6.storage 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `storage.energy_capacity` 储能初始可用能量 | number / kWh | {"exclusiveMinimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH10,CH14,CH15,CH16,CH17 | S |
| `storage.nominal_energy` 储能标称能量 | number / kWh | {"exclusiveMinimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH10,CH14,CH15,CH16,CH17 | S |
| `storage.charge_power` 最大充电功率 | number / kW | {"exclusiveMinimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH10,CH14,CH15,CH16,CH17 | S |
| `storage.discharge_power` 最大放电功率 | number / kW | {"exclusiveMinimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH10,CH14,CH15,CH16,CH17 | S |
| `storage.charge_efficiency` 单向充电效率 | number / 1 | {"exclusiveMinimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH10,CH14,CH15,CH16,CH17 | S |
| `storage.discharge_efficiency` 单向放电效率 | number / 1 | {"exclusiveMinimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH10,CH14,CH15,CH16,CH17 | S |
| `storage.soc_min` 最小SOC | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；0<=SOC_min<=SOC_initial,terminal<=SOC_max<=1；SOC对应当期可用容量。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH10,CH14,CH15,CH16,CH17 | S |
| `storage.soc_max` 最大SOC | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH10,CH14,CH15,CH16,CH17 | S |
| `storage.soc_initial` 初始SOC | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH10,CH14,CH15,CH16,CH17 | S |
| `storage.soc_terminal` 终端SOC约束 | number / 1 | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH10,CH14,CH15,CH16,CH17 | S |
| `storage.self_discharge_rate` 每小时自放电率 | number / 1/hour | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH10,CH14,CH15,CH16,CH17 | S |
| `storage.calendar_fade` 年度日历衰减 | number / 1/year | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH10,CH14,CH15,CH16,CH17 | S |
| `storage.cycle_fade` 每等效循环衰减 | number / 1/cycle | {"minimum":0,"maximum":1} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH10,CH14,CH15,CH16,CH17 | S |
| `storage.cycle_life` 循环寿命 | number / cycle | {"exclusiveMinimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH10,CH14,CH15,CH16,CH17 | S |
| `storage.reserve_energy` 备用能量 | number / kWh | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH10,CH14,CH15,CH16,CH17 | S |
| `storage.auxiliary_power` 辅机功率 | number / kW | {"minimum":0} | O/R/R | U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH06,CH07,CH08,CH10,CH14,CH15,CH16,CH17 | S |
| `storage.coupling` AC/DC耦合 | string / — | {"enum":["ac_coupled","dc_coupled"]} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH07,CH10,CH16 | S |
| `storage.dispatch_mode` 调度目标 | string / — | {"enum":["self_consumption","arbitrage","contract_dispatch","hybrid"]} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH07,CH10,CH16 | S |
| `storage.grid_charging` 是否允许网充 | string / — | {"enum":["allowed","forbidden","pending"]} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH07,CH10,CH16 | S |
| `storage.simultaneous_charge_discharge` 同时充放电约束 | string / — | {"enum":["forbidden","requires_proof"]} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH07,CH10,CH16 | S |
| `storage.base_pv_type` 光伏基础工程分类 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 必须为已单独验收的非pv_storage基础类别；组合能力另验收，不能递归引用。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH07,CH09,CH10,CH12,CH15,CH16 | S |
| `storage.connection_boundary` 储能接入及计量边界 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH07,CH09,CH10,CH12,CH15,CH16 | S |
| `storage.dispatch_contract_id` 调度/收益合同依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH07,CH09,CH10,CH12,CH15,CH16 | S |
| `storage.fire_safety_reference` 储能安全消防依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH07,CH09,CH10,CH12,CH15,CH16 | S |
| `storage.replacement_rule` 电池更换与容量重置规则 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH07,CH09,CH10,CH12,CH15,CH16 | S |
| `storage.cycle_definition` 等效完整循环定义 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH04,CH07,CH09,CH10,CH12,CH15,CH16 | S |
| `storage.dispatch` 逐时储能调度 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=storage.dispatch.timestamp,storage.dispatch.interval_minutes,storage.dispatch.charge_from_pv,storage.dispatch.charge_from_grid,storage.dispatch.discharge_to_load,storage.dispatch.discharge_to_export,storage.dispatch.stored_energy_begin,storage.dispatch.stored_energy_end,storage.dispatch.usable_capacity,storage.dispatch.auxiliary_energy,storage.dispatch.row_id | C/C/C | U,D,C | 独立电池能量守恒、SOC/功率/效率/终端约束；光伏与网充收益分开，禁止同时充放电及重复售电收入。；所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH08,CH10,CH16 | S |
| `storage.dispatch.timestamp` 时段开始 | string / — | {"format":"date-time","timezoneRequired":true} | C/C/C | C,U,D | 严格解析ISO-8601带时区时间戳，拒绝无时区或不存在的本地时刻。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH08,CH10,CH16 | S |
| `storage.dispatch.interval_minutes` 时长 | number / minute | {"exclusiveMinimum":0} | C/C/C | C,U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH08,CH10,CH16 | S |
| `storage.dispatch.charge_from_pv` 光伏充电 | number / kWh | {"minimum":0} | C/C/C | C,U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH08,CH10,CH16 | S |
| `storage.dispatch.charge_from_grid` 网充 | number / kWh | {"minimum":0} | C/C/C | C,U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH08,CH10,CH16 | S |
| `storage.dispatch.discharge_to_load` 向负荷放电 | number / kWh | {"minimum":0} | C/C/C | C,U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH08,CH10,CH16 | S |
| `storage.dispatch.discharge_to_export` 放电上网 | number / kWh | {"minimum":0} | C/C/C | C,U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH08,CH10,CH16 | S |
| `storage.dispatch.stored_energy_begin` 期初电池能量 | number / kWh | {"minimum":0} | C/C/C | C,U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH08,CH10,CH16 | S |
| `storage.dispatch.stored_energy_end` 期末电池能量 | number / kWh | {"minimum":0} | C/C/C | C,U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH08,CH10,CH16 | S |
| `storage.dispatch.usable_capacity` 当期可用容量 | number / kWh | {"exclusiveMinimum":0} | C/C/C | C,U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH08,CH10,CH16 | S |
| `storage.dispatch.auxiliary_energy` 辅机用电 | number / kWh | {"minimum":0} | C/C/C | C,U,D | 拒绝NaN/Infinity及数字字符串；以unit明确维度，比例用0..1而非百分数文本；超范围需拒绝或显式人工复核。；类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH08,CH10,CH16 | S |
| `storage.dispatch.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。；只可在列出的pv_types专项schema内使用；不具备该类实现时返回NOT_IMPLEMENTED。 | 不可；证据不足保留UNKNOWN | CH08,CH10,CH16 | S |

### 6.scenarios 字段

| field_id / 名称 | 类型·单位 | 约束 | L1/L2/L3 | 来源 | 验证 | 可替代 | 章节 | 分类 |
|---|---|---|---|---|---|---|---|---|
| `scenarios.options` 方案及情景输入 | array / — | 稳定row_id；minItems=0，maxItems=1000000；item字段=scenarios.options.scenario_id,scenarios.options.kind,scenarios.options.changed_field_id,scenarios.options.changed_value_text,scenarios.options.basis,scenarios.options.source_snapshot_id,scenarios.options.row_id | O/R/R | U,D,C | 基准和至少一个可行替代方案；单因素只改一个有效输入，目标门槛不能修改现实参数。；所有item必须有稳定row_id；逐item和逐原子字段独立provenance；空数组表示无资料而非零值；按子字段约束校验。 | 不可；证据不足保留UNKNOWN | CH06,CH17 | ALL |
| `scenarios.options.scenario_id` 方案ID | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D,C,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH17 | ALL |
| `scenarios.options.kind` 情景类 | string / — | {"enum":["baseline","alternative","pessimistic","optimistic","single_factor"]} | O/R/R | U,D,C,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH17 | ALL |
| `scenarios.options.changed_field_id` 变更字段ID | string / — | {"note":"必须引用本目录字段，禁止变更目标以外的真实性标签。"} | O/R/R | U,D,C,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH17 | ALL |
| `scenarios.options.changed_value_text` 按字段类型解析的值 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D,C,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH17 | ALL |
| `scenarios.options.basis` 变更依据 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D,C,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH17 | ALL |
| `scenarios.options.source_snapshot_id` 独立来源快照 | string / — | {"minLength":1,"maxLength":2000} | O/R/R | U,D,C,AI | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH17 | ALL |
| `scenarios.options.row_id` 稳定行标识 | string / — | {"pattern":"^[A-Za-z0-9][A-Za-z0-9._-]{0,95}$"} | C/C/C | U,D,C | 类型及范围校验；与所引来源位置、适用地理及有效期复核；冲突保留多候选且不静默覆盖。 | 不可；证据不足保留UNKNOWN | CH06,CH17 | ALL |

## 7. Phase 2接口与未来验收设计

- 运行时输入契约计划分 `field_catalog_version`、`project_values`（值信封）、`source_records`、`attachments`、`category_extension`、`validation_issues`。共享层不接管分类方法学；实例和候选不覆盖源附件。输入/单位/来源快照进入input_hash，详见10；原始商业资料不得写入公开case。
- 通用schema与九个分类schema计划路径见07。未知分类/尚未实现分类显式NOT_IMPLEMENTED，不回退P0。模式判定、单位换算、冲突、来源失效、等级/建议均需确定性规则与人工复核入口。
- 未来测试标识按 `T-IN-FIELD-<field_id>` 派生，每个字段至少有有效、类型错误、范围边界、UNKNOWN、缺来源、CONFLICT、单位变换等适用用例；每个数组再测item结构、row_id重复、单元provenance与跨行约束。不是只断言字符串存在。
- 未来专项包含：0/负面积，kW/MW与kVA错用，百分数错用，摄氏/开尔文，闰年/DST、重复负荷、无曲线高自用、无并网意见、政策过期、外部接口失败、跨年造价、报价失效、0债务服务、税折旧超原值、负收入、IRR无根/多根、期内未回收、极端限发及分类串用。属性/变形测试验证输入改变后的数值和四文件同步变化；所有当前NOT_IMPLEMENTED。
- 本次只有文档/目录结构与字段引用一致性的静态检查；不能将其算作上述单元/集成/属性/端到端测试通过。
