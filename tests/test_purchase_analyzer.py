"""采购分析 Skill 的本地验收测试；输入均为虚构数据。"""
from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "packages" / "skills" / "wangbin-purchase-analyzer" / "scripts" / "analyze_purchase.py"
EXAMPLE_INPUT = ROOT / "packages" / "skills" / "wangbin-purchase-analyzer" / "examples" / "fictional-purchases.csv"
EXPECTED_OUTPUT = ROOT / "packages" / "skills" / "wangbin-purchase-analyzer" / "examples" / "fictional-purchases.expected.json"

FIELDS = [
    "order_id", "material", "supplier", "order_date", "quantity", "unit_price",
    "unit", "specification", "currency", "tax_treatment",
]


def load_analyzer():
    spec = importlib.util.spec_from_file_location("purchase_analyzer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, object]], *, fields: list[str] = FIELDS) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def row(order_id: str = "O1", **changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "order_id": order_id, "material": "Steel", "supplier": "Supplier-A",
        "order_date": "2026-01-01", "quantity": "2", "unit_price": "10.00",
        "unit": "kg", "specification": "304", "currency": "CNY", "tax_treatment": "EX",
    }
    value.update(changes)
    return value


def test_normal_calculation_uses_same_comparable_group_and_decimal_totals(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    path = tmp_path / "fictional.csv"
    write_csv(path, [
        row("O1", supplier="Supplier-A", quantity="2", unit_price="10.00", order_date="2026-01-01"),
        row("O2", supplier="Supplier-B", quantity="3", unit_price="12.00", order_date="2026-01-15"),
        row("O3", supplier="Supplier-C", quantity="1", unit_price="11.00", order_date="2026-02-01"),
        row("O4", supplier="Supplier-D", quantity="1", unit_price="20.00", order_date="2026-02-15", tax_treatment="INCLUSIVE"),
        row("O5", supplier="Supplier-E", quantity="1", unit_price="99.99", order_date="2026-02-20", currency="USD"),
        row("O6", material="Bolt", supplier="Supplier-A", quantity="10", unit_price="0.10", unit="pcs", specification="M3", order_date="2026-01-10"),
        row("O7", material="Bolt", supplier="Supplier-A", quantity="10", unit_price="0.30", unit="pcs", specification="M3", order_date="2026-02-10"),
    ])

    result = analyzer.analyze_csv(path, "2026-01-01", "2026-02-28")

    assert result["summary"]["valid_rows"] == 7
    assert result["purchasing_totals"] == [
        {"currency": "CNY", "order_count": 6, "quantity": "27", "total": "91"},
        {"currency": "USD", "order_count": 1, "quantity": "1", "total": "99.99"},
    ]
    steel = next(item for item in result["comparable_price_changes"] if item["material"] == "Steel" and item["tax_treatment"] == "EX")
    assert steel["changes"] == []
    bolt = next(item for item in result["comparable_price_changes"] if item["material"] == "Bolt")
    assert bolt["changes"][0]["change_pct"] == "200"
    assert bolt["changes"][0]["supplier"] == "Supplier-A"
    assert bolt["changes"][0]["comparison_scope"] == "SAME_SUPPLIER"
    assert any(item["type"] == "PRICE_CHANGE" and item["material"] == "Bolt" for item in result["anomaly_candidates"])
    assert any(item["type"] == "SUPPLIER_QUOTE_SPREAD" and item["material"] == "Steel" for item in result["anomaly_candidates"])
    assert not any(item["type"] == "SUPPLIER_QUOTE_SPREAD" and item["material"] == "Bolt" for item in result["anomaly_candidates"])
    steel_spread = next(item for item in result["supplier_quote_spread"] if item["material"] == "Steel" and item["tax_treatment"] == "EX")
    assert steel_spread["comparison_scope"] == "CROSS_SUPPLIER"
    assert steel_spread["supplier_count"] == 3
    assert steel_spread["comparison_period"] == {"start": "2026-01-01", "end": "2026-02-28"}
    assert any(item["status"] == "NOT_COMPARABLE" and "tax_treatment" in item["different_fields"] for item in result["incompatible_group_differences"])
    assert not any(item["material"] == "Steel" and item["type"] == "PRICE_CHANGE" and item.get("order_id") == "O4" for item in result["anomaly_candidates"])
    trend = next(item for item in result["same_period_trend"] if item["currency"] == "CNY")
    assert trend["first_period"]["total"] == "57"
    assert trend["second_period"]["total"] == "34"
    assert trend["change"]["absolute"] == "-23"


def test_missing_columns_and_empty_input_are_clear_fatal_errors(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    missing = tmp_path / "missing.csv"
    write_csv(missing, [row()], fields=FIELDS[:-1])
    with pytest.raises(analyzer.InputError, match="MISSING_COLUMNS"):
        analyzer.analyze_csv(missing, "2026-01-01", "2026-01-31")

    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(analyzer.InputError, match="EMPTY_INPUT"):
        analyzer.analyze_csv(empty, "2026-01-01", "2026-01-31")


def test_missing_empty_and_wrong_type_rows_are_reported_without_crashing(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    path = tmp_path / "invalid.csv"
    write_csv(path, [
        row("O1", supplier="", quantity="2"),
        row("O2", quantity="not-a-number"),
        row("O3", quantity="2", unit_price=""),
    ])
    result = analyzer.analyze_csv(path, "2026-01-01", "2026-01-31")
    assert result["summary"]["valid_rows"] == 0
    assert result["summary"]["invalid_rows"] == 3
    assert {item["code"] for item in result["invalid_rows"]} == {"MISSING_FIELD", "INVALID_DECIMAL"}
    assert all("not-a-number" not in json.dumps(item, ensure_ascii=False) for item in result["invalid_rows"])


def test_missing_unit_is_not_comparable_and_same_supplier_changes_are_not_spreads(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    path = tmp_path / "comparison-boundaries.csv"
    write_csv(path, [
        row("S1", supplier="Supplier-A", unit_price="10", order_date="2026-01-01"),
        row("S2", supplier="Supplier-A", unit_price="15", order_date="2026-01-15"),
        row("MISSING-UNIT", supplier="Supplier-B", unit="", unit_price="12"),
    ])
    result = analyzer.analyze_csv(path, "2026-01-01", "2026-01-31")
    group = next(item for item in result["comparable_price_changes"] if item["material"] == "Steel")
    assert len(group["changes"]) == 1
    assert group["changes"][0]["comparison_scope"] == "SAME_SUPPLIER"
    assert result["supplier_quote_spread"] == []
    assert result["summary"]["invalid_rows"] == 1
    assert result["invalid_rows"][0]["code"] == "MISSING_FIELD"


def test_duplicate_ids_invalid_dates_and_negative_values_are_excluded(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    path = tmp_path / "invalid-values.csv"
    write_csv(path, [
        row("DUP", quantity="1"), row("DUP", quantity="2"),
        row("BAD-DATE", order_date="2026-02-31"),
        row("NEG", quantity="-1"), row("NEGPRICE", unit_price="-0.01"),
        row("OUT", order_date="2027-01-01"),
    ])
    result = analyzer.analyze_csv(path, "2026-01-01", "2026-12-31")
    assert result["summary"]["valid_rows"] == 0
    assert result["summary"]["duplicate_order_ids"] == ["DUP"]
    assert {item["code"] for item in result["invalid_rows"]} >= {"DUPLICATE_ORDER_ID", "INVALID_DATE", "NEGATIVE_VALUE"}
    assert result["summary"]["out_of_range_rows"] == 1


def test_wrong_currency_and_formula_cells_are_rejected_without_leaking_input(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    path = tmp_path / "private.csv"
    write_csv(path, [row("FORMULA", material="=SECRET(1)", currency="CNY"), row("CURRENCY", currency="人民币")])
    result = analyzer.analyze_csv(path, "2026-01-01", "2026-01-31")
    serialized = json.dumps(result, ensure_ascii=False)
    assert "FORMULA_CELL_UNSAFE" in serialized
    assert "INVALID_CURRENCY" in serialized
    assert "=SECRET(1)" not in serialized
    assert str(path) not in serialized
    assert result["privacy"] == {
        "execution_scope": "local_script_only",
        "remote_upload": False,
        "absolute_path_disclosed": False,
        "raw_rows_disclosed": False,
        "identifiers_in_output": True,
    }

def test_formula_order_id_is_never_echoed_in_duplicate_report(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    path = tmp_path / "private.csv"
    write_csv(path, [row("=PRIVATE()"), row("=PRIVATE()")])
    result = analyzer.analyze_csv(path, "2026-01-01", "2026-01-31")
    assert result["summary"]["valid_rows"] == 0
    assert "=PRIVATE()" not in json.dumps(result, ensure_ascii=False)


def test_decimal_precision_big_file_limit_and_missing_cli_file(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    path = tmp_path / "precision.csv"
    write_csv(path, [row("P1", quantity="3", unit_price="0.10"), row("P2", quantity="7", unit_price="0.20", order_date="2026-01-02")])
    result = analyzer.analyze_csv(path, "2026-01-01", "2026-01-31")
    assert result["purchasing_totals"][0]["total"] == "1.7"
    assert result["purchasing_totals"][0]["quantity"] == "10"

    oversized = tmp_path / "oversized.csv"
    oversized.write_bytes(b"x" * (analyzer.MAX_INPUT_BYTES + 1))
    with pytest.raises(analyzer.InputError, match="INPUT_TOO_LARGE"):
        analyzer.analyze_csv(oversized, "2026-01-01", "2026-01-31")

    completed = subprocess.run([sys.executable, str(SCRIPT), "--input", str(tmp_path / "not-there.csv"), "--start-date", "2026-01-01", "--end-date", "2026-01-31"], capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    assert completed.returncode == 2
    assert "INPUT_NOT_FOUND" in completed.stderr
    assert str(tmp_path) not in completed.stderr


def test_determinism_and_example_cli_match_expected_json() -> None:
    analyzer = load_analyzer()
    first = analyzer.analyze_csv(EXAMPLE_INPUT, "2026-01-01", "2026-02-28")
    second = analyzer.analyze_csv(EXAMPLE_INPUT, "2026-01-01", "2026-02-28")
    assert first == second
    completed = subprocess.run([sys.executable, str(SCRIPT), "--input", str(EXAMPLE_INPUT), "--start-date", "2026-01-01", "--end-date", "2026-02-28"], capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == json.loads(EXPECTED_OUTPUT.read_text(encoding="utf-8"))
    assert completed.stderr == ""


def test_required_skill_files_exist() -> None:
    assert (SCRIPT.parent.parent / "SKILL.md").is_file()
    assert (SCRIPT.parent.parent / "manifest.json").is_file()
    assert EXAMPLE_INPUT.is_file()
    assert EXPECTED_OUTPUT.is_file()
