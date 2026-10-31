"""Frozen Phase 3E financial-metric kernels.

The kernels are deliberately value-only.  They accept the exact namespaces
listed by the frozen formula definitions and never manufacture missing cash,
owner transactions, dates, targets, or bank-account events.  Project assembly
belongs to the Phase 3E orchestration layer; this module is also used by the
formula registry and independent Decimal reference checks.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from ..errors import ContractError
from .common import calculated, integer, nonnegative, nonvalue, number, precision_context

FORMULA_IDS = (
    "F-PROJECT-CASH-FLOW", "F-PROJECT-PRETAX-CASH-FLOW", "F-EQUITY-AVAILABLE-CASH-FLOW",
    "F-EQUITY-INVESTOR-CASH-FLOW", "F-CASH-FUNDING-BALANCE", "F-NPV", "F-DATED-NPV",
    "F-NOMINAL-REAL-RATE", "F-IRR-PROJECT", "F-IRR-EQUITY", "F-CUMULATIVE-CASH-FLOW",
    "F-STATIC-PAYBACK", "F-DISCOUNTED-CUMULATIVE-CASH", "F-DYNAMIC-PAYBACK",
    "F-LIFECYCLE-COST", "F-LCOE", "F-CFADS", "F-DSCR", "F-BREAK-EVEN-PRICE",
    "F-WORST-CASH-YEAR", "F-INVESTMENT-HURDLE-GAP",
)

_REQUIRED = {
    "F-PROJECT-CASH-FLOW": ("finance.project_operating_cash_benefit", "opex.cash_annual", "tax.project_cash_total", "capex.unlevered_cash_annual", "working_capital.project_net_change", "finance.project_terminal_cash"),
    "F-PROJECT-PRETAX-CASH-FLOW": ("finance.project_cash_flow", "tax.project_income_cash_paid"),
    "F-EQUITY-AVAILABLE-CASH-FLOW": ("finance.project_operating_cash_benefit", "opex.cash_annual", "tax.equity_cash_total", "capex.equity_asset_cash_annual", "working_capital.equity_net_change", "finance.equity_terminal_cash", "debt.cash_drawdown", "debt.principal_paid", "debt.interest_paid", "debt.finance_fees_paid"),
    "F-EQUITY-INVESTOR-CASH-FLOW": ("equity.distributions", "equity.exit_receipts", "equity.contributions"),
    "F-CASH-FUNDING-BALANCE": ("checks.cash_opening", "finance.equity_available_cash_flow", "equity.contributions", "equity.distributions"),
    "F-NPV": ("finance.selected_cash_flow", "finance.selected_discount_rate", "finance.cash_flow_basis", "time.financial_end_year"),
    "F-DATED-NPV": ("finance.dated_cash_flows", "finance.selected_discount_rate", "finance.cash_event_year_fraction", "finance.cash_event_ids", "finance.cash_flow_basis"),
    "F-NOMINAL-REAL-RATE": ("finance.real_discount_rate", "finance.general_inflation"),
    "F-IRR-PROJECT": ("finance.irr_search_domain", "finance.project_irr_cash_flow", "time.financial_end_year"),
    "F-IRR-EQUITY": ("finance.irr_search_domain", "finance.equity_investor_cash_flow", "time.financial_end_year"),
    "F-CUMULATIVE-CASH-FLOW": ("finance.selected_cash_flow", "time.cumulative_end_year", "finance.cash_flow_basis"),
    "F-STATIC-PAYBACK": ("finance.first_recovery_year", "finance.pre_recovery_cumulative_cash", "finance.recovery_year_cash_flow", "finance.cash_flow_basis", "time.financial_end_year"),
    "F-DISCOUNTED-CUMULATIVE-CASH": ("finance.selected_cash_flow", "finance.selected_discount_rate", "time.cumulative_end_year", "finance.cash_flow_basis"),
    "F-DYNAMIC-PAYBACK": ("finance.first_discounted_recovery_year", "finance.pre_discounted_recovery_cumulative", "finance.discounted_recovery_year_cash_flow", "finance.selected_discount_rate", "finance.cash_flow_basis", "time.financial_end_year"),
    "F-LIFECYCLE-COST": ("capex.unlevered_cash_annual", "opex.cash_annual", "lcoe.cost_taxes", "working_capital.project_net_change", "finance.project_terminal_cash", "lcoe.cost_subsidy_offset"),
    "F-LCOE": ("lcoe.project_cost_annual", "energy.delivered_annual_kwh", "lcoe.discount_rate", "time.financial_end_year"),
    "F-CFADS": ("finance.project_operating_cash_benefit", "opex.cash_annual", "tax.equity_cash_total", "debt.cfads_working_capital_change", "debt.cfads_mandatory_capex", "debt.cfads_adjustments"),
    "F-DSCR": ("debt.cfads", "debt.service_due"),
    "F-BREAK-EVEN-PRICE": ("sensitivity.price_search_domain", "finance.npv", "sensitivity.price_cash_flow_vector", "finance.selected_discount_rate", "finance.cash_flow_basis"),
    "F-WORST-CASH-YEAR": ("finance.selected_cash_flow", "risk.cash_year_scope", "finance.cash_flow_basis"),
    "F-INVESTMENT-HURDLE-GAP": ("decision.calculated_metric", "decision.target_metric"),
}

_ALLOWED_OPTION_KEYS = {"precision_digits", "applicable", "root_tolerance", "maximum_iterations"}
_ZERO = Decimal(0)
_ONE = Decimal(1)


def _options(options):
    if options is None:
        return {}
    if not isinstance(options, dict) or set(options) - _ALLOWED_OPTION_KEYS:
        raise ContractError("OPTIONS_KEYS")
    if "applicable" in options and type(options["applicable"]) is not bool:
        raise ContractError("APPLICABILITY_BOOLEAN_REQUIRED")
    if "precision_digits" in options:
        integer(options["precision_digits"], "precision.precision_digits", minimum=34, maximum=1024)
    if "root_tolerance" in options:
        number(options["root_tolerance"], "irr.root_tolerance")
    if "maximum_iterations" in options:
        integer(options["maximum_iterations"], "break_even.maximum_iterations", minimum=1, maximum=10000)
    return options


def _missing(formula_id, fields):
    return nonvalue("BLOCKED_MISSING_INPUT", "BLOCKED_MISSING_INPUT", details={"formula_id": formula_id, "missing_field_ids": sorted(fields)})


def _contains_none(value):
    if value is None:
        return True
    if isinstance(value, dict):
        return any(_contains_none(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_none(item) for item in value)
    return False


def _ids(value, field):
    if not isinstance(value, (list, tuple)) or not value or len(set(value)) != len(value) or any(type(x) is not str or not x for x in value):
        raise ContractError("INDEX_IDS_SEQUENCE_REQUIRED", field)
    return tuple(value)


def _scalar(value, field, *, signed=True):
    return number(value, field) if signed else nonnegative(value, field)


def _series(value, field, *, ids=None, signed=True, length=None):
    """Return an ordered Decimal series from a stable map or explicit list."""
    convert = _scalar if signed else lambda x, f: nonnegative(x, f)
    if isinstance(value, dict):
        if ids is None:
            keys = tuple(value)
        else:
            keys = tuple(ids)
            if set(value) != set(keys):
                missing = sorted(set(keys) - set(value))
                if missing:
                    raise ContractError("INDEX_SET_MISMATCH", field)
                raise ContractError("INDEXED_VALUES_KEYS", field)
        result = [convert(value[key], field) for key in keys]
    elif isinstance(value, (list, tuple)):
        result = [convert(item, field) for item in value]
    else:
        if length not in (None, 1):
            raise ContractError("NUMERIC_SEQUENCE_REQUIRED", field)
        result = [convert(value, field)]
    if length is not None and len(result) != length:
        raise ContractError("PERIOD_VECTOR_LENGTH_MISMATCH", field)
    return result


def _aligned_series(values, fields, *, unsigned=()):
    """Align labeled operands to the first operand's year labels."""
    labeled = [isinstance(values[field], dict) for field in fields]
    if any(labeled) and not all(labeled):
        raise ContractError("INDEXED_VALUES_KEYS", fields[0])
    ids = tuple(values[fields[0]]) if all(labeled) else None
    return [_series(values[field], field, ids=ids, signed=field not in unsigned) for field in fields]

