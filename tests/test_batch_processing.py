from __future__ import annotations

from pathlib import Path

from wangbin_document_engine import DocumentEngine

FIXTURES = Path(__file__).parent / "fixtures"


def test_batch_continues_after_one_failure() -> None:
    result = DocumentEngine().parse_many([FIXTURES / "sample.txt", FIXTURES / "missing.txt", FIXTURES / "sample.md"], FIXTURES)
    assert result.status == "partial_failure"
    assert result.success_count == 2
    assert result.failure_count == 1
    assert result.items[1].error["code"] == "FILE_NOT_FOUND"


def test_batch_limits_are_reported() -> None:
    from wangbin_document_engine.security import SecurityPolicy

    engine = DocumentEngine(SecurityPolicy(max_files=1))
    result = engine.parse_many([FIXTURES / "sample.txt", FIXTURES / "sample.md"], FIXTURES)
    assert result.status == "failed"
    assert all(item.error["code"] == "TOO_MANY_FILES" for item in result.items)
