"""A01–A18 offline acceptance regression; fictional fixtures only."""
import importlib.util
import json
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

SCRIPT = Path(__file__).resolve().parents[1] / "packages/skills/wangbin-supplier-reconciliation/scripts/reconcile.py"
spec = importlib.util.spec_from_file_location("supplier_reconcile", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
HEADER = "reconciliation_id,document_id,line_id,item_code,amount,currency\n"


def run(tmp_path, supplier="B1,D1,1,M1,100.00,CNY\n", internal="B1,D1,1,M1,100.00,CNY\n", **options):
    tmp_path.mkdir(parents=True, exist_ok=True)
    folder = tmp_path / "in"
    folder.mkdir(exist_ok=True)
    a, b = folder / "supplier.csv", folder / "internal.csv"
    a.write_text(HEADER + supplier, encoding="utf-8")
    b.write_text(HEADER + internal, encoding="utf-8")
    config = {"supplier_input": {"path": str(a), "format": "csv"}, "internal_input": {"path": str(b), "format": "csv"},
              "output_dir": str(tmp_path / "out"), "key_fields": ["reconciliation_id", "document_id", "line_id", "item_code", "currency"], **options}
    return execute(tmp_path, config)


def execute(tmp_path, config):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    status = mod.main(["--config", str(cfg)])
    output = Path(config["output_dir"])
    data = json.loads((output / "reconciliation.json").read_text(encoding="utf-8")) if (output / "reconciliation.json").exists() else None
    return status, data, output


def rows(data):
    return data["results"]


def assert_failure(result, code):
    status, data, out = result
    assert status == 2 and data["errors"][0]["code"] == code
    assert "summary" not in data and not (out / "reconciliation.xlsx").exists()


def test_a01(tmp_path):
    status, data, out = run(tmp_path)
    assert status == 0 and len(rows(data)) == 1 and rows(data)[0]["status"] == "MATCHED"
    assert rows(data)[0]["difference"] == "0.00" and rows(data)[0]["sources"][0]["row_number"] == 2
    assert data["schema_version"] == "1.0" and data["product_id"] == mod.PRODUCT and data["task_id"] == mod.TASK
    assert load_workbook(out / "reconciliation.xlsx").sheetnames == ["Summary", "Matched", "Amount Differences", "Supplier Only", "Internal Only", "Manual Review"]
    assert (out / "reconciliation.md").read_text(encoding="utf-8")


def test_a02(tmp_path):
    _, data, _ = run(tmp_path, internal="B1,D1,1,M1,100.02,CNY\n")
    assert [(r["status"], r["difference"], r["absolute_difference"]) for r in rows(data)] == [("AMOUNT_DIFFERENCE", "-0.02", "0.02")]


def test_a03(tmp_path):
    _, data, _ = run(tmp_path, internal="B1,D2,1,M1,100.00,CNY\n")
    assert {r["status"] for r in rows(data)} == {"ONLY_SUPPLIER", "ONLY_INTERNAL"}
    assert all(r["difference"] is None and (r["supplier"] is None or r["internal"] is None) for r in rows(data))


def test_a04(tmp_path):
    _, data, _ = run(tmp_path, supplier="B1,D1,1,M1,10.00,CNY\nB1,D1,1,M1,20.00,CNY\n")
    assert len(rows(data)) == 1 and rows(data)[0]["status"] == "AMBIGUOUS" and len(rows(data)[0]["sources"]) == 3


def test_a05(tmp_path):
    result = run(tmp_path, supplier="B1,D1,1,M1,100.00,CNY\n", field_mapping={"currency": "missing"})
    assert_failure(result, "FIELD_MAPPING_AMBIGUOUS")
    _, data, _ = run(tmp_path / "invalid-row", supplier="B1,D1,1,M1,100.00,\n")
    assert data["summary"]["by_status"]["INVALID"] == 1
    assert data["results"][0]["sources"][0]["row_number"] == 2
    missing = tmp_path / "missing-header"
    run(missing)
    cfg = json.loads((missing / "config.json").read_text(encoding="utf-8"))
    Path(cfg["supplier_input"]["path"]).write_text(HEADER.replace("currency", "unknown") + "B1,D1,1,M1,1,CNY\n", encoding="utf-8")
    cfg["output_dir"] = str(missing / "fatal")
    assert_failure(execute(missing, cfg), "REQUIRED_FIELD_MISSING")



@pytest.mark.parametrize("value,code", [("abc", "INVALID_AMOUNT"), ("1.234", "INVALID_AMOUNT"), ("NaN", "INVALID_AMOUNT"), ("=SUM(A1:A2)", "FORMULA_CELL")])
def test_a06_amount(tmp_path, value, code):
    _, data, _ = run(tmp_path, supplier=f"B1,D1,1,M1,{value},CNY\n")
    assert {r["status"] for r in rows(data)} == {"INVALID"}
    assert any(e["code"] == code for e in data["errors"])


def test_a06_currency_and_key(tmp_path):
    _, data, _ = run(tmp_path, supplier="B1,D1,1,M1,1.00,人民币\n,D2,1,M1,1.00,CNY\n")
    assert [r["status"] for r in rows(data)].count("INVALID") == 2
    assert {e["code"] for e in data["errors"]} == {"INVALID_CURRENCY", "INVALID_KEY"}


def test_a07(tmp_path):
    a = tmp_path / "supplier.csv"
    a.write_text(HEADER.replace("amount,currency", "amount,amount,currency") + "B1,D1,1,M1,1,1,CNY\n", encoding="utf-8")
    b = tmp_path / "internal.csv"
    b.write_text(HEADER + "B1,D1,1,M1,1,CNY\n", encoding="utf-8")
    cfg = {"supplier_input": {"path": str(a)}, "internal_input": {"path": str(b)}, "output_dir": str(tmp_path / "out")}
    assert_failure(execute(tmp_path, cfg), "DUPLICATE_HEADER")
    a.write_text(HEADER.replace("amount,currency", "金额,含税金额,currency") + "B1,D1,1,M1,1,1,CNY\n", encoding="utf-8")
    cfg["output_dir"] = str(tmp_path / "alias")
    assert_failure(execute(tmp_path, cfg), "FIELD_MAPPING_AMBIGUOUS")


def xlsx(path, sheets=("对账明细", "汇总"), formula=False):
    book = Workbook()
    sheet = book.active
    sheet.title = sheets[0]
    for i, name in enumerate(sheets):
        target = sheet if i == 0 else book.create_sheet(name)
        target.append(HEADER.strip().split(","))
        target.append(["B1", "D1", "1", "M1", "=1+1" if formula else "100.00", "CNY"])
    book.save(path)


def test_a08_a09(tmp_path):
    a = tmp_path / "supplier.xlsx"
    xlsx(a)
    b = tmp_path / "internal.csv"
    b.write_text(HEADER + "B1,D1,1,M1,100.00,CNY\n", encoding="utf-8")
    cfg = {"supplier_input": {"path": str(a), "sheet": "对账明细"}, "internal_input": {"path": str(b)}, "output_dir": str(tmp_path / "out")}
    assert execute(tmp_path, cfg)[1]["results"][0]["supplier"]["source"]["sheet"] == "对账明细"
    cfg["output_dir"] = str(tmp_path / "missing")
    del cfg["supplier_input"]["sheet"]
    assert_failure(execute(tmp_path, cfg), "SHEET_SELECTION_REQUIRED")
    cfg["output_dir"] = str(tmp_path / "notfound")
    cfg["supplier_input"]["sheet"] = "无"
    assert_failure(execute(tmp_path, cfg), "SHEET_NOT_FOUND")


@pytest.mark.parametrize("encoding", ["utf-8-sig", "utf-16", "gb18030"])
def test_a10(tmp_path, encoding):
    status, data, out = run(tmp_path)
    cfg = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    Path(cfg["supplier_input"]["path"]).write_text(HEADER + "B1,D1,1,M1,100.00,CNY\n", encoding=encoding)
    cfg["supplier_input"]["encoding"] = encoding
    cfg["output_dir"] = str(tmp_path / "correct")
    assert execute(tmp_path, cfg)[0] == 0
    cfg["output_dir"] = str(tmp_path / "wrong")
    cfg["supplier_input"]["encoding"] = "utf-16" if encoding != "utf-16" else "utf-8"
    assert_failure(execute(tmp_path, cfg), "ENCODING_INVALID")


def test_a11(tmp_path):
    _, data, out = run(tmp_path, supplier="B1,=1+1,1,+cmd,100.00,CNY\n")
    workbook = load_workbook(out / "reconciliation.xlsx")
    assert all(cell.data_type != "f" for sheet in workbook for row in sheet for cell in row)
    assert any(e["code"] == "FORMULA_CELL" for e in data["errors"])
    assert mod.safe_excel("+cmd").startswith("'+cmd")
    a = tmp_path / "formula.xlsx"
    xlsx(a, formula=True)
    cfg = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    cfg["supplier_input"] = {"path": str(a), "sheet": "对账明细"}
    cfg["output_dir"] = str(tmp_path / "formulaout")
    assert "FORMULA_CELL" in [e["code"] for e in execute(tmp_path, cfg)[1]["errors"]]
    cfg["supplier_input"]["path"] = str(a.with_suffix(".xlsm"))
    cfg["output_dir"] = str(tmp_path / "unsupported")
    assert_failure(execute(tmp_path, cfg), "UNSUPPORTED_FORMAT")


def test_a12(tmp_path):
    run(tmp_path)
    cfg = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    cfg["limits"] = {"max_file_bytes": 30}
    cfg["output_dir"] = str(tmp_path / "size")
    assert_failure(execute(tmp_path, cfg), "INPUT_TOO_LARGE")
    cfg["limits"] = {"max_data_rows": 1}
    cfg["output_dir"] = str(tmp_path / "rows")
    path = Path(cfg["supplier_input"]["path"])
    path.write_text(HEADER + "B1,D1,1,M1,100,CNY\nB1,D2,2,M1,100,CNY\n", encoding="utf-8")
    assert_failure(execute(tmp_path, cfg), "ROW_LIMIT_EXCEEDED")
    cfg["limits"] = {"max_columns": 5}
    cfg["output_dir"] = str(tmp_path / "columns")
    assert_failure(execute(tmp_path, cfg), "COLUMN_LIMIT_EXCEEDED")
    cfg["limits"] = {"max_data_rows": 100000}
    cfg["output_dir"] = str(tmp_path / "actual-rows")
    path.write_text(HEADER + "B1,D1,1,M1,100,CNY\n" * 100001, encoding="utf-8")
    assert_failure(execute(tmp_path, cfg), "ROW_LIMIT_EXCEEDED")
    cfg["output_dir"] = str(tmp_path / "actual-size")
    path.write_bytes(b"X" * (10485760 + 1))
    assert_failure(execute(tmp_path, cfg), "INPUT_TOO_LARGE")


def test_a13(tmp_path):
    _, data, _ = run(tmp_path, supplier="B1,D1,001,abc,1,CNY\nB1,D1,1,ABC,1,CNY\nB1,D2,1,café,1,CNY\n", internal="B1,D1,1,abc,1,CNY\nB1,D2,1,café,1,CNY\n")
    assert [r["status"] for r in rows(data)].count("MATCHED") == 1
    assert [r["status"] for r in rows(data)].count("ONLY_SUPPLIER") == 2


def test_a14(tmp_path):
    _, data, _ = run(tmp_path, supplier="B1,D1,1,M1,-1.00,USD\n", internal="B1,D1,1,M1,0.00,CNY\n", key_fields=["reconciliation_id", "document_id", "line_id", "item_code"])
    assert rows(data)[0]["status"] == "AMBIGUOUS" and len(rows(data)[0]["sources"]) == 2


def test_a15(tmp_path):
    _, data, _ = run(tmp_path, supplier="B1,D1,1,M1,abc,CNY\n")
    assert {r["status"] for r in rows(data)} == {"INVALID"}
    assert_failure(run(tmp_path / "empty", supplier="B1,D1,1,M1,abc,CNY\n", internal="B1,D1,1,M1,abc,CNY\n"), "REQUIRED_FIELD_MISSING")


def test_a16(tmp_path):
    _, one, _ = run(tmp_path)
    cfg = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    cfg["output_dir"] = str(tmp_path / "second")
    _, two, _ = execute(tmp_path, cfg)
    assert one == two
    assert str(tmp_path) not in json.dumps(two)


def test_a17(tmp_path):
    supplier = "B1,D1,1,M1,1,CNY\nB1,D2,2,M1,1,CNY\nB1,D3,3,M1,1,CNY\nB1,D5,5,M1,1,CNY\nB1,D5,5,M1,2,CNY\nB1,D6,6,M1,abc,CNY\n"
    internal = "B1,D1,1,M1,1,CNY\nB1,D2,2,M1,2,CNY\nB1,D4,4,M1,1,CNY\nB1,D5,5,M1,1,CNY\n"
    _, data, out = run(tmp_path, supplier=supplier, internal=internal)
    assert {r["status"] for r in rows(data)} == set(mod.STATUSES)
    assert data["summary"]["total_result_rows"] == len(rows(data))
    assert "来源" in (out / "reconciliation.md").read_text(encoding="utf-8")
    assert load_workbook(out / "reconciliation.xlsx").sheetnames == ["Summary", "Matched", "Amount Differences", "Supplier Only", "Internal Only", "Manual Review"]


@pytest.mark.parametrize("kind,code", [("directory", "INPUT_NOT_REGULAR_FILE"), ("unknown", "UNSUPPORTED_FORMAT"), ("corrupt", "XLSX_PARSE_ERROR"), ("symlink", "INPUT_NOT_REGULAR_FILE")])
def test_a18(tmp_path, kind, code):
    run(tmp_path)
    cfg = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    if kind == "directory":
        path = tmp_path / "directory.csv"
        path.mkdir()
    elif kind == "unknown":
        path = tmp_path / "unknown.xlsm"
        path.write_text("bad", encoding="utf-8")
    elif kind == "corrupt":
        path = tmp_path / "bad.xlsx"
        path.write_bytes(b"not a zip")
        cfg["supplier_input"]["sheet"] = "sheet"
        cfg["supplier_input"].pop("format", None)
    else:
        path = tmp_path / "link.csv"
        try:
            path.symlink_to(cfg["supplier_input"]["path"])
        except OSError:
            pytest.skip("symlink creation requires privileges")
    cfg["supplier_input"]["path"] = str(path)
    cfg["output_dir"] = str(tmp_path / "failed")
    assert_failure(execute(tmp_path, cfg), code)
