"""Input geometry/observations and engineering declarations; no output forecasting."""
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.models import ProjectData
from synthetic_support import record,row,put_rows

CAT=Catalog()


def issues(p):
    from wangbin_solar_pv.quality import assess_input_quality
    return {i.code for i in assess_input_quality(p,CAT)}


def polygon(coords):
    p=ProjectData.new("SYNTHETIC-POLYGON","industrial_rooftop",CAT)
    p.values["site.crs"]=record(CAT,"site.crs","EPSG:4326")
    put_rows(p,CAT,"site.boundary_vertices",[row(CAT,"site.boundary_vertices","r"+str(i),{"polygon_id":"P","ring_index":0,"vertex_index":i,"latitude":a,"longitude":b}) for i,(a,b) in enumerate(coords)])
    return p


def test_closed_polygon_and_self_intersection_are_distinguished():
    good=polygon([(0,0),(0,1),(1,1),(1,0),(0,0)])
    assert "POLYGON_SELF_INTERSECTION" not in issues(good)
    bad=polygon([(0,0),(1,1),(0,1),(1,0),(0,0)])
    assert "POLYGON_SELF_INTERSECTION" in issues(bad)


def test_open_ring_is_reported_not_silently_closed():
    p=polygon([(0,0),(0,1),(1,1),(1,0)])
    assert "POLYGON_NOT_CLOSED" in issues(p)
    assert len(p.values["site.boundary_vertices"]["value"])==4


def test_usable_capacity_is_not_implicitly_converted_from_kva():
    p=ProjectData.new("SYNTHETIC-CAPACITY","industrial_rooftop",CAT)
    for fid,v in [("system.ac_capacity",100),("grid.transformer_capacity",100),("grid.power_factor",0.8)]:
        p.values[fid]=record(CAT,fid,v)
    assert "TRANSFORMER_LIMIT_EXCEEDED" in issues(p)
    p.values["grid.power_factor"]["value"]=0
    assert "POWER_FACTOR_NOT_POSITIVE" in issues(p)


def test_evidence_expiry_and_grid_rejection_are_explicit():
    p=ProjectData.new("SYNTHETIC-GRID","industrial_rooftop",CAT)
    p.values["project.evaluation_date"]=record(CAT,"project.evaluation_date","2026-10-28")
    p.values["grid.opinion_status"]=record(CAT,"grid.opinion_status","confirmed")
    p.values["grid.opinion_valid_until"]=record(CAT,"grid.opinion_valid_until","2025-12-31")
    assert "GRID_OPINION_EXPIRED" in issues(p)
    p.values["grid.opinion_status"]["value"]="rejected"
    assert "GRID_REJECTED" in issues(p)
