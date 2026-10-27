# WorkBuddy Product Factory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add per-product registration, initialization, validation, testing, deterministic packaging, evidence/metrics and portfolio reporting, and a genuinely runnable tender-analysis Skill candidate without changing existing published assets.

**Architecture:** Keep the four legacy `tooling` CLI commands intact. Add a separate `tooling.products` CLI, JSON registry/metrics, product-specific archive and evidence gates, reusable strict Expert profile, and a self-contained tender text analysis script. Keep inputs and outputs scoped by ID, preserve historical candidate bytes, and never promote local outcomes into platform verification.

**Tech Stack:** Python 3.11+ stdlib, existing PyYAML and document-engine dependencies; JSON and ZIP.

**Spec:** `docs/superpowers/specs/2026-10-27-product-factory-design.md`

## Global Constraints

- Preserve `wangbin-software-consultant` 1.0.0 source and ZIP SHA-256 `577f3089d2f4707178f44ba1e5c395a99853bb9558f3e8c0e752a0e6ba2e30de`.
- Do not modify legacy document assistant or CLI Connector candidate content; keep legacy four commands unchanged.
- New tests are explicitly requested; write only focused verification code in existing `tests/` or product-local tests, no new dependencies.
- Unknown metrics use UNKNOWN/NOT_AVAILABLE; software consultant review is USER_REPORTED_SUBMITTED without inferred approval.
- No platform upload/publish, push, PR or tag mutation. Local commit only after green verification.

---

## File map

- `tooling/expert_rules.py`: strict reusable prompt-only Expert profile, called by legacy wrapper and new factory.
- `tooling/product_factory.py`: registry/schema, per-product operations, archive, evidence, portfolio; may split into small modules if needed.
- `tooling/products.py`: isolated CLI entry point with `--root` and `--id`.
- `products/catalog.json`, `products/metrics.json`: five candidate records plus existing assets, unknown/real evidence.
- `packages/skills/wangbin-tender-analyzer/`: SKILL, references, analysis script, public fictional example and expected output.
- `tests/test_product_factory.py`, `tests/test_tender_analyzer.py`: focused new verification; do not edit legacy tests.
- `docs/product-factory.md`, `reports/product-factory-audit.md`, `reports/product-factory-release.md`: usage, audit, release evidence.

### Task 1: Registry and product-level CLI

**Files:** Create `tooling/product_factory.py`, `tooling/products.py`, `products/catalog.json`, `products/metrics.json`; Test `tests/test_product_factory.py`.

**Interfaces:** `load_catalog(root: Path) -> dict`, `get_product(root: Path, product_id: str) -> dict`, `validate_catalog(root: Path) -> list[str]`; CLI `python -m tooling.products list --root ...`.

- [ ] Step 1: Add focused tests for ID uniqueness, type/status/version validation, missing-data preservation and lookup; run `.venv/Scripts/python.exe -m pytest -q tests/test_product_factory.py` and observe expected missing-feature failure.
- [ ] Step 2: Populate eight independent existing/candidate records in JSON with accurate source/status evidence, no fabricated dates or metrics. Implement strict schema and collision checking, including existing unregistered package names; run focused tests.
- [ ] Step 3: Add independent CLI parser for `list`/`validate`, with `--root` and `--id` as needed; run CLI to inspect records.

### Task 2: Safe init and strict Expert profile

**Files:** Modify `tooling/phase5_expert_packager.py`, `tooling/generators.py`; Create `tooling/expert_rules.py`; add cases in `tests/test_product_factory.py`.

**Interfaces:** `validate_prompt_expert(source: Path, *, name: str, version: str, category: str) -> dict`; `init_product(root: Path, product_id: str, kind: str, connector_mode: str | None) -> Path`. Existing `validate_source(source)` remains callable.

- [ ] Step 1: Add regression assertions for 16-character Chinese display name rejection, bilingual fields, avatar and dependency rejection using disposable copies; add init-collision and per-type initialization checks; run focused tests for expected failure.
- [ ] Step 2: Extract strict reusable Expert validation preserving all phase5 checks; leave old fixed identity/version/category/member contract in phase5 wrapper, replacing only its common validation body. Keep legacy source and ZIP untouched.
- [ ] Step 3: Init Skill via existing generator, Expert/Connector via current templates; replace only safe identity fields, avoid fake auth claims and reject duplicates before writing; run focused tests.