def _n(values, field):
    n = integer(values[field], field, minimum=0, maximum=10000)
    return n


def _rate(value, field):
    rate = number(value, field)
    if rate <= -1:
        raise ContractError("RATE_DOMAIN", field)
    return rate


def _discounted(cash, rate):
    rate = _rate(rate, "finance.selected_discount_rate")
    return sum((amount / ((_ONE + rate) ** index) for index, amount in enumerate(cash)), _ZERO)


def _domain(value, field):
    if isinstance(value, dict):
        low = value.get("minimum", value.get("min"))
        high = value.get("maximum", value.get("max"))
    elif isinstance(value, (list, tuple)) and len(value) == 2:
        low, high = value
    else:
        raise ContractError("SEARCH_DOMAIN_REQUIRED", field)
    low = _rate(low, field + ".minimum")
    high = _rate(high, field + ".maximum")
    if low >= high:
        raise ContractError("SEARCH_DOMAIN_ORDER", field)
    return low, high


def _numeric_domain(value, field):
    if isinstance(value, dict):
        low = value.get("minimum", value.get("min"))
        high = value.get("maximum", value.get("max"))
    elif isinstance(value, (list, tuple)) and len(value) == 2:
        low, high = value
    else:
        raise ContractError("SEARCH_DOMAIN_REQUIRED", field)
    low = number(low, field + ".minimum")
    high = number(high, field + ".maximum")
    if low >= high:
        raise ContractError("SEARCH_DOMAIN_ORDER", field)
    return low, high


