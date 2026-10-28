"""A/N: frozen catalog coverage and executable schema, not numerical solar tests."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


def api():
    from wangbin_solar_pv.catalog import Catalog
    from wangbin_solar_pv.models import ProjectData
    return Catalog(), ProjectData


def test_runtime_catalog_has_exact_frozen_469_fields():
    catalog, _ = api()
    frozen = json.loads((catalog.baseline_dir / "03-input-fields.json").read_text(encoding="utf-8"))
    assert set(catalog.fields) == {f["field_id"] for f in frozen["fields"]}
    assert len(catalog.fields) == 469
    assert catalog.fields["schedule.tasks.predecessor_ids"]["type"] == "array"
    assert catalog.fields["schedule.tasks.predecessor_ids"]["constraints"]["minItems"] == 0
    assert "C" in catalog.fields["capex.items.amount"]["provenance_kinds"]


def test_all_fields_metadata_covers_the_fifteen_required_concepts():
    catalog, _ = api()
    keys = {"field_id", "label_zh", "technical_name", "type", "unit", "constraints",
            "required_level", "pv_types", "chapter_ids", "provenance_kinds", "substitutable",
            "evidence_requirements", "validation_status", "formula_bindings", "baseline_reference"}
    for field_id in catalog.fields:
        data = catalog.metadata(field_id)
        assert keys <= data.keys(), field_id
        assert data["technical_name"] == field_id
        assert data["baseline_reference"]["sha256"]
        assert data["validation_status"] == "SCHEMA_SUPPORTED_CALCULATION_NOT_IMPLEMENTED"


def test_schema_202012_includes_all_469_envelopes_and_exact_arrays():
    catalog, _ = api()
    schema = catalog.project_schema()
    Draft202012Validator.check_schema(schema)
    assert set(catalog.fields) <= schema["$defs"].keys()
    assert set(schema["properties"]["values"]["properties"]) == {
        f["field_id"] for f in catalog.fields.values() if not f.get("repeat_group")}
    arr = schema["$defs"]["schedule.tasks.predecessor_ids"]["properties"]["value"]
    assert arr["anyOf"][0]["items"]["properties"]["value"]["type"] == "string"
    for field_id, definition in catalog.fields.items():
        assert schema["$defs"][field_id]["x-field-definition"] == definition


def test_new_project_serializes_without_inventing_input_values():
    catalog, model = api()
    project = model.new("SYNTHETIC-EMPTY", "industrial_rooftop", catalog)
    assert project.values == {}
    loaded = model.from_dict(project.to_dict(), catalog)
    assert loaded.to_dict() == project.to_dict()
    assert loaded.schema_version == "solar-pv-project/1.0.0"


@pytest.mark.parametrize("mutation", ["version", "baseline", "extra", "unknown", "child_at_root"])
def test_project_rejects_unsupported_versions_and_unknown_shape(mutation):
    catalog, model = api()
    data = model.new("SYNTHETIC-INVALID", "industrial_rooftop", catalog).to_dict()
    if mutation == "version":
        data["schema_version"] = "solar-pv-project/999.0.0"
    elif mutation == "baseline":
        data["baseline_hashes"]["03-input-fields.json"] = "0" * 64
    elif mutation == "extra":
        data["surprise"] = True
    elif mutation == "unknown":
        data["values"]["site.invented"] = {}
    else:
        data["values"]["load.series.energy"] = {}
    from wangbin_solar_pv.errors import ContractError
    with pytest.raises(ContractError):
        model.from_dict(data, catalog)


def test_json_roundtrip_preserves_exact_decimal_numbers_and_duplicate_rejection():
    from wangbin_solar_pv.serialization import dumps, loads
    from wangbin_solar_pv.errors import ContractError
    value = {"price": Decimal("12345678901234567890.1234567890123456789"), "ratio": Decimal("0.8")}
    assert loads(dumps(value)) == value
    for bad in ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}']:
        with pytest.raises(ContractError):
            loads(bad)
    for bad in [float("nan"), float("inf"), Decimal("NaN")]:
        with pytest.raises(ContractError):
            dumps({"x": bad})


def test_catalog_rejects_baseline_drift_and_never_mutates_frozen_files(tmp_path):
    import shutil
    catalog, _ = api()
    for name in catalog.baseline_hashes:
        shutil.copy2(catalog.baseline_dir / name, tmp_path / name)
    target = tmp_path / "03-input-fields.json"
    changed = json.loads(target.read_text(encoding="utf-8"))
    changed["fields"].pop()
    target.write_text(json.dumps(changed, ensure_ascii=False), encoding="utf-8")
    from wangbin_solar_pv.catalog import Catalog
    from wangbin_solar_pv.errors import ContractError
    with pytest.raises(ContractError, match="BASELINE_DRIFT"):
        Catalog(tmp_path)
