"""Build the independent, prompt-only WorkBuddy expert candidate."""
from __future__ import annotations

import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path

import yaml

NAME = "wangbin-software-consultant"
VERSION = "1.0.0"
MEMBERS = (
    ".codebuddy-plugin/plugin.json",
    "agents/wangbin-software-consultant.md",
    "avatars/expert.png",
    "README.md",
)
_REQUIRED = (
    "name", "version", "description", "author", "agents", "expertType",
    "agentName", "displayName", "profession", "displayDescription", "avatar",
    "categoryId", "defaultInitPrompt", "plugin", "tags", "quickPrompts",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_source(source: Path) -> dict[str, object]:
    source = source.resolve(strict=True)
    for rel in MEMBERS:
        path = source / rel
        if not path.is_file() or path.is_symlink() or path.resolve() != path:
            raise ValueError(f"missing or linked expert asset: {rel}")
    meta = json.loads((source / MEMBERS[0]).read_text(encoding="utf-8"))
    missing = [key for key in _REQUIRED if not meta.get(key)]
    if missing:
        raise ValueError(f"missing official expert fields: {', '.join(missing)}")
    if (meta["name"], meta["version"], meta["expertType"], meta["plugin"]) != (NAME, VERSION, "agent", NAME):
        raise ValueError("expert identity, version or type mismatched")
    if meta["agents"] != [f"./agents/{NAME}.md"] or meta["agentName"] != NAME or meta["avatar"] != MEMBERS[2]:
        raise ValueError("agentName, agent path or avatar path mismatched")
    if meta["categoryId"] != "12-IndustryConsultant":
        raise ValueError("expert category mismatched")
    if not isinstance(meta["author"], dict) or not all(meta["author"].get(key) for key in ("name", "email")):
        raise ValueError("author name/email required")
    for key in ("displayName", "profession", "displayDescription", "defaultInitPrompt"):
        if not isinstance(meta[key], dict) or any(not isinstance(meta[key].get(lang), str) or not meta[key][lang].strip() for lang in ("zh", "en")):
            raise ValueError(f"{key} must provide zh/en strings")
    if not 40 <= len(meta["displayDescription"]["zh"]) <= 50:
        raise ValueError("Chinese market description must be 40-50 characters")
    for key in ("tags", "quickPrompts"):
        values = meta[key]
        if not isinstance(values, list) or len(values) != 3 or any(not isinstance(v, dict) or any(not isinstance(v.get(lang), str) or not v[lang].strip() for lang in ("zh", "en")) for v in values):
            raise ValueError(f"{key} requires exactly three bilingual entries")
    if any(meta["defaultInitPrompt"][lang] != meta["quickPrompts"][0][lang] for lang in ("zh", "en")):
        raise ValueError("default prompt must match the first quick prompt")
    agent = (source / MEMBERS[1]).read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", agent, flags=re.DOTALL)
    if match is None:
        raise ValueError("agent YAML frontmatter missing")
    front = yaml.safe_load(match.group(1))
    if not isinstance(front, dict) or front.get("name") != NAME or not front.get("description"):
        raise ValueError("agent frontmatter identity/description mismatched")
    for key in ("displayName", "profession"):
        if front.get(key) != meta[key]:
            raise ValueError(f"agent {key} differs from plugin.json")
    if "skills" in front or "dependencies" in meta or "skills" in meta or "tools" in front:
        raise ValueError("expert must not declare external tool/runtime dependencies")
    avatar = (source / MEMBERS[2]).read_bytes()
    if len(avatar) > 500_000 or avatar[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR":
        raise ValueError("avatar must be a PNG smaller than 500 KB")
    if struct.unpack(">II", avatar[16:24]) != (512, 512):
        raise ValueError("avatar must measure 512x512")
    return meta


def build(root: Path) -> dict[str, object]:
    root = root.resolve(strict=True)
    source = root / "packages" / "experts" / NAME
    validate_source(source)
    output = root / "dist"
    output.mkdir(exist_ok=True)
    destination = output / f"{NAME}-{VERSION}-expert-candidate.zip"
    expected: dict[str, bytes] = {}
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in sorted(MEMBERS):
            data = (source / rel).read_bytes()
            member = f"{NAME}/{rel}"
            expected[member] = data
            entry = zipfile.ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
            entry.external_attr = 0o100644 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(destination) as archive:
        if archive.testzip() is not None or set(archive.namelist()) != set(expected) or len(archive.namelist()) != len(expected):
            raise ValueError("candidate ZIP member mismatch/corruption")
        for member, payload in expected.items():
            if archive.read(member) != payload:
                raise ValueError(f"candidate ZIP member content mismatch: {member}")
    result = {
        "name": NAME,
        "version": VERSION,
        "status": "PASS",
        "status_scope": "local_schema_and_archive_integrity_only",
        "workbuddy_install": "BLOCKED",
        "workbuddy_dialogue": "BLOCKED",
        "zip": str(destination),
        "sha256": digest(destination.read_bytes()),
        "members": [{"path": name, "size": len(data), "sha256": digest(data)} for name, data in expected.items()],
    }
    (output / f"{destination.name}.sha256").write_bytes(f"{result['sha256']}  {destination.name}\n".encode("ascii"))
    (output / f"{NAME}-{VERSION}-expert-manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(build(Path.cwd()), ensure_ascii=False, indent=2))
