#!/usr/bin/env python3
"""Deterministic, local-only inventory analysis for UTF-8 CSV files."""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any, Iterable

VERSION = "0.1.0"
MAX_INPUT_BYTES = 1 * 1024 * 1024
ALLOWED_SUFFIXES = frozenset({".csv"})
DATE_TEXT = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DECIMAL_TEXT = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")
CURRENCY_TEXT = re.compile(r"^[A-Z]{3}$")
BALANCE_COLUMNS = ("item_id", "warehouse", "balance_date", "quantity", "unit_cost", "currency")
RECEIPT_COLUMNS = ("receipt_id", "item_id", "warehouse", "receipt_date", "quantity", "unit_cost", "currency")
ISSUE_COLUMNS = ("issue_id", "item_id", "warehouse", "issue_date", "quantity", "currency")
MASTER_COLUMNS = ("item_id",)
SLOW_TURNOVER_MAX = Decimal("1")
OVERSTOCK_DAYS = Decimal("90")


class InputError(ValueError):
    """A stable, non-sensitive error code suitable for CLI stderr."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _parse_date(value: Any) -> date:
    if not isinstance(value, str) or not DATE_TEXT.fullmatch(value.strip()):
        raise ValueError("INVALID_DATE")
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError("INVALID_DATE") from exc


def _parse_decimal(value: Any) -> Decimal:
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


def _format_ratio(value: Decimal | None) -> str | None:
    if value is None:
        return None
    with localcontext() as context:
        context.prec = 50
        return _format_decimal(value.quantize(Decimal("0.00000001")))


def _formula_cell(value: Any) -> bool:
    if not isinstance(value, str):
        return True
    text = value.strip()
    if not text:
        return False
    if text[0] in "=+@":
        return True
    return text.startswith("-") and not DECIMAL_TEXT.fullmatch(text)


def _safe_source_name(path: Path) -> str:
    return path.name or "input.csv"


def _read_csv(path_value: str | Path, required: tuple[str, ...], kind: str) -> tuple[str, list[dict[str | None, str | None]], list[str]]:
    path = Path(path_value)
    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise InputError("INPUT_TYPE_UNSUPPORTED")
    try:
        if path.is_symlink():
            raise InputError("INPUT_SYMLINK")
        metadata = path.stat()
    except FileNotFoundError as exc:
        raise InputError("INPUT_NOT_FOUND") from exc
    except OSError as exc:
        raise InputError("INPUT_READ_FAILED") from exc
    if not path.is_file():
        raise InputError("INPUT_NOT_REGULAR")
    if metadata.st_size > MAX_INPUT_BYTES:
        raise InputError("INPUT_TOO_LARGE")
    try:
        raw = path.read_bytes()
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
        headers = [header.strip() if isinstance(header, str) else "" for header in (reader.fieldnames or [])]
        if not headers or any(not header for header in headers):
            raise InputError("MISSING_COLUMNS")
        if len(headers) != len(set(headers)):
            raise InputError("DUPLICATE_COLUMNS")
        missing = [column for column in required if column not in headers]
        if missing:
            raise InputError("MISSING_COLUMNS")
        rows = list(reader)
    except csv.Error as exc:
        raise InputError("INVALID_CSV") from exc
    return _safe_source_name(path), rows, headers


def _row_error(kind: str, row_number: int, code: str) -> dict[str, Any]:
    return {"dataset": kind, "row": row_number, "code": code}


def _clean_required(raw: dict[str | None, str | None], columns: Iterable[str]) -> tuple[dict[str, str] | None, str | None]:
    if None in raw:
        return None, "INVALID_CSV_ROW"
    values: dict[str, str] = {}
    for field in columns:
        value = raw.get(field)
        if value is None or not isinstance(value, str) or not value.strip():
            return None, "MISSING_FIELD"
        values[field] = value.strip()
    if any(_formula_cell(value) for value in values.values()):
        return None, "FORMULA_CELL_UNSAFE"
    return values, None


def _currency(value: str) -> str:
    result = value.upper()
    if not CURRENCY_TEXT.fullmatch(result):
        raise ValueError("INVALID_CURRENCY")
    return result


def _parse_balance(raw: dict[str | None, str | None], row_number: int, as_of: date) -> tuple[dict[str, Any] | None, dict[str, Any] | None, bool]:
    values, error = _clean_required(raw, BALANCE_COLUMNS)
    if error:
        return None, _row_error("balances", row_number, error), False
    assert values is not None
    try:
        parsed = {"item_id": values["item_id"], "warehouse": values["warehouse"], "balance_date": _parse_date(values["balance_date"]), "quantity": _parse_decimal(values["quantity"]), "unit_cost": _parse_decimal(values["unit_cost"]), "currency": _currency(values["currency"]), "row": row_number}
    except ValueError as exc:
        return None, _row_error("balances", row_number, str(exc)), False
    if parsed["quantity"] < 0 or parsed["unit_cost"] < 0:
        return None, _row_error("balances", row_number, "NEGATIVE_VALUE"), False
    if parsed["balance_date"] > as_of:
        return None, None, True
    return parsed, None, False


def _parse_receipt(raw: dict[str | None, str | None], row_number: int, as_of: date) -> tuple[dict[str, Any] | None, dict[str, Any] | None, bool]:
    values, error = _clean_required(raw, RECEIPT_COLUMNS)
    if error:
        return None, _row_error("receipts", row_number, error), False
    assert values is not None
    try:
        parsed = {"receipt_id": values["receipt_id"], "item_id": values["item_id"], "warehouse": values["warehouse"], "receipt_date": _parse_date(values["receipt_date"]), "quantity": _parse_decimal(values["quantity"]), "unit_cost": _parse_decimal(values["unit_cost"]), "currency": _currency(values["currency"]), "row": row_number}
    except ValueError as exc:
        return None, _row_error("receipts", row_number, str(exc)), False
    if parsed["quantity"] <= 0 or parsed["unit_cost"] < 0:
        return None, _row_error("receipts", row_number, "NEGATIVE_VALUE" if parsed["quantity"] < 0 or parsed["unit_cost"] < 0 else "NON_POSITIVE_QUANTITY"), False
    if parsed["receipt_date"] > as_of:
        return None, None, True
    return parsed, None, False


def _parse_issue(raw: dict[str | None, str | None], row_number: int, as_of: date) -> tuple[dict[str, Any] | None, dict[str, Any] | None, bool]:
    values, error = _clean_required(raw, ISSUE_COLUMNS)
    if error:
        return None, _row_error("issues", row_number, error), False
    assert values is not None
    try:
        parsed = {"issue_id": values["issue_id"], "item_id": values["item_id"], "warehouse": values["warehouse"], "issue_date": _parse_date(values["issue_date"]), "quantity": _parse_decimal(values["quantity"]), "currency": _currency(values["currency"]), "row": row_number}
    except ValueError as exc:
        return None, _row_error("issues", row_number, str(exc)), False
    if parsed["quantity"] <= 0:
        return None, _row_error("issues", row_number, "NEGATIVE_VALUE" if parsed["quantity"] < 0 else "NON_POSITIVE_QUANTITY"), False
    if parsed["issue_date"] > as_of:
        return None, None, True
    return parsed, None, False


def _parse_master(path_value: str | Path, invalid: list[dict[str, Any]], as_of: date) -> tuple[dict[str, dict[str, Any]], int]:
    _source, raw_rows, headers = _read_csv(path_value, MASTER_COLUMNS, "master")
    masters: dict[str, dict[str, Any]] = {}
    for row_number, raw in enumerate(raw_rows, start=2):
        values, error = _clean_required(raw, MASTER_COLUMNS)
        if error:
            invalid.append(_row_error("master", row_number, error))
            continue
        assert values is not None
        item_id = values["item_id"]
        record: dict[str, Any] = {"item_id": item_id}
        for field in ("item_name", "unit"):
            value = raw.get(field)
            if value is not None and isinstance(value, str) and value.strip():
                if _formula_cell(value):
                    invalid.append(_row_error("master", row_number, "FORMULA_CELL_UNSAFE"))
                    record = {}
                    break
                record[field] = value.strip()
        if not record:
            continue
        for field in ("reorder_point", "max_stock"):
            value = raw.get(field)
            if value is None or not str(value).strip():
                continue
            if _formula_cell(value):
                invalid.append(_row_error("master", row_number, "FORMULA_CELL_UNSAFE"))
                record = {}
                break
            try:
                parsed = _parse_decimal(str(value))
            except ValueError:
                invalid.append(_row_error("master", row_number, "INVALID_DECIMAL"))
                record = {}
                break
            if parsed < 0:
                invalid.append(_row_error("master", row_number, "NEGATIVE_VALUE"))
                record = {}
                break
            record[field] = parsed
        if record:
            if item_id in masters:
                invalid.append(_row_error("master", row_number, "DUPLICATE_ID"))
            else:
                masters[item_id] = record
    return masters, len(raw_rows)


def _duplicate_keys(raw_rows: list[dict[str | None, str | None]], kind: str) -> tuple[set[Any], list[str]]:
    counts: dict[Any, int] = defaultdict(int)
    for raw in raw_rows:
        if kind == "balances":
            key = (str(raw.get("item_id") or "").strip(), str(raw.get("warehouse") or "").strip(), str(raw.get("balance_date") or "").strip())
            label = key[0]
        else:
            field = "receipt_id" if kind == "receipts" else "issue_id"
            key = str(raw.get(field) or "").strip()
            label = key
        if key and (key if kind == "balances" else label):
            counts[key] += 1
    duplicate_keys = {key for key, count in counts.items() if count > 1}
    labels = sorted({key[0] if kind == "balances" else key for key in duplicate_keys})
    return duplicate_keys, labels


def _pct(numerator: Decimal, denominator: Decimal) -> Decimal | None:
    if denominator == 0:
        return None
    return numerator / denominator * Decimal("100")


def _key(item: dict[str, Any]) -> tuple[str, str, str]:
    return item["item_id"], item["warehouse"], item["currency"]


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    result = Decimal("0")
    for value in values:
        result += value
    return result


def _calculate(balances: list[dict[str, Any]], receipts: list[dict[str, Any]], issues: list[dict[str, Any]], masters: dict[str, dict[str, Any]], as_of: date, source_names: dict[str, str], invalid: list[dict[str, Any]], counts: dict[str, int], out_of_range: int, duplicate_ids: list[str]) -> dict[str, Any]:
    balance_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in balances:
        balance_groups[_key(item)].append(item)
    for group in balance_groups.values():
        group.sort(key=lambda item: (item["balance_date"], item["row"]))

    inventory: list[dict[str, Any]] = []
    no_movement: list[dict[str, Any]] = []
    slow_moving: list[dict[str, Any]] = []
    overstock: list[dict[str, Any]] = []
    anomalies: list[dict[str, Any]] = []
    value_by_currency: dict[str, dict[str, Decimal]] = defaultdict(lambda: {"value": Decimal("0"), "quantity": Decimal("0")})

    for key in sorted(balance_groups):
        item_id, warehouse, currency = key
        snapshots = balance_groups[key]
        ending = snapshots[-1]
        prior = [snapshot for snapshot in snapshots if snapshot["balance_date"] < ending["balance_date"]]
        beginning = prior[-1] if prior else None
        start_date = beginning["balance_date"] if beginning else ending["balance_date"]
        item_receipts = [item for item in receipts if (item["item_id"], item["warehouse"], item["currency"]) == key and start_date < item["receipt_date"] <= as_of]
        item_issues = [item for item in issues if (item["item_id"], item["warehouse"], item["currency"]) == key and start_date < item["issue_date"] <= as_of]
        quantity = ending["quantity"]
        value = quantity * ending["unit_cost"]
        master = masters.get(item_id, {})
        average = (beginning["quantity"] + quantity) / Decimal("2") if beginning else None
        turnover = _pct(_sum_decimal(item["quantity"] for item in item_issues), average) / Decimal("100") if average else None
        # Quantity turnover is outbound quantity divided by average quantity, not a percentage.
        turnover_text = _format_ratio(turnover)
        movement_count = len(item_receipts) + len(item_issues)
        record: dict[str, Any] = {
            "item_id": item_id,
            "warehouse": warehouse,
            "currency": currency,
            "item_name": master.get("item_name"),
            "unit": master.get("unit"),
            "balance_date": ending["balance_date"].isoformat(),
            "quantity": _format_decimal(quantity),
            "unit_cost": _format_decimal(ending["unit_cost"]),
            "value": _format_decimal(value),
            "beginning_quantity": _format_decimal(beginning["quantity"]) if beginning else None,
            "beginning_date": beginning["balance_date"].isoformat() if beginning else None,
            "receipt_quantity": _format_decimal(_sum_decimal(item["quantity"] for item in item_receipts)),
            "issue_quantity": _format_decimal(_sum_decimal(item["quantity"] for item in item_issues)),
            "movement_count": movement_count,
            "quantity_turnover": turnover_text if beginning and item_issues else "UNKNOWN",
            "turnover_status": "KNOWN" if beginning and item_issues else "UNKNOWN",
        }
        inventory.append(record)
        value_by_currency[currency]["value"] += value
        value_by_currency[currency]["quantity"] += quantity

        if movement_count == 0:
            no_movement.append({"item_id": item_id, "warehouse": warehouse, "currency": currency, "as_of": as_of.isoformat(), "reason": "在可观察区间内没有有效收货或发料记录；候选需业务核实。"})
        if turnover is not None and turnover <= SLOW_TURNOVER_MAX:
            slow_moving.append({"item_id": item_id, "warehouse": warehouse, "currency": currency, "quantity_turnover": _format_ratio(turnover), "threshold": _format_decimal(SLOW_TURNOVER_MAX), "reason": "数量周转率不高于 1；仅为慢动候选。"})
        max_stock = master.get("max_stock")
        if max_stock is not None and quantity > max_stock:
            overstock.append({"item_id": item_id, "warehouse": warehouse, "currency": currency, "quantity": _format_decimal(quantity), "max_stock": _format_decimal(max_stock), "reason": "期末数量超过主数据 max_stock；仅为超储候选。"})
        elif turnover is not None and item_issues and _sum_decimal(item["quantity"] for item in item_issues) > 0:
            days_supply = quantity / _sum_decimal(item["quantity"] for item in item_issues) * Decimal("30")
            if days_supply > OVERSTOCK_DAYS:
                overstock.append({"item_id": item_id, "warehouse": warehouse, "currency": currency, "quantity": _format_decimal(quantity), "days_supply": _format_decimal(days_supply), "reason": "按观察期发料量折算的库存覆盖天数超过 90 天；仅为超储候选。"})

        if beginning and beginning["balance_date"] < as_of and ending["balance_date"] <= as_of:
            expected = beginning["quantity"] + _sum_decimal(item["quantity"] for item in item_receipts) - _sum_decimal(item["quantity"] for item in item_issues)
            if expected != quantity:
                anomalies.append({"type": "BALANCE_MISMATCH", "item_id": item_id, "warehouse": warehouse, "currency": currency, "beginning_quantity": _format_decimal(beginning["quantity"]), "receipts": _format_decimal(_sum_decimal(item["quantity"] for item in item_receipts)), "issues": _format_decimal(_sum_decimal(item["quantity"] for item in item_issues)), "ending_quantity": _format_decimal(quantity), "expected_ending_quantity": _format_decimal(expected), "reason": "期初数量 + 收货 - 发料与期末快照不一致；需核对盘点、损耗和未入账移动。"})

    for rows in (inventory, no_movement, slow_moving, overstock, anomalies):
        rows.sort(key=lambda row: (row["item_id"], row["warehouse"], row["currency"], row.get("type", "")))
    invalid.sort(key=lambda row: (row["dataset"], row["row"], row["code"]))
    return {
        "schema_version": VERSION,
        "input": {"source_names": {key: source_names[key] for key in sorted(source_names)}, "as_of": as_of.isoformat()},
        "summary": {**counts, "invalid_rows": len(invalid), "out_of_range_rows": out_of_range, "duplicate_ids": sorted(duplicate_ids)},
        "inventory": inventory,
        "inventory_value": [{"currency": currency, "value": _format_decimal(values["value"]), "quantity": _format_decimal(values["quantity"])} for currency, values in sorted(value_by_currency.items())],
        "no_movement_candidates": no_movement,
        "slow_moving_candidates": slow_moving,
        "overstock_candidates": overstock,
        "anomaly_candidates": anomalies,
        "invalid_rows": invalid,
        "assumptions": [
            "balances 是授权库存快照；每个 item_id + warehouse + currency 取 as-of 前最近快照作为期末库存和估值。",
            "数量周转率 = 观察区间发料数量 / ((期初快照数量 + 期末快照数量) / 2)；必须同时有不同日期的期初、期末快照和有效发料记录，否则为 UNKNOWN。",
            "收货和发料按日期纳入期初快照之后至 as-of 的区间；快照不等同于完整盘点证据。",
            "无移动、慢动和超储均是候选；主数据 max_stock 优先，缺少主数据时不臆测安全库存。",
        ],
        "anomaly_rules": [
            "BALANCE_MISMATCH：期初 + 收货 - 发料不等于期末快照。",
            "DUPLICATE_ID、INVALID_DATE、INVALID_DECIMAL、NEGATIVE_VALUE、FORMULA_CELL_UNSAFE 等输入异常只排除对应行，不回显原始单元格。",
        ],
        "privacy": {"execution_scope": "local_script_only", "remote_upload": False, "absolute_path_disclosed": False, "raw_input_disclosed": False},
        "limitations": ["仅接受 UTF-8 CSV；Excel/XLSX、PDF 和隐式文件发现不在 0.1.0 范围内。", "币种分别汇总，不进行汇率换算；异常和候选不是审计结论。"],
    }


def analyze_csv(balances_path: str | Path, receipts_path: str | Path, issues_path: str | Path, as_of_date: str | None = None, master_path: str | Path | None = None, *, as_of: str | None = None) -> dict[str, Any]:
    selected_as_of = as_of_date if as_of_date is not None else as_of
    if selected_as_of is None:
        raise InputError("AS_OF_REQUIRED")
    try:
        as_of_value = _parse_date(selected_as_of)
    except ValueError as exc:
        raise InputError(str(exc)) from exc
    source_names: dict[str, str] = {}
    raw_sources: dict[str, tuple[list[dict[str | None, str | None]], tuple[str, ...]]] = {}
    for kind, path, required in (("balances", balances_path, BALANCE_COLUMNS), ("receipts", receipts_path, RECEIPT_COLUMNS), ("issues", issues_path, ISSUE_COLUMNS)):
        source, rows, headers = _read_csv(path, required, kind)
        source_names[kind] = source
        raw_sources[kind] = (rows, tuple(headers))
    invalid: list[dict[str, Any]] = []
    duplicate_ids: list[str] = []
    duplicate_keys: dict[str, set[Any]] = {}
    for kind in ("balances", "receipts", "issues"):
        keys, labels = _duplicate_keys(raw_sources[kind][0], kind)
        duplicate_keys[kind] = keys
        duplicate_ids.extend(labels)
    masters: dict[str, dict[str, Any]] = {}
    master_count = 0
    if master_path is not None:
        source, _rows, _headers = _read_csv(master_path, MASTER_COLUMNS, "master")
        source_names["master"] = source
        # Parse once through the same bounded reader while preserving its raw rows.
        masters, master_count = _parse_master(master_path, invalid, as_of_value)
    parsed: dict[str, list[dict[str, Any]]] = {"balances": [], "receipts": [], "issues": []}
    out_of_range = 0
    parsers = {"balances": _parse_balance, "receipts": _parse_receipt, "issues": _parse_issue}
    for kind in ("balances", "receipts", "issues"):
        for row_number, raw in enumerate(raw_sources[kind][0], start=2):
            if (kind == "balances" and (str(raw.get("item_id") or "").strip(), str(raw.get("warehouse") or "").strip(), str(raw.get("balance_date") or "").strip()) in duplicate_keys[kind]) or (kind == "receipts" and str(raw.get("receipt_id") or "").strip() in duplicate_keys[kind]) or (kind == "issues" and str(raw.get("issue_id") or "").strip() in duplicate_keys[kind]):
                invalid.append(_row_error(kind, row_number, "DUPLICATE_ID"))
                continue
            item, error, was_out_of_range = parsers[kind](raw, row_number, as_of_value)
            if error:
                invalid.append(error)
            elif was_out_of_range:
                out_of_range += 1
            elif item:
                parsed[kind].append(item)
    counts = {"balances_read": len(raw_sources["balances"][0]), "receipts_read": len(raw_sources["receipts"][0]), "issues_read": len(raw_sources["issues"][0]), "valid_balances": len(parsed["balances"]), "valid_receipts": len(parsed["receipts"]), "valid_issues": len(parsed["issues"])}
    if master_path is not None:
        counts["master_read"] = master_count
    return _calculate(parsed["balances"], parsed["receipts"], parsed["issues"], masters, as_of_value, source_names, invalid, counts, out_of_range, sorted(set(duplicate_ids)))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze inventory from bounded UTF-8 CSV files")
    parser.add_argument("--balances", required=True, help="inventory balance snapshots CSV")
    parser.add_argument("--receipts", required=True, help="receipt transactions CSV")
    parser.add_argument("--issues", required=True, help="issue transactions CSV")
    parser.add_argument("--master", help="optional item master CSV")
    parser.add_argument("--as-of", required=True, help="inclusive ISO date YYYY-MM-DD")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = analyze_csv(args.balances, args.receipts, args.issues, args.as_of, args.master)
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
