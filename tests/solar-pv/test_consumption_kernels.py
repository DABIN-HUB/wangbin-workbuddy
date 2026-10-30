"""Independent SYNTHETIC numerical checks for the nine Phase 3C kernels."""
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
from importlib import import_module, util

import pytest

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.calculation.execution_registry import _planned_module
from wangbin_solar_pv.errors import ContractError

D = Decimal
MODULE = "wangbin_solar_pv.calculation.consumption"


def evaluate(formula_id, values, options=None):
    # An absent implementation fails an assertion, not test collection.
    assert util.find_spec(MODULE) is not None, "Phase 3C consumption kernel is missing"
    return import_module(MODULE).evaluate(formula_id, values, options)


@pytest.mark.parametrize("available,load,expected", [
    ("100.25", "60.125", "60.125"),
    ("40.125", "60.125", "40.125"),
    ("0", "100", "0"),
    ("100", "0", "0"),
    ("100", "100", "100"),
])
def test_self_consumption_uses_interval_minimum(available, load, expected):
    result = evaluate("F-SELF-CONSUMPTION", {
        "energy.available_kwh": D(available), "load.interval_kwh": D(load),
    })
    assert result["status"] == "CALCULATED"
    assert result["value"] == D(expected)
    assert isinstance(result["value"], D)
    assert result["reason"] is None


@pytest.mark.parametrize("available,self_kwh,limit,expected", [
    ("100", "60", "30", "30"),
    ("100", "60", "80", "40"),
    ("100", "100", "80", "0"),
    ("100", "0", "80", "80"),
    ("100", "60", "0", "0"),
    ("0", "0", "80", "0"),
])
def test_export_is_bounded_by_surplus_and_explicit_interval_limit(available, self_kwh, limit, expected):
    result = evaluate("F-EXPORTED-ENERGY", {
        "energy.available_kwh": D(available),
        "consumption.self_kwh": D(self_kwh),
        "grid.export_limit_kwh": D(limit),
    })
    assert result["value"] == D(expected)


@pytest.mark.parametrize("self_kwh,export,expected", [
    ("60.125", "30.100", "10.025"),
    ("100.25", "0", "0"),
    ("0", "0", "100.25"),
])
def test_curtailment_is_exact_unallocated_energy(self_kwh, export, expected):
    assert evaluate("F-CURTAILED-ENERGY", {
        "energy.available_kwh": D("100.25"),
        "consumption.self_kwh": D(self_kwh),
        "consumption.export_kwh": D(export),
    })["value"] == D(expected)


@pytest.mark.parametrize("curtailed,expected", [("10", "0"), ("9.9", "0.1"), ("10.1", "-0.1")])
def test_energy_balance_returns_signed_diagnostic_without_clamping(curtailed, expected):
    assert evaluate("F-ENERGY-BALANCE", {
        "energy.available_kwh": D("100"),
        "consumption.self_kwh": D("60"),
        "consumption.export_kwh": D("30"),
        "consumption.curtailed_kwh": D(curtailed),
    })["value"] == D(expected)


@pytest.mark.parametrize("formula_id,values", [
    ("F-EXPORTED-ENERGY", {"energy.available_kwh": D("100"), "consumption.self_kwh": D("100.01"), "grid.export_limit_kwh": D("30")}),
    ("F-CURTAILED-ENERGY", {"energy.available_kwh": D("100"), "consumption.self_kwh": D("60"), "consumption.export_kwh": D("40.01")}),
])
def test_overallocation_is_rejected_not_hidden_by_max_zero(formula_id, values):
    with pytest.raises(ContractError, match="ENERGY_ALLOCATION_EXCEEDS_AVAILABLE"):
        evaluate(formula_id, values)


