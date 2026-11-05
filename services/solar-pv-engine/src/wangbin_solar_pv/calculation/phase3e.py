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
from ..serialization import digest, dumps
from ..timeseries_private import local_target
from .break_even_execution import _target, validate_price_selector
from .break_even_replay import _derive, _verify_bundles
from .financial_metrics import evaluate
from .input_contract import validate_export
from .result_contract import seal_result, validate_result
from .terminal_binding import bind_terminal_candidate, reconcile_terminal_cash

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


def _record_sourced_project_irr(result, catalog, methods, cash, period):
    """Use only the declared project basis and fully sourced D2 root controls."""
    ids = ("irr.method", "irr.minimum_rate", "irr.maximum_rate",
           "irr.root_tolerance", "irr.maximum_degree")
    parameters = methods.to_dict()["parameters"]
    metric = next(item for item in result["results"]["metrics"]
                  if item["metric_id"] == "financial.phase3e.project_irr")
    missing = [parameter_id for parameter_id in ids if parameter_id not in parameters]
    unreviewed = [parameter_id for parameter_id in ids if parameter_id in parameters and
                  (parameters[parameter_id]["status"] not in {"ASSUMED", "VERIFIED"} or
                   parameters[parameter_id]["license_status"] != "AUTHORIZED")]
    if missing or unreviewed:
        metric.update(status="BLOCKED_MISSING_INPUT" if missing else "BLOCKED_METHOD_REVIEW",
                      reason="IRR_METHOD_CONTROLS_INCOMPLETE" if missing else "IRR_METHOD_SOURCE_UNVERIFIED",
                      details={"missing_method_parameter_ids": missing,
                               "unreviewed_method_parameter_ids": unreviewed})
        return
    maximum_degree = methods.require("irr.maximum_degree")
    if maximum_degree < len(cash) - 1:
        metric.update(status="BLOCKED_METHOD_REVIEW", reason="IRR_DEGREE_BUDGET",
                      details={"financial_end_year": len(cash) - 1, "maximum_degree": maximum_degree})
        return
    result["results"]["metrics"].remove(metric)
    _record(result, catalog, "financial.phase3e.project_irr", "F-IRR-PROJECT", {
        "finance.irr_search_domain": {
            "minimum": methods.require("irr.minimum_rate"),
            "maximum": methods.require("irr.maximum_rate"),
        },
        "finance.project_irr_cash_flow": cash,
        "time.financial_end_year": len(cash) - 1,
    }, "1", period, options={"root_tolerance": methods.require("irr.root_tolerance")})


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


