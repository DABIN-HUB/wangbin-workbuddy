#!/usr/bin/env python3
"""Strict, local-only two-sided CSV amount reconciliation."""
from __future__ import annotations
import argparse, csv, io, json, os, re, shutil, sys, tempfile
from decimal import Decimal, InvalidOperation
from pathlib import Path

HEADER = ["id", "left_amount", "right_amount", "left_row", "right_row"]
AMOUNT = re.compile(r"-?(0|[1-9][0-9]*)(\.[0-9]{1,2})?\Z")
FORMULA = ("=", "+", "-", "@")
CODES = {"INPUT_PATH_ERROR", "OUTPUT_ERROR", "CSV_FORMAT_ERROR", "SCHEMA_ERROR", "EMPTY_ID", "DUPLICATE_ID", "INVALID_AMOUNT", "INVALID_ID", "INTERNAL_ERROR"}

class ReconcileError(Exception):
    def __init__(self, code: str, side: str | None = None, row: int | None = None, message: str = "invalid input"):
        self.code, self.side, self.row, self.message = code, side, row, message
        super().__init__(message)

def error(code, side=None, row=None, message="invalid input"):
    raise ReconcileError(code, side, row, message)

def _read(path: Path, side: str) -> dict[str, tuple[Decimal, str, int]]:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig")
    except (OSError, UnicodeDecodeError):
        error("CSV_FORMAT_ERROR", side, None, "file is not valid UTF-8 CSV")
        raise AssertionError("unreachable")
    try:
        rows = list(csv.reader(io.StringIO(text, newline=""), strict=True))
    except csv.Error:
        error("CSV_FORMAT_ERROR", side, None, "malformed CSV")
        raise AssertionError("unreachable")
    if not rows or rows[0] != ["id", "amount"]:
        error("SCHEMA_ERROR", side, 1, "header must be exactly id,amount")
    result = {}
    for row_no, row in enumerate(rows[1:], 2):
        if len(row) != 2:
            error("CSV_FORMAT_ERROR", side, row_no, "record must contain exactly two columns")
        ident, amount = row
        if not ident.strip():
            error("EMPTY_ID", side, row_no, "id is empty")
        if ident.startswith(FORMULA) or any(ord(c) < 32 for c in ident):
            error("INVALID_ID", side, row_no, "id starts with a forbidden character")
        if ident in result:
            error("DUPLICATE_ID", side, row_no, "id occurs more than once")
        if not amount.strip() or not AMOUNT.fullmatch(amount):
            error("INVALID_AMOUNT", side, row_no, "amount must be a decimal with at most two places")
        try:
            value = Decimal(amount)
        except InvalidOperation:
            error("INVALID_AMOUNT", side, row_no, "amount is not decimal")
            raise AssertionError("unreachable")
        result[ident] = (value, f"{value:.2f}", row_no)
    return result

def reconcile(left: Path, right: Path, output: Path) -> dict:
    try:
        left = left.resolve(); right = right.resolve(); output = output.resolve()
    except OSError:
        error("INPUT_PATH_ERROR", None, None, "path cannot be resolved")
    if left == right:
        error("INPUT_PATH_ERROR", None, None, "inputs must be distinct files")
    for path, side in ((left, "left"), (right, "right")):
        if not path.is_file() or path.suffix.lower() != ".csv":
            error("INPUT_PATH_ERROR", side, None, "input must be an existing CSV file")
    if output in (left, right) or output.exists() and not output.is_dir():
        error("OUTPUT_ERROR", None, None, "output must be a directory distinct from inputs")
    ldata = _read(left, "left")
    rdata = _read(right, "right")
    names = ["matched.csv", "left_missing.csv", "right_missing.csv", "amount_mismatch.csv", "summary.json"]
    try:
        output.mkdir(parents=True, exist_ok=True)
        if any((output / name).exists() for name in names):
            error("OUTPUT_ERROR", None, None, "output target already exists")

    except ReconcileError:
        raise
    except OSError:
        error("OUTPUT_ERROR", None, None, "output is not writable")
    groups = {"matched": [], "left_missing": [], "right_missing": [], "amount_mismatch": []}
    for ident in sorted(set(ldata) | set(rdata)):
        lv, lf, lr = ldata[ident] if ident in ldata else (None, "", None)
        rv, rf, rr = rdata[ident] if ident in rdata else (None, "", None)
        if lv is None: kind = "left_missing"
        elif rv is None: kind = "right_missing"
        elif lv == rv: kind = "matched"
        else: kind = "amount_mismatch"
        groups[kind].append([ident, lf, rf, "" if lr is None else lr, "" if rr is None else rr])
    summary = {"status": "ok", **{k: len(v) for k, v in groups.items()}, "distinct_ids": sum(map(len, groups.values()))}
    temp = Path(tempfile.mkdtemp(prefix=".reconcile-", dir=output))
    created = []
    try:
        for kind, rows in groups.items():
            with (temp / f"{kind}.csv").open("w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f, lineterminator="\n"); writer.writerow(HEADER); writer.writerows(rows)
        (temp / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        for name in names:
            os.link(temp / name, output / name)
            created.append(name)
    except OSError:
        for name in created: (output / name).unlink(missing_ok=True)
        error("OUTPUT_ERROR", None, None, "could not commit output")
    finally:
        shutil.rmtree(temp)
    return summary

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__); p.add_argument("--left", required=True); p.add_argument("--right", required=True); p.add_argument("--output", required=True)
    args = p.parse_args()
    try:
        result = reconcile(Path(args.left), Path(args.right), Path(args.output))
    except ReconcileError as exc:
        print(json.dumps({"status":"error", "code":exc.code, "side":exc.side, "row":exc.row, "message":exc.message}, ensure_ascii=False, separators=(",", ":")), file=sys.stderr); return 2
    except Exception:
        print(json.dumps({"status":"error", "code":"INTERNAL_ERROR", "side":None, "row":None, "message":"internal failure"}, separators=(",", ":")), file=sys.stderr); return 2
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":"))); return 0
if __name__ == "__main__": raise SystemExit(main())
