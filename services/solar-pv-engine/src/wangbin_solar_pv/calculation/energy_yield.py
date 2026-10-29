"""Phase 3B bounded generation orchestration over the approved D2/D3 contracts.

Physical interval means are replayed only under an explicit representative-year
scenario. Each year's DC and each inverter's clipping are recalculated. The
canonical result is the existing Phase 3A result, not a second result format.
"""
from __future__ import annotations

import hashlib
import shutil
from datetime import datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from ..errors import ContractError
from ..serialization import dumps
from ..timeseries_bundle import BundleBudget, _encode
from ..timeseries_private import Meter, local_target, write_file
from .capacity import capacity, validate_rooftop, validate_ground
from .common import precision_context
from .degradation import performance_schedule
from .energy_inputs import EnergyInputs
from .engineering import evaluate
from .input_contract import calculation_identity
from .result_contract import empty_result, seal_result, validate_result, serialize_result
from .solar_resource import intervals, month_parts, monthly_poa, elapsed_hours, _stamp
from .temperature import prepare_temperature

DC_KINDS = ("shading", "soiling", "snow", "mismatch", "dc_cable")
POST_KINDS = ("ac_cable", "transformer", "export_line", "curtailment")


def _calendar_hours(year, timezone_name):
    zone = ZoneInfo(timezone_name)
    return elapsed_hours(datetime(year, 1, 1, tzinfo=zone), datetime(year+1, 1, 1, tzinfo=zone))


def _losses(inputs):
    upstream = inputs.methods.require("energy.upstream_included_losses")
    if set(upstream) - set(DC_KINDS + POST_KINDS):
        raise ContractError("ENERGY_LOSS_UPSTREAM_MODEL_CONFLICT")
    selected = {}
    for row in inputs.rows("system.losses"):
        get = lambda name: inputs.value("system.losses."+name, row=row)
        kind = get("kind")
        if kind in selected or kind not in DC_KINDS + POST_KINDS:
            raise ContractError("ENERGY_LOSS_DUPLICATE_OR_MODELLED")
        boundary = "DC" if kind in DC_KINDS else ("AC" if kind == "ac_cable" else "GRID")
        if get("boundary") != boundary or get("method") != "INDEPENDENT_CONSTANT_RATE" or get("period") != "ALL_OPERATING_YEARS":
            raise ContractError("BLOCKED_METHOD_REVIEW", "system.losses")
        included = get("included_in_source")
        if included != (kind in upstream):
            raise ContractError("ENERGY_LOSS_INCLUSION_MISMATCH")
        record = inputs.record("system.losses.value", row=row)
        selected[kind] = {"id": row["row_id"], "kind": kind, "rate": get("value"),
            "sequence": get("sequence"), "boundary": boundary, "included_in_source": included,
            "source_id": record["source_id"], "field_instance_id": record["field_instance_id"]}
    if set(selected) != set(DC_KINDS + POST_KINDS):
        raise ContractError("BLOCKED_MISSING_INPUT", "system.losses")
    order = DC_KINDS + POST_KINDS
    if [r["kind"] for r in sorted(selected.values(), key=lambda r: r["sequence"])] != list(order):
        raise ContractError("ENERGY_LOSS_PHYSICAL_ORDER")
    if len({r["sequence"] for r in selected.values()}) != len(order):
        raise ContractError("ENERGY_LOSS_PHYSICAL_ORDER")
    return selected


def _apply(power, kind, losses, ledger):
    rec = losses[kind]
    lost = Decimal(0) if rec["included_in_source"] else power*rec["rate"]
    ledger[kind] = lost
    return power-lost


