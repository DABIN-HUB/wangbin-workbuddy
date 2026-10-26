"""Metadata and output path helpers."""
from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Any

from .errors import ExportFailure

def file_metadata(path: Path) -> dict[str, Any]:
    stat = path.stat()
    return {
        "name": path.name,
        "extension": path.suffix.lower(),
        "mime_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        "size_bytes": stat.st_size,
        "modified_time": stat.st_mtime,
    }


def safe_output_path(output_dir: Path, source_name: str, suffix: str) -> Path:
    stem = Path(source_name).stem
    clean = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in stem).strip(".") or "document"
    candidate = (output_dir / f"{clean}{suffix}").resolve()
    candidate.relative_to(output_dir.resolve())
    counter = 1
    original = candidate
    while candidate.exists():
        candidate = original.with_name(f"{original.stem}-{counter}{original.suffix}")
        counter += 1
    return candidate


def publish_new_file(temporary: Path, target: Path) -> None:
    """Publish a same-directory temporary file without replacing an existing target."""
    try:
        os.link(temporary, target)
    except FileExistsError as exc:
        raise ExportFailure("OUTPUT_CONFLICT", "导出目标已被其他任务占用") from exc
