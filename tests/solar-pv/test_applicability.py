"""Not-applicable is a reviewed applicability record, never a sixth evidence status."""
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.models import ProjectData
from synthetic_support import record,row,put_rows

CAT=Catalog()


def test_safe_nonapplicability_requires_source_review_and_known_rule():
    from wangbin_solar_pv.applicability import is_not_applicable,validate_applicability
    p=ProjectData.new("SYNTHETIC-NA","industrial_rooftop",CAT)
    p.values["tax.regime_reference"]=record(CAT,"tax.regime_reference","SYNTHETIC reviewed tax treatment",status="VERIFIED")
    p.applicability["tax.incentive_reference"]={"field_id":"tax.incentive_reference","row_id":None,
        "status":"NOT_APPLICABLE","rule_id":"NO_TAX_INCENTIVE","reason":"SYNTHETIC no incentive applies",
        "reviewer":"SYNTHETIC-REVIEWER","evidence_source_ids":["SYNTHETIC-LOCAL"],"reviewed_at":"2026-10-28T12:00:00Z"}
    assert is_not_applicable(p,CAT,"tax.incentive_reference")
    assert not validate_applicability(p,CAT)
    restored=ProjectData.from_dict(p.to_dict(),CAT)
    assert restored.applicability==p.applicability
    assert p.values["tax.regime_reference"]["status"]=="VERIFIED"


def test_safety_or_resource_cannot_be_waived_by_arbitrary_not_applicable_claim():
    from wangbin_solar_pv.applicability import validate_applicability
    p=ProjectData.new("SYNTHETIC-BAD-NA","industrial_rooftop",CAT)
    p.applicability["roof.structure_report_id"]={"field_id":"roof.structure_report_id","row_id":None,
        "status":"NOT_APPLICABLE","rule_id":"NO_TAX_INCENTIVE","reason":"SYNTHETIC invalid waiver",
        "reviewer":"SYNTHETIC-REVIEWER","evidence_source_ids":["SYNTHETIC-MISSING"],"reviewed_at":"2026-10-28T12:00:00Z"}
    assert any(i.code=="INVALID_APPLICABILITY" for i in validate_applicability(p,CAT))
