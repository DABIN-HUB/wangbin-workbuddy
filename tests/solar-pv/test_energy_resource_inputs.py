"""Independent SYNTHETIC resource and evidence selection references."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
import importlib

import pytest

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.intake import IntakeSession
from wangbin_solar_pv.provenance import make_record
from wangbin_solar_pv.calculation.method_config import MethodConfig, make_parameter
from wangbin_solar_pv.errors import ContractError


@pytest.fixture(scope="module")
def catalog():
    return Catalog()


def atom(catalog, fid, value, instance=None, **metadata):
    return make_record(catalog, fid, value, source_kind="USER_PROVIDED",
        source_id="SYNTHETIC-energy-resource", source_url_or_attachment="SYNTHETIC:resource-reference",
        source_section_or_cell=instance or fid, field_instance_id=instance or fid,
        confidence_basis="SYNTHETIC independent arithmetic reference; not real site data",
        license_status="AUTHORIZED", retrieved_at="2026-10-29T00:00:00Z",
        last_updated="2026-10-29T00:00:00Z", **metadata)


def methods():
    return MethodConfig.from_dict({"schema_version":"solar-pv-method-config/1.0.0", "config_id":"SYNTHETIC-resource",
        "data_mode":"SYNTHETIC", "pv_types":["industrial_rooftop","utility_scale_ground"],
        "parameters": {"precision.digits":make_parameter("precision.digits",80,source_id="SYNTHETIC-precision",
            source_reference="SYNTHETIC:exact-arithmetic",status="ASSUMED",source_kind="SYNTHETIC",license_status="AUTHORIZED")}})


def project(catalog, *, zone="Asia/Shanghai", pv_type="industrial_rooftop"):
    s = IntakeSession.new("SYNTHETIC-resource",pv_type,catalog)
    for fid,value in {"project.evaluation_date":"2026-10-29","site.timezone":zone,
                      "resource.poa_boundary":"ARRAY_PLANE_INTERVAL_MEAN"}.items():
        s.project.values[fid]=atom(catalog,fid,value)
    return s


def interval_project(catalog, *, start="2025-01-01T00:00:00+08:00", minutes=15, poa=(800,600,400,200), zone="Asia/Shanghai"):
    s=project(catalog,zone=zone); rows=[]
    utc=datetime.fromisoformat(start).astimezone(timezone.utc)
    from zoneinfo import ZoneInfo
    for i,value in enumerate(poa):
        stamp=(utc+timedelta(minutes=i*minutes)).astimezone(ZoneInfo(zone)).isoformat()
        data={"timestamp":stamp,"interval_minutes":minutes,"poa":value,
              "ambient_temperature":20,"wind_speed":1,"quality_flag":"valid","row_id":f"r{i}"}
        rows.append({"row_id":f"r{i}","fields": {"resource.timeseries."+k:atom(catalog,"resource.timeseries."+k,v,f"r{i}:{k}") for k,v in data.items()}})
    end=(utc+timedelta(minutes=len(poa)*minutes)).astimezone(ZoneInfo(zone)).isoformat()
    s.project.values['resource.timeseries']=atom(catalog,'resource.timeseries',rows,
        measurement_period={'start':start,'end':end,'timezone':zone,'interval_minutes':minutes,'coverage':1})
    return s


def api():
    return importlib.import_module("wangbin_solar_pv.calculation.solar_resource")


def inputs(s,catalog):
    from wangbin_solar_pv.calculation.energy_inputs import EnergyInputs
    return EnergyInputs(s.export(),methods(),catalog)


def test_exact_watt_to_kilowatt_interval_integration(catalog):
    rows=list(api().intervals(inputs(interval_project(catalog),catalog)))
    # Independent rational arithmetic: (800+600+400+200)/1000 * 15/60 = 1/2.
    assert sum((r.poa_kw_m2*r.hours for r in rows),D(0))==D('0.5')
    assert all(r.hours==D('0.25') for r in rows)
    assert all(r.source_instance_ids for r in rows)


@pytest.mark.parametrize("field,value,code",[("quality_flag","missing","ENERGY_RESOURCE_QUALITY"),
    ("timestamp","2025-01-01T00:00:00+08:00","INPUT_VALIDATION_FAILED"),
    ("interval_minutes",30,"ENERGY_RESOURCE_INTERVAL")])
def test_quality_duplicate_and_mixed_resolution_block(catalog,field,value,code):
    s=interval_project(catalog);s.project.values['resource.timeseries']['value'][1]['fields']['resource.timeseries.'+field]['value']=value
    # Keep the raw and normalized claims identical; source validation is not bypassed.
    rec=s.project.values['resource.timeseries']['value'][1]['fields']['resource.timeseries.'+field];rec['original_value']=value
    with pytest.raises(ContractError,match=code):list(api().intervals(inputs(s,catalog)))


def test_ghi_is_not_poa(catalog):
    s=interval_project(catalog)
    for row in s.project.values['resource.timeseries']['value']:
        del row['fields']['resource.timeseries.poa']
        row['fields']['resource.timeseries.ghi']=atom(catalog,'resource.timeseries.ghi',800,row['row_id']+':ghi')
    with pytest.raises(ContractError,match="BLOCKED_METHOD_REVIEW"):
        list(api().intervals(inputs(s,catalog)))


def test_fall_back_two_wall_clock_hours_are_two_real_hours(catalog):
    s=interval_project(catalog,start="2025-11-02T01:00:00-04:00",minutes=60,poa=(1000,1000),zone="America/New_York")
    rows=list(api().intervals(inputs(s,catalog)))
    assert len(rows)==2 and sum((r.hours for r in rows),D(0))==2
    assert rows[0].start!=rows[1].start


def test_spring_forward_is_real_elapsed_time_not_three_wall_hours(catalog):
    s=interval_project(catalog,start="2025-03-09T01:00:00-05:00",minutes=60,poa=(1000,1000),zone="America/New_York")
    assert sum((r.hours for r in api().intervals(inputs(s,catalog))),D(0))==2


def test_month_boundary_interval_is_split_without_energy_loss(catalog):
    s=interval_project(catalog,start="2025-01-31T23:30:00+08:00",minutes=60,poa=(1000,))
    row=next(api().intervals(inputs(s,catalog)))
    parts=list(api().month_parts(row, "Asia/Shanghai"))
    assert parts==[("2025-01",D('0.5')),("2025-02",D('0.5'))]


def test_expired_record_is_not_usable_despite_successful_export(catalog):
    s=interval_project(catalog)
    s.project.values['site.timezone']['effective_to']='2020-01-01'
    with pytest.raises(ContractError,match="ENERGY_SOURCE_EXPIRED"):
        list(api().intervals(inputs(s,catalog)))