# Fixed independent inputs/answers; no production result generates an expectation.
CASES = {
    "F-SELF-CONSUMPTION": ({"energy.available_kwh": D("100"), "load.interval_kwh": D("60")}, D("60")),
    "F-EXPORTED-ENERGY": ({"energy.available_kwh": D("100"), "consumption.self_kwh": D("60"), "grid.export_limit_kwh": D("30")}, D("30")),
    "F-CURTAILED-ENERGY": ({"energy.available_kwh": D("100"), "consumption.self_kwh": D("60"), "consumption.export_kwh": D("30")}, D("10")),
    "F-ENERGY-BALANCE": ({"energy.available_kwh": D("100"), "consumption.self_kwh": D("60"), "consumption.export_kwh": D("30"), "consumption.curtailed_kwh": D("10")}, D("0")),
    "F-DELIVERED-ENERGY": ({
        "consumption.self_kwh": {"t1": D("60"), "t2": D("20")},
        "consumption.export_kwh": {"t2": D("0"), "t1": D("30")},
        "time.operating_interval_ids": ["t1", "t2"],
    }, D("110")),
    "F-SELF-CONSUMPTION-RATIO": ({
        "consumption.self_kwh": {"t1": D("60"), "t2": D("20")},
        "energy.delivered_annual_kwh": D("110"),
        "time.operating_interval_ids": ["t1", "t2"],
    }, Fraction(8, 11)),
    "F-LOAD-COVERAGE-RATIO": ({
        "consumption.self_kwh": {"t1": D("60"), "t2": D("20")},
        "load.interval_kwh": {"t2": D("80"), "t1": D("80")},
        "time.operating_interval_ids": ["t1", "t2"],
    }, D("0.5")),
    "F-ENERGY-REVENUE": ({
        "consumption.self_kwh": {"t1": D("60"), "t2": D("20")},
        "tariff.avoidable_price": {"t2": D("1.2"), "t1": D("0.8")},
        "consumption.export_kwh": {"t1": D("30"), "t2": D("0")},
        "tariff.export_price": {"t2": D("-0.1"), "t1": D("0.4")},
        "revenue.other_benefit": D("5"),
        "time.settlement_interval_ids": ["t1", "t2"],
    }, D("89")),
    "F-PPA-REVENUE": ({
        "consumption.host_delivery_kwh": {"t1": D("60"), "t2": D("20")},
        "tariff.ppa_price": {"t2": D("0.6"), "t1": D("0.5")},
        "consumption.export_kwh": {"t1": D("30"), "t2": D("0")},
        "tariff.export_price": {"t2": D("-0.1"), "t1": D("0.4")},
        "revenue.other_benefit": D("5"),
        "time.settlement_interval_ids": ["t1", "t2"],
    }, D("59")),
}
ANNUAL = ("F-DELIVERED-ENERGY", "F-SELF-CONSUMPTION-RATIO", "F-LOAD-COVERAGE-RATIO")


def reference_decimal(value, precision=80):
    with localcontext() as ctx:
        ctx.prec = precision
        if isinstance(value, Fraction):
            return D(value.numerator) / D(value.denominator)
        return value


@pytest.mark.parametrize("formula_id", ANNUAL)
def test_annual_energy_and_ratios_use_independent_reference(formula_id):
    values, expected = CASES[formula_id]
    result = evaluate(formula_id, deepcopy(values))
    assert result["status"] == "CALCULATED"
    assert result["value"] == reference_decimal(expected)


@pytest.mark.parametrize("formula_id", ANNUAL[1:])
@pytest.mark.parametrize("positive_numerator", [False, True])
def test_zero_denominator_is_undefined_even_with_positive_numerator(formula_id, positive_numerator):
    values = deepcopy(CASES[formula_id][0])
    values["consumption.self_kwh"] = {"t1": D(int(positive_numerator)), "t2": D("0")}
    if formula_id == "F-SELF-CONSUMPTION-RATIO":
        values["energy.delivered_annual_kwh"] = D("0")
    else:
        values["load.interval_kwh"] = {"t1": D("0"), "t2": D("0")}
    result = evaluate(formula_id, values)
    assert result["status"] == "UNDEFINED"
    assert result["reason"] == "ZERO_DENOMINATOR"
    assert result["value"] is None


@pytest.mark.parametrize("formula_id", ANNUAL[1:])
def test_overallocated_ratio_cannot_exceed_one(formula_id):
    values = deepcopy(CASES[formula_id][0])
    values["consumption.self_kwh"]["t1"] = D("200")
    with pytest.raises(ContractError, match="ENERGY_ALLOCATION"):
        evaluate(formula_id, values)


