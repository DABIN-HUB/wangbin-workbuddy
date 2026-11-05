from pathlib import Path

from typing import Any

import pytest

from tooling.validators import Finding
from tooling.validators.project_validator import validate_user_facing_standard


SECTIONS = "\n".join([
    "## Preparation / 准备\n准备一个已授权的 PDF、Excel 或 CSV 文件。",
    "## Usage / 使用\n描述你希望整理的用户目标。",
    "## Processing / 处理\n按用户选择处理内容并保留原始事实。",
    "## Outputs / 输出\n输出可供用户查看的结果文件。",
    "## Limits / 边界\n不能保证复杂布局和未提供内容的准确性。",
])


def front(**overrides):
    data = {
        "display_name": "文档整理",
        "display_name_en": "Document Organizer",
        "description": "帮助用户整理已授权的办公文件。",
        "description_en": "Help users organize authorized office files.",
        "user_facing_standard": "v1",
        "examples_zh": ["请整理这份销售报表中的重点", "请比较两份客户名单的差异", "请导出按月份汇总的结果"],
        "examples_en": ["Please summarize the key points in this sales report", "Please compare the differences between two customer lists", "Please export the results grouped by month"],
    }
    data.update(overrides)
    return data


def run(tmp_path: Path, data: Any, body: str = SECTIONS):
    path = tmp_path / "SKILL.md"
    path.write_text(body, encoding="utf-8")
    checks: list[dict] = []
    findings: list[Finding] = []
    validate_user_facing_standard(data, path, checks, findings)
    return {item["name"]: item["status"] for item in checks}, findings


def test_valid_bilingual_copy_and_canonical_sections(tmp_path):
    checks, findings = run(tmp_path, front())
    assert checks["skill.USER_DESCRIPTION_PASS"] == "PASS"
    assert checks["skill.USER_EXAMPLES_PASS"] == "PASS"
    assert checks["skill.USER_SECTIONS_PASS"] == "PASS"
    assert checks["skill.capability_boundary_review"] == "NOT_TESTED"
    assert not findings


@pytest.mark.parametrize("bad", [
    {"examples_zh": ["请整理这份销售报表中的重点"]},
    {"examples_zh": ["请整理这份销售报表中的重点"] * 3},
    {"examples_en": ["Please summarize the key points in this sales report"] * 3},
    {"examples_zh": ["请处理这个文档", "   请处理   这个文档。", "请导出按月份汇总的结果"]},
    {"examples_en": ["Please compare the differences between two customer lists", "Please compare the differences between two customer lists!", "Please export the results grouped by month"]},
    {"examples_zh": ["请运行 python 脚本处理这份文件", "请比较两份客户名单的差异", "请导出按月份汇总的结果"]},
    {"examples_en": ["Please guarantee perfect results on any platform", "Please compare two customer lists carefully", "Please export the results grouped by month"]},
])
def test_examples_reject_quantity_duplicate_terminology_and_claims(tmp_path, bad):
    checks, findings = run(tmp_path, front(**bad))
    assert checks["skill.USER_EXAMPLES_PASS"] == "FAIL"
    assert any(item.code == "USER_EXAMPLES_PASS" for item in findings)


def test_yaml_mapping_and_missing_limits_are_failures(tmp_path):
    checks, findings = run(tmp_path, [])
    assert checks["skill.USER_DESCRIPTION_PASS"] == "FAIL"
    assert findings
    body = SECTIONS.replace("不能保证复杂布局和未提供内容的准确性。", "")
    checks, findings = run(tmp_path, front(), body)
    assert checks["skill.USER_SECTIONS_PASS"] == "FAIL"
