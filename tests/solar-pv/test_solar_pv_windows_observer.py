"""Authorized real-Windows probes for the native process-tree observer.

These tests launch real Windows processes and assert native API observations. They
are intentionally skipped on non-Windows hosts; no synthetic resource receipt is
accepted as a substitute for the Windows run.
"""
from __future__ import annotations

import os
import json
from pathlib import Path
import sys
import textwrap
import time

import pytest

from tooling.solar_pv_windows_observer import (
    ProcessAccessError,
    WindowsProcessTreeObserver,
    read_process_snapshot,
    run_observed,
)
from tooling.solar_pv_windows_observer_verify import EvidenceError, verify


pytestmark = pytest.mark.skipif(os.name != "nt", reason="requires native Windows APIs")


def _python(code: str) -> list[str]:
    return [sys.executable, "-c", textwrap.dedent(code)]


def _child_tree_code() -> str:
    grandchild = "import time; time.sleep(0.12)"
    return (
        "import subprocess, sys, time\n"
        f"grandchild = subprocess.Popen([sys.executable, '-c', {grandchild!r}])\n"
        "time.sleep(0.18)\n"
        "grandchild.wait()\n"
    )


def test_native_snapshot_reports_real_memory_creation_and_parent_values():
    snapshot = read_process_snapshot(os.getpid())

    assert snapshot.pid == os.getpid()
    assert snapshot.creation_time_100ns > 0
    assert snapshot.parent_pid is not None
    assert snapshot.memory.working_set_bytes > 0
    assert snapshot.memory.peak_working_set_bytes >= snapshot.memory.working_set_bytes
    assert snapshot.memory.private_usage_bytes > 0
    assert snapshot.image_path


def test_job_lifecycle_captures_parent_descendants_and_short_children():
    child_code = _child_tree_code()
    parent_code = (
        "import subprocess, sys, time\n"
        f"child = subprocess.Popen([sys.executable, '-c', {child_code!r}])\n"
        "short = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(0.01)'])\n"
        "short.wait()\n"
        "child.wait()\n"
        "time.sleep(0.05)\n"
    )

    report = run_observed(_python(parent_code), timeout=10)

    assert report.raw_evidence_complete
    assert report.complete_tree_accounting
    assert report.job_accounting["active_processes"] == 0
    assert report.job_accounting["total_processes"] == len(report.processes)
    assert report.job_accounting["process_private_commit_limit_bytes"] == 512 * 1024**2
    assert report.job_accounting["job_private_commit_limit_bytes"] == 512 * 1024**2
    assert 0 < report.job_accounting["peak_job_private_commit_bytes"] <= 512 * 1024**2
    assert len(report.processes) >= 4
    assert len({(p.pid, p.creation_time_100ns) for p in report.processes}) == len(report.processes)
    assert report.root_pid in {p.pid for p in report.processes}
    assert any(p.parent_pid == report.root_pid for p in report.processes if p.pid != report.root_pid)
    assert all(p.exit_event_seen for p in report.processes)
    assert all(p.memory.peak_working_set_bytes >= p.memory.working_set_bytes for p in report.processes)
    assert any(p.memory.peak_working_set_bytes > 0 for p in report.processes)
    assert any(event.get("message") == "NEW_PROCESS" for event in report.raw_events)
    assert any(event.get("message") == "EXIT_PROCESS" for event in report.raw_events)

    # The raw peaks are genuine, but Microsoft's contract does not make the
    # notification stream an admissible no-missed-child proof.
    assert report.verdict == "BLOCKED"
    assert not report.admission_ready
    assert any("not guaranteed" in reason for reason in report.blockers)


def test_native_peak_working_set_survives_allocation_and_free(tmp_path):
    ready = tmp_path / "allocated.ready"
    release = tmp_path / "release.signal"
    code = f"""
        import ctypes
        import os
        import time
        size = 32 * 1024 * 1024
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel32.VirtualAlloc.restype = ctypes.c_void_p
        kernel32.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong, ctypes.c_ulong]
        kernel32.VirtualFree.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong]
        address = kernel32.VirtualAlloc(None, size, 0x3000, 0x04)
        if not address:
            raise ctypes.WinError(ctypes.get_last_error())
        ctypes.memset(address, 0xA5, size)
        open({str(ready)!r}, 'w', encoding='ascii').write(str(os.getpid()))
        while not os.path.exists({str(release)!r}):
            time.sleep(0.01)
        if not kernel32.VirtualFree(address, 0, 0x8000):
            raise ctypes.WinError(ctypes.get_last_error())
        time.sleep(0.12)
    """

    observer = WindowsProcessTreeObserver.launch(_python(code), cwd=tmp_path)
    try:
        observer.resume()
        deadline = time.monotonic() + 5
        while (not observer.processes or not ready.exists()) and time.monotonic() < deadline:
            observer.pump(50)
        assert observer.processes
        assert ready.exists()
        target_pid = int(ready.read_text(encoding="ascii"))
        while not any(process.pid == target_pid for process in observer.processes) and time.monotonic() < deadline:
            observer.pump(50)
        live = observer.capture_live_snapshot(target_pid)
        assert live.memory.peak_working_set_bytes >= 8 * 1024 * 1024
        release.write_text("release", encoding="ascii")
        report = observer.wait(timeout=5)
    finally:
        observer.close()

    assert report.raw_evidence_complete
    target = next(p for p in report.processes if p.pid == target_pid)
    assert target.memory.peak_working_set_bytes >= target.memory.working_set_bytes
    assert target.observed_peak_working_set_bytes >= live.memory.peak_working_set_bytes
    assert target.final_memory is not None
    assert target.live_snapshot_count >= 2
    assert not report.lifetime_peak_proof
    assert target.memory.private_usage_bytes >= 0


