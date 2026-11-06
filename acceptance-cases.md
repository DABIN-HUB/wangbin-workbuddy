# Acceptance Cases / 验收用例

All cases use the frozen input/output contract. Unless a case says otherwise, tolerances are absolute `0.00`, the key is `(po_number, po_line_id, item_code)`, and decimal arithmetic is used. Each case is independently executable and must assert both values and traceability.

| ID | Setup / 输入 | Expected result / 预期 | Contract |
|---|---|---|---|
| **A01** | One PO line 10 @ 5.00 USD; one receipt 10; one invoice 10 @ 5.00, amount 50.00. | `MATCHED`; zero variances; all seven sheets exist in frozen order; summary and line rows carry source file/sheet/row. | requirements §3–§4; IO-01–17 |
| **A02** | PO, receipt, and invoice are each supplied as explicitly named worksheets in XLSX files; all required columns are present. | Correct worksheets are read; other worksheets are not implicitly treated as inputs; source sheet names are retained. | requirements §3; IO-01 |
| **A03** | One PO line 10; receipts split 4 + 6 across two files; invoice split 3 + 7 across two invoice files. | Aggregates are 10/10; `MATCHED`; source trace has all four component rows; no split row is lost or deduplicated. | requirements §3–§4.1; IO-02, IO-03 |
| **A04** | PO 10 @ 5.00, receipt 8, invoice 10 @ 5.00. | Headline is not `MATCHED`; includes `QTY_UNDER` for receipt; invoice comparison may pass; all applicable codes retained. | requirements §4.2; IO-03 |
| **A05** | PO quantity 10, price 5.00, amount 50.00; invoice qty 10, price 5.01, amount 50.10; amount tolerance 0.01 (and price tolerance 0.01). | `PRICE_MISMATCH` is not raised because the price difference is 0.01 and the comparison is inclusive. `AMOUNT_MISMATCH` is raised because amount variance is exactly 0.10, which exceeds the 0.01 amount tolerance; the row is not `MATCHED`, and `amount_variance=0.10`. | requirements §4.2; IO-08 |
| **A06** | Same as A04 but invoice price 5.02 and amount 50.20 with tolerance 0.01. | `PRICE_MISMATCH` and `AMOUNT_MISMATCH`; not matched; exact decimal variances are 0.02 and 0.20. | requirements §4.2; IO-08 |
| **A07** | PO amount omitted; PO qty and price present; invoice amount present. | Expected amount is explicitly derived and labeled derived; result is comparable; no fabricated input amount. A missing qty or price instead yields `NOT_COMPARABLE`. | requirements §4.1–§4.2; IO-07 |
| **A08** | Two PO rows share the same default composite key; no repeated-line allowance. | Both remain in trace; `DUPLICATE_PO_KEY`; no silent aggregation; headline not `MATCHED`. | requirements §4.3; IO-10 |
| **A09** | Receipt row has missing `item_code`; one or more PO rows could otherwise appear compatible. | Row is retained exactly once, excluded from aggregate, and receives `MISSING_REQUIRED_FIELD`; missing key data is not treated as multiple candidates, so `AMBIGUOUS_KEY` is not required. It appears once in unmatched receipt and in source trace. | requirements §4.1, §4.3; IO-10 |
| **A10** | One invoice document-line appears twice with same invoice number and line id. | Both physical rows retained; `DUPLICATE_SOURCE_ROW`; invoice is not silently halved/deduplicated; exception sheet has source references for both. | requirements §4.3; IO-10 |
| **A11** | One invoice is missing one component of the required exact key `(po_number, po_line_id, item_code)`; no partial-key candidate search is configured. | Invoice is retained exactly once, contributes to neither aggregate, and receives `MISSING_REQUIRED_FIELD` plus the report reason `无法匹配 / cannot match`. It appears once in unmatched invoice and source trace. No candidate is inferred and `AMBIGUOUS_KEY` is not asserted. `AMBIGUOUS_KEY` remains applicable only to a complete explicit key that genuinely maps to more than one PO candidate. | requirements §4.1, §4.3; IO-10–11 |
| **A12** | PO key has PO currency USD and Invoice currency CNY; Receipt has no currency field in this contract; no conversion config. | `CURRENCY_MISMATCH` and `NOT_COMPARABLE`; no exchange rate guessed; the PO/Invoice currency fields and all source rows are retained. No receipt-currency field is required or added. | requirements §4.1–§4.2; IO-10 |
| **A13** | One key has receipt 11 for PO 10 and invoice 11 at wrong price. | One line result contains both `QTY_OVER` and `PRICE_MISMATCH`; exceptions sheet has separate rows; headline precedence is deterministic. | requirements §4.2–§4.4; IO-12 |
| **A14** | Orphan receipt and orphan invoice with no matching PO. | They appear in their respective unmatched worksheets and exception counts; summary does not count them as matched. | requirements §4.3; IO-14–15 |
| **A15** | Run a valid dataset twice with identical config and files. | Same statuses, decimal values, exception ordering, worksheet order, and deterministic source hashes; run manifest records input hashes. | requirements §3–§4.1; IO-13–17 |
| **A16** | Input path is outside `input_root`, a symlink, traversal path, unsupported extension, or output root equals input root. | Reject with `INVALID_INPUT`; no input overwrite; no external file read. | requirements §5; IO-18 |
| **A17** | File is 50 MiB + 1 byte or batch exceeds 200 MiB/50 files. | Reject with `LIMIT_EXCEEDED`; actual limit and offending file recorded; no success claim. | requirements §5; IO-18 |
| **A18** | XLSX contains formula/macro/remote link or a value beginning `=`, `+`, `-`, `@`. | No macro/formula/script execution or remote fetch; exported text is safely textualized; warning/error is traceable. | requirements §5; IO-16 |
| **A19** | Required invoice quantity is blank, not zero; malformed decimal or unsupported UOM. | Blank is not zero; row gets `MISSING_REQUIRED_FIELD` or `INVALID_INPUT`; unsupported UOM gets `UOM_MISMATCH`; output status is not matched. | requirements §4.1, §5; IO-18 |

## Acceptance checklist / 验收检查清单

- [ ] Three logical inputs and multi-file/sheet ingestion are tested.
- [ ] Split receipts and split invoices aggregate only on explicit keys.
- [ ] Quantity, unit price, amount, currency, and UOM rules use Decimal and explicit tolerances.
- [ ] Missing values are never converted to zero; guesses are prohibited.
- [ ] Duplicate, ambiguous, orphan, and multi-exception cases preserve all evidence.
- [ ] Exactly seven worksheets are generated in the specified order, plus JSON/Markdown outputs.
- [ ] Every source row has file/sheet/physical-row/hash provenance.
- [ ] Security, limits, formula/macro handling, and output isolation are verified.
- [ ] No case claims platform installation, approval, payment release, or external publication.

## Evidence recording / 证据记录

The implementer must record command, environment, input fixture identifiers, observed output, and pass/fail for every A01–A19 case. Unrun cases must be reported as `NOT_TESTED`, never inferred as passed. Any implementation deviation requires a new version or explicit requirements change review; it must not be hidden in examples or display text.
