"""Executable A01–A19 product contract checks (isolated pytest tmp_path)."""
import csv
import hashlib
import json

import subprocess
import sys
import zipfile
from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

SCRIPT = Path(__file__).resolve().parents[1] / "packages/skills/wangbin-purchase-threeway-match/scripts/threeway_match.py"
SHEETS = ["Match Summary", "Line Results", "Exceptions", "Unmatched Receipts", "Unmatched Invoices", "Source Trace", "Run Manifest"]
KEY = {"po_number": "P1", "po_line_id": "1", "item_code": "SKU"}


def po(**kw):
    return {**KEY, "ordered_quantity": "10", "po_unit_price": "5.00", "po_amount": "50.00", "currency": "USD", "uom": "EA", **kw}


def receipt(**kw):
    return {**KEY, "receipt_number": "R1", "receipt_line_id": "1", "received_quantity": "10", "uom": "EA", **kw}


def invoice(**kw):
    return {**KEY, "invoice_number": "I1", "invoice_line_id": "1", "invoiced_quantity": "10", "invoice_unit_price": "5.00", "invoice_amount": "50.00", "currency": "USD", "uom": "EA", **kw}


def rows(ws):
    values = list(ws.values)
    return [dict(zip(values[0], row)) for row in values[1:]]


def run(tmp_path, *, pos=None, receipts=None, invoices=None, config=None, xlsx=False, split=False):
    root = tmp_path / "input"
    root.mkdir()
    manifest = {"input_root": "input", "po_files": [], "receipt_files": [], "invoice_files": [], "config": config or {}}
    sources = {"po": pos if pos is not None else [po()], "receipt": receipts if receipts is not None else [receipt()], "invoice": invoices if invoices is not None else [invoice()]}
    for kind, items in sources.items():
        chunks = [[item] for item in items] if split else [items]
        for number, chunk in enumerate(chunks):
            name = f"{kind}{number}.{'xlsx' if xlsx else 'csv'}"
            path = root / name
            fields = list(dict.fromkeys(k for item in chunk for k in item)) or list({"po": po(), "receipt": receipt(), "invoice": invoice()}[kind])
            if xlsx:
                book = Workbook()
                sheet = book.active
                sheet.title = kind
                sheet.append(fields)
                for item in chunk:
                    sheet.append([item.get(field, "") for field in fields])
                book.create_sheet("ignored")
                book.save(path)
                manifest[kind + "_files"].append({"path": name, "sheet": kind})
            else:
                with path.open("w", encoding="utf-8", newline="") as file:
                    writer = csv.DictWriter(file, fields)
                    writer.writeheader()
                    writer.writerows(chunk)
                manifest[kind + "_files"].append(name)
    mp = tmp_path / "manifest.json"
    mp.write_text(json.dumps(manifest), encoding="utf-8")
    output = tmp_path / "output"
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}
    cmd = [sys.executable, str(SCRIPT), "--manifest", str(mp), "--output", str(output)]
    completed = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp_path)
    if completed.returncode:
        return completed, None, None, None, output
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    report = (output / "report.md").read_text(encoding="utf-8")
    wb = load_workbook(output / "threeway_match.xlsx", data_only=False)
    assert wb.sheetnames == SHEETS
    assert {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir()} == before
    source = rows(wb["Source Trace"])
    assert len(source) == sum(len(items) for items in sources.values())
    assert all(r["source_row_number"] >= 2 and len(r["source_row_hash"]) == 64 and r["original_key_values"] for r in source)
    assert len({(r["source_file"], r["source_row_number"]) for r in source}) == len(source)
    recorded = json.loads(rows(wb["Run Manifest"])[0]["input_files"])
    assert {entry["name"]: entry["sha256"] for entry in recorded} == before
    assert summary["totals"]["exceptions"] == len(rows(wb["Exceptions"]))
    assert len(summary["line_results"]) == len(rows(wb["Match Summary"]))
    for actual, excel in zip(summary["line_results"], rows(wb["Match Summary"])):
        for field in ("status", "ordered_quantity", "received_quantity", "invoiced_quantity", "expected_amount", "invoiced_amount", "amount_variance", "weighted_invoice_unit_price", "currency"):
            assert actual[field] == (excel[field] or "")
        assert actual["invoice_amounts_by_currency"] == json.loads(excel["invoice_amounts_by_currency"])
    return completed, summary, wb, report, output


