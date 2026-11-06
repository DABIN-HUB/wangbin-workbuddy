"""Distinct 25-year SYNTHETIC Phase 2/D3 preparation; never edits the 3-year smoke.

Usage: python -m tooling.solar_pv_phase7l_full_cases CATEGORY NEW_SCRATCH_DIRECTORY
Then execute the ordinary CLI `project` with the emitted input/methods/budget/
bundle/terminal source and document. The source is a model assumption, not a
permit, executed contract, professional opinion or observed 25-year resource.
"""
from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import sys
import zipfile
from dataclasses import asdict
from decimal import Decimal as D, localcontext
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/solar-pv-engine/src"))

from tooling.solar_pv_synthetic_cases import BASIS, _series, build_input, build_methods
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.categories import category_contract
from wangbin_solar_pv.calculation.input_contract import validate_export
from wangbin_solar_pv.calculation.result_contract import validate_result
from wangbin_solar_pv.calculation.method_config import MethodConfig, make_parameter
from wangbin_solar_pv.intake import IntakeSession
from wangbin_solar_pv.provenance import make_record
from wangbin_solar_pv.serialization import dumps, loads
from wangbin_solar_pv.timeseries_bundle import BundleBudget, write_bundle
from wangbin_solar_pv.validation import validate_project

FIXTURES = ROOT / "services/solar-pv-engine/src/wangbin_solar_pv/fixtures/solar_pv_phase7l_full_cases"
CATEGORIES = ("industrial_rooftop", "utility_scale_ground")


def reconcile_category_obligations(matrix: dict, category: str, catalog: Catalog) -> dict:
    """Correct a catalog-wide audit by the frozen per-category allowed set.

    The read-only audit intentionally iterates catalog pv_types; it does not
    subtract category-specific forbidden IDs/prefixes. Ground export cannot
    enter `tariff.non_avoidable_charges` even though its shared catalog L2
    definition says REQUIRED. Keep both views, never insert forbidden data.
    """
    allowed = set(category_contract(category, catalog)["allowed_field_ids"])
    records = matrix["fields"]
    relevant = [row for row in records if row["applicable"] and row["field_id"] in allowed]
    required = [row for row in relevant if row["effective"]["L2"]["requirement"] == "REQUIRED"]
    missing = [row["field_id"] for row in required if not row["present"] and
               (not row["repeat_parent"] or row["repeat_parent_rows"])]
    pending = [row["field_id"] for row in relevant
               if row["effective"]["L2"]["requirement"] == "PENDING_CONDITION"]
    return {"schema_version": "phase7l-category-effective-obligations/1.0.0",
            "project_type": category, "catalog_definition_count": len(catalog.fields),
            "category_allowed_field_count": len(allowed),
            "category_disallowed_catalog_ids": sorted(row["field_id"] for row in records
                if row["applicable"] and row["field_id"] not in allowed),
            "l2_required_definition_count": len(required),
            "l2_required_present_definition_count": sum(row["present"] for row in required),
            "l2_required_child_without_parent_count": sum(bool(row["repeat_parent"])
                and not row["repeat_parent_rows"] and not row["present"]
                for row in required),
            "l2_missing_effective_ids": missing,
            "l2_pending_condition_ids": pending,
            "note": "A PENDING_CONDITION is not waived. Category-forbidden shared fields cannot be entered; repeated children without a parent do not create fabricated instances."}


def _atom(catalog, category, fid, value, document_hash, instance=None):
    section = ("PROJECT_POST_TAX_NOMINAL_CNY_YEAR_END"
               if fid == "finance.project_discount_rate" else "§ model assumptions")
    kwargs = dict(source_kind="ASSUMPTION", source_id=f"SYNTHETIC-PHASE7L-{category}-v1",
        source_url_or_attachment=f"documents/source-material.md#sha256={document_hash}",
        source_section_or_cell=section, field_instance_id=instance or fid,
        confidence_basis="Fictional authored model input, not observed, signed, approved or independently reviewed",
        location_status="TEXT_FRAGMENT", license_status="AUTHORIZED",
        assumption={"reason": "Explicit fictional 25-year scenario for integration testing only",
                    "method": "Synthetic authored planning scenario; source material § model assumptions",
                    "maturity_ceiling": "L1", "noncritical": False,
                    "decision_invariant": False})
    if "currency" in (catalog.fields[fid]["unit"] or ""):
        kwargs["economic_basis"] = BASIS.copy()
    return make_record(catalog, fid, value, **kwargs)


