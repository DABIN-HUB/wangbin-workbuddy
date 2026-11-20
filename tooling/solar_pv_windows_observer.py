"""Fail-closed native Windows process-tree lifecycle observation.

The observer launches the root process suspended, associates an inactive Job
Object with a completion port, assigns the root before resuming it, and reads
per-process lifetime counters from ``GetProcessMemoryInfo``. It never uses
sampling to manufacture a peak. ``PeakWorkingSetSize`` is a lifetime
high-water value returned by Windows for a retained process handle.

This module deliberately does not claim a complete process-tree admission gate.
Microsoft documents ordinary Job completion-port process notifications as not
guaranteed. A run therefore remains ``BLOCKED`` for admission even when the
raw counters, Job accounting, and observed events are internally complete.
"""
from __future__ import annotations

from dataclasses import dataclass
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Mapping, Sequence


_SCHEMA = "solar-pv-windows-observer/1"
_LIMIT_BYTES = 512 * 1024 * 1024
_PROCESS_QUERY_INFORMATION = 0x0400
_PROCESS_VM_READ = 0x0010
_SYNCHRONIZE = 0x00100000
_CREATE_SUSPENDED = 0x00000004
_CREATE_UNICODE_ENVIRONMENT = 0x00000400
_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
_JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
_JOB_OBJECT_ASSOCIATE_COMPLETION_PORT_INFORMATION = 7
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION = 1
_WAIT_OBJECT_0 = 0
_WAIT_TIMEOUT = 258
_INFINITE = 0xFFFFFFFF
_ERROR_ACCESS_DENIED = 5
_ERROR_INVALID_HANDLE = 6
_ERROR_OPERATION_ABORTED = 995
_JOB_OBJECT_MSG_ACTIVE_PROCESS_ZERO = 4
_JOB_OBJECT_MSG_NEW_PROCESS = 6
_JOB_OBJECT_MSG_EXIT_PROCESS = 7
_JOB_OBJECT_MSG_ABNORMAL_EXIT_PROCESS = 8


class NativeObserverError(RuntimeError):
    """A required native operation failed."""

    def __init__(self, operation: str, winerror: int | None = None, detail: str = ""):
        self.operation = operation
        self.winerror = winerror
        suffix = f" (WinError {winerror})" if winerror is not None else ""
        super().__init__(f"{operation}{suffix}{': ' + detail if detail else ''}")


class ObserverUnsupported(NativeObserverError):
    """The native Windows observer was requested on a non-Windows host."""


class ProcessAccessError(NativeObserverError):
    """OpenProcess or a required process query was denied."""


class MonitorLostError(NativeObserverError):
    """The Job completion-port monitor could no longer be read."""


@dataclass(frozen=True, slots=True)
class ProcessMemory:
    working_set_bytes: int
    peak_working_set_bytes: int
    private_usage_bytes: int
    page_fault_count: int

    def to_dict(self) -> dict[str, int]:
        return {
            "working_set_bytes": self.working_set_bytes,
            "peak_working_set_bytes": self.peak_working_set_bytes,
            "private_usage_bytes": self.private_usage_bytes,
            "page_fault_count": self.page_fault_count,
        }


@dataclass(frozen=True, slots=True)
class ProcessSnapshot:
    pid: int
    creation_time_100ns: int
    parent_pid: int
    image_path: str
    memory: ProcessMemory

    def to_dict(self) -> dict[str, object]:
        return {
            "pid": self.pid,
            "creation_time_100ns": self.creation_time_100ns,
            "parent_pid": self.parent_pid,
            "image_path": self.image_path,
            "memory": self.memory.to_dict(),
        }


@dataclass(slots=True)
class ProcessRecord:
    snapshot: ProcessSnapshot
    new_event_seen: bool = True
    exit_event_seen: bool = False
    exit_message: str | None = None
    exit_code: int | None = None
    handle: int | None = None
    live_snapshot_count: int = 1
    observed_peak_working_set_bytes: int = 0
    final_memory: ProcessMemory | None = None

    @property
    def pid(self) -> int:
        return self.snapshot.pid

    @property
    def creation_time_100ns(self) -> int:
        return self.snapshot.creation_time_100ns

    @property
    def parent_pid(self) -> int:
        return self.snapshot.parent_pid

    @property
    def image_path(self) -> str:
        return self.snapshot.image_path

    @property
    def memory(self) -> ProcessMemory:
        return self.snapshot.memory

    def to_dict(self) -> dict[str, object]:
        return {
            **self.snapshot.to_dict(),
            "new_event_seen": self.new_event_seen,
            "exit_event_seen": self.exit_event_seen,
            "exit_message": self.exit_message,
            "exit_code": self.exit_code,
            "live_snapshot_count": self.live_snapshot_count,
            "observed_peak_working_set_bytes": self.observed_peak_working_set_bytes,
            "final_memory_after_exit": self.final_memory.to_dict() if self.final_memory else None,
            "lifetime_peak_valid": False,
        }


