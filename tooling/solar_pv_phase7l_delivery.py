"""Export a pre-existing, freshly calculated PV run and audit its input coverage.

No calculation is fabricated here. This step binds one Phase 2/D3/3G identity to
DOCX, workbooks, a 469-row input audit and a human-review-required claim sheet.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services/solar-pv-engine/src"))

from wangbin_solar_pv.calculation.input_contract import validate_export
from wangbin_solar_pv.calculation.result_contract import validate_result
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.local_files import Workspace
from wangbin_solar_pv.report_export import export_ground_report, export_rooftop_report
from wangbin_solar_pv.serialization import loads
from wangbin_solar_pv.timeseries_bundle import BundleBudget, read_bundle

from .solar_pv_input_audit import audit


def _file(path: Path) -> dict:
    return {"path": path.name, "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def deliver(run_dir: Path, output_root: Path, output_name: str, *, fixture_file: Path | None = None,
            canonical_file: Path | None = None) -> dict:
    if not output_root.is_dir():
        raise ValueError("OUTPUT_ROOT_MUST_EXIST")
    output = output_root / output_name
    if output.exists():
        raise FileExistsError(output)
    catalog = Catalog()
    exported = loads((run_dir / "input.json").read_bytes())
    validated = validate_export(exported, catalog)
    result = loads((canonical_file or run_dir / "project/canonical.json").read_bytes())
    validate_result(result, catalog)
    if canonical_file is not None:
        baseline = loads((run_dir / "project/canonical.json").read_bytes())
        validate_result(baseline, catalog)
        if (result["source_snapshot"].get("datasets") != baseline["source_snapshot"].get("datasets")
                or result["inputs"].get("upstream_settlement_result_hash") !=
                baseline["inputs"].get("upstream_settlement_result_hash")):
            raise ValueError("CANONICAL_OVERRIDE_UPSTREAM_IDENTITY_MISMATCH")
    if validated.project.project_id != result["project_id"] or validated.project.pv_type != result["pv_type"]:
        raise ValueError("PROJECT_IDENTITY_MISMATCH")
    if result["inputs"]["identity_payload"]["phase2_input_hash"] != exported["input_hash"]:
        raise ValueError("INPUT_HASH_MISMATCH")
    fixture = loads(fixture_file.read_bytes()) if fixture_file else None
    if fixture and (fixture.get("linked_calculation_project_id") != result["project_id"]
                    or fixture.get("result_hash") != result["result_hash"]):
        raise ValueError("EDITORIAL_CALCULATION_IDENTITY_MISMATCH")
    with ExitStack() as stack:
        bundle_dir = run_dir / "bundle"
        if not (bundle_dir / "base.json").is_file():
            archive = run_dir / "archived-d3-and-intervals.zip"
            if not archive.is_file():
                raise FileNotFoundError("D3_BUNDLE_NOT_AVAILABLE")
            restored = Path(stack.enter_context(TemporaryDirectory(prefix="phase7l-report-bundle-",
                                                                    dir=os.getenv("TMPDIR")))) / "bundle"
            restored.mkdir()
            shutil.copyfile(bundle_dir / "manifest.json", restored / "manifest.json")
            with zipfile.ZipFile(archive) as zipped:
                for member in zipped.namelist():
                    if not member.startswith("bundle/"):
                        continue
                    leaf = member.removeprefix("bundle/")
                    if not leaf or "/" in leaf or "\\" in leaf or leaf in {".", ".."}:
                        raise ValueError("D3_ARCHIVE_PATH_INVALID")
                    with zipped.open(member) as source, (restored / leaf).open("wb") as target:
                        shutil.copyfileobj(source, target)
            bundle_dir = restored
        bundle = stack.enter_context(read_bundle(bundle_dir, catalog=catalog, budget=BundleBudget()))
        if bundle.base_export != exported:
            raise ValueError("D3_INPUT_IDENTITY_MISMATCH")
        if result["pv_type"] == "industrial_rooftop":
            reporter = export_rooftop_report
        elif result["pv_type"] == "utility_scale_ground":
            reporter = export_ground_report
        else:
            raise ValueError("UNSUPPORTED_PV_TYPE")
        receipt = reporter(result, catalog, Workspace(output_root), output_name, editorial_fixture=fixture)
        checklist_file = output / "content-checklist.json"
        checklist = json.loads(checklist_file.read_text(encoding="utf-8"))
        matrix = audit(exported, bundle.manifest, result, checklist, catalog, d3_validated=True)
    matrix_file = output / "input-coverage-matrix.json"
    matrix_file.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    review = {"schema_version": "phase7l-human-claim-review/1.0.0",
              "identity": checklist["identity"], "status": "HUMAN_REVIEW_REQUIRED",
              "reason": "Field/metric binding and text presence cannot prove professional content quality",
              "items": [{"section_id": row["id"], "question": row["core_question"],
                         "central_claim": row["central_claim"], "claim_status": row["claim_status"],
                         "source_ids": row["source_ids"], "formula_ids": row["supporting_formula_ids"],
                         "reasoning": row["causal_reasoning"], "decision": row["decision"],
                         "review_status": "NOT_MANUALLY_APPROVED"} for row in checklist["records"]]}
    if len(review["items"]) != 126 or len({i["section_id"] for i in review["items"]}) != 126:
        raise ValueError("CLAIM_OUTLINE_INCOMPLETE")
    review_file = output / "central-claim-review.json"
    review_file.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evidence = {"identity": checklist["identity"],
                "calculation_status": result["status"],
                "formula_execution": [{"metric_id": m["metric_id"], "formula_id": m.get("formula_id"),
                                       "status": m["status"], "missing_field_ids": m.get("details", {}).get("missing_field_ids")}
                                      for m in result["results"]["metrics"]],
                "source_snapshot_id": result["source_snapshot_id"],
                "d3_content_hash": bundle.manifest["content_hash"]}
    evidence_file = output / "calculation-and-source-evidence.json"
    evidence_file.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"identity": checklist["identity"], "status": receipt["status"],
            "calculation_status": result["status"], "quality_gates": receipt["quality_gates"],
            "catalog_l2": matrix["catalog_l2"], "input_coverage": _file(matrix_file),
            "claims": _file(review_file), "formula_execution": _file(evidence_file),
            "report_files": receipt["files"], "manifest": _file(output / "manifest.json")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("output_root", type=Path)
    parser.add_argument("output_name")
    parser.add_argument("--editorial-fixture", type=Path)
    parser.add_argument("--canonical", type=Path, help="Recalculated canonical with the same Phase 2/D3/3C source")
    args = parser.parse_args()
    print(json.dumps(deliver(args.run_dir, args.output_root, args.output_name,
                             fixture_file=args.editorial_fixture, canonical_file=args.canonical),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
