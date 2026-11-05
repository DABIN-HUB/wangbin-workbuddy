"""Offline deterministic two-sided supplier reconciliation. Python 3.10+, openpyxl."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import unicodedata
import zipfile
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

PRODUCT = "wangbin-supplier-reconciliation"
TASK = "t_9d7ec034"
REQUIRED = ("reconciliation_id", "document_id", "line_id", "item_code", "amount", "currency")
DEFAULT_KEY = list(REQUIRED[:4]) + ["currency"]
ALIASES = {
    "reconciliation_id": ("对账批次", "批次号"), "document_id": ("单据号", "发票号", "订单号"),
    "line_id": ("行号", "明细行号"), "item_code": ("物料编码", "商品编码"),
    "amount": ("金额", "含税金额", "总额"), "currency": ("币种", "货币"),
    "supplier_id": ("供应商", "供应商编码"), "document_date": ("单据日期", "日期"),
    "quantity": ("数量",), "unit": ("单位",), "description": ("描述", "备注"),
}
STATUSES = ("MATCHED", "AMOUNT_DIFFERENCE", "ONLY_SUPPLIER", "ONLY_INTERNAL", "AMBIGUOUS", "INVALID")
AMOUNT = re.compile(r"[+-]?(?:0|[0-9]+)(?:\.[0-9]+)?\Z", re.ASCII)
CURRENCY = re.compile(r"[A-Z]{3}\Z", re.ASCII)


class Problem(Exception):
    def __init__(self, code, side=None, source=None):
        super().__init__(code)
        self.code, self.side, self.source = code, side, source


def issue(code, side=None, source=None, fatal=True):
    return {"code": code, "message": code, "side": side, "source": source, "fatal": fatal}


def stable(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def normalized(value):
    return unicodedata.normalize("NFC", str(value)).strip() if value is not None else ""


def checked_file(spec, side, limits):
    if not isinstance(spec, dict) or not isinstance(spec.get("path"), str):
        raise Problem("INPUT_NOT_FOUND", side)
    path = Path(spec["path"])
    if path.suffix.lower() not in (".csv", ".xlsx") or spec.get("format", path.suffix[1:].lower()) != path.suffix[1:].lower():
        raise Problem("UNSUPPORTED_FORMAT", side)
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise Problem("INPUT_NOT_REGULAR_FILE", side)
    if not path.is_file():
        raise Problem("INPUT_NOT_FOUND", side)
    if path.stat().st_size > limits["max_file_bytes"]:
        raise Problem("INPUT_TOO_LARGE", side)
    if path.suffix.lower() == ".xlsx" and not spec.get("sheet"):
        raise Problem("SHEET_SELECTION_REQUIRED", side)
    if path.suffix.lower() == ".csv" and spec.get("sheet") is not None:
        raise Problem("SHEET_SELECTION_REQUIRED", side)
    try:
        raw = path.read_bytes()
    except OSError:
        raise Problem("INPUT_NOT_FOUND", side) from None
    return path, raw


def rows_for(path, raw, spec, side, limits):
    if path.suffix.lower() == ".csv":
        encoding = spec.get("encoding") or "utf-8-sig"
        if encoding.lower().replace("_", "-") not in ("utf-8", "utf-8-sig", "utf-16", "gb18030"):
            raise Problem("ENCODING_INVALID", side)
        if encoding.lower() == "utf-16" and not raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            raise Problem("ENCODING_INVALID", side)
        try:
            text = raw.decode(encoding)
            if text.startswith("\ufeff"):
                text = text[1:]
            if "\x00" in text or "\ufffd" in text:
                raise UnicodeError()
            reader = csv.reader(io.StringIO(text, newline=""), strict=True)
            rows = list(reader)
            if not rows:
                raise Problem("REQUIRED_FIELD_MISSING", side)
        except (UnicodeError, LookupError):
            raise Problem("ENCODING_INVALID", side) from None
        except csv.Error:
            raise Problem("CSV_PARSE_ERROR", side) from None
    else:
        try:
            from openpyxl import load_workbook
        except ImportError:
            raise Problem("DEPENDENCY_MISSING", side) from None
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                if archive.testzip() is not None or len(archive.namelist()) > 5000 or sum(i.file_size for i in archive.infolist()) > 100 * 1024 * 1024:
                    raise ValueError("unsafe archive")
            book = load_workbook(io.BytesIO(raw), read_only=True, data_only=False, keep_links=False)
            if spec["sheet"] not in book.sheetnames:
                book.close()
                raise Problem("SHEET_NOT_FOUND", side)
            sheet = book[spec["sheet"]]
            rows = []
            for row in sheet.iter_rows():
                if len(row) > limits["max_columns"]:
                    raise Problem("COLUMN_LIMIT_EXCEEDED", side)
                rows.append([("=FORMULA_CELL" if cell.data_type == "f" else cell.value) for cell in row])
                if len(rows) > limits["max_data_rows"] + 1:
                    raise Problem("ROW_LIMIT_EXCEEDED", side)
            book.close()
            if not rows:
                raise Problem("REQUIRED_FIELD_MISSING", side)
        except Problem:
            raise
        except Exception:
            raise Problem("XLSX_PARSE_ERROR", side) from None
    if len(rows[0]) > limits["max_columns"] or any(len(row) > limits["max_columns"] for row in rows):
        raise Problem("COLUMN_LIMIT_EXCEEDED", side)
    while len(rows) > 1 and not any(v is not None and str(v).strip() for v in rows[-1]):
        rows.pop()
    if len(rows) - 1 > limits["max_data_rows"]:
        raise Problem("ROW_LIMIT_EXCEEDED", side)
    return rows


def mapping_for(headers, explicit, side):
    headers = [normalized(h) for h in headers]
    if len(headers) != len(set(headers)):
        raise Problem("DUPLICATE_HEADER", side)
    if not isinstance(explicit, dict) or any(k not in ALIASES or not isinstance(v, str) for k, v in explicit.items()):
        raise Problem("FIELD_MAPPING_AMBIGUOUS", side)
    mapping = {}
    for key in ALIASES:
        if key in explicit:
            hits = [i for i, h in enumerate(headers) if h == normalized(explicit[key])]
            if len(hits) != 1:
                raise Problem("FIELD_MAPPING_AMBIGUOUS", side)
        else:
            hits = [i for i, h in enumerate(headers) if h in (key, *ALIASES[key])]
            if len(hits) > 1:
                raise Problem("FIELD_MAPPING_AMBIGUOUS", side)
        if hits:
            mapping[key] = hits[0]
    if len(set(mapping.values())) != len(mapping):
        raise Problem("FIELD_MAPPING_AMBIGUOUS", side)
    if any(key not in mapping for key in REQUIRED):
        raise Problem("REQUIRED_FIELD_MISSING", side)
    return mapping, {key: headers[pos] for key, pos in mapping.items()}


def amount_of(value, scale, negative):
    text = normalized(value)
    if text.startswith("=") or text.startswith("@") or (text.startswith("+") and not AMOUNT.fullmatch(text)):
        raise Problem("FORMULA_CELL")
    if not AMOUNT.fullmatch(text):
        raise Problem("INVALID_AMOUNT")
    try:
        number = Decimal(text)
        if number.as_tuple().exponent < -scale or (not negative and number < 0):
            raise Problem("INVALID_AMOUNT")
        return number
    except InvalidOperation:
        raise Problem("INVALID_AMOUNT") from None


def safe_excel(value):
    text = "" if value is None else str(value)
    if text.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + text + " [SAFE_TEXT]"
    return text


def safe_md(value):
    return normalized(value).replace("|", "\\|").replace("\n", " ").replace("\r", " ")[:80]


def reconcile(config):
    limits = {"max_file_bytes": 10485760, "max_data_rows": 100000, "max_columns": 200}
    for key, val in config.get("limits", {}).items():
        if key not in limits or type(val) is not int or val < 1 or val > limits[key]:
            raise Problem("INPUT_TOO_LARGE")
        limits[key] = val
    key_fields = config.get("key_fields", DEFAULT_KEY)
    if not isinstance(key_fields, list) or not key_fields or len(key_fields) != len(set(key_fields)) or any(f not in REQUIRED or f == "amount" for f in key_fields):
        raise Problem("INVALID_KEY")
    scale = config.get("amount_scale", 2)
    if type(scale) is not int or not 0 <= scale <= 2:
        raise Problem("INVALID_AMOUNT")
    try:
        tolerance_text = config.get("amount_tolerance", "0.01")
        if not isinstance(tolerance_text, str):
            raise ValueError()
        tolerance = amount_of(tolerance_text, scale, True)
        if tolerance < 0:
            raise ValueError()
    except (Problem, ValueError):
        raise Problem("INVALID_AMOUNT") from None
    indexed = {"supplier": defaultdict(list), "internal": defaultdict(list)}
    invalid_keys = {"supplier": set(), "internal": set()}
    invalid, errors, inputs = [], [], []
    for side in ("supplier", "internal"):
        spec = config.get(side + "_input")
        path, raw = checked_file(spec, side, limits)
        rows = rows_for(path, raw, spec, side, limits)
        mapping, mapping_names = mapping_for(rows[0], config.get("field_mapping", {}), side)
        digest = hashlib.sha256(raw).hexdigest()
        inputs.append({"side": side, "file_name": path.name, "sheet": spec.get("sheet"), "sha256": digest, "field_mapping": mapping_names})
        for rownum, row in enumerate(rows[1:], 2):
            if not any(v is not None and str(v).strip() for v in row):
                continue
            source = {"file_name": path.name, "sheet": spec.get("sheet"), "row_number": rownum}
            fields = {k: normalized(row[pos] if pos < len(row) else None) for k, pos in mapping.items()}
            try:
                if any(v.startswith("=FORMULA_CELL") for v in fields.values()):
                    raise Problem("FORMULA_CELL")
                if any(fields.get(k, "").startswith(("=", "+", "@")) for k in key_fields):
                    raise Problem("FORMULA_CELL")
                if any(not fields.get(k) or fields[k].upper() in ("NA", "NULL") for k in REQUIRED if k != "amount"):
                    raise Problem("INVALID_KEY")
                if not CURRENCY.fullmatch(fields["currency"]):
                    raise Problem("INVALID_CURRENCY")
                amount = amount_of(fields["amount"], scale, config.get("allow_negative_amount", True))
                key = tuple(fields[k] for k in key_fields)
                indexed[side][key].append({"amount": amount, "source": source, "currency": fields["currency"]})
            except Problem as exc:
                if all(fields.get(k) for k in key_fields):
                    invalid_keys[side].add(tuple(fields[k] for k in key_fields))
                err = issue(exc.code, side, source, False)
                errors.append(err)
                invalid.append({"result_id": stable([side, digest, spec.get("sheet"), rownum, exc.code]), "status": "INVALID", "key": None, "supplier": None, "internal": None, "difference": None, "absolute_difference": None, "error_codes": [exc.code], "sources": [source]})
    if not any(indexed[s] for s in indexed):
        raise Problem("REQUIRED_FIELD_MISSING")
    results = []
    for key in sorted(set(indexed["supplier"]) | set(indexed["internal"])):
        left, right = indexed["supplier"][key], indexed["internal"][key]
        if (not left and key in invalid_keys["supplier"]) or (not right and key in invalid_keys["internal"]):
            continue
        currencies = {item["currency"] for item in left + right}
        if len(left) > 1 or len(right) > 1 or len(currencies) > 1:
            status = "AMBIGUOUS"
        elif not left:
            status = "ONLY_INTERNAL"
        elif not right:
            status = "ONLY_SUPPLIER"
        else:
            status = "MATCHED" if abs(left[0]["amount"] - right[0]["amount"]) <= tolerance else "AMOUNT_DIFFERENCE"
        diff = left[0]["amount"] - right[0]["amount"] if status in ("MATCHED", "AMOUNT_DIFFERENCE") else None
        row = {"result_id": stable([status, key]), "status": status, "key": dict(zip(key_fields, key)),
               "supplier": {"amount": f'{left[0]["amount"]:.{scale}f}', "source": left[0]["source"]} if len(left) == 1 else None,
               "internal": {"amount": f'{right[0]["amount"]:.{scale}f}', "source": right[0]["source"]} if len(right) == 1 else None,
               "difference": f"{diff:.{scale}f}" if diff is not None else None,
               "absolute_difference": f"{abs(diff):.{scale}f}" if diff is not None else None,
               "error_codes": [], "sources": [r["source"] for r in left + right]}
        results.append(row)
    results += invalid
    results.sort(key=lambda r: (r["status"], json.dumps(r["key"], sort_keys=True, ensure_ascii=False) if r["key"] else "", r["result_id"]))
    by_currency = defaultdict(lambda: Counter())
    for row in results:
        currency = row["key"].get("currency", "UNSPECIFIED") if row["key"] else "UNSPECIFIED"
        by_currency[currency][row["status"]] += 1
    report = {"schema_version": "1.0", "product_id": PRODUCT, "task_id": TASK,
              "run": {"key_fields": key_fields, "amount_tolerance": f"{tolerance:.{scale}f}", "inputs": inputs},
              "summary": {"total_result_rows": len(results), "by_status": {k: sum(r["status"] == k for r in results) for k in STATUSES}, "by_currency": {k: dict(sorted(v.items())) for k, v in sorted(by_currency.items())}},
              "results": results, "errors": errors, "security": {"network": False, "formulas_executed": False, "macros_executed": False}}
    return report


def write_report(report, output):
    try:
        from openpyxl import Workbook
    except ImportError:
        raise Problem("DEPENDENCY_MISSING") from None
    output.mkdir(parents=True, exist_ok=True)
    book = Workbook()
    table = book.active
    assert table is not None
    table.title = "Results"
    headers = ["status", "result_id", "key", "supplier_amount", "internal_amount", "difference", "absolute_difference", "supplier_source", "internal_source", "sources", "error_codes"]
    table.append(headers)
    for r in report.get("results", []):
        table.append([safe_excel(v) for v in (r["status"], r["result_id"], json.dumps(r["key"], ensure_ascii=False),
                      r["supplier"]["amount"] if r["supplier"] else None, r["internal"]["amount"] if r["internal"] else None,
                      r["difference"], r["absolute_difference"], json.dumps(r["supplier"]["source"], ensure_ascii=False) if r["supplier"] else None,
                      json.dumps(r["internal"]["source"], ensure_ascii=False) if r["internal"] else None,
                      json.dumps(r["sources"], ensure_ascii=False), ",".join(r["error_codes"]))])
    summary = book.create_sheet("Summary")
    summary.append(["currency", "status", "count"])
    for currency, statuses in report.get("summary", {}).get("by_currency", {}).items():
        for status, count in statuses.items():
            summary.append([safe_excel(currency), status, count])
    errors = book.create_sheet("Errors")
    errors.append(["code", "side", "source", "message"])
    for err in report["errors"]:
        errors.append([safe_excel(err["code"]), safe_excel(err["side"]), safe_excel(json.dumps(err["source"], ensure_ascii=False)), safe_excel(err["message"])])
    book.save(output / "reconciliation.xlsx")
    lines = ["# 供应商双边对账", "", "规则：确定性键、金额 Decimal；不换汇；不执行公式。", f"阈值: {report.get('run', {}).get('amount_tolerance', 'N/A')}",
             "限制：单文件 10 MiB、数据行 100000、列 200；平台未验证。", "", "## 输入与来源"]
    for item in report.get("run", {}).get("inputs", []):
        lines.append(f"- {item['side']}: {safe_md(item['file_name'])} / {safe_md(item['sheet'])} / SHA-256 {item['sha256']}")
    lines.extend(["", "## 状态摘要"])
    for status, count in report.get("summary", {}).get("by_status", {}).items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## 结果", "| 状态 | 键 | 供应商金额 | 内部金额 | 差额 | 来源 |", "|---|---|---|---|---|---|"])
    for r in report.get("results", []):
        sources = "; ".join(f"{safe_md(s['file_name'])}:{safe_md(s['sheet'])}:{s['row_number']}" for s in r["sources"])
        key_text = "; ".join(f"{k}={safe_md(v)}" for k, v in (r["key"] or {}).items())
        values = (r["status"], r["supplier"]["amount"] if r["supplier"] else None,
                  r["internal"]["amount"] if r["internal"] else None, r["difference"])
        lines.append("| " + " | ".join((safe_md(values[0]), key_text, *(safe_md(v) for v in values[1:]), sources)) + " |")
    lines.extend(["", "## 错误"] + [f"- {e['code']} ({e['side']}; {safe_md(e['source'])})" for e in report["errors"]])
    (output / "reconciliation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output / "reconciliation.json").write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args(argv)
    output = None
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        output = Path(config["output_dir"])
        if output.is_symlink() or (output.exists() and not output.is_dir()):
            raise Problem("INPUT_NOT_REGULAR_FILE")
        if output.resolve() in (Path(config[s + "_input"]["path"]).resolve() for s in ("supplier", "internal")):
            raise Problem("INPUT_NOT_REGULAR_FILE")
        for name in ("reconciliation.json", "reconciliation.xlsx", "reconciliation.md"):
            target = output / name
            if target.is_symlink() or target.resolve() in (Path(config[s + "_input"]["path"]).resolve() for s in ("supplier", "internal")):
                raise Problem("INPUT_NOT_REGULAR_FILE")
            if target.exists():
                raise Problem("OUTPUT_EXISTS")
        report = reconcile(config)
        write_report(report, output)
        return 0
    except (Problem, KeyError, ValueError, OSError, json.JSONDecodeError) as exc:
        code = exc.code if isinstance(exc, Problem) else "INPUT_NOT_FOUND"
        error = issue(code, exc.side if isinstance(exc, Problem) else None, exc.source if isinstance(exc, Problem) else None)
        payload = {"schema_version": "1.0", "product_id": PRODUCT, "task_id": TASK, "errors": [error], "security": {"network": False, "formulas_executed": False, "macros_executed": False}}
        if output is not None and not output.is_symlink() and (not output.exists() or output.is_dir()) and not (output / "reconciliation.json").exists():
            output.mkdir(parents=True, exist_ok=True)
            (output / "reconciliation.json").write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(error, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
