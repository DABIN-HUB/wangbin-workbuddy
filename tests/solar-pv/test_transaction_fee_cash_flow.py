"""Trace separately billed settlement transaction fees into project cash, once."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.calculation.financial_ledger import _annual_revenue, calculate_financial_ledger
from wangbin_solar_pv.calculation.phase3e import _ledger_vectors, calculate_phase3e
from wangbin_solar_pv.calculation.result_contract import seal_result
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.serialization import loads


_CASES = Path(__file__).resolve().parents[2] / "reports/solar-pv/phase7l-r2-full-cases"


@pytest.fixture(scope="module", params=("industrial_rooftop", "utility_scale_ground"))
def case(request):
    root = _CASES / request.param
    exported, methods, settlement = (loads((root / file).read_bytes())
                                      for file in ("input.json", "methods.json", "project/3c/result.json"))
    return exported, methods, settlement


def _financial(case):
    exported, methods, settlement = case
    return calculate_financial_ledger(exported, methods, settlement, catalog=Catalog())


def test_gross_receipt_and_separate_fee_accrual_do_not_invent_cash_payment(case):
    _, _, settlement = case
    result = _financial(case)
    years = result["evidence"]["financial-ledger"]["annual"]
    vectors = _ledger_vectors(years)
    assert len(years) == 26
    assert vectors["missing"]["transaction_cost_cash_paid"] == [
        f"OPERATING_YEAR_{index}" for index in range(1, 26)]
    assert vectors["benefit"] is None
    assert result["status"] == "PARTIAL"
    assert any(finding["code"] == "TRANSACTION_FEE_PAYMENT_SOURCE_REQUIRED"
               for finding in result["findings"])
    assert years[0]["period"] == "CONSTRUCTION"
    for index, row in enumerate(years[1:], 1):
        source = next(metric for metric in settlement["results"]["metrics"]
                      if metric["metric_id"] == f"revenue.year.{index}")["details"]["ledger"]
        fee = source["transaction_cost"]
        assert fee > 0
        assert row["transaction_cost_accrued"] == fee
        assert row["transaction_cost_cash_paid"] is None
        assert row["transaction_cost_payable_opening"] is None
        assert row["transaction_cost_payable_closing"] is None
        assert abs(row["invoiced_gross"] - source["export_sales_revenue"]) < Decimal("0.000000000000000001")
        assert row["transaction_cost_payment_status"] == "BLOCKED_MISSING_INPUT"
        assert vectors["opex"][index] == row["opex_cash_paid"]
        assert row["taxable_income_project"] is not None  # Tax is a separate deduction, not fee payment.
    assert vectors["transaction_cost"] is None
    partial = calculate_phase3e(result, case[1], Catalog())
    assert partial["status"] == "PARTIAL"
    for metric_id in ("financial.phase3e.project_cash_flow", "financial.phase3e.project_npv",
                      "financial.phase3e.project_irr", "financial.phase3e.static_payback"):
        metric = next(metric for metric in partial["results"]["metrics"] if metric["metric_id"] == metric_id)
        assert metric["status"] == "BLOCKED_MISSING_INPUT"
    assert next(metric for metric in partial["results"]["metrics"]
                if metric["metric_id"] == "revenue.year.1")["status"] == "CALCULATED"


def test_zero_fee_is_not_an_invented_expense(case):
    exported, methods, settlement = case
    revised = deepcopy(settlement)
    for metric in revised["results"]["metrics"]:
        if metric["metric_id"].startswith("revenue.year."):
            ledger = metric["details"]["ledger"]
            ledger["transaction_cost"] = Decimal(0)
            ledger["benefit_after_transaction_cost"] = ledger["gross_benefit"]
    revised = seal_result(revised)
    rows = calculate_financial_ledger(exported, methods, revised)["evidence"]["financial-ledger"]["annual"]
    assert all(row["transaction_cost_cash_paid"] == 0 for row in rows[1:])
    vectors = _ledger_vectors(rows)
    assert all(vectors["benefit"][index] == row["revenue_cash_receipts"] + row["self_use_avoided_expenditure"]
               for index, row in enumerate(rows[1:], 1))


def test_opex_and_collection_fractions_do_not_source_fee_payment(case):
    exported, methods, settlement = case
    changed = deepcopy(methods)
    changed["parameters"]["cash.opex_payment_fractions"]["value"][0] = Decimal(0)
    changed["parameters"]["cash.collection_fractions"]["value"][0] = Decimal(0)
    rows = calculate_financial_ledger(exported, changed, settlement)["evidence"]["financial-ledger"]["annual"]
    first_fee = next(metric for metric in settlement["results"]["metrics"]
                     if metric["metric_id"] == "revenue.year.1")["details"]["ledger"]["transaction_cost"]
    second_fee = next(metric for metric in settlement["results"]["metrics"]
                      if metric["metric_id"] == "revenue.year.2")["details"]["ledger"]["transaction_cost"]
    assert rows[1]["revenue_cash_receipts"] == 0
    assert first_fee > 0 and second_fee > 0
    assert rows[1]["transaction_cost_cash_paid"] is None
    assert rows[2]["transaction_cost_cash_paid"] is None
    assert rows[2]["transaction_cost_payable_closing"] is None
    assert rows[-1]["transaction_cost_payable_closing"] is None


def test_changing_opex_fraction_cannot_change_transaction_fee_payment(case):
    exported, methods, settlement = case
    altered = deepcopy(methods)
    altered["parameters"]["cash.opex_payment_fractions"]["value"][0] = Decimal(0)
    original = _financial(case)["evidence"]["financial-ledger"]["annual"][1]
    revised = calculate_financial_ledger(exported, altered, settlement)[
        "evidence"]["financial-ledger"]["annual"][1]
    assert revised["opex_cash_paid"] != original["opex_cash_paid"]
    assert original["transaction_cost_cash_paid"] is revised["transaction_cost_cash_paid"] is None
    assert revised["transaction_cost_accrued"] == original["transaction_cost_accrued"]


def test_missing_settlement_fee_source_is_not_silently_treated_as_zero(case):
    exported, methods, settlement = case
    incomplete = deepcopy(settlement)
    next(metric for metric in incomplete["results"]["metrics"]
         if metric["metric_id"] == "revenue.year.1")["details"]["ledger"].pop("transaction_cost")
    with pytest.raises(ContractError, match="UPSTREAM_REVENUE_LEDGER_INCOMPLETE"):
        calculate_financial_ledger(exported, methods, seal_result(incomplete))


def test_forged_fee_payment_parameter_cannot_bypass_frozen_method_contract(case):
    exported, methods, settlement = case
    invalid = deepcopy(methods)
    invalid["parameters"]["cash.transaction_fee_payment_fractions"] = deepcopy(
        invalid["parameters"]["cash.opex_payment_fractions"])
    with pytest.raises(ContractError, match="METHOD_CONFIG_SCHEMA"):
        calculate_financial_ledger(exported, invalid, settlement)


def test_changed_settlement_fee_reaches_tax_basis_but_not_unbacked_cash(case):
    exported, methods, settlement = case
    original = _financial(case)["evidence"]["financial-ledger"]["annual"]
    revised = deepcopy(settlement)
    source = next(metric for metric in revised["results"]["metrics"]
                  if metric["metric_id"] == "revenue.year.1")["details"]["ledger"]
    source["transaction_cost"] += Decimal(1)
    source["benefit_after_transaction_cost"] -= Decimal(1)
    changed = calculate_financial_ledger(exported, methods, seal_result(revised))[
        "evidence"]["financial-ledger"]["annual"]
    before, after = _ledger_vectors(original), _ledger_vectors(changed)
    assert changed[1]["revenue_cash_receipts"] == original[1]["revenue_cash_receipts"]
    assert abs(changed[1]["transaction_cost_accrued"] - original[1]["transaction_cost_accrued"] - 1) < Decimal("0.000000000000000001")
    assert changed[1]["transaction_cost_cash_paid"] is original[1]["transaction_cost_cash_paid"] is None
    assert changed[1]["taxable_income_project"] < original[1]["taxable_income_project"]
    assert changed[1]["cash_tax_total_project"] < original[1]["cash_tax_total_project"]
    assert after["benefit"] is before["benefit"] is None
    assert changed[2]["transaction_cost_cash_paid"] is original[2]["transaction_cost_cash_paid"] is None


def test_net_price_has_no_second_cash_deduction():
    settlement = {"boundaries": {"SETTLEMENT": {"fee_treatment": "ALREADY_IN_PRICE"}},
                  "results": {"metrics": [{"metric_id": "revenue.year.1", "status": "CALCULATED",
                                           "details": {"ledger": {"gross_benefit": Decimal(90),
                                                                  "benefit_after_transaction_cost": Decimal(90),
                                                                  "export_sales_revenue": Decimal(90),
                                                                  "self_value": Decimal(0),
                                                                  "transaction_cost": Decimal(0),
                                                                  "embedded_transaction_cost": Decimal(10)}}}]}}
    assert _annual_revenue(settlement, 1, "ALREADY_IN_PRICE", Decimal("0.000001"))[0]["transaction_cost"] == 0
    rows = [{"period": "CONSTRUCTION", "capex_cash_paid": Decimal(0), "working_capital_increase": Decimal(0),
             "debt_drawdown": Decimal(0), "principal_paid": Decimal(0), "interest_paid": Decimal(0),
             "finance_fees_paid": Decimal(0)},
            {"period": "OPERATING_YEAR_1", "revenue_cash_receipts": Decimal(90),
             "self_use_avoided_expenditure": Decimal(0), "transaction_cost_cash_paid": Decimal(0),
             "opex_cash_paid": Decimal(4), "cash_tax_total_project": Decimal(1),
             "cash_tax_total_equity": Decimal(1), "capex_cash_paid": Decimal(0),
             "working_capital_increase": Decimal(0), "working_capital_release": Decimal(0),
             "debt_drawdown": Decimal(0), "principal_paid": Decimal(0),
             "interest_paid": Decimal(0), "finance_fees_paid": Decimal(0), "debt_service_due": Decimal(0)}]
    vector = _ledger_vectors(rows)
    assert vector["missing"] == {}
    assert vector["benefit"] == [Decimal(0), Decimal(90)]
    assert vector["transaction_cost"] == [Decimal(0), Decimal(0)]


def test_price_net_of_fee_cannot_be_reclassified_as_separately_paid():
    settlement = {"boundaries": {"SETTLEMENT": {"fee_treatment": "ALREADY_IN_PRICE"}},
                  "results": {"metrics": []}}
    with pytest.raises(ContractError, match="UPSTREAM_TRANSACTION_FEE_METHOD_MISMATCH"):
        _annual_revenue(settlement, 1, "SEPARATE_LEDGER", Decimal("0.000001"))
