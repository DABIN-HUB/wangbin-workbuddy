# wangbin WorkBuddy Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and locally verify a real `wangbin AI Document Assistant` candidate package with a secure MarkItDown-based document engine, reusable WorkBuddy asset templates, executable validation/testing/packaging commands, and a release-candidate ZIP.

**Architecture:** Keep the WorkBuddy-facing candidate assets independent from a Python document engine and from the local engineering toolchain. The engine exposes structured single-file and batch APIs, applies security policy before parsing, and uses MarkItDown as the first parser. The tooling validates manifests and paths, runs real tests, and packages only an explicit allowlist; platform compatibility remains a separately reported gate.

**Tech Stack:** Python 3.11+, MarkItDown with only required format extras, standard library (`argparse`, `zipfile`, `json`, `hashlib`, `pathlib`, `tempfile`), `pytest` for explicitly requested real tests, `openpyxl` only where needed for safe spreadsheet export, Markdown/YAML/JSON metadata, ZIP release packages.

**Spec:** `docs/superpowers/specs/2026-10-26-workbuddy-phase1-design.md`

## Global Constraints

- Project root is exactly `F:/ideaWorkSpace/wangbin-workbuddy`; do not create a nested same-name directory.
- Product, package prefix, and developer are `wangbin`; do not use any legacy brand identifier.
- Do not run `git commit`, `git push`, `git reset`, or branch switching.
- Do not log into WorkBuddy, publish, set prices, enable monetization, or deploy production.
- Do not claim WorkBuddy compatibility until a real authorized platform run succeeds.
- Officially unconfirmed platform requirements must be labeled `BLOCKED` or `待确认`, never invented.
- The document engine must really process PDF, DOCX, XLSX, PPTX, HTML, TXT, and Markdown files.
- User explicitly requested tests, so real test fixtures and test code are in scope; do not replace engine tests with mocks.
- Do not add Docling unless a real MarkItDown capability gap is demonstrated and recorded.
- Redact secrets, credentials, connection strings, and user paths in reports.

---

### Task 1: Establish and self-review the approved design

**Files:**
- Create: `docs/superpowers/specs/2026-10-26-workbuddy-phase1-design.md`
- Create: `docs/superpowers/plans/2026-10-26-workbuddy-phase1.md`

**Interfaces:**
- Produces the architecture and implementation boundaries used by every later task.

- [x] Record scope, non-goals, platform-unknown policy, component boundaries, data flow, security controls, testing, and release gates in the design document.
- [x] Map each requested deliverable to a later implementation task; exclude Git writes and platform publishing.
- [x] Self-review for placeholders, contradictions, missing seven-format coverage, accidental legacy naming, and claims of platform compatibility.

**Verification:** Search the design and plan for placeholders and unowned requirements; all must be absent or intentionally explained. Read both files before starting implementation.

### Task 2: Verify official WorkBuddy rules without guessing

**Files:**
- Create: `docs/workbuddy-platform-spec.md`
- Create: `reports/platform-research.json`

**Interfaces:**
- Produces a structured `requirements[]` list with `topic`, `source_url`, `checked_at`, `status`, `evidence`, and `implementation_impact`.
- Later validators consume the status values `PASS`, `BLOCKED`, `NOT_TESTED`, or `FAIL`.

- [ ] Read the official root, Skill, Expert, Connector, monetization, developer agreement, developer enrollment, asset publishing, authentication, and version-update pages using search/browser fallbacks when direct extraction fails.
- [ ] Record an entry for every requested topic, including personal developer eligibility, package root layout, required fields, runtime, MCP/CLI rules, file permissions, external APIs, open-source licenses, paid/free restrictions, and platform testing.
- [ ] Mark unreadable or undocumented claims `BLOCKED`; do not infer a package layout from other platforms.
- [ ] Write the implementation consequence beside each requirement, distinguishing confirmed rules from local candidate conventions.

**Verification:** Re-run the URL list through the available browser/search tool; compare the document's status table to the JSON report; ensure no undocumented WorkBuddy field appears in a package manifest as an official field.

### Task 3: Create the Python project and dependency boundary

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `.gitignore`
- Create: `README.md`
- Create: `services/document-engine/src/wangbin_document_engine/__init__.py`
- Create: `services/document-engine/src/wangbin_document_engine/py.typed`
- Create: `tooling/__init__.py`
- Create: `tooling/__main__.py`
- Create: `tooling/config.py`

