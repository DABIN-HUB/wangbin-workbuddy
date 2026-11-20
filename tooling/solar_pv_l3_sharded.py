"""Bounded *prototype* for auditing disjoint solar-PV pytest processes.

No full-tree mode and no replacement for ``l3-solar``/``verify``. Each selected
file is collected once, then executed in its own fresh process. The existing
bundle memory budget and its lifetime high-water check are not changed.
"""
from __future__ import annotations

import argparse
import ctypes
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from .solar_pv_regression import GateError, ROOT, _conditions, _identity, _junit, _node_cases

MAX_PROTOTYPE_FILES = 3
MAX_COLLECTION_BYTES = 2_000_000
PROTOTYPE_FILES = frozenset({
    "tests/solar-pv/test_method_configuration.py",
    "tests/solar-pv/test_phase3e_irr_roots.py",
    "tests/solar-pv/test_solar_pv_regression_tool.py",
})

@lru_cache(maxsize=1)
def _windows_counters():
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("faults", wintypes.DWORD)] + [
            (key, ctypes.c_size_t) for key in ("peak", "current", "paged_peak",
            "paged", "nonpaged_peak", "nonpaged", "pagefile", "pagefile_peak")]
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
    return Counters, psapi.GetProcessMemoryInfo

def _sample_memory(proc: subprocess.Popen) -> tuple[int, int] | None:
    if os.name != "nt":
        return None
    counters, get_info = _windows_counters()
    values = counters()
    values.cb = ctypes.sizeof(values)
    if not get_info(proc._handle, ctypes.byref(values), values.cb):
        return None
    return values.current, values.peak

def _sample_process_tree(proc: subprocess.Popen) -> list[tuple[int, int, int]]:
    # Optional observation only: never change Meter's own budget/checks.
    # Windows venv python.exe may be a small launcher spawning the actual
    # interpreter; sampling only Popen's PID can therefore be misleading.
    try:
        import psutil
    except ImportError:
        return []
    try:
        parent = psutil.Process(proc.pid)
        processes = [parent, *parent.children(recursive=True)]
        readings = []
        for process in processes:
            try:
                memory = process.memory_info()
                readings.append((process.pid, memory.rss,
                                 getattr(memory, "peak_wset", memory.rss)))
            except psutil.Error:
                pass
        return readings
    except psutil.Error:
        return []


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _select(files: list[str]) -> tuple[str, ...]:
    if not 2 <= len(files) <= MAX_PROTOTYPE_FILES or len(set(files)) != len(files):
        raise GateError("prototype requires 2-3 distinct test files")
    for name in files:
        path = ROOT / name
        if (name not in PROTOTYPE_FILES or path.is_symlink() or not path.is_file()
                or not path.resolve().is_relative_to(ROOT.resolve())):
            raise GateError(f"invalid prototype selection: {name}")
    return tuple(sorted(files))


def _collect_ids(log: Path, files: tuple[str, ...]) -> list[str]:
    if log.stat().st_size > MAX_COLLECTION_BYTES:
        raise GateError("oversized collection log")
    text = log.read_text(encoding="utf-8", errors="replace")
    ids = [line.strip() for line in text.splitlines()
           if line.startswith("tests/solar-pv/") and "::" in line]
    match = re.search(r"(?:^|\n)(\d+) tests? collected\b", text)
    if (not ids or not match or len(ids) != int(match.group(1))
            or len(ids) != len(set(ids))
            or any(name.split("::", 1)[0] not in files for name in ids)):
        raise GateError("incomplete, duplicate, or out-of-scope collection")
    return ids