@dataclass(slots=True)
class ObservationReport:
    command: list[str]
    root_pid: int
    root_creation_time_100ns: int
    processes: list[ProcessRecord]
    raw_events: list[dict[str, object]]
    job_accounting: dict[str, int]
    complete_tree_accounting: bool
    raw_evidence_complete: bool
    timed_out: bool
    monitor_error: dict[str, object] | None
    blockers: list[str]
    resumed: bool
    active_process_zero_seen: bool
    lifetime_peak_proof: bool

    @property
    def physical_peak_working_set_bytes(self) -> int:
        """Largest native PeakWorkingSetSize returned by a live snapshot."""
        return max((p.observed_peak_working_set_bytes for p in self.processes), default=0)

    @property
    def sum_peak_working_set_bytes(self) -> int:
        """Conservative sum of per-process lifetime peaks, not simultaneous RSS."""
        return sum(p.observed_peak_working_set_bytes for p in self.processes)

    @property
    def admission_ready(self) -> bool:
        return self.raw_evidence_complete and self.lifetime_peak_proof and not self.blockers

    @property
    def verdict(self) -> str:
        return "PASS" if self.admission_ready else "BLOCKED"

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": _SCHEMA,
            "verdict": self.verdict,
            "admission_ready": self.admission_ready,
            "command": self.command,
            "root": {
                "pid": self.root_pid,
                "creation_time_100ns": self.root_creation_time_100ns,
            },
            "processes": [p.to_dict() for p in self.processes],
            "raw_events": self.raw_events,
            "job_accounting": self.job_accounting,
            "complete_tree_accounting": self.complete_tree_accounting,
            "raw_evidence_complete": self.raw_evidence_complete,
            "timed_out": self.timed_out,
            "resumed": self.resumed,
            "active_process_zero_seen": self.active_process_zero_seen,
            "lifetime_peak_proof": self.lifetime_peak_proof,
            "monitor_error": self.monitor_error,
            "blockers": self.blockers,
            "physical_peak_working_set_bytes": self.physical_peak_working_set_bytes,
            "sum_peak_working_set_bytes": self.sum_peak_working_set_bytes,
            "physical_peak_source": "GetProcessMemoryInfo.PROCESS_MEMORY_COUNTERS_EX.PeakWorkingSetSize",
            "private_commit_source": "JobObjectExtendedLimitInformation.PeakJobMemoryUsed",
            "process_identity_source": "GetProcessTimes + NtQueryInformationProcess.ProcessBasicInformation",
            "tree_membership_source": "JobObject completion-port events + JobObjectBasicAccountingInformation",
            "notification_reliability": "BLOCKED: Windows documents ordinary job notifications as not guaranteed",
            "peak_lifecycle_reliability": "BLOCKED: post-exit GetProcessMemoryInfo cannot prove a pre-exit lifetime peak",
        }

    def write_json(self, path: str | os.PathLike[str]) -> None:
        """Write one raw, self-contained receipt; callers must protect the path."""
        target = Path(path)
        with target.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n")


class _ProcessMemoryCountersEx(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("page_fault_count", wintypes.DWORD),
        ("peak_working_set_size", ctypes.c_size_t),
        ("working_set_size", ctypes.c_size_t),
        ("quota_peak_paged_pool_usage", ctypes.c_size_t),
        ("quota_paged_pool_usage", ctypes.c_size_t),
        ("quota_peak_non_paged_pool_usage", ctypes.c_size_t),
        ("quota_non_paged_pool_usage", ctypes.c_size_t),
        ("pagefile_usage", ctypes.c_size_t),
        ("peak_pagefile_usage", ctypes.c_size_t),
        ("private_usage", ctypes.c_size_t),
    ]


class _BasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("per_process_user_time", ctypes.c_int64),
        ("per_job_user_time", ctypes.c_int64),
        ("limit_flags", wintypes.DWORD),
        ("minimum_working_set_size", ctypes.c_size_t),
        ("maximum_working_set_size", ctypes.c_size_t),
        ("active_process_limit", wintypes.DWORD),
        ("affinity", ctypes.c_size_t),
        ("priority_class", wintypes.DWORD),
        ("scheduling_class", wintypes.DWORD),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in (
        "read_operations", "write_operations", "other_operations",
        "read_transfer_bytes", "write_transfer_bytes", "other_transfer_bytes",
    )]


class _ExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("basic_limit_information", _BasicLimitInformation),
        ("io_info", _IoCounters),
        ("process_memory_limit", ctypes.c_size_t),
        ("job_memory_limit", ctypes.c_size_t),
        ("peak_process_memory_used", ctypes.c_size_t),
        ("peak_job_memory_used", ctypes.c_size_t),
    ]


class _BasicAccountingInformation(ctypes.Structure):
    _fields_ = [
        ("total_user_time", ctypes.c_int64),
        ("total_kernel_time", ctypes.c_int64),
        ("this_process_user_time", ctypes.c_int64),
        ("this_process_kernel_time", ctypes.c_int64),
        ("total_page_fault_count", wintypes.DWORD),
        ("total_processes", wintypes.DWORD),
        ("active_processes", wintypes.DWORD),
        ("terminated_processes", wintypes.DWORD),
    ]


