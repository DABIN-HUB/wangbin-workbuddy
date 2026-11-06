# Data Import Precheck 0.1.2 — local candidate

Entry: `scripts/precheck.py` (Python >=3.11, `openpyxl>=3.1,<4`; openpyxl is not bundled). Install dependency into an explicitly selected environment before running; the WorkBuddy host Python/runtime and third-party package availability are NOT_TESTED. This ZIP is local only, not a platform installation or publication receipt.

Dependency: openpyxl 3.1.5 (MIT) and transitive et_xmlfile 2.0.0 (MIT), as reported by installed Python distribution metadata; neither wheel is bundled. Python standard library: csv, hashlib, json, pathlib, zipfile. No network calls. Source/target data supplied by caller; no bundled customer records. Static SKILL instructions are not proof of real natural-language model orchestration.

Product-specific distribution rights, StarCore Lab brand rights, account-effective platform agreement and dependency redistribution terms are NOT_VERIFIED. No license grant is claimed for this candidate; release gate is BLOCKED until an authorized human makes and records the rights decision. Do not submit or upload the ZIP as release-ready.

Limits: local raw CSV UTF-8 (including BOM), XLSX without formulas/macros/external links; max 20 MiB input, 50,000 rows and 1,000,000 cells, no OCR and no live target-system connection. XLSX output cells are stored as literal strings. Partial checks are not a promise of import success.