def checked(tmp_path, **kw):
    result = run(tmp_path, **kw)
    assert result[0].returncode == 0, result[0].stderr
    return result


def line(wb):
    return rows(wb["Match Summary"])[0]


def codes(wb):
    return set((line(wb)["exception_codes"] or "").split(";"))


def test_a01_csv_matched_seven_sheets_and_evidence(tmp_path):
    _, s, wb, report, _ = checked(tmp_path)
    assert s["totals"] == {"po_keys": 1, "matched": 1, "exceptions": 0}
    assert s["run_status"] == "SUCCEEDED" and line(wb)["status"] == "MATCHED"
    assert all(Decimal(line(wb)[field]) == 0 for field in ("receipt_variance", "invoice_variance", "amount_variance"))
    assert len(rows(wb["Source Trace"])) == 3 and len(rows(wb["Line Results"])) == 1
    assert "SUCCEEDED" in report


def test_a02_named_xlsx_sheets(tmp_path):
    _, s, wb, _, _ = checked(tmp_path, xlsx=True)
    assert s["totals"]["matched"] == 1
    assert {r["source_sheet"] for r in rows(wb["Source Trace"])} == {"po", "receipt", "invoice"}


def test_a03_split_receipts_and_invoices(tmp_path):
    _, s, wb, _, _ = checked(tmp_path, receipts=[receipt(receipt_number="R1", received_quantity="4"), receipt(receipt_number="R2", received_quantity="6")], invoices=[invoice(invoice_number="I1", invoiced_quantity="3", invoice_amount="15"), invoice(invoice_number="I2", invoiced_quantity="7", invoice_amount="35")], split=True)
    assert s["totals"]["matched"] == 1 and len(rows(wb["Source Trace"])) == 5
    assert line(wb)["received_quantity"] == line(wb)["invoiced_quantity"] == "10"


def test_a04_under_receipt(tmp_path):
    _, _, wb, _, _ = checked(tmp_path, receipts=[receipt(received_quantity="8")])
    assert "QTY_UNDER" in codes(wb) and line(wb)["status"] != "MATCHED"


def test_a05_inclusive_price_exclusive_amount(tmp_path):
    cfg = {"unit_price_tolerance": {"mode": "absolute", "value": "0.01"}, "amount_tolerance": {"mode": "absolute", "value": "0.01"}}
    _, _, wb, _, _ = checked(tmp_path, invoices=[invoice(invoice_unit_price="5.01", invoice_amount="50.10")], config=cfg)
    assert codes(wb) == {"AMOUNT_MISMATCH"} and line(wb)["amount_variance"] == "0.10"


def test_a06_quantity_price_amount_multi_exception(tmp_path):
    _, _, wb, _, _ = checked(tmp_path, receipts=[receipt(received_quantity="8")], invoices=[invoice(invoice_unit_price="5.02", invoice_amount="50.20")], config={"unit_price_tolerance": {"mode": "absolute", "value": "0.01"}, "amount_tolerance": {"mode": "absolute", "value": "0.01"}})
    assert {"QTY_UNDER", "PRICE_MISMATCH", "AMOUNT_MISMATCH"} <= codes(wb)
    assert line(wb)["amount_variance"] == "0.20"


def test_a07_derived_po_amount(tmp_path):
    _, _, wb, _, _ = checked(tmp_path, pos=[po(po_amount="")])
    assert line(wb)["expected_amount_source"] == "DERIVED" and line(wb)["expected_amount"] == "50.00"

