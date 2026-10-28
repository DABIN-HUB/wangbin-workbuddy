# Phase 2 输入资料架构与接口

> 当前为Phase2开发文档，最终通过/失败以reports/solar-pv/phase2-review-and-acceptance.md及实际JUnit为准。尚未联合验收的模块不能据本说明认定完成。全部长期需求仍以原始总提示词/469字段目录/89公式/需求矩阵为准；不进入Phase3。

## 1. 单一目录与版本

`services/solar-pv-engine/src/wangbin_solar_pv/`是同仓库独立输入包，没有新工厂/数据库/微服务。Catalog只读12份冻结文件并核验LF规范化SHA-256；metadata将字段技术标识、中文名、类型/单位/范围、条件等级、分类/章节、取得/替代/来源、验证状态和公式交叉引用关联同一field_id。不重命名469字段，不从英文显示名反推新ID。

`ProjectData`使用solar-pv-project/1.0.0；输入基线版本从08实际读取为1.0.0（SOLAR-PV-1.0.0为文档标签）。schema_version未知、baseline_hashes不符、重复JSON键、非有限数和额外属性拒绝。新增applicability为兼容可选元数据，缺失默认空集合只表示没有已登记豁免，不是任一业务事实默认值。未来破坏性版本需显式迁移，不猜测语义。

## 2. JSON结构与信封

- values仅放274个非repeat_group字段的实际提供值，不自动补齐469项；字段定义仍全部存在。
- 对象数组value为`[{row_id,fields:{完整field_id:信封}}]`；父容器、row_id原子值和每单元独立证据；field_instance_id在已选输入中唯一。
- schedule.tasks.predecessor_ids为元素信封列表，每元素value仍是字符串，不给字符串伪加row_id；[]为已确认无前置，null为未知，引用和循环专项校验。
- `original_value/original_unit`保留原输入，`value/unit`为规范值；normalization保存转换ID、精确标志和显式舍入策略，并回放防止只改标签。金额economic_basis区分币种、价格年、税含和名实口径，单位换算不做汇率/含税/价格基准推断。
- 五种证据status不变；六类source_kind映射U/D/C，ASSUMPTION表示用户显式接受的情景，不把AI分析当客观值。UNKNOWN=null、缺口留原因；VERIFIED要求来源/位置/复核/授权，绝不因提取或用户陈述自动赋值。
- C类必须有formula_id/formula_version/run_id及上游实例；投资金额严格同明细数量/单价链，原报价和计算候选分别保存；本阶段只校验声明血缘，不执行投资/发电/财务公式。

## 3. 来源与冲突

候选按内容摘要获得稳定candidate_id，selected values与candidates分开；不同数据保留两候选，状态CONFLICT且有效value=null，不能静默平均或覆盖。人工选择需要reviewer和reason，但不自动将被选数据改为VERIFIED。历史记录只保存必要标识/理由，客户原文不进入诊断日志。source_snapshot可包含完整受控项目证据，不可自动写入公共仓库。

所有来源真实性评估基于明确的声明和本地格式/一致性核验，不等于已经向电网/产权机关/数据提供者独立认证。外部API/站址数据适配仍属Phase4，平台和正式文件证据另有门禁。

## 4. 条件、适用性与九类主权

conditions提供13个IN-C规则和所有97条件字段的显式predicate；T/F/U三态，U不按F豁免；父数组未适用不制造item，但已有item和row_id按实际等级逐项核验。融资比例0不能覆盖债务计划，纯售电无需企业负荷；价格表与市场时序二选一，但结算模式未知不同时免除两类。

applicability独立于证据status，使用字段ID/可选row_id、受控rule_id、理由、reviewer、evidence_source_ids、reviewed_at；仅允许税惠不适用、无替代政策、经复核无更换计划、特定屋顶无需地面勘察等命名边界，不能豁免结构安全、产权、真实资源或并网许可。声明的证据必须能在已选VERIFIED且授权记录中关联；无依据NA无效。

九类使用各自scenarios/<pv_type>/contract.json，并共享冻结字段定义。storage只组合八种非储能基座，不递归，不自动设屋顶。输入契约可实现不等于该分类计算/E2E支持；九类计算仍NOT_IMPLEMENTED。

## 5. 完整度并非字段填写比例

评价identity/site_rights/engineering/resource/grid/consumption_tariff/cost_operation/finance_tax/traceability九个输入证据轴；L1/L2/L3逐等级检查冻结必需项、触发条件、父子上下文、证据和假设上限，不能由填写率或附件数量升档。未达L1输出L1_DRAFT，接受草稿并给缺口，不生成临时事实项目名或站址。

`current_level`的scope严格为INPUT_EVIDENCE_ONLY，assessment_basis明确为声明证据加本地结构/一致性检查；`report_maturity=NOT_EVALUATED`。实际18章/四文件、投资建议、真实数据、平台安装/审核不从这个等级推导。inputs_ready_for_calculation / can_enter_next_calculation_stage仅表示可向未来引擎移交资料，can_execute_calculation始终false，CALCULATION_ENGINE_NOT_IMPLEMENTED明确阻断执行。

缺正式并网证据绝不回显confirmed；无负荷曲线真实自用率UNKNOWN，有曲线仍NOT_COMPUTED。目标回收期/IRR只保存约束，不产生或修改客观结果。未核实资源、来源冲突、严格L1上限假设、质量问题均阻止高等级；尚未实现的代表性负荷映射、复杂几何专项复核保留待核，不用假数据填补。

