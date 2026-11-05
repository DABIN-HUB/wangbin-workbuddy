"""0.1.1 minimal-input acceptance, independent from the legacy advanced fixtures."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "packages/skills/wangbin-supplier-reconciliation/scripts/reconcile.py"
spec = importlib.util.spec_from_file_location("reconcile_mvp", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
NAMES = ["Summary", "Matched", "Amount Differences", "Supplier Only", "Internal Only", "Manual Review"]


def invoke(tmp_path, supplier, internal, *, xlsx=False, **options):
    tmp_path.mkdir(parents=True, exist_ok=True)
    inputs = {}
    for side, lines in (("supplier", supplier), ("internal", internal)):
        path = tmp_path / (side + (".xlsx" if xlsx else ".csv"))
        if xlsx:
            book = Workbook()
            sheet = book.active
            assert sheet is not None
            sheet.title = "明细"
            for line in lines.strip().splitlines():
                sheet.append(line.split(","))
            book.save(path)
        else:
            path.write_text(lines, encoding="utf-8")
        inputs[side + "_input"] = {"path": str(path), **({"sheet": "明细"} if xlsx else {})}
    config = {**inputs, "output_dir": str(tmp_path / "out"), **options}
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(config), encoding="utf-8")
    proc = subprocess.run([sys.executable, str(SCRIPT), "--config", str(cfg)], cwd=tmp_path, capture_output=True, text=True)
    data = json.loads((tmp_path / "out/reconciliation.json").read_text(encoding="utf-8"))
    return proc, data, tmp_path / "out"


@pytest.mark.parametrize("xlsx", [False, True])
def test_two_column_default_and_exact_difference(tmp_path, xlsx):
    proc, data, out = invoke(tmp_path, "document_no,amount\nD1,20.00\nD2,4.00\n", "document_no,amount\nD1,20.01\nD3,4.00\n", xlsx=xlsx)
    assert proc.returncode == 0, proc.stderr
    assert data["run"]["matching_mode"] == "basic"
    assert data["run"]["key_fields"] == ["document_no"]
    assert data["run"]["amount_tolerance"] == "0.00"
    assert data["summary"]["by_status"]["AMOUNT_DIFFERENCE"] == 1
    assert {r["status"] for r in data["results"]} == {"AMOUNT_DIFFERENCE", "ONLY_SUPPLIER", "ONLY_INTERNAL"}
    assert next(r for r in data["results"] if r["key"] == {"document_no": "D1"})["difference"] == "-0.01"
    book = load_workbook(out / "reconciliation.xlsx")
    assert book.sheetnames == NAMES
    assert len(list(book["Amount Differences"].values)) == 2
    assert len(list(book["Supplier Only"].values)) == 2
    assert len(list(book["Internal Only"].values)) == 2
    assert len(list(book["Matched"].values)) == 1


def test_explicit_tolerance_and_duplicate_manual(tmp_path):
    _, data, out = invoke(tmp_path, "document_no,amount\nD1,20.00\nD1,20.00\n", "document_no,amount\nD1,20.01\n", amount_tolerance="0.01")
    assert [r["status"] for r in data["results"]] == ["AMBIGUOUS"]
    assert len(data["results"][0]["sources"]) == 3
    assert len(list(load_workbook(out / "reconciliation.xlsx")["Manual Review"].values)) == 2
    _, data, _ = invoke(tmp_path / "unique", "document_no,amount\nD1,20.00\n", "document_no,amount\nD1,20.01\n", amount_tolerance="0.01")
    assert data["results"][0]["status"] == "MATCHED"


def test_supplier_disambiguation_and_missing_id(tmp_path):
    supplier = "supplier_id,document_no,amount\nS1,D1,20.00\nS2,D1,9.00\n"
    internal = "supplier_id,document_no,amount\nS1,D1,20.00\nS2,D1,9.00\n"
    _, data, _ = invoke(tmp_path, supplier, internal)
    assert data["run"]["supplier_id_required"] is True
    assert data["run"]["key_fields"] == ["supplier_id", "document_no"]
    assert data["summary"]["by_status"]["MATCHED"] == 2
    _, data, _ = invoke(tmp_path / "missing", supplier, internal.replace("S2,D1,9.00", ",D1,9.00"))
    assert any(r["status"] == "AMBIGUOUS" and "SUPPLIER_ID_REQUIRED" in r["error_codes"] for r in data["results"])
    assert not any(r["status"] == "MATCHED" and r["key"]["supplier_id"] == "S2" for r in data["results"])


def test_six_sheet_counts_with_invalid_and_ambiguous(tmp_path):
    supplier = "document_no,amount\nM,1.00\nA,2.00\nS,3.00\nD,4.00\nD,5.00\nX,abc\n"
    internal = "document_no,amount\nM,1.00\nA,2.01\nI,3.00\nD,4.00\n"
    proc, data, out = invoke(tmp_path, supplier, internal)
    assert proc.returncode == 0
    book = load_workbook(out / "reconciliation.xlsx")
    assert book.sheetnames == NAMES
    status_counts = data["summary"]["by_status"]
    for status, sheet in (("MATCHED", "Matched"), ("AMOUNT_DIFFERENCE", "Amount Differences"), ("ONLY_SUPPLIER", "Supplier Only"), ("ONLY_INTERNAL", "Internal Only")):
        assert status_counts[status] == len(list(book[sheet].values)) - 1 == 1
    assert status_counts["AMBIGUOUS"] == status_counts["INVALID"] == 1
    assert len(list(book["Manual Review"].values)) - 1 == 2
    assert sum(int(v) for _, status, v in list(book["Summary"].values)[1:]) == data["summary"]["total_result_rows"]
    assert all(cell.data_type != "f" for sheet in book for row in sheet for cell in row)


def test_explicit_advanced_key_and_legacy_alias(tmp_path):
    header = "reconciliation_id,document_id,line_id,item_code,amount,currency\n"
    row = "B,D,1,M,20.00,CNY\n"
    proc, data, _ = invoke(tmp_path, header + row, header + row, key_fields=["reconciliation_id", "document_id", "line_id", "item_code", "currency"])
    assert proc.returncode == 0
    assert data["run"]["matching_mode"] == "advanced"
    assert data["run"]["key_fields"] == ["reconciliation_id", "document_no", "line_id", "item_code", "currency"]
    assert data["results"][0]["status"] == "MATCHED"


def test_shipped_two_column_xlsx_fixture(tmp_path):
    fixture = ROOT / "tests/fixtures/supplier-reconciliation"
    config = {side + "_input": {"path": str(fixture / f"minimal-{side}.xlsx"), "sheet": "Details"}
              for side in ("supplier", "internal")}
    config["output_dir"] = str(tmp_path / "out")
    cfg = tmp_path / "fixture.json"
    cfg.write_text(json.dumps(config), encoding="utf-8")
    run = subprocess.run([sys.executable, str(SCRIPT), "--config", str(cfg)], cwd=tmp_path, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    data = json.loads((tmp_path / "out/reconciliation.json").read_text(encoding="utf-8"))
    assert data["results"][0]["status"] == "AMOUNT_DIFFERENCE"
    assert load_workbook(tmp_path / "out/reconciliation.xlsx").sheetnames == NAMES
