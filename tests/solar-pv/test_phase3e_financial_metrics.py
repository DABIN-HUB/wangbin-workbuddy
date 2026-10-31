"""Independent Decimal checks for the frozen Phase 3E formula kernels."""
from decimal import Decimal, localcontext

import pytest

from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.calculation.financial_metrics import FORMULA_IDS, evaluate

D = Decimal


def test_all_phase3e_formula_ids_have_executable_kernels():
    assert len(FORMULA_IDS) == 21
    for formula_id in FORMULA_IDS:
        assert evaluate(formula_id, {})["status"] == "BLOCKED_MISSING_INPUT"


def test_all_remaining_formula_kernels_have_independent_normal_case():
    cases = {
        "F-PROJECT-PRETAX-CASH-FLOW": {"finance.project_cash_flow": [D("10"), D("20")], "tax.project_income_cash_paid": [D("2"), D("3")]},
        "F-EQUITY-AVAILABLE-CASH-FLOW": {"finance.project_operating_cash_benefit": [D("100"), D("120")], "opex.cash_annual": [D("10"), D("10")], "tax.equity_cash_total": [D("5"), D("5")], "capex.equity_asset_cash_annual": [D("80"), D("0")], "working_capital.equity_net_change": [D("0"), D("2")], "finance.equity_terminal_cash": [D("0"), D("4")], "debt.cash_drawdown": [D("0"), D("0")], "debt.principal_paid": [D("0"), D("0")], "debt.interest_paid": [D("0"), D("0")], "debt.finance_fees_paid": [D("0"), D("0")]},
        "F-EQUITY-INVESTOR-CASH-FLOW": {"equity.distributions": [D("0"), D("20")], "equity.exit_receipts": [D("0"), D("10")], "equity.contributions": [D("100"), D("0")]},
        "F-CASH-FUNDING-BALANCE": {"checks.cash_opening": [D("0"), D("100")], "finance.equity_available_cash_flow": [D("100"), D("-20")], "equity.contributions": [D("0"), D("20")], "equity.distributions": [D("0"), D("10")]},
        "F-DATED-NPV": {"finance.dated_cash_flows": {"a": D("-100"), "b": D("120")}, "finance.selected_discount_rate": D("0.1"), "finance.cash_event_year_fraction": {"a": D("0"), "b": D("1")}, "finance.cash_event_ids": ["a", "b"], "finance.cash_flow_basis": "PROJECT"},
        "F-IRR-EQUITY": {"finance.irr_search_domain": {"minimum": D("-0.9"), "maximum": D("10")}, "finance.equity_investor_cash_flow": [D("-100"), D("60"), D("60")], "time.financial_end_year": 2},
        "F-CUMULATIVE-CASH-FLOW": {"finance.selected_cash_flow": [D("-100"), D("60"), D("60")], "time.cumulative_end_year": 2, "finance.cash_flow_basis": "PROJECT"},
        "F-STATIC-PAYBACK": {"finance.first_recovery_year": 2, "finance.pre_recovery_cumulative_cash": D("-40"), "finance.recovery_year_cash_flow": D("80"), "finance.cash_flow_basis": "PROJECT", "time.financial_end_year": 2},
        "F-DISCOUNTED-CUMULATIVE-CASH": {"finance.selected_cash_flow": [D("-100"), D("60"), D("60")], "finance.selected_discount_rate": D("0.1"), "time.cumulative_end_year": 2, "finance.cash_flow_basis": "PROJECT"},
        "F-DYNAMIC-PAYBACK": {"finance.first_discounted_recovery_year": 2, "finance.pre_discounted_recovery_cumulative": D("-40"), "finance.discounted_recovery_year_cash_flow": D("80"), "finance.selected_discount_rate": D("0.1"), "finance.cash_flow_basis": "PROJECT", "time.financial_end_year": 2},
        "F-LIFECYCLE-COST": {"capex.unlevered_cash_annual": [D("100"), D("0")], "opex.cash_annual": [D("0"), D("20")], "lcoe.cost_taxes": [D("0"), D("2")], "working_capital.project_net_change": [D("5"), D("0")], "finance.project_terminal_cash": [D("0"), D("10")], "lcoe.cost_subsidy_offset": [D("0"), D("1")]},
        "F-WORST-CASH-YEAR": {"finance.selected_cash_flow": {"y0": D("-100"), "y1": D("20"), "y2": D("-100")}, "risk.cash_year_scope": ["y0", "y1", "y2"], "finance.cash_flow_basis": "PROJECT"},
        "F-INVESTMENT-HURDLE-GAP": {"decision.calculated_metric": D("0.12"), "decision.target_metric": D("0.08")},
    }
    assert set(cases) == set(FORMULA_IDS) - {"F-PROJECT-CASH-FLOW", "F-NPV", "F-NOMINAL-REAL-RATE", "F-IRR-PROJECT", "F-LCOE", "F-CFADS", "F-DSCR", "F-BREAK-EVEN-PRICE"}
    for formula_id, values in cases.items():
        result = evaluate(formula_id, values)
        assert result["status"] == "CALCULATED", (formula_id, result)


