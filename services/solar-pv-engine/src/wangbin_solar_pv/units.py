"""Explicit, context-independent unit conversions for input contracts only.

No field aggregation, PV models, monetary valuation, or exchange-rate inference.
Floats are interpreted using their shortest round-trip decimal spelling; original
input preservation is the caller's responsibility.
"""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from fractions import Fraction
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .errors import ContractError


@dataclass(frozen=True)
class Conversion:
    value: Decimal
    source_unit: str | None
    target_unit: str | None
    rule_id: str
    exact: bool
    rounding_policy: dict | None


# Dimension, rational scale to that dimension's reference unit.
_UNITS = {
    "W": ("power", Fraction(1)), "kW": ("power", Fraction(1000)),
    "MW": ("power", Fraction(10**6)), "GW": ("power", Fraction(10**9)),
    "Wp": ("dc_nameplate", Fraction(1)), "kWp": ("dc_nameplate", Fraction(1000)),
    "MWp": ("dc_nameplate", Fraction(10**6)),
    "Wac": ("ac_nameplate", Fraction(1)), "kWac": ("ac_nameplate", Fraction(1000)),
    "MWac": ("ac_nameplate", Fraction(10**6)), "GWac": ("ac_nameplate", Fraction(10**9)),
    "Wh": ("energy", Fraction(1)), "kWh": ("energy", Fraction(1000)),
    "MWh": ("energy", Fraction(10**6)), "GWh": ("energy", Fraction(10**9)),
    "m2": ("area", Fraction(1)), "m²": ("area", Fraction(1)),
    "公顷": ("area", Fraction(10000)), "亩": ("area", Fraction(2000, 3)),
    "1": ("ratio", Fraction(1)), "%": ("ratio", Fraction(1, 100)),
    "m": ("length", Fraction(1)), "km": ("length", Fraction(1000)),
    "minute": ("duration", Fraction(60)), "hour": ("duration", Fraction(3600)),
    "day": ("duration", Fraction(86400)),
    "m/s": ("speed", Fraction(1)), "km/h": ("speed", Fraction(5, 18)),
    "W/m2": ("irradiance", Fraction(1)), "W/m²": ("irradiance", Fraction(1)),
    "kW/m2": ("irradiance", Fraction(1000)), "kW/m²": ("irradiance", Fraction(1000)),
    "kWh/m2": ("irradiation", Fraction(1)), "kWh/m²": ("irradiation", Fraction(1)),
    "V": ("voltage", Fraction(1)), "kV": ("voltage", Fraction(1000)),
    "kgCO2e/kWh": ("emission_factor_co2e", Fraction(1)),
    "tCO2e/kWh": ("emission_factor_co2e", Fraction(1000)),
    "K": ("absolute_temperature", Fraction(1)),
    "degC": ("absolute_temperature", Fraction(1)),
    "°C": ("absolute_temperature", Fraction(1)),
    "degF": ("absolute_temperature", Fraction(5, 9)),
    # Opaque identities deliberately do not participate in dimensional algebra.
    **{unit: (f"identity:{unit}", Fraction(1)) for unit in (
        None, "year", "degree", "A", "kVA", "kg", "kN/m2", "piece",
        "1/degC", "1/hour", "1/year", "1/cycle", "cycle",
    )},
}

_MONEY = {
    # Explicit denomination (None means caller-selected), boundary, scale.
    "CNY": ("CNY", "amount", Fraction(1)), "元": ("CNY", "amount", Fraction(1)),
    "万元": ("CNY", "amount", Fraction(10000)), "currency": (None, "amount", Fraction(1)),
    "元/Wp": ("CNY", "dc_nameplate_price", Fraction(1)),
    "元/kWp": ("CNY", "dc_nameplate_price", Fraction(1, 1000)),
    "万元/MWp": ("CNY", "dc_nameplate_price", Fraction(1, 100)),
    "元/kWh": ("CNY", "energy_price", Fraction(1)),
    "currency/kWh": (None, "energy_price", Fraction(1)),
    "currency/year": (None, "annual_amount_rate", Fraction(1)),
    "currency/unit": (None, "unspecified_unit_price", Fraction(1)),
}


