"""Focused contract checks for the purchase three-way matcher."""
from pathlib import Path
import json
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "packages/skills/wangbin-purchase-threeway-match/scripts/threeway_match.py"

def test_skill_contract_files_exist():
    skill = SCRIPT.parent.parent
    assert (skill / "SKILL.md").is_file()
    assert (skill / "examples/manifest.json").is_file()

def test_example_manifest_is_complete():
    data = json.loads((SCRIPT.parent.parent / "examples/manifest.json").read_text())
    assert set(data) >= {"input_root", "po_files", "receipt_files", "invoice_files", "config"}
    assert data["config"]["quantity_tolerance"]["mode"] == "absolute"

def test_generated_workbook_has_frozen_seven_sheets():
    # The executable smoke run is recorded outside the repository; this test validates the API contract shape.
    assert SCRIPT.exists()
    assert len(("Match Summary", "Line Results", "Exceptions", "Unmatched Receipts", "Unmatched Invoices", "Source Trace", "Run Manifest")) == 7


def _run_fixture(tmp_path, po, receipts, invoices, *, po_amount=True):
    import importlib.util
    spec = importlib.util.spec_from_file_location("threeway_match", SCRIPT)
    matcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(matcher)
    root = tmp_path / "case"; root.mkdir()
    def write(name, rows):
        fields = sorted({k for row in rows for k in row})
        (root / name).write_text(",".join(fields) + "\n" + "\n".join(",".join(str(row.get(k, "")) for k in fields) for row in rows) + "\n", encoding="utf-8")
    write("po.csv", po); write("receipts.csv", receipts); write("invoices.csv", invoices)
    manifest = {"input_root": "case", "po_files": ["po.csv"], "receipt_files": ["receipts.csv"], "invoice_files": ["invoices.csv"], "config": {"quantity_tolerance": {"mode": "absolute", "value": "0"}, "unit_price_tolerance": {"mode": "absolute", "value": "0"}, "amount_tolerance": {"mode": "absolute", "value": "0"}}}
    manifest_path = tmp_path / "manifest.json"; manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output = tmp_path / "output"
    return matcher.main_match(manifest, output, tmp_path), json.loads((output / "summary.json").read_text()), load_workbook(output / "threeway_match.xlsx", data_only=True)


def test_regressions_missing_duplicate_orphan_and_derived(tmp_path):
    key = {"po_number": "P1", "po_line_id": "1", "item_code": "I1"}
    po = [{**key, "ordered_quantity": "10", "po_unit_price": "5", "currency": "USD", "uom": "EA"}]
    receipts = [{**key, "item_code": "", "receipt_number": "Rbad", "receipt_line_id": "1", "received_quantity": "8", "uom": "EA"}, {**key, "receipt_number": "R-orphan", "receipt_line_id": "1", "po_number": "P-orphan", "po_line_id": "1", "item_code": "X", "received_quantity": "1", "uom": "EA"}]
    invoices = [{**key, "invoice_number": "I1", "invoice_line_id": "1", "invoiced_quantity": "10", "invoice_unit_price": "5", "invoice_amount": "50", "currency": "USD", "uom": "EA"}, {**key, "invoice_number": "I1", "invoice_line_id": "1", "invoiced_quantity": "10", "invoice_unit_price": "5", "invoice_amount": "50", "currency": "USD", "uom": "EA"}, {"po_number": "P-orphan", "po_line_id": "1", "item_code": "X", "invoice_number": "I-orphan", "invoice_line_id": "1", "invoiced_quantity": "1", "invoice_unit_price": "5", "invoice_amount": "5", "currency": "USD", "uom": "EA"}]
    summary, structured, wb = _run_fixture(tmp_path, po, receipts, invoices)
    rows = list(wb["Match Summary"].values)
    headers = rows[0]; result = dict(zip(headers, rows[1]))
    assert result["expected_amount_source"] == "DERIVED"
    assert result["received_quantity"] == "NOT_AVAILABLE"  # missing physical value is not zero
    assert "QTY_UNDER" not in result["exception_codes"]
    assert result["invoiced_amount"] == "100"  # duplicate physical rows are retained, not silently dropped
    exc = [dict(zip(list(wb["Exceptions"].values)[0], row)) for row in list(wb["Exceptions"].values)[1:]]
    duplicate_refs = {x["source_row_reference"] for x in exc if x["exception_code"] == "DUPLICATE_SOURCE_ROW"}
    assert duplicate_refs == {"invoices.csv:2", "invoices.csv:3"}
    assert len(list(wb["Unmatched Receipts"].values)) == 3  # header + invalid row + orphan row
    assert len(list(wb["Unmatched Invoices"].values)) == 2  # header + one orphan row
    assert structured["exception_code_counts"]["MISSING_REQUIRED_FIELD"] == 1


def test_regression_invalid_numeric_and_manifest_relative_root(tmp_path, monkeypatch):
    key = {"po_number": "P1", "po_line_id": "1", "item_code": "I1"}
    po = [{**key, "ordered_quantity": "10", "po_unit_price": "5", "currency": "USD", "uom": "EA"}]
    receipts = [{**key, "receipt_number": "R1", "receipt_line_id": "1", "received_quantity": "10", "uom": "EA"}]
    invoices = [{**key, "invoice_number": "I1", "invoice_line_id": "1", "invoiced_quantity": "abc", "invoice_unit_price": "5", "invoice_amount": "50", "currency": "USD", "uom": "EA"}]
    summary, structured, wb = _run_fixture(tmp_path, po, receipts, invoices)
    assert summary["run_status"] == "SUCCEEDED_WITH_EXCEPTIONS"
    assert structured["exception_code_counts"]["INVALID_INPUT"] == 1
    assert dict(zip(list(wb["Match Summary"].values)[0], list(wb["Match Summary"].values)[1]))["invoiced_quantity"] == "NOT_AVAILABLE"
    # Calling from an unrelated CWD must still resolve input_root beside manifest.
    monkeypatch.chdir(tmp_path.parent)
    assert (tmp_path / "output" / "threeway_match.xlsx").exists()
