# wangbin-solar-pv-prestudy

WorkBuddy Skill candidate for evidence-bounded solar PV preliminary feasibility reports.

- Developer: 星核实验室 StarCore Lab
- Version: 0.1.2
- Scope: industrial rooftop and utility-scale ground projects only
- Local status: candidate only; WorkBuddy platform installation and runtime not tested
- Recommended delivery: pair this Skill with the `wangbin-solar-pv-cli` Python CLI Connector
- Report structure: 18 chapters / 100 chapter items / 13 appendices / 26 appendix items
- Deliverables: DOCX, real PDF when a legal renderer is available, calculation XLSX, source/assumption XLSX; review exports also include `canonical.json` and 126-record `content-checklist.json`
- PDF status: depends on a real `soffice`/`libreoffice` runtime; no fake PDF is produced
- License: proprietary candidate; rights and platform agreement require manual review

The package is a wrapper around the existing `wangbin_solar_pv` calculation and report-export engine. It intentionally does not embed a second calculation implementation. The Skill ZIP does not install Python or pip dependencies. The recommended WorkBuddy path is CLI + Skill: the Connector declares a WorkBuddy-managed Python runtime and installs the two version-pinned internal wheels from a trusted package index. Those wheels are not published by this repository, so platform installation remains blocked until an authorized distribution source is configured and verified.

## Supported report types

- **Industrial rooftop PV (`industrial_rooftop`)**: roof area/usable boundary, structural and waterproofing evidence, load matching, self-use/export/curtailment, equipment, generation, tariff, CAPEX/OPEX, finance, scenarios and evidence gaps.
- **Utility-scale ground PV (`utility_scale_ground`)**: land and construction boundary, terrain/geology, foundations, roads/drainage, collector/step-up/export, centralized grid connection and curtailment, market sales, generation, CAPEX/OPEX, finance, scenarios and evidence gaps.

Agrivoltaics, fishery PV, PV-plus-storage, residential PV, carport/BIPV and other unlisted types are **not supported**. Unsupported or legally unsubstantiated conclusions remain `UNKNOWN`/`BLOCKED`; this candidate is not platform-tested and cannot be described as fully available.
