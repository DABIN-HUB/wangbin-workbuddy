"""One executable input-contract acceptance case for each frozen field ID."""
import pytest
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.provenance import make_record
from wangbin_solar_pv.serialization import dumps,loads
from wangbin_solar_pv.validation import validate_record
CAT=Catalog()

@pytest.mark.parametrize("field_id",sorted(CAT.fields))
def test_input_field_contract(field_id):
    field=CAT.fields[field_id];metadata=CAT.metadata(field_id)
    assert all(metadata[k]==v for k,v in field.items())
    assert metadata["technical_name"]==field_id and metadata["evidence_requirements"]
    assert metadata["baseline_reference"]["sha256"]==CAT.baseline_hashes["03-input-fields.json"]
    unknown=make_record(CAT,field_id,None,source_kind="UNKNOWN",missing_reason="SYNTHETIC absent, never zero")
    assert unknown["value"] is None and unknown["status"]=="UNKNOWN"
    assert not [i for i in validate_record(unknown,CAT) if i.severity=="ERROR"]
    assert loads(dumps(unknown))==unknown
    wrong={"number":True,"integer":True,"string":1,"boolean":1,"array":"SYNTHETIC-not-an-array"}[field["type"]]
    invalid=make_record(CAT,field_id,wrong,source_kind="USER_PROVIDED",source_id="SYNTHETIC")
    assert any(i.code=="FIELD_SCHEMA" for i in validate_record(invalid,CAT))
    if "pattern" in field["constraints"]:
        bad_pattern=make_record(CAT,field_id,"SYNTHETIC invalid / value",source_kind="USER_PROVIDED",source_id="SYNTHETIC")
        assert any(i.code=="FIELD_SCHEMA" for i in validate_record(bad_pattern,CAT))