class _AssociateCompletionPort(ctypes.Structure):
    _fields_ = [
        ("completion_key", ctypes.c_void_p),
        ("completion_port", wintypes.HANDLE),
    ]


class _StartupInfo(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lp_reserved", wintypes.LPWSTR),
        ("lp_desktop", wintypes.LPWSTR),
        ("lp_title", wintypes.LPWSTR),
        ("dw_x", wintypes.DWORD),
        ("dw_y", wintypes.DWORD),
        ("dw_x_size", wintypes.DWORD),
        ("dw_y_size", wintypes.DWORD),
        ("dw_x_count_chars", wintypes.DWORD),
        ("dw_y_count_chars", wintypes.DWORD),
        ("dw_fill_attribute", wintypes.DWORD),
        ("dw_flags", wintypes.DWORD),
        ("w_show_window", wintypes.WORD),
        ("cb_reserved2", wintypes.WORD),
        ("lp_reserved2", ctypes.POINTER(ctypes.c_byte)),
        ("h_std_input", wintypes.HANDLE),
        ("h_std_output", wintypes.HANDLE),
        ("h_std_error", wintypes.HANDLE),
    ]


class _ProcessInformation(ctypes.Structure):
    _fields_ = [
        ("h_process", wintypes.HANDLE),
        ("h_thread", wintypes.HANDLE),
        ("dw_process_id", wintypes.DWORD),
        ("dw_thread_id", wintypes.DWORD),
    ]


class _FileTime(ctypes.Structure):
    _fields_ = [("low_date_time", wintypes.DWORD), ("high_date_time", wintypes.DWORD)]


class _ProcessBasicInformation(ctypes.Structure):
    _fields_ = [
        ("exit_status", ctypes.c_long),
        ("peb_base_address", ctypes.c_void_p),
        ("affinity_mask", ctypes.c_size_t),
        ("base_priority", ctypes.c_long),
        ("unique_process_id", ctypes.c_size_t),
        ("inherited_from_unique_process_id", ctypes.c_size_t),
    ]


class _NativeApi:
    def __init__(self):
        if os.name != "nt":
            raise ObserverUnsupported("Windows native APIs are unavailable")
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self.psapi = ctypes.WinDLL("psapi", use_last_error=True)
        self.ntdll = ctypes.WinDLL("ntdll", use_last_error=True)

        self.kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel32.OpenProcess.restype = wintypes.HANDLE
        self.kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel32.CloseHandle.restype = wintypes.BOOL
        self.kernel32.GetProcessTimes.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(_FileTime), ctypes.POINTER(_FileTime),
            ctypes.POINTER(_FileTime), ctypes.POINTER(_FileTime),
        ]
        self.kernel32.GetProcessTimes.restype = wintypes.BOOL
        self.kernel32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD),
        ]
        self.kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
        self.kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self.kernel32.WaitForSingleObject.restype = wintypes.DWORD
        self.kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        self.kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        self.kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        self.kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.kernel32.TerminateProcess.restype = wintypes.BOOL
        self.kernel32.ResumeThread.argtypes = [wintypes.HANDLE]
        self.kernel32.ResumeThread.restype = wintypes.DWORD
        self.kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.kernel32.TerminateJobObject.restype = wintypes.BOOL
        self.kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        self.kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD,
        ]
        self.kernel32.SetInformationJobObject.restype = wintypes.BOOL
        self.kernel32.QueryInformationJobObject.argtypes = [
            wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p,
        ]
        self.kernel32.QueryInformationJobObject.restype = wintypes.BOOL
        self.kernel32.CreateIoCompletionPort.argtypes = [
            wintypes.HANDLE, wintypes.HANDLE, ctypes.c_size_t, wintypes.DWORD,
        ]
        self.kernel32.CreateIoCompletionPort.restype = wintypes.HANDLE
        self.kernel32.GetQueuedCompletionStatus.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(ctypes.c_size_t),
            ctypes.POINTER(ctypes.c_void_p), wintypes.DWORD,
        ]
        self.kernel32.GetQueuedCompletionStatus.restype = wintypes.BOOL
        self.kernel32.CreateProcessW.argtypes = [
            wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.c_void_p, ctypes.c_void_p,
            wintypes.BOOL, wintypes.DWORD, ctypes.c_void_p, wintypes.LPCWSTR,
            ctypes.POINTER(_StartupInfo), ctypes.POINTER(_ProcessInformation),
        ]
        self.kernel32.CreateProcessW.restype = wintypes.BOOL
        self.psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
        ]
        self.psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        self.ntdll.NtQueryInformationProcess.argtypes = [
            wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.ULONG,
            ctypes.POINTER(wintypes.ULONG),
        ]
        self.ntdll.NtQueryInformationProcess.restype = ctypes.c_long


