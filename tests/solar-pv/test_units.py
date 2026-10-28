"""Real, synthetic-number tests for Phase 2 unit contracts; no PV/finance formulas."""
from dataclasses import FrozenInstanceError
from decimal import Decimal, localcontext
from importlib import import_module, util

import pytest

from wangbin_solar_pv.errors import ContractError


def units():
    assert util.find_spec("wangbin_solar_pv.units") is not None, "Phase 2B units module is missing"
    return import_module("wangbin_solar_pv.units")


@pytest.mark.parametrize("source,target,value,expected", [
    ("W", "kW", 1250, "1.25"), ("kW", "W", Decimal("1.25"), "1250"),
    ("MW", "GW", 2500, "2.5"), ("GW", "W", 2, "2000000000"),
    ("Wp", "kWp", 615, "0.615"), ("kWp", "Wp", Decimal("0.615"), "615"),
    ("MWp", "kWp", Decimal("1.5"), "1500"),
    ("Wac", "kWac", 2500, "2.5"), ("kWac", "Wac", Decimal("2.5"), "2500"),
    ("MWac", "GWac", 1250, "1.25"), ("GWac", "MWac", 2, "2000"),
    ("Wh", "kWh", 250, "0.25"), ("kWh", "Wh", Decimal("0.25"), "250"),
    ("MWh", "GWh", 1500, "1.5"), ("GWh", "MWh", 3, "3000"),
    ("kW", "W", 0, "0"), ("kW", "W", -2, "-2000"),
    ("kW", "W", 0.1, "100"),
])
def test_power_energy_exact_forward_reverse_boundary(source, target, value, expected):
    result = units().convert_unit(value, source, target)
    assert result.value == Decimal(expected)
    assert isinstance(result.value, Decimal)
    assert (result.source_unit, result.target_unit) == (source, target)
    assert result.rule_id and result.exact is True and result.rounding_policy is None
    with pytest.raises(FrozenInstanceError):
        result.value = Decimal(0)


@pytest.mark.parametrize("source,target", [
    ("kW", "kWp"), ("kWp", "kWac"), ("kWac", "kW"),
    ("kWh", "kW"), ("Wh", "Wp"), ("kW", "kVA"),
    ("imaginary", "imaginary"), ("kw", "kW"), (" W", "W"),
    ("", ""), (None, "1"), ([], "W"),
])
def test_unknown_and_physical_boundaries_are_not_aliases(source, target):
    with pytest.raises(ContractError):
        units().convert_unit(1, source, target)


@pytest.mark.parametrize("value", [True, False, "1.25", None, [], {},
    float("nan"), float("inf"), float("-inf"),
    Decimal("NaN"), Decimal("sNaN"), Decimal("Infinity"), Decimal("-Infinity")])
def test_strict_finite_numeric_inputs(value):
    with pytest.raises(ContractError):
        units().convert_unit(value, "W", "W")


def test_decimal_context_must_not_truncate_exact_values():
    value = Decimal("123456789012345678901234567890.123456789")
    with localcontext() as context:
        context.prec = 3
        result = units().convert_unit(value, "kW", "W")
    assert result.value == Decimal("123456789012345678901234567890123.456789")
    assert result.exact is True


@pytest.mark.parametrize("source,target,value,expected", [
    ("m2", "m²", Decimal("12.5"), "12.5"),
    ("公顷", "m2", Decimal("1.25"), "12500"), ("m²", "公顷", 12500, "1.25"),
    ("亩", "m2", 3, "2000"), ("m2", "亩", 2000, "3"),
    ("公顷", "亩", 1, "15"), ("亩", "公顷", 15, "1"),
    ("%", "1", 12.5, "0.125"), ("1", "%", Decimal("0.125"), "12.5"),
    ("%", "1", 0, "0"), ("%", "1", 100, "1"),
    ("m", "km", 1250, "1.25"), ("km", "m", Decimal("1.25"), "1250"),
    ("minute", "hour", 90, "1.5"), ("hour", "minute", Decimal("1.5"), "90"),
    ("day", "hour", 2, "48"), ("hour", "day", 48, "2"),
    ("day", "minute", 1, "1440"), ("minute", "day", 1440, "1"),
    ("m/s", "km/h", 10, "36"), ("km/h", "m/s", 36, "10"),
    ("m/s", "km/h", 0, "0"),
    ("W/m2", "kW/m²", 850, "0.85"), ("kW/m2", "W/m²", Decimal("0.85"), "850"),
    ("kWh/m²", "kWh/m2", Decimal("123.45"), "123.45"),
    ("kV", "V", Decimal("0.4"), "400"), ("V", "kV", 400, "0.4"),
    ("kgCO2e/kWh", "tCO2e/kWh", Decimal("0.55"), "0.00055"),
    ("tCO2e/kWh", "kgCO2e/kWh", Decimal("0.00055"), "0.55"),
])
def test_nonmonetary_scale_families(source, target, value, expected):
    result = units().convert_unit(value, source, target)
    assert result.value == Decimal(expected)
    assert result.exact and result.rounding_policy is None


