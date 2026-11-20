"""Independent structural verifier for R9 native observer *diagnostic* receipts.

A JSON receipt is not a trusted OS attestation. This verifier recomputes its
internal counts and peaks without importing the producer. It never grants full
L3 admission: ordinary Job notifications and post-exit peaks lack that proof.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

SCHEMA = "solar-pv-windows-observer/1"
LIMIT = 512 * 1024**2
MAX_RECEIPT_BYTES = 10_000_000


class EvidenceError(ValueError):
    """Invalid or incomplete native resource evidence."""


def _integer(value: object, label: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise EvidenceError(f"invalid {label}")
    return value


def _memory(value: object) -> None:
    if not isinstance(value, dict) or set(value) != {
        "working_set_bytes", "peak_working_set_bytes", "private_usage_bytes", "page_fault_count"
    }:
        raise EvidenceError("invalid native memory counters")
    for key, item in value.items():
        _integer(item, key)
    if not 0 < value["working_set_bytes"] <= value["peak_working_set_bytes"] <= LIMIT:
        raise EvidenceError("native working-set peak is inconsistent")


def verify(path: Path, *, expected_sha256: str | None = None) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_RECEIPT_BYTES:
        raise EvidenceError("missing, linked or oversized resource receipt")
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and expected_sha256 != digest:
        raise EvidenceError("resource receipt differs from frozen SHA-256")
    try:
        report = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceError("invalid resource JSON") from exc
    if not isinstance(report, dict) or report.get("schema") != SCHEMA:
        raise EvidenceError("invalid resource schema")
    if (report.get("verdict") != "BLOCKED" or report.get("admission_ready") is not False
            or report.get("lifetime_peak_proof") is not False
            or report.get("resumed") is not True or report.get("timed_out") is not False
            or report.get("monitor_error") is not None
            or report.get("active_process_zero_seen") is not True
            or report.get("raw_evidence_complete") is not True
            or report.get("complete_tree_accounting") is not True
            or not isinstance(report.get("blockers"), list) or not report["blockers"]
            or not isinstance(report.get("notification_reliability"), str)
            or "BLOCKED" not in report["notification_reliability"]
            or not isinstance(report.get("peak_lifecycle_reliability"), str)
            or "BLOCKED" not in report["peak_lifecycle_reliability"]):
        raise EvidenceError("diagnostic is incomplete or incorrectly claims admission")
    job = report.get("job_accounting")
    if not isinstance(job, dict):
        raise EvidenceError("missing Job accounting")
    total = _integer(job.get("total_processes"), "total_processes", minimum=2)
    if (_integer(job.get("active_processes"), "active_processes") != 0
            or _integer(job.get("terminated_processes"), "terminated_processes") > total
            or _integer(job.get("process_private_commit_limit_bytes"), "process_limit") != LIMIT
            or _integer(job.get("job_private_commit_limit_bytes"), "job_limit") != LIMIT
            or not 0 < _integer(job.get("peak_job_private_commit_bytes"), "peak_job") <= LIMIT):
        raise EvidenceError("Job private-commit limit or accounting inconsistent")
    processes = report.get("processes")
    events = report.get("raw_events")
    root = report.get("root")
    if (not isinstance(processes, list) or len(processes) != total
            or not isinstance(events, list) or not isinstance(root, dict)):
        raise EvidenceError("missing Job process/event evidence")
    identities: set[tuple[int, int]] = set()
    by_pid: dict[int, dict] = {}
    for item in processes:
        if not isinstance(item, dict):
            raise EvidenceError("invalid process record")
        pid = _integer(item.get("pid"), "pid", minimum=1)
        creation = _integer(item.get("creation_time_100ns"), "creation time", minimum=1)
        _integer(item.get("parent_pid"), "parent pid", minimum=1)
        if ((pid, creation) in identities or pid in by_pid
                or not isinstance(item.get("image_path"), str) or not item["image_path"]
                or item.get("new_event_seen") is not True or item.get("exit_event_seen") is not True
                or item.get("exit_message") not in {"EXIT_PROCESS", "ABNORMAL_EXIT_PROCESS"}
                or item.get("lifetime_peak_valid") is not False
                or _integer(item.get("live_snapshot_count"), "snapshot count", minimum=1) < 1):
            raise EvidenceError("duplicate, unobserved or invalid process identity")
        identities.add((pid, creation))
        by_pid[pid] = item
        _memory(item.get("memory"))
        final = item.get("final_memory_after_exit")
        if final is None:
            raise EvidenceError("missing after-exit diagnostic counters")
        # After-exit values are deliberately NOT used to certify the lifetime peak.
        if not isinstance(final, dict) or set(final) != set(item["memory"]):
            raise EvidenceError("invalid after-exit diagnostic counters")
        for key, value in final.items():
            _integer(value, f"after-exit {key}")
        if final["peak_working_set_bytes"] > LIMIT:
            raise EvidenceError("after-exit native peak exceeds 512 MiB; lifetime proof still absent")
        if (not item["memory"]["peak_working_set_bytes"]
                <= _integer(item.get("observed_peak_working_set_bytes"), "observed peak", minimum=1)
                <= LIMIT
                or _integer(item.get("exit_code"), "exit code") != 0):
            raise EvidenceError("invalid process peak or exit code")
    root_pid = _integer(root.get("pid"), "root pid", minimum=1)
    if root_pid not in by_pid or root.get("creation_time_100ns") != by_pid[root_pid]["creation_time_100ns"]:
        raise EvidenceError("root PID and creation-time identity mismatch")
    if by_pid[root_pid]["parent_pid"] in by_pid:
        raise EvidenceError("root parent cannot be itself or a Job descendant")
    if any(item["parent_pid"] not in by_pid for pid, item in by_pid.items() if pid != root_pid):
        raise EvidenceError("descendant parent absent from Job tree")
    for pid in by_pid:
        if pid == root_pid:
            continue
        ancestors = set()
        cursor = pid
        while cursor != root_pid:
            if cursor in ancestors or cursor not in by_pid:
                raise EvidenceError("cyclic or orphaned process ancestry")
            ancestors.add(cursor)
            cursor = by_pid[cursor]["parent_pid"]
    new = Counter()
    exits = Counter()
    zero = 0
    for event in events:
        if not isinstance(event, dict):
            raise EvidenceError("invalid Job event")
        if event.get("kind") == "control" and event.get("event") == "RESUME":
            if event.get("pid") != root_pid or new or exits or zero:
                raise EvidenceError("unexpected resume event order")
            continue
        if event.get("kind") != "job":
            raise EvidenceError("unknown Job event")
        message, code, pid = event.get("message"), event.get("message_code"), event.get("pid")
        if message == "NEW_PROCESS" and code == 6 and pid in by_pid and not zero:
            new[pid] += 1
        elif (message in {"EXIT_PROCESS", "ABNORMAL_EXIT_PROCESS"}
              and code == (7 if message == "EXIT_PROCESS" else 8)
              and pid in by_pid and new[pid] == 1 and event.get("matched") is True and not zero):
            exits[pid] += 1
            if by_pid[pid]["exit_message"] != message:
                raise EvidenceError("exit message contradicts record")
        elif message == "ACTIVE_PROCESS_ZERO" and code == 4 and pid is None and not zero:
            zero += 1
        else:
            raise EvidenceError("unknown, repeated or out-of-order Job event")
    if (not zero or any(new[pid] != 1 or exits[pid] != 1 for pid in by_pid)
            or report.get("physical_peak_working_set_bytes") != max(
                item["observed_peak_working_set_bytes"] for item in processes)
            or report.get("sum_peak_working_set_bytes") != sum(
                item["observed_peak_working_set_bytes"] for item in processes)):
        raise EvidenceError("event multiset or peak aggregates differ from raw process records")
    return {"schema": "solar-pv-windows-observer-verification/1", "verdict": "BLOCKED",
            "raw_sha256": digest, "process_count": total, "job_private_commit_limit_bytes": LIMIT,
            "internal_consistency": True, "native_attestation": False,
            "reason": "Job event delivery and actual lifetime working-set peak are not proven"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--sha256", help="expected frozen raw receipt digest")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(verify(args.evidence, expected_sha256=args.sha256), sort_keys=True))
    except (EvidenceError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
    return 2  # A diagnostic, even internally consistent, cannot admit the full suite.


if __name__ == "__main__":
    raise SystemExit(main())
