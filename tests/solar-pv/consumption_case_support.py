"""Explicit SYNTHETIC settlement inputs; no production output is a reference.

The generation helpers below invoke the actual, separately verified Phase 3B
entry point when an end-to-end source is needed. Calendar-only tests use an
axis object, never a fabricated Phase 3B numerical result.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from fractions import Fraction as F
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from energy_case_support import case, resource_header, resource_rows
from wangbin_solar_pv.intake import IntakeSession
from wangbin_solar_pv.provenance import make_record
from wangbin_solar_pv.calculation.method_config import MethodConfig, make_parameter

BASIS = {"currency":"CNY","price_year":2025,"tax_basis":"inclusive","price_basis":"nominal"}


def atom(catalog,fid,value,instance=None,**kwargs):
    if "currency" in (catalog.fields[fid]["unit"] or ""):
        kwargs.setdefault("economic_basis",deepcopy(BASIS))
    return make_record(catalog,fid,value,source_kind="USER_PROVIDED",source_id="SYNTHETIC-settlement",
        source_url_or_attachment="SYNTHETIC:controlled-load-price-scenario",source_section_or_cell=instance or fid,
        field_instance_id=instance or fid,confidence_basis="SYNTHETIC, not real enterprise or policy evidence",
        license_status="AUTHORIZED",retrieved_at="2026-10-30T00:00:00Z",last_updated="2026-10-30T00:00:00Z",**kwargs)


def parameter(pid,value):
    return make_parameter(pid,value,source_id="SYNTHETIC-settlement-methods",source_reference="SYNTHETIC:explicit approved D2 settlement controls",
        status="ASSUMED",source_kind="SYNTHETIC",license_status="AUTHORIZED")


def extend(session,methods,*,category=None,market=False,ppa=None,cap=20,price=D("0.4"),avoid=D("0.8"),basis=None):
    category = category or session.project.pv_type
    boundary = "GRID_DELIVERABLE" if category == "utility_scale_ground" else "AVAILABLE_PRE_CONSUMPTION"
    data = {"grid.metering_boundary":boundary,"tariff.contract_id":"SYNTHETIC-CONTRACT",
        "tariff.settlement_mode":"SYNTHETIC_SIGNED_ENERGY_SETTLEMENT","tariff.negative_price_rule":"SYNTHETIC contract explicitly settles signed prices",
        "revenue.other_items":[],"tariff.transaction_fee":D("0.01")}
    if category == "industrial_rooftop":
        data.update({"project.ownership_mode":"ppa" if ppa else "owner_invested","load.timezone":session.project.values["site.timezone"]["value"],
            "load.meter_boundary":boundary,"load.meter_id":"SYNTHETIC-SAME-NODE","load.quality_basis":"SYNTHETIC complete controlled scenario",
            "tariff.non_avoidable_charges":"SYNTHETIC energy-only marginal prices exclude demand, capacity and fixed charges"})
    if ppa == "PPA_FIXED":
        data["tariff.ppa_price"] = D("0.5")
    for fid,value in data.items():
        session.project.values[fid] = atom(session.catalog,fid,value)
    session.project.values["tariff.periods"] = atom(session.catalog,"tariff.periods",[period_row(session.catalog,"flat",price=price,avoid=avoid if category == "industrial_rooftop" else None)])
    config = methods.to_dict() if isinstance(methods,MethodConfig) else deepcopy(methods)
    controls = {"consumption.load_repetition":"NO_LOAD_GROUND" if category == "utility_scale_ground" else config["parameters"]["energy.resource_repetition"]["value"],
        "consumption.commercial_export_limit_kw":cap,"settlement.price_source":"MARKET_SERIES" if market else "PERIOD_TABLE",
        "settlement.revenue_method":"EXPORT_ONLY" if category == "utility_scale_ground" else ppa or "OWNER_AVOIDED_COST",
        "settlement.fee_treatment":"SEPARATE_LEDGER","settlement.negative_price_treatment":"SETTLE_SIGNED_CONTRACT_PRICE",
        "settlement.other_benefit_months":[],"prices.escalation_fraction":D(0)}
    controls.update({"settlement."+k:v for k,v in (basis or BASIS).items()})
    if ppa == "PPA_DISCOUNT":
        controls["settlement.ppa_discount_factor"] = D("0.75")
    config["parameters"].update({pid:parameter(pid,value) for pid,value in controls.items()})
    return session,MethodConfig.from_dict(config)


def period_row(catalog,row_id,*,start="00:00",end="24:00",first="2020-01-01",last="2100-12-31",months="ALL",weekdays="ALL",price=D("0.4"),avoid=D("0.8"),basis=None):
    basis = basis or BASIS
    values = {"effective_from":first,"effective_to":last,"season":months,"weekday_rule":weekdays,"start_time":start,"end_time":end,
        "period_label":row_id,"avoidable_price":avoid,"sale_price":price,"tax_included":basis["tax_basis"] == "inclusive",
        "vat_rate":D("0.13"),"policy_id":"SYNTHETIC-POLICY-NOT-REAL","row_id":row_id}
    fields = {}
    for key,value in values.items():
        if key == "avoidable_price" and value is None:
            continue  # Ground has no host purchase-price fact or saving model.
        fid = "tariff.periods."+key
        kwargs = {"economic_basis":basis} if key in {"avoidable_price","sale_price"} else {}
        fields[fid] = atom(catalog,fid,value,"price-"+row_id+"-"+key,**kwargs)
    return {"row_id":row_id,"fields":fields}


def axis(year=2025,minutes=60,zone="Asia/Shanghai",days=None,years=1):
    z = ZoneInfo(zone)
    start = datetime(year,1,1,tzinfo=z).astimezone(timezone.utc)
    end = start+timedelta(days=days) if days is not None else datetime(year+years,1,1,tzinfo=z).astimezone(timezone.utc)
    return SimpleNamespace(zone=z,start=start,end=end,period={"start":start.astimezone(z).isoformat(),"end":end.astimezone(z).isoformat(),
        "timezone":zone,"interval_minutes":minutes,"coverage":1})


def series_header(catalog,fid,a):
    rec = atom(catalog,fid,None)
    rec.pop("value"); rec.pop("original_value")
    rec["measurement_period"] = deepcopy(a.period)
    return rec


def load_rows(catalog,a,*,power=D(40),use_power=False):
    point = a.start; i = 0
    step = timedelta(minutes=a.period["interval_minutes"])
    hours = F(a.period["interval_minutes"])/60
    energy = D((F(power)*hours).numerator)/D((F(power)*hours).denominator)
    while point < a.end:
        data = {"timestamp":point.astimezone(a.zone).isoformat(),"interval_minutes":a.period["interval_minutes"],
            "quality_flag":"valid","row_id":f"l{i}","power" if use_power else "energy":power if use_power else energy}
        yield {"row_id":f"l{i}","fields":{"load.series."+k:atom(catalog,"load.series."+k,v,f"load-{i}-{k}") for k,v in data.items()}}
        point += step; i += 1


def market_rows(catalog,a,*,price=D("0.4"),fee=D("0.01")):
    point = a.start; i = 0
    step = timedelta(minutes=a.period["interval_minutes"])
    while point < a.end:
        selected = (D("-0.1") if 12 <= point.astimezone(a.zone).hour < 14 else price)
        data = {"timestamp":point.astimezone(a.zone).isoformat(),"interval_minutes":a.period["interval_minutes"],
                "sale_price":selected,"transaction_fee":fee,"row_id":f"m{i}"}
        yield {"row_id":f"m{i}","fields":{"tariff.market_series."+k:atom(catalog,"tariff.market_series."+k,v,f"market-{i}-{k}") for k,v in data.items()}}
        point += step; i += 1


def inline_series(session,fid,a,rows):
    rec = atom(session.catalog,fid,list(rows));rec["measurement_period"] = deepcopy(a.period)
    session.project.values[fid] = rec


def session_from_export(exported,catalog):
    return IntakeSession.from_dict(deepcopy(exported["project"]),catalog)
