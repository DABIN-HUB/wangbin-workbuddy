"""Value-only Phase 3C consumption kernels using frozen formula field IDs.

Interval kernels take scalar Decimal/integer kWh. Annual kernels take explicit
stable-ID maps and the exact operating/settlement ID sequence. This module does
not select methods, construct calendars, infer missing values, or run projects.
"""
from __future__ import annotations

from decimal import Decimal

from ..errors import ContractError
from .common import calculated, integer, nonnegative, nonvalue, number, precision_context

FORMULA_IDS = (
    "F-SELF-CONSUMPTION", "F-EXPORTED-ENERGY", "F-CURTAILED-ENERGY", "F-ENERGY-BALANCE",
    "F-DELIVERED-ENERGY", "F-SELF-CONSUMPTION-RATIO", "F-LOAD-COVERAGE-RATIO",
    "F-ENERGY-REVENUE", "F-PPA-REVENUE",
)

_REQUIRED_FIELDS = {
    "F-SELF-CONSUMPTION": ("energy.available_kwh", "load.interval_kwh"),
    "F-EXPORTED-ENERGY": ("energy.available_kwh", "consumption.self_kwh", "grid.export_limit_kwh"),
    "F-CURTAILED-ENERGY": ("energy.available_kwh", "consumption.self_kwh", "consumption.export_kwh"),
    "F-ENERGY-BALANCE": ("energy.available_kwh", "consumption.self_kwh", "consumption.export_kwh", "consumption.curtailed_kwh"),
    "F-DELIVERED-ENERGY": ("consumption.self_kwh", "consumption.export_kwh", "time.operating_interval_ids"),
    "F-SELF-CONSUMPTION-RATIO": ("consumption.self_kwh", "energy.delivered_annual_kwh", "time.operating_interval_ids"),
    "F-LOAD-COVERAGE-RATIO": ("consumption.self_kwh", "load.interval_kwh", "time.operating_interval_ids"),
    "F-ENERGY-REVENUE": ("consumption.self_kwh", "tariff.avoidable_price", "consumption.export_kwh", "tariff.export_price", "revenue.other_benefit", "time.settlement_interval_ids"),
    "F-PPA-REVENUE": ("consumption.host_delivery_kwh", "tariff.ppa_price", "consumption.export_kwh", "tariff.export_price", "revenue.other_benefit", "time.settlement_interval_ids"),
}

_ALLOWED_OPTION_KEYS = {"precision_digits", "applicable", "index_ids"}


def evaluate(formula_id, values, options=None):
    """Evaluate a frozen atomic formula without early monetary rounding."""
    if type(formula_id) is not str or formula_id not in FORMULA_IDS:
        raise ContractError("UNKNOWN_FORMULA", formula_id if isinstance(formula_id, str) else None)
    options = _options(options)
    if options.get("applicable", True) is False:
        return nonvalue("NOT_APPLICABLE", "EXPLICITLY_NOT_APPLICABLE", details={"formula_id": formula_id})
    if not isinstance(values, dict):
        raise ContractError("FORMULA_VALUES_MAPPING_REQUIRED", formula_id)
    required = set(_REQUIRED_FIELDS[formula_id])
    missing = required - set(values)
    if missing:
        return _missing(formula_id, missing)
    if set(values) != required:
        raise ContractError("FORMULA_VALUES_KEYS", formula_id)
    missing = {field for field in required if _contains_none(values[field])}
    if missing:
        return _missing(formula_id, missing)
    precision = options.get("precision_digits", 80)
    with precision_context(precision):
        if formula_id in FORMULA_IDS[:4]:
            value = _interval(formula_id, values)
        elif formula_id in FORMULA_IDS[4:7]:
            value = _annual(formula_id, values)
        else:
            value = _revenue(formula_id, values)
    if isinstance(value, dict) and "status" in value:
        return value
    return calculated(value, details={"formula_id": formula_id, "precision_digits": precision})


def _missing(formula_id, fields):
    return nonvalue("BLOCKED_MISSING_INPUT", "BLOCKED_MISSING_INPUT", details={"formula_id": formula_id, "missing_field_ids": sorted(fields)})


def _contains_none(value):
    if value is None:
        return True
    if isinstance(value, dict):
        return any(_contains_none(child) for child in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_none(child) for child in value)
    return False


def _options(options):
    if options is None:
        return {}
    if not isinstance(options, dict):
        raise ContractError("OPTIONS_MAPPING_REQUIRED")
    if set(options) - _ALLOWED_OPTION_KEYS:
        raise ContractError("OPTIONS_KEYS")
    if "applicable" in options and type(options["applicable"]) is not bool:
        raise ContractError("APPLICABILITY_BOOLEAN_REQUIRED")
    if "precision_digits" in options:
        integer(options["precision_digits"], "precision.precision_digits", minimum=34, maximum=1024)
    if "index_ids" in options:
        if not isinstance(options["index_ids"], dict):
            raise ContractError("INDEX_IDS_MAPPING_REQUIRED")
        for field, ids in options["index_ids"].items():
            if not isinstance(field, str):
                raise ContractError("INDEX_FIELD_ID_REQUIRED")
            _validate_ids(ids, field)
    return options


