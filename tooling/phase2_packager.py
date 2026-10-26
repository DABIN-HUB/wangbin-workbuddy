"""Create and read back phase-two WorkBuddy candidate archives.

This builds only official Skill/CLI Connector resources. The Python wheel is a
separate local deliverable until a versioned distribution is authorized.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from tooling.validators.project_validator import validate_connector, validate_skill

VERSION = "1.1.0"
SKILL = "wangbin-document-assistant"
CONNECTOR = "wangbin-document-cli"
SKILL_FILES = ("SKILL.md", "references/runtime.md")
CONNECTOR_FILES = (
    "connector-meta.json", "cli.json", "icon.svg",
    "skills/wangbin-document-assistant/SKILL.md",
    "skills/wangbin-document-assistant/references/runtime.md",
)


def sha256(data: bytes) -> str:
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
        packaged = connector_source / "skills" / SKILL / rel
        if (skill_source / rel).read_bytes() != packaged.read_bytes():
            raise ValueError(f"embedded Skill differs: {rel}")
    config = json.loads((connector_source / "cli.json").read_text(encoding="utf-8"))
    meta = json.loads((connector_source / "connector-meta.json").read_text(encoding="utf-8"))
    if meta.get("version") != VERSION or config.get("runtime", {}).get("type") != "python":
        raise ValueError("connector version/runtime mismatch")
    install_commands = config["init"].values()
    if any(f"wangbin-document-cli=={VERSION}" not in value for value in install_commands):
        raise ValueError("install command not pinned to candidate version")
    wheel = root / "dist" / f"wangbin_document_cli-{VERSION}-py3-none-any.whl"
    if not wheel.is_file():
        raise FileNotFoundError("build the versioned Python wheel before packaging the connector")
    with zipfile.ZipFile(wheel) as package:
        names = package.namelist()
        if not any(name.endswith(".dist-info/METADATA") for name in names):
            raise ValueError("Python wheel has no metadata")
        for module in ("wangbin_document_engine", "wangbin_document_cli"):
            source_modules = list((root / "services/document-engine/src" / module).glob("*.py"))
            if not source_modules:
                raise ValueError(f"Python wheel source missing: {module}")
            wheel_modules = {item for item in names if item.startswith(module + "/") and item.endswith(".py")}
            if wheel_modules != {f"{module}/{item.name}" for item in source_modules}:
                raise ValueError(f"Python wheel module set differs: {module}")
            for item in source_modules:
                if package.read(f"{module}/{item.name}") != item.read_bytes():
                    raise ValueError(f"Python wheel source differs: {item.name}")
        license_member = f"wangbin_document_cli-{VERSION}.dist-info/licenses/LICENSE"
        if license_member not in names or package.read(license_member) != (root / "services/document-engine/LICENSE").read_bytes():
            raise ValueError("Python wheel license missing or differs")
    output = root / "dist"
    output.mkdir(exist_ok=True)
    archives: dict[str, dict[str, object]] = {}
    for kind, source, members, prefix, name in (
        ("skill", skill_source, SKILL_FILES, SKILL, f"{SKILL}-{VERSION}-skill-candidate.zip"),
        ("connector", connector_source, CONNECTOR_FILES, CONNECTOR, f"{CONNECTOR}-{VERSION}-connector-candidate.zip"),
    ):
        destination = output / name
        manifest = []
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
                manifest.append({"path": member, "size": len(payload), "sha256": sha256(payload)})
        with zipfile.ZipFile(destination) as archive:
            if archive.testzip() is not None or set(archive.namelist()) != {m["path"] for m in manifest}:
                raise ValueError(f"candidate archive integrity failed: {kind}")
            for item in manifest:
                member = item["path"]
                if ".." in Path(member).parts or archive.getinfo(member).external_attr >> 16 & 0o170000 == 0o120000:
                    raise ValueError(f"candidate archive unsafe: {member}")
                if sha256(archive.read(member)) != item["sha256"]:
                    raise ValueError(f"candidate archive member mismatch: {member}")
        archives[kind] = {"path": str(destination), "size_bytes": destination.stat().st_size, "sha256": sha256(destination.read_bytes()), "members": manifest}
        (output / f"{name}.sha256").write_text(f"{archives[kind]['sha256']}  {name}\n", encoding="utf-8")
    result = {"version": VERSION, "status": "PASS", "wheel": {"path": str(wheel), "size_bytes": wheel.stat().st_size, "sha256": sha256(wheel.read_bytes())}, "archives": archives, "platform_install": "BLOCKED", "reason": "The wheel version is not published to an accessible package index; WorkBuddy ZIP parsing and runtime are untested."}
    (output / f"{wheel.name}.sha256").write_text(f"{result['wheel']['sha256']}  {wheel.name}\n", encoding="utf-8")
    (output / f"{CONNECTOR}-{VERSION}-candidate-manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    print(json.dumps(build(args.root), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
