"""Exact independently factored references for frozen IRR root-set behavior."""
from decimal import Decimal as D

import pytest

from wangbin_solar_pv.calculation.financial_metrics import evaluate
from wangbin_solar_pv.errors import ContractError


@pytest.mark.parametrize("formula_id,field", [
    ("F-IRR-PROJECT", "finance.project_irr_cash_flow"),
    ("F-IRR-EQUITY", "finance.equity_investor_cash_flow"),
])
def test_double_root_is_not_lost(formula_id, field):
    # -100*x*x + 220*x - 121 = -100*(x-1.1)^2, x = 1+r.
    result = evaluate(formula_id, {
        "finance.irr_search_domain": [D("-0.5"), D("2")],
        field: [D("-100"), D("220"), D("-121")],
        "time.financial_end_year": 2,
    })
    assert result["status"] == "CALCULATED"
    assert abs(result["value"] - D("0.1")) < D("1e-18")
    assert len(result["details"]["roots"]) == 1
    assert abs(result["details"]["residuals"][0]) < D("1e-18")


@pytest.mark.parametrize("cash,domain,reason,expected", [
    ([-100, 120], ["-0.5", "1"], None, ["0.2"]),
    ([-100, 230, -132], ["-0.5", "1"], "MULTIPLE_ROOTS", ["0.1", "0.2"]),
    ([-100, "220.001", "-121.0011"], ["-0.5", "1"], "MULTIPLE_ROOTS", ["0.1", "0.10001"]),
    ([-100, 50], ["-0.5", "1"], None, ["-0.5"]),
    ([-100, 150], ["-0.5", "0.5"], None, ["0.5"]),
    ([-100, 80], ["-0.5", "1"], None, ["-0.2"]),
    ([1, -2, 2], ["-0.5", "1"], "NO_ROOT", []),
    ([-100, 120], ["0.3", "1"], "NO_ROOT", []),
    ([0, 0, 0], ["-0.5", "1"], "INDETERMINATE", []),
    ([0, 0, 5], ["-0.5", "1"], "NO_SIGN_CHANGE", []),
    ([-100, 220, "-121.00000000000000000001"], ["-0.5", "1"], "NO_ROOT", []),
])
def test_factored_root_sets(cash, domain, reason, expected):
    result = evaluate("F-IRR-PROJECT", {
        "finance.irr_search_domain": [D(x) for x in domain],
        "finance.project_irr_cash_flow": [D(str(x)) for x in cash],
        "time.financial_end_year": len(cash) - 1,
    })
    assert result["reason"] == reason
    roots = result["details"]["roots"]
    assert len(roots) == len(expected)
    for actual, reference in zip(roots, expected):
        assert abs(actual - D(reference)) < D("1e-18")
        assert abs(sum(D(str(v)) / (1 + actual) ** i for i, v in enumerate(cash))) < D("1e-14")


def test_invalid_irr_domain_is_not_accepted_as_a_degenerate_cash_flow():
    with pytest.raises(ContractError):
        evaluate("F-IRR-PROJECT", {
            "finance.irr_search_domain": [D("-1"), D("1")],
            "finance.project_irr_cash_flow": [D(0), D(0)],
            "time.financial_end_year": 1,
        })


def test_distinct_roots_closer_than_configured_interval_tolerance_stay_distinct():
    # -100*(x-1.1)*(x-1.10000000000000000001), r = x-1.
    result = evaluate("F-IRR-EQUITY", {
        "finance.irr_search_domain": [D("-0.5"), D("1")],
        "finance.equity_investor_cash_flow": [D("-100"), D("220.000000000000000001"), D("-121.0000000000000000011")],
        "time.financial_end_year": 2,
    })
    assert result["reason"] == "MULTIPLE_ROOTS"
    assert len(result["details"]["roots"]) == 2
    assert result["details"]["roots"][0] < result["details"]["roots"][1]
    assert abs(result["details"]["roots"][0] - D("0.1")) < D("1e-21")
    assert abs(result["details"]["roots"][1] - D("0.10000000000000000001")) < D("1e-21")


def test_boundary_root_and_interior_root_are_both_reported():
    # -100*(x-0.5)*(x-1.2) = -100*x*x + 170*x - 60.
    result = evaluate("F-IRR-PROJECT", {
        "finance.irr_search_domain": [D("-0.5"), D("1")],
        "finance.project_irr_cash_flow": [D("-100"), D("170"), D("-60")],
        "time.financial_end_year": 2,
    })
    assert result["reason"] == "MULTIPLE_ROOTS"
    assert len(result["details"]["roots"]) == 2
    assert result["details"]["roots"][0] == D("-0.5")
    assert abs(result["details"]["roots"][1] - D("0.2")) < D("1e-18")


def test_high_derivative_near_negative_one_needs_residual_refinement():
    cash = [D("-100000")] + list(map(D, [4240, -662, 1444, 3663, -835, -472, 5714,
        4548, 1554, -1743, -986, 2289, 2000, 4146, 84, 5447, 3855, 1550,
        3668, 5131, 2889, 2040, 1578, 2056, -444]))
    # Independent sign bracket near -0.8177; a rate-only interval width does
    # not control the currency residual when the discounted derivative is large.
    def npv(rate):
        return sum((amount / (1 + rate) ** i for i, amount in enumerate(cash)), D(0))
    assert npv(D("-0.82")) * npv(D("-0.81")) < 0
    result = evaluate("F-IRR-PROJECT", {
        "finance.irr_search_domain": [D("-0.9"), D("1")],
        "finance.project_irr_cash_flow": cash,
        "time.financial_end_year": 25,
    })
    assert result["status"] in ("CALCULATED", "UNDEFINED")
    assert result["reason"] != "NON_CONVERGENT"
    assert any(D("-0.82") < r < D("-0.81") for r in result["details"]["roots"])
    assert all(abs(value) < D("1e-18") * sum(map(abs, cash)) for value in result["details"]["residuals"])