def test_load_coverage_rejects_cross_interval_overallocation_hidden_by_annual_total():
    values = deepcopy(CASES["F-LOAD-COVERAGE-RATIO"][0])
    values["consumption.self_kwh"] = {"t1": D("90"), "t2": D("0")}
    with pytest.raises(ContractError, match="ENERGY_ALLOCATION_EXCEEDS_LOAD"):
        evaluate("F-LOAD-COVERAGE-RATIO", values)


REVENUES = ("F-ENERGY-REVENUE", "F-PPA-REVENUE")


@pytest.mark.parametrize("formula_id,expected",[("F-ENERGY-REVENUE",D(79)),("F-PPA-REVENUE",D(49))])
def test_signed_other_benefit_follows_unrestricted_frozen_amount_domain(formula_id,expected):
    # The frozen revenue.other_items.amount has no nonnegative minimum.
    # An explicit contract adjustment is not electrical energy or a tax model.
    values = deepcopy(CASES[formula_id][0])
    values["revenue.other_benefit"] = D(-5)
    assert evaluate(formula_id,values)["value"] == expected


@pytest.mark.parametrize("formula_id", REVENUES)
def test_revenue_reference_does_not_mix_owner_and_ppa_benefits(formula_id):
    values, expected = CASES[formula_id]
    result = evaluate(formula_id, deepcopy(values))
    assert result["status"] == "CALCULATED"
    assert result["value"] == expected


@pytest.mark.parametrize("formula_id", REVENUES)
@pytest.mark.parametrize("price_field", ["local", "tariff.export_price"])
def test_negative_prices_are_not_clamped_and_can_produce_negative_income(formula_id, price_field):
    values = deepcopy(CASES[formula_id][0])
    local = "tariff.avoidable_price" if formula_id == "F-ENERGY-REVENUE" else "tariff.ppa_price"
    field = local if price_field == "local" else price_field
    for key, value in values.items():
        if isinstance(value, dict):
            values[key] = {"t1": D("0"), "t2": D("0")}
    energy_field = ("consumption.self_kwh" if formula_id == "F-ENERGY-REVENUE" else "consumption.host_delivery_kwh") if price_field == "local" else "consumption.export_kwh"
    values[energy_field]["t1"] = D("10")
    values[field]["t1"] = D("-0.25")
    values["revenue.other_benefit"] = D("0")
    assert evaluate(formula_id, values)["value"] == D("-2.50")


@pytest.mark.parametrize("formula_id", REVENUES)
def test_revenue_keeps_subcent_amounts_and_matches_independent_rational_sum(formula_id):
    values = deepcopy(CASES[formula_id][0])
    # Mutually distinct, non-cent inputs also detect index/order mixups.
    for key, value in values.items():
        if isinstance(value, dict):
            values[key] = {"t1": D("0.0013"), "t2": D("0.0027")}
    first_energy = "consumption.self_kwh" if formula_id == "F-ENERGY-REVENUE" else "consumption.host_delivery_kwh"
    first_price = "tariff.avoidable_price" if formula_id == "F-ENERGY-REVENUE" else "tariff.ppa_price"
    values[first_price] = {"t2": D("0.987654321"), "t1": D("0.123456789")}
    values["tariff.export_price"] = {"t1": D("-0.3333"), "t2": D("0.2222")}
    values["revenue.other_benefit"] = D("0.000001")
    expected = Fraction(values["revenue.other_benefit"])
    for item in ("t1", "t2"):
        expected += Fraction(values[first_energy][item]) * Fraction(values[first_price][item])
        expected += Fraction(values["consumption.export_kwh"][item]) * Fraction(values["tariff.export_price"][item])
    assert evaluate(formula_id, values)["value"] == reference_decimal(expected)


FIELDS = [(fid, field) for fid, (values, _) in CASES.items() for field in values]
NUMERIC_FIELDS = [(fid, field) for fid, (values, _) in CASES.items() for field, value in values.items() if not isinstance(value, (list, tuple))]
INDEXED_FIELDS = [(fid, field) for fid, (values, _) in CASES.items() for field, value in values.items() if isinstance(value, dict)]


@pytest.fixture(scope="module")
def catalog():
    return Catalog()


