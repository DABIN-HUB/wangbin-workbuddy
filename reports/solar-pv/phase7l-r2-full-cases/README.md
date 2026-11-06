# Phase 7L-R2 B — SYNTHETIC calculation-only inputs

These are two **new** 25-year Phase 2/D3/3G cases. The R1 sealed trees and the separate 3-year SMOKE are unchanged. No PDF/report approval, title, roof structural signoff, grid permission, signed contract, or real-project verification is implied. Both ordinary CLI project runs finished `PARTIAL`; real-project maturity remains `NOT_VERIFIED`.

| Category | Phase 2 input hash | D3 content hash | SHA-256 `documents/source-material.md` | run ID | source snapshot ID | canonical result hash |
|---|---|---|---|---|---|---|
| industrial_rooftop | `0cc4cfd1a96bf692656676a857d81abe903a436e91b733dfec28454f01f1b29a` | `9082017aa1a4228fa8a265a450f0aad7cac50acb4e0995da73d1db8d977dad8e` | `29127128fbcc74341626f93f63bf8b2eb6a6fc3e9f6ea4300b83a8fcebe2c04a` | `1ea495b0-b638-4a35-986d-38d9d364586d` | `99d4cf30ec62cb5fa433fb94f91af514b2de7e93c723b4ef87e31f950d392dd9` | `398474aff972dee9f0a34bf85380a348bb27f8d4b102d7337ca0478ae0d34fe4` |
| utility_scale_ground | `1f9723362f4395f95023b38051e53ff5d1575f90140bc34848f2a70707e11b90` | `aea0dabbf5642b105d77bb01b7539ac06e45a59d0325c480196283ff69d55c1c` | `40faeccb5c7471704049d5edc7052b92c7248f7bd48ae2d7bb634313e3912225` | `7896dc20-58d5-4c46-88aa-06c13659feec` | `d9327d4ff6902b69d33fe557a0876403e0ccbc4d8d0922588716e2860d98d1f6` | `cd4fca1268dea37283a65680512774053d8e3008cd268375e7dd9f7e9abb2b46` |

Canonical `input_hash` is a **different** 3G identity (`656f694764e2afc1437cb6db603ecc23a9072fa5bea28495c9b036d540624556` roof; `41ffe63a77738f275dc6fefa3ad9bed6f6ce953098924eb2d27d84d3e1e025d3` ground), not the Phase 2 export hash. Terminal-document SHA-256: roof `61f0c30b522aa6a422fcb19874bb5e5c88131a1cd888b4b569508a6301a12576`; ground `721fd0c18ef95bf5479347d2c6cee13bb2c8f7545077d5047dfe6fbab621760d`.

## Coverage interpretation (definition counts, not row-instance counts)

The frozen catalog has 469 definitions. R1 roof category-allowed 386; 309 **effective L2 REQUIRED definitions**, 260 present, 47 required repeated children with no parent rows, 2 actionable gaps (`grid.power_factor`, `schedule.tasks`), and 67 category-effective pending conditions. R1 ground has 375 shared-catalog applicable definitions but only **345 category-allowed definitions**; 295 effective L2 REQUIRED, 249 present, 45 repeated children without parents, 1 actionable gap (`schedule.tasks`), and 41 pending conditions. These are not 49 or 46 independent missing observations. The shared-catalog `tariff.non_avoidable_charges` is forbidden by the ground category and is not a ground deficit. A parent with no rows does not imply fabricated missing child instances. The broader matrix `levels.L2.CHILD_WITHOUT_PARENT_ROWS` (R2 65 roof, 66 ground) also counts non-required children; it is not the effective required-child count.

R2 roof: **270/309** effective required definitions present; 39 repeated child definitions have no parent rows; 0 independent required gaps; 67 pending conditions. R2 ground: **258/295** present; 37 required child definitions have no parent rows; 0 independent required gaps; 41 pending conditions. All 469 definition rows and the D3 atoms were audited through the public reader (`d3_validation=ALL_ATOMS_VALIDATED`). These counts **do not** establish full real-world L2 evidence or resolve conditional obligations.

Five modeled task rows per category have names, owners, start/finish dates, inclusive calendar-day durations in the authored source, predecessor atoms with individual provenance, and a one-day January 1, 2027 **planning** milestone. Roof `grid.power_factor=0.95` is an explicit model assumption, not utility consent. The output audit marks this roof field and schedule tasks as **not reported consumed by numerical calculation**; the ground power factor was already present and reported consumed. Nonetheless these changed Phase 2 inputs were passed through the ordinary full-horizon CLI once per category to produce new identities. Compared with R1, project NPV/IRR and the 25 annual generation values remained numerically equal for both categories; no fictitious numeric change is claimed.

## Reproduction and validation from repository root

For each `CATEGORY` in `industrial_rooftop`, `utility_scale_ground`, use a **fresh** directory in the Hermes scratch directory:

```sh
python -m tooling.solar_pv_phase7l_r2_inputs CATEGORY C:/Users/wangbin/AppData/Local/hermes/cache/scratch/CATEGORY-r2-fresh
python services/solar-pv-engine/solar_pv.py --workspace C:/Users/wangbin/AppData/Local/hermes/cache/scratch/CATEGORY-r2-fresh project --input input.json --methods methods.json --budget budget.json --bundle bundle --terminal-source terminal.json --terminal-document terminal.txt --output project
python -m tooling.solar_pv_phase7l_r2_inputs audit C:/Users/wangbin/AppData/Local/hermes/cache/scratch/CATEGORY-r2-fresh
python -m pytest tests/solar-pv/test_phase7l_r2_inputs.py tests/solar-pv/test_phase7l_full_cases.py --basetemp=C:/Users/wangbin/AppData/Local/hermes/cache/scratch/phase7l-r2-pytest -q
python -m tooling.solar_pv_phase7l_full_cases verify reports/solar-pv/phase7l-r1-full-cases/CATEGORY
```

The generated canonical run UUID/hash is new on each execution. For the recorded cases here, inspect `CATEGORY/input.json`, `CATEGORY/bundle/manifest.json`, `CATEGORY/project/{canonical.json,receipt.json}`, `CATEGORY/actual-effective-obligation-matrix.json`, and `CATEGORY/category-effective-obligations.json`. The `audit` command reads and verifies all D3 rows, writes calculation-only evidence files once, and intentionally refuses overwriting existing outputs. It is not a report-export or platform acceptance gate.
