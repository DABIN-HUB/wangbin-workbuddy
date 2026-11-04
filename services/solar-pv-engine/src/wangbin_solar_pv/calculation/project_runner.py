"""One project execution path over the existing Phase 2/D3 and 3B–3E producers.

The canonical result is the existing 3E result contract, not a second model.
A failed upstream stage never publishes a partial project as a success.
"""
from __future__ import annotations

from pathlib import Path
from time import perf_counter

from ..errors import ContractError
from ..local_files import Workspace
from ..serialization import digest, dumps
from ..timeseries_bundle import BundleBudget, read_bundle
from .break_even_replay import _remove_owned
from .energy_yield import calculate_ground as generate_ground, calculate_rooftop as generate_rooftop
from .financial_ledger import calculate_financial_ledger, write_financial_bundle
from .formula_execution import formula_execution_map
from .input_contract import validate_export
from .method_config import MethodConfig
from .phase3e import calculate_phase3e, write_phase3e_bundle
from .result_contract import validate_result
from .revenue import calculate_ground as settle_ground, calculate_rooftop as settle_rooftop
from .scenario_runner import _RUN_ID


def run_project(exported, methods, *, bundle_dir, catalog, budget, workspace, run_id,
                generation_dir=None, generation_result_hash=None):
    """Run and publish a single, source-bound BASE project calculation.

    An externally pinned 3B trace is read-only; the real 3C consumer verifies
    its full receipt, interval chain and compatibility before 3D is invoked.
    All output directories are exclusive children of the authorized workspace.
    """
    if (type(budget) is not BundleBudget or not isinstance(workspace, Workspace)
            or not isinstance(run_id, str) or _RUN_ID.fullmatch(run_id) is None
            or (generation_dir is None) != (generation_result_hash is None)):
        raise ContractError("PROJECT_EXECUTION_CONTEXT")
    original = validate_export(exported, catalog).export
    config = MethodConfig.from_dict(methods.to_dict() if isinstance(methods, MethodConfig) else methods)
    pv_type = original["project"]["pv_type"]
    if pv_type not in {"industrial_rooftop", "utility_scale_ground"}:
        raise ContractError("PROJECT_CATEGORY_NOT_IMPLEMENTED")
    if pv_type not in config.to_dict()["pv_types"]:
        raise ContractError("METHOD_CONFIG_CATEGORY")
    root = workspace.path(run_id, json_only=False)
    if root.exists():
        raise ContractError("PROJECT_OUTPUT_EXISTS")
    # Validate the complete D3 input before creating any published output.
    with read_bundle(bundle_dir, catalog=catalog, budget=budget) as bundle:
        if dumps(bundle.base_export) != dumps(original):
            raise ContractError("PROJECT_BUNDLE_BASE_MISMATCH")
        root.mkdir(mode=0o700)
        identity = root.stat().st_dev, root.stat().st_ino
        started = perf_counter()
        try:
            stages = {}
            if generation_dir is None:
                generate = generate_ground if pv_type == "utility_scale_ground" else generate_rooftop
                generation = generate(original, config, catalog=catalog,
                                      output_dir=root / "3b", budget=budget, bundle=bundle)
                validate_result(generation, catalog)
                generation_dir = root / "3b"
                generation_result_hash = generation["result_hash"]
                stages["3B"] = {"result_hash": generation_result_hash, "reuse": False}
            else:
                generation_dir = Path(generation_dir)
                stages["3B"] = {"result_hash": generation_result_hash, "reuse": True}
            settle = settle_ground if pv_type == "utility_scale_ground" else settle_rooftop
            settlement = settle(original, config, generation_dir=generation_dir,
                                generation_result_hash=generation_result_hash,
                                catalog=catalog, output_dir=root / "3c", budget=budget,
                                bundle=bundle)
            validate_result(settlement, catalog)
            stages["3C"] = {"result_hash": settlement["result_hash"], "reuse": False}
            financial = calculate_financial_ledger(original, config, settlement, catalog=catalog)
            validate_result(financial, catalog)
            write_financial_bundle(financial, root / "3d")
            stages["3D"] = {"result_hash": financial["result_hash"], "reuse": False}
            result = calculate_phase3e(financial, config, catalog)
            validate_result(result, catalog)
            write_phase3e_bundle(result, root / "3e")
            stages["3E"] = {"result_hash": result["result_hash"], "reuse": False}
            # The report layer consumes this one canonical 3E result, including
            # the upstream metric, source, method and formula snapshots.
            Workspace(root).create("canonical.json", result)
            mapping = formula_execution_map(result, catalog)
            Workspace(root).create("formula-execution.json", mapping)
            receipt = {"project_id": result["project_id"], "pv_type": pv_type,
                       "scenario_id": "BASE", "input_hash": result["input_hash"],
                       "phase2_input_hash": original["input_hash"],
                       "source_snapshot_id": result["source_snapshot_id"],
                       "method_config_hash": config.hash,
                       "definition_version": catalog.definition_version,
                       "definition_hash": catalog.definition_hash,
                       "canonical_result_hash": result["result_hash"],
                       "formula_mapping_hash": mapping["mapping_hash"],
                       "status": result["status"], "stages": stages}
            receipt["receipt_hash"] = digest(receipt)
            receipt["elapsed_seconds"] = str(perf_counter() - started)
            Workspace(root).create("receipt.json", receipt)
            return receipt
        except BaseException:
            _remove_owned(root, identity, workspace)
            raise