def _npv(cash, rate):
    return _discounted(cash, rate)


def _bisection(func, left, right, tolerance, maximum=160):
    fl, fr = func(left), func(right)
    if fl == 0:
        return left
    if fr == 0:
        return right
    if fl * fr > 0:
        return None
    for _ in range(maximum):
        mid = (left + right) / 2
        fm = func(mid)
        if abs(fm) <= tolerance or abs(right - left) <= tolerance:
            return mid
        if fl * fm <= 0:
            right, fr = mid, fm
        else:
            left, fl = mid, fm
    return (left + right) / 2


def _irr(cash, domain, options):
    if not any(cash):
        return nonvalue("UNDEFINED", "ALL_ZERO_CASH_FLOW", details={"roots": []})
    if all(item >= 0 for item in cash) or all(item <= 0 for item in cash):
        return nonvalue("UNDEFINED", "NO_SIGN_CHANGE", details={"roots": []})
    low, high = _domain(domain, "finance.irr_search_domain")
    tolerance = number(options.get("root_tolerance", Decimal("1e-18")), "irr.root_tolerance")
    if tolerance <= 0:
        raise ContractError("IRR_TOLERANCE_DOMAIN")
    steps = min(8192, max(256, len(cash) * 128))
    step = (high - low) / steps
    roots = []
    previous_x = low
    previous_y = _npv(cash, previous_x)
    for index in range(1, steps + 1):
        current_x = high if index == steps else low + step * index
        current_y = _npv(cash, current_x)
        if abs(previous_y) <= tolerance:
            roots.append(previous_x)
        if previous_y * current_y < 0:
            root = _bisection(lambda rate: _npv(cash, rate), previous_x, current_x, tolerance)
            if root is not None:
                roots.append(root)
        previous_x, previous_y = current_x, current_y
    if abs(previous_y) <= tolerance:
        roots.append(previous_x)
    unique = []
    for root in sorted(roots):
        if not unique or abs(root - unique[-1]) > tolerance * 10:
            unique.append(root)
    details = {"roots": unique, "domain": {"minimum": low, "maximum": high}, "root_tolerance": tolerance, "residuals": [_npv(cash, root) for root in unique]}
    if not unique:
        return nonvalue("UNDEFINED", "NO_ROOT", details=details)
    if len(unique) != 1:
        return nonvalue("UNDEFINED", "MULTIPLE_ROOTS", details=details)
    return calculated(unique[0], details=details)


def _interpolate_vector(left, right, fraction):
    return [a + (b - a) * fraction for a, b in zip(left, right)]


def _price_samples(value, field):
    if isinstance(value, dict) and "prices" in value and "cash_flows" in value:
        prices = _series(value["prices"], field + ".prices", signed=True)
        vectors = value["cash_flows"]
    elif isinstance(value, dict):
        prices = [_scalar(key, field + ".price") for key in value]
        vectors = [value[key] for key in value]
    else:
        raise ContractError("PRICE_CASH_FLOW_VECTOR_REQUIRED", field)
    if len(prices) < 2 or len(prices) != len(vectors):
        raise ContractError("PRICE_SAMPLE_COUNT", field)
    pairs = sorted(zip(prices, vectors), key=lambda pair: pair[0])
    result = []
    labeled = [isinstance(vector, dict) for _, vector in pairs]
    if any(labeled) and not all(labeled):
        raise ContractError("INDEXED_VALUES_KEYS", field)
    ids = tuple(pairs[0][1]) if all(labeled) else None
    for price, vector in pairs:
        result.append((price, _series(vector, field + ".cash_flows", ids=ids, signed=True)))
    if len({price for price, _ in result}) != len(result):
        raise ContractError("DUPLICATE_PRICE_SAMPLE", field)
    length = len(result[0][1])
    if any(len(vector) != length for _, vector in result):
        raise ContractError("PRICE_VECTOR_LENGTH_MISMATCH", field)
    return result


