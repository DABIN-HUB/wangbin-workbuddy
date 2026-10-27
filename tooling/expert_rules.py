"""Strict prompt-only WorkBuddy Expert validation, independent of legacy identity."""
from __future__ import annotations

import json
import re
import struct
from pathlib import Path

import yaml

REQUIRED = ("name", "version", "description", "author", "agents", "expertType", "agentName",
            "displayName", "profession", "displayDescription", "avatar", "categoryId",
            "defaultInitPrompt", "plugin", "tags", "quickPrompts")


def validate_prompt_expert(source: Path, *, name: str, version: str, category: str) -> dict:
    if not source.is_dir() or source.is_symlink():
        raise ValueError("missing or linked expert source")
    members = (".codebuddy-plugin/plugin.json", f"agents/{name}.md", "avatars/expert.png", "README.md", "LICENSE")
    for rel in members:
        path = source / rel
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(source.resolve()):
            raise ValueError(f"missing or linked expert asset: {rel}")
    if any(path.is_symlink() for path in source.rglob("*")):
        raise ValueError("linked expert asset")
    meta = json.loads((source / members[0]).read_text(encoding="utf-8"))
    missing = [key for key in REQUIRED if not meta.get(key)]
    if missing:
        raise ValueError(f"missing official expert fields: {', '.join(missing)}")
    if (meta["name"], meta["version"], meta["expertType"], meta["plugin"]) != (name, version, "agent", name):
        raise ValueError("expert identity, version or type mismatched")
    if meta["agents"] != [f"./agents/{name}.md"] or meta["agentName"] != name or meta["avatar"] != members[2]:
        raise ValueError("agentName, agent path or avatar path mismatched")
    if meta["categoryId"] != category:
        raise ValueError("expert category mismatched")
    if not isinstance(meta["author"], dict) or not all(meta["author"].get(key) for key in ("name", "email")):
        raise ValueError("author name/email required")
    for key in ("displayName", "profession", "displayDescription", "defaultInitPrompt"):
        if not isinstance(meta[key], dict) or any(not isinstance(meta[key].get(lang), str) or not meta[key][lang].strip() for lang in ("zh", "en")):
            raise ValueError(f"{key} must provide zh/en strings")
    if not 40 <= len(meta["displayDescription"]["zh"]) <= 50:
        raise ValueError("Chinese market description must be 40-50 characters")
    if len(meta["displayName"]["zh"]) > 15:
        raise ValueError("Chinese displayName must be at most 15 characters")
    for key in ("tags", "quickPrompts"):
        values = meta[key]
        if not isinstance(values, list) or len(values) != 3 or any(not isinstance(v, dict) or any(not isinstance(v.get(lang), str) or not v[lang].strip() for lang in ("zh", "en")) for v in values):
            raise ValueError(f"{key} requires exactly three bilingual entries")
    if any(meta["defaultInitPrompt"][lang] != meta["quickPrompts"][0][lang] for lang in ("zh", "en")):
        raise ValueError("default prompt must match the first quick prompt")
    agent = (source / members[1]).read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", agent, flags=re.DOTALL)
    if match is None:
        raise ValueError("agent YAML frontmatter missing")
    front = yaml.safe_load(match.group(1))
    if not isinstance(front, dict) or front.get("name") != name or not front.get("description"):
        raise ValueError("agent frontmatter identity/description mismatched")
    for key in ("displayName", "profession"):
        if front.get(key) != meta[key]:
            raise ValueError(f"agent {key} differs from plugin.json")
    if "skills" in front or "dependencies" in meta or "skills" in meta or "tools" in front:
        raise ValueError("expert must not declare external tool/runtime dependencies")
    avatar = (source / members[2]).read_bytes()
    if len(avatar) > 500_000 or avatar[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR":
        raise ValueError("avatar must be a PNG smaller than 500 KB")
    if struct.unpack(">II", avatar[16:24]) != (512, 512):
        raise ValueError("avatar must measure 512x512")
    return meta