def _row(catalog, category, group, row_id, values, source_hash):
    fields = {group + "." + key: _atom(catalog, category, group + "." + key, value, source_hash,
                                      f"{group}:{row_id}:{key}") for key, value in {**values, "row_id": row_id}.items()}
    return {"row_id": row_id, "fields": fields}


def _documented_series(catalog, category, fid, legacy, source_hash):
    """Rebind *every* D3 atom to this case's hashed first-year model source.

    The 3D producer retains upstream metric source IDs but its own source
    snapshot only holds the Phase 2 source inventory. Reusing the smoke D3
    source ID would make the otherwise sealed 3D result fail validation.
    """
    upstream = _series(catalog, category, fid, legacy)
    header = _atom(catalog, category, fid, None, source_hash)
    header.pop("value")
    header.pop("original_value")
    header["measurement_period"] = upstream["header"]["measurement_period"]

    def rows():
        for row in upstream["rows"]:
            yield {"row_id": row["row_id"], "fields": {
                key: _atom(catalog, category, key, record["value"], source_hash,
                           record["field_instance_id"])
                for key, record in row["fields"].items()}}

    return {"header": header, "rows": rows()}


def _document(case):
    lines = ["# SYNTHETIC Phase 7L 25-year model source v1.0.0", "",
        "§ model assumptions", "", "Authored 2026-11-06 for offline calculation testing only.",
        "This is not an approval, engineering signoff, real quotation, legal opinion, signed contract,",
        "measured weather record, metered load, actual payment, or tax advice.",
        f"Case identity: {case['project_id']} ({case['pv_type']}).", ""]
    for key in ("site_model", "engineering_model", "commercial_model", "capital_model",
                "operating_model", "constraints"):
        lines.extend((f"## {key}", case[key], ""))
    lines.extend(("## Forecast boundary",
        "PROJECT_POST_TAX_NOMINAL_CNY_YEAR_END is the explicitly authored discounted project-cash boundary.",
        "25 operating years begin 2027-01-01, finish 2051-12-31; 2025 8760-hour weather is a",
        "fictional representative resource year; each operating year is recomputed under the declared",
        "annual 0.8% module degradation and explicit year-13 inverter replacement/downtime method.",
        "All forward collections and expenses are planning assumptions, not bank transactions.",
        "Year-25 no-disposition is explicit: no terminal sale proceeds or disposal taxes;",
        "working capital recovery is already in the 3D ledger, not counted twice.", "",
        "## Professional evidence limitations",
        "Rights, roof structural capacity, fire setback, grid consent, metering, market trading,",
        "geotechnical and flood design remain pending real project verification. Synthetic authored",
        "documents are explicitly classified ASSUMED and cannot pass real-project maturity.", ""))
    return ("\n".join(lines)).encode("utf-8")


