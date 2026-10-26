"""Repeatable real CLI acceptance from an installed, isolated Windows venv.

Run this with the *project* interpreter; every CLI subprocess is launched from
an independently installed venv, with source import variables removed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from tooling.validators.project_validator import validate_connector, validate_skill


def run(root: Path, python_env: Path, missing_env: Path, scratch: Path) -> dict[str, object]:
    root, python_env, missing_env, scratch = (p.resolve() for p in (root, python_env, missing_env, scratch))
    fixtures = root / "tests/fixtures"
    executable = python_env / "Scripts/wangbin-document-cli.exe"
    missing_exe = missing_env / "Scripts/wangbin-document-cli.exe"
    if not executable.is_file() or not missing_exe.is_file():
        raise FileNotFoundError("Install the wheel into both the clean and the --no-deps probe environments first")
    env = os.environ.copy()
    env.pop("WANGBIN_ENGINE_SRC", None)
    env.pop("PYTHONPATH", None)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cases: list[dict[str, object]] = []

    def probe(case_id: str, command: list[str], expected_exit: int = 0, expected_status: str | None = None, expected_code: str | None = None, marker: str | None = None, raw: bool = False) -> dict[str, object] | None:
        result = subprocess.run(command, cwd=scratch, env=env, text=True, encoding="utf-8", capture_output=True, timeout=90)
        try:
            payload = None if raw else json.loads(result.stdout)
            actual = result.stdout.strip() if raw else payload.get("status")
            code = None if raw else (payload.get("error") or {}).get("code")
            passed = result.returncode == expected_exit and (expected_status is None or actual == expected_status) and (expected_code is None or code == expected_code) and (marker is None or marker in result.stdout)
            evidence = {"exit_code": result.returncode, "status": actual, "error_code": code, "marker_present": marker in result.stdout if marker else None}
        except (json.JSONDecodeError, AttributeError, TypeError):
            passed, evidence, payload = False, {"exit_code": result.returncode, "error": "invalid JSON; output redacted"}, None
        cases.append({"id": case_id, "status": "PASS" if passed else "FAIL", "command": subprocess.list2cmdline(command), "evidence": evidence})
        return payload

    with tempfile.TemporaryDirectory(prefix="wangbin-phase2-accept-", dir=scratch) as temporary:
        work = Path(temporary)
        input_dir = work / "输入 文件"
        input_dir.mkdir()
        output_dir = work / "导出 结果"
        pdf = input_dir / "中文 文件.pdf"
        shutil.copy2(fixtures / "sample.pdf", pdf)
        spreadsheet = input_dir / "表格 数据.xlsx"
        shutil.copy2(fixtures / "sample.xlsx", spreadsheet)
        cli = str(executable)
        probe("C01_version", [cli, "version"], expected_status="success", marker="1.1.0")
        probe("C02_doctor", [cli, "doctor"], expected_status="success", marker='"dependencies": "ready"')
        probe("C03_status", [cli, "status"], expected_status="LOCAL_READY", raw=True)
        probe("C04_auth_no_account", [cli, "auth"], expected_status="success", marker='"auth_mode": "none"')
        sentinel = work / "user-owned.txt"
        sentinel.write_text("untouched", encoding="utf-8")
        probe("C05_logout_no_delete", [cli, "logout"], expected_status="success", marker='"auth_mode": "none"')
        if sentinel.read_text(encoding="utf-8") != "untouched":
            cases[-1]["status"] = "FAIL"
            cases[-1]["evidence"] = {"error": "logout modified a user file"}
        specs = (("pdf", pdf, "WANGBIN PDF MARKER"), ("docx", fixtures / "sample.docx", "WANGBIN DOCX MARKER"), ("xlsx", spreadsheet, "Name"), ("pptx", fixtures / "sample.pptx", "WANGBIN PPTX MARKER"), ("html", fixtures / "sample.html", "WANGBIN HTML MARKER"), ("txt", fixtures / "sample.txt", "WANGBIN TXT MARKER"), ("markdown", fixtures / "sample.md", "WANGBIN MARKDOWN MARKER"))
        for kind, path, marker in specs:
            source_root = input_dir if path.parent == input_dir else fixtures
            probe(f"C06_{kind}", [cli, "parse", "--input", str(path), "--input-root", str(source_root), "--output-root", str(output_dir)], expected_status="success", marker=marker)
        probe("C07_batch_partial", [cli, "batch", "--files", str(pdf), str(spreadsheet), str(input_dir / "missing.pdf"), "--input-root", str(input_dir), "--output-root", str(output_dir)], expected_exit=1, expected_status="partial_failure", marker='"failure_count": 1')
        for fmt in ("xlsx", "csv"):
            result = probe(f"C08_dedup_{fmt}", [cli, "deduplicate", "--input", str(spreadsheet), "--input-root", str(input_dir), "--output-root", str(output_dir), "--format", fmt], expected_status="success", marker='"duplicates_removed": 1')
            if result and result.get("output_path"):
                exported = Path(result["output_path"])
                valid = exported.is_file() and exported.stat().st_size > 0 and exported.resolve().is_relative_to(output_dir.resolve()) and exported != spreadsheet
                if valid:
                    if fmt == "xlsx":
                        with zipfile.ZipFile(exported) as archive:
                            valid = archive.testzip() is None and "xl/workbook.xml" in archive.namelist()
                    else:
                        with exported.open(encoding="utf-8-sig", newline="") as handle:
                            valid = len(list(csv.reader(handle))) == 3
                cases[-1]["evidence"]["output_validated"] = valid
                cases[-1]["evidence"]["output_sha256"] = hashlib.sha256(exported.read_bytes()).hexdigest() if valid else None
                if not valid:
                    cases[-1]["status"] = "FAIL"
        probe("C09_corrupt_pdf", [cli, "parse", "--input", str(fixtures / "damaged.pdf"), "--input-root", str(fixtures)], expected_exit=1, expected_status="failed", expected_code="CORRUPT_DOCUMENT")
        probe("C10_wrong_extension", [cli, "parse", "--input", str(fixtures / "mismatched.pdf"), "--input-root", str(fixtures)], expected_exit=1, expected_status="failed", expected_code="MISMATCHED_EXTENSION")
        probe("C11_missing_file", [cli, "parse", "--input", str(input_dir / "not-found.txt"), "--input-root", str(input_dir)], expected_exit=1, expected_status="failed", expected_code="FILE_NOT_FOUND")
        probe("C11_missing_root", [cli, "parse", "--input", str(pdf), "--input-root", str(work / "root-not-found")], expected_exit=1, expected_status="failed", expected_code="INPUT_ROOT_MISSING")
        probe("C12_outside_root", [cli, "parse", "--input", str(fixtures / "sample.txt"), "--input-root", str(input_dir)], expected_exit=1, expected_status="failed", expected_code="PATH_OUTSIDE_ROOT")
        probe("C13_output_inside_input", [cli, "parse", "--input", str(pdf), "--input-root", str(input_dir), "--output-root", str(input_dir / "nested")], expected_exit=1, expected_status="failed", expected_code="OUTPUT_EQUALS_INPUT_ROOT")
        output_file = work / "not-a-directory"
        output_file.write_text("preserved", encoding="utf-8")
        probe("C13_output_file_rejected", [cli, "parse", "--input", str(pdf), "--input-root", str(input_dir), "--output-root", str(output_file)], expected_exit=1, expected_status="failed", expected_code="OUTPUT_PATH_INVALID")
        if output_file.read_text(encoding="utf-8") != "preserved":
            cases[-1]["status"] = "FAIL"
        oversized = input_dir / "large.txt"
        with oversized.open("wb") as handle:
            handle.seek(50 * 1024 * 1024 + 1)
            handle.write(b"x")
        probe("C14_oversize", [cli, "parse", "--input", str(oversized), "--input-root", str(input_dir)], expected_exit=1, expected_status="failed", expected_code="FILE_TOO_LARGE")
        outside = work / "outside"
        outside.mkdir()
        shutil.copy2(fixtures / "sample.txt", outside / "sample.txt")
        junction = input_dir / "junction"
        joined = subprocess.run(["cmd", "/c", "mklink", "/J", str(junction), str(outside)], cwd=scratch, env=env, capture_output=True)
        if joined.returncode == 0:
            try:
                probe("C15_windows_junction", [cli, "parse", "--input", str(junction / "sample.txt"), "--input-root", str(input_dir)], expected_exit=1, expected_status="failed", expected_code="SYMLINK_INPUT")
            finally:
                subprocess.run(["cmd", "/c", "rmdir", str(junction)], cwd=scratch, env=env, capture_output=True)
        else:
            cases.append({"id": "C15_windows_junction", "status": "SKIP", "command": "cmd /c mklink /J <scratch paths>", "evidence": {"reason": "Windows refused to create a junction; no simulated PASS"}})
        symlink = input_dir / "link.txt"
        try:
            symlink.symlink_to(outside / "sample.txt")
        except (OSError, NotImplementedError):
            cases.append({"id": "C16_windows_symlink", "status": "SKIP", "command": "Path.symlink_to(<scratch target>)", "evidence": {"reason": "OS token lacks symlink creation privilege"}})
        else:
            probe("C16_windows_symlink", [cli, "parse", "--input", str(symlink), "--input-root", str(input_dir)], expected_exit=1, expected_status="failed", expected_code="SYMLINK_INPUT")
        probe("C17_missing_dependencies", [str(missing_exe), "status"], expected_exit=78, expected_status="failed", expected_code="ENGINE_RUNTIME_MISSING")
        probe("C17_parse_missing_dependencies", [str(missing_exe), "parse", "--input", str(pdf), "--input-root", str(input_dir)], expected_exit=78, expected_status="failed", expected_code="ENGINE_RUNTIME_MISSING")
        check_list: list[dict[str, object]] = []
        findings = []
        validate_connector(root / "packages/connectors/wangbin-document-cli", check_list, findings)
        validate_skill(root / "packages/skills/wangbin-document-assistant-cli", check_list, findings)
        config = json.loads((root / "packages/connectors/wangbin-document-cli/cli.json").read_text(encoding="utf-8"))
        skill = (root / "packages/skills/wangbin-document-assistant-cli/SKILL.md").read_text(encoding="utf-8")
        expected = ("wangbin-document-cli parse", "wangbin-document-cli batch", "wangbin-document-cli deduplicate", "--input-root", "--output-root", "--files")
        verified = not findings and config.get("runtime") == {"type": "python", "version": "3.12"} and "auth" not in config and "unAuth" not in config and all(s in skill for s in expected)
        cases.append({"id": "C18_platform_metadata_and_skill_commands", "status": "PASS" if verified else "FAIL", "command": "validate_connector + validate_skill + CLI/Skill command consistency", "evidence": {"findings": [item.code for item in findings], "runtime": config.get("runtime")}})
        immutable = subprocess.run([str(python_env / "Scripts/python.exe"), "-I", "-c", "import wangbin_document_engine,wangbin_document_cli;print(wangbin_document_cli.__file__);print(wangbin_document_engine.__file__)"], cwd=scratch, env=env, capture_output=True, text=True)
        locations = immutable.stdout.splitlines()
        local = immutable.returncode == 0 and len(locations) == 2 and all(Path(path).resolve().is_relative_to(python_env) for path in locations)
        matching_modules = local and all(
            (root / "services/document-engine/src" / module / source.name).read_bytes() == (Path(locations[index]).parent / source.name).read_bytes()
            for index, module in enumerate(("wangbin_document_cli", "wangbin_document_engine"))
            for source in (root / "services/document-engine/src" / module).glob("*.py")
        )
        cases.append({"id": "C19_isolated_install_paths", "status": "PASS" if local and matching_modules else "FAIL", "command": "clean-venv/python -I -c <import origin check> + installed source byte comparison", "evidence": {"inside_clean_venv": local, "matches_current_source": matching_modules, "source_env_variables_removed": True}})
    counts = {status: sum(c["status"] == status for c in cases) for status in ("PASS", "FAIL", "SKIP")}
    result = {"checked_at": datetime.now(timezone.utc).isoformat(), "platform": "Windows (actual local execution)", "install_mode": "versioned local wheel, PyPI dependencies downloaded into a fresh venv", "clean_env": str(python_env), "test_command": "python -m tooling.phase2_acceptance --clean-env <scratch venv> --missing-env <scratch no-deps venv>", "cases": cases, "counts": counts, "status": "PASS" if counts["FAIL"] == 0 else "FAIL"}
    reports = root / "reports"
    (reports / "phase2-clean-install.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Phase 2 干净环境验收", "", f"- 状态：{result['status']}；PASS {counts['PASS']} / FAIL {counts['FAIL']} / SKIP {counts['SKIP']}", "- 实际环境：Windows Python 3.12，scratch 新建 venv；不使用开发机的 WANGBIN_ENGINE_SRC/PYTHONPATH。", "- 安装：`python -m pip install --no-input --only-binary=:all: --no-cache-dir dist/wangbin_document_cli-1.1.0-py3-none-any.whl`；`python -m pip check`。", "- SKIP 不计为 PASS；平台 WorkBuddy 安装/运行与 macOS/Linux 运行均未验证。", "", "| 用例 | 状态 | 实际退出码/错误码 |", "|---|---|---|"]
    for item in cases:
        detail = item["evidence"]
        lines.append(f"| {item['id']} | {item['status']} | {detail.get('exit_code', '')} {detail.get('error_code') or ''} |")
    lines.extend(["", "完整命令、输出状态和结果文件 SHA-256 见 `reports/phase2-clean-install.json`。未保存用户文档正文。", ""])
    (reports / "phase2-clean-install.md").write_text("\n".join(lines), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--clean-env", type=Path, required=True)
    parser.add_argument("--missing-env", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.root, args.clean_env, args.missing_env, args.scratch)
    print(json.dumps({"status": result["status"], "counts": result["counts"]}, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
