"""Read back and archive the two R3 local-review reports without recalculation.

Requires local pypdfium2 for PDF text-page checks. This is not a professional
visual review or a WorkBuddy platform acceptance test.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re
import zipfile

from docx import Document
from openpyxl import load_workbook
import pypdfium2

CASES = {
    "industrial_rooftop": "ca4bdff3f5e89e6770d43f4dad3b4efd57d965aba6c9ba0f1b4299f99295a43f",
    "utility_scale_ground": "69882cc39020f03fb3ef6cdb1a10b188c324de0f66066392970776b7495ad138",
}


def _hash(path: Path) -> dict[str, object]:
    content = path.read_bytes()
    return {"bytes": len(content), "sha256": sha256(content).hexdigest()}


def _readback(folder: Path, expected_hash: str) -> dict[str, object]:
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    canonical = json.loads((folder / "canonical.json").read_text(encoding="utf-8"))
    if manifest["identity"]["result_hash"] != canonical["result_hash"] or canonical["result_hash"] != expected_hash:
        raise ValueError("CANONICAL_HASH_MISMATCH:" + str(folder))
    if manifest["pdf_status"] != "GENERATED" or manifest["quality_gates"]["VISUAL_REVIEW"] != "NOT_TESTED":
        raise ValueError("PDF_OR_VISUAL_STATUS_MISMATCH")
    for entry in manifest["files"].values():
        if entry.get("status") == "BLOCKED":
            continue
        file = folder / entry.get("path", entry.get("file", ""))
        actual = _hash(file) if file.is_file() else None
        if (actual is None or actual["sha256"] != entry["sha256"]
                or ("size" in entry and actual["bytes"] != entry["size"])):
            raise ValueError("REPORT_MANIFEST_BYTE_MISMATCH:" + str(file))
    docx = folder / manifest["files"]["F01"]["path"]
    pdf = folder / manifest["files"]["F02"]["path"]
    document = Document(docx)
    toc = [(line.text.rsplit("\t", 1)[0], int(line.text.rsplit("\t", 1)[1]))
           for line in document.paragraphs if line.style.name.lower().startswith("toc ")
           and "\t" in line.text and line.text.rsplit("\t", 1)[1].isdigit()]
    if len(toc) < 126:
        raise ValueError("TOC_INCOMPLETE")
    rendered = pypdfium2.PdfDocument(str(pdf))
    page_text = [re.sub(r"\s+", "", rendered[i].get_textpage().get_text_range()) for i in range(len(rendered))]
    if any(len(text) < 20 for text in page_text):
        raise ValueError("PDF_EMPTY_TEXT_PAGE")
    for title, page in toc:
        if page < 1 or page > len(page_text) or re.sub(r"\s+", "", title) not in page_text[page - 1]:
            raise ValueError(f"TOC_PAGE_MISMATCH:{title}:{page}")
    review = json.loads((folder / "independent-content-review.json").read_text(encoding="utf-8"))
    if review["docx_sha256"] != _hash(docx)["sha256"] or (review["counts"]["chapters"], review["counts"]["appendices"], review["counts"]["formula_groups"]) != (100, 26, 42):
        raise ValueError("CONTENT_REVIEW_IDENTITY_OR_COVERAGE_MISMATCH")
    model_file = folder / manifest["files"]["F03"]["path"]
    workbook = load_workbook(model_file, read_only=True, data_only=True)
    metrics = {r["metric_id"]: r for r in canonical["results"]["metrics"]}
    npv_id = "financial.phase3e.project_npv"
    irr_id = "financial.phase3e.project_irr"
    flow_id = "financial.phase3e.project_cash_flow"
    rows = {row[0]: row for row in workbook["财务指标"].iter_rows(values_only=True) if row[0] in (npv_id, irr_id)}
    if (set(rows) != {npv_id, irr_id} or rows[npv_id][1] != "CALCULATED"
            or abs(Decimal(str(rows[npv_id][2])) - Decimal(str(metrics[npv_id]["value"]))) > Decimal("0.01")
            or rows[irr_id][1] != "CALCULATED" or rows[irr_id][3] != "—"
            or abs(Decimal(str(rows[irr_id][2]).rstrip("%")) / 100 - Decimal(str(metrics[irr_id]["value"]))) > Decimal("0.0001")):
        raise ValueError("FINANCIAL_METRIC_OR_IRR_UNIT_MISMATCH")
    flow = next(row for row in workbook["项目现金流"].iter_rows(values_only=True) if row[0] == flow_id)
    actual_flow = json.loads(flow[2])
    expected_flow = metrics[flow_id]["value"]
    if len(actual_flow) != 26 or any(Decimal(str(a)) != Decimal(str(b)) for a, b in zip(actual_flow, expected_flow)):
        raise ValueError("ANNUAL_CASH_FLOW_MISMATCH")
    bridge = [table for table in document.tables if "营运资金回收（元）" in [cell.text for cell in table.rows[0].cells]]
    if len(bridge) != 1:
        raise ValueError("APP06_CASH_BRIDGE_MISSING")
    header = [cell.text for cell in bridge[0].rows[0].cells]
    terminal = [dict(zip(header, [cell.text for cell in row.cells])) for row in bridge[0].rows[1:]
                if "第25年" in row.cells[0].text]
    if len(terminal) != 1 or Decimal(terminal[0]["营运资金回收（元）"].replace(",", "")) != 12000:
        raise ValueError("TERMINAL_WORKING_CAPITAL_SOURCE_MISSING")
    fee = canonical["evidence"]["financial-ledger"]["trading_fee_payment"]
    if _hash(folder / "assumptions/trading-fee-payment.json")["sha256"] != fee["raw_sha256"]:
        raise ValueError("TRADING_FEE_SOURCE_BYTES_MISMATCH")
    return {"result_hash": expected_hash, "pdf_pages": len(rendered), "toc_entries": len(toc),
            "toc_page_mapping": "ALL_TEXT_MATCHED", "empty_text_pages": 0,
            "body_items": 100, "appendix_items": 26, "formula_groups": 42,
            "independent_items_flagged_for_professional_review": review["counts"]["items_flagged"],
            "app06_year25_working_capital_recovery_yuan": "12000",
            "workbook_cash_periods": 26, "workbook_irr_unit": "—",
            "trading_fee_source_sha256": fee["raw_sha256"],
            "pdf_visual_review": "NOT_PERFORMED", "professional_content_review": "REQUIRED",
            "workbuddy_platform_gate": "NOT_VERIFIED"}


def _pack(zip_path: Path, root: Path, entries: list[dict[str, object]], extras: tuple[Path, ...] = ()) -> dict[str, object]:
    with zipfile.ZipFile(zip_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for entry in entries:
            output.write(root / entry["path"], entry["path"])
        for extra in extras:
            output.write(extra, extra.relative_to(root).as_posix())
    with zipfile.ZipFile(zip_path) as archive:
        expected = {entry["path"] for entry in entries} | {extra.relative_to(root).as_posix() for extra in extras}
        if set(archive.namelist()) != expected or len(archive.namelist()) != len(expected):
            raise ValueError("ZIP_INVENTORY_MISMATCH")
        for entry in entries:
            raw = archive.read(entry["path"])
            if len(raw) != entry["bytes"] or sha256(raw).hexdigest() != entry["sha256"]:
                raise ValueError("ZIP_MEMBER_HASH_MISMATCH:" + entry["path"])
        for extra in extras:
            if archive.read(extra.relative_to(root).as_posix()) != extra.read_bytes():
                raise ValueError("ZIP_EXTRA_BYTE_MISMATCH")
    return {"path": zip_path.name, **_hash(zip_path), "member_count": len(expected)}


def package(root: Path) -> dict[str, object]:
    if any((root / filename).exists() for filename in ("PACKAGE-MANIFEST.json", "CASE-ZIP-RECEIPT.json", "ARCHIVE-RECEIPT.json")):
        raise FileExistsError("R3_PACKAGE_ALREADY_EXISTS")
    if not (root / "FINAL-DELIVERY.md").is_file():
        raise FileNotFoundError("FINAL_DELIVERY_NOTE_MISSING")
    audits = {case: _readback(root / case, expected) for case, expected in CASES.items()}
    for case, audit in audits.items():
        (root / case / "delivery-audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        case_entries = [{"path": p.relative_to(root).as_posix(), **_hash(p)}
                        for p in sorted((root / case).rglob("*")) if p.is_file()]
        case_manifest = {"schema_version": "phase7l-r3-case-review/1.0.0",
                         "case": case, "result_hash": audit["result_hash"],
                         "professional_review_gate": "REQUIRED", "visual_review_gate": "NOT_PERFORMED",
                         "members": case_entries}
        (root / case / "CASE-MANIFEST.json").write_text(
            json.dumps(case_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    members = [{"path": p.relative_to(root).as_posix(), **_hash(p)} for p in sorted(root.rglob("*"))
               if p.is_file() and p.name != "PACKAGE-MANIFEST.json"]
    manifest = {"schema_version": "phase7l-r3-local-review/1.0.0", "report_content_version": "phase7l-r3-v1-professional-content-and-full-cash-bridge",
                "canonical_cases": audits, "toc_page_gate": "ALL_TEXT_PAGE_MAPPING_VERIFIED",
                "pdf_render_gate": "GENERATED_WITH_WPS", "visual_review_gate": "NOT_PERFORMED",
                "professional_review_gate": "REQUIRED", "four_file_gate": "NOT_FORMAL_ACCEPTANCE",
                "workbuddy_platform_gate": "NOT_VERIFIED", "members": members}
    package_manifest = root / "PACKAGE-MANIFEST.json"
    package_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    case_archives = {}
    for case in CASES:
        case_entries = [entry for entry in members if entry["path"].startswith(case + "/")]
        case_archives[case] = _pack(root / ("phase7l-r3-" + case + "-review.zip"), root, case_entries)
    combined = _pack(root / "phase7l-r3-two-case-review.zip", root, members, (package_manifest,))
    case_receipt = {"status": "LOCAL_BYTE_VERIFIED_NOT_PROFESSIONALLY_ACCEPTED", "archives": case_archives}
    (root / "CASE-ZIP-RECEIPT.json").write_text(json.dumps(case_receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt = {"status": "LOCAL_BYTE_VERIFIED_NOT_PLATFORM_ACCEPTED", "archive": combined,
               "manifest": _hash(package_manifest), "case_archives": case_archives}
    (root / "ARCHIVE-RECEIPT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("delivery_dir", type=Path)
    args = parser.parse_args()
    print(json.dumps(package(args.delivery_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