def _break_even(values, options):
    samples = _price_samples(values["sensitivity.price_cash_flow_vector"], "sensitivity.price_cash_flow_vector")
    low, high = _numeric_domain(values["sensitivity.price_search_domain"], "sensitivity.price_search_domain")
    samples = [(price, vector) for price, vector in samples if low <= price <= high]
    if len(samples) < 2:
        return nonvalue("UNDEFINED", "NO_ROOT", details={"roots": [], "domain": {"minimum": low, "maximum": high}})
    rate = _rate(values["finance.selected_discount_rate"], "finance.selected_discount_rate")
    tolerance = number(options.get("root_tolerance", values.get("sensitivity.price_tolerance", Decimal("1e-12"))), "break_even.price_tolerance")
    def f(price, left, right):
        fraction = (price - left[0]) / (right[0] - left[0])
        return _npv(_interpolate_vector(left[1], right[1], fraction), rate)
    roots = []
    for left, right in zip(samples, samples[1:]):
        fl, fr = f(left[0], left, right), f(right[0], left, right)
        if fl == 0:
            roots.append(left[0])
        if fl * fr < 0:
            root = _bisection(lambda price: f(price, left, right), left[0], right[0], tolerance, maximum=options.get("maximum_iterations", 160))
            if root is not None:
                roots.append(root)
    if _npv(samples[-1][1], rate) == 0:
        roots.append(samples[-1][0])
    unique = []
    for root in sorted(roots):
        if not unique or abs(root - unique[-1]) > tolerance * 10:
            unique.append(root)
    details = {"roots": unique, "domain": {"minimum": low, "maximum": high}, "price_tolerance": tolerance, "method": "PIECEWISE_AFFINE_SAMPLE_INTERPOLATION"}
    if not unique:
        return nonvalue("UNDEFINED", "NO_ROOT", details=details)
    if len(unique) > 1:
        return nonvalue("UNDEFINED", "MULTIPLE_ROOTS", details=details)
    return calculated(unique[0], details=details)


