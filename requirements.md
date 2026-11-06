# Purchase Three-Way Match — Requirements / 采购三单匹配需求

- **product_id:** `wangbin-purchase-threeway-match`
- **version:** `0.1.0`
- **type:** WorkBuddy Skill
- **status:** frozen requirements contract; implementation is out of scope for this task

## 1. Product definition / 产品定义

**中文说明：** 面向采购、财务和仓库人员，将采购订单（PO）、收货/入库记录（Receipt）和供应商发票（Invoice）按明确业务键进行三单匹配，逐行给出可解释的匹配结果、差异、例外和来源追溯。它不是采购价格分析、应收账款核销、供应商评分或自动审批工具。

**English description:** A WorkBuddy Skill for procurement, finance, and warehouse users that matches purchase orders, receipts, and supplier invoices using explicit business keys, then reports row-level match results, variances, exceptions, and source traceability. It is not a spend-analysis, receivables-reconciliation, supplier-scoring, or auto-approval tool.

### Independent value / 独立价值

The independent job is a three-document control: ordered quantity/price/amount versus received quantity versus invoiced quantity/price/amount. Unlike a purchase-price analysis, this product detects fulfillment and billing mismatches; unlike a generic document assistant, every result is computed from structured source rows and linked to source locations. Missing, ambiguous, duplicate, or conflicting evidence is reported as an exception—not silently inferred.

## 2. Users and problem / 用户与问题

| User / 用户 | Problem solved / 解决问题 |
|---|---|
| Procurement / 采购 | Identify PO lines not fully received or billed and supplier over/under-billing. |
| AP/finance / 应付财务 | Hold invoices with quantity, unit-price, amount, currency, duplicate, or key ambiguity exceptions. |
| Warehouse / 仓库 | Compare receipts with order commitments and invoice claims. |
| Controller / 内控 | Obtain deterministic, auditable row-level evidence and an exception work queue. |

## 3. MVP scope / MVP 范围

1. Accept exactly three logical inputs: PO, receipt records, invoice records; each may be one or more CSV/XLSX files or explicitly named worksheets.
2. Support split receipts and split invoices: multiple rows may aggregate against one PO line.
3. Match only by a configured explicit composite key. Default key: `po_number + po_line_id + item_code`; optional `receipt_number`/`invoice_number` identify source documents but are not substitutes for the PO key.
4. Compare exact decimal quantities, unit prices, and line amounts, with explicit configured tolerances. Never use binary floating-point semantics.
5. Produce seven output worksheets, a machine-readable summary, and a human-readable report; output row values include source traceability.
6. Surface duplicate keys, ambiguous keys, missing required values, unsupported currencies/units, and every applicable exception on the same result row.
7. Preserve deterministic ordering and calculations for the same inputs, configuration, and software version.

## 4. Explicit rules / 可测试规则

### 4.1 Normalization and aggregation

- Trim surrounding whitespace from text fields; preserve original values in traceability fields.
- Key comparison is case-sensitive unless configuration explicitly sets `case_insensitive=true`; no fuzzy matching, transliteration, or guessed aliases.
- Receipt and invoice rows are aggregated by the exact configured PO composite key. Splits are allowed across files, sheets, documents, dates, and row numbers.
- A row with a missing key component is not aggregated or matched; it receives exactly one `MISSING_REQUIRED_FIELD` finding for the missing required key data and is retained once in the relevant unmatched output. Missing key data is not evidence of multiple candidates and must not be labeled `AMBIGUOUS_KEY`.
- Numeric fields are parsed as decimal values only. Blank, `NA`, `-`, malformed, negative (where not explicitly allowed), or contradictory values are not converted to zero.
- If line amount is supplied, compare it to `quantity × unit_price` using `amount_tolerance`; if absent, do not fabricate it. Derived amounts must be labeled derived.
- Currency and unit of measure must agree across records that provide the corresponding field, unless an explicit conversion table/configuration is supplied. The Receipt input has no currency field in this contract; therefore currency comparison is between PO and Invoice only. No exchange rate or unit conversion is guessed.

### 4.2 Matching and tolerance

For each distinct PO key:

- `ordered_qty = sum(PO.quantity)`; `received_qty = sum(Receipt.quantity)`; `invoiced_qty = sum(Invoice.quantity)`.
- `qty_variance_receipt = received_qty - ordered_qty` and `qty_variance_invoice = invoiced_qty - ordered_qty`.
- `price_variance = invoice_unit_price - po_unit_price` when both are present; for split invoices, report weighted-average invoice price and retain component rows.
- `amount_variance = invoiced_amount - expected_amount`, where expected amount is the PO line amount (or ordered quantity × PO unit price only when both are present).
- A comparison passes only when required values exist and absolute variance is `<=` its configured tolerance. Tolerances are explicit per dimension: `quantity_tolerance`, `unit_price_tolerance`, `amount_tolerance` (default `0`, never implicit percentage).
- Tolerance configuration must include units/currency and whether absolute or relative; relative tolerance is `abs(actual-expected) <= max(abs_tol, abs(expected)*relative_tol)`.
- Over-receipt, over-invoice, under-receipt, under-invoice, price mismatch, amount mismatch, currency mismatch, and UOM mismatch are distinct exception codes.
- No row is marked `MATCHED` if any required comparison is unavailable or any exception applies.

### 4.3 Duplicate and ambiguity handling

- Duplicate PO composite keys are `DUPLICATE_PO_KEY` unless configuration explicitly permits repeated PO lines with an additional disambiguating field.
- Duplicate receipt or invoice document-line identifiers are `DUPLICATE_SOURCE_ROW`; they remain visible and are not deduplicated silently.
- A complete source row whose explicit configured key matches multiple candidate PO keys is `AMBIGUOUS_KEY`; it contributes to no aggregate. A source row with an incomplete key is handled only as `MISSING_REQUIRED_FIELD` and contributes to no aggregate; do not infer candidates or manufacture ambiguity.
- Unmatched receipts/invoices are retained as exceptions (`ORPHAN_RECEIPT`, `ORPHAN_INVOICE`).
- Exception codes are an ordered set, not a single enum. A result row may contain multiple codes, joined deterministically with `;` and also emitted as separate exception rows.

### 4.4 Status precedence

`INVALID_INPUT` (file/schema-level) > `AMBIGUOUS_KEY`/duplicate > `MISSING_REQUIRED_FIELD` > `CURRENCY_OR_UOM_MISMATCH` > quantity exceptions > price exception > amount exception > `MATCHED`. The precedence controls the headline status only; all applicable codes must remain in `exception_codes`.

## 5. Limits and security / 限制与安全

- Inputs must be files inside user-selected `input_root`; reject missing files, directories, symlinks, traversal, and unsupported extensions.
- Default limits: 50 MiB per file, 50 files per batch, 200 MiB batch, and 200 MiB expanded container; configuration may lower but not silently raise limits.
- Do not execute macros, formulas, embedded scripts, or remote links. Treat cell contents as untrusted data.
- Do not send source documents externally unless the user explicitly authorizes the destination and retention/deletion policy.
- Do not log credentials, complete invoice/PO contents, or unnecessary absolute paths. Outputs go to a distinct output directory and never overwrite inputs.
- Parse errors are isolated per file where safe; the batch report records the error and does not claim completeness.

## 6. Non-goals / 不做项

No OCR/scanned-document interpretation; no fuzzy entity resolution; no automatic supplier/PO inference; no tax-law determination; no accounting posting; no approval or payment release; no exchange-rate or UOM guessing; no external ERP/API writes; no cloud upload; no automatic duplicate deletion; no claiming “approved”, “paid”, or “platform tested”.

## 7. Frozen examples / 冻结示例

### examples_zh

> “请用 PO、收货记录和发票逐行做采购三单匹配。允许同一 PO 行拆成多次收货和多张发票；数量、单价和金额容差均为 0.01，币种必须一致。输出七个工作表，并保留文件名、工作表、行号和原始键。缺失或歧义不要猜，所有例外放在同一结果行并列出。”

### examples_en

> “Match this purchase order, the receipt records, and the supplier invoices. Allow split receipts and split invoices for one PO line; use 0.01 tolerance for quantity, unit price, and amount, and require the same currency. Produce the seven worksheets with file, sheet, row, and original-key traceability. Do not guess missing or ambiguous data; list every applicable exception on the same result row.”

## 8. Difference statement / 与相邻产品差异

- **Versus purchase-price analysis:** this evaluates PO–receipt–invoice fulfillment and billing control, not historical price trends or savings.
- **Versus receivable/supplier reconciliation:** this starts from a PO and uses receipt evidence; it does not reconcile customer receivables or supplier statements.
- **Versus generic document assistant:** it has fixed schemas, exact decimal rules, explicit tolerances, seven controlled sheets, and row-level evidence rather than free-form extraction.

## 9. Traceability map / 追溯映射

| Requirement | Contract / acceptance references |
|---|---|
| Three inputs and split aggregation | IO-01–IO-04; A01–A03 |
| Exact values and tolerances | IO-05–IO-09; A04–A06 |
| Duplicate/ambiguity/multi-exception | IO-10–IO-12; A07–A10 |
| Seven outputs and provenance | IO-13–IO-17; A11–A14 |
| Security/limits/non-goals | IO-18; A15–A18 |
