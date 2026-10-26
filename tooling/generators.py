"""Reusable local generators for WorkBuddy asset candidates."""
from __future__ import annotations

import json
from pathlib import Path


def generate_skill(target: Path, *, skill_id: str, display_name: str, display_name_en: str, author: str, version: str, description_zh: str, description_en: str) -> None:
    target.mkdir(parents=True, exist_ok=True)
    (target / "references").mkdir(exist_ok=True)
    (target / "scripts").mkdir(exist_ok=True)
    (target / "templates").mkdir(exist_ok=True)
    frontmatter = "\n".join([
        "---",
        f"name: {skill_id}",
        f"display_name: {display_name}",
        f"display_name_en: {display_name_en}",
        f"description: {description_zh}",
        f"description_zh: {description_zh}",
        f"description_en: {description_en}",
        "examples_zh:",
        "  - \"请处理这个文档\"",
        "examples_en:",
        "  - \"Process this document\"",
        f"version: {version}",
        f"author: {author}",
        "---",
        "",
        f"# {display_name}",
        "",
        "请根据任务协议执行，不要伪造未读取到的内容。",
        "",
    ])
    (target / "SKILL.md").write_text(frontmatter, encoding="utf-8")
    (target / "manifest.json").write_text(json.dumps({"id": skill_id, "version": version, "author": author}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
