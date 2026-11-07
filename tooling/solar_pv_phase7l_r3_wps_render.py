"""Finalize an R3 local-review case with a real WPS TOC refresh and PDF.

This is opt-in Windows-only post-processing, not a PDF fallback or a platform gate.
The input export remains untouched. The output directory must not exist.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import time
import zipfile

from docx import Document


def _identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": path.name, "size": len(data), "sha256": sha256(data).hexdigest()}


def finalize(source: Path, destination: Path, evidence_case: Path,
             generator_receipt: Path) -> dict[str, object]:
    if not source.is_dir() or not (source / "manifest.json").is_file():
        raise FileNotFoundError("R3_SOURCE_EXPORT_MISSING")
    if destination.exists():
        raise FileExistsError(destination)
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    original = source / manifest["files"]["F01"]["path"]
    if not original.is_file() or sha256(original.read_bytes()).hexdigest() != manifest["files"]["F01"]["sha256"]:
        raise ValueError("ORIGINAL_DOCX_MANIFEST_MISMATCH")
    canonical = json.loads((source / "canonical.json").read_text(encoding="utf-8"))
    if manifest.get("identity", {}).get("result_hash") != canonical["result_hash"]:
        raise ValueError("CANONICAL_IDENTITY_MISMATCH")
    fee = canonical["evidence"]["financial-ledger"]["trading_fee_payment"]
    fee_source = evidence_case / "assumptions/trading-fee-payment.json"
    if (not generator_receipt.is_file() or not fee_source.is_file() or
            sha256(fee_source.read_bytes()).hexdigest() != fee["raw_sha256"] or
            json.loads((evidence_case / "canonical.json").read_text(encoding="utf-8"))["result_hash"] != canonical["result_hash"]):
        raise ValueError("R3_EVIDENCE_CASE_OR_GENERATOR_RECEIPT_MISMATCH")
    generator = json.loads(generator_receipt.read_text(encoding="utf-8"))
    if generator.get("identity", {}).get("result_hash") != canonical["result_hash"]:
        raise ValueError("R3_GENERATOR_RECEIPT_IDENTITY_MISMATCH")
    destination.mkdir(parents=True, exist_ok=False)
    for file in source.iterdir():
        if file.is_file():
            shutil.copyfile(file, destination / file.name)
    for folder in ("assumptions", "calculation"):
        shutil.copytree(evidence_case / folder, destination / folder)
    execution = destination / "execution"
    execution.mkdir(exist_ok=False)
    shutil.copyfile(generator_receipt, execution / "generator-pre-render-receipt.json")
    document = destination / original.name
    pdf = document.with_suffix(".pdf")
    if pdf.exists():
        raise FileExistsError(pdf)
    before = Document(original)
    body_headings = [p.text for p in before.paragraphs if p.style.name.startswith("Heading") and p.text.startswith(("CH", "APP", "F-"))]
    app = None
    word = None
    began = time.perf_counter()
    try:
        import win32com.client  # pywin32 and WPS are local optional renderer prerequisites.
        app = win32com.client.DispatchEx("KWPS.Application")
        app.Visible = False
        word = app.Documents.Open(str(document.resolve()), ReadOnly=False)
        if word.TablesOfContents.Count != 1:
            raise RuntimeError("EXPECTED_ONE_EDITABLE_TOC")
        word.TablesOfContents(1).Update()
        word.Save()
        word.ExportAsFixedFormat(str(pdf.resolve()), 17)
    finally:
        if word is not None:
            word.Close(False)
        if app is not None:
            app.Quit()
    if not pdf.is_file() or pdf.stat().st_size < 1024 or not pdf.read_bytes().startswith(b"%PDF-"):
        raise RuntimeError("WPS_PDF_RENDER_FAILED")
    with zipfile.ZipFile(document) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("REFRESHED_DOCX_CORRUPT")
    after = Document(document)
    if body_headings != [p.text for p in after.paragraphs if p.style.name.startswith("Heading") and p.text.startswith(("CH", "APP", "F-"))]:
        raise RuntimeError("OUTLINE_CHANGED_BY_TOC_REFRESH")
    toc = [p for p in after.paragraphs if p.style.name.lower().startswith("toc ")]
    if not toc or not any("CH01" in p.text for p in toc):
        raise RuntimeError("REFRESHED_TOC_NOT_CACHED")
    elapsed = round(time.perf_counter() - began, 6)
    manifest["files"]["F01"].update(_identity(document))
    manifest["files"]["F01"]["toc_status"] = "FIELD_REFRESHED_BY_WPS_PAGE_NUMBERS_REVIEW_REQUIRED"
    manifest["files"]["F02"] = {**_identity(pdf), "status": "GENERATED", "renderer": "WPS_KWPS_COM",
                                  "generation_seconds": elapsed, **manifest["identity"]}
    manifest["pdf_status"] = "GENERATED"
    manifest["quality_gates"]["TOC_VALID"] = "FIELD_REFRESHED_BY_WPS_PAGE_NUMBERS_REVIEW_REQUIRED"
    manifest["quality_gates"]["PDF_RENDER"] = "GENERATED"
    manifest["quality_gates"]["FOUR_FILE_GATE"] = "NOT_FORMAL_ACCEPTANCE"
    manifest["quality_gates"]["VISUAL_REVIEW"] = "NOT_TESTED"
    manifest["four_file_gate"] = "NOT_FORMAL_ACCEPTANCE"
    manifest["render_evidence"] = {"kind": "LOCAL_WPS_TOC_UPDATE_AND_PDF_EXPORT",
                                   "original_docx_sha256": sha256(original.read_bytes()).hexdigest(),
                                   "cached_toc_paragraphs": len(toc), "status": "PAGE_VISUAL_REVIEW_REQUIRED"}
    (destination / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt = {"report_content_version": manifest["report_content_version"],
               "canonical_result_hash": manifest["identity"]["result_hash"],
               "docx": _identity(document), "pdf": _identity(pdf),
               "cached_toc_paragraphs": len(toc), "quality_gates": manifest["quality_gates"]}
    (execution / "wps-render-receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("evidence_case", type=Path, help="Previously verified fee-payment case with identical canonical")
    parser.add_argument("generator_receipt", type=Path, help="Unmodified JSON stdout of the R3 source export")
    args = parser.parse_args()
    print(json.dumps(finalize(args.source, args.destination, args.evidence_case, args.generator_receipt),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