def _unit_spec(unit: str | None, currency: str | None) -> tuple[str, Fraction]:
    if unit in _MONEY:
        denomination, boundary, scale = _MONEY[unit]
        if denomination is None:
            if currency is None:
                raise ContractError("UNIT_CURRENCY_REQUIRED")
            denomination = currency
        elif currency is not None and denomination != currency:
            raise ContractError("UNIT_CURRENCY_MISMATCH")
        return f"money:{denomination}:{boundary}", scale
    if unit not in _UNITS:
        raise ContractError("UNIT_UNKNOWN")
    return _UNITS[unit]


_TEMPERATURE_OFFSETS = {"K": Fraction(0), "degC": Fraction(27315, 100),
                        "°C": Fraction(27315, 100), "degF": Fraction(45967, 180)}

_ROUNDING_MODES = frozenset({
    "ROUND_DOWN", "ROUND_UP", "ROUND_CEILING", "ROUND_FLOOR", "ROUND_HALF_UP",
    "ROUND_HALF_DOWN", "ROUND_HALF_EVEN", "ROUND_05UP",
})


def _number(value: int | float | Decimal) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ContractError("UNIT_VALUE_TYPE")
    decimal = Decimal(str(value)) if isinstance(value, float) else Decimal(value)
    if not decimal.is_finite():
        raise ContractError("UNIT_VALUE_NONFINITE")
    return Fraction(decimal)


def _decimal(value: Fraction) -> Decimal:
    denominator = value.denominator
    twos = fives = 0
    while denominator % 2 == 0:
        denominator //= 2
        twos += 1
    while denominator % 5 == 0:
        denominator //= 5
        fives += 1
    if denominator != 1:
        raise ContractError("UNIT_ROUNDING_REQUIRED")
    places = max(twos, fives)
    coefficient = abs(value.numerator) * 2 ** (places - twos) * 5 ** (places - fives)
    digits = Decimal(coefficient).as_tuple().digits
    return Decimal((int(value < 0), digits, -places))


def _round_decimal(value: Fraction, places: int, mode: str) -> Decimal:
    """Round rational values with integer arithmetic, never ambient Decimal precision."""
    quotient, remainder = divmod(abs(value.numerator) * 10**places, value.denominator)
    increment = False
    if remainder:
        twice = remainder * 2
        increment = (
            mode == "ROUND_UP"
            or (mode == "ROUND_CEILING" and value > 0)
            or (mode == "ROUND_FLOOR" and value < 0)
            or (mode == "ROUND_HALF_UP" and twice >= value.denominator)
            or (mode == "ROUND_HALF_DOWN" and twice > value.denominator)
            or (mode == "ROUND_HALF_EVEN" and (
                twice > value.denominator or (twice == value.denominator and quotient % 2 == 1)))
            or (mode == "ROUND_05UP" and quotient % 10 in (0, 5))
        )
    coefficient = quotient + int(increment)
    return Decimal((int(value < 0), Decimal(coefficient).as_tuple().digits, -places))


