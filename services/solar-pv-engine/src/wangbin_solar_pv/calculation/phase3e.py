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
    unit = catalog.formulas[formula_id].get("unit", unit)
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
    missing = {}

    def required(rows_, key):
        absent = [row.get("period", str(index)) for index, row in enumerate(rows_) if key not in row]
        if absent:
            missing[key] = absent
            return None
        return [row[key] for row in rows_]

    receipts = required(rows, "revenue_cash_receipts")
    avoided = required(rows, "self_use_avoided_expenditure")
    benefit = None if receipts is None or avoided is None else [Decimal(0)] + [a + b for a, b in zip(receipts, avoided)]
    opex_rows = required(rows, "opex_cash_paid")
    opex = None if opex_rows is None else [Decimal(0)] + opex_rows
    project_tax_rows = required(rows, "cash_tax_total_project")
    project_tax = None if project_tax_rows is None else [Decimal(0)] + project_tax_rows
    equity_tax_rows = required(rows, "cash_tax_total_equity")
    equity_tax = None if equity_tax_rows is None else [Decimal(0)] + equity_tax_rows
    capex = required(annual, "capex_cash_paid")
    wc_increase = required(annual, "working_capital_increase")
    # The Phase 3D construction row records the initial occupation only;
    # release is a sourced operating-year event in that ledger's contract.
    operating_release = required(rows, "working_capital_release")
    wc_release = None if operating_release is None else [Decimal(0)] + operating_release
    working_capital = None if wc_increase is None or wc_release is None else [a - b for a, b in zip(wc_increase, wc_release)]
    debt_drawdown = required(annual, "debt_drawdown")
    principal = required(annual, "principal_paid")
    interest = required(annual, "interest_paid")
    fees = required(annual, "finance_fees_paid")
    debt_service = required(rows, "debt_service_due")
    return {
        "benefit": benefit, "opex": opex, "project_tax": project_tax,
        "equity_tax": equity_tax, "capex": capex, "working_capital": working_capital,
        "debt_drawdown": debt_drawdown, "principal": principal,
        "interest": interest, "fees": fees, "debt_service": debt_service,
        "missing": missing,
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
    project_ledger_fields = {"revenue_cash_receipts", "self_use_avoided_expenditure", "opex_cash_paid", "cash_tax_total_project", "capex_cash_paid", "working_capital_increase", "working_capital_release"}
    terminal_missing = {"missing_field_ids": ["finance.project_terminal_cash", *sorted(project_ledger_fields & vectors["missing"].keys())], "policy": "NO_DEFAULT_ZERO"}
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
    if "finance.real_discount_rate" in normalized and "finance.general_inflation" in normalized:
        _record(result, catalog, "financial.phase3e.nominal_discount_rate", "F-NOMINAL-REAL-RATE", {
            "finance.real_discount_rate": normalized["finance.real_discount_rate"],
            "finance.general_inflation": normalized["finance.general_inflation"],
        }, "1", "LIFECYCLE")
    else:
        _record(result, catalog, "financial.phase3e.nominal_discount_rate", "F-NOMINAL-REAL-RATE", {}, "1", "LIFECYCLE", blocked_reason="BLOCKED_MISSING_INPUT", blocked_details={"missing_field_ids": ["finance.real_discount_rate", "finance.general_inflation"]})

    # A configured CFADS method does not itself source the protocol's cash
    # adjustments.  Never treat the absent adjustment vector as zero.
    method_data = methods.to_dict() if hasattr(methods, "to_dict") else methods
    method_parameters = method_data.get("parameters", {}) if isinstance(method_data, dict) else {}
    cfads_missing = []
    definition = normalized.get("finance.cfads_definition")
    method = method_parameters.get("cfads.method", {}).get("value")
    if not definition:
        cfads_missing.append("finance.cfads_definition")
    if not method or definition != method:
        cfads_missing.append("cfads.method")
    adjustments = result.get("evidence", {}).get("financial-ledger", {}).get("cfads_adjustments")
    if adjustments is None:
        cfads_missing.append("debt.cfads_adjustments")
    cfads_vectors = {"finance.project_operating_cash_benefit": vectors["benefit"][1:] if vectors["benefit"] is not None else None,
                     "opex.cash_annual": vectors["opex"][1:] if vectors["opex"] is not None else None,
                     "tax.equity_cash_total": vectors["equity_tax"][1:] if vectors["equity_tax"] is not None else None,
                     "debt.cfads_working_capital_change": vectors["working_capital"][1:] if vectors["working_capital"] is not None else None,
                     "debt.cfads_mandatory_capex": vectors["capex"][1:] if vectors["capex"] is not None else None,
                     "debt.cfads_adjustments": adjustments}
    cfads = _record(result, catalog, "financial.phase3e.cfads", "F-CFADS", cfads_vectors, "CNY", "OPERATING_YEARS",
                    blocked_reason="BLOCKED_MISSING_INPUT" if cfads_missing else None,
                    blocked_details={"missing_field_ids": cfads_missing} if cfads_missing else None)
    if vectors["debt_service"] is not None and any(value == 0 for value in vectors["debt_service"]):
        _metric(result, catalog, "financial.phase3e.dscr", "F-DSCR", None, "1", "OPERATING_YEARS", status="UNDEFINED", reason="ZERO_DEBT_SERVICE", details={"zero_service_periods": [annual[index + 1]["period"] for index, value in enumerate(vectors["debt_service"]) if value == 0]})
    elif cfads["status"] == "CALCULATED":
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
