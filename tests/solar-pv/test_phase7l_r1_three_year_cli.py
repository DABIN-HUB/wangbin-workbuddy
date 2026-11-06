"""Slow but real three-year SYNTHETIC ordinary CLI finance smoke (not bank actuals)."""
from dataclasses import asdict
from decimal import Decimal as D, localcontext
from hashlib import sha256
import os
from pathlib import Path
from uuid import uuid4

from tooling.solar_pv_synthetic_cases import _record, _series, build_input, build_methods
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.calculation.method_config import MethodConfig, make_parameter
from wangbin_solar_pv.calculation.result_contract import validate_result
from wangbin_solar_pv.cli import main
from wangbin_solar_pv.intake import IntakeSession
from wangbin_solar_pv.provenance import make_record
from wangbin_solar_pv.serialization import dumps, loads
from wangbin_solar_pv.timeseries_bundle import BundleBudget, write_bundle


def test_three_year_roof_project_cli_sourced_npv_irr_and_payback(tmp_path):
    root = Path(os.environ.get("TMPDIR", str(tmp_path))) / ("phase7l-r1-" + uuid4().hex)
    root.mkdir(parents=True)
    catalog = Catalog()
    case, original = build_input(catalog, "industrial_rooftop")
    session = IntakeSession.from_dict(original["project"], catalog)
    for fid, value in (("project.evaluation_date", "2026-12-31"),
                       ("project.cashflow_tax_basis", "post_tax"),
                       ("project.ownership_mode", "owner_invested")):
        session.project.values[fid] = _record(catalog, "industrial_rooftop", fid, value)
    session.project.values["finance.project_discount_rate"] = make_record(
        catalog, "finance.project_discount_rate", D("0.075"), source_kind="ASSUMPTION",
        source_id="SYNTHETIC-three-year-project-rate", source_url_or_attachment="SYNTHETIC:project-rate",
        source_section_or_cell="PROJECT_POST_TAX_NOMINAL_CNY_YEAR_END",
        confidence_basis="Synthetic nominal post-tax unlevered project rate, not verified",
        license_status="AUTHORIZED", assumption={"reason": "Project year-end smoke assumption",
        "method": "Explicit synthetic discount rate", "maturity_ceiling": "L1",
        "noncritical": False, "decision_invariant": False})
    exported = session.export()
    methods_dict = build_methods("industrial_rooftop", case).to_dict()
    for pid, value in (("irr.method", "EXACT_RATIONAL_POLYNOMIAL_ISOLATION"),
                       ("irr.minimum_rate", D("-0.9")), ("irr.maximum_rate", D("5")),
                       ("irr.root_tolerance", D("0.000000000001")), ("irr.maximum_degree", 3)):
        methods_dict["parameters"][pid] = make_parameter(pid, value,
            source_id="SYNTHETIC-three-year-irr", source_reference="SYNTHETIC:IRR-search",
            source_kind="SYNTHETIC", status="ASSUMED", license_status="AUTHORIZED")
    methods = MethodConfig.from_dict(methods_dict)
    terminal_date = "2029-12-31"
    assets = sorted({row["fields"]["capex.items.asset_id"] for row in exported["normalized_inputs"]["capex.items"]})
    document = ("SYNTHETIC forecast project_id=" + exported["project"]["project_id"]
                + " terminal_date=" + terminal_date + " "
                + " ".join("asset_id=" + asset for asset in assets)
                + " no additional recovery tax_treatment=NO_DISPOSITION_TAX"
                + " working_capital_treatment=LEDGER_ALREADY_RECOVERED").encode("utf-8")
    declaration = {"source_id": "SYNTHETIC-three-year-terminal", "source_kind": "SYNTHETIC",
        "source_reference": "SYNTHETIC:terminal-declaration", "source_section_or_cell": assets[0],
        "source_excerpt": "no additional recovery", "source_content_sha256": sha256(document).hexdigest(),
        "source_status": "ASSUMED", "economic_status": "SYNTHETIC_ASSUMPTION",
        "source_timestamp": "2026-12-31", "effective_from": "2026-12-31",
        "effective_to": terminal_date, "reviewer": "SYNTHETIC-only", "license_status": "AUTHORIZED"}
    source = {"project_id": exported["project"]["project_id"], "pv_type": "industrial_rooftop",
        "evaluation_date": "2026-12-31", "terminal_date": terminal_date, "currency": "CNY",
        "mode": "NO_DISPOSITION", "covered_asset_ids": assets, "events": [],
        "no_disposition": {"covered_asset_ids": assets, "reason": "no additional recovery",
            "tax_treatment": "NO_DISPOSITION_TAX", "working_capital_treatment": "LEDGER_ALREADY_RECOVERED",
            "source": declaration}}
    budget = BundleBudget(max_input_bytes=512 * 1024**2, max_disk_bytes=1024**3,
        max_rows=30000, max_seconds=1800, max_memory_bytes=1024**3)
    for name, payload in (("input.json", exported), ("methods.json", methods.to_dict()),
                          ("budget.json", asdict(budget)), ("terminal.json", source)):
        (root / name).write_text(dumps(payload), encoding="utf-8")
    (root / "terminal.txt").write_bytes(document)
    write_bundle(root / "bundle", base_export=exported,
        datasets={fid: _series(catalog, "industrial_rooftop", fid, case)
                  for fid in ("resource.timeseries", "load.series")},
        catalog=catalog, budget=budget, rows_per_chunk=256)
    assert main(["--workspace", str(root), "project", "--input", "input.json",
        "--methods", "methods.json", "--bundle", "bundle", "--budget", "budget.json",
        "--terminal-source", "terminal.json", "--terminal-document", "terminal.txt",
        "--output", "project"]) == 0
    result = loads((root / "project/canonical.json").read_bytes())
    validate_result(result, catalog)
    finance = loads((root / "project/3d/result.json").read_bytes())
    receipt = loads((root / "project/receipt.json").read_bytes())
    metrics = {m["metric_id"].removeprefix("financial.phase3e."): m
               for m in result["results"]["metrics"] if m["metric_id"].startswith("financial.phase3e.")}
    cash = metrics["project_cash_flow"]["value"]
    rows = finance["evidence"]["financial-ledger"]["annual"]
    assert len(cash) == len(rows) == 4
    assert all({"debt_drawdown", "principal_paid", "interest_paid", "finance_fees_paid"} <= row.keys() for row in rows)
    with localcontext() as ctx:
        ctx.prec = 80
        expected = [sum((value / D("1.075") ** index for index, value in enumerate(cash)), D(0))]
    assert abs(metrics["project_npv"]["value"] - expected[0]) < D("1e-48")
    assert metrics["discounted_cumulative_cash"]["value"][-1] == metrics["project_npv"]["value"]
    assert receipt["canonical_result_hash"] == result["result_hash"]
    assert result["source_snapshot"]["phase3e_terminal"]["phase3d_result_hash"] == finance["result_hash"]
    print("THREE_YEAR_RESULT", root, dumps({name: {"status": metrics[name]["status"],
        "value": metrics[name]["value"], "reason": metrics[name]["reason"]}
        for name in ("project_cash_flow", "project_npv", "project_irr", "static_payback", "dynamic_payback")}))
