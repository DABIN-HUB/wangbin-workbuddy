"""Versioned P2-1 execution control for one existing settlement price atom.

Selection does not certify a generation receipt, a candidate replay, a cash
flow, or a break-even root. Those are separate, fail-closed execution gates.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit

from ..errors import ContractError
from ..schemas import StrictValidator
from ..serialization import digest, dumps, loads
from ..timeseries_bundle import TimeSeriesBundle
from .input_contract import ValidatedInput, calculation_identity, validate_export
from .method_config import MethodConfig

_SCHEMA = loads((Path(__file__).parent / "schema" / "break-even-execution.schema.json").read_bytes())
_PRICE_BASIS = {"项目税前": "pre_tax", "项目税后": "post_tax"}
_BASIS_KEYS = ("currency", "price_year", "tax_basis", "price_basis")


@dataclass(frozen=True, slots=True)
class ValidatedPriceSelector:
    control: dict
    original_atom: dict
    selector_hash: str
    original_input_hash: str
    original_dataset_content_hash: str | None


def execution_schema():
    return deepcopy(_SCHEMA)


def _source_reference(reference):
    if (re.search(r"(?:^|\s)[A-Za-z]:[\\/]", reference)
            or reference.startswith(("/", "\\", "file:"))):
        raise ContractError("PRIVATE_PATH_REFERENCE")
    for address in re.findall(r"https?://[^\s]+", reference):
        try:
            url = urlsplit(address)
            if (url.username or url.password or any(key.casefold() in {
                    "token", "api_key", "api-key", "password", "access_token", "client_secret", "secret", "authorization"
            } for key in parse_qs(url.query, keep_blank_values=True))):
                raise ContractError("CREDENTIAL_URL")
        except ValueError:
            raise ContractError("BREAK_EVEN_SOURCE_REFERENCE") from None


def _record_source(record):
    if (not isinstance(record, dict) or record.get("status") not in {"ASSUMED", "UNVERIFIED", "VERIFIED"}
            or record.get("license_status") != "AUTHORIZED"
            or not all(record.get(key) for key in ("source_id", "source_url_or_attachment", "source_section_or_cell"))):
        raise ContractError("BREAK_EVEN_SOURCE_UNAVAILABLE")
    _source_reference(record["source_url_or_attachment"])
    return record


def _cash_basis(control, validated):
    # The frozen registry names the project pre-/post-tax and investor actual
    # cash bases. The 05-field-bindings mapping is not itself a cash event.
    tax = _record_source(validated.project.values.get("project.cashflow_tax_basis"))["value"]
    _record_source(validated.project.values.get("project.ownership_mode"))
    expected = _PRICE_BASIS.get(control["basis"])
    if expected is None or tax not in {expected, "both"}:
        raise ContractError("BREAK_EVEN_BASIS_NOT_SOURCED")
    # No verified equity receipt vector or its rate is established here.
    return expected


def _target(validated, bundle, field_id, row_id):
    if field_id == "tariff.ppa_price":
        return validated.project.values.get(field_id)
    if field_id == "tariff.market_series.sale_price":
        if bundle is None or "tariff.market_series" not in bundle.dataset_ids:
            raise ContractError("BREAK_EVEN_MARKET_BUNDLE_REQUIRED")
        matches = []
        for row in bundle.rows("tariff.market_series"):
            if row["row_id"] == row_id:
                matches.append(row["fields"].get(field_id))
        if len(matches) != 1:
            raise ContractError("BREAK_EVEN_ROW_NOT_UNIQUE")
        return matches[0]
    table = validated.project.values.get("tariff.periods", {}).get("value", [])
    if not isinstance(table, list):
        raise ContractError("BREAK_EVEN_ROW_NOT_UNIQUE")
    matches = [row for row in table if row["row_id"] == row_id]
    if len(matches) != 1:
        raise ContractError("BREAK_EVEN_ROW_NOT_UNIQUE")
    row = matches[0]
    try:
        fields = row["fields"]
        start = date.fromisoformat(fields["tariff.periods.effective_from"]["value"])
        end = date.fromisoformat(fields["tariff.periods.effective_to"]["value"])
        evaluation = date.fromisoformat(validated.project.values["project.evaluation_date"]["value"])
        if end < evaluation or start > end:
            raise ContractError("BREAK_EVEN_PRICE_NOT_EFFECTIVE")
    except (KeyError, TypeError, ValueError):
        raise ContractError("BREAK_EVEN_PRICE_NOT_EFFECTIVE") from None
    return fields.get(field_id)


def validate_price_selector(control, original_export, methods, original_bundle, catalog):
    """Bind a strict control to a validated original quote, D2 and full D3.

    Physical 3B receipt identity and actual period sales are checked by replay;
    the selector carries the claimed generation hash but cannot authenticate
    a physical result without the generation directory and its full receipt.
    """
    from .common import exact_json_numbers
    exact_json_numbers(control)
    if next(StrictValidator(_SCHEMA).iter_errors(control), None) is not None:
        raise ContractError("BREAK_EVEN_EXECUTION_SCHEMA")
    source = control["source"]
    for reference in (source["source_id"], source["source_reference"]):
        _source_reference(reference)
    if (source["status"] == "VERIFIED"  # reviewer absent from approved control
            or (source["source_kind"] == "SYNTHETIC") != (source["status"] == "ASSUMED")):
        raise ContractError("BREAK_EVEN_SOURCE_UNAVAILABLE")
    export = original_export.export if isinstance(original_export, ValidatedInput) else original_export
    validated = validate_export(export, catalog)
    method = MethodConfig.from_dict(methods.to_dict() if isinstance(methods, MethodConfig) else methods)
    project = validated.project
    if (project.project_id != control["project_id"] or project.pv_type != control["pv_type"]
            or project.pv_type not in method.to_dict()["pv_types"]
            or validated.phase2_input_hash != control["original_input_hash"]
            or validated.phase2_source_snapshot_id != control["original_source_snapshot_id"]
            or method.hash != control["method_config_hash"]):
        raise ContractError("BREAK_EVEN_ORIGINAL_IDENTITY")
    if original_bundle is not None and not isinstance(original_bundle, TimeSeriesBundle):
        raise ContractError("BREAK_EVEN_ORIGINAL_BUNDLE_REQUIRED")
    identity = calculation_identity(validated, method, catalog, datasets=original_bundle)
    bundle_hash = None if original_bundle is None else identity["input_identity_payload"]["datasets"]["content_hash"]
    if bundle_hash != control["original_dataset_content_hash"]:
        raise ContractError("BREAK_EVEN_ORIGINAL_BUNDLE_IDENTITY")
    _cash_basis(control, validated)
    selector = control["selector"]
    field_id = selector["field_id"]
    price_source = method.require("settlement.price_source")
    revenue_method = method.require("settlement.revenue_method")
    if ((field_id == "tariff.periods.sale_price" and price_source != "PERIOD_TABLE")
            or (field_id == "tariff.market_series.sale_price" and price_source != "MARKET_SERIES")
            or (field_id == "tariff.periods.avoidable_price" and (
                revenue_method not in {"OWNER_AVOIDED_COST", "PPA_DISCOUNT"} or project.pv_type != "industrial_rooftop"))
            or (field_id == "tariff.ppa_price" and revenue_method != "PPA_FIXED")):
        raise ContractError("BREAK_EVEN_PRICE_NOT_CONSUMED")
    atom = _record_source(_target(validated, original_bundle, field_id, selector["row_id"]))
    if (atom.get("field_id") != field_id or atom.get("field_instance_id") != selector["field_instance_id"]
            or atom.get("unit") != selector["unit"] or digest(atom) != selector["original_atom_hash"]):
        raise ContractError("BREAK_EVEN_ORIGINAL_ATOM_IDENTITY")
    economic = {key: method.require("settlement." + key) for key in _BASIS_KEYS}
    if atom.get("economic_basis") != economic or selector["economic_basis"] != economic:
        raise ContractError("BREAK_EVEN_PRICE_BASIS")
    method.require("break_even.method")
    low, high = method.require("break_even.minimum_price"), method.require("break_even.maximum_price")
    method.require("break_even.price_tolerance")
    method.require("break_even.maximum_iterations")
    if low < 0 or atom["value"] < 0:
        method.require("settlement.negative_price_treatment")
        _record_source(project.values.get("tariff.negative_price_rule"))
    if not low < high:
        raise ContractError("BREAK_EVEN_PRICE_DOMAIN")
    return ValidatedPriceSelector(deepcopy(control), deepcopy(atom), digest(control),
                                  validated.phase2_input_hash, bundle_hash)