def _fields(case, legacy, roof):
    category = case["pv_type"]
    output = {
        "project.evaluation_date": "2026-12-31", "project.evaluation_years": 25,
        "project.cashflow_tax_basis": "post_tax", "project.developer": "FICTIONAL: same model owner",
        "project.operator": "FICTIONAL: same model owner", "project.contact_reference": "SYNTHETIC internal model only",
        "schedule.development_start": "2026-11-06", "schedule.construction_start": "2026-12-01",
        "targets.risk_preference": "balanced", "site.province": "SYNTHETIC unlocated province",
        "site.city": "SYNTHETIC unlocated city", "site.district": "SYNTHETIC unlocated district",
        "site.country": "CN", "site.crs": "SYNTHETIC_LOCAL_SCHEMATIC_NOT_SURVEYED",
        "site.elevation": 30 if roof else 45, "site.terrain_slope": 0 if roof else 2,
        "site.shading_fraction": D("0.025"), "site.rights_holder": "FICTIONAL model owner",
        "site.rights_document_id": "SYNTHETIC-PLANNING-NOTE-NO-TITLE",
        "site.local_restrictions": "Real permits and zoning not examined",
        "site.transport_access": "Concept only; road and lifting access not surveyed",
        "site.disaster_reference": "SYNTHETIC-PLANNING-NOTE-NO-HAZARD-REVIEW",
        "site.ecology_reference": "SYNTHETIC-PLANNING-NOTE-NO-ECOLOGY-CLEARANCE",
        "site.rights_expiry": "2052-12-31", "site.rights_status": "pending",
        "system.dc_capacity": 165 if roof else 330, "system.ac_capacity": 150 if roof else 300,
        "system.dc_ac_ratio": D("1.1"), "system.module_efficiency": D("0.215"),
        "system.module_mass": D("28.5"), "layout.fire_setback": 2 if roof else 3,
        "system.module_model": "SYNTHETIC-550Wp-MODEL-NOT-SUPPLIER",
        "system.inverter_model": "SYNTHETIC-50kW-MODEL" if roof else "SYNTHETIC-100kW-MODEL",
        "system.topology": "FIXED_STRING_INVERTERS", "system.capacity_boundary": "DC_STC_MODULE_NAMEPLATE_TO_AC_INVERTER",
        "resource.dataset_id": f"SYNTHETIC-HOURLY-2025-{category}", "resource.version": "v1.0.0",
        "resource.provider": "Authored offline generator, no observation",
        "resource.model_method": "Constant synthetic daylight POA and temperature; 8760-hour modeled representative year",
        "resource.license_id": "AUTHOR_SYNTHETIC_AUTHORIZED", "resource.tmy_method": "NOT_A_MEASURED_TMY",
        "resource.spatial_resolution": "FICTIONAL_SINGLE_NODE", "resource.time_resolution": "60_minutes",
        "resource.uncertainty_basis": "Not quantified as a meteorological confidence interval",
        "resource.period_start": "2025-01-01", "resource.period_end": "2025-12-31",
        "resource.is_tmy": False, "resource.uncertainty_fraction": D("0.15"),
        "grid.connection_point": "FICTIONAL_NOT_APPROVED_METER_NODE",
        "grid.opinion_attachment_id": "SYNTHETIC-PLANNING-NOTE-NO-GRID-OPINION",
        "grid.permit_reference": "SYNTHETIC-PLANNING-NOTE-NO-PERMIT",
        "grid.transaction_opinion": "No real grid or commercial export approval",
        "grid.protection_plan": "Concept protection only; engineering review pending",
        "grid.upgrade_plan": "No upgrade confirmed; cost exposure unverified",
        "grid.curtailment_basis": "Declared synthetic system losses only; no operating dispatch history",
        "grid.connection_voltage": D("0.4") if roof else D("10"),
        "grid.line_length": D("0.1") if roof else D("1.5"),
        "grid.opinion_status": "pending", "grid.opinion_valid_until": "2051-12-31",
        "grid.curtailment_assumption": 0 if roof else D("0.015"),
        "tariff.market_region": "SYNTHETIC_NO_TRADING_REGION",
        "tariff.policy_reference": "SYNTHETIC-PLANNING-NOTE-NOT-POLICY",
        "tariff.revenue_share_boundary": "100% project-owner modeled benefit; no distribution evidenced",
        "finance.shareholder_cost": D("0.09"), "finance.inflation_rate": D("0.02"),
        "tax.regime_reference": "SYNTHETIC-PLANNING-NOTE-NOT-TAX-OPINION",
        "tax.incentive_reference": "SYNTHETIC-PLANNING-NOTE-NO-INCENTIVES",
        "environment.grid_emission_factor": D("0.55"),
        "environment.factor_period": "SYNTHETIC calculation only, not verified grid factor",
        "environment.fire_reference": "SYNTHETIC-PLANNING-NOTE-NO-FIRE-APPROVAL",
        "environment.approval_reference": "SYNTHETIC-PLANNING-NOTE-NO-PERMIT",
    }
    if roof:
        output.update({"roof.remaining_life": 30, "roof.structure_type": "Fictional industrial steel frame",
            "roof.material": "Modeled standing-seam metal", "roof.age": 5,
            "roof.slope": 10, "roof.azimuth": 180,
            "roof.structure_report_id": "SYNTHETIC-PLANNING-NOTE-NO-STRUCTURAL-SIGNOFF",
            "roof.fire_access_reference": "SYNTHETIC-PLANNING-NOTE-NO-FIRE-APPROVAL",
            "roof.waterproof_plan": "Synthetic clamps and penetration avoidance concept; waterproof warranty pending",
            "site.land_classification": "Existing fictional factory parcel; title not assessed",
            "site.geotechnical_reference": "SYNTHETIC-PLANNING-NOTE-NO-GEOTECH-SIGNOFF",
            "site.flood_reference": "SYNTHETIC-PLANNING-NOTE-NO-FLOOD-ASSESSMENT",
            "load.work_schedule": "Synthetic representative factory operations all days",
            "load.profile_attachment_id": "SYNTHETIC-MODELED-8760H-LOAD-ONLY",
            "load.annual_energy": (legacy["load"]["daylight_kw"] *
                (legacy["resource"]["daylight_end"] - legacy["resource"]["daylight_start"]) +
                legacy["load"]["night_kw"] *
                (24 - legacy["resource"]["daylight_end"] + legacy["resource"]["daylight_start"])) * 365,
        })
    else:
        output.update({"project.ownership_mode": "owner_invested",
            "site.land_classification": "Fictional land-classification scenario, no verification",
            "site.geotechnical_reference": "SYNTHETIC-PLANNING-NOTE-NO-GEOTECH-SIGNOFF",
            "site.flood_reference": "SYNTHETIC-PLANNING-NOTE-NO-FLOOD-ASSESSMENT",
            "grid.power_factor": D("0.95"),
        })
    return output