@pytest.mark.parametrize("unit", [None, "year", "degree", "A", "kVA", "kg", "kN/m2", "piece",
    "1/degC", "1/hour", "1/year", "1/cycle", "cycle", "kWh/m2", "W/m2"])
@pytest.mark.parametrize("value", [0, Decimal("-1.25"), Decimal("1.234567890123456789")])
def test_frozen_units_support_known_identity_only(unit, value):
    assert units().convert_unit(value, unit, unit).value == Decimal(value)


@pytest.mark.parametrize("source,target", [
    ("W/m2", "kWh/m2"), ("kWh/m2", "W/m2"), ("kWh/m2", "kWh"),
    ("year", "day"), ("day", "year"), ("1/year", "1/hour"),
    ("kN/m2", "kg"), ("m2", "m"), ("degree", "1"), ("cycle", "piece"),
    ("1/degC", "degC"), ("tCO2/MWh", "kgCO2e/kWh"),
])
def test_no_implicit_integration_or_calendar_or_semantic_conversion(source, target):
    with pytest.raises(ContractError):
        units().convert_unit(1, source, target)


@pytest.mark.parametrize("source,target", [("亩", "m2"), ("minute", "hour"), ("km/h", "m/s")])
def test_nonterminating_decimal_requires_explicit_rounding(source, target):
    with pytest.raises(ContractError) as error:
        units().convert_unit(1, source, target)
    assert error.value.code == "UNIT_ROUNDING_REQUIRED"


@pytest.mark.parametrize("mode,positive,negative", [
    ("ROUND_DOWN", "666.66", "-666.66"), ("ROUND_UP", "666.67", "-666.67"),
    ("ROUND_CEILING", "666.67", "-666.66"), ("ROUND_FLOOR", "666.66", "-666.67"),
    ("ROUND_HALF_UP", "666.67", "-666.67"), ("ROUND_HALF_DOWN", "666.67", "-666.67"),
    ("ROUND_HALF_EVEN", "666.67", "-666.67"), ("ROUND_05UP", "666.66", "-666.66"),
])
def test_rational_rounding_and_audit_policy(mode, positive, negative):
    for value, expected in [(1, positive), (-1, negative)]:
        result = units().convert_unit(value, "亩", "m2", decimal_places=2, rounding=mode)
        assert result.value == Decimal(expected)
        assert result.value.as_tuple().exponent == -2
        assert result.exact is False
        assert result.rounding_policy == {"decimal_places": 2, "rounding": mode}
        assert mode in result.rule_id


@pytest.mark.parametrize("value,mode,expected", [
    ("1.245", "ROUND_HALF_EVEN", "1.24"), ("1.255", "ROUND_HALF_EVEN", "1.26"),
    ("-1.245", "ROUND_HALF_UP", "-1.25"), ("1.245", "ROUND_HALF_DOWN", "1.24"),
    ("1.2501", "ROUND_05UP", "1.26"), ("-1.2501", "ROUND_05UP", "-1.26"),
])
def test_rounding_exact_decimal_ties_and_05up(value, mode, expected):
    result = units().convert_unit(Decimal(value), "W", "W", decimal_places=2, rounding=mode)
    assert result.value == Decimal(expected)
    assert result.exact is False


@pytest.mark.parametrize("kwargs", [
    {"decimal_places": 2}, {"rounding": "ROUND_HALF_UP"},
    {"decimal_places": True, "rounding": "ROUND_DOWN"},
    {"decimal_places": -1, "rounding": "ROUND_DOWN"},
    {"decimal_places": 2.5, "rounding": "ROUND_DOWN"},
    {"decimal_places": "2", "rounding": "ROUND_DOWN"},
    {"decimal_places": 2, "rounding": "HALF_UP"},
    {"decimal_places": 2, "rounding": []},
    {"decimal_places": 1001, "rounding": "ROUND_DOWN"},
])
def test_incomplete_or_invalid_rounding_policy_is_rejected_even_on_identity(kwargs):
    with pytest.raises(ContractError):
        units().convert_unit(1, "W", "W", **kwargs)


