from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from wangbin_solar_pv.calculation import engineering
from wangbin_solar_pv.errors import ContractError

D = Decimal


def _fraction(numerator, denominator):
    with localcontext() as ctx:
        ctx.prec = 80
        return D(numerator) / D(denominator)


def _case_values(**values):
    return values


CASES = {
    "F-DC-CAPACITY": {
        "values": _case_values(**{"equipment.module_count": 1200, "equipment.module_power_kwp": D("0.550")}),
        "expected": D("660.000"),
        "invalid_field": "equipment.module_power_kwp",
        "boundary": (_case_values(**{"equipment.module_count": 0, "equipment.module_power_kwp": D("0.550")}), D("0")),
    },
    "F-AC-CAPACITY": {
        "values": _case_values(**{"equipment.inverters.rated_ac_kw": {"inv-a": D("250"), "inv-b": D("100")}, "equipment.inverters.ids": ["inv-a", "inv-b"]}),
        "expected": D("350"),
        "invalid_field": "equipment.inverters.rated_ac_kw",
        "boundary": (_case_values(**{"equipment.inverters.rated_ac_kw": {"inv-a": D("0")}, "equipment.inverters.ids": ["inv-a"]}), D("0")),
    },
    "F-DC-AC-RATIO": {
        "values": _case_values(**{"capacity.dc_kwp": D("660"), "capacity.ac_kw": D("350")}),
        "expected": _fraction(660, 350),
        "invalid_field": "capacity.dc_kwp",
        "boundary": (_case_values(**{"capacity.dc_kwp": D("0"), "capacity.ac_kw": D("350")}), D("0")),
    },
    "F-POA-IRRADIATION": {
        "values": _case_values(**{"resource.poa_irradiance_kw_m2": {"t1": D("0.8"), "t2": D("0.6"), "t3": D("0.4"), "t4": D("0.2")}, "time.interval_hours": {"t1": D("0.25"), "t2": D("0.25"), "t3": D("0.25"), "t4": D("0.25")}, "time.resource_intervals": ["t1", "t2", "t3", "t4"]}),
        "expected": D("0.500"),
        "invalid_field": "time.interval_hours",
        "boundary": (_case_values(**{"resource.poa_irradiance_kw_m2": {"t1": D("0")}, "time.interval_hours": {"t1": D("1")}, "time.resource_intervals": ["t1"]}), D("0")),
    },
    "F-FIRST-YEAR-ENERGY": {
        "values": _case_values(**{"capacity.dc_kwp": D("660"), "resource.poa_irradiation_kwh_m2": D("0.5"), "constants.stc_irradiance_kw_m2": D("1"), "energy.pr_assumed": D("0.8")}),
        "expected": D("264.0"),
        "invalid_field": "energy.pr_assumed",
        "boundary": (_case_values(**{"capacity.dc_kwp": D("0"), "resource.poa_irradiation_kwh_m2": D("0.5"), "constants.stc_irradiance_kw_m2": D("1"), "energy.pr_assumed": D("0.8")}), D("0")),
    },
    "F-LOSS-COMPOSITE": {
        "values": _case_values(**{"losses.independent_rates": {"dc": D("0.1"), "ac": D("0.05")}, "losses.active_ids": ["dc", "ac"]}),
        "expected": D("0.855"),
        "invalid_field": "losses.independent_rates",
        "boundary": (_case_values(**{"losses.independent_rates": {}, "losses.active_ids": []}), D("1")),
    },
    "F-DC-TIME-POWER": {
        "values": _case_values(**{"capacity.dc_kwp": D("660"), "resource.effective_poa_kw_m2": D("0.8"), "constants.stc_irradiance_kw_m2": D("1"), "equipment.power_temperature_coefficient": D("-0.004"), "resource.cell_temperature_c": D("45"), "constants.stc_cell_temperature_c": D("25"), "losses.dc_retention": D("0.855")}),
        "expected": D("415.3248000"),
        "invalid_field": "losses.dc_retention",
        "boundary": (_case_values(**{"capacity.dc_kwp": D("660"), "resource.effective_poa_kw_m2": D("0"), "constants.stc_irradiance_kw_m2": D("1"), "equipment.power_temperature_coefficient": D("-0.004"), "resource.cell_temperature_c": D("45"), "constants.stc_cell_temperature_c": D("25"), "losses.dc_retention": D("0.855")}), D("0")),
    },
    "F-AC-INVERTER-POWER": {
        "values": _case_values(**{"capacity.ac_kw": D("250"), "losses.inverter_efficiency": D("0.98"), "energy.dc_power_kw": D("300")}),
        "expected": D("250"),
        "invalid_field": "losses.inverter_efficiency",
        "boundary": (_case_values(**{"capacity.ac_kw": D("250"), "losses.inverter_efficiency": D("0"), "energy.dc_power_kw": D("300")}), D("0")),
    },
    "F-AVAILABLE-ENERGY": {
        "values": _case_values(**{"energy.inverter_ac_power_kw": D("297"), "losses.ac_retention": D("0.99"), "losses.transformer_retention": D("0.98"), "losses.export_line_retention": D("0.97"), "energy.auxiliary_kw": D("2"), "time.interval_hours": D("0.25"), "losses.availability": D("0.95")}),
        "expected": D("65.9074180250"),
        "invalid_field": "losses.availability",
        "boundary": (_case_values(**{"energy.inverter_ac_power_kw": D("1"), "losses.ac_retention": D("1"), "losses.transformer_retention": D("1"), "losses.export_line_retention": D("1"), "energy.auxiliary_kw": D("2"), "time.interval_hours": D("1"), "losses.availability": D("1")}), D("0")),
    },
    "F-ENERGY-AGGREGATION": {
        "values": _case_values(**{"energy.boundary_interval_kwh": {"i1": D("1.1"), "i2": D("2.2"), "i3": D("3.3")}, "energy.boundary_id": "available", "time.aggregation_period": "2026-01", "time.period_interval_ids": ["i1", "i2", "i3"]}),
        "expected": D("6.6"),
        "invalid_field": "energy.boundary_interval_kwh",
        "boundary": (_case_values(**{"energy.boundary_interval_kwh": {"i1": D("0")}, "energy.boundary_id": "available", "time.aggregation_period": "2026-01", "time.period_interval_ids": ["i1"]}), D("0")),
    },
    "F-INITIAL-DEGRADATION": {
        "values": _case_values(**{"energy.first_year_pre_initial_kwh": D("1000"), "degradation.initial_fraction": D("0.03")}),
        "expected": D("970"),
        "invalid_field": "degradation.initial_fraction",
        "boundary": (_case_values(**{"energy.first_year_pre_initial_kwh": D("1000"), "degradation.initial_fraction": D("0")}), D("1000")),
    },
    "F-ANNUAL-DEGRADATION": {
        "values": _case_values(**{"energy.first_year_ac_kwh": D("1000"), "degradation.annual_fraction": D("0.02"), "time.operating_year": 5}),
        "expected": D("922.36816"),
        "invalid_field": "degradation.annual_fraction",
        "boundary": (_case_values(**{"energy.first_year_ac_kwh": D("1000"), "degradation.annual_fraction": D("0"), "time.operating_year": 1}), D("1000")),
    },
    "F-PIECEWISE-DEGRADATION": {
        "values": _case_values(**{"degradation.previous_retention": D("0.95"), "degradation.yearly_fraction": D("0.02"), "degradation.replacement_uplift": D("0.03")}),
        "expected": D("0.961"),
        "invalid_field": "degradation.yearly_fraction",
        "boundary": (_case_values(**{"degradation.previous_retention": D("1"), "degradation.yearly_fraction": D("0"), "degradation.replacement_uplift": D("0")}), D("1")),
    },
    "F-EQUIVALENT-HOURS": {
        "values": _case_values(**{"energy.annual_kwh": D("4380"), "energy.reference_capacity_kw": D("1")}),
        "expected": D("4380"),
        "invalid_field": "energy.reference_capacity_kw",
        "boundary": (_case_values(**{"energy.annual_kwh": D("0"), "energy.reference_capacity_kw": D("1")}), D("0")),
    },
    "F-CAPACITY-FACTOR": {
        "values": _case_values(**{"energy.annual_kwh": D("4380"), "energy.reference_capacity_kw": D("1"), "time.year_hours": D("8760")}),
        "expected": D("0.5"),
        "invalid_field": "time.year_hours",
        "boundary": (_case_values(**{"energy.annual_kwh": D("0"), "energy.reference_capacity_kw": D("1"), "time.year_hours": D("8760")}), D("0")),
    },
    "F-PR-OBSERVED": {
        "values": _case_values(**{"energy.annual_kwh": D("400"), "capacity.dc_kwp": D("100"), "resource.poa_irradiation_kwh_m2": D("500"), "constants.stc_irradiance_kw_m2": D("1")}),
        "expected": D("0.008"),
        "invalid_field": "capacity.dc_kwp",
        "boundary": (_case_values(**{"energy.annual_kwh": D("0"), "capacity.dc_kwp": D("100"), "resource.poa_irradiation_kwh_m2": D("500"), "constants.stc_irradiance_kw_m2": D("1")}), D("0")),
    },
    "F-EXPORT-LIMIT-ENERGY": {
        "values": _case_values(**{"grid.export_limit_kw": D("100"), "time.interval_hours": D("0.25")}),
        "expected": D("25"),
        "invalid_field": "grid.export_limit_kw",
        "boundary": (_case_values(**{"grid.export_limit_kw": D("0"), "time.interval_hours": D("0.25")}), D("0")),
    },
    "F-UNIT-KW-MW": {
        "values": _case_values(**{"units.power_kw": D("1250"), "constants.kilo_scale": D("1000")}),
        "expected": D("1.25"),
        "invalid_field": "units.power_kw",
        "boundary": (_case_values(**{"units.power_kw": D("0"), "constants.kilo_scale": D("1000")}), D("0")),
    },
    "F-UNIT-KWH-MWH": {
        "values": _case_values(**{"units.energy_kwh": D("2500"), "constants.kilo_scale": D("1000")}),
        "expected": D("2.5"),
        "invalid_field": "units.energy_kwh",
        "boundary": (_case_values(**{"units.energy_kwh": D("0"), "constants.kilo_scale": D("1000")}), D("0")),
    },
    "F-UNIT-IRRADIANCE-W-KW": {
        "values": _case_values(**{"units.irradiance_w_m2": D("800"), "constants.kilo_scale": D("1000")}),
        "expected": D("0.8"),
        "invalid_field": "units.irradiance_w_m2",
        "boundary": (_case_values(**{"units.irradiance_w_m2": D("0"), "constants.kilo_scale": D("1000")}), D("0")),
    },
    "F-UNIT-COST-WP-KWP": {
        "values": _case_values(**{"units.cost_per_wp": D("1.25"), "constants.kilo_scale": D("1000")}),
        "expected": D("1250"),
        "invalid_field": "units.cost_per_wp",
        "boundary": (_case_values(**{"units.cost_per_wp": D("0"), "constants.kilo_scale": D("1000")}), D("0")),
    },
    "F-UNIT-DC-CAPACITY": {
        "values": _case_values(**{"capacity.dc_kwp": D("660"), "constants.kilo_scale": D("1000")}),
        "expected": D("0.66"),
        "invalid_field": "capacity.dc_kwp",
        "boundary": (_case_values(**{"capacity.dc_kwp": D("0"), "constants.kilo_scale": D("1000")}), D("0")),
    },
    "F-UNIT-AC-CAPACITY": {
        "values": _case_values(**{"capacity.ac_kw": D("350"), "constants.kilo_scale": D("1000")}),
        "expected": D("0.35"),
        "invalid_field": "capacity.ac_kw",
        "boundary": (_case_values(**{"capacity.ac_kw": D("0"), "constants.kilo_scale": D("1000")}), D("0")),
    },
    "F-USABLE-AREA": {
        "values": _case_values(**{"site.total_area": D("1000"), "site.exclusion_area": {"road": D("150"), "setback": D("50")}}),
        "options": {"index_ids": {"site.exclusion_area": ["road", "setback"]}},
        "expected": D("800"),
        "invalid_field": "site.total_area",
        "boundary": (_case_values(**{"site.total_area": D("1000"), "site.exclusion_area": {}}), D("1000")),
        "boundary_options": {"index_ids": {"site.exclusion_area": []}},
    },
    "F-AVERAGE-ANNUAL-ENERGY": {
        "values": _case_values(**{"energy.annual_kwh": {"y1": D("1000"), "y2": D("900"), "y3": D("1100")}, "time.operating_year_count": 3}),
        "options": {"index_ids": {"energy.annual_kwh": ["y1", "y2", "y3"]}},
        "expected": D("1000"),
        "invalid_field": "time.operating_year_count",
        "boundary": (_case_values(**{"energy.annual_kwh": {"y1": D("0")}, "time.operating_year_count": 1}), D("0")),
        "boundary_options": {"index_ids": {"energy.annual_kwh": ["y1"]}},
    },
    "F-EMISSIONS-AVOIDED": {
        "values": _case_values(**{"environment.eligible_energy": D("1000"), "environment.grid_emission_factor": D("0.0005")}),
        "expected": D("0.5000"),
        "invalid_field": "environment.grid_emission_factor",
        "boundary": (_case_values(**{"environment.eligible_energy": D("0"), "environment.grid_emission_factor": D("0.0005")}), D("0")),
    },
    "F-TRANSFORMER-ACTIVE-LIMIT": {
        "values": _case_values(**{"grid.transformer_capacity": D("1000"), "grid.power_factor": D("0.9")}),
        "expected": D("900.0"),
        "invalid_field": "grid.power_factor",
        "boundary": (_case_values(**{"grid.transformer_capacity": D("1000"), "grid.power_factor": D("1")}), D("1000")),
    },
}


