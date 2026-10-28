"""Exhaustive frozen scalar bounds and untrusted-envelope negative cases."""
from decimal import Decimal
import pytest
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.validation import validate_record,validate_project
from wangbin_solar_pv.models import ProjectData
from synthetic_support import record,row,put_rows,scalar_item

CAT=Catalog()
CASES=[]
for fid,f in CAT.fields.items():
    c=f["constraints"]
    if f["type"] in {"number","integer"}:
        for key in ("minimum","maximum","exclusiveMinimum","exclusiveMaximum"):
            if key in c:
                n=Decimal(str(c[key]))
                value=n if key.startswith("exclusive") else (n-1 if key=="minimum" else n+1)
                if f["type"]=="integer": value=int(value)
                CASES.append((fid,key,value))
    if f["type"]=="string" and c.get("minLength",0)>0:
        CASES.append((fid,"minLength",""))
    if "enum" in c:
        CASES.append((fid,"enum","SYNTHETIC-NOT-ENUM"))


@pytest.mark.parametrize("fid,kind,value",CASES)
def test_every_frozen_scalar_boundary_is_rejected(fid,kind,value):
    r=record(CAT,fid,value)
    assert any(i.code=="FIELD_SCHEMA" for i in validate_record(r,CAT)), (fid,kind)


def test_invalid_numbers_are_reported_not_crashed_or_logged_as_real_values():
    p=ProjectData.new("SYNTHETIC-NAN","industrial_rooftop",CAT)
    r=row(CAT,"capex.items","a",{"quantity":2,"unit_price":100,"amount":Decimal("NaN")})
    put_rows(p,CAT,"capex.items",[r])
    issues=validate_project(p,CAT)
    assert any(i.code=="FIELD_SCHEMA" for i in issues)
    assert all("NaN" not in i.message for i in issues)


def test_task_graph_long_chain_does_not_depend_on_python_recursion_limit():
    p=ProjectData.new("SYNTHETIC-LONG-GRAPH","industrial_rooftop",CAT)
    fid="schedule.tasks.predecessor_ids"
    rows=[]
    for i in range(1100):
        predecessors=[] if i==0 else [scalar_item(CAT,fid,"t"+str(i-1),"SYNTHETIC-element-"+str(i))]
        rows.append(row(CAT,"schedule.tasks","r"+str(i),{"task_id":"t"+str(i),"predecessor_ids":predecessors}))
    rows.reverse()
    put_rows(p,CAT,"schedule.tasks",rows)
    assert not [i for i in validate_project(p,CAT) if i.severity=="ERROR"]


def test_single_numeric_confidence_is_not_an_evidence_explanation():
    r=record(CAT,"site.usable_area",100)
    r["confidence_basis"]="0.99"
    assert any(i.code=="CONFIDENCE_BASIS_REQUIRED" for i in validate_record(r,CAT))
