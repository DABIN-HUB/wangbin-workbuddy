"""Build a minimal WorkBuddy Skill candidate ZIP from an explicit allowlist."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

from .validators.zip_validator import sha256, validate_zip


ALLOWED_SKILL_FILES = {
    "SKILL.md",
    "references/task-protocol.md",
    "references/privacy.md",
    "scripts/run_document_engine.py",
    "templates/summary-output.md",
}


def build_candidate_zip(root: Path, destination: Path) -> dict[str, Any]:
    source = root / "packages" / "skills" / "wangbin-document-assistant"
    destination.parent.mkdir(parents=True, exist_ok=True)
    members: list[dict[str, Any]] = []
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for rel in sorted(ALLOWED_SKILL_FILES):
            path = source / rel
            if not path.is_file():
                raise FileNotFoundError(f"candidate member missing: {path}")
            arcname = f"wangbin-document-assistant/{rel}"
            archive.write(path, arcname)
            data = path.read_bytes()
            members.append({"path": arcname, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    valid, findings, actual_members = validate_zip(destination)
    if not valid:
        raise ValueError("candidate ZIP invalid: " + "; ".join(item.message for item in findings))
    return {
        "package": "wangbin-document-assistant",
        "version": "1.0.0",
        "zip": str(destination),
        "zip_sha256": sha256(destination),
        "zip_size_bytes": destination.stat().st_size,
        "members": members,
        "validated_members": actual_members,
    }


def write_manifest(manifest: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
