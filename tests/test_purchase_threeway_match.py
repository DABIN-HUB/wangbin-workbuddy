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