@pytest.mark.parametrize("formula_id", list(CASES))
def test_every_engineering_kernel_calculates_independent_reference(formula_id):
    case = CASES[formula_id]
    result = engineering.evaluate(formula_id, deepcopy(case["values"]), deepcopy(case.get("options")))
    assert result["status"] == "CALCULATED"
    assert result["value"] == case["expected"]


def test_formula_ids_expose_exactly_the_27_engineering_formulas():
    assert len(engineering.FORMULA_IDS) == 27
    assert set(engineering.FORMULA_IDS) == set(CASES)
    assert len(set(engineering.FORMULA_IDS)) == 27


@pytest.mark.parametrize("formula_id", list(CASES))
def test_missing_any_frozen_field_is_blocked_not_zero(formula_id):
    case = CASES[formula_id]
    missing_field = next(iter(case["values"]))
    values = deepcopy(case["values"])
    del values[missing_field]
    result = engineering.evaluate(formula_id, values, deepcopy(case.get("options")))
    assert result["status"] == "BLOCKED_MISSING_INPUT"
    assert result["value"] is None
    assert result["reason"] == "BLOCKED_MISSING_INPUT"


@pytest.mark.parametrize("formula_id", list(CASES))
def test_explicit_false_is_the_only_not_applicable_switch(formula_id):
    case = CASES[formula_id]
    result = engineering.evaluate(formula_id, {}, {"applicable": False})
    assert result["status"] == "NOT_APPLICABLE"
    assert result["value"] is None
    assert result["reason"] == "EXPLICITLY_NOT_APPLICABLE"