@pytest.mark.parametrize("missing,available", [("ordered_quantity", "po_unit_price"), ("po_unit_price", "ordered_quantity")])
def test_a07_complete_po_key_with_missing_operand_retains_comparison(tmp_path, missing, available):
    _, summary, wb, report, _ = checked(tmp_path, pos=[po(**{missing: "", "po_amount": ""})])
    assert summary["run_status"] == "SUCCEEDED_WITH_EXCEPTIONS"
    assert summary["totals"] == {"po_keys": 1, "matched": 0, "exceptions": 2}
    assert summary["exception_code_counts"] == {"MISSING_REQUIRED_FIELD": 1, "NOT_COMPARABLE": 1}
    result = summary["line_results"][0]
    assert result["comparison_key"] == json.dumps(["P1", "1", "SKU"])
    assert result["status"] == "MISSING_REQUIRED_FIELD"
    assert result["exception_codes"] == "MISSING_REQUIRED_FIELD;NOT_COMPARABLE"
    assert result["source_file"] == "po0.csv" and result["source_row_number"] == 2
    assert result["expected_amount"] == result["expected_amount_source"] == "NOT_AVAILABLE"
    assert result["ordered_quantity" if missing == "ordered_quantity" else "weighted_invoice_unit_price"] == ("NOT_AVAILABLE" if missing == "ordered_quantity" else "5.00")
    assert result["received_quantity"] == result["invoiced_quantity"] == "10"
    assert result["receipt_variance"] == result["invoice_variance"] == ("NOT_AVAILABLE" if missing == "ordered_quantity" else "0")
    assert result["amount_variance"] == "NOT_AVAILABLE"
    assert len(rows(wb["Match Summary"])) == len(rows(wb["Line Results"])) == 1
    assert rows(wb["Unmatched Receipts"]) == rows(wb["Unmatched Invoices"]) == []
    trace = rows(wb["Source Trace"])
    assert [(r["_kind"], r["source_row_number"]) for r in trace] == [("po", 2), ("receipt", 2), ("invoice", 2)]
    assert trace[0][missing] is None and trace[0][available] is not None
    assert {r["_reason"] for r in trace[1:]} == {"INCLUDED"}
    assert {(r["exception_code"], r["source_row_reference"]) for r in rows(wb["Exceptions"])} == {("MISSING_REQUIRED_FIELD", "po0.csv:2"), ("NOT_COMPARABLE", "po0.csv:2")}
    assert "NOT_COMPARABLE" in report and "MISSING_REQUIRED_FIELD" in report and "po0.csv:2" in report


def test_a08_duplicate_po_key(tmp_path):
    _, s, wb, _, _ = checked(tmp_path, pos=[po(), po()])
    assert s["totals"]["matched"] == 0 and "DUPLICATE_PO_KEY" in codes(wb)
    assert len(rows(wb["Source Trace"])) == 4


def test_a09_missing_receipt_key(tmp_path):
    _, s, wb, _, _ = checked(tmp_path, receipts=[receipt(item_code="")])
    assert s["exception_code_counts"]["MISSING_REQUIRED_FIELD"] == 1
    assert "AMBIGUOUS_KEY" not in s["exception_code_counts"]
    assert len(rows(wb["Unmatched Receipts"])) == 1 and len(rows(wb["Source Trace"])) == 3


def test_a10_duplicate_invoice_document_line(tmp_path):
    _, _, wb, _, _ = checked(tmp_path, invoices=[invoice(), invoice()])
    assert line(wb)["invoiced_quantity"] == "20"
    assert {r["source_row_reference"] for r in rows(wb["Exceptions"]) if r["exception_code"] == "DUPLICATE_SOURCE_ROW"} == {"invoice0.csv:2", "invoice0.csv:3"}


