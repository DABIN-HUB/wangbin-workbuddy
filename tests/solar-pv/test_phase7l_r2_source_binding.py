"""R2 schedule provenance must bind nested atoms to their own Phase 2 instances."""
from copy import deepcopy
from pathlib import Path

import pytest

from wangbin_solar_pv.report_claims import _source_value
from wangbin_solar_pv.report_export import ReportModel, _resource_rows
from wangbin_solar_pv.serialization import loads

CASES = Path(__file__).resolve().parents[2] / "reports/solar-pv/phase7l-r2-full-cases"


def _case(category):
    canonical = loads((CASES / category / "project/canonical.json").read_bytes())
    return canonical["inputs"]["normalized"], canonical["source_snapshot"]["phase2"]["records"]


def _bound(normalized, records):
    return _source_value(normalized, records, "schedule.tasks")


def _parent(records):
    return next(row for row in records if row["field_id"] == "schedule.tasks")


def _flat(records, instance):
    return next(row for row in records if row.get("field_instance_id") == instance)


@pytest.mark.parametrize("category", ("industrial_rooftop", "utility_scale_ground"))
def test_valid_tasks_and_reordered_rows_bind_by_stable_identity(category):
    normalized, records = _case(category)
    assert len(_bound(normalized, records)) == 5
    normalized["schedule.tasks"].reverse()
    _parent(records)["value"].reverse()
    assert len(_bound(normalized, records)) == 5


@pytest.mark.parametrize("change", ("unknown_source", "other_task", "other_field",
                                    "same_value_other_source", "bad_status", "missing_flat",
                                    "other_project", "wrong_predecessor"))
def test_wrong_child_identity_never_becomes_sourced(change):
    normalized, records = _case("industrial_rooftop")
    parent = _parent(records)
    atom = parent["value"][0]["fields"]["schedule.tasks.name"]
    instance = atom["field_instance_id"]
    flat = _flat(records, instance)
    if change == "unknown_source":
        atom["source_id"] = flat["source_id"] = "unknown-source"
    elif change == "other_task":
        atom["field_instance_id"] = flat["field_instance_id"] = "schedule.tasks:roof-readiness:name"
    elif change == "other_field":
        atom["field_id"] = flat["field_id"] = "schedule.tasks.owner"
    elif change == "same_value_other_source":
        atom["source_url_or_attachment"] = flat["source_url_or_attachment"] = "other-document"
    elif change == "bad_status":
        atom["status"] = flat["status"] = "UNVERIFIED"
    elif change == "missing_flat":
        records.remove(flat)
    elif change == "other_project":
        foreign_normalized, foreign_records = _case("utility_scale_ground")
        foreign = _parent(foreign_records)["value"][0]["fields"]["schedule.tasks.name"]
        atom.update(source_id=foreign["source_id"], source_url_or_attachment=foreign["source_url_or_attachment"])
        flat.update(source_id=foreign["source_id"], source_url_or_attachment=foreign["source_url_or_attachment"])
        assert foreign_normalized["schedule.tasks"][0]["row_id"] != normalized["schedule.tasks"][0]["row_id"]
    else:
        predecessor = parent["value"][1]["fields"]["schedule.tasks.predecessor_ids"]["value"][0]
        _flat(records, predecessor["field_instance_id"])["source_id"] = "unrelated-source"
    assert _bound(normalized, records) is None


def test_duplicate_and_mismatched_parent_records_rejected():
    normalized, records = _case("industrial_rooftop")
    records.append(deepcopy(_parent(records)))
    assert _bound(normalized, records) is None
    records.pop()
    _parent(records)["status"] = "UNVERIFIED"
    assert _bound(normalized, records) is None


def test_ch05_and_app02_resource_values_reject_wrong_row_source_just_as_m04_does():
    result = loads((CASES / "industrial_rooftop" / "project/canonical.json").read_bytes())
    normalized = result["inputs"]["normalized"]
    records = result["source_snapshot"]["phase2"]["records"]
    assert len(_source_value(normalized, records, "resource.monthly")) == 12
    metrics = tuple(result["results"]["metrics"])
    model = ReportModel(result, metrics, {row["metric_id"]: row for row in metrics})
    assert _resource_rows(model)[1][0][1] != "UNKNOWN"
    parent = next(record for record in records if record["field_id"] == "resource.monthly")
    atom = parent["value"][0]["fields"]["resource.monthly.ghi"]
    _flat(records, atom["field_instance_id"])["source_id"] = "another-project"
    atom["source_id"] = "another-project"
    assert _source_value(normalized, records, "resource.monthly") is None
    assert _source_value(normalized, records, "resource.monthly.ghi") is None
    assert _resource_rows(model)[1][0][1] == "UNKNOWN"
