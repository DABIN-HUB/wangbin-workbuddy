"""Complete JSON Schema 2020-12 projection of the frozen 469 field contracts."""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import math

from jsonschema import Draft202012Validator, FormatChecker, validators
from . import SCHEMA_VERSION
from .errors import ContractError

STRING_OR_NULL = {"type": ["string", "null"]}


def _number(_, value):
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    return isinstance(value, (float, Decimal)) and (value.is_finite() if isinstance(value, Decimal) else math.isfinite(value))


def _integer(_, value):
    # Do not coerce 1.0, numeric text, or booleans into an integer field.
    return type(value) is int


StrictValidator = validators.extend(Draft202012Validator, type_checker=Draft202012Validator.TYPE_CHECKER.redefine("number", _number).redefine("integer", _integer))


def format_checker():
    # jsonschema's optional RFC3339 dependency must not decide evidence validity.
    from .units import validate_date, validate_datetime
    checker = FormatChecker()
    checker.checks("date", raises=ContractError)(lambda value: not isinstance(value, str) or bool(validate_date(value)))
    checker.checks("date-time", raises=ContractError)(lambda value: not isinstance(value, str) or bool(validate_datetime(value)))
    return checker


def evidence_properties():
    string = {"type": "string", "minLength": 1, "maxLength": 4000}
    arr = {"type": "array", "items": {"type": "string", "minLength": 1}, "uniqueItems": True}
    return {
        "field_id": string, "field_instance_id": string, "value": {}, "unit": STRING_OR_NULL,
        "provenance_kind": {"enum": ["U", "D", "C", "AI", None]},
        "source_kind": {"enum": ["USER_PROVIDED", "DOCUMENT_EXTRACTED", "EXTERNAL_SOURCE", "CALCULATED", "ASSUMPTION", "UNKNOWN"]},
        "original_value": {}, "original_unit": STRING_OR_NULL,
        "source_id": STRING_OR_NULL, "source_url_or_attachment": STRING_OR_NULL,
        "source_section_or_cell": STRING_OR_NULL,
        "measurement_period": {"type": ["object", "null"], "additionalProperties": False, "properties": {
            "start": STRING_OR_NULL, "end": STRING_OR_NULL, "timezone": STRING_OR_NULL,
            "interval_minutes": {"type": ["number", "null"], "exclusiveMinimum": 0},
            "coverage": {"type": ["number", "null"], "minimum": 0, "maximum": 1}}},
        "published_at": {"type": ["string", "null"], "format": "date"},
        "retrieved_at": {"type": ["string", "null"], "format": "date-time"},
        "effective_from": {"type": ["string", "null"], "format": "date"},
        "effective_to": {"type": ["string", "null"], "format": "date"},
        "geography": STRING_OR_NULL,
        "status": {"enum": ["VERIFIED", "UNVERIFIED", "ASSUMED", "UNKNOWN", "CONFLICT"]},
        "confidence_basis": string, "reviewer": STRING_OR_NULL,
        "last_updated": {"type": "string", "format": "date-time"}, "missing_reason": STRING_OR_NULL,
        "candidate_ids": arr, "transformation_rule_ids": arr, "upstream_instance_ids": arr,
        "license_status": {"enum": ["AUTHORIZED", "REQUIRES_REVIEW", "DENIED", "UNKNOWN"]},
        "sensitivity": {"enum": ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"]},
        "location_status": {"enum": ["EXACT", "TEXT_FRAGMENT", "UNKNOWN", "NOT_APPLICABLE"]},
        "formula_id": STRING_OR_NULL, "formula_version": STRING_OR_NULL, "run_id": STRING_OR_NULL,
        "assumption": {"type": ["object", "null"], "additionalProperties": False, "properties": {
            "reason": string, "method": string, "lower": {}, "upper": {},
            "maturity_ceiling": {"enum": ["L1", "L2"]}, "noncritical": {"type": "boolean"},
            "decision_invariant": {"type": "boolean"}}, "required": ["reason", "method", "maturity_ceiling", "noncritical", "decision_invariant"]},
        "normalization": {"type": ["object", "null"], "additionalProperties": False, "properties": {
            "rule_id": string, "exact": {"type": "boolean"}, "rounding_policy": {"type": ["object", "null"]},
            "currency": {"type": ["string", "null"], "pattern": "^[A-Z]{3}$"}},
            "required": ["rule_id", "exact", "rounding_policy"]},
        "economic_basis": {"type": ["object", "null"], "additionalProperties": False, "properties": {
            "currency": {"type": "string", "pattern": "^[A-Z]{3}$"}, "price_year": {"type": "integer", "minimum": 1900, "maximum": 2200},
            "tax_basis": {"enum": ["inclusive", "exclusive", "not_applicable"]}, "price_basis": {"enum": ["nominal", "real"]}},
            "required": ["currency", "price_year", "tax_basis", "price_basis"]},
    }


def _envelope(field, value_schema):
    properties = deepcopy(evidence_properties())
    properties.update(field_id={"const": field["field_id"]}, unit={"const": field["unit"]},
                      value={"anyOf": [value_schema, {"type": "null"}]})
    return {"type": "object", "additionalProperties": False, "properties": properties,
            "required": list(properties), "x-field-definition": deepcopy(field)}


def _value_schema(field, catalog):
    allowed = {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "enum", "pattern", "format", "minLength", "maxLength", "minItems", "maxItems", "uniqueItems"}
    result = {"type": field["type"], **{k: deepcopy(v) for k, v in field["constraints"].items() if k in allowed}}
    if field["type"] != "array":
        return result
    items = field["constraints"]["items"]
    if items["type"] == "object":
        item_fields = {child: {"$ref": "#/$defs/" + child} for child in items["field_ids"]}
        result["items"] = {"type": "object", "additionalProperties": False, "properties": {
            "row_id": {"type": "string", "minLength": 1, "maxLength": 2000},
            "fields": {"type": "object", "additionalProperties": False, "properties": item_fields}}, "required": ["row_id", "fields"]}
    else:
        scalar = _envelope(field, {"type": items["type"], "minLength": 1})
        scalar["properties"]["value"] = {"type": items["type"], "minLength": 1}
        result["items"] = scalar
        # Equality of scalar values is checked semantically, not entire envelopes.
        result.pop("uniqueItems", None)
    return result


def build_schema(catalog) -> dict:
    from .applicability import RULE_FIELDS
    definitions = {fid: _envelope(field, _value_schema(field, catalog)) for fid, field in catalog.fields.items()}
    root_fields = {fid: {"$ref": "#/$defs/" + fid} for fid, field in catalog.fields.items() if not field.get("repeat_group")}
    record_union = {"anyOf": [{"$ref": "#/$defs/" + fid} for fid in catalog.fields]}
    properties = {
        "schema_version": {"const": SCHEMA_VERSION}, "baseline_version": {"const": catalog.baseline_version},
        "baseline_hashes": {"const": catalog.baseline_hashes},
        "project_id": {"type": "string", "minLength": 1, "maxLength": 200},
        "pv_type": {"enum": list(catalog.pv_types)},
        "values": {"type": "object", "additionalProperties": False, "properties": root_fields},
        "candidates": {"type": "object", "maxProperties": 100000, "additionalProperties": record_union},
        "resolutions": {"type": "array", "items": {"type": "object"}},
        "revision": {"type": "integer", "minimum": 0},
        "submission_ids": {"type": "object", "additionalProperties": {"type": "string", "pattern": "^[0-9a-f]{64}$"}},
        "history": {"type": "array", "items": {"type": "object"}},
        "applicability": {"type": "object", "additionalProperties": {
            "type": "object", "additionalProperties": False, "properties": {
                "field_id": {"enum": list(catalog.fields)}, "row_id": STRING_OR_NULL,
                "status": {"enum": ["APPLICABLE", "NOT_APPLICABLE", "PENDING"]},
                "rule_id": {"enum": list(RULE_FIELDS)}, "reason": {"type": "string", "minLength": 1},
                "reviewer": {"type": "string", "minLength": 1},
                "evidence_source_ids": {"type": "array", "minItems": 1, "uniqueItems": True, "items": {"type": "string", "minLength": 1}},
                "reviewed_at": {"type": "string", "format": "date-time"}},
            "required": ["field_id", "row_id", "status", "rule_id", "reason", "reviewer", "evidence_source_ids", "reviewed_at"]}},
    }
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "urn:wangbin:solar-pv:project:1.0.0",
            "title": "wangbin光伏项目输入契约（不是计算结果）", "type": "object", "additionalProperties": False,
            "properties": properties, "required": [key for key in properties if key != "applicability"], "$defs": definitions}


def validate_shape(data, catalog):
    validator = StrictValidator(catalog.project_schema(), format_checker=format_checker())
    error = next(validator.iter_errors(data), None)
    if error is not None:
        # jsonschema's default text includes actual values. Never expose it.
        raise ContractError("SCHEMA_VALIDATION_FAILED")
