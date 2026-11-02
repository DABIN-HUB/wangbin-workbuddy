"""Bind bounded terminal evidence to one validated, recomputed 3D candidate.

This gate establishes provenance and asset scope; it does not authorize an
unbooked disposal event's cash/tax treatment. That separate gate must fail
closed before any Phase 3E project cash-flow metric is calculated.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ..errors import ContractError
from ..serialization import digest, dumps
from .break_even_financial_replay import _check_financial, _check_settlement
from .financial_ledger import calculate_financial_ledger
from .input_contract import calculation_identity, validate_export
from .method_config import MethodConfig
from .result_contract import HASH_EXCLUDED, validate_result
from .terminal_disposition import validate_terminal_disposition


@dataclass(frozen=True, slots=True)
class BoundTerminalCandidate:
    source_content_hash: str
    binding_hash: str
    financial_result_hash: str
    asset_ids: tuple[str, ...]
    source: dict
    binding: dict


def _recomputed_content(result):
    """Compare sealed 3D content allowing only unordered evidence-ID ordering.

    A result reloaded from canonical JSON has its evidence object keys sorted;
    the original producer enumerates keys in insertion order when constructing
    metric evidence IDs. Both are the same *set* of verified references.
    """
    content = {key: deepcopy(value) for key, value in result.items() if key not in HASH_EXCLUDED}
    for metric in content["results"]["metrics"]:
        metric["evidence_ids"] = sorted(metric["evidence_ids"])
    return dumps(content)


def _asset_scope(ledger, normalized):
    """Reconcile paid capital items, book assets and linked replacements."""
    capex_rows = normalized.get("capex.items") or []
    depreciation_rows = normalized.get("assets.depreciation") or []
    replacement_rows = normalized.get("assets.replacements") or []
    paid = {row["row_id"]: row["fields"].get("capex.items.asset_id") for row in capex_rows}
    book_input = {row["fields"].get("assets.depreciation.asset_id") for row in depreciation_rows}
    book_ledger = {row["asset_id"] for row in ledger["depreciation"]["records"]}
    links = ledger["capex"]["replacement_links"]
    declared_links = {row["row_id"]: row["fields"].get("assets.replacements.asset_id")
                      for row in replacement_rows}
    if (not paid or not book_input or None in paid.values() or None in book_input or
            len(paid) != len(capex_rows) or len(declared_links) != len(replacement_rows) or
            set(paid) != set(ledger["capex"]["ids"]) or book_ledger != book_input or
            set(links) != set(declared_links) or any(
                link["capex_row_id"] not in paid or paid[link["capex_row_id"]] != link["asset_id"] or
                declared_links[event_id] != link["asset_id"]
                for event_id, link in links.items())):
        raise ContractError("TERMINAL_ASSET_LEDGER_INVENTORY_MISMATCH")
    return book_ledger | set(paid.values()) | set(declared_links.values())


def bind_terminal_candidate(carrier, source_documents, exported, methods, bundle,
                            generation, settlement, financial, catalog):
    """Reject self-asserted result hashes and cross-scenario source reuse."""
    validated = validate_export(exported, catalog)
    method = MethodConfig.from_dict(methods.to_dict() if isinstance(methods, MethodConfig) else methods)
    checked = validate_terminal_disposition(carrier, source_documents)
    validate_result(generation, catalog)
    validate_result(settlement, catalog)
    validate_result(financial, catalog)
    if generation["project_id"] != validated.project.project_id or generation["pv_type"] != validated.project.pv_type:
        raise ContractError("TERMINAL_GENERATION_PROJECT_MISMATCH")
    generation_hash = generation["result_hash"]
    # Reject impossible self-asserted identities *before* streaming the full
    # D3 bundle. This is only a preflight, never permission to calculate.
    claimed = {
        "project_id": validated.project.project_id,
        "pv_type": validated.project.pv_type,
        "evaluation_date": validated.project.values["project.evaluation_date"]["value"],
        "currency": validated.project.values["project.currency"]["value"],
        "scenario_id": financial["scenario_id"],
        "phase2_input_hash": validated.phase2_input_hash,
        "phase2_source_snapshot_id": validated.phase2_source_snapshot_id,
        "method_config_hash": method.hash,
        "d3_content_hash": bundle.content_hash,
        "phase3b_result_hash": generation_hash,
        "phase3c_result_hash": settlement["result_hash"],
        "phase3d_result_hash": financial["result_hash"],
    }
    if any(checked.binding[key] != value for key, value in claimed.items()):
        raise ContractError("TERMINAL_CANDIDATE_BINDING_MISMATCH")
    selected_basis = {"项目税前": "pre_tax", "项目税后": "post_tax"}[checked.binding["basis"]]
    project_basis = validated.project.values.get("project.cashflow_tax_basis")
    if not project_basis or project_basis["value"] not in (selected_basis, "both"):
        raise ContractError("TERMINAL_BASIS_NOT_SELECTED")
    identity = calculation_identity(validated, method, catalog, datasets=bundle)
    settlement_hash = _check_settlement(settlement, validated.export, method,
                                        identity["input_identity_payload"]["datasets"]["content_hash"],
                                        generation_hash, catalog)
    if (settlement["source_snapshot"].get("datasets") != identity["source_snapshot"]["datasets"]
            or settlement["scenario_id"] != financial["scenario_id"]):
        raise ContractError("TERMINAL_SETTLEMENT_IDENTITY_MISMATCH")
    _check_financial(financial, settlement_hash, validated.export, method, catalog)
    # Canonical hashes alone do not prove nested ledger rows came from 3D.
    # Compare to the actual approved producer, never to caller-supplied rows.
    recomputed = calculate_financial_ledger(validated.export, method, settlement, catalog=catalog)
    if _recomputed_content(financial) != _recomputed_content(recomputed):
        raise ContractError("TERMINAL_FINANCIAL_LEDGER_NOT_RECOMPUTED")

    if checked.binding["basis"] not in ("项目税前", "项目税后"):
        raise ContractError("TERMINAL_BASIS_NOT_SELECTED")
    ledger = financial["evidence"]["financial-ledger"]
    assets = _asset_scope(ledger, validated.export["normalized_inputs"])
    if not assets or assets != set(checked.source["covered_asset_ids"]):
        raise ContractError("TERMINAL_ASSET_SCOPE_MISMATCH")
    return BoundTerminalCandidate(checked.source_content_hash, digest(checked.binding),
                                  financial["result_hash"], tuple(sorted(assets)),
                                  checked.source, checked.binding)
