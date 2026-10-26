"""Build the Phase 3 1.2.0 candidate assets without touching Phase 2 evidence."""
from __future__ import annotations

import hashlib
import json
import zipfile
from email.parser import Parser
from pathlib import Path

from tooling.validators.project_validator import validate_connector, validate_skill

VERSION = "1.2.0"
SKILL = "wangbin-document-assistant"
CONNECTOR = "wangbin-document-cli"
SKILL_FILES = ("SKILL.md", "references/runtime.md")
CONNECTOR_FILES = (
    "connector-meta.json", "cli.json", "icon.svg",
    "skills/wangbin-document-assistant/SKILL.md",
    "skills/wangbin-document-assistant/references/runtime.md",
)
PHASE2_BASELINE = {
    "wangbin_document_cli-1.1.0-py3-none-any.whl": "51071474a8668d5c4ba153896a5cde4d4233881f6042d7b16f305259fda702f9",
    "wangbin-document-assistant-1.1.0-skill-candidate.zip": "c96a8644047146c595a2267769aadf8b7e6d6532615be4343d34014efb33678c",
    "wangbin-document-cli-1.1.0-connector-candidate.zip": "e04486c39f804307b98d33eabe5a477c6336910708c260ead8703b7fee305fbf",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(root: Path) -> dict[str, object]:
    root = root.resolve()
    skill_source = root / "packages/skills/wangbin-document-assistant-cli"
    connector_source = root / "packages/connectors" / CONNECTOR
    checks: list[dict[str, object]] = []
    findings = []
    validate_skill(skill_source, checks, findings)
    validate_connector(connector_source, checks, findings)
    if findings:
        raise ValueError("validation failed: " + "; ".join(f.code for f in findings))
    for rel in SKILL_FILES:
        if (skill_source / rel).read_bytes() != (connector_source / "skills" / SKILL / rel).read_bytes():
            raise ValueError(f"embedded Skill differs: {rel}")
    config = json.loads((connector_source / "cli.json").read_text(encoding="utf-8"))
    meta = json.loads((connector_source / "connector-meta.json").read_text(encoding="utf-8"))
    if meta.get("version") != VERSION or config.get("runtime") != {"type": "python", "version": "3.12"}:
        raise ValueError("connector version/runtime mismatch")
    if any(f"wangbin-document-cli=={VERSION}" not in command for command in config["init"].values()):
        raise ValueError("init is not pinned to the phase 3 version")
    wheel = root / "dist" / f"wangbin_document_cli-{VERSION}-py3-none-any.whl"
    if not wheel.is_file():
        raise FileNotFoundError(f"build {wheel.name} before packaging")
    with zipfile.ZipFile(wheel) as package:
        names = set(package.namelist())
        if f"wangbin_document_cli-{VERSION}.dist-info/licenses/LICENSE" not in names:
            raise ValueError("wheel license missing")
        metadata = Parser().parsestr(package.read(f"wangbin_document_cli-{VERSION}.dist-info/METADATA").decode("utf-8"))
        if metadata.get("Name") != "wangbin-document-cli" or metadata.get("Version") != VERSION:
            raise ValueError("wheel package metadata differs from candidate version")
        for module in ("wangbin_document_engine", "wangbin_document_cli"):
            source = root / "services/document-engine/src" / module
            expected = {f"{module}/{item.name}" for item in source.glob("*.py")}
            actual = {name for name in names if name.startswith(module + "/") and name.endswith(".py")}
            if expected != actual:
                raise ValueError(f"wheel module set differs for {module}")
            for item in source.glob("*.py"):
                if package.read(f"{module}/{item.name}") != item.read_bytes():
                    raise ValueError(f"wheel source differs for {module}/{item.name}")
    output = root / "dist"
    output.mkdir(exist_ok=True)
    phase2_available = any((output / name).exists() for name in PHASE2_BASELINE)
    phase2_preserved = all(
        (output / name).is_file() and digest((output / name).read_bytes()) == expected
        for name, expected in PHASE2_BASELINE.items()
    )
    if phase2_available and not phase2_preserved:
        raise ValueError("Phase 2 baseline artifacts partially present or modified")
    archives: dict[str, dict[str, object]] = {}
    for kind, source, members, prefix, name in (
        ("skill", skill_source, SKILL_FILES, SKILL, f"{SKILL}-{VERSION}-skill-candidate.zip"),
        ("connector", connector_source, CONNECTOR_FILES, CONNECTOR, f"{CONNECTOR}-{VERSION}-connector-candidate.zip"),
    ):
        destination = output / name
        member_manifest = []
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for rel in sorted(members):
                source_file = source / rel
                if source_file.is_symlink() or not source_file.is_file():
                    raise ValueError(f"missing or linked candidate member: {rel}")
                payload = source_file.read_bytes()
                member = f"{prefix}/{rel}"
                info = zipfile.ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
                member_manifest.append({"path": member, "size": len(payload), "sha256": digest(payload)})
        with zipfile.ZipFile(destination) as archive:
            if archive.testzip() is not None or set(archive.namelist()) != {item["path"] for item in member_manifest}:
                raise ValueError(f"archive integrity failed: {kind}")
            for item in member_manifest:
                if digest(archive.read(item["path"])) != item["sha256"]:
                    raise ValueError(f"archive member mismatch: {item['path']}")
        record = {"path": str(destination), "size_bytes": destination.stat().st_size, "sha256": digest(destination.read_bytes()), "members": member_manifest}
        archives[kind] = record
        (output / f"{name}.sha256").write_bytes(f"{record['sha256']}  {name}\n".encode("ascii"))
    wheel_record = {"path": str(wheel), "size_bytes": wheel.stat().st_size, "sha256": digest(wheel.read_bytes())}
    (output / f"{wheel.name}.sha256").write_bytes(f"{wheel_record['sha256']}  {wheel.name}\n".encode("ascii"))
    manifest = {
        "version": VERSION,
        "status": "PASS",
        "status_scope": "package_structure_only",
        "wheel": wheel_record,
        "archives": archives,
        "distribution_source": "BLOCKED",
        "reason": "No authorized public or trusted index publication was performed; WorkBuddy installation remains untested.",
        "phase2_artifacts_preserved": phase2_preserved,
        "phase2_artifacts_available": phase2_available,
    }
    (output / f"{CONNECTOR}-{VERSION}-candidate-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(build(Path.cwd()), ensure_ascii=False, indent=2))
