"""Conservative credential scanner; reports locations, never values."""
from __future__ import annotations

import re
from pathlib import Path

from . import Finding

PATTERNS = [
    re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|private[_-]?key|password)\b\s*[:=]\s*[\"']([^\"']+)[\"']"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]
SKIP_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", "dist", "reports"}
TEXT_SUFFIXES = {".py", ".md", ".json", ".yaml", ".yml", ".toml", ".txt", ".sh", ".js", ".ts"}
SAFE_VALUES = {"", "example", "changeme", "your-token", "your_api_key", "${SERVICE_TOKEN}", "[REDACTED]"}


def scan_for_secrets(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES or any(part in SKIP_PARTS for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in PATTERNS:
            for match in pattern.finditer(text):
                value = match.group(1) if match.groups() else match.group(0)
                if value.strip().lower() in SAFE_VALUES:
                    continue
                findings.append(Finding("SECRET_PATTERN", str(path.relative_to(root)), "检测到疑似凭证模式，值已隐藏"))
                break
    return findings
