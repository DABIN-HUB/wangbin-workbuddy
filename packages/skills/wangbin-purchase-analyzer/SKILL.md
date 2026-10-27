---
name: wangbin-purchase-analyzer
display_name: 采购价格分析
display_name_en: Purchase Price Analyzer
description: Analyze UTF-8 purchase CSV prices with currency-safe comparisons, explainable candidates, and deterministic JSON.
description_zh: 读取 UTF-8 CSV，按可比条件计算采购价格变动、供应商报价价差、币种总额、集中度和同周期趋势，并输出可解释的异常候选。
description_en: Analyze UTF-8 CSV purchase data with comparable price changes, supplier quote spreads, currency totals, concentration, same-period trends, and explainable candidates.
examples_zh:
  - 请分析这个 UTF-8 采购 CSV 在 2026-01-01 至 2026-02-28 的价格变化。
examples_en:
  - Analyze this UTF-8 purchase CSV from 2026-01-01 through 2026-02-28.
version: 0.1.1
author: Wangbin Research
license_candidate: MIT
license_status: REQUIRES_MANUAL_REVIEW
---

# 采购价格分析

这是一个本地、确定性的采购价格分析 Skill。入口脚本为 `scripts/analyze_purchase.py`，只接受显式指定的 UTF-8 CSV 和显式的包含起止日期：

```text
python scripts/analyze_purchase.py --input examples/fictional-purchases.csv --start-date 2026-01-01 --end-date 2026-02-28
```

## 输入

CSV 必须包含以下列：`order_id, material, supplier, order_date, quantity, unit_price, unit, specification, currency, tax_treatment`。
`order_date` 仅接受 `YYYY-MM-DD`，不接受时间戳；这是日期型、无时区输入。数量和单价使用 Python `Decimal` 计算。CSV 文件大小上限为 1 MiB。Excel/XLSX 不在本版本支持范围内，请先使用经审查的本地工具导出 UTF-8 CSV；普通 Skill 上的 Python 执行能力尚未获平台验证。

## 计算边界

- 可比组严格要求 `material + specification + unit + currency + tax_treatment` 五项完全一致。供应商不是可比键，因此同一组可计算不同供应商之间的价格变化和报价价差。
- 采购总额按 `quantity × unit_price` 计算，并按币种分别汇总；绝不跨币种相加。
- 供应商集中度按币种统计供应商金额占比和 HHI，不把不同币种合并。
- 同周期趋势将选定日期范围的首尾等长半区间比较；奇数天的中间日期不纳入趋势比较。JSON 中明确列出两个半区间。
- 报价相邻变动和同一可比组最高/最低报价价差达到 20% 时，输出 `anomaly_candidates`。这只是带阈值和证据订单号的候选，不是舞弊或最终结论。
- 同一 `material` 但规格、单位、币种或税务处理不同的组输出 `NOT_COMPARABLE`；这些差异不会生成异常候选，也不会被当作价格变化。

## 校验和隐私

缺失字段、错误数字、非法日期、负值、重复订单号、非法币种和疑似表格公式单元格会进入 `invalid_rows`，并以行号和稳定错误码说明，不回显原始单元格。重复订单号的所有行均排除。日期范围外的合法行计入 `out_of_range_rows`，不参与计算。

脚本只在本地读取文件，不上传数据；输出仅保留文件名，不输出绝对路径或原始整行输入，但**会包含物料、供应商和订单标识及聚合金额**，必须仅向获授权人员提供。输出 JSON 使用稳定排序，便于审计和复现。本地执行通过不能证明 WorkBuddy 平台安装、调用或审核通过。

## 输出

输出包含 `purchasing_totals`、`supplier_concentration`、`comparable_price_changes`、`supplier_quote_spread`、`same_period_trend`、`anomaly_candidates`、`incompatible_group_differences` 和 `invalid_rows`。金额、数量、百分比均为字符串以避免 JSON 浮点精度损失；百分比单位为 `%`。