def test_access_denied_is_an_observed_native_error_not_an_empty_snapshot():
    with pytest.raises(ProcessAccessError) as caught:
        # PID 4 is the protected System process on supported Windows hosts.
        read_process_snapshot(4)

    assert caught.value.winerror == 5
    assert "OpenProcess" in str(caught.value)


def test_incomplete_event_lifecycle_fails_closed_on_timeout():
    observer = WindowsProcessTreeObserver.launch(_python("import time; time.sleep(1)"))
    try:
        observer.resume()
        report = observer.wait(timeout=0.05)
    finally:
        observer.close()

    assert report.timed_out
    assert not report.raw_evidence_complete
    assert not report.admission_ready
    assert any("timeout" in reason for reason in report.blockers)


def test_completion_port_loss_fails_closed_with_native_error():
    observer = WindowsProcessTreeObserver.launch(_python("import time; time.sleep(0.4)"))
    try:
        observer.resume()
        # Deliberately destroy the native monitor port. This is a narrow,
        # explicitly authorized failure probe, not a production code path.
        observer._close_completion_port_for_probe()
        report = observer.wait(timeout=2)
    finally:
        observer.close()

    assert not report.raw_evidence_complete
    assert not report.admission_ready
    assert any("monitor" in reason.lower() for reason in report.blockers)
    assert report.monitor_error is not None
    assert report.monitor_error["winerror"] in {6, 995}


def test_report_serialization_keeps_pid_creation_time_and_raw_events():
    report = run_observed(_python("import time; time.sleep(0.08)"), timeout=5)
    data = report.to_dict()

    assert data["schema"] == "solar-pv-windows-observer/1"
    assert data["root"]["pid"] == report.root_pid
    assert data["root"]["creation_time_100ns"] == report.root_creation_time_100ns
    assert data["processes"]
    assert all("pid" in item and "creation_time_100ns" in item for item in data["processes"])
    assert data["raw_events"]
    assert data["physical_peak_source"] == "GetProcessMemoryInfo.PROCESS_MEMORY_COUNTERS_EX.PeakWorkingSetSize"
    assert data["private_commit_source"] == "JobObjectExtendedLimitInformation.PeakJobMemoryUsed"


def test_separate_verifier_recomputes_native_receipt_without_admitting_full(tmp_path):
    report = run_observed(_python("import time; time.sleep(0.12)"), timeout=5)
    path = tmp_path / "resource.json"
    report.write_json(path)
    result = verify(path)
    assert result["internal_consistency"] is True
    assert result["process_count"] == report.job_accounting["total_processes"]
    assert result["job_private_commit_limit_bytes"] == 512 * 1024**2
    assert result["native_attestation"] is False
    assert result["verdict"] == "BLOCKED"


def test_separate_verifier_rejects_rewritten_resource_peaks_and_claims(tmp_path):
    report = run_observed(_python("import time; time.sleep(0.12)"), timeout=5)
    original = report.to_dict()
    for key, changed in (("physical_peak_working_set_bytes", 1),
                         ("verdict", "PASS"),
                         ("lifetime_peak_proof", True)):
        mutated = json.loads(json.dumps(original))
        mutated[key] = changed
        path = tmp_path / f"tampered-{key}.json"
        path.write_text(json.dumps(mutated), encoding="utf-8")
        with pytest.raises(EvidenceError):
            verify(path)
    over_limit = json.loads(json.dumps(original))
    over_limit["processes"][0]["observed_peak_working_set_bytes"] = 512 * 1024**2 + 1
    over_limit["physical_peak_working_set_bytes"] = 512 * 1024**2 + 1
    over_limit["sum_peak_working_set_bytes"] = sum(
        process["observed_peak_working_set_bytes"] for process in over_limit["processes"])
    path = tmp_path / "tampered-over-512.json"
    path.write_text(json.dumps(over_limit), encoding="utf-8")
    with pytest.raises(EvidenceError):
        verify(path)
    self_parent = json.loads(json.dumps(original))
    child = next(process for process in self_parent["processes"]
                 if process["pid"] != self_parent["root"]["pid"])
    child["parent_pid"] = child["pid"]
    path = tmp_path / "tampered-self-parent.json"
    path.write_text(json.dumps(self_parent), encoding="utf-8")
    with pytest.raises(EvidenceError):
        verify(path)
    root_parent = json.loads(json.dumps(original))
    root_process = next(process for process in root_parent["processes"]
                        if process["pid"] == root_parent["root"]["pid"])
    root_process["parent_pid"] = root_process["pid"]
    path = tmp_path / "tampered-root-self-parent.json"
    path.write_text(json.dumps(root_parent), encoding="utf-8")
    with pytest.raises(EvidenceError):
        verify(path)
    post_exit = json.loads(json.dumps(original))
    post_exit["processes"][0]["final_memory_after_exit"]["peak_working_set_bytes"] = 600 * 1024**2
    path = tmp_path / "tampered-post-exit-peak.json"
    path.write_text(json.dumps(post_exit), encoding="utf-8")
    with pytest.raises(EvidenceError):
        verify(path)