_API: _NativeApi | None = None


def _api() -> _NativeApi:
    global _API
    if _API is None:
        _API = _NativeApi()
    return _API


def _require_windows() -> None:
    if os.name != "nt":
        raise ObserverUnsupported("Windows native observer requires os.name == 'nt'")


def _handle_value(handle: object) -> int:
    value = getattr(handle, "value", handle)
    if value is None:
        return 0
    return int(value)


def _close_handle(handle: int | None) -> None:
    if handle:
        _api().kernel32.CloseHandle(wintypes.HANDLE(handle))


def _filetime_value(value: _FileTime) -> int:
    return (int(value.high_date_time) << 32) | int(value.low_date_time)


def _query_parent_pid(api: _NativeApi, handle: int, pid: int) -> int:
    info = _ProcessBasicInformation()
    returned = wintypes.ULONG()
    status = api.ntdll.NtQueryInformationProcess(
        wintypes.HANDLE(handle), 0, ctypes.byref(info), ctypes.sizeof(info), ctypes.byref(returned)
    )
    if status != 0:
        raise NativeObserverError(
            f"NtQueryInformationProcess(parent,pid={pid})", int(status) & 0xFFFFFFFF
        )
    return int(info.inherited_from_unique_process_id)


def _query_image_path(api: _NativeApi, handle: int, pid: int) -> str:
    buffer = ctypes.create_unicode_buffer(32768)
    length = wintypes.DWORD(len(buffer))
    if not api.kernel32.QueryFullProcessImageNameW(
        wintypes.HANDLE(handle), 0, buffer, ctypes.byref(length)
    ):
        raise NativeObserverError(
            f"QueryFullProcessImageNameW(pid={pid})", ctypes.get_last_error()
        )
    return buffer.value[: int(length.value)]


def _query_memory(api: _NativeApi, handle: int, pid: int) -> ProcessMemory:
    counters = _ProcessMemoryCountersEx()
    counters.cb = ctypes.sizeof(counters)
    if not api.psapi.GetProcessMemoryInfo(
        wintypes.HANDLE(handle), ctypes.byref(counters), counters.cb
    ):
        raise NativeObserverError(
            f"GetProcessMemoryInfo(pid={pid})", ctypes.get_last_error()
        )
    return ProcessMemory(
        working_set_bytes=int(counters.working_set_size),
        peak_working_set_bytes=int(counters.peak_working_set_size),
        private_usage_bytes=int(counters.private_usage),
        page_fault_count=int(counters.page_fault_count),
    )


def _snapshot_from_handle(api: _NativeApi, handle: int, pid: int) -> ProcessSnapshot:
    creation, exit_time, kernel_time, user_time = (_FileTime() for _ in range(4))
    if not api.kernel32.GetProcessTimes(
        wintypes.HANDLE(handle), ctypes.byref(creation), ctypes.byref(exit_time),
        ctypes.byref(kernel_time), ctypes.byref(user_time)
    ):
        raise NativeObserverError(f"GetProcessTimes(pid={pid})", ctypes.get_last_error())
    return ProcessSnapshot(
        pid=pid,
        creation_time_100ns=_filetime_value(creation),
        parent_pid=_query_parent_pid(api, handle, pid),
        image_path=_query_image_path(api, handle, pid),
        memory=_query_memory(api, handle, pid),
    )


def _open_process(pid: int) -> int:
    api = _api()
    handle = api.kernel32.OpenProcess(
        _PROCESS_QUERY_INFORMATION | _PROCESS_VM_READ | _SYNCHRONIZE, False, int(pid)
    )
    value = _handle_value(handle)
    if not value:
        code = ctypes.get_last_error()
        if code == _ERROR_ACCESS_DENIED:
            raise ProcessAccessError(f"OpenProcess(pid={pid})", code)
        raise NativeObserverError(f"OpenProcess(pid={pid})", code)
    return value


def read_process_snapshot(pid: int) -> ProcessSnapshot:
    """Read one process using native handles and lifetime counters.

    The caller receives a creation-time identity and must not use a PID alone
    for later correlation. Access failure is raised, never converted to zero.
    """
    _require_windows()
    pid = int(pid)
    if pid <= 0:
        raise NativeObserverError(f"OpenProcess(pid={pid})", 87)
    handle = _open_process(pid)
    try:
        return _snapshot_from_handle(_api(), handle, pid)
    finally:
        _close_handle(handle)


def _environment_block(env: Mapping[str, str]) -> ctypes.Array[ctypes.c_wchar]:
    values = []
    for key in sorted(env):
        if "=" in key or "\x00" in key or "\x00" in str(env[key]):
            raise ValueError("invalid Windows environment key/value")
        values.append(f"{key}={env[key]}")
    return ctypes.create_unicode_buffer("\0".join(values) + "\0\0")


