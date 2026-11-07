"""M04 resource values must come from the matching Phase 2 row and atom."""
from __future__ import annotations

from copy import deepcopy

import pytest

from wangbin_solar_pv.report_export import ReportModel, _resource_rows, _sheet_data, _word_number
from wangbin_solar_pv.report_resource_display import prepare_resource_word_rows


_FIELDS = {
    "ghi": ("kWh/m2", (101, 201)),
    "dni": ("kWh/m2", (81, 181)),
    "dhi": ("kWh/m2", (21, 41)),
    "poa": ("kWh/m2", (120, 240)),
    "ambient_temperature": ("degC", (15, 25)),
    "wind_speed": ("m/s", (2, 4)),
    "coverage": ("1", (0.9, 1)),
}
_SOURCE = "synthetic-monthly-fixture"
_DOCUMENT = "documents/monthly-source.md#sha256=fixture"


def _atom(field: str, row_id: str, value, unit=None):
    return {
        "field_id": "resource.monthly." + field,
        "field_instance_id": f"resource.monthly:{row_id}:{field}",
        "value": value,
        "unit": unit,
        "source_id": _SOURCE,
        "source_url_or_attachment": _DOCUMENT,
        "status": "ASSUMED",
        "source_kind": "ASSUMPTION",
        "license_status": "AUTHORIZED",
        "effective_from": None,
        "effective_to": None,
    }


def _model():
    plain = []
    sourced = []
    records = []
    for month in (1, 2):
        row_id = f"m{month:02d}"
        values = {"month": month, "row_id": row_id, **{key: pair[1][month - 1] for key, pair in _FIELDS.items()}}
        atoms = {"resource.monthly." + key: _atom(key, row_id, value, _FIELDS[key][0] if key in _FIELDS else None)
                 for key, value in values.items()}
        records.extend(deepcopy(atom) for atom in atoms.values())
        plain.append({"row_id": row_id, "fields": {key: atom["value"] for key, atom in atoms.items()}})
        sourced.append({"row_id": row_id, "fields": atoms})
    records.insert(0, {
        "field_id": "resource.monthly", "field_instance_id": "resource.monthly",
        "value": sourced, "source_id": _SOURCE, "source_url_or_attachment": _DOCUMENT,
        "status": "ASSUMED", "source_kind": "ASSUMPTION", "license_status": "AUTHORIZED",
        "effective_from": None, "effective_to": None,
    })
    for field, value in (("resource.period_start", "2025-01-01"), ("resource.period_end", "2025-12-31")):
        records.append({"field_id": field, "field_instance_id": field, "value": value,
                        "source_id": _SOURCE, "source_url_or_attachment": _DOCUMENT,
                        "status": "ASSUMED", "source_kind": "ASSUMPTION", "license_status": "AUTHORIZED"})
    for field, value in (("resource.dataset_id", "synthetic-monthly-2025"),
                         ("resource.version", "v1"), ("site.timezone", "Asia/Shanghai")):
        records.append({"field_id": field, "field_instance_id": field, "value": value,
                        "source_id": _SOURCE, "source_url_or_attachment": _DOCUMENT,
                        "status": "ASSUMED", "source_kind": "ASSUMPTION", "license_status": "AUTHORIZED"})
    result = {"evaluation_date": "2026-12-31", "inputs": {"normalized": {
        "resource.monthly": plain, "resource.period_start": "2025-01-01",
        "resource.period_end": "2025-12-31", "resource.dataset_id": "synthetic-monthly-2025",
        "resource.version": "v1", "site.timezone": "Asia/Shanghai"}},
        "source_snapshot": {"phase2": {"records": records}}}
    return ReportModel(result, (), {})


def _rows(model):
    return _sheet_data(model, "M04", "资源月度", "utility_scale_ground")[1]


def _row(model, month):
    return next(row for row in _rows(model) if row[0] == month)


def _record(model, row_id, field):
    return next(record for record in model.result["source_snapshot"]["phase2"]["records"]
                if record.get("field_instance_id") == f"resource.monthly:{row_id}:{field}")


def _source_row(model, row_id):
    parent = model.result["source_snapshot"]["phase2"]["records"][0]
    return next(row for row in parent["value"] if row["row_id"] == row_id)


