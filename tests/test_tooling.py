from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tooling.packager import build_candidate_zip
from tooling.validators.project_validator import validate_project
from tooling.validators.zip_validator import validate_zip

ROOT = Path(__file__).resolve().parents[1]


def test_project_validator_passes_real_templates() -> None:
    report = validate_project(ROOT)
    assert report.status == "PASS", [finding.to_dict() for finding in report.findings]


def test_cli_validate_is_executable() -> None:
    completed = subprocess.run([sys.executable, "-m", "tooling", "validate"], cwd=ROOT, capture_output=True, text=True)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    parsed = json.loads(completed.stdout)
    assert parsed["status"] == "PASS"


def test_candidate_zip_is_safe_and_has_expected_root(tmp_path: Path) -> None:
    zip_path = tmp_path / "candidate.zip"
    manifest = build_candidate_zip(ROOT, zip_path)
    valid, findings, members = validate_zip(zip_path)
    assert valid, [finding.to_dict() for finding in findings]
    assert manifest["zip_sha256"]
    assert any(member["path"] == "wangbin-document-assistant/SKILL.md" for member in members)
    assert all(not member["path"].startswith(".git/") for member in members)
