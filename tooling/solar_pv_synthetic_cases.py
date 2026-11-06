"""Build fresh, explicitly fictional Phase 2 -> D3 -> 3G PV calculation cases.

Usage: python -m tooling.solar_pv_synthetic_cases industrial_rooftop OUTPUT_DIRECTORY
OUTPUT_DIRECTORY must not exist. This is a bounded, low-coverage, three-year
demonstration, NOT a high-coverage Phase 7L project. Nothing here is a permit,
signed study, quote, measured weather/load, loan agreement, verified tariff,
tax opinion, actual payment, or investment approval.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/solar-pv-engine/src"))

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.calculation.input_contract import validate_export
from wangbin_solar_pv.calculation.method_config import MethodConfig, make_parameter
from wangbin_solar_pv.calculation.project_runner import run_project
from wangbin_solar_pv.calculation.result_contract import validate_result
from wangbin_solar_pv.intake import IntakeSession
from wangbin_solar_pv.local_files import Workspace
from wangbin_solar_pv.provenance import make_record
from wangbin_solar_pv.serialization import dumps, loads
from wangbin_solar_pv.timeseries_bundle import BundleBudget, write_bundle
from wangbin_solar_pv.validation import validate_project

FIXTURES = ROOT / "services/solar-pv-engine/src/wangbin_solar_pv/fixtures/solar_pv_calculation"
ZONE = ZoneInfo("Asia/Shanghai")
BASIS = {"currency": "CNY", "price_year": 2025, "tax_basis": "inclusive", "price_basis": "nominal"}

COMMON = {
    "project.evaluation_date": "2026-11-06", "project.evaluation_years": 3,
    "project.currency": "CNY", "project.has_storage": False, "project.price_basis": "nominal",
    "project.cashflow_tax_basis": "both", "site.timezone": "Asia/Shanghai",
    "schedule.commissioning_date": "2027-01-01",
    "system.module_length": Decimal("2.1"), "system.module_width": Decimal("1.1"),
    "system.module_voc": 50, "system.module_vmp": 41,
    "system.module_isc": 14, "system.module_imp": 13,
    "system.inverter_max_dc_voltage": 1100, "system.inverter_mppt_min": 400,
    "system.inverter_efficiency": Decimal("0.98"),
    "system.temperature_coefficient": Decimal("-0.0037"),
    "system.mounting_type": "FIXED", "system.first_year_degradation": Decimal("0.015"),
    "system.annual_degradation": Decimal("0.008"), "system.unavailability": Decimal("0.012"),
    "layout.tilt": 18, "layout.azimuth": 180,
    "layout.string_validation_reference": "SYNTHETIC STC string arithmetic only; unsigned cold/hot design review pending",
    "resource.poa_boundary": "ARRAY_PLANE_INTERVAL_MEAN",
    "tariff.transaction_fee": Decimal("0.012"),
    "revenue.other_items": [],
    "capex.contingency_rate": Decimal("0.04"),
    "capex.estimate_basis": "SYNTHETIC item costs; no supplier quotations or approved budget",
    "capex.includes_construction_interest": False, "capex.includes_land": False,
    "capex.includes_storage": False,
    "finance.debt_ratio": 0, "finance.working_capital": 12000,
    "finance.project_discount_rate": Decimal("0.075"),
    "finance.equity_discount_rate": Decimal("0.09"),
    "finance.cashflow_timing": "PERIOD_END",
    "finance.cfads_definition": "OPERATING_CASH_AFTER_TAX_MANDATORY_CAPEX",
    "tax.corporate_income_rate": Decimal("0.25"),
    "tax.vat_output_rate": Decimal("0.13"),
    "tax.surcharge_rate": Decimal("0.12"),
    "tax.surcharge_basis": "INCOME_TAX_ACCRUAL",
    "tax.loss_carryforward_years": 5,
    "tax.vat_recovery_timing": "PERIOD_OF_ELIGIBLE_INPUT",
}


def _record(catalog, category, fid, value, instance=None):
    metadata = dict(source_id=f"SYNTHETIC-CALC-{category}",
        source_url_or_attachment=("SYNTHETIC:tooling/solar_pv_synthetic_cases.py"
            f"+fixtures/solar_pv_calculation/{category}.json"),
        source_section_or_cell=instance or fid, field_instance_id=instance or fid,
        confidence_basis="Fictional author-declared scenario; not observed or independently verified",
        location_status="TEXT_FRAGMENT", license_status="AUTHORIZED",
        assumption={"reason": "Fictional scenario, no measurements, contracts or approvals",
                    "method": "Explicit synthetic calculation fixture with authored units",
                    "maturity_ceiling": "L1", "noncritical": False,
                    "decision_invariant": False})
    if "currency" in (catalog.fields[fid]["unit"] or ""):
        metadata["economic_basis"] = BASIS.copy()
    return make_record(catalog, fid, value, source_kind="ASSUMPTION", **metadata)


def _missing_document(catalog, fid, instance=None):
    """Record an absent document as UNKNOWN, never as a fictional attachment ID."""
    return make_record(catalog, fid, None, source_kind="UNKNOWN",
        field_instance_id=instance or fid,
        confidence_basis="No third-party document, contract, quote, or reviewed tax basis was supplied",
        missing_reason="Real documentary evidence is required; the synthetic model is not a substitute")


DOCUMENT_CHILD_FIELDS = frozenset({
    "capex.items.quote_attachment_id", "assets.depreciation.tax_basis_reference",
    "opex.items.contract_id",
})


def _rows(catalog, category, group, descriptions):
    rows = []
    for row_id, values in descriptions:
        fields = {group + "." + key: (
            _missing_document(catalog, group + "." + key, f"{group}:{row_id}:{key}")
            if group + "." + key in DOCUMENT_CHILD_FIELDS else
            _record(catalog, category, group + "." + key, value, f"{group}:{row_id}:{key}"))
            for key, value in {**values, "row_id": row_id}.items()}
        rows.append({"row_id": row_id, "fields": fields})
    return rows


def _finance_rows(category):
    roof = category == "industrial_rooftop"
    items = [("modules", 300 if roof else 600, 700),
             ("inverters", 3, 24000 if roof else 45000),
             ("mounting", 1, 90000 if roof else 220000),
             ("construction", 1, 95000 if roof else 175000)]
    capex, depreciation = [], []
    for asset, quantity, unit_price in items:
        asset_id = f"scenario-{asset}"
        capex.append((asset_id, {"asset_id": asset_id, "category": asset,
            "description": f"SYNTHETIC modeled {asset}, no quotation", "quantity": quantity,
            "quantity_unit": "unit", "unit_price": unit_price, "amount": quantity * unit_price,
            "currency": "CNY", "fx_rate": 1, "tax_included": True, "vat_rate": Decimal("0.13"),
            "recoverable_vat_share": 1, "quote_attachment_id": None,
            "payment_date": "2026-12-01"}))
        depreciation.append((asset_id, {"asset_id": asset_id, "asset_class": asset,
            "depreciable_basis": Decimal(quantity * unit_price) / Decimal("1.13"),
            "residual_value": Decimal(quantity * unit_price) / Decimal("22.6"),
            "depreciation_years": 10 if asset != "inverters" else 8,
            "in_service_date": "2027-01-01", "method": "straight_line",
            "tax_basis_reference": None}))
    opex = [("maintenance", {"category": "maintenance", "base_amount": 7200 if roof else 15000,
        "contract_id": None, "escalation_rate": Decimal("0.02"),
        "from_year": 1, "to_year": 3, "tax_included": True, "vat_rate": Decimal("0.06"),
        "recoverable_vat_share": 1}),
        ("insurance", {"category": "insurance", "base_amount": 3800 if roof else 9500,
        "contract_id": None, "escalation_rate": Decimal("0.02"),
        "from_year": 1, "to_year": 3, "tax_included": True, "vat_rate": Decimal("0.06"),
        "recoverable_vat_share": 1})]
    return capex, depreciation, opex


def build_input(catalog, category):
    case = loads((FIXTURES / f"{category}.json").read_bytes())
    if case["pv_type"] != category or case["schema_version"] != "solar-pv-synthetic-case/1.0.0":
        raise ValueError("Synthetic case fixture identity mismatch")
    session = IntakeSession.new(case["project_id"], category, catalog)
    fields = {**COMMON, **case["fields"], "project.pv_type": category}
    fields["system.inverter_mppt_max"] = 900
    for fid, value in fields.items():
        session.project.values[fid] = _record(catalog, category, fid, value)
    for fid in ("tax.regime_reference", "tax.incentive_reference"):
        session.project.values[fid] = _missing_document(catalog, fid)
    roof = category == "industrial_rooftop"
    losses = []
    for seq, (kind, value) in enumerate((
        ("shading", Decimal("0.025")), ("soiling", Decimal("0.018")),
        ("snow", 0), ("mismatch", Decimal("0.012")), ("dc_cable", Decimal("0.01")),
        ("ac_cable", Decimal("0.009")), ("transformer", 0 if roof else Decimal("0.012")),
        ("export_line", 0 if roof else Decimal("0.006")),
        ("curtailment", 0 if roof else Decimal("0.015")))):
        losses.append((kind, {"kind": kind, "value": value, "sequence": seq,
            "boundary": "DC" if seq < 5 else ("AC" if seq == 5 else "GRID"),
            "included_in_source": False, "method": "INDEPENDENT_CONSTANT_RATE",
            "period": "ALL_OPERATING_YEARS"}))
    session.project.values["system.losses"] = _record(catalog, category, "system.losses", _rows(catalog, category, "system.losses", losses))
    periods = []
    for period in case["tariff_periods"]:
        row_id = period["row_id"]
        periods.append((row_id, {**period, "effective_from": "2025-01-01",
            "effective_to": "2030-12-31", "season": "ALL", "weekday_rule": "ALL",
            "period_label": row_id, "tax_included": True, "vat_rate": Decimal("0.13"),
            # The frozen tariff adapter requires a non-null policy_id even for
            # modeled price tables. This explicit sentinel is NOT a policy ID.
            "policy_id": "NO_POLICY_EXISTS__SYNTHETIC_PRICE_TABLE_ONLY"}))
        periods[-1][1].pop("row_id")
    session.project.values["tariff.periods"] = _record(catalog, category, "tariff.periods", _rows(catalog, category, "tariff.periods", periods))
    capex, dep, opex = _finance_rows(category)
    for fid, rows in (("capex.items", capex), ("assets.depreciation", dep), ("opex.items", opex)):
        session.project.values[fid] = _record(catalog, category, fid, _rows(catalog, category, fid, rows))
    session.project.values["assets.replacements"] = _record(catalog, category, "assets.replacements", [])
    session.project.values["finance.debt_schedule"] = _record(catalog, category, "finance.debt_schedule", [])
    errors = [issue.to_dict() for issue in validate_project(session.project, catalog) if issue.severity == "ERROR"]
    if errors:
        raise ValueError(f"Synthetic Phase 2 source invalid: {errors[:3]}")
    export = session.export()
    validate_export(export, catalog)
    return case, export


def build_methods(category, case):
    values = loads((FIXTURES / "method_values.json").read_bytes())["values"]
    values["consumption.commercial_export_limit_kw"] = case["commercial_export_limit_kw"]
    if category == "utility_scale_ground":
        values.update({"consumption.load_repetition": "NO_LOAD_GROUND",
            "settlement.price_source": "MARKET_SERIES", "settlement.revenue_method": "EXPORT_ONLY",
            "cash.self_use_treatment": "CONTRACT_PPA", "tax.self_use_basis": "TAXABLE_INCREMENTAL_SAVING",
            "energy.auxiliary_kw": Decimal("3.0")})
    config = {"schema_version": "solar-pv-method-config/1.0.0",
        "config_id": f"SYNTHETIC-CALC-{category}-MODELED-UNAPPROVED",
        "data_mode": "SYNTHETIC", "pv_types": [category],
        "parameters": {pid: make_parameter(pid, value, source_id=f"SYNTHETIC-CALC-{category}",
            source_reference=("SYNTHETIC:tooling/solar_pv_synthetic_cases.py"
                f"+fixtures/solar_pv_calculation/method_values.json+{category}.json; unapproved"),
            source_kind="SYNTHETIC", status="ASSUMED", license_status="AUTHORIZED")
            for pid, value in values.items()}}
    return MethodConfig.from_dict(config)


def _series(catalog, category, field, case):
    start = datetime(2025, 1, 1, tzinfo=ZONE)
    end = datetime(2026, 1, 1, tzinfo=ZONE)
    period = {"start": start.isoformat(), "end": end.isoformat(),
        "timezone": "Asia/Shanghai", "interval_minutes": 60, "coverage": 1}
    header = _record(catalog, category, field, None)
    header.pop("value"); header.pop("original_value")
    header["measurement_period"] = period

    def rows():
        current = start.astimezone(timezone.utc)
        finish = end.astimezone(timezone.utc)
        n = 0
        while current < finish:
            local = current.astimezone(ZONE)
            daylight = case["resource"]["daylight_start"] <= local.hour < case["resource"]["daylight_end"]
            values = {"timestamp": local.isoformat(), "interval_minutes": 60, "row_id": f"{field.split('.')[0]}-{n}"}
            if field == "resource.timeseries":
                values.update(poa=case["resource"]["poa_w_m2"] if daylight else 0,
                    ambient_temperature=case["resource"]["ambient_c"],
                    wind_speed=case["resource"]["wind_m_s"], quality_flag="valid")
            elif field == "load.series":
                values.update(energy=case["load"]["daylight_kw"] if daylight else case["load"]["night_kw"],
                    quality_flag="valid")
            else:
                market = case["market"]
                price = (market["midday_price"] if market["midday_start"] <= local.hour < market["midday_end"]
                    else market["day_price"] if daylight else market["night_price"])
                values.update(sale_price=price, transaction_fee=market["transaction_fee"])
            yield {"row_id": values["row_id"], "fields": {
                field + "." + key: _record(catalog, category, field + "." + key, value,
                    f"{field}:{n}:{key}") for key, value in values.items()}}
            current += timedelta(hours=1)
            n += 1
    return {"header": header, "rows": rows()}


def run(category, output):
    target = Path(output).resolve()
    if target.exists() or not target.parent.is_dir():
        raise ValueError("Output must be a new child of an existing private scratch directory")
    catalog = Catalog()
    case, export = build_input(catalog, category)
    methods = build_methods(category, case)
    budget = BundleBudget(max_input_bytes=512 * 1024**2, max_disk_bytes=1024**3,
                          max_rows=30000, max_seconds=1800, max_memory_bytes=1024**3)
    target.mkdir(mode=0o700)
    (target / "input.json").write_text(dumps(export), encoding="utf-8")
    (target / "methods.json").write_text(dumps(methods.to_dict()), encoding="utf-8")
    (target / "budget.json").write_text(dumps(asdict(budget)), encoding="utf-8")
    datasets = {fid: _series(catalog, category, fid, case) for fid in (
        ("resource.timeseries", "load.series") if category == "industrial_rooftop"
        else ("resource.timeseries", "tariff.market_series"))}
    manifest = write_bundle(target / "bundle", base_export=export, datasets=datasets,
                            catalog=catalog, budget=budget, rows_per_chunk=256)
    receipt = run_project(export, methods, bundle_dir=target / "bundle", catalog=catalog,
        budget=budget, workspace=Workspace(target), run_id="project")
    canonical = loads((target / "project/canonical.json").read_bytes())
    validate_result(canonical, catalog)
    if receipt["canonical_result_hash"] != canonical["result_hash"]:
        raise ValueError("Canonical/receipt identity mismatch")
    blocked = {m["metric_id"]: m.get("details", {}).get("missing_field_ids", [])
               for m in canonical["results"]["metrics"] if m["status"] == "BLOCKED_MISSING_INPUT"}
    summary = {"project_id": case["project_id"], "pv_type": category,
        "scenario_class": "BOUNDED_LOW_COVERAGE_SYNTHETIC_DEMO_NOT_PHASE7L",
        "decision_ready": False, "evaluation_years": case["fields"].get("project.evaluation_years", COMMON["project.evaluation_years"]),
        "phase2_root_fields_present": sum(r["value"] is not None for r in export["source_snapshot"]["records"]
            if r["field_instance_id"] == r["field_id"] and r["field_id"] in export["normalized_inputs"]),
        "l2_required_definitions": sum(category in f["pv_types"] and f["required_level"]["L2"] == "REQUIRED"
            for f in catalog.fields.values()),
        "coverage_note": "Root field count is not L2 instance coverage; documentary approvals and financial events remain missing.",
        "phase2_input_hash": export["input_hash"], "d3_content_hash": manifest["content_hash"],
        "d3_rows": {fid: row["row_count"] for fid, row in manifest["datasets"].items()},
        "run_id": canonical["run_id"], "input_hash": canonical["input_hash"],
        "source_snapshot_id": canonical["source_snapshot_id"], "result_hash": canonical["result_hash"],
        "receipt_hash": receipt["receipt_hash"], "status": canonical["status"],
        "metric_statuses": dict(Counter(m["status"] for m in canonical["results"]["metrics"])),
        "blocked_missing_fields": blocked, "path": str(target / "project")}
    (target / "synthetic-run-summary.json").write_text(dumps(summary), encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("category", choices=("industrial_rooftop", "utility_scale_ground"))
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(dumps(run(args.category, args.output)))


if __name__ == "__main__":
    main()
