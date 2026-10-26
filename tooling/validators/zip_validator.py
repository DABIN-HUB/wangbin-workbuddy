"""ZIP member safety and manifest validation."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from . import Finding


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_zip(zip_path: Path) -> tuple[bool, list[Finding], list[dict[str, str | int]]]:
    findings: list[Finding] = []
    members: list[dict[str, str | int]] = []
    try:
        with zipfile.ZipFile(zip_path) as archive:
            for info in archive.infolist():
                name = info.filename.replace("\\", "/")
                if name.startswith("/") or "../" in name.split("/"):
                    findings.append(Finding("ZIP_PATH_TRAVERSAL", name, "ZIP 成员包含绝对路径或路径穿越"))
                    continue
                if info.is_dir():
                    members.append({"path": name, "size": 0, "sha256": ""})
                    continue
                data = archive.read(info)
                members.append({"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    except (OSError, zipfile.BadZipFile) as exc:
        findings.append(Finding("ZIP_INVALID", str(zip_path), f"ZIP 无法读取: {exc}"))
    return not findings, findings, members
