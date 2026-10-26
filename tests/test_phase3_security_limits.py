"""Regression checks for the bounded Phase 3 runtime paths."""
from __future__ import annotations

import json
import multiprocessing
import os
import subprocess
import sys
from pathlib import Path

import pytest
from openpyxl import Workbook
from openpyxl.worksheet._writer import ALL_TEMP_FILES

from wangbin_document_engine import DocumentEngine, SecurityPolicy, SpreadsheetService
from wangbin_document_engine.errors import ExportFailure, SecurityViolation
from wangbin_document_engine.metadata import publish_new_file
from wangbin_document_engine.resource_slots import hold_resource_slot

FIXTURES = Path(__file__).parent / "fixtures"


def test_parser_uses_private_input_snapshot_and_cleans_it(tmp_path: Path) -> None:
    source = tmp_path / "sample.txt"
    source.write_text("original content", encoding="utf-8")
    with SecurityPolicy().snapshot_input(source, tmp_path) as staged:
        assert staged.read_text(encoding="utf-8") == "original content"
        assert staged != source
        source.write_text("changed content", encoding="utf-8")
        assert staged.read_text(encoding="utf-8") == "original content"
    assert not staged.exists()


def test_capacity_is_enforced_across_cli_processes() -> None:
    with hold_resource_slot(), hold_resource_slot():
        busy = subprocess.run(
            [sys.executable, "-m", "wangbin_document_cli.main", "parse", "--input", str(FIXTURES / "sample.txt"), "--input-root", str(FIXTURES)],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "services" / "document-engine" / "src"),
                 "WANGBIN_ENGINE_SRC": "", "PYTHONNOUSERSITE": "1"},
        )
        assert busy.returncode == 1
        assert json.loads(busy.stdout)["error"]["code"] == "RESOURCE_BUSY"
    available = DocumentEngine().parse_file(FIXTURES / "sample.txt", FIXTURES)
    assert available.status == "success", available.error


def test_spreadsheet_limits_fail_without_output(tmp_path: Path) -> None:
    policy = SecurityPolicy(max_spreadsheet_rows=1)
    result = SpreadsheetService(policy).deduplicate(FIXTURES / "sample.xlsx", FIXTURES, tmp_path)
    assert result.status == "failed" and result.error["code"] == "SPREADSHEET_ROW_LIMIT"
    assert not list(tmp_path.iterdir())


def test_spreadsheet_cell_limit_applies_to_inspection_and_export(tmp_path: Path) -> None:
    service = SpreadsheetService(SecurityPolicy(max_spreadsheet_cells=2))
    with pytest.raises(SecurityViolation) as error:
        service.inspect(FIXTURES / "sample.xlsx", FIXTURES)
    assert error.value.code == "SPREADSHEET_CELL_LIMIT"
    result = service.deduplicate(FIXTURES / "sample.xlsx", FIXTURES, tmp_path)
    assert result.status == "failed" and result.error["code"] == "SPREADSHEET_CELL_LIMIT"
    assert not list(tmp_path.iterdir())


def test_export_size_limit_cleans_temporary_file(tmp_path: Path) -> None:
    result = SpreadsheetService(SecurityPolicy(max_export_bytes=100)).deduplicate(FIXTURES / "sample.xlsx", FIXTURES, tmp_path)
    assert result.status == "failed" and result.error["code"] == "EXPORT_TOO_LARGE"
    assert not list(tmp_path.iterdir())


def test_publish_new_file_never_overwrites_existing_user_output(tmp_path: Path) -> None:
    temporary = tmp_path / "temporary.xlsx"
    target = tmp_path / "existing.xlsx"
    temporary.write_bytes(b"candidate")
    target.write_bytes(b"original")
    with pytest.raises(ExportFailure) as error:
        publish_new_file(temporary, target)
    assert error.value.code == "OUTPUT_CONFLICT"
    assert target.read_bytes() == b"original" and temporary.read_bytes() == b"candidate"


def test_rejection_cleans_openpyxl_scratch(tmp_path: Path) -> None:
    before = set(ALL_TEMP_FILES)
    input_root = tmp_path / "input"
    input_root.mkdir()
    source = input_root / "input.xlsx"
    workbook = Workbook()
    workbook.active.append(["header"])
    workbook.active.append(["short"])
    workbook.active.append(["x" * 200])
    workbook.save(source)
    workbook.close()
    output = tmp_path / "output"
    output.mkdir()
    result = SpreadsheetService(SecurityPolicy(max_export_bytes=100)).deduplicate(source, input_root, output)
    assert result.status == "failed" and result.error["code"] == "SPREADSHEET_CELL_LIMIT"
    assert not list(output.iterdir())
    assert set(ALL_TEMP_FILES) == before


def test_timeout_reaps_parser_process_and_releases_capacity() -> None:
    before = {child.pid for child in multiprocessing.active_children()}
    result = DocumentEngine(SecurityPolicy(timeout_seconds=0.001)).parse_file(FIXTURES / "sample.pdf", FIXTURES)
    assert result.status == "failed" and result.error["code"] == "PARSER_TIMEOUT"
    assert {child.pid for child in multiprocessing.active_children()} == before
    assert DocumentEngine().parse_file(FIXTURES / "sample.txt", FIXTURES).status == "success"
