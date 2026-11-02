"""Independent SYNTHETIC Phase 2→D3→3B→3C→3D price and cash reference."""
from copy import deepcopy
from decimal import Decimal as D
import os
from pathlib import Path
from uuid import uuid4

import pytest

from consumption_case_support import atom, axis, case, extend, load_rows, parameter, series_header
from energy_case_support import resource_header, resource_rows
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.calculation.break_even_financial_replay import (
    _check_financial, _check_settlement, replay_financial_candidate,
)
from wangbin_solar_pv.calculation.energy_yield import calculate_rooftop as generate
from wangbin_solar_pv.calculation.financial_ledger import calculate_financial_ledger
from wangbin_solar_pv.calculation.input_contract import validate_export
from wangbin_solar_pv.calculation.method_config import MethodConfig
from wangbin_solar_pv.calculation.result_contract import seal_result, validate_result
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.intake import IntakeSession
from wangbin_solar_pv.local_files import Workspace
from wangbin_solar_pv.provenance import make_record
from wangbin_solar_pv.serialization import digest, dumps, loads
from wangbin_solar_pv.timeseries_bundle import BundleBudget, read_bundle, write_bundle


def _row(catalog, family, row_id, values):
    return {"row_id": row_id, "fields": {
        family + "." + key: atom(catalog, family + "." + key, value, row_id + "-" + key)
        for key, value in values.items()}}


def _finance(session, methods):
    catalog = session.catalog
    scalar = {
        "schedule.commissioning_date": "2025-01-01", "finance.working_capital": D("200"),
        "finance.debt_ratio": D("0.5"), "finance.loan_rate": D("0.1"),
        "finance.loan_years": 1, "finance.grace_years": 0, "finance.repayment_method": "bullet",
        "tax.corporate_income_rate": D("0.25"), "tax.vat_output_rate": D("0.13"),
        "tax.surcharge_rate": D("0"),
    }
    for fid, value in scalar.items():
        session.project.values[fid] = atom(catalog, fid, value)
    session.project.values["capex.items"] = atom(catalog, "capex.items", [
        _row(catalog, "capex.items", "SYNTHETIC-capex-1", {
            "row_id": "SYNTHETIC-capex-1", "category": "modules", "description": "SYNTHETIC financed construction",
            "quantity": 1, "quantity_unit": "set", "unit_price": D("1130"), "amount": D("1130"),
            "tax_included": True, "vat_rate": D("0.13"), "recoverable_vat_share": 1,
            "quote_date": "2024-10-01", "quote_valid_until": "2025-10-01",
            "quote_attachment_id": "SYNTHETIC-capex-quote", "payment_date": "2024-12-01",
            "currency": "CNY", "fx_rate": 1, "asset_id": "SYNTHETIC-asset",
        }),
    ])
    session.project.values["opex.items"] = atom(catalog, "opex.items", [
        _row(catalog, "opex.items", "SYNTHETIC-opex-1", {
            "row_id": "SYNTHETIC-opex-1", "category": "operations", "base_amount": D("113"),
            "from_year": 1, "to_year": 1, "escalation_rate": D(0),
            "tax_included": True, "vat_rate": D("0.13"), "recoverable_vat_share": 1,
            "contract_id": "SYNTHETIC-opex-contract",
        }),
    ])
    session.project.values["assets.depreciation"] = atom(catalog, "assets.depreciation", [
        _row(catalog, "assets.depreciation", "SYNTHETIC-asset-depreciation", {
            "row_id": "SYNTHETIC-asset-depreciation", "asset_id": "SYNTHETIC-asset",
            "asset_class": "modules", "depreciable_basis": D("1000"),
            "depreciation_years": 1, "method": "straight_line", "residual_value": D(0),
            "in_service_date": "2025-01-01", "tax_basis_reference": "SYNTHETIC-net-capex",
        }),
    ])
    config = methods.to_dict()
    config["parameters"].update({pid: parameter(pid, value) for pid, value in {
        "cash.method": "ACCRUAL_WORKING_CAPITAL", "cash.self_use_treatment": "INCREMENTAL_AVOIDED_EXPENDITURE",
        "cash.collection_fractions": [D("0.75")], "cash.opex_payment_fractions": [D(1)],
        "cash.capex_payment_fractions": [D(1), D(0)], "cash.tax_payment_fractions": [D("0.5")],
        "cash.vat_payment_fractions": [D(1)], "cash.opening_cash": D(0),
        "cash.opening_receivables": D(0), "cash.opening_advances": D(0),
        "cash.terminal_collection_fraction": D(0),
        "tax.method": "EXPLICIT_SCENARIO_LEDGER", "tax.loss_usage_fraction": D(1),
        "tax.opening_project_losses": D("34000"), "tax.opening_equity_losses": D("34000"),
        "tax.opening_income_payable": D(0), "tax.opening_income_prepaid": D(0),
        "tax.opening_vat_credit": D(0), "tax.opening_vat_payable": D(0),
        "tax.self_use_basis": "NONTAXABLE_DECLARED_SCENARIO",
        "tax.asset_depreciation_timing": "FULL_OPERATION_YEAR", "tax.vat_refund_fraction": D(0),
        "debt.drawdown_basis": "CAPEX_PROPORTIONAL_SCENARIO",
        "debt.principal_payment_fractions": [D(0), D(1)],
        "debt.interest_payment_fractions": [D(0), D(1)],
        "debt.interest_capitalization_fractions": [D(0), D(0)],
        "debt.fee_payment_fractions": [D(0), D(1)],
        "debt.opening_principal": D(0), "debt.opening_interest_payable": D(0),
        "time.day_count": "ACT_365F",
        "break_even.minimum_price": D(0), "break_even.maximum_price": D(2),
        "break_even.price_tolerance": D("0.000001"), "break_even.maximum_iterations": 256,
        "break_even.method": "CERTIFIED_MONOTONE_RECALCULATION",
    }.items()})
    if session.project.values.get("finance.project_discount_rate") is not None:
        config["parameters"]["time.cashflow_timing"] = parameter("time.cashflow_timing", "YEAR_END")
    return MethodConfig.from_dict(config)


