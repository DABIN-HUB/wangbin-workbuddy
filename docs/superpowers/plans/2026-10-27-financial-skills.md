# Four Financial Skills Implementation Plan

> **For agentic workers:** Use independent product workstreams, review each product before a local commit. Steps use checkbox syntax for tracking.

**Goal:** Develop four independent business-calculation Skills, preserve the immutable tender 0.1.0 and Expert candidates, and report local vs WorkBuddy gates separately.

**Architecture:** Reuse the current `python -m tooling.products` registry, Skill generator, validation, test, package and verify commands. Bundle one self-contained Python CSV calculator per product with `Decimal` and ISO dates; no network, macros, code execution, implicit platform Python assumption or external paid API. Review existing document-engine Excel/XLSX security APIs; any XLSX conversion is an optional local preflight, never an unverified runtime promise. Each ZIP contains only its own product files.

**Tech Stack:** Python >=3.11 standard library for CSV, decimal, datetime, JSON; repository pytest and tooling; optional existing openpyxl/document-engine only for separately documented local Excel workflow.

**Spec:** User's four product descriptions and acceptance matrix in this task; `docs/product-factory.md` and `reports/product-factory-release.md` bind factory and protected artifacts.

## Global Constraints

- Protected ZIPs: software consultant SHA-256 `577f3089d2f4707178f44ba1e5c395a99853bb9558f3e8c0e752a0e6ba2e30de`; tender 0.1.0 SHA-256 `2e68809033301c97b02ec7c7fd59f7b477fcd2f1f86d515d69b5fc7b20146bc7`.
- CSV UTF-8 with header, explicit file selection, at most 1 MiB, reject symlinks and non-regular files; reject formula-like input cells (`=`, `+`, `@` and suspicious expression values) rather than evaluating. Support additional formats only with safely verified dependencies, and state WorkBuddy runtime unknown.
- Money uses `Decimal` throughout, explicit currency and units; no inferred profit, legal conclusion, review pass, usage count or development hours. Dates are calendar dates `YYYY-MM-DD`, comparisons at a named as-of date, without implicit timezone conversion.
- Every line-item with invalid date, negative/invalid amount, missing required header, duplicate ID or other anomaly is reported or rejected per documented rule; never silently count it as valid. Stable JSON output does not contain local absolute input paths or unmasked raw personal/financial row data.
- Product-specific test files may be added because this task explicitly requests tests. Tests cover normal, missing, empty, wrong type, duplicate, invalid date, negative, decimal precision, size, privacy, deterministic output and isolated package.
- Platform installation/calls, approval, publication and commercial performance remain `NOT_TESTED`/`BLOCKED`/`UNKNOWN` without direct evidence. Only local commits, no push/PR/tag edits.

## Task 1: Registry and scaffolds

**Files:** `products/catalog.json`, `products/metrics.json`, `tests/test_product_factory.py`, four new `packages/skills/<id>/SKILL.md` and `manifest.json` scaffolds.

- [ ] Register `wangbin-purchase-analyzer` and `wangbin-sales-analyzer` version `0.1.0` alongside already-registered receivable and inventory, with every missing metric `UNKNOWN`.
- [ ] Update the catalog-count assertion to 10 and run `pytest -q tests/test_product_factory.py`.
- [ ] Initialize all four via `python -m tooling.products init --id <id>`; leave scaffold placeholders until each product implementation is ready. Commit registry and scaffold changes only after reviewed tests or fold each scaffold into its product commit.

## Task 2: Receivables

**Files:** `packages/skills/wangbin-receivable-analyzer/{SKILL.md,manifest.json,scripts/analyze_receivables.py,examples/*}`, `tests/test_receivable_analyzer.py`.

- [ ] Define CSV headers for invoice ID, customer, due date, open balance and currency; `--as-of YYYY-MM-DD`, an explicit aging bucket boundary, dedupe invoice IDs, identify negatives/missing/invalid fields.
- [ ] Calculate total open and overdue in `Decimal` per currency; age by overdue calendar days, rank overdue customers, output explainable *review* priority not automatic collection instructions.
- [ ] Write fictional CSV, expected JSON from actual execution, and matrix tests; run product-scoped validate/test/package/verify/release-check; preserve platform gate separately. Commit reviewed product files/catalog hash after passing.

## Task 3: Inventory

**Files:** `packages/skills/wangbin-inventory-analyzer/{SKILL.md,manifest.json,scripts/analyze_inventory.py,examples/*}`, `tests/test_inventory_analyzer.py`.

- [ ] Input CSV balances, receipts and issues, optional product master; explicit `--as-of`, unit/currency per SKU, record identity and time window. Flag mismatched units, duplicates, invalid dates and negative quantities/prices.
- [ ] Compute balance value; identify no-movement and slow-moving candidates by documented threshold; calculate turnover only with complete beginning/ending inventory and consumption for an explicitly comparable window, else `UNKNOWN`.
- [ ] Produce fictional CSVs, actual-output expected JSON and matrix tests; product-scoped gates, repeat build and reviewed product commit.

## Task 4: Purchasing

**Files:** `packages/skills/wangbin-purchase-analyzer/{SKILL.md,manifest.json,scripts/analyze_purchase.py,examples/*}`, `tests/test_purchase_analyzer.py`.

- [ ] Input order ID, material, supplier, order date, quantity, unit price, unit, specification, currency and tax treatment. Compare prices only within identical unit/spec/currency/tax groups, not across incompatible terms.
- [ ] Calculate `Decimal` purchasing totals by currency and documented period, supplier concentration, comparable price changes, supplier spread and anomalous candidates with explanatory thresholds; flag invalid/duplicate rows.
- [ ] Produce fictional CSV/expected JSON and test matrix; product-scoped gates, repeat build and reviewed product commit.

## Task 5: Sales

**Files:** `packages/skills/wangbin-sales-analyzer/{SKILL.md,manifest.json,scripts/analyze_sales.py,examples/*}`, `tests/test_sales_analyzer.py`.

- [ ] Input order ID, customer, product, order date, amount and currency; reject duplicates, invalid/negative amounts/dates. Keep currencies separate.
- [ ] Calculate `Decimal` period sales trend, product ranking, customer contribution/concentration; YoY/MoM only when both compared periods are documented complete, else `UNKNOWN`. Never label revenue profit.
- [ ] Produce fictional CSV/expected JSON and test matrix; product-scoped gates, repeat build and reviewed product commit.

## Task 6: Tender blocker and portfolio closure

**Files:** `reports/second-batch-release.md`, `reports/second-batch-portfolio.md`, optional tender `0.2.0` source only if real local fix is needed (never edit protected `0.1.0` ZIP).

- [ ] Audit actual existing tender ZIP member root, license and dependencies and check current official WorkBuddy Skill documentation. If no authorized private platform environment is confirmed, record exact `BLOCKED` reason instead of claiming success.
- [ ] Run full repository tests and Expert candidate integrity hash; run legacy CLI in isolated copy if fixed paths could overwrite prior assets. Confirm per-product CSV example outputs equal checked-in expected JSON, independent package SHA-256 and stable rebuild in a fresh copy.
- [ ] Record only observed local test/package outcomes and hashes, keeping platform metrics and costs `UNKNOWN`; create bounded reports, review staged allowlist and secret scan, commit reports locally. Recommend a third batch based on actual reuse potential and outstanding runtime limitations.