def _dispatch(formula_id, values, options):
    if formula_id == "F-PROJECT-CASH-FLOW":
        keys = ("finance.project_operating_cash_benefit", "opex.cash_annual", "tax.project_cash_total", "capex.unlevered_cash_annual", "working_capital.project_net_change", "finance.project_terminal_cash")
        series = _aligned_series(values, keys)
        if len({len(item) for item in series}) != 1:
            raise ContractError("PERIOD_VECTOR_LENGTH_MISMATCH", formula_id)
        return [sum(items, _ZERO) for items in zip(series[0], *[[-x for x in item] for item in series[1:5]], series[5])]
    if formula_id == "F-PROJECT-PRETAX-CASH-FLOW":
        a, b = _aligned_series(values, ("finance.project_cash_flow", "tax.project_income_cash_paid"))
        if len(a) != len(b): raise ContractError("PERIOD_VECTOR_LENGTH_MISMATCH", formula_id)
        return [x + y for x, y in zip(a, b)]
    if formula_id == "F-EQUITY-AVAILABLE-CASH-FLOW":
        keys = ("finance.project_operating_cash_benefit", "opex.cash_annual", "tax.equity_cash_total", "capex.equity_asset_cash_annual", "working_capital.equity_net_change", "finance.equity_terminal_cash", "debt.cash_drawdown", "debt.principal_paid", "debt.interest_paid", "debt.finance_fees_paid")
        benefit, *parts = _aligned_series(values, keys)
        subtract = parts[:4]
        terminal, add, principal, interest, fees = parts[4:]
        all_series = [benefit, terminal, add, *subtract, principal, interest, fees]
        if len({len(x) for x in all_series}) != 1: raise ContractError("PERIOD_VECTOR_LENGTH_MISMATCH", formula_id)
        return [b - sum(x[i] for x in subtract) + terminal[i] + add[i] - principal[i] - interest[i] - fees[i] for i, b in enumerate(benefit)]
    if formula_id == "F-EQUITY-INVESTOR-CASH-FLOW":
        d, e, c = _aligned_series(values, ("equity.distributions", "equity.exit_receipts", "equity.contributions"))
        if len({len(d), len(e), len(c)}) != 1: raise ContractError("PERIOD_VECTOR_LENGTH_MISMATCH", formula_id)
        return [x + y - z for x, y, z in zip(d, e, c)]
    if formula_id == "F-CASH-FUNDING-BALANCE":
        opening, available, contributions, distributions = _aligned_series(values, ("checks.cash_opening", "finance.equity_available_cash_flow", "equity.contributions", "equity.distributions"), unsigned=("checks.cash_opening", "equity.distributions"))
        if len({len(opening), len(available), len(contributions), len(distributions)}) != 1: raise ContractError("PERIOD_VECTOR_LENGTH_MISMATCH", formula_id)
        closing = []
        balance = None
        for i, (o, a, c, d) in enumerate(zip(opening, available, contributions, distributions)):
            if balance is not None and o != balance: raise ContractError("CASH_OPENING_ROLL_FORWARD_MISMATCH", str(i))
            balance = o + a + c - d
            closing.append(balance)
        return closing
    if formula_id == "F-NPV":
        n = _n(values, "time.financial_end_year")
        return _npv(_series(values["finance.selected_cash_flow"], "finance.selected_cash_flow", length=n + 1), values["finance.selected_discount_rate"])
    if formula_id == "F-DATED-NPV":
        ids = _ids(values["finance.cash_event_ids"], "finance.cash_event_ids")
        cash = _series(values["finance.dated_cash_flows"], "finance.dated_cash_flows", ids=ids, length=len(ids))
        tau = _series(values["finance.cash_event_year_fraction"], "finance.cash_event_year_fraction", ids=ids, signed=False, length=len(ids))
        rate = _rate(values["finance.selected_discount_rate"], "finance.selected_discount_rate")
        return sum((amount / ((_ONE + rate) ** year_fraction) for amount, year_fraction in zip(cash, tau)), _ZERO)
    if formula_id == "F-NOMINAL-REAL-RATE":
        return (1 + _rate(values["finance.real_discount_rate"], "finance.real_discount_rate")) * (1 + _rate(values["finance.general_inflation"], "finance.general_inflation")) - 1
    if formula_id in {"F-IRR-PROJECT", "F-IRR-EQUITY"}:
        field = "finance.project_irr_cash_flow" if formula_id == "F-IRR-PROJECT" else "finance.equity_investor_cash_flow"
        return _irr(_series(values[field], field, length=_n(values, "time.financial_end_year") + 1), values["finance.irr_search_domain"], options)
    if formula_id == "F-CUMULATIVE-CASH-FLOW":
        n = _n(values, "time.cumulative_end_year"); cash = _series(values["finance.selected_cash_flow"], "finance.selected_cash_flow", length=n + 1)
        total = _ZERO; result = []
        for item in cash: total += item; result.append(total)
        return result
    if formula_id == "F-STATIC-PAYBACK":
        n = integer(values["finance.first_recovery_year"], "finance.first_recovery_year", minimum=1)
        horizon = _n(values, "time.financial_end_year")
        prior = number(values["finance.pre_recovery_cumulative_cash"], "finance.pre_recovery_cumulative_cash")
        current = number(values["finance.recovery_year_cash_flow"], "finance.recovery_year_cash_flow")
        if n > horizon or prior + current < 0: return nonvalue("UNDEFINED", "NOT_RECOVERED_WITHIN_HORIZON")
        if prior >= 0 or current <= 0: return nonvalue("UNDEFINED", "INVALID_RECOVERY_CROSSING")
        return n - 1 + (-prior / current)
    if formula_id == "F-DISCOUNTED-CUMULATIVE-CASH":
        n = _n(values, "time.cumulative_end_year"); cash = _series(values["finance.selected_cash_flow"], "finance.selected_cash_flow", length=n + 1); rate = values["finance.selected_discount_rate"]
        total = _ZERO; result = []
        for i, item in enumerate(cash): total += item / ((_ONE + _rate(rate, "finance.selected_discount_rate")) ** i); result.append(total)
        return result
    if formula_id == "F-DYNAMIC-PAYBACK":
        n = integer(values["finance.first_discounted_recovery_year"], "finance.first_discounted_recovery_year", minimum=1)
        horizon = _n(values, "time.financial_end_year")
        prior = number(values["finance.pre_discounted_recovery_cumulative"], "finance.pre_discounted_recovery_cumulative")
        current = number(values["finance.discounted_recovery_year_cash_flow"], "finance.discounted_recovery_year_cash_flow")
        rate = _rate(values["finance.selected_discount_rate"], "finance.selected_discount_rate")
        if prior >= 0 or current <= 0: return nonvalue("UNDEFINED", "INVALID_RECOVERY_CROSSING")
        discounted = current / ((_ONE + rate) ** n)
        if n > horizon or prior + discounted < 0: return nonvalue("UNDEFINED", "NOT_RECOVERED_WITHIN_HORIZON")
        if discounted <= 0: return nonvalue("UNDEFINED", "ZERO_DISCOUNTED_RECOVERY_FLOW")
        return n - 1 + (-prior / discounted)
    if formula_id == "F-LIFECYCLE-COST":
        series = _aligned_series(values, _REQUIRED[formula_id])
        if len({len(x) for x in series}) != 1: raise ContractError("PERIOD_VECTOR_LENGTH_MISMATCH", formula_id)
        return [a + b + c + d - e - f for a, b, c, d, e, f in zip(*series)]
    if formula_id == "F-LCOE":
        n = _n(values, "time.financial_end_year"); costs, energy = _aligned_series(values, ("lcoe.project_cost_annual", "energy.delivered_annual_kwh"), unsigned=("energy.delivered_annual_kwh",)); rate = values["lcoe.discount_rate"]
        if len(costs) != n + 1 or len(energy) != n + 1: raise ContractError("PERIOD_VECTOR_LENGTH_MISMATCH", formula_id)
        numerator = _discounted(costs, rate); denominator = _discounted(energy, rate)
        if denominator == 0: return nonvalue("UNDEFINED", "ZERO_DELIVERY")
        return numerator / denominator
    if formula_id == "F-CFADS":
        series = _aligned_series(values, _REQUIRED[formula_id])
        if len({len(x) for x in series}) != 1: raise ContractError("PERIOD_VECTOR_LENGTH_MISMATCH", formula_id)
        return [a - b - c - d - e + f for a, b, c, d, e, f in zip(*series)]
    if formula_id == "F-DSCR":
        cfads, service = _aligned_series(values, ("debt.cfads", "debt.service_due"), unsigned=("debt.service_due",))
        if len(cfads) != len(service): raise ContractError("PERIOD_VECTOR_LENGTH_MISMATCH", formula_id)
        if all(item == 0 for item in service): return nonvalue("UNDEFINED", "ZERO_DEBT_SERVICE")
        if any(item == 0 for item in service): return nonvalue("UNDEFINED", "ZERO_DEBT_SERVICE", details={"zero_service_periods": [i for i, item in enumerate(service) if item == 0]})
        return [cash / debt for cash, debt in zip(cfads, service)]
    if formula_id == "F-BREAK-EVEN-PRICE":
        return _break_even(values, options)
    if formula_id == "F-WORST-CASH-YEAR":
        scope = _ids(values["risk.cash_year_scope"], "risk.cash_year_scope")
        cash = _series(values["finance.selected_cash_flow"], "finance.selected_cash_flow", ids=scope)
        minimum = min(cash); return [scope[index] for index, value in enumerate(cash) if value == minimum]
    if formula_id == "F-INVESTMENT-HURDLE-GAP":
        return number(values["decision.calculated_metric"], "decision.calculated_metric") - number(values["decision.target_metric"], "decision.target_metric")
    raise ContractError("UNKNOWN_FORMULA", formula_id)


def evaluate(formula_id, values, options=None):
    if formula_id not in FORMULA_IDS:
        raise ContractError("UNKNOWN_FORMULA", formula_id)
    options = _options(options)
    if options.get("applicable", True) is False:
        return nonvalue("NOT_APPLICABLE", "EXPLICITLY_NOT_APPLICABLE", details={"formula_id": formula_id})
    if not isinstance(values, dict):
        raise ContractError("FORMULA_VALUES_MAPPING_REQUIRED", formula_id)
    required = set(_REQUIRED[formula_id])
    missing = required - set(values)
    if missing:
        return _missing(formula_id, missing)
    if set(values) != required:
        raise ContractError("FORMULA_VALUES_KEYS", formula_id)
    if any(_contains_none(values[field]) for field in required):
        return _missing(formula_id, {field for field in required if _contains_none(values[field])})
    precision = options.get("precision_digits", 80)
    with precision_context(precision):
        result = _dispatch(formula_id, values, options)
    if isinstance(result, dict) and "status" in result:
        return result
    return calculated(result, details={"formula_id": formula_id, "precision_digits": precision})
