# Phase 7L-R2 synthetic trading-fee payment delivery v1

本地审阅包仅包含两个明确绑定的 SYNTHETIC/ASSUMED 年度预测案例，不是实际合同、付款凭证、银行流水或投资建议。交易费按本年度 3C 单列计提额在同一运营年度 100% 预计支付，期初交易费应付为 0 元。

## Case identities

| case | canonical result hash | source SHA-256 | status |
|---|---|---|---|
| industrial_rooftop | `ca4bdff3f5e89e6770d43f4dad3b4efd57d965aba6c9ba0f1b4299f99295a43f` | `a554f6ad45d094348cf513ada1ddc073b9529603bee9c8a7f4274b13e0af908b` | PARTIAL / synthetic |
| utility_scale_ground | `69882cc39020f03fb3ef6cdb1a10b188c324de0f66066392970776b7495ad138` | `09e80d600b67ffdca96c2a77d3fb1d2f85a797f9d9c5a951f1670d2dc9423e1a` | PARTIAL / synthetic |

Both hashes are the final replay/CLI identities. The source hash identifies JSON bytes only; it does not prove external payment.

## Evidence gates

- `LOCAL_CALCULATION_CHAIN`: verified for both cases through replay, ordinary `project` CLI, and rooftop `project-report`; ground wrapper is run separately and its receipt is included with this delivery evidence.
- `SYNTHETIC_FINANCIAL_VALIDATION`: 25 operating-year fee accrual/payment/payable bridge verified for each case; missing-source behavior remains blocked.
- `DOCUMENT_GENERATION`: final DOCX, model XLSX, source/assumption XLSX, canonical and manifests generated from the final canonical identities.
- `DOCUMENT_PROFESSIONAL_REVIEW`: `CONTENT_REVIEW_REQUIRED`; not a human professional approval.
- `FOUR_FILE_GATE`: `BLOCKED`; PDF renderer unavailable and TOC page refresh not performed.
- `WORKBUDDY_PLATFORM_TEST`: `NOT_VERIFIED`; no upload, review, publication or Phase 8 action performed.

The combined formal ZIP and its member/hash receipt are generated alongside this file. Separate user-review ZIPs are also provided as `industrial_rooftop-review-v1.zip` and `utility_scale_ground-review-v1.zip`, with `CASE-ZIP-RECEIPT.json` recording their byte sizes and SHA-256 values. Historical v5, v6 and diagnostic v7 trees remain separate and are not overwritten.