@pytest.mark.parametrize("formula_id", list(CASES))
def test_invalid_numeric_contract_is_rejected(formula_id):
    case = CASES[formula_id]
    values = deepcopy(case["values"])
    field = case["invalid_field"]
    values[field] = True
    with pytest.raises(ContractError):
        engineering.evaluate(formula_id, values, deepcopy(case.get("options")))


@pytest.mark.parametrize("formula_id", list(CASES))
def test_boundary_case_is_not_silently_truncated(formula_id):
    case = CASES[formula_id]
    result = engineering.evaluate(formula_id, deepcopy(case["boundary"][0]), deepcopy(case.get("boundary_options", case.get("options"))))
    assert result["status"] == "CALCULATED"
    assert result["value"] == case["boundary"][1]


def test_index_sets_must_match_exactly_without_zip_truncation():
    values = deepcopy(CASES["F-AC-CAPACITY"]["values"])
    values["equipment.inverters.ids"] = ["inv-a"]
    with pytest.raises(ContractError, match="INDEX_SET_MISMATCH"):
        engineering.evaluate("F-AC-CAPACITY", values)

    values = deepcopy(CASES["F-USABLE-AREA"]["values"])
    with pytest.raises(ContractError, match="INDEX_SET_MISMATCH"):
        engineering.evaluate("F-USABLE-AREA", values, {"index_ids": {"site.exclusion_area": ["road"]}})


