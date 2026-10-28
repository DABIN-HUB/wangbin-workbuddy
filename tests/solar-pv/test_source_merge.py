"""Source candidates distinguish absence, compatible evidence, and scope conflicts."""
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.models import ProjectData
from wangbin_solar_pv.provenance import make_record,register_candidate
from wangbin_solar_pv.validation import validate_record
from synthetic_support import record

CAT=Catalog()


def test_unknown_can_be_filled_without_creating_a_conflicting_fact():
    p=ProjectData.new("SYNTHETIC-FILL","industrial_rooftop",CAT)
    register_candidate(p,make_record(CAT,"site.total_area",None,source_kind="UNKNOWN",missing_reason="SYNTHETIC missing"),CAT)
    register_candidate(p,record(CAT,"site.total_area",100),CAT)
    assert p.values["site.total_area"]["status"]=="UNVERIFIED"
    assert p.values["site.total_area"]["value"]==100


def test_equal_amount_in_two_price_years_is_not_silently_overwritten():
    p=ProjectData.new("SYNTHETIC-BASIS-CONFLICT","industrial_rooftop",CAT)
    basis={"currency":"CNY","price_year":2025,"tax_basis":"inclusive","price_basis":"nominal"}
    register_candidate(p,record(CAT,"capex.user_budget",100,economic_basis=basis),CAT)
    register_candidate(p,record(CAT,"capex.user_budget",100,economic_basis={**basis,"price_year":2026}),CAT)
    assert p.values["capex.user_budget"]["status"]=="CONFLICT"


def test_currency_unit_scaling_does_not_invent_price_year_or_tax_status():
    r=make_record(CAT,"capex.user_budget",100,source_kind="USER_PROVIDED",source_id="SYNTHETIC",
        original_unit="万元",currency="CNY",confidence_basis="SYNTHETIC unit and currency explicitly provided")
    assert r["value"]==1000000 and r["economic_basis"] is None
    assert not [i for i in validate_record(r,CAT) if i.severity=="ERROR"]
