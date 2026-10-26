"""Command line entry points for the wangbin WorkBuddy project."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import ProjectConfig
from .packager import build_candidate_zip, write_manifest
from .release_check import run_release_check
from .test_runner import run_tests, write_test_report
from .validators.project_validator import validate_project
from .validators.zip_validator import validate_zip


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m tooling", description="wangbin WorkBuddy engineering toolkit")
    parser.add_argument("command", choices=["validate", "test", "package", "release-check"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    return parser


def _dump(value: object, path: Path, heading: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    markdown = [f"# {heading}", "", "```json", json.dumps(value, ensure_ascii=False, indent=2, default=str), "```", ""]
    path.with_suffix(".md").write_text("\n".join(markdown), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    config = ProjectConfig.from_root(args.root)
    config.ensure_dirs()
    if args.command == "validate":
        report = validate_project(config.root)
        _dump(report.to_dict(), config.reports_dir / "validate.json", "项目校验报告")
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return 0 if report.status == "PASS" else 1
    if args.command == "test":
        result = run_tests(config.root)
        write_test_report(result, config.reports_dir / "test-results.json", config.reports_dir / "test-results.md")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "PASS" else 1
    if args.command == "package":
        destination = config.dist_dir / "wangbin-document-assistant-1.0.0-candidate.zip"
        manifest = build_candidate_zip(config.root, destination)
        write_manifest(manifest, config.dist_dir / "wangbin-document-assistant-1.0.0-candidate.manifest.json")
        (config.dist_dir / "wangbin-document-assistant-1.0.0-candidate.sha256").write_text(manifest["zip_sha256"] + "  " + destination.name + "\n", encoding="utf-8")
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0
    report = run_release_check(config)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all(status in {"PASS", "NOT_TESTED", "BLOCKED"} for status in report["gates"].values()) and report["gates"]["PUBLISH_READY"] == "BLOCKED" else 1
