"""Seal an independently calculated Phase 7L-R2 case without changing its results.

Losslessly archive D3 and 3B/3C interval data, write byte manifests and
replay the frozen input/canonical/financial invariants. Never accepts R1 cases.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from tooling.solar_pv_phase7l_r2_inputs import verify_delivery
from wangbin_solar_pv.serialization import loads


def seal_delivery(case_dir: Path) -> dict:
    case_dir = case_dir.resolve()
    export = loads((case_dir / "input.json").read_bytes())
    if not str(export["project"]["project_id"]).startswith("SYNTHETIC-PHASE7L-R2-"):
        raise ValueError("ONLY_R2_CASES_MAY_BE_SEALED")
    reserved = ("file-manifest.json", "expanded-file-manifest.json",
                "archived-d3-and-intervals.zip", "verification.json")
    if not (case_dir / "REPRODUCE.md").is_file() or any((case_dir / name).exists() for name in reserved):
        raise ValueError("CASE_NOT_READY_FOR_FIRST_SEAL")

    def entry(path: Path) -> dict:
        h = hashlib.sha256()
        size = 0
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(chunk)
                size += len(chunk)
        return {"path": path.relative_to(case_dir).as_posix(), "bytes": size, "sha256": h.hexdigest()}

    def write_manifest(filename: str, entries: list[dict]) -> None:
        (case_dir / filename).write_text(json.dumps({
            "schema_version": "phase7l-file-manifest/1.0.0", "files": entries,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    files = sorted((path for path in case_dir.rglob("*") if path.is_file()),
                   key=lambda path: path.relative_to(case_dir).as_posix())
    expanded = [entry(path) for path in files]
    archive_entries = [item for item in expanded if
                       item["path"] == "bundle/base.json" or
                       (item["path"].startswith("bundle/") and item["path"].endswith(".jsonl")) or
                       (item["path"].startswith(("project/3b/interval-", "project/3c/interval-"))
                        and item["path"].endswith(".jsonl"))]
    if len(archive_entries) < 100:
        raise ValueError("CASE_INTERVAL_INVENTORY_INCOMPLETE")
    write_manifest("expanded-file-manifest.json", expanded)
    archive = case_dir / "archived-d3-and-intervals.zip"
    temporary = case_dir / ".archived-d3-and-intervals.tmp.zip"
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipout:
        for item in archive_entries:
            zipout.write(case_dir / item["path"], arcname=item["path"])
    with zipfile.ZipFile(temporary) as zipin:
        if set(zipin.namelist()) != {item["path"] for item in archive_entries}:
            raise ValueError("CASE_ARCHIVE_INVENTORY_MISMATCH")
        for item in archive_entries:
            h = hashlib.sha256()
            size = 0
            with zipin.open(item["path"]) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    h.update(chunk)
                    size += len(chunk)
            if size != item["bytes"] or h.hexdigest() != item["sha256"]:
                raise ValueError("CASE_ARCHIVE_BYTE_MISMATCH: " + item["path"])
    temporary.replace(archive)
    for item in archive_entries:
        (case_dir / item["path"]).unlink()

    verification = case_dir / "verification.json"
    verification.write_text(json.dumps({"status": "AWAITING_READ_ONLY_VERIFICATION"}) + "\n", encoding="utf-8")

    def refresh_current() -> None:
        write_manifest("file-manifest.json", [entry(path) for path in sorted(
            (path for path in case_dir.rglob("*") if path.is_file() and path.name != "file-manifest.json"),
            key=lambda path: path.relative_to(case_dir).as_posix())])

    refresh_current()
    result = verify_delivery(case_dir)
    verification.write_text(json.dumps({"status": "VERIFIED_BY_READ_ONLY_REPLAY", "result": result},
                                       ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    refresh_current()
    return verify_delivery(case_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(seal_delivery(args.case_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
