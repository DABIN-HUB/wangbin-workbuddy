"""Product-scoped, fictional-data acceptance for the receivables Skill."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "packages/skills/wangbin-receivable-analyzer"
SCRIPT = SKILL / "scripts/analyze_receivables.py"
HEADER = "invoice_id,customer_id,due_date,open_balance,currency\n"


def run(path: Path, *, as_of: str = "2026-10-27") -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), "--input", str(path), "--as-of", as_of],
                          cwd=ROOT, text=True, capture_output=True)


def csv_file(tmp_path: Path, body: str, name: str = "invoices.csv") -> Path:
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return path


def test_amounts_aging_customer_priority_and_decimal_precision(tmp_path: Path) -> None:
    path = csv_file(tmp_path, HEADER + "i1,c1,2026-10-26,0.10,CNY\n"
                    "i2,c1,2026-09-20,0.20,CNY\n"
                    "i3,c2,2026-10-27,0.30,CNY\n"
                    "i4,c3,2026-06-01,2.00,USD\n")
    result = run(path)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["as_of"] == "2026-10-27"
    assert data["totals"]["CNY"] == {"open": "0.60", "overdue": "0.30"}
    assert data["totals"]["USD"] == {"open": "2.00", "overdue": "2.00"}
    assert data["aging"]["CNY"]["1-30"]["amount"] == "0.10"
    assert data["aging"]["CNY"]["31-60"]["amount"] == "0.20"
    assert data["aging"]["USD"]["91+"]["amount"] == "2.00"
    assert data["customers"]["CNY"][0]["customer_id"] == "c1"
    assert data["customers"]["CNY"][0]["priority"] in {"HIGH", "MEDIUM", "REVIEW"}
    assert data["valid_rows"] == 4
    assert data["issues"] == []
    assert run(path).stdout == result.stdout


def test_missing_header_empty_wrong_type_and_invalid_as_of(tmp_path: Path) -> None:
    for text in ("", "invoice_id,customer_id\na,c\n"):
        result = run(csv_file(tmp_path, text))
        assert result.returncode != 0
        assert str(tmp_path) not in result.stderr + result.stdout
    for name in ("orders.txt", "orders.xlsx"):
        result = run(csv_file(tmp_path, HEADER + "i,c,2026-10-01,1.00,CNY\n", name))
        assert result.returncode != 0
    assert run(csv_file(tmp_path, HEADER), as_of="2026-02-30").returncode != 0


def test_duplicate_invalid_date_negative_missing_and_formula_are_excluded(tmp_path: Path) -> None:
    path = csv_file(tmp_path, HEADER + "i1,c1,2026-09-01,1.00,CNY\n"
                    "i1,c2,2026-09-01,999,CNY\n"
                    "i3,c3,2026-02-30,2,CNY\n"
                    "i4,c4,2026-09-01,-5,CNY\n"
                    "i5,,2026-09-01,3,CNY\n"
                    "i6,c6,2026-09-01,=4+1,CNY\n")
    result = run(path)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["valid_rows"] == 1
    assert data["totals"]["CNY"]["open"] == "1.00"
    assert len(data["issues"]) == 5
    assert all("row" in issue and "code" in issue for issue in data["issues"])
    assert "999" not in result.stdout and "c6" not in result.stdout
    assert str(tmp_path) not in result.stdout + result.stderr


def test_header_only_large_input_symlink_and_non_utf8(tmp_path: Path) -> None:
    result = run(csv_file(tmp_path, HEADER))
    assert result.returncode != 0
    path = csv_file(tmp_path, HEADER + "x,c,2026-09-01,1,CNY\n" + (" " * 1_048_576))
    assert run(path).returncode != 0
    bad = tmp_path / "bad.csv"
    bad.write_bytes(b"\xff\xfe")
    assert run(bad).returncode != 0
    target = csv_file(tmp_path, HEADER + "i,c,2026-09-01,1,CNY\n", "real.csv")
    alias = tmp_path / "linked.csv"
    try:
        alias.symlink_to(target)
    except (OSError, NotImplementedError):
        return
    assert run(alias).returncode != 0


def test_fictional_example_matches_generated_expected_json() -> None:
    result = run(SKILL / "examples/fictional-receivables.csv")
    assert result.returncode == 0, result.stderr
    expected = json.loads((SKILL / "examples/fictional-receivables.expected.json").read_text(encoding="utf-8"))
    assert json.loads(result.stdout) == expected


def test_multiline_csv_issue_uses_actual_physical_line_number(tmp_path: Path) -> None:
    path = csv_file(tmp_path, HEADER + 'i1,"cust\n id",2026-09-01,1.00,CNY\n'
                    "i2,c2,2026-02-30,2.00,CNY\n")
    result = run(path)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["issues"] == [{"row": 4, "code": "INVALID_DATE"}]