def calculate_sourced_project_npv(carrier, source_documents, exported, methods, bundle,
                                 generation, settlement, financial, catalog, *, basis_control,
                                 original_export, original_bundle):
    """Calculate only sourced, year-end unlevered project metrics; other gates stay blocked."""
    bound = bind_terminal_candidate(carrier, source_documents, exported, methods, bundle,
                                    generation, settlement, financial, catalog)
    bridge = reconcile_terminal_cash(bound, financial, exported, methods, source_documents)
    values = exported["project"]["values"]
    chosen = bound.binding["basis"]
    expected_basis = {"项目税前": "pre_tax", "项目税后": "post_tax"}[chosen]
    tax_basis = values.get("project.cashflow_tax_basis")
    ownership = values.get("project.ownership_mode")
    price_basis = values.get("project.price_basis")
    rate = values.get("finance.project_discount_rate")
    if not all(isinstance(record, dict) and record.get("status") in {"ASSUMED", "VERIFIED"}
               and record.get("license_status") == "AUTHORIZED" and record.get("source_id")
               for record in (tax_basis, ownership, price_basis, rate)):
        raise ContractError("PROJECT_NPV_BASIS_OR_RATE_UNVERIFIED")
    if (tax_basis["value"] not in (expected_basis, "both") or
            rate["unit"] != "1" or not isinstance(rate["value"], Decimal) or
            price_basis["value"] not in {"nominal", "real"} or
            price_basis["value"] != methods.require("settlement.price_basis") or
            methods.require("settlement.currency") != bound.source["currency"]):
        raise ContractError("PROJECT_NPV_RATE_BASIS_MISMATCH")
    mode = methods.data_mode
    if mode != "SYNTHETIC":
        raise ContractError("PROJECT_NPV_SYNTHETIC_SCOPE_ONLY")
    for record in (tax_basis, ownership, price_basis, rate):
        if record["status"] == "ASSUMED" and (mode != "SYNTHETIC" or record["source_kind"] != "ASSUMPTION" or not record.get("assumption")):
            raise ContractError("PROJECT_NPV_SYNTHETIC_BASIS_ONLY")
        if record["status"] == "VERIFIED" and not record.get("reviewer"):
            raise ContractError("PROJECT_NPV_BASIS_OR_RATE_UNVERIFIED")
    rate_scope = ("PROJECT_PRE_TAX" if chosen == "项目税前" else "PROJECT_POST_TAX")
    declared_scope = f"{rate_scope}_{price_basis['value'].upper()}_{bound.source['currency']}_YEAR_END"
    if rate["source_section_or_cell"] != declared_scope:
        raise ContractError("PROJECT_NPV_RATE_BASIS_MISMATCH")
    if not isinstance(basis_control, dict) or basis_control.get("basis") != chosen or basis_control.get("project_id") != bound.source["project_id"] or basis_control.get("pv_type") != bound.source["pv_type"] or basis_control.get("method_config_hash") != bound.binding["method_config_hash"] or basis_control.get("generation_result_hash") != bound.binding["phase3b_result_hash"]:
        raise ContractError("PROJECT_NPV_EXECUTION_BASIS_MISMATCH")
    control_source = basis_control.get("source", {})
    if (control_source.get("status") != "ASSUMED" or control_source.get("source_kind") != "SYNTHETIC"
            or control_source.get("license_status") != "AUTHORIZED" or not control_source.get("source_id")):
        raise ContractError("PROJECT_NPV_EXECUTION_BASIS_MISMATCH")
    selected_control = validate_price_selector(basis_control, original_export, methods, original_bundle, catalog)
    source_is_original = exported["input_hash"] == basis_control.get("original_input_hash")
    if source_is_original:
        if (exported["source_snapshot_id"] != basis_control.get("original_source_snapshot_id") or
                bundle.content_hash != original_bundle.content_hash or
                dumps(exported) != dumps(validate_export(original_export, catalog).export)):
            raise ContractError("PROJECT_NPV_EXECUTION_BASIS_MISMATCH")
    else:
        key = basis_control["selector"]
        actual_atom = _target(validate_export(exported, catalog), bundle, key["field_id"], key["row_id"])
        derived, expected_atom = _derive(original_export, selected_control, actual_atom["value"], catalog)
        if dumps(exported) != dumps(derived) or dumps(actual_atom) != dumps(expected_atom):
            raise ContractError("PROJECT_NPV_EXECUTION_BASIS_MISMATCH")
        _verify_bundles(original_bundle, bundle, key["field_id"], key["row_id"])

    result = calculate_phase3e(financial, methods, catalog)
    annual = result["evidence"]["financial-ledger"]["annual"]
    vectors = result["evidence"]["phase3e-financial"]["vectors"]
    if any(vectors[name] is None for name in ("benefit", "opex", "project_tax", "capex", "working_capital")):
        raise ContractError("PROJECT_NPV_LEDGER_INCOMPLETE")
    result["source_snapshot"]["phase3e_terminal"] = {
        "source": bound.source, "source_content_hash": bound.source_content_hash,
        "binding": bound.binding, "binding_hash": bound.binding_hash,
        "phase3d_result_hash": bound.financial_result_hash,
        "basis_control_hash": digest(basis_control), "basis_control": basis_control,
        "rate_source": rate,
    }
    snapshot_id = digest(result["source_snapshot"])
    result["source_snapshot_id"] = snapshot_id
    payload = result["inputs"]["identity_payload"]
    payload.update(source_snapshot_id=snapshot_id, upstream_financial_result_hash=bound.financial_result_hash,
                   terminal_binding_hash=bound.binding_hash, terminal_source_content_hash=bound.source_content_hash,
                   basis_control_hash=digest(basis_control), selected_project_rate_source_hash=digest(rate))
    result["input_hash"] = digest(payload)
    source_ids = {bound.source["no_disposition"]["source"]["source_id"]}
    result["inputs"]["used_sources"] = sorted(set(result["inputs"].get("used_sources", [])) |
                                                  source_ids | {rate["source_id"], control_source["source_id"]})
    result["inputs"]["used_fields"] = sorted(set(result["inputs"].get("used_fields", [])) | {
        "project.cashflow_tax_basis", "project.ownership_mode", "project.price_basis",
        "finance.project_discount_rate", "project.evaluation_date", "project.evaluation_years",
        "schedule.commissioning_date",
    })
    result["evidence"]["phase3e-terminal-reconciliation"] = bridge
    result["evidence"]["phase3e-financial"]["terminal_cash"] = bridge["terminal_cash"]
    result["evidence"]["phase3e-financial"]["vectors"].update({
        "project_tax": bridge["total_project_tax"], "terminal_cash": bridge["terminal_cash"],
        "project_income_tax": bridge["total_income_tax"],
    })
    result["boundaries"][_BOUNDARY].update(terminal_cash_policy="SOURCE_AND_LEDGER_RECONCILED",
                                          project_basis=chosen, price_basis=price_basis["value"],
                                          upstream_financial_result_hash=bound.financial_result_hash)
    metric_ids = {"financial.phase3e.project_cash_flow", "financial.phase3e.project_pretax_cash_flow",
                  "financial.phase3e.project_npv", "financial.phase3e.cumulative_cash_flow",
                  "financial.phase3e.discounted_cumulative_cash", "financial.phase3e.static_payback",
                  "financial.phase3e.dynamic_payback"}
    result["results"]["metrics"] = [m for m in result["results"]["metrics"] if m["metric_id"] not in metric_ids]
    span = f"{len(annual)}_PERIODS"
    post = _record(result, catalog, "financial.phase3e.project_cash_flow", "F-PROJECT-CASH-FLOW", {
        "finance.project_operating_cash_benefit": vectors["benefit"],
        "opex.cash_annual": vectors["opex"],
        "tax.project_cash_total": bridge["total_project_tax"],
        "capex.unlevered_cash_annual": vectors["capex"],
        "working_capital.project_net_change": vectors["working_capital"],
        "finance.project_terminal_cash": bridge["terminal_cash"],
    }, result["currency"], span)
    if post["status"] != "CALCULATED":
        raise ContractError("PROJECT_NPV_CASHFLOW_NOT_CALCULATED")
    pre = _record(result, catalog, "financial.phase3e.project_pretax_cash_flow", "F-PROJECT-PRETAX-CASH-FLOW", {
        "finance.project_cash_flow": post["value"],
        "tax.project_income_cash_paid": bridge["total_income_tax"],
    }, result["currency"], span)
    if pre["status"] != "CALCULATED":
        raise ContractError("PROJECT_NPV_PRETAX_NOT_CALCULATED")
    selected = pre["value"] if chosen == "项目税前" else post["value"]
    npv = _record(result, catalog, "financial.phase3e.project_npv", "F-NPV", {
        "finance.selected_cash_flow": selected, "finance.selected_discount_rate": rate["value"],
        "finance.cash_flow_basis": chosen, "time.financial_end_year": len(annual) - 1,
    }, result["currency"], span)
    if npv["status"] != "CALCULATED":
        raise ContractError("PROJECT_NPV_NOT_CALCULATED")
    cumulative = _record(result, catalog, "financial.phase3e.cumulative_cash_flow",
                         "F-CUMULATIVE-CASH-FLOW", {
                             "finance.selected_cash_flow": selected,
                             "time.cumulative_end_year": len(annual) - 1,
                             "finance.cash_flow_basis": chosen,
                         }, result["currency"], span)
    discounted = _record(result, catalog, "financial.phase3e.discounted_cumulative_cash",
                         "F-DISCOUNTED-CUMULATIVE-CASH", {
                             "finance.selected_cash_flow": selected,
                             "finance.selected_discount_rate": rate["value"],
                             "time.cumulative_end_year": len(annual) - 1,
                             "finance.cash_flow_basis": chosen,
                         }, result["currency"], span)
    if (cumulative["status"] != "CALCULATED" or discounted["status"] != "CALCULATED"
            or discounted["value"][-1] != npv["value"]):
        raise ContractError("PROJECT_RETURN_CASHFLOW_RECONCILIATION")

    # Recovery requires the first proven crossing of the complete project
    # series.  The discounted kernel itself discounts the current year's raw
    # cash; do not feed it a discounted amount for a second discount.
    for metric_id, formula_id, totals in (
            ("financial.phase3e.static_payback", "F-STATIC-PAYBACK", cumulative["value"]),
            ("financial.phase3e.dynamic_payback", "F-DYNAMIC-PAYBACK", discounted["value"])):
        year = next((index for index in range(1, len(totals))
                     if totals[index - 1] < 0 <= totals[index]), None)
        if year is None:
            _metric(result, catalog, metric_id, formula_id, None, "year", span,
                    status="UNDEFINED", reason=("INVALID_RECOVERY_CROSSING" if all(total >= 0 for total in totals)
                                                else "NOT_RECOVERED_WITHIN_HORIZON"),
                    details={"cash_flow_basis": chosen, "last_period": len(annual) - 1})
            continue
        values = {"finance.cash_flow_basis": chosen,
                  "time.financial_end_year": len(annual) - 1}
        if formula_id == "F-STATIC-PAYBACK":
            values.update({"finance.first_recovery_year": year,
                           "finance.pre_recovery_cumulative_cash": totals[year - 1],
                           "finance.recovery_year_cash_flow": selected[year]})
        else:
            values.update({"finance.first_discounted_recovery_year": year,
                           "finance.pre_discounted_recovery_cumulative": totals[year - 1],
                           "finance.discounted_recovery_year_cash_flow": selected[year],
                           "finance.selected_discount_rate": rate["value"]})
        outcome = _record(result, catalog, metric_id, formula_id, values, "year", span)
        if outcome["status"] != "CALCULATED":
            raise ContractError("PROJECT_RETURN_RECOVERY_RECONCILIATION")
        outcome["details"].update({
            "cash_flow_basis": chosen,
            "first_recovery_year": year,
            "later_negative_cumulative_periods": [index for index in range(year + 1, len(totals))
                                                  if totals[index] < 0],
        })

    # Unspecified IRR parameters block this project's result, not the existing
    # kernel's product-level implementation; no default domain is inferred.
    _record_sourced_project_irr(result, catalog, methods, selected, span)
    # The worst-year formula still needs an approved year scope and numeric
    # result representation; its existing blocked integration is unchanged.
    for metric in result["results"]["metrics"]:
        if metric["metric_id"] == "financial.phase3e.worst_cash_year":
            metric.update(status="NOT_IMPLEMENTED", reason="PROJECT_RETURN_INTEGRATION_NOT_IN_R1_3_SCOPE",
                          details={"upstream_project_cash_flow": "CALCULATED"})
    result["evidence"]["phase3e-financial"]["selected_basis"] = chosen
    result["evidence"]["phase3e-financial"]["project_discount_rate"] = rate["value"]
    result["evidence"]["phase3e-financial"]["project_npv"] = npv["value"]
    result["findings"].append({"code": "SOURCED_PROJECT_NPV_SYNTHETIC_ONLY",
                               "status": "PARTIAL", "unimplemented": ["EQUITY_CASH_FLOW", "DATED_NPV", "BREAK_EVEN_ROOT"]})
    # Source JSON sorts evidence object keys on readback. Phase 3E metric
    # references are sets in meaning, so canonicalize their order here only;
    # do not touch sealed 3D metrics or the original no-source execution path.
    for metric in result["results"]["metrics"]:
        if metric["boundary_id"] == _BOUNDARY:
            metric["evidence_ids"] = sorted(metric["evidence_ids"])
    result = seal_result(result)
    validate_result(result, catalog)
    return result


def write_phase3e_bundle(result, output_dir):
    target = local_target(output_dir)
    target.mkdir()
    (target / "result.json").write_text(dumps(result), encoding="utf-8")
    (target / "result.sha256").write_text(result["result_hash"] + "\n", encoding="utf-8")
    return target