def test_distinct_months_and_fields_keep_their_own_sourced_values_and_lineage():
    model = _model()
    assert [(row[0], row[1:8]) for row in _rows(model)] == [
        (1, [101, 81, 21, 120, 15, 2, 0.9]),
        (2, [201, 181, 41, 240, 25, 4, 1]),
    ]
    for row_id, month in (("m01", 1), ("m02", 2)):
        note = _row(model, month)[-1]
        assert row_id in note and _SOURCE in note
        assert _DOCUMENT in note
        for field, (unit, _) in _FIELDS.items():
            assert f"resource.monthly.{field}=resource.monthly:{row_id}:{field}(ASSUMED,{unit},{_SOURCE})" in note


def test_reordered_normalized_and_source_rows_still_join_by_row_id_and_month():
    model = _model()
    model.result["inputs"]["normalized"]["resource.monthly"].reverse()
    model.result["source_snapshot"]["phase2"]["records"][0]["value"].reverse()
    model.result["source_snapshot"]["phase2"]["records"][1:] = list(
        reversed(model.result["source_snapshot"]["phase2"]["records"][1:]))
    assert [_row(model, month)[1] for month in (1, 2)] == [101, 201]


@pytest.mark.parametrize("mutation", ("missing_flat", "duplicate_flat", "missing_nested", "duplicate_nested",
                                     "wrong_row", "wrong_month", "wrong_field", "wrong_instance",
                                     "wrong_status", "wrong_unit", "wrong_source", "wrong_document",
                                     "wrong_source_kind",
                                     "unauthorized", "expired", "future"))
def test_bad_ghi_atom_cannot_borrow_another_month_or_variable(mutation):
    model = _model()
    records = model.result["source_snapshot"]["phase2"]["records"]
    flat = _record(model, "m01", "ghi")
    nested = _source_row(model, "m01")["fields"]["resource.monthly.ghi"]
    if mutation == "missing_flat":
        records.remove(flat)
    elif mutation == "duplicate_flat":
        records.append(deepcopy(flat))
    elif mutation == "missing_nested":
        del _source_row(model, "m01")["fields"]["resource.monthly.ghi"]
    elif mutation == "duplicate_nested":
        records[0]["value"].append(deepcopy(_source_row(model, "m01")))
    elif mutation == "wrong_row":
        flat["field_instance_id"] = nested["field_instance_id"] = "resource.monthly:m02:ghi"
    elif mutation == "wrong_month":
        _source_row(model, "m01")["fields"]["resource.monthly.month"]["value"] = 2
    elif mutation == "wrong_field":
        flat["field_id"] = nested["field_id"] = "resource.monthly.dni"
    elif mutation == "wrong_instance":
        nested["field_instance_id"] = "resource.monthly:m02:ghi"
    elif mutation == "wrong_status":
        flat["status"] = nested["status"] = "UNVERIFIED"
    elif mutation == "wrong_unit":
        flat["unit"] = nested["unit"] = "W/m2"
    elif mutation == "wrong_source":
        flat["source_id"] = nested["source_id"] = "unrelated-source"
    elif mutation == "wrong_document":
        flat["source_url_or_attachment"] = nested["source_url_or_attachment"] = "other-document"
    elif mutation == "wrong_source_kind":
        flat["source_kind"] = nested["source_kind"] = "EXTERNAL_SOURCE"
    elif mutation == "unauthorized":
        flat["license_status"] = nested["license_status"] = "DENIED"
    elif mutation == "expired":
        flat["effective_to"] = nested["effective_to"] = "2026-12-30"
    else:
        flat["effective_from"] = nested["effective_from"] = "2027-01-01"
    assert _row(model, 1)[1] == "UNKNOWN"
    if mutation not in {"duplicate_nested", "wrong_month"}:
        assert _row(model, 1)[2] == 81  # atom failures need not erase siblings
    if mutation not in {"wrong_row", "wrong_instance"}:
        assert _row(model, 2)[1] == 201  # duplicate instance invalidates both users


def test_duplicate_month_and_row_id_do_not_select_first_matching_row():
    model = _model()
    normalized = model.result["inputs"]["normalized"]["resource.monthly"]
    normalized[1]["fields"]["resource.monthly.month"] = 1
    assert all(row[1] == "UNKNOWN" for row in _rows(model) if row[0] == 1)
    model = _model()
    model.result["inputs"]["normalized"]["resource.monthly"].append(
        deepcopy(model.result["inputs"]["normalized"]["resource.monthly"][0]))
    assert all(row[1] == "UNKNOWN" for row in _rows(model) if row[0] == 1)


@pytest.mark.parametrize("start,end", (("2025-01-02", "2025-02-28"),
                                            ("2025-01-01", "2025-01-30")))
