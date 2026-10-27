# 四个经营分析 Skill 功能、输入输出与独立价值矩阵

日期：2026-10-27。源码位置均为仓库相对路径；`IMPLEMENTED` 仅表示代码和既有本地证据支持该项，不表示平台运行或业务法律结论。

## 功能画像

### 应收账款逾期分析

| 项目 | 结论 | 证据 |
|---|---|---|
| 到期/逾期判断 | `IMPLEMENTED` | `scripts/analyze_receivables.py:127-132`：`due_date < as_of` 且余额大于零 |
| 逾期天数 | `IMPLEMENTED`（聚合使用） | `:127` 计算 `overdue_days`，输出客户 `max_days_overdue`；不输出逐发票天数 |
| 账龄分桶 | `IMPLEMENTED` | `:71-78`、`:148-149`：1-30、31-60、61-90、91+ |
| 应收金额 | `IMPLEMENTED` | `:126-147`：按币种输出 `totals.open/overdue` |
| 客户风险/排序 | `IMPLEMENTED`（候选） | `:150-156`：同币种按逾期余额排序，>90 天 HIGH，否则 MEDIUM |
| 回款优先级建议 | `PARTIAL` | `:153-154` 只有粗粒度 HIGH/MEDIUM 和人工复核建议，不含逐发票优先级、付款条件或信用风险 |
| 业务异常 | `PARTIAL` | `:100-124` 主要是输入质量问题，不含逾期趋势、集中度或回款异常 |

必填字段：`invoice_id`、`customer_id`、`due_date`、`open_balance`、`currency`（`SKILL.md:23-25`）。可选列忽略；基准日显式传入。输出：`as_of`、`totals`、`aging`、`customers`、`issues`、`limitations`。金额分币种且不换汇。实际测试：`tests/test_receivable_analyzer.py:26-105`，包含金额、账龄、客户排序、非法输入和样例 expected JSON。

### 库存呆滞分析

| 项目 | 结论 | 证据 |
|---|---|---|
| 库存数量/快照 | `IMPLEMENTED` | `scripts/analyze_inventory.py:307-317`：按 item/warehouse/currency 取 as-of 前最近快照 |
| 入库和出库 | `IMPLEMENTED` | `:314-315`、`:336-338`：receipt/issue quantity 和 movement_count |
| 最后出库时间 | `NOT_IMPLEMENTED` | 代码统计发料数量和记录数，但未输出每项最后 issue_date |
| 呆滞天数 | `NOT_IMPLEMENTED` | 没有以最后出库日计算 days-since-last-issue；用周转率和覆盖天数候选替代 |
| 呆滞金额 | `PARTIAL` | `:316-317` 计算库存 value，但慢动候选没有明确的呆滞金额字段 |
| 无移动/慢动/超储 | `PARTIAL` | `:346-356` 有候选；无发料时 `turnover_status=UNKNOWN` 仍可能生成周转率 `0` 的慢动候选 |
| 余额一致性 | `IMPLEMENTED` | `:358-361` 输出 `BALANCE_MISMATCH` |
| reorder_point | `NOT_IMPLEMENTED` | `:232-255` 解析但不写入输出、不触发补货判断，当前 SKILL 文案超出实现 |

必填数据集：balances、receipts、issues；master 可选（`SKILL.md:31-37`）。输出：`inventory`、`inventory_value`、`no_movement_candidates`、`slow_moving_candidates`、`overstock_candidates`、`anomaly_candidates`、`invalid_rows`。实际测试：`tests/test_inventory_analyzer.py:76-192`，覆盖快照价值、周转、候选、输入安全和 expected JSON，但未覆盖上述矛盾。

### 采购价格分析

| 项目 | 结论 | 证据 |
|---|---|---|
| 价格变化 | `IMPLEMENTED` | `scripts/analyze_purchase.py:256-279` 对五项可比组计算相邻价格变化 |
| 供应商价格比较 | `PARTIAL` | `:280-295` 取组内最高/最低报价，但没有要求来自不同供应商；样例 Bolt 的 O6/O7 均 Supplier-A |
| 同物料价格差异 | `IMPLEMENTED`（受可比键限制） | `:189-197` 物料+规格+单位+币种+税务处理完全相等才进入组 |
| 异常采购价格 | `IMPLEMENTED`（候选） | `:272-294` 20% 阈值输出 `PRICE_CHANGE`/`SUPPLIER_QUOTE_SPREAD`，不是舞弊结论 |
| 价格波动/趋势 | `IMPLEMENTED` | `:313-332` 首尾等长半区间趋势；不检查期间完整性 |
| 潜在成本节约 | `PARTIAL` | 可输出 spread 候选，但没有采购量加权、供应商不同约束或实际节约金额/可执行建议 |
| 不可比保护 | `IMPLEMENTED` | `:297-311` 输出 `NOT_COMPARABLE`，不跨规格、单位、币种、税务处理比较 |

必填字段：`order_id, material, supplier, order_date, quantity, unit_price, unit, specification, currency, tax_treatment`（`SKILL.md:26-38`）。输出：`purchasing_totals`、`supplier_concentration`、`comparable_price_changes`、`supplier_quote_spread`、`same_period_trend`、`anomaly_candidates`、`incompatible_group_differences`。测试：`tests/test_purchase_analyzer.py:49-189`。

### 销售数据分析