## 6. 安全与资源边界

沿用原document-engine已知限制：不是OS沙箱，Windows资源/后代进程隔离问题未解决。新解析层须在同一稳定快照检查格式/活动内容，再受限读取，拒绝宏/公式/外链，不执行用户内容。无OCR或复杂表格定位不足要PARTIAL/NEEDS_OCR，不把解析失败说成无资料。

JSON默认32MiB/64层、有界数字表示；纯units函数无应用层有效数字截断，二者资源边界不同。容器行/附件大小均需显式限制，超限返回原因而非静默截断。超过512顶点或多环/洞的复杂几何保留数据但要求专项拓扑复核，不声称通用GIS有效性。IANA数据库Windows新包显式依赖tzdata，不改变旧产品依赖。

本地测试资料明确SYNTHETIC；旧产品测试在scratch副本执行，历史包/旧源码与测试保持保护哈希。安装、外部访问/许可、真实数据、四文件渲染和平台等门禁分别报告，不以单测数替代。

## 7. 本地多轮资料事务

IntakeSession.new/from_dict接收分类与版本化项目；submit、revise、resolve、review、remove、accept_candidates分别处理补充、显式修订、冲突选择、人工证据复核、带理由移除及已解析候选的显式选择。每个请求有不可修复的原样submission_id与内容摘要；同ID同内容幂等，不同内容拒绝；expected_revision阻止旧版本覆盖。草稿副本先通过结构、来源、关联及分类校验，再一次性替换会话；失败不留下半次提交。

用户入口仅能写用户提供、明确假设或未知的输入，不接受CALCULATED来源或直接VERIFIED声明。提取候选也不等于已核实；人工review是另一个带复核人、理由和授权声明的操作，不可把ASSUMPTION/UNKNOWN/CONFLICT升级成事实。修改位置/分类使已核实的相关资源/并网/屋顶等证据回到待核，保留原值、旧候选与失效历史。修改目标回收期不改变其他输入，也不生成投资或发电量。

普通冲突之外还比较金额的价格年/税含、测量期、适用期和地理口径；相同金额不表示同口径。UNKNOWN资料被实际补齐不是冲突，新UNKNOWN不自动擦除已有事实。显式修订或移除都保留历史候选。金额单位缩放可单独记录normalization.currency，不为“100万元转元”虚构价格年或税基，也不自动换汇。

## 8. 六格式受限提取的真实边界

DOCX只处理正文段落和可重建的简单表格，定位paragraph/table/row/cell，不声称页码；PDF页码来自实际extract_pages，页内仅文本片段定位，版面需复核；XLSX真实工作表/单元格，CSV含多行字段的实际物理行跨度/列，TXT/MD实际行号。XML数值直接取已审查的worksheet数字token构造Decimal，避免openpyxl中间float静默舍位。

仅确定性完整字段ID、唯一中文目录名和少量明确标签别名；重复组表头必须完整字段ID，不猜一般自然语言、枚举或MW对应MWp。数值需明确单位；金额规范转换还需先显式声明文档币种，缺失或冲突返回待确认。未提供技术row_id时才按附件摘要/实际源行派生；已给出的ID原样保留，非法/重复ID返回PARTIAL待核，不替用户修复。

parse_attachment输出PARSED/PARTIAL/NEEDS_OCR/FAILED/BLOCKED及未经核实的候选；PARSED仅表示受支持内容已提取，不代表项目字段合法或证据真实。accept_candidates还要通过完整输入校验；复杂表格、图片、扫描/无文本及无法判定的单位不补0、不猜页。来源登记包含真实采集时间、实际定位、附件摘要；用户选入后完整SHA-256与basename登记到受控history，并进入source_snapshot.attachments，无需持久化原文或绝对路径。

安全检查和读取使用同一私有稳定快照。公共SecurityPolicy做已支持格式/容器检查；新包额外拒绝链接/硬链接/路径逃逸、宏/XLM/OLE/DDE、重复ZIP成员/XML实体、活动PDF对象（含压缩对象与转义名字）、公式及外链。纯带符号数值不是公式，表达式和实际公式节点仍拒绝。独立spawn worker及父墙钟超时限制解析，子输出/日志被抑制，只传受限JSON；不声称Windows硬内存/后代进程问题已解决。默认最多20,000解析单元格、8MiB提取文本/输出，JSON仍32MiB；超限明确阻断，不静默截断，大曲线需后续受控流式/分块方案，不能拿本地小样证明全年15分钟文件的吞吐能力。

## 9. Phase 3 移交而非计算结果

IntakeSession.export输出solar-pv-input-export/1.0.0，含完整project、normalized_inputs、逐原子provenance_records、source_snapshot/source_snapshot_id、input_hash、scenario_config与input_maturity。input_hash用sha256/solar-pv-input-v1覆盖规范输入/基线/来源快照/适用性，不依赖导出当时的墙钟。反序列化后可重现；这不是12-canonical-result-contract的计算结果JSON，没有run_id/result_hash或财务指标。calculation_status=NOT_IMPLEMENTED、result_contract_status=NOT_CREATED，不能据此生成四文件正式成果。
