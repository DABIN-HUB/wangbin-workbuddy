"""Audit a frozen PV input catalog against one actual Phase 2/D3/3G project.

Read-only inspection: never fills missing fields or upgrades evidence maturity.
Usage: python -m tooling.solar_pv_input_audit INPUT_JSON BUNDLE_MANIFEST CANONICAL_JSON CHECKLIST_JSON OUTPUT_JSON
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from decimal import Decimal
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/solar-pv-engine/src"))

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.calculation.input_contract import validate_export
from wangbin_solar_pv.calculation.result_contract import validate_result
from wangbin_solar_pv.categories import validate_category
from wangbin_solar_pv.conditions import effective_requirement
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.models import ProjectData
from wangbin_solar_pv.serialization import loads
from wangbin_solar_pv.timeseries_bundle import BundleBudget, read_bundle
from wangbin_solar_pv.validation import iter_records, validate_record, validate_project


def _value_summary(record: dict | None) -> str | None:
    if record is None or record.get("value") is None:
        return None
    value = record["value"]
    if isinstance(value, list):
        return f"ARRAY_ROWS:{len(value)}"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float, Decimal)):
        return str(value)
    # Text may contain owner names, attachment locations, and other sensitive data.
    return f"TEXT_PRESENT:{len(str(value))}_CHARS"


def audit(exported: dict, bundle: dict, canonical: dict, checklist: dict, catalog: Catalog,
          *, d3_validated: bool = False) -> dict:
    try:
        validated = validate_export(exported, catalog)
        phase2_status = "VALIDATED_INPUT_EXPORT"
        project = validated.project
    except ContractError as exc:
        if exc.code != "INPUT_EXPORT_INTEGRITY_MISMATCH":
            raise
        project = ProjectData.from_dict(exported["project"], catalog)
        structural_issues = validate_project(project, catalog) + validate_category(project, catalog)
        if any(issue.severity == "ERROR" for issue in structural_issues):
            raise ValueError("AUDIT_PHASE2_SCHEMA_INVALID") from exc
        phase2_status = "STRUCTURE_VALID_BUT_EXPORT_INTEGRITY_MISMATCH"
    result = validate_result(canonical, catalog)
    if (result["pv_type"] != project.pv_type or result["project_id"] != project.project_id
            or result["inputs"]["identity_payload"]["phase2_input_hash"] != exported["input_hash"]):
        raise ValueError("AUDIT_CROSS_RUN_IDENTITY")
    if (checklist.get("project_id") != project.project_id or checklist.get("pv_type") != project.pv_type
            or any(checklist.get("identity", {}).get(key) != result[key]
                   for key in ("run_id", "input_hash", "source_snapshot_id", "result_hash"))):
        raise ValueError("AUDIT_CHECKLIST_CROSS_RUN_IDENTITY")
    if bundle.get("base_export", {}).get("input_hash") not in (None, exported["input_hash"]):
        raise ValueError("AUDIT_D3_IDENTITY")
    records = defaultdict(list)
    issues = defaultdict(list)
    for record, scalar in iter_records(project.values, catalog):
        fid = record["field_id"]
        records[fid].append(record)
        issues[fid].extend(issue.code for issue in validate_record(record, catalog, scalar_item=scalar)
                      if issue.severity == "ERROR")
    reported = defaultdict(list)
    for item in checklist.get("records", []):
        for field in item.get("input_field_ids", []):
            reported[field].append(item["id"])
    used = set(result["inputs"].get("used_fields", []))
    datasets = bundle.get("datasets", {})
    coverage = []
    for fid, definition in catalog.fields.items():
        applicable = project.pv_type in definition["pv_types"]
        parent = definition.get("repeat_group")
        # A repeated child has instances only if its actual parent has rows; an absent
        # parent is not N fabricated missing child instances.
        parent_rows = records.get(parent, ()) if parent else ()
        parent_count = sum(len(row.get("value") or ()) for row in parent_rows) if parent_rows else 0
        reqs = {level: effective_requirement(fid, level, project, catalog)
                for level in ("L1", "L2", "L3")} if applicable else {}
        supplied = [r for r in records.get(fid, ()) if r.get("value") is not None]
        first = supplied[0] if supplied else None
        descriptor = datasets.get(parent or fid) or {}
        bundle_present = bool(descriptor.get("row_count"))
        present = bool(supplied) or bundle_present
        header = descriptor.get("header") or {}
        source_ids = sorted({r.get("source_id") for r in supplied if r.get("source_id")} |
                            ({header["source_id"]} if bundle_present and header.get("source_id") else set()))
        kind = "SYNTHETIC" if project.project_id.startswith("SYNTHETIC") and present else (
            "REAL_UNVERIFIED" if present else "MISSING")
        r = {
            "field_id": fid, "label_zh": definition["label_zh"], "type": definition["type"],
            "unit": definition["unit"], "pv_types": definition["pv_types"],
            "required_level": definition["required_level"], "effective": reqs,
            "applicable": applicable, "present": present,
            "value_summary": _value_summary(first) if supplied else (f"D3_ROWS:{descriptor['row_count']}" if bundle_present else None),
            "instance_count": len(records.get(fid, ())) + (descriptor["row_count"] if bundle_present else 0),
            "populated_instances": len(supplied) + (descriptor["row_count"] if bundle_present else 0), "repeat_parent": parent,
            "repeat_parent_rows": parent_count if parent else None,
            "d3_dataset_rows": descriptor.get("row_count"),
            "source_ids": source_ids, "source_statuses": sorted({r.get("status", "UNKNOWN") for r in supplied} |
                                                     ({header.get("status", "UNKNOWN")} if bundle_present else set())),
            "provenance_kinds": sorted({str(r.get("provenance_kind")) for r in supplied} |
                                       ({str(header.get("provenance_kind"))} if bundle_present else set())),
            "evidence_kind": kind, "schema_valid": (not issues.get(fid)) if supplied else (
                True if d3_validated else None) if bundle_present else None,
            "schema_validation_scope": "PHASE2_RECORD" if supplied else (
                "D3_ALL_ATOMS_VALIDATED" if d3_validated else "D3_MANIFEST_METADATA_ONLY") if bundle_present else "NO_INSTANCE",
            "d3_atom_count": descriptor.get("atom_count"),
            "schema_issues": sorted(set(issues.get(fid, ()))),
            "phase2_present": bool(supplied), "d3_in_bundle": bundle_present,
            "calculation_consumed_reported": fid in used or (parent in used if parent else False),
            "report_binding_ids": sorted(set(reported.get(fid, []) + reported.get(parent, []))) if parent else sorted(set(reported.get(fid, []))),
            "catalog_chapter_ids": definition["chapter_ids"],
            "missing_reason": ("NOT_APPLICABLE_PROJECT_TYPE" if not applicable else
                               "NO_PARENT_ROWS" if parent and not parent_count and not bundle_present else
                               "NO_VALID_INPUT_INSTANCE" if not present else None),
            "blocks_l2": applicable and reqs["L2"]["requirement"] == "REQUIRED" and not present,
        }
        coverage.append(r)
    relevant = [r for r in coverage if r["applicable"]]
    def summary(level: str) -> dict:
        counts = Counter()
        for r in relevant:
            requirement = r["effective"][level]["requirement"]
            counts[requirement] += 1
            if r["present"]:
                counts[requirement + "_PRESENT"] += 1
            elif requirement == "REQUIRED" and (not r["repeat_parent"] or r["repeat_parent_rows"] or r["d3_in_bundle"]):
                counts["REQUIRED_MISSING"] += 1
            if r["repeat_parent"] and not r["repeat_parent_rows"] and not r["d3_in_bundle"]:
                counts["CHILD_WITHOUT_PARENT_ROWS"] += 1
        return dict(sorted(counts.items()))
    metric_statuses = Counter(m["status"] for m in result["results"]["metrics"])
    catalog_l2 = {
        requirement: {
            "definitions": sum(r["required_level"]["L2"] == requirement for r in relevant),
            "provided": sum(r["required_level"]["L2"] == requirement and r["present"] for r in relevant),
            "not_provided": sum(r["required_level"]["L2"] == requirement and not r["present"] for r in relevant),
        }
        for requirement in ("REQUIRED", "CONDITIONAL", "OPTIONAL")
    }
    return {
        "schema_version": "solar-pv-input-coverage/1.0.0",
        "project_id": project.project_id, "pv_type": project.pv_type,
        "identity": {k: result[k] for k in ("run_id", "input_hash", "source_snapshot_id", "result_hash")},
        "phase2_input_hash": exported["input_hash"],
        "catalog_count": len(catalog.fields), "applicable_count": len(relevant),
        "not_applicable_project_type": len(coverage) - len(relevant),
        "phase2_schema": phase2_status, "d3_validation": "ALL_ATOMS_VALIDATED" if d3_validated else "MANIFEST_METADATA_ONLY",
        "catalog_l2": catalog_l2,
        "levels": {level: summary(level) for level in ("L1", "L2", "L3")},
        "source_missing_count": sum(r["present"] and not r["source_ids"] for r in relevant),
        "invalid_field_count": sum(r["schema_valid"] is False for r in relevant),
        "d3_unverified_field_count": sum(r["schema_valid"] is None and r["d3_in_bundle"] for r in relevant),
        "calculation_input_count": sum(r["calculation_consumed_reported"] for r in relevant),
        "report_bound_count": sum(bool(r["report_binding_ids"]) for r in relevant),
        "unconsumed_supplied_fields": [r["field_id"] for r in relevant if r["present"] and
                                       not r["calculation_consumed_reported"] and not r["report_binding_ids"]],
        "calculation_status": result["status"], "metric_status_counts": dict(metric_statuses),
        "real_project_maturity": result["maturity"].get("real_project", "UNKNOWN"),
        "fields": coverage,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("input_json", "bundle_manifest", "canonical_json", "checklist_json", "output_json"):
        parser.add_argument(name, type=Path)
    parser.add_argument("--bundle-dir", type=Path, help="Validate every D3 row, atom and source before marking schema valid")
    args = parser.parse_args()
    paths = (args.input_json, args.bundle_manifest, args.canonical_json, args.checklist_json)
    data = [loads(path.read_bytes()) for path in paths]
    catalog = Catalog()
    if args.bundle_dir:
        with read_bundle(args.bundle_dir, catalog=catalog, budget=BundleBudget()) as verified:
            if verified.manifest != data[1] or verified.base_export != data[0]:
                raise ValueError("AUDIT_D3_CONTENT_IDENTITY")
            output = audit(*data, catalog, d3_validated=True)
    else:
        output = audit(*data, catalog)
    if args.output_json.exists():
        raise FileExistsError(args.output_json)
    args.output_json.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: output[k] for k in ("pv_type", "catalog_count", "applicable_count", "levels",
                                              "invalid_field_count", "source_missing_count", "calculation_status")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