def test_zero_denominators_are_undefined_not_contract_errors():
    ratio = deepcopy(CASES["F-DC-AC-RATIO"]["values"])
    ratio["capacity.ac_kw"] = D("0")
    assert engineering.evaluate("F-DC-AC-RATIO", ratio)["status"] == "UNDEFINED"

    hours = deepcopy(CASES["F-EQUIVALENT-HOURS"]["values"])
    hours["energy.reference_capacity_kw"] = D("0")
    assert engineering.evaluate("F-EQUIVALENT-HOURS", hours)["status"] == "UNDEFINED"

    factor = deepcopy(CASES["F-CAPACITY-FACTOR"]["values"])
    factor["time.year_hours"] = D("0")
    assert engineering.evaluate("F-CAPACITY-FACTOR", factor)["status"] == "UNDEFINED"

    pr = deepcopy(CASES["F-PR-OBSERVED"]["values"])
    pr["resource.poa_irradiation_kwh_m2"] = D("0")
    assert engineering.evaluate("F-PR-OBSERVED", pr)["status"] == "UNDEFINED"


def test_per_group_inverter_clipping_is_not_replaced_by_total_clipping():
    group_a = engineering.evaluate(
        "F-AC-INVERTER-POWER",
        {"capacity.ac_kw": D("200"), "losses.inverter_efficiency": D("0.98"), "energy.dc_power_kw": D("250")},
    )
    group_b = engineering.evaluate(
        "F-AC-INVERTER-POWER",
        {"capacity.ac_kw": D("150"), "losses.inverter_efficiency": D("0.97"), "energy.dc_power_kw": D("100")},
    )
    assert group_a["value"] + group_b["value"] == D("297")
    assert group_a["value"] + group_b["value"] != min(D("350"), D("0.98") * D("350"))


