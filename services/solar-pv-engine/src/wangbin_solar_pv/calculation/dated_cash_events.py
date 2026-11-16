"""Versioned, source-byte-bound dated project cash events for synthetic Phase 3E.

The CSV is an independently supplied source, never generated from the 3D
annual cash series. The JSON carrier binds those bytes, provenance, selected
cash-flow basis and upstream identities; both are required for calculation.
"""
from __future__ import annotations

import csv
import io
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext
from hashlib import sha256

from ..errors import ContractError
from ..schemas import StrictValidator
from ..serialization import digest
from .break_even_execution import _source_reference
from .common import exact_json_numbers
from .method_config import MethodConfig

VERSION = "solar-pv-dated-cash-events/1.0.0"
MAX_SOURCE_BYTES = 1024 * 1024
MAX_EVENTS = 10000
_COLUMNS = ["kind", "event_id", "date", "period", "amount", "source_id"]
_NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")
_SHA256 = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
_TEXT = {"type": "string", "minLength": 1, "maxLength": 4000}
_DATE = {"type": "string", "format": "date"}


def _object(fields):
    return {"type": "object", "additionalProperties": False,
            "required": list(fields), "properties": fields}


def dated_cash_event_schema():
    """Public format for the carrier paired with the exact original CSV bytes."""
    provenance = _object({"source_id": _TEXT, "source_reference": _TEXT,
                          "source_kind": {"enum": ["SYNTHETIC", "USER_PROVIDED", "DOCUMENT_EXTRACTED"]},
                          "status": {"enum": ["ASSUMED", "VERIFIED", "UNVERIFIED"]},
                          "license_status": {"enum": ["AUTHORIZED", "REQUIRES_REVIEW", "UNKNOWN", "DENIED"]},
                          "reviewer": {"type": ["string", "null"], "minLength": 1},
                          "source_content_sha256": _SHA256, "source_location": _TEXT})
    binding = _object({"project_id": _TEXT, "pv_type": _TEXT, "scenario_id": _TEXT,
                       "currency": {"type": "string", "pattern": "^[A-Z]{3}$"},
                       "cashflow_basis": {"enum": ["pre_tax", "post_tax"]},
                       "price_basis": {"enum": ["nominal", "real"]},
                       "evaluation_date": _DATE, "terminal_date": _DATE,
                       "phase2_input_hash": _SHA256, "method_config_hash": _SHA256,
                       "phase3d_result_hash": _SHA256, "selected_cash_flow_hash": _SHA256})
    event = _object({"event_id": _TEXT, "date": _DATE, "period": _TEXT,
                     "amount": {"type": "number"}, "source_id": _TEXT})
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": VERSION,
            **_object({"schema_version": {"const": VERSION}, "binding": binding,
                       "source_content_sha256": _SHA256, "event_source": provenance,
                       "rate_source": _object({**provenance["properties"], "rate_scope": _TEXT}),
                       "discount_rate": {"type": "number", "exclusiveMinimum": -1},
                       "events": {"type": "array", "minItems": 2, "maxItems": MAX_EVENTS,
                                  "items": event}})}


@dataclass(frozen=True, slots=True)
class ValidatedDatedCashEvents:
    carrier: dict
    source_sha256: str
    carrier_hash: str
    dates: tuple[date, ...]
    amounts: tuple[Decimal, ...]
    year_fractions: tuple[Decimal, ...]
    discount_rate: Decimal
    source_ids: tuple[str, str]


def _decimal_token(token):
    if not isinstance(token, str) or len(token) > 80 or not _NUMBER.fullmatch(token):
        raise ContractError("DATED_CASH_SOURCE_NUMBER")
    number = Decimal(token)
    if not number.is_finite():
        raise ContractError("DATED_CASH_SOURCE_NUMBER")
    return number


def _parsed_date(token):
    try:
        value = date.fromisoformat(token)
    except (TypeError, ValueError):
        raise ContractError("DATED_CASH_EVENT_DATE") from None
    if value.isoformat() != token:
        raise ContractError("DATED_CASH_EVENT_DATE")
    return value


