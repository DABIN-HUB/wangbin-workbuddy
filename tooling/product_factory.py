"""Independent product registry, local evidence gates and deterministic candidate archives."""
from __future__ import annotations

import hashlib
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .expert_rules import validate_prompt_expert
from .generators import generate_skill
from .validators.project_validator import SEMVER, validate_connector, validate_skill
from .validators.secret_scanner import scan_for_secrets

KINDS = {"Skill": "skills", "Expert": "experts", "Connector": "connectors"}
STATES = {"BACKLOG", "DEVELOPING", "TESTED", "SUBMITTED", "APPROVED", "REJECTED", "PUBLISHED", "PAUSED"}
REVIEWS = {"UNKNOWN", "NOT_AVAILABLE", "BLOCKED", "NOT_TESTED", "USER_REPORTED_SUBMITTED", "APPROVED", "REJECTED"}
METRIC_FIELDS = {"exposures", "installs", "uses", "feedback", "review_result", "development_cost", "maintenance_cost"}
TEXT_SUFFIXES = {".md", ".json", ".py", ".txt", ".yaml", ".yml", ".svg", ".toml", ".sh", ".js", ".ts", ".png", ".html", ".csv"}


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _safe_relative(root: Path, value: str, *, label: str) -> Path:
    """Resolve a catalog path without following links or allowing traversal."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a relative path")
    relative = Path(value)
    if relative.is_absolute() or any(part in {"..", ""} for part in relative.parts):
        raise ValueError(f"{label} must not traverse or be absolute")
    root = root.absolute()
    current = root
    if current.is_symlink():
        raise ValueError("root path must not be a symlink")
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"{label} has symlink ancestor: {value}")
    return current


def _relative(root: Path, path: Path) -> str:
    try:
        return path.absolute().relative_to(root.absolute()).as_posix()
    except ValueError as exc:
        raise ValueError("evidence path escapes root") from exc


def _atomic_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def _version_entry(item: dict) -> dict:
    active = item.get("active_version")
    if active is not None:
        for entry in item["versions"]:
            if entry.get("version") == active:
                return entry
        raise ValueError(f"active version is not registered: {active}")
    return item["versions"][-1]


def load_catalog(root: Path) -> dict:
    return _json(root / "products" / "catalog.json")


def validate_catalog(root: Path) -> list[str]:
    data = load_catalog(root)
    errors = []
    if data.get("schema_version") != 1 or not isinstance(data.get("products"), list):
        return ["unsupported catalog schema"]
    ids, sources = set(), {}
    for item in data["products"]:
        if not isinstance(item, dict):
            errors.append("product must be an object")
            continue
        pid, kind = item.get("id"), item.get("type")
        if not isinstance(pid, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", pid):
            errors.append(f"invalid product id: {pid}")
        if pid in ids:
            errors.append(f"duplicate product id: {pid}")
        ids.add(pid)
        if kind not in KINDS or item.get("status") not in STATES or item.get("review_status") not in REVIEWS:
            errors.append(f"invalid type/status/review: {pid}")
        for key in ("name", "target_users", "scenario", "development", "maintenance", "review_evidence"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f"missing {key}: {pid}")
        if "published_at" in item and (not isinstance(item["published_at"], str) or not item["published_at"].strip()):
            errors.append(f"invalid published_at: {pid}")
        validation_metrics = item.get("validation_metrics")
        if validation_metrics is not None and not isinstance(validation_metrics, (str, dict)):
            errors.append(f"invalid validation_metrics: {pid}")
        if item.get("review_status") == "APPROVED" and isinstance(item.get("review_evidence"), str):
            errors.append(f"platform approval must have independently verified evidence: {pid}")
        active_version = item.get("active_version")
        versions = item.get("versions")
        if not isinstance(versions, list) or not versions:
            errors.append(f"missing versions: {pid}")
            continue
        seen_versions = set()
        for version in versions:
            if not isinstance(version, dict):
                errors.append(f"invalid version: {pid}")
                continue
            number = version.get("version")
            if not isinstance(number, str) or not SEMVER.fullmatch(number) or number in seen_versions:
                errors.append(f"invalid/duplicate version: {pid}")
            seen_versions.add(number)
            source = version.get("source")
            expected = f"packages/{KINDS.get(kind, 'INVALID')}/{pid}"
            try:
                _safe_relative(root, source, label=f"source for {pid}")
            except ValueError as exc:
                errors.append(str(exc))
            if source != expected or (isinstance(source, str) and source in sources and sources[source] != pid):
                errors.append(f"source collision or invalid source: {pid}")
            if isinstance(source, str):
                sources[source] = pid
            for key in ("candidate", "sha256", "date"):
                if not isinstance(version.get(key), str) or not version[key].strip():
                    errors.append(f"missing {key}: {pid}")
            digest = version.get("sha256")
            if isinstance(digest, str) and digest != "UNKNOWN" and not re.fullmatch(r"[0-9a-f]{64}", digest):
                errors.append(f"invalid sha256: {pid}")
            for key in ("candidate", "archive_evidence"):
                value = version.get(key)
                if value and value != "UNKNOWN":
                    try:
                        _safe_relative(root, value, label=f"{key} for {pid}")
                    except ValueError as exc:
                        errors.append(str(exc))
            if version.get("published_at") is not None and not isinstance(version.get("published_at"), str):
                errors.append(f"invalid version published_at: {pid}")
        if active_version is not None and active_version not in seen_versions:
            errors.append(f"active version is not registered: {pid}")
    return errors


def get_product(root: Path, product_id: str) -> dict:
    problems = validate_catalog(root)
    if problems:
        raise ValueError("; ".join(problems))
    for item in load_catalog(root)["products"]:
        if item["id"] == product_id:
            return item
    raise ValueError(f"unregistered product: {product_id}")


def _source(root: Path, item: dict) -> Path:
    return _safe_relative(root, _version_entry(item)["source"], label="source")


def _version(item: dict) -> str:
    return _version_entry(item)["version"]


def init_product(root: Path, product_id: str, kind: str | None = None, connector_mode: str | None = None) -> Path:
    item = get_product(root, product_id)
    if kind and kind != item["type"]:
        raise ValueError("kind differs from registration")
    if item["type"] == "Connector" and connector_mode not in {"cli", "mcp"}:
        raise ValueError("Connector requires --connector-mode cli or mcp")
    target = _source(root, item)
    if target.exists() or target.is_symlink():
        raise ValueError("source directory already exists")
    archive, sidecar, manifest = _paths(root, item)
    registered = item["versions"][-1]["candidate"]
    if any(path.exists() or path.is_symlink() for path in (archive, sidecar, manifest)) or (registered != "UNKNOWN" and (root / registered).exists()):
        raise ValueError("candidate path already reserved")
    # Metadata and paths in all installed packages, including unregistered templates, are reserved.
    for sibling in (root / "packages").glob("*/*"):
        if sibling.name == product_id:
            raise ValueError("package directory name collision")
        for rel, key in (("manifest.json", "id"), (".codebuddy-plugin/plugin.json", "name"),
                         ("connector-meta.json", "source"), ("connector-meta.json", "name")):
            file = sibling / rel
            if file.is_file() and _json(file).get(key) == product_id:
                raise ValueError("package metadata name collision")
        skill = sibling / "SKILL.md"
        if skill.is_file():
            text = skill.read_text(encoding="utf-8")
            if text.startswith("---") and yaml.safe_load(text.split("---", 2)[1]).get("name") == product_id:
                raise ValueError("Skill metadata name collision")
    version = _version(item)
    if item["type"] == "Skill":
        generate_skill(target, skill_id=product_id, display_name=item["name"], display_name_en=item["name"],
                       author="TODO-author", version=version, description_zh="TODO: describe verified capabilities",
                       description_en="TODO: describe verified capabilities")
    elif item["type"] == "Expert":
        template = root / "packages/experts/wangbin-expert-template"
        if not template.is_dir():
            raise ValueError("Expert template missing")
        shutil.copytree(template, target)
        meta_file = target / ".codebuddy-plugin/plugin.json"
        meta = _json(meta_file)
        old = meta["agentName"]
        meta.update(name=product_id, plugin=product_id, agentName=product_id, version=version,
                    agents=[f"./agents/{product_id}.md"], categoryId=item.get("category", "UNKNOWN"),
                    description="TODO: describe reviewed prompt-only behavior",
                    author={"name": "TODO-author", "email": "TODO@example.invalid"},
                    displayName={"zh": "待完善专家", "en": item["name"]},
                    profession={"zh": "待完善领域", "en": "TODO profession"},
                    displayDescription={"zh": "本模板仅用于建立候选专家目录，所有工作能力与输出边界尚未完成审查，禁止用于正式发布或提供真实建议。", "en": "TODO: reviewed expert description"},
                    defaultInitPrompt={"zh": "请先完善产品能力", "en": "TODO: complete product"},
                    quickPrompts=[{"zh": "请先完善产品能力", "en": "TODO: complete product"},
                                  {"zh": "待补充", "en": "TODO"}, {"zh": "待补充", "en": "TODO"}],
                    tags=[{"zh": "待完善", "en": "TODO"}] * 3)
        meta_file.write_bytes(_dump(meta))
        agent = target / "agents" / f"{old}.md"
        agent.rename(target / "agents" / f"{product_id}.md")
        renamed = target / "agents" / f"{product_id}.md"
        front = {"name": product_id, "description": meta["description"], "displayName": meta["displayName"],
                 "profession": meta["profession"]}
        renamed.write_text("---\n" + yaml.safe_dump(front, allow_unicode=True, sort_keys=False) +
                           "---\n# TODO: define expert behavior and safety boundaries before validation.\n", encoding="utf-8")
        (target / "README.md").write_text("TODO: review this Expert's behavior, avatar rights, license and claims.\n", encoding="utf-8")
        (target / "LICENSE").write_text("TODO: choose license before release\n", encoding="utf-8")
    else:
        template = root / "packages/connectors" / f"wangbin-{connector_mode}-connector-template"
        if not template.is_dir():
            raise ValueError("Connector template missing")
        shutil.copytree(template, target)
        meta_path = target / "connector-meta.json"
        meta = _json(meta_path)
        meta.update(name=product_id, source=product_id, version=version, type=connector_mode,
                    description="TODO: describe verified implementation", description_zh="TODO", description_en="TODO")
        meta_path.write_bytes(_dump(meta))
        # Template commands/servers refer to a different product; never imply they work.
        (target / ("cli.json" if connector_mode == "cli" else "mcp.json")).write_bytes(
            _dump({"runtime": {"type": "node", "version": "20"}} if connector_mode == "cli" else {"mcpServers": {}}))
        shutil.rmtree(target / "skills", ignore_errors=True)
        (target / "README.md").write_text("TODO: implement and review this Connector's runtime, permissions, icon and claims before release.\n", encoding="utf-8")
    return target


def _files(source: Path, kind: str) -> list[Path]:
    if not source.is_dir() or source.is_symlink():
        raise ValueError("source missing or linked")
    files = []
    allowed = {
        "Skill": {"SKILL.md", "manifest.json", "README.md", "LICENSE", "references", "scripts", "templates", "examples"},
        "Expert": {".codebuddy-plugin", "agents", "avatars", "README.md", "LICENSE", "tests"},
        "Connector": {"connector-meta.json", "cli.json", "mcp.json", "icon.svg", "README.md", "LICENSE", "skills"},
    }[kind]
    for path in source.rglob("*"):
        rel = path.relative_to(source)
        if source.is_symlink() or any((source / parent).is_symlink() for parent in path.relative_to(source).parents):
            raise ValueError(f"symlink ancestor: {rel}")
        if rel.parts[0] not in allowed:
            raise ValueError(f"unapproved source path: {rel}")
        if path.is_symlink():
            raise ValueError(f"symlink forbidden: {rel}")
        if any(part.startswith(".") and not (kind == "Expert" and part == ".codebuddy-plugin") for part in rel.parts) or any(part.lower() in {"__pycache__", "tests", ".pytest_cache", "venv", "node_modules", "dist"} for part in rel.parts):
            if "__pycache__" in rel.parts or "tests" in rel.parts:
                continue
            raise ValueError(f"private or cache path forbidden: {rel}")
        if path.is_file():
            if (path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"LICENSE"}) or path.name.lower() in {"id_rsa", "credentials.json", "secrets.json"}:
                raise ValueError(f"unapproved file type/name: {rel}")
            files.append(path)
    return sorted(files, key=lambda p: p.relative_to(source).as_posix())


def validate_product(root: Path, product_id: str) -> dict:
    item = get_product(root, product_id)
    source = _source(root, item)
    if not source.is_dir():
        return {"id": product_id, "status": "BLOCKED", "findings": ["source absent (backlog)"]}
    findings = []
    try:
        files = _files(source, item["type"])
        if not files:
            findings.append("empty source")
        if item["type"] == "Expert":
            validate_prompt_expert(source, name=product_id, version=_version(item), category=item.get("category", "UNKNOWN"))
        else:
            checks = []
            from .validators import Finding
            issues: list[Finding] = []
            if item["type"] == "Skill":
                validate_skill(source, checks, issues)
                front = yaml.safe_load((source / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
                if not isinstance(front, dict) or front.get("name") != product_id or str(front.get("version")) != _version(item):
                    findings.append("Skill identity/version mismatch")
            else:
                validate_connector(source, checks, issues)
                meta = _json(source / "connector-meta.json")
                if meta.get("source") != product_id or meta.get("version") != _version(item):
                    findings.append("Connector identity/version mismatch")
            findings += [f.code for f in issues]
        findings += [f.code for f in scan_for_secrets(source)]
        for path in files:
            if path.suffix.lower() == ".json":
                text = path.read_text(encoding="utf-8")
                if re.search(r'(?i)"(?:api[_-]?key|access[_-]?token|client[_-]?secret|private[_-]?key|password)"\s*:\s*"(?!example"|changeme"|your-token"|\$\{)[^"]+"', text):
                    findings.append(f"SECRET_PATTERN: {path.relative_to(source)}")
            if path.suffix.lower() in {".md", ".json", ".py", ".txt"} and "TODO" in path.read_text(encoding="utf-8"):
                findings.append(f"unfinished placeholder: {path.relative_to(source)}")
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError, yaml.YAMLError) as exc:
        findings.append(str(exc))
    return {"id": product_id, "status": "FAIL" if findings else "PASS", "findings": findings}


def test_product(root: Path, product_id: str) -> dict:
    item = get_product(root, product_id)
    test_path = item.get("test_path")
    if not _source(root, item).is_dir() or not test_path:
        return {"id": product_id, "status": "NOT_TESTED", "reason": "source or product-specific test absent"}
    try:
        path = _safe_relative(root, test_path, label="test_path")
    except ValueError:
        return {"id": product_id, "status": "NOT_TESTED", "reason": "registered product test unavailable"}
    source_rel = _version_entry(item)["source"]
    if not path.is_file() or path.suffix != ".py" or not (test_path.startswith("tests/test_") or test_path.startswith(source_rel + "/tests/test_")):
        return {"id": product_id, "status": "NOT_TESTED", "reason": "registered product test unavailable"}
    run = subprocess.run([sys.executable, "-m", "pytest", "-q", test_path], cwd=root, capture_output=True, text=True)
    return {"id": product_id, "status": "PASS" if run.returncode == 0 else "FAIL", "returncode": run.returncode,
            "output": (run.stdout + run.stderr)[-4000:], "scope": "local product test only; not platform verification"}


def _paths(root: Path, item: dict) -> tuple[Path, Path, Path]:
    filename = f"{item['id']}-{_version(item)}-{item['type'].lower()}-candidate.zip"
    archive = _safe_relative(root, f"dist/{filename}", label="candidate")
    return archive, archive.with_name(filename + ".sha256"), archive.with_name(filename + ".manifest.json")


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def register_version(root: Path, product_id: str, version: str, *, source: str | None = None,
                     candidate: str = "UNKNOWN", sha256: str = "UNKNOWN", date: str = "UNKNOWN",
                     published_at: str = "UNKNOWN", activate: bool = True) -> dict:
    """Append immutable version metadata and optionally select it as active."""
    if not SEMVER.fullmatch(version):
        raise ValueError("invalid semantic version")
    catalog = load_catalog(root)
    item = next((entry for entry in catalog.get("products", []) if entry.get("id") == product_id), None)
    if item is None:
        raise ValueError(f"unregistered product: {product_id}")
    if any(entry.get("version") == version for entry in item.get("versions", [])):
        raise ValueError("version already registered; immutable history cannot be overwritten")
    expected_source = f"packages/{KINDS[item['type']]}/{product_id}"
    source = source or expected_source
    _safe_relative(root, source, label="source")
    if candidate != "UNKNOWN":
        _safe_relative(root, candidate, label="candidate")
    if sha256 != "UNKNOWN" and not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise ValueError("invalid sha256")
    if published_at != "UNKNOWN" and not isinstance(published_at, str):
        raise ValueError("published_at must be a string")
    entry = {"version": version, "source": source, "candidate": candidate, "sha256": sha256,
             "date": date, "published_at": published_at, "archive_evidence": candidate}
    item["versions"].append(entry)
    if activate:
        item["active_version"] = version
    _atomic_bytes(root / "products" / "catalog.json", _dump(catalog))
    return {"id": product_id, "active_version": item.get("active_version", _version(item)), "version": entry}


def package_product(root: Path, product_id: str) -> dict:
    item = get_product(root, product_id)
    report = validate_product(root, product_id)
    if report["status"] != "PASS":
        raise ValueError(f"product not valid: {report['findings']}")
    source = _source(root, item)
    version = _version_entry(item)
    # Read the complete payload once. The archive and manifest are both derived
    # from this immutable in-memory snapshot, never from a second source walk.
    content = {f"{product_id}/{p.relative_to(source).as_posix()}": p.read_bytes() for p in _files(source, item["type"])}
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zipped:
        for name, payload in sorted(content.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.external_attr = 0o100644 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            zipped.writestr(entry, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    raw = out.getvalue()
    with zipfile.ZipFile(io.BytesIO(raw)) as zipped:
        if zipped.testzip() is not None or zipped.namelist() != sorted(content) or any(zipped.read(name) != payload for name, payload in content.items()):
            raise ValueError("candidate archive readback failed")
    archive, sidecar, manifest = _paths(root, item)
    digest = _hash(raw)
    members = [{"path": name, "sha256": _hash(payload), "size": len(payload)} for name, payload in sorted(content.items())]
    archive_rel = _relative(root, archive)
    manifest_data = {"id": product_id, "version": _version(item), "status": "PASS", "archive": archive_rel,
                     "source": _relative(root, source), "sha256": digest, "members": members,
                     "payload_snapshot_sha256": _hash(_dump({"members": members})),
                     "scope": "local archive integrity only", "platform": "BLOCKED"}
    # Keep the historical API's absolute local readback path out of the
    # persisted manifest while retaining it for callers that open the result.
    result = {**manifest_data, "zip": str(archive)}
    expected_sidecar = f"{digest}  {archive.name}\n".encode("ascii")
    expected_manifest = _dump(manifest_data)
    artifacts = ((archive, raw), (sidecar, expected_sidecar), (manifest, expected_manifest))
    existing = {path: path.read_bytes() for path, _ in artifacts if path.exists()}
    if any(existing[path] != data for path, data in artifacts if path in existing):
        raise ValueError("refusing to overwrite different existing artifact")
    if existing and len(existing) != len(artifacts):
        # A partial candidate is never silently completed: callers can remove
        # it deliberately, but a failed run cannot create a mixed evidence set.
        raise ValueError("candidate artifact set is incomplete")
    archive.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{archive.stem}.staging-", dir=archive.parent))
    try:
        staged = []
        for path, data in artifacts:
            staged_path = staging / path.name
            staged_path.write_bytes(data)
            staged.append((staged_path, path))
        # Every member was fully written and is ready before any destination
        # is replaced. Each replacement is atomic on the same filesystem.
        if not existing:
            for staged_path, path in staged:
                os.replace(staged_path, path)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    catalog = load_catalog(root)
    catalog_item = next(entry for entry in catalog["products"] if entry["id"] == product_id)
    catalog_version = _version_entry(catalog_item)
    catalog_version.update(candidate=archive_rel, archive_evidence=archive_rel, sha256=digest)
    _atomic_bytes(root / "products" / "catalog.json", _dump(catalog))
    return result


def verify_package(root: Path, product_id: str) -> dict:
    item = get_product(root, product_id)
    archive, sidecar, manifest = _paths(root, item)
    try:
        info = _json(manifest)
        raw = archive.read_bytes()
        digest = _hash(raw)
        expected_archive = _relative(root, archive)
        version = _version_entry(item)
        if (info.get("id") != product_id or info.get("version") != _version(item) or info.get("status") != "PASS"
                or info.get("archive") != expected_archive or info.get("source") != _relative(root, _source(root, item))
                or info.get("sha256") != digest or version.get("candidate") != expected_archive
                or version.get("archive_evidence") != expected_archive or version.get("sha256") != digest
                or sidecar.read_bytes() != f"{digest}  {archive.name}\n".encode("ascii")):
            raise ValueError("manifest or sidecar hash mismatch")
        source = _source(root, item)
        expected = {f"{product_id}/{p.relative_to(source).as_posix()}": p.read_bytes() for p in _files(source, item["type"])}
        with zipfile.ZipFile(io.BytesIO(raw)) as zipped:
            if zipped.testzip() is not None or set(zipped.namelist()) != set(expected) or len(zipped.namelist()) != len(expected):
                raise ValueError("archive member mismatch")
            members = {entry["path"]: entry for entry in info["members"]}
            if set(members) != set(expected):
                raise ValueError("manifest member mismatch")
            for name, payload in expected.items():
                if zipped.read(name) != payload or members[name]["sha256"] != _hash(payload) or members[name]["size"] != len(payload):
                    raise ValueError(f"source/archive/manifest content mismatch: {name}")
        return {"id": product_id, "status": "PASS", "sha256": digest}
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        return {"id": product_id, "status": "FAIL", "reason": str(exc)}


def record_metric(root: Path, product_id: str, field: str, value: int | float | str, *, evidence: str) -> dict:
    item = get_product(root, product_id)
    if field not in METRIC_FIELDS or not evidence.strip() or evidence in {"UNKNOWN", "NOT_AVAILABLE"}:
        raise ValueError("metric field and concrete provenance required")
    if field != "review_result" and (isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0):
        raise ValueError("numeric metric must be nonnegative finite observed value")
    if field == "review_result" and value == "APPROVED":
        raise ValueError("verified platform approval cannot be created by a local metric record")
    if field == "review_result" and value not in {"REJECTED", "USER_REPORTED_SUBMITTED", "NOT_TESTED", "BLOCKED"}:
        raise ValueError("unsupported review result")
    path = root / "products/metrics.json"
    data = _json(path)
    version = _version(item)
    entry = next((x for x in data["metrics"] if x["id"] == product_id and x["version"] == version), None)
    if entry is None:
        entry = {"id": product_id, "version": version, **{key: "UNKNOWN" for key in METRIC_FIELDS}, "evidence": {}}
        data["metrics"].append(entry)
    entry[field] = value
    entry["evidence"][field] = evidence
    entry.setdefault("evidence_scope", {})[field] = "user-provided; unverified"
    entry["recorded_at"] = datetime.now(timezone.utc).isoformat()
    _atomic_bytes(path, _dump(data))
    return entry


def portfolio_report(root: Path) -> dict:
    catalog = load_catalog(root)
    data = _json(root / "products/metrics.json")
    output = []
    for item in catalog["products"]:
        metrics = next((x for x in data["metrics"] if x["id"] == item["id"] and x["version"] == _version(item)), {})
        exposures, installs = metrics.get("exposures", "UNKNOWN"), metrics.get("installs", "UNKNOWN")
        if not (isinstance(exposures, (int, float)) and not isinstance(exposures, bool) and math.isfinite(exposures) and exposures >= 0):
            exposures = "UNKNOWN"
        if not (isinstance(installs, (int, float)) and not isinstance(installs, bool) and math.isfinite(installs) and installs >= 0):
            installs = "UNKNOWN"
        rate = installs / exposures if (isinstance(exposures, (int, float)) and not isinstance(exposures, bool)
                                        and math.isfinite(exposures) and exposures > 0
                                        and isinstance(installs, (int, float)) and not isinstance(installs, bool)
                                        and math.isfinite(installs)) else "UNKNOWN"
        development = metrics.get("development_cost", "UNKNOWN")
        maintenance = metrics.get("maintenance_cost", "UNKNOWN")
        if not (isinstance(development, (int, float)) and not isinstance(development, bool) and math.isfinite(development) and development >= 0):
            development = "UNKNOWN"
        if not (isinstance(maintenance, (int, float)) and not isinstance(maintenance, bool) and math.isfinite(maintenance) and maintenance >= 0):
            maintenance = "UNKNOWN"
        total_cost = development + maintenance if (isinstance(development, (int, float)) and not isinstance(development, bool)
                                                   and math.isfinite(development) and isinstance(maintenance, (int, float))
                                                   and not isinstance(maintenance, bool) and math.isfinite(maintenance)) else "UNKNOWN"
        output.append({"id": item["id"], "type": item["type"], "status": item["status"], "review_status": item["review_status"],
                       "version": _version(item), "exposures": exposures, "installs": installs, "uses": metrics.get("uses", "UNKNOWN"),
                       "feedback": metrics.get("feedback", "UNKNOWN"), "development_cost": development,
                       "maintenance_cost": maintenance, "total_cost": total_cost, "install_rate": rate,
                       "success_rate": "UNKNOWN", "review_result": metrics.get("review_result", "UNKNOWN"),
                       "commercial_potential": "UNKNOWN", "data_gaps": [key for key in METRIC_FIELDS if metrics.get(key, "UNKNOWN") in {"UNKNOWN", "NOT_AVAILABLE"}]})
    return {"products": output, "scope": "observed metrics only; no commercial prediction"}


def _license_dependency_gate(source: Path, kind: str) -> dict:
    if not (source / "LICENSE").is_file():
        return {"status": "BLOCKED", "reason": "license file is absent; no license claim is verified"}
    declarations = []
    for path in source.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".json", ".yaml", ".yml", ".md"}:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if re.search(r"(?im)\b(dependencies|runtime|requires|tools|skills)\b", text):
                declarations.append(path.relative_to(source).as_posix())
    return {"status": "REQUIRES_MANUAL_REVIEW",
            "reason": "local files declare no independently verified license/dependency approval" if not declarations
                      else "declarations require manual license and dependency verification",
            "declarations": declarations}


def release_check(root: Path, product_id: str) -> dict:
    product = get_product(root, product_id)
    validation = validate_product(root, product_id)
    archive = verify_package(root, product_id)
    tests = test_product(root, product_id)
    local_candidate = "PASS" if validation["status"] == archive["status"] == tests["status"] == "PASS" else "BLOCKED"
    return {"id": product_id, "status": local_candidate, "local_validation": validation, "local_tests": tests, "archive": archive,
            "local_candidate": local_candidate,
            "platform": "BLOCKED", "platform_install": "NOT_TESTED", "platform_dialogue": "NOT_TESTED",
            "review": product["review_status"], "review_evidence": product["review_evidence"],
            "license_and_dependencies": _license_dependency_gate(_source(root, product), product["type"]),
            "publication": "BLOCKED"}
