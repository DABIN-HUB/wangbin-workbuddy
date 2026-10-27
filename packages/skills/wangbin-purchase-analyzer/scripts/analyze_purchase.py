#!/usr/bin/env python3
"""Deterministic, local-only purchase analysis for UTF-8 CSV files."""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import stat
import sys
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable

VERSION = "0.1.0"
MAX_INPUT_BYTES = 1_048_576
ALLOWED_SUFFIXES = frozenset({".csv"})
REQUIRED_COLUMNS = (
    "order_id", "material", "supplier", "order_date", "quantity", "unit_price",
    "unit", "specification", "currency", "tax_treatment",
)
DECIMAL_TEXT = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
DATE_TEXT = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CURRENCY_TEXT = re.compile(r"^[A-Z]{3}$")
COMPARABLE_CHANGE_THRESHOLD = Decimal("20")


class InputError(ValueError):
    """A safe, stable error code suitable for CLI stderr."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _parse_date(value: str) -> date:
    if not isinstance(value, str) or not DATE_TEXT.fullmatch(value.strip()):
        raise ValueError("INVALID_DATE")
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError("INVALID_DATE") from exc


def _parse_decimal(value: str) -> Decimal:
    if not isinstance(value, str) or not value.strip() or not DECIMAL_TEXT.fullmatch(value.strip()):
        raise ValueError("INVALID_DECIMAL")
    try:
        result = Decimal(value.strip())
    except InvalidOperation as exc:
        raise ValueError("INVALID_DECIMAL") from exc
    if not result.is_finite():
        raise ValueError("INVALID_DECIMAL")
    return result


def _format_decimal(value: Decimal | None) -> str | None:
    if value is None:
        return None
    if value == 0:
        return "0"
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _formula_cell(value: Any) -> bool:
    if not isinstance(value, str):
        return True
    text = value.strip()
    if not text:
        return False
    if text[0] in "=+@":
        return True
    return text[0] == "-" and not DECIMAL_TEXT.fullmatch(text)


def _safe_source_name(path: Path) -> str:
    name = path.name
    return name if name else "input.csv"


def _read_csv(path_value: str | Path) -> tuple[Path, str, list[dict[str, str | None]], list[str]]:
    path = Path(path_value)
    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise InputError("INPUT_TYPE_UNSUPPORTED")
    try:
        absolute = path.absolute()
        if any(part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction())
               for part in (absolute, *absolute.parents)):
            raise InputError("INPUT_SYMLINK")
        metadata = path.stat()
    except FileNotFoundError as exc:
        raise InputError("INPUT_NOT_FOUND") from exc
    except OSError as exc:
        raise InputError("INPUT_READ_FAILED") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise InputError("INPUT_NOT_REGULAR")
    if metadata.st_size > MAX_INPUT_BYTES:
        raise InputError("INPUT_TOO_LARGE")
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
                raise InputError("INPUT_CHANGED")
            raw = stream.read(MAX_INPUT_BYTES + 1)
            finished = os.fstat(stream.fileno())
            if (opened.st_size, opened.st_mtime_ns) != (finished.st_size, finished.st_mtime_ns):
                raise InputError("INPUT_CHANGED")
    except OSError as exc:
        raise InputError("INPUT_READ_FAILED") from exc
    if len(raw) > MAX_INPUT_BYTES:
        raise InputError("INPUT_TOO_LARGE")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InputError("INVALID_UTF8") from exc
    if not text.strip():
        raise InputError("EMPTY_INPUT")
    try:
        reader = csv.DictReader(io.StringIO(text), strict=True)
        headers = reader.fieldnames or []
        if not headers or len(set(headers)) != len(headers):
            raise InputError("MISSING_COLUMNS")
        missing = [column for column in REQUIRED_COLUMNS if column not in headers]
        if missing:
            raise InputError("MISSING_COLUMNS")
        rows = list(reader)
    except csv.Error as exc:
        raise InputError("INVALID_CSV") from exc
    return path, text, rows, headers


def _row_error(row_number: int, code: str) -> dict[str, Any]:
    return {"row": row_number, "code": code}


def _parse_row(raw: dict[str | None, str | None], row_number: int, start: date, end: date) -> tuple[dict[str, Any] | None, dict[str, Any] | None, bool]:
    if None in raw:
        return None, _row_error(row_number, "INVALID_CSV_ROW"), False
    values: dict[str, str] = {}
    for field in REQUIRED_COLUMNS:
        value = raw.get(field)
        if value is None or not isinstance(value, str) or not value.strip():
            return None, _row_error(row_number, "MISSING_FIELD"), False
        values[field] = value.strip()
    if any(_formula_cell(values[field]) for field in REQUIRED_COLUMNS):
        return None, _row_error(row_number, "FORMULA_CELL_UNSAFE"), False
    try:
        order_date = _parse_date(values["order_date"])
    except ValueError as exc:
        return None, _row_error(row_number, str(exc)), False
    try:
        quantity = _parse_decimal(values["quantity"])
        unit_price = _parse_decimal(values["unit_price"])
    except ValueError as exc:
        return None, _row_error(row_number, str(exc)), False
    if quantity < 0 or unit_price < 0:
        return None, _row_error(row_number, "NEGATIVE_VALUE"), False
    if quantity == 0:
        return None, _row_error(row_number, "NON_POSITIVE_QUANTITY"), False
    currency = values["currency"].upper()
    if not CURRENCY_TEXT.fullmatch(currency):
        return None, _row_error(row_number, "INVALID_CURRENCY"), False
    if order_date < start or order_date > end:
        return None, None, True
    return {
        "order_id": values["order_id"],
        "material": values["material"],
        "supplier": values["supplier"],
        "order_date": order_date,
        "quantity": quantity,
        "unit_price": unit_price,
        "unit": values["unit"],
        "specification": values["specification"],
        "currency": currency,
        "tax_treatment": values["tax_treatment"],
        "row": row_number,
    }, None, False


def _group_key(item: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (item["material"], item["specification"], item["unit"], item["currency"], item["tax_treatment"])


def _group_object(key: tuple[str, str, str, str, str]) -> dict[str, str]:
    return {
        "material": key[0], "specification": key[1], "unit": key[2],
        "currency": key[3], "tax_treatment": key[4],
    }


def _quote(item: dict[str, Any]) -> dict[str, str]:
    return {
        "order_id": item["order_id"], "supplier": item["supplier"],
        "order_date": item["order_date"].isoformat(),
        "unit_price": _format_decimal(item["unit_price"]),
    }


def _pct(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == 0:
        return None
    return numerator / denominator * Decimal("100")


def _sum_totals(items: Iterable[dict[str, Any]]) -> dict[str, Decimal]:
    total = Decimal("0")
    quantity = Decimal("0")
    count = 0
    for item in items:
        total += item["quantity"] * item["unit_price"]
        quantity += item["quantity"]
        count += 1
    return {"total": total, "quantity": quantity, "order_count": count}


def _calculate(rows: list[dict[str, Any]], start: date, end: date, source_name: str, invalid: list[dict[str, Any]], duplicate_ids: list[str], out_of_range: int) -> dict[str, Any]:
    groups: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    by_currency: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in rows:
        groups[_group_key(item)].append(item)
        by_currency[item["currency"]].append(item)
    for values in groups.values():
        values.sort(key=lambda item: (item["order_date"], item["order_id"], item["row"]))

    totals = []
    concentration = []
    for currency in sorted(by_currency):
        aggregate = _sum_totals(by_currency[currency])
        total = aggregate["total"]
        totals.append({"currency": currency, "order_count": aggregate["order_count"], "quantity": _format_decimal(aggregate["quantity"]), "total": _format_decimal(total)})
        supplier_totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for item in by_currency[currency]:
            supplier_totals[item["supplier"]] += item["quantity"] * item["unit_price"]
        suppliers = [
            {"supplier": supplier, "total": _format_decimal(value), "share_pct": _format_decimal(_pct(value, total))}
            for supplier, value in sorted(supplier_totals.items(), key=lambda pair: (-pair[1], pair[0]))
        ]
        hhi = sum((_pct(value, total) or Decimal("0")) ** 2 for value in supplier_totals.values()) / Decimal("10000")
        concentration.append({
            "currency": currency,
            "total": _format_decimal(total),
            "top_supplier_share_pct": suppliers[0]["share_pct"] if suppliers else "0",
            "hhi": _format_decimal(hhi),
            "suppliers": suppliers,
        })

    comparable = []
    spreads = []
    anomalies = []
    for key in sorted(groups):
        items = groups[key]
        observations = [_quote(item) for item in items]
        changes = []
        items_by_supplier: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in items:
            items_by_supplier[item["supplier"]].append(item)
        for supplier in sorted(items_by_supplier):
            supplier_items = items_by_supplier[supplier]
            for previous, current in zip(supplier_items, supplier_items[1:]):
                absolute = current["unit_price"] - previous["unit_price"]
                percentage = _pct(absolute, previous["unit_price"])
                changes.append({
                    "supplier": supplier,
                    "comparison_scope": "SAME_SUPPLIER",
                    "from_order_id": previous["order_id"], "to_order_id": current["order_id"],
                    "from_date": previous["order_date"].isoformat(), "to_date": current["order_date"].isoformat(),
                    "from_price": _format_decimal(previous["unit_price"]), "to_price": _format_decimal(current["unit_price"]),
                    "change_absolute": _format_decimal(absolute), "change_pct": _format_decimal(percentage),
                })
                if percentage is not None and abs(percentage) >= COMPARABLE_CHANGE_THRESHOLD:
                    anomalies.append({
                        "type": "PRICE_CHANGE", **_group_object(key),
                        "supplier": supplier, "from_order_id": previous["order_id"], "to_order_id": current["order_id"],
                        "change_pct": _format_decimal(percentage), "threshold_pct": _format_decimal(COMPARABLE_CHANGE_THRESHOLD),
                        "evidence_status": "OBSERVATION_REQUIRES_REVIEW",
                        "explanation": "同一物料、规格、单位、币种及税务处理下同一供应商的相邻报价变动达到20%阈值；这是观察结果和建议调查线索，不是舞弊结论。",
                    })
        comparable.append({**_group_object(key), "observations": observations, "changes": changes})
        if len(items_by_supplier) >= 2:
            minimum = min(items, key=lambda item: (item["unit_price"], item["supplier"], item["order_id"]))
            maximum = max(items, key=lambda item: (item["unit_price"], item["supplier"], item["order_id"]))
            spread = maximum["unit_price"] - minimum["unit_price"]
            spread_pct = _pct(spread, minimum["unit_price"])
            spreads.append({
                **_group_object(key), "min_quote": _quote(minimum), "max_quote": _quote(maximum),
                "comparison_scope": "CROSS_SUPPLIER", "supplier_count": len(items_by_supplier),
                "comparison_period": {"start": start.isoformat(), "end": end.isoformat()},
                "spread": _format_decimal(spread), "spread_pct": _format_decimal(spread_pct),
            })
            if spread_pct is not None and spread_pct >= COMPARABLE_CHANGE_THRESHOLD:
                anomalies.append({
                    "type": "SUPPLIER_QUOTE_SPREAD", **_group_object(key),
                    "min_order_id": minimum["order_id"], "max_order_id": maximum["order_id"],
                    "spread_pct": _format_decimal(spread_pct), "threshold_pct": _format_decimal(COMPARABLE_CHANGE_THRESHOLD),
                    "comparison_scope": "CROSS_SUPPLIER", "supplier_count": len(items_by_supplier),
                    "comparison_period": {"start": start.isoformat(), "end": end.isoformat()},
                    "evidence_status": "OBSERVATION_REQUIRES_REVIEW",
                    "explanation": "同一物料、规格、单位、币种及税务处理、同一比较期间内不同供应商报价最高与最低价差达到20%阈值；这是观察结果和建议调查线索，不是已确认节约金额。",
                })

    incompatible = []
    by_material: dict[str, list[tuple[str, str, str, str, str]]] = defaultdict(list)
    for key in groups:
        by_material[key[0]].append(key)
    for material in sorted(by_material):
        keys = sorted(by_material[material])
        for left_index, left in enumerate(keys):
            for right in keys[left_index + 1:]:
                different = [field for field, before, after in zip(("specification", "unit", "currency", "tax_treatment"), left[1:], right[1:]) if before != after]
                if different:
                    incompatible.append({
                        "status": "NOT_COMPARABLE", "material": material, "different_fields": different,
                        "group_a": _group_object(left), "group_b": _group_object(right),
                        "reason": "仅在 material、specification、unit、currency、tax_treatment 完全一致时比较；本组差异不可作为异常。",
                    })

    span = (end - start).days + 1
    same_period = []
    half = span // 2
    if half:
        first_start, first_end = start, start + timedelta(days=half - 1)
        second_start, second_end = end - timedelta(days=half - 1), end
        currencies = sorted(set(by_currency))
        for currency in currencies:
            first_items = [item for item in rows if item["currency"] == currency and first_start <= item["order_date"] <= first_end]
            second_items = [item for item in rows if item["currency"] == currency and second_start <= item["order_date"] <= second_end]
            first = _sum_totals(first_items)
            second = _sum_totals(second_items)
            absolute = second["total"] - first["total"]
            same_period.append({
                "currency": currency,
                "first_period": {"start": first_start.isoformat(), "end": first_end.isoformat(), "total": _format_decimal(first["total"]), "order_count": first["order_count"]},
                "second_period": {"start": second_start.isoformat(), "end": second_end.isoformat(), "total": _format_decimal(second["total"]), "order_count": second["order_count"]},
                "change": {"absolute": _format_decimal(absolute), "pct": _format_decimal(_pct(absolute, first["total"]))},
                "method": "selected date range 的首尾等长半区间；奇数天的中间日期不纳入比较",
            })

    invalid.sort(key=lambda item: item["row"])
    anomalies.sort(key=lambda item: (item["type"], item["material"], item.get("specification", ""), item.get("from_order_id", item.get("min_order_id", ""))))
    return {
        "schema_version": VERSION,
        "input": {"source_name": source_name, "date_range": {"start": start.isoformat(), "end": end.isoformat()}},
        "summary": {"rows_read": len(rows) + len(invalid) + out_of_range, "valid_rows": len(rows), "invalid_rows": len(invalid), "out_of_range_rows": out_of_range, "duplicate_order_ids": duplicate_ids, "currencies": sorted(by_currency)},
        "purchasing_totals": totals,
        "supplier_concentration": concentration,
        "comparable_price_changes": comparable,
        "supplier_quote_spread": spreads,
        "same_period_trend": same_period,
        "anomaly_candidates": anomalies,
        "incompatible_group_differences": incompatible,
        "invalid_rows": invalid,
        "privacy": {"execution_scope": "local_script_only", "remote_upload": False, "absolute_path_disclosed": False,
                    "raw_rows_disclosed": False, "identifiers_in_output": True},
        "limitations": ["Excel/XLSX 未启用；请先导出为 UTF-8 CSV。", "同一供应商多次报价属于 SAME_SUPPLIER 价格波动；supplier_quote_spread 只有至少两个供应商且五项可比键一致时才输出，不满足条件时不产生跨供应商节约结论。", "异常仅是可解释的观察结果和建议调查线索，不代表舞弊、节约金额或最终结论。"],
    }


def analyze_csv(path: str | Path, start_date: str, end_date: str) -> dict[str, Any]:
    try:
        start = _parse_date(start_date)
        end = _parse_date(end_date)
    except ValueError as exc:
        raise InputError(str(exc)) from exc
    if start > end:
        raise InputError("INVALID_DATE_RANGE")
    source, _text, raw_rows, _headers = _read_csv(path)
    ids: dict[str, int] = {}
    for number, raw in enumerate(raw_rows, start=2):
        value = raw.get("order_id") if isinstance(raw, dict) else None
        if isinstance(value, str) and value.strip() and not _formula_cell(value):
            ids[value.strip()] = ids.get(value.strip(), 0) + 1
    duplicate_ids = sorted(order_id for order_id, count in ids.items() if count > 1)
    invalid: list[dict[str, Any]] = []
    valid: list[dict[str, Any]] = []
    out_of_range = 0
    for number, raw in enumerate(raw_rows, start=2):
        order_id = raw.get("order_id") if isinstance(raw, dict) else None
        if isinstance(order_id, str) and order_id.strip() in duplicate_ids:
            invalid.append(_row_error(number, "DUPLICATE_ORDER_ID"))
            continue
        item, error, was_out_of_range = _parse_row(raw, number, start, end)
        if error:
            invalid.append(error)
        elif was_out_of_range:
            out_of_range += 1
        elif item:
            valid.append(item)
    return _calculate(valid, start, end, _safe_source_name(source), invalid, duplicate_ids, out_of_range)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze purchase prices from a UTF-8 CSV file")
    parser.add_argument("--input", required=True, help="CSV input file")
    parser.add_argument("--start-date", required=True, help="inclusive ISO date YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="inclusive ISO date YYYY-MM-DD")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = analyze_csv(args.input, args.start_date, args.end_date)
    except InputError as exc:
        sys.stderr.write(f"{exc.code}\n")
        return 2
    except (OSError, csv.Error):
        sys.stderr.write("INPUT_READ_FAILED\n")
        return 2
    sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
