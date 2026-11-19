"""Build this one Expert's local candidate; platform loading remains unverified."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

NAME = "wangbin-software-consultant"
VERSION = "1.1.2"
MEMBERS = (
    ".codebuddy-plugin/plugin.json",
    "agents/wangbin-software-consultant.md",
    "avatars/expert.png",
    "README.md",
    "LICENSE",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_source(source: Path) -> dict[str, object]:
    """Keep the original fixed identity and member contract; share only strict rules."""
    try:
        from tooling.expert_rules import validate_prompt_expert
    except ModuleNotFoundError:  # Direct `python tooling/phase5_expert_packager.py` execution.
        from expert_rules import validate_prompt_expert

    return validate_prompt_expert(source, name=NAME, version=VERSION, category="12-IndustryConsultant")


def build(root: Path, *, source_commit: str | None = None) -> dict[str, object]:
    """Build from a caller-controlled clean source tree, without replacing archives."""
    root = root.resolve(strict=True)
    source = root / "packages" / "experts" / NAME
    meta = validate_source(source)
    members = list(MEMBERS)
    if meta.get("skills"):
        members.extend("skills/wangbin-estimate-calculator/" + rel for rel in ("SKILL.md", "scripts/estimator.py", "references/input-output-contract.md", "LICENSE"))
    output = root / "dist"
    output.mkdir(exist_ok=True)
    destination = output / f"{NAME}-{VERSION}-expert-candidate.zip"
    sidecar = output / f"{destination.name}.sha256"
    manifest = output / f"{NAME}-{VERSION}-expert-manifest.json"
    if any(path.exists() for path in (destination, sidecar, manifest)):
        raise FileExistsError("candidate version already exists; preserve immutable release and use an empty dist")
    expected: dict[str, bytes] = {}
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel in sorted(members):
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
        "source_commit": source_commit or "NOT_VERIFIED",
        "workbuddy_install": "NOT_TESTED_VALIDATION_WAIVED",
        "workbuddy_dialogue": "NOT_TESTED_VALIDATION_WAIVED",
        "zip": str(destination),
        "sha256": digest(destination.read_bytes()),
        "members": [{"path": name, "size": len(data), "sha256": digest(data)} for name, data in expected.items()],
    }
    sidecar.write_bytes(f"{result['sha256']}  {destination.name}\n".encode("ascii"))
    manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(build(Path.cwd()), ensure_ascii=False, indent=2))