def _source_rows(raw):
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_SOURCE_BYTES:
        raise ContractError("DATED_CASH_SOURCE_BYTES_REQUIRED")
    try:
        text = raw.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""), restkey="_extra", strict=True)
        if reader.fieldnames != _COLUMNS:
            raise ContractError("DATED_CASH_SOURCE_COLUMNS")
        rows = list(reader)
    except (UnicodeError, csv.Error):
        raise ContractError("DATED_CASH_SOURCE_CSV") from None
    if not rows or len(rows) > MAX_EVENTS + 1:
        raise ContractError("DATED_CASH_SOURCE_SIZE_LIMIT")
    if any(set(row) != set(_COLUMNS) or any(value is None for value in row.values())
           for row in rows):
        raise ContractError("DATED_CASH_SOURCE_COLUMNS")
    if any(row["kind"] not in {"RATE", "EVENT"} for row in rows):
        raise ContractError("DATED_CASH_SOURCE_ROW_KIND")
    return rows


def _year_fraction(start, end, convention):
    if end < start:
        raise ContractError("DATED_CASH_DATE_ORDER")
    if convention == "ACT_365F":
        return Decimal((end - start).days) / Decimal(365)
    if convention == "30E_360":
        return (Decimal((end.year - start.year) * 360 + (end.month - start.month) * 30
                        + min(end.day, 30) - min(start.day, 30)) / Decimal(360))
    if convention != "ACT_ACT":
        raise ContractError("DATED_CASH_DAY_COUNT_UNSUPPORTED")
    total = Decimal(0)
    current = start
    while current < end:
        following = min(end, date(current.year + 1, 1, 1))
        leap = current.year % 4 == 0 and (current.year % 100 != 0 or current.year % 400 == 0)
        total += Decimal((following - current).days) / Decimal(366 if leap else 365)
        current = following
    return total


