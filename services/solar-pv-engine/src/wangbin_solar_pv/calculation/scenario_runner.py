"""Phase 3F scenario input preparation; never edits a project or a sealed result.

A scenario is an explicitly sourced set of single-atom alternatives. The existing
Phase 2 intake/export and D2 method validators remain the authority for values.
This module only prepares inputs; financial results are produced by 3B-3E.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
import re

from ..errors import ContractError
from ..intake import IntakeSession
from ..provenance import make_record
from ..serialization import digest
from .common import exact_json_numbers
from .input_contract import validate_export
from .method_config import MethodConfig, make_parameter

SCENARIO_IDS = frozenset({"BASE", "PESSIMISTIC", "OPTIMISTIC"})
_RUN_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\Z")


@dataclass(frozen=True, slots=True)
class PreparedScenario:
    scenario_id: str
    run_id: str
    input_export: dict
    methods: MethodConfig
    original_input_hash: str
    original_source_snapshot_id: str
    scenario_hash: str
    changed_field_ids: tuple[str, ...]
    changed_method_ids: tuple[str, ...]


def _shape(value, keys, required, code):
    if not isinstance(value, dict) or set(value) - keys or not required <= set(value):
        raise ContractError(code)


def _source(source, methods):
    _shape(source, {"source_id", "source_reference", "source_kind", "status", "license_status"},
           {"source_id", "source_reference", "source_kind", "status", "license_status"},
           "SCENARIO_SOURCE_SHAPE")
    if (source["source_kind"] not in {"USER_PROVIDED", "SYNTHETIC"}
            or source["status"] != "ASSUMED" or source["license_status"] != "AUTHORIZED"
            or source["source_kind"] == "SYNTHETIC" and methods.data_mode != "SYNTHETIC"
            or any(not isinstance(source[key], str) or not source[key].strip()
                   for key in ("source_id", "source_reference"))):
        raise ContractError("SCENARIO_SOURCE_UNAVAILABLE")
    # Reuse the approved source-reference guard, including URL credentials.
    from .break_even_execution import _source_reference
    _source_reference(source["source_id"])
    _source_reference(source["source_reference"])


def _target(project, selector):
    _shape(selector, {"field_id", "row_id", "field_instance_id", "original_atom_hash"},
           {"field_id", "row_id", "field_instance_id", "original_atom_hash"},
           "SCENARIO_SELECTOR_SHAPE")
    fid, row_id = selector["field_id"], selector["row_id"]
    if not isinstance(fid, str) or not isinstance(selector["field_instance_id"], str):
        raise ContractError("SCENARIO_SELECTOR_SHAPE")
    if row_id is None:
        atom = project["values"].get(fid)
        parent = None
    else:
        if not isinstance(row_id, str) or not row_id:
            raise ContractError("SCENARIO_ROW_ID")
        parent_id = fid.rsplit(".", 1)[0]
        parent = project["values"].get(parent_id)
        if not isinstance(parent, dict) or not isinstance(parent.get("value"), list):
            raise ContractError("SCENARIO_ROW_ID")
        rows = [r for r in parent["value"] if isinstance(r, dict) and r.get("row_id") == row_id]
        if len(rows) != 1:
            raise ContractError("SCENARIO_ROW_ID")
        atom = rows[0]["fields"].get(fid)
    if (not isinstance(atom, dict) or atom.get("field_id") != fid
            or atom.get("field_instance_id") != selector["field_instance_id"]
            or digest(atom) != selector["original_atom_hash"]):
        raise ContractError("SCENARIO_ORIGINAL_ATOM_MISMATCH", fid)
    if atom.get("status") not in {"VERIFIED", "ASSUMED", "UNVERIFIED"} or atom.get("license_status") != "AUTHORIZED":
        raise ContractError("SCENARIO_ORIGINAL_SOURCE_UNAVAILABLE", fid)
    return atom, parent


def _candidate(project, old, value, source, selector, catalog):
    fid = old["field_id"]
    if old.get("original_unit") != old.get("unit"):
        raise ContractError("SCENARIO_ORIGINAL_UNIT_UNSUPPORTED", fid)
    if type(value) is bool or not isinstance(value, (int, Decimal)) or value == old["value"]:
        raise ContractError("SCENARIO_CHANGE_REQUIRED", fid)
    atom = make_record(
        catalog, fid, value, source_kind="ASSUMPTION", original_unit=old["unit"],
        field_instance_id=old["field_instance_id"], source_id=source["source_id"],
        source_url_or_attachment=source["source_reference"],
        source_section_or_cell=(old["source_section_or_cell"] if fid == "finance.project_discount_rate"
                                else selector["row_id"] or fid),
        license_status="AUTHORIZED", economic_basis=old.get("economic_basis"),
        confidence_basis="Explicit scenario alternative, not verified project fact",
        assumption={"reason": "Explicit scenario alternative from " + source["source_reference"],
                    "method": "SINGLE_ATOM_ABSOLUTE_REPLACEMENT", "maturity_ceiling": "L1",
                    "noncritical": False, "decision_invariant": False},
    )
    old_id = "candidate-" + digest(old)
    new_id = "candidate-" + digest(atom)
    project["candidates"].setdefault(old_id, deepcopy(old))
    project["candidates"][new_id] = deepcopy(atom)
    atom["candidate_ids"] = list(dict.fromkeys([*old.get("candidate_ids", []), old_id, new_id]))
    return atom, old_id, new_id


def _input_change(project, selector, value, source, catalog):
    old, parent = _target(project, selector)
    atom, old_id, new_id = _candidate(project, old, value, source, selector, catalog)
    if parent is None:
        project["values"][selector["field_id"]] = atom
    else:
        parent_id = parent["field_id"]
        old_parent = deepcopy(parent)
        old_parent_id = "candidate-" + digest(old_parent)
        project["candidates"].setdefault(old_parent_id, old_parent)
        for row in parent["value"]:
            if row["row_id"] == selector["row_id"]:
                row["fields"][selector["field_id"]] = atom
        parent["original_value"] = deepcopy(parent["value"])
        # The array envelope is also a new scenario candidate: an unchanged
        # parent source must not claim authorship of a changed child value.
        parent.update(source_kind="ASSUMPTION", provenance_kind="U", source_id=source["source_id"],
                      source_url_or_attachment=source["source_reference"], status="ASSUMED",
                      reviewer=None, license_status="AUTHORIZED", retrieved_at=None,
                      confidence_basis="Explicit scenario row alternative, not verified project fact",
                      assumption={"reason": "Explicit row alternative from " + source["source_reference"],
                                  "method": "SINGLE_ROW_ATOM_ABSOLUTE_REPLACEMENT", "maturity_ceiling": "L1",
                                  "noncritical": False, "decision_invariant": False})
        pending = deepcopy(parent)
        pending["candidate_ids"] = []
        new_parent_id = "candidate-" + digest(pending)
        project["candidates"][new_parent_id] = pending
        parent["candidate_ids"] = list(dict.fromkeys([*old_parent.get("candidate_ids", []), old_parent_id, new_parent_id]))
        project["history"].append({"event": "scenario_array_candidate", "field_id": parent_id,
                                   "row_id": selector["row_id"], "candidate_id": new_parent_id})
    project["history"].append({"event": "scenario_input_candidate", "field_id": selector["field_id"],
                               "row_id": selector["row_id"], "previous_candidate_id": old_id,
                               "candidate_id": new_id, "source_id": source["source_id"]})


def _method_change(data, selector, value, source, pv_type):
    _shape(selector, {"parameter_id", "original_parameter_hash"},
           {"parameter_id", "original_parameter_hash"}, "SCENARIO_SELECTOR_SHAPE")
    pid = selector["parameter_id"]
    old = data["parameters"].get(pid)
    if (not isinstance(old, dict) or digest(old) != selector["original_parameter_hash"]
            or old["status"] not in {"ASSUMED", "VERIFIED"}
            or old["license_status"] != "AUTHORIZED" or value == old["value"]):
        raise ContractError("SCENARIO_ORIGINAL_METHOD_MISMATCH", pid)
    data["parameters"][pid] = make_parameter(
        pid, value, source_id=source["source_id"], source_reference=source["source_reference"],
        source_kind=source["source_kind"], status="ASSUMED", pv_types=[pv_type],
        license_status="AUTHORIZED")


def prepare_scenario(control, original_export, methods, catalog):
    """Validate one explicit scenario and create independent Phase 2/D2 identities."""
    exact_json_numbers(control)
    _shape(control, {"scenario_id", "run_id", "project_id", "pv_type", "original_input_hash",
                     "original_source_snapshot_id", "method_config_hash", "changes"},
           {"scenario_id", "run_id", "project_id", "pv_type", "original_input_hash",
            "original_source_snapshot_id", "method_config_hash", "changes"}, "SCENARIO_CONTROL_SHAPE")
    export = validate_export(original_export, catalog).export
    methods = MethodConfig.from_dict(methods.to_dict() if isinstance(methods, MethodConfig) else methods)
    if (control["project_id"] != export["project"]["project_id"]
            or control["pv_type"] != export["project"]["pv_type"]
            or control["pv_type"] not in methods.to_dict()["pv_types"]
            or control["original_input_hash"] != export["input_hash"]
            or control["original_source_snapshot_id"] != export["source_snapshot_id"]
            or control["method_config_hash"] != methods.hash):
        raise ContractError("SCENARIO_ORIGINAL_IDENTITY")
    sid, rid = control["scenario_id"], control["run_id"]
    if sid not in SCENARIO_IDS or not isinstance(rid, str) or _RUN_ID.fullmatch(rid) is None:
        raise ContractError("SCENARIO_IDENTITY")
    changes = control["changes"]
    if (not isinstance(changes, list) or len(changes) > 50
            or (sid == "BASE" and changes) or (sid != "BASE" and not changes)):
        raise ContractError("SCENARIO_CHANGES_REQUIRED")
    project = deepcopy(export["project"])
    data = methods.to_dict()
    fields, parameters, seen = [], [], set()
    for change in changes:
        _shape(change, {"factor", "target_kind", "selector", "value", "source"},
               {"factor", "target_kind", "selector", "value", "source"}, "SCENARIO_CHANGE_SHAPE")
        source = change["source"]
        _source(source, methods)
        selector, kind = change["selector"], change["target_kind"]
        if kind not in {"INPUT", "METHOD"} or not isinstance(selector, dict):
            raise ContractError("SCENARIO_CHANGE_SHAPE")
        name = selector.get("field_id") if kind == "INPUT" else selector.get("parameter_id")
        key = (kind, name, selector.get("row_id"))
        if key in seen:
            raise ContractError("SCENARIO_DUPLICATE_TARGET")
        seen.add(key)
        # The factor selector is a consumer whitelist, not a free-form input editor.
        from .sensitivity import validate_factor
        validate_factor(change["factor"], kind, name, selector.get("row_id"), change["value"], export, methods)
        if kind == "INPUT":
            _input_change(project, selector, change["value"], source, catalog)
            fields.append(name)
        else:
            _method_change(data, selector, change["value"], source, control["pv_type"])
            parameters.append(name)
    updated_methods = MethodConfig.from_dict(data)
    if changes:
        project["revision"] += 1
        project["history"].append({"event": "phase3f_scenario", "scenario_id": sid, "run_id": rid,
                                   "original_input_hash": export["input_hash"],
                                   "original_method_config_hash": methods.hash,
                                   "control_hash": digest(control)})
    candidate_export = validate_export(IntakeSession.from_dict(project, catalog).export(), catalog).export
    if changes and candidate_export["input_hash"] == export["input_hash"] and updated_methods.hash == methods.hash:
        raise ContractError("SCENARIO_IDENTITY_NOT_CHANGED")
    return PreparedScenario(sid, rid, candidate_export, updated_methods,
                            export["input_hash"], export["source_snapshot_id"], digest(control),
                            tuple(sorted(set(fields))), tuple(sorted(set(parameters))))


def prepare_scenarios(controls, original_export, methods, catalog):
    """All three named cases are explicit; no silent percentage shocks."""
    if not isinstance(controls, list) or len(controls) != 3:
        raise ContractError("SCENARIO_SET_REQUIRED")
    prepared = [prepare_scenario(item, original_export, methods, catalog) for item in controls]
    if {item.scenario_id for item in prepared} != SCENARIO_IDS or len({item.run_id for item in prepared}) != 3:
        raise ContractError("SCENARIO_SET_REQUIRED")
    return {item.scenario_id: item for item in prepared}


def seal_scenario_run(prepared, results, catalog):
    """Hash only verified producer outputs; never synthesize a financial result."""
    from .result_contract import validate_result
    if not isinstance(prepared, PreparedScenario) or not isinstance(results, dict) or not results:
        raise ContractError("SCENARIO_RESULTS_REQUIRED")
    for stage, result in results.items():
        if stage not in {"3B", "3C", "3D", "3E"} or not isinstance(result, dict):
            raise ContractError("SCENARIO_RESULTS_REQUIRED")
        validate_result(result, catalog)
        if (result["project_id"] != prepared.input_export["project"]["project_id"]
                or result["pv_type"] != prepared.input_export["project"]["pv_type"]
                or result["scenario_id"] != prepared.scenario_id
                or result["inputs"].get("normalized") != prepared.input_export["normalized_inputs"]
                or result["inputs"].get("method_config_hash") != prepared.methods.hash
                or result["inputs"].get("identity_payload", {}).get("phase2_input_hash")
                    != prepared.input_export["input_hash"]
                or result["source_snapshot"].get("phase2") != prepared.input_export["source_snapshot"]
                or result["source_snapshot"].get("methods") != prepared.methods.to_dict()):
            raise ContractError("SCENARIO_RESULT_IDENTITY_MISMATCH")
    if ("3D" in results and "3C" in results and
            results["3D"]["inputs"].get("upstream_settlement_result_hash") != results["3C"]["result_hash"]):
        raise ContractError("SCENARIO_UPSTREAM_RESULT_MISMATCH")
    if "3E" in results and "3D" in results:
        phase3e, financial = results["3E"], results["3D"]
        upstream_hash = phase3e["inputs"].get("identity_payload", {}).get("upstream_financial_result_hash")
        if upstream_hash is None:
            # The common 3E producer extends a sealed 3D result in place and
            # retains the same input/source identity and actual annual ledger.
            if (phase3e["input_hash"] != financial["input_hash"]
                    or phase3e["source_snapshot"] != financial["source_snapshot"]
                    or phase3e["evidence"].get("financial-ledger")
                        != financial["evidence"].get("financial-ledger")):
                raise ContractError("SCENARIO_UPSTREAM_RESULT_MISMATCH")
        elif upstream_hash != financial["result_hash"]:
            raise ContractError("SCENARIO_UPSTREAM_RESULT_MISMATCH")
    receipt = {"scenario_id": prepared.scenario_id, "run_id": prepared.run_id,
               "original_input_hash": prepared.original_input_hash,
               "original_source_snapshot_id": prepared.original_source_snapshot_id,
               "input_hash": prepared.input_export["input_hash"],
               "source_snapshot_id": prepared.input_export["source_snapshot_id"],
               "method_config_hash": prepared.methods.hash,
               "scenario_hash": prepared.scenario_hash,
               "stage_result_hashes": {stage: result["result_hash"] for stage, result in sorted(results.items())}}
    return {**receipt, "result_hash": digest(receipt)}


def _trusted_original_settlement(result, original_export, original_methods, catalog):
    from .result_contract import validate_result
    validate_result(result, catalog)
    if (result["project_id"] != original_export["project"]["project_id"]
            or result["pv_type"] != original_export["project"]["pv_type"]
            or result["inputs"].get("normalized") != original_export["normalized_inputs"]
            or result["inputs"].get("method_config_hash") != original_methods.hash
            or result["inputs"].get("identity_payload", {}).get("phase2_input_hash")
                != original_export["input_hash"]
            or result["source_snapshot"].get("phase2") != original_export["source_snapshot"]
            or result["source_snapshot"].get("methods") != original_methods.to_dict()
            or result["results"]["domains"].get("revenue") is None):
        raise ContractError("SCENARIO_ORIGINAL_SETTLEMENT_IDENTITY")
    return result


def run_scenario(prepared, original_export, original_methods, *, catalog, budget, workspace,
                 original_bundle=None, generation_dir=None, generation_result_hash=None,
                 original_settlement=None):
    """Execute affected 3B→3E producers, reusing only a pinned unaffected 3C.

    The common Phase 3E producer remains partial without terminal cash. A
    discount-only scenario cannot claim a new NPV using the old 3D result.
    No calculated metric is scaled or copied into a new result envelope.
    """
    from pathlib import Path
    from time import perf_counter

    from ..local_files import Workspace
    from ..timeseries_bundle import BundleBudget, TimeSeriesBundle, read_bundle, write_bundle
    from .break_even_replay import _remove_owned, _verify_bundles
    from .energy_yield import calculate_ground as generate_ground, calculate_rooftop as generate_rooftop
    from .financial_ledger import calculate_financial_ledger, write_financial_bundle
    from .phase3e import calculate_phase3e, write_phase3e_bundle
    from .revenue import calculate_ground as settle_ground, calculate_rooftop as settle_rooftop
    from .sensitivity import scenario_calculation_graph

    if not isinstance(prepared, PreparedScenario) or type(budget) is not BundleBudget or not isinstance(workspace, Workspace):
        raise ContractError("SCENARIO_EXECUTION_CONTEXT")
    original = validate_export(original_export, catalog).export
    original_methods = MethodConfig.from_dict(
        original_methods.to_dict() if isinstance(original_methods, MethodConfig) else original_methods)
    if (prepared.original_input_hash != original["input_hash"]
            or prepared.original_source_snapshot_id != original["source_snapshot_id"]
            or prepared.input_export["project"]["project_id"] != original["project"]["project_id"]
            or prepared.input_export["project"]["pv_type"] != original["project"]["pv_type"]):
        raise ContractError("SCENARIO_ORIGINAL_IDENTITY")
    validate_export(prepared.input_export, catalog)
    MethodConfig.from_dict(prepared.methods.to_dict())
    graph = scenario_calculation_graph(catalog, original["project"]["pv_type"], prepared.methods)
    affected = graph.affected_by(prepared.changed_field_ids,
                                 method_parameter_ids=prepared.changed_method_ids)
    # The current 3C trace consumer accepts only INTERVAL_DC_AC; the POA_PR
    # producer has a distinct boundary. A valid D2 PR alternative alone is
    # therefore not a runnable 3B→3C→3D sensitivity chain.
    if "energy.pr" in prepared.changed_method_ids:
        raise ContractError("BLOCKED_METHOD_REVIEW", "scenario.generation_interval_boundary")
    # The only sourced terminal/NPV branch currently accepts an exact
    # single-price derivative. It cannot legitimize a changed project rate.
    if "finance.project_discount_rate" in prepared.changed_field_ids:
        raise ContractError("BLOCKED_MISSING_INPUT", "scenario.project_npv_terminal_binding")
    finance_only = not set(affected).intersection({"3B", "3C"})
    reused = None
    if finance_only and original_settlement is not None and prepared.methods.hash == original_methods.hash:
        reused = _trusted_original_settlement(original_settlement, original, original_methods, catalog)
    if reused is None and (not isinstance(original_bundle, TimeSeriesBundle)
                           or generation_dir is None or generation_result_hash is None):
        raise ContractError("BLOCKED_MISSING_INPUT", "scenario.upstream_generation_and_d3")
    if original_bundle is not None and original_bundle.base_export != original:
        raise ContractError("SCENARIO_ORIGINAL_BUNDLE_IDENTITY")
    root = workspace.path(prepared.run_id, json_only=False)
    if root.exists():
        raise ContractError("SCENARIO_OUTPUT_EXISTS")
    root.mkdir(mode=0o700)
    identity = root.stat().st_dev, root.stat().st_ino
    started = perf_counter()
    try:
        results = {}
        if reused is None:
            datasets = {name: {"header": original_bundle.manifest["datasets"][name]["header"],
                               "rows": original_bundle.rows(name)}
                        for name in original_bundle.dataset_ids}
            write_bundle(root / "scenario-d3", base_export=prepared.input_export,
                         datasets=datasets, catalog=catalog, budget=budget)
            with read_bundle(root / "scenario-d3", catalog=catalog, budget=budget) as bundle:
                _verify_bundles(original_bundle, bundle, "", None)
                if "3B" in affected or prepared.scenario_id == "BASE" and generation_dir is None:
                    generate = generate_ground if prepared.input_export["project"]["pv_type"] == "utility_scale_ground" else generate_rooftop
                    results["3B"] = generate(prepared.input_export, prepared.methods, catalog=catalog,
                                               output_dir=root / "scenario-3b", budget=budget, bundle=bundle,
                                               scenario_id=prepared.scenario_id)
                    generation_dir = root / "scenario-3b"
                    generation_result_hash = results["3B"]["result_hash"]
                settle = settle_ground if prepared.input_export["project"]["pv_type"] == "utility_scale_ground" else settle_rooftop
                results["3C"] = settle(prepared.input_export, prepared.methods,
                                        generation_dir=Path(generation_dir),
                                        generation_result_hash=generation_result_hash,
                                        catalog=catalog, output_dir=root / "scenario-3c", budget=budget,
                                        bundle=bundle, scenario_id=prepared.scenario_id)
        settlement = results.get("3C", reused)
        if settlement is None:
            raise ContractError("SCENARIO_SETTLEMENT_REQUIRED")
        results["3D"] = calculate_financial_ledger(prepared.input_export, prepared.methods,
                                                     settlement, catalog=catalog,
                                                     scenario_id=prepared.scenario_id)
        results["3E"] = calculate_phase3e(results["3D"], prepared.methods, catalog)
        receipt = seal_scenario_run(prepared, results, catalog)
        receipt["affected_stages"] = affected
        receipt["reused_settlement_result_hash"] = None if reused is None else reused["result_hash"]
        receipt["reused_generation_result_hash"] = (
            generation_result_hash if "3B" not in results and reused is None else None)
        receipt["result_hash"] = digest({key: value for key, value in receipt.items() if key != "result_hash"})
        # Elapsed duration is operational evidence, not a scenario calculation
        # identity. It is deliberately excluded from the reproducible digest.
        receipt["elapsed_seconds"] = Decimal(str(perf_counter() - started))
        write_financial_bundle(results["3D"], root / "scenario-3d")
        write_phase3e_bundle(results["3E"], root / "scenario-3e")
        Workspace(root).create("receipt.json", receipt)
        return receipt
    except BaseException:
        _remove_owned(root, identity, workspace)
        raise