def convert_unit(value: int | float | Decimal, source_unit: str | None,
                 target_unit: str | None, *, currency: str | None = None,
                 decimal_places: int | None = None, rounding: str | None = None) -> Conversion:
    """Normalize registered compatible dimensions; rounding requires both arguments.

    Explicit decimal_places is limited to 0..1000; exact conversion otherwise has
    no application-imposed significant-digit limit. Negative physical values and
    ratio field ranges belong to field validation, not unit scaling.
    """
    number = _number(value)
    policy = None
    if decimal_places is not None or rounding is not None:
        if (type(decimal_places) is not int or not 0 <= decimal_places <= 1000
                or not isinstance(rounding, str) or rounding not in _ROUNDING_MODES):
            raise ContractError("UNIT_ROUNDING_POLICY")
        policy = {"decimal_places": decimal_places, "rounding": rounding}
    if (source_unit is not None and not isinstance(source_unit, str)
            or target_unit is not None and not isinstance(target_unit, str)):
        raise ContractError("UNIT_UNKNOWN")
    if currency is not None and (not isinstance(currency, str) or re.fullmatch(r"[A-Z]{3}", currency) is None):
        raise ContractError("UNIT_CURRENCY_INVALID")
    source_dimension, source_scale = _unit_spec(source_unit, currency)
    target_dimension, target_scale = _unit_spec(target_unit, currency)
    if source_dimension != target_dimension:
        raise ContractError("UNIT_DIMENSION_MISMATCH")
    reference_value = number * source_scale + _TEMPERATURE_OFFSETS.get(source_unit, Fraction(0))
    if source_dimension == "absolute_temperature" and reference_value < 0:
        raise ContractError("UNIT_TEMPERATURE_RANGE")
    rational = (reference_value - _TEMPERATURE_OFFSETS.get(target_unit, Fraction(0))) / target_scale
    result = _decimal(rational) if policy is None else _round_decimal(rational, decimal_places, rounding)
    if (target_dimension == "absolute_temperature"
            and Fraction(result) * target_scale + _TEMPERATURE_OFFSETS[target_unit] < 0):
        raise ContractError("UNIT_TEMPERATURE_RANGE")
    rule = f"unit/v1:{source_unit}->{target_unit}"
    if source_dimension.startswith("money:"):
        rule += f":currency={source_dimension.split(':')[1]}"
    if policy is not None:
        rule += f":dp={decimal_places}:{rounding}"
    return Conversion(result, source_unit, target_unit, rule, Fraction(result) == rational, policy)


def validate_date(value: str) -> str:
    """Require a real proleptic Gregorian YYYY-MM-DD date, preserving its spelling."""
    if not isinstance(value, str) or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value) is None:
        raise ContractError("DATE_INVALID")
    try:
        date.fromisoformat(value)
    except ValueError:
        raise ContractError("DATE_INVALID") from None
    return value


_TIME_PATTERN = r"([0-9]{2}):([0-9]{2})(?::([0-9]{2})(?:\.([0-9]{1,6}))?)?"


def validate_time(value: str, *, allow_24: bool = False) -> str:
    """Validate a local daily time, optionally allowing the exact next-day boundary.

    HH:MM and HH:MM:SS[.ffffff] are accepted; no implicit timezone or leap second.
    """
    if type(allow_24) is not bool or not isinstance(value, str):
        raise ContractError("TIME_INVALID")
    match = re.fullmatch(_TIME_PATTERN, value)
    if match is None:
        raise ContractError("TIME_INVALID")
    hour, minute, second = (int(component or "0") for component in match.groups()[:3])
    fractional = match.group(4) or "0"
    if (hour == 24 and allow_24 and minute == second == 0
            and all(digit == "0" for digit in fractional)):
        return value
    if not (0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59):
        raise ContractError("TIME_INVALID")
    return value


_DATETIME_PATTERN = (
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?P<zone>Z|[+-][0-9]{2}:[0-9]{2})?"
)


def validate_datetime(value: str, *, timezone_required: bool = True) -> str:
    """Require an ISO extended timestamp with explicit UTC offset by default.

    -00:00 denotes an unknown offset and is rejected. IANA site-zone/DST alignment
    is a separate field-level check; an explicit offset alone cannot establish it.
    Opting out permits a naive timestamp but never silently localizes one.
    """
    if type(timezone_required) is not bool or not isinstance(value, str):
        raise ContractError("DATETIME_INVALID")
    match = re.fullmatch(_DATETIME_PATTERN, value)
    if match is None:
        raise ContractError("DATETIME_INVALID")
    zone = match.group("zone")
    if (timezone_required and zone is None) or zone == "-00:00":
        raise ContractError("DATETIME_INVALID")
    if zone is not None and zone != "Z":
        if int(zone[1:3]) >= 24 or int(zone[4:6]) >= 60:
            raise ContractError("DATETIME_INVALID")
    try:
        datetime.fromisoformat(value)
    except ValueError:
        raise ContractError("DATETIME_INVALID") from None
    return value


def validate_timezone(value: str) -> str:
    """Resolve an actual IANA ZoneInfo key without guessing a site or offset.

    The host must provide an IANA database (system zoneinfo or installed tzdata).
    """
    if not isinstance(value, str) or not value or value != value.strip():
        raise ContractError("TIMEZONE_INVALID")
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        raise ContractError("TIMEZONE_INVALID") from None
    return value
