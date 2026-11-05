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
from .scenario_runner import SCENARIO_IDS, _RUN_ID, prepare_scenario, run_scenario


def _prepare_cases(controls, original, methods, catalog):
    if controls is None:
        return [], []
    if (not isinstance(controls, list) or len(controls) != 3
            or any(not isinstance(item, dict) for item in controls)
            or any(not isinstance(item.get("scenario_id"), str) for item in controls)
            or {item.get("scenario_id") for item in controls} != SCENARIO_IDS
            or any(not isinstance(item.get("run_id"), str) or _RUN_ID.fullmatch(item["run_id"]) is None
                   for item in controls)
            or len({item["run_id"] for item in controls}) != 3):
        raise ContractError("SCENARIO_SET_REQUIRED")
    prepared, blocked = [], []
    for control in controls:
        try:
            prepared.append(prepare_scenario(control, original, methods, catalog))
        except ContractError as exc:
            if control["scenario_id"] == "BASE":
                raise
            if exc.code not in {"BLOCKED_MISSING_INPUT", "BLOCKED_METHOD_REVIEW",
                                "SCENARIO_FACTOR_NOT_CONSUMED", "SCENARIO_CURTAILMENT_NOT_CONSUMED"}:
                raise
            blocked.append({"scenario_id": control["scenario_id"], "run_id": control["run_id"],
                            "status": "BLOCKED_MISSING_INPUT" if exc.code == "BLOCKED_MISSING_INPUT"
                                      else "BLOCKED_METHOD_REVIEW", "reason_code": exc.code})
    return prepared, blocked


