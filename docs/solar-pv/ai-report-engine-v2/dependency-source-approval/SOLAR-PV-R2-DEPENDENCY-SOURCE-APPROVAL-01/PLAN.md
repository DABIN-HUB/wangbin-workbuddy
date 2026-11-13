# Dependency source approval execution plan

> Execute this approved metadata-only plan with one document/script writer and a separate independent QA worker. All participants must read `AGENTS.md`, the full root `agent.md`, the frozen report requirements and the current authorization before work.

**Task:** `SOLAR-PV-R2-DEPENDENCY-SOURCE-APPROVAL-01`
**Goal:** Obtain real official release metadata, compatibility and license evidence for the historical missing dependencies, then deliver a non-installable candidate lock and controlled future acquisition/install plan.
**Architecture:** Reuse and hash-bind the previous 12-target observed graph and the existing 0.3.2 wheel. Preserve historical evidence. Collect only public metadata/documents into a new ignored runtime directory, derive deterministic candidate files with existing tools, freeze them for genuinely separate QA, commit only this task's useful documents/scripts, and seal a source-and-dependency review archive after approval.
**Stack:** Existing Python/standard library; already available `packaging` only if confirmed. No dependency acquisition.
**Authorization:** User attachment `pasted_content_2026-11-13_13-57-11-734_2602a1.txt`.

## Global constraints

- Expected baseline HEAD `177951690bab2f0a11a75be15e2204be4820409c`, branch `main`; live state overrides historical claims and differences require review.
- Protected wheel `wangbin_solar_pv_input-0.3.2-py3-none-any.whl`, 557392 bytes, SHA-256 `cd7be44ca5350da87c4760898ddeb46b8a73646d8f2f8de6be61e48cca9f7808`; never rebuild or overwrite.
- Existing review ZIP SHA-256 `fd4d52d6b6725902439779956c49b0fa8560839c562fa5ffaba605798198ae4c`; reuse identities, not repeat every old wheel check.
- No wheel/sdist/install-script download, pip install/download, build-tool installation, venv/global changes, product source/Connector/Skill changes, model tasks, CH08, report generation, publish, push/merge/rebase/reset, or Phase E/F/G.
- Public metadata API bodies and license/document text may be retrieved; reject release-archive endpoints and redirects in collectors. Record HTTP status, original bytes/SHA, and exact URL. Record official hashes separately from actual local hashes. Third-party artifacts remain `ARTIFACT_NOT_ACQUIRED`.
- Skill Bash and Connector interpreters remain UNKNOWN until directly evidenced; Windows x86_64 CPython 3.12 is a conditional research target, not an observed formal deployment.
- Candidate lock is always `PROPOSED_NOT_INSTALLABLE`; dependency closure remains BLOCKED. Preserve every historical gate and the 12 external baselines, 11 optional fixtures and incomplete historical replay.
- Each recorded command has a hard cap of 1–120 seconds. Task-wide recorded execution budget 1200 seconds including failures; allocate manager 180, source analyst 300, license analyst 240, developer 220, independent quality 200, reserve 60. Delegation wall time is not command time. Collectors must split bounded network batches; stop at their role budgets.
- Preserve original inputs before every recorded execution, stdout/stderr and failed receipts; do not patch a previously executed script without retaining its exact executed bytes.
- No new production tests or product changes. User-authorized negative checks only for this task's candidate-lock validator; no broad pytest.

## Paths and ownership

- `DOC = docs/solar-pv/ai-report-engine-v2/dependency-source-approval/SOLAR-PV-R2-DEPENDENCY-SOURCE-APPROVAL-01/`.
- `RUN = .runtime/solar-pv/SOLAR-PV-R2-DEPENDENCY-SOURCE-APPROVAL-01/` (ignored local evidence and review artifacts).
- Manager: this initial PLAN and `RUN/manager-*`, command recorder, baseline/target/protection evidence and final archive readback. After handoff, no concurrent DOC edits.
- Source analyst: only `RUN/source-research/` plus its `analyst-*` command receipts. Official metadata and source-side tag/resolution research; no Git writes.
- License/identity analyst: only `RUN/license-identity/` plus `license-*`/`identity-*` receipts. License documents, document-wheel dual identity and external-baseline research; no Git writes.
- Developer: sole subsequent writer of DOC and DOC/scripts, derived RUN/candidate files and payload scripts, explicit allowlist local commits. Never edits prior task assets.
- Quality: only new `RUN/independent-qa/`, explicit confirmation and `quality-*` receipts. No candidate, document, source or Git edits.

## 当前候选交接状态（唯一 writer 更新）

