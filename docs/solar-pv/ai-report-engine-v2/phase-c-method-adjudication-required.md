# Phase C 盈利评价方法裁定单（2.0 原需求未闭合）

状态：REQUIRES_METHOD_OWNER_APPROVAL；不启动2.1，不改变冻结89公式和469字段。当前只读评价契约为 `reporting/financial_evaluation.py:evaluate_financial`，三项继续 NOT_CALCULABLE。

| 项目 | 当前已有结果 | 缺少的输入/方法 | 可行口径差异 | 影响范围 | 确认责任 | 批准前允许/禁止 |
|---|---|---|---|---|---|---|
| 会计盈利年度 | 3D年度收入、税务折旧、项目/股东税基、所得税计提和支付 | 独立会计收入确认、会计费用与折旧政策、会计税费、主体及逐年净利润生产者 | 会计确认不等于收付款；税务折旧、亏损结转与应税所得不等于会计利润；屋顶避免支出与销售收入不能混同 | `financial_ledger.py` 中 taxable_income_project、depreciation、income_tax_accrual；F-TAXABLE-INCOME-PROJECT 为税基公式，不授权替代净利润公式 | 财务方法负责人/会计专业人员与用户 | 可解释税基及项目指标，禁止断言某年会计盈利 |
| 经营现金转正 | revenue_cash_receipts、self_use_avoided_expenditure、opex_cash_paid、cash_tax_total_project、working_capital_increase/release | 独立经营现金分类、屋顶节费经济边界、经营营运资金、资本开支剔除规则与年度/累计生产者 | 银行现金口径与包含避免购电支出的增量经济口径不同；单年为正、累计转正、投资回本各不相同 | F-CASH-RECEIPTS、F-CASH-TAX-TOTAL、F-PROJECT-CASH-FLOW 及相关台账字段；不能直接从最后者截取定义经营现金 | 财务方法负责人、项目业主 | 可解释已经计算的项目现金，禁止将其重命名为经营现金或自行求和形成新口径 |
| 股东资金回收 | 债务比例、已有债务偿付台账；股东投资者现金流指标保持原 BLOCKED_MISSING_INPUT | 出资、分配、退出事件的主体/日期、资金留存规则及股东累计回收方法 | 项目无杠杆现金流与股东可分配/实际分配现金不同；零债务并不证明项目净流入已支付股东 | financial.phase3e.equity-investor-cash-flow、irr-equity 与 owner_cash_events；项目回收公式不得替用 | 融资/财务方法负责人、股东或授权业主 | 可说明原始阻断，禁止给出股东回本年或用项目IRR代替股东IRR |

## 需求与变更边界

这些都是冻结2.0的未闭合要求，不转移至 AFTER_V2。裁定既有结果的读取与不可计算状态不改变需求；新增会计确认、现金分类或股东回收计算则涉及冻结方法边界，须走现有例外审批后才实施。当前未新增任何财务公式、字段或会计政策。

## 本轮真实案例边界

- 两个基准 canonical 的项目 NPV/IRR及静动态回收仍保留原生产者结果；整体PARTIAL不能抹除这些可用指标。
- 运维候选交易费来源已独立接入，终期现金尚未完成候选来源重放，候选经济排名仍为空。
- 用户回收年限/口径、收益率及预算目标未提供，不能从结果反推目标或声称达标。
- 依据现有合法指标开展 CH08、CH10、CH16 AI内容预览，不以以上方法缺口阻断全部内容工作。
