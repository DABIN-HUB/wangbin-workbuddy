"""One sourced price candidate through the existing physical, cash and NPV chain.

This is an evaluator, not a root solver or a monotonicity certificate. The
caller supplies an original NO_DISPOSITION carrier with actual source bytes;
only its scenario binding is regenerated for the derived candidate.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from time import perf_counter

from ..errors import ContractError
from ..serialization import dumps, loads
from ..timeseries_bundle import read_bundle
from .break_even_financial_replay import replay_financial_candidate
from .break_even_replay import _remove_owned
from .phase3e import calculate_sourced_project_npv, write_phase3e_bundle
from .result_contract import validate_result
from .terminal_disposition import validate_terminal_disposition


@dataclass(frozen=True, slots=True)
class ProjectNpvCandidate:
    price: Decimal
    original_npv: Decimal
    candidate_npv: Decimal
    original_result_hash: str
    candidate_result_hash: str
    terminal_source_hash: str
    phase3b_result_hash: str
    phase3c_result_hash: str
    phase3d_result_hash: str
    candidate_input_hash: str
    candidate_bundle_hash: str
    elapsed_seconds: float


def _npv(result, catalog):
    validate_result(result, catalog)
    metrics = [metric for metric in result["results"]["metrics"]
               if metric["metric_id"] == "financial.phase3e.project_npv"]
    if (len(metrics) != 1 or metrics[0]["formula_id"] != "F-NPV"
            or metrics[0]["status"] != "CALCULATED"
            or not isinstance(metrics[0]["value"], Decimal)
            or metrics[0]["unit"] != catalog.formulas["F-NPV"]["unit"]):
        raise ContractError("BREAK_EVEN_PROJECT_NPV_UNAVAILABLE")
    return metrics[0]["value"]


def calculate_price_project_npv(control, original_export, methods, original_bundle,
                                generation_dir, candidate_price, terminal_carrier,
                                source_documents, *, catalog, budget, workspace, run_name):
    """Return a verified NPV(p); never infer roots from a pair of candidates.

    The original carrier must bind to the re-executed original 3C/3D result.
    A private exclusive run directory is owned by the caller, and is removed
    on failure. No original input, generation result or source bytes are edited.
    """
    validate_terminal_disposition(terminal_carrier, source_documents)
    started = perf_counter()
    replay = replay_financial_candidate(
        control, original_export, methods, original_bundle, generation_dir,
        candidate_price, catalog=catalog, budget=budget, workspace=workspace,
        run_name=run_name)
    root = workspace.path(run_name, json_only=False)
    identity = root.stat().st_dev, root.stat().st_ino
    try:
        generation = loads((Path(generation_dir) / "result.json").read_bytes())
        original = calculate_sourced_project_npv(
            terminal_carrier, source_documents, original_export, methods,
            original_bundle, generation, replay.settlement.original_revenue,
            replay.original_financial, catalog, basis_control=control,
            original_export=original_export, original_bundle=original_bundle)
        original_npv = _npv(original, catalog)
        candidate_carrier = deepcopy(terminal_carrier)
        binding = candidate_carrier["binding"]
        with read_bundle(root / "candidate-d3", catalog=catalog, budget=budget) as bundle:
            binding.update(
                scenario_id=replay.candidate_financial["scenario_id"],
                phase2_input_hash=replay.settlement.candidate_export["input_hash"],
                phase2_source_snapshot_id=replay.settlement.candidate_export["source_snapshot_id"],
                d3_content_hash=bundle.content_hash,
                phase3c_result_hash=replay.settlement.candidate_revenue["result_hash"],
                phase3d_result_hash=replay.candidate_financial["result_hash"],
            )
            candidate = calculate_sourced_project_npv(
                candidate_carrier, source_documents, replay.settlement.candidate_export,
                methods, bundle, generation, replay.settlement.candidate_revenue,
                replay.candidate_financial, catalog, basis_control=control,
                original_export=original_export, original_bundle=original_bundle)
            candidate_npv = _npv(candidate, catalog)
        if (original["source_snapshot"]["phase3e_terminal"]["source_content_hash"]
                != candidate["source_snapshot"]["phase3e_terminal"]["source_content_hash"]
                or original["result_hash"] == candidate["result_hash"]):
            raise ContractError("BREAK_EVEN_CANDIDATE_NPV_IDENTITY")
        pending = root / "_pending-3e"
        pending.mkdir()
        write_phase3e_bundle(original, pending / "original-3e")
        write_phase3e_bundle(candidate, pending / "candidate-3e")
        elapsed = perf_counter() - started
        (pending / "execution.json").write_text(dumps({
            "candidate_price": candidate_price, "original_npv": original_npv,
            "candidate_npv": candidate_npv, "elapsed_seconds": elapsed,
            "replay_calls": 1, "phase3c_calculations": 2,
            "phase3d_calculations": 2, "phase3e_calculations": 2,
            "original_result_hash": original["result_hash"],
            "candidate_result_hash": candidate["result_hash"],
            "terminal_source_hash": candidate_carrier["source_content_hash"],
            "phase3b_result_hash": generation["result_hash"],
            "phase3c_result_hash": replay.settlement.candidate_revenue["result_hash"],
            "phase3d_result_hash": replay.candidate_financial["result_hash"],
            "candidate_input_hash": replay.settlement.candidate_export["input_hash"],
            "candidate_bundle_hash": replay.settlement.candidate_bundle_hash,
        }), encoding="utf-8")
        pending.rename(root / "phase3e")
        return ProjectNpvCandidate(
            candidate_price, original_npv, candidate_npv, original["result_hash"],
            candidate["result_hash"], candidate_carrier["source_content_hash"],
            generation["result_hash"], replay.settlement.candidate_revenue["result_hash"],
            replay.candidate_financial["result_hash"],
            replay.settlement.candidate_export["input_hash"],
            replay.settlement.candidate_bundle_hash, elapsed)
    except BaseException:
        _remove_owned(root, identity, workspace)
        raise
