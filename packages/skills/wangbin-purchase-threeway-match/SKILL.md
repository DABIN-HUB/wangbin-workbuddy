---
name: wangbin-purchase-threeway-match
display_name: 采购三单匹配
display_name_en: Purchase Three-Way Match
description: Deterministic local CSV/XLSX PO, receipt, and invoice matching with exact Decimal arithmetic, explicit tolerances, seven worksheets, and traceable exceptions.
description_zh: 在本地读取明确指定的 PO、收货和发票 CSV/XLSX，按显式键做精确 Decimal 三单匹配，支持拆分、容差、多例外和七个追溯工作表。
description_en: Locally match explicitly selected PO, receipt, and invoice CSV/XLSX files by configured keys using exact Decimal arithmetic, split aggregation, tolerances, multi-exception evidence, and seven traceable worksheets.
examples_zh:
  - 请用 PO、收货记录和发票逐行做采购三单匹配。允许同一 PO 行拆成多次收货和多张发票；数量、单价和金额容差均为 0.01，币种必须一致。输出七个工作表，并保留文件名、工作表、行号和原始键。缺失或歧义不要猜，所有例外放在同一结果行并列出。
examples_en:
  - Match this purchase order, the receipt records, and the supplier invoices. Allow split receipts and split invoices for one PO line; use 0.01 tolerance for quantity, unit price, and amount, and require the same currency. Produce the seven worksheets with file, sheet, row, and original-key traceability. Do not guess missing or ambiguous data; list every applicable exception on the same result row.
version: 0.1.0
author: Wangbin Research
license_type: PROPRIETARY
license_status: REQUIRES_MANUAL_REVIEW
---

# 采购三单匹配 / Purchase Three-Way Match

这是一个仅在本地执行的确定性 WorkBuddy Skill。它不会上传数据、调用 ERP、批准付款或猜测缺失键。输入必须是 JSON manifest，路径相对于 `input_root`，每个 XLSX 多工作表文件必须显式指定 `sheet`：

```bash
python scripts/threeway_match.py --manifest examples/manifest.json --output examples/output
```

## 输入 / Input

Manifest 包含 `po_files`、`receipt_files`、`invoice_files` 三个逻辑输入，可分别列出多个 CSV/XLSX 文件。默认键为 `po_number + po_line_id + item_code`。数量、单价和金额使用 Python `Decimal`，容差对象必须显式给出 `mode`、`value` 和 `unit`。空值不是零；重复、歧义、孤儿行和不支持的币种/UOM 都保留证据。

## 输出 / Output

新建输出目录，生成 `threeway_match.xlsx`（严格七表顺序：Match Summary、Line Results、Exceptions、Unmatched Receipts、Unmatched Invoices、Source Trace、Run Manifest）、`summary.json` 和 `report.md`。每个源行含文件名、工作表、物理行号、原始键及 SHA-256 行哈希。表格值以文本方式保护公式注入；输入目录不会被覆盖。

结果是控制证据而不是“已批准/已付款”结论。超过文件、批次或文件数限制时失败并记录限制。支持 CSV/XLSX 读取，不执行宏、公式、脚本或远程链接；不支持 OCR、模糊匹配、汇率或 UOM 猜测。