def _state_power(item, design, thermal, inputs, losses, schedule, constants):
    """One year/interval physical chain; all energies follow actual UTC hours."""
    stc, stc_cell, gamma, auxiliary, availability, transformer_limit, grid_limit = constants
    ledger = {}
    ideal = design["dc_kwp"] * item.poa_kw_m2/stc
    # Performance changes DC generation, never an already-clipped annual total.
    after_performance = ideal*schedule["retention"]
    retained_without_outage = ideal*schedule.get("full_retention", schedule["retention"])
    ledger["degradation"] = ideal-retained_without_outage
    ledger["replacement_outage"] = retained_without_outage-after_performance
    dc = after_performance
    for kind in DC_KINDS[:3]:
        dc = _apply(dc, kind, losses, ledger)
    temperature = thermal.evaluate(item.poa_kw_m2, item.ambient_c, item.wind_m_s)
    if temperature["status"] != "CALCULATED":
        raise ContractError("BLOCKED_METHOD_REVIEW", "thermal.method")
    factor = 1+gamma*(temperature["value"]-stc_cell)
    if factor < 0:
        raise ContractError("TEMPERATURE_POWER_FACTOR_DOMAIN")
    ledger["temperature"] = dc*(1-factor)  # negative means a cold-weather gain
    dc *= factor
    for kind in DC_KINDS[3:]:
        dc = _apply(dc, kind, losses, ledger)
    ac = Decimal(0)
    clipping = Decimal(0)
    conversion = Decimal(0)
    groups = []
    for group in design["groups"]:
        group_dc = dc * group["dc_kwp"]/design["dc_kwp"]
        if group["id"] in schedule.get("disabled_inverter_ids", ()):
            ledger["replacement_outage"] += group_dc
            groups.append({"id": group["id"], "dc_kw": group_dc, "converted_kw": Decimal(0),
                           "ac_kw": Decimal(0), "clipping_kw": Decimal(0)})
            continue
        converted = group_dc*group["efficiency"]
        output = min(group["ac_kw"], converted)
        conversion += group_dc-converted
        clipping += converted-output
        ac += output
        groups.append({"id": group["id"], "dc_kw": group_dc, "converted_kw": converted,
                       "ac_kw": output, "clipping_kw": converted-output})
    ledger["inverter"] = conversion
    ledger["clipping"] = clipping
    power = _apply(ac, "ac_cable", losses, ledger)
    ledger["transformer_limit"] = Decimal(0)
    if transformer_limit is not None:
        ledger["transformer_limit"] = max(Decimal(0), power-transformer_limit)
        power -= ledger["transformer_limit"]
    power = _apply(power, "transformer", losses, ledger)
    power = _apply(power, "export_line", losses, ledger)
    ledger["auxiliary"] = min(power, auxiliary)
    power = max(Decimal(0), power-auxiliary)
    available = power*availability
    ledger["availability"] = power-available
    delivered = available
    ledger["export_limit"] = Decimal(0)
    if grid_limit is not None:
        ledger["export_limit"] = max(Decimal(0), delivered-grid_limit)
        delivered -= ledger["export_limit"]
    delivered = _apply(delivered, "curtailment", losses, ledger)
    residual = ideal-delivered-sum(ledger.values(), Decimal(0))
    tolerance = inputs.methods.require("precision.abs_tolerance")
    if abs(residual) > tolerance:
        raise ContractError("ENERGY_CONSERVATION")
    return {"ideal_kw": ideal, "dc_kw": dc, "inverter_ac_kw": ac,
            "available_kw": available, "output_kw": delivered, "losses_kw": ledger,
            "cell_temperature_c": temperature["value"],
            "module_temperature_c": temperature["details"]["module_temp"],
            "groups": groups, "conservation_residual_kw": residual}


