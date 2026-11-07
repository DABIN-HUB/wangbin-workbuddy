"""Archive two independently recomputed synthetic fee-payment reports without touching sealed cases."""
from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
import shutil
import zipfile

from wangbin_solar_pv.calculation.result_contract import validate_result
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.serialization import loads


CASES = ("industrial_rooftop", "utility_scale_ground")
METRICS = ("project_npv", "project_irr", "static_payback", "dynamic_payback")


def _file(path: Path) -> dict:
    raw = path.read_bytes()
    return {"path": path.as_posix(), "bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def _metric(result: dict, name: str) -> dict:
    record = next(row for row in result["results"]["metrics"]
                  if row["metric_id"] == "financial.phase3e." + name)
    return {"status": record["status"], "value": record.get("value"),
            "reason": record.get("reason")}


def _number(value) -> Decimal:
    return Decimal(str(value))


def _yearly(case: str, old: dict, diagnostic: dict, current: dict) -> list[dict]:
    ledgers = [run["evidence"]["financial-ledger"]["annual"][1:]
               for run in (old, diagnostic, current)]
    flows = [next(row["value"] for row in run["results"]["metrics"]
                  if row["metric_id"] == "financial.phase3e.project_cash_flow")
             for run in (old, diagnostic, current)]
    settlement = loads((Path("reports/solar-pv/phase7l-r2-full-cases") / case /
                        "project/3c/result.json").read_bytes())
    fees = [next(row for row in settlement["results"]["metrics"]
                 if row["metric_id"] == f"revenue.year.{year}")["details"]["ledger"]["transaction_cost"]
            for year in range(1, 26)]
    records = []
    for index in range(25):
        prior, diag, now = (ledger[index] for ledger in ledgers)
        accrued = _number(fees[index])
        opening = _number(now["transaction_cost_payable_opening"])
        paid = _number(now["transaction_cost_cash_paid"])
        closing = _number(now["transaction_cost_payable_closing"])
        with localcontext() as context:
            context.prec = max(len(str(accrued)), len(str(opening)), len(str(paid)), 80)
            balance = opening + accrued - paid
        if (accrued != _number(now["transaction_cost_accrued"]) or
                paid != accrued or balance != closing or closing != 0):
            raise ValueError(f"FEE_LEDGER_NOT_CLOSED:{case}:{index+1}")
        record = {"period": now["period"], "phase3c_fee_accrued": str(accrued),
                  "v6_fee_payment": "UNKNOWN_NOT_SEPARATELY_RECORDED",
                  "diagnostic_v7_fee_payment": diag["transaction_cost_cash_paid"],
                  "fee_v1_payment": str(paid), "fee_v1_payable_opening": str(opening),
                  "fee_v1_payable_closing": str(closing),
                  "v6_project_cash_tax": prior["cash_tax_total_project"],
                  "diagnostic_v7_project_cash_tax": diag["cash_tax_total_project"],
                  "fee_v1_project_cash_tax": now["cash_tax_total_project"],
                  "v6_project_cash_flow": flows[0][index + 1],
                  "diagnostic_v7_project_cash_flow": flows[1][index + 1],
                  "fee_v1_project_cash_flow": flows[2][index + 1],
                  "fee_v1_delta_vs_v6_cash_flow": str(_number(flows[2][index + 1]) - _number(flows[0][index + 1])),
                  "fee_v1_delta_vs_diagnostic_cash_flow": str(_number(flows[2][index + 1]) - _number(flows[1][index + 1]))}
        records.append(record)
    return records


def archive(root: Path, scratch: Path) -> dict:
    root = root.resolve()
    scratch = scratch.resolve()
    catalog = Catalog()
    summaries = {}
    for case in CASES:
        sealed = Path("reports/solar-pv/phase7l-r2-full-cases") / case / "project/canonical.json"
        diagnostic = Path("reports/solar-pv/phase7l-r2-delivery-final-v7/calculation") / case / "canonical.json"
        new = scratch / case
        delivery = root / case
        if not delivery.is_dir():
            raise ValueError("REPORT_DELIVERY_MISSING:" + case)
        old_result, diagnostic_result, result = (loads(path.read_bytes()) for path in
                                                  (sealed, diagnostic, new / "canonical.json"))
        for run in (old_result, diagnostic_result, result):
            validate_result(run, catalog)
        if (result["result_hash"] == old_result["result_hash"] or
                result["result_hash"] == diagnostic_result["result_hash"] or
                loads((delivery / "canonical.json").read_bytes())["result_hash"] != result["result_hash"]):
            raise ValueError("RESULT_IDENTITY_MISMATCH:" + case)
        fee = result["evidence"]["financial-ledger"]["trading_fee_payment"]
        source = Path("reports/solar-pv/phase7l-r2-trading-fee-synthetic-source-v1") / case / "trading-fee-payment.json"
        if sha256(source.read_bytes()).hexdigest() != fee["raw_sha256"]:
            raise ValueError("FEE_SOURCE_BYTE_MISMATCH:" + case)
        calculation = delivery / "calculation"
        assumption = delivery / "assumptions"
        for folder in (calculation, assumption):
            folder.mkdir(exist_ok=False)
        for name in ("phase3d.json", "replay-receipt.json"):
            shutil.copyfile(new / name, calculation / name)
        shutil.copyfile(source, assumption / "trading-fee-payment.json")
        yearly = _yearly(case, old_result, diagnostic_result, result)
        (calculation / "annual-three-way.json").write_text(
            json.dumps({"schema_version": "solar-pv-trading-fee-three-way/1.0.0",
                        "project_id": result["project_id"],
                        "source_sha256": fee["raw_sha256"],
                        "source_id": fee["source_id"],
                        "v6_result_hash": old_result["result_hash"],
                        "diagnostic_v7_result_hash": diagnostic_result["result_hash"],
                        "fee_v1_result_hash": result["result_hash"],
                        "metrics": {name: {"v6": _metric(old_result, name),
                                           "diagnostic_v7": _metric(diagnostic_result, name),
                                           "fee_v1": _metric(result, name)} for name in METRICS},
                        "annual": yearly}, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
        summaries[case] = {"result_hash": result["result_hash"], "source_sha256": fee["raw_sha256"],
                           "phase3c_result_hash": result["inputs"]["upstream_settlement_result_hash"],
                           "annual_periods": len(yearly), "metrics": {name: _metric(result, name) for name in METRICS}}
    manifest_path = root / "PACKAGE-MANIFEST.json"
    archive_path = root / "trading-fee-payment-synthetic-v1.zip"
    receipt_path = root / "ARCHIVE-RECEIPT.json"
    if any(path.exists() for path in (manifest_path, archive_path, receipt_path)):
        raise FileExistsError("PACKAGE_ALREADY_EXISTS")
    members = sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix())
    manifest = {"schema_version": "solar-pv-trading-fee-delivery/1.0.0",
                "scope": "SYNTHETIC_ASSUMED_ANNUAL_FORECAST_NOT_ACTUAL_PAYMENT",
                "cases": summaries,
                "pdf_gate": "BLOCKED_RENDERER_UNAVAILABLE",
                "toc_page_gate": "NOT_VERIFIED_RENDER_REFRESH",
                "full_visual_gate": "NOT_VERIFIED",
                "workbuddy_platform_gate": "NOT_VERIFIED",
                "members": [{**_file(p), "path": p.relative_to(root).as_posix()} for p in members]}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as packed:
        for path in (*members, manifest_path):
            packed.write(path, path.relative_to(root).as_posix())
    with zipfile.ZipFile(archive_path) as packed:
        expected = {item["path"] for item in manifest["members"]} | {manifest_path.name}
        if set(packed.namelist()) != expected or len(packed.namelist()) != len(expected):
            raise ValueError("ZIP_MEMBER_INVENTORY_MISMATCH")
        for item in manifest["members"]:
            raw = packed.read(item["path"])
            if len(raw) != item["bytes"] or sha256(raw).hexdigest() != item["sha256"]:
                raise ValueError("ZIP_MEMBER_BYTE_MISMATCH:" + item["path"])
        if packed.read(manifest_path.name) != manifest_path.read_bytes():
            raise ValueError("ZIP_MANIFEST_BYTE_MISMATCH")
    receipt = {"schema_version": "solar-pv-trading-fee-archive-receipt/1.0.0",
               "archive": _file(archive_path), "manifest": _file(manifest_path),
               "members": len(expected), "status": "LOCAL_HASH_VERIFIED_NOT_PLATFORM_ACCEPTED"}
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("delivery_dir", type=Path)
    parser.add_argument("replay_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(archive(args.delivery_dir, args.replay_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
