"""Inspect solar-PV artifacts and remove only explicitly marked disposable runs.

The tool never stages or commits changes. A developer must review the receipt,
run the relevant verification, and explicitly stage/commit authorized files.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOLAR_ROOT = ROOT / ".runtime" / "solar-pv"
DISPOSABLE_MARKER = ".solar-pv-disposable.json"
MARKER_KIND = "REGENERABLE_SOLAR_PV_RUN"
PROTECTED_NAMES = {"phase7l-r4-final-v2", "protected-r2-recovery", "hygiene-receipts"}


def _git(*args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def _paths(*args: str) -> list[str]:
    return [item.decode("utf-8") for item in _git(args[0], "-z", *args[1:]).split(b"\0") if item]


def _size(path: Path) -> int:
    return path.stat().st_size if path.is_file() else 0


def _sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_redirect(path: Path) -> bool:
    """Also reject Windows junctions/reparse points on Python 3.11."""
    return path.is_symlink() or bool(path.exists() and
        getattr(path.lstat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _dist() -> list[dict[str, object]]:
    results = []
    for archive in sorted((ROOT / "dist").glob("wangbin-solar-pv-*.zip")):
        ignored = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "-q", "--",
                                  str(archive.relative_to(ROOT))], check=False).returncode == 0
        try:
            with zipfile.ZipFile(archive) as package:
                valid = package.testzip() is None
                names = package.namelist()
        except (OSError, zipfile.BadZipFile, RuntimeError):
            valid, names = False, []
        results.append({"path": archive.relative_to(ROOT).as_posix(), "bytes": _size(archive),
                        "git_ignored": ignored, "readable": valid, "members": len(names),
                        "license_present": any("LICENSE" in name.upper() for name in names),
                        "manifest_present": (any("MANIFEST" in name.upper() for name in names)
                                             or archive.with_suffix(archive.suffix + ".manifest.json").is_file())})
    return results


def check() -> dict[str, object]:
    tracked = _paths("ls-files")
    untracked = _paths("ls-files", "--others", "--exclude-standard")
    reports = [path for path in (ROOT / "reports" / "solar-pv").rglob("*") if path.is_file()]
    added = _paths("diff", "--cached", "--name-only", "--diff-filter=A")
    large = [path for path in reports if path.stat().st_size >= 5_000_000]
    by_content: dict[tuple[int, str], list[str]] = defaultdict(list)
    for path in large:
        by_content[path.stat().st_size, _sha256(path)].append(path.relative_to(ROOT).as_posix())
    duplicates = [names for names in by_content.values() if len(names) > 1]
    historical = sorted({path.relative_to(ROOT / "reports" / "solar-pv").parts[0]
                         for path in reports if path.relative_to(ROOT / "reports" / "solar-pv").parts[0].startswith("phase")})
    stale = [name for name in tracked if name.startswith("reports/solar-pv/")
             and (name.endswith((".xml", ".log")) or "-pytest.txt" in name
                  or "-test-ids.txt" in name or "-junit.txt" in name)]
    disposable = [directory.relative_to(ROOT).as_posix() for directory in sorted(SOLAR_ROOT.iterdir())
                  if directory.is_dir() and (directory / DISPOSABLE_MARKER).is_file()] if SOLAR_ROOT.is_dir() else []
    return {"schema_version": "solar-pv-workspace-hygiene/1", "branch": _git("branch", "--show-current").decode().strip(),
            "tracked": {"count": len(tracked), "bytes": sum(_size(ROOT / name) for name in tracked)},
            "reports": {"count": len(reports), "bytes": sum(_size(path) for path in reports)},
            "untracked": {"count": len(untracked), "bytes": sum(_size(ROOT / name) for name in untracked),
                          "paths": untracked},
            "newly_staged": {"count": len(added), "bytes": sum(_size(ROOT / name) for name in added)},
            "large_report_files": [{"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size}
                                   for path in large],
            "duplicate_large_reports": duplicates, "historical_report_groups": historical,
            "tracked_generated_logs": {"count": len(stale), "paths": stale},
            "dist_candidates": _dist(), "marked_disposable_runs": disposable,
            "git_status": _git("status", "--short", "--untracked-files=all").decode("utf-8")}


def clean(target: Path) -> dict[str, object]:
    """Delete a single explicit, marked run; never recursively delete a root."""
    if ".." in target.parts:
        raise ValueError("TARGET_OUTSIDE_DISPOSABLE_SOLAR_RUNS")
    if not target.is_absolute():
        target = ROOT / target
    if (any(_is_redirect(path) for path in (SOLAR_ROOT.parent, SOLAR_ROOT, target))
            or target.resolve().parent != SOLAR_ROOT.resolve()
            or target.name.casefold() in PROTECTED_NAMES):
        raise ValueError("TARGET_OUTSIDE_DISPOSABLE_SOLAR_RUNS")
    if not target.exists():
        pending = SOLAR_ROOT / "hygiene-receipts" / f"{target.name}-cleanup.pending.json"
        if pending.exists() or _is_redirect(pending):
            raise ValueError("PENDING_RECEIPT_REQUIRES_MANUAL_REVIEW")
        return {"target": str(target), "status": "ALREADY_ABSENT", "deleted": []}
    if not target.is_dir():
        raise ValueError("TARGET_NOT_A_DIRECTORY")
    marker = target / DISPOSABLE_MARKER
    if _is_redirect(marker) or not marker.is_file():
        raise ValueError("EXPLICIT_DISPOSABLE_MARKER_REQUIRED")
    declaration = json.loads(marker.read_text(encoding="utf-8"))
    if declaration != {"kind": MARKER_KIND, "scope": target.name}:
        raise ValueError("DISPOSABLE_MARKER_SCOPE_MISMATCH")
    if any((ROOT / name).resolve().is_relative_to(target.resolve()) for name in _paths("ls-files")):
        raise ValueError("TRACKED_FILE_IN_DISPOSABLE_RUN")
    children = list(target.rglob("*"))
    if any(_is_redirect(item) for item in children):
        raise ValueError("LINK_IN_DISPOSABLE_RUN")
    files = [file for file in children if file.is_file()]
    deleted = [{"path": file.relative_to(ROOT).as_posix(), "bytes": _size(file), "sha256": _sha256(file)}
               for file in sorted(files)]
    receipts = SOLAR_ROOT / "hygiene-receipts"
    receipts.mkdir(parents=True, exist_ok=True)
    if (_is_redirect(receipts)
            or receipts.resolve().parent != SOLAR_ROOT.resolve()):
        raise ValueError("UNSAFE_RECEIPT_DIRECTORY")
    receipt_path = receipts / f"{target.name}-cleanup.json"
    pending_path = receipts / f"{target.name}-cleanup.pending.json"
    if _is_redirect(receipt_path) or receipt_path.exists() or _is_redirect(pending_path):
        raise FileExistsError(receipt_path)
    if pending_path.exists():
        receipt = json.loads(pending_path.read_text(encoding="utf-8"))
        original = {row["path"]: (row["bytes"], row["sha256"]) for row in receipt["deleted"]}
        if (receipt.get("status") != "PENDING" or receipt.get("target") != target.relative_to(ROOT).as_posix()
                or any(row["path"] not in original or original[row["path"]] != (row["bytes"], row["sha256"])
                       for row in deleted)):
            raise ValueError("PENDING_RECEIPT_MISMATCH")
    else:
        receipt = {"schema_version": "solar-pv-workspace-cleanup/1", "target": target.relative_to(ROOT).as_posix(),
                   "status": "PENDING", "deleted": deleted, "total_bytes": sum(item["bytes"] for item in deleted)}
        with pending_path.open("x", encoding="utf-8") as output:
            output.write(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    for file in files:
        file.unlink()
    for directory in sorted((path for path in target.rglob("*") if path.is_dir()),
                            key=lambda path: len(path.parts), reverse=True):
        directory.rmdir()
    target.rmdir()
    receipt["status"] = "DELETED"
    with pending_path.open("w", encoding="utf-8") as output:
        output.write(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    os.replace(pending_path, receipt_path)
    return {"target": receipt["target"], "status": "DELETED", "receipt": receipt_path.relative_to(ROOT).as_posix(),
            "deleted_files": len(deleted), "deleted_bytes": receipt["total_bytes"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Read-only inventory and policy report")
    mode.add_argument("--clean", metavar="RUN", type=Path, help="Delete one explicitly marked, direct solar runtime run")
    args = parser.parse_args()
    try:
        result = check() if args.check else clean(args.clean)
    except (OSError, ValueError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        print(f"SOLAR_HYGIENE_FAILED:{type(exc).__name__}:{exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