def test_registry_and_all_frozen_formula_fields_are_exact(catalog):
    module = import_module(MODULE)
    planned = {fid for fid in catalog.formulas if _planned_module(fid) == "consumption"}
    assert len(module.FORMULA_IDS) == len(set(module.FORMULA_IDS)) == 9
    assert set(module.FORMULA_IDS) == set(CASES) == planned
    for fid, (values, _) in CASES.items():
        assert set(values) == set(catalog.formulas[fid]["input_field_ids"])
        for field in values:
            binding = catalog.bindings[field]
            assert binding["formula_field_id"] == field
            assert fid in binding["consumer_formula_ids"]


@pytest.mark.parametrize("formula_id,field", FIELDS)
@pytest.mark.parametrize("missing_mode", ["absent", "null"])
def test_every_missing_frozen_input_blocks_without_zero_fill(formula_id, field, missing_mode):
    values = deepcopy(CASES[formula_id][0])
    if missing_mode == "absent":
        del values[field]
    else:
        values[field] = None
    result = evaluate(formula_id, values)
    assert result["status"] == "BLOCKED_MISSING_INPUT"
    assert result["reason"] == "BLOCKED_MISSING_INPUT"
    assert result["value"] is None
    assert field in result["details"]["missing_field_ids"]


@pytest.mark.parametrize("formula_id,field", INDEXED_FIELDS)
def test_nested_missing_input_is_not_zero_even_for_zero_energy(formula_id, field):
    values = deepcopy(CASES[formula_id][0])
    values[field]["t2"] = None
    result = evaluate(formula_id, values)
    assert result["status"] == "BLOCKED_MISSING_INPUT"
    assert result["value"] is None
    assert field in result["details"]["missing_field_ids"]


@pytest.mark.parametrize("formula_id", list(CASES))
def test_extra_formula_fields_are_not_silently_accepted(formula_id):
    values = deepcopy(CASES[formula_id][0])
    # In particular, investor income cannot accept host avoided-cost benefit.
    values["tariff.avoidable_price" if formula_id == "F-PPA-REVENUE" else "unknown.field"] = D("999")
    with pytest.raises(ContractError, match="FORMULA_VALUES_KEYS"):
        evaluate(formula_id, values)


@pytest.mark.parametrize("formula_id", list(CASES))
def test_only_explicit_boolean_false_marks_not_applicable(formula_id):
    result = evaluate(formula_id, {}, {"applicable": False})
    assert result["status"] == "NOT_APPLICABLE"
    assert result["value"] is None
    assert result["reason"] == "EXPLICITLY_NOT_APPLICABLE"


@pytest.mark.parametrize("formula_id,field", NUMERIC_FIELDS)
@pytest.mark.parametrize("invalid", [True, 1.25, "1.25", D("NaN"), D("Infinity"), D("-Infinity")])
def test_exact_finite_numeric_contract_is_required_in_every_operand(formula_id, field, invalid):
    values = deepcopy(CASES[formula_id][0])
    if isinstance(values[field], dict):
        values[field]["t2"] = invalid
    else:
        values[field] = invalid
    with pytest.raises(ContractError, match="FINITE_EXACT_NUMBER_REQUIRED"):
        evaluate(formula_id, values)


@pytest.mark.parametrize("formula_id,field", [(fid, field) for fid, field in NUMERIC_FIELDS if field.startswith(("energy.","consumption.","load.","grid."))])
def test_electricity_operands_cannot_be_negative(formula_id, field):
    values = deepcopy(CASES[formula_id][0])
    if isinstance(values[field], dict):
        values[field]["t2"] = D("-0.01")
    else:
        values[field] = D("-0.01")
    with pytest.raises(ContractError, match="NEGATIVE_INPUT"):
        evaluate(formula_id, values)


@pytest.mark.parametrize("formula_id,field", INDEXED_FIELDS)
@pytest.mark.parametrize("mode", ["missing", "extra", "wrong_same_length"])
def test_every_indexed_operand_has_exact_declared_members(formula_id, field, mode):
    values = deepcopy(CASES[formula_id][0])
    if mode != "extra":
        del values[field]["t2"]
    if mode != "missing":
        values[field]["t3"] = D("0")
    with pytest.raises(ContractError, match="INDEX_SET_MISMATCH"):
        evaluate(formula_id, values)


