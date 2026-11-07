"""Source-byte-bound, synthetic-only annual trading-fee payment convention.

This independent carrier is a Phase 3D source, not a frozen Phase 2/D2/D3
field, a settlement fee rate, or evidence of a real-world payment.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from ..errors import ContractError
from ..schemas import StrictValidator
from ..serialization import digest, loads
from .break_even_execution import _source_reference
from .common import exact_json_numbers
from .method_config import MethodConfig

VERSION = "solar-pv-trading-fee-payment/1.0.0"
MAX_SOURCE_BYTES = 64 * 1024


@lru_cache(maxsize=1)
def _schema():
    path = Path(__file__).with_name("schema") / "trading-fee-payment.schema.json"
    schema = loads(path.read_bytes(), max_bytes=MAX_SOURCE_BYTES)
    if schema.get("$id") != VERSION:
        raise ContractError("TRADING_FEE_SOURCE_SCHEMA_VERSION")
    return schema


def trading_fee_payment_schema():
    return deepcopy(_schema())


@dataclass(frozen=True, slots=True)
class ValidatedTradingFeePayment:
    contract: dict
    source_sha256: str
    contract_hash: str
    payment_fractions: dict[str, Decimal]


def validate_trading_fee_payment(raw, *, exported, methods, settlement, scenario_id="BASE"):
    """Bind exactly the raw JSON bytes to this sealed 3C and current project."""
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_SOURCE_BYTES:
        raise ContractError("TRADING_FEE_SOURCE_BYTES_REQUIRED")
    contract = loads(raw, max_bytes=MAX_SOURCE_BYTES)
    exact_json_numbers(contract)
    if not isinstance(contract, dict) or next(StrictValidator(_schema()).iter_errors(contract), None):
        raise ContractError("TRADING_FEE_SOURCE_SCHEMA")
    config = methods if isinstance(methods, MethodConfig) else MethodConfig.from_dict(methods)
    if config.data_mode != "SYNTHETIC":
        raise ContractError("TRADING_FEE_SOURCE_SYNTHETIC_ONLY")
    binding = contract["binding"]
    values = exported["project"]["values"]
    datasets = settlement.get("source_snapshot", {}).get("datasets", {})
    d3_hash = datasets.get("content_hash")
    if not d3_hash:
        raise ContractError("TRADING_FEE_SOURCE_D3_BINDING_REQUIRED")
    expected = {
        "project_id": exported["project"]["project_id"],
        "pv_type": exported["project"]["pv_type"],
        "currency": values["project.currency"]["value"],
        "scenario_id": scenario_id,
        "evaluation_years": values["project.evaluation_years"]["value"],
        "phase2_input_hash": exported["input_hash"],
        "phase2_source_snapshot_id": exported["source_snapshot_id"],
        "method_config_hash": config.hash,
        "d3_content_hash": d3_hash,
        "phase3c_result_hash": settlement["result_hash"],
        "fee_treatment": config.require("settlement.fee_treatment"),
    }
    if settlement.get("boundaries", {}).get("SETTLEMENT", {}).get("fee_treatment") != "SEPARATE_LEDGER":
        raise ContractError("TRADING_FEE_SOURCE_SETTLEMENT_CONFLICT")
    for key, expected_value in expected.items():
        if binding[key] != expected_value:
            raise ContractError("TRADING_FEE_SOURCE_BINDING_MISMATCH", key)
    periods = [f"OPERATING_YEAR_{year}" for year in range(1, int(expected["evaluation_years"]) + 1)]
    annual = contract["payment"]["annual"]
    if [row["period"] for row in annual] != periods:
        raise ContractError("TRADING_FEE_SOURCE_PERIOD_MISMATCH")
    for key in ("source_reference", "source_location"):
        _source_reference(contract["source"][key])
    return ValidatedTradingFeePayment(
        contract=deepcopy(contract),
        source_sha256=sha256(raw).hexdigest(),
        contract_hash=digest(contract),
        payment_fractions={row["period"]: Decimal(row["payment_fraction"]) for row in annual},
    )
