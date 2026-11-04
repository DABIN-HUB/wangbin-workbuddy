"""One scoped 1-year SYNTHETIC producer replay; no sealed-project claims."""
from decimal import Decimal as D

from test_phase3e_financial_candidate_replay import _build_financial_case
from test_phase3f_scenario_runner import _control, _input
from wangbin_solar_pv.calculation.revenue import calculate_rooftop as settle
from wangbin_solar_pv.calculation.scenario_runner import prepare_scenario, run_scenario
from wangbin_solar_pv.calculation.result_contract import validate_result
from wangbin_solar_pv.local_files import Workspace
from wangbin_solar_pv.serialization import digest, dumps, loads
from wangbin_solar_pv.timeseries_bundle import read_bundle


def _result(root, name, phase, catalog):
    result = loads((root / name / f"scenario-{phase}" / "result.json").read_bytes())
    validate_result(result, catalog)
    return result


def test_one_sourced_price_opex_and_loan_replay_from_real_producers():
    root, catalog, budget, export, methods, _, generation_hash = _build_financial_case()
    source_before = dumps(export), dumps(methods.to_dict())
    with read_bundle(root / "original", catalog=catalog, budget=budget) as bundle:
        baseline = settle(export, methods, generation_dir=root / "generation",
                          generation_result_hash=generation_hash, catalog=catalog,
                          output_dir=root / "baseline-3c", budget=budget, bundle=bundle)
        price = _input(export, "SALE_PRICE", "tariff.periods.sale_price", D("0.6"), "flat")
        prepared_price = prepare_scenario(_control(export, methods, rid="scenario-price", changes=[price]),
                                          export, methods, catalog)
        priced = run_scenario(prepared_price, export, methods, catalog=catalog, budget=budget,
                              workspace=Workspace(root), original_bundle=bundle,
                              generation_dir=root / "generation", generation_result_hash=generation_hash)
    price_result = _result(root, "scenario-price", "3c", catalog)
    old_revenue = next(m for m in baseline["results"]["metrics"] if m["metric_id"] == "revenue.year.1")
    new_revenue = next(m for m in price_result["results"]["metrics"] if m["metric_id"] == "revenue.year.1")
    # The pinned physical export kWh is a source input to this independent
    # arithmetic check; expected money is not produced by the new scenario.
    assert new_revenue["details"]["ledger"]["export_sales_revenue"] - old_revenue["details"]["ledger"]["export_sales_revenue"] == old_revenue["details"]["ledger"]["export_kwh"] * D("0.2")
    assert priced["stage_result_hashes"]["3C"] == price_result["result_hash"]
    assert priced["reused_generation_result_hash"] == generation_hash
    assert priced["stage_result_hashes"]["3D"] != priced["stage_result_hashes"]["3C"]

    opex = _input(export, "OPERATING_MAINTENANCE", "opex.items.base_amount", D("226"), "SYNTHETIC-opex-1")
    prepared_opex = prepare_scenario(_control(export, methods, rid="scenario-opex", changes=[opex]),
                                     export, methods, catalog)
    expense = run_scenario(prepared_opex, export, methods, catalog=catalog, budget=budget,
                            workspace=Workspace(root), original_settlement=baseline)
    expense_result = _result(root, "scenario-opex", "3d", catalog)
    assert expense["reused_settlement_result_hash"] == baseline["result_hash"]
    assert expense_result["evidence"]["financial-ledger"]["annual"][1]["opex_accrued"] == D("226")
    assert expense_result["evidence"]["financial-ledger"]["opex"]["net"]["1"] == D("200")
    assert expense_result["results"]["domains"]["revenue"] == baseline["results"]["domains"]["revenue"]

    loan = _input(export, "LOAN_INTEREST", "finance.loan_rate", D("0.2"))
    prepared_loan = prepare_scenario(_control(export, methods, rid="scenario-loan", changes=[loan]),
                                     export, methods, catalog)
    debt = run_scenario(prepared_loan, export, methods, catalog=catalog, budget=budget,
                        workspace=Workspace(root), original_settlement=baseline)
    debt_result = _result(root, "scenario-loan", "3d", catalog)
    annual = debt_result["evidence"]["financial-ledger"]["annual"][1]
    assert annual["interest_accrued"] == D("113")  # 1130 capex × 0.5 debt ratio × 0.2 declared rate
    assert debt_result["evidence"]["financial-ledger"]["capex"]["total"] == D("1130")
    assert debt["result_hash"] == digest({k: v for k, v in debt.items() if k not in {"result_hash", "elapsed_seconds"}})
    assert (dumps(export), dumps(methods.to_dict())) == source_before
    for run in (priced, expense, debt):
        assert run["elapsed_seconds"] > 0
        phase3e = _result(root, run["run_id"], "3e", catalog)
        blocked = next(m for m in phase3e["results"]["metrics"] if m["metric_id"] == "financial.phase3e.project_npv")
        assert blocked["status"] == "BLOCKED_MISSING_INPUT" and blocked["value"] is None
