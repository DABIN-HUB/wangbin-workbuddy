"""Phase 3F factor-to-producer bindings; no scaling of calculated metrics.

Only a factor's consumed, approved input or D2 control can be varied. A frozen
field being present is not evidence that the current production chain uses it.
"""
from __future__ import annotations

from ..errors import ContractError
from .calculation_graph import CalculationGraph, CalculationNode

FACTOR_TARGETS = {
    "INVESTMENT": {("INPUT", "capex.items.amount"), ("INPUT", "capex.items.unit_price")},
    "GENERATION": {("METHOD", "energy.pr")},
    "SALE_PRICE": {("INPUT", "tariff.periods.sale_price"),
                   ("INPUT", "tariff.ppa_price")},
    "SELF_USE_RATIO": set(),  # load.proposed_self_use_ratio is not consumed by Phase 3C.
    "CURTAILMENT": {("INPUT", "system.losses.value")},
    "OPERATING_MAINTENANCE": {("INPUT", "opex.items.base_amount")},
    "LOAN_INTEREST": {("INPUT", "finance.loan_rate")},
    "PROJECT_DISCOUNT": {("INPUT", "finance.project_discount_rate")},
}


def _row(export, parent, row_id):
    if not isinstance(row_id, str) or not row_id:
        raise ContractError("SCENARIO_ROW_ID")
    group = export["project"]["values"].get(parent)
    if not isinstance(group, dict) or not isinstance(group.get("value"), list):
        raise ContractError("SCENARIO_ROW_ID")
    matches = [r for r in group["value"] if r["row_id"] == row_id]
    if len(matches) != 1:
        raise ContractError("SCENARIO_ROW_ID")
    return matches[0]["fields"]


def validate_factor(factor, kind, name, row_id, export, methods):
    if factor not in FACTOR_TARGETS:
        raise ContractError("SCENARIO_UNKNOWN_FACTOR")
    if (kind, name) not in FACTOR_TARGETS[factor]:
        raise ContractError("BLOCKED_MISSING_INPUT", factor)
    values = export["project"]["values"]
    if kind == "INPUT":
        if name in {"capex.items.amount", "capex.items.unit_price"}:
            _row(export, "capex.items", row_id)
        elif name == "opex.items.base_amount":
            row = _row(export, "opex.items", row_id)
            if row.get("opex.items.category", {}).get("value") not in {"maintenance", "cleaning", "operations"}:
                raise ContractError("SCENARIO_WRONG_OPEX_CATEGORY")
        elif name == "system.losses.value":
            row = _row(export, "system.losses", row_id)
            if (row.get("system.losses.kind", {}).get("value") != "curtailment"
                    or row.get("system.losses.included_in_source", {}).get("value") is not False):
                raise ContractError("SCENARIO_CURTAILMENT_NOT_CONSUMED")
        elif row_id is not None:
            if name == "tariff.periods.sale_price":
                _row(export, "tariff.periods", row_id)
            else:
                raise ContractError("SCENARIO_ROW_ID")
        elif name == "tariff.periods.sale_price":
            raise ContractError("SCENARIO_ROW_ID")
    elif row_id is not None:
        raise ContractError("SCENARIO_ROW_ID")
    if factor == "GENERATION":
        if methods.require("energy.method") != "POA_PR":
            raise ContractError("SCENARIO_FACTOR_NOT_CONSUMED")
        methods.require("energy.pr")
    elif factor == "SALE_PRICE":
        if (name == "tariff.periods.sale_price" and methods.require("settlement.price_source") != "PERIOD_TABLE"
                or name == "tariff.ppa_price" and methods.require("settlement.revenue_method") != "PPA_FIXED"):
            raise ContractError("SCENARIO_FACTOR_NOT_CONSUMED")
    elif factor == "LOAN_INTEREST":
        if not values.get("finance.debt_ratio") or values["finance.debt_ratio"]["value"] <= 0:
            raise ContractError("BLOCKED_MISSING_INPUT", "finance.debt_ratio")
    elif factor == "PROJECT_DISCOUNT" and not values.get("finance.project_discount_rate"):
        raise ContractError("BLOCKED_MISSING_INPUT", "finance.project_discount_rate")


def scenario_calculation_graph(catalog, pv_type, methods):
    """Coarse execution DAG, with explicit factor inputs at their first consumer.

    Nodes are actual existing stage producers, not formula-only calculators.
    All affected descendants must be recomputed, even if a factor's first
    consumer appears in a later stage. Stage 3E remains partial as in Phase 3E.
    """
    if pv_type not in {"industrial_rooftop", "utility_scale_ground"}:
        raise ContractError("SCENARIO_UNSUPPORTED_PROJECT_TYPE")
    generation_method = methods.require("energy.method")
    settlement_method = methods.require("settlement.revenue_method")
    return CalculationGraph([
        CalculationNode("3B", "F-FIRST-YEAR-ENERGY", (), ("system.losses.value",),
                        "OPERATING_YEARS", "PHYSICAL_DELIVERY", generation_method,
                        ("energy.pr",)),
        CalculationNode("3C", "F-ENERGY-REVENUE", ("3B",),
                        ("tariff.periods.sale_price", "tariff.ppa_price"),
                        "OPERATING_YEARS", "SETTLEMENT", settlement_method),
        CalculationNode("3D", "F-PROJECT-CASH-FLOW", ("3C",),
                        ("capex.items.amount", "capex.items.unit_price",
                         "opex.items.base_amount", "finance.loan_rate"),
                        "FINANCIAL_PERIODS", "PROJECT_AND_ENTITY", "FINANCIAL_LEDGER"),
        CalculationNode("3E", "F-NPV", ("3D",), ("finance.project_discount_rate",),
                        "FINANCIAL_PERIODS", "PROJECT_YEAR_END", "SOURCED_PROJECT_ONLY"),
    ], catalog)