def _power(item, design, thermal, inputs, losses, schedule, constants):
    """Exact two-state equivalent scenario, not scaling clipped output.

    With no event dates, the declared downtime fraction is uniformly assigned
    to each interval. BOTH plant states re-evaluate inverter/transformer/export
    constraints. This is explicitly a scenario, never a real outage timeline.
    """
    normal = _state_power(item, design, thermal, inputs, losses, schedule, constants)
    event = schedule["event"]
    if not event or event["downtime_days"] == 0:
        return normal
    fraction = event["downtime_days"]/schedule["year_days"]
    offline = {**schedule, "full_retention": schedule["retention"]}
    if event["scope"] == "MODULES_UNIFORM_FRACTION":
        offline["retention"] = schedule["aged_retention_before_replacement"]*(1-event["capacity_fraction"])
    else:
        offline["disabled_inverter_ids"] = event["inverter_ids"]
    outage = _state_power(item, design, thermal, inputs, losses, offline, constants)
    blend = lambda a, b: a*(1-fraction)+b*fraction
    mixed = {**normal}
    for key in ("ideal_kw", "dc_kw", "inverter_ac_kw", "available_kw", "output_kw", "conservation_residual_kw"):
        mixed[key] = blend(normal[key], outage[key])
    mixed["losses_kw"] = {key: blend(value, outage["losses_kw"][key]) for key,value in normal["losses_kw"].items()}
    mixed["groups"] = [{"id": a["id"], **{key: blend(a[key], b[key]) for key in ("dc_kw", "converted_kw", "ac_kw", "clipping_kw")}}
                       for a,b in zip(normal["groups"],outage["groups"])]
    mixed["replacement_states"] = {"equivalent_downtime_fraction": fraction, "normal": normal, "outage": outage}
    return mixed


def _period(inputs, bundle):
    zone = ZoneInfo(inputs.value("site.timezone"))
    if bundle is not None:
        ds = bundle.manifest["datasets"].get("resource.timeseries")
        if ds is None:
            raise ContractError("BLOCKED_MISSING_INPUT", "resource.timeseries")
        header = ds["header"]
        # Header provenance is not a fake empty resource array.
        if header.get("license_status") in {"UNKNOWN", "DENIED"}:
            raise ContractError("ENERGY_SOURCE_NOT_AUTHORIZED")
        for key, earlier in (("effective_from", False), ("effective_to", True)):
            if header.get(key):
                stamp = header[key][:10]
                if (stamp < inputs.evaluation_date.isoformat()) == earlier and stamp != inputs.evaluation_date.isoformat():
                    raise ContractError("ENERGY_SOURCE_EXPIRED_OR_NOT_EFFECTIVE")
        p = header["measurement_period"]
    else:
        p = inputs.record("resource.timeseries")["measurement_period"]
    start, end = _stamp(p["start"], zone), _stamp(p["end"], zone)
    if p["interval_minutes"] > 60:
        raise ContractError("ENERGY_CLIPPING_RESOLUTION_INSUFFICIENT")
    first, last = start.astimezone(zone), end.astimezone(zone)
    if first != datetime(first.year, 1, 1, tzinfo=zone) or last != datetime(last.year, 1, 1, tzinfo=zone) or last.year <= first.year:
        raise ContractError("ENERGY_COMPLETE_CALENDAR_YEARS_REQUIRED")
    return first.year, last.year, p


class _EvidenceWriter:
    def __init__(self, target, meter):
        self.target, self.meter = target, meter
        self.pending = bytearray()
        self.chunks = []
        self.hash = hashlib.sha256(b"[")
        self.count = 0

    def add(self, row):
        payload = _encode(row, 1024**2)
        if self.count:
            self.hash.update(b",")
        self.hash.update(payload)
        self.count += 1
        if len(self.pending)+len(payload)+1 > 4*1024**2:
            self.flush()
        self.pending.extend(payload+b"\n")

    def flush(self):
        if self.pending:
            self.chunks.append(write_file(self.target/f"interval-{len(self.chunks):05d}.jsonl", bytes(self.pending), self.meter))
            self.pending.clear()

    def finish(self):
        self.flush()
        self.hash.update(b"]")
        return {"row_count": self.count, "canonical_array_hash": self.hash.hexdigest()}


