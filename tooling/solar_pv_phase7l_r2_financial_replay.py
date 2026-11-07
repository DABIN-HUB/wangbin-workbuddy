"""Recompute only 3D and sourced 3E from an immutable 7L-R2 sealed case.

The Phase 2 inputs, D3 archive and calculated 3B/3C stages are read without
modification. The new canonical and stage receipts go to a fresh directory.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from hashlib import sha256
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import zipfile

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.calculation.financial_ledger import calculate_financial_ledger
from wangbin_solar_pv.calculation.method_config import MethodConfig
from wangbin_solar_pv.calculation.phase3e import calculate_sourced_project_npv
from wangbin_solar_pv.calculation.result_contract import validate_result
from wangbin_solar_pv.calculation.terminal_disposition import VERSION as TERMINAL_VERSION
from wangbin_solar_pv.calculation.trading_fee_payment import MAX_SOURCE_BYTES
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.serialization import digest, dumps, loads
from wangbin_solar_pv.timeseries_bundle import BundleBudget, read_bundle


def replay(case_dir: Path, output_dir: Path, scratch_dir: Path, *, trading_fee_source_path: Path | None = None) -> dict:
    case_dir, output_dir, scratch_dir = case_dir.resolve(), output_dir.resolve(), scratch_dir.resolve()
    if output_dir.exists() or not scratch_dir.is_dir():
        raise ValueError("FRESH_OUTPUT_AND_EXISTING_SCRATCH_REQUIRED")
    catalog = Catalog()
    exported = loads((case_dir / "input.json").read_bytes())
    methods = MethodConfig.from_dict(loads((case_dir / "methods.json").read_bytes()))
    original = loads((case_dir / "project/canonical.json").read_bytes())
    generation = loads((case_dir / "project/3b/result.json").read_bytes())
    settlement = loads((case_dir / "project/3c/result.json").read_bytes())
    for result in (original, generation, settlement):
        validate_result(result, catalog)
    if not str(exported["project"]["project_id"]).startswith("SYNTHETIC-PHASE7L-R2-"):
        raise ValueError("ONLY_SEALED_R2_SYNTHETIC_CASES")
    source = loads((case_dir / "terminal.json").read_bytes())
    provenance = source["no_disposition"]["source"]
    documents = {provenance["source_id"]: (case_dir / "terminal.txt").read_bytes()}
    if trading_fee_source_path is not None and trading_fee_source_path.stat().st_size > MAX_SOURCE_BYTES:
        raise ContractError("TRADING_FEE_SOURCE_BYTES_REQUIRED")
    fee_source_bytes = trading_fee_source_path.read_bytes() if trading_fee_source_path is not None else None
    with ExitStack() as stack:
        restored = Path(stack.enter_context(TemporaryDirectory(prefix="pv-v7-bundle-", dir=scratch_dir))) / "bundle"
        restored.mkdir()
        shutil.copyfile(case_dir / "bundle/manifest.json", restored / "manifest.json")
        with zipfile.ZipFile(case_dir / "archived-d3-and-intervals.zip") as zipped:
            for member in zipped.namelist():
                if not member.startswith("bundle/"):
                    continue
                leaf = member.removeprefix("bundle/")
                if not leaf or leaf in {".", ".."} or "/" in leaf or "\\" in leaf:
                    raise ValueError("D3_ARCHIVE_PATH_INVALID")
                with zipped.open(member) as stream, (restored / leaf).open("wb") as target:
                    shutil.copyfileobj(stream, target)
        bundle = stack.enter_context(read_bundle(restored, catalog=catalog, budget=BundleBudget()))
        if bundle.base_export != exported:
            raise ValueError("D3_INPUT_IDENTITY_MISMATCH")
        financial = calculate_financial_ledger(exported, methods, settlement, catalog=catalog,
                                               trading_fee_source_bytes=fee_source_bytes)
        validate_result(financial, catalog)
        if financial["boundaries"]["FINANCIAL_LEDGER"]["transaction_fee_payment"] == "BLOCKED_MISSING_INPUT":
            raise ContractError("TRANSACTION_FEE_PAYMENT_SOURCE_REQUIRED")
        binding = {"project_id": exported["project"]["project_id"],
                   "pv_type": exported["project"]["pv_type"],
                   "evaluation_date": exported["project"]["values"]["project.evaluation_date"]["value"],
                   "currency": exported["project"]["values"]["project.currency"]["value"],
                   "scenario_id": financial["scenario_id"],
                   "phase2_input_hash": exported["input_hash"],
                   "phase2_source_snapshot_id": exported["source_snapshot_id"],
                   "method_config_hash": methods.hash,
                   "d3_content_hash": bundle.content_hash,
                   "phase3b_result_hash": generation["result_hash"],
                   "phase3c_result_hash": settlement["result_hash"],
                   "phase3d_result_hash": financial["result_hash"],
                   "basis": "项目税后"}
        carrier = {"schema_version": TERMINAL_VERSION, "source": source,
                   "source_content_hash": digest(source), "binding": binding}
        canonical = calculate_sourced_project_npv(carrier, documents, exported, methods, bundle,
                                                  generation, settlement, financial, catalog,
                                                  trading_fee_source_bytes=fee_source_bytes)
        validate_result(canonical, catalog)
        if (canonical["result_hash"] == original["result_hash"] or
                canonical["inputs"]["upstream_settlement_result_hash"] != settlement["result_hash"] or
                canonical["source_snapshot"].get("datasets") != original["source_snapshot"].get("datasets")):
            raise ValueError("REPLAY_CALCULATION_IDENTITY_NOT_UPDATED")
    previous = {m["metric_id"]: m for m in original["results"]["metrics"]}
    latest = {m["metric_id"]: m for m in canonical["results"]["metrics"]}
    focus = ("project_cash_flow", "project_npv", "project_irr", "static_payback", "dynamic_payback")
    impact = {name: {"previous": previous["financial.phase3e." + name].get("value"),
                     "current": latest["financial.phase3e." + name].get("value"),
                     "status": latest["financial.phase3e." + name]["status"]}
              for name in focus}
    old_rows = original["evidence"]["financial-ledger"]["annual"]
    rows = canonical["evidence"]["financial-ledger"]["annual"]
    stages = []
    for year, (old, row) in enumerate(zip(old_rows[1:], rows[1:]), 1):
        source_fee = next(m for m in settlement["results"]["metrics"]
                          if m["metric_id"] == f"revenue.year.{year}")["details"]["ledger"]["transaction_cost"]
        stages.append({"period": row["period"], "phase3c_fee_accrued": source_fee,
                       "phase3d_receipt": row["revenue_cash_receipts"],
                       "phase3d_self_use_saving": row["self_use_avoided_expenditure"],
                       "phase3d_fee_paid": row["transaction_cost_cash_paid"],
                       "phase3d_fee_payable_closing": row["transaction_cost_payable_closing"],
                       "phase3d_opex_paid": row["opex_cash_paid"],
                       "phase3d_project_cash_tax": row["cash_tax_total_project"],
                       "old_project_cash_tax": old["cash_tax_total_project"],
                       "phase3e_project_cash_flow": latest["financial.phase3e.project_cash_flow"]["value"][year],
                       "old_project_cash_flow": previous["financial.phase3e.project_cash_flow"]["value"][year]})
    receipt = {"source_case": case_dir.as_posix(), "phase2_input_hash": exported["input_hash"],
               "d3_content_hash": binding["d3_content_hash"], "method_config_hash": methods.hash,
               "phase3b_result_hash": generation["result_hash"],
               "phase3c_result_hash": settlement["result_hash"],
               "previous_result_hash": original["result_hash"],
               "phase3d_result_hash": financial["result_hash"],
               "canonical_result_hash": canonical["result_hash"],
               "fee_treatment": settlement["boundaries"]["SETTLEMENT"]["fee_treatment"],
               "fee_payment_status": financial["boundaries"]["FINANCIAL_LEDGER"]["transaction_fee_payment"],
               "trading_fee_source_sha256": financial["evidence"]["financial-ledger"].get("trading_fee_payment",{}).get("raw_sha256"),
               "impact": impact, "operating_periods": stages}
    output_dir.mkdir(parents=True)
    try:
        (output_dir / "phase3d.json").write_text(dumps(financial), encoding="utf-8")
        (output_dir / "canonical.json").write_text(dumps(canonical), encoding="utf-8")
        (output_dir / "replay-receipt.json").write_text(dumps(receipt), encoding="utf-8")
        for name, result in (("phase3d.json", financial), ("canonical.json", canonical)):
            assert loads((output_dir / name).read_bytes())["result_hash"] == result["result_hash"]
    except BaseException:
        for path in output_dir.iterdir():
            path.unlink()
        output_dir.rmdir()
        raise
    return {"canonical_result_hash": canonical["result_hash"],
            "previous_result_hash": original["result_hash"],
            "phase3d_result_hash": financial["result_hash"],
            "receipt_sha256": sha256((output_dir / "replay-receipt.json").read_bytes()).hexdigest(),
            "impact": impact}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--trading-fee-payment-source", type=Path, help="Explicit synthetic trading-fee assumption JSON")
    args = parser.parse_args()
    print(json.dumps(replay(args.case_dir, args.output_dir, args.scratch,
                            trading_fee_source_path=args.trading_fee_payment_source),
                     ensure_ascii=False, default=str, indent=2))


if __name__ == "__main__":
    main()
