"""Focused offline Phase 4 contracts; no third-party network request."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from openpyxl import load_workbook

from test_phase3f_scenario_runner import _fixture
from wangbin_solar_pv.data_adaptation import RESPONSE_VERSION, adapt_offline_response, approve_candidates
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.intake import IntakeSession
from wangbin_solar_pv.local_files import Workspace
from wangbin_solar_pv.provenance import make_record, register_candidate
from wangbin_solar_pv.serialization import digest, dumps, loads
from wangbin_solar_pv.source_xlsx import SHEETS, create_source_workbook


def _case():
    catalog, export, _ = _fixture()
    project = IntakeSession.from_dict(export["project"], catalog).project
    for fid, value in (("site.latitude", 45), ("site.longitude", 8)):
        record = make_record(catalog, fid, value, source_kind="USER_PROVIDED",
            source_id="SYNTHETIC:site", source_url_or_attachment="SYNTHETIC:site",
            source_section_or_cell=fid, license_status="AUTHORIZED")
        register_candidate(project, record, catalog)
    project.revision += 1
    export = IntakeSession(project, catalog).export()
    now = datetime.now(timezone.utc)
    descriptor = {"source_id": "SYNTHETIC:fixed-weather", "source_kind": "EXTERNAL_SOURCE",
        "mode": "SYNTHETIC", "dataset_id": "SYNTHETIC:offline", "dataset_version": "1",
        "license_status": "AUTHORIZED", "license_reference": "SYNTHETIC:internal-only",
        "source_reference": "SYNTHETIC:fixed-response",
        "acquired_at": (now - timedelta(days=1)).isoformat(),
        "valid_until": (now + timedelta(days=1)).isoformat(),
        "coverage": {"lat_min": 44, "lat_max": 46, "lon_min": 7, "lon_max": 9,
                     "start": "2026-01-01", "end": "2027-12-31", "timezone": "Asia/Shanghai",
                     "interval_minutes": 60},
        "required_fields": ["resource.provider"], "economic_basis": None}
    raw = dumps({"schema_version": RESPONSE_VERSION, "observations": [
        {"field_id": "resource.provider", "unit": None, "value": "SYNTHETIC weather"}]}).encode()
    return catalog, export, descriptor, raw, now.isoformat()


def test_synthetic_response_stays_isolated_from_real_approval():
    catalog, export, descriptor, raw, now = _case()
    original_hash = digest(export)
    adapted = adapt_offline_response(export, descriptor, raw, catalog, as_of=now)
    assert adapted["status"] == "SYNTHETIC_ONLY"
    assert adapted["records"][0]["status"] == "UNVERIFIED"
    assert adapted["records"][0]["source_id"] == descriptor["source_id"]
    assert digest(export) == original_hash
    with pytest.raises(ContractError) as rejected:
        approve_candidates(export, adapted, catalog, raw=raw, descriptor=descriptor,
                           reviewer="human", reviewed_at=now,
                           evidence_note="review required")
    assert rejected.value.code == "ADAPTER_APPROVAL_REQUIRED"


def test_missing_conflicting_expired_and_unlicensed_responses_block():
    catalog, export, descriptor, raw, now = _case()
    missing = dumps({"schema_version": RESPONSE_VERSION, "observations": []}).encode()
    assert adapt_offline_response(export, descriptor, missing, catalog, as_of=now)["reason"] == "ADAPTER_MISSING_OR_CONFLICT"
    repeated = dumps({"schema_version": RESPONSE_VERSION, "observations": [
        {"field_id": "resource.provider", "unit": None, "value": "SYNTHETIC A"},
        {"field_id": "resource.provider", "unit": None, "value": "SYNTHETIC B"}]}).encode()
    assert adapt_offline_response(export, descriptor, repeated, catalog, as_of=now)["records"] == []
    denied = deepcopy(descriptor)
    denied["license_status"] = "DENIED"
    assert adapt_offline_response(export, denied, raw, catalog, as_of=now)["reason"] == "ADAPTER_LICENSE_NOT_AUTHORIZED"
    old = deepcopy(descriptor)
    old["valid_until"] = old["acquired_at"]
    assert adapt_offline_response(export, old, raw, catalog, as_of=now)["reason"] == "ADAPTER_EXPIRED"


def test_rejects_false_real_label_for_synthetic_source():
    catalog, export, descriptor, raw, now = _case()
    descriptor["mode"] = "REAL"
    with pytest.raises(ContractError) as rejected:
        adapt_offline_response(export, descriptor, raw, catalog, as_of=now)
    assert rejected.value.code == "ADAPTER_SYNTHETIC_IDENTITY"


def test_f04_private_draft_has_frozen_sheets_and_canonical_identity(tmp_path):
    catalog, _, _ = _fixture()
    base = Path(__file__).resolve().parents[2] / "reports" / "solar-pv" / "phase3g-synthetic" / "rooftop" / "base"
    result = loads((base / "canonical.json").read_bytes())
    mapping = loads((base / "formula-execution.json").read_bytes())
    receipt = create_source_workbook(result, catalog, Workspace(tmp_path), "source-draft.xlsx", formula_map=mapping)
    assert receipt["status"] == "DRAFT_PARTIAL"
    workbook = load_workbook(tmp_path / "source-draft.xlsx", read_only=True, data_only=False)
    try:
        assert workbook.sheetnames == [name for _, name in SHEETS]
        for sheet in workbook:
            assert sheet[5][1].value == result["input_hash"]
            assert sheet[6][1].value == result["source_snapshot_id"]
            assert sheet[7][1].value == result["result_hash"]
        assert workbook["变量-术语词典"][2][1].value == "变量/术语词典"
        assert workbook["冲突与缺口"].max_row > 9
        assert workbook["输入台账"].max_row > 9
    finally:
        workbook.close()
    with pytest.raises(ContractError) as rejected:
        create_source_workbook(result, catalog, Workspace(tmp_path), "source-draft.xlsx", formula_map=mapping)
    assert rejected.value.code == "OUTPUT_EXISTS"
