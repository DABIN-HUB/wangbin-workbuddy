# 四个经营分析 Skill 交叉测试

> 历史测试快照：本文件记录整改前缺口；Phase 9 的专项与全仓回归结果见 `reports/financial-skills-phase9-release-candidate.md`。

日期：2026-10-27
数据：仓库内四组 fictional UTF-8 CSV；未使用真实客户、供应商或财务数据。
执行目录：仓库外 scratch `financial-cross-tests-20261027`；结果原始 JSON 未写入仓库。

## 方法

每组调用均使用实际脚本入口，而不是直接调用假对象：

- 应收：`packages/skills/wangbin-receivable-analyzer/scripts/analyze_receivables.py --input ... --as-of 2026-10-27`
- 库存：`packages/skills/wangbin-inventory-analyzer/scripts/analyze_inventory.py --balances ... --receipts ... --issues ... --master ... --as-of 2026-02-28`
- 采购：`packages/skills/wangbin-purchase-analyzer/scripts/analyze_purchase.py --input ... --start-date 2026-01-01 --end-date 2026-02-28`
- 销售：`packages/skills/wangbin-sales-analyzer/scripts/analyze_sales.py --input ... --start-date 2026-01-01 --end-date 2026-02-28 --as-of-date 2026-03-01 --complete-period 2026-01-01:2026-01-31 --complete-period 2026-02-01:2026-02-28`

## 八组结果

| # | 输入 | 调用 Skill | 退出码 | 结果 | 证据 |
|---:|---|---|---:|---|---|
| 1 | fictional-receivables.csv | 应收 | 0 | `PASS` | 输出 `totals`、`aging`、`customers`；与 `fictional-receivables.expected.json` 相等 |
| 2 | fictional-receivables.csv | 销售 | 2 | `REJECTED` | `ERROR MISSING_COLUMNS`；无销售订单字段，不伪造销售分析 |
| 3 | balances+receipts+issues+master | 库存 | 0 | `PASS` | 输出 `inventory_value`、`inventory`、慢动/无移动候选；与 expected JSON 相等 |
| 4 | fictional-balances.csv | 采购 | 2 | `REJECTED` | `MISSING_COLUMNS`；快照不是采购订单，不伪造价格分析 |
| 5 | fictional-purchases.csv | 采购 | 0 | `PASS` | 输出 `purchasing_totals`、`comparable_price_changes`、`anomaly_candidates`；与 expected JSON 相等 |
| 6 | fictional-purchases.csv | 销售 | 2 | `REJECTED` | `ERROR MISSING_COLUMNS`；无客户、产品、金额字段，不伪造收入分析 |
| 7 | fictional-sales.csv | 销售 | 0 | `PASS` | 输出 `sales_totals`、`sales_trend`、`product_ranking`、`customer_contribution`；与 expected JSON 相等 |
| 8 | fictional-sales.csv | 应收 | 2 | `REJECTED` | `error: MISSING_OR_DUPLICATE_HEADER`；无发票到期/余额字段，不伪造逾期分析 |

执行断言：8 组、正确领域成功 4 组、错误领域拒绝 4 组；终端输出为 `cross cases 8 correct-domain passes 4 wrong-domain rejects 4`。

## 交叉边界结论

1. 四个 Skill 不会把不具备必要字段的核心输入伪造成同类成功报告；错误领域输入均返回明确非零码。
2. 该结果证明输入边界具有一定独立性，不证明平台的 Skill 路由、附件权限或 Python 运行时可用。
3. 错误领域拒绝不是要求拒绝所有共享字段：例如 `currency`、日期和数量可以合法存在于不同领域，是否能完成核心任务仍由领域字段和算法决定。
4. 真实综合经营场景需要多个专业数据集：应收需要发票余额/到期日，库存需要快照与收发料，采购需要规格/单位/税务可比信息，销售需要客户/产品/金额订单。单一 Skill 不能从另一领域文件推断这些缺失事实。

## 与既有专项测试的关系

- 应收专项：`30` 个四产品专项测试中的应收覆盖金额、账龄、客户排序、非法日期/重复发票、公式输入和样例 expected JSON。
- 库存专项覆盖快照价值、周转、候选、边界和样例 JSON，但暴露了无发料时 `UNKNOWN` 明细与 `0` 慢动候选的逻辑矛盾。
- 采购专项覆盖五项可比键、价格变化、不可比组、Decimal 和样例 JSON，但未强制最高/最低报价来自不同供应商。
- 销售专项覆盖收入趋势、产品/客户贡献、集中度、完整期间条件、数据质量和样例 JSON，但未覆盖客户/产品跨期结构异常。

这些缺口不会因交叉测试通过而消失，已纳入发布建议。
