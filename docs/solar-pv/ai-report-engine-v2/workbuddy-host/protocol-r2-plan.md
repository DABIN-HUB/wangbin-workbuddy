# CH08 Host Protocol R2 Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans`; implementation stays in this session on user-authorized main. Read-only diagnosis/review may be isolated; no parallel production edits.

**Goal:** Fix the bounded CH08 host output handoff without changing research structure, financial calculations or strict chapter acceptance.

**Architecture:** Retain chapter-result/2.0 and whole-chapter generation first. Add opt-in `prepare-r2` and `publish` around the existing host session: a model writes an immutable draft; installed Python validates the entire envelope and unchanged chapter rules, then atomically publishes a serialized response plus a completion receipt. No Python prose, claim synthesis, automatic semantic repair or section merger.

**Tech Stack:** Existing Python, Workspace/HostWorkspace, exact serialization, jsonschema and pytest; no dependency changes.

**Spec:** User contract `Hermes_SolarPV_WorkBuddy_CH08_Host_Protocol_R2.md`; frozen requirements 40, architecture 41; V2-EXC-004. New necessary publication contract will be recorded as V2-EXC-005 without editing frozen report-spec.

## Global constraints

- Scope SOLAR-PV-AI-REPORT-ENGINE-2.0.0, CH08, industrial_rooftop/utility_scale_ground only; no Phase E/F/G, client upload, dependency installation, Expert creation or push.
- Keep exact frozen hash `59e379906f6b83d91a76179f14fdc00e5c0dc9346ef5d272bbcf04da90df7532` and 18/100,13/26,469/89/281/189 counts.
- Bare numeric text remains rejected, including technical IDs; IDs belong to metadata or existing registered term slots, not a new regex exception. Natural reader-language instructions do not alter old output.
- Claims are a nonempty used subset of allowed IDs, maximum 24, not a quota. Each claim covers all slots in every linked paragraph and their real sources. SUPPORTED requires existing CALCULATED/VERIFIED facts; risk semantics unchanged.
- Old responses remain negative evidence only. No accepted old output, patched envelope, old authored prose or synthetic fixture can count as new model success.
- Every execution is bounded, preserving stdout/stderr/exit/JUnit and source identity. Protocol fixtures are explicitly NOT AI. Formal wb-quality is distinct from supplemental isolated technical review.

## R2-0: reproduced baseline

- [x] main HEAD `9faf44b86f4bb99a8a1021e1b35c70a4a49571e9`, tree `e72a6d03ac79268be358822d6c311e830a301d9e`, clean; remote main `d6b4043e19d391ce6055747ef058e46af1ffd3c0`, no fetch/merge.
- [x] Original archive 99 members/98 payloads, CRC and hashes verified; read-only diagnostic map produced and key counts independently recomputed.
- [x] Actual spec-check exit 0. Baseline host subset hit 180-second TIMEOUT after progress output, no final JUnit; do not count progress as passes. Split subsequent expensive real-canonical checks into bounded individual selections.
- [ ] Commit this failure baseline and implementation plan as non-release evidence before changing production.

Runtime evidence: `.runtime/solar-pv/ai-v2-host-protocol-r2-20261113-101239/`. `diagnosis/original-failure-map.json` contains exact pointers, tokens, fact/source gaps, risk errors and original UTF-8 byte spans. Diagnostic scripts must not modify source ZIP or accept old responses.

## R2-1: minimal compatible publication

Files: new `reporting/host_output.py`; modify `reporting/chapter_writer.py`, `reporting/host_session.py`; Skill `SKILL.md` and `references/host-orchestration.md`; new focused `tests/solar-pv/test_ai_host_output_r2.py`; V2-EXC-005.

- [ ] Add opt-in `prepare-r2`; legacy `prepare` and legacy report/ground-report remain unchanged. New request hash binds a delivery protocol and explicit writing guidance. Never edit an existing request.
- [ ] New `publish` reads only `<request-id>-draft.json`. A requested publication attempt consumes the existing reserved attempt: malformed/invalid output records a terminal failure and next generation needs a newly prepared request within the existing budget. Missing/incomplete output never produces a result.
- [ ] Revalidate request, authorization, canonical, source, model, expiry and upstream through existing `_request`/host checks. Check envelope/output budget and original `validate_chapter`, not Schema alone.
- [ ] Persist immutable publication intent with raw draft hash before publishing. Use existing Workspace atomic no-clobber publication for final response and receipt. Preserve raw draft, structured output digest and each paragraph hash. Serialization may change formatting only; no text/claim/metadata auto-correction.
- [ ] Recovery accepts only the same draft/request/response identities; existing conflicting response rejected. A crash after response publication can only finish the same receipt. No new model call, extra budget or duplicate result on recovery.
- [ ] R2 accept/resume require verified publication receipt; legacy requests do not. Checkpoint differentiates incomplete, pending publication, interrupted publication and published-but-not-accepted. Cancel still blocks publication/accept, without asserting remote cancellation.
- [ ] Skill explains natural reader text versus metadata, 1–24 actual claims rather than all allowed IDs, paragraph union/source coverage, evidence status, and non-optional professional review of undeclared free-text risks. No complete professional paragraph examples.

Design decision: first reduce claim inflation (about two thirds of old response bytes) while preserving all required evidence/tables. Do not implement section generation yet: no new approved host experiment demonstrates concise whole-chapter failure. If that later fails under its budget, stop and separately review same-request section orchestration rather than silently increasing calls. Manual mode without installed runtime may save a draft, but cannot claim atomic publication/contract validation.

## R2-2: bounded verification and review

- [ ] Focused fast tests with labeled protocol data: existing registered IDs in metadata/term slots; raw IDs and unknown IDs rejected; years/amounts/rates/zeros/negatives/full-width digits rejected; valid and invalid slots.
- [ ] Small claim coverage, two-slot paragraph/one-slot claim rejected, support state conflicts, source mismatch, unknown facts, risk mismatch and semantic-review boundary.
- [ ] Draft truncation, missing envelope layer, no-clobber, output limit, mutation, duplicate publication, crash recovery, consumed attempt, expired request, cancellation, wrong request/model and changed authorization/upstream.
- [ ] Actual real-canonical CH08 protocol checks split by project and operation, command limits 180–240 seconds, no repeated whole-repository suite. R13 styles/display/OMML use focused existing tests, no layout change.
- [ ] Supplemental isolated technical review of final diff and raw receipts; seek actual wb-quality capability. If unavailable, retain INDEPENDENT_QA_NOT_EXECUTED for that formal gate, not a fabricated pass.
- [ ] Verified implementation commit, then candidate/document closeout commit if needed; explicit staging only, no ignored evidence/ZIP staged.

## R2 delivery / stop

- [ ] New uniquely named Skill ZIP, preserve product ID/version/permissions and all older ZIPs; validate exact members, CRC, manifest and SHA, without overwriting catalog artifacts.
- [ ] Final change log, gates, source diff, JUnit/receipts, raw failure map, protection inventory, incremental Git bundle and evidence manifest/CRC/member hashes.
- [ ] Stop awaiting user approval of exact candidate SHA. New requests and WorkBuddy outputs are NOT_RUN until that approval; no reuse of expired requests. Final answer must explicitly say two new strictly accepted CH08 chapters have not yet been demonstrated.