**Interfaces:**
- Package import: `from wangbin_document_engine import DocumentEngine, SecurityPolicy`.
- CLI entry: `python -m tooling <validate|test|package|release-check>`.
- Configuration object: `ProjectConfig(root: Path, reports_dir: Path, dist_dir: Path)`.

- [ ] Set project metadata to `wangbin-workbuddy`, Python floor to 3.11, and product constants to `wangbin`/`1.0.0`.
- [ ] Pin or constrain MarkItDown only after verifying the available release and required extras; do not add Docling by default.
- [ ] Add only dependencies needed for real parsing, spreadsheet export, YAML validation, and the explicit pytest suite.
- [ ] Define package discovery so the engine works from an editable install and from the repository CLI.
- [ ] Configure `.gitignore` for virtual environments, caches, reports that contain local paths, generated outputs, and temporary processing directories while retaining release evidence explicitly copied to `reports/`.

**Verification:** Create a clean virtual environment if available, install declared dependencies, import the engine, and run `python -m tooling --help` without writing outside the project and scratch directories.

### Task 4: Implement security policy and structured result types

**Files:**
- Create: `services/document-engine/src/wangbin_document_engine/models.py`
- Create: `services/document-engine/src/wangbin_document_engine/security.py`
- Create: `services/document-engine/src/wangbin_document_engine/errors.py`
- Create: `services/document-engine/src/wangbin_document_engine/paths.py`

**Interfaces:**
- `SecurityPolicy(max_file_bytes: int, max_files: int, max_batch_bytes: int, max_uncompressed_bytes: int, max_zip_entries: int, timeout_seconds: float)`.
- `SecurityPolicy.validate_input(path: Path, input_root: Path) -> Path`.
- `SecurityPolicy.validate_container(path: Path) -> None`.
- `DocumentResult` fields: `source_name`, `source_type`, `status`, `size_bytes`, `text`, `metadata`, `sections`, `quality_notes`, `error`, `duration_ms`.
- `BatchResult` fields: `status`, `items`, `success_count`, `failure_count`, `duration_ms`.

- [ ] Resolve paths and reject missing paths, directories, symlinks, paths outside the allowed input root, and files over configured limits.
- [ ] Validate the batch count and cumulative bytes before processing.
- [ ] Inspect Office ZIP central directories and reject excessive entries or declared uncompressed sizes before handing files to a parser.
- [ ] Use stable error codes and redacted messages; never include secrets or full user paths in serialized results.
- [ ] Sanitize output names and prevent output collisions from overwriting source files.

**Verification:** Exercise these checks through direct CLI probes and later real tests for traversal, missing input, symlink, oversized file, and oversized Office container.

### Task 5: Implement the real MarkItDown adapter and document engine

**Files:**
- Create: `services/document-engine/src/wangbin_document_engine/markitdown_adapter.py`
- Create: `services/document-engine/src/wangbin_document_engine/engine.py`
- Create: `services/document-engine/src/wangbin_document_engine/metadata.py`
- Create: `services/document-engine/src/wangbin_document_engine/serialization.py`

**Interfaces:**
- `MarkItDownAdapter.convert(path: Path) -> ParsedDocument`.
- `DocumentEngine.parse_file(path: Path, input_root: Path, output_dir: Path | None = None) -> DocumentResult`.
- `DocumentEngine.parse_many(paths: Sequence[Path], input_root: Path, output_dir: Path | None = None) -> BatchResult`.
- `serialize_result(result: DocumentResult | BatchResult, destination: Path) -> None`.

- [ ] Call the installed MarkItDown library for the seven required formats; do not implement extension-only renaming or fake text.
- [ ] Map detected MIME/extension and parser metadata into the stable result model.
- [ ] Extract headings/sections only when the parser exposes reliable Markdown structure; record a quality note when layout fidelity is limited.
- [ ] Catch parser failures per file and continue batch processing.
- [ ] Ensure input files remain read-only and output is written only beneath the selected output directory.
- [ ] Record real parser version and engine version in reports.

**Verification:** Process one real fixture of each required format and inspect non-empty extracted text and source metadata; keep any format limitations in the report.

### Task 6: Implement spreadsheet operations and safe exports

**Files:**
- Create: `services/document-engine/src/wangbin_document_engine/spreadsheets.py`
- Create: `services/document-engine/src/wangbin_document_engine/exports.py`

**Interfaces:**
- `SpreadsheetService.inspect(path: Path, input_root: Path) -> SpreadsheetSummary`.
- `SpreadsheetService.deduplicate(path: Path, input_root: Path, output_dir: Path, keys: Sequence[str] | None = None) -> ExportResult`.
- `sanitize_cell_for_csv(value: object) -> str`.

