# Input–Output Contract / 输入输出合同

## 1. Invocation / 调用

The Skill accepts an input manifest and a matching configuration. It must not infer paths from the current directory.

```yaml
input_root: ./authorized-inputs
po_files: [po.xlsx]
receipt_files: [receipts-jan.csv, receipts-feb.xlsx]
invoice_files: [invoice-001.xlsx, invoice-002.xlsx]
config:
  key_fields: [po_number, po_line_id, item_code]
  case_insensitive: false
  quantity_tolerance: {mode: absolute, value: "0.00", unit: "base_uom"}
  unit_price_tolerance: {mode: absolute, value: "0.00", unit: "currency/unit"}
  amount_tolerance: {mode: absolute, value: "0.00", unit: "currency"}
  allow_repeated_po_lines: false
```

All paths are relative to `input_root`; reject absolute paths, traversal, symlinks, directories, unsupported extensions, and files outside the root.

## 2. Input files and required fields / 输入文件及必需字段

Each logical input may contain multiple files and worksheets. CSV is UTF-8 (BOM accepted); XLSX worksheet names must be specified when multiple sheets exist. Column aliases may be configured explicitly; unknown aliases are not guessed.

### PO (required)

| Field | Type | Required | Rule |
|---|---|---:|---|
| `po_number` | text | yes | nonblank |
| `po_line_id` | text | yes | nonblank and stable within PO |
| `item_code` | text | yes by default | part of default key; can be removed only by explicit config |
| `ordered_quantity` | Decimal | yes | finite, nonnegative |
| `po_unit_price` | Decimal | yes | finite, nonnegative |
| `po_amount` | Decimal | conditional | required when amount comparison is enabled; otherwise derivable only if quantity and price exist |
| `currency` | text | yes | ISO-like configured code; no conversion guessed |
| `uom` | text | yes | nonblank |

### Receipt (required)

| Field | Type | Required | Rule |
|---|---|---:|---|
| `po_number`, `po_line_id`, `item_code` | text | yes | exact configured key |
| `receipt_number` | text | yes | source-document identity |
| `receipt_line_id` | text | yes | duplicate detection with receipt number |
| `received_quantity` | Decimal | yes | finite, nonnegative |
| `receipt_date` | ISO date | no | invalid supplied dates are errors |
| `uom` | text | yes | must match PO unless conversion configured |

### Invoice (required)

| Field | Type | Required | Rule |
|---|---|---:|---|
| `po_number`, `po_line_id`, `item_code` | text | yes | exact configured key |
| `invoice_number` | text | yes | duplicate detection |
| `invoice_line_id` | text | yes | duplicate detection with invoice number |
| `invoiced_quantity` | Decimal | yes | finite, nonnegative |
| `invoice_unit_price` | Decimal | yes | finite, nonnegative |
| `invoice_amount` | Decimal | yes | finite, nonnegative; never blank-as-zero |
| `currency` | text | yes | must match PO unless conversion configured |
| `uom` | text | yes | must match PO unless conversion configured |

### Provenance required on every source row

`source_file`, `source_sheet` (empty for CSV), `source_row_number` (1-based physical row), `original_key_values`, and `source_row_hash` (deterministic hash of normalized raw row). Original text values must be preserved separately from normalized comparison values.

## 3. Calculation contract / 计算合同

Use decimal arithmetic with explicit scale/rounding defined by configuration. Never coerce missing numeric data to zero. For key `K`:

- `ordered_qty = Σ PO.ordered_quantity`; `received_qty = Σ Receipt.received_quantity`; `invoiced_qty = Σ Invoice.invoiced_quantity`.
- `expected_amount = PO.po_amount` when present; otherwise `ordered_qty × PO.po_unit_price` only when both are present.
- `invoiced_amount = Σ Invoice.invoice_amount`.
- `weighted_invoice_unit_price = Σ(invoice_qty × invoice_unit_price) / invoiced_qty` when invoice quantities exist and `invoiced_qty > 0`; otherwise `NOT_AVAILABLE`.
- Variance is actual minus expected. Each comparison has a configured tolerance object `{mode: absolute|relative, value: Decimal, unit}`. Default is absolute zero. A pass is `abs(variance) <= tolerance` (relative mode uses `max(abs_tol, abs(expected)×value)`).
- Any unavailable operand yields `NOT_COMPARABLE`, not pass and not zero.