def _interval(formula_id, values):
    available = nonnegative(values["energy.available_kwh"], "energy.available_kwh")
    if formula_id == "F-SELF-CONSUMPTION":
        return min(available, nonnegative(values["load.interval_kwh"], "load.interval_kwh"))
    self_kwh = nonnegative(values["consumption.self_kwh"], "consumption.self_kwh")
    if formula_id == "F-EXPORTED-ENERGY":
        limit = nonnegative(values["grid.export_limit_kwh"], "grid.export_limit_kwh")
        if self_kwh > available:
            raise ContractError("ENERGY_ALLOCATION_EXCEEDS_AVAILABLE", "consumption.self_kwh")
        return min(max(available - self_kwh, Decimal(0)), limit)
    export = nonnegative(values["consumption.export_kwh"], "consumption.export_kwh")
    remainder = available - self_kwh - export
    if formula_id == "F-CURTAILED-ENERGY":
        if remainder < 0:
            raise ContractError("ENERGY_ALLOCATION_EXCEEDS_AVAILABLE", "consumption.export_kwh")
        return remainder
    # The balance formula is diagnostic: a signed nonzero residual is evidence
    # for the caller, not a physical energy value to clamp or silently repair.
    return remainder - nonnegative(values["consumption.curtailed_kwh"], "consumption.curtailed_kwh")


def _validate_ids(ids, field_id):
    if not isinstance(ids, (list, tuple)):
        raise ContractError("INDEX_IDS_SEQUENCE_REQUIRED", field_id)
    seen = set()
    for item in ids:
        if type(item) is not str or not item:
            raise ContractError("STABLE_INDEX_ID_REQUIRED", field_id)
        if item in seen:
            raise ContractError("DUPLICATE_INDEX_ID", field_id)
        seen.add(item)
    return tuple(ids)


def _indexed(values, field_id, ids, *, signed=False):
    mapping = values[field_id]
    if not isinstance(mapping, dict):
        raise ContractError("INDEXED_DECIMAL_MAPPING_REQUIRED", field_id)
    if any(type(key) is not str or not key for key in mapping):
        raise ContractError("STABLE_INDEX_ID_REQUIRED", field_id)
    if set(mapping) != set(ids):
        raise ContractError("INDEX_SET_MISMATCH", field_id)
    convert = number if signed else nonnegative
    return {item: convert(mapping[item], field_id) for item in ids}


def _annual(formula_id, values):
    ids = _validate_ids(values["time.operating_interval_ids"], "time.operating_interval_ids")
    self_kwh = _indexed(values, "consumption.self_kwh", ids)
    total_self = sum(self_kwh.values(), Decimal(0))
    if formula_id == "F-DELIVERED-ENERGY":
        export = _indexed(values, "consumption.export_kwh", ids)
        return sum((self_kwh[item] + export[item] for item in ids), Decimal(0))
    if formula_id == "F-SELF-CONSUMPTION-RATIO":
        denominator = nonnegative(values["energy.delivered_annual_kwh"], "energy.delivered_annual_kwh")
    else:
        load = _indexed(values, "load.interval_kwh", ids)
        denominator = sum(load.values(), Decimal(0))
    if denominator == 0:
        return nonvalue("UNDEFINED", "ZERO_DENOMINATOR", details={"formula_id": formula_id})
    if formula_id == "F-LOAD-COVERAGE-RATIO":
        if any(self_kwh[item] > load[item] for item in ids):
            raise ContractError("ENERGY_ALLOCATION_EXCEEDS_LOAD", "consumption.self_kwh")
    elif total_self > denominator:
        raise ContractError("ENERGY_ALLOCATION_EXCEEDS_DELIVERED", "consumption.self_kwh")
    return total_self / denominator


def _revenue(formula_id, values):
    ids = _validate_ids(values["time.settlement_interval_ids"], "time.settlement_interval_ids")
    if formula_id == "F-ENERGY-REVENUE":
        local_energy_field, local_price_field = "consumption.self_kwh", "tariff.avoidable_price"
    else:
        # The host's avoided purchase benefit is not investor PPA income.
        local_energy_field, local_price_field = "consumption.host_delivery_kwh", "tariff.ppa_price"
    local_energy = _indexed(values, local_energy_field, ids)
    local_price = _indexed(values, local_price_field, ids, signed=True)
    export = _indexed(values, "consumption.export_kwh", ids)
    export_price = _indexed(values, "tariff.export_price", ids, signed=True)
    # Frozen revenue.other_items.amount has no nonnegative constraint. Preserve
    # a source-backed signed adjustment instead of changing that input domain.
    other = number(values["revenue.other_benefit"], "revenue.other_benefit")
    return sum((local_energy[item] * local_price[item] + export[item] * export_price[item] for item in ids), Decimal(0)) + other