def test_worst_cash_year_preserves_supplied_year_labels():
    result = evaluate("F-WORST-CASH-YEAR", {
        "finance.selected_cash_flow": {"construction": D("-100"), "year_1": D("20"), "year_2": D("-100")},
        "risk.cash_year_scope": ["construction", "year_1", "year_2"],
        "finance.cash_flow_basis": "PROJECT",
    })
    assert result["value"] == ["construction", "year_2"]


def test_project_cash_flow_rejects_mismatched_period_vectors():
    values = {
        "finance.project_operating_cash_benefit": [D("1"), D("2")], "opex.cash_annual": [D("0")],
        "tax.project_cash_total": [D("0"), D("0")], "capex.unlevered_cash_annual": [D("0"), D("0")],
        "working_capital.project_net_change": [D("0"), D("0")], "finance.project_terminal_cash": [D("0"), D("0")],
    }
    with pytest.raises(ContractError):
        evaluate("F-PROJECT-CASH-FLOW", values)


def test_project_cash_flow_is_signed_and_does_not_round_early():
    result = evaluate("F-PROJECT-CASH-FLOW", {
        "finance.project_operating_cash_benefit": [D("-100.125"), D("60.125")],
        "opex.cash_annual": [D("0.125"), D("1.125")],
        "tax.project_cash_total": [D("0"), D("2")],
        "capex.unlevered_cash_annual": [D("100"), D("0")],
        "working_capital.project_net_change": [D("0"), D("3")],
        "finance.project_terminal_cash": [D("0"), D("4")],
    })
    assert result["status"] == "CALCULATED"
    assert result["value"] == [D("-200.25"), D("58")]


def test_npv_dated_npv_and_real_nominal_bridge_use_independent_reference_math():
    cash = [D("-100"), D("60"), D("60")]
    npv = evaluate("F-NPV", {
        "finance.selected_cash_flow": cash,
        "finance.selected_discount_rate": D("0.1"),
        "finance.cash_flow_basis": "PROJECT",
        "time.financial_end_year": 2,
    })
    dated = evaluate("F-DATED-NPV", {
        "finance.dated_cash_flows": {"c0": D("-100"), "c1": D("60"), "c2": D("60")},
        "finance.selected_discount_rate": D("0.1"),
        "finance.cash_event_year_fraction": {"c0": D("0"), "c1": D("1"), "c2": D("2")},
        "finance.cash_event_ids": ["c0", "c1", "c2"],
        "finance.cash_flow_basis": "PROJECT",
    })
    with localcontext() as context:
        context.prec = 80
        expected = D("-100") + D("60") / D("1.1") + D("60") / D("1.21")
    assert abs(npv["value"] - expected) < D("1e-70")
    assert abs(dated["value"] - expected) < D("1e-70")
    bridge = evaluate("F-NOMINAL-REAL-RATE", {
        "finance.real_discount_rate": D("0.08"),
        "finance.general_inflation": D("0.02"),
    })
    assert bridge["value"] == D("0.1016")


def test_irr_reports_unique_root_and_multiple_or_no_root_states():
    unique = evaluate("F-IRR-PROJECT", {
        "finance.irr_search_domain": {"minimum": D("-0.9"), "maximum": D("10")},
        "finance.project_irr_cash_flow": [D("-100"), D("60"), D("60")],
        "time.financial_end_year": 2,
    })
    assert unique["status"] == "CALCULATED"
    assert abs(unique["details"]["residuals"][0]) < D("1e-15")
    no_root = evaluate("F-IRR-PROJECT", {
        "finance.irr_search_domain": {"minimum": D("-0.9"), "maximum": D("10")},
        "finance.project_irr_cash_flow": [D("1"), D("2"), D("3")],
        "time.financial_end_year": 2,
    })
    assert no_root["status"] == "UNDEFINED"
    assert no_root["reason"] == "NO_SIGN_CHANGE"