def prepare(category: str, output: Path):
    if category not in CATEGORIES:
        raise ValueError("PV_CATEGORY_UNKNOWN")
    output = Path(output).resolve()
    if output.exists() or not output.parent.is_dir():
        raise ValueError("Output must be a fresh directory under an existing authorized workspace")
    case = loads((FIXTURES / f"{category}.json").read_bytes())
    if (case["schema_version"] != "solar-pv-phase7l-full-case/1.0.0"
            or case["pv_type"] != category or not case["project_id"].startswith("SYNTHETIC-")):
        raise ValueError("Full-case fixture identity mismatch")
    roof = category == "industrial_rooftop"
    catalog = Catalog()
    legacy, original = build_input(catalog, category)
    session = IntakeSession.from_dict(original["project"], catalog)
    session.project.project_id = case["project_id"]
    document = _document(case)
    source_hash = sha256(document).hexdigest()

    def put(fid, value):
        session.project.values[fid] = _atom(catalog, category, fid, value, source_hash)

    # Existing short-horizon physical geometry and first-year resource shapes are
    # a starting model only. Every sourced record is rebound to this distinct
    # versioned 25-year document and this case's independent Phase 2 identity.
    for fid, record in tuple(session.project.values.items()):
        if record.get("value") is None:
            continue
        value = record["value"]
        if isinstance(value, list) and value and isinstance(value[0], dict) and "fields" in value[0]:
            value = [_row(catalog, category, fid, row["row_id"],
                    {key.removeprefix(fid + "."): atom["value"] for key, atom in row["fields"].items()
                     if atom.get("value") is not None and key != fid + ".row_id"}, source_hash)
                     for row in value]
        put(fid, value)
    for fid, value in _fields(case, legacy, roof).items():
        put(fid, value)
    for fid in ("tariff.contract_id",):
        put(fid, "SYNTHETIC-UNSIGNED-PRICE-SCENARIO-NOT-CONTRACT")
    for fid in ("capex.items", "opex.items", "assets.depreciation", "tariff.periods"):
        rows = session.project.values[fid]["value"]
        for row in rows:
            children = row["fields"]
            def child(key, value):
                full = fid + "." + key
                children[full] = _atom(catalog, category, full, value, source_hash,
                                       f"{fid}:{row['row_id']}:{key}")
            if fid == "capex.items":
                child("quote_attachment_id", "SYNTHETIC-AUTHORED-PRICE-NOTE-NOT-QUOTE")
                child("quote_date", "2026-11-06")
                child("quote_valid_until", "2026-12-31")
            elif fid == "opex.items":
                child("contract_id", "SYNTHETIC-OPERATING-SCENARIO-NOT-CONTRACT")
                child("to_year", 25)
            elif fid == "assets.depreciation":
                child("tax_basis_reference", "SYNTHETIC-TAX-DEPRECIATION-NOT-OPINION")
            else:
                child("effective_to", "2051-12-31")
                child("policy_id", "SYNTHETIC-TARIFF-SCENARIO-NOT-POLICY")
    event_id = "inverters-year13"
    replacement = _row(catalog, category, "assets.replacements", event_id, {
        "asset_id": case["replacement_asset"], "year": case["replacement_year"],
        "cost": case["replacement_cost"], "salvage": 0,
        "downtime_days": case["replacement_downtime_days"],
        "new_life": case["replacement_life"], "performance_reset": "EXPLICIT_METHOD_RULE",
    }, source_hash)
    put("assets.replacements", [replacement])
    items = session.project.values["capex.items"]["value"]
    items.append(_row(catalog, category, "capex.items", event_id, {
        "asset_id": case["replacement_asset"], "category": "inverters",
        "description": "Year-13 SYNTHETIC inverter renewal; planning cost, not supplier quotation",
        "quantity": 3, "quantity_unit": "unit",
        "unit_price": case["replacement_cost"] // 3, "amount": case["replacement_cost"],
        "currency": "CNY", "fx_rate": 1, "tax_included": True,
        "vat_rate": D("0.13"), "recoverable_vat_share": 1,
        "quote_date": "2026-11-06", "quote_valid_until": "2051-12-31",
        "quote_attachment_id": "SYNTHETIC-AUTHORED-PRICE-NOTE-NOT-QUOTE",
        "payment_date": "2039-01-01",
    }, source_hash))
    put("capex.items", items)
    days = [calendar.monthrange(2025, month)[1] for month in range(1, 13)]
    poa = legacy["resource"]["poa_w_m2"]
    daylight = legacy["resource"]["daylight_end"] - legacy["resource"]["daylight_start"]
    monthly = [_row(catalog, category, "resource.monthly", f"m{month:02d}", {
        "month": month, "ghi": D("3.8") * n, "dni": D("2.8") * n,
        "dhi": D("1.0") * n, "poa": D(poa) * daylight * n / 1000,
        "ambient_temperature": legacy["resource"]["ambient_c"],
        "wind_speed": legacy["resource"]["wind_m_s"], "days": n, "coverage": 1,
    }, source_hash) for month, n in enumerate(days, 1)]
    put("resource.monthly", monthly)
    for group in ("system.degradation_segments", "resource.annual_comparison", "policy.applicability",
                  "scenarios.options"):
        put(group, [])
    # There is no independent measured resource reference: a self-comparison
    # with a zero difference would counterfeit annual comparison coverage.
    put("resource.annual_comparison", [])
    put("attachments.register", [_row(catalog, category, "attachments.register",
        "synthetic-model-source-v1", {
            "attachment_id": "SYNTHETIC-MODEL-SOURCE-v1-NOT-THIRD-PARTY",
            "kind": "other", "local_reference": "documents/source-material.md",
            "sha256": source_hash, "license_status": "authorized",
            "remote_upload_consent": False, "sensitivity": "internal",
            "retention_until": "2052-12-31", "document_date": "2026-11-06",
        }, source_hash)])
    # Risk and dated task inventories make unresolved real-world gates explicit.
    put("risk.items", [_row(catalog, category, "risk.items", "unverified-rights", {
        "risk_id": "unverified-rights", "category": "DOCUMENTARY",
        "description": "Real site rights and engineering approvals not supplied",
        "severity": "major", "evidence_state": "pending", "owner": "Fictional project sponsor",
        "deadline": "2027-01-01", "trigger": "Before real investment approval",
        "mitigation": "Obtain legally valid title and professional engineering review",
    }, source_hash)])
    errors = [i.to_dict() for i in validate_project(session.project, catalog) if i.severity == "ERROR"]
    if errors:
        raise ValueError(f"Full-case Phase 2 errors: {errors[:8]}")
    exported = session.export()
    validate_export(exported, catalog)
    values = build_methods(category, legacy).to_dict()
    parameters = values["parameters"]
    replacements = {
        "cash.collection_fractions": [1] * 25,
        "cash.opex_payment_fractions": [1] * 25,
        "cash.tax_payment_fractions": [1] * 25,
        "cash.vat_payment_fractions": [1] * 25,
        "cash.capex_payment_fractions": [1] + [0] * 25,
        "replacement.method": "EXPLICIT_ASSET_EVENTS",
        "degradation.performance_ceiling": 1,
        "replacement.rules": [{"event_id": event_id, "scope": "INVERTERS_UNIFORM_FRACTION",
            "capacity_fraction": 1, "target_retention": None,
            "timing": "YEAR_START_RECOVERY_UNIFORM_EQUIVALENT_DOWNTIME",
            "inverter_ids": ["inv-1", "inv-2", "inv-3"]}],
        "irr.method": "EXACT_RATIONAL_POLYNOMIAL_ISOLATION", "irr.minimum_rate": D("-0.9"),
        "irr.maximum_rate": 5, "irr.root_tolerance": D("0.000000000001"),
        "irr.maximum_degree": 25,
    }
    for pid, value in replacements.items():
        parameters[pid] = make_parameter(pid, value,
            source_id=f"SYNTHETIC-PHASE7L-{category}-v1",
            source_reference=f"documents/source-material.md#sha256={source_hash}; planning only",
            source_kind="SYNTHETIC", status="ASSUMED", license_status="AUTHORIZED")
    values["config_id"] = f"SYNTHETIC-PHASE7L-25Y-{category}-v1"
    for pid, entry in parameters.items():
        if pid in replacements:
            continue
        entry["source_id"] = f"SYNTHETIC-PHASE7L-{category}-v1"
        entry["source_reference"] = f"documents/source-material.md#sha256={source_hash}; planning only"
    methods = MethodConfig.from_dict(values)
    # The source document is byte-checked by the ordinary CLI, not represented
    # by an editorial note or a blank terminal value.
    terminal_date = "2051-12-31"
    assets = sorted({row["fields"]["capex.items.asset_id"] for row in exported["normalized_inputs"]["capex.items"]})
    terminal_bytes = (f"SYNTHETIC no-disposition forecast v1.0.0; project_id={case['project_id']} "
        f"terminal_date={terminal_date}\n" + "\n".join(f"asset_id={a}" for a in assets) +
        "\nno additional recovery; tax_treatment=NO_DISPOSITION_TAX; "
        "working_capital_treatment=LEDGER_ALREADY_RECOVERED\n"
        "Not an approval, legal opinion, actual payment or asset-disposition contract.\n").encode("utf-8")
    terminal_source = {"source_id": f"SYNTHETIC-PHASE7L-{category}-terminal-v1",
        "source_kind": "SYNTHETIC", "source_reference": "terminal.txt#sha256=" + sha256(terminal_bytes).hexdigest(),
        "source_section_or_cell": "no additional recovery", "source_excerpt": "no additional recovery",
        "source_content_sha256": sha256(terminal_bytes).hexdigest(),
        "source_status": "ASSUMED", "economic_status": "SYNTHETIC_ASSUMPTION",
        "source_timestamp": "2026-12-31", "effective_from": "2026-12-31",
        "effective_to": terminal_date, "reviewer": "SYNTHETIC-only", "license_status": "AUTHORIZED"}
    terminal = {"project_id": case["project_id"], "pv_type": category,
        "evaluation_date": "2026-12-31", "terminal_date": terminal_date,
        "currency": "CNY", "mode": "NO_DISPOSITION", "covered_asset_ids": assets,
        "events": [], "no_disposition": {"covered_asset_ids": assets,
            "reason": "no additional recovery", "tax_treatment": "NO_DISPOSITION_TAX",
            "working_capital_treatment": "LEDGER_ALREADY_RECOVERED", "source": terminal_source}}
    budget = BundleBudget(max_input_bytes=512 * 1024**2, max_disk_bytes=1024**3,
        max_rows=30000, max_seconds=1800, max_memory_bytes=1024**3)
    output.mkdir(mode=0o700)
    (output / "documents").mkdir()
    (output / "documents/source-material.md").write_bytes(document)
    (output / "terminal.txt").write_bytes(terminal_bytes)
    for name, payload in (("input.json", exported), ("methods.json", methods.to_dict()),
                          ("budget.json", asdict(budget)), ("terminal.json", terminal)):
        (output / name).write_text(dumps(payload), encoding="utf-8")
    fields = ("resource.timeseries", "load.series") if roof else ("resource.timeseries", "tariff.market_series")
    manifest = write_bundle(output / "bundle", base_export=exported,
        datasets={fid: _documented_series(catalog, category, fid, legacy, source_hash) for fid in fields},
        catalog=catalog, budget=budget, rows_per_chunk=256)
    return {"project_id": case["project_id"], "phase2_input_hash": exported["input_hash"],
            "d3_content_hash": manifest["content_hash"], "source_sha256": source_hash,
            "terminal_sha256": sha256(terminal_bytes).hexdigest(),
            "d3_rows": {key: row["row_count"] for key, row in manifest["datasets"].items()},
            "run_command": f"python services/solar-pv-engine/solar_pv.py --workspace {output} project --input input.json --methods methods.json --budget budget.json --bundle bundle --terminal-source terminal.json --terminal-document terminal.txt --output project"}