def test_exact_numbers_reject_float_string_and_nan():
    values = deepcopy(CASES["F-DC-CAPACITY"]["values"])
    for bad in (0.55, "0.55", D("NaN")):
        values["equipment.module_power_kwp"] = bad
        with pytest.raises(ContractError):
            engineering.evaluate("F-DC-CAPACITY", values)


def test_values_keys_and_options_are_strict_contracts():
    values = deepcopy(CASES["F-DC-CAPACITY"]["values"])
    values["unexpected.field"] = D("1")
    with pytest.raises(ContractError, match="FORMULA_VALUES_KEYS"):
        engineering.evaluate("F-DC-CAPACITY", values)

    with pytest.raises(ContractError):
        engineering.evaluate("F-DC-CAPACITY", CASES["F-DC-CAPACITY"]["values"], {"applicable": 0})


def test_precision_option_is_local_and_does_not_change_formula_domain():
    result = engineering.evaluate(
        "F-DC-AC-RATIO",
        CASES["F-DC-AC-RATIO"]["values"],
        {"precision_digits": 40},
    )
    with localcontext() as ctx:
        ctx.prec = 40
        expected = D(660) / D(350)
    assert result["value"] == expected


@pytest.mark.parametrize("formula_id", [fid for fid in CASES if fid.startswith("F-UNIT-")])
def test_si_kilo_scale_is_a_frozen_definition_not_a_free_parameter(formula_id):
    values = deepcopy(CASES[formula_id]["values"])
    values["constants.kilo_scale"] = D("999")
    with pytest.raises(ContractError, match="CONSTANT_DEFINITION"):
        engineering.evaluate(formula_id, values)


@pytest.mark.parametrize("formula_id", ["F-FIRST-YEAR-ENERGY", "F-DC-TIME-POWER", "F-PR-OBSERVED"])
def test_frozen_one_kw_per_square_metre_reference_is_not_redefined(formula_id):
    values = deepcopy(CASES[formula_id]["values"])
    values["constants.stc_irradiance_kw_m2"] = D("0.8")
    with pytest.raises(ContractError, match="CONSTANT_DEFINITION"):
        engineering.evaluate(formula_id, values)


def test_pr_above_one_allowed_by_d2_is_not_treated_as_a_loss_fraction():
    values = deepcopy(CASES["F-FIRST-YEAR-ENERGY"]["values"])
    values["energy.pr_assumed"] = D("1.2")
    # Independent arithmetic: 660 * (0.5/1) * 1.2 = 396.
    assert engineering.evaluate("F-FIRST-YEAR-ENERGY", values)["value"] == D("396")


def test_negative_temperature_power_factor_is_outside_method_not_clipped_to_success():
    values = deepcopy(CASES["F-DC-TIME-POWER"]["values"])
    values["resource.cell_temperature_c"] = D("300")
    # 1 - .004*(300-25) = -.1: the frozen assumption requires a domain error.
    with pytest.raises(ContractError, match="TEMPERATURE_POWER_FACTOR_DOMAIN"):
        engineering.evaluate("F-DC-TIME-POWER", values)


def test_poa_time_integral_requires_positive_physical_interval_duration():
    values = deepcopy(CASES["F-POA-IRRADIATION"]["values"])
    values["time.interval_hours"]["t1"] = D("0")
    with pytest.raises(ContractError, match="INTERVAL_DURATION_DOMAIN"):
        engineering.evaluate("F-POA-IRRADIATION", values)
