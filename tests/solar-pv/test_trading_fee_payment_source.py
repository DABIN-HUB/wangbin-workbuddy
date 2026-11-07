"""Trading-fee source identity, strict scope and annual cash bridge."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.calculation.financial_ledger import calculate_financial_ledger
from wangbin_solar_pv.calculation.method_config import MethodConfig
from wangbin_solar_pv.calculation.phase3e import _ledger_vectors
from wangbin_solar_pv.calculation.trading_fee_payment import validate_trading_fee_payment
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.serialization import dumps, loads

_ROOT = Path(__file__).resolve().parents[2] / "reports/solar-pv"


@pytest.fixture(scope="module", params=("industrial_rooftop", "utility_scale_ground"))
def case(request):
    kind = request.param
    sealed = _ROOT / "phase7l-r2-full-cases" / kind
    source = _ROOT / "phase7l-r2-trading-fee-synthetic-source-v1" / kind / "trading-fee-payment.json"
    return (loads((sealed / "input.json").read_bytes()),
            loads((sealed / "methods.json").read_bytes()),
            loads((sealed / "project/3c/result.json").read_bytes()), source.read_bytes())


def _validate(case, raw=None, methods=None, settlement=None):
    exported, configured, upstream, source = case
    return validate_trading_fee_payment(source if raw is None else raw, exported=exported,
                                        methods=configured if methods is None else methods,
                                        settlement=upstream if settlement is None else settlement)


def _edited(case, path, value):
    source = loads(case[3])
    current = source
    for key in path[:-1]:
        current = current[key]
    current[path[-1]] = value
    return dumps(source).encode("utf-8")


def test_authorized_synthetic_source_binds_each_year_to_current_settlement(case):
    checked = _validate(case)
    assert checked.contract["source_status"] == "ASSUMED"
    assert checked.contract["payment_evidence"] is False
    assert len(checked.payment_fractions) == 25
    assert set(checked.payment_fractions.values()) == {Decimal(1)}
    assert checked.contract["binding"]["phase3c_result_hash"] == case[2]["result_hash"]


@pytest.mark.parametrize("path,value,code", [
    (("binding", "project_id"), "ANOTHER_PROJECT", "TRADING_FEE_SOURCE_BINDING_MISMATCH"),
    (("binding", "phase3c_result_hash"), "0" * 64, "TRADING_FEE_SOURCE_BINDING_MISMATCH"),
    (("binding", "currency"), "USD", "TRADING_FEE_SOURCE_BINDING_MISMATCH"),
    (("binding", "fee_category"), "OPERATIONS", "TRADING_FEE_SOURCE_SCHEMA"),
    (("binding", "fee_treatment"), "ALREADY_IN_PRICE", "TRADING_FEE_SOURCE_SCHEMA"),
    (("schema_version",), "2.0", "TRADING_FEE_SOURCE_SCHEMA"),
    (("payment", "opening_payable"), Decimal(1), "TRADING_FEE_SOURCE_SCHEMA"),
    (("payment", "historical_arrears"), Decimal(1), "TRADING_FEE_SOURCE_SCHEMA"),
    (("payment", "payment_rule"), "DELAYED", "TRADING_FEE_SOURCE_SCHEMA"),
    (("payment", "annual"), [], "TRADING_FEE_SOURCE_SCHEMA"),
])
def test_wrong_scope_or_unsupported_payment_is_rejected(case, path, value, code):
    with pytest.raises(ContractError, match=code):
        _validate(case, raw=_edited(case, path, value))


def test_missing_duplicate_and_non_one_years_are_rejected(case):
    source = loads(case[3])
    source["payment"]["annual"].pop(3)
    with pytest.raises(ContractError, match="TRADING_FEE_SOURCE_PERIOD_MISMATCH"):
        _validate(case, raw=dumps(source).encode())
    source = loads(case[3])
    source["payment"]["annual"][1]["period"] = "OPERATING_YEAR_1"
    with pytest.raises(ContractError, match="TRADING_FEE_SOURCE_SCHEMA|TRADING_FEE_SOURCE_PERIOD_MISMATCH"):
        _validate(case, raw=dumps(source).encode())
    source = loads(case[3])
    source["payment"]["annual"][0]["payment_fraction"] = Decimal("0.5")
    with pytest.raises(ContractError, match="TRADING_FEE_SOURCE_SCHEMA"):
        _validate(case, raw=dumps(source).encode())


def test_original_bytes_and_extra_fields_have_identity_or_contract_effect(case):
    checked = _validate(case)
    other = _validate(case, raw=case[3] + b"\n")
    assert checked.contract_hash == other.contract_hash
    assert checked.source_sha256 != other.source_sha256
    edited = loads(case[3])
    edited["source"]["unreviewed"] = "ignored?"
    with pytest.raises(ContractError, match="TRADING_FEE_SOURCE_SCHEMA"):
        _validate(case, raw=dumps(edited).encode())
    with pytest.raises(ContractError, match="DUPLICATE_JSON_KEY"):
        _validate(case, raw=case[3].replace(b'"payment_evidence": false,',
                                             b'"payment_evidence": false, "payment_evidence": false,', 1))


def test_net_settlement_cannot_accept_separate_payment_source(case):
    settlement = deepcopy(case[2])
    settlement["boundaries"]["SETTLEMENT"]["fee_treatment"] = "ALREADY_IN_PRICE"
    with pytest.raises(ContractError, match="TRADING_FEE_SOURCE_SETTLEMENT_CONFLICT"):
        _validate(case, settlement=settlement)


def test_same_year_full_payment_closes_each_annual_payable(case):
    exported, methods, settlement, raw = case
    financial = calculate_financial_ledger(exported, methods, settlement,
                                           trading_fee_source_bytes=raw)
    ledger = financial["evidence"]["financial-ledger"]
    source = ledger["trading_fee_payment"]
    assert source["raw_sha256"] == _validate(case).source_sha256
    assert financial["source_snapshot"]["trading_fee_payment"]["raw_sha256"] == source["raw_sha256"]
    assert financial["status"] == "CALCULATED_SYNTHETIC"
    vectors = _ledger_vectors(ledger["annual"])
    assert vectors["missing"] == {}
    assert ledger["annual"][0]["transaction_cost_payable_closing"] == 0
    for year, row in enumerate(ledger["annual"][1:], 1):
        fee = next(m for m in settlement["results"]["metrics"]
                   if m["metric_id"] == f"revenue.year.{year}")["details"]["ledger"]["transaction_cost"]
        assert row["transaction_cost_accrued"] == fee
        assert row["transaction_cost_cash_paid"] == fee
        assert row["transaction_cost_payable_opening"] == 0
        assert row["transaction_cost_payable_closing"] == 0
        assert row["transaction_cost_source_sha256"] == source["raw_sha256"]
        assert row["transaction_cost_payment_status"] == "SYNTHETIC_ASSUMED_SAME_YEAR"
        assert vectors["benefit"][year] == (row["revenue_cash_receipts"]
                                            + row["self_use_avoided_expenditure"] - fee)
        assert row["taxable_income_project"] is not None
    assert ledger["annual"][-1]["transaction_cost_payable_closing"] == 0
    rebound = calculate_financial_ledger(exported, methods, settlement,
                                          trading_fee_source_bytes=raw + b"\n")
    assert rebound["evidence"]["financial-ledger"]["annual"][1]["transaction_cost_cash_paid"] == ledger["annual"][1]["transaction_cost_cash_paid"]
    assert rebound["source_snapshot_id"] != financial["source_snapshot_id"]
    assert rebound["input_hash"] != financial["input_hash"]
    assert rebound["result_hash"] != financial["result_hash"]


def test_opex_fractions_do_not_change_fee_payment_under_explicit_source(case):
    exported, methods, settlement, raw = case
    changed = deepcopy(methods)
    changed["parameters"]["cash.opex_payment_fractions"]["value"][0] = Decimal(0)
    document = loads(raw)
    document["binding"]["method_config_hash"] = MethodConfig.from_dict(changed).hash
    rows = calculate_financial_ledger(exported, changed, settlement,
                                      trading_fee_source_bytes=dumps(document).encode())["evidence"]["financial-ledger"]["annual"]
    fee = next(m for m in settlement["results"]["metrics"]
               if m["metric_id"] == "revenue.year.1")["details"]["ledger"]["transaction_cost"]
    assert rows[1]["transaction_cost_cash_paid"] == fee
    assert rows[1]["opex_cash_paid"] == 0
    assert rows[1]["transaction_cost_payable_closing"] == 0