def validate_dated_cash_events(carrier, source_bytes, *, exported, methods, financial,
                               scenario_id, cashflow_basis, selected_cash_flow, terminal_date):
    """Fail closed on provenance, exact CSV bytes and every selected annual total."""
    exact_json_numbers(carrier)
    if not isinstance(carrier, dict) or next(StrictValidator(dated_cash_event_schema()).iter_errors(carrier), None):
        raise ContractError("DATED_CASH_SOURCE_SCHEMA")
    config = methods if isinstance(methods, MethodConfig) else MethodConfig.from_dict(methods)
    if config.data_mode != "SYNTHETIC":
        raise ContractError("DATED_CASH_SOURCE_SYNTHETIC_ONLY")
    day_count = config.require("time.day_count")
    day_count_source = config.to_dict()["parameters"]["time.day_count"]
    if day_count_source["license_status"] != "AUTHORIZED" or not day_count_source["source_reference"]:
        raise ContractError("DATED_CASH_DAY_COUNT_SOURCE_UNREVIEWED")
    _source_reference(day_count_source["source_reference"])
    source_hash = sha256(source_bytes).hexdigest() if isinstance(source_bytes, bytes) else None
    if source_hash != carrier["source_content_sha256"]:
        raise ContractError("DATED_CASH_SOURCE_HASH_MISMATCH")
    for key in ("event_source", "rate_source"):
        record = carrier[key]
        if record["source_content_sha256"] != source_hash or record["license_status"] != "AUTHORIZED":
            raise ContractError("DATED_CASH_SOURCE_UNREVIEWED", key)
        if record["status"] not in {"ASSUMED", "VERIFIED"} or (record["status"] == "VERIFIED" and not record["reviewer"]):
            raise ContractError("DATED_CASH_SOURCE_UNREVIEWED", key)
        if record["source_kind"] == "SYNTHETIC" and record["status"] != "ASSUMED":
            raise ContractError("DATED_CASH_SOURCE_UNREVIEWED", key)
        _source_reference(record["source_reference"])
        _source_reference(record["source_location"])
    if carrier["event_source"]["source_id"] == carrier["rate_source"]["source_id"]:
        raise ContractError("DATED_CASH_SOURCE_ID_CONFLICT")
    values = exported["project"]["values"]
    rate_scope = (f"PROJECT_{cashflow_basis.upper()}_"
                  f"{values['project.price_basis']['value'].upper()}_"
                  f"{values['project.currency']['value']}_DATED")
    if carrier["rate_source"]["rate_scope"] != rate_scope:
        raise ContractError("DATED_CASH_RATE_BASIS_MISMATCH")
    expected = {"project_id": exported["project"]["project_id"],
                "pv_type": exported["project"]["pv_type"], "scenario_id": scenario_id,
                "currency": values["project.currency"]["value"], "cashflow_basis": cashflow_basis,
                "price_basis": values["project.price_basis"]["value"],
                "evaluation_date": values["project.evaluation_date"]["value"],
                "terminal_date": terminal_date, "phase2_input_hash": exported["input_hash"],
                "method_config_hash": config.hash, "phase3d_result_hash": financial["result_hash"],
                "selected_cash_flow_hash": digest(selected_cash_flow)}
    for key, value in expected.items():
        if carrier["binding"][key] != value:
            raise ContractError("DATED_CASH_SOURCE_BINDING_MISMATCH", key)
    if len(selected_cash_flow) < 2 or len(selected_cash_flow) > MAX_EVENTS:
        raise ContractError("DATED_CASH_PERIOD_COUNT")
    rows = _source_rows(source_bytes)
    rate_rows = [row for row in rows if row["kind"] == "RATE"]
    event_rows = [row for row in rows if row["kind"] == "EVENT"]
    if len(rate_rows) != 1 or len(event_rows) != len(carrier["events"]):
        raise ContractError("DATED_CASH_SOURCE_ROW_COUNT")
    rate = rate_rows[0]
    if (rate["event_id"] or rate["date"] or rate["period"] != "DATED_DISCOUNT_RATE"
            or rate["source_id"] != carrier["rate_source"]["source_id"]
            or _decimal_token(rate["amount"]) != carrier["discount_rate"]):
        raise ContractError("DATED_CASH_RATE_SOURCE_MISMATCH")
    seen = set()
    dates = []
    amounts = []
    period_totals = [Decimal(0) for _ in selected_cash_flow]
    period_counts = [0 for _ in selected_cash_flow]
    base_date = _parsed_date(expected["evaluation_date"])
    last_date = _parsed_date(terminal_date)
    commissioning = _parsed_date(values["schedule.commissioning_date"]["value"])
    if last_date <= base_date:
        raise ContractError("DATED_CASH_DATE_ORDER")
    for source_row, event in zip(event_rows, carrier["events"]):
        if event["event_id"] in seen:
            raise ContractError("DATED_CASH_DUPLICATE_EVENT")
        seen.add(event["event_id"])
        if (source_row["event_id"] != event["event_id"] or source_row["date"] != event["date"]
                or source_row["period"] != event["period"] or source_row["source_id"] != event["source_id"]
                or _decimal_token(source_row["amount"]) != event["amount"]):
            raise ContractError("DATED_CASH_EVENT_SOURCE_MISMATCH")
        if event["source_id"] != carrier["event_source"]["source_id"]:
            raise ContractError("DATED_CASH_EVENT_SOURCE_MISMATCH")
        event_date = _parsed_date(event["date"])
        period = event["period"]
        if period == "CONSTRUCTION":
            index = 0
            if event_date != base_date:
                raise ContractError("DATED_CASH_BASE_DATE_REQUIRED")
        elif period.startswith("OPERATING_YEAR_") and period[15:].isdigit():
            index = int(period[15:])
            if (not 1 <= index < len(selected_cash_flow) or not base_date < event_date <= last_date
                    or event_date < commissioning or event_date.year != commissioning.year + index - 1):
                raise ContractError("DATED_CASH_EVENT_PERIOD")
        else:
            raise ContractError("DATED_CASH_EVENT_PERIOD")
        dates.append(event_date)
        amounts.append(event["amount"])
        period_totals[index] += event["amount"]
        period_counts[index] += 1
    if not all(period_counts) or not any(d == last_date for d in dates):
        raise ContractError("DATED_CASH_PERIOD_COVERAGE")
    if any(observed != expected_amount for observed, expected_amount in zip(period_totals, selected_cash_flow)):
        raise ContractError("DATED_CASH_LEDGER_RECONCILIATION")
    with localcontext() as ctx:
        ctx.prec = 80
        fractions = tuple(_year_fraction(base_date, event_date, day_count) for event_date in dates)
    return ValidatedDatedCashEvents(deepcopy(carrier), source_hash, digest(carrier),
                                    tuple(dates), tuple(amounts), fractions,
                                    carrier["discount_rate"],
                                    (carrier["event_source"]["source_id"], carrier["rate_source"]["source_id"]))
