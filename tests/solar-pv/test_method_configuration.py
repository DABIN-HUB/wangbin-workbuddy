"""SYNTHETIC D2 controls: provenance, bounds and mutually consistent methods."""
from copy import deepcopy
from decimal import Decimal

import pytest

from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.calculation.method_config import MethodConfig, make_parameter, method_schema, PARAMETERS
from wangbin_solar_pv.schemas import StrictValidator


def configuration(values):
    return {"schema_version": "solar-pv-method-config/1.0.0", "config_id": "SYNTHETIC-ONLY", "data_mode": "SYNTHETIC", "pv_types": ["industrial_rooftop"], "parameters": {
        key: make_parameter(key, value, source_id="SYNTHETIC:method", source_reference="SYNTHETIC explicit unit and model boundary", status="ASSUMED", source_kind="SYNTHETIC", pv_types=["industrial_rooftop"])
        for key, value in values.items()}}


def test_all_control_definitions_are_typed_explained_and_have_no_numeric_default():
    StrictValidator.check_schema(method_schema())
    for definition in PARAMETERS.values():
        assert definition["value_type"] in {"number", "integer", "string", "boolean", "array"}
        assert definition["meaning_zh"] and definition["english_name"] and definition["boundary_id"]
        assert "default" not in definition and "default" not in definition["constraints"]


@pytest.mark.parametrize("low,high", [("irr.minimum_rate", "irr.maximum_rate"), ("break_even.minimum_price", "break_even.maximum_price"), ("thermal.minimum_cell_temperature", "thermal.maximum_cell_temperature")])
@pytest.mark.parametrize("minimum,maximum", [(1, 1), (2, 1)])
def test_reversed_and_zero_width_search_or_temperature_domains_are_not_calculations(low, high, minimum, maximum):
    with pytest.raises(ContractError, match="METHOD_PARAMETER_ORDER"):
        MethodConfig.from_dict(configuration({low: minimum, high: maximum}))


@pytest.mark.parametrize("parameter,value", [("irr.minimum_rate", -1), ("precision.digits", 33), ("precision.digits", 1025), ("precision.abs_tolerance", 0), ("constants.stc_irradiance", 0), ("cash.opening_cash", -1), ("cash.collection_fractions", [Decimal("1.01")]), ("debt.interest_payment_fractions", [-1]), ("tax.loss_usage_fraction", 2)])
def test_invalid_critical_parameters_are_rejected_by_strict_schema(parameter, value):
    with pytest.raises(ContractError, match="METHOD_CONFIG_SCHEMA"):
        MethodConfig.from_dict(configuration({parameter: value}))


def test_zero_cash_is_preserved_only_when_explicitly_provided():
    provided = MethodConfig.from_dict(configuration({"cash.opening_cash": 0}))
    missing = MethodConfig.from_dict(configuration({}))
    assert provided.require("cash.opening_cash") == 0
    with pytest.raises(ContractError, match="BLOCKED_METHOD_REVIEW"):
        missing.require("cash.opening_cash")
    assert provided.hash != missing.hash


def test_auxiliary_station_power_is_typed_explicit_and_missing_is_blocked():
    provided = MethodConfig.from_dict(configuration({"energy.auxiliary_kw": Decimal("2.5")}))
    assert provided.require("energy.auxiliary_kw") == Decimal("2.5")
    missing = MethodConfig.from_dict(configuration({}))
    with pytest.raises(ContractError, match="BLOCKED_METHOD_REVIEW"):
        missing.require("energy.auxiliary_kw")
    assert provided.hash != missing.hash


def test_auxiliary_station_power_rejects_negative_and_float_values():
    with pytest.raises(ContractError, match="METHOD_CONFIG_SCHEMA"):
        MethodConfig.from_dict(configuration({"energy.auxiliary_kw": Decimal("-0.1")}))
    with pytest.raises(ContractError, match="EXACT_JSON_NUMBER_REQUIRED"):
        MethodConfig.from_dict(configuration({"energy.auxiliary_kw": 2.5}))


@pytest.mark.parametrize("mutate", ["synthetic_verified", "synthetic_real", "missing_review", "denied", "wrong_category", "unknown_parameter", "extra_root", "future_version", "private_source_path", "credential_url"])
def test_source_states_category_and_version_never_bypass_method_authorization(mutate):
    data = configuration({"precision.digits": 80})
    record = data["parameters"]["precision.digits"]
    if mutate == "synthetic_verified": record["status"] = "VERIFIED"
    elif mutate == "synthetic_real": data["data_mode"] = "DECLARED_INPUTS"
    elif mutate == "missing_review": record.update(status="VERIFIED", source_kind="USER_PROVIDED", license_status="AUTHORIZED")
    elif mutate == "denied": record["license_status"] = "DENIED"
    elif mutate == "wrong_category": record["pv_types"] = ["utility_scale_ground"]
    elif mutate == "unknown_parameter": data["parameters"]["second_dictionary.fake_field"] = deepcopy(record)
    elif mutate == "extra_root": data["numerical_default"] = 0
    elif mutate == "future_version": data["schema_version"] = "solar-pv-method-config/99.0.0"
    elif mutate == "private_source_path": record["source_reference"] = "C:/SYNTHETIC/private/material.pdf"
    else: record["source_reference"] = "https://example.invalid/data?access_token=SYNTHETIC-NOT-A-CREDENTIAL"
    with pytest.raises(ContractError):
        MethodConfig.from_dict(data)


def test_unverified_method_is_valid_pending_record_but_not_executable():
    data = configuration({"precision.digits": 80})
    data["parameters"]["precision.digits"].update(status="UNVERIFIED", source_kind="USER_PROVIDED")
    config = MethodConfig.from_dict(data)
    with pytest.raises(ContractError, match="BLOCKED_METHOD_REVIEW"):
        config.require("precision.digits")
