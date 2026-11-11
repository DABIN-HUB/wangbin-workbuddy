"""Bounded structured text; no model-authored tables or Office XML."""
from ..errors import ContractError
from ..schemas import StrictValidator


def result_schema():
    text = {"type": "string", "minLength": 1, "maxLength": 6000}
    texts = {"type": "array", "items": text, "maxItems": 24}
    refs = {"type": "array", "items": {"type": "string", "minLength": 1, "maxLength": 240},
            "uniqueItems": True, "maxItems": 800}
    properties = {"section_id": text, "paragraphs": {**texts, "minItems": 1},
                  "decision_impact": text, "missing_evidence": texts,
                  "review_state": {"const": "PENDING_REVIEW"}}
    for key in ("metric_refs", "formula_refs", "table_refs", "figure_refs", "claim_ids", "fact_refs", "source_refs"):
        properties[key] = refs
    section = {"type": "object", "additionalProperties": False,
               "required": list(properties), "properties": properties}
    top = {"chapter_id": text, "chapter_intro": text,
           "sections": {"type": "array", "items": section, "minItems": 1, "maxItems": 8},
           "chapter_findings": {**texts, "minItems": 1}, "decision_implications": {**texts, "minItems": 1}}
    return {"$schema": "https://json-schema.org/draft/2020-12/schema",
            "type": "object", "additionalProperties": False, "required": list(top), "properties": top}


def validate_schema(output):
    if next(StrictValidator(result_schema()).iter_errors(output), None) is not None:
        raise ContractError("CHAPTER_RESULT_SCHEMA")


def evidence_schema():
    text = {"type": "string", "maxLength": 6000}
    refs = {"type": "array", "items": text, "uniqueItems": True, "maxItems": 4000}
    identity = {"type": "object", "additionalProperties": False,
                "required": ["model_version", "run_id", "input_hash", "source_snapshot_id", "result_hash"],
                "properties": {k: text for k in ("model_version", "run_id", "input_hash", "source_snapshot_id", "result_hash")}}
    fact_properties = {"kind": {"enum": ["input", "metric"]}, "field_id": text, "metric_id": text,
                       "label": text, "value": {"type": ["string", "number", "boolean", "null"]},
                       "display": text, "unit": {"type": ["string", "null"]}, "display_unit": text,
                       "status": text, "reason": {"type": ["string", "null"]}, "source_ids": refs,
                       "source_location": text, "period": {"type": ["string", "object", "null"]},
                       "boundary": {"type": ["string", "object"]}, "formula_id": text}
    fact = {"type": "object", "additionalProperties": False,
            "required": ["kind", "label", "value", "display", "unit", "status", "source_ids", "period", "boundary"],
            "properties": fact_properties}
    section_properties = {key: refs for key in ("fact_refs", "metric_refs", "formula_refs", "table_refs", "figure_refs", "source_refs", "claim_ids", "missing_evidence")}
    section_properties["not_applicable_reason"] = {"type": ["string", "null"]}
    section = {"type": "object", "additionalProperties": False,
               "required": list(section_properties), "properties": section_properties}
    top = {key: text for key in ("schema_version", "report_spec_version", "prompt_version", "spec_hash", "chapter_id", "pv_type", "evidence_hash")}
    top.update({"identity": identity, "maturity": {"type": "object"},
                "sections": {"type": "object", "minProperties": 1, "maxProperties": 8, "additionalProperties": section},
                "facts": {"type": "object", "maxProperties": 4000, "additionalProperties": fact},
                "formulas": {"type": "object"}, "tables": {"type": "object"}, "figures": {"type": "object"},
                "constraints": refs, "authorization_source_ids": refs})
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object",
            "additionalProperties": False, "required": list(top), "properties": top}


def validate_evidence(pack):
    if next(StrictValidator(evidence_schema()).iter_errors(pack), None) is not None:
        raise ContractError("CHAPTER_EVIDENCE_SCHEMA")
