"""Unit-driven reader formatting; canonical and workbook precision remain untouched."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any


_DECISION_PLACES = {
    "CNY": 0, "元": 0, "kWh": 0,
    "year": 2, "年": 2,
    "kWp": 0, "kW": 0, "kWac": 0,
}


def decision_number(value: Any, unit: str) -> str:
    """Round only declared metric units; preserve other dimensions for review."""
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return "UNKNOWN"
    try:
        number = Decimal(str(value))
        if not number.is_finite():
            return "UNKNOWN"
        places = _DECISION_PLACES.get(unit, 4)
        rounded = number.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)
        return f"{rounded:,.{places}f}"
    except InvalidOperation:
        return "UNKNOWN"


def decision_percent(fraction: Any) -> str:
    """A certified rate is stored as a fraction, displayed as percent (2 dp)."""
    if isinstance(fraction, bool) or not isinstance(fraction, (int, float, Decimal)):
        return "UNKNOWN"
    try:
        number = Decimal(str(fraction)) * 100
        if number.is_finite():
            return f"{number.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}%"
    except InvalidOperation:
        pass
    return "UNKNOWN"
