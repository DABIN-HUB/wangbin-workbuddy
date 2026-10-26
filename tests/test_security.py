from __future__ import annotations

from pathlib import Path

from wangbin_document_engine import DocumentEngine, SecurityPolicy

FIXTURES = Path(__file__).parent / "fixtures"


def test_path_traversal_is_rejected(tmp_path: Path) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    result = DocumentEngine().parse_file(outside, FIXTURES)
    assert result.status == "failed"
    assert result.error["code"] == "PATH_OUTSIDE_ROOT"


def test_file_size_limit_is_enforced() -> None:
    policy = SecurityPolicy(max_file_bytes=8)
    result = DocumentEngine(policy).parse_file(FIXTURES / "sample.txt", FIXTURES)
    assert result.status == "failed"
    assert result.error["code"] == "FILE_TOO_LARGE"


def test_zip_container_limits_are_enforced() -> None:
    policy = SecurityPolicy(max_uncompressed_bytes=10)
    result = DocumentEngine(policy).parse_file(FIXTURES / "sample.docx", FIXTURES)
    assert result.status == "failed"
    assert result.error["code"] in {"ZIP_ENTRY_TOO_LARGE", "ZIP_TOO_LARGE"}


def test_symlink_is_rejected_when_supported(tmp_path: Path) -> None:
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(FIXTURES / "sample.txt")
    except (OSError, NotImplementedError):
        import pytest
        pytest.skip("当前 Windows 环境未允许创建符号链接")
    result = DocumentEngine().parse_file(link, tmp_path)
    assert result.status == "failed"
    assert result.error["code"] == "SYMLINK_INPUT"
