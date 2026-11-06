"""R2 Phase 2 input-only regression: no real approval and no reuse of R1 identity."""
from datetime import date
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest

from tooling.solar_pv_phase7l_r2_inputs import prepare
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.calculation.input_contract import validate_export
from wangbin_solar_pv.models import ProjectData
from wangbin_solar_pv.serialization import loads
from wangbin_solar_pv.validation import validate_project

R1 = Path(__file__).resolve().parents[2] / "reports/solar-pv/phase7l-r1-full-cases"


@pytest.mark.parametrize("category", ("industrial_rooftop", "utility_scale_ground"))
def test_r2_planning_rows_have_atomic_sources_and_valid_dependency_graph(tmp_path, category):
    dest = tmp_path / category
    prepared = prepare(category, dest)
    exported = loads((dest / "input.json").read_bytes())
    catalog = Catalog()
    validate_export(exported, catalog)
    project = ProjectData.from_dict(exported["project"], catalog)
    assert not [i.code for i in validate_project(project, catalog) if i.severity == "ERROR"]
    source = (dest / "documents/source-material.md").read_bytes()
    digest = sha256(source).hexdigest()
    assert digest == prepared["source_sha256"]
    assert prepared["phase2_input_hash"] == exported["input_hash"]
    assert exported["input_hash"] != loads((R1 / category / "input.json").read_bytes())["input_hash"]
    assert exported["project"]["project_id"] != loads((R1 / category / "input.json").read_bytes())["project"]["project_id"]
    assert b"not an approval" in source and b"planning assumption" in source.lower()
    assert b"milestone" in source.lower()
    normalized = exported["normalized_inputs"]
    rows = normalized["schedule.tasks"]
    assert len(rows) >= 4
    tasks = {r["fields"]["schedule.tasks.task_id"]: r for r in rows}
    assert len(tasks) == len(rows)
    assert all(r["fields"]["schedule.tasks.name"] for r in rows)
    assert all(r["fields"]["schedule.tasks.critical_path"] is True for r in rows)
    assert any(r["fields"]["schedule.tasks.predecessor_ids"] for r in rows)
    assert any("milestone" in r["fields"]["schedule.tasks.name"].lower() for r in rows)
    assert all(date.fromisoformat(r["fields"]["schedule.tasks.finish_date"]) >=
               date.fromisoformat(r["fields"]["schedule.tasks.start_date"]) for r in rows)
    raw = exported["project"]["values"]["schedule.tasks"]
    assert raw["status"] == "ASSUMED"
    assert raw["source_url_or_attachment"].endswith(digest)
    for row in raw["value"]:
        for child in row["fields"].values():
            assert child["status"] == "ASSUMED"
            assert child["source_url_or_attachment"].endswith(digest)
            if child["field_id"] == "schedule.tasks.predecessor_ids":
                for predecessor in child["value"]:
                    assert predecessor["status"] == "ASSUMED"
                    assert predecessor["source_url_or_attachment"].endswith(digest)
    if category == "utility_scale_ground":
        assert "tariff.non_avoidable_charges" not in normalized
    if category == "industrial_rooftop":
        pf = exported["project"]["values"]["grid.power_factor"]
        assert pf["value"] == Decimal("0.95")
        assert pf["status"] == "ASSUMED" and pf["source_url_or_attachment"].endswith(digest)
        assert b"0.95" in source and b"power factor" in source.lower()
    manifest = loads((dest / "bundle/manifest.json").read_bytes())
    assert loads((dest / "bundle/base.json").read_bytes())["input_hash"] == exported["input_hash"]
    assert all(row["row_count"] == 8760 for row in manifest["datasets"].values())
    assert all(row["header"]["source_url_or_attachment"].endswith(digest)
               for row in manifest["datasets"].values())
    assert prepared["d3_content_hash"] == manifest["content_hash"]


def test_r2_does_not_overwrite_preexisting_case(tmp_path):
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(ValueError, match="fresh directory"):
        prepare("industrial_rooftop", existing)