## 4. Output contract / 输出合同

Outputs are written to a new output directory and include exactly these seven worksheets in this order:

1. **Match Summary / 匹配汇总** — one row per PO key, headline `status`, counts, aggregate quantities/amounts, variances, currency/UOM, and `exception_codes`.
2. **Line Results / 行级结果** — each PO/receipt/invoice logical comparison, all component values, pass flags, and every applicable exception code.
3. **Exceptions / 例外明细** — one row per `(comparison_key, exception_code, source_row_reference)`; no loss when one result has multiple exceptions.
4. **Unmatched Receipts / 未匹配收货** — receipt rows not safely assigned to a PO key, including orphan and ambiguous reasons.
5. **Unmatched Invoices / 未匹配发票** — invoice rows not safely assigned to a PO key, including orphan and ambiguous reasons.
6. **Source Trace / 来源追溯** — every consumed source row with file/sheet/row/hash, normalized key, inclusion/exclusion reason, and output row references.
7. **Run Manifest / 运行清单** — product/version, configuration, input file names and byte hashes, row counts, timestamps, warnings/errors, limits, and completion status.

All worksheet names, column names, status values, and exception codes are stable contract identifiers; display labels may include Chinese/English. Spreadsheet formula injection must be prevented by textualizing values beginning with `=`, `+`, `-`, or `@` when written as text.

Additional outputs:

- `summary.json`: schema version, run status (`SUCCEEDED`, `SUCCEEDED_WITH_EXCEPTIONS`, `FAILED_INPUT`, `FAILED_LIMIT`, `FAILED_INTERNAL`), totals, exception-code counts, and output file references.
- `report.md`: concise bilingual explanation, limitations, and links to worksheet names/row references. It must not claim approval, payment, or completeness when errors exist.

## 5. Error/status contract / 错误合同

| Code | Meaning | Required behavior |
|---|---|---|
| `INVALID_INPUT` | missing/unreadable/unsupported file or schema | fail affected logical input; no success claim |
| `LIMIT_EXCEEDED` | file/batch/container/row/time limit | stop affected work and record actual limit |
| `MISSING_REQUIRED_FIELD` | required field blank/missing | exclude row from comparison; retain trace |
| `AMBIGUOUS_KEY` | a complete explicit key maps to >1 candidate PO keys | exclude from aggregate; do not use this code merely because a required key component is missing |
| `DUPLICATE_PO_KEY` | repeated PO key without explicit permission | exception; do not silently merge |
| `DUPLICATE_SOURCE_ROW` | repeated receipt/invoice document-line identity | retain both; flag |
| `ORPHAN_RECEIPT` / `ORPHAN_INVOICE` | no valid PO key | unmatched sheet + exception |
| `QTY_OVER` / `QTY_UNDER` | quantity outside tolerance | row exception |
| `PRICE_MISMATCH` | invoice and PO price outside tolerance | row exception |
| `AMOUNT_MISMATCH` | amount outside tolerance | row exception |
| `CURRENCY_MISMATCH` / `UOM_MISMATCH` | comparison dimensions conflict | not comparable; no conversion guessed |
| `NOT_COMPARABLE` | required operand unavailable | no pass; preserve reason |

A failed run must still emit `Run Manifest` and `summary.json` where possible, with `completion_status` and machine-readable errors. No missing value becomes `0`, `MATCHED`, or an empty success.

## 6. Limits/security contract / 限制安全合同

Defaults: 50 MiB/file, 50 files/batch, 200 MiB/batch, 200 MiB expanded container. Only lower overrides are permitted. Input root and output root must be distinct. Do not execute macros/formulas/scripts or fetch remote resources; do not log secrets or full source content; do not upload source data or write external systems without explicit authorization.
