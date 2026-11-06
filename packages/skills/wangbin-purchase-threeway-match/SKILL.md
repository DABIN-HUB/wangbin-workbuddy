---
name: wangbin-purchase-threeway-match
display_name: 采购三单匹配
display_name_en: Purchase Three-Way Match
description: Deterministic local PO, receipt, and invoice matching with explicit tolerances, seven worksheets, and traceable exceptions.
description_zh: 在本地读取明确指定的采购订单、收货和发票表格，按明确键进行三单匹配，支持拆分、容差、多例外和七个追溯工作表。
description_en: Locally match explicitly selected purchase orders, receipts, and invoices by configured keys with tolerances, split aggregation, multi-exception evidence, and seven traceable worksheets.
examples_zh:
  - 请核对这批采购订单、收货记录和供应商发票，允许同一订单行分批收货和开票；输出汇总、例外和来源行号，金额差异超过 0.01 时标记为需复核。
  - 请检查这份发票中缺少订单号、行号或物料编码的行；不要猜测归属，只保留一次并在未匹配发票和来源追溯中说明缺少的信息。
  - 请核对没有对应采购订单的收货和发票；分别列入未匹配收货、未匹配发票和例外明细，不要为孤立记录创建无关的不可比较结果。
examples_en:
  - Match these purchase orders, receipt records, and supplier invoices, allowing one order line to be received and invoiced in splits; show totals, exceptions, and source row references, and flag amounts beyond 0.01 for review.
  - Review invoice rows missing an order number, line number, or item code; do not infer ownership, retain each row once, and explain the missing information in unmatched invoices and source trace.
  - Check receipts and invoices with no corresponding purchase order; place them in their respective unmatched sheets and exception details without creating unrelated non-comparable results for orphan records.
version: 0.1.3
author: Wangbin Research
license_type: PROPRIETARY
license_status: REQUIRES_MANUAL_REVIEW
---

# 采购三单匹配 / Purchase Three-Way Match

这是一个仅在本地执行的确定性 WorkBuddy Skill。它不会上传数据、调用 ERP、批准付款或猜测缺失键。请提供采购订单、收货和发票文件，并为多工作表文件明确指定工作表：

## 技术说明 / Technical notes

维护者可使用 JSON manifest，通过本地 Python 命令运行：
```bash
python scripts/threeway_match.py --manifest examples/manifest.json --output examples/output
```

## 输入 / Input

Manifest 包含 `po_files`、`receipt_files`、`invoice_files` 三个逻辑输入，可分别列出多个 CSV/XLSX 文件。默认键为 `po_number + po_line_id + item_code`。数量、单价和金额按精确规则比较，容差对象必须显式给出模式、数值和单位。空值不是零；重复、歧义、孤儿行和不支持的币种/UOM 都保留证据。

## 输出 / Output

新建输出目录，生成 `threeway_match.xlsx`（严格七表顺序：Match Summary、Line Results、Exceptions、Unmatched Receipts、Unmatched Invoices、Source Trace、Run Manifest）、`summary.json` 和 `report.md`。每个源行含文件名、工作表、物理行号、原始键及稳定行指纹。表格值以文本方式保护公式注入；输入目录不会被覆盖。

结果是控制证据而不是“已批准/已付款”结论。超过文件、批次或文件数限制时失败并记录限制。支持 CSV/XLSX 读取，不执行宏、公式、脚本或远程链接；不支持 OCR、模糊匹配、汇率或 UOM 猜测。
