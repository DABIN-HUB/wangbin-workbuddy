from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "packages" / "skills" / "wangbin-tender-analyzer" / "scripts" / "analyze_tender.py"
EXAMPLE_INPUT = ROOT / "packages" / "skills" / "wangbin-tender-analyzer" / "examples" / "fictional-tender.txt"
EXPECTED_OUTPUT = ROOT / "packages" / "skills" / "wangbin-tender-analyzer" / "examples" / "fictional-tender.expected.json"


def load_analyzer():
    spec = importlib.util.spec_from_file_location("tender_analyzer", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _evidence_lines(result: dict, category: str) -> list[dict]:
    return [item["evidence"] for item in result[category] if item.get("evidence")]


def test_analyze_extracts_four_categories_with_source_line_evidence() -> None:
    analyzer = load_analyzer()
    text = (
        "招标项目：城市档案数字化服务\n"
        "资格条件：投标人须具有独立法人资格，营业执照在有效期内。\n"
        "资格条件：近三年完成过1个同类项目，金额不低于100万元。\n"
        "评分办法：技术方案满分30分，其中实施计划10分。\n"
        "技术要求：系统应支持PDF/A格式，检索响应时间不超过2秒。\n"
        "投标截止时间：2026年11月20日10:00。\n"
        "履约保证金：金额以采购人通知为准。\n"
    )

    result = analyzer.analyze(text, "fictional.txt")

    assert result["source_name"] == "fictional.txt"
    assert {"eligibility", "scoring", "technical", "dates", "checklist", "risks", "evidence"} <= result.keys()
    assert len(result["eligibility"]) == 2
    assert result["eligibility"][0]["status"] == "待核实"
    assert result["eligibility"][0]["evidence"] == {
        "source_name": "fictional.txt",
        "line": 2,
        "quote": "资格条件：投标人须具有独立法人资格，营业执照在有效期内。",
        "label": "redacted excerpt",
    }

    assert result["scoring"][0]["max_score"] == 30
    assert result["scoring"][0]["awarded_score"] is None
    assert result["scoring"][0]["status"] == "待核实"
    assert result["scoring"][0]["evidence"]["line"] == 4
    assert result["scoring"][0]["evidence"]["quote"] == "评分办法：技术方案满分30分，其中实施计划10分。"

    assert result["technical"][0]["status"] == "待核实"
    assert result["technical"][0]["evidence"]["line"] == 5
    assert result["technical"][0]["evidence"]["quote"] == "技术要求：系统应支持PDF/A格式，检索响应时间不超过2秒。"

    deadline = next(item for item in result["dates"] if item["name"] == "投标截止时间")
    assert deadline["value"] == "2026年11月20日10:00"
    assert deadline["evidence"]["line"] == 6
    assert deadline["evidence"]["quote"] == "投标截止时间：2026年11月20日10:00。"

    assert any(item["name"] == "开标时间" and item["status"] == "待核实" and item["evidence"] is None for item in result["dates"])
    assert any("以采购人通知为准" in risk["description"] and risk["status"] == "待核实" for risk in result["risks"])
    assert all(evidence["quote"] in text for evidence in result["evidence"])
    assert all(evidence["line"] == text.splitlines().index(evidence["quote"]) + 1 for evidence in result["evidence"])


def test_analyze_marks_ambiguous_and_absent_information_as_pending_verification() -> None:
    analyzer = load_analyzer()

    result = analyzer.analyze("评分标准：相关业绩分值另行通知。\n", "ambiguous.md")

    assert result["scoring"][0]["status"] == "待核实"
    assert result["scoring"][0]["max_score"] is None
    assert result["scoring"][0]["evidence"]["line"] == 1
    assert result["dates"]
    assert all(item["status"] == "待核实" for item in result["dates"])
    assert any(item["status"] == "待核实" for item in result["checklist"])
    assert any("未发现" in risk["description"] for risk in result["risks"])


def test_result_declares_scanned_and_complex_layout_limitations() -> None:
    analyzer = load_analyzer()

    result = analyzer.analyze("技术要求见附件表格。\n", "layout.pdf")

    assert result["limitations"]
    limitation_text = " ".join(result["limitations"])
    assert "扫描" in limitation_text
    assert "复杂版式" in limitation_text
    assert "表格" in limitation_text
    assert result["technical"][0]["status"] == "待核实"
    assert result["technical"][0]["evidence"]["quote"] == "技术要求见附件表格。"


def test_example_cli_output_matches_checked_in_expected_json() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(EXAMPLE_INPUT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    actual = json.loads(completed.stdout)
    expected = json.loads(EXPECTED_OUTPUT.read_text(encoding="utf-8"))
    assert actual == expected
    assert completed.stderr == ""


def test_cli_rejects_non_utf8_input_without_echoing_document_content(tmp_path: Path) -> None:
    private_marker = "PRIVATE-TENDER-CONTENT"
    source = tmp_path / "bad.txt"
    source.write_bytes(private_marker.encode("utf-16"))

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(source)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    assert completed.returncode != 0
    assert "INVALID_UTF8" in completed.stderr
    assert private_marker not in completed.stdout
    assert private_marker not in completed.stderr


def test_cli_rejects_unsupported_non_regular_and_oversized_inputs_without_leaking_path_or_content(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    private_marker = "PRIVATE-TENDER-CONTENT"

    unsupported = tmp_path / "private.pdf"
    unsupported.write_bytes(private_marker.encode("utf-8"))
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(unsupported)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert completed.returncode == 2
    assert "INPUT_TYPE_UNSUPPORTED" in completed.stderr
    assert private_marker not in completed.stdout + completed.stderr
    assert str(unsupported) not in completed.stdout + completed.stderr

    directory = tmp_path / "input.txt"
    directory.mkdir()
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(directory)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert completed.returncode == 2
    assert "INPUT_NOT_REGULAR" in completed.stderr

    oversized = tmp_path / "oversized.txt"
    oversized.write_bytes(b"x" * (analyzer.MAX_INPUT_BYTES + 1))
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(oversized)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert completed.returncode == 2
    assert "INPUT_TOO_LARGE" in completed.stderr

    symlink = tmp_path / "link.txt"
    try:
        symlink.symlink_to(unsupported)
    except OSError:
        pytest.skip("symlink creation is unavailable on this Windows runner")
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--input", str(symlink)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert completed.returncode == 2
    assert "INPUT_SYMLINK" in completed.stderr


def test_result_uses_basename_truthful_privacy_and_bounded_redacted_evidence() -> None:
    analyzer = load_analyzer()
    private_marker = "张三"
    text = (
        "联系人：张三，电话：13800138000，邮箱：secret@example.com；"
        "技术要求：系统应支持PDF/A格式。\n"
    )

    result = analyzer.analyze(text, r"C:\private\source\customer-tender.txt")
    serialized = json.dumps(result, ensure_ascii=False)

    assert result["source_name"] == "customer-tender.txt"
    assert result["privacy"]["execution_scope"] == "local_script_only"
    assert result["privacy"]["authorization_verified"] is False
    assert result["privacy"]["remote_upload"] is False
    assert result["privacy"]["platform_installation"] == "BLOCKED/NOT_TESTED"
    assert "authorized_input_only" not in result["privacy"]
    assert private_marker not in serialized
    assert "secret@example.com" not in serialized
    for evidence in result["evidence"]:
        assert evidence["label"] == "redacted excerpt"
        assert len(evidence["quote"]) <= analyzer.MAX_EVIDENCE_CHARS

    long_result = analyzer.analyze("技术要求：" + "x" * 500 + "。\n", "long.txt")
    assert len(long_result["technical"][0]["evidence"]["quote"]) == analyzer.MAX_EVIDENCE_CHARS


def test_duplicate_and_variant_deadlines_are_preserved_and_risk_links_all_evidence() -> None:
    analyzer = load_analyzer()
    text = (
        "投标文件递交截止日期：2026年11月20日10:00。\n"
        "投标截止时间：2026年11月21日10:00。\n"
        "开标日期：2026-11-21 10:30。\n"
    )

    result = analyzer.analyze(text, "dates.md")
    deadlines = [item for item in result["dates"] if item["name"] == "投标截止时间"]
    assert [item["value"] for item in deadlines] == ["2026年11月20日10:00", "2026年11月21日10:00"]
    assert [item["evidence"]["line"] for item in deadlines] == [1, 2]
    conflict = next(risk for risk in result["risks"] if risk["name"] == "日期冲突")
    assert {item["line"] for item in conflict["evidence"]} == {1, 2}
    opening = next(item for item in result["dates"] if item["name"] == "开标时间")
    assert opening["value"] == "2026-11-21 10:30"


def test_checklist_is_item_level_and_covers_submission_materials() -> None:
    analyzer = load_analyzer()
    text = (
        "投标保证金：提交金额以采购人通知为准。\n"
        "须填写投标函和承诺函。\n"
        "附件：营业执照、业绩证明。\n"
        "投标文件须密封后在截止时间前递交。\n"
        "投标文件须法定代表人签字并加盖公章。\n"
    )

    result = analyzer.analyze(text, "response.txt")
    checklist_names = " ".join(item["name"] for item in result["checklist"])
    for keyword in ("保证金", "表单", "附件", "提交", "签字"):
        assert keyword in checklist_names
    evidence_lines = {
        item["evidence"]["line"]
        for item in result["checklist"]
        if item.get("evidence")
    }
    assert {1, 2, 3, 4, 5} <= evidence_lines
    assert all(item["status"] == "待核实" for item in result["checklist"])


def test_missing_important_dates_are_explicit_risks() -> None:
    analyzer = load_analyzer()

    result = analyzer.analyze("项目说明：请按采购文件准备响应文件。\n", "missing.md")
    descriptions = " ".join(risk["description"] for risk in result["risks"])
    assert "投标截止时间" in descriptions
    assert "开标时间" in descriptions
    assert "报名截止时间" in descriptions
    assert "投标保证金截止时间" in descriptions


@pytest.mark.parametrize("name", ["SKILL.md", "scripts/analyze_tender.py"])
def test_required_skill_files_exist(name: str) -> None:
    assert (SCRIPT.parent.parent / name).is_file()
