---
name: wangbin-sales-analyzer
display_name: 销售收入分析
display_name_en: Sales Revenue Analytics
description: 基于授权销售订单 CSV 计算收入趋势、产品排名、客户贡献与集中度，并对期间完整性和数据风险做出明确标注
description_zh: 基于授权销售订单 CSV 计算收入趋势、产品排名、客户贡献与集中度，并对期间完整性和数据风险做出明确标注
description_en: Analyze authorized sales-order CSV data for revenue trends, product ranking, customer contribution and concentration with explicit completeness and data-risk status
examples_zh:
- 请使用本地 UTF-8 CSV 分析 2026 年 1 月至 2 月销售收入，按 CNY 和 USD 分开，并仅在我提供完整期间和 as-of 日期时计算 MoM/YoY。
examples_en:
- Analyze local UTF-8 CSV revenue for January and February 2026, keep CNY and USD separate, and calculate MoM/YoY only for periods explicitly marked complete with an as-of date.
version: 0.1.2
author: wangbin
license_type: PROPRIETARY
license_status: REQUIRES_MANUAL_REVIEW
---

# 销售收入分析 Skill 0.1.2

## 能力边界

- 输入：本地、授权的 UTF-8 CSV；必需列为 `order_id, customer, product, order_date, amount, currency`。
- 输出：选定期间的销售收入总额与月度趋势、产品收入排名、客户贡献、客户集中度、异常候选和运营风险。
- 金额使用 Python `Decimal`，币种始终分开汇总，不做汇率换算；日期必须是 `YYYY-MM-DD`，按 date-only 处理，不做时区转换。
- `MoM`/`YoY` 只有在 `--as-of-date` 存在且当前期间及对应可比期间都通过 `--complete-period START:END` 明确声明完整时才计算；否则返回 `UNKNOWN`，不根据订单行数量猜测完整性。
- 没有成本数据时，利润、毛利率和盈利能力均为 `UNKNOWN`；收入不等于利润，本 Skill 不做利润推断。
- XLSX/PDF 当前不支持；不会假装已读取这些格式。输入公式单元格、重复订单号、无效日期、负金额和其他无效行会被拒绝或排除，并给出不含原始单元格值的风险信息。

## CLI

```bash
python packages/skills/wangbin-sales-analyzer/scripts/analyze_sales.py \
  --input packages/skills/wangbin-sales-analyzer/examples/fictional-sales.csv \
  --start-date 2026-01-01 --end-date 2026-02-28 \
  --as-of-date 2026-03-01 \
  --complete-period 2026-01-01:2026-01-31 \
  --complete-period 2026-02-01:2026-02-28
```

CLI 成功时仅向 stdout 输出稳定 JSON，输入错误以退出码 2 和安全错误码写入 stderr；不输出绝对路径、原始日志或原始单元格内容。示例 CSV 与由实际 CLI 运行生成的 expected JSON 位于 `examples/`。

## 不应声称的内容

本地脚本测试不等于 WorkBuddy 平台安装或运行验证；本 Skill 不上传数据、不提供利润结论、不跨币种比较，也不把 MoM/YoY 的 `UNKNOWN` 改写为零或估算值。