@pytest.mark.parametrize("formula_id,field", INDEXED_FIELDS)
@pytest.mark.parametrize("bad_mapping", [[D("1"), D("2")], D("2"), {1: D("1"), "t2": D("2")}, {"": D("1"), "t2": D("2")}])
def test_indexed_values_are_stable_id_maps_not_positional_arrays(formula_id, field, bad_mapping):
    values = deepcopy(CASES[formula_id][0])
    values[field] = bad_mapping
    with pytest.raises(ContractError, match="INDEXED_DECIMAL_MAPPING_REQUIRED|STABLE_INDEX_ID_REQUIRED"):
        evaluate(formula_id, values)


@pytest.mark.parametrize("formula_id", ANNUAL + REVENUES)
@pytest.mark.parametrize("bad_ids,code", [
    (["t1", "t1"], "DUPLICATE_INDEX_ID"),
    (["t1", ""], "STABLE_INDEX_ID_REQUIRED"),
    (["t1", 2], "STABLE_INDEX_ID_REQUIRED"),
    ("t1,t2", "INDEX_IDS_SEQUENCE_REQUIRED"),
    ({"t1", "t2"}, "INDEX_IDS_SEQUENCE_REQUIRED"),
])
def test_declared_sets_reject_duplicates_unstable_ids_and_nonsequences(formula_id, bad_ids, code):
    values = deepcopy(CASES[formula_id][0])
    ids_field = "time.settlement_interval_ids" if formula_id in REVENUES else "time.operating_interval_ids"
    values[ids_field] = bad_ids
    with pytest.raises(ContractError, match=code):
        evaluate(formula_id, values)


@pytest.mark.parametrize("formula_id", ANNUAL + REVENUES)
def test_explicit_empty_sets_are_not_confused_with_missing_sets(formula_id):
    values = deepcopy(CASES[formula_id][0])
    for field, value in values.items():
        if isinstance(value, dict):
            values[field] = {}
        elif isinstance(value, list):
            values[field] = []
    result = evaluate(formula_id, values)
    if formula_id == "F-LOAD-COVERAGE-RATIO":
        assert result["status"] == "UNDEFINED"
        assert result["reason"] == "ZERO_DENOMINATOR"
        assert result["value"] is None
    else:
        expected = D("0") if formula_id not in REVENUES else D("5")
        assert result["status"] == "CALCULATED"
        assert result["value"] == expected


@pytest.mark.parametrize("formula_id", list(CASES))
def test_zero_numerator_boundary_and_inputs_are_not_mutated(formula_id):
    values = deepcopy(CASES[formula_id][0])
    if formula_id in ANNUAL[1:]:
        values["consumption.self_kwh"] = {"t1": D("0"), "t2": D("0")}
    else:
        for field, value in values.items():
            if isinstance(value, dict):
                values[field] = {item: D("0") for item in value}
            elif isinstance(value, D):
                values[field] = D("0")
    before = deepcopy(values)
    result = evaluate(formula_id, values)
    assert result["status"] == "CALCULATED"
    assert result["value"] == D("0")
    assert values == before


@pytest.mark.parametrize("formula_id", list(CASES))
def test_integer_operands_are_accepted_without_binary_float_conversion(formula_id):
    values, expected = deepcopy(CASES[formula_id])
    # Prices remain Decimal; integral energy and other-benefit inputs become int.
    for field, value in values.items():
        if field.startswith("tariff."):
            continue
        if isinstance(value, dict):
            values[field] = {item: int(amount) for item, amount in value.items()}
        elif isinstance(value, D):
            values[field] = int(value)
    result = evaluate(formula_id, values)
    assert result["value"] == reference_decimal(expected)
    assert isinstance(result["value"], D)


