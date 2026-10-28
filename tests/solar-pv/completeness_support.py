"""Coherent but explicitly SYNTHETIC evidence declarations, NOT an engineering case."""
import calendar
from decimal import Decimal
from wangbin_solar_pv.models import ProjectData
from wangbin_solar_pv.conditions import effective_requirement
from synthetic_support import record,row,put_rows


def value(field):
    fid,c=field["field_id"],field["constraints"]
    if "enum" in c: return c["enum"][0]
    if field["type"]=="boolean": return False
    if field["type"] in {"number","integer"}:
        n=max(Decimal("0"),Decimal(str(c.get("minimum",0))))
        if "exclusiveMinimum" in c: n=max(n,Decimal(str(c["exclusiveMinimum"]))+1)
        if "maximum" in c: n=min(n,Decimal(str(c["maximum"])))
        return int(n) if field["type"]=="integer" else n
    if c.get("format")=="date": return "2026-10-28"
    if c.get("format")=="date-time": return "2024-01-01T00:00:00Z"
    if fid.endswith(".currency"): return "CNY"
    if fid.endswith(".row_id"): return "SYNTHETIC-row"
    if fid.endswith(".sha256"): return "a"*64
    return "SYNTHETIC reviewed declaration, not actual project evidence"


def declared_project(cat, level="L2"):
    from wangbin_solar_pv.categories import category_contract
    p=ProjectData.new("SYNTHETIC-DECLARED-"+level,"industrial_rooftop",cat)
    overrides={
        "project.pv_type":"industrial_rooftop","project.name":"SYNTHETIC input-only fixture",
        "project.has_storage":False,"project.sales_mode":"full_export","project.ownership_mode":"owner_invested",
        "project.currency":"CNY","project.evaluation_years":20,"project.evaluation_date":"2026-10-28",
        "project.price_basis":"nominal","project.cashflow_tax_basis":"post_tax",
        "site.address":"SYNTHETIC not an actual address","site.latitude":Decimal("0"),"site.longitude":Decimal("0"),
        "site.crs":"EPSG:4326","site.timezone":"UTC","site.total_area":10000,"site.usable_area":8000,
        "site.exclusion_area":2000,"site.rights_status":"verified","site.rights_expiry":"2050-01-01",
        "roof.allowable_additional_load":Decimal("0.2"),"roof.design_added_load":Decimal("0.15"),"roof.remaining_life":30,
        "resource.model_method":"monthly_pr","resource.period_start":"2024-01-01","resource.period_end":"2024-12-31",
        "resource.uncertainty_fraction":Decimal("0.1"),"resource.is_tmy":False,
        "tariff.settlement_mode":"fixed","tariff.transaction_fee":Decimal("0"),
        "finance.debt_ratio":Decimal("0"),"finance.project_discount_rate":Decimal("0.08"),"finance.equity_discount_rate":Decimal("0.08"),
        "targets.payback_years":8,"targets.payback_basis":"static_from_investment",
        "system.dc_capacity":1000,"system.ac_capacity":800,"system.dc_ac_ratio":Decimal("1.25"),
        "system.module_count":2000,"system.module_power":500,"system.modules_per_string":20,"system.parallel_strings":100,
        "system.inverter_unit_ac":100,"system.inverter_count":8,
        "grid.opinion_status":"confirmed","grid.opinion_valid_until":"2027-10-28","grid.power_factor":Decimal("0.9"),
        "grid.transformer_capacity":1000,"grid.available_capacity":1000,"grid.export_power_limit":800,
        "schedule.development_start":"2027-01-01","schedule.construction_start":"2027-02-01","schedule.commissioning_date":"2027-03-01",
    }
    allowed=set(category_contract(p.pv_type,cat)["allowed_field_ids"])
    for fid,v in overrides.items():
        p.values[fid]=record(cat,fid,v,status="VERIFIED")
    for fid,f in cat.fields.items():
        if f.get("repeat_group") or f["type"]=="array" or fid in p.values or fid not in allowed: continue
        if effective_requirement(fid,level,p,cat)["requirement"]=="REQUIRED":
            p.values[fid]=record(cat,fid,value(f),status="VERIFIED")
    for fid,f in cat.fields.items():
        if f.get("repeat_group") or f["type"]!="array" or fid not in allowed: continue
        if effective_requirement(fid,level,p,cat)["requirement"]!="REQUIRED": continue
        if fid=="assets.replacements":
            p.applicability[fid]={"field_id":fid,"row_id":None,"status":"NOT_APPLICABLE","rule_id":"NO_REPLACEMENTS_PLANNED",
                "reason":"SYNTHETIC reviewed lifecycle plan within the fictional horizon","reviewer":"SYNTHETIC-REVIEWER",
                "evidence_source_ids":["SYNTHETIC-LOCAL"],"reviewed_at":"2026-10-28T12:00:00Z"}
            continue
        count=12 if fid=="resource.monthly" else (2 if fid in {"resource.annual_comparison","scenarios.options"} else (5 if fid=="site.boundary_vertices" else 1))
        loss_kinds=cat.fields["system.losses.kind"]["constraints"]["enum"]
        if fid=="system.losses": count=len(loss_kinds)
        rows=[]
        for n in range(count):
            rid="row"+str(n)
            vals={child[len(fid)+1:]:value(cat.fields[child]) for child in f["constraints"]["items"]["field_ids"]
                  if child!=fid+".row_id" and effective_requirement(child,level,p,cat)["requirement"]=="REQUIRED"}
            if fid=="resource.monthly": vals.update(month=n+1,days=calendar.monthrange(2024,n+1)[1],ghi=100,dni=100,dhi=100,poa=100,coverage=1,ambient_temperature=20,wind_speed=3)
            elif fid=="resource.annual_comparison": vals.update(year=2023+n,poa=1200,coverage=1,difference_from_reference=0)
            elif fid=="system.losses": vals.update(kind=loss_kinds[n],sequence=n,value=0,included_in_source=False)
            elif fid=="system.degradation_segments": vals.update(from_year=1,to_year=20,rate=Decimal("0.005"))
            elif fid=="tariff.periods": vals.update(start_time="00:00",end_time="24:00",sale_price=Decimal("0.5"),season="all",weekday_rule="all",effective_from="2026-01-01",effective_to="2027-12-31")
            elif fid=="capex.items": vals.update(category="design",quantity=2,unit_price=100,amount=200,currency="CNY",quote_date="2026-10-28",quote_valid_until="2027-10-28")
            elif fid=="opex.items": vals.update(from_year=1,to_year=20)
            elif fid=="assets.depreciation": vals.update(depreciable_basis=200,residual_value=0,depreciation_years=20)
            elif fid=="risk.items": vals.update(severity="minor",evidence_state="resolved",deadline="2027-01-01")
            elif fid=="schedule.tasks": vals.update(task_id="task1",predecessor_ids=[],start_date="2027-01-01",finish_date="2027-01-02")
            elif fid=="site.boundary_vertices":
                coordinates=[(0,0),(0,1),(1,1),(1,0),(0,0)]
                vals.update(polygon_id="SYNTHETIC-POLYGON",ring_index=0,vertex_index=n,latitude=coordinates[n][0],longitude=coordinates[n][1])
            elif fid=="scenarios.options":
                vals.update(scenario_id="s"+str(n),kind="baseline" if n==0 else "alternative",changed_field_id="layout.tilt",changed_value_text="0" if n==0 else "10")
            elif fid=="policy.applicability":
                vals.pop("superseded_by",None);vals.update(applicability_status="applicable",effective_to="2027-12-31")
                child=fid+".superseded_by"
                p.applicability[child+"@"+rid]={"field_id":child,"row_id":rid,"status":"NOT_APPLICABLE","rule_id":"NO_POLICY_SUPERSESSION",
                    "reason":"SYNTHETIC no replacement document in fictional policy review","reviewer":"SYNTHETIC-REVIEWER",
                    "evidence_source_ids":["SYNTHETIC-LOCAL"],"reviewed_at":"2026-10-28T12:00:00Z"}
            rows.append(row(cat,fid,rid,vals,status="VERIFIED"))
        put_rows(p,cat,fid,rows,status="VERIFIED")
    return p
