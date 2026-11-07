"""Trace separately billed settlement transaction fees into project cash, once."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.calculation.financial_ledger import _annual_revenue, calculate_financial_ledger
from wangbin_solar_pv.calculation.phase3e import _ledger_vectors
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


def test_gross_receipt_and_separate_fee_are_counted_once_in_all_25_cash_periods(case):
    _, _, settlement = case
    result = _financial(case)
    years = result["evidence"]["financial-ledger"]["annual"]
    vectors = _ledger_vectors(years)
    assert len(years) == 26 and vectors["missing"] == {}
    assert years[0]["period"] == "CONSTRUCTION"
    for index, row in enumerate(years[1:], 1):
        source = next(metric for metric in settlement["results"]["metrics"]
                      if metric["metric_id"] == f"revenue.year.{index}")["details"]["ledger"]
        fee = source["transaction_cost"]
        assert fee > 0
        assert row["transaction_cost_accrued"] == fee
        assert abs(row["transaction_cost_cash_paid"] - fee) < Decimal("0.000000000000000001")
        assert row["transaction_cost_payable_closing"] == 0
        assert abs(row["invoiced_gross"] - source["export_sales_revenue"]) < Decimal("0.000000000000000001")
        assert vectors["benefit"][index] == row["revenue_cash_receipts"] + row["self_use_avoided_expenditure"] - row["transaction_cost_cash_paid"]
        assert vectors["opex"][index] == row["opex_cash_paid"]
        assert row["taxable_income_project"] is not None  # Tax is a separate deduction, not fee payment.
    assert abs(sum(vectors["transaction_cost"][1:], Decimal(0)) - sum(
        metric["details"]["ledger"]["transaction_cost"] for metric in settlement["results"]["metrics"]
        if metric["metric_id"].startswith("revenue.year."))) < Decimal("0.000000000000000001")


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


def test_fee_payment_may_differ_from_collection_period_without_being_lost(case):
    exported, methods, settlement = case
    changed = deepcopy(methods)
    changed["parameters"]["cash.opex_payment_fractions"]["value"][0] = Decimal(0)
    changed["parameters"]["cash.collection_fractions"]["value"][0] = Decimal(0)
    rows = calculate_financial_ledger(exported, changed, settlement)["evidence"]["financial-ledger"]["annual"]
    first_fee = next(metric for metric in settlement["results"]["metrics"]
                     if metric["metric_id"] == "revenue.year.1")["details"]["ledger"]["transaction_cost"]
    second_fee = next(metric for metric in settlement["results"]["metrics"]
                      if metric["metric_id"] == "revenue.year.2")["details"]["ledger"]["transaction_cost"]
    assert rows[1]["revenue_cash_receipts"] == rows[1]["transaction_cost_cash_paid"] == 0
    assert abs(rows[1]["transaction_cost_payable_closing"] - first_fee) < Decimal("0.000000000000000001")
    assert abs(rows[2]["transaction_cost_cash_paid"] - (first_fee + second_fee)) < Decimal("0.000000000000000001")
    assert rows[2]["transaction_cost_payable_closing"] == 0
    assert rows[-1]["transaction_cost_payable_closing"] == 0


def test_missing_settlement_fee_source_is_not_silently_treated_as_zero(case):
    exported, methods, settlement = case
    incomplete = deepcopy(settlement)
    next(metric for metric in incomplete["results"]["metrics"]
         if metric["metric_id"] == "revenue.year.1")["details"]["ledger"].pop("transaction_cost")
    with pytest.raises(ContractError, match="UPSTREAM_REVENUE_LEDGER_INCOMPLETE"):
        calculate_financial_ledger(exported, methods, seal_result(incomplete))


def test_changed_settlement_fee_reaches_tax_basis_and_phase3e_benefit(case):
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
    assert changed[1]["transaction_cost_cash_paid"] - original[1]["transaction_cost_cash_paid"] == 1
    assert changed[1]["taxable_income_project"] < original[1]["taxable_income_project"]
    assert changed[1]["cash_tax_total_project"] < original[1]["cash_tax_total_project"]
    assert after["benefit"][1] - before["benefit"][1] == -1
    assert changed[2]["transaction_cost_cash_paid"] == original[2]["transaction_cost_cash_paid"]


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