def test_a11_missing_invoice_key(tmp_path):
    _, s, wb, report, _ = checked(tmp_path, invoices=[invoice(item_code="")])
    assert s["exception_code_counts"]["MISSING_REQUIRED_FIELD"] == 1
    assert "AMBIGUOUS_KEY" not in s["exception_code_counts"]
    assert len(rows(wb["Unmatched Invoices"])) == 1 and "无法匹配 / cannot match" in report


def test_a12_qa_original_currency_and_quantity(tmp_path):
    _, s, wb, report, _ = checked(tmp_path, invoices=[invoice(currency="CNY", invoice_unit_price="70", invoice_amount="700")])
    r = line(wb)
    assert codes(wb) == {"CURRENCY_MISMATCH", "NOT_COMPARABLE"}
    assert s["exception_code_counts"] == {"CURRENCY_MISMATCH": 1, "NOT_COMPARABLE": 1}
    assert (r["amount_variance"], r["weighted_invoice_unit_price"], r["invoiced_amount"]) == ("NOT_AVAILABLE",) * 3
    assert json.loads(r["invoice_amounts_by_currency"]) == {"CNY": "700"}
    assert r["currency"] == "USD" and r["invoice_currencies"] == "CNY"
    assert "币种不可比" in report and "CNY" in report and "USD" in report
    assert {(x["_kind"], x["currency"]) for x in rows(wb["Source Trace"])} == {("po", "USD"), ("invoice", "CNY"), ("receipt", None)}
    assert s["line_results"][0]["amount_variance"] == "NOT_AVAILABLE"


def test_a12_mixed_currency_and_self_check_and_quantity(tmp_path):
    _, s, wb, _, _ = checked(tmp_path, receipts=[receipt(received_quantity="11")], invoices=[invoice(invoice_number="I1", invoiced_quantity="5", invoice_amount="25"), invoice(invoice_number="I2", currency="CNY", invoiced_quantity="5", invoice_unit_price="70", invoice_amount="351")])
    r = line(wb)
    assert {"QTY_OVER", "CURRENCY_MISMATCH", "NOT_COMPARABLE", "AMOUNT_MISMATCH"} <= codes(wb)
    assert "PRICE_MISMATCH" not in codes(wb) and r["amount_variance"] == r["weighted_invoice_unit_price"] == r["invoiced_amount"] == "NOT_AVAILABLE"
    assert json.loads(r["invoice_amounts_by_currency"]) == {"USD": "25", "CNY": "351"}
    assert s["line_results"][0]["invoiced_amount"] == "NOT_AVAILABLE"

def test_a12_absent_invoice_and_incompatible_uom_have_no_monetary_variance(tmp_path):
    (tmp_path / "absent").mkdir(); (tmp_path / "uom").mkdir()
    _, s, wb, _, _ = checked(tmp_path / "absent", invoices=[])
    assert s["totals"]["matched"] == 0 and "NOT_COMPARABLE" in codes(wb)
    assert all(line(wb)[field] == "NOT_AVAILABLE" for field in ("invoiced_amount", "amount_variance", "weighted_invoice_unit_price"))
    _, s, wb, _, _ = checked(tmp_path / "uom", invoices=[invoice(uom="BOX", invoiced_quantity="1", invoice_unit_price="50", invoice_amount="50")])
    assert {"UOM_MISMATCH", "NOT_COMPARABLE"} <= codes(wb)
    assert not {"PRICE_MISMATCH", "AMOUNT_MISMATCH"} & codes(wb)
    assert line(wb)["amount_variance"] == line(wb)["weighted_invoice_unit_price"] == "NOT_AVAILABLE"
    assert s["totals"]["matched"] == 0

