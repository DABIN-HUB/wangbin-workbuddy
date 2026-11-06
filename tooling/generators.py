"""Reusable local generators for WorkBuddy asset candidates."""
from __future__ import annotations

import json
from pathlib import Path

import yaml


def generate_skill(target: Path, *, skill_id: str, display_name: str, display_name_en: str, author: str, version: str, description_zh: str, description_en: str) -> None:
    target.mkdir(parents=True, exist_ok=True)
    (target / "references").mkdir(exist_ok=True)
    (target / "scripts").mkdir(exist_ok=True)
    (target / "templates").mkdir(exist_ok=True)
    fields = {
        "name": skill_id,
        "display_name": display_name,
        "display_name_en": display_name_en,
        "description": description_zh,
        "description_zh": description_zh,
        "description_en": description_en,
        # New candidates explicitly opt into the user-facing migration gate.
        "user_facing_standard": "v1",
        "examples_zh": ["请整理这份文件中的重点内容", "请比较两份文件的关键信息差异", "请导出便于查看的整理结果"],
        "examples_en": ["Please summarize the key points in this file", "Please compare key information across two files", "Please export an organized result for review"],
        "version": version,
        "author": author,
    }
    frontmatter = "---\n" + yaml.safe_dump(fields, allow_unicode=True, sort_keys=False) + (
        f"---\n\n# {display_name} / {display_name_en}\n\n"
        "## Preparation / 准备\n"
        "准备用户已授权且内容可读取的输入文件，并说明期望结果。\n\n"
        "## Usage / 使用\n"
        "用自然语言描述要完成的用户目标，并提供相关文件或资料。\n\n"
        "## Processing / 处理\n"
        "按目标整理可读取内容；遇到缺失或不清晰的信息时保留事实并提示用户。\n\n"
        "## Outputs / 输出\n"
        "返回用户可查看的整理结果，并说明结果所依据的输入范围。\n\n"
        "## Limits / 限制\n"
        "不能替代人工核对，也不支持未提供内容或无法读取格式的准确判断。\n"
    )
    (target / "SKILL.md").write_text(frontmatter, encoding="utf-8")
    (target / "manifest.json").write_text(json.dumps({"id": skill_id, "version": version, "author": author}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
