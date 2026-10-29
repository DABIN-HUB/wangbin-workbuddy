"""SYNTHETIC-only inputs and an independent, rational generation reference."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal as D
from fractions import Fraction as F
from math import exp
from zoneinfo import ZoneInfo

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.intake import IntakeSession
from wangbin_solar_pv.provenance import make_record
from wangbin_solar_pv.calculation.method_config import MethodConfig, make_parameter


def atom(catalog, fid, value, instance=None, **kwargs):
    return make_record(catalog, fid, value, source_kind="USER_PROVIDED",
        source_id="SYNTHETIC-generation", source_url_or_attachment="SYNTHETIC:independent-generation-case",
        source_section_or_cell=instance or fid, field_instance_id=instance or fid,
        confidence_basis="SYNTHETIC deterministic reference, NOT real site evidence",
        license_status="AUTHORIZED", retrieved_at="2026-10-29T00:00:00Z",
        last_updated="2026-10-29T00:00:00Z", **kwargs)


def case(catalog, category="industrial_rooftop", years=3, year=2025, zone="Asia/Shanghai", scale=1):
    s = IntakeSession.new("SYNTHETIC-"+category, category, catalog)
    values = {"project.evaluation_date": "2026-10-29", "project.currency": "CNY",
        "project.evaluation_years": years, "project.has_storage": False,
        "project.sales_mode": "full_export" if category == "utility_scale_ground" else "self_use_surplus_export",
        "site.timezone": zone, "site.total_area": 1000, "site.exclusion_area": 100,
        "site.usable_area": 900, "site.area_basis": "SYNTHETIC non-overlapping exclusion union, module surface GCR",
        "site.land_classification": "SYNTHETIC permitted scenario", "site.geotechnical_reference": "SYNTHETIC geotechnical scenario",
        "site.flood_reference": "SYNTHETIC flood scenario",
        "roof.design_added_load": D("0.1"), "roof.allowable_additional_load": D("0.2"),
        "roof.remaining_life": 100, "roof.structure_report_id": "SYNTHETIC-structure",
        "roof.fire_access_reference": "SYNTHETIC-fire", "roof.waterproof_plan": "SYNTHETIC-waterproof",
        "system.module_count": 200, "system.module_power": 500,
        "system.inverter_unit_ac": 40, "system.inverter_count": 2, "system.inverter_efficiency": D("0.98"),
        "system.module_length": 2, "system.module_width": 1,
        "system.modules_per_string": 20, "system.parallel_strings": 10,
        "system.module_voc": 50, "system.module_vmp": 40,
        "system.module_isc": 14, "system.module_imp": 13,
        "system.inverter_max_dc_voltage": 1100, "system.inverter_mppt_min": 400,
        "system.inverter_mppt_max": 900, "system.inverter_max_input_current": 100,
        "system.temperature_coefficient": D("-0.004"), "system.mounting_type": "FIXED",
        "system.first_year_degradation": D("0.02"), "system.annual_degradation": D("0.1"),
        "system.unavailability": D("0.01"), "assets.replacements": [],
        "layout.tilt": 20, "layout.azimuth": 180, "layout.row_pitch": 3,
        "layout.ground_coverage_ratio": D("0.5"), "layout.string_validation_reference": "SYNTHETIC independent cold/hot string design scenario",
        "grid.transformer_capacity": 100, "grid.power_factor": D("0.9"),
        "grid.export_power_limit": 60, "grid.available_capacity": 70,
        "resource.poa_boundary": "ARRAY_PLANE_INTERVAL_MEAN"}
    for fid in ("site.total_area", "site.exclusion_area", "site.usable_area", "system.module_count",
                "system.inverter_unit_ac", "system.parallel_strings", "system.inverter_max_input_current",
                "grid.transformer_capacity", "grid.export_power_limit", "grid.available_capacity"):
        values[fid] *= scale
    for fid, value in values.items():
        # Do not put rooftop-only facts into a ground project (or vice versa).
        if category == "utility_scale_ground" and fid.startswith("roof."):
            continue
        if category == "industrial_rooftop" and fid in {"site.land_classification", "site.geotechnical_reference", "site.flood_reference"}:
            continue
        s.project.values[fid] = atom(catalog, fid, value)
    rows = []
    order = ("shading", "soiling", "snow", "mismatch", "dc_cable", "ac_cable", "transformer", "export_line", "curtailment")
    for seq, kind in enumerate(order):
        rate = D("0.01")
        if kind == "snow" or (category == "industrial_rooftop" and kind in ("transformer", "export_line", "curtailment")):
            rate = D(0)
        boundary = "DC" if seq < 5 else ("AC" if kind == "ac_cable" else "GRID")
        data = {"kind": kind, "value": rate, "sequence": seq, "boundary": boundary,
            "included_in_source": False, "method": "INDEPENDENT_CONSTANT_RATE", "period": "ALL_OPERATING_YEARS", "row_id": kind}
        rows.append({"row_id": kind, "fields": {"system.losses."+k: atom(catalog, "system.losses."+k, v, f"loss-{kind}-{k}") for k,v in data.items()}})
    s.project.values["system.losses"] = atom(catalog, "system.losses", rows)
    params = {"precision.digits": 60, "precision.abs_tolerance": D("0.000000001"), "precision.rel_tolerance": D("0.000000000001"),
        "energy.method": "INTERVAL_DC_AC", "energy.resource_repetition": "EXPLICIT_REPRESENTATIVE_SCENARIO",
        "energy.dc_allocation": [D("0.5"), D("0.5")], "energy.auxiliary_kw": D("0.2")*scale,
        "energy.pr_includes_initial_degradation": False, "energy.upstream_included_losses": [],
        "thermal.method": "SANDIA", "thermal.a": D(-4), "thermal.b": D(0), "thermal.delta_temperature": D(0),
        "thermal.minimum_cell_temperature": D(-50), "thermal.maximum_cell_temperature": D(120),
        "constants.stc_irradiance": D(1), "constants.stc_cell_temperature": D(25),
        "degradation.method": "ANNUAL", "replacement.method": "NONE_DECLARED",
        "time.horizon_basis": "OPERATING_YEARS"}
    config = {"schema_version": "solar-pv-method-config/1.0.0", "config_id": "SYNTHETIC-generation-methods",
        "data_mode": "SYNTHETIC", "pv_types": [category], "parameters": {
            pid: make_parameter(pid, value, source_id="SYNTHETIC-generation-methods",
                source_reference="SYNTHETIC:explicit physical scenario, not recommended device defaults",
                status="ASSUMED", source_kind="SYNTHETIC", license_status="AUTHORIZED") for pid,value in params.items()}}
    return s, MethodConfig.from_dict(config)


def resource_header(catalog, year=2025, minutes=60, zone="Asia/Shanghai", years=1):
    header = atom(catalog, "resource.timeseries", None)
    del header["value"]; del header["original_value"]
    tz = ZoneInfo(zone)
    header["measurement_period"] = {"start": datetime(year,1,1,tzinfo=tz).isoformat(),
        "end": datetime(year+years,1,1,tzinfo=tz).isoformat(), "timezone": zone,
        "interval_minutes": minutes, "coverage": 1}
    return header


def resource_rows(catalog, year=2025, minutes=60, zone="Asia/Shanghai", years=1):
    tz = ZoneInfo(zone)
    start = datetime(year,1,1,tzinfo=tz).astimezone(timezone.utc)
    finish = datetime(year+years,1,1,tzinfo=tz).astimezone(timezone.utc)
    cursor = start; i = 0
    while cursor < finish:
        local = cursor.astimezone(tz)
        data = {"timestamp": local.isoformat(), "interval_minutes": minutes, "poa": 1000 if 6 <= local.hour < 18 else 0,
            "ambient_temperature": 25, "wind_speed": 1, "quality_flag": "valid", "row_id": f"r{i}"}
        yield {"row_id": f"r{i}", "fields": {"resource.timeseries."+k: atom(catalog, "resource.timeseries."+k, v, f"r{i}-{k}") for k,v in data.items()}}
        cursor += timedelta(minutes=minutes); i += 1


def independent_reference(days=365, category="industrial_rooftop", years=3, allocations=(F(1,2), F(1,2)), event=None):
    """No production calculations. Rational chain + independent libm exp.

    Daylight is exactly twelve hours per day in these artificial Asia/Shanghai
    inputs. Absolute errors from libm exp are bounded separately in assertions.
    """
    factor = F(str(1-4*exp(-4)))
    def physical(q):
        dc = F(100)*q*F(99,100)**4*factor
        ac = sum(min(F(40), dc*fraction*F(98,100)) for fraction in allocations)
        power = ac*F(99,100)
        if category == "utility_scale_ground":
            power = min(power, F(90))*F(99,100)**2
        power = max(F(0), power-F(1,5))*F(99,100)
        if category == "utility_scale_ground":
            power = min(power,F(60))*F(99,100)
        return power
    yearly = []
    q=F(98,100)
    for y in range(years):
        if y:
            q *= F(9,10)
        aged=q
        if event and y+1==event["year"]:
            q = aged*(1-event["fraction"])+event["target"]*event["fraction"]
            duration=event["days"]/days
            power=physical(q)*(1-duration)+physical(aged*(1-event["fraction"]))*duration
        else:
            power=physical(q)
        yearly.append(power*12*days)
    return [D(v.numerator)/D(v.denominator) for v in yearly]