### Task 3: Product-level validate/test/package/verify and release

**Files:** Extend `tooling/product_factory.py`, `tooling/products.py`, `tests/test_product_factory.py`.

**Interfaces:** `validate_product(root: Path, product_id: str) -> dict`, `test_product(root: Path, product_id: str) -> dict`, `package_product(root: Path, product_id: str) -> dict`, `verify_package(root: Path, product_id: str) -> dict`, `release_check(root: Path, product_id: str) -> dict`.

- [ ] Step 1: Add focused tests: independent package, deterministic bytes, symlink rejection, exact members/source readback, hash mismatch, no overwrite of conflicting output, no cross-product packaging; observe feature-missing failures.
- [ ] Step 2: Implement type-aware validation invoking existing structure validators and scanner, explicit allowlist of source files, stable ZIP timestamp/order/permissions and sidecar/manifest readback. Reject hidden/cache/private files and non-source tree links. No package operation rebuilds other products.
- [ ] Step 3: Add product-local test routing with an honest NOT_TESTED outcome when a product lacks tests, and separate local/package/platform release gates. Preserve archive and local sources on failure. Run focused tests and CLI scenarios.

### Task 4: Tender analyzer runnable MVP

**Files:** Create `packages/skills/wangbin-tender-analyzer/SKILL.md`, `scripts/analyze_tender.py`, references, example input and expected output; Test `tests/test_tender_analyzer.py`.

**Interfaces:** `analyze(text: str, source_name: str) -> dict`; CLI `python scripts/analyze_tender.py --input <authorized UTF-8 file>` emits JSON with eligibility, scoring, technical, dates, checklist, risks, evidence.

- [ ] Step 1: Write focused tests for four categories, source line quotes, ambiguous clauses, absent data, date text preservation, and explicit scanned/complex-layout limitations; observe expected missing-feature failure.
- [ ] Step 2: Implement a transparent conservative text-based extraction; use source line and exact excerpt only, no fabricated page or score. Unknown classification becomes 待核实 rather than PASS. Include source privacy boundaries and explicit executable usage in Skill.
- [ ] Step 3: Add fictional example and expected JSON; run analysis on example and compare to expected output; run focused tests. Parse only authorized files and do not log full input outside user output.

### Task 5: Metrics, portfolio and publication evidence

**Files:** Extend `tooling/product_factory.py`, `tooling/products.py`; Create `docs/product-factory.md`, `reports/product-factory-audit.md`, `reports/product-factory-release.md`; add focused tests.

**Interfaces:** `record_metric(root: Path, product_id: str, ...)->dict`, `portfolio_report(root: Path)->dict`; CLI `record`, `portfolio`, `release-check`.

- [ ] Step 1: Write tests for UNKNOWN/NOT_AVAILABLE, no divide-by-zero success rate, review evidence and cost totals, report with no deterministic commercial conclusion; observe expected failure.
- [ ] Step 2: Implement scoped metrics writes with atomic replacement and explicit status/evidence provenance, meaningful rates only from observed outcomes; human-readable portfolio comparison and missing-data notes.
- [ ] Step 3: Document command examples, audit findings, reuse decisions, per-product release gates and required platform/manual steps.

### Task 6: Acceptance and local commit

**Files:** Update only implementation documents and reports with observed command results.

- [ ] Step 1: Run new focused tests then legacy `.venv/Scripts/python.exe -m pytest -q`, the four legacy CLI commands and new per-product init/validate/test/package/verify/release-check/portfolio scenarios. Report exact failures and skips; do not fabricate PASS.
- [ ] Step 2: Recheck Expert ZIP baseline hash, directory/git diff, deterministic rebuild SHA-256, ZIP readback/sidecar, identity collisions, report evidence and license/dependency boundaries. Record final artifact path/hash.
- [ ] Step 3: `git diff --check`; stage explicit reviewed paths, review staged names/check, commit `feat: add reusable WorkBuddy product factory and tender skill` locally only if key acceptance checks pass. Read back commit SHA and status. Never push/PR/tag.
