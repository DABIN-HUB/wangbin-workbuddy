---
name: wangbin-team-smoke-test
display_name: 双侧 CSV 金额核对
display_name_en: Two-sided CSV Amount Reconciler
description: 仅在本地按原样 id 和 Decimal 金额核对两份虚构 CSV，输出四类明细与汇总。
description_zh: 本地核对两份用户明确指定的 UTF-8 CSV；不联网、不读取目录、不推测数据。
description_en: Reconcile two explicitly selected fictional UTF-8 CSV files locally by exact id and Decimal amount.
version: 0.1.0
author: wangbin
allowed-tools: Read, Bash
---
# 双侧 CSV 金额核对

只处理用户明确指定的两份虚构 CSV 和输出目录。运行：

```bash
python packages/skills/wangbin-team-smoke-test/scripts/reconcile_csv.py --left examples/left.csv --right examples/right.csv --output /path/to/empty-output
```

输入必须是 UTF-8（可 BOM）且表头严格为 `id,amount`；金额只允许十进制整数或最多两位小数。id 保留原文，不 trim、不大小写折叠；失败输出 stderr 单行 JSON 并返回 2。成功会在新的输出目录生成 `matched.csv`、`left_missing.csv`、`right_missing.csv`、`amount_mismatch.csv` 和 `summary.json`，不覆盖已有目标文件。`left_missing` 表示左侧没有、右侧有；`right_missing` 表示右侧没有、左侧有。

这是本地 MVP，不代表平台安装、审核、发布或真实业务结论；不得将缺失金额当作零，也不得改写输入或猜测字段。
