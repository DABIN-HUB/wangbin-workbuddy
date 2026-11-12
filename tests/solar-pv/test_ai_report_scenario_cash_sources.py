"""Source-policy boundary checks; full economic comparison remains blocked."""
from copy import deepcopy
from pathlib import Path

import pytest

from wangbin_solar_pv.calculation.method_config import MethodConfig
from wangbin_solar_pv.calculation.scenario_cash_sources import rebind_opex_fee
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.serialization import loads, dumps

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module", params=["industrial_rooftop", "utility_scale_ground"])
def case(request):
    path = ROOT / "reports/solar-pv/phase7l-r2-full-cases" / request.param
    export = loads((path / "input.json").read_bytes())
    settlement = loads((path / "project/3c/result.json").read_bytes())
    methods = MethodConfig.from_dict(loads((path / "methods.json").read_bytes()))
    raw = (ROOT / "reports/solar-pv/phase7l-r2-trading-fee-synthetic-source-v1" /
           request.param / "trading-fee-payment.json").read_bytes()
    return export, settlement, methods, raw


def test_rule_is_rebound_not_cash_or_original_bytes(case):
    original, settlement, methods, raw = case
    candidate = deepcopy(original)
    candidate["input_hash"] = "a" * 64
    candidate["source_snapshot_id"] = "sources-" + "b" * 64
    candidate["normalized_inputs"]["opex.items"][0]["fields"]["opex.items.base_amount"] *= 2
    rebound, receipt = rebind_opex_fee(raw, original, candidate, methods, settlement, settlement, "PESSIMISTIC")
    old, new = loads(raw), loads(rebound)
    assert new["payment"] == old["payment"]
    assert new["source"] == old["source"]
    assert new["binding"]["phase2_input_hash"] == candidate["input_hash"]
    assert new["binding"]["scenario_id"] == "PESSIMISTIC"
    assert receipt["original_raw_sha256"] != receipt["derived_raw_sha256"]
    assert "cash_paid" not in dumps(new)


@pytest.mark.parametrize("field,value", [("project.evaluation_years", 1),
    ("project.cashflow_tax_basis", "pre_tax"), ("finance.project_discount_rate", "0.123"),
    ("project.currency", "USD"), ("system.dc_capacity", 1)])
def test_changed_policy_scope_rejected(case, field, value):
    original, settlement, methods, raw = case
    candidate = deepcopy(original)
    candidate["normalized_inputs"][field] = value
    with pytest.raises(ContractError, match="SCENARIO_CASH_SOURCE_SCOPE_CHANGED"):
        rebind_opex_fee(raw, original, candidate, methods, settlement, settlement, "PESSIMISTIC")


@pytest.mark.parametrize("mutation", ["unauthorized", "missing", "period", "identity", "fee"])
def test_invalid_original_source_never_rebound(case, mutation):
    original, settlement, methods, raw = case
    source = loads(raw)
    if mutation == "unauthorized": source["source"]["license_status"] = "UNKNOWN"
    elif mutation == "missing": raw = None
    elif mutation == "period": source["payment"]["annual"].pop()
    elif mutation == "identity": source["binding"]["phase3c_result_hash"] = "0" * 64
    elif mutation == "fee": source["binding"]["fee_treatment"] = "NET_REVENUE"
    if mutation != "missing": raw = dumps(source).encode()
    with pytest.raises(ContractError):
        rebind_opex_fee(raw, original, original, methods, settlement, settlement, "PESSIMISTIC")