def test_lcoe_cfads_dscr_and_break_even_are_bounded():
    lcoe = evaluate("F-LCOE", {
        "lcoe.project_cost_annual": [D("100"), D("20"), D("20")],
        "energy.delivered_annual_kwh": [D("0"), D("100"), D("100")],
        "lcoe.discount_rate": D("0.1"),
        "time.financial_end_year": 2,
    })
    with localcontext() as context:
        context.prec = 80
        expected_lcoe = (D("100") + D("20") / D("1.1") + D("20") / D("1.21")) / (D("100") / D("1.1") + D("100") / D("1.21"))
    assert abs(lcoe["value"] - expected_lcoe) < D("1e-70")
    cfads = evaluate("F-CFADS", {
        "finance.project_operating_cash_benefit": [D("100"), D("120")],
        "opex.cash_annual": [D("10"), D("20")],
        "tax.equity_cash_total": [D("5"), D("10")],
        "debt.cfads_working_capital_change": [D("2"), D("3")],
        "debt.cfads_mandatory_capex": [D("1"), D("4")],
        "debt.cfads_adjustments": [D("0"), D("2")],
    })
    assert cfads["value"] == [D("82"), D("85")]
    dscr = evaluate("F-DSCR", {"debt.cfads": [D("82"), D("85")], "debt.service_due": [D("41"), D("17")]})
    assert dscr["value"] == [D("2"), D("5")]
    break_even = evaluate("F-BREAK-EVEN-PRICE", {
        "sensitivity.price_search_domain": {"minimum": D("0"), "maximum": D("10")},
        "finance.npv": D("0"),
        "sensitivity.price_cash_flow_vector": {"prices": [D("0"), D("10")], "cash_flows": [[D("-100"), D("0")], [D("-100"), D("200")] ]},
        "finance.selected_discount_rate": D("0"),
        "finance.cash_flow_basis": "PROJECT",
    })
    assert break_even["status"] == "CALCULATED"
    assert abs(break_even["value"] - D("5")) < D("1e-15")


@pytest.mark.parametrize("formula_id", ["F-EQUITY-INVESTOR-CASH-FLOW", "F-CASH-FUNDING-BALANCE", "F-DATED-NPV", "F-INVESTMENT-HURDLE-GAP"])
def test_missing_frozen_project_inputs_are_not_converted_to_zero(formula_id):
    result = evaluate(formula_id, {})
    assert result["status"] == "BLOCKED_MISSING_INPUT"
    assert result["value"] is None
    assert result["reason"] == "BLOCKED_MISSING_INPUT"


def test_dated_npv_does_not_omit_a_cash_event_when_vectors_are_short():
    values = {
        "finance.dated_cash_flows": [D("100")],
        "finance.selected_discount_rate": D("0"),
        "finance.cash_event_year_fraction": [D("0"), D("1")],
        "finance.cash_event_ids": ["event_0", "event_1"],
        "finance.cash_flow_basis": "PROJECT",
    }
    with pytest.raises(ContractError):
        evaluate("F-DATED-NPV", values)


@pytest.mark.parametrize("formula_id,year_field,prior_field,cash_field", [
    ("F-STATIC-PAYBACK", "finance.first_recovery_year", "finance.pre_recovery_cumulative_cash", "finance.recovery_year_cash_flow"),
    ("F-DYNAMIC-PAYBACK", "finance.first_discounted_recovery_year", "finance.pre_discounted_recovery_cumulative", "finance.discounted_recovery_year_cash_flow"),
])
def test_payback_must_recover_within_horizon(formula_id, year_field, prior_field, cash_field):
    values = {year_field: 3, prior_field: D("-100"), cash_field: D("10"),
              "finance.cash_flow_basis": "PROJECT", "time.financial_end_year": 2}
    if formula_id == "F-DYNAMIC-PAYBACK":
        values["finance.selected_discount_rate"] = D("0")
    result = evaluate(formula_id, values)
    assert result["status"] == "UNDEFINED"
    assert result["reason"] == "NOT_RECOVERED_WITHIN_HORIZON"


def test_project_cash_flow_aligns_labeled_years_regardless_of_mapping_order():
    values = {
        "finance.project_operating_cash_benefit": {"year_0": D("100"), "year_1": D("200")},
        "opex.cash_annual": {"year_1": D("10"), "year_0": D("1")},
        "tax.project_cash_total": {"year_0": D("0"), "year_1": D("0")},
        "capex.unlevered_cash_annual": {"year_0": D("0"), "year_1": D("0")},
        "working_capital.project_net_change": {"year_0": D("0"), "year_1": D("0")},
        "finance.project_terminal_cash": {"year_0": D("0"), "year_1": D("0")},
    }
    assert evaluate("F-PROJECT-CASH-FLOW", values)["value"] == [D("99"), D("190")]


def test_construction_working_capital_does_not_require_a_release_field():
    from wangbin_solar_pv.calculation.phase3e import _ledger_vectors

    vectors = _ledger_vectors([
        {"period": "CONSTRUCTION", "working_capital_increase": D("50")},
        {"period": "OPERATING_YEAR_1", "working_capital_increase": D("0"), "working_capital_release": D("50")},
    ])
    assert vectors["working_capital"] == [D("50"), D("-50")]
    assert "working_capital_release" not in vectors["missing"]
