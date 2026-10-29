"""Real full-year D3 -> thermal/DC/per-inverter AC -> lifecycle acceptance."""
from dataclasses import asdict
from decimal import Decimal as D
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time
from fractions import Fraction as F

import pytest

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.serialization import dumps, loads, MAX_JSON_BYTES
from wangbin_solar_pv.timeseries_bundle import BundleBudget, write_bundle, read_bundle
from wangbin_solar_pv.calculation.energy_yield import calculate_ground, calculate_rooftop
from wangbin_solar_pv.calculation.result_contract import validate_result, serialize_result, deserialize_result
from energy_case_support import case, resource_header, resource_rows, independent_reference, atom


@pytest.mark.parametrize("year,minutes,count,category", [
    (2025,60,8760,"industrial_rooftop"), (2024,60,8784,"utility_scale_ground"),
    (2025,15,35040,"utility_scale_ground"), (2024,15,35136,"industrial_rooftop")])
def test_full_year_actual_generation_against_independent_reference(tmp_path, year, minutes, count, category):
    catalog=Catalog()
    s,m=case(catalog,category,year=year,scale=10)
    budget=BundleBudget(max_seconds=1800,max_memory_bytes=1024**3)
    exported=s.export()
    (tmp_path/"input.json").write_text(dumps(exported),encoding="utf-8")
    (tmp_path/"methods.json").write_text(dumps(m.to_dict()),encoding="utf-8")
    (tmp_path/"budget.json").write_text(dumps(asdict(budget)),encoding="utf-8")
    begin=time.monotonic()
    manifest=write_bundle(tmp_path/"resource",base_export=exported,catalog=catalog,budget=budget,
        datasets={"resource.timeseries":{"header":resource_header(catalog,year,minutes),
            "rows":resource_rows(catalog,year,minutes)}})
    write_seconds=time.monotonic()-begin
    assert manifest["datasets"]["resource.timeseries"]["row_count"]==count
    begin=time.monotonic()
    with read_bundle(tmp_path/"resource",catalog=catalog,budget=budget) as bundle:
        validation_stats=bundle.stats
        assert validation_stats["rows_validated"]==count
        assert validation_stats["input_bytes"]>MAX_JSON_BYTES
        fn=calculate_ground if category=="utility_scale_ground" else calculate_rooftop
        result=fn(exported,m,catalog=catalog,budget=budget,bundle=bundle,output_dir=tmp_path/"generation")
    compute_seconds=time.monotonic()-begin
    metrics={v["metric_id"]:v for v in result["results"]["metrics"]}
    actual=metrics["energy.annual_array"]["value"]
    expected=[value*10 for value in independent_reference(days=366 if year==2024 else 365,category=category)]
    assert all(abs(a-b)<D("0.00000001") for a,b in zip(actual,expected))
    assert abs(sum(actual)-metrics["energy.lifecycle"]["value"])<D("0.000000001")
    for i in range(1,4):
        details=metrics[f"energy.year.{i}"]["details"]
        assert len(details["monthly_kwh"])==12
        assert abs(sum(details["monthly_kwh"])-actual[i-1])<D("0.000000001")
    assert deserialize_result(serialize_result(result,catalog),catalog)==result
    validate_result(result,catalog)
    receipt=loads((tmp_path/"generation/receipt.json").read_bytes())
    assert receipt["input_rows"]==count
    assert receipt["physical_evaluations"]==count*3
    assert receipt["stats"]["os_peak_working_set_bytes"]<=budget.max_memory_bytes
    assert receipt["resource_enforcement"]=="COOPERATIVE_APPLICATION_CHECKPOINTS_NOT_OS_SANDBOX"
    for chunk in receipt["chunks"]:
        payload=(tmp_path/"generation"/chunk["file"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest()==chunk["sha256"]
    if count==8760:
        # A separate real CLI execution must reproduce the API result identity.
        repo=Path(__file__).resolve().parents[2]
        command=[sys.executable,"-B",str(repo/"services/solar-pv-engine/solar_pv.py"),
            "--workspace",str(tmp_path),"energy","--input","input.json","--methods","methods.json",
            "--budget","budget.json","--bundle","resource","--output","cli-generation"]
        completed=subprocess.run(command,capture_output=True,text=True,timeout=1800)
        assert completed.returncode==0,completed.stderr
        cli=loads((tmp_path/"cli-generation/result.json").read_bytes())
        assert cli["result_hash"]==result["result_hash"]
    evidence={"kind":"SYNTHETIC_NOT_REAL_WEATHER","year":year,"minutes":minutes,"count":count,
        "category":category,"write_seconds":str(write_seconds),"read_and_compute_seconds":str(compute_seconds),
        "input_validation":validation_stats,"actual_annual_kwh":[str(v) for v in actual],
        "independent_expected_kwh":[str(v) for v in expected],"absolute_errors_kwh":[str(abs(a-b)) for a,b in zip(actual,expected)],
        "result_hash":result["result_hash"],"input_hash":result["input_hash"],
        "bundle_content_hash":manifest["content_hash"],"receipt":json.loads(dumps(receipt)),
        "input_manifest_sha256":hashlib.sha256((tmp_path/"resource/manifest.json").read_bytes()).hexdigest()}
    (tmp_path/"acceptance.json").write_text(json.dumps(evidence,indent=2),encoding="utf-8")


@pytest.mark.parametrize("category",["industrial_rooftop","utility_scale_ground"])
def test_25_year_1mwp_complete_case_with_explicit_replacement(tmp_path,category):
    from wangbin_solar_pv.calculation.method_config import MethodConfig,make_parameter
    catalog=Catalog()
    s,m=case(catalog,category,years=25,scale=10)
    event={"asset_id":"SYNTHETIC-modules", "year":12,"downtime_days":10,
           "performance_reset":"EXPLICIT_METHOD_RULE","row_id":"modules-year12"}
    row={"row_id":"modules-year12","fields":{"assets.replacements."+k:atom(catalog,"assets.replacements."+k,v,"25year-event-"+k) for k,v in event.items()}}
    s.project.values["assets.replacements"]=atom(catalog,"assets.replacements",[row])
    config=m.to_dict()
    extra={"replacement.method":"EXPLICIT_ASSET_EVENTS","degradation.performance_ceiling":D(1),
        "replacement.rules":[{"event_id":"modules-year12","scope":"MODULES_UNIFORM_FRACTION",
          "capacity_fraction":D(".5"),"target_retention":D(".99"),
          "timing":"YEAR_START_RECOVERY_UNIFORM_EQUIVALENT_DOWNTIME"}]}
    config["parameters"].update({pid:make_parameter(pid,value,source_id="SYNTHETIC-replacement",
        source_reference="SYNTHETIC:year12 partial replacement, explicit equivalent two-state scenario",
        status="ASSUMED",source_kind="SYNTHETIC",license_status="AUTHORIZED") for pid,value in extra.items()})
    m=MethodConfig.from_dict(config)
    budget=BundleBudget(max_seconds=1800,max_memory_bytes=1024**3,max_disk_bytes=2*1024**3)
    exported=s.export()
    for filename,data in (("input.json",exported),("methods.json",m.to_dict()),("budget.json",asdict(budget))):
        (tmp_path/filename).write_text(dumps(data),encoding="utf-8")
    manifest=write_bundle(tmp_path/"resource",base_export=exported,catalog=catalog,budget=budget,
        datasets={"resource.timeseries":{"header":resource_header(catalog),"rows":resource_rows(catalog)}})
    start=time.monotonic()
    with read_bundle(tmp_path/"resource",catalog=catalog,budget=budget) as bundle:
        fn=calculate_ground if category=="utility_scale_ground" else calculate_rooftop
        result=fn(exported,m,catalog=catalog,budget=budget,bundle=bundle,output_dir=tmp_path/"generation")
    elapsed=time.monotonic()-start
    metrics={v["metric_id"]:v for v in result["results"]["metrics"]}
    actual=metrics["energy.annual_array"]["value"]
    expected=[v*10 for v in independent_reference(years=25,category=category,
        event={"year":12,"fraction":F(1,2),"target":F(99,100),"days":F(10)})]
    assert len(actual)==25 and all(abs(a-b)<D("1E-8") for a,b in zip(actual,expected))
    assert metrics["dc_capacity"]["value"]==1000
    assert len(metrics["energy.monthly.year.1"]["value"])==12
    assert actual[11]>actual[10]
    assert deserialize_result(serialize_result(result,catalog),catalog)==result
    receipt=loads((tmp_path/"generation/receipt.json").read_bytes())
    disk_input=sum(p.stat().st_size for p in (tmp_path/"resource").iterdir())
    disk_output=sum(p.stat().st_size for p in (tmp_path/"generation").iterdir())
    assert receipt["stats"]["disk_bytes"]==disk_input+disk_output
    proof={"kind":"SYNTHETIC_1MWP_25_YEAR_NOT_REAL_SITE", "category":category,
        "input_rows":8760,"elapsed_seconds":str(elapsed),"actual_kwh":[str(v) for v in actual],
        "independent_kwh":[str(v) for v in expected],"errors_kwh":[str(abs(a-b)) for a,b in zip(actual,expected)],
        "result_hash":result["result_hash"],"bundle_content_hash":manifest["content_hash"],
        "disk_input_bytes":disk_input,"disk_output_bytes":disk_output}
    (tmp_path/"acceptance.json").write_text(json.dumps(proof,indent=2),encoding="utf-8")


@pytest.mark.parametrize("zone,count,first_hours",[("America/New_York",17544,8784),("Asia/Almaty",17545,8785)])
def test_year_specific_leap_and_dst_resource_mapping(tmp_path,zone,count,first_hours):
    from wangbin_solar_pv.calculation.method_config import MethodConfig
    catalog=Catalog()
    s,m=case(catalog,"utility_scale_ground",years=2,year=2024,zone=zone)
    data=m.to_dict();data["parameters"]["energy.resource_repetition"]["value"]="YEAR_SPECIFIC"
    m=MethodConfig.from_dict(data)
    budget=BundleBudget(max_seconds=1800,max_memory_bytes=1024**3)
    exported=s.export()
    write_bundle(tmp_path/"resource",base_export=exported,catalog=catalog,budget=budget,
        datasets={"resource.timeseries":{"header":resource_header(catalog,2024,60,zone,2),
            "rows":resource_rows(catalog,2024,60,zone,2)}})
    with read_bundle(tmp_path/"resource",catalog=catalog,budget=budget) as bundle:
        assert bundle.manifest["datasets"]["resource.timeseries"]["row_count"]==count
        out=calculate_ground(exported,m,catalog=catalog,budget=budget,bundle=bundle,output_dir=tmp_path/"generation")
    metrics={v["metric_id"]:v for v in out["results"]["metrics"]}
    expected=[independent_reference(days=366,category="utility_scale_ground",years=2)[0],
              independent_reference(days=365,category="utility_scale_ground",years=2)[1]]
    assert all(abs(a-b)<D("1E-8") for a,b in zip(metrics["energy.annual_array"]["value"],expected))
    assert metrics["energy.year.1"]["details"]["actual_hours"]==first_hours
    assert metrics["energy.year.2"]["details"]["actual_hours"]==8760
    assert not any(f["code"]=="REPEATED_RESOURCE_YEAR_NOT_MULTIPLE_OBSERVED_YEARS" for f in out["findings"])
