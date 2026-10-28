"""Explicit value provenance, immutable source candidates and reviewed conflict choice."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from .errors import ContractError
from .serialization import digest

SOURCE_KINDS = {"USER_PROVIDED": "U", "DOCUMENT_EXTRACTED": "D", "EXTERNAL_SOURCE": "D",
                "CALCULATED": "C", "ASSUMPTION": "U", "UNKNOWN": None}


def make_record(catalog, field_id, value, *, source_kind, original_unit=None, field_instance_id=None, currency=None, **metadata):
    if field_id not in catalog.fields:
        raise ContractError("UNKNOWN_FIELD", field_id)
    if source_kind not in SOURCE_KINDS:
        raise ContractError("UNKNOWN_SOURCE_KIND", field_id)
    field = catalog.fields[field_id]
    now = datetime.now(timezone.utc).isoformat()
    unit = field["unit"]
    raw_unit = unit if original_unit is None else original_unit
    normalized = deepcopy(value)
    transformation = []
    normalization = None
    if value is not None and field["type"] in {"number", "integer"} and raw_unit != unit:
        from .units import convert_unit
        conversion_currency = currency or (metadata.get("economic_basis") or {}).get("currency")
        conversion = convert_unit(value, raw_unit, unit, currency=conversion_currency,
                                  decimal_places=metadata.pop("decimal_places", None), rounding=metadata.pop("rounding", None))
        normalized = conversion.value
        if field["type"] == "integer":
            if normalized != normalized.to_integral_value():
                raise ContractError("INTEGER_CONVERSION_NOT_EXACT", field_id)
            normalized = int(normalized)
        transformation.append(conversion.rule_id)
        normalization = {"rule_id": conversion.rule_id, "exact": conversion.exact, "rounding_policy": conversion.rounding_policy, "currency": conversion_currency}
    record = {
        "field_id": field_id, "field_instance_id": field_instance_id or field_id,
        "value": normalized, "unit": unit, "original_value": deepcopy(value), "original_unit": raw_unit,
        "source_kind": source_kind, "provenance_kind": SOURCE_KINDS[source_kind],
        "source_id": None, "source_url_or_attachment": None, "source_section_or_cell": None,
        "measurement_period": None, "published_at": None,
        "retrieved_at": now if source_kind == "USER_PROVIDED" else None,
        "effective_from": None, "effective_to": None, "geography": None,
        "status": "UNKNOWN" if source_kind == "UNKNOWN" else ("ASSUMED" if source_kind == "ASSUMPTION" else "UNVERIFIED"),
        "confidence_basis": "来源未核实；不是模型置信概率", "reviewer": None, "last_updated": now,
        "missing_reason": "未提供的元数据保持未知；不适用须另附依据", "candidate_ids": [],
        "transformation_rule_ids": transformation, "upstream_instance_ids": [],
        "license_status": "REQUIRES_REVIEW", "sensitivity": "CONFIDENTIAL", "location_status": "UNKNOWN",
        "formula_id": None, "formula_version": None, "run_id": None, "assumption": None,
        "economic_basis": None, "normalization": normalization,
    }
    unknown = set(metadata) - set(record)
    if unknown:
        raise ContractError("UNKNOWN_ENVELOPE_PROPERTY", field_id)
    record.update(deepcopy(metadata))
    return record


def _logical_value(value):
    if isinstance(value, list):
        return [_logical_value(item) for item in value]
    if isinstance(value, dict):
        if "field_id" in value and "value" in value:
            return {key: _logical_value(value.get(key)) for key in ("field_id", "value", "unit", "economic_basis")}
        return {key: _logical_value(item) for key, item in value.items()}
    return value


def _incompatible(a, b):
    if digest(_logical_value(a["value"])) != digest(_logical_value(b["value"])) or a["unit"] != b["unit"]:
        return True
    return any(a.get(key) is not None and b.get(key) is not None and a[key] != b[key]
               for key in ("economic_basis", "measurement_period", "effective_from", "effective_to", "geography"))


def register_candidate(project, record, catalog, *, replacement_reason=None):
    from .validation import validate_record
    errors = [i for i in validate_record(record, catalog) if i.severity == "ERROR"]
    if errors:
        raise ContractError(errors[0].code, record.get("field_id"))
    fid = record["field_id"]
    if catalog.fields[fid].get("repeat_group"):
        raise ContractError("ARRAY_ITEM_REQUIRES_PARENT", fid)
    candidate = deepcopy(record)
    candidate_id = "candidate-" + digest(candidate)
    project.candidates.setdefault(candidate_id, candidate)
    current = project.values.get(fid)
    previous_ids = list(current.get("candidate_ids", [])) if current else []
    if current and not previous_ids:
        previous_id = "candidate-" + digest(current)
        project.candidates.setdefault(previous_id, deepcopy(current))
        previous_ids = [previous_id]
    all_ids = list(dict.fromkeys([*previous_ids, candidate_id]))
    if current and current["status"] != "CONFLICT" and candidate["status"] == "UNKNOWN" and current["status"] != "UNKNOWN" and not replacement_reason:
        selected = deepcopy(current)
        selected["candidate_ids"] = all_ids
    elif current and current["status"] != "UNKNOWN" and (current["status"] == "CONFLICT" or _incompatible(current, candidate)) and not replacement_reason:
        selected = deepcopy(current)
        selected.update(value=None, status="CONFLICT", candidate_ids=all_ids,
                        confidence_basis="来源候选冲突，需有证据选择，未自动取平均或取有利值")
    else:
        selected = deepcopy(candidate)
        selected["candidate_ids"] = all_ids
    project.values[fid] = selected
    project.history.append({"field_id": fid, "candidate_id": candidate_id, "previous_candidate_ids": previous_ids,
                            "reason": replacement_reason or "new candidate", "at": candidate["last_updated"]})
    return candidate_id


def resolve_conflict(project, field_id, candidate_id, *, reviewer, reason):
    active = project.values.get(field_id)
    if not active or active["status"] != "CONFLICT" or candidate_id not in active["candidate_ids"]:
        raise ContractError("INVALID_CONFLICT_CHOICE", field_id)
    if not reviewer or not reason:
        raise ContractError("CONFLICT_REVIEW_REQUIRED", field_id)
    choice = deepcopy(project.candidates[candidate_id])
    choice["candidate_ids"] = list(active["candidate_ids"])
    # Choosing a source is not factual verification of that source.
    project.values[field_id] = choice
    project.resolutions.append({"field_id": field_id, "candidate_id": candidate_id, "reviewer": reviewer,
                                "reason": reason, "at": datetime.now(timezone.utc).isoformat()})


def source_snapshot(project, catalog):
    from .validation import iter_records
    records = [deepcopy(r) for r, _ in iter_records(project.values, catalog)]
    candidates = deepcopy(project.candidates)
    attachments=[deepcopy(event) for event in project.history if event.get("event")=="attachment_registered"]
    snapshot = {"baseline_version": project.baseline_version, "records": records, "candidates": candidates,"attachments":attachments,
                "resolutions": deepcopy(project.resolutions)}
    return {"source_snapshot_id": "sources-" + digest(snapshot), **snapshot}
