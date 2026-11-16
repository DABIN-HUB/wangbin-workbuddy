"""P2-3A: replay an approved price through the existing 3C and 3D engines.

Only a private, exclusive workspace is written. This is a financial foundation
ledger, not an assembled Phase 3E cash flow or break-even price result.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..errors import ContractError
from ..serialization import digest, dumps
from .break_even_replay import CandidateReplay, _remove_owned, _replay_price_candidate
from .financial_ledger import calculate_financial_ledger, write_financial_bundle
from .input_contract import validate_export
from .method_config import MethodConfig
from .result_contract import validate_result


@dataclass(frozen=True, slots=True)
class FinancialCandidateReplay:
    settlement: CandidateReplay
    original_financial: dict
    candidate_financial: dict


def _check_settlement(result, exported, methods, bundle_hash, generation_hash, catalog):
    validate_result(result, catalog)
    validated = validate_export(exported, catalog)
    snapshot = result["source_snapshot"]
    payload = result["inputs"].get("identity_payload", {})
    if (result["project_id"] != validated.project.project_id
            or result["pv_type"] != validated.project.pv_type
            or result["inputs"].get("normalized") != exported["normalized_inputs"]
            or result["inputs"].get("method_config_hash") != methods.hash
            or snapshot.get("phase2") != exported["source_snapshot"]
            or snapshot.get("methods") != methods.to_dict()
            or snapshot.get("datasets", {}).get("content_hash") != bundle_hash
            or snapshot.get("generation", {}).get("result_hash") != generation_hash
            or result["inputs"].get("generation_result_hash") != generation_hash
            or result["source_snapshot_id"] != digest(snapshot)
            or payload.get("phase2_input_hash") != exported["input_hash"]
            or result["input_hash"] != digest(payload)):
        raise ContractError("BREAK_EVEN_SETTLEMENT_IDENTITY_MISMATCH")
    return result["result_hash"]


def _check_financial(result, settlement_hash, exported, methods, catalog):
    validate_result(result, catalog)
    snapshot = result["source_snapshot"]
    payload = result["inputs"].get("identity_payload", {})
    if (result["project_id"] != exported["project"]["project_id"]
            or result["pv_type"] != exported["project"]["pv_type"]
            or result["inputs"].get("method_config_hash") != methods.hash
            or result["inputs"].get("normalized") != exported["normalized_inputs"]
            or result["inputs"].get("upstream_settlement_result_hash") != settlement_hash
            or snapshot.get("phase3c_settlement") != {
                "result_hash": settlement_hash, "project_id": exported["project"]["project_id"]}
            or snapshot.get("phase2") != exported["source_snapshot"]
            or snapshot.get("methods") != methods.to_dict()
            or result["source_snapshot_id"] != digest(snapshot)
            or payload.get("phase2_input_hash") != exported["input_hash"]
            or payload.get("method_config_hash") != methods.hash
            or result["input_hash"] != digest(payload)):
        raise ContractError("BREAK_EVEN_FINANCIAL_IDENTITY_MISMATCH")


def replay_financial_candidate(control, original_export, methods, original_bundle, generation_dir, candidate_price, *,
                               catalog, budget, workspace, run_name,
                               original_trading_fee_source_bytes=None, candidate_trading_fee_source_bytes=None):
    """Replay with separately supplied, sealed-3C-bound payment sources.

    Neither source is inferred or rebound. Missing sources retain the ledger
    missing-payment behavior. Callers must supply each role independently.
    """
    return _replay_financial_candidate(control, original_export, methods, original_bundle,
                                       generation_dir, candidate_price, catalog=catalog,
                                       budget=budget, workspace=workspace, run_name=run_name,
                                       original_revenue=None, original_financial=None,
                                       original_trading_fee_source_bytes=original_trading_fee_source_bytes,
                                       candidate_trading_fee_source_bytes=candidate_trading_fee_source_bytes)


def _replay_financial_candidate(control, original_export, methods, original_bundle, generation_dir, candidate_price, *,
                                catalog, budget, workspace, run_name, original_revenue, original_financial,
                                original_trading_fee_source_bytes=None, candidate_trading_fee_source_bytes=None):
    """Publish both 3D ledgers only after their scenario identities validate."""
    if (original_revenue is None) != (original_financial is None):
        raise ContractError("BREAK_EVEN_ORIGINAL_CACHE_INCOMPLETE")
    if original_financial is not None and original_trading_fee_source_bytes is not None:
        raise ContractError("BREAK_EVEN_CACHED_FEE_SOURCE_UNSUPPORTED")
    method = MethodConfig.from_dict(methods.to_dict() if isinstance(methods, MethodConfig) else methods)
    replay = _replay_price_candidate(control, original_export, method, original_bundle, generation_dir,
                                     candidate_price, catalog=catalog, budget=budget, workspace=workspace,
                                     run_name=run_name, original_revenue=original_revenue)
    root = workspace.path(run_name, json_only=False)
    identity = root.stat().st_dev, root.stat().st_ino
    try:
        original_hash = _check_settlement(replay.original_revenue, original_export, method,
                                          replay.original_bundle_hash, replay.generation_result_hash, catalog)
        candidate_hash = _check_settlement(replay.candidate_revenue, replay.candidate_export, method,
                                           replay.candidate_bundle_hash, replay.generation_result_hash, catalog)
        if original_hash == candidate_hash or replay.original_input_hash != original_export["input_hash"]:
            raise ContractError("BREAK_EVEN_SETTLEMENT_IDENTITY_MISMATCH")
        if original_financial is None:
            original_financial = calculate_financial_ledger(original_export, method, replay.original_revenue, catalog=catalog,
                trading_fee_source_bytes=original_trading_fee_source_bytes)
        candidate_financial = calculate_financial_ledger(replay.candidate_export, method, replay.candidate_revenue,
                                                          catalog=catalog,
                                                          trading_fee_source_bytes=candidate_trading_fee_source_bytes)
        _check_financial(original_financial, original_hash, original_export, method, catalog)
        _check_financial(candidate_financial, candidate_hash, replay.candidate_export, method, catalog)
        if (original_financial["result_hash"] == candidate_financial["result_hash"]
                or dumps(original_financial["evidence"]["financial-ledger"]["annual"])
                == dumps(candidate_financial["evidence"]["financial-ledger"]["annual"])):
            raise ContractError("BREAK_EVEN_FINANCIAL_NOT_CONSUMED")
        if original_revenue is None:
            write_financial_bundle(original_financial, root / "original-3d")
        write_financial_bundle(candidate_financial, root / "candidate-3d")
        return FinancialCandidateReplay(replay, original_financial, candidate_financial)
    except BaseException:
        _remove_owned(root, identity, workspace)
        raise
