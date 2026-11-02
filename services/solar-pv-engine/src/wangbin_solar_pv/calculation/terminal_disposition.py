"""Bounded, source-byte-checked project terminal disposition evidence.

This is a calculation-source carrier, not a new Phase 2 field, D2 control, D3
series, or an arbitrary cash-flow override. Validation alone never proves that
an event is absent from a particular Phase 3D ledger.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from hashlib import sha256
import re

from ..errors import ContractError
from ..schemas import StrictValidator, format_checker
from ..serialization import digest, loads
from .break_even_execution import _source_reference
from .common import exact_json_numbers, nonnegative
from .result_contract import result_schema

VERSION = "solar-pv-project-terminal-disposition/1.0.0"
_HASH = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
_ID = {"type": "string", "minLength": 1, "maxLength": 96}
_TEXT = {"type": "string", "minLength": 1, "maxLength": 4000}
_DATE = {"type": "string", "format": "date", "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"}
_CURRENCY = {"type": "string", "pattern": "^[A-Z]{3}$"}
_PV_TYPE = {"enum": result_schema()["properties"]["pv_type"]["enum"]}


def _object(properties):
    return {"type": "object", "additionalProperties": False,
            "properties": properties, "required": list(properties)}


_SOURCE = _object({
    "source_id": _ID, "source_kind": {"enum": ["SYNTHETIC", "USER_PROVIDED", "DOCUMENT_EXTRACTED", "EXTERNAL_SOURCE"]},
    "source_reference": _TEXT, "source_section_or_cell": _TEXT, "source_excerpt": _TEXT,
    "source_content_sha256": _HASH, "source_status": {"enum": ["ASSUMED", "VERIFIED"]},
    "economic_status": {"enum": ["ACTUAL_CASH", "CONTRACT_FORECAST", "SYNTHETIC_ASSUMPTION"]},
    "source_timestamp": _DATE, "effective_from": _DATE, "effective_to": _DATE,
    "reviewer": _TEXT, "license_status": {"const": "AUTHORIZED"},
})
_FACT = _object({"amount": {"type": "number", "minimum": 0}, "date": _DATE,
                 "currency": _CURRENCY, "unit": _CURRENCY, "source": _SOURCE})
_EVENT = _object({
    "event_id": _ID, "asset_id": _ID, "transaction_id": _ID,
    "disposal_object": _TEXT, "category": {"enum": ["ASSET_DISPOSITION", "RESIDUAL_FUND_RECOVERY"]},
    "project_boundary": {"const": "PROJECT_UNLEVERED"},
    "ledger_booking": _object({"already_recorded": {"type": "boolean"},
                               "ledger_event_id": {"type": ["string", "null"], "minLength": 1, "maxLength": 96}}),
    "receipt": _FACT, "direct_cost": _FACT, "income_tax_cash": _FACT,
    "other_tax_cash": _FACT, "vat_cash": _FACT, "tax_included": {"type": "boolean"},
})
_NO_DISPOSITION = _object({
    "covered_asset_ids": {"type": "array", "minItems": 1, "maxItems": 100, "uniqueItems": True, "items": _ID},
    "reason": _TEXT, "tax_treatment": {"const": "NO_DISPOSITION_TAX"},
    "working_capital_treatment": {"enum": ["LEDGER_ALREADY_RECOVERED", "NO_WORKING_CAPITAL_DECLARED"]},
    "source": _SOURCE,
})
_SOURCE_FACTS = _object({
    "project_id": _ID, "pv_type": _PV_TYPE,
    "evaluation_date": _DATE, "terminal_date": _DATE, "currency": _CURRENCY,
    "mode": {"enum": ["EVENTS", "NO_DISPOSITION"]},
    "covered_asset_ids": {"type": "array", "minItems": 1, "maxItems": 100, "uniqueItems": True, "items": _ID},
    "events": {"type": "array", "maxItems": 100, "items": _EVENT},
    "no_disposition": {"anyOf": [_NO_DISPOSITION, {"type": "null"}]},
})
_BINDING = _object({
    "project_id": _ID, "pv_type": _PV_TYPE,
    "evaluation_date": _DATE, "currency": _CURRENCY, "scenario_id": _ID,
    # Phase 2 canonical source snapshot IDs are `sources-` + SHA-256; they
    # are identifiers, not bare digests. Retain bare-hash compatibility for
    # existing R1-1 carriers while accepting the actual validated Phase 2 ID.
    "phase2_input_hash": _HASH,
    "phase2_source_snapshot_id": {"anyOf": [_HASH, {"type": "string", "pattern": "^sources-[0-9a-f]{64}$"}]},
    "method_config_hash": _HASH, "d3_content_hash": {"anyOf": [_HASH, {"type": "null"}]},
    "phase3b_result_hash": _HASH, "phase3c_result_hash": _HASH,
    "phase3d_result_hash": _HASH, "basis": {"enum": ["项目税前", "项目税后"]},
})
_SCHEMA = _object({"schema_version": {"const": VERSION}, "source": _SOURCE_FACTS,
                   "source_content_hash": _HASH, "binding": _BINDING})


@dataclass(frozen=True, slots=True)
class ValidatedTerminalDisposition:
    source: dict
    binding: dict
    source_content_hash: str


def terminal_disposition_schema():
    return deepcopy(_SCHEMA)


def _date(value):
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError
        return parsed
    except (TypeError, ValueError):
        raise ContractError("TERMINAL_DATE_INVALID") from None


def _check_provenance(source, documents, fact_date, *, fact_key=None, amount=None, currency=None):
    source_id = source["source_id"]
    _source_reference(source["source_reference"])
    _source_reference(source["source_section_or_cell"])
    if source["source_kind"] == "SYNTHETIC":
        if source["source_status"] != "ASSUMED" or source["economic_status"] != "SYNTHETIC_ASSUMPTION":
            raise ContractError("SYNTHETIC_IS_NOT_VERIFIED")
    elif source["source_status"] != "VERIFIED" or source["economic_status"] == "SYNTHETIC_ASSUMPTION":
        raise ContractError("TERMINAL_SOURCE_UNVERIFIED")
    if not _date(source["effective_from"]) <= fact_date <= _date(source["effective_to"]):
        raise ContractError("TERMINAL_SOURCE_OUT_OF_DATE")
    if _date(source["source_timestamp"]) > fact_date:
        raise ContractError("TERMINAL_SOURCE_OUT_OF_DATE")
    raw = documents.get(source_id)
    if not isinstance(raw, bytes) or not raw or len(raw) > 1024 * 1024:
        raise ContractError("TERMINAL_SOURCE_BYTES_REQUIRED")
    if sha256(raw).hexdigest() != source["source_content_sha256"]:
        raise ContractError("TERMINAL_SOURCE_BYTES_MISMATCH")
    try:
        text = raw.decode("utf-8")
    except UnicodeError:
        raise ContractError("TERMINAL_SOURCE_TEXT_REQUIRED") from None
    if source["source_excerpt"] not in text or source["source_section_or_cell"] not in text:
        raise ContractError("TERMINAL_SOURCE_LOCATION_MISMATCH")
    if fact_key is not None:
        # These are reviewed *extractions* from source bytes, not independent
        # caller assertions. Never accept a rehashed carrier that changes a
        # number while leaving the underlying economic evidence unchanged.
        match = re.search(r"(?<![A-Za-z0-9_])" + re.escape(fact_key) +
                          r"=([0-9]+(?:\.[0-9]+)?)(?![0-9.])", source["source_excerpt"])
        if (match is None or Decimal(match.group(1)) != amount or
                fact_date.isoformat() not in text or currency not in text):
            raise ContractError("TERMINAL_FACT_NOT_SUPPORTED_BY_SOURCE")


def validate_terminal_disposition(carrier, source_documents):
    """Validate immutable source facts and candidate binding structure.

    The caller supplies exact source bytes, never caller-asserted hashes alone.
    The binding's relationship to a *real* validated 3D result is a separate gate.
    """
    if isinstance(carrier, (str, bytes)):
        carrier = loads(carrier, max_bytes=2 * 1024 * 1024)
    exact_json_numbers(carrier)
    if next(StrictValidator(_SCHEMA, format_checker=format_checker()).iter_errors(carrier), None) is not None:
        raise ContractError("TERMINAL_DISPOSITION_SCHEMA")
    source, binding = carrier["source"], carrier["binding"]
    if digest(source) != carrier["source_content_hash"]:
        raise ContractError("TERMINAL_SOURCE_CONTENT_MISMATCH")
    if not isinstance(source_documents, dict) or len(source_documents) > 100 or set(source_documents) != {
        fact["source"]["source_id"] for event in source["events"] for fact in (
            event["receipt"], event["direct_cost"], event["income_tax_cash"],
            event["other_tax_cash"], event["vat_cash"])
    } | ({source["no_disposition"]["source"]["source_id"]} if source["no_disposition"] else set()):
        raise ContractError("TERMINAL_SOURCE_DOCUMENT_MEMBERSHIP")
    if any(source[key] != binding[key] for key in ("project_id", "pv_type", "evaluation_date", "currency")):
        raise ContractError("TERMINAL_PROJECT_IDENTITY")
    _date(source["evaluation_date"])
    if _date(source["terminal_date"]) <= _date(source["evaluation_date"]):
        raise ContractError("TERMINAL_DATE_OUTSIDE_PROJECT")
    coverage = set(source["covered_asset_ids"])
    if source["mode"] == "NO_DISPOSITION":
        declaration = source["no_disposition"]
        if source["events"] or not declaration or set(declaration["covered_asset_ids"]) != coverage:
            raise ContractError("TERMINAL_COVERAGE_INCOMPLETE")
        _check_provenance(declaration["source"], source_documents, _date(source["terminal_date"]))
        zero_text = source_documents[declaration["source"]["source_id"]].decode("utf-8")
        if (declaration["reason"] not in zero_text or
                any(f"asset_id={asset}" not in zero_text for asset in coverage) or
                f"tax_treatment={declaration['tax_treatment']}" not in zero_text or
                f"working_capital_treatment={declaration['working_capital_treatment']}" not in zero_text):
            raise ContractError("TERMINAL_ZERO_DECLARATION_UNSUPPORTED")
    else:
        if source["no_disposition"] is not None or not source["events"]:
            raise ContractError("TERMINAL_COVERAGE_INCOMPLETE")
        ids = [(e["event_id"], e["asset_id"], e["transaction_id"]) for e in source["events"]]
        if any(len({row[i] for row in ids}) != len(ids) for i in range(3)) or {row[1] for row in ids} != coverage:
            raise ContractError("TERMINAL_EVENT_DUPLICATE_OR_UNCOVERED")
        for event in source["events"]:
            if event["ledger_booking"]["already_recorded"] or event["ledger_booking"]["ledger_event_id"] is not None:
                raise ContractError("TERMINAL_ALREADY_RECORDED")
            for key in ("receipt", "direct_cost", "income_tax_cash", "other_tax_cash", "vat_cash"):
                fact = event[key]
                nonnegative(fact["amount"], key)
                if fact["currency"] != source["currency"] or fact["unit"] != fact["currency"]:
                    raise ContractError("TERMINAL_CURRENCY_MISMATCH")
                at = _date(fact["date"])
                if not _date(source["evaluation_date"]) <= at <= _date(source["terminal_date"]):
                    raise ContractError("TERMINAL_DATE_OUTSIDE_PROJECT")
                _check_provenance(fact["source"], source_documents, at, fact_key={
                    "receipt": "receipt", "direct_cost": "cost", "income_tax_cash": "income_tax",
                    "other_tax_cash": "other_tax", "vat_cash": "vat_cash",
                }[key], amount=fact["amount"], currency=fact["currency"])
            receipt_document = source_documents[event["receipt"]["source"]["source_id"]]
            if any(claim not in receipt_document for claim in (
                f"asset_id={event['asset_id']}".encode(),
                f"transaction_id={event['transaction_id']}".encode(),
                f"category={event['category']}".encode(),
                f"project_boundary={event['project_boundary']}".encode(),
                f"ledger_booking={str(event['ledger_booking']['already_recorded']).lower()}".encode(),
            )):
                raise ContractError("TERMINAL_TRANSACTION_NOT_SUPPORTED_BY_SOURCE")
            expected_tax_flag = b"tax_included=true" if event["tax_included"] else b"tax_included=false"
            if expected_tax_flag not in receipt_document:
                raise ContractError("TERMINAL_TAX_BOUNDARY_UNSUPPORTED")
            if event["category"] == "RESIDUAL_FUND_RECOVERY" and event["tax_included"]:
                raise ContractError("TERMINAL_TAX_BOUNDARY")
    return ValidatedTerminalDisposition(deepcopy(source), deepcopy(binding), carrier["source_content_hash"])
