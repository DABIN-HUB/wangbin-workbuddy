"""库存分析 Skill 的本地验收测试；输入均为虚构数据。"""
from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "packages" / "skills" / "wangbin-inventory-analyzer"
SCRIPT = SKILL / "scripts" / "analyze_inventory.py"
EXAMPLES = SKILL / "examples"
EXAMPLE_BALANCES = EXAMPLES / "fictional-balances.csv"
EXAMPLE_RECEIPTS = EXAMPLES / "fictional-receipts.csv"
EXAMPLE_ISSUES = EXAMPLES / "fictional-issues.csv"
EXAMPLE_MASTER = EXAMPLES / "fictional-master.csv"
EXPECTED_OUTPUT = EXAMPLES / "fictional-inventory.expected.json"

BALANCE_FIELDS = ["item_id", "warehouse", "balance_date", "quantity", "unit_cost", "currency"]
RECEIPT_FIELDS = ["receipt_id", "item_id", "warehouse", "receipt_date", "quantity", "unit_cost", "currency"]
ISSUE_FIELDS = ["issue_id", "item_id", "warehouse", "issue_date", "quantity", "currency"]
MASTER_FIELDS = ["item_id", "item_name", "unit", "reorder_point", "max_stock"]


def load_analyzer():
    spec = importlib.util.spec_from_file_location("inventory_analyzer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def balance(item_id="A", **changes):
    value = {"item_id": item_id, "warehouse": "WH-A", "balance_date": "2026-01-01", "quantity": "100", "unit_cost": "2.50", "currency": "CNY"}
    value.update(changes)
    return value


def receipt(receipt_id="R1", **changes):
    value = {"receipt_id": receipt_id, "item_id": "A", "warehouse": "WH-A", "receipt_date": "2026-01-15", "quantity": "20", "unit_cost": "2.50", "currency": "CNY"}
    value.update(changes)
    return value


def issue(issue_id="I1", **changes):
    value = {"issue_id": issue_id, "item_id": "A", "warehouse": "WH-A", "issue_date": "2026-01-20", "quantity": "30", "currency": "CNY"}
    value.update(changes)
    return value


def make_inputs(tmp_path: Path, balances=None, receipts=None, issues=None, master=None):
    paths = {}
    for name, rows, fields, default in (("balances", balances, BALANCE_FIELDS, [balance()]), ("receipts", receipts, RECEIPT_FIELDS, [receipt()]), ("issues", issues, ISSUE_FIELDS, [issue()])):
        rows_to_write = default if rows is None else rows
        path = tmp_path / f"{name}.csv"
        write_csv(path, rows_to_write, fields)
        paths[name] = path
    if master is not None:
        path = tmp_path / "master.csv"
        write_csv(path, master, MASTER_FIELDS)
        paths["master"] = path
    return paths


def test_normal_balances_value_candidates_and_complete_turnover(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    paths = make_inputs(
        tmp_path,
        balances=[
            balance("A", balance_date="2026-01-01", quantity="100"),
            balance("A", balance_date="2026-01-31", quantity="90"),
            balance("B", balance_date="2026-01-01", quantity="50", unit_cost="1.10"),
            balance("B", balance_date="2026-01-31", quantity="50", unit_cost="1.10"),
            balance("C", balance_date="2026-01-01", quantity="300", unit_cost="1"),
            balance("C", balance_date="2026-01-31", quantity="300", unit_cost="1"),
        ],
        receipts=[receipt("R-A", item_id="A", receipt_date="2026-01-10", quantity="20")],
        issues=[issue("I-A", item_id="A", issue_date="2026-01-20", quantity="30")],
        master=[
            {"item_id": "A", "item_name": "青铜齿轮", "unit": "pcs", "reorder_point": "20", "max_stock": "120"},
            {"item_id": "B", "item_name": "蓝色垫片", "unit": "pcs", "reorder_point": "10", "max_stock": "100"},
            {"item_id": "C", "item_name": "慢速轴承", "unit": "pcs", "reorder_point": "20", "max_stock": "200"},
        ],
    )
    result = analyzer.analyze_csv(paths["balances"], paths["receipts"], paths["issues"], "2026-01-31", paths["master"])
    assert result["summary"] == {"balances_read": 6, "receipts_read": 1, "issues_read": 1, "valid_balances": 6, "valid_receipts": 1, "valid_issues": 1, "master_read": 3, "invalid_rows": 0, "out_of_range_rows": 0, "duplicate_ids": []}
    assert result["inventory_value"] == [{"currency": "CNY", "value": "580", "quantity": "440"}]
    item_a = next(item for item in result["inventory"] if item["item_id"] == "A")
    assert item_a["quantity"] == "90" and item_a["value"] == "225"
    assert item_a["quantity_turnover"] == "0.31578947"
    assert not any(item["item_id"] == "B" for item in result["no_movement_candidates"])
    assert any(item["item_id"] == "C" for item in result["overstock_candidates"])
    assert result["anomaly_candidates"] == []


def test_turnover_is_unknown_without_comparable_evidence_and_master_is_optional(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    paths = make_inputs(tmp_path, balances=[balance("A")], receipts=[], issues=[])
    result = analyzer.analyze_csv(paths["balances"], paths["receipts"], paths["issues"], "2026-01-31")
    assert result["inventory"][0]["quantity_turnover"] == "UNKNOWN"
    assert result["inventory"][0]["turnover_status"] == "UNKNOWN_INCOMPLETE_PERIOD"
    assert result["overstock_candidates"] == []
    assert result["assumptions"]


def test_missing_issue_data_is_not_treated_as_zero_turnover(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    paths = make_inputs(
        tmp_path,
        balances=[balance("A", balance_date="2026-01-01"), balance("A", balance_date="2026-01-31")],
        receipts=[],
        issues=[],
    )
    result = analyzer.analyze_csv(paths["balances"], paths["receipts"], paths["issues"], "2026-01-31")
    item = result["inventory"][0]
    assert item["turnover_status"] == "UNKNOWN_NO_ISSUE_DATA"
    assert item["issue_data_status"] == "NOT_PROVIDED"
    assert item["quantity_turnover"] == "UNKNOWN"
    assert result["slow_moving_candidates"] == []
    assert result["no_movement_candidates"] == []


def test_known_zero_issue_period_and_no_inventory_are_distinct(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    paths = make_inputs(
        tmp_path,
        balances=[
            balance("A", balance_date="2025-12-31", quantity="10"),
            balance("A", balance_date="2026-01-31", quantity="10"),
            balance("EMPTY", balance_date="2025-12-31", quantity="0"),
            balance("EMPTY", balance_date="2026-01-31", quantity="0"),
        ],
        receipts=[],
        issues=[issue("OLD", item_id="A", issue_date="2025-12-01", quantity="1")],
    )
    result = analyzer.analyze_csv(paths["balances"], paths["receipts"], paths["issues"], "2026-01-31")
    known_zero = next(item for item in result["inventory"] if item["item_id"] == "A")
    no_inventory = next(item for item in result["inventory"] if item["item_id"] == "EMPTY")
    assert known_zero["turnover_status"] == "KNOWN_ZERO"
    assert known_zero["quantity_turnover"] == "0"
    assert any(item["item_id"] == "A" for item in result["slow_moving_candidates"])
    assert no_inventory["turnover_status"] == "NO_INVENTORY"
    assert no_inventory["quantity_turnover"] == "UNKNOWN"
    assert not any(item["item_id"] == "EMPTY" for item in result["slow_moving_candidates"] + result["no_movement_candidates"])


def test_latest_snapshot_before_as_of_is_incomplete_cross_period(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    paths = make_inputs(
        tmp_path,
        balances=[balance("A", balance_date="2026-01-01"), balance("A", balance_date="2026-01-31")],
        receipts=[],
        issues=[issue("I1", issue_date="2026-01-15")],
    )
    result = analyzer.analyze_csv(paths["balances"], paths["receipts"], paths["issues"], "2026-02-28")
    item = result["inventory"][0]
    assert item["period_status"] == "INCOMPLETE"
    assert item["turnover_status"] == "UNKNOWN_INCOMPLETE_PERIOD"
    assert result["slow_moving_candidates"] == []
    assert result["no_movement_candidates"] == []


def test_missing_columns_and_empty_input_are_fatal(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    paths = make_inputs(tmp_path)
    missing = tmp_path / "missing.csv"
    write_csv(missing, [balance()], BALANCE_FIELDS[:-1])
    with pytest.raises(analyzer.InputError, match="MISSING_COLUMNS"):
        analyzer.analyze_csv(missing, paths["receipts"], paths["issues"], "2026-01-31")
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(analyzer.InputError, match="EMPTY_INPUT"):
        analyzer.analyze_csv(empty, paths["receipts"], paths["issues"], "2026-01-31")


def test_wrong_type_duplicate_invalid_date_negative_and_formula_are_safe(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    paths = make_inputs(
        tmp_path,
        balances=[balance("DUP"), balance("DUP", balance_date="2026-01-01"), balance("BAD", balance_date="2026-02-31"), balance("NEG", quantity="-1"), balance("TEXT", unit_cost="not-number"), balance("=SECRET(1)")],
        receipts=[receipt("DUP-R", quantity="-1"), receipt("TEXT-R", quantity="oops")],
        issues=[issue("DUP-I"), issue("DUP-I", issue_date="2026-01-21")],
    )
    result = analyzer.analyze_csv(paths["balances"], paths["receipts"], paths["issues"], "2026-01-31")
    serialized = json.dumps(result, ensure_ascii=False)
    codes = {item["code"] for item in result["invalid_rows"]}
    assert {"DUPLICATE_ID", "INVALID_DATE", "NEGATIVE_VALUE", "INVALID_DECIMAL", "FORMULA_CELL_UNSAFE"} <= codes
    assert "=SECRET(1)" not in serialized
    assert str(tmp_path) not in serialized
    assert result["summary"]["duplicate_ids"] == ["DUP", "DUP-I"]


def test_decimal_precision_size_and_invalid_date_range(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    paths = make_inputs(tmp_path, balances=[balance("P", quantity="3", unit_cost="0.10"), balance("P", balance_date="2026-01-31", quantity="7", unit_cost="0.20")], receipts=[], issues=[])
    result = analyzer.analyze_csv(paths["balances"], paths["receipts"], paths["issues"], "2026-01-31")
    assert result["inventory"][0]["value"] == "1.4"
    oversized = tmp_path / "oversized.csv"
    oversized.write_bytes(b"x" * (analyzer.MAX_INPUT_BYTES + 1))
    with pytest.raises(analyzer.InputError, match="INPUT_TOO_LARGE"):
        analyzer.analyze_csv(oversized, paths["receipts"], paths["issues"], "2026-01-31")
    with pytest.raises(analyzer.InputError, match="INVALID_DATE"):
        analyzer.analyze_csv(paths["balances"], paths["receipts"], paths["issues"], "31-01-2026")


def test_determinism_and_actual_sample_expected_json() -> None:
    analyzer = load_analyzer()
    first = analyzer.analyze_csv(EXAMPLE_BALANCES, EXAMPLE_RECEIPTS, EXAMPLE_ISSUES, "2026-02-28", EXAMPLE_MASTER)
    second = analyzer.analyze_csv(EXAMPLE_BALANCES, EXAMPLE_RECEIPTS, EXAMPLE_ISSUES, "2026-02-28", EXAMPLE_MASTER)
    assert first == second
    completed = subprocess.run([sys.executable, str(SCRIPT), "--balances", str(EXAMPLE_BALANCES), "--receipts", str(EXAMPLE_RECEIPTS), "--issues", str(EXAMPLE_ISSUES), "--master", str(EXAMPLE_MASTER), "--as-of", "2026-02-28"], capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == json.loads(EXPECTED_OUTPUT.read_text(encoding="utf-8"))
    assert completed.stderr == ""


def test_cli_missing_input_is_safe_and_required_files_exist(tmp_path: Path) -> None:
    completed = subprocess.run([sys.executable, str(SCRIPT), "--balances", str(tmp_path / "absent.csv"), "--receipts", str(tmp_path / "r.csv"), "--issues", str(tmp_path / "i.csv"), "--as-of", "2026-01-31"], capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    assert completed.returncode == 2
    assert "INPUT_NOT_FOUND" in completed.stderr
    assert str(tmp_path) not in completed.stderr
    assert (SKILL / "SKILL.md").is_file() and (SKILL / "manifest.json").is_file()


def test_wrong_type_and_symlink_are_rejected(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    paths = make_inputs(tmp_path)
    wrong_type = tmp_path / "balances.txt"
    wrong_type.write_text(paths["balances"].read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(analyzer.InputError, match="INPUT_TYPE_UNSUPPORTED"):
        analyzer.analyze_csv(wrong_type, paths["receipts"], paths["issues"], "2026-01-31")
    link = tmp_path / "linked.csv"
    try:
        link.symlink_to(paths["balances"])
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(analyzer.InputError, match="INPUT_SYMLINK"):
        analyzer.analyze_csv(link, paths["receipts"], paths["issues"], "2026-01-31")
