# SYNTHETIC full-case evidence v1.0.0

This case is a 25-year fictional model, NOT a real approval or signed engineering study.
The ordinary project receipt is `PARTIAL`, and the real-project maturity is
`NOT_VERIFIED`: do not call this a complete real project or an approval.
The full D3 bundle and 3B/3C hourly interval traces are preserved losslessly in
`archived-d3-and-intervals.zip`; their original byte hashes and paths are
recorded in `expanded-file-manifest.json`. All stage results, receipts,
canonical, calculation-only coverage matrix and source material are readable.

Reproduce from the repository root:

0. Check the durable package, archive entries, receipt and independently
   recalculated annual generation, degradation, cash, NPV, IRR residual and
   payback: `python -m tooling.solar_pv_phase7l_full_cases verify reports/solar-pv/phase7l-r1-full-cases/industrial_rooftop`
1. Copy this case directory to a fresh private scratch directory.
2. `python -m zipfile -e archived-d3-and-intervals.zip .` from that copied case.
3. Verify the SHA-256/bytes of every path in `expanded-file-manifest.json`.
4. `python services/solar-pv-engine/solar_pv.py --workspace CASE_SCRATCH project --input input.json --methods methods.json --budget budget.json --bundle bundle --terminal-source terminal.json --terminal-document terminal.txt --output project-recomputed`
5. Audit the stored original canonical/receipt (not the new UUID): `python -m tooling.solar_pv_input_audit CASE_SCRATCH/input.json CASE_SCRATCH/bundle/manifest.json CASE_SCRATCH/project/canonical.json CASE_SCRATCH/calculation-only-checklist.json CASE_SCRATCH/new-audit.json --bundle-dir CASE_SCRATCH/bundle`

The stored canonical carries a run-specific UUID; a fresh execution has a new
run ID and hash. Compare numeric outputs and inputs, not a fabricated
bit-identical run identity. The checklist intentionally has no report bindings.

Obligations: `actual-effective-obligation-matrix.json` records all 469 catalog
definitions and `category-effective-obligations.json` records the frozen
category-allowed view: 386 allowed, 309 L2-required definitions, 260 present,
47 repeated children without parent instances, **2 effective required gaps**
(`grid.power_factor`, `schedule.tasks`), plus 67 L2 conditions whose truth is
pending. Nothing has been invented to fill these gaps. The power factor lacks
a source-backed grid/design basis, and the schedule lacks sourced task rows.
Rights, engineering, permitting, negotiated tariff and tax status remain
synthetic assumptions, not field verification or professional sign-off.
