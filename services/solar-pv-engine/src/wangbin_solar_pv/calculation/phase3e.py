"""Phase 3E orchestration over the sealed Phase 3D financial ledger.

This layer consumes the existing ledger and emits the canonical result shape.
It never invents terminal proceeds, owner cash events, dated events, targets, or
instantaneous bank balances.  Missing frozen inputs become metric-level blocked
states while independent CFADS/DSCR and rate calculations may still proceed.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal

from ..errors import ContractError
from ..serialization import dumps
from ..timeseries_private import local_target
from .financial_metrics import evaluate
from .result_contract import seal_result, validate_result

_BOUNDARY = "PHASE3E_FINANCIAL_EVALUATION"


def _metric(result, catalog, metric_id, formula_id, value, unit, period, *, status="CALCULATED", reason=None, details=None):
    result["results"]["metrics"].append({
        "metric_id": metric_id, "value": value, "unit": unit, "status": status,
        "reason": reason, "boundary_id": _BOUNDARY, "period": period,
        "scenario_id": result["scenario_id"],
        "input_field_ids": list(result["inputs"].get("used_fields", [])),
        "source_ids": sorted(set(result["inputs"].get("used_sources", [])) | {
            p["source_id"] for p in result["source_snapshot"].get("methods", {}).get("parameters", {}).values()
        }),
        "formula_id": formula_id,
        "formula_version": catalog.definition_version,
        "evidence_ids": list(result["evidence"]), "report_locations": catalog.formulas[formula_id]["report_chapter_ids"],
        "workbook_locations": [], "rounding_rule": "DECLARED_DECIMAL_NO_DISPLAY_ROUNDING",
        "method_parameter_ids": sorted(result["source_snapshot"].get("methods", {}).get("parameters", {})),
        "upstream_metric_ids": [], "details": details or {},
    })


def _record(result, catalog, metric_id, formula_id, values, unit, period, *, options=None, blocked_reason=None, blocked_details=None):
    if blocked_reason:
        _metric(result, catalog, metric_id, formula_id, None, unit, period,
                status="BLOCKED_MISSING_INPUT", reason=blocked_reason, details=blocked_details)
        return {"status": "BLOCKED_MISSING_INPUT", "value": None, "reason": blocked_reason, "details": blocked_details or {}}
    outcome = evaluate(formula_id, values, options)
    if outcome["status"] == "CALCULATED":
        _metric(result, catalog, metric_id, formula_id, outcome["value"], unit, period, details=outcome.get("details"))
    else:
        _metric(result, catalog, metric_id, formula_id, None, unit, period,
                status=outcome["status"], reason=outcome["reason"], details=outcome.get("details"))
    return outcome


def _ledger_vectors(annual):
    rows = annual[1:]
    benefit = [Decimal(0)] + [row["revenue_cash_receipts"] + row["self_use_avoided_expenditure"] for row in rows]
    opex = [Decimal(0)] + [row["opex_cash_paid"] for row in rows]
    project_tax = [Decimal(0)] + [row["cash_tax_total_project"] for row in rows]
    equity_tax = [Decimal(0)] + [row["cash_tax_total_equity"] for row in rows]
    capex = [row["capex_cash_paid"] for row in annual]
    working_capital = [row.get("working_capital_increase", Decimal(0)) - row.get("working_capital_release", Decimal(0)) for row in annual]
    debt_drawdown = [row.get("debt_drawdown", Decimal(0)) for row in annual]
    principal = [row.get("principal_paid", Decimal(0)) for row in annual]
    interest = [row.get("interest_paid", Decimal(0)) for row in annual]
    fees = [Decimal(0)] * len(annual)
    debt_service = [row.get("debt_service_due", Decimal(0)) for row in rows]
    return {
        "benefit": benefit, "opex": opex, "project_tax": project_tax,
        "equity_tax": equity_tax, "capex": capex, "working_capital": working_capital,
        "debt_drawdown": debt_drawdown, "principal": principal,
        "interest": interest, "fees": fees, "debt_service": debt_service,
    }


def calculate_phase3e(financial_result, methods, catalog):
    """Attach Phase 3E metric results to a validated Phase 3D result.

    The returned object remains a single canonical calculation result.  The
    caller is responsible for writing it to a new output directory.
    """
    validate_result(financial_result, catalog)
    result = deepcopy(financial_result)
    result["boundaries"][_BOUNDARY] = {
        "phase": "3E", "cashflow_timing": "PERIOD_END",
        "instantaneous_bank_coverage": "OUTSIDE_FROZEN_PHASE3E_COMMON_GATE",
        "terminal_cash_policy": "BLOCKED_WHEN_NOT_EXPLICITLY_SOURCED",
    }
    result["formula_snapshot"]["financial_definitions"].update({fid: catalog.formulas[fid] for fid in (
        "F-PROJECT-CASH-FLOW", "F-PROJECT-PRETAX-CASH-FLOW", "F-EQUITY-AVAILABLE-CASH-FLOW",
        "F-EQUITY-INVESTOR-CASH-FLOW", "F-CASH-FUNDING-BALANCE", "F-NPV", "F-DATED-NPV",
        "F-NOMINAL-REAL-RATE", "F-IRR-PROJECT", "F-IRR-EQUITY", "F-CUMULATIVE-CASH-FLOW",
        "F-STATIC-PAYBACK", "F-DISCOUNTED-CUMULATIVE-CASH", "F-DYNAMIC-PAYBACK",
        "F-LIFECYCLE-COST", "F-LCOE", "F-CFADS", "F-DSCR", "F-BREAK-EVEN-PRICE",
        "F-WORST-CASH-YEAR", "F-INVESTMENT-HURDLE-GAP")})
    result["metrics_before_phase3e"] = len(result["results"]["metrics"])
    result["results"]["metrics"] = [m for m in result["results"]["metrics"] if not m["metric_id"].startswith("financial.phase3e.")]
    ledger = result.get("evidence", {}).get("financial-ledger", {})
    annual = ledger.get("annual")
    if not isinstance(annual, list) or len(annual) < 2:
        raise ContractError("PHASE3D_LEDGER_MISSING")
    vectors = _ledger_vectors(annual)
    result["evidence"]["phase3e-financial"] = {
        "periods": [row["period"] for row in annual],
        "operating_periods": [row["period"] for row in annual[1:]],
        "vectors": deepcopy(vectors),
        "terminal_cash": "BLOCKED_MISSING_INPUT",
        "owner_cash_events": "BLOCKED_MISSING_INPUT",
        "dated_cash_events": "BLOCKED_MISSING_INPUT",
        "investment_targets": "BLOCKED_MISSING_INPUT",
        "instantaneous_payment_coverage": "INDETERMINATE_PRESERVED",
    }

    # The explicit Phase 3D ledger contains no sourced terminal asset cash
    # realization.  Keep all formulas that depend on it blocked rather than
    # silently treating residual book values as cash.
    terminal_missing = {"missing_field_ids": ["finance.project_terminal_cash"], "policy": "NO_DEFAULT_ZERO"}
    project_values = {
        "finance.project_operating_cash_benefit": vectors["benefit"],
        "opex.cash_annual": vectors["opex"],
        "tax.project_cash_total": vectors["project_tax"],
        "capex.unlevered_cash_annual": vectors["capex"],
        "working_capital.project_net_change": vectors["working_capital"],
        "finance.project_terminal_cash": None,
    }
    _record(result, catalog, "financial.phase3e.project_cash_flow", "F-PROJECT-CASH-FLOW", project_values, "CNY", "26_PERIODS", blocked_reason="BLOCKED_MISSING_INPUT", blocked_details=terminal_missing)
    for formula_id, metric_id in (("F-PROJECT-PRETAX-CASH-FLOW", "financial.phase3e.project_pretax_cash_flow"), ("F-NPV", "financial.phase3e.project_npv"), ("F-IRR-PROJECT", "financial.phase3e.project_irr"), ("F-CUMULATIVE-CASH-FLOW", "financial.phase3e.cumulative_cash_flow"), ("F-STATIC-PAYBACK", "financial.phase3e.static_payback"), ("F-DISCOUNTED-CUMULATIVE-CASH", "financial.phase3e.discounted_cumulative_cash"), ("F-DYNAMIC-PAYBACK", "financial.phase3e.dynamic_payback"), ("F-WORST-CASH-YEAR", "financial.phase3e.worst_cash_year")):
        _record(result, catalog, metric_id, formula_id, {}, "CNY", "26_PERIODS", blocked_reason="BLOCKED_UPSTREAM_PROJECT_CASH_FLOW", blocked_details={"upstream_formula_id": "F-PROJECT-CASH-FLOW"})

    # A nominal/real bridge is independent of project terminal evidence.
    normalized = result["inputs"].get("normalized", {})
    if "finance.project_discount_rate" in normalized and "finance.inflation_rate" in normalized:
        _record(result, catalog, "financial.phase3e.nominal_discount_rate", "F-NOMINAL-REAL-RATE", {
            "finance.real_discount_rate": normalized["finance.project_discount_rate"],
            "finance.general_inflation": normalized["finance.inflation_rate"],
        }, "1", "LIFECYCLE")
    else:
        _record(result, catalog, "financial.phase3e.nominal_discount_rate", "F-NOMINAL-REAL-RATE", {}, "1", "LIFECYCLE", blocked_reason="BLOCKED_MISSING_INPUT", blocked_details={"missing_field_ids": ["finance.project_discount_rate", "finance.inflation_rate"]})

    # CFADS is a declared synthetic method scenario.  Mandatory operating
    # capex is limited to operating-year payments; construction is outside the
    # debt-service period.  No debt service is deducted from CFADS itself.
    cfads_values = {
        "finance.project_operating_cash_benefit": vectors["benefit"][1:],
        "opex.cash_annual": vectors["opex"][1:],
        "tax.equity_cash_total": vectors["equity_tax"][1:],
        "debt.cfads_working_capital_change": vectors["working_capital"][1:],
        "debt.cfads_mandatory_capex": vectors["capex"][1:],
        "debt.cfads_adjustments": [Decimal(0)] * (len(annual) - 1),
    }
    cfads = _record(result, catalog, "financial.phase3e.cfads", "F-CFADS", cfads_values, "CNY", "OPERATING_YEARS")
    if cfads["status"] == "CALCULATED":
        _record(result, catalog, "financial.phase3e.dscr", "F-DSCR", {"debt.cfads": cfads["value"], "debt.service_due": vectors["debt_service"]}, "1", "OPERATING_YEARS")
    else:
        _record(result, catalog, "financial.phase3e.dscr", "F-DSCR", {}, "1", "OPERATING_YEARS", blocked_reason="BLOCKED_UPSTREAM_CFADS", blocked_details={"upstream_formula_id": "F-CFADS"})

    missing = {
        "F-EQUITY-AVAILABLE-CASH-FLOW": "BLOCKED_MISSING_OWNER_TERMINAL_CASH",
        "F-EQUITY-INVESTOR-CASH-FLOW": "BLOCKED_MISSING_OWNER_CASH_EVENTS",
        "F-CASH-FUNDING-BALANCE": "BLOCKED_MISSING_ENTITY_OPENING_AND_OWNER_EVENTS",
        "F-DATED-NPV": "BLOCKED_MISSING_DATED_CASH_EVENTS",
        "F-IRR-EQUITY": "BLOCKED_MISSING_OWNER_CASH_EVENTS",
        "F-LIFECYCLE-COST": "BLOCKED_MISSING_TERMINAL_CASH",
        "F-LCOE": "BLOCKED_MISSING_TERMINAL_COST_BOUNDARY",
        "F-BREAK-EVEN-PRICE": "BLOCKED_MISSING_FULL_CHAIN_PRICE_RECALCULATION",
        "F-INVESTMENT-HURDLE-GAP": "BLOCKED_MISSING_USER_TARGET",
    }
    for formula_id, reason in missing.items():
        _record(result, catalog, "financial.phase3e." + formula_id.lower().replace("f-", ""), formula_id, {}, "CNY", "PROJECT", blocked_reason=reason, blocked_details={"project_result": "BLOCKED_MISSING_INPUT"})

    result["evidence"]["phase3e-financial"]["metric_count"] = len(result["results"]["metrics"]) - result["metrics_before_phase3e"]
    del result["metrics_before_phase3e"]
    result["findings"] = [f for f in result.get("findings", []) if f.get("code") != "PHASE3E_CASHFLOW_AND_FINANCIAL_RETURNS_NOT_IMPLEMENTED"]
    result["findings"].append({"code": "PHASE3E_PARTIAL_MISSING_FROZEN_INPUTS", "status": "PARTIAL", "blocked_formula_ids": sorted(missing), "instantaneous_payment_coverage": "INDETERMINATE"})
    result["maturity"]["calculation"] = "PARTIAL"
    result["status"] = "PARTIAL"
    result["results"]["domains"]["financial_metrics"] = [m["metric_id"] for m in result["results"]["metrics"] if m["metric_id"].startswith("financial.phase3e.")]
    return seal_result(result)


def write_phase3e_bundle(result, output_dir):
    target = local_target(output_dir)
    target.mkdir()
    (target / "result.json").write_text(dumps(result), encoding="utf-8")
    (target / "result.sha256").write_text(result["result_hash"] + "\n", encoding="utf-8")
    return target
