#!/usr/bin/env python3
"""Local, deterministic revenue analytics for fictional or authorized UTF-8 CSV data."""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable

MAX_INPUT_BYTES = 5 * 1024 * 1024
REQUIRED_COLUMNS = ("order_id", "customer", "product", "order_date", "amount", "currency")
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PERCENT_QUANTUM = Decimal("0.00000001")


class InputError(ValueError):
    """A safe, user-facing input error whose message contains no local path or raw cell."""


def _parse_date(value: str, *, code: str = "INVALID_DATE") -> date:
    if not isinstance(value, str) or not ISO_DATE_RE.fullmatch(value):
        raise InputError(code)
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise InputError(code) from exc


def _parse_period(start: str, end: str) -> tuple[date, date]:
    first = _parse_date(start)
    last = _parse_date(end)
    if first > last:
        raise InputError("INVALID_PERIOD")
    return first, last


def _decimal(value: str) -> Decimal:
    try:
        number = Decimal(value.strip())
    except (InvalidOperation, AttributeError) as exc:
        raise InputError("INVALID_DECIMAL") from exc
    if not number.is_finite():
        raise InputError("INVALID_DECIMAL")
    return number


def _number(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _percentage(value: Decimal) -> str:
    return _number(value.quantize(PERCENT_QUANTUM, rounding=ROUND_HALF_UP))


def _formula(value: object) -> bool:
    if not isinstance(value, str):
        return False
    stripped = value.lstrip()
    return stripped.startswith(("=", "+", "@")) or (stripped.startswith("-") and len(stripped) > 1 and not stripped[1].isdigit())


def _clean_periods(periods: Iterable[tuple[str, str]] | None) -> list[tuple[date, date]]:
    cleaned: set[tuple[date, date]] = set()
    for item in periods or ():
        if isinstance(item, dict):
            start, end = item.get("start"), item.get("end")
        else:
            try:
                start, end = item
            except (TypeError, ValueError) as exc:
                raise InputError("INVALID_COMPLETE_PERIOD") from exc
        first, last = _parse_period(str(start), str(end))
        cleaned.add((first, last))
    return sorted(cleaned)


def _month_end(year: int, month: int) -> date:
    if month == 12:
        return date(year + 1, 1, 1) - timedelta(days=1)
    return date(year, month + 1, 1) - timedelta(days=1)


def _previous_month(period: tuple[date, date]) -> tuple[date, date] | None:
    first, last = period
    if first.day != 1 or last != _month_end(first.year, first.month):
        return None
    previous_last = first - timedelta(days=1)
    return date(previous_last.year, previous_last.month, 1), previous_last


def _previous_year(period: tuple[date, date]) -> tuple[date, date] | None:
    first, last = period
    if first.day != 1 or last != _month_end(first.year, first.month):
        return None
    try:
        previous = first.replace(year=first.year - 1)
        previous_last = last.replace(year=last.year - 1)
    except ValueError:
        return None
    return previous, previous_last


def _complete(period: tuple[date, date] | None, *, as_of: date | None, declared: set[tuple[date, date]]) -> bool:
    return period is not None and as_of is not None and period[1] <= as_of and period in declared


def _revenue(rows: list[dict], start: date, end: date) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for row in rows:
        if start <= row["date"] <= end:
            totals[row["currency"]] += row["amount"]
    return dict(totals)


def _comparison(rows: list[dict], current: tuple[date, date], previous: tuple[date, date] | None, *, as_of: date | None, declared: set[tuple[date, date]]) -> object:
    if not _complete(current, as_of=as_of, declared=declared) or not _complete(previous, as_of=as_of, declared=declared):
        return "UNKNOWN"
    current_totals = _revenue(rows, *current)
    previous_totals = _revenue(rows, *previous)  # type: ignore[arg-type]
    currencies = sorted(set(current_totals) | set(previous_totals))
    values = []
    for currency in currencies:
        current_value = current_totals.get(currency, Decimal("0"))
        previous_value = previous_totals.get(currency, Decimal("0"))
        change = "UNKNOWN" if previous_value == 0 else _percentage((current_value - previous_value) / previous_value * 100)
        values.append({"currency": currency, "current": _number(current_value), "previous": _number(previous_value), "change_pct": change})
    if len(values) == 1:
        return values[0]
    return values


def _aggregate(rows: list[dict], key: str) -> list[dict]:
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for row in rows:
        group = (row["currency"], row[key])
        item = grouped.setdefault(group, {"currency": row["currency"], key: row[key], "order_count": 0, "revenue": Decimal("0")})
        item["order_count"] += 1  # type: ignore[operator]
        item["revenue"] += row["amount"]  # type: ignore[operator]
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for (currency, _), item in grouped.items():
        totals[currency] += item["revenue"]  # type: ignore[operator]
    output = []
    for item in grouped.values():
        currency = item["currency"]
        revenue = item["revenue"]
        output.append({**item, "revenue": _number(revenue), "share_pct": _percentage(revenue / totals[currency] * 100)})  # type: ignore[operator]
    return sorted(output, key=lambda item: (item["currency"], -Decimal(item["revenue"]), item[key]))


def _concentration(rows: list[dict]) -> list[dict]:
    contributions = _aggregate(rows, "customer")
    by_currency: dict[str, list[dict]] = defaultdict(list)
    for item in contributions:
        by_currency[item["currency"]].append(item)
    result = []
    for currency in sorted(by_currency):
        items = by_currency[currency]
        shares = [Decimal(item["share_pct"]) for item in items]
        result.append({
            "currency": currency,
            "customer_count": len(items),
            "top_1_share_pct": _number(max(shares)),
            "hhi_pct": _percentage(sum((share * share for share in shares), Decimal("0")) / 100),
        })
    return result


def _read_rows(path: Path) -> tuple[list[dict], list[dict], dict]:
    if not path.exists() or not path.is_file():
        raise InputError("INPUT_NOT_FOUND")
    if path.suffix.lower() != ".csv":
        raise InputError("UNSUPPORTED_FORMAT")
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise InputError("INPUT_UNREADABLE") from exc
    if size > MAX_INPUT_BYTES:
        raise InputError("INPUT_TOO_LARGE")
    try:
        stream = path.open("r", encoding="utf-8-sig", newline="")
    except (OSError, UnicodeError) as exc:
        raise InputError("INPUT_UNREADABLE") from exc
    try:
        with stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames is None:
                raise InputError("EMPTY_INPUT")
            missing = [field for field in REQUIRED_COLUMNS if field not in reader.fieldnames]
            if missing:
                raise InputError("MISSING_COLUMNS")
            raw_rows = list(reader)
    except InputError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        raise InputError("INPUT_UNREADABLE") from exc
    if not raw_rows:
        raise InputError("EMPTY_INPUT")

    candidates: list[dict] = []
    invalid: list[dict] = []
    input_rows = len(raw_rows)
    for line, raw in enumerate(raw_rows, start=2):
        fields = {field: (raw.get(field) or "").strip() for field in REQUIRED_COLUMNS}
        formula_field = next((field for field, value in fields.items() if _formula(value)), None)
        if formula_field:
            invalid.append({"line": line, "code": "FORMULA_CELL_UNSAFE", "field": formula_field})
            continue
        missing_field = next((field for field, value in fields.items() if not value), None)
        if missing_field:
            invalid.append({"line": line, "code": "MISSING_FIELD", "field": missing_field})
            continue
        try:
            parsed_date = _parse_date(fields["order_date"])
        except InputError:
            invalid.append({"line": line, "code": "INVALID_DATE", "field": "order_date"})
            continue
        try:
            amount = _decimal(fields["amount"])
        except InputError:
            invalid.append({"line": line, "code": "INVALID_DECIMAL", "field": "amount"})
            continue
        if amount < 0:
            invalid.append({"line": line, "code": "NEGATIVE_AMOUNT", "field": "amount"})
            continue
        if not CURRENCY_RE.fullmatch(fields["currency"]):
            invalid.append({"line": line, "code": "INVALID_CURRENCY", "field": "currency"})
            continue
        candidates.append({"line": line, "order_id": fields["order_id"], "customer": fields["customer"], "product": fields["product"], "date": parsed_date, "amount": amount, "currency": fields["currency"]})

    counts = Counter(row["order_id"] for row in candidates)
    duplicate_ids = sorted(order_id for order_id, count in counts.items() if count > 1)
    valid = []
    for row in candidates:
        if row["order_id"] in duplicate_ids:
            invalid.append({"line": row["line"], "code": "DUPLICATE_ORDER_ID", "field": "order_id"})
        else:
            valid.append(row)
    invalid.sort(key=lambda item: (item["line"], item["code"]))
    return valid, invalid, {"input_rows": input_rows, "duplicate_order_ids": duplicate_ids}


def analyze_csv(path: str | Path, start_date: str, end_date: str, *, as_of_date: str | None = None, complete_periods: Iterable[tuple[str, str]] | None = None) -> dict:
    """Analyze local UTF-8 CSV order revenue without timezone conversion or profit inference."""
    start, end = _parse_period(start_date, end_date)
    as_of = _parse_date(as_of_date, code="INVALID_AS_OF_DATE") if as_of_date is not None else None
    declared_periods = _clean_periods(complete_periods)
    valid, invalid, input_meta = _read_rows(Path(path))
    selected = [row for row in valid if start <= row["date"] <= end]
    out_of_range = len(valid) - len(selected)
    trend_groups: dict[tuple[str, str], dict[str, object]] = {}
    for row in selected:
        key = (row["currency"], row["date"].strftime("%Y-%m"))
        item = trend_groups.setdefault(key, {"currency": row["currency"], "period": key[1], "order_count": 0, "revenue": Decimal("0")})
        item["order_count"] += 1  # type: ignore[operator]
        item["revenue"] += row["amount"]  # type: ignore[operator]
    trend = [{**item, "revenue": _number(item["revenue"])} for item in trend_groups.values()]
    trend.sort(key=lambda item: (item["currency"], item["period"]))
    totals = _aggregate(selected, "product")
    sales_totals: dict[str, dict[str, object]] = {}
    for row in selected:
        item = sales_totals.setdefault(row["currency"], {"currency": row["currency"], "order_count": 0, "revenue": Decimal("0")})
        item["order_count"] += 1  # type: ignore[operator]
        item["revenue"] += row["amount"]  # type: ignore[operator]
    sales_total_list = [{**item, "revenue": _number(item["revenue"])} for item in sales_totals.values()]
    sales_total_list.sort(key=lambda item: item["currency"])

    anomalies = []
    by_currency: dict[str, list[dict]] = defaultdict(list)
    for row in selected:
        by_currency[row["currency"]].append(row)
    for currency, currency_rows in sorted(by_currency.items()):
        average = sum((row["amount"] for row in currency_rows), Decimal("0")) / len(currency_rows)
        for row in sorted(currency_rows, key=lambda item: item["line"]):
            if average > 0 and row["amount"] >= average * 3 and len(currency_rows) >= 3:
                anomalies.append({"type": "LARGE_ORDER", "currency": currency, "order_id": row["order_id"], "amount": _number(row["amount"]), "threshold": "3x_selected_average"})

    period = (start, end)
    mom_period = _previous_month(period)
    yoy_period = _previous_year(period)
    comparisons = {"mom": _comparison(valid, period, mom_period, as_of=as_of, declared=set(declared_periods)), "yoy": _comparison(valid, period, yoy_period, as_of=as_of, declared=set(declared_periods))}
    risks = []
    if invalid:
        risks.append({"type": "DATA_QUALITY", "severity": "HIGH", "description": "存在无效订单行，已排除出收入汇总"})
    if input_meta["duplicate_order_ids"]:
        risks.append({"type": "DUPLICATE_ORDER_ID", "severity": "HIGH", "description": "重复订单号已排除，需核对源数据"})
    if out_of_range:
        risks.append({"type": "OUT_OF_RANGE_ROWS", "severity": "MEDIUM", "description": "存在分析期间之外的有效订单，未计入本期汇总"})
    if comparisons["mom"] == "UNKNOWN" or comparisons["yoy"] == "UNKNOWN":
        risks.append({"type": "PERIOD_COMPLETENESS", "severity": "MEDIUM", "description": "MoM/YoY 仅在 as-of 与可比期间均被明确标记完整时计算"})
    if any(item["top_1_share_pct"] == "100" or Decimal(item["top_1_share_pct"]) >= 80 for item in _concentration(selected)):
        risks.append({"type": "CUSTOMER_CONCENTRATION", "severity": "MEDIUM", "description": "至少一个币种的单一客户贡献达到或超过80%"})
    risks.append({"type": "PROFIT_NOT_INFERRED", "severity": "INFO", "description": "未提供成本数据；收入不等于利润，未推断利润或毛利率"})

    return {
        "schema_version": "0.1.0",
        "input_format": "UTF-8 CSV",
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "as_of_date": as_of.isoformat() if as_of else "UNKNOWN",
        "declared_complete_periods": [{"start": first.isoformat(), "end": last.isoformat()} for first, last in declared_periods],
        "summary": {"input_rows": input_meta["input_rows"], "valid_rows": len(valid), "invalid_rows": len(invalid), "out_of_range_rows": out_of_range, "duplicate_order_ids": input_meta["duplicate_order_ids"]},
        "sales_totals": sales_total_list,
        "sales_trend": trend,
        "product_ranking": totals,
        "customer_contribution": _aggregate(selected, "customer"),
        "customer_concentration": _concentration(selected),
        "period_comparisons": comparisons,
        "anomalies": anomalies,
        "invalid_rows": invalid,
        "operational_risks": risks,
        "profit_analysis": {"status": "UNKNOWN", "reason": "成本数据未提供；收入不等于利润，未进行利润或毛利率推断"},
        "limitations": ["仅支持本地 UTF-8 CSV；XLSX/PDF 当前不支持", "日期按 ISO 8601 date-only 解析，不做时区转换", "币种分开汇总，不进行汇率换算", "MoM/YoY 不从数据行数量推断完整性", "输出不包含原始单元格内容、原始日志或绝对路径"],
        "privacy": {"execution_scope": "local_script_only", "remote_upload": False, "absolute_path_disclosed": False, "raw_input_disclosed": False},
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze revenue from a local UTF-8 CSV")
    parser.add_argument("--input", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--as-of-date")
    parser.add_argument("--complete-period", action="append", default=[], metavar="START:END")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        complete_periods = []
        for value in args.complete_period:
            start, separator, end = value.partition(":")
            if not separator:
                raise InputError("INVALID_COMPLETE_PERIOD")
            complete_periods.append((start, end))
        result = analyze_csv(args.input, args.start_date, args.end_date, as_of_date=args.as_of_date, complete_periods=complete_periods)
    except InputError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
