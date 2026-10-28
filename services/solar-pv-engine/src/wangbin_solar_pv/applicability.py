"""Reviewed applicability exceptions, kept separate from the five evidence states."""
from __future__ import annotations

from .errors import Issue
from .units import validate_datetime

RULE_FIELDS = {
    "NO_TAX_INCENTIVE": {"tax.incentive_reference"},
    "NO_POLICY_SUPERSESSION": {"policy.applicability.superseded_by"},
    "NO_REPLACEMENTS_PLANNED": {"assets.replacements"},
    "ROOF_NO_GROUND_STUDY": {"site.geotechnical_reference"},
}


def _entry_key(field_id, row_id):
    return field_id + ("@" + row_id if row_id is not None else "")


def validate_applicability(project, catalog):
    from .validation import iter_records
    from .conditions import known
    records = [r for r, _ in iter_records(project.values, catalog)]
    verified_sources = {r.get("source_id") for r in records if r.get("status") == "VERIFIED" and r.get("license_status") == "AUTHORIZED" and r.get("source_section_or_cell") and r.get("reviewer")}
    issues = []
    for key, entry in project.applicability.items():
        fid, row_id = entry.get("field_id"), entry.get("row_id")
        rule = entry.get("rule_id")
        valid = fid in catalog.fields and key == _entry_key(fid, row_id)
        valid = valid and rule in RULE_FIELDS and fid in RULE_FIELDS.get(rule, set())
        valid = valid and bool(entry.get("reason")) and bool(entry.get("reviewer")) and bool(entry.get("evidence_source_ids"))
        valid = valid and set(entry.get("evidence_source_ids", [])) <= verified_sources
        try:
            validate_datetime(entry.get("reviewed_at"))
        except ValueError:
            valid = False
        if fid in catalog.fields:
            parent = catalog.fields[fid].get("repeat_group")
            if parent:
                container = project.values.get(parent, {}).get("value")
                valid = valid and isinstance(container, list) and any(row.get("row_id") == row_id for row in container)
            else:
                valid = valid and row_id is None
        if entry.get("status") == "NOT_APPLICABLE":
            if rule == "NO_TAX_INCENTIVE":
                valid = valid and project.values.get("tax.regime_reference", {}).get("status") == "VERIFIED"
            elif rule == "ROOF_NO_GROUND_STUDY":
                roof_type = project.pv_type in {"industrial_rooftop", "public_rooftop", "residential_pv"}
                roof_type = roof_type or (project.pv_type == "pv_storage" and known(project, "storage.base_pv_type") in {"industrial_rooftop", "public_rooftop", "residential_pv"})
                valid = valid and roof_type and project.values.get("roof.structure_report_id", {}).get("status") == "VERIFIED"
            elif rule == "NO_REPLACEMENTS_PLANNED":
                valid = valid and known(project, "project.evaluation_years") is not None
                valid = valid and not project.values.get("assets.replacements", {}).get("value")
            elif rule == "NO_POLICY_SUPERSESSION":
                container = project.values.get("policy.applicability", {}).get("value") or []
                row = next((row for row in container if row.get("row_id") == row_id), {})
                existing = row.get("fields", {}).get(fid, {}).get("value")
                valid = valid and existing is None
        if entry.get("status") not in {"APPLICABLE", "NOT_APPLICABLE", "PENDING"}:
            valid = False
        if not valid:
            issues.append(Issue("INVALID_APPLICABILITY", fid if fid in catalog.fields else "", "不适用记录缺规则/证据/复核，或与适用域及现有资料冲突"))
    return issues


def is_not_applicable(project, catalog, field_id, row_id=None):
    entry = project.applicability.get(_entry_key(field_id, row_id))
    if not entry or entry.get("status") != "NOT_APPLICABLE":
        return False
    return not any(i.field_id == field_id for i in validate_applicability(project, catalog))
