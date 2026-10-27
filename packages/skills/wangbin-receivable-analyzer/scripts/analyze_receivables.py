#!/usr/bin/env python3
"""Local, bounded receivables analysis; no platform runtime is implied."""
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
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

MAX_BYTES = 1_048_576
FIELDS = ("invoice_id", "customer_id", "due_date", "open_balance", "currency")
BUCKETS = ("1-30", "31-60", "61-90", "91+")
MONEY = Decimal("0.01")


class InputError(ValueError):
    pass


def _date(value: str) -> date:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("date format")
    return date.fromisoformat(value)


def _input(path: Path) -> str:
    if path.suffix.lower() != ".csv":
        raise InputError("UNSUPPORTED_FORMAT")
    absolute = path.absolute()
    if any(part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction())
           for part in (absolute, *absolute.parents)):
        raise InputError("SYMLINK_INPUT")
    try:
        info = path.stat()
        if not stat.S_ISREG(info.st_mode):
            raise InputError("NOT_A_FILE")
        if not 0 < info.st_size <= MAX_BYTES:
            raise InputError("EMPTY_OR_TOO_LARGE")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                raise InputError("INPUT_CHANGED")
            data = stream.read(MAX_BYTES + 1)
            final = os.fstat(stream.fileno())
            if len(data) > MAX_BYTES or (final.st_size, final.st_mtime_ns) != (opened.st_size, opened.st_mtime_ns):
                raise InputError("INPUT_CHANGED_OR_TOO_LARGE")
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InputError("INVALID_UTF8") from exc
    except OSError as exc:
        raise InputError("INPUT_UNAVAILABLE") from exc


def _money(value: str) -> Decimal:
    number = Decimal(value)
    if not number.is_finite() or number < 0 or number != number.quantize(MONEY):
        raise ValueError("invalid nonnegative two-decimal amount")
    return number


def _bucket(days: int) -> str:
    if days <= 30:
        return "1-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    return "91+"


def analyze(text: str, as_of: date) -> dict:
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
        header = reader.fieldnames
        if not header or len(header) != len(set(header)) or any(field not in header for field in FIELDS):
            raise InputError("MISSING_OR_DUPLICATE_HEADER")
        totals: dict[str, dict[str, Decimal]] = defaultdict(lambda: {"open": Decimal(0), "overdue": Decimal(0)})
        aging: dict[str, dict[str, dict[str, object]]] = defaultdict(
            lambda: {name: {"amount": Decimal(0), "count": 0} for name in BUCKETS})
        customers: dict[str, dict[str, dict[str, object]]] = defaultdict(
            lambda: defaultdict(lambda: {"overdue": Decimal(0), "invoices": 0, "max_days_overdue": 0}))
        issues: list[dict] = []
        seen: set[str] = set()
        valid = rows = 0
        for row in reader:
            line = reader.line_num
            rows += 1
            if rows > 20_000:
                raise InputError("ROW_LIMIT")
            if None in row or any(isinstance(value, str) and value.lstrip().startswith(("=", "+", "@")) for value in row.values()):
                issues.append({"row": line, "code": "INVALID_COLUMNS_OR_FORMULA"})
                continue
            if any(not (row.get(field) or "").strip() for field in FIELDS):
                issues.append({"row": line, "code": "MISSING_FIELD"})
                continue
            invoice = row["invoice_id"].strip()
            if invoice in seen:
                issues.append({"row": line, "code": "DUPLICATE_INVOICE"})
                continue
            seen.add(invoice)
            currency = row["currency"].strip().upper()
            if not re.fullmatch(r"[A-Z]{3}", currency):
                issues.append({"row": line, "code": "INVALID_CURRENCY"})
                continue
            try:
                due = _date(row["due_date"].strip())
            except ValueError:
                issues.append({"row": line, "code": "INVALID_DATE"})
                continue
            try:
                amount = _money(row["open_balance"].strip())
            except (InvalidOperation, ValueError):
                issues.append({"row": line, "code": "INVALID_AMOUNT"})
                continue
            valid += 1
            totals[currency]["open"] += amount
            overdue_days = (as_of - due).days
            if overdue_days > 0 and amount > 0:
                totals[currency]["overdue"] += amount
                bracket = aging[currency][_bucket(overdue_days)]
                bracket["amount"] += amount
                bracket["count"] += 1
                customer = customers[currency][row["customer_id"].strip()]
                customer["overdue"] += amount
                customer["invoices"] += 1
                customer["max_days_overdue"] = max(customer["max_days_overdue"], overdue_days)
        if not rows:
            raise InputError("NO_DATA_ROWS")
    except csv.Error as exc:
        raise InputError("MALFORMED_CSV") from exc
    if not valid:
        raise InputError("NO_VALID_ROWS")
    currencies = sorted(totals)
    return {
        "as_of": as_of.isoformat(),
        "basis": "Calendar dates without timezone conversion; overdue only when due_date < as_of and open_balance > 0; invalid rows excluded; no currency conversion or legal conclusion.",
        "totals": {currency: {key: f"{value:.2f}" for key, value in totals[currency].items()} for currency in currencies},
        "aging": {currency: {bucket: {"amount": f"{aging[currency][bucket]['amount']:.2f}",
                                       "count": aging[currency][bucket]["count"]} for bucket in BUCKETS} for currency in currencies},
        "customers": {currency: [
            {"customer_id": name, "overdue": f"{stats['overdue']:.2f}",
             "invoices": stats["invoices"], "max_days_overdue": stats["max_days_overdue"],
             "priority": "HIGH" if stats["max_days_overdue"] > 90 else "MEDIUM",
             "recommendation": "Human review of invoice, contract and payment record before any collection action"}
            for name, stats in sorted(customers[currency].items(), key=lambda item: (-item[1]["overdue"], item[0]))]
            for currency in currencies},
        "valid_rows": valid, "rejected_rows": len(issues), "issues": issues,
        "platform": "NOT_TESTED", "limitations": ["UTF-8 CSV only; no XLSX/PDF/DOCX, formulas or macros are executed.",
                                                "Missing invoices or payment records cannot be inferred from this file."]
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze one authorized local receivables CSV")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--as-of", required=True)
    args = parser.parse_args()
    try:
        as_of = _date(args.as_of)
        report = analyze(_input(args.input), as_of)
    except (ValueError, InputError) as exc:
        code = str(exc) if isinstance(exc, InputError) else "INVALID_AS_OF"
        print(f"error: {code}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