def verify_delivery(case_dir: Path) -> dict:
    """Replay immutable archive/manifest, receipt and independent finance checks.

    No extraction or new project run is required for this read-only check.
    Recomputing the ordinary pipeline is documented separately in REPRODUCE.md.
    """
    case_dir = case_dir.resolve()
    def digest(path):
        h = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()

    def verify_entry(entry, reader):
        h = hashlib.sha256()
        size = 0
        for chunk in iter(lambda: reader.read(1024 * 1024), b""):
            h.update(chunk)
            size += len(chunk)
        assert size == entry["bytes"] and h.hexdigest() == entry["sha256"], entry["path"]

    current = json.loads((case_dir / "file-manifest.json").read_bytes())["files"]
    current_paths = {entry["path"] for entry in current}
    assert len(current_paths) == len(current)
    assert current_paths == {p.relative_to(case_dir).as_posix() for p in case_dir.rglob("*")
                             if p.is_file() and p.name != "file-manifest.json"}
    for entry in current:
        with (case_dir / entry["path"]).open("rb") as stream:
            verify_entry(entry, stream)
    expanded = json.loads((case_dir / "expanded-file-manifest.json").read_bytes())["files"]
    with zipfile.ZipFile(case_dir / "archived-d3-and-intervals.zip") as archive:
        names = set(archive.namelist())
        assert len(names) == len(archive.namelist())
        assert names <= {e["path"] for e in expanded}
        for entry in expanded:
            if entry["path"] in names:
                with archive.open(entry["path"]) as stream:
                    verify_entry(entry, stream)
            else:
                with (case_dir / entry["path"]).open("rb") as stream:
                    verify_entry(entry, stream)

    catalog = Catalog()
    exported = loads((case_dir / "input.json").read_bytes())
    canonical = loads((case_dir / "project/canonical.json").read_bytes())
    receipt = loads((case_dir / "project/receipt.json").read_bytes())
    three_b = loads((case_dir / "project/3b/result.json").read_bytes())
    three_d = loads((case_dir / "project/3d/result.json").read_bytes())
    for result in (canonical, three_b, three_d):
        validate_result(result, catalog)
    validate_export(exported, catalog)
    assert receipt["phase2_input_hash"] == exported["input_hash"]
    assert canonical["result_hash"] == receipt["canonical_result_hash"]
    assert receipt["stages"]["3B"]["result_hash"] == three_b["result_hash"]
    assert receipt["stages"]["3D"]["result_hash"] == three_d["result_hash"]
    for key, stage in (("3C", "3c"), ("3E", "3e")):
        result = loads((case_dir / f"project/{stage}/result.json").read_bytes())
        validate_result(result, catalog)
        assert receipt["stages"][key]["result_hash"] == result["result_hash"]
    assert canonical["source_snapshot"]["phase3e_terminal"]["source"]["no_disposition"]["source"]["source_content_sha256"] == digest(case_dir / "terminal.txt")
    assert any(row.get("source_url_or_attachment", "").endswith(digest(case_dir / "documents/source-material.md"))
               for row in exported["source_snapshot"]["records"])
    manifest = json.loads((case_dir / "bundle/manifest.json").read_bytes())
    assert all(row["row_count"] == 8760 for row in manifest["datasets"].values())
    assert receipt["source_snapshot_id"] == canonical["source_snapshot_id"]
    matrix_bytes = (case_dir / "actual-effective-obligation-matrix.json").read_bytes()
    matrix = json.loads(matrix_bytes)
    assert len(matrix["fields"]) == 469 and matrix["d3_validation"] == "ALL_ATOMS_VALIDATED"
    reconciled = reconcile_category_obligations(matrix, receipt["pv_type"], catalog)
    effective = json.loads((case_dir / "category-effective-obligations.json").read_bytes())
    assert all(effective[key] == val for key, val in reconciled.items())
    assert effective["matrix_sha256"] == hashlib.sha256(matrix_bytes).hexdigest()
    annual = {m["metric_id"]: m for m in three_b["results"]["metrics"]}["energy.annual_array"]["value"]
    assert len(annual) == 25 and len(set(annual)) == 25
    assert all(annual[y] < annual[y-1] for y in range(1, 25) if y != 13)
    assert annual[13] > annual[12]  # year 14 recovery after modeled year-13 downtime
    performance = three_b["evidence"]["performance"]["years"]
    assert len(performance) == 25
    with localcontext() as ctx:
        ctx.prec = 80
        retention = D("0.985")
        for year, row in enumerate(performance, 1):
            if year > 1:
                retention *= D("0.992")
            assert abs(row["retention"] - retention) < D("1e-50")
            assert abs(row["equivalent_availability"] -
                       (1 - D(6) / D(row["year_days"]) if year == 13 else D(1))) < D("1e-50")
        ledger = three_d["evidence"]["financial-ledger"]["annual"]
        cash = [-(ledger[0]["capex_cash_paid"] + ledger[0]["working_capital_increase"])]
        for row in ledger[1:]:
            cash.append(row["revenue_cash_receipts"] + row["self_use_avoided_expenditure"] -
                        row["opex_cash_paid"] - row["cash_tax_total_project"] -
                        row["capex_cash_paid"] - row["working_capital_increase"] + row["working_capital_release"])
        metrics = {m["metric_id"].removeprefix("financial.phase3e."): m
                   for m in canonical["results"]["metrics"]
                   if m["metric_id"].startswith("financial.phase3e.")}
        assert len(cash) == 26 and all(abs(x - y) < D("1e-16")
                                      for x, y in zip(cash, metrics["project_cash_flow"]["value"]))
        rate = D(canonical["source_snapshot"]["phase3e_terminal"]["rate_source"]["value"])
        npv = sum((amount / (1 + rate)**year for year, amount in enumerate(cash)), D(0))
        assert abs(npv - metrics["project_npv"]["value"]) < D("1e-16")
        irr = metrics["project_irr"]
        assert irr["status"] == "CALCULATED"
        residual = sum((amount / (1 + irr["value"])**year for year, amount in enumerate(cash)), D(0))
        assert abs(residual) < D("0.0001")
        accumulated = D(0)
        discounted = D(0)
        static_year = dynamic_year = None
        for year, amount in enumerate(cash):
            previous, previous_discounted = accumulated, discounted
            accumulated += amount
            discounted += amount / (1 + rate)**year
            if year and static_year is None and previous < 0 <= accumulated:
                static_year = year - 1 - previous / amount
            if year and dynamic_year is None and previous_discounted < 0 <= discounted:
                dynamic_year = year - 1 - previous_discounted / (amount / (1 + rate)**year)
        assert abs(metrics["static_payback"]["value"] - static_year) < D("1e-16")
        assert abs(metrics["dynamic_payback"]["value"] - dynamic_year) < D("1e-16")
    return {"category": receipt["pv_type"], "status": receipt["status"],
            "project_id": receipt["project_id"], "phase2_input_hash": exported["input_hash"],
            "source_snapshot_id": receipt["source_snapshot_id"],
            "d3_content_hash": manifest["content_hash"],
            "canonical_result_hash": canonical["result_hash"],
            "file_count": len(current), "archived_file_count": len(names),
            "catalog_fields": len(matrix["fields"]),
            "l2_missing_category_effective_ids": effective["l2_missing_effective_ids"],
            "l2_pending_condition_count": len(effective["l2_pending_condition_ids"]),
            "real_project_maturity": matrix["real_project_maturity"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("category", choices=(*CATEGORIES, "verify"))
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(dumps(verify_delivery(args.output) if args.category == "verify"
                else prepare(args.category, args.output)))


if __name__ == "__main__":
    main()