def _create_suspended_process(
    command: Sequence[str], cwd: str | os.PathLike[str] | None, env: Mapping[str, str] | None,
) -> tuple[int, int, int]:
    if not command or any(not isinstance(part, (str, os.PathLike)) for part in command):
        raise ValueError("command must contain at least one string path/argument")
    api = _api()
    command_line = subprocess.list2cmdline([os.fspath(part) for part in command])
    command_buffer = ctypes.create_unicode_buffer(command_line)
    startup = _StartupInfo()
    startup.cb = ctypes.sizeof(startup)
    info = _ProcessInformation()
    env_buffer = None
    environment = None
    flags = _CREATE_SUSPENDED
    if env is not None:
        env_buffer = _environment_block(env)
        environment = ctypes.cast(env_buffer, ctypes.c_void_p)
        flags |= _CREATE_UNICODE_ENVIRONMENT
    cwd_text = os.fspath(cwd) if cwd is not None else None
    if not api.kernel32.CreateProcessW(
        None, command_buffer, None, None, False, flags, environment, cwd_text,
        ctypes.byref(startup), ctypes.byref(info)
    ):
        raise NativeObserverError("CreateProcessW(CREATE_SUSPENDED)", ctypes.get_last_error())
    return _handle_value(info.h_process), _handle_value(info.h_thread), int(info.dw_process_id)


def _create_job_and_port() -> tuple[int, int]:
    api = _api()
    job = _handle_value(api.kernel32.CreateJobObjectW(None, None))
    if not job:
        raise NativeObserverError("CreateJobObjectW", ctypes.get_last_error())
    try:
        limits = _ExtendedLimitInformation()
        limits.basic_limit_information.limit_flags = (
            _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            | _JOB_OBJECT_LIMIT_PROCESS_MEMORY
            | _JOB_OBJECT_LIMIT_JOB_MEMORY
        )
        limits.process_memory_limit = _LIMIT_BYTES
        limits.job_memory_limit = _LIMIT_BYTES
        if not api.kernel32.SetInformationJobObject(
            wintypes.HANDLE(job), _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits), ctypes.sizeof(limits)
        ):
            raise NativeObserverError("SetInformationJobObject(extended limits)", ctypes.get_last_error())
        invalid = wintypes.HANDLE(ctypes.c_void_p(-1).value)
        port = _handle_value(api.kernel32.CreateIoCompletionPort(invalid, None, 0, 1))
        if not port:
            raise NativeObserverError("CreateIoCompletionPort", ctypes.get_last_error())
        association = _AssociateCompletionPort(
            completion_key=ctypes.c_void_p(1), completion_port=wintypes.HANDLE(port)
        )
        if not api.kernel32.SetInformationJobObject(
            wintypes.HANDLE(job), _JOB_OBJECT_ASSOCIATE_COMPLETION_PORT_INFORMATION,
            ctypes.byref(association), ctypes.sizeof(association)
        ):
            _close_handle(port)
            raise NativeObserverError("SetInformationJobObject(completion port)", ctypes.get_last_error())
        return job, port
    except Exception:
        _close_handle(job)
        raise


