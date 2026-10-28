# 12 统一计算结果与跨文件一致性契约（Phase1设计）

本文件冻结接口要求，不是已实现的JSON Schema或引擎。Phase2才实施机器Schema。所有四文件基于同一不可变结果；任何renderer不得另行计算指标、补造未知数或调用AI编造数字。

## 根结构与标识

必有 `schema_version, model_version, run_id, input_hash, source_snapshot_id, result_hash, project_id, pv_type, scenario_id, created_at, evaluation_date, currency, maturity, status, boundaries, inputs, source_snapshot, formula_snapshot, results, findings, evidence, artifact_manifest`。

- `input_hash`：标准化后的业务输入与provenance快照的规范字节摘要；记录哈希算法/版本。用户目标与客观参数分域，目标改变不得改变客观发电/成本结果。
- `source_snapshot_id`：所选数据源版本、访问时间、有效区间、许可、处理链/输入位置的不可变快照；不能只给当前URL而不记录内容版本。机密材料只存受控局部ID/必要单元格，完整原文件不进入公开结果。
- `result_hash`：不包含自身、run_id、生成时刻及导出artifact_manifest的结果核心规范表示摘要，避免自引用和将运行身份混作数值可复现性；包含输入hash、来源快照、公式/模型版本、类型、情景、边界和实际结果。与10四文件契约的result_payload一致。Phase2固定排序/字符串编码/时间/有限小数表示，金额不依赖平台浮点格式；拒绝NaN/Inf。
- `run_id` 标识一次真实执行；不能把旧四文件仅改run_id再宣称重算。四份实际输出、附表和Excel中相关场景均写五标识。artifact_manifest单独登记四文件名/媒体类型/字节/hash/校验/视觉记录，避免导出文件hash与result_hash互相引用。

## 领域结果

1. 站址/几何/法规分类分别留字段，不用工程分类替代监管分类；所有面积/容量需参考边界。
2. 资源：数据集、版本、时期、时间分辨率、时区/坐标系、GHI/DNI/DHI/POA/GTI/温度/风、转换方法、12个月/逐年统计和不确定性；原始资源≠真实项目发电。
3. 容量布局：DC/AC、可用面积、组件数量与设备规格、方位/倾角/间距、变压器及接入限制；基准与至少一项可行替代方案。
4. 能量：month/year/interval索引；气象区间与评价年、闰年小时、缺测/重复时段；理论/DC/逆变AC/计量交付/自用/上网/限发各边界；分项损失的应用顺序、已在上游扣除项和防重计标识；首年初始衰减与以后年度衰减分离。
5. 消纳：仅可靠同粒度时序可计算真实自用；无时序只存显式假设情景。功率上限以时段长度转电量；储能独立SOC流量图与充放电约束，不能沿用无储能min公式冒充。
6. 成本/税费/融资：CAPEX含税状态/分期/利息、OPEX现金与非现金、折旧/更新/残值、营运资金、融资本金/利息/费用/宽限与偿还、税前税后/名义实际口径。
7. 财务：项目投资与资本金两条现金流、各自折现率、NPV/IRR/静态动态回收期；交付电量边界LCOE、CFADS/DSCR、盈亏平衡价、最差年与投资/债务本息校验；负值/无根/多根/未回收/无债不适用都有结构原因。
8. 风险/建议：已证实、待核实、假设分别列示；土地/安全/并网阻断先于财务；四态建议与所用证据和未关闭条件相连。

## 指标记录

每个指标至少 `metric_id, value, unit, status, reason, boundary_id, period, scenario_id, input_field_ids, source_ids, formula_id, formula_version, evidence_ids, report_locations, workbook_locations, rounding_rule`。缺数用null+UNKNOWN及原因，不使用0、空串或虚构范围掩盖。展示四舍五入只在renderer，交叉核对使用原始确定性值加已声明的显示精度容差；禁止调整报告值使其符合目标。

图表dataset引用同metric_id/period/scenario和原始数据，不额外计算新结果。工作簿行/单元格映射与DOCX章节/表/公式/图ID由稳定索引生成；PDF页码只有实际渲染后才登记，不提前由AI估计。来源清单与报告引文均引用同source_id及具体位置。

## 变更、重算与发布

输入、来源、公式/方法或模型改变即需新run及相关hash，连带全部指标/表图/文件重建；方案比较保留各方案ID及相同可比边界，不混不同模型年或税口径结果。只修改目标门槛也需记录新评价，不能偷偷改基准假设。

先在授权输出根的事务目录渲染、重开检查、数值/结构/视觉门禁；成功后一次发布manifest明确关联的四文件。任一失败整个交付BLOCKED，保留已完成产物的真实状态供诊断，不伪造四件齐备；不得覆盖已有用户成果。发布目录/文件名防非法字符、穿越、符号链接和Office注入。
