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
        "examples_zh": ["请处理这个文档"],
        "examples_en": ["Process this document"],
        "version": version,
        "author": author,
    }
    frontmatter = "---\n" + yaml.safe_dump(fields, allow_unicode=True, sort_keys=False) + (
        f"---\n\n# {display_name}\n\n请根据任务协议执行，不要伪造未读取到的内容。\n"
    )
    (target / "SKILL.md").write_text(frontmatter, encoding="utf-8")
    (target / "manifest.json").write_text(json.dumps({"id": skill_id, "version": version, "author": author}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
