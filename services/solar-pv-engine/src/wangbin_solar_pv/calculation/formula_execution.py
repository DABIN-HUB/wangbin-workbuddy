"""Project-specific mapping of the frozen formula inventory to canonical metrics.

Product-level numerical verification, project-level computation and formula
applicability are separate facts. A blocked metric never acquires a value here.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from ..serialization import digest
from .execution_registry import execution_inventory
from .result_contract import validate_result


def formula_execution_map(result, catalog):
    """Return one source/result-bound row for every effective frozen formula."""
    validate_result(result, catalog)
    observed = defaultdict(list)
    for metric in result["results"]["metrics"]:
        observed[metric["formula_id"]].append(metric)
    rows = []
    for registered in execution_inventory(catalog):
        fid = registered["formula_id"]
        metrics = observed[fid]
        # Older stage placeholders cannot turn a later explicit 3E blocker
        # into a false NOT_IMPLEMENTED verdict for the same formula.
        effective = [m for m in metrics if m["status"] != "NOT_IMPLEMENTED"] or metrics
        states = {m["status"] for m in effective}
        if states == {"CALCULATED"}:
            status = "CALCULATED"
        elif "CALCULATED" in states:
            status = "PARTIAL"
        elif "BLOCKED_METHOD_REVIEW" in states:
            status = "BLOCKED_METHOD_REVIEW"
        elif "BLOCKED_MISSING_INPUT" in states:
            status = "BLOCKED_MISSING_INPUT"
        elif states == {"NOT_APPLICABLE"}:
            status = "NOT_APPLICABLE"
        elif states == {"UNDEFINED"}:
            status = "UNDEFINED"
        elif states == {"UNKNOWN"}:
            status = "UNKNOWN"
        elif states == {"NOT_IMPLEMENTED"} or not registered["executor"]:
            status = "NOT_IMPLEMENTED"
        else:
            status = "NOT_TESTED"
        rows.append({"formula_id": fid, "phase3_applicable": registered["phase3_applicable"],
                     "product_status": registered["status"],
                     "numerical_validation_status": registered["numerical_validation_status"],
                     "executor": registered["executor"],
                     "project_status": status,
                     "metric_ids": [m["metric_id"] for m in metrics],
                     "metric_statuses": [m["status"] for m in metrics],
                     "blocked_reasons": sorted({m["reason"] for m in effective if m["status"].startswith("BLOCKED_")})})
    content = {"project_id": result["project_id"], "pv_type": result["pv_type"],
               "scenario_id": result["scenario_id"], "input_hash": result["input_hash"],
               "source_snapshot_id": result["source_snapshot_id"],
               "canonical_result_hash": result["result_hash"],
               "definition_version": catalog.definition_version,
               "definition_hash": catalog.definition_hash,
               "product_counts": dict(sorted(Counter(x["product_status"] for x in rows).items())),
               "project_counts": dict(sorted(Counter(x["project_status"] for x in rows).items())),
               "formulas": rows}
    return {**content, "mapping_hash": digest(content)}
