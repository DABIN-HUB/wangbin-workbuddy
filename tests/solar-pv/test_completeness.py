"""G/M: evidence-qualified input levels, never document or platform maturity."""
from copy import deepcopy
from decimal import Decimal
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.models import ProjectData
from synthetic_support import record
from completeness_support import declared_project

CAT=Catalog()


def evaluate(p):
    from wangbin_solar_pv.completeness import evaluate_completeness
    return evaluate_completeness(p,CAT)


def missing(result):
    return {entry["field_id"] for entry in result["missing_required_fields"]}


def test_city_area_budget_are_accepted_as_a_draft_without_fake_coordinates():
    p=ProjectData.new("SYNTHETIC-CITY","industrial_rooftop",CAT)
    p.values={"site.city":record(CAT,"site.city","SYNTHETIC city only"),"site.total_area":record(CAT,"site.total_area",1000),"capex.user_budget":record(CAT,"capex.user_budget",100)}
    old=deepcopy(p.to_dict()); result=evaluate(p)
    assert result["current_level"]=="L1_DRAFT"
    assert not result["can_enter_next_calculation_stage"]
    assert result["missing_required_fields"] and result["next_questions"]
    assert len(result["next_questions"])<=5
    assert old==p.to_dict() and "site.latitude" not in p.values and "system.dc_capacity" not in p.values


def test_declared_l2_without_irrelevant_load_or_debt_is_input_ready_only():
    p=declared_project(CAT,"L2");r=evaluate(p)
    assert r["current_level"]=="L2",r
    assert r["inputs_ready_for_calculation"] and not r["can_execute_calculation"]
    assert r["level_scope"]=="INPUT_EVIDENCE_ONLY"
    assert r["report_maturity"]=="NOT_EVALUATED"
    assert not {"load.series","load.monthly_bills","finance.loan_rate","finance.loan_agreement_id","finance.cfads_definition"}&missing(r)


def test_declared_l3_requires_survey_polygon_and_deeper_evidence_not_attachment_count():
    p=declared_project(CAT,"L3");r=evaluate(p)
    assert r["current_level"]=="L3",r
    assert r["report_maturity"]=="NOT_EVALUATED"
    p.values.pop("site.boundary_vertices")
    assert evaluate(p)["current_level"]=="L2"


def test_same_filled_count_with_unverified_critical_resource_cannot_be_l2():
    p=declared_project(CAT,"L2")
    before=len(p.values);p.values["resource.provider"]["status"]="UNVERIFIED"
    r=evaluate(p)
    assert len(p.values)==before
    assert r["current_level"]=="L1"
    assert "resource.provider" in {x["field_id"] for x in r["unverified_fields"]}
    assert not r["can_enter_next_calculation_stage"]


def test_self_use_annual_energy_does_not_prove_real_profile_or_self_consumption():
    p=declared_project(CAT,"L2")
    p.values["project.sales_mode"]=record(CAT,"project.sales_mode","self_use_surplus_export",status="VERIFIED")
    p.values["load.annual_energy"]=record(CAT,"load.annual_energy",100000,status="VERIFIED")
    r=evaluate(p)
    assert not r["inputs_ready_for_calculation"]
    assert "load.series" in missing(r)
    assert r["self_use_ratio_status"]=="UNKNOWN"
    assert "actual_self_use_ratio" not in r


def test_no_formal_grid_evidence_never_echoes_confirmed_status():
    p=declared_project(CAT,"L2");p.values.pop("grid.opinion_attachment_id")
    r=evaluate(p)
    assert r["grid_connection_status"]=="PENDING_VERIFICATION"
    assert not r["inputs_ready_for_calculation"]
    assert "grid.opinion_attachment_id" in missing(r)


def test_explicit_degradation_assumption_obeys_frozen_l1_ceiling():
    p=declared_project(CAT,"L2")
    p.values["system.annual_degradation"]=record(CAT,"system.annual_degradation",Decimal("0.005"),source_kind="ASSUMPTION",status="ASSUMED",
        assumption={"reason":"SYNTHETIC scenario only","method":"editable declared scenario","lower":0,"upper":Decimal("0.01"),"maturity_ceiling":"L1","noncritical":False,"decision_invariant":False})
    r=evaluate(p)
    assert r["current_level"]=="L1"
    assert any(a["field_id"]=="system.annual_degradation" for a in r["unverified_assumptions"])


def test_conflicting_cost_source_is_not_silently_selected():
    from wangbin_solar_pv.provenance import register_candidate
    p=declared_project(CAT,"L2")
    register_candidate(p,record(CAT,"site.usable_area",7000,status="VERIFIED"),CAT)
    r=evaluate(p)
    assert r["conflicting_fields"] and not r["inputs_ready_for_calculation"]
    assert p.values["site.usable_area"]["value"] is None


def test_power_factor_zero_is_preserved_but_cannot_pass_input_maturity():
    p=declared_project(CAT,"L2");p.values["grid.power_factor"]["value"]=0
    r=evaluate(p)
    assert not r["inputs_ready_for_calculation"]
    assert any(i["code"]=="POWER_FACTOR_NOT_POSITIVE" for i in r["quality_issues"])
    assert p.values["grid.power_factor"]["value"]==0


def test_changed_investment_target_cannot_rewrite_objective_facts():
    p=declared_project(CAT,"L2");before=deepcopy(p.to_dict())
    p.values["targets.payback_years"]=record(CAT,"targets.payback_years",1,status="VERIFIED")
    evaluate(p)
    assert all(v==p.values[k] for k,v in before["values"].items() if k!="targets.payback_years")
    assert "investment_recommendation" not in evaluate(p)