def _control(exported, methods, bundle_hash, generation_hash):
    price_row = exported["project"]["values"]["tariff.periods"]["value"][0]
    atom_price = price_row["fields"]["tariff.periods.sale_price"]
    return {"schema_version": "solar-pv-break-even-execution/1.0.0", "formula_id": "F-BREAK-EVEN-PRICE",
            "project_id": exported["project"]["project_id"], "pv_type": "industrial_rooftop",
            "basis": "项目税后", "original_input_hash": exported["input_hash"],
            "original_source_snapshot_id": exported["source_snapshot_id"],
            "original_dataset_content_hash": bundle_hash, "generation_result_hash": generation_hash,
            "method_config_hash": methods.hash,
            "selector": {"field_id": "tariff.periods.sale_price", "row_id": price_row["row_id"],
                         "field_instance_id": atom_price["field_instance_id"], "original_atom_hash": digest(atom_price),
                         "unit": atom_price["unit"], "economic_basis": atom_price["economic_basis"]},
            "source": {"source_kind": "SYNTHETIC", "status": "ASSUMED",
                       "source_id": "SYNTHETIC:p2-3a", "source_reference": "SYNTHETIC:p2-3a:price",
                       "license_status": "AUTHORIZED"}}


def _build_financial_case(*, evaluation_date=None, project_rate=None):
    root = Path(os.environ["TMPDIR"]) / ("synthetic-p2-3a-finance-" + uuid4().hex)
    root.mkdir(mode=0o700)
    catalog = Catalog()
    budget = BundleBudget(max_seconds=1800)
    session, generation_methods = case(catalog, "industrial_rooftop", years=1)
    session, settlement_methods = extend(session, generation_methods)
    if evaluation_date is not None:
        session.project.values["project.evaluation_date"] = atom(catalog, "project.evaluation_date", evaluation_date)
    session.project.values["project.cashflow_tax_basis"] = atom(catalog, "project.cashflow_tax_basis", "post_tax")
    if project_rate is not None:
        for fid, value in (
            ("project.cashflow_tax_basis", "post_tax"),
            ("project.ownership_mode", "owner_invested"),
            ("project.price_basis", "nominal"),
            ("finance.project_discount_rate", project_rate),
        ):
            session.project.values[fid] = make_record(
                catalog, fid, value, source_kind="ASSUMPTION",
                source_id="SYNTHETIC-project-npv-basis",
                source_url_or_attachment="SYNTHETIC:project-post-tax-nominal-CNY-year-end",
                source_section_or_cell="PROJECT_POST_TAX_NOMINAL_CNY_YEAR_END",
                confidence_basis="SYNTHETIC post-tax nominal CNY project year-end evaluation assumption",
                license_status="AUTHORIZED",
                assumption={"reason": "Explicit independent synthetic project NPV scope",
                            "method": "Scenario assumption, not a verified enterprise discount rate",
                            "maturity_ceiling": "L1", "noncritical": False,
                            "decision_invariant": False},
            )
    methods = _finance(session, settlement_methods)
    generation_input = validate_export(session.export(), catalog).export
    write_bundle(root / "resource", base_export=generation_input,
                 datasets={"resource.timeseries": {"header": resource_header(catalog), "rows": resource_rows(catalog)}},
                 catalog=catalog, budget=budget)
    with read_bundle(root / "resource", catalog=catalog, budget=budget) as resource:
        # Physical generation must retain these assets, but need not claim that
        # later cash/tax forecasting controls were used by the physical engine.
        generation = generate(generation_input, settlement_methods, catalog=catalog,
                              output_dir=root / "generation", budget=budget, bundle=resource)
    exported = generation_input
    period = axis()
    write_bundle(root / "original", base_export=exported,
                 datasets={"resource.timeseries": {"header": resource_header(catalog), "rows": resource_rows(catalog)},
                           "load.series": {"header": series_header(catalog, "load.series", period),
                                           "rows": load_rows(catalog, period)}},
                 catalog=catalog, budget=budget)
    with read_bundle(root / "original", catalog=catalog, budget=budget) as bundle:
        control = _control(exported, methods, bundle.content_hash, generation["result_hash"])
    return root, catalog, budget, exported, methods, control, generation["result_hash"]