- 基线/保护、官方来源与许可身份研究已完成；manager 原证不冒充独立 QA。
- 十二份正式文件已生成。CANDIDATE_LOCK.json / DEPENDENCY_RESOLUTION.json 为精简身份入口，完整机器锁/图/下载计划仅留 RUN/candidate，避免把大生成 JSON 入库；入口绑定路径/size/SHA，并非缺省占位。
- 生成及冻结输入重建校验已真实执行；AST/隐私/卫生/保护/精确暂存与本地候选提交的最终门禁，以 RUN/commands/developer-* 和 RUN/developer-final-state.json 实测读回为准。
- 独立 QA 为 NOT_RUN / PENDING；本轮冻结后交给独立角色，不自行签 QA，不封 ZIP。后续独立报告纳入与最终 payload 必须再次限定复审。
- 候选锁始终 PROPOSED_NOT_INSTALLABLE，所有分发/许可/实际运行阻断不变；本轮本地提交使用显式 wip 语义。

## Ordered execution and acceptance

1. [x] **Baseline and protection.** Record all requested Git commands and remote main without sync; inventory tracked/untracked/ignored paths without reading credentials; verify wheel/old ZIP/index/approved-source identities; capture current tracked and historical evidence hashes, installed exact membership/hashes and R8–R13 metadata-only identities. Probe live OS/CPU/client executable/process versions and known Python identities without invoking Connector or model tasks.
2. [x] **Official source research.** Extract all 12 graphs' real missing normalized name/version pairs; query exact-version official PyPI JSON, preserving successful and failed responses. Also obtain official project metadata when an exact release is absent, but do not silently substitute a version. Record files, official hashes, Requires-Python/Dist, extras, markers, time, yanked and tags; include separately scoped build-backend evidence. Deduplicate by exact filename/hash/URL, not 42×12. Preserve all incompatibilities and metadata discrepancies.
3. [x] **License and identity research (parallel independent domain).** Read version-specific official license/NOTICE sources, bundled-component obligations and uncertainty for every node; do not infer wheel licensing from a badge. Compare both document 1.2.0 wheels (bytes, payload/METADATA/RECORD/LICENSE, source lineage and build receipts) without selecting by time. Bind external baseline acquisition/checksum plan and optional-fixture semantics.
4. [x] **Generate candidate artifacts.** After reading both analyst outputs, the sole writer creates the requested twelve DOC deliverables plus machine source/index/license/compatibility/download plans and reusable generation/validation scripts. Resolve official-versus-installed metadata conflicts explicitly; never fill missing release records. Include all active direct/transitive/extras/marker edges and all targets. Provide a concrete conditional first-target table and exact available file list, with gaps BLOCKED. Future offline install instructions are text only, never executed this round.
5. [ ] **Freeze and independently verify.** Hash-freeze candidate documents/scripts and exact sharing allowlist. Independent QA re-reads original public metadata, historical graph and generated outputs, independently evaluates tags/markers/constraints and exercises the required negative rejection cases (name/version/SHA, tags, missing edge/marker, acquired/hash, license/source/READY/closure). Preserve real failure results; remediate only by sole writer and obtain bounded re-review when needed.
6. [ ] **Closeout.** Copy independent QA verbatim into DOC; keep its frozen-snapshot scope explicit. Verify new documentation, citations/source references, privacy, task script syntax, hygiene and exact staged blobs/normalization; commit only reviewed task paths. Freeze final sharing tree and get scoped independent payload approval after substantive closeout edits. Then build new `SOURCE_AND_DEPENDENCY_REVIEW_ONLY` ZIP, append only declared QA/manifest/final-state records, read every member back (safe unique paths/type/CRC/size/SHA/exact set), verify old protected items and final Git state, and report actual command budget and counts.

## Required deliverables

`PLAN.md`, `RESULT.md`, `BASELINE_AND_ARTIFACT_IDENTITY.md`, `TARGET_RUNTIME_MATRIX.md`, `DEPENDENCY_SOURCE_MATRIX.csv`, `THIRD_PARTY_LICENSE_MATRIX.md`, `DEPENDENCY_RESOLUTION.json`, `CANDIDATE_LOCK.json`, `WHEELHOUSE_AND_INSTALL_PLAN.md`, `DOCUMENT_CLI_ARTIFACT_IDENTITY.md`, `QUALITY_REPORT.md`, `NEXT_GATE.md`.

Also retain exact official metadata/document evidence, their provenance/redaction index, candidate/download/license/compatibility JSON, parser scripts, all actual execution receipts, negative-check results, independent QA originals, final frozen payload index, ZIP/manifest/SHA and final Git/protection receipts. Raw public metadata may include unnecessary email fields: preserve raw locally and share separately hashed minimal derivatives with explicit lineage; never mislabel a derivative as raw.

## Final verdict discipline

Complete official research can yield `SOURCE_RESEARCH_COMPLETE` + `ARTIFACT_ACQUISITION_NOT_AUTHORIZED` + `DEPENDENCY_CLOSURE_BLOCKED`. Unconfirmed exact releases must be individually reported as partial source research, not hidden behind a completion label. A public metadata hash is only `OFFICIAL_HASH_RECORDED`, never `ARTIFACT_HASH_VERIFIED`. Independent QA is distinct from developer self-check. The ZIP is not a Skill install package, complete wheelhouse, deployable distribution, release or complete historical backup.
