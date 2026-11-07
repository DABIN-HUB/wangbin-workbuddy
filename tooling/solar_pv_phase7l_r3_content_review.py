"""Independent structural/content-risk readback of a generated PV Word report.

This audit records actual Word text for every outlined item. Its machine findings
are review prompts, never a professional approval or a rendered-page verdict.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

_ID = re.compile(r"^(CH\d{2}\.\d{2}|APP\d{2}\.\d{2})\s")
_FORMULA = re.compile(r"^F-[A-Z0-9-]+\s")
_GENERIC = (
    "本项尚未形成可引用的项目直接结果",
    "本项尚不能形成无条件工程、合规或投资认可",
    "不能以某结果证明某项条件",
    "某参数是多少",
)


def review(docx_file: Path, checklist_file: Path) -> dict:
    source = json.loads(checklist_file.read_text(encoding="utf-8"))
    expected = {row["id"]: row for row in source["records"]}
    if len(expected) != 126 or len(source["records"]) != 126:
        raise ValueError("EXPECTED_126_UNIQUE_OUTLINE_ITEMS")
    document = Document(docx_file)
    items: dict[str, list[str]] = {}
    formulas: dict[str, list[str]] = {}
    active: str | None = None
    formula: str | None = None
    for block in document.iter_inner_content():
        text = block.text.strip() if isinstance(block, Paragraph) else "\n".join(
            " | ".join(cell.text.strip() for cell in row.cells) for row in block.rows
        ).strip() if isinstance(block, Table) else ""
        if isinstance(block, Paragraph):
            item_match = _ID.match(text) if block.style.name.startswith("Heading") else None
            formula_match = _FORMULA.match(text) if block.style.name.startswith("Heading") else None
            if item_match:
                active = item_match.group(1)
                if active in items:
                    raise ValueError(f"DUPLICATE_OUTLINE_HEADING:{active}")
                items[active] = []
                formula = None
                continue
            if formula_match:
                formula = text.split(" ", 1)[0]
                formulas.setdefault(formula, [])
                active = None
                continue
            if block.style.name == "Heading 1":
                active = None
                formula = None
        if text and active:
            items[active].append(text)
        if text and formula:
            formulas[formula].append(text)
    if set(items) != set(expected):
        raise ValueError(f"OUTLINE_MISMATCH:missing={sorted(set(expected)-set(items))};extra={sorted(set(items)-set(expected))}")
    chapters = sum(item.startswith("CH") for item in items)
    appendices = len(items) - chapters
    if (chapters, appendices) != (100, 26):
        raise ValueError("OUTLINE_CATEGORY_COUNT_MISMATCH")
    normalized = defaultdict(list)
    records = []
    for key, expected_row in expected.items():
        body = "\n".join(items[key])
        flags = []
        if not body:
            flags.append("EMPTY_GENERATED_BODY")
        if len(body) < 70:
            flags.append("THIN_BODY_REVIEW_REQUIRED")
        if any(s in body for s in _GENERIC):
            flags.append("GENERIC_CAVEAT_REVIEW_REQUIRED")
        if re.search(r"(?:factory-roof calculation demo|ground PV calculation demo)\s*\(no real site\)", body, re.I):
            flags.append("RAW_ENGLISH_DEMO_NAME")
        if re.search(r"(?:IRR|内部收益率)[^。；\n]{0,35}%\s*(?:%|百分比)", body):
            flags.append("POSSIBLE_DUPLICATE_PERCENT_UNIT")
        canonical_hash = expected_row.get("canonical_result_hash")
        if canonical_hash != source["identity"]["result_hash"]:
            flags.append("CLAIM_RESULT_IDENTITY_MISMATCH")
        normalized[re.sub(r"[\d\s,.，。；;:：%]+", "", body)].append(key)
        records.append({
            "id": key, "title": expected_row["title"], "actual_word_body": body,
            "actual_text_characters": len(body),
            "input_field_ids": expected_row.get("input_field_ids", []),
            "metric_ids": expected_row.get("metric_ids", []),
            "source_ids": expected_row.get("source_ids", []),
            "formula_ids": expected_row.get("supporting_formula_ids", []),
            "machine_review_flags": flags,
            "professional_review_status": "INDEPENDENT_HUMAN_REVIEW_REQUIRED",
            "review_opinion": "文本与证据索引已记录；机器检查不能证明工程判断或版面可接受。"
            if not flags else "需核查：" + "、".join(flags),
        })
    for keys in normalized.values():
        if len(keys) > 1:
            for record in records:
                if record["id"] in keys:
                    record["machine_review_flags"].append("DUPLICATE_BODY_GROUP")
                    record["review_opinion"] += "；与" + "、".join(k for k in keys if k != record["id"]) + "正文近重复"
    return {
        "schema_version": "solar-pv-phase7l-r3-independent-content-readback/1.0.0",
        "docx_sha256": sha256(docx_file.read_bytes()).hexdigest(),
        "canonical_result_hash": source["identity"]["result_hash"],
        "status": "STRUCTURAL_READBACK_COMPLETE_PROFESSIONAL_REVIEW_REQUIRED",
        "rendered_page_status": "NOT_VERIFIED_BY_THIS_AUDIT",
        "counts": {"chapters": chapters, "appendices": appendices, "formula_groups": len(formulas),
                   "items_flagged": sum(bool(r["machine_review_flags"]) for r in records)},
        "formula_review": [{"formula_id": key, "actual_word_body": "\n".join(body),
                            "review_status": "SYMBOL_AND_APPLICABILITY_REVIEW_REQUIRED"}
                           for key, body in formulas.items()],
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path)
    parser.add_argument("checklist", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = review(args.docx, args.checklist)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "counts": result["counts"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