@pytest.fixture(scope="module")
def financial_case():
    return _build_financial_case()


def _execute(info, price, name):
    root, catalog, budget, exported, methods, control, _ = info
    with read_bundle(root / "original", catalog=catalog, budget=budget) as bundle:
        return replay_financial_candidate(control, exported, methods, bundle, root / "generation", price,
                                          catalog=catalog, budget=budget, workspace=Workspace(root), run_name=name)


def _annual(result):
    return result["evidence"]["financial-ledger"]["annual"][1]


@pytest.fixture(scope="module")
def replays(financial_case):
    first = _execute(financial_case, D("0.6"), "financial-first")
    second = _execute(financial_case, D("0.8"), "financial-second")
    repeated = _execute(financial_case, D("0.6"), "financial-repeated")
    return first, second, repeated


def test_b1_cash_invoices_receivables_and_real_receipts(financial_case, replays):
    root, catalog, budget, exported, methods, control, generation_hash = financial_case
    first, second, repeated = replays
    for outcome, price in ((first, D("0.6")), (second, D("0.8"))):
        validate_result(outcome.original_financial, catalog)
        validate_result(outcome.candidate_financial, catalog)
        expected_original = D("87600") * D("0.4")
        expected_candidate = D("87600") * price
        for ledger, expected in ((_annual(outcome.original_financial), expected_original),
                                 (_annual(outcome.candidate_financial), expected_candidate)):
            assert ledger["invoiced_gross"] == expected
            assert ledger["revenue_cash_receipts"] == expected * D("0.75")
            assert ledger["accounts_receivable_closing"] == expected * D("0.25")
            assert ledger["receivables_terminal_collection"] == 0
            assert ledger["self_use_avoided_expenditure"] > 0
            assert ledger["working_capital_release"] == D("200")
        assert outcome.settlement.original_input_hash == exported["input_hash"]
        assert outcome.settlement.generation_result_hash == generation_hash
        assert outcome.settlement.original_bundle_hash != outcome.settlement.candidate_bundle_hash
        assert outcome.settlement.candidate_export["input_hash"] != exported["input_hash"]
        assert outcome.original_financial["result_hash"] != outcome.candidate_financial["result_hash"]
        assert outcome.original_financial["inputs"]["upstream_settlement_result_hash"] == outcome.settlement.original_revenue["result_hash"]
        assert outcome.candidate_financial["inputs"]["upstream_settlement_result_hash"] == outcome.settlement.candidate_revenue["result_hash"]
        assert outcome.candidate_financial["source_snapshot"]["phase2"] == outcome.settlement.candidate_export["source_snapshot"]
        assert control["source"]["source_id"] in outcome.candidate_financial["inputs"]["used_sources"]
    assert first.candidate_financial["result_hash"] != second.candidate_financial["result_hash"]
    assert first.candidate_financial["source_snapshot_id"] != second.candidate_financial["source_snapshot_id"]
    assert repeated.candidate_financial["result_hash"] == first.candidate_financial["result_hash"]
    assert repeated.settlement.candidate_revenue["result_hash"] == first.settlement.candidate_revenue["result_hash"]
    assert repeated.settlement.candidate_bundle_hash == first.settlement.candidate_bundle_hash
    assert digest(exported) == digest(validate_export(exported, catalog).export)
    for name, expected in (("original-3d", first.original_financial),
                           ("candidate-3d", first.candidate_financial)):
        published = loads((root / "financial-first" / name / "result.json").read_bytes())
        validate_result(published, catalog)
        assert published["result_hash"] == expected["result_hash"]
        assert (root / "financial-first" / name / "result.sha256").read_text().strip() == expected["result_hash"]
    assert (root / "original" / "manifest.json").is_file()


