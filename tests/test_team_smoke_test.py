"""Frozen A01–A12 and local transactional reconciliation regressions."""
import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "packages/skills/wangbin-team-smoke-test/scripts/reconcile_csv.py"
TARGETS = ["matched.csv", "left_missing.csv", "right_missing.csv", "amount_mismatch.csv", "summary.json"]
HEADER = ["id", "left_amount", "right_amount", "left_row", "right_row"]
BASE = b"id,amount\nA,1.00\n"


def run(tmp_path, left: bytes = BASE, right: bytes | None = BASE, *, same=False, existing=False):
    left_path = tmp_path / "left.csv"
    right_path = left_path if same else tmp_path / "right.csv"
    left_path.write_bytes(left)
    if not same and right is not None:
        right_path.write_bytes(right)
    output = tmp_path / "output"
    if existing:
        output.mkdir()
        (output / "matched.csv").write_bytes(b"original")
    proc = subprocess.run([sys.executable, str(SCRIPT), "--left", str(left_path), "--right", str(right_path), "--output", str(output)], capture_output=True, text=True)
    return proc, output


def records(output, kind):
    with (output / f"{kind}.csv").open(encoding="utf-8", newline="") as f:
        lines = list(csv.reader(f))
    assert lines[0] == HEADER
    return lines[1:]


def test_a01_four_groups(tmp_path):
    example = ROOT / "packages/skills/wangbin-team-smoke-test/examples"
    proc, output = run(tmp_path, (example / "left.csv").read_bytes(), (example / "right.csv").read_bytes())
    assert proc.returncode == 0, proc.stderr
    assert sorted(p.name for p in output.iterdir()) == sorted(TARGETS)
    assert records(output, "matched") == [["A", "1.00", "1.00", "2", "2"]]
    assert records(output, "left_missing") == [["C", "", "3.00", "", "3"]]
    assert records(output, "right_missing") == [["B", "2.00", "", "3", ""]]
    assert records(output, "amount_mismatch") == [["D", "4.00", "4.01", "4", "4"]]
    assert json.loads((output / "summary.json").read_text()) == {"status": "ok", "matched": 1, "left_missing": 1, "right_missing": 1, "amount_mismatch": 1, "distinct_ids": 4}


@pytest.mark.parametrize("left,right,expected", [
    (b"id,amount\nX,0\nY,-1.2\n", b"id,amount\nX,0.00\nY,-1.20\n", [["X", "0.00", "0.00", "2", "2"], ["Y", "-1.20", "-1.20", "3", "3"]]),
    (b"id,amount\n", b"id,amount\n", []),
    (b"id,amount\nA,1\n A ,1\n", b"id,amount\nA,1\n", [["A", "1.00", "1.00", "2", "2"]]),
])
def test_a02_a03_and_id_original(tmp_path, left, right, expected):
    proc, out = run(tmp_path, left, right)
    assert proc.returncode == 0, proc.stderr
    assert records(out, "matched") == expected
    if b" A " in left:
        assert records(out, "right_missing") == [[" A ", "1.00", "", "3", ""]]
    if left == b"id,amount\n":
        assert all(records(out, name) == [] for name in ("matched", "left_missing", "right_missing", "amount_mismatch"))
        assert json.loads((out / "summary.json").read_text())["distinct_ids"] == 0


@pytest.mark.parametrize("left,right,same,existing,code,side,row", [
    (b"id,amount\nA,1\nA,2\n", BASE, False, False, "DUPLICATE_ID", "left", 3),
    (BASE, b"id,amount\n,2\n", False, False, "EMPTY_ID", "right", 2),
    (BASE, b"id,amount\n   ,2\n", False, False, "EMPTY_ID", "right", 2),
    (b"id,amount\nA,\n", BASE, False, False, "INVALID_AMOUNT", "left", 2),
    (b"id,amount\nA, \n", BASE, False, False, "INVALID_AMOUNT", "left", 2),
    (BASE, b"id,amount\nA,1.234\n", False, False, "INVALID_AMOUNT", "right", 2),
    (BASE, b"id,amount\nA,NaN\n", False, False, "INVALID_AMOUNT", "right", 2),
    (b"id,value\n", BASE, False, False, "SCHEMA_ERROR", "left", 1),
    (b"id,amount,extra\n", BASE, False, False, "SCHEMA_ERROR", "left", 1),
    (BASE, b"id,amount\nA,1,extra\n", False, False, "CSV_FORMAT_ERROR", "right", 2),
    (b"\xff", BASE, False, False, "CSV_FORMAT_ERROR", "left", None),
    (b'id,amount\n"A,1\n', BASE, False, False, "CSV_FORMAT_ERROR", "left", None),
    (BASE, BASE, True, False, "INPUT_PATH_ERROR", None, None),
    (b"id,amount\n=1,2\n", BASE, False, False, "INVALID_ID", "left", 2),
    (b"id,amount\n\x7fdel,2\n", BASE, False, False, "INVALID_ID", "left", 2),
    ("id,amount\n\u0085c1,2\n".encode(), BASE, False, False, "INVALID_ID", "left", 2),
    (BASE, BASE, False, True, "OUTPUT_ERROR", None, None),
    (b"id,amount\nA,1\nA,2\n", b"id,amount\nA,NaN\n", False, False, "DUPLICATE_ID", "left", 3),
])
def test_a04_a12_and_priority(tmp_path, left, right, same, existing, code, side, row):
    proc, output = run(tmp_path, left, right, same=same, existing=existing)
    assert proc.returncode == 2
    payload = json.loads(proc.stderr)
    assert (payload["status"], payload["code"], payload["side"], payload["row"]) == ("error", code, side, row)
    assert not proc.stdout
    assert sorted(p.name for p in output.iterdir()) == (["matched.csv"] if existing else []) if output.exists() else True
    if existing:
        assert (output / "matched.csv").read_bytes() == b"original"


def test_missing_right_path(tmp_path):
    proc, output = run(tmp_path, right=None)
    assert proc.returncode == 2
    assert json.loads(proc.stderr)["code"] == "INPUT_PATH_ERROR"
    assert not output.exists()