- [ ] Read worksheet names, headers, row counts, duplicates, and null counts without executing formulas.
- [ ] Deduplicate rows without modifying the source workbook.
- [ ] Write a new CSV or XLSX result after validating that it can be reopened.
- [ ] Escape formula-like leading characters in CSV/worksheet outputs to prevent spreadsheet formula injection.
- [ ] Reject output paths that collide with source paths or leave the allowed output root.

**Verification:** Run deduplication against a real XLSX fixture containing duplicate rows, blanks, and formula-like strings; reopen the generated output and compare counts.

### Task 7: Build executable validation, test, packaging, and release-check commands

**Files:**
- Create: `tooling/cli.py`
- Create: `tooling/validators/__init__.py`
- Create: `tooling/validators/project_validator.py`
- Create: `tooling/validators/secret_scanner.py`
- Create: `tooling/validators/zip_validator.py`
- Create: `tooling/test_runner.py`
- Create: `tooling/packager.py`
- Create: `tooling/release_check.py`
- Create: `tooling/generators.py`

**Interfaces:**
- `validate_project(root: Path) -> ValidationReport`.
- `scan_for_secrets(root: Path) -> list[Finding]`.
- `build_candidate_zip(root: Path, destination: Path) -> PackageManifest`.
- `validate_candidate_zip(zip_path: Path) -> PackageManifest`.
- CLI subcommands return nonzero on a failed gate and write both JSON and Markdown reports.

- [ ] Validate required files, version format, JSON/YAML syntax, referenced resources, dependency/license manifests, path safety, and forbidden secret patterns.
- [ ] Keep the secret scanner conservative and report redacted finding locations without copying credential contents.
- [ ] Run the actual pytest command and capture command, exit code, duration, and per-test summary.
- [ ] Package from an explicit allowlist into a temporary directory, reject absolute/traversal ZIP members, and validate the ZIP after creation.
- [ ] Generate a self-contained candidate package without tests, caches, local reports, credentials, or unrelated repository files.
- [ ] Make `release-check` aggregate all gates and emit `PUBLISH_READY=BLOCKED` when platform runtime or eligibility is unconfirmed.

**Verification:** Run every subcommand from the repository root and from a separate current working directory; inspect generated JSON/Markdown reports and the ZIP member list.

### Task 8: Create the first product Skill and reusable templates

**Files:**
- Create: `packages/skills/wangbin-document-assistant/SKILL.md`
- Create: `packages/skills/wangbin-document-assistant/manifest.json`
- Create: `packages/skills/wangbin-document-assistant/references/task-protocol.md`
- Create: `packages/skills/wangbin-document-assistant/references/privacy.md`
- Create: `packages/skills/wangbin-document-assistant/scripts/run_document_engine.py`
- Create: `packages/skills/wangbin-document-assistant/templates/summary-output.md`
- Create: `packages/experts/wangbin-expert-template/EXPERT.md`
- Create: `packages/experts/wangbin-expert-template/manifest.json`
- Create: `packages/connectors/wangbin-connector-template/CONNECTOR.md`
- Create: `packages/connectors/wangbin-connector-template/manifest.json`

**Interfaces:**
- Skill task protocol maps natural-language intents to `parse`, `batch`, `spreadsheet_deduplicate`, and `structured_summary_input` operations.
- Template manifests use only confirmed platform fields; local-only fields are namespaced as internal metadata and excluded from official claims.

- [ ] Document the seven-format support, triggers, input requirements, processing flow, output schema, failure handling, unsupported scenarios, and privacy policy.
- [ ] Add examples for the required Chinese natural-language prompts without claiming unsupported model behavior.
- [ ] Keep credentials out of scripts and describe future connector authentication by environment/hosted secret mechanism only.
- [ ] Generate templates through the reusable generator and validate them with the same project validator.
- [ ] Include product copy, usage instructions, FAQ, update log, third-party notices, and explicit local/platform status distinctions.

**Verification:** Run `validate` against each asset directory and inspect the candidate package manifest for absent unconfirmed official fields.