def test_b2_independent_vat_loss_income_tax_debt_and_cash(financial_case, replays):
    for outcome, price in ((replays[0], D("0.6")), (replays[1], D("0.8"))):
        for result, p in ((outcome.original_financial, D("0.4")), (outcome.candidate_financial, price)):
            construction, year = result["evidence"]["financial-ledger"]["annual"]
            sales = D("87600") * p
            project_base = sales - D("100") - D("1000")
            equity_base = project_base - D("56.5")
            expected_project_tax = max(D(0), project_base - D("34000")) * D("0.25")
            expected_equity_tax = max(D(0), equity_base - D("34000")) * D("0.25")
            vat_output = sales - sales / D("1.13")
            vat_paid = vat_output - D("143")
            assert construction["capex_accrued"] == construction["capex_cash_paid"] == D("1130")
            assert construction["debt_drawdown"] == D("565")
            assert construction["working_capital_increase"] == D("200")
            assert year["taxable_income_project"] == project_base
            assert year["taxable_income_equity"] == equity_base
            assert year["tax_loss_project_closing"] == max(D(0), D("34000") - project_base)
            assert year["tax_loss_equity_closing"] == max(D(0), D("34000") - equity_base)
            assert year["income_tax_accrual_project"] == expected_project_tax
            assert year["income_tax_accrual_equity"] == expected_equity_tax
            assert year["income_tax_accrual"] == expected_equity_tax
            assert year["income_tax_cash_paid_project"] == expected_project_tax * D("0.5")
            assert year["income_tax_cash_paid"] == expected_equity_tax * D("0.5")
            assert year["vat_output"] == vat_output
            assert year["vat_input_eligible"] == D("143")
            assert year["vat_credit_closing"] == D(0)
            # The frozen annual row has no separate VAT-cash field; verify it
            # through the actual cash-tax bridge, not an invented result key.
            assert year["cash_tax_total"] - year["income_tax_cash_paid"] == vat_paid
            assert year["interest_accrued"] == year["interest_paid"] == D("56.5")
            assert year["principal_due"] == year["principal_paid"] == D("565")
            assert year["cash_tax_total"] == expected_equity_tax * D("0.5") + vat_paid
            assert year["cash_tax_total_project"] == expected_project_tax * D("0.5") + vat_paid
            assert year["phase3e_cashflow"] is None