def test_explicit_policy_exact_flag_and_decimal_context_independence():
    with localcontext() as context:
        context.prec = 2
        result = units().convert_unit(1, "亩", "m2", decimal_places=12, rounding="ROUND_HALF_UP")
        exact = units().convert_unit(3, "亩", "m2", decimal_places=2, rounding="ROUND_HALF_UP")
    assert result.value == Decimal("666.666666666667") and result.exact is False
    assert exact.value == Decimal("2000.00") and exact.exact is True
    assert exact.rounding_policy == {"decimal_places": 2, "rounding": "ROUND_HALF_UP"}


@pytest.mark.parametrize("source,target,value,expected", [
    ("degC", "K", 0, "273.15"), ("K", "degC", Decimal("273.15"), "0"),
    ("degC", "degF", 100, "212"), ("degF", "degC", 212, "100"),
    ("degF", "K", 32, "273.15"), ("K", "degF", Decimal("273.15"), "32"),
    ("degC", "°C", Decimal("-40"), "-40"),
    ("°C", "degF", Decimal("-40"), "-40"),
    ("K", "degC", 0, "-273.15"), ("degC", "K", Decimal("-273.15"), "0"),
    ("degF", "K", Decimal("-459.67"), "0"),
    ("K", "degF", 0, "-459.67"),
    ("degF", "degF", Decimal("-459.67"), "-459.67"),
])
def test_absolute_temperature_affine_conversion_and_absolute_zero(source, target, value, expected):
    result = units().convert_unit(value, source, target)
    assert result.value == Decimal(expected) and result.exact


@pytest.mark.parametrize("unit,value", [("K", Decimal("-0.0001")),
    ("degC", Decimal("-273.15001")), ("degF", Decimal("-459.67001"))])
def test_temperature_below_absolute_zero_is_rejected_on_identity_too(unit, value):
    with pytest.raises(ContractError) as error:
        units().convert_unit(value, unit, unit)
    assert error.value.code == "UNIT_TEMPERATURE_RANGE"


def test_temperature_nonterminating_and_explicit_rounding():
    with pytest.raises(ContractError) as error:
        units().convert_unit(1, "degF", "degC")
    assert error.value.code == "UNIT_ROUNDING_REQUIRED"
    result = units().convert_unit(1, "degF", "degC", decimal_places=4, rounding="ROUND_HALF_UP")
    assert result.value == Decimal("-17.2222") and not result.exact


def test_temperature_rounding_cannot_create_below_absolute_zero_result():
    with pytest.raises(ContractError) as error:
        units().convert_unit(0, "K", "degC", decimal_places=0, rounding="ROUND_FLOOR")
    assert error.value.code == "UNIT_TEMPERATURE_RANGE"


@pytest.mark.parametrize("source,target,value,currency,expected", [
    ("CNY", "元", Decimal("125.5"), None, "125.5"),
    ("元", "CNY", Decimal("125.5"), None, "125.5"),
    ("万元", "元", Decimal("1.25"), None, "12500"),
    ("元", "万元", 12500, None, "1.25"),
    ("万元", "currency", Decimal("1.25"), "CNY", "12500"),
    ("currency", "万元", 12500, "CNY", "1.25"),
    ("currency", "currency", Decimal("10.25"), "USD", "10.25"),
    ("元/Wp", "万元/MWp", Decimal("3.2"), None, "320"),
    ("万元/MWp", "元/Wp", 320, None, "3.2"),
    ("元/kWp", "元/Wp", 3200, None, "3.2"),
    ("元/Wp", "元/kWp", Decimal("3.2"), None, "3200"),
    ("currency/kWh", "元/kWh", Decimal("0.45"), "CNY", "0.45"),
    ("元/kWh", "currency/kWh", Decimal("0.45"), "CNY", "0.45"),
    ("currency/unit", "currency/unit", Decimal("12.25"), "EUR", "12.25"),
    ("currency/year", "currency/year", Decimal("12500.5"), "USD", "12500.5"),
    ("currency/kWh", "currency/kWh", Decimal("-0.1"), "USD", "-0.1"),
    ("元", "万元", 0, "CNY", "0"),
])
def test_money_and_price_scaling_without_exchange_or_valuation(source, target, value, currency, expected):
    result = units().convert_unit(value, source, target, currency=currency)
    assert result.value == Decimal(expected) and result.exact
    if currency:
        assert currency in result.rule_id


