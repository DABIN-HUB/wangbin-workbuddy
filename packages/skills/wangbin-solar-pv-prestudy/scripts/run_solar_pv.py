#!/usr/bin/env python3
"""Stable local wrapper for the existing solar-PV calculation/report CLI.

This file intentionally contains no PV or financial formulas. It validates the
workspace boundary, selects the category-bound engine command, and returns a
small JSON receipt. The engine remains an explicit runtime dependency.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
from typing import Any


PROJECT_TYPES = {
    "industrial_rooftop": "report",
    "utility_scale_ground": "ground-report",
}


class WrapperError(Exception):
    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _is_link(path: Path) -> bool:
    """Reject symlinks and Windows junctions/reparse points at the boundary."""
    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _safe_relative(value: str, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise WrapperError("INVALID_PATH", f"{label} is required")
    path = Path(value)
    if path.is_absolute() or any(part in {"", ".."} for part in path.parts):
        raise WrapperError("PATH_BOUNDARY", f"{label} must stay inside workspace")
    return path


def _workspace(value: str) -> Path:
    supplied = Path(value).expanduser()
    if _is_link(supplied) or any(_is_link(parent) for parent in supplied.parents if parent.exists()):
        raise WrapperError("WORKSPACE_SYMLINK", "workspace and its existing ancestors must not be symlinks")
    path = supplied.resolve()
    if not path.is_dir():
        raise WrapperError("WORKSPACE_UNAVAILABLE", "workspace must be an existing non-symlink directory")
    return path


def _engine(value: str | None) -> tuple[Path, Path, Path]:
    raw = value or os.environ.get("SOLAR_PV_ENGINE_ROOT")
    bundled_baseline = Path(__file__).resolve().parents[1] / "references" / "baseline"
    candidates: list[Path] = ([Path(raw).expanduser().resolve()] if raw else [
        Path.cwd().resolve(),
        Path(__file__).resolve().parents[3],
    ])
    engine_root = None
    src = None
    for candidate in candidates:
        options = [candidate, candidate / "services" / "solar-pv-engine"]
        for option in options:
            option_src = option / "src"
            if (option_src / "wangbin_solar_pv").is_dir():
                engine_root, src = option, option_src
                break
        if engine_root is not None:
            break
    if engine_root is None or src is None:
        if raw:
            raise WrapperError("ENGINE_UNAVAILABLE", "wangbin_solar_pv engine source was not found")
        spec = importlib.util.find_spec("wangbin_solar_pv")
        package_dir = Path(spec.origin).parent if spec and spec.origin else None
        if package_dir is None or not package_dir.is_dir():
            raise WrapperError("ENGINE_UNAVAILABLE", "wangbin_solar_pv engine is not installed")
        engine_root, src = package_dir.parent, package_dir.parent
    repo_root = engine_root.parent.parent if engine_root.name == "solar-pv-engine" else engine_root
    baseline = repo_root / "docs" / "solar-pv"
    if not baseline.is_dir():
        baseline = engine_root / "docs" / "solar-pv"
    if not baseline.is_dir() and bundled_baseline.is_dir():
        baseline = bundled_baseline
    if not baseline.is_dir():
        raise WrapperError("BASELINE_UNAVAILABLE", "solar-PV frozen baseline directory was not found")
    return engine_root, src, baseline


def _read_result(workspace: Path, relative: Path, project_type: str) -> dict[str, Any]:
    path = workspace / relative
    if not path.is_file() or _is_link(path):
        raise WrapperError("RESULT_UNAVAILABLE", "canonical result is missing")
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WrapperError("RESULT_INVALID", "canonical result is not readable JSON") from exc
    if not isinstance(result, dict) or result.get("pv_type") != project_type:
        raise WrapperError("REPORT_CATEGORY_MISMATCH", "canonical result project type does not match requested report")
    return result


def _redact(text: str, workspace: Path) -> str:
    value = (text or "").replace(str(workspace), "<workspace>")
    value = re.sub(r"(?i)(api[_-]?key|token|password|secret)\s*[=:]\s*[^\s,;]+", r"\1=[REDACTED]", value)
    return value[-1200:]


def _engine_command(engine_root: Path, src: Path, baseline: Path, workspace: Path, command: str, arguments: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(src) + (os.pathsep + existing if existing else "")
    argv = [sys.executable, "-m", "wangbin_solar_pv.cli", "--workspace", str(workspace),
            "--baseline-dir", str(baseline), command, *arguments]
    started = time.perf_counter()
    try:
        completed = subprocess.run(argv, cwd=str(engine_root), env=env, capture_output=True, text=True,
                                   timeout=1800, check=False)
    except subprocess.TimeoutExpired as exc:
        raise WrapperError("ENGINE_TIMEOUT", "solar-PV engine exceeded the configured 30 minute limit") from exc
    elapsed = round(time.perf_counter() - started, 6)
    if completed.returncode != 0:
        match = re.search(r'"code"\s*:\s*"([A-Z0-9_]+)"', completed.stderr or "")
        code = match.group(1) if match else "ENGINE_COMMAND_FAILED"
        raise WrapperError(code, _redact(completed.stderr, workspace) or "solar-PV engine command failed")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise WrapperError("ENGINE_INVALID_RESPONSE", "solar-PV engine did not return JSON") from exc
    if not isinstance(payload, dict):
        raise WrapperError("ENGINE_INVALID_RESPONSE", "solar-PV engine returned a non-object response")
    payload["elapsed_seconds"] = elapsed
    return payload


def _report(args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(args.workspace)
    engine_root, src, baseline = _engine(args.engine_root)
    result_rel = _safe_relative(args.result, "result")
    output_rel = _safe_relative(args.output, "output")
    output = workspace / output_rel
    if output.exists() or _is_link(output):
        raise WrapperError("OUTPUT_EXISTS", "output directory already exists")
    _read_result(workspace, result_rel, args.project_type)
    arguments = ["--result", result_rel.as_posix(), "--output", output_rel.as_posix()]
    if args.mapping:
        arguments.extend(["--mapping", _safe_relative(args.mapping, "mapping").as_posix()])
    payload = _engine_command(engine_root, src, baseline,
                              workspace, PROJECT_TYPES[args.project_type], arguments)
    return {"status": "SUCCESS", "project_type": args.project_type, "report": payload,
            "execution_scope": "canonical-to-report-export; not full input-to-calculation E2E"}


def _project_report(args: argparse.Namespace) -> dict[str, Any]:
    workspace = _workspace(args.workspace)
    engine_root, src, baseline = _engine(args.engine_root)
    project_output = _safe_relative(args.project_output, "project-output")
    report_output = _safe_relative(args.report_output, "report-output")
    if (_is_link(workspace / project_output) or (workspace / project_output).exists()
            or _is_link(workspace / report_output) or (workspace / report_output).exists()):
        raise WrapperError("OUTPUT_EXISTS", "project-output or report-output already exists")
    project_args = ["--input", _safe_relative(args.input, "input").as_posix(),
                    "--methods", _safe_relative(args.methods, "methods").as_posix(),
                    "--bundle", _safe_relative(args.bundle, "bundle").as_posix(),
                    "--budget", _safe_relative(args.budget, "budget").as_posix(),
                    "--output", project_output.as_posix()]
    if args.generation:
        project_args.extend(["--generation", _safe_relative(args.generation, "generation").as_posix()])
    if args.generation_hash:
        if not args.generation:
            raise WrapperError("INVALID_ARGUMENT", "generation-hash requires generation")
        project_args.extend(["--generation-hash", args.generation_hash])
    if args.scenarios:
        project_args.extend(["--scenarios", _safe_relative(args.scenarios, "scenarios").as_posix()])
    if bool(args.terminal_source) != bool(args.terminal_document):
        raise WrapperError("INVALID_ARGUMENT", "terminal-source and terminal-document must be supplied together")
    if args.terminal_source:
        project_args.extend(["--terminal-source", _safe_relative(args.terminal_source, "terminal-source").as_posix(),
                             "--terminal-document", _safe_relative(args.terminal_document, "terminal-document").as_posix()])
    calculation = _engine_command(engine_root, src, baseline, workspace, "project", project_args)
    if calculation.get("status") not in {"PASS", "PARTIAL"}:
        return {"status": calculation.get("status", "BLOCKED"), "project_type": args.project_type,
                "calculation": calculation, "execution_scope": "input-to-calculation stopped before report export"}
    canonical_rel = _safe_relative(args.canonical, "canonical") if args.canonical else None
    if canonical_rel is None:
        candidates = sorted((workspace / project_output).rglob("canonical.json"))
        if len(candidates) != 1:
            raise WrapperError("CANONICAL_AMBIGUOUS", "provide --canonical when project output has zero or multiple canonical results")
        canonical_rel = candidates[0].relative_to(workspace)
    _read_result(workspace, canonical_rel, args.project_type)
    report_args = ["--result", canonical_rel.as_posix(), "--output", report_output.as_posix()]
    if args.mapping:
        report_args.extend(["--mapping", _safe_relative(args.mapping, "mapping").as_posix()])
    report = _engine_command(engine_root, src, baseline, workspace, PROJECT_TYPES[args.project_type], report_args)
    return {"status": "SUCCESS", "project_type": args.project_type, "calculation": calculation,
            "canonical": canonical_rel.as_posix(), "report": report,
            "execution_scope": "full local project-to-report chain; not WorkBuddy platform E2E"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evidence-bounded solar-PV report wrapper")
    parser.add_argument("command", choices=("report", "project-report"))
    parser.add_argument("--project-type", choices=sorted(PROJECT_TYPES), required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--engine-root")
    parser.add_argument("--mapping")
    parser.add_argument("--result")
    parser.add_argument("--output")
    parser.add_argument("--input")
    parser.add_argument("--methods")
    parser.add_argument("--bundle")
    parser.add_argument("--budget")
    parser.add_argument("--project-output")
    parser.add_argument("--report-output")
    parser.add_argument("--canonical")
    parser.add_argument("--generation")
    parser.add_argument("--generation-hash")
    parser.add_argument("--scenarios")
    parser.add_argument("--terminal-source")
    parser.add_argument("--terminal-document")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        if args.command == "report":
            required = ("result", "output")
            if any(not getattr(args, name) for name in required):
                raise WrapperError("INVALID_ARGUMENT", "report requires result and output")
            result = _report(args)
        else:
            required = ("input", "methods", "bundle", "budget", "project_output", "report_output")
            if any(not getattr(args, name) for name in required):
                raise WrapperError("INVALID_ARGUMENT", "project-report requires input, methods, bundle, budget, project-output and report-output")
            result = _project_report(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except WrapperError as exc:
        print(json.dumps({"status": "BLOCKED", "error_code": exc.code,
                          "message": exc.message or "solar-PV execution was blocked"}, ensure_ascii=False))
        return 2
    except Exception:
        print(json.dumps({"status": "FAILED", "error_code": "WRAPPER_FAILURE",
                          "message": "unexpected wrapper failure; inspect the local runtime"}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
