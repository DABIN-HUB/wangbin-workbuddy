"""Explicit AI-origin interpretation is not a verified fact or a seventh source kind."""
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.provenance import make_record
from wangbin_solar_pv.validation import validate_record
CAT=Catalog()
ASSUMPTION={"reason":"SYNTHETIC model interpretation, not an observed fact","method":"SYNTHETIC labelled model inference","maturity_ceiling":"L1","noncritical":True,"decision_invariant":True}


def test_ai_allowed_risk_interpretation_has_explicit_origin_and_stays_assumed():
    r=make_record(CAT,"risk.items.description","SYNTHETIC inferred possible risk",source_kind="ASSUMPTION",provenance_kind="AI",assumption=ASSUMPTION)
    assert not [i for i in validate_record(r,CAT) if i.severity=="ERROR"]
    assert r["status"]=="ASSUMED" and r["source_kind"]=="ASSUMPTION"
    r.update(status="VERIFIED",reviewer="SYNTHETIC",license_status="AUTHORIZED")
    assert any(i.code=="ASSUMPTION_NOT_FACT" for i in validate_record(r,CAT))


def test_critical_physical_input_cannot_accept_ai_origin_even_if_flagged_assumption():
    r=make_record(CAT,"site.total_area",1000,source_kind="ASSUMPTION",provenance_kind="AI",assumption=ASSUMPTION)
    assert any(i.code=="SOURCE_NOT_ALLOWED" for i in validate_record(r,CAT))
