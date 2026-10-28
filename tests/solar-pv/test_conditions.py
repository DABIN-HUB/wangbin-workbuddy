"""Frozen conditional rules are three-valued; unknown never means waived."""
import pytest
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.models import ProjectData
from synthetic_support import record,row,put_rows

CAT=Catalog()


def project(mode=None,debt=None):
    p=ProjectData.new("SYNTHETIC-CONDITIONS","industrial_rooftop",CAT)
    if mode is not None: p.values["project.sales_mode"]=record(CAT,"project.sales_mode",mode)
    if debt is not None: p.values["finance.debt_ratio"]=record(CAT,"finance.debt_ratio",debt)
    return p


def api():
    from wangbin_solar_pv.conditions import condition_registry,condition_state,effective_requirement
    return condition_registry,condition_state,effective_requirement


def test_all_97_conditional_fields_have_specific_machine_condition_and_baseline_reference():
    registry,_,_=api(); data=registry(CAT)
    expected={fid for fid,f in CAT.fields.items() if "CONDITIONAL" in f["required_level"].values()}
    assert set(data)==expected
    for fid,item in data.items():
        assert item["predicate"] and item["baseline_reference"] and item["rule_id"],fid
        assert item["predicate"]!="always_false",fid


@pytest.mark.parametrize("mode,expected",[("full_export","F"),("self_use_surplus_export","T"),("off_grid","T"),("undecided","U"),(None,"U")])
def test_load_trigger_uses_actual_sales_mode_not_absence_of_curve(mode,expected):
    _,state,_=api()
    assert state("IN-C04",project(mode),CAT)["truth"]==expected


@pytest.mark.parametrize("debt,expected",[(None,"U"),(0,"F"),(0.5,"T"),(1,"T")])
def test_debt_unknown_is_not_zero(debt,expected):
    _,state,_=api();assert state("IN-C06",project("full_export",debt),CAT)["truth"]==expected


def test_explicit_debt_plan_overrides_zero_ratio_and_is_not_waived():
    _,state,require=api();p=project("full_export",0)
    put_rows(p,CAT,"finance.debt_schedule",[row(CAT,"finance.debt_schedule","loan",{"date":"2027-01-01","drawdown":100})])
    assert state("IN-C06",p,CAT)["truth"]=="T"
    assert require("finance.loan_rate","L2",p,CAT)["requirement"]=="REQUIRED"


def test_fixed_and_market_prices_are_alternatives_not_both_waived():
    _,_,require=api();p=project("full_export",0)
    assert require("tariff.periods","L2",p,CAT)["requirement"]=="PENDING_CONDITION"
    for method,table,series in [("fixed","REQUIRED","NOT_APPLICABLE"),("market","NOT_APPLICABLE","REQUIRED")]:
        p.values["tariff.settlement_mode"]=record(CAT,"tariff.settlement_mode",method)
        assert require("tariff.periods","L2",p,CAT)["requirement"]==table
        assert require("tariff.market_series","L2",p,CAT)["requirement"]==series


def test_pure_export_does_not_require_avoidable_price_load_or_debt_agreement():
    _,_,require=api();p=project("full_export",0)
    p.values["tariff.settlement_mode"]=record(CAT,"tariff.settlement_mode","fixed")
    for fid in ["load.series","load.monthly_bills","finance.loan_agreement_id","finance.cfads_definition","tariff.periods.avoidable_price"]:
        assert require(fid,"L2",p,CAT)["requirement"]=="NOT_APPLICABLE",fid
    assert require("tariff.periods.sale_price","L2",p,CAT)["requirement"]=="REQUIRED"


def test_off_grid_sale_price_is_not_manufactured():
    _,_,require=api();p=project("off_grid",0)
    assert require("tariff.periods.sale_price","L2",p,CAT)["requirement"]=="NOT_APPLICABLE"


def test_array_items_inherit_parent_condition_but_empty_roots_do_not_create_rows():
    _,_,require=api();p=project("full_export",0)
    assert require("load.series.energy","L2",p,CAT)["requirement"]=="NOT_APPLICABLE"
    assert require("schedule.tasks.row_id","L1",p,CAT)["requirement"]=="REQUIRED"


def test_unknown_model_method_does_not_silently_select_monthly_or_hourly():
    _,_,require=api();p=project("full_export",0)
    assert require("resource.timeseries","L2",p,CAT)["requirement"]=="PENDING_CONDITION"
    p.values["resource.model_method"]=record(CAT,"resource.model_method","monthly_pr")
    assert require("resource.timeseries","L2",p,CAT)["requirement"]=="NOT_APPLICABLE"
    p.values["resource.model_method"]=record(CAT,"resource.model_method","hourly")
    assert require("resource.timeseries","L2",p,CAT)["requirement"]=="REQUIRED"