def _metric(result, catalog, mid, value, unit, formula, boundary, period, *, details=None, status="CALCULATED", reason=None):
    evidence = result["evidence"]
    source_ids = set(result["inputs"].get("used_sources", []))
    source_ids.update(p["source_id"] for p in result["source_snapshot"].get("methods", {}).get("parameters", {}).values())
    result["results"]["metrics"].append({"metric_id": mid, "value": value,
        "unit": unit, "status": status, "reason": reason, "boundary_id": boundary,
        "period": period, "scenario_id": result["scenario_id"],
        "input_field_ids": list(result["inputs"].get("used_fields", [])),
        "source_ids": sorted(source_ids), "formula_id": formula,
        "formula_version": catalog.definition_version, "evidence_ids": list(evidence),
        "report_locations": catalog.formulas[formula]["report_chapter_ids"],
        "workbook_locations": [], "rounding_rule": "DECLARED_DECIMAL_NO_DISPLAY_ROUNDING",
        "method_parameter_ids": sorted(result["source_snapshot"].get("methods", {}).get("parameters", {})),
        "upstream_metric_ids": [], "details": details or {}})


def _calculate(exported, methods, *, catalog, output_dir, budget, bundle, category):
    if type(budget) is not BundleBudget:
        raise ContractError("BUNDLE_BUDGET")
    budget.__post_init__()
    meter = Meter(budget)
    inputs = EnergyInputs(exported, methods, catalog)
    meter.input = bundle.stats["input_bytes"] if bundle is not None else len(dumps(inputs.validated.export).encode("utf-8"))
    meter.disk = meter.input
    meter.check()
    (validate_rooftop if category == "industrial_rooftop" else validate_ground)(inputs)
    target = local_target(output_dir)
    try:
        target.mkdir()  # Exclusive. Never remove an existing caller directory.
    except FileExistsError:
        raise ContractError("ENERGY_OUTPUT_EXISTS") from None
    try:
        with precision_context(inputs.methods.require("precision.digits")):
            design = capacity(inputs)
            mode = inputs.methods.require("energy.method")
            losses = _losses(inputs)
            repetition = inputs.methods.require("energy.resource_repetition")
            years = inputs.value("project.evaluation_years")
            if inputs.methods.require("time.horizon_basis") != "OPERATING_YEARS":
                raise ContractError("BLOCKED_METHOD_REVIEW", "time.horizon_basis")
            result = empty_result(project_id=inputs.validated.project.project_id,
                pv_type=inputs.pv_type, evaluation_date=inputs.evaluation_date.isoformat(),
                currency=inputs.value("project.currency"), scenario_id="BASE",
                input_hash="pending", source_snapshot_id="pending",
                baseline_hashes=catalog.baseline_hashes, definition_version=catalog.definition_version,
                definition_hash=catalog.definition_hash)
            writer = _EvidenceWriter(target, meter)
            if mode == "INTERVAL_DC_AC":
                first, last, period = _period(inputs, bundle)
                if repetition == "EXPLICIT_REPRESENTATIVE_SCENARIO":
                    if last-first != 1:
                        raise ContractError("ENERGY_REPRESENTATIVE_YEAR_COUNT")
                    resource_years = [first]*years
                else:
                    if last-first != years:
                        raise ContractError("ENERGY_RESOURCE_YEAR_COUNT")
                    resource_years = list(range(first, last))
                year_hours = [_calendar_hours(y, inputs.value("site.timezone")) for y in resource_years]
                days = [hours/24 for hours in year_hours]
                schedule = performance_schedule(inputs, days)
                thermal = prepare_temperature(inputs.methods)
                if inputs.methods.require("constants.stc_irradiance") != 1 or inputs.methods.require("constants.stc_cell_temperature") != 25:
                    raise ContractError("CONSTANT_DEFINITION")
                auxiliary = inputs.methods.require("energy.auxiliary_kw")
                availability = 1-inputs.numeric("system.unavailability")
                if category == "utility_scale_ground":
                    pf = inputs.numeric("grid.power_factor")
                    transformer = evaluate("F-TRANSFORMER-ACTIVE-LIMIT", {
                        "grid.transformer_capacity": inputs.numeric("grid.transformer_capacity"),
                        "grid.power_factor": pf})["value"]
                    grid_limit = min(inputs.numeric("grid.export_power_limit"), inputs.numeric("grid.available_capacity"))
                else:
                    transformer = grid_limit = None
                    if any(losses[k]["rate"] != 0 for k in ("transformer", "export_line", "curtailment")):
                        raise ContractError("ENERGY_ROOFTOP_PRE_CONSUMPTION_BOUNDARY")
                constants = (Decimal(1), Decimal(25), inputs.numeric("system.temperature_coefficient"),
                             auxiliary, availability, transformer, grid_limit)
                annual = [{"output": Decimal(0), "inverter": Decimal(0), "available": Decimal(0),
                    "poa": Decimal(0), "hours": Decimal(0), "monthly": [Decimal(0)]*12,
                    "losses": {}} for _ in range(years)]
                timezone_name = inputs.value("site.timezone")
                for item in intervals(inputs, bundle=bundle):
                    meter.rows += 1
                    meter.check()
                    local_year = item.start.astimezone(ZoneInfo(timezone_name)).year
                    affected = range(years) if repetition == "EXPLICIT_REPRESENTATIVE_SCENARIO" else [local_year-first]
                    calculations = []
                    parts = list(month_parts(item, timezone_name))
                    for i in affected:
                        state = _power(item, design, thermal, inputs, losses, schedule[i], constants)
                        a = annual[i]
                        a["output"] += state["output_kw"]*item.hours
                        a["inverter"] += state["inverter_ac_kw"]*item.hours
                        a["available"] += state["available_kw"]*item.hours
                        a["poa"] += item.poa_kw_m2*item.hours
                        a["hours"] += item.hours
                        for month, hours in parts:
                            a["monthly"][int(month[-2:])-1] += state["output_kw"]*hours
                        for kind, power in state["losses_kw"].items():
                            a["losses"][kind] = a["losses"].get(kind, Decimal(0))+power*item.hours
                        calculations.append({"operating_year": i+1, "state": state})
                    writer.add({"resource_row_id": item.row_id, "start": item.start.isoformat(),
                        "end": item.end.isoformat(), "hours": item.hours, "poa_kw_m2": item.poa_kw_m2,
                        "source_instance_ids": list(item.source_instance_ids), "source_ids": list(item.source_ids),
                        "calculations": calculations})
                if any(a["hours"] != hours for a, hours in zip(annual, year_hours)):
                    raise ContractError("ENERGY_ANNUAL_COVERAGE")
            else:
                # Monthly PR is a separate measured/assumed boundary; never
                # manufacture clipping or hourly temperatures from these totals.
                if bundle is not None or repetition != "EXPLICIT_REPRESENTATIVE_SCENARIO":
                    raise ContractError("BLOCKED_METHOD_REVIEW", "energy.resource_repetition")
                if inputs.methods.require("thermal.method") != "NOT_REQUIRED_PR":
                    raise ContractError("ENERGY_PR_THERMAL_DUPLICATION")
                supplied = monthly_poa(inputs)
                first = int(supplied[0]["period"][:4])
                pr_hours = _calendar_hours(first, inputs.value("site.timezone"))
                days = [pr_hours/24]*years
                schedule = performance_schedule(inputs, days)
                pr = inputs.methods.require("energy.pr")
                if any(s["event"] and s["event"]["downtime_days"] != 0 for s in schedule):
                    raise ContractError("BLOCKED_METHOD_REVIEW", "assets.replacements.downtime_days")
                if inputs.methods.require("constants.stc_irradiance") != 1:
                    raise ContractError("CONSTANT_DEFINITION")
                # This PR branch is an explicitly identified net AC meter,
                # before dispatch/curtailment. It cannot claim grid delivery.
                if inputs.value("grid.metering_boundary") != "SYSTEM_AVAILABLE_AFTER_AUXILIARY_AVAILABILITY_PRE_CURTAILMENT":
                    raise ContractError("BLOCKED_METHOD_REVIEW", "grid.metering_boundary")
                if (not all(r["included_in_source"] for kind,r in losses.items() if kind != "curtailment")
                        or losses["curtailment"]["included_in_source"]):
                    raise ContractError("ENERGY_PR_LOSS_COVERAGE")
                annual = []
                for i, perf in enumerate(schedule):
                    monthly = [design["dc_kwp"]*m["poa_kwh_m2"]*pr*perf["retention"]*perf["equivalent_availability"] for m in supplied]
                    annual.append({"output": sum(monthly), "monthly": monthly,
                        "poa": sum(m["poa_kwh_m2"] for m in supplied), "hours": pr_hours,
                        "inverter": None, "available": None, "losses": {}})
                period = {"start": f"{first}-01-01", "end_inclusive": f"{first}-12-31"}
                for m in supplied:
                    meter.rows += 1
                    meter.check()
                    writer.add(m)
            # Revalidation includes ALL datasets, complete canonical hashes and
            # full source snapshots before any complete result can be published.
            identity = calculation_identity(inputs.validated, inputs.methods, catalog, datasets=bundle)
            result["input_hash"] = identity["input_hash"]
            result["source_snapshot_id"] = identity["source_snapshot_id"]
            result["source_snapshot"] = identity["source_snapshot"]
            meter.input = bundle.stats["input_bytes"] if bundle is not None else len(dumps(inputs.validated.export).encode("utf-8"))
            meter.check()
            output_identity = writer.finish()
            output_identity["formula_version"] = catalog.definition_version
            output_identity["physical_chain"] = {
                "dc_kw": "F-DC-TIME-POWER", "inverter_ac_kw": "F-AC-INVERTER-POWER",
                "available_kw": "F-AVAILABLE-ENERGY", "poa_kw_m2_times_hours": "F-POA-IRRADIATION",
                "monthly_and_annual_sums": "F-ENERGY-AGGREGATION",
                "retention": "F-PIECEWISE-DEGRADATION" if inputs.methods.require("degradation.method") == "PIECEWISE" else "F-ANNUAL-DEGRADATION"}
            result["inputs"].update(identity_payload=identity["input_identity_payload"],
                method_config_hash=inputs.methods.hash, normalized=inputs.validated.export["normalized_inputs"],
                used_fields=sorted(inputs.used), used_sources=sorted({r["source_id"] for r in inputs.used.values()}))
            result["evidence"] = {"interval-calculations": output_identity,
                "engineering": design, "performance": {"years": schedule},
                "loss-coverage": losses, "input-lineage": inputs.used}
            boundary = "GRID_DELIVERABLE" if category == "utility_scale_ground" else "AVAILABLE_PRE_CONSUMPTION"
            if mode == "POA_PR":
                boundary = "DECLARED_PR_BOUNDARY"
            result["boundaries"] = {boundary: {"resource_period": period,
                "resource_repetition": repetition, "unit": "kWh", "method": mode},
                "DC_NAMEPLATE": {"unit": "kWp"}, "AC_NAMEPLATE": {"unit": "kWac"},
                "INVERTER_AC": {"unit": "kWh", "position": "AFTER_INVERTER_CLIPPING_BEFORE_AC_LOSSES"},
                "SYSTEM_AVAILABLE": {"unit": "kWh", "position": "AFTER_SYSTEM_LOSSES_BEFORE_EXPORT_LIMIT"}}
            result["formula_snapshot"]["engineering_definitions"] = {
                fid: catalog.formulas[fid] for fid in ("F-DC-CAPACITY", "F-AC-CAPACITY", "F-DC-AC-RATIO",
                    "F-POA-IRRADIATION", "F-FIRST-YEAR-ENERGY", "F-LOSS-COMPOSITE", "F-DC-TIME-POWER",
                    "F-AC-INVERTER-POWER", "F-AVAILABLE-ENERGY", "F-ENERGY-AGGREGATION",
                    "F-INITIAL-DEGRADATION", "F-ANNUAL-DEGRADATION", "F-PIECEWISE-DEGRADATION",
                    "F-EXPORT-LIMIT-ENERGY", "F-EQUIVALENT-HOURS", "F-PR-OBSERVED", "F-CAPACITY-FACTOR")}
            result["findings"] = [
                {"code": "NO_REAL_PROJECT_VERIFICATION", "status": "BLOCKED"},
                {"code": "NO_PHASE3C_LOAD_OR_REVENUE_CALCULATIONS", "status": "NOT_IMPLEMENTED"},
                {"code": "INTERVAL_MEAN_NOT_SUBINTERVAL_CLIPPING", "status": "KNOWN_LIMITATION"}]
            if mode == "POA_PR":
                result["boundaries"][boundary]["metering_boundary"] = inputs.value("grid.metering_boundary")
                result["findings"].append({"code": "FIXED_PR_SCENARIO_NOT_EXACT_ANNUAL_CLIPPING_OR_GRID_DELIVERY", "status": "KNOWN_LIMITATION"})
            if repetition == "EXPLICIT_REPRESENTATIVE_SCENARIO":
                result["findings"].append({"code": "REPEATED_RESOURCE_YEAR_NOT_MULTIPLE_OBSERVED_YEARS", "status": "DECLARED_SCENARIO"})
            if any(s["event"] for s in schedule):
                result["findings"].append({"code": "REPLACEMENT_YEAR_START_AND_UNIFORM_DOWNTIME_NOT_REAL_DATES", "status": "DECLARED_SCENARIO"})
            for mid, val, unit, fid, bnd in [
                ("dc_capacity", design["dc_kwp"], "kWp", "F-DC-CAPACITY", "DC_NAMEPLATE"),
                ("ac_capacity", design["ac_kw"], "kWac", "F-AC-CAPACITY", "AC_NAMEPLATE"),
                ("dc_ac_ratio", design["dc_ac_ratio"], "1", "F-DC-AC-RATIO", "DC_NAMEPLATE")]:
                _metric(result, catalog, mid, val, unit, fid, bnd, "NAMEPLATE")
            for i, a in enumerate(annual, 1):
                if abs(sum(a["monthly"])-a["output"]) > inputs.methods.require("precision.abs_tolerance"):
                    raise ContractError("ENERGY_MONTHLY_CONSERVATION")
                _metric(result, catalog, f"energy.year.{i}", a["output"], "kWh", "F-ENERGY-AGGREGATION", boundary, f"OPERATING_YEAR_{i}",
                        details={"monthly_kwh": a["monthly"], "losses_kwh": a["losses"], "resource_year": resource_years[i-1] if mode == "INTERVAL_DC_AC" else first,
                                 "performance": schedule[i-1], "poa_kwh_m2": a["poa"], "actual_hours": a["hours"]})
                _metric(result, catalog, f"energy.monthly.year.{i}", a["monthly"], "kWh", "F-ENERGY-AGGREGATION", boundary, f"OPERATING_YEAR_{i}_MONTHS_1_TO_12")
                for name, val, fid in (("equivalent_hours", a["output"]/design["dc_kwp"], "F-EQUIVALENT-HOURS"),
                        ("capacity_factor", a["output"]/(design["dc_kwp"]*a["hours"]), "F-CAPACITY-FACTOR"),
                        ("pr_observed", None if a["poa"] == 0 else a["output"]/(design["dc_kwp"]*a["poa"]), "F-PR-OBSERVED"),
                        ("inverter_kwh", a["inverter"], "F-AC-INVERTER-POWER"),
                        ("available_kwh", a["available"], "F-AVAILABLE-ENERGY")):
                    _metric(result, catalog, f"{name}.year.{i}", val, "h" if name == "equivalent_hours" else ("kWh" if name.endswith("kwh") else "1"),
                        fid, "INVERTER_AC" if name == "inverter_kwh" else ("SYSTEM_AVAILABLE" if name == "available_kwh" else boundary),
                        f"OPERATING_YEAR_{i}", status="CALCULATED" if val is not None else "UNDEFINED",
                        reason=None if val is not None else "MONTHLY_PR_NO_INTERVAL_BOUNDARY_OR_ZERO_POA")
            annual_values = [a["output"] for a in annual]
            _metric(result, catalog, "energy.annual_array", annual_values, "kWh", "F-ENERGY-AGGREGATION", boundary, "LIFECYCLE")
            _metric(result, catalog, "energy.lifecycle", sum(annual_values), "kWh", "F-ENERGY-AGGREGATION", boundary, "LIFECYCLE")
            _metric(result, catalog, "energy.mean_annual", sum(annual_values)/years, "kWh/year", "F-AVERAGE-ANNUAL-ENERGY", boundary, "LIFECYCLE")
            for mid, fid in (("consumption", "F-SELF-CONSUMPTION"), ("revenue", "F-ENERGY-REVENUE"), ("npv", "F-NPV")):
                _metric(result, catalog, mid, None, None, fid, boundary, "LIFECYCLE", status="NOT_IMPLEMENTED", reason="OUTSIDE_PHASE3B")
            result["results"]["domains"] = {"energy": [m["metric_id"] for m in result["results"]["metrics"] if m["status"] == "CALCULATED"]}
            # Deferred domains remain NOT_IMPLEMENTED; root PARTIAL is truthful
            # even when this generation chain has a complete synthetic solution.
            result["status"] = "PARTIAL"
            result["maturity"]["calculation"] = "CALCULATED_SYNTHETIC" if inputs.methods.data_mode == "SYNTHETIC" else "CALCULATED_CONDITIONAL"
            result = seal_result(result)
            validate_result(result, catalog)
            result_bytes = serialize_result(result, catalog).encode("utf-8")
            write_file(target/"result.pending", result_bytes, meter)
            stats = meter.stats()
            receipt = {"stats": {k: Decimal(str(v)) if isinstance(v, float) else v for k, v in stats.items()},
                "physical_evaluations": meter.rows*years if repetition == "EXPLICIT_REPRESENTATIVE_SCENARIO" else meter.rows,
                "input_rows": meter.rows, "resource_enforcement": "COOPERATIVE_APPLICATION_CHECKPOINTS_NOT_OS_SANDBOX",
                "measurement_scope": "RESULT_DATA_FSYNC_COMPLETE; DISK_INCLUDES_RECEIPT; TIME_AND_MEMORY_SAMPLED_BEFORE_RECEIPT_FSYNC",
                "chunks": writer.chunks, "result_hash": result["result_hash"]}
            # Include the receipt's own bytes without an unbounded self-encoding
            # loop. Only integer digit lengths can change; eight is a hard cap.
            for _ in range(8):
                receipt_bytes = dumps(receipt).encode("utf-8")
                final_disk = meter.disk+len(receipt_bytes)
                if receipt["stats"]["disk_bytes"] == final_disk:
                    break
                receipt["stats"]["disk_bytes"] = final_disk
                receipt["stats"]["peak_disk_reserved_bytes"] = max(stats["peak_disk_reserved_bytes"], final_disk)
            else:
                raise ContractError("ENERGY_RECEIPT_SIZE")
            write_file(target/"receipt.json", receipt_bytes, meter)
            meter.check()
            # Publish the canonical complete result last. Failures anywhere above
            # remove this new private directory, never a pre-existing artifact.
            (target/"result.pending").rename(target/"result.json")
            return result
    except BaseException:
        shutil.rmtree(target)
        raise


def calculate_rooftop(exported, methods, *, catalog, output_dir, budget, bundle=None):
    return _calculate(exported, methods, catalog=catalog, output_dir=output_dir,
                      budget=budget, bundle=bundle, category="industrial_rooftop")


def calculate_ground(exported, methods, *, catalog, output_dir, budget, bundle=None):
    return _calculate(exported, methods, catalog=catalog, output_dir=output_dir,
                      budget=budget, bundle=bundle, category="utility_scale_ground")
