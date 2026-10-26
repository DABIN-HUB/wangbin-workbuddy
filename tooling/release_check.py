"""Aggregate validation, tests, packaging and platform-aware gates."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import ProjectConfig
from .license_report import write_license_report
from .packager import build_candidate_zip, write_manifest
from .test_runner import run_tests, write_test_report
from .validators.project_validator import validate_project
from .validators.zip_validator import validate_zip


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def run_release_check(config: ProjectConfig) -> dict[str, Any]:
    config.ensure_dirs()
    validation = validate_project(config.root)
    _write_json(config.reports_dir / "validate.json", validation.to_dict())
    tests = run_tests(config.root)
    write_test_report(tests, config.reports_dir / "test-results.json", config.reports_dir / "test-results.md")
    licenses = write_license_report(config.root)
    package_path = config.dist_dir / "wangbin-document-assistant-1.0.0-candidate.zip"
    package_error = None
    manifest: dict[str, Any] | None = None
    try:
        manifest = build_candidate_zip(config.root, package_path)
        write_manifest(manifest, config.dist_dir / "wangbin-document-assistant-1.0.0-candidate.manifest.json")
        (config.dist_dir / "wangbin-document-assistant-1.0.0-candidate.sha256").write_text(manifest["zip_sha256"] + "  " + package_path.name + "\n", encoding="utf-8")
    except Exception as exc:
        package_error = str(exc)
    zip_valid = False
    zip_findings = []
    if package_path.exists():
        zip_valid, zip_findings, _ = validate_zip(package_path)
    gates = {
        "PLATFORM_SPEC_PASS": "PASS" if (config.root / "docs/workbuddy-platform-spec.md").exists() else "FAIL",
        "SKILL_SCHEMA_PASS": validation.status,
        "OPEN_SOURCE_LICENSE_PASS": licenses["status"],
        "DOCUMENT_ENGINE_PASS": "PASS" if tests["status"] == "PASS" else "FAIL",
        "SECURITY_PASS": "PASS" if validation.status == "PASS" and tests["status"] == "PASS" else "FAIL",
        "INTEGRATION_TEST_PASS": tests["status"],
        "PACKAGE_VALIDATION_PASS": "PASS" if manifest and zip_valid else "FAIL",
        "WORKBUDDY_RUNTIME_PASS": "BLOCKED",
        "PUBLISH_READY": "BLOCKED",
    }
    report = {
        "gates": gates,
        "validation": validation.to_dict(),
        "tests": tests,
        "licenses": licenses,
        "package": manifest,
        "package_error": package_error,
        "zip_findings": [item.to_dict() for item in zip_findings],
    }
    _write_json(config.reports_dir / "release-check.json", report)
    markdown = ["# Phase 1 Release Check", ""]
    for name, status in gates.items():
        markdown.append(f"- `{name}`: **{status}**")
    markdown.extend(["", "`WORKBUDDY_RUNTIME_PASS` 与 `PUBLISH_READY` 在没有平台授权环境时必须保持 BLOCKED。", ""])
    (config.reports_dir / "release-check.md").write_text("\n".join(markdown), encoding="utf-8")
    return report
