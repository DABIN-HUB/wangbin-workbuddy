"""Value-free errors, exact input conversion, explicit local Decimal precision.

JSON financial inputs are Decimal or integer, not binary floats or numeric text.
Rounding occurs at the declared numerical context, never at display cents.
"""
from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal, ROUND_HALF_EVEN, localcontext, InvalidOperation, DivisionByZero, Overflow
from fractions import Fraction

from ..errors import ContractError


def exact_json_numbers(value):
    """New calculation contracts reject float; legacy serialization is unchanged.

    Validate bounded JSON first, then walk without converting a numeric token or
    silently changing a legacy identity. Callers supply Decimal or integer.
    """
    from ..serialization import dumps
    dumps(value)
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, float):
            raise ContractError("EXACT_JSON_NUMBER_REQUIRED")
        # The unchanged legacy decoder reads integer token -0 as int(0).
        # Reject that spelling, without rewriting provenance or rejecting
        # stable decimal/exponent tokens such as -0.0 and -0E+3.
        if isinstance(item, Decimal) and item.is_zero() and item.is_signed() and item.as_tuple().exponent == 0:
            raise ContractError("NONCANONICAL_NEGATIVE_ZERO")
        if isinstance(item, dict):
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)


def number(value, field_id=None):
    if type(value) is int:
        return Decimal(value)
    if not isinstance(value, Decimal) or not value.is_finite():
        raise ContractError("FINITE_EXACT_NUMBER_REQUIRED", field_id)
    if len(value.as_tuple().digits) > 1024 or abs(value.adjusted()) > 10000:
        raise ContractError("NUMBER_SIZE_LIMIT", field_id)
    return value


def integer(value, field_id=None, *, minimum=None, maximum=None):
    if type(value) is not int or (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
        raise ContractError("INTEGER_DOMAIN", field_id)
    return value


def finite_sequence(value, field_id=None, *, nonnegative=False):
    if not isinstance(value, (list, tuple)):
        raise ContractError("NUMERIC_SEQUENCE_REQUIRED", field_id)
    result = [number(v, field_id) for v in value]
    if nonnegative and any(v < 0 for v in result):
        raise ContractError("NEGATIVE_INPUT", field_id)
    return result


def required(values, field_id):
    if field_id not in values or values[field_id] is None:
        raise ContractError("BLOCKED_MISSING_INPUT", field_id)
    return values[field_id]


def nonnegative(value, field_id=None):
    value = number(value, field_id)
    if value < 0:
        raise ContractError("NEGATIVE_INPUT", field_id)
    return value


def ratio(value, field_id=None, *, include_one=True):
    value = nonnegative(value, field_id)
    if value > 1 or (value == 1 and not include_one):
        raise ContractError("RATIO_DOMAIN", field_id)
    return value


@contextmanager
def precision_context(digits=80):
    integer(digits, "precision.digits", minimum=34, maximum=1024)
    with localcontext() as context:
        context.prec = digits
        context.rounding = ROUND_HALF_EVEN
        context.traps[InvalidOperation] = True
        context.traps[DivisionByZero] = True
        context.traps[Overflow] = True
        yield context


def decimal_fraction(value, digits=80):
    """Only explicit mathematical rational results cross this rounding boundary."""
    if not isinstance(value, Fraction):
        raise ContractError("RATIONAL_REQUIRED")
    with precision_context(digits):
        return Decimal(value.numerator) / Decimal(value.denominator)


def calculated(value, *, details=None):
    return {"status": "CALCULATED", "value": value, "reason": None, "details": details or {}}


def nonvalue(status, reason, *, details=None):
    if status not in {"NOT_APPLICABLE", "UNDEFINED", "BLOCKED_MISSING_INPUT", "BLOCKED_METHOD_REVIEW", "NOT_IMPLEMENTED"} or not reason:
        raise ContractError("INVALID_NONNUMERICAL_STATUS")
    return {"status": status, "value": None, "reason": reason, "details": details or {}}
