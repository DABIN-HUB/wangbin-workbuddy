"""Product-scoped, offline consultant regression and immutable per-run receipts.

Preparation is deliberately separate. This module's CLI starts using stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import types
from pathlib import Path

NAME = "wangbin-software-consultant"
SOURCE = f"packages/experts/{NAME}"
BASELINE = f"{SOURCE}/tests/fixtures/regression-baseline.json"
SEALED_COMMIT = "e376395df4e09267ef494f4e421fc49d4fbdb6dd"
RUNTIME = f".runtime/{NAME}"
ARCHIVE = f"dist/{NAME}-1.2.0-expert-candidate.zip"
ORIGINAL = {ARCHIVE: "d42eaa2090eb07660cbb6f712ae506a2f731e5fd62035d5ccd58fec0f236bd47",
            ARCHIVE + ".manifest.json": "59a7f5001637a0ba1d3537e7aa3c61d9e891d26f0ea557e31a8badb9e672c318",
            ARCHIVE + ".sha256": "95407556349acc880f29cb7ee6f0992730e0d4c7799ac689eea9e400992cd1dd"}
CURRENT_ARCHIVE = f"dist/{NAME}-1.2.1-expert-candidate.zip"
CURRENT_FILES = (CURRENT_ARCHIVE, CURRENT_ARCHIVE + ".sha256", CURRENT_ARCHIVE + ".manifest.json")

def _current_files(version):
    archive = f"dist/{NAME}-{version}-expert-candidate.zip"
    return (archive, archive + ".sha256", archive + ".manifest.json")
ROOT_NODES = ("tests/test_product_factory.py::test_legacy_expert_validator_rejects_overlong_name",
              "tests/test_product_factory.py::test_phase5_validator_remains_callable_when_loaded_as_script")
COUNT_KEYS = ("collected", "selected", "passed", "failed", "errors", "skipped", "deselected", "unexecuted", "timeout")
CASE_STATUSES = ("PASS", "FAIL", "ERROR", "SKIPPED", "DESELECTED", "NOT_EXECUTED", "BLOCKED", "TIMEOUT")
OFFLINE_GIT = {"GIT_NO_LAZY_FETCH": "1", "GIT_NO_REPLACE_OBJECTS": "1", "GIT_TERMINAL_PROMPT": "0",
               "GIT_OPTIONAL_LOCKS": "0", "GIT_ALLOW_PROTOCOL": ""}
RUNNER = "tooling/consultant_regression.py"
SUPPORT = "tooling/consultant_regression_support.py"
# Keep the identity at module execution, not a later read of a possibly edited
# file. Check the executing code as well, since a stale bytecode cache may have
# been loaded despite the source file already containing different bytes.
_LOADED_PATH = Path(__file__).absolute()
_LOADED_RAW = _LOADED_PATH.read_bytes()
_LOADED_CODE = sys._getframe().f_code


class IdentityConflict(ValueError):
    """An observed identity mismatch, rather than an unavailable prerequisite."""


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _json_bytes(data):
    return (json.dumps(data, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _write(path, data):
    with path.open("xb") as stream:
        stream.write(_json_bytes(data))


def _check_link(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ValueError(f"link/reparse point refused: {path}")


def safe_path(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise ValueError("unsafe relative path")
    parts = relative.split("/")
    if any(p in {"", ".", ".."} or p.endswith((" ", ".")) for p in parts):
        raise ValueError("unsafe relative path")
    root = Path(root).absolute()
    for parent in reversed((root, *root.parents)):
        _check_link(parent)
    current = root
    for part in parts:
        current /= part
        _check_link(current)
    return current


def _env():
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith(("GIT_", "PYTEST_", "PYTHON", "WANGBIN_CONSULTANT_TEST_"))}
    env.update(OFFLINE_GIT)
    return env


def _git(root, *args):
    return subprocess.run(["git", "--no-replace-objects", "-c", "core.longpaths=true", *args], cwd=root,
                          env=_env(), capture_output=True, check=True, timeout=30).stdout


def _commit(root, name):
    if not re.fullmatch(r"[0-9a-f]{40}", name or ""):
        raise ValueError("formal run requires explicit full lowercase Git commit SHA")
    if _git(root, "rev-parse", "--verify", f"{name}^{{commit}}").decode().strip() != name:
        raise IdentityConflict("not an exact Git commit")
    return name


def _blob(root, commit, rel):
    entry = _git(root, "ls-tree", "-z", commit, "--", rel)
    if not entry or entry.split(b"\t", 1)[0].split()[:2] not in ([b"100644", b"blob"], [b"100755", b"blob"]):
        raise ValueError(f"not a regular committed file: {rel}")
    return _git(root, "show", f"{commit}:{rel}")


def _regular(root, rel):
    path = safe_path(root, rel)
    if not path.is_file():
        raise FileNotFoundError(f"required file absent: {rel}")
    return path.read_bytes()


def _canonical(rel, data):
    return data if rel.endswith(".png") else data.replace(b"\r\n", b"\n")


def _worktree(root):
    status = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    return {"dirty": bool(status), "status": status.decode("utf-8", errors="surrogateescape").split("\0")[:-1]}


def _supervisor_identity(root, rows, mode, commit, support_raw=None):
    """Bind the actual runner and the explicitly source-loaded support module."""
    path = safe_path(root, RUNNER)
    if _LOADED_PATH != path or Path(__file__).absolute() != path:
        raise IdentityConflict("orchestrator was not loaded from selected repository")
    raw = _regular(root, RUNNER)
    if raw != _LOADED_RAW or compile(raw, str(_LOADED_PATH), "exec", dont_inherit=True) != _LOADED_CODE:
        raise IdentityConflict("orchestrator loaded code/source differs from current file")
    support_path = safe_path(root, SUPPORT)
    current_support = _regular(root, SUPPORT)
    if support_raw is not None and current_support != support_raw:
        raise IdentityConflict("orchestrator support source changed during execution")
    identities = {}
    for rel, module_path, data in ((RUNNER, path, raw), (SUPPORT, support_path, current_support)):
        row = {"path": str(module_path), "sha256": digest(data), "canonical_sha256": digest(_canonical(rel, data)), "size": len(data)}
        if row["canonical_sha256"] != rows[rel]["canonical_sha256"] or (mode == "development" and row["sha256"] != rows[rel]["sha256"]):
            raise IdentityConflict(f"orchestrator differs from snapshot: {rel}")
        if mode == "formal":
            blob = _blob(root, commit, rel)
            if digest(blob) != rows[rel]["sha256"] or _canonical(rel, data) != _canonical(rel, blob):
                raise IdentityConflict(f"orchestrator differs from selected commit: {rel}")
            row["git_blob_sha256"] = digest(blob)
        identities[rel] = row
    return identities, current_support


def _load_support(root, raw):
    # Do not use a possibly cached package import from a different checkout or
    # a stale pyc. Execute the exact bytes bound above, from this root only.
    path = safe_path(root, SUPPORT)
    module = types.ModuleType("tooling.consultant_regression_support")
    module.__file__ = str(path)
    module.__package__ = "tooling"
    exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
    if Path(module.__file__).absolute() != path:
        raise IdentityConflict("orchestrator support was not loaded from selected repository")
    return module


def _snapshot(root, target, mode, commit):
    read = (lambda rel: _blob(root, commit, rel)) if mode == "formal" else (lambda rel: _regular(root, rel))
    plan = json.loads(read(BASELINE))
    if set(plan["files"]) != set(APPROVED_FILES) or len(plan["files"]) != len(APPROVED_FILES):
        raise ValueError("snapshot allowlist differs from approved inputs")
    if len(plan["case_ids"]) != 307 or len(set(plan["case_ids"])) != 307:
        raise ValueError("307 baseline case identities required")
    added = plan["added_case_ids"]
    if not added or len(set(added)) != len(added) or set(added) & set(plan["case_ids"]):
        raise ValueError("new approved case identities invalid")
    rows = {}
    for rel in APPROVED_FILES:
        raw = read(rel)
        path = safe_path(target, rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(raw)
        rows[rel] = {"sha256": digest(raw), "canonical_sha256": digest(_canonical(rel, raw)), "size": len(raw)}
    return plan, rows


class _Recorder:
    """Record real pytest hooks incrementally so a killed child retains partial results."""
    def __init__(self, events, allowed):
        self.events = events
        self.allowed = allowed

    def emit(self, kind, **fields):
        with self.events.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"kind": kind, **fields}, ensure_ascii=True) + "\n")

    def pytest_collection_modifyitems(self, items):
        if self.allowed is not None:
            self.emit("discovered", ids=[item.nodeid for item in items])
            items[:] = [item for item in items if item.nodeid in self.allowed]

    def pytest_collection_finish(self, session):
        self.emit("collection", ids=[item.nodeid for item in session.items])

    def pytest_deselected(self, items):
        self.emit("deselected", ids=[item.nodeid for item in items])

    def pytest_collectreport(self, report):
        if report.failed or report.skipped:
            self.emit("collect_error" if report.failed else "collect_skip", id=report.nodeid)

    def pytest_runtest_logstart(self, nodeid, location):
        self.emit("start", id=nodeid)

    def pytest_runtest_logreport(self, report):
        self.emit("report", id=report.nodeid, phase=report.when, outcome=report.outcome,
                  xfail=bool(getattr(report, "wasxfail", False)))

    def pytest_sessionfinish(self, session, exitstatus):
        self.emit("finish", exitcode=int(exitstatus))


def _worker(args):
    # Isolated interpreter: explicitly add only this snapshot to imports.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import pytest
    events, plan, config, basetemp = map(Path, args[:4])
    selection = json.loads(plan.read_bytes())
    recorder = _Recorder(events, selection["allowed"])
    options = ["--noconftest", "-p", "no:cacheprovider", "-c", str(config), "--rootdir", str(Path.cwd()), "--basetemp", str(basetemp), "-q", "-ra"]
    if selection["allowed"] is None:
        options.append("--collect-only")
    return int(pytest.main([*options, *selection["selectors"]], plugins=[recorder]))


def _child(snapshot, output, python, selectors, allowed, label, timeout, env):
    plan, events = output / f"{label}-selection.json", output / f"{label}-events.jsonl"
    _write(plan, {"selectors": selectors, "allowed": allowed})
    config = snapshot / "pyproject.toml"
    if not config.is_file():
        config = output / "pytest.ini"
        if not config.exists():
            config.write_text("[pytest]\n", encoding="utf-8")
    child_env = _env()
    child_env.update(env or {})
    child_env.update(OFFLINE_GIT)
    child_env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    command = [str(python), "-I", "-B", str(snapshot / "tooling/consultant_regression.py"), "_worker",
               str(events), str(plan), str(config), str(snapshot / f"tmp-{label}")]
    timed_out = False
    with (output / f"{label}.stdout").open("xb") as stdout, (output / f"{label}.stderr").open("xb") as stderr:
        try:
            proc = subprocess.run(command, cwd=snapshot, env=child_env, stdout=stdout, stderr=stderr, timeout=timeout)
            code = proc.returncode
        except subprocess.TimeoutExpired:
            code, timed_out = None, True
    records = []
    malformed = False
    if events.exists():
        for line in events.read_bytes().splitlines():
            try:
                records.append(json.loads(line))
            except (ValueError, UnicodeError):
                malformed = True
    return {"exitcode": code, "timeout": timed_out, "events": records, "malformed": malformed}


def _ids(events, kind):
    return [node for event in events if event["kind"] == kind for node in event["ids"]]


def _case_counts(cases):
    counts = dict.fromkeys(CASE_STATUSES, 0)
    for case in cases.values():
        counts[case["status"]] += 1
    return counts


def _phase_counts():
    return {phase: dict.fromkeys(("passed", "failed", "skipped", "xfail"), 0)
            for phase in ("setup", "call", "teardown")}


def _pytest_outcomes(phase_counts, collected, executed, collection_errors, collection_skips):
    return {"call_failures": phase_counts["call"]["failed"], "setup_errors": phase_counts["setup"]["failed"],
            "teardown_errors": phase_counts["teardown"]["failed"], "collection_errors": len(collection_errors),
            "collection_skips": len(collection_skips), "collection_timeout": bool(collected and collected["timeout"]),
            "execution_timeout": bool(executed and executed["timeout"]),
            "collection_exitcode": collected["exitcode"] if collected else None,
            "execution_exitcode": executed["exitcode"] if executed else None}


def execute_cases(snapshot, output, python, selectors, blockers, *, timeout=600, env=None, baseline=()):
    """Collect once, execute independent actual IDs; prerequisite blocks are not pytest skips."""
    snapshot, output, python = Path(snapshot).absolute(), Path(output).absolute(), Path(python).absolute()
    collected_run = _child(snapshot, output, python, selectors, None, "collect", timeout, env)
    events = collected_run["events"]
    ids = _ids(events, "collection")
    deselected = set(_ids(events, "deselected"))
    unique = set(ids)
    absent = sorted(set(baseline) - unique)
    counts = dict.fromkeys(COUNT_KEYS, 0)
    # Terminal counts have exactly one status per case. Phase counts preserve
    # independent pytest outcomes, including a call failure plus teardown error.
    phase_counts = _phase_counts()
    counts["collected"] = len(unique | deselected)
    cases = {node: {"status": "NOT_EXECUTED"} for node in sorted(unique | deselected | set(absent))}
    for node in deselected:
        cases[node] = {"status": "DESELECTED"}
    for node in absent:
        cases[node] = {"status": "NOT_EXECUTED", "reason": "required baseline case absent from collection"}
    collection_errors = [e["id"] for e in events if e["kind"] == "collect_error"]
    collection_skips = [e["id"] for e in events if e["kind"] == "collect_skip"]
    counts["errors"] = len(collection_errors)
    counts["skipped"] = len(collection_skips)
    for node in unique:
        reason = blockers.get(node)
        if reason:
            cases[node] = {"status": "BLOCKED", "reason": reason}
    allowed = [node for node in ids if not blockers.get(node)]
    counts["selected"] = len(set(allowed))
    issues = []
    if absent or len(ids) != len(unique) or not ids or collected_run["exitcode"] != 0 or collected_run["malformed"]:
        issues.append("incomplete or invalid collection")
    executed = None
    if allowed and collected_run["exitcode"] == 0 and not collected_run["malformed"] and len(ids) == len(unique):
        executed = _child(snapshot, output, python, selectors, allowed, "run", timeout, env)
        run_events = executed["events"]
        if set(_ids(run_events, "discovered")) != unique or set(_ids(run_events, "collection")) != set(allowed):
            issues.append("collection changed between collection and execution")
        for node in _ids(run_events, "deselected"):
            cases[node] = {"status": "DESELECTED"}
        phases = {}
        active = set()
        for event in run_events:
            if event["kind"] == "start":
                active.add(event["id"])
            elif event["kind"] == "report":
                phases.setdefault(event["id"], []).append(event)
                phase_counts[event["phase"]][event["outcome"]] += 1
                if event["xfail"]:
                    phase_counts[event["phase"]]["xfail"] += 1
                if event["phase"] == "teardown":
                    active.discard(event["id"])
            elif event["kind"] == "collect_error":
                collection_errors.append(event["id"])
                counts["errors"] += 1
            elif event["kind"] == "collect_skip":
                collection_skips.append(event["id"])
                counts["skipped"] += 1
        for node, reports in phases.items():
            if node not in allowed:
                issues.append("unselected case executed")
            if any(r["outcome"] == "failed" and r["phase"] != "call" for r in reports):
                status = "ERROR"
            elif any(r["outcome"] == "failed" for r in reports):
                status = "FAIL"
            elif any(r["outcome"] == "skipped" or r["xfail"] for r in reports):
                status = "SKIPPED"
            elif {r["phase"] for r in reports if r["outcome"] == "passed"} == {"setup", "call", "teardown"}:
                status = "PASS"
            else:
                status = "NOT_EXECUTED"
            cases[node] = {"status": status, "reports": reports}
        if executed["timeout"]:
            for node in active:
                if cases.get(node, {}).get("status") not in {"FAIL", "ERROR"}:
                    cases.setdefault(node, {})["status"] = "TIMEOUT"
            issues.append("execution timed out")
        if executed["exitcode"] != 0 or executed["malformed"]:
            issues.append("nonzero or incomplete execution")
    if collected_run["timeout"]:
        issues.append("collection timed out")
    mapping = {"PASS": "passed", "FAIL": "failed", "ERROR": "errors", "SKIPPED": "skipped",
               "DESELECTED": "deselected", "NOT_EXECUTED": "unexecuted", "BLOCKED": "unexecuted", "TIMEOUT": "timeout"}
    for case in cases.values():
        counts[mapping[case["status"]]] += 1
    if collected_run["timeout"] or (executed and executed["timeout"] and not counts["timeout"]):
        counts["timeout"] += 1  # run-level timeout when no active case is known
    fail = bool(issues or any(counts[k] for k in ("failed", "errors", "skipped", "deselected", "timeout"))
                or any(case["status"] == "NOT_EXECUTED" for case in cases.values()))
    status = "FAIL" if fail else "BLOCKED" if counts["unexecuted"] else "PASS"
    return {"status": status, "returncode": 0 if status == "PASS" else 1, "counts": counts, "cases": cases,
            "case_counts": _case_counts(cases), "phase_counts": phase_counts,
            "pytest_outcomes": _pytest_outcomes(phase_counts, collected_run, executed, collection_errors, collection_skips),
            "collection_errors": collection_errors, "collection_skips": collection_skips, "missing_baseline": absent,
            "issues": issues, "selectors": selectors, "collected_ids": ids, "selected_ids": allowed,
            "collection_exitcode": collected_run["exitcode"], "pytest_exitcode": executed["exitcode"] if executed else None}


def _sealed_source_binding(rows, sealed, members):
    # Compare the actual selected snapshot, not the independently inspected
    # original archive. A known mismatch remains FAIL even with missing data.
    blobs = sealed["blobs"]
    for member in members:
        path = f"{SOURCE}/{member}"
        if path not in rows:
            return "FAIL"
        if path in blobs and rows[path]["canonical_sha256"] != blobs[path]["sha256"]:
            return "FAIL"
    if sealed["status"] != "PASS":
        return sealed["status"]
    return "PASS" if all(f"{SOURCE}/{member}" in blobs for member in members) else "FAIL"



def _prerequisites(history, candidate, baseline):
    result = {}
    for node in baseline:
        gate = None
        if node.endswith("test_122_history_and_pinned_prior_catalog") and any(g["status"] != "PASS" for g in history.values()):
            result[node] = "failed or missing required historical objects"
        if "test_fixed_price_source.py::test_fixed_source_cli[" in node:
            gate = history["price"]
        elif node.endswith("test_expert_candidate.py::test_zip_members_are_exact_and_source_identical"):
            gate = history["legacy"]
        elif node.endswith(("test_current_snapshot_matches_sealed_bytes", "test_archive_is_deterministic_and_binds_formal_bytes", "test_rebuilt_candidate_runtime", "test_package_rejects_uncommitted_member_bytes", "test_original_candidate_identity_and_runtime", "test_current_wrong_historical_commit_cannot_be_current_seal", "test_current_121_snapshot_matches_registered_seal")):
            gate = history["sealed"]
            if gate["status"] == "PASS" and node.endswith("test_original_candidate_identity_and_runtime"):
                gate = candidate
        if gate is not None and gate["status"] != "PASS":
            result[node] = "failed or missing required history/original prerequisite"
        if "delivery" in history and node.endswith(("test_current_snapshot_matches_sealed_bytes", "test_archive_is_deterministic_and_binds_formal_bytes", "test_rebuilt_candidate_runtime", "test_package_rejects_uncommitted_member_bytes", "test_original_candidate_identity_and_runtime")) and history["delivery"]["status"] != "PASS":
            result[node] = "failed or missing historical seventh-batch delivery prerequisite"
        if "delivery_catalog" in history and node.endswith(("test_original_catalog_identity", "test_archive_is_deterministic_and_binds_formal_bytes")) and history["delivery_catalog"]["status"] != "PASS":
            result[node] = "failed or missing historical catalog prerequisite"
    return result


def _current_prerequisites(current, baseline, *, version="1.2.1"):
    prefix = "/test_bundled_calculator.py::test_current_" + version.replace(".", "") + "_"
    result = {}
    for node in baseline:
        if prefix not in node:
            continue
        if current["source_binding"] != "PASS":
            result[node] = "failed or missing current registered source seal"
        elif node.endswith(prefix + "original_runtime") and current["status"] != "PASS":
            result[node] = "failed or missing current registered archive prerequisite"
    return result


def _case_gate(cases, suffix):
    case = cases.get(f"{SOURCE}/tests/test_bundled_calculator.py::{suffix}", {})
    status = case.get("status", "BLOCKED")
    return "PASS" if status == "PASS" else "BLOCKED" if status in {"BLOCKED", "NOT_EXECUTED"} else "FAIL"


def _package_evidence(snapshot, output, result, *, current=False, version="1.2.1"):
    """Read back exact test-owned archives/CLI receipts before discarding scratch."""
    tests = {"rebuild": "test_archive_is_deterministic_and_binds_formal_bytes",
             "rebuilt_runtime": "test_rebuilt_candidate_runtime",
             "original_runtime": "test_original_candidate_identity_and_runtime"}
    archive_paths = {name: tuple(ORIGINAL) for name in tests}
    if current:
        versions = (("prior_121", "1.2.1"), ("current", version)) if version == "1.2.2" else (("current", version),)
        for label, selected in versions:
            prefix = "test_current_" + selected.replace(".", "") + "_"
            new_tests = {label + "_rebuild": prefix + "archive_is_deterministic",
                         label + "_rebuilt_runtime": prefix + "rebuilt_runtime",
                         label + "_original_runtime": prefix + "original_runtime"}
            tests.update(new_tests)
            archive_paths.update({name: _current_files(selected) for name in new_tests})
    for name, test in tests.items():
        result["gates"][name] = _case_gate(result["cases"], test)
    evidence = {}
    result["package_evidence"] = evidence
    temp = safe_path(snapshot, "tmp-run")
    if not temp.is_dir():
        for name in tests:
            if result["gates"][name] == "PASS":
                result["gates"][name] = "FAIL"
        return
    for name, test in tests.items():
        prefix = test[:30]
        # pytest's tmp_path factory retains truncated test names + numeric suffix.
        dirs = [p for p in temp.iterdir() if re.fullmatch(re.escape(prefix) + r"[0-9]+", p.name)]
        if not dirs:
            if result["gates"][name] == "PASS":
                result["gates"][name] = "FAIL"
            continue
        if len(dirs) != 1:
            raise ValueError("ambiguous package test evidence directory")
        directory = safe_path(temp, dirs[0].name)
        kind = name.removeprefix("current_").removeprefix("prior_121_")
        files = [] if kind == "rebuild" else ["fictional-receipt.json", "fictional-v2-receipt.json"]
        if kind == "rebuild":
            files.extend(f"{entry}/{rel}" for entry in ("dedicated", "generic") for rel in archive_paths[name])
        elif kind == "rebuilt_runtime":
            files.extend(f"dedicated/{rel}" for rel in archive_paths[name])
        identities = {}
        for rel in files:
            path = safe_path(directory, rel)
            if path.is_file():
                raw = path.read_bytes()
                identities[rel] = {"size": len(raw), "sha256": digest(raw)}
                if not rel.endswith(".zip"):
                    filename = f"{name}-{rel.replace('/', '-')}"
                    retained = safe_path(output, filename)
                    with retained.open("xb") as stream:
                        stream.write(raw)
                    if retained.read_bytes() != raw:
                        raise ValueError("retained package evidence differs from source")
                    identities[rel]["retained"] = filename
        evidence[name] = identities
        if result["gates"][name] == "PASS" and set(identities) != set(files):
            result["gates"][name] = "FAIL"
        if kind == "rebuild" and result["gates"][name] == "PASS":
            archive = archive_paths[name][0]
            if identities["dedicated/" + archive]["sha256"] != identities["generic/" + archive]["sha256"]:
                result["gates"][name] = "FAIL"



def _cleanup_owned(path):
    _check_link(path)
    for directory, dirs, files in os.walk(path, followlinks=False):
        for name in dirs + files:
            _check_link(Path(directory) / name)
    def retry_readonly(function, filename, error):
        candidate = Path(filename)
        _check_link(candidate)
        if not candidate.absolute().is_relative_to(path.absolute()):
            raise ValueError("cleanup escaped owned scratch")
        if not isinstance(error, PermissionError):
            raise error
        candidate.chmod(stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
        function(filename)

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=retry_readonly)
    else:
        shutil.rmtree(path, onerror=lambda fn, filename, info: retry_readonly(fn, filename, info[1]))


def _gate(value):
    return value.get("status", "BLOCKED") if isinstance(value, dict) else value


def run(root, *, mode="development", commit=None, python=None, timeout=600):
    """Execute only the approved product snapshot. Formal requires an exact commit."""
    root = Path(root).absolute()
    result = {"id": NAME, "version": "UNKNOWN", "mode": mode, "commit": None, "status": "BLOCKED", "returncode": 1,
              "scope": "local regression only; no platform/release acceptance", "counts": dict.fromkeys(COUNT_KEYS, 0),
              "case_counts": _case_counts({}), "phase_counts": _phase_counts(),
              "pytest_outcomes": _pytest_outcomes(_phase_counts(), None, None, [], []),
              "gates": dict.fromkeys(("snapshot", "environment", "history", "original", "source_binding", "original_source_binding", "regression", "rebuild", "rebuilt_runtime", "original_runtime", "cleanup"), "BLOCKED")}
    evidence = None
    snapshot = None
    try:
        base = safe_path(root, RUNTIME)
        if mode not in {"development", "formal"} or (mode == "development" and commit is not None) or not 0 < timeout <= 3600:
            raise ValueError("invalid regression mode/commit")
        if mode == "formal":
            _commit(root, commit)
        head = _git(root, "rev-parse", "HEAD").decode().strip()
        if Path(_git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() != root.resolve():
            raise ValueError("root is not exact Git repository root")
        result.update(commit=commit if mode == "formal" else None, base_head=head)
        if _LOADED_PATH != safe_path(root, RUNNER):
            raise IdentityConflict("orchestrator was not loaded from selected repository")
        result["worktree"] = _worktree(root)
        if not _git(root, "check-ignore", "--", f"{RUNTIME}/receipt-probe.json"):
            raise ValueError("receipt location must be Git ignored")
        base.mkdir(parents=True, exist_ok=True)
        evidence = Path(tempfile.mkdtemp(prefix="r-", dir=base))
        snapshot = evidence / "s"
        snapshot.mkdir()
        plan, rows = _snapshot(root, snapshot, mode, commit)
        result["files"] = rows
        result["snapshot_sha256"] = digest(_json_bytes(rows))
        identities, support_raw = _supervisor_identity(root, rows, mode, commit)
        support = _load_support(root, support_raw)
        result["loaded_modules"] = identities
        result["gates"]["snapshot"] = "PASS"
        if python is None:
            preferred = safe_path(root, f"{RUNTIME}/venv/Scripts/python.exe")
            python = preferred if preferred.is_file() else Path(sys.executable)
        python = Path(python).absolute()
        environment = support.inspect_environment(python)
        original = support.inspect_candidate(root)
        # Read selection from the isolated selected snapshot, never the live catalog.
        # Tiny synthetic executor tests have no catalog in their explicit allowlist.
        current = prior = None
        history_version = "1.2.0"
        if "products/catalog.json" in rows:
            catalog = json.loads(_regular(snapshot, "products/catalog.json"))
            item, = (p for p in catalog["products"] if p["id"] == NAME)
            history_version = result["version"] = item["active_version"]
            if history_version not in ("1.2.0", "1.2.1", "1.2.2"):
                raise ValueError("unsupported active consultant version")
        history = support.inspect_history(root, version=history_version)
        if history_version in ("1.2.1", "1.2.2"):
            historical_rows = {path: {"canonical_sha256": row["sha256"]} for path, row in history["delivery"]["blobs"].items()}
            historical_binding = (_sealed_source_binding(historical_rows, history["sealed"], support.CANDIDATE_MEMBERS)
                                  if history["delivery"]["status"] == "PASS" else history["delivery"]["status"])
            current = support.inspect_current(root, rows, catalog, version=history_version)
            result["current"] = current
            result["gates"].update(current_source_binding=current["source_binding"],
                                   current_original=current["integrity"], current_archive_binding=current["archive_binding"],
                                   current_rebuild="BLOCKED", current_rebuilt_runtime="BLOCKED", current_original_runtime="BLOCKED")
            if current["status"] == "PASS":
                for rel in _current_files(history_version):
                    raw = _regular(root, rel)
                    if digest(raw) != current["files"][rel]["sha256"]:
                        raise ValueError("current original identity changed during snapshot creation")
                    target = safe_path(snapshot, rel)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open("xb") as stream:
                        stream.write(raw)
        if history_version == "1.2.2":
            prior = support.inspect_prior_121(root, catalog)
            result["prior_121"] = prior
            result["gates"].update(prior_121_source_binding=prior["source_binding"],
                                   prior_121_original=prior["integrity"], prior_121_rebuild="BLOCKED",
                                   prior_121_rebuilt_runtime="BLOCKED", prior_121_original_runtime="BLOCKED")
            if prior["status"] == "PASS":
                for rel in CURRENT_FILES:
                    raw = _regular(root, rel)
                    if digest(raw) != prior["files"][Path(rel).name]["sha256"]:
                        raise ValueError("prior 1.2.1 original identity changed during snapshot creation")
                    target = safe_path(snapshot, rel)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open("xb") as stream:
                        stream.write(raw)
        result.update(environment=environment, history=history, original=original)
        result["gates"].update(environment=_gate(environment), original=_gate(original.get("integrity")),
                               source_binding=historical_binding if current is not None else _sealed_source_binding(rows, history["sealed"], support.CANDIDATE_MEMBERS),
                               original_source_binding=_gate(original.get("source_binding")),
                               history="FAIL" if any(_gate(g) == "FAIL" for g in history.values()) else
                               "PASS" if all(_gate(g) == "PASS" for g in history.values()) else "BLOCKED")
        if _gate(original) == "PASS":
            for rel, expected in ORIGINAL.items():
                raw = _regular(root, rel)
                if digest(raw) != expected:
                    raise ValueError("original identity changed during snapshot creation")
                target = safe_path(snapshot, rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as stream:
                    stream.write(raw)
        required = [*plan["case_ids"], *plan["added_case_ids"]]
        result["required_baseline_ids"] = required
        selectors = [rel for rel in APPROVED_FILES if rel.startswith(f"{SOURCE}/tests/test_") and rel.endswith(".py")] + list(ROOT_NODES)
        result["selectors"] = selectors
        if _gate(environment) == "PASS":
            git_dir = _git(root, "rev-parse", "--absolute-git-dir").decode().strip()
            child_env = {"GIT_DIR": git_dir, "WANGBIN_CONSULTANT_TEST_CANDIDATE_ROOT": str(snapshot),
                         "WANGBIN_CONSULTANT_TEST_SOURCE_REPO": str(root), "WANGBIN_CONSULTANT_TEST_SOURCE_COMMIT": SEALED_COMMIT,
                         "TMP": str(snapshot), "TEMP": str(snapshot), "TMPDIR": str(snapshot)}
            blockers = _prerequisites(history, original, required)
            if current is not None:
                blockers.update(_current_prerequisites(current, required, version=history_version))
            if prior is not None:
                blockers.update(_current_prerequisites(prior, required, version="1.2.1"))
            tests = execute_cases(snapshot, evidence, python, selectors, blockers,
                                  timeout=timeout, env=child_env, baseline=required)
            result.update({k: v for k, v in tests.items() if k not in {"status", "returncode"}})
            result["gates"]["regression"] = tests["status"]
            _package_evidence(snapshot, evidence, result, current=current is not None, version=history_version)
        else:
            result["cases"] = {node: {"status": "BLOCKED", "reason": "required independent environment unavailable"} for node in required}
            result["counts"]["unexecuted"] = len(required)
            result["case_counts"] = _case_counts(result["cases"])
        for rel, row in rows.items():
            after = _regular(snapshot, rel)
            source_bytes = _blob(root, commit, rel) if mode == "formal" else _regular(root, rel)
            if digest(after) != row["sha256"] or digest(source_bytes) != row["sha256"]:
                raise ValueError(f"snapshot or source drift: {rel}")
        if (Path(support.__file__).absolute() != safe_path(root, SUPPORT) or
                _supervisor_identity(root, rows, mode, commit, support_raw)[0] != identities):
            raise ValueError("orchestrator identity drift during execution")
        if support.inspect_environment(python) != environment:
            raise ValueError("environment status changed during execution")
        after_history = support.inspect_history(root, version=history_version)
        if current is not None:
            if support.inspect_current(root, rows, catalog, version=history_version) != current:
                raise ValueError("current seal or original identity changed during execution")
            if current["status"] == "PASS" and any(digest(_regular(snapshot, rel)) != current["files"][rel]["sha256"] for rel in _current_files(history_version)):
                raise ValueError("current snapshot original identity changed during execution")
        if prior is not None:
            if support.inspect_prior_121(root, catalog) != prior:
                raise ValueError("prior 1.2.1 identity changed during execution")
            if prior["status"] == "PASS" and any(digest(_regular(snapshot, rel)) != prior["files"][Path(rel).name]["sha256"] for rel in CURRENT_FILES):
                raise ValueError("prior 1.2.1 snapshot original identity changed during execution")
        if after_history != history or support.inspect_candidate(root) != original:
            raise ValueError("history or original identity changed during execution")
        if _git(root, "rev-parse", "HEAD").decode().strip() != head:
            raise ValueError("HEAD drift during execution")
        result["worktree_after"] = _worktree(root)
        if result["worktree_after"] != result["worktree"]:
            raise ValueError("worktree status drift during execution")
        if _gate(original) == "PASS" and any(digest(_regular(root, rel)) != sha or digest(_regular(snapshot, rel)) != sha for rel, sha in ORIGINAL.items()):
            raise ValueError("original identity changed during execution")
    except IdentityConflict as exc:
        result["reason"] = str(exc)
        result["gates"]["snapshot"] = "FAIL"
    except (OSError, ValueError, KeyError, ImportError, subprocess.SubprocessError) as exc:
        result["reason"] = str(exc)
        result["gates"]["snapshot"] = "FAIL" if result["gates"]["snapshot"] == "PASS" else "BLOCKED"
    finally:
        if snapshot is not None and snapshot.exists():
            try:
                _cleanup_owned(snapshot)
                result["gates"]["cleanup"] = "PASS"
            except (OSError, ValueError) as exc:
                result["gates"]["cleanup"] = "FAIL"
                result["cleanup_error"] = str(exc)
        gates = result["gates"].values()
        result["status"] = "FAIL" if "FAIL" in gates else "PASS" if all(g == "PASS" for g in gates) else "BLOCKED"
        result["returncode"] = 0 if result["status"] == "PASS" else 1
        if evidence is not None:
            result["evidence"] = {p.name: digest(p.read_bytes()) for p in sorted(evidence.iterdir()) if p.is_file()}
            receipt = evidence / "receipt.json"
            _write(receipt, result)
            result["receipt"] = str(receipt)
            result["receipt_sha256"] = digest(receipt.read_bytes())
    return result


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "_worker":
        return _worker(argv[1:])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "prepare-env", "prepare-history", "restore-original"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--python", type=Path)
    parser.add_argument("--mode", choices=("development", "formal"), default="development")
    parser.add_argument("--commit")
    parser.add_argument("--source-dir", type=Path)
    parser.add_argument("--timeout", type=float, default=600)
    args = parser.parse_args(argv)
    if args.command == "run":
        result = run(args.root, mode=args.mode, commit=args.commit, python=args.python, timeout=args.timeout)
    else:
        from . import consultant_regression_support as support
        if args.command == "prepare-env":
            result = support.prepare_environment(args.root, args.python or Path(sys.executable))
        elif args.command == "prepare-history":
            catalog = json.loads(_regular(args.root, "products/catalog.json"))
            item, = (p for p in catalog["products"] if p["id"] == NAME)
            result = support.prepare_history(args.root, version=item["active_version"])
        else:
            if args.source_dir is None:
                parser.error("restore-original requires --source-dir")
            result = support.restore_candidate(args.root, args.source_dir)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result.get("status") == "PASS" else 1


# Exact approved file selection; never recursively copy a live product tree.
APPROVED_FILES = (
    'AGENTS.md',
    'agent.md',
    'docs/development-task-template.md',
    'packages/experts/wangbin-software-consultant/.codebuddy-plugin/plugin.json',
    'packages/experts/wangbin-software-consultant/LICENSE',
    'packages/experts/wangbin-software-consultant/README.md',
    'packages/experts/wangbin-software-consultant/agents/wangbin-software-consultant.md',
    'packages/experts/wangbin-software-consultant/avatars/expert.png',
    'packages/experts/wangbin-software-consultant/docs/acceptance-cases.md',
    'packages/experts/wangbin-software-consultant/docs/decimal-integration.md',
    'packages/experts/wangbin-software-consultant/docs/input-output-contract.md',
    'packages/experts/wangbin-software-consultant/docs/p01-r5-rate-policy-addendum.md',
    'packages/experts/wangbin-software-consultant/docs/p01-r7-s29-acceptance.md',
    'packages/experts/wangbin-software-consultant/docs/p01-r8-s10-s31-acceptance.md',
    'packages/experts/wangbin-software-consultant/docs/requirements.md',
    'packages/experts/wangbin-software-consultant/docs/traceability.csv',
    'packages/experts/wangbin-software-consultant/experiments/decimal-poc/fixture_branches_synthetic.json',
    'packages/experts/wangbin-software-consultant/experiments/decimal-poc/fixture_synthetic.json',
    'packages/experts/wangbin-software-consultant/skills/wangbin-estimate-calculator/LICENSE',
    'packages/experts/wangbin-software-consultant/skills/wangbin-estimate-calculator/SKILL.md',
    'packages/experts/wangbin-software-consultant/skills/wangbin-estimate-calculator/references/input-output-contract.md',
    'packages/experts/wangbin-software-consultant/skills/wangbin-estimate-calculator/scripts/estimator.py',
    'packages/experts/wangbin-software-consultant/tests/cross-domain-scenarios.json',
    'packages/experts/wangbin-software-consultant/tests/fixtures/buffer-unconfirmed-sentence.input.json',
    'packages/experts/wangbin-software-consultant/tests/fixtures/buffer-unknown-explicit-cn.input.json',
    'packages/experts/wangbin-software-consultant/tests/fixtures/precision-boundary.input.json',
    'packages/experts/wangbin-software-consultant/tests/fixtures/regression-baseline.json',
    'packages/experts/wangbin-software-consultant/tests/scenarios.json',
    'packages/experts/wangbin-software-consultant/tests/test_buffer_source.py',
    'packages/experts/wangbin-software-consultant/tests/test_bundled_calculator.py',
    'packages/experts/wangbin-software-consultant/tests/test_consultant_regression.py',
    'packages/experts/wangbin-software-consultant/tests/test_consultant_regression_support.py',
    'packages/experts/wangbin-software-consultant/tests/test_duplicate_json.py',
    'packages/experts/wangbin-software-consultant/tests/test_estimator_v2_contract.py',
    'packages/experts/wangbin-software-consultant/tests/test_expert_candidate.py',
    'packages/experts/wangbin-software-consultant/tests/test_fix1_three_output_units.py',
    'packages/experts/wangbin-software-consultant/tests/test_fix2_oa_schedule_units.py',
    'packages/experts/wangbin-software-consultant/tests/test_fixed_price_source.py',
    'packages/experts/wangbin-software-consultant/tests/test_industry_method_20.py',
    'packages/experts/wangbin-software-consultant/tests/test_p01_contract.py',
    'packages/experts/wangbin-software-consultant/tests/test_p01_r3_focus.py',
    'packages/experts/wangbin-software-consultant/tests/test_p01_r4_separation.py',
    'packages/experts/wangbin-software-consultant/tests/test_p01_r6_s29_gap.py',
    'packages/experts/wangbin-software-consultant/tests/test_p01_r7_s29_delivery.py',
    'packages/experts/wangbin-software-consultant/tests/test_p01_r8_s10_s31.py',
    'packages/experts/wangbin-software-consultant/tests/test_p03_mes_iot_contract.py',
    'packages/experts/wangbin-software-consultant/tests/test_p03_wms_contract.py',
    'packages/experts/wangbin-software-consultant/tests/test_p04_ai_cost_contract.py',
    'packages/experts/wangbin-software-consultant/tests/test_p04_ecommerce_contract.py',
    'packages/experts/wangbin-software-consultant/tests/test_quote_change_sequence.py',
    'packages/experts/wangbin-software-consultant/tests/test_source_line_locator.py',
    'products/catalog.json',
    'pyproject.toml',
    'tests/test_product_factory.py',
    'tooling/__init__.py',
    'tooling/consultant_regression.py',
    'tooling/consultant_regression_support.py',
    'tooling/expert_rules.py',
    'tooling/generators.py',
    'tooling/phase5_expert_packager.py',
    'tooling/product_factory.py',
    'tooling/products.py',
    'tooling/similarity.py',
    'tooling/validators/__init__.py',
    'tooling/validators/project_validator.py',
    'tooling/validators/secret_scanner.py',
)

if __name__ == "__main__":
    raise SystemExit(main())
