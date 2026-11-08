"""Reject newly added generated assets and credentials, without rewriting legacy Git assets.

The pinned baseline is the reviewed team branch HEAD before this gate was installed.
Only additions since that ancestor are checked; use --staged for the local index.
This is a conservative safety net, not a replacement for staged content/privacy review.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import PurePosixPath

BASELINE = "b2b2f6d4aeec90fc5343962616f3eafb19d1af88"
MAX_SOURCE = 1024 * 1024
MAX_FIXTURE = 12 * 1024 * 1024
TEXT_EXTENSIONS = {".py", ".md", ".json", ".yaml", ".yml", ".toml", ".txt", ".sh", ".js", ".ts", ".env", ".ini"}
SAFE_VALUES = {"", "example", "changeme", "your-token", "your_api_key", "${SERVICE_TOKEN}", "[REDACTED]"}
ASSIGNMENT = re.compile(rb"(?im)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|private[_-]?key|password)\b\s*[:=]\s*['\"]?([^'\"\s,;#}]+)")
PEM_HEADER = re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def additions(base: str | None) -> list[str]:
    if base is not None:
        # Fail closed on a wrong, missing, or unrelated baseline; do not silently scan only HEAD.
        git("cat-file", "-e", f"{base}^{{commit}}")
        if git("merge-base", base, "HEAD").strip().decode("ascii") != base:
            raise ValueError("baseline is not an ancestor of HEAD")
        args = ("diff", "--diff-filter=A", "--name-only", "-z", base, "HEAD", "--")
    else:
        args = ("diff", "--cached", "--diff-filter=A", "--name-only", "-z", "HEAD", "--")
    raw = git(*args)
    return [p.decode("utf-8", "surrogateescape") for p in raw.split(b"\0") if p]


def reasons(path: str, data: bytes) -> list[str]:
    """Classify a new Git blob. Names and sizes are reported, never credential values."""
    p = PurePosixPath(path)
    parts = [s.lower() for s in p.parts]
    name = p.name.lower()
    problems = []
    if any(s in {"dist", "__pycache__", ".pytest_cache", ".venv", ".phase3-ci-venv", ".runtime", "output", "generated", "build", ".idea", ".vscode"} for s in parts):
        problems.append("generated/cache directory")
    if name.endswith((".pyc", ".pyo", ".log")) or name in {"thumbs.db", ".ds_store"}:
        problems.append("cache or machine output")
    if name.startswith(".env") or any(s in name for s in ("credential", "secret", "id_rsa", "id_ed25519")) or p.suffix.lower() in {".pem", ".p12", ".pfx", ".key"}:
        problems.append("credential filename")
    if name.endswith((".sha256", ".zip.sha256", ".zip.manifest.json")) and not (parts[:2] == ["tests", "fixtures"]):
        problems.append("generated sidecar")
    if name.endswith(".zip") and not (parts[:2] == ["tests", "fixtures"]):
        problems.append("archive outside reviewed fixed fixture location")
    if parts[0] == "reports" and ("raw" in parts or "actual" in name or name in {"result.json", "results.json", "test-results.json"}):
        problems.append("actual result or raw evidence")
    is_fixture = parts[:2] == ["tests", "fixtures"] or (len(parts) >= 4 and parts[0] == "packages" and parts[1] == "skills" and parts[3] == "examples" and ("fictional" in name or "expected" in name))
    if len(data) > (MAX_FIXTURE if is_fixture else MAX_SOURCE):
        problems.append("oversized new blob; require explicit fixture review")
    if p.suffix.lower() in TEXT_EXTENSIONS or name.startswith(".env"):
        if PEM_HEADER.search(data) or any(m.group(1).decode("utf-8", "replace").strip().lower() not in SAFE_VALUES for m in ASSIGNMENT.finditer(data)):
            problems.append("possible credential content")
    return problems


def check(base: str | None) -> int:
    paths = additions(base)
    failed = 0
    for path in paths:
        data = git("show", f"{'HEAD' if base is not None else ''}:{path}")
        found = reasons(path, data)
        if found:
            failed += 1
            print(f"REJECT {path!r}: {', '.join(found)}", file=sys.stderr)
    print(f"asset guard: checked {len(paths)} new Git path(s), rejected {failed}")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--base", help="trusted ancestor SHA for CI added-path scan")
    group.add_argument("--staged", action="store_true", help="scan newly staged paths vs HEAD")
    args = parser.parse_args(argv)
    try:
        return check(args.base)
    except (ValueError, subprocess.CalledProcessError, UnicodeError) as exc:
        # Git stderr can contain user data; don't echo it in CI output.
        print(f"asset guard: cannot verify Git input ({type(exc).__name__}); failing closed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
