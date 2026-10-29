"""The only project calculation ingress: revalidate a Phase 2 export in full.

Recomputed projections are compared, not trusted because a supplied hash exists.
A legacy input export's identity stays intact. D2 methods and D3 datasets get an
explicit composite identity; they never overwrite the Phase 2 provenance hash.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from ..categories import validate_category
from ..errors import ContractError
from ..intake import IntakeSession
from ..models import ProjectData
from ..serialization import digest, dumps
from ..validation import iter_records, validate_project, validate_record

SUPPORTED_INPUT_MODULE_VERSIONS = {"0.2.0", "0.3.0"}


@dataclass(frozen=True, slots=True)
class ValidatedInput:
    project: ProjectData
    export: dict
    phase2_input_hash: str
    phase2_source_snapshot_id: str
    validation_issues: tuple


def validate_export(exported, catalog):
    dumps(exported)
    if not isinstance(exported, dict) or exported.get("schema_version") != "solar-pv-input-export/1.0.0":
        raise ContractError("INPUT_EXPORT_VERSION")
    if exported.get("input_module_version") not in SUPPORTED_INPUT_MODULE_VERSIONS:
        raise ContractError("INPUT_MODULE_VERSION")
    if not isinstance(exported.get("project"), dict):
        raise ContractError("INPUT_EXPORT_PROJECT_REQUIRED")
    project = ProjectData.from_dict(exported["project"], catalog)
    issues = validate_project(project, catalog) + validate_category(project, catalog)
    for candidate in project.candidates.values():
        for record, scalar in iter_records({candidate["field_id"]: candidate}, catalog):
            issues.extend(validate_record(record, catalog, scalar_item=scalar))
    errors = [issue for issue in issues if issue.severity == "ERROR"]
    if errors:
        error = ContractError("INPUT_VALIDATION_FAILED", errors[0].field_id)
        error.issues = [issue.to_dict() for issue in errors]
        raise error
    # The legacy source snapshot hashes an ordered record list. Canonical JSON
    # sorts object keys; recover the original traversal, not a new input identity.
    snapshot = exported.get("source_snapshot")
    records = snapshot.get("records") if isinstance(snapshot, dict) else None
    if not isinstance(records, list) or any(not isinstance(r, dict) or not isinstance(r.get("field_instance_id"), str) for r in records):
        raise ContractError("INPUT_EXPORT_INTEGRITY_MISMATCH")
    rank = {r["field_instance_id"]: index for index, r in enumerate(records)}
    actual = [r["field_instance_id"] for r, _ in iter_records(project.values, catalog)]
    if len(rank) != len(records) or len(set(actual)) != len(actual) or set(actual) != set(rank):
        raise ContractError("INPUT_EXPORT_INTEGRITY_MISMATCH")

    def restore(values):
        ordered = dict(sorted(values.items(), key=lambda item: rank[item[1]["field_instance_id"]]))
        for record in ordered.values():
            field = catalog.fields[record["field_id"]]
            if field["type"] == "array" and isinstance(record["value"], list) and field["constraints"]["items"]["type"] == "object":
                for row in record["value"]:
                    row["fields"] = restore(row["fields"])
        return ordered

    project.values = restore(project.values)
    regenerated = IntakeSession(project, catalog).export()
    # The old module version is accepted only for the same declared 1.0.0 input
    # contract. This does not silently migrate business values or their hashes.
    regenerated["input_module_version"] = exported["input_module_version"]
    if dumps(exported) != dumps(regenerated):
        raise ContractError("INPUT_EXPORT_INTEGRITY_MISMATCH")
    return ValidatedInput(project, deepcopy(exported), exported["input_hash"],
                          exported["source_snapshot_id"], tuple(issue.to_dict() for issue in issues))


def calculation_identity(validated, methods, catalog, *, datasets=None, scenario=None):
    from .method_config import MethodConfig
    if not isinstance(validated, ValidatedInput) or not isinstance(methods, MethodConfig):
        raise ContractError("CALCULATION_INPUT_NOT_VALIDATED")
    checked = validate_export(validated.export, catalog)
    if (dumps(checked.project.to_dict()) != dumps(validated.project.to_dict())
            or checked.phase2_input_hash != validated.phase2_input_hash
            or checked.phase2_source_snapshot_id != validated.phase2_source_snapshot_id):
        raise ContractError("CALCULATION_INPUT_CHANGED")
    validated = checked
    methods = MethodConfig.from_dict(methods.to_dict())
    catalog.definition_identity()
    if validated.project.pv_type not in methods.to_dict()["pv_types"]:
        raise ContractError("METHOD_CONFIG_CATEGORY")
    # Dataset transport paths, chunking, elapsed time and process memory are not
    # business content. Only the verified, layout-independent content identity
    # and original provenance header belong in this canonical payload.
    dataset_identity = {}
    if datasets is not None:
        from ..timeseries_bundle import TimeSeriesBundle, canonical_array_hash
        if not isinstance(datasets, TimeSeriesBundle):
            raise ContractError("CALCULATION_DATASET_NOT_VALIDATED")
        if dumps(datasets.base_export) != dumps(validated.export):
            raise ContractError("CALCULATION_DATASET_BASE_MISMATCH")
        manifest = datasets.manifest
        # Finish every iterator before publishing an identity. This rechecks the
        # immutable on-disk manifest, membership and whole-block hashes and fails
        # closed when the bundle was closed or modified after read_bundle.
        content = {}
        for fid in datasets.dataset_ids:
            descriptor = manifest["datasets"][fid]
            if canonical_array_hash(datasets.rows(fid)) != descriptor["canonical_array_hash"]:
                raise ContractError("CALCULATION_DATASET_CHANGED")
            content[fid] = {key: deepcopy(value) for key, value in descriptor.items() if key != "chunks"}
        dataset_identity = {"schema_version": manifest["schema_version"],
                            "content_hash": datasets.content_hash, "datasets": content}
    scenario_identity = {"scenario_id": "BASE"} if scenario is None else deepcopy(scenario)
    definition = {"version": catalog.definition_version, "hash": catalog.definition_hash}
    snapshot = {"phase2": deepcopy(validated.export["source_snapshot"]),
                "methods": methods.to_dict(), "datasets": dataset_identity,
                "formula_definition": definition}
    source_id = digest(snapshot)
    business = {"hash_algorithm_version": "sha256/solar-pv-calculation-input-v1",
                "phase2_input_hash": validated.phase2_input_hash,
                "phase2_source_snapshot_id": validated.phase2_source_snapshot_id,
                "source_snapshot_id": source_id, "method_config_hash": methods.hash,
                "formula_definition": definition, "datasets": dataset_identity,
                "scenario": scenario_identity}
    return {"input_hash": digest(business), "source_snapshot_id": source_id,
            "phase2_input_hash": validated.phase2_input_hash,
            "phase2_source_snapshot_id": validated.phase2_source_snapshot_id,
            "method_config_hash": methods.hash, "source_snapshot": snapshot,
            "input_identity_payload": business}
