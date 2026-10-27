---
name: wangbin-inventory-analyzer
display_name: 库存呆滞分析
display_name_en: Inventory Slow-Moving Analysis
description: Analyze bounded UTF-8 inventory CSV snapshots and movements locally with deterministic, evidence-aware candidates.
description_zh: 读取 UTF-8 库存快照、收货、发料 CSV，计算库存价值并识别无移动、慢动、超储候选；数量周转证据不足时明确返回 UNKNOWN。
description_en: Analyze UTF-8 inventory balances, receipts, issues, and optional item master data locally; return deterministic values, candidates, and UNKNOWN when turnover evidence is incomplete.
examples_zh:
  - 请用 2026-02-28 作为 as-of 分析这些库存 CSV。
examples_en:
  - Analyze these inventory CSV files as of 2026-02-28.
version: 0.1.2
author: Wangbin Research
license_type: PROPRIETARY
license_status: REQUIRES_MANUAL_REVIEW
---

# 库存呆滞分析

这是一个本地、确定性的库存分析 Skill。入口脚本为 `scripts/analyze_inventory.py`，必须显式提供三类 UTF-8 CSV 和 `--as-of` 日期；不会自动发现文件、上传数据或执行表格公式：

```text
python scripts/analyze_inventory.py \
  --balances examples/fictional-balances.csv \
  --receipts examples/fictional-receipts.csv \
  --issues examples/fictional-issues.csv \
  --master examples/fictional-master.csv \
  --as-of 2026-02-28
```

## 输入

- `balances` 必须包含 `item_id, warehouse, balance_date, quantity, unit_cost, currency`。它是库存快照，不是交易流水。
- `receipts` 必须包含 `receipt_id, item_id, warehouse, receipt_date, quantity, unit_cost, currency`。
- `issues` 必须包含 `issue_id, item_id, warehouse, issue_date, quantity, currency`。
- `master` 可选，至少包含 `item_id`；若提供 `item_name, unit, reorder_point, max_stock`，脚本会在结果中使用已读取的值。
- 日期只接受 `YYYY-MM-DD`；数量、单价和主数据阈值使用 `Decimal`。每个 CSV 的大小上限为 1 MiB，且只接受 `.csv` 和 UTF-8。

## 计算和证据边界

- 每个 `item_id + warehouse + currency` 取 `as-of` 当日及之前日期最近的有效余额快照作为期末库存；库存价值为 `quantity × unit_cost`，按币种分别汇总，不跨币种换算。
- 观察区间从该组最近期末快照之前的最近快照开始；收货和发料只计入期初日之后至 `as-of` 的有效记录。
- 数量周转率为 `区间发料数量 / ((期初数量 + 期末数量) / 2)`。只有同时存在不同日期的期初快照、期末快照和至少一条有效发料记录时才计算；否则 `quantity_turnover` 和 `turnover_status` 为 `UNKNOWN`，不以零代替缺失证据。
- 无移动候选：可观察区间没有有效收货或发料。慢动候选：数量周转率不高于 1。超储候选：主数据 `max_stock` 存在且期末数量超过它；缺少主数据时不会臆测安全库存，已有周转证据时才可按发料折算覆盖天数超过 90 天列候选。
- `BALANCE_MISMATCH`：期初数量 + 收货 - 发料不等于期末快照。候选和异常都带有解释，但不代表审计、舞弊或最终业务结论。

## 校验、隐私和限制

缺列或空文件是明确的输入错误；错误类型、非法日期、负值、零发料、重复快照/交易 ID、疑似公式单元格会进入 `invalid_rows` 并排除对应行。超过 `as-of` 的合法行计入 `out_of_range_rows`。结果只保留文件名，不输出绝对路径或原始单元格；拒绝符号链接、非 UTF-8 和超过 1 MiB 文件。

输出包含 `inventory`、`inventory_value`、`no_movement_candidates`、`slow_moving_candidates`、`overstock_candidates`、`anomaly_candidates`、`invalid_rows`、`assumptions` 和 `anomaly_rules`。数量、金额和比率以字符串输出，确保 JSON 确定性和 Decimal 精度。Excel/XLSX、PDF、汇率换算及平台运行时验证不在本版本范围内。