def run_project(exported, methods, *, bundle_dir, catalog, budget, workspace, run_id,
                generation_dir=None, generation_result_hash=None, scenario_controls=None):
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
    prepared, blocked = _prepare_cases(scenario_controls, original, config, catalog)
    root = workspace.path(run_id, json_only=False)
    if root.exists():
        raise ContractError("PROJECT_OUTPUT_EXISTS")
    # Validate the complete D3 input before creating any published output.
    timing = {"bundle_read_seconds": perf_counter()}
    with read_bundle(bundle_dir, catalog=catalog, budget=budget) as bundle:
        timing["bundle_read_seconds"] = perf_counter() - timing["bundle_read_seconds"]
        if dumps(bundle.base_export) != dumps(original):
            raise ContractError("PROJECT_BUNDLE_BASE_MISMATCH")
        root.mkdir(mode=0o700)
        identity = root.stat().st_dev, root.stat().st_ino
        started = perf_counter()
        try:
            stages = {}
            if generation_dir is None:
                stage_started = perf_counter()
                generate = generate_ground if pv_type == "utility_scale_ground" else generate_rooftop
                generation = generate(original, config, catalog=catalog,
                                      output_dir=root / "3b", budget=budget, bundle=bundle)
                validate_result(generation, catalog)
                generation_dir = root / "3b"
                generation_result_hash = generation["result_hash"]
                stages["3B"] = {"result_hash": generation_result_hash, "reuse": False}
                timing["phase3b_seconds"] = perf_counter() - stage_started
            else:
                generation_dir = Path(generation_dir)
                stages["3B"] = {"result_hash": generation_result_hash, "reuse": True}
                timing["phase3b_seconds"] = 0.0
            settle = settle_ground if pv_type == "utility_scale_ground" else settle_rooftop
            stage_started = perf_counter()
            settlement = settle(original, config, generation_dir=generation_dir,
                                generation_result_hash=generation_result_hash,
                                catalog=catalog, output_dir=root / "3c", budget=budget,
                                bundle=bundle)
            validate_result(settlement, catalog)
            stages["3C"] = {"result_hash": settlement["result_hash"], "reuse": False}
            timing["phase3c_seconds"] = perf_counter() - stage_started
            stage_started = perf_counter()
            financial = calculate_financial_ledger(original, config, settlement, catalog=catalog)
            validate_result(financial, catalog)
            write_financial_bundle(financial, root / "3d")
            stages["3D"] = {"result_hash": financial["result_hash"], "reuse": False}
            timing["phase3d_seconds"] = perf_counter() - stage_started
            stage_started = perf_counter()
            result = calculate_phase3e(financial, config, catalog)
            validate_result(result, catalog)
            write_phase3e_bundle(result, root / "3e")
            stages["3E"] = {"result_hash": result["result_hash"], "reuse": False}
            timing["phase3e_seconds"] = perf_counter() - stage_started
            stage_started = perf_counter()
            # The report layer consumes this one canonical 3E result, including
            # the upstream metric, source, method and formula snapshots.
            Workspace(root).create("canonical.json", result)
            mapping = formula_execution_map(result, catalog)
            Workspace(root).create("formula-execution.json", mapping)
            timing["canonical_serialization_seconds"] = perf_counter() - stage_started
            scenarios = []
            if scenario_controls is not None:
                scenarios.append({"scenario_id": "BASE", "run_id": next(
                    item.run_id for item in prepared if item.scenario_id == "BASE"),
                    "status": result["status"], "input_hash": result["input_hash"],
                    "canonical_result_hash": result["result_hash"],
                    "formula_mapping_hash": mapping["mapping_hash"],
                    "reuse_project_baseline": True})
                (root / "scenarios").mkdir(mode=0o700)
                scenario_workspace = Workspace(root / "scenarios")
                for item in prepared:
                    if item.scenario_id == "BASE":
                        continue
                    try:
                        replay = run_scenario(item, original, config, catalog=catalog,
                                              budget=budget, workspace=scenario_workspace,
                                              original_bundle=bundle,
                                              generation_dir=generation_dir,
                                              generation_result_hash=generation_result_hash,
                                              original_settlement=settlement)
                    except ContractError as exc:
                        if exc.code not in {"BLOCKED_MISSING_INPUT", "BLOCKED_METHOD_REVIEW"}:
                            raise
                        blocked.append({"scenario_id": item.scenario_id, "run_id": item.run_id,
                                        "status": exc.code, "reason_code": exc.code})
                        continue
                    output = Workspace(root / "scenarios" / item.run_id)
                    scenario_result = output.read("scenario-3e/result.json")[0]
                    validate_result(scenario_result, catalog)
                    if (scenario_result["result_hash"] != replay["stage_result_hashes"]["3E"]
                            or scenario_result["scenario_id"] != item.scenario_id):
                        raise ContractError("PROJECT_SCENARIO_RESULT_MISMATCH")
                    output.create("canonical.json", scenario_result)
                    scenario_map = formula_execution_map(scenario_result, catalog)
                    output.create("formula-execution.json", scenario_map)
                    scenarios.append({"scenario_id": item.scenario_id, "run_id": item.run_id,
                                      "status": scenario_result["status"],
                                      "input_hash": scenario_result["input_hash"],
                                      "canonical_result_hash": scenario_result["result_hash"],
                                      "formula_mapping_hash": scenario_map["mapping_hash"],
                                      "replay_receipt_hash": replay["result_hash"]})
                scenarios.extend(blocked)
            receipt = {"project_id": result["project_id"], "pv_type": pv_type,
                       "scenario_id": "BASE", "input_hash": result["input_hash"],
                       "phase2_input_hash": original["input_hash"],
                       "source_snapshot_id": result["source_snapshot_id"],
                       "method_config_hash": config.hash,
                       "definition_version": catalog.definition_version,
                       "definition_hash": catalog.definition_hash,
                       "canonical_result_hash": result["result_hash"],
                       "formula_mapping_hash": mapping["mapping_hash"],
                       "status": result["status"], "stages": stages,
                       "scenarios": scenarios,
                       "timings_seconds": {key: str(value) for key, value in timing.items()}}
            receipt["receipt_hash"] = digest(receipt)
            receipt["elapsed_seconds"] = str(perf_counter() - started)
            Workspace(root).create("receipt.json", receipt)
            return receipt
        except BaseException:
            _remove_owned(root, identity, workspace)
            raise
