# wangbin-solar-pv-prestudy

WorkBuddy Skill candidate for evidence-bounded solar PV preliminary feasibility reports.

- Developer: 星核实验室 StarCore Lab
- Version: 0.1.1
- Scope: industrial rooftop and utility-scale ground projects
- Local status: candidate only; WorkBuddy platform installation and runtime not tested
- Recommended delivery: pair this Skill with the `wangbin-solar-pv-cli` Python CLI Connector
- PDF status: depends on a real `soffice`/`libreoffice` runtime; no fake PDF is produced
- License: proprietary candidate; rights and platform agreement require manual review

The package is a wrapper around the existing `wangbin_solar_pv` calculation and report-export engine. It intentionally does not embed a second calculation implementation. The Skill ZIP does not install Python or pip dependencies. The recommended WorkBuddy path is CLI + Skill: the Connector declares a WorkBuddy-managed Python runtime and installs the two version-pinned internal wheels from a trusted package index. Those wheels are not published by this repository, so platform installation remains blocked until an authorized distribution source is configured and verified.
