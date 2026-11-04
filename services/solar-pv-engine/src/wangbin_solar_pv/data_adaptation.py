"""Offline, source-bound Phase 4 ingress; no network or source promotion by default.

This module does not parse arbitrary vendor formats or reproduce Phase 2/D3.
A licensed fixed response is only a candidate until a human reviews it.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timezone
from decimal import Decimal
from hashlib import sha256

from .calculation.common import exact_json_numbers
from .calculation.input_contract import validate_export
from .errors import ContractError
from .intake import IntakeSession
from .provenance import make_record, register_candidate
from .serialization import digest, dumps, loads
from .timeseries_bundle import read_bundle
from .validation import validate_record

MAX_RESPONSE_BYTES = 8 * 1024 * 1024
RESPONSE_VERSION = "solar-pv-adapter-response/1.0.0"
DESCRIPTOR_KEYS = frozenset({"source_id", "source_kind", "mode", "dataset_id", "dataset_version",
    "license_status", "license_reference", "source_reference", "acquired_at", "valid_until",
    "coverage", "required_fields", "economic_basis"})
COVERAGE_KEYS = frozenset({"lat_min", "lat_max", "lon_min", "lon_max", "start", "end",
                           "timezone", "interval_minutes"})


def _instant(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.utcoffset() is None:
            raise ValueError
        return parsed.astimezone(timezone.utc)
    except (AttributeError, ValueError, TypeError) as exc:
        raise ContractError("ADAPTER_TIME_INVALID") from exc


def _descriptor(data, catalog):
    exact_json_numbers(data)
    if (not isinstance(data, dict) or set(data) != DESCRIPTOR_KEYS
            or not all(isinstance(data[k], str) and data[k].strip() for k in (
                "source_id", "source_kind", "mode", "dataset_id", "dataset_version",
                "license_status", "license_reference", "source_reference", "acquired_at", "valid_until"))
            or data["source_kind"] not in {"EXTERNAL_SOURCE", "DOCUMENT_EXTRACTED", "USER_PROVIDED"}
            or data["mode"] not in {"REAL", "SYNTHETIC"}
            or data["license_status"] not in {"AUTHORIZED", "REQUIRES_REVIEW", "DENIED", "UNKNOWN"}
            or not isinstance(data["coverage"], dict) or set(data["coverage"]) != COVERAGE_KEYS
            or not isinstance(data["required_fields"], list)
            or not data["required_fields"]
            or any(not isinstance(fid, str) for fid in data["required_fields"])
            or len(set(data["required_fields"])) != len(data["required_fields"])
            or any(fid not in catalog.fields or catalog.fields[fid].get("repeat_group")
                   or catalog.fields[fid]["type"] == "array" for fid in data["required_fields"])):
        raise ContractError("ADAPTER_DESCRIPTOR_INVALID")
    c = data["coverage"]
    if (any(type(c[key]) not in {int, Decimal} for key in ("lat_min", "lat_max", "lon_min", "lon_max"))
            or not -90 <= c["lat_min"] <= c["lat_max"] <= 90
            or not -180 <= c["lon_min"] <= c["lon_max"] <= 180
            or type(c["interval_minutes"]) is not int or c["interval_minutes"] <= 0
            or not all(isinstance(c[key], str) and c[key] for key in ("start", "end", "timezone"))
            or c["start"] > c["end"] or _instant(data["valid_until"]) < _instant(data["acquired_at"])):
        raise ContractError("ADAPTER_COVERAGE_INVALID")
    try:
        date.fromisoformat(c["start"]); date.fromisoformat(c["end"])
    except ValueError as exc:
        raise ContractError("ADAPTER_COVERAGE_INVALID") from exc
    synthetic_id = data["source_id"].startswith(("SYNTHETIC:", "SYNTHETIC-"))
    if data["mode"] == "SYNTHETIC" and not synthetic_id:
        raise ContractError("ADAPTER_SYNTHETIC_IDENTITY")
    if data["mode"] == "REAL" and synthetic_id:
        raise ContractError("ADAPTER_SYNTHETIC_IDENTITY")
    if data["economic_basis"] is not None and not isinstance(data["economic_basis"], dict):
        raise ContractError("ADAPTER_ECONOMIC_BASIS")
    return deepcopy(data)


def adapt_offline_response(exported, descriptor, raw, catalog, *, as_of):
    """Inspect a fixed JSON response without treating a supplier label as verification.

    ``raw`` is caller-owned private bytes; it is not emitted or uploaded. The
    public response format is deliberately separate from a vendor API response.
    """
    original = validate_export(exported, catalog).export
    source = _descriptor(descriptor, catalog)
    moment = _instant(as_of)
    metadata = {"project_id": original["project"]["project_id"],
                "phase2_input_hash": original["input_hash"],
                "phase2_source_snapshot_id": original["source_snapshot_id"],
                "source_id": source["source_id"], "source_kind": source["source_kind"],
                "mode": source["mode"], "dataset_id": source["dataset_id"],
                "dataset_version": source["dataset_version"],
                "license_status": source["license_status"], "license_reference": source["license_reference"],
                "coverage": source["coverage"], "acquired_at": source["acquired_at"],
                "valid_until": source["valid_until"], "raw_sha256": None,
                "records": [], "missing_fields": [], "conflicting_fields": []}
    if raw is None:
        return {**metadata, "status": "UNAVAILABLE", "reason": "ADAPTER_RESPONSE_ABSENT"}
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_RESPONSE_BYTES:
        raise ContractError("ADAPTER_RESPONSE_LIMIT")
    metadata["raw_sha256"] = sha256(raw).hexdigest()
    if source["license_status"] != "AUTHORIZED":
        return {**metadata, "status": "BLOCKED", "reason": "ADAPTER_LICENSE_NOT_AUTHORIZED"}
    if moment < _instant(source["acquired_at"]):
        return {**metadata, "status": "BLOCKED", "reason": "ADAPTER_NOT_YET_ACQUIRED"}
    if moment > _instant(source["valid_until"]):
        return {**metadata, "status": "BLOCKED", "reason": "ADAPTER_EXPIRED"}
    normalized = original["normalized_inputs"]
    latitude, longitude, site_zone = (normalized.get(fid) for fid in
        ("site.latitude", "site.longitude", "site.timezone"))
    coverage = source["coverage"]
    if (latitude is None or longitude is None or site_zone is None
            or not coverage["lat_min"] <= latitude <= coverage["lat_max"]
            or not coverage["lon_min"] <= longitude <= coverage["lon_max"]
            or site_zone != coverage["timezone"]):
        return {**metadata, "status": "BLOCKED", "reason": "ADAPTER_SITE_COVERAGE"}
    resource_only = all(fid.startswith("resource.") for fid in source["required_fields"])
    if resource_only:
        period_start, period_end = normalized.get("resource.period_start"), normalized.get("resource.period_end")
        if ((period_start and period_start[:10] < coverage["start"])
                or (period_end and period_end[:10] > coverage["end"])):
            return {**metadata, "status": "BLOCKED", "reason": "ADAPTER_TIME_COVERAGE"}
    elif not coverage["start"] <= normalized.get("project.evaluation_date", "") <= coverage["end"]:
        return {**metadata, "status": "BLOCKED", "reason": "ADAPTER_TIME_COVERAGE"}
    payload = loads(raw)
    if (not isinstance(payload, dict) or set(payload) != {"schema_version", "observations"}
            or payload["schema_version"] != RESPONSE_VERSION
            or not isinstance(payload["observations"], list)
            or len(payload["observations"]) > 10000):
        raise ContractError("ADAPTER_RESPONSE_SHAPE")
    seen = {}
    for index, item in enumerate(payload["observations"]):
        if (not isinstance(item, dict) or set(item) != {"field_id", "value", "unit"}
                or item["field_id"] not in source["required_fields"]):
            raise ContractError("ADAPTER_OBSERVATION_SHAPE")
        fid = item["field_id"]
        if fid in seen:
            metadata["conflicting_fields"].append(fid)
            continue
        if item["value"] is None:
            continue
        if (fid.startswith(("tariff.", "capex.", "opex."))
                and source["economic_basis"] is None):
            return {**metadata, "status": "BLOCKED", "reason": "ADAPTER_ECONOMIC_BASIS_REQUIRED"}
        seen[fid] = item
        record = make_record(catalog, fid, item["value"], source_kind=source["source_kind"],
            original_unit=item["unit"], source_id=source["source_id"],
            source_url_or_attachment=source["source_reference"],
            source_section_or_cell=f"/observations/{index}/value", retrieved_at=source["acquired_at"],
            effective_from=coverage["start"], effective_to=coverage["end"],
            measurement_period={"start": coverage["start"], "end": coverage["end"],
                                "timezone": coverage["timezone"],
                                "interval_minutes": coverage["interval_minutes"], "coverage": 1},
            geography=f"{coverage['lat_min']},{coverage['lon_min']}..{coverage['lat_max']},{coverage['lon_max']}",
            license_status=source["license_status"], economic_basis=source["economic_basis"],
            confidence_basis="固定响应未经过人工逐字段核验；仅为待审候选",
            location_status="EXACT")
        if any(issue.severity == "ERROR" for issue in validate_record(record, catalog)):
            raise ContractError("ADAPTER_FIELD_INVALID", fid)
        metadata["records"].append(record)
    metadata["missing_fields"] = sorted(set(source["required_fields"]) - set(seen))
    if metadata["missing_fields"] or metadata["conflicting_fields"]:
        return {**metadata, "records": [], "status": "BLOCKED", "reason": "ADAPTER_MISSING_OR_CONFLICT"}
    metadata["snapshot_hash"] = digest(metadata)
    return {**metadata, "status": "SYNTHETIC_ONLY" if source["mode"] == "SYNTHETIC" else "READY_FOR_REVIEW",
            "reason": "NOT_APPROVED_FOR_CALCULATION"}


def approve_candidates(exported, adaptation, catalog, *, raw, descriptor, reviewer, reviewed_at, evidence_note):
    """Explicit human approval creates new Phase 2 candidates; never auto-picks conflicts."""
    original = validate_export(exported, catalog).export
    if (not isinstance(adaptation, dict) or adaptation.get("status") != "READY_FOR_REVIEW"
            or adaptation.get("mode") != "REAL" or adaptation.get("license_status") != "AUTHORIZED"
            or adaptation.get("phase2_input_hash") != original["input_hash"]
            or adaptation.get("phase2_source_snapshot_id") != original["source_snapshot_id"]
            or not all(isinstance(x, str) and x.strip() for x in (reviewer, evidence_note))
            or not isinstance(adaptation.get("records"), list) or not adaptation["records"]):
        raise ContractError("ADAPTER_APPROVAL_REQUIRED")
    moment = _instant(reviewed_at)
    if moment > _instant(adaptation["valid_until"]) or moment < _instant(adaptation["acquired_at"]):
        raise ContractError("ADAPTER_EXPIRED")
    expected = digest({k: v for k, v in adaptation.items()
                       if k not in {"status", "reason", "snapshot_hash"}})
    if adaptation.get("snapshot_hash") != expected:
        raise ContractError("ADAPTER_SNAPSHOT_CHANGED")
    if (not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_RESPONSE_BYTES
            or sha256(raw).hexdigest() != adaptation.get("raw_sha256")):
        raise ContractError("ADAPTER_RAW_CHANGED")
    source = _descriptor(descriptor, catalog)
    if (source["mode"] != "REAL" or source["license_status"] != "AUTHORIZED"
            or any(source[key] != adaptation[key] for key in (
                "source_id", "source_kind", "dataset_id", "dataset_version",
                "license_status", "license_reference", "coverage", "acquired_at", "valid_until"))):
        raise ContractError("ADAPTER_DESCRIPTOR_CHANGED")
    payload = loads(raw)
    if (not isinstance(payload, dict) or payload.get("schema_version") != RESPONSE_VERSION
            or not isinstance(payload.get("observations"), list)):
        raise ContractError("ADAPTER_RESPONSE_SHAPE")
    observed = payload["observations"]
    project = IntakeSession.from_dict(original["project"], catalog).project
    for unreviewed in adaptation["records"]:
        checked = deepcopy(unreviewed)
        position = checked.get("source_section_or_cell", "")
        try:
            index = int(position.split("/")[2])
            item = observed[index]
        except (ValueError, IndexError, AttributeError, TypeError) as exc:
            raise ContractError("ADAPTER_CANDIDATE_CHANGED") from exc
        if (checked["source_id"] != adaptation["source_id"] or checked["status"] != "UNVERIFIED"
                or checked["license_status"] != "AUTHORIZED"
                or position != f"/observations/{index}/value"
                or checked["source_url_or_attachment"] != source["source_reference"]
                or item.get("field_id") != checked["field_id"]
                or item.get("value") != checked["original_value"]
                or item.get("unit") != checked["original_unit"]):
            raise ContractError("ADAPTER_CANDIDATE_CHANGED")
        checked.update(status="VERIFIED", reviewer=reviewer, last_updated=reviewed_at,
                       confidence_basis=evidence_note)
        if any(issue.severity == "ERROR" for issue in validate_record(checked, catalog)):
            raise ContractError("ADAPTER_CANDIDATE_INVALID")
        register_candidate(project, checked, catalog)
    project.revision += 1
    return validate_export(IntakeSession(project, catalog).export(), catalog).export


def inspect_resource_bundle(exported, descriptor, bundle_dir, catalog, budget, *, as_of):
    """Check an existing validated D3 resource; do not convert raw vendor bytes.

    D3 remains the sole producer of canonical time-series/quality evidence.
    A labelled data set alone cannot override its source, time or base identity.
    """
    original = validate_export(exported, catalog).export
    source = _descriptor(descriptor, catalog)
    if (source["license_status"] != "AUTHORIZED"
            or not _instant(source["acquired_at"]) <= _instant(as_of) <= _instant(source["valid_until"])):
        return {"status": "BLOCKED", "reason": "ADAPTER_LICENSE_OR_EXPIRY"}
    location = original["normalized_inputs"]
    coverage = source["coverage"]
    latitude, longitude = location.get("site.latitude"), location.get("site.longitude")
    if (source["mode"] == "REAL" and (latitude is None or longitude is None
            or location.get("site.timezone") != coverage["timezone"]
            or not coverage["lat_min"] <= latitude <= coverage["lat_max"]
            or not coverage["lon_min"] <= longitude <= coverage["lon_max"])):
        return {"status": "BLOCKED", "reason": "ADAPTER_SITE_COVERAGE"}
    with read_bundle(bundle_dir, catalog=catalog, budget=budget) as bundle:
        if dumps(bundle.base_export) != dumps(original):
            raise ContractError("ADAPTER_D3_BASE_MISMATCH")
        dataset = bundle.manifest["datasets"].get("resource.timeseries")
        if dataset is None:
            return {"status": "UNAVAILABLE", "reason": "ADAPTER_RESOURCE_SERIES_ABSENT"}
        header, meta = dataset["header"], dataset["metadata"]
        if (header.get("source_id") != source["source_id"]
                or header.get("license_status") != "AUTHORIZED"
                or header.get("source_kind") != source["source_kind"]
                or meta["timezone"] != coverage["timezone"]
                or meta["interval_minutes"] != coverage["interval_minutes"]
                or not coverage["start"] <= meta["start"][:10]
                or not meta["end"][:10] <= coverage["end"]
                or "resource.timeseries.poa" not in meta["units"]
                or "resource.timeseries.quality_flag" not in meta["units"]):
            return {"status": "BLOCKED", "reason": "ADAPTER_RESOURCE_IDENTITY_OR_COVERAGE"}
        for row in bundle.rows("resource.timeseries"):
            fields = row["fields"]
            quality = fields.get("resource.timeseries.quality_flag", {})
            required = ("poa", "ambient_temperature", "wind_speed")
            if (quality.get("value") != "valid"
                    or any(fields.get("resource.timeseries." + part, {}).get("value") is None
                           for part in required)):
                return {"status": "BLOCKED", "reason": "ADAPTER_RESOURCE_QUALITY_OR_MISSING"}
        return {"status": "SYNTHETIC_ONLY" if source["mode"] == "SYNTHETIC" else "READY_FOR_REVIEW",
                "project_id": original["project"]["project_id"], "input_hash": original["input_hash"],
                "source_id": source["source_id"], "dataset_id": source["dataset_id"],
                "dataset_version": source["dataset_version"],
                "d3_content_hash": bundle.manifest["content_hash"],
                "rows": dataset["row_count"], "period": meta}