def test_partial_calendar_month_does_not_pass_as_full_month(start, end):
    model = _model()
    model.result["inputs"]["normalized"].update({"resource.period_start": start, "resource.period_end": end})
    records = model.result["source_snapshot"]["phase2"]["records"]
    for record in records:
        if record.get("field_id") == "resource.period_start":
            record["value"] = start
        elif record.get("field_id") == "resource.period_end":
            record["value"] = end
    assert _row(model, 1)[1:8] == ["UNKNOWN"] * 7
    assert _row(model, 2)[1] == "UNKNOWN"


def test_absent_or_mismatched_period_and_parent_source_fail_closed():
    model = _model()
    _record(model, "m01", "ghi")["source_id"] = "unrelated-source"
    assert _row(model, 1)[1] == "UNKNOWN"
    model = _model()
    model.result["source_snapshot"]["phase2"]["records"] = [record for record in
        model.result["source_snapshot"]["phase2"]["records"] if record.get("field_id") != "resource.period_end"]
    assert all(row[1:8] == ["UNKNOWN"] * 7 for row in _rows(model))


def test_parent_source_identity_must_match_each_child():
    model = _model()
    model.result["source_snapshot"]["phase2"]["records"][0]["source_url_or_attachment"] = "other-document"
    assert all(row[1:8] == ["UNKNOWN"] * 7 for row in _rows(model))


def test_dataset_timezone_and_complete_local_year_are_required_for_months():
    for field, value in (("resource.dataset_id", "another-dataset"),
                         ("site.timezone", "America/New_York"),
                         ("resource.period_end", "2026-01-01")):
        model = _model()
        model.result["inputs"]["normalized"][field] = value
        assert all(row[1:8] == ["UNKNOWN"] * 7 for row in _rows(model))


def test_valid_local_month_boundaries_are_stated_in_source_note():
    model = _model()
    assert "Asia/Shanghai" in _row(model, 1)[-1]
    assert "2025-01-01—2025-01-31" in _row(model, 1)[-1]
    assert "2025-02-01—2025-02-28" in _row(model, 2)[-1]


def _display(model):
    return prepare_resource_word_rows(model.result, _resource_rows(model)[1], _word_number)


def test_word_reference_resolves_each_field_atom_without_squashing_months_or_projects():
    model = _model()
    model.result.update(project_id="roof-a", source_snapshot_id="snapshot-1")
    intro, irradiance, weather, mapping = _display(model)
    assert len(mapping) == 14
    assert "synthetic-monthly-2025" in intro and _DOCUMENT in intro
    assert len({row[-1] for row in irradiance}) == 2
    assert [row[-1] for row in irradiance] == [row[-1] for row in weather]
    assert weather[0][3] == "90%" and weather[1][3] == "100%"
    for month, row in enumerate(irradiance, 1):
        for field in _FIELDS:
            atom = _record(model, f"m{month:02d}", field)
            binding = mapping[f"{row[-1]}/{field}"]
            assert (binding["month"], binding["row_id"], binding["field_instance_id"],
                    binding["source_id"], binding["unit"], binding["value"]) == (
                        month, f"m{month:02d}", atom["field_instance_id"], atom["source_id"],
                        atom["unit"], atom["value"])
    other = _model()
    other.result.update(project_id="ground-b", source_snapshot_id="snapshot-1")
    assert set(_display(other)[3]).isdisjoint(mapping)


def test_word_reference_follows_reordered_rows_and_never_masks_wrong_source():
    model = _model()
    model.result.update(project_id="roof-a", source_snapshot_id="snapshot-1")
    model.result["inputs"]["normalized"]["resource.monthly"].reverse()
    _, irradiance, _, mapping = _display(model)
    assert [row[0] for row in irradiance] == [1, 2]
    assert len(mapping) == 14
    _record(model, "m01", "ghi")["source_id"] = "unrelated-source"
    _, irradiance, _, mapping = _display(model)
    assert irradiance[0][1] == "UNKNOWN"
    assert f"{irradiance[0][-1]}/ghi" not in mapping
    assert f"{irradiance[0][-1]}/dni" in mapping


def test_word_reference_does_not_invent_identity_when_month_row_is_duplicated():
    model = _model()
    model.result.update(project_id="roof-a", source_snapshot_id="snapshot-1")
    parent = model.result["source_snapshot"]["phase2"]["records"][0]
    parent["value"].append(deepcopy(parent["value"][0]))
    _, irradiance, _, mapping = _display(model)
    assert irradiance[0][-1] == "UNKNOWN"
    assert not any(value["month"] == 1 for value in mapping.values())
    assert irradiance[1][-1] != "UNKNOWN"