def _execute(command: list[str], directory: Path, timeout: int, expected_identity: dict,
             expected_conditions: dict) -> dict:
    directory.mkdir(exist_ok=False)
    tmp = directory / "workspace-tmp"
    tmp.mkdir()
    base = directory / "pytest-basetemp"
    env = os.environ.copy()
    env.update({"TMPDIR": str(tmp), "TMP": str(tmp), "TEMP": str(tmp),
                "PYTHONPATH": expected_conditions["pythonpath"],
                "PYTHONDONTWRITEBYTECODE": "1"})
    entry = {"command": command, "started_utc": datetime.now(timezone.utc).isoformat(),
             "scratch": {"TMPDIR": str(tmp), "basetemp": str(base)},
             "identity_before": _identity(), "conditions_before": _conditions()}
    if entry["identity_before"] != expected_identity or entry["conditions_before"] != expected_conditions:
        raise GateError("prototype input or environment drift before process")
    started = time.monotonic()
    with (directory / "output.log").open("x", encoding="utf-8") as stream:
        proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stream,
                                stderr=subprocess.STDOUT)
        deadline = started + timeout
        resource = {"source": "Windows GetProcessMemoryInfo, sampled; not the bundle Meter",
                    "samples": 0, "max_current_working_set_bytes": 0,
                    "max_os_lifetime_peak_bytes": 0,
                    "process_tree_sampler": "optional psutil, not a runtime dependency",
                    "process_tree_peak_by_pid_bytes": {}}
        while proc.poll() is None:
            sample = _sample_memory(proc)
            if sample is not None:
                resource["samples"] += 1
                resource["max_current_working_set_bytes"] = max(
                    resource["max_current_working_set_bytes"], sample[0])
                resource["max_os_lifetime_peak_bytes"] = max(
                    resource["max_os_lifetime_peak_bytes"], sample[1])
            for pid, current, peak in _sample_process_tree(proc):
                key = str(pid)
                prior = resource["process_tree_peak_by_pid_bytes"].get(key, 0)
                resource["process_tree_peak_by_pid_bytes"][key] = max(prior, current, peak)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                entry["timed_out"] = True
                if os.name == "nt":
                    tree = subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                                          capture_output=True, timeout=15, check=False)
                    entry["timeout_tree_kill_exit"] = tree.returncode
                if proc.poll() is None:
                    proc.kill()
                break
            try:
                proc.wait(timeout=min(remaining, 0.25))
            except subprocess.TimeoutExpired:
                pass
        entry["exit_code"] = proc.wait()
        entry["os_memory"] = (resource if resource["samples"] or
                              resource["process_tree_peak_by_pid_bytes"] else
                              {"source": "UNAVAILABLE"})
    entry["finished_utc"] = datetime.now(timezone.utc).isoformat()
    entry["elapsed_seconds"] = round(time.monotonic() - started, 3)
    entry["log_sha256"] = _sha(directory / "output.log")
    entry["identity_after"] = _identity()
    entry["conditions_after"] = _conditions()
    if (entry["identity_after"] != expected_identity
            or entry["conditions_after"] != expected_conditions):
        entry["identity_drift"] = True
    xml = directory / "junit.xml"
    if xml.is_file():
        entry["junit_sha256"] = _sha(xml)
        try:
            parsed = _junit(xml)
            entry["junit"] = {"counts": parsed["counts"],
                              "element_counts": parsed["element_counts"],
                              "declared_tests": parsed["declared_tests"],
                              "unrepresented_tests": parsed["unrepresented_tests"],
                              "skips": parsed["skips"]}
            entry["executed_ids"] = list(_node_cases(parsed["cases"]))
        except (GateError, ValueError, ET.ParseError) as exc:
            entry["evidence_error"] = str(exc)
    elif "--collect-only" not in command:
        entry["evidence_error"] = "missing shard JUnit"
    (directory / "receipt.json").write_text(
        json.dumps(entry, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return entry


def _run(files: list[str], out: Path, timeout: int) -> int:
    selected = _select(files)
    out = out.resolve()
    if out.exists() or out == ROOT or ROOT in out.parents:
        raise GateError("prototype output must be a new directory outside the worktree")
    if timeout < 10 or timeout > 600:
        raise GateError("prototype per-process timeout must be 10..600 seconds")
    # A converter identity is not established in prototype scope. OMML tests
    # must not be silently attempted through an inherited PATH or env override.
    if os.environ.get("WANGBIN_SOLAR_PV_PANDOC") or shutil.which("pandoc"):
        raise GateError("Pandoc-bound tests require separately approved executable identity")
    conditions, identity = _conditions(), _identity()
    out.mkdir(parents=True, exist_ok=False)
    summary = {"schema": "solar-pv-sharded-prototype/1",
               "verdict": "INCOMPLETE", "formal_l3_replacement": False,
               "selection": selected, "identity": identity, "conditions": conditions,
               "pandoc_identity": "NOT_CONFIGURED", "process_timeout_seconds": timeout,
               "collect": None, "shards": []}
    try:
        collect_dir = out / "collect"
        command = [sys.executable, "-m", "pytest", *selected, "-q", "-ra",
                   "-p", "no:cacheprovider", f"--basetemp={collect_dir / 'pytest-basetemp'}",
                   "--collect-only"]
        collected = _execute(command, collect_dir, timeout, identity, conditions)
        summary["collect"] = collected
        if collected["exit_code"] or collected.get("timed_out") or collected.get("identity_drift"):
            raise GateError("collection did not finish on frozen identity")
        ids = _collect_ids(collect_dir / "output.log", selected)
        collected["collected_ids"] = ids
        collected["collected_sha256"] = hashlib.sha256("\n".join(ids).encode()).hexdigest()
        # A receipt is immutable once written; write the augmented collection
        # metadata only to the top-level aggregate, never rewrite raw receipts.
        for index, name in enumerate(selected):
            expected = [node for node in ids if node.split("::", 1)[0] == name]
            if not expected:
                raise GateError(f"empty selected test file: {name}")
            shard_dir = out / f"shard-{index:02d}"
            command = [sys.executable, "-m", "pytest", name, "-q", "-ra",
                       "-p", "no:cacheprovider", f"--basetemp={shard_dir / 'pytest-basetemp'}",
                       f"--junitxml={shard_dir / 'junit.xml'}"]
            shard = _execute(command, shard_dir, timeout, identity, conditions)
            shard["assigned_ids"] = expected
            summary["shards"].append(shard)
            if (shard["exit_code"] or shard.get("timed_out") or shard.get("identity_drift")
                    or shard.get("evidence_error") or shard.get("executed_ids") != expected
                    or shard.get("junit", {}).get("counts", {}).get("failure", 0)
                    or shard.get("junit", {}).get("counts", {}).get("error", 0)):
                raise GateError(f"shard incomplete, failed or node mismatch: {name}")
        executed = [node for shard in summary["shards"] for node in shard["executed_ids"]]
        if len(executed) != len(set(executed)) or set(executed) != set(ids):
            raise GateError("duplicate, missing or unknown shard nodes")
        if any(shard["junit"]["unrepresented_tests"] or shard["junit"]["skips"]
               for shard in summary["shards"]):
            summary["verdict"] = "COVERED_WITH_SKIPS_OR_UNREPRESENTED_TESTS_PROTOTYPE_ONLY"
            summary["error"] = "skipped assertions or unrepresented subtests are not passed"
            return 2
        else:
            summary["verdict"] = "PASSED_PROTOTYPE_ONLY"
        return 0
    except (GateError, OSError, ValueError, ET.ParseError) as exc:
        summary["error"] = str(exc)
        summary["verdict"] = "NOT_PASSED_PROTOTYPE_ONLY"
        return 2
    finally:
        (out / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--select", action="append", required=True,
                        help="repeat for 2-3 explicit small solar-PV test files")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=180, help="seconds per process")
    args = parser.parse_args(argv)
    try:
        return _run(args.select, args.out, args.timeout)
    except (GateError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
