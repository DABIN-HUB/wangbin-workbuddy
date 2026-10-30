"""Phase 3D synthetic finance bridges against independently computed balances."""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.intake import IntakeSession
from wangbin_solar_pv.models import ProjectData
from wangbin_solar_pv.serialization import loads
from wangbin_solar_pv.calculation.financial_ledger import calculate_financial_ledger
from wangbin_solar_pv.calculation.input_contract import validate_export
from wangbin_solar_pv.calculation.result_contract import validate_result

CASES = Path(__file__).resolve().parents[2] / "reports" / "solar-pv" / "phase3d-cases"


def case_files(kind):
    directory = CASES / kind
    return tuple(loads((directory / name).read_bytes()) for name in ("input.json", "methods.json", "settlement.json"))


@pytest.mark.parametrize("kind,invoice,avoided", [
    ("industrial_rooftop", Decimal("350400"), Decimal("1606000")),
    ("utility_scale_ground", Decimal("784750"), Decimal(0)),
])
def test_invoice_receivables_exclude_avoided_purchases(kind, invoice, avoided):
    exported, methods, settlement = updated_replacement_export(kind)
    result = calculate_financial_ledger(exported, methods, settlement)
    validate_result(result, Catalog())
    rows = result["evidence"]["financial-ledger"]["annual"]
    assert len(rows) == 26
    assert rows[1]["invoiced_gross"] == invoice
    assert rows[1]["revenue_cash_receipts"] == invoice
    assert rows[1]["self_use_avoided_expenditure"] == avoided
    assert all(row["accounts_receivable_closing"] == 0 for row in rows[1:])
    assert sum((row["revenue_cash_receipts"] for row in rows[1:]), Decimal(0)) == sum(
        (row["invoiced_gross"] for row in rows[1:]), Decimal(0))


def updated_replacement_export(kind):
    exported, methods, settlement = case_files(kind)
    catalog = Catalog()
    project = ProjectData.from_dict(exported["project"], catalog)
    parent = project.values["capex.items"]
    for replacement in project.values["assets.replacements"]["value"]:
        fields = replacement["fields"]
        year = fields["assets.replacements.year"]["value"]
        cost = fields["assets.replacements.cost"]["value"]
        asset = fields["assets.replacements.asset_id"]["value"]
        event = replacement["row_id"]
        row = deepcopy(parent["value"][0 if asset == "modules-asset" else 1])
        row["row_id"] = event + "-payment"
        changes = {
            "amount": cost, "asset_id": asset,
            "description": "SYNTHETIC explicit replacement payment",
            "payment_date": f"{2025 + year}-06-01",
            "quote_date": f"{2025 + year}-01-01",
            "quote_valid_until": f"{2025 + year}-12-31",
            "quantity": 1, "unit_price": cost,
            "quote_attachment_id": "SYNTHETIC-" + event,
            "row_id": row["row_id"], "tax_included": False,
            "vat_rate": Decimal(0), "recoverable_vat_share": Decimal(0),
        }
        for fid, record in row["fields"].items():
            field = fid.removeprefix("capex.items.")
            record["field_instance_id"] = row["row_id"] + "-" + field
            record["source_id"] = "SYNTHETIC-phase3d-repair"
            record["source_section_or_cell"] = record["field_instance_id"]
            record["source_url_or_attachment"] = "SYNTHETIC:explicit-replacement-payment"
            record["confidence_basis"] = "SYNTHETIC full payment in replacement year"
            if field in changes:
                record["original_value"] = record["value"] = changes[field]
        parent["value"].append(row)
    parent["original_value"] = deepcopy(parent["value"])
    updated = IntakeSession(project, catalog).export()
    validate_export(updated, catalog)
    return updated, methods, settlement


@pytest.mark.parametrize("kind,original_total", [
    ("industrial_rooftop", Decimal("1660000")),
    ("utility_scale_ground", Decimal("2510000")),
])
def test_replacement_payment_separate_from_asset_addition(kind, original_total):
    exported, methods, settlement = updated_replacement_export(kind)
    result = calculate_financial_ledger(exported, methods, settlement)
    validate_result(result, Catalog())
    ledger = result["evidence"]["financial-ledger"]
    rows = ledger["annual"]
    assert rows[0]["capex_cash_paid"] == original_total
    assert rows[0]["debt_drawdown"] == original_total * exported["normalized_inputs"]["finance.debt_ratio"]
    assert rows[12]["replacement_capex_accrued"] == Decimal("190000")
    assert rows[12]["replacement_cash_paid"] == Decimal("190000")
    assert rows[15]["replacement_capex_accrued"] == Decimal("720000")
    assert rows[15]["replacement_cash_paid"] == Decimal("720000")
    assert rows[-1]["capex_payable_closing"] == 0
    assert ledger["capex"]["total"] == original_total + Decimal("910000")
    assert sum((row["capex_cash_paid"] for row in rows), Decimal(0)) == ledger["capex"]["total"]


