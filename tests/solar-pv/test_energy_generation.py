"""Independent Phase3B physical/yearly references; no production-generated expected values."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
from math import exp

import pytest

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.calculation.energy_inputs import EnergyInputs
from wangbin_solar_pv.calculation.capacity import capacity, validate_rooftop, validate_ground
from wangbin_solar_pv.calculation.degradation import performance_schedule
from wangbin_solar_pv.calculation.temperature import prepare_temperature
from wangbin_solar_pv.calculation.energy_yield import _power, _losses, calculate_rooftop, calculate_ground
from wangbin_solar_pv.calculation.method_config import MethodConfig, make_parameter
from wangbin_solar_pv.calculation.result_contract import serialize_result, deserialize_result
from wangbin_solar_pv.calculation.solar_resource import ResourceInterval
from wangbin_solar_pv.timeseries_bundle import BundleBudget
from energy_case_support import case, atom, independent_reference


@pytest.fixture(scope="module")
def catalog():
    return Catalog()


def change(session, fid, value):
    session.project.values[fid]["value"] = value
    session.project.values[fid]["original_value"] = value


def control(methods, **values):
    data = methods.to_dict()
    for pid, value in values.items():
        data["parameters"][pid] = make_parameter(pid, value, source_id="SYNTHETIC-rule",
            source_reference="SYNTHETIC:independent scenario", status="ASSUMED", source_kind="SYNTHETIC", license_status="AUTHORIZED")
    return MethodConfig.from_dict(data)


def prepared(catalog, category="industrial_rooftop", **controls):
    s, m = case(catalog, category)
    m = control(m, **controls)
    inputs = EnergyInputs(s.export(), m, catalog)
    design = capacity(inputs)
    schedule = performance_schedule(inputs, [365]*3)
    temp = prepare_temperature(m)
    constants = (D(1), D(25), D("-0.004"), D("0.2"), D("0.99"),
                 D(90) if category == "utility_scale_ground" else None,
                 D(60) if category == "utility_scale_ground" else None)
    start = datetime(2025,1,1,tzinfo=timezone.utc)
    item = ResourceInterval("one", start, start+timedelta(hours=1), D(1), D(1), D(25), D(1), ("SYNTHETIC",), ("SYNTHETIC-generation",))
    return inputs, design, schedule, temp, constants, item


@pytest.mark.parametrize("category", ["industrial_rooftop", "utility_scale_ground"])
def test_each_year_reclips_and_matches_independent_fraction_reference(catalog, category):
    inputs, design, schedule, temp, constants, item = prepared(catalog, category)
    with localcontext() as c:
        c.prec = 60
        actual = [_power(item, design, temp, inputs, _losses(inputs), y, constants)["output_kw"]*4380 for y in schedule]
        reference = independent_reference(category=category)
        assert all(abs(a-b) < D("0.000000001") for a,b in zip(actual,reference))
        assert actual[1] != actual[0]*D("0.9")


def test_unequal_dc_groups_clip_before_sum_not_after_aggregation(catalog):
    args = prepared(catalog, **{"energy.dc_allocation": [D("0.7"), D("0.3")]})
    inputs, design, schedule, temp, constants, item = args
    with localcontext() as c:
        c.prec = 60
        out = _power(item, design, temp, inputs, _losses(inputs), schedule[0], constants)
        assert abs(out["output_kw"]*4380-independent_reference(allocations=(F(7,10),F(3,10)))[0]) < D("0.000000001")
        assert out["inverter_ac_kw"] < min(D(80), out["dc_kw"]*D("0.98"))


def test_night_and_loss_energy_conservation_allow_cold_temperature_gain(catalog):
    inputs, design, schedule, temp, constants, item = prepared(catalog)
    with localcontext() as c:
        c.prec = 60
        out = _power(item, design, temp, inputs, _losses(inputs), schedule[0], constants)
        assert abs(out["ideal_kw"]-out["output_kw"]-sum(out["losses_kw"].values())) < D("1E-50")
        cold = ResourceInterval("cold",item.start,item.end,D(1),D("0.5"),D(-20),D(1),(),())
        assert _power(cold,design,temp,inputs,_losses(inputs),schedule[0],constants)["losses_kw"]["temperature"] < 0
        night = ResourceInterval("night",item.start,item.end,D(1),D(0),D(25),D(1),(),())
        assert _power(night,design,temp,inputs,_losses(inputs),schedule[0],constants)["output_kw"] == 0


def test_annual_initial_retention_is_applied_exactly_once(catalog):
    s,m = case(catalog)
    actual = performance_schedule(EnergyInputs(s.export(),m,catalog),[365]*3)
    assert [r["retention"] for r in actual] == [D("0.98"),D("0.882"),D("0.7938")]
    m = control(m, **{"energy.pr_includes_initial_degradation": True})
    with pytest.raises(ContractError, match="ENERGY_INITIAL_DEGRADATION_DUPLICATED"):
        performance_schedule(EnergyInputs(s.export(),m,catalog),[365]*3)


def replacement_case(catalog, scope="MODULES_UNIFORM_FRACTION", target=D("0.99")):
    s,m=case(catalog)
    values={"asset_id":"SYNTHETIC-modules", "year":2,"downtime_days":D(10),
            "performance_reset":"EXPLICIT_METHOD_RULE","row_id":"replace-2"}
    row={"row_id":"replace-2","fields":{"assets.replacements."+k:atom(catalog,"assets.replacements."+k,v,"event-"+k) for k,v in values.items()}}
    change(s,"assets.replacements",[row])
    m=control(m, **{"replacement.method":"EXPLICIT_ASSET_EVENTS", "degradation.performance_ceiling":D(1),
        "replacement.rules":[{"event_id":"replace-2","scope":scope,"capacity_fraction":D("0.5"),
            "target_retention":target,"timing":"YEAR_START_RECOVERY_UNIFORM_EQUIVALENT_DOWNTIME",
            **({"inverter_ids":["inv-1"]} if scope=="INVERTERS_UNIFORM_FRACTION" else {})}]})
    return s,m


def test_replacement_explicit_target_fraction_and_downtime_not_ceiling_default(catalog):
    s,m=replacement_case(catalog)
    y=performance_schedule(EnergyInputs(s.export(),m,catalog),[365]*3)
    assert y[1]["retention"] == D("0.936")  # .882 + .5*(.99-.882)
    assert y[2]["retention"] == D("0.8424")
    with localcontext() as c:
        c.prec=60
        assert y[1]["equivalent_availability"] == 1-D(5)/365
    data=m.to_dict();del data["parameters"]["replacement.rules"]
    with pytest.raises(ContractError,match="BLOCKED_METHOD_REVIEW"):
        performance_schedule(EnergyInputs(s.export(),MethodConfig.from_dict(data),catalog),[365]*3)


def test_inverter_replacement_downtime_does_not_restore_dc_performance(catalog):
    s,m=replacement_case(catalog,"INVERTERS_UNIFORM_FRACTION",None)
    y=performance_schedule(EnergyInputs(s.export(),m,catalog),[365]*3)
    assert y[1]["retention"]==D("0.882")
    s,m=replacement_case(catalog,"INVERTERS_UNIFORM_FRACTION",D(1))
    with pytest.raises(ContractError,match="ENERGY_INVERTER_RECOVERY_NOT_DC"):
        performance_schedule(EnergyInputs(s.export(),m,catalog),[365]*3)


def test_piecewise_rates_have_full_nonoverlapping_coverage(catalog):
    s,m=case(catalog)
    rows=[]
    for i,(a,b,r) in enumerate([(1,2,D("0.1")),(3,3,D("0.2"))]):
        values={"from_year":a,"to_year":b,"rate":r,"reset_on_replacement":"EXPLICIT_METHOD_RULE","row_id":f"seg{i}"}
        rows.append({"row_id":f"seg{i}","fields":{"system.degradation_segments."+k:atom(catalog,"system.degradation_segments."+k,v,f"seg{i}-{k}") for k,v in values.items()}})
    s.project.values["system.degradation_segments"]=atom(catalog,"system.degradation_segments",rows)
    m=control(m, **{"degradation.method":"PIECEWISE"})
    assert [y["retention"] for y in performance_schedule(EnergyInputs(s.export(),m,catalog),[365]*3)]==[D(".98"),D(".882"),D(".7056")]
    change(s,"system.degradation_segments",rows[:1])
    with pytest.raises(ContractError,match="ENERGY_DEGRADATION_GAP"):
        performance_schedule(EnergyInputs(s.export(),m,catalog),[365]*3)


@pytest.mark.parametrize("fid,value,code", [
    ("system.modules_per_string",19,"ENERGY_STRING_COUNT"),
    ("system.inverter_max_dc_voltage",900,"ENERGY_ELECTRICAL_CONFIGURATION"),
    ("site.usable_area",950,"ENERGY_AREA_INCONSISTENT"),
    ("layout.ground_coverage_ratio",D(".1"),"ENERGY_LAYOUT_AREA"),
    ("roof.remaining_life",1,"ENERGY_ROOF_LIFE"),
    ("roof.design_added_load",D(".3"),"ENERGY_ROOF_LOAD")])
def test_engineering_boundary_failures_do_not_become_zero(catalog,fid,value,code):
    s,m=case(catalog);change(s,fid,value)
    with pytest.raises(ContractError,match=code):
        i=EnergyInputs(s.export(),m,catalog);validate_rooftop(i);capacity(i)


def test_ground_rules_never_read_roof_fields_and_wrong_entry_rejects(catalog):
    s,m=case(catalog,"utility_scale_ground")
    i=EnergyInputs(s.export(),m,catalog);validate_ground(i);capacity(i)
    assert not any(fid.startswith("roof.") for fid in i.used)
    with pytest.raises(ContractError,match="ENERGY_CATEGORY_MISMATCH"):
        validate_rooftop(i)


def monthly_case(catalog,category="industrial_rooftop"):
    s,m=case(catalog,category)
    s.project.values["grid.metering_boundary"]=atom(catalog,"grid.metering_boundary","SYSTEM_AVAILABLE_AFTER_AUXILIARY_AVAILABILITY_PRE_CURTAILMENT")
    s.project.values["resource.poa_boundary"]=atom(catalog,"resource.poa_boundary","ARRAY_PLANE_MONTHLY_CUMULATIVE")
    for fid,value in (("resource.period_start","2025-01-01"),("resource.period_end","2025-12-31")):
        s.project.values[fid]=atom(catalog,fid,value)
    import calendar
    rows=[]
    for month in range(1,13):
        values={"month":month,"days":calendar.monthrange(2025,month)[1],"coverage":1,"poa":100,"row_id":f"m{month}"}
        rows.append({"row_id":f"m{month}","fields":{"resource.monthly."+k:atom(catalog,"resource.monthly."+k,v,f"m{month}-{k}") for k,v in values.items()}})
    s.project.values["resource.monthly"]=atom(catalog,"resource.monthly",rows)
    upstream=[]
    for row in s.project.values["system.losses"]["value"]:
        if row["row_id"] != "curtailment":
            rec=row["fields"]["system.losses.included_in_source"];rec["value"]=rec["original_value"]=True
            upstream.append(row["row_id"])
    s.project.values["system.losses"]["original_value"]=deepcopy(s.project.values["system.losses"]["value"])
    m=control(m, **{"energy.method":"POA_PR","thermal.method":"NOT_REQUIRED_PR","energy.pr":D(".8"),"energy.upstream_included_losses":upstream})
    return s,m


def test_monthly_pr_real_api_canonical_roundtrip_and_reproducibility(catalog,tmp_path):
    from wangbin_solar_pv.serialization import dumps,loads
    s,m=monthly_case(catalog)
    a=calculate_rooftop(s.export(),m,catalog=catalog,output_dir=tmp_path/"one",budget=BundleBudget())
    b=calculate_rooftop(loads(dumps(s.export())),MethodConfig.from_dict(loads(dumps(m.to_dict()))),catalog=catalog,output_dir=tmp_path/"two",budget=BundleBudget())
    metrics={v["metric_id"]:v for v in a["results"]["metrics"]}
    assert metrics["energy.annual_array"]["value"]==[D(94080),D(84672),D("76204.8")]
    assert a["result_hash"]==b["result_hash"] and a["run_id"]!=b["run_id"]
    assert deserialize_result(serialize_result(a,catalog),catalog)==a
    assert metrics["revenue"]["value"] is None and metrics["revenue"]["status"]=="NOT_IMPLEMENTED"
    assert (tmp_path/"one/result.json").is_file()


def test_output_not_overwritten_and_failed_calculation_leaves_no_complete_result(catalog,tmp_path):
    s,m=monthly_case(catalog)
    (tmp_path/"existing").mkdir();(tmp_path/"existing/owned.txt").write_text("unchanged")
    with pytest.raises(ContractError,match="ENERGY_OUTPUT_EXISTS"):
        calculate_rooftop(s.export(),m,catalog=catalog,output_dir=tmp_path/"existing",budget=BundleBudget())
    assert (tmp_path/"existing/owned.txt").read_text()=="unchanged"
    data=m.to_dict();del data["parameters"]["energy.pr"]
    with pytest.raises(ContractError,match="BLOCKED_METHOD_REVIEW"):
        calculate_rooftop(s.export(),MethodConfig.from_dict(data),catalog=catalog,output_dir=tmp_path/"failed",budget=BundleBudget())
    assert not (tmp_path/"failed").exists()


@pytest.mark.parametrize("category", ["agri_pv","fishery_pv","pv_storage","public_rooftop","residential_pv","pv_carport_bipv","desert_mining"])
def test_other_seven_categories_do_not_enter_generation(catalog,category):
    from wangbin_solar_pv.intake import IntakeSession
    s=IntakeSession.new("SYNTHETIC-isolation",category,catalog)
    _,m=case(catalog)
    with pytest.raises(ContractError):
        EnergyInputs(s.export(),m,catalog)


@pytest.mark.parametrize("kind,value", [("max_rows",1),("max_input_bytes",1),("max_disk_bytes",1)])
def test_budget_limits_fail_closed_without_output(catalog,tmp_path,kind,value):
    s,m=monthly_case(catalog)
    with pytest.raises(ContractError,match="BUNDLE_(ROW|INPUT|DISK)_LIMIT"):
        calculate_rooftop(s.export(),m,catalog=catalog,output_dir=tmp_path/"limited",budget=BundleBudget(**{kind:value}))
    assert not (tmp_path/"limited/result.json").exists()


def test_interrupt_during_evidence_output_cleans_only_new_directory(catalog,tmp_path,monkeypatch):
    from wangbin_solar_pv.calculation.energy_yield import _EvidenceWriter
    s,m=monthly_case(catalog)
    def interrupt(self,row):
        raise KeyboardInterrupt("SYNTHETIC controlled interruption")
    monkeypatch.setattr(_EvidenceWriter,"add",interrupt)
    with pytest.raises(KeyboardInterrupt):
        calculate_rooftop(s.export(),m,catalog=catalog,output_dir=tmp_path/"interrupted",budget=BundleBudget())
    assert not (tmp_path/"interrupted").exists()


def test_method_change_reexecutes_but_preserves_phase2_identity(catalog,tmp_path):
    s,m=monthly_case(catalog)
    a=calculate_rooftop(s.export(),m,catalog=catalog,output_dir=tmp_path/"old",budget=BundleBudget())
    b=calculate_rooftop(s.export(),control(m,**{"energy.pr":D(".7")}),catalog=catalog,output_dir=tmp_path/"new",budget=BundleBudget())
    assert a["input_hash"]!=b["input_hash"] and a["result_hash"]!=b["result_hash"]
    assert a["source_snapshot"]["phase2"]==b["source_snapshot"]["phase2"]
    assert a["results"]["metrics"]!=b["results"]["metrics"]


def test_missing_auxiliary_invalid_source_and_unreviewed_method_block(catalog):
    s,m=case(catalog)
    data=m.to_dict();del data["parameters"]["energy.auxiliary_kw"]
    with pytest.raises(ContractError,match="BLOCKED_METHOD_REVIEW"):
        MethodConfig.from_dict(data).require("energy.auxiliary_kw")
    s.project.values["system.module_power"]["effective_to"]="2020-01-01"
    with pytest.raises(ContractError,match="ENERGY_SOURCE_EXPIRED"):
        capacity(EnergyInputs(s.export(),m,catalog))
    data=m.to_dict();data["parameters"]["thermal.a"].update(status="UNVERIFIED",source_kind="DOCUMENT_EXTRACTED")
    with pytest.raises(ContractError,match="BLOCKED_METHOD_REVIEW"):
        prepare_temperature(MethodConfig.from_dict(data))


def test_replacement_outage_reclips_both_states_not_post_clipping_scaling(catalog):
    s,m=replacement_case(catalog)
    inputs=EnergyInputs(s.export(),m,catalog)
    design=capacity(inputs)
    # Both the full and half-module plant remain inverter-limited at 2kW.
    design["groups"]=[{**g,"ac_kw":D(1)} for g in design["groups"]]
    perf=performance_schedule(inputs,[365]*3)[1]
    _,_,_,thermal,constants,item=prepared(catalog)
    with localcontext() as c:
        c.prec=60
        out=_power(item,design,thermal,inputs,_losses(inputs),perf,constants)
        expected=(D(2)*D(".99")-D(".2"))*D(".99")
        assert abs(out["output_kw"]-expected)<D("1E-50")
        states=out["replacement_states"]
        assert states["normal"]["output_kw"]==states["outage"]["output_kw"]==expected
        assert out["output_kw"]!=expected*perf["equivalent_availability"]
        assert abs(out["ideal_kw"]-out["output_kw"]-sum(out["losses_kw"].values()))<D("1E-50")


def test_inverter_outage_recomputes_shared_transformer_bottleneck(catalog):
    s,m=replacement_case(catalog,"INVERTERS_UNIFORM_FRACTION",None)
    inputs=EnergyInputs(s.export(),m,catalog);design=capacity(inputs)
    perf=performance_schedule(inputs,[365]*3)[1]
    _,_,_,thermal,constants,item=prepared(catalog)
    constants=(*constants[:5],D(5),None)
    with localcontext() as c:
        c.prec=60
        out=_power(item,design,thermal,inputs,_losses(inputs),perf,constants)
        assert out["replacement_states"]["outage"]["groups"][0]["ac_kw"]==0
        assert abs(out["output_kw"]-(D(5)-D(".2"))*D(".99"))<D("1E-50")


def test_ground_monthly_pr_rejects_zero_pf_at_public_entry(catalog,tmp_path):
    s,m=monthly_case(catalog,"utility_scale_ground")
    change(s,"grid.power_factor",D(0))
    with pytest.raises(ContractError,match="POWER_FACTOR"):
        calculate_ground(s.export(),m,catalog=catalog,output_dir=tmp_path/"bad-pf",budget=BundleBudget())
    assert not (tmp_path/"bad-pf/result.json").exists()


def test_receipt_disk_includes_result_and_its_own_size(catalog,tmp_path):
    from wangbin_solar_pv.serialization import loads,dumps
    s,m=monthly_case(catalog)
    calculate_rooftop(s.export(),m,catalog=catalog,output_dir=tmp_path/"out",budget=BundleBudget())
    receipt=loads((tmp_path/"out/receipt.json").read_bytes())
    actual=len(dumps(s.export()).encode("utf-8"))+sum(p.stat().st_size for p in (tmp_path/"out").iterdir())
    assert receipt["stats"]["disk_bytes"]==actual


def test_real_cli_accepts_result_directory_but_rejects_escape(catalog,tmp_path,capsys):
    from dataclasses import asdict
    from wangbin_solar_pv.cli import main
    from wangbin_solar_pv.serialization import dumps,loads
    s,m=monthly_case(catalog)
    for filename,data in (("input.json",s.export()),("methods.json",m.to_dict()),("budget.json",asdict(BundleBudget()))):
        (tmp_path/filename).write_text(dumps(data),encoding="utf-8")
    args=["--workspace",str(tmp_path),"energy","--input","input.json","--methods","methods.json","--budget","budget.json","--output"]
    assert main(args+["cli-result"])==0
    assert loads((tmp_path/"cli-result/result.json").read_bytes())["maturity"]["calculation"]=="CALCULATED_SYNTHETIC"
    capsys.readouterr()
    assert main(args+["../outside-result"])==2
    assert "PATH_TRAVERSAL" in capsys.readouterr().err


def test_calendar_year_hours_use_utc_elapsed_time_not_local_days_times_24():
    from wangbin_solar_pv.calculation.energy_yield import _calendar_hours
    assert _calendar_hours(2025,"Asia/Shanghai")==8760
    assert _calendar_hours(2024,"America/New_York")==8784
    assert _calendar_hours(2024,"Asia/Almaty")==8785