### Task 9: Generate real fixtures and run the requested test matrix

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_document_engine_real_formats.py`
- Create: `tests/test_batch_processing.py`
- Create: `tests/test_spreadsheets.py`
- Create: `tests/test_security.py`
- Create: `tests/test_tooling.py`
- Create: `tests/fixtures/` containing generated PDF, DOCX, XLSX, PPTX, HTML, TXT, Markdown, empty, damaged, and filename edge-case files.
- Create: `reports/test-results.json`
- Create: `reports/test-results.md`

**Interfaces:**
- Fixture generation is deterministic and local; tests invoke the real installed parsers and engine.
- Test report enumerates T01–T20 and maps each to a concrete command and result.

- [ ] Generate real files using appropriate local libraries or minimal binary fixtures; do not create Mock parser objects.
- [ ] Verify all seven required formats have non-empty, expected marker text after parsing.
- [ ] Cover batch partial failure, empty input, mismatched extension, corruption, size limits, Chinese/special filenames, missing files, conversion reopen, spreadsheet deduplication, traversal, metadata, and ZIP structure.
- [ ] Run the full suite through `python -m tooling test`, not only direct individual tests.
- [ ] Mark unavailable external/platform/model tests as `SKIP`, `BLOCKED`, or `NOT_TESTED` with reasons; never count them as local passes.

**Verification:** Compare the enumerated T01–T20 rows to the requested list, ensure no row is silently omitted, and inspect real output files in a separate output directory.

### Task 10: Write project documentation, licenses, and roadmap

**Files:**
- Create: `docs/architecture.md`
- Create: `docs/development-guide.md`
- Create: `docs/publishing-guide.md`
- Create: `docs/security-guide.md`
- Create: `docs/product-roadmap.md`
- Create: `docs/third-party-notices.md`
- Create: `docs/release-notes-1.0.0.md`
- Create: `docs/market-copy.zh-CN.md`
- Create: `docs/market-copy.en-US.md`

**Interfaces:**
- Documentation references the same CLI commands, product constants, gate names, and platform status vocabulary as the implementation.

- [ ] Explain local setup, supported Python versions, dependency installation, commands, output directories, and troubleshooting.
- [ ] Explain platform upload steps only as manual instructions and explicitly state that no upload has occurred.
- [ ] Document file security limits, data flow, no-network behavior, macro/formula policy, cleanup, and known parser limitations.
- [ ] Describe the five-product roadmap with user group, MVP, reusable components, review risk, difficulty, monetization possibility, and maintenance cost without asserting platform approval.
- [ ] Generate third-party license notices from the actual dependency lock/metadata; redact machine-specific paths and secrets.

**Verification:** Check all paths and command examples against the files actually present; run a link/path scan on local references.

### Task 11: Produce and validate the release candidate

**Files:**
- Create: `dist/wangbin-document-assistant-1.0.0-candidate.zip`
- Create: `dist/wangbin-document-assistant-1.0.0-candidate.sha256`
- Create: `dist/wangbin-document-assistant-1.0.0-candidate.manifest.json`
- Create: `reports/release-check.json`
- Create: `reports/release-check.md`
- Create: `reports/acceptance-report.md`

**Interfaces:**
- ZIP contains only the candidate asset root and explicitly allowed runtime resources; it does not contain `.git`, caches, credentials, tests, or local machine reports.
- Manifest records relative path, byte size, SHA-256, and package role for every member.

- [ ] Run `python -m tooling release-check` after all code, docs, fixtures, and tests exist.
- [ ] Reopen the generated ZIP, validate every member and hash, and compare it to the manifest.
- [ ] Calculate SHA-256 through an actual command and record the exact file size.
- [ ] Write the acceptance table with the required PASS/FAIL/BLOCKED/NOT_TESTED vocabulary, local test totals, real processing result, known limitations, and unresolved risks.
- [ ] State `PUBLISH_READY` according to the platform gate, not merely local test success.

**Verification:** Perform a clean extraction into the scratch directory and run the candidate's documented local validation command; do not upload it.

### Task 12: Final closure review without Git mutation

**Files:**
- Modify only if needed: `README.md`, reports, or docs found inconsistent during closure.

**Interfaces:**
- Final response must include the absolute project path, structure, commands, test evidence, ZIP path/size/hash, platform status, unresolved blockers, and Git status.

- [ ] Run `git status --short --branch` and `git diff --stat`/`git diff --` without staging or committing.
- [ ] Check all generated paths, report totals, ZIP hash, and product naming for consistency.
- [ ] Confirm no credentials or legacy brand identifiers are present in tracked project content.
- [ ] Update the task checklist only after real command output verifies each deliverable.
- [ ] Report any failed or blocked gate honestly and give the next phase's smallest actionable recommendation.

**Verification:** The final report and final response must agree on counts, statuses, paths, and hashes; no claim of platform approval may appear unless a real authorized test exists.