@pytest.mark.parametrize("options,code", [
    ([], "OPTIONS_MAPPING_REQUIRED"),
    ({"applicable": 0}, "APPLICABILITY_BOOLEAN_REQUIRED"),
    ({"precision_digits": True}, "INTEGER_DOMAIN"),
    ({"precision_digits": 33}, "INTEGER_DOMAIN"),
    ({"precision_digits": 1025}, "INTEGER_DOMAIN"),
    ({"unknown": True}, "OPTIONS_KEYS"),
    ({"index_ids": []}, "INDEX_IDS_MAPPING_REQUIRED"),
    ({"index_ids": {1: []}}, "INDEX_FIELD_ID_REQUIRED"),
    ({"index_ids": {"a": ["x", "x"]}}, "DUPLICATE_INDEX_ID"),
])
def test_options_follow_engineering_contract(options, code):
    with pytest.raises(ContractError, match=code):
        evaluate("F-SELF-CONSUMPTION", CASES["F-SELF-CONSUMPTION"][0], options)


@pytest.mark.parametrize("formula_id", ["F-UNKNOWN", None, [], True])
def test_unknown_formula_id_has_stable_error(formula_id):
    with pytest.raises(ContractError, match="UNKNOWN_FORMULA"):
        evaluate(formula_id, {})


@pytest.mark.parametrize("values", [[], True, D("0"), None])
def test_values_must_be_a_mapping(values):
    with pytest.raises(ContractError, match="FORMULA_VALUES_MAPPING_REQUIRED"):
        evaluate("F-SELF-CONSUMPTION", values)


@pytest.mark.parametrize("precision", [34, 80, 120])
def test_declared_decimal_precision_is_local_and_no_cents_are_rounded(precision):
    values = deepcopy(CASES["F-SELF-CONSUMPTION-RATIO"][0])
    expected = reference_decimal(Fraction(8, 11), precision)
    with localcontext() as outer:
        outer.prec = 7
        outer.rounding = "ROUND_DOWN"
        before_flags = dict(outer.flags)
        result = evaluate("F-SELF-CONSUMPTION-RATIO", values, {"precision_digits": precision})
        assert outer.prec == 7
        assert outer.rounding == "ROUND_DOWN"
        assert outer.flags == before_flags
    assert result["value"] == expected
    assert result["details"]["precision_digits"] == precision


@pytest.mark.parametrize("formula_id", ANNUAL[1:])
def test_ratio_one_boundary_uses_the_frozen_denominator(formula_id):
    values = deepcopy(CASES[formula_id][0])
    if formula_id == "F-SELF-CONSUMPTION-RATIO":
        values["energy.delivered_annual_kwh"] = D("80")
    else:
        values["load.interval_kwh"] = {"t1": D("60"), "t2": D("20")}
    assert evaluate(formula_id, values)["value"] == D("1")


@pytest.mark.parametrize("formula_id", ANNUAL + REVENUES)
def test_declared_tuple_order_and_mapping_insertion_order_do_not_change_identity(formula_id):
    values, expected = deepcopy(CASES[formula_id])
    ids_field = "time.settlement_interval_ids" if formula_id in REVENUES else "time.operating_interval_ids"
    values[ids_field] = ("t2", "t1")
    assert evaluate(formula_id, values)["value"] == reference_decimal(expected)


def test_options_index_ids_cannot_override_a_frozen_operating_set():
    values = deepcopy(CASES["F-DELIVERED-ENERGY"][0])
    values["consumption.self_kwh"] = {"t1": D("60")}
    with pytest.raises(ContractError, match="INDEX_SET_MISMATCH"):
        evaluate("F-DELIVERED-ENERGY", values, {"index_ids": {"consumption.self_kwh": ["t1"]}})


@pytest.mark.parametrize("formula_id", REVENUES)
def test_zero_export_still_requires_explicit_finite_settlement_price(formula_id):
    values = deepcopy(CASES[formula_id][0])
    values["consumption.export_kwh"] = {"t1": D("0"), "t2": D("0")}
    values["tariff.export_price"]["t1"] = None
    result = evaluate(formula_id, values)
    assert result["status"] == "BLOCKED_MISSING_INPUT"
    assert result["value"] is None


def test_interval_minimum_cannot_be_replaced_by_annual_minimum():
    # Opposite generation/load periods: annual totals alone invent consumption.
    first = evaluate("F-SELF-CONSUMPTION", {"energy.available_kwh": D("100"), "load.interval_kwh": D("0")})
    second = evaluate("F-SELF-CONSUMPTION", {"energy.available_kwh": D("0"), "load.interval_kwh": D("100")})
    assert first["value"] == D("0")
    assert second["value"] == D("0")