@pytest.mark.parametrize("unit", ["currency", "currency/kWh", "currency/year", "currency/unit"])
def test_unresolved_currency_is_rejected_even_on_identity(unit):
    with pytest.raises(ContractError) as error:
        units().convert_unit(1, unit, unit)
    assert error.value.code == "UNIT_CURRENCY_REQUIRED"


@pytest.mark.parametrize("source,target,currency", [
    ("currency", "元", "USD"), ("元", "currency", "EUR"),
    ("CNY", "万元", "USD"), ("currency/kWh", "元/kWh", "USD"),
    ("USD", "CNY", "USD"), ("EUR", "EUR", "EUR"),
    ("currency/year", "currency", "CNY"),
    ("currency/kWh", "currency", "CNY"),
    ("元/Wp", "元/kWh", "CNY"), ("currency/unit", "元/Wp", "CNY"),
    ("元_含税", "元_不含税", "CNY"), ("元_2025", "元_2026", "CNY"),
])
def test_currency_and_price_tax_year_basis_are_not_inferred(source, target, currency):
    with pytest.raises(ContractError):
        units().convert_unit(1, source, target, currency=currency)


@pytest.mark.parametrize("currency", ["", "cny", "CN", "CNYY", " CNY", 1, [], True])
def test_malformed_currency_is_not_silently_ignored(currency):
    with pytest.raises(ContractError):
        units().convert_unit(1, "currency", "currency", currency=currency)


@pytest.mark.parametrize("value", ["2024-02-29", "2000-02-29", "2026-10-28", "1900-03-01", "0001-01-01", "9999-12-31"])
def test_real_calendar_dates(value):
    assert units().validate_date(value) == value


@pytest.mark.parametrize("value", ["2023-02-29", "1900-02-29", "2026-04-31", "2026-00-10",
    "2026-13-01", "2026-01-00", "0000-01-01", "20261028", "2026-W44-3", "2026-1-01",
    "2026-10-28T00:00:00Z", " 2026-10-28", "２０２６-１０-２８", None, 20261028])
def test_invalid_calendar_or_noncanonical_dates_are_rejected(value):
    with pytest.raises(ContractError) as error:
        units().validate_date(value)
    assert error.value.code == "DATE_INVALID"


@pytest.mark.parametrize("value", ["00:00", "23:59", "00:00:00", "23:59:59.123456"])
def test_daily_start_time_boundaries(value):
    assert units().validate_time(value) == value


@pytest.mark.parametrize("value", ["24:00", "24:00:00", "24:00:00.000000"])
def test_only_explicit_end_time_can_use_24(value):
    assert units().validate_time(value, allow_24=True) == value
    with pytest.raises(ContractError):
        units().validate_time(value)


@pytest.mark.parametrize("value", ["24:01", "24:00:01", "24:00:00.000001", "25:00", "23:60",
    "23:59:60", "9:00", "0900", "00:00Z", "12:30+08:00", "12:30:00.1234567",
    "12:30:00.", " 12:30", "１２:３０", "-01:00", None, 1230])
def test_invalid_daily_times_even_in_end_mode(value):
    with pytest.raises(ContractError) as error:
        units().validate_time(value, allow_24=True)
    assert error.value.code == "TIME_INVALID"


@pytest.mark.parametrize("value", ["2024-02-29T00:00:00Z", "2026-10-28T12:30:45+08:00",
    "2026-10-28T12:30:45.123456-04:00", "0001-01-01T00:00:00+00:00"])
def test_datetime_requires_real_calendar_and_utc_offset(value):
    assert units().validate_datetime(value) == value


@pytest.mark.parametrize("value", ["2023-02-29T00:00:00Z", "2026-10-28T24:00:00Z",
    "2026-10-28T12:00:60Z", "2026-10-28T12:00:00+24:00", "2026-10-28T12:00:00+08:60",
    "2026-10-28T12:00:00-00:00", "2026-10-28T12:00:00", "2026-10-28",
    "20261028T120000Z", "2026-10-28 12:00:00Z", "2026-10-28T12:00Z",
    "2026-10-28T12:00:00+0800", "2026-10-28T12:00:00.1234567Z", "2026-10-28T12:00:00[Asia/Shanghai]",
    None, 123])
def test_invalid_or_naive_datetime_is_not_implicitly_localized(value):
    with pytest.raises(ContractError) as error:
        units().validate_datetime(value)
    assert error.value.code == "DATETIME_INVALID"


def test_naive_datetime_only_when_caller_explicitly_allows_it():
    value = "2024-02-29T12:34:56"
    assert units().validate_datetime(value, timezone_required=False) == value
    with pytest.raises(ContractError):
        units().validate_datetime("2023-02-29T12:34:56", timezone_required=False)


