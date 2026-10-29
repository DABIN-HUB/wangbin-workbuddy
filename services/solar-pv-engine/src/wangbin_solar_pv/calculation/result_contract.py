"""Frozen 12-numbered canonical result contract and invariant content hashing.

This is the only numerical result format, not a document renderer. No artifact,
real-project or platform gate is upgraded by constructing or sealing a result.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4

from ..errors import ContractError
from ..schemas import StrictValidator, format_checker
from ..serialization import digest, dumps, loads
from . import MODEL_VERSION, RESULT_SCHEMA_VERSION
from .common import exact_json_numbers

HASH_EXCLUDED = frozenset({"result_hash", "run_id", "created_at", "artifact_manifest"})
ROOTS = "schema_version model_version run_id input_hash source_snapshot_id result_hash project_id pv_type scenario_id created_at evaluation_date currency maturity status boundaries inputs source_snapshot formula_snapshot results findings evidence artifact_manifest".split()
METRIC_KEYS = "metric_id value unit status reason boundary_id period scenario_id input_field_ids source_ids formula_id formula_version evidence_ids report_locations workbook_locations rounding_rule".split()


def result_schema():
    text = {"type": "string", "minLength": 1, "maxLength": 4000}
    strings = {"type": "array", "items": text, "uniqueItems": True}
    nullable_text = {"type": ["string", "null"], "minLength": 1}
    metric = {"type": "object", "additionalProperties": False, "required": METRIC_KEYS, "properties": {
        "metric_id": text, "value": {"anyOf": [{"type": "number"}, {"type": "null"}, {"type": "array", "items": {"type": "number"}}]},
        "unit": nullable_text, "status": {"enum": ["CALCULATED", "UNKNOWN", "UNDEFINED", "NOT_APPLICABLE", "BLOCKED_MISSING_INPUT", "BLOCKED_METHOD_REVIEW", "NOT_IMPLEMENTED"]},
        "reason": nullable_text, "boundary_id": text, "period": text, "scenario_id": text,
        "input_field_ids": strings, "source_ids": strings, "formula_id": text, "formula_version": text,
        "evidence_ids": strings, "report_locations": strings, "workbook_locations": strings,
        "rounding_rule": text, "method_parameter_ids": strings, "upstream_metric_ids": strings,
        "details": {"type": "object"}}}
    fields = {
        "schema_version": {"const": RESULT_SCHEMA_VERSION}, "model_version": {"const": MODEL_VERSION},
        "run_id": text, "input_hash": text, "source_snapshot_id": text, "result_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "project_id": text, "pv_type": {"enum": ["industrial_rooftop", "utility_scale_ground", "agri_pv", "fishery_pv", "pv_storage", "public_rooftop", "residential_pv", "pv_carport_bipv", "desert_mining"]},
        "scenario_id": text, "created_at": {"type": "string", "format": "date-time"},
        "evaluation_date": {"type": "string", "format": "date"}, "currency": {"type": "string", "pattern": "^[A-Z]{3}$"},
        "maturity": {"type": "object", "additionalProperties": False,
                     "required": ["calculation", "real_project", "four_files", "platform"],
                     "properties": {
                         "calculation": {"enum": ["NOT_IMPLEMENTED", "CALCULATED_SYNTHETIC", "CALCULATED_CONDITIONAL", "PARTIAL", "BLOCKED"]},
                         "real_project": {"enum": ["NOT_VERIFIED", "BLOCKED"]},
                         "four_files": {"enum": ["NOT_IMPLEMENTED", "BLOCKED"]},
                         "platform": {"enum": ["NOT_TESTED", "BLOCKED"]},
                         "input_evidence": {"type": "object"}}},
        "status": {"enum": ["CALCULATED_SYNTHETIC", "CALCULATED_CONDITIONAL", "PARTIAL", "BLOCKED_MISSING_INPUT", "BLOCKED_METHOD_REVIEW", "NOT_IMPLEMENTED"]},
        "boundaries": {"type": "object"}, "inputs": {"type": "object"}, "source_snapshot": {"type": "object"},
        "formula_snapshot": {"type": "object", "required": ["definition_version", "definition_hash"], "properties": {"definition_version": text, "definition_hash": text}},
        "results": {"type": "object", "additionalProperties": False, "required": ["metrics", "domains"], "properties": {
            "metrics": {"type": "array", "maxItems": 200000, "items": metric},
            "domains": {"type": "object", "additionalProperties": {"type": "array", "items": text, "uniqueItems": True}}}},
        "findings": {"type": "array", "items": {"type": "object"}},
        "evidence": {"type": "object"}, "artifact_manifest": {"type": "array", "items": {"type": "object"}},
    }
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": RESULT_SCHEMA_VERSION,
            "type": "object", "additionalProperties": False, "properties": fields, "required": ROOTS}


def result_hash(result):
    exact_json_numbers(result)
    return digest({key: value for key, value in result.items() if key not in HASH_EXCLUDED})


def seal_result(result):
    result = deepcopy(result)
    result["result_hash"] = result_hash(result)
    return result


def empty_result(*, project_id, pv_type, evaluation_date, currency, scenario_id, input_hash,
                 source_snapshot_id, baseline_hashes, definition_version, definition_hash):
    result = {"schema_version": RESULT_SCHEMA_VERSION, "model_version": MODEL_VERSION,
              "run_id": str(uuid4()), "created_at": datetime.now(timezone.utc).isoformat(),
              "input_hash": input_hash, "source_snapshot_id": source_snapshot_id,
              "project_id": project_id, "pv_type": pv_type, "scenario_id": scenario_id,
              "evaluation_date": evaluation_date, "currency": currency,
              "maturity": {"calculation": "NOT_IMPLEMENTED", "real_project": "NOT_VERIFIED", "four_files": "NOT_IMPLEMENTED", "platform": "NOT_TESTED"},
              "status": "NOT_IMPLEMENTED", "boundaries": {}, "inputs": {"baseline_hashes": deepcopy(baseline_hashes)},
              "source_snapshot": {}, "formula_snapshot": {"definition_version": definition_version, "definition_hash": definition_hash},
              "results": {"metrics": [], "domains": {}}, "findings": [], "evidence": {}, "artifact_manifest": []}
    return seal_result(result)


def validate_result(result, catalog):
    exact_json_numbers(result)
    catalog.definition_identity()
    if not isinstance(result, dict) or result.get("schema_version") != RESULT_SCHEMA_VERSION:
        raise ContractError("RESULT_SCHEMA_VERSION")
    if result.get("result_hash") != result_hash(result):
        raise ContractError("RESULT_HASH_MISMATCH")
    if next(StrictValidator(result_schema(), format_checker=format_checker()).iter_errors(result), None) is not None:
        raise ContractError("RESULT_SCHEMA")
    if result["formula_snapshot"]["definition_version"] != catalog.definition_version or result["formula_snapshot"]["definition_hash"] != catalog.definition_hash:
        raise ContractError("RESULT_DEFINITION_VERSION_REEXECUTION_REQUIRED")
    if result["inputs"].get("baseline_hashes") != catalog.baseline_hashes:
        raise ContractError("RESULT_BASELINE_MISMATCH")
    metrics = result["results"]["metrics"]
    ids = {m["metric_id"] for m in metrics}
    if len(ids) != len(metrics):
        raise ContractError("DUPLICATE_METRIC_ID")
    source_ids = set()
    pending = [result["source_snapshot"]]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            source_id = item.get("source_id")
            if isinstance(source_id, str):
                source_ids.add(source_id)
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    methods = result["source_snapshot"].get("methods", {})
    method_ids = set(methods.get("parameters", {})) if isinstance(methods, dict) else set()
    for metric in metrics:
        if metric["formula_id"] not in catalog.formulas or metric["formula_version"] != catalog.definition_version:
            raise ContractError("METRIC_FORMULA_REFERENCE")
        if metric["scenario_id"] != result["scenario_id"]:
            raise ContractError("METRIC_SCENARIO_REFERENCE")
        if metric["status"] == "CALCULATED" and metric["value"] is None:
            raise ContractError("CALCULATED_METRIC_REQUIRES_VALUE")
        if metric["status"] != "CALCULATED" and (metric["value"] is not None or not metric["reason"]):
            raise ContractError("NONNUMERICAL_METRIC_REQUIRES_REASON")
        if set(metric.get("input_field_ids", [])) - set(catalog.fields):
            raise ContractError("METRIC_RAW_FIELD_REFERENCE")
        if set(metric.get("upstream_metric_ids", [])) - ids:
            raise ContractError("METRIC_UPSTREAM_REFERENCE")
        if metric["boundary_id"] not in result["boundaries"]:
            raise ContractError("METRIC_BOUNDARY_REFERENCE")
        if set(metric["source_ids"]) - source_ids:
            raise ContractError("METRIC_SOURCE_REFERENCE")
        if set(metric["evidence_ids"]) - set(result["evidence"]):
            raise ContractError("METRIC_EVIDENCE_REFERENCE")
        if set(metric.get("method_parameter_ids", [])) - method_ids:
            raise ContractError("METRIC_METHOD_REFERENCE")
    for members in result["results"]["domains"].values():
        if set(members) - ids:
            raise ContractError("RESULT_DOMAIN_METRIC_REFERENCE")
    if result["status"].startswith("CALCULATED_") or any(m["status"] == "CALCULATED" for m in metrics):
        if not metrics or digest(result["source_snapshot"]) != result["source_snapshot_id"]:
            raise ContractError("RESULT_SOURCE_IDENTITY")
        identity = result["inputs"].get("identity_payload")
        if not identity or digest(identity) != result["input_hash"]:
            raise ContractError("RESULT_INPUT_IDENTITY")
        if identity.get("source_snapshot_id") != result["source_snapshot_id"]:
            raise ContractError("RESULT_INPUT_SOURCE_IDENTITY")
    return deepcopy(result)


def serialize_result(result, catalog):
    validate_result(result, catalog)
    return dumps(result)


def deserialize_result(text, catalog):
    return validate_result(loads(text), catalog)
