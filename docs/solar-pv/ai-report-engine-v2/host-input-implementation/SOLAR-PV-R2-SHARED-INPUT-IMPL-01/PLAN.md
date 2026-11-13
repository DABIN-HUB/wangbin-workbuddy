# SOLAR-PV-R2-SHARED-INPUT-IMPL-01 — approved local implementation plan

## Authority and real baseline

User task source: `C:/Users/wangbin/AppData/Local/hermes/attachments/pasted_content_2026-11-13_08-36-48-039_f370d7.txt` (full requirements; read before implementation). Root `AGENTS.md` and full `agent.md` apply to every participant. Scope follows user task over generic skill workflows.

Live start HEAD `9cf8cdae81402119ccc76d697346289b1b361e89`, main, clean staged/unstaged/untracked. Read-only origin main now matches this HEAD (different from previous audit remote baseline; no sync performed). Previous production baseline remains `71ba9b8b2ed6ba7d96ad6619a29a44875d2a6c9a`. User expressly authorizes local stage commits in this worktree. No new worktree, merge or cleanup of old worktrees.

Historical EXC006 stays `PROPOSED_NOT_APPROVED` unchanged. Approved subset ONLY: shared-object representation module, necessary lifecycle/CLI/wrapper source integration, directly related offline production tests, independent QA, source-review archive and local allowlist commits. No typed rows production selector, new host/model task, old input re-delivery, install/download/wheel build/Skill packaging or replacement, Connector readiness/distribution, financial calculation, canonical/formula/Schema/validator changes, Office rendering, Phase E/F/G, push/merge/reset/rebase.

## Global constraints and task ownership

One developer owns all production/test edits. Manager owns coordination, protection, packaging, final state. Quality independently reviews frozen code and runs bounded focused checks, writes its own verbatim findings and payload confirmation. No child spawns subagents. All changes outside approved paths require a concrete blocked dependency report, not silent expansion.

Runtime: `.runtime/solar-pv/SOLAR-PV-R2-SHARED-INPUT-IMPL-01/`. New docs only this directory. Both were absent before creation. Old audit, old requests/expiry, original views, dist, installed Skill and other worktrees protected. `protected-files-before.json` hashes current tracked plus previous audit runtime/originals; reconcile permitted source edits separately. History R8–R13 uses prior metadata-only inventory, not content proof. Installed inventory has 22 actual files; distinguish 21 package payload members from extra metadata, do not rewrite it.

Use existing root `.venv/Scripts/python.exe` (3.12 with pytest/Pillow/docx/yaml/jsonschema) for developer source tests. This does not prove normal installation. Engine `.venv` lacks these modules and Hermes Python lacks pytest. No dependency repair or PYTHONPATH masquerading as installation. Wrapper retains `sys.executable -I` and environment cleaning.

Every executable verification uses runtime `record_command.py` with unique role/label, input/code snapshot hashes, full stdout/stderr, real exit, timestamps and timeout <=120s. Cumulative all-role cap 900s. Allocate developer <=420s, quality <=300s, manager <=120s (leave reserve). Recorder is a local diagnostic, not product code. No full-repo pytest or financial replay. Preserve failures/timeouts and JUnit. Do not aggregate historical counts.

## Plan

1. Developer reads full user requirements, audit RESULT/EXC006/QA_INDEX/QA provenance/original report/NEXT, actual reporting callchain, local instructions, 40/41 and EXC004/005; read minimal old frozen material using saved hashes where unchanged. Write detailed protocol decisions and requirement-to-case map before code.
2. Implement explicit opt-in immutable request policy, exact-number bounded shared view codec, detached manifest, trusted-original reconstruction and common validation for checkpoint/publish/verify/accept/resume/cache. Full legacy default hash and byte-budget semantics unchanged. Deterministic generation and exclusive no-clobber inside existing locks; no recovery/autofill. Cache-depth/expanded UTF-8/pool/ref/node/chain bounds enforced before amplification. Do not copy audit script wholesale or use partial closure helper as permissions gate.
3. Save reproducible directly relevant tests including both historical requests, NOT_AI new-workspace lifecycle, QA-F01 four resealed cases, resource-depth counterexample, no-clobber/partial/expiry/accepted-after-expiry/cancel/budgets/cache. Test fixtures must not run financial calculation or alter historical copies to forge fresh requests. Record real failures and final result. Freeze source/test snapshot and local candidate commit with exact allowlist.
4. Independent quality reviews actual full diff plus unchanged trust entrypoints, independently executes necessary scoped tests within budget, reports spec/code quality and exact code tree identity. Developer fixes any substantive findings; quality rechecks changed risks. Old audit PARTIAL never changes.
5. Developer/manager prepare SOURCE/REVIEW ONLY payload with source diff and source/test files, protocol, requirements/cases, command/JUnit receipts, new views and binding measurements, original QA and source snapshot. No package metadata pretending to be an install artifact; large original files external with hashes. Quality approves a fixed exact payload hash index and privacy. Its confirmation itself and deterministic manifest/archive identity are explicitly excluded from self-reference.
6. Manager verifies approved payload bytes unchanged, adds original quality confirmation and deterministic manifest only, verifies ZIP exact set, unique/safe paths, sizes/SHA/CRC. Local final docs commit allowlist, final Git status/diff and protection checks; no push. Archive identity/final HEAD stored runtime to avoid tracked self-reference.

## Interface/cross-task preflight scan

| Tasks sharing interface | Producer → consumer | Constraint/result |
|---|---|---|
| 1→2 | protocol decision → codec/lifecycle | Authoritative full user task; preserve legacy and expiry semantics; resolve against actual code |
| 2→3 | deterministic views → tests | Tests compare full trusted bytes incl LF; original request budget excludes final LF |
| 2→4 | frozen source → independent quality | One writer, no concurrent code edits during review |
| 3→4 | receipts/case map → QA | Independent review not a restatement; bounded new focused execution |
| 4→5 | finding fixes → approved payload | Changed code rechecked by quality; no developer-only remediation claim |
| 5→6 | fixed file SHA allowlist → archive | Do not mutate approved payload; exclude confirmation/archive self-reference |
| Task 1 | scope vs reading | Reuse unchanged large inventories, no generic re-audit stall |
| Task 2 | opt-in vs default | No default fields/hash changes; no skip-check public toggle |
| Task 3 | offline tests vs no host/financial work | Explicit NOT_AI lifecycle fixtures from snapshots and controlled current clock |
| Task 4 | local QA vs historical gates | Local result separate from old PARTIAL/host/professional/install gates |
| Task 5 | complete sharing vs original privacy | Derivatives separately hashed, raw originals untouched |
| Task 6 | local commit vs release | Source candidate only, no wheel/Skill ZIP/install/publication |

No cross-task contradiction found. User-selected runtime replaces generic skill scratch workspace; all evidence retained under authorized paths, no generic workspace deletion.

## Status ledger

- Preflight complete: live git/remote, existing env modules and protection inventories recorded in commands/manager-preflight.* (20.720157700125128s).
- Developer candidate44c26c9 and tests-only remediationa7dbe7c frozen. R1 quality PARTIAL retained; R2 quality PASS_LOCAL_QA_NOT_AI_NOT_HOST_E2E closes QAI-R1-01, seven non-test source files unchanged. Reports/commands in independent-qa and independent-qa-r2, original failures/timeouts retained. Final docs and fixed payload are separately reviewed before deterministic ZIP sealing; no production/test edits after R2 review. Exact historical gate values remain verbatim in RESULT.