@pytest.mark.parametrize("kind", ["industrial_rooftop", "utility_scale_ground"])
def test_project_and_financed_income_taxes_are_separate_scenarios(kind):
    exported, methods, settlement = updated_replacement_export(kind)
    result = calculate_financial_ledger(exported, methods, settlement)
    first = result["evidence"]["financial-ledger"]["annual"][1]
    tax_rate = exported["normalized_inputs"]["tax.corporate_income_rate"]
    project_reference = max(Decimal(0), first["taxable_income_project"]) * tax_rate
    equity_reference = max(Decimal(0), first["taxable_income_equity"]) * tax_rate
    tolerance = Decimal("1e-18")
    assert abs(first["income_tax_accrual_project"] - project_reference) < tolerance
    assert abs(first["income_tax_accrual"] - equity_reference) < tolerance
    assert abs(first["income_tax_cash_paid"] - equity_reference) < tolerance
    assert first["income_tax_accrual_project"] != first["income_tax_accrual"]
    assert abs(first["tax_cash_bridge"] - first["income_tax_cash_paid"]) < tolerance


@pytest.mark.parametrize("kind", ["industrial_rooftop", "utility_scale_ground"])
def test_replacement_without_payment_source_cannot_be_assumed_paid_or_free(kind):
    exported, methods, settlement = case_files(kind)
    with pytest.raises(ContractError, match="REPLACEMENT_PAYMENT_SOURCE_REQUIRED"):
        calculate_financial_ledger(exported, methods, settlement)


def test_replacement_accrual_precedes_cash_payment_and_preserves_payable():
    exported, methods, settlement = updated_replacement_export("industrial_rooftop")
    project = ProjectData.from_dict(exported["project"], Catalog())
    row = next(r for r in project.values["capex.items"]["value"] if r["row_id"] == "replacement-inverter-payment")
    row["fields"]["capex.items.payment_date"]["value"] = "2038-06-01"
    row["fields"]["capex.items.payment_date"]["original_value"] = "2038-06-01"
    project.values["capex.items"]["original_value"] = deepcopy(project.values["capex.items"]["value"])
    exported = IntakeSession(project, Catalog()).export()
    rows = calculate_financial_ledger(exported, methods, settlement)["evidence"]["financial-ledger"]["annual"]
    assert rows[12]["replacement_capex_accrued"] == Decimal("190000")
    assert rows[12]["replacement_cash_paid"] == 0
    assert rows[12]["capex_payable_closing"] == Decimal("190000")
    assert rows[13]["replacement_cash_paid"] == Decimal("190000")
    assert rows[13]["capex_payable_closing"] == 0
    assert all(row["capex_payment_residual"] == 0 for row in rows)


def test_uncollected_invoices_and_unpaid_tax_remain_balances_not_cash():
    exported, methods, settlement = updated_replacement_export("industrial_rooftop")
    methods = deepcopy(methods)
    methods["parameters"]["cash.collection_fractions"]["value"][0] = Decimal("0.75")
    methods["parameters"]["cash.tax_payment_fractions"]["value"][0] = Decimal("0.5")
    rows = calculate_financial_ledger(exported, methods, settlement)["evidence"]["financial-ledger"]["annual"]
    assert rows[1]["revenue_cash_receipts"] == Decimal("262800")
    assert rows[1]["accounts_receivable_closing"] == Decimal("87600")
    assert abs(rows[25]["receivables_terminal_collection"] - Decimal("87600")) < Decimal("1e-18")
    assert rows[25]["accounts_receivable_closing"] == 0
    assert abs(rows[1]["income_tax_cash_paid"] * 2 - rows[1]["income_tax_accrual"]) < Decimal("1e-18")
    assert abs(rows[1]["income_tax_payable_closing"] - rows[1]["income_tax_cash_paid"]) < Decimal("1e-18")