def test_a12_invoice_internal_arithmetic_only_on_complete_invoice_row(tmp_path):
    for name in ("consistent", "inconsistent", "missing_price"):
        (tmp_path / name).mkdir()
    _, s, wb, _, _ = checked(tmp_path / "consistent", invoices=[invoice(currency="CNY", invoice_unit_price="70", invoice_amount="700")])
    assert codes(wb) == {"CURRENCY_MISMATCH", "NOT_COMPARABLE"}
    _, s, wb, _, _ = checked(tmp_path / "inconsistent", invoices=[invoice(currency="CNY", invoice_unit_price="70", invoice_amount="701")])
    assert codes(wb) == {"CURRENCY_MISMATCH", "NOT_COMPARABLE", "AMOUNT_MISMATCH"}
    assert line(wb)["amount_variance"] == "NOT_AVAILABLE"
    _, s, wb, _, _ = checked(tmp_path / "missing_price", invoices=[invoice(currency="CNY", invoice_unit_price="", invoice_amount="701")])
    assert "MISSING_REQUIRED_FIELD" in s["exception_code_counts"]
    assert "AMOUNT_MISMATCH" not in codes(wb)


def test_a13_multi_exception_separate_rows(tmp_path):
    _, _, wb, _, _ = checked(tmp_path, receipts=[receipt(received_quantity="11")], invoices=[invoice(invoiced_quantity="11", invoice_unit_price="6", invoice_amount="66")])
    assert {"QTY_OVER", "PRICE_MISMATCH", "AMOUNT_MISMATCH"} <= codes(wb)
    assert {"QTY_OVER", "PRICE_MISMATCH"} <= {r["exception_code"] for r in rows(wb["Exceptions"])}


def test_a14_orphans(tmp_path):
    _, s, wb, _, _ = checked(tmp_path, pos=[], receipts=[receipt(po_number="OTHER")], invoices=[invoice(po_number="OTHER")])
    assert s["totals"]["matched"] == 0 and s["exception_code_counts"] == {"ORPHAN_INVOICE": 1, "ORPHAN_RECEIPT": 1}
    assert len(rows(wb["Unmatched Receipts"])) == len(rows(wb["Unmatched Invoices"])) == 1


def test_a15_deterministic_repeat(tmp_path):
    first = tmp_path / "first"; second = tmp_path / "second"
    first.mkdir(); second.mkdir()
    _, s1, w1, _, _ = checked(first)
    _, s2, w2, _, _ = checked(second)
    assert s1 == s2 and rows(w1["Source Trace"]) == rows(w2["Source Trace"])
    assert rows(w1["Match Summary"]) == rows(w2["Match Summary"])


@pytest.mark.parametrize("bad", ["../outside.csv", "/outside.csv", "bad.txt", "symlink", "same_root"])
def test_a16_reject_paths(tmp_path, bad):
    case = tmp_path / "case"; case.mkdir()
    result = run(case)
    assert result[0].returncode == 0
    mp = case / "manifest.json"
    manifest = json.loads(mp.read_text(encoding="utf-8"))
    if bad == "symlink":
        target = case / "outside.csv"; target.write_text("secret", encoding="utf-8")
        try:
            (case / "input" / "link.csv").symlink_to(target)
        except (OSError, NotImplementedError):
            pytest.skip("symlink privilege unavailable")
        manifest["po_files"] = ["link.csv"]
    elif bad == "same_root":
        pass
    else:
        manifest["po_files"] = [bad]
    mp.write_text(json.dumps(manifest), encoding="utf-8")
    out = case / "input" if bad == "same_root" else case / "rejected"
    proc = subprocess.run([sys.executable, str(SCRIPT), "--manifest", str(mp), "--output", str(out)], capture_output=True, text=True, cwd=case)
    assert proc.returncode == 2 and json.loads(proc.stderr)["error_code"] == "INVALID_INPUT"
    assert not (case / "rejected").exists()


def test_a17_file_limit(tmp_path):
    case = tmp_path / "case"; case.mkdir()
    checked(case)
    mp = case / "manifest.json"
    manifest = json.loads(mp.read_text(encoding="utf-8"))
    manifest["config"] = {"limits": {"max_file_bytes": 1}}
    mp.write_text(json.dumps(manifest), encoding="utf-8")
    proc = subprocess.run([sys.executable, str(SCRIPT), "--manifest", str(mp), "--output", str(case / "limited")], capture_output=True, text=True)
    assert proc.returncode == 2 and json.loads(proc.stderr)["error_code"] == "LIMIT_EXCEEDED"