| 项目 | 结论 | 证据 |
|---|---|---|
| 销售收入 | `IMPLEMENTED` | `scripts/analyze_sales.py:269-275`、`:304-323` |
| 销售趋势 | `IMPLEMENTED` | `:260-267` 按币种和自然月聚合 |
| 客户贡献 | `IMPLEMENTED` | `:314` 调用 `_aggregate(..., "customer")` |
| 产品贡献/排名 | `IMPLEMENTED` | `:268`、`:313` |
| 销售结构 | `PARTIAL` | 客户/产品份额和集中度存在，但不是跨期结构迁移分析 |
| 收入异常 | `PARTIAL` | `:277-285` 只识别金额达到选定平均值 3 倍的大订单 |
| 客户/产品结构异常 | `NOT_IMPLEMENTED` | 没有客户流失、新增客户、产品组合迁移或跨期结构变化 |
| MoM/YoY | `IMPLEMENTED`（严格条件） | `:113-139`：as-of 与完整期间声明齐全才计算，否则 UNKNOWN |
| 利润/毛利率 | `NOT_IMPLEMENTED`且明确标 UNKNOWN | `:320` 未提供成本即不推断 |

必填字段：`order_id, customer, product, order_date, amount, currency`（`SKILL.md:20-27`）。输出：`sales_totals`、`sales_trend`、`product_ranking`、`customer_contribution`、`customer_concentration`、`period_comparisons`、`anomalies`、`operational_risks`。测试：`tests/test_sales_analyzer.py:52-190`。

## 六组输入、算法、输出矩阵

| 对比 | 输入差异 | 核心算法差异 | 输出/决策差异 | 替代判断 |
|---|---|---|---|---|
| 应收 vs 库存 | 单发票 CSV vs 三个数据集+主数据 | 日期逾期/账龄 vs 快照+移动+余额平衡 | 客户逾期优先级 vs 库存价值/慢动/超储 | 不能完整替代 |
| 应收 vs 采购 | 发票到期日/余额 vs 采购订单/规格/税务 | overdue buckets vs 五项可比组、价格变化 | aging/customer vs comparable changes/supplier | 不能完整替代 |
| 应收 vs 销售 | due/open_balance/customer_id vs order/customer/product/amount | 逾期余额 vs 收入趋势和贡献 | aging/collections review vs revenue/ranking/concentration | 不能完整替代 |
| 库存 vs 采购 | item/warehouse/snapshot/movement vs material/supplier/quote | 库存状态、周转、平衡 vs 可比报价/供应商集中度 | slow/overstock vs price candidates | 不能完整替代 |
| 库存 vs 销售 | 快照、收货、发料 vs 销售订单 | 期初+移动=期末 vs 收入月度聚合/客户产品贡献 | inventory candidates vs sales trend/ranking | 不能完整替代 |
| 采购 vs 销售 | supplier/material/specification/unit/tax vs customer/product/amount | 采购首尾半区间 vs 销售自然月及完整期间 MoM/YoY | supplier/quote spread vs customer/product contribution | 不能完整替代 |

通用交集如 `currency`、`order_id`、`quantity`、`summary`、`invalid_rows` 属于数据处理基础，不足以证明核心服务相同。

## 产品必要性

| 产品 | 独立用户 | 独立问题 | 独立输入 | 独立算法/输出 | 独立维护/收费必要性 | 当前结论 |
|---|---|---|---|---|---|---|
| 应收 | 财务/应收人员 | 回款与逾期核查 | 发票余额/到期日 | 账龄/客户逾期 | 有 | 保留独立，先修正细粒度能力边界 |
| 库存 | 仓储/运营 | 库存积压与流转 | 快照/收货/发料 | 周转/平衡/候选 | 有 | 保留独立，但必须修复 UNKNOWN/0 矛盾 |
| 采购 | 采购/供应链 | 可比采购价格 | 订单/规格/单位/税务 | 可比组/价格变化 | 有 | 保留独立，但收窄供应商价差表述或修复算法 |
| 销售 | 销售/经营分析 | 收入结构与趋势 | 销售订单 | 月度/客户/产品 | 有 | 保留独立；结构异常标为未实现 |

## 方案比较

| 维度 | 方案 A：四个独立 Skill | 方案 B：合并企业经营数据分析 Skill |
|---|---|---|
| 公约风险 | 每个资产都须证明独立价值、图标、简介和真实能力；当前需人工复核 | 减少重复铺量表面风险，但合并后仍须准确描述四个模块 |
| 用户选择成本 | 低：岗位和数据入口清晰 | 高：一个资产需要用户理解多个输入协议 |
| 功能清晰度 | 高，领域边界明确 | 可能被通用“经营分析”掩盖 |
| 维护成本 | 四套输入和领域规则分别维护 | 共用入口/版本管理成本更高，模块仍需分别维护 |
| 审核成本 | 四次审核与平台资料核验 | 一次资产审核，但复杂输入和能力声明集中 |
| 用户价值 | 可按岗位按需使用，数据最小化 | 需要同时接受不相关模块时浪费搜索/安装成本 |
| 商业化 | 可按岗位/模块定价，但协议尚未核实 | 统一定价简单，功能边界和支持范围更难说明 |

**建议 A，但前提是先完成实际整改和平台确认。**当前没有证据显示四个产品核心价值实质相同到必须合并；也没有依据在未经修复和平台验证前声明分别合规。若平台或业务负责人要求最大化单一资产，才另行制定合并方案，不自动删除旧产品。
