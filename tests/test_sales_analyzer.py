"""销售收入分析 Skill 的本地验收测试；输入均为虚构数据。"""
from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "packages" / "skills" / "wangbin-sales-analyzer" / "scripts" / "analyze_sales.py"
EXAMPLE_INPUT = ROOT / "packages" / "skills" / "wangbin-sales-analyzer" / "examples" / "fictional-sales.csv"
EXPECTED_OUTPUT = ROOT / "packages" / "skills" / "wangbin-sales-analyzer" / "examples" / "fictional-sales.expected.json"
FIELDS = ["order_id", "customer", "product", "order_date", "amount", "currency"]


def load_analyzer():
    spec = importlib.util.spec_from_file_location("sales_analyzer", SCRIPT)
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
        "order_id": order_id,
        "customer": "Customer-A",
        "product": "Product-X",
        "order_date": "2026-02-01",
        "amount": "10.00",
        "currency": "CNY",
    }
    value.update(changes)
    return value


def complete_months(*periods: tuple[str, str]) -> list[tuple[str, str]]:
    return list(periods)


def test_normal_revenue_trend_ranking_and_customer_concentration_keep_currencies_separate(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    path = tmp_path / "sales.csv"
    write_csv(path, [
        row("O1", customer="Customer-A", product="Product-X", order_date="2026-01-15", amount="10.10"),
        row("O2", customer="Customer-B", product="Product-Y", order_date="2026-01-31", amount="20.20"),
        row("O3", customer="Customer-A", product="Product-X", order_date="2026-02-01", amount="30.30"),
        row("O4", customer="Customer-C", product="Product-Y", order_date="2026-02-28", amount="40.40"),
        row("O5", customer="Customer-A", product="Product-Z", order_date="2026-02-20", amount="9.99", currency="USD"),
    ])
    result = analyzer.analyze_csv(
        path,
        "2026-01-01",
        "2026-02-28",
        as_of_date="2026-03-01",
        complete_periods=complete_months(("2026-01-01", "2026-01-31"), ("2026-02-01", "2026-02-28")),
    )
    assert result["summary"] == {"input_rows": 5, "valid_rows": 5, "invalid_rows": 0, "out_of_range_rows": 0, "duplicate_order_ids": []}
    assert result["sales_trend"] == [
        {"currency": "CNY", "period": "2026-01", "order_count": 2, "revenue": "30.3"},
        {"currency": "CNY", "period": "2026-02", "order_count": 2, "revenue": "70.7"},
        {"currency": "USD", "period": "2026-02", "order_count": 1, "revenue": "9.99"},
    ]
    assert result["product_ranking"] == [
        {"currency": "CNY", "product": "Product-Y", "order_count": 2, "revenue": "60.6", "share_pct": "60"},
        {"currency": "CNY", "product": "Product-X", "order_count": 2, "revenue": "40.4", "share_pct": "40"},
        {"currency": "USD", "product": "Product-Z", "order_count": 1, "revenue": "9.99", "share_pct": "100"},
    ]
    assert result["customer_contribution"] == [
        {"currency": "CNY", "customer": "Customer-A", "order_count": 2, "revenue": "40.4", "share_pct": "40"},
        {"currency": "CNY", "customer": "Customer-C", "order_count": 1, "revenue": "40.4", "share_pct": "40"},
        {"currency": "CNY", "customer": "Customer-B", "order_count": 1, "revenue": "20.2", "share_pct": "20"},
        {"currency": "USD", "customer": "Customer-A", "order_count": 1, "revenue": "9.99", "share_pct": "100"},
    ]
    assert result["customer_concentration"] == [
        {"currency": "CNY", "customer_count": 3, "top_1_share_pct": "40", "hhi_pct": "36"},
        {"currency": "USD", "customer_count": 1, "top_1_share_pct": "100", "hhi_pct": "100"},
    ]
    assert result["period_comparisons"]["mom"] == "UNKNOWN"
    assert result["profit_analysis"]["status"] == "UNKNOWN"


def test_mom_yoy_require_explicit_complete_comparable_periods(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    path = tmp_path / "periods.csv"
    write_csv(path, [
        row("JAN", order_date="2025-01-01", amount="10"),
        row("JAN26", order_date="2026-01-01", amount="20"),
        row("DEC", order_date="2025-12-01", amount="30"),
        row("FEB26", order_date="2026-02-01", amount="40"),
    ])
    complete = complete_months(
        ("2025-01-01", "2025-01-31"), ("2025-12-01", "2025-12-31"),
        ("2026-01-01", "2026-01-31"), ("2026-02-01", "2026-02-28"),
    )
    complete_result = analyzer.analyze_csv(path, "2026-01-01", "2026-01-31", as_of_date="2026-02-28", complete_periods=complete)
    assert complete_result["period_comparisons"]["mom"] == {"currency": "CNY", "current": "20", "previous": "30", "change_pct": "-33.33333333"}
    assert complete_result["period_comparisons"]["yoy"] == {"currency": "CNY", "current": "20", "previous": "10", "change_pct": "100"}

    incomplete = analyzer.analyze_csv(path, "2026-01-01", "2026-01-31", as_of_date="2026-02-28", complete_periods=[])
    assert incomplete["period_comparisons"] == {"mom": "UNKNOWN", "yoy": "UNKNOWN"}


def test_missing_columns_and_empty_input_are_fatal(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    missing = tmp_path / "missing.csv"
    write_csv(missing, [row()], fields=FIELDS[:-1])
    with pytest.raises(analyzer.InputError, match="MISSING_COLUMNS"):
        analyzer.analyze_csv(missing, "2026-01-01", "2026-01-31")
    empty = tmp_path / "empty.csv"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(analyzer.InputError, match="EMPTY_INPUT"):
        analyzer.analyze_csv(empty, "2026-01-01", "2026-01-31")


def test_wrong_type_missing_fields_duplicate_invalid_date_and_negative_are_reported(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    path = tmp_path / "invalid.csv"
    write_csv(path, [
        row("DUP", amount="1"), row("DUP", amount="2"),
        row("BAD-DATE", order_date="2026-02-31"),
        row("NEG", amount="-1"), row("WRONG", amount="not-a-number"),
        row("MISSING", customer=""),
    ])
    result = analyzer.analyze_csv(path, "2026-01-01", "2026-12-31")
    assert result["summary"]["valid_rows"] == 0
    assert result["summary"]["duplicate_order_ids"] == ["DUP"]
    assert {item["code"] for item in result["invalid_rows"]} >= {"DUPLICATE_ORDER_ID", "INVALID_DATE", "NEGATIVE_AMOUNT", "INVALID_DECIMAL", "MISSING_FIELD"}
    assert result["operational_risks"]


def test_decimal_precision_large_limit_and_out_of_range(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    path = tmp_path / "precision.csv"
    write_csv(path, [row("P1", amount="0.10", order_date="2026-01-01"), row("P2", amount="0.20", order_date="2026-01-02"), row("OUT", amount="9", order_date="2027-01-01")])
    result = analyzer.analyze_csv(path, "2026-01-01", "2026-01-31")
    assert result["summary"]["valid_rows"] == 3
    assert result["summary"]["out_of_range_rows"] == 1
    assert result["sales_totals"] == [{"currency": "CNY", "order_count": 2, "revenue": "0.3"}]
    oversized = tmp_path / "oversized.csv"
    oversized.write_bytes(b"x" * (analyzer.MAX_INPUT_BYTES + 1))
    with pytest.raises(analyzer.InputError, match="INPUT_TOO_LARGE"):
        analyzer.analyze_csv(oversized, "2026-01-01", "2026-01-31")


def test_privacy_formula_cells_and_unsupported_formats_are_honest(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    path = tmp_path / "private.csv"
    write_csv(path, [row("FORMULA", product="=SECRET(1)"), row("CURRENCY", currency="人民币")])
    result = analyzer.analyze_csv(path, "2026-01-01", "2026-01-31")
    serialized = json.dumps(result, ensure_ascii=False)
    assert "FORMULA_CELL_UNSAFE" in serialized
    assert "INVALID_CURRENCY" in serialized
    assert "=SECRET(1)" not in serialized
    assert str(path) not in serialized
    assert result["privacy"] == {"execution_scope": "local_script_only", "remote_upload": False, "absolute_path_disclosed": False, "raw_input_disclosed": False}
    assert "XLSX/PDF" in " ".join(result["limitations"])


def test_cli_missing_file_is_safe_and_example_is_deterministic() -> None:
    analyzer = load_analyzer()
    first = analyzer.analyze_csv(EXAMPLE_INPUT, "2026-01-01", "2026-02-28", as_of_date="2026-03-01", complete_periods=complete_months(("2026-01-01", "2026-01-31"), ("2026-02-01", "2026-02-28")))
    second = analyzer.analyze_csv(EXAMPLE_INPUT, "2026-01-01", "2026-02-28", as_of_date="2026-03-01", complete_periods=complete_months(("2026-01-01", "2026-01-31"), ("2026-02-01", "2026-02-28")))
    assert first == second
    completed = subprocess.run([sys.executable, str(SCRIPT), "--input", str(EXAMPLE_INPUT), "--start-date", "2026-01-01", "--end-date", "2026-02-28", "--as-of-date", "2026-03-01", "--complete-period", "2026-01-01:2026-01-31", "--complete-period", "2026-02-01:2026-02-28"], capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == json.loads(EXPECTED_OUTPUT.read_text(encoding="utf-8"))
    assert completed.stderr == ""
    missing = subprocess.run([sys.executable, str(SCRIPT), "--input", str(ROOT / "does-not-exist.csv"), "--start-date", "2026-01-01", "--end-date", "2026-01-31"], capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    assert missing.returncode == 2
    assert "INPUT_NOT_FOUND" in missing.stderr
    assert str(ROOT) not in missing.stderr


def test_required_skill_files_exist() -> None:
    assert SCRIPT.parent.parent.joinpath("SKILL.md").is_file()
    assert SCRIPT.parent.parent.joinpath("manifest.json").is_file()
    assert EXAMPLE_INPUT.is_file()
    assert EXPECTED_OUTPUT.is_file()


def test_market_copy_matches_implemented_sales_boundary() -> None:
    skill_copy = (SCRIPT.parent.parent / "SKILL.md").read_text(encoding="utf-8")
    market_copy = (ROOT / "docs" / "financial-skills-market-copy.zh-CN.md").read_text(encoding="utf-8")
    market_copy_en = (ROOT / "docs" / "financial-skills-market-copy.en-US.md").read_text(encoding="utf-8")
    for text in (skill_copy, market_copy, market_copy_en):
        assert "customer/product" not in text.lower() or "not" in text.lower() or "不" in text
        assert "profit" not in text.lower() or "not" in text.lower() or "不" in text
    assert "客户或产品的新增、流失、组合迁移和跨期结构异常尚未实现" in skill_copy
    assert "客户/产品跨期结构异常检测" in skill_copy
    assert "cross-period structural anomaly detection are not implemented" in market_copy_en.lower()