def test_a17_real_default_file_limit_and_file_count(tmp_path):
    case = tmp_path / "real"; case.mkdir()
    root = case / "input"; root.mkdir()
    oversized = root / "po.csv"
    with oversized.open("wb") as stream:
        stream.truncate(50 * 1024 * 1024 + 1)
    manifest = {"input_root": "input", "po_files": ["po.csv"], "receipt_files": [], "invoice_files": [], "config": {}}
    mp = case / "manifest.json"; mp.write_text(json.dumps(manifest), encoding="utf-8")
    def rejected(name):
        out = case / name
        proc = subprocess.run([sys.executable, str(SCRIPT), "--manifest", str(mp), "--output", str(out)], capture_output=True, text=True)
        assert proc.returncode == 2 and not out.exists()
        assert json.loads(proc.stderr)["error_code"] == "LIMIT_EXCEEDED"
        return json.loads(proc.stderr)["message"]
    assert "52428801" in rejected("oversized") and oversized.stat().st_size == 50 * 1024 * 1024 + 1
    oversized.unlink()
    (root / "po.csv").write_text("po_number\n", encoding="utf-8")
    manifest["po_files"] = ["po.csv"] * 51
    mp.write_text(json.dumps(manifest), encoding="utf-8")
    assert "50 files" in rejected("too_many_files")


def test_a18_formula_text_injection(tmp_path):
    _, _, wb, _, _ = checked(tmp_path, pos=[po(item_code="=CMD")], receipts=[receipt(item_code="=CMD")], invoices=[invoice(item_code="=CMD")])
    assert all(r["item_code"].startswith("'=") for r in rows(wb["Source Trace"]))
    assert all(wb["Source Trace"].cell(row=i, column=3).data_type != "f" for i in range(2, 5))

@pytest.mark.parametrize("hazard", ["formula", "ignored_sheet_formula", "macro", "external_link", "external_relationship"])
def test_a18_reject_active_xlsx_with_traceable_error(tmp_path, hazard):
    case = tmp_path / hazard
    case.mkdir()
    checked(case, xlsx=True)
    source = case / "input" / "po0.xlsx"
    if hazard in {"formula", "ignored_sheet_formula"}:
        book = load_workbook(source)
        book["ignored" if hazard == "ignored_sheet_formula" else "po"]["A2"] = "=1+1"
        book.save(source)
    else:
        member = {"macro": "xl/vbaProject.bin", "external_link": "xl/externalLinks/externalLink1.xml", "external_relationship": "xl/worksheets/_rels/sheet1.xml.rels"}[hazard]
        payload = (b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" '
                   b'Target="https://example.invalid/" TargetMode="External"/></Relationships>') if hazard == "external_relationship" else b"fixture"
        with zipfile.ZipFile(source, "a") as archive:
            archive.writestr(member, payload)
    out = case / "hazard-output"
    proc = subprocess.run([sys.executable, str(SCRIPT), "--manifest", str(case / "manifest.json"), "--output", str(out)], capture_output=True, text=True)
    error = json.loads(proc.stderr)
    assert proc.returncode == 2 and error["error_code"] == "INVALID_INPUT"
    assert "po0.xlsx" in error["message"] and not out.exists()


@pytest.mark.parametrize("value,field,expected", [("", "invoiced_quantity", "MISSING_REQUIRED_FIELD"), ("abc", "invoiced_quantity", "INVALID_INPUT"), ("BOX", "uom", "UOM_MISMATCH")])
def test_a19_missing_malformed_uom(tmp_path, value, field, expected):
    _, s, wb, _, _ = checked(tmp_path, invoices=[invoice(**{field: value})])
    assert expected in s["exception_code_counts"] and s["totals"]["matched"] == 0
    assert not (line(wb)["invoiced_quantity"] == "0")