def test_mismatched_financial_inputs_and_method_hash_rejected(financial_case, replays):
    root, catalog, budget, exported, methods, control, generation_hash = financial_case
    candidate = replays[0].settlement.candidate_revenue
    changed_method = methods.to_dict()
    changed_method["parameters"]["cash.collection_fractions"] = parameter("cash.collection_fractions", [D(1)])
    with pytest.raises(ContractError, match="BREAK_EVEN_SETTLEMENT_IDENTITY_MISMATCH"):
        _check_settlement(candidate, replays[0].settlement.candidate_export,
                          MethodConfig.from_dict(changed_method), replays[0].settlement.candidate_bundle_hash,
                          generation_hash, catalog)
    with pytest.raises(ContractError, match="BREAK_EVEN_SETTLEMENT_IDENTITY_MISMATCH"):
        _check_settlement(candidate, exported, methods, replays[0].settlement.candidate_bundle_hash,
                          generation_hash, catalog)
    with pytest.raises(ContractError, match="BREAK_EVEN_SETTLEMENT_IDENTITY_MISMATCH"):
        _check_settlement(candidate, replays[0].settlement.candidate_export, methods,
                          replays[0].settlement.candidate_bundle_hash, "0" * 64, catalog)
    with pytest.raises(ContractError, match="BREAK_EVEN_SETTLEMENT_IDENTITY_MISMATCH"):
        _check_settlement(replays[1].settlement.candidate_revenue,
                          replays[0].settlement.candidate_export, methods,
                          replays[0].settlement.candidate_bundle_hash, generation_hash, catalog)
    altered = deepcopy(replays[0].candidate_financial)
    altered["inputs"]["upstream_settlement_result_hash"] = replays[1].settlement.candidate_revenue["result_hash"]
    altered = seal_result(altered)
    with pytest.raises(ContractError, match="BREAK_EVEN_FINANCIAL_IDENTITY_MISMATCH"):
        _check_financial(altered, replays[0].settlement.candidate_revenue["result_hash"],
                         replays[0].settlement.candidate_export, methods, catalog)
    altered = deepcopy(replays[0].candidate_financial)
    altered["inputs"]["normalized"]["finance.working_capital"] = D("201")
    altered = seal_result(altered)
    with pytest.raises(ContractError, match="BREAK_EVEN_FINANCIAL_IDENTITY_MISMATCH"):
        _check_financial(altered, replays[0].settlement.candidate_revenue["result_hash"],
                         replays[0].settlement.candidate_export, methods, catalog)
    assert not (root / "cross-contaminated-3d").exists()


def test_missing_financial_input_fails_without_valid_ledger(financial_case, replays):
    root, catalog, budget, exported, methods, control, generation_hash = financial_case
    session = IntakeSession.from_dict(replays[0].settlement.candidate_export["project"], catalog)
    session.project.values.pop("capex.items")
    missing = validate_export(session.export(), catalog).export
    with pytest.raises(ContractError, match="BLOCKED_MISSING_INPUT"):
        calculate_financial_ledger(missing, methods, replays[0].settlement.candidate_revenue, catalog=catalog)
    assert not (root / "missing-financial-3d").exists()


def test_missing_financial_method_cleans_owned_run_after_valid_settlement(financial_case):
    root, catalog, budget, exported, methods, control, generation_hash = financial_case
    incomplete = methods.to_dict()
    incomplete["parameters"].pop("cash.collection_fractions")
    incomplete = MethodConfig.from_dict(incomplete)
    incomplete_control = deepcopy(control)
    incomplete_control["method_config_hash"] = incomplete.hash
    with read_bundle(root / "original", catalog=catalog, budget=budget) as bundle:
        with pytest.raises(ContractError, match="BLOCKED_METHOD_REVIEW"):
            replay_financial_candidate(incomplete_control, exported, incomplete, bundle,
                                       root / "generation", D("0.7"), catalog=catalog,
                                       budget=budget, workspace=Workspace(root), run_name="financial-incomplete")
    assert not (root / "financial-incomplete").exists()
    assert (root / "generation" / "result.json").is_file()
    assert (root / "original" / "manifest.json").is_file()
