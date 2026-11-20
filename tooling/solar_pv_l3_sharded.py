"""Preserve the R7 prototype; gate R8 formal file shards separately.

Neither mode replaces ``l3-solar``/``verify``. The R8 full entry is blocked
until independent resource and input-identity admission can be established.
The existing bundle memory budget and its lifetime high-water check are unchanged.
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


# R8 mode is deliberately separate from the R7 prototype. In particular none
# of _run/_execute/_select or their CLI arguments change.
def _formal_prerequisites(pandoc: Path) -> dict:
    from .solar_pv_l3_sharded_verify import LIMIT
    if os.name != 'nt':
        raise GateError('formal OS Job Object gate requires Windows')
    if not pandoc.is_absolute() or not pandoc.is_file() or pandoc.is_symlink():
        raise GateError('absolute, regular Pandoc executable required')
    if _sha(pandoc) != '81b551129ae36faa420e07223390252547af92e00e2cc570bc57fee61ccbc623':
        raise GateError('Pandoc exe bytes differ from authorized R8 identity')
    version = subprocess.run([str(pandoc), '--version'], capture_output=True, text=True,
                             timeout=20, check=True).stdout.splitlines()[0]
    if version != 'pandoc 3.14':
        raise GateError('Pandoc version mismatch')
    if any(os.environ.get(key) for key in ('PYTEST_ADDOPTS', 'PYTEST_PLUGINS', 'PYTHONPATH')):
        raise GateError('uncontrolled pytest selection or Python import environment')
    import psutil
    if psutil.__version__ != '7.2.2':
        raise GateError('psutil runtime version not pinned to audited environment')
    if LIMIT != 512 * 1024 * 1024:
        raise GateError('OS resource limit drift')
    return {'path': str(pandoc), 'sha256': _sha(pandoc), 'version': version}


def _unlinked_input(name: str) -> Path:
    path = ROOT
    for part in Path(name).parts:
        path = path / part
        if path.is_symlink() or getattr(path.lstat(), 'st_file_attributes', 0) & 0x400:
            raise GateError(f'linked formal input: {name}')
    if not path.is_file() or not path.resolve().is_relative_to(ROOT.resolve()):
        raise GateError(f'missing or escaped formal input: {name}')
    return path


def _formal_identity() -> dict:
    # R7's executable surface excludes archived report fixtures. R8 binds the
    # tracked report bytes too; no historical receipt is modified.
    from .solar_pv_regression import _git
    identity = _identity()
    names = [os.fsdecode(item) for item in _git('ls-files', '-z', 'reports/solar-pv').split(b'\0') if item]
    reports = {}
    for name in names:
        reports[name] = _sha(_unlinked_input(name))
    identity['report_inputs'] = reports
    identity['report_sha256'] = hashlib.sha256(json.dumps(reports, sort_keys=True,
                                                        separators=(',', ':')).encode()).hexdigest()
    # These historical test inputs are ignored by Git; a Git-only inventory
    # would silently miss their mutation or absence. This is not a claim that
    # every dynamic/ignored input in the entire suite has been inventoried.
    historical = 'r2-client-552-20261113-132354/workspaces'
    fixture_names = (
        f'.runtime/solar-pv/{historical}/industrial_rooftop/roof-primary/CH08-1-request.json',
        f'.runtime/solar-pv/{historical}/utility_scale_ground/ground-primary/CH08-1-request.json',
    )
    fixtures = {}
    for name in fixture_names:
        fixtures[name] = _sha(_unlinked_input(name))
    identity['ignored_fixture_inputs'] = fixtures
    identity['ignored_fixture_sha256'] = hashlib.sha256(json.dumps(
        fixtures, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return identity


def _job_guard():
    """Kernel hard private-commit limit for entire process tree; no sampling substitute.

    Accounting catches children that exit between samples. Job creation/assignment
    errors block rather than silently falling back to observing the launcher.
    """
    from ctypes import wintypes
    from .solar_pv_l3_sharded_verify import LIMIT
    class Basic(ctypes.Structure):
        _fields_ = [('user_time', ctypes.c_int64), ('job_time', ctypes.c_int64),
                    ('flags', wintypes.DWORD), ('min_ws', ctypes.c_size_t),
                    ('max_ws', ctypes.c_size_t), ('active', wintypes.DWORD),
                    ('affinity', ctypes.c_size_t), ('priority', wintypes.DWORD),
                    ('scheduling', wintypes.DWORD)]
    class IO(ctypes.Structure):
        _fields_ = [(key, ctypes.c_uint64) for key in ('reads', 'writes', 'other',
                     'read_bytes', 'written_bytes', 'other_bytes')]
    class Extended(ctypes.Structure):
        _fields_ = [('basic', Basic), ('io', IO), ('process_limit', ctypes.c_size_t),
                    ('job_limit', ctypes.c_size_t), ('peak_process', ctypes.c_size_t),
                    ('peak_job', ctypes.c_size_t)]
    class Accounting(ctypes.Structure):
        _fields_ = [('total_user', ctypes.c_int64), ('total_kernel', ctypes.c_int64),
                    ('this_user', ctypes.c_int64), ('this_kernel', ctypes.c_int64),
                    ('total_page_faults', wintypes.DWORD), ('total_processes', wintypes.DWORD),
                    ('active_processes', wintypes.DWORD), ('terminated_processes', wintypes.DWORD)]
    dll = ctypes.WinDLL('kernel32', use_last_error=True)
    dll.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    dll.CreateJobObjectW.restype = wintypes.HANDLE
    dll.SetInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int,
                                            ctypes.c_void_p, wintypes.DWORD)
    dll.SetInformationJobObject.restype = wintypes.BOOL
    dll.QueryInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int,
                                              ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p)
    dll.QueryInformationJobObject.restype = wintypes.BOOL
    dll.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    dll.AssignProcessToJobObject.restype = wintypes.BOOL
    dll.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
    dll.CloseHandle.argtypes = (wintypes.HANDLE,)
    handle = dll.CreateJobObjectW(None, None)
    if not handle:
        raise GateError(f'CreateJobObjectW failed: {ctypes.get_last_error()}')
    limits = Extended()
    limits.basic.flags = 0x100 | 0x200 | 0x2000  # process, job, kill-on-close
    limits.process_limit = LIMIT
    limits.job_limit = LIMIT
    if not dll.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
        error = ctypes.get_last_error()
        dll.CloseHandle(handle)
        raise GateError(f'SetInformationJobObject failed: {error}')
    return dll, handle, Extended, Accounting


def _formal_process(command: list[str], directory: Path, timeout: int,
                    identity: dict, conditions: dict, pandoc: dict, kind: str) -> dict:
    from .solar_pv_l3_sharded_verify import LIMIT
    from ctypes import wintypes
    import psutil
    directory.mkdir(exist_ok=False)
    tmp, base = directory / 'workspace-tmp', directory / 'pytest-basetemp'
    tmp.mkdir()
    env = os.environ.copy()
    env.update({'TMPDIR': str(tmp), 'TMP': str(tmp), 'TEMP': str(tmp),
                'PYTHONPATH': conditions['pythonpath'], 'PYTHONDONTWRITEBYTECODE': '1',
                'WANGBIN_SOLAR_PV_PANDOC': pandoc['path']})
    entry = {'schema': 'solar-pv-l3-sharded-process/1', 'kind': kind, 'command': command,
             'scratch': {'TMPDIR': str(tmp), 'basetemp': str(base)},
             'pandoc': pandoc, 'identity_before': _formal_identity(), 'conditions_before': _conditions(),
             'started_utc': datetime.now(timezone.utc).isoformat(), 'timed_out': False,
             'resource': {'enforcement': 'OS_JOB_MEMORY_HARD_LIMIT', 'limit_bytes': LIMIT,
                          'max_current_bytes': 0, 'max_lifetime_peak_bytes': 0,
                          'actual_child_observed': False, 'complete_tree_accounting': False,
                          'guard_error': None}}
    proc = None
    job = None
    seen = {}
    try:
        if entry['identity_before'] != identity or entry['conditions_before'] != conditions:
            raise GateError('frozen input/environment drift before process')
        dll, job, Extended, Accounting = _job_guard()
        with ((directory / 'stdout.log').open('xb') as stdout,
              (directory / 'stderr.log').open('xb') as stderr):
            proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stdout,
                                    stderr=stderr, creationflags=0x4)  # CREATE_SUSPENDED
            if not dll.AssignProcessToJobObject(job, proc._handle):
                raise GateError(f'AssignProcessToJobObject failed: {ctypes.get_last_error()}')
            # CPython Popen closes ht. A suspended process has exactly one
            # thread. Open it by TID only after it belongs to the hard-limited job.
            tids = psutil.Process(proc.pid).threads()
            if len(tids) != 1:
                raise GateError('suspended process thread identity ambiguous')
            dll.OpenThread.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
            dll.OpenThread.restype = wintypes.HANDLE
            thread = dll.OpenThread(0x0002, False, tids[0].id)
            if not thread:
                raise GateError('cannot open suspended child thread')
            try:
                dll.ResumeThread.argtypes = (wintypes.HANDLE,)
                dll.ResumeThread.restype = wintypes.DWORD
                if dll.ResumeThread(thread) != 1:
                    raise GateError('cannot resume hard-limited child')
            finally:
                dll.CloseHandle(thread)
            deadline = time.monotonic() + timeout
            while True:
                try:
                    parent = psutil.Process(proc.pid)
                    processes = [parent, *parent.children(recursive=True)]
                    current = 0
                    for process in processes:
                        try:
                            mem = process.memory_info()
                            key = (process.pid, process.create_time())
                            seen[key] = max(seen.get(key, 0), mem.rss,
                                            getattr(mem, 'peak_wset', mem.rss))
                            current += mem.rss
                            if process.pid != proc.pid and 'python' in process.name().lower():
                                entry['resource']['actual_child_observed'] = True
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            entry['resource']['guard_error'] = 'process lost/denied during sample'
                    entry['resource']['max_current_bytes'] = max(entry['resource']['max_current_bytes'], current)
                    entry['resource']['max_lifetime_peak_bytes'] = sum(seen.values())
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    if proc.poll() is None or not any(pid == proc.pid for pid, _ in seen):
                        entry['resource']['guard_error'] = 'launcher lost before tree accounting'
                if time.monotonic() >= deadline and proc.poll() is None:
                    entry['timed_out'] = True
                    break
                if proc.poll() is not None:
                    break
                time.sleep(0.05)
            accounting, ext = Accounting(), Extended()
            if not dll.QueryInformationJobObject(job, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None):
                raise GateError('OS job accounting unavailable')
            if not dll.QueryInformationJobObject(job, 9, ctypes.byref(ext), ctypes.sizeof(ext), None):
                raise GateError('OS job peak unavailable')
            entry['resource']['total_job_processes'] = accounting.total_processes
            entry['resource']['peak_job_private_commit_bytes'] = ext.peak_job
            entry['resource']['complete_tree_accounting'] = accounting.total_processes == len(seen)
            if (entry['timed_out'] or entry['resource']['guard_error']
                    or accounting.active_processes != 0
                    or not entry['resource']['complete_tree_accounting']
                    or not entry['resource']['actual_child_observed']
                    or entry['resource']['max_current_bytes'] > LIMIT
                    or entry['resource']['max_lifetime_peak_bytes'] > LIMIT
                    or ext.peak_job > LIMIT):
                raise GateError('timeout, incomplete OS process tree or 512MiB limit exceeded')
            entry['exit_code'] = proc.wait(timeout=5)
    except (OSError, ValueError, psutil.Error, GateError) as exc:
        entry['error'] = str(exc)
    finally:
        if job:
            dll.TerminateJobObject(job, 1) if proc and proc.poll() is None else None
            dll.CloseHandle(job)
        if proc:
            try:
                entry['exit_code'] = proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                entry['exit_code'] = proc.wait()
        entry['finished_utc'] = datetime.now(timezone.utc).isoformat()
        entry['identity_after'], entry['conditions_after'] = _formal_identity(), _conditions()
        for name in ('stdout', 'stderr'):
            path = directory / f'{name}.log'
            if path.exists():
                entry[f'{name}_sha256'] = _sha(path)
        xml = directory / 'junit.xml'
        if xml.exists():
            entry['junit_sha256'] = _sha(xml)
        (directory / 'receipt.json').write_text(json.dumps(entry, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return entry


def _formal_run(out: Path, pandoc_path: Path, timeout: int, selected: list[str]) -> int:
    from .solar_pv_l3_sharded_verify import verify, _collection, _hash, _xml
    if not 10 <= timeout <= 14400:
        raise GateError('formal per-file timeout must be 10..14400 seconds')
    if not selected:
        # B1 is a development deliverable. Hard-block B3 until the independent
        # B2 reviewer proves physical-working-set coverage and wheel bytes.
        raise GateError('formal full BLOCKED: B2 OS working-set/wheel-byte admission not established')
    out = out.resolve()
    if out.exists() or out == ROOT or ROOT in out.parents:
        raise GateError('formal evidence requires a new private directory outside repository')
    pandoc = _formal_prerequisites(pandoc_path)
    files = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / 'tests/solar-pv').glob('test_*.py'))
    if selected:
        if not 2 <= len(selected) <= 3 or sorted(set(selected)) != sorted(selected) or any(f not in files for f in selected):
            raise GateError('smoke accepts 2-3 distinct complete test files only')
        files = sorted(selected)
    identity, conditions = _formal_identity(), _conditions()
    out.mkdir(parents=True, exist_ok=False)
    summary = {'schema': 'solar-pv-l3-sharded/1', 'mode': 'smoke' if selected else 'full',
               'verdict': 'INCOMPLETE', 'identity': identity, 'conditions': conditions,
               'pandoc': pandoc, 'files': files, 'collected_ids': [], 'collection_sha256': None,
               'shards': [], 'process_timeout_seconds': timeout}
    try:
        folder = out / 'collect'
        selection = files if selected else ['tests/solar-pv']
        command = [sys.executable, '-m', 'pytest', *selection, '-q', '-ra', '-p', 'no:cacheprovider',
                   f'--basetemp={folder / "pytest-basetemp"}', '--collect-only']
        receipt = _formal_process(command, folder, timeout, identity, conditions, pandoc, 'collect')
        if receipt.get('error') or receipt.get('exit_code') != 0:
            raise GateError('collection process failed; raw receipt retained')
        ids = _collection((folder / 'stdout.log').read_bytes())
        if sorted({n.split('::')[0] for n in ids}) != files:
            raise GateError('collection file inventory does not match complete scope')
        summary['collected_ids'] = ids
        summary['collection_sha256'] = _hash('\n'.join(ids).encode())
        for index, name in enumerate(files):
            folder = out / f'shard-{index:03d}'
            command = [sys.executable, '-m', 'pytest', name, '-q', '-ra', '-p', 'no:cacheprovider',
                       f'--basetemp={folder / "pytest-basetemp"}', f'--junitxml={folder / "junit.xml"}']
            receipt = _formal_process(command, folder, timeout, identity, conditions, pandoc, 'shard')
            summary['shards'].append(folder.name)
            if receipt.get('error') or receipt.get('exit_code') != 0 or 'junit_sha256' not in receipt:
                raise GateError(f'failed shard: {name}; raw receipt retained')
            parsed = _xml((folder / 'junit.xml').read_bytes())
            if list(parsed) != [n for n in ids if n.split('::')[0] == name]:
                raise GateError(f'shard IDs differ from frozen collection: {name}')
        # Only an independent reparse of every raw artifact can mark completed.
        summary['verdict'] = 'SMOKE_ONLY' if selected else 'FULL_ALL_PASSED'
    except (GateError, OSError, ValueError, ET.ParseError) as exc:
        summary['error'] = str(exc)
    finally:
        (out / 'summary.json').write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    if summary.get('error'):
        return 2
    try:
        result = verify(out)
        return 0 if result['verdict'] == summary['verdict'] else 2
    except (GateError, OSError, ValueError, ET.ParseError):
        return 2


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == 'full':
        formal = argparse.ArgumentParser(description='R8 formal L3; new immutable external evidence')
        formal.add_argument('--out', type=Path, required=True)
        formal.add_argument('--pandoc', type=Path, required=True)
        formal.add_argument('--timeout', type=int, default=7200)
        formal.add_argument('--smoke-select', action='append', default=[])
        args = formal.parse_args(argv[1:])
        try:
            return _formal_run(args.out, args.pandoc, args.timeout, args.smoke_select)
        except (GateError, OSError, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            print(f'BLOCKED: {exc}', file=sys.stderr)
            return 2
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
