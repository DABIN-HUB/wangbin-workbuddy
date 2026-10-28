"""Read-only Phase 0/1 solar-PV baseline contract verifier, not a PV engine.

Default exit 0 means documentation/index integrity only. --release additionally
requires actual product acceptance and all six orthogonal gates to pass.
No network, package execution, customer-file parsing, or repository writes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


class BaselineError(ValueError):
    """Invalid or incomplete persisted requirements contract."""


def load_json(path: Path) -> Any:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise BaselineError(f"duplicate JSON key: {path.name}: {key}")
            result[key] = value
        return result

    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object)


def verify(root: Path, *, release: bool) -> dict[str, Any]:
    document_root = root / "docs" / "solar-pv"
    errors: list[str] = []
    checks = 0

    def check(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(message)

    def unique(records: list[dict[str, Any]], key: str, label: str) -> set[str]:
        values = [record[key] for record in records]
        check(len(values) == len(set(values)), f"duplicate {label} identifiers")
        return set(values)

    def parts(value: str) -> set[str]:
        return set(filter(None, value.split("|")))

    def safe_evidence(relative: str) -> bool:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or path.suffix.lower() not in {".md", ".json", ".txt", ".xml", ".png", ".pdf", ".xlsx", ".docx"}:
            return False
        target = root / path
        return target.is_file() and not target.is_symlink() and target.resolve().is_relative_to(root.resolve())

    contract = load_json(document_root / "08-baseline-contract.json")
    for name in contract["required_document_files"]:
        check((document_root / name).is_file(), f"required baseline document missing: {name}")
    manifest = load_json(document_root / "00-baseline-manifest.json")
    original = (document_root / manifest["baseline_file"]).read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    check(hashlib.sha256(original.encode("utf-8")).hexdigest() == manifest["normalized_utf8_sha256"], "frozen original baseline hash mismatch")
    check(set(re.findall(r"^## (\d+)\.", original, re.M)) == {str(i) for i in range(12)}, "original baseline must retain sections 0..11")

    fields_document = load_json(document_root / "03-input-fields.json")
    fields = fields_document["fields"]
    field_ids = unique(fields, "field_id", "input field")
    field_map = {field["field_id"]: field for field in fields}
    digests = load_json(document_root / "08-field-contract-digests.json")["field_sha256"]
    check(set(digests) == field_ids, "field review digest index incomplete")
    for field in fields:
        digest = hashlib.sha256(json.dumps(field, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        check(digests[field["field_id"]] == digest, f"field changed without review/spec synchronization: {field['field_id']}")
    check("C" in field_map["capex.items.amount"]["provenance_kinds"], "computed cost amount must allow C provenance")
    check(any("F-CAPEX-ITEM-AMOUNT" in item and "run_id" in item for item in field_map["capex.items.amount"]["validation"]), "computed cost amount must require upstream/formula/run evidence")
    for key in ("load.work_schedule", "load.meter_id", "load.meter_boundary", "load.quality_basis", "load.profile_attachment_id", "load.timezone", "load.monthly_bills", "finance.loan_agreement_id", "finance.cfads_definition"):
        field = field_map[key]
        check(field["required_level"]["L2"] == field["required_level"]["L3"] == "CONDITIONAL", f"unconditional load/debt requirement: {key}")
        check(field["conditional_rule_id"] in fields_document["conditional_rules"], f"unbound conditional requirement: {key}")
    start_pattern = field_map["tariff.periods.start_time"]["constraints"]["pattern"]
    end_pattern = field_map["tariff.periods.end_time"]["constraints"]["pattern"]
    check(all(re.fullmatch(start_pattern, value) for value in ("00:00", "23:59")) and not any(re.fullmatch(start_pattern, value) for value in ("24:00", "29:59", "12:60")), "invalid start-time catalog constraint")
    check(all(re.fullmatch(end_pattern, value) for value in ("00:00", "23:59", "24:00")) and not any(re.fullmatch(end_pattern, value) for value in ("24:01", "29:59", "12:60")), "invalid end-time catalog constraint")
    predecessors = field_map["schedule.tasks.predecessor_ids"]
    check(predecessors["type"] == "array" and predecessors["constraints"]["minItems"] == 0 and predecessors["constraints"]["uniqueItems"], "starting tasks must support confirmed empty dependency array")
    check(predecessors["constraints"]["items"]["type"] == "string" and predecessors["constraints"]["references"] == "schedule.tasks.task_id" and predecessors["constraints"]["rejectSelfReference"] and predecessors["constraints"]["rejectCycles"] and predecessors["constraints"]["perScalarItemProvenance"], "task reference/provenance contract incomplete")
    pv_types = set(contract["pv_types"])
    check(len(pv_types) == 9 and set(fields_document["pv_types"]) == pv_types, "nine engineering categories must remain distinct")
    required_provenance = {"field_id", "value", "unit", "provenance_kind", "source_id", "source_url_or_attachment", "source_section_or_cell", "measurement_period", "published_at", "retrieved_at", "effective_from", "effective_to", "geography", "status", "confidence_basis", "reviewer", "last_updated"}
    check(required_provenance <= set(fields_document["provenance_record"]["required_keys"]), "required per-value provenance missing")
    field_keys = {"field_id", "type", "unit", "constraints", "required_level", "provenance_kinds", "validation", "substitutable", "chapter_ids", "pv_types"}
    chapter_ids = set(contract["chapter_ids"])
    appendix_ids = set(contract["appendix_ids"])
    for field in fields:
        name = field["field_id"]
        check(field_keys <= field.keys(), f"incomplete field contract: {name}")
        check(bool(re.fullmatch(fields_document["field_id_pattern"], name)), f"invalid field ID: {name}")
        check(set(field["required_level"]) == {"L1", "L2", "L3"}, f"maturity levels missing: {name}")
        check(set(field["chapter_ids"]) <= chapter_ids, f"unknown field chapter: {name}")
        check(set(field["pv_types"]) <= pv_types and bool(field["pv_types"]), f"unknown/empty field category: {name}")

    formulas: list[dict[str, Any]] = []
    for name in contract["formula_files"]:
        formulas.extend(load_json(document_root / name)["formulas"])
    formula_ids = unique(formulas, "formula_id", "formula")
    bindings = load_json(document_root / "05-field-bindings.json")["bindings"]
    binding_ids = unique(bindings, "formula_field_id", "formula field binding")
    formula_keys = {"formula_id", "chinese_name", "english_name", "latex", "text_equation", "every_symbol_definition", "subscript_definition", "unit", "input_field_ids", "output_field_id", "calculation_boundary", "assumptions", "precedence", "source_reference", "sample_case", "test_id", "report_chapter_ids"}
    referenced_formula_fields: set[str] = set()
    for formula in formulas:
        name = formula["formula_id"]
        check(formula_keys <= formula.keys(), f"incomplete formula: {name}")
        check(bool(formula["every_symbol_definition"]) and bool(formula["subscript_definition"]), f"formula symbols or subscripts missing: {name}")
        for symbol in formula["every_symbol_definition"]:
            check(all(symbol.get(key) for key in ("symbol", "definition_zh", "unit")), f"symbol without definition/unit: {name}")
            if symbol.get("field_id"):
                referenced_formula_fields.add(symbol["field_id"])
        referenced_formula_fields.update(formula["input_field_ids"])
        referenced_formula_fields.add(formula["output_field_id"])
        check(set(formula["report_chapter_ids"]) <= chapter_ids, f"formula references unknown chapter: {name}")
    check(referenced_formula_fields == binding_ids, "formula field crosswalk incomplete or stale")
    for binding in bindings:
        name = binding["formula_field_id"]
        check(set(binding["input_field_ids"]) <= field_ids, f"binding references unknown input: {name}")
        check(set(binding["producer_formula_ids"] + binding["consumer_formula_ids"]) <= formula_ids, f"binding references unknown formula: {name}")
        check(bool(binding["input_field_ids"] or binding["producer_formula_ids"] or binding["constant_definition"]), f"unexplained formula field: {name}")
    groups = load_json(document_root / "05-formulas.json")["baseline_group_coverage"]
    check({group["baseline_group"] for group in groups} == set(range(1, 17)), "minimum 16 formula groups missing")
    for group in groups:
        check(set(group["formula_ids"]) <= formula_ids, "unknown formula in minimum group index")

    terms: list[dict[str, Any]] = []
    for name in contract["glossary_files"]:
        terms.extend(load_json(document_root / name)["terms"])
    term_ids = unique(terms, "term_id", "glossary")
    abbreviations = {term["abbreviation"] for term in terms if term.get("abbreviation")}
    minimum_terms = {"GHI", "DNI", "DHI", "POA", "GTI", "PVOUT", "PR", "DC", "AC", "STC", "CAPEX", "OPEX", "PPA", "NPV", "IRR", "LCOE", "DSCR", "CFADS", "SOC", "EPC", "GIS", "TMY"}
    check(minimum_terms <= abbreviations, "required bilingual terminology missing")
    for term in terms:
        check(all(term.get(key) for key in ("chinese_name", "english_name", "first_occurrence_form", "definition_zh")), f"incomplete bilingual term: {term['term_id']}")
        check(set(term["related_formula_ids"]) <= formula_ids, f"term references unknown formula: {term['term_id']}")
    for formula in formulas:
        linked = formula.get("glossary_term_ids", ["TERM-" + formula["formula_id"]])
        check(set(linked) <= term_ids, f"formula English name missing in glossary: {formula['formula_id']}")

    source_index = load_json(document_root / contract["source_index"])
    sources: list[dict[str, Any]] = []
    for source_set in source_index["source_sets"]:
        sources.extend(load_json(document_root / source_set["file"])[source_set["key"]])
    source_ids = unique(sources, "source_id", "source") | set(source_index["normative_sources"])
    check(len({source["url"] for source in sources}) == len(sources), "duplicate logical source URL across source sets; de-duplicate or state relation")
    for source in sources:
        check(all(source.get(key) is not None for key in ("source_id", "title", "url", "type", "license_status")), f"incomplete source record: {source['source_id']}")
    technical = load_json(document_root / "04-sources.json")
    stats = technical["statistics"]
    cohort = technical["sources"]
    for key, actual in {
        "discovered_registered_sources": len(cohort),
        "effective_body_or_metadata_verified_sources": sum(source["body_verified"] for source in cohort),
        "strict_full_text_readable_complete_publications": sum(source["full_text_readable"] for source in cohort),
        "structure_extracted_sources": sum(source["structure_extracted"] for source in cohort),
        "verified_specific_real_project_sources": sum(source["is_real_project"] for source in cohort),
        "license_requires_review_sources": sum(source["license_status"] == "REQUIRES_REVIEW" for source in cohort),
    }.items():
        check(stats[key] == actual, f"source statistic mismatch: {key}: declared {stats[key]}, actual {actual}")
    with (document_root / "04-source-chapter-comparison.csv").open(encoding="utf-8-sig", newline="") as stream:
        source_rows = list(csv.DictReader(stream))
    check(len(source_rows) == len(cohort), "source chapter comparison row count mismatch")

    outline = (document_root / "02-report-outline-18-chapters.md").read_text(encoding="utf-8")
    check(set(re.findall(r"^### (CH\d{2})\b", outline, re.M)) == chapter_ids, "18 chapter definitions incomplete")
    check(set(re.findall(r"^### (APP\d{2})\b", outline, re.M)) == appendix_ids, "13 appendix definitions incomplete")
    content_ids = re.findall(r"^\| ((?:CH|APP)\d{2}\.\d{2}) \|", outline, re.M)
    check(len(content_ids) == len(set(content_ids)), "duplicate report content IDs")
    check(len([key for key in content_ids if key.startswith("CH")]) == 100, "100 chapter subitems missing")
    check(len([key for key in content_ids if key.startswith("APP")]) == 26, "26 appendix subitems missing")
    for line in outline.splitlines():
        if re.match(r"^\| CH\d{2} \|", line):
            check(len(line.strip().strip("|").split("|")) == 10, "nine-category chapter applicability row incomplete")
    category_document = (document_root / "07-category-boundaries.md").read_text(encoding="utf-8")
    check(set(re.findall(r"^### CAT\d+ `([^`]+)`", category_document, re.M)) == pv_types, "category designs incomplete")
    sheets = contract["sheets"]
    sheet_ids = unique(sheets, "sheet_id", "sheet")
    check(sum(sheet["file_id"] == "F03" for sheet in sheets) == 19, "19 model workbook sheets missing")
    check(sum(sheet["file_id"] == "F04" for sheet in sheets) == 10, "10 provenance workbook sheets missing")
    for sheet in sheets:
        check(0 < len(sheet["physical_name"]) <= 31 and not re.search(r"[\\/*?:\[\]]", sheet["physical_name"]), f"invalid physical Excel sheet name: {sheet['sheet_id']}")
    dictionary_sheet = next(sheet for sheet in sheets if sheet["sheet_id"] == "S09")
    check(dictionary_sheet["logical_name"] == "变量/术语词典" and dictionary_sheet["physical_name"] == "变量-术语词典", "logical/physical sheet name exception must remain explicit")

    cases: list[dict[str, Any]] = []
    for name in contract["case_files"]:
        cases.extend(load_json(document_root / name)["cases"])
    case_ids = unique(cases, "test_id", "acceptance case")
    case_map = {case["test_id"]: case for case in cases}
    for case in cases:
        check(bool(case.get("expected") and case.get("method")), f"acceptance case without method/expectation: {case['test_id']}")
        if case["status"] == "PASS":
            check(bool(case.get("executor")) and safe_evidence(case.get("evidence") or ""), f"PASS without actual execution evidence: {case['test_id']}")
    for formula in formulas:
        check(formula["test_id"] in case_ids, f"formula test undefined: {formula['formula_id']}")
    with (document_root / "08-requirement-traceability.csv").open(encoding="utf-8-sig", newline="") as stream:
        matrix = list(csv.DictReader(stream))
    unique(matrix, "requirement_id", "requirement")
    check(len(matrix) == contract["matrix_rows"], "requirement matrix row count mismatch")
    statuses = {"PASS", "FAIL", "BLOCKED", "NOT_IMPLEMENTED", "NOT_STARTED", "NOT_TESTED"}
    for row in matrix:
        rid = row["requirement_id"]
        check(bool(row["source_text"] and row["acceptance_criterion"] and row["stage"]), f"missing requirement/criterion/stage: {rid}")
        check(parts(row["pv_type"]) <= pv_types and bool(row["pv_type"]), f"unknown/empty matrix category: {rid}")
        check(parts(row["chapter_id"]) <= chapter_ids | appendix_ids, f"unknown matrix chapter: {rid}")
        check(parts(row["user_input_ids"]) <= field_ids, f"unknown matrix input: {rid}")
        check(parts(row["data_source_ids"]) <= source_ids, f"unknown matrix source: {rid}")
        check(parts(row["formula_ids"]) <= formula_ids, f"unknown matrix formula: {rid}")
        check(parts(row["formula_field_ids"]) <= binding_ids, f"unknown formula field binding: {rid}")
        check(parts(row["output_file"]) <= set(contract["outputs"]) and parts(row["sheet"]) <= sheet_ids, f"unknown matrix output/sheet: {rid}")
        check(row["test_id"] in case_ids, f"undefined matrix test: {rid}")
        if rid.startswith("R-FIELD-") or rid.startswith("R-SHEET-"):
            check(case_map[row["test_id"]]["expected"] == row["acceptance_criterion"], f"field/sheet acceptance specification drift: {rid}")
        check(row["status"] in statuses and row["baseline_status"] == "FROZEN", f"invalid requirement status: {rid}")
        if row["status"] == "PASS":
            check(safe_evidence(row["evidence"]) and case_map[row["test_id"]]["status"] == "PASS", f"requirement PASS lacks verified evidence: {rid}")
    expected_lines = {str(index): line for index, line in enumerate(original.splitlines(), 1) if line.strip() and not line.lstrip().startswith(("#", "```"))}
    source_lines = {row["source_line"]: row["source_text"] for row in matrix if row["source_line"]}
    check(source_lines == expected_lines, "original baseline line coverage changed or incomplete")
    check({row["requirement_id"][8:] for row in matrix if row["requirement_id"].startswith("R-FIELD-")} == field_ids, "input requirements coverage incomplete")
    check({row["requirement_id"][10:] for row in matrix if row["requirement_id"].startswith("R-FORMULA-")} == formula_ids, "formula requirements coverage incomplete")
    check({row["requirement_id"][2:] for row in matrix if row["requirement_id"].startswith("R-TERM-")} == term_ids, "glossary requirements coverage incomplete")

    protection = load_json(document_root / "00-protected-artifacts.json")
    for entry in protection["files"]:
        path = root / entry["path"]
        check(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"], f"protected historical file changed: {entry['path']}")

    product_rows = [row for row in matrix if row["scope_kind"] == "PRODUCT"]
    release_blockers = [key for key, status in contract["product_gates"].items() if status != "PASS"]
    if any(row["status"] != "PASS" for row in product_rows):
        release_blockers.append("UNVERIFIED_PRODUCT_REQUIREMENTS")
    document_status = "PASS" if not errors else "FAIL"
    release_status = "PASS" if not errors and not release_blockers else "BLOCKED"
    return {
        "scope": "Phase 0/1 persisted documentation/index integrity only; no calculation/rendering/platform acceptance",
        "mode": "release" if release else "baseline",
        "status": release_status if release else document_status,
        "baseline_document_integrity": document_status,
        "checks": checks,
        "passed_checks": checks - len(errors),
        "failed_checks": len(errors),
        "errors": errors,
        "counts": {"requirements": len(matrix), "original_baseline_lines_traced": len(source_lines), "fields": len(fields), "formulas": len(formulas), "formula_field_bindings": len(bindings), "glossary_terms": len(terms), "acceptance_specifications": len(cases), "source_records": len(sources), "chapters": len(chapter_ids), "chapter_subitems": 100, "appendices": len(appendix_ids), "appendix_subitems": 26, "core_workbook_sheets": len(sheets), "protected_files": len(protection["files"])},
        "product_gates": contract["product_gates"],
        "release_status": release_status,
        "release_blockers": release_blockers,
        "not_claimed": ["numerical correctness", "authentic project data", "four actual deliverables", "WorkBuddy installation or invocation", "platform review", "OS sandbox security"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--release", action="store_true")
    arguments = parser.parse_args()
    try:
        result = verify(arguments.root.resolve(), release=arguments.release)
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as exc:
        # No customer data is accepted; nevertheless avoid emitting source contents.
        result = {"status": "FAIL", "error_type": type(exc).__name__, "message": str(exc), "release_status": "BLOCKED"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
