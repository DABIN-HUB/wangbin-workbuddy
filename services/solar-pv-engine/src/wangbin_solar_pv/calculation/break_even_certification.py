"""Fail-closed canonical F-BREAK-EVEN-PRICE certification gate.

A sampled sign change and an idealized affine proof do not establish the root
set of the finite-precision executable NPV(p). No provisional root is returned.
"""
from __future__ import annotations

from copy import deepcopy


from ..errors import ContractError
from .break_even_project_session import ProjectNpvSession
from .result_contract import seal_result, validate_result


def certify_project_root_set(session):
    """Return a sealed nonnumeric result until *all* domain obligations hold.

    The existing D2 absolute tolerance is a dimensionless comparison control;
    no approved independent yuan NPV-root tolerance or finite-arithmetic
    completeness certificate is presently available. In particular this
    method must never promote legacy sample interpolation to a project result.
    """
    if not isinstance(session, ProjectNpvSession):
        raise ContractError("BREAK_EVEN_SESSION_REQUIRED")
    with session._lock:
        session._check_pins()
        result = deepcopy(session.original_result)
        matches = [m for m in result["results"]["metrics"]
                   if m["metric_id"] == "financial.phase3e.break-even-price"]
        if len(matches) != 1 or matches[0]["formula_id"] != "F-BREAK-EVEN-PRICE":
            raise ContractError("BREAK_EVEN_FORMAL_METRIC_UNAVAILABLE")
        metric = matches[0]
        if metric["status"] != "BLOCKED_MISSING_INPUT" or metric["value"] is not None:
            raise ContractError("BREAK_EVEN_FORMAL_METRIC_UNAVAILABLE")
        evidence = {
            "method": session.methods.require("break_even.method"),
            "price_domain_yuan_per_kwh": [session.price_min, session.price_max],
            "price_tolerance_yuan_per_kwh": session.methods.require("break_even.price_tolerance"),
            "maximum_iterations": session.methods.require("break_even.maximum_iterations"),
            "selector": deepcopy(session.control["selector"]),
            "project_id": session.control["project_id"],
            "basis": session.control["basis"],
            "evaluation_date": session.original_result["evaluation_date"],
            "discount_rate": session.original_export["project"]["values"]["finance.project_discount_rate"]["value"],
            "formula_id": "F-BREAK-EVEN-PRICE",
            "formula_version": session.catalog.definition_version,
            "definition_hash": session.catalog.definition_hash,
            "executor_sha256": session.executor_sha256,
            "executor_identity_scope": "pinned source-file SHA-256, not proof of imported Python bytecode identity",
            "original_input_hash": session.original_export["input_hash"],
            "d3_content_hash": session.original_bundle.content_hash,
            "phase3b_result_hash": session.control["generation_result_hash"],
            "phase3c_result_hash": session.original_revenue["result_hash"],
            "phase3d_result_hash": session.original_financial["result_hash"],
            "phase3e_result_hash": session.original_result["result_hash"],
            "terminal_source_hash": session.terminal_carrier["source_content_hash"],
            "certificate_status": "NOT_PROVEN",
            "whole_domain_continuity": False,
            "whole_domain_strict_monotonicity": False,
            "price_branches_certified": [],
            "root_count_certified": None,
            "root_intervals": None,
            "npv_residual_yuan": None,
            "bracket_width_yuan_per_kwh": None,
            "approved_monetary_root_tolerance_yuan": None,
            "candidate_executions_in_certification": 0,
            "unmet_obligations": [
                "NO_APPROVED_YUAN_NPV_ROOT_RESIDUAL_TOLERANCE",
                "FINITE_DECIMAL_REPLAY_NOT_CERTIFIED_CONTINUOUS_AND_STRICTLY_MONOTONE_ON_FULL_DOMAIN",
                "TAX_VAT_COLLECTION_AND_SETTLEMENT_BRANCHES_NOT_EXHAUSTIVELY_CERTIFIED",
                "NO_PROOF_ALL_ROOTS_ARE_ENUMERATED",
            ],
            "legacy_sample_interpolation_accepted": False,
        }
        result["evidence"]["phase3e-break-even-root-certification"] = evidence
        metric["status"] = "BLOCKED_MISSING_INPUT"
        metric["reason"] = "BLOCKED_ROOT_SET_COMPLETENESS_UNPROVEN"
        metric["details"] = {"root_certification": "NOT_PROVEN",
                             "evidence_id": "phase3e-break-even-root-certification",
                             "unmet_obligations": evidence["unmet_obligations"]}
        metric["evidence_ids"] = sorted(set(metric["evidence_ids"]) | {
            "phase3e-break-even-root-certification"})
        result = seal_result(result)
        return validate_result(result, session.catalog)
