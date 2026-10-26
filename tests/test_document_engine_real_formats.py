from __future__ import annotations

from pathlib import Path

import pytest

from wangbin_document_engine import DocumentEngine

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.real_format
@pytest.mark.parametrize(
    ("filename", "marker"),
    [
        ("sample.pdf", "WANGBIN PDF MARKER"),
        ("sample.docx", "WANGBIN DOCX MARKER"),
        ("sample.xlsx", "Name"),
        ("sample.pptx", "WANGBIN PPTX MARKER"),
        ("sample.html", "WANGBIN HTML MARKER"),
        ("sample.txt", "WANGBIN TXT MARKER"),
        ("sample.md", "WANGBIN MARKDOWN MARKER"),
    ],
)
def test_real_format_extraction(filename: str, marker: str) -> None:
    result = DocumentEngine().parse_file(FIXTURES / filename, FIXTURES)
    assert result.status.startswith("success"), result.error
    assert marker in result.text, result.text[:500]


def test_sections_are_extracted_from_markdown() -> None:
    result = DocumentEngine().parse_file(FIXTURES / "sample.md", FIXTURES)
    assert result.sections[0]["title"] == "WANGBIN MARKDOWN MARKER"


def test_empty_file_is_reported_without_fabrication() -> None:
    result = DocumentEngine().parse_file(FIXTURES / "empty.txt", FIXTURES)
    assert result.status in {"success_with_warning", "failed"}
    if result.status == "success_with_warning":
        assert result.text == ""
        assert result.quality_notes


def test_corrupt_and_mismatched_documents_fail() -> None:
    corrupt = DocumentEngine().parse_file(FIXTURES / "damaged.pdf", FIXTURES)
    mismatch = DocumentEngine().parse_file(FIXTURES / "mismatched.pdf", FIXTURES)
    assert corrupt.status == "failed"
    assert mismatch.status == "failed"
    assert mismatch.error["code"] == "MISMATCHED_EXTENSION"


def test_unicode_and_special_names_are_processed() -> None:
    engine = DocumentEngine()
    chinese = engine.parse_file(FIXTURES / "中文 文件.txt", FIXTURES)
    special = engine.parse_file(FIXTURES / "special [name] #1.txt", FIXTURES)
    assert chinese.status.startswith("success")
    assert special.status.startswith("success")