class WindowsProcessTreeObserver:
    """Observe one suspended-root Job Object without sampling the process tree."""

    def __init__(
        self, *, command: list[str], job: int, completion_port: int, process_handle: int,
        thread_handle: int, root_snapshot: ProcessSnapshot,
    ):
        self.command = command
        self._job = job
        self._completion_port = completion_port
        self._root_process_handle = process_handle
        self._thread_handle = thread_handle
        self._root_snapshot = root_snapshot
        self._resumed = False
        self._closed = False
        self._timed_out = False
        self._monitor_error: dict[str, object] | None = None
        self._operational_blocked = False
        self._blockers: list[str] = [
            "Windows documents ordinary Job completion-port process notifications as not guaranteed; no-missed-child proof is unavailable",
            "Job private commit is measured separately; simultaneous physical working-set peak is not measured",
            "GetProcessMemoryInfo after process exit cannot prove the process lifetime peak; no native pre-exit lifecycle barrier exists",
        ]
        self._raw_events: list[dict[str, object]] = []
        self._records: list[ProcessRecord] = []
        self._active_by_pid: dict[int, ProcessRecord] = {}
        self._handles: dict[int, int] = {root_snapshot.pid: process_handle}
        self._accounting = {"total_processes": 0, "active_processes": 0, "terminated_processes": 0,
                            "process_private_commit_limit_bytes": 0, "job_private_commit_limit_bytes": 0,
                            "peak_job_private_commit_bytes": 0}
        self._active_process_zero_seen = False
        self._root_exited = False


    @classmethod
    def launch(
        cls, command: Sequence[str], *, cwd: str | os.PathLike[str] | None = None,
        env: Mapping[str, str] | None = None,
    ) -> "WindowsProcessTreeObserver":
        """Create an inactive Job, launch suspended, assign, then expose ``resume``."""
        _require_windows()
        command_list = [os.fspath(part) for part in command]
        job, port = _create_job_and_port()
        process = thread = None
        try:
            process, thread, pid = _create_suspended_process(command_list, cwd, env)
            snapshot = _snapshot_from_handle(_api(), process, pid)
            if not _api().kernel32.AssignProcessToJobObject(
                wintypes.HANDLE(job), wintypes.HANDLE(process)
            ):
                raise NativeObserverError("AssignProcessToJobObject", ctypes.get_last_error())
            return cls(
                command=command_list, job=job, completion_port=port,
                process_handle=process, thread_handle=thread, root_snapshot=snapshot,
            )
        except Exception:
            if process:
                _api().kernel32.TerminateProcess(wintypes.HANDLE(process), 1)
            _close_handle(thread)
            _close_handle(process)
            _close_handle(port)
            _close_handle(job)
            raise

    def resume(self) -> None:
        if self._closed:
            raise NativeObserverError("ResumeThread", detail="observer is closed")
        if self._resumed:
            raise NativeObserverError("ResumeThread", detail="root was already resumed")
        result = _api().kernel32.ResumeThread(wintypes.HANDLE(self._thread_handle))
        if result == 0xFFFFFFFF:
            raise NativeObserverError("ResumeThread", ctypes.get_last_error())
        if result != 1:
            raise NativeObserverError("ResumeThread", detail=f"unexpected suspend count {result}")
        self._resumed = True
        self._raw_events.append({"kind": "control", "event": "RESUME", "pid": self._root_snapshot.pid})

    def _block(self, reason: str) -> None:
        self._operational_blocked = True
        if reason not in self._blockers:
            self._blockers.append(reason)

    def _query_accounting(self) -> bool:
        info = _BasicAccountingInformation()
        if not _api().kernel32.QueryInformationJobObject(
            wintypes.HANDLE(self._job), _JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION,
            ctypes.byref(info), ctypes.sizeof(info), None
        ):
            code = ctypes.get_last_error()
            self._block(f"JobObjectBasicAccountingInformation failed (WinError {code})")
            return False
        limits = _ExtendedLimitInformation()
        if not _api().kernel32.QueryInformationJobObject(
            wintypes.HANDLE(self._job), _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits), ctypes.sizeof(limits), None
        ):
            self._block(f"JobObjectExtendedLimitInformation failed (WinError {ctypes.get_last_error()})")
            return False
        flags = limits.basic_limit_information.limit_flags
        required = (_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | _JOB_OBJECT_LIMIT_PROCESS_MEMORY
                    | _JOB_OBJECT_LIMIT_JOB_MEMORY)
        if (flags & required != required or limits.process_memory_limit != _LIMIT_BYTES
                or limits.job_memory_limit != _LIMIT_BYTES):
            self._block("512 MiB Job private-commit limit missing or changed")
        self._accounting = {
            "total_processes": int(info.total_processes),
            "active_processes": int(info.active_processes),
            "terminated_processes": int(info.terminated_processes),
            "process_private_commit_limit_bytes": int(limits.process_memory_limit),
            "job_private_commit_limit_bytes": int(limits.job_memory_limit),
            "peak_job_private_commit_bytes": int(limits.peak_job_memory_used),
        }
        return True

    def _monitor_failure(self, operation: str, winerror: int) -> None:
        self._monitor_error = {"operation": operation, "winerror": int(winerror)}
        self._block(f"monitor lost: {operation} (WinError {winerror})")

    def _next_message(self, timeout_ms: int) -> tuple[int, int] | None:
        if not self._completion_port:
            self._monitor_failure("GetQueuedCompletionStatus(completion port closed)", _ERROR_INVALID_HANDLE)
            return None
        transferred = wintypes.DWORD()
        key = ctypes.c_size_t()
        overlapped = ctypes.c_void_p()
        ok = _api().kernel32.GetQueuedCompletionStatus(
            wintypes.HANDLE(self._completion_port), ctypes.byref(transferred), ctypes.byref(key),
            ctypes.byref(overlapped), timeout_ms
        )
        if not ok:
            code = ctypes.get_last_error()
            if code == _WAIT_TIMEOUT:
                return None
            self._monitor_failure("GetQueuedCompletionStatus", code)
            return None
        pid = int(overlapped.value or 0)
        return int(transferred.value), pid

    def _record_new_process(self, pid: int) -> None:
        if pid <= 0 or pid in self._active_by_pid:
            self._block(f"duplicate or invalid NEW_PROCESS event for pid {pid}")
            return
        handle = self._root_process_handle if pid == self._root_snapshot.pid else None
        opened_here = False
        try:
            if handle is None:
                handle = _open_process(pid)
                opened_here = True
            snapshot = _snapshot_from_handle(_api(), handle, pid)
            if pid != self._root_snapshot.pid and snapshot.parent_pid <= 0:
                self._block(f"child pid {pid} has no native parent identity")
            record = ProcessRecord(
                snapshot=snapshot,
                handle=handle,
                observed_peak_working_set_bytes=snapshot.memory.peak_working_set_bytes,
            )
            self._records.append(record)
            self._active_by_pid[pid] = record
            self._handles[pid] = handle
            self._raw_events.append({"kind": "job", "message": "NEW_PROCESS", "message_code": _JOB_OBJECT_MSG_NEW_PROCESS, "pid": pid})
        except ProcessAccessError as exc:
            self._block(f"access denied opening NEW_PROCESS pid {pid} (WinError {exc.winerror})")
            self._raw_events.append({"kind": "job", "message": "NEW_PROCESS_ACCESS_DENIED", "message_code": _JOB_OBJECT_MSG_NEW_PROCESS, "pid": pid, "winerror": exc.winerror})
            if opened_here:
                _close_handle(handle)
        except NativeObserverError as exc:
            self._block(str(exc))
            self._raw_events.append({"kind": "job", "message": "NEW_PROCESS_QUERY_FAILED", "message_code": _JOB_OBJECT_MSG_NEW_PROCESS, "pid": pid, "winerror": exc.winerror})
            if opened_here:
                _close_handle(handle)

    def _record_exit(self, pid: int, message: str, message_code: int) -> None:
        record = self._active_by_pid.pop(pid, None)
        if record is None or record.handle is None:
            self._block(f"{message} event has no matching observed process pid {pid}")
            self._raw_events.append({"kind": "job", "message": message, "message_code": message_code, "pid": pid, "matched": False})
            return
        handle = record.handle
        wait_result = _api().kernel32.WaitForSingleObject(wintypes.HANDLE(handle), 5000)
        if wait_result != _WAIT_OBJECT_0:
            self._block(f"process handle for pid {pid} did not signal before exit evidence")
        try:
            record.final_memory = _query_memory(_api(), handle, pid)
            exit_code = wintypes.DWORD()
            if _api().kernel32.GetExitCodeProcess(wintypes.HANDLE(handle), ctypes.byref(exit_code)):
                record.exit_code = int(exit_code.value)
            else:
                self._block(f"GetExitCodeProcess failed for pid {pid} (WinError {ctypes.get_last_error()})")
        except NativeObserverError as exc:
            self._block(str(exc))
        record.exit_event_seen = True
        record.exit_message = message
        if pid == self._root_snapshot.pid:
            self._root_exited = True
        self._raw_events.append({"kind": "job", "message": message, "message_code": message_code, "pid": pid, "matched": True})
        _close_handle(handle)
        record.handle = None
        self._handles.pop(pid, None)

    def _consume(self, message_code: int, pid: int) -> None:
        if message_code == _JOB_OBJECT_MSG_NEW_PROCESS:
            self._record_new_process(pid)
        elif message_code in (_JOB_OBJECT_MSG_EXIT_PROCESS, _JOB_OBJECT_MSG_ABNORMAL_EXIT_PROCESS):
            self._record_exit(
                pid,
                "EXIT_PROCESS" if message_code == _JOB_OBJECT_MSG_EXIT_PROCESS else "ABNORMAL_EXIT_PROCESS",
                message_code,
            )
        elif message_code == _JOB_OBJECT_MSG_ACTIVE_PROCESS_ZERO:
            self._active_process_zero_seen = True
            self._raw_events.append({"kind": "job", "message": "ACTIVE_PROCESS_ZERO", "message_code": message_code, "pid": None})
        else:
            self._block(f"unexpected Job completion message code {message_code}")
            self._raw_events.append({"kind": "job", "message": "UNEXPECTED", "message_code": message_code, "pid": pid})

    def _drain_nonblocking(self) -> None:
        for _ in range(100000):
            message = self._next_message(0)
            if message is None:
                return
            self._consume(*message)

    @property
    def processes(self) -> tuple[ProcessRecord, ...]:
        """Observed records so far; callers correlate by PID and creation time."""
        return tuple(self._records)

    @property
    def root_pid(self) -> int:
        return self._root_snapshot.pid

    @property
    def root_creation_time_100ns(self) -> int:
        return self._root_snapshot.creation_time_100ns

    def pump(self, timeout_ms: int = 50) -> bool:
        """Consume at most one native Job message for a live-workload probe."""
        if self._closed:
            raise NativeObserverError("pump", detail="observer is closed")
        message = self._next_message(max(0, int(timeout_ms)))
        if message is None:
            self._query_accounting()
            return False
        self._consume(*message)
        self._query_accounting()
        return True

    def capture_live_snapshot(self, pid: int) -> ProcessSnapshot:
        """Read a member while it is alive, before a caller-controlled barrier.

        This is a diagnostic primitive for a cooperative workload that holds
        itself alive after its peak allocation. It is not a complete lifecycle
        proof: the observer cannot know that no allocation occurs after this
        read and before process exit. The report therefore remains blocked.
        """
        record = self._active_by_pid.get(int(pid))
        if record is None or record.handle is None:
            raise NativeObserverError(f"capture_live_snapshot(pid={pid})", detail="process is not observed and alive")
        try:
            snapshot = _snapshot_from_handle(_api(), record.handle, int(pid))
        except NativeObserverError as exc:
            self._block(str(exc))
            raise
        if snapshot.creation_time_100ns != record.creation_time_100ns:
            self._block(f"PID reuse detected while capturing pid {pid}")
            raise NativeObserverError(f"capture_live_snapshot(pid={pid})", detail="creation time changed")
        record.snapshot = snapshot
        record.live_snapshot_count += 1
        record.observed_peak_working_set_bytes = max(
            record.observed_peak_working_set_bytes,
            snapshot.memory.peak_working_set_bytes,
        )
        return snapshot

    def _build_report(self) -> ObservationReport:
        self._query_accounting()
        total = self._accounting["total_processes"]
        complete = (
            not self._monitor_error
            and not self._timed_out
            and self._resumed
            and bool(self._records)
            and self._accounting["active_processes"] == 0
            and total == len(self._records)
            and len(self._active_by_pid) == 0
            and all(p.new_event_seen and p.exit_event_seen for p in self._records)
            and all(p.final_memory is not None for p in self._records)
            and not self._operational_blocked
            and self._active_process_zero_seen
            and all(p.parent_pid > 0 for p in self._records)
        )
        if total != len(self._records):
            self._block(f"Job accounting total_processes={total} differs from observed NEW_PROCESS records={len(self._records)}")
        if self._accounting["active_processes"] != 0:
            self._block(f"Job accounting still has active_processes={self._accounting['active_processes']}")
        if not self._active_process_zero_seen:
            self._block("ACTIVE_PROCESS_ZERO was not observed; lifecycle event stream is incomplete")
        if any(p.parent_pid not in {r.pid for r in self._records} for p in self._records if p.pid != self._root_snapshot.pid):
            self._block("one or more observed processes has a parent outside the observed Job tree")
        if not complete:
            self._block("raw process-tree lifecycle evidence is incomplete")
        return ObservationReport(
            command=list(self.command), root_pid=self._root_snapshot.pid,
            root_creation_time_100ns=self._root_snapshot.creation_time_100ns,
            processes=list(self._records), raw_events=list(self._raw_events),
            job_accounting=dict(self._accounting), complete_tree_accounting=complete,
            raw_evidence_complete=complete, timed_out=self._timed_out,
            monitor_error=self._monitor_error, blockers=list(self._blockers),
            resumed=self._resumed, active_process_zero_seen=self._active_process_zero_seen,
            lifetime_peak_proof=False,
        )

    def wait(self, timeout: float) -> ObservationReport:
        """Drain events until Job accounting reaches zero or fail closed."""
        if self._closed:
            raise NativeObserverError("wait", detail="observer is closed")
        if not self._resumed:
            self._block("root process was not resumed")
            return self._build_report()
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            message = self._next_message(min(100, max(1, int((deadline - time.monotonic()) * 1000))))
            if message is not None:
                self._consume(*message)
            self._query_accounting()
            root_done = self._root_exited or (
                _api().kernel32.WaitForSingleObject(wintypes.HANDLE(self._root_process_handle), 0)
                == _WAIT_OBJECT_0
            )
            if root_done and self._accounting["active_processes"] == 0:
                self._drain_nonblocking()
                self._query_accounting()
                return self._build_report()
            if self._monitor_error:
                self._timed_out = True
                return self._build_report()
        self._timed_out = True
        self._block(f"observation timeout after {timeout} seconds")
        return self._build_report()

    def _close_completion_port_for_probe(self) -> None:
        """Test-only native failure injection; never used by production integration."""
        if self._completion_port:
            _close_handle(self._completion_port)
            self._completion_port = None

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._job:
            active = self._query_accounting() and self._accounting["active_processes"] != 0
            if active:
                _api().kernel32.TerminateJobObject(wintypes.HANDLE(self._job), 1)
        for handle in list(self._handles.values()):
            if handle:
                _api().kernel32.WaitForSingleObject(wintypes.HANDLE(handle), 2000)
        for handle in list(self._handles.values()):
            _close_handle(handle)
        self._handles.clear()
        _close_handle(self._thread_handle)
        self._thread_handle = 0
        if self._completion_port:
            _close_handle(self._completion_port)
            self._completion_port = 0
        _close_handle(self._job)
        self._job = 0

    def __enter__(self) -> "WindowsProcessTreeObserver":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def run_observed(
    command: Sequence[str], *, timeout: float, cwd: str | os.PathLike[str] | None = None,
    env: Mapping[str, str] | None = None,
) -> ObservationReport:
    """Launch, assign before resume, observe, and always clean up the Job."""
    observer = WindowsProcessTreeObserver.launch(command, cwd=cwd, env=env)
    try:
        observer.resume()
        return observer.wait(timeout)
    finally:
        observer.close()


__all__ = [
    "NativeObserverError", "ObserverUnsupported", "ProcessAccessError", "MonitorLostError",
    "ProcessMemory", "ProcessSnapshot", "ProcessRecord", "ObservationReport",
    "WindowsProcessTreeObserver", "read_process_snapshot", "run_observed",
]