@pytest.mark.parametrize("value", ["UTC", "Asia/Shanghai", "America/New_York", "Etc/GMT+8"])
def test_real_iana_timezone_keys(value):
    assert units().validate_timezone(value) == value


@pytest.mark.parametrize("value", ["", "Asia/NotARealZone", "UTC+08:00", "+08:00", "CST",
    "../UTC", "/etc/localtime", " Asia/Shanghai", None, [], 8])
def test_fake_offset_and_path_timezone_keys_are_rejected(value):
    with pytest.raises(ContractError) as error:
        units().validate_timezone(value)
    assert error.value.code == "TIMEZONE_INVALID"


@pytest.mark.parametrize("flag", [1, "yes", None])
def test_validation_mode_flags_require_booleans(flag):
    with pytest.raises(ContractError):
        units().validate_time("24:00", allow_24=flag)
    with pytest.raises(ContractError):
        units().validate_datetime("2026-10-28T12:00:00", timezone_required=flag)


@pytest.mark.parametrize("as_decimal", [False, True])
def test_large_finite_numbers_do_not_hit_integer_string_conversion_limits(as_decimal):
    value = 10**5000 + 1
    if as_decimal:
        value = Decimal(value)
    with localcontext() as context:
        context.prec = 3
        result = units().convert_unit(value, "kW", "W")
        rounded = units().convert_unit(value, "W", "W", decimal_places=2, rounding="ROUND_DOWN")
    assert result.value == Decimal((10**5000 + 1) * 1000)
    assert rounded.value == Decimal(10**5000 + 1)
    assert result.exact and rounded.exact


def test_every_frozen_catalog_unit_has_a_known_exact_identity():
    import json
    from pathlib import Path
    catalog = json.loads((Path(__file__).resolve().parents[2] / "docs/solar-pv/03-input-fields.json").read_text(encoding="utf-8"))
    for unit in {field["unit"] for field in catalog["fields"]}:
        result = units().convert_unit(Decimal("12.5"), unit, unit, currency="CNY")
        assert result.value == Decimal("12.5") and result.exact, unit


@pytest.mark.parametrize("left,right", [
    ("W", "kWp"), ("kWp", "kWac"), ("W", "kWac"), ("kWh", "W"),
    ("W/m2", "kWh/m2"), ("currency", "currency/year"),
    ("currency/kWh", "元/Wp"), ("m", "m2"), ("A", "V"), ("kVA", "kW"),
    ("degree", "1"), ("year", "day"), ("1/degC", "degC"), ("kg", "kN/m2"),
    ("1/hour", "1/year"), ("cycle", "piece"), (None, "1"),
])
def test_cross_dimension_rejection_is_bidirectional_even_with_rounding(left, right):
    for source, target in [(left, right), (right, left)]:
        with pytest.raises(ContractError) as error:
            units().convert_unit(1, source, target, currency="CNY", decimal_places=2, rounding="ROUND_HALF_UP")
        assert error.value.code == "UNIT_DIMENSION_MISMATCH"


@pytest.mark.parametrize("mode", ["ROUND_DOWN", "ROUND_UP", "ROUND_CEILING", "ROUND_FLOOR",
    "ROUND_HALF_UP", "ROUND_HALF_DOWN", "ROUND_HALF_EVEN", "ROUND_05UP"])
def test_integer_rounding_matches_independent_decimal_quantize_oracle(mode):
    with localcontext() as context:
        context.prec = 60
        for numerator in range(-51, 52):
            value = Decimal(numerator) / Decimal(8)
            for places in (0, 1, 2):
                quantum = Decimal(1).scaleb(-places)
                expected = value.quantize(quantum, rounding=mode)
                result = units().convert_unit(value, "W", "W", decimal_places=places, rounding=mode)
                assert result.value == expected
                assert result.exact == (value == expected)


@pytest.mark.parametrize("unit", ["W", "Wp", "Wac", "Wh", "m2", "1", "m", "minute", "m/s", "W/m2",
    "kWh/m2", "V", "A", "kVA", "kg", "kN/m2", "degree", "currency", "currency/kWh", "元/Wp"])
def test_scaling_families_preserve_zero_and_finite_sign_without_field_range_guess(unit):
    for value in (Decimal(0), Decimal("-0.125")):
        result = units().convert_unit(value, unit, unit, currency="CNY")
        assert result.value == value and result.exact
        with pytest.raises(ContractError):
            units().convert_unit(Decimal("NaN"), unit, unit, currency="CNY")
