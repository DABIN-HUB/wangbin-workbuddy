"""Conservative R9 Python dependency byte-closure auditor.

The auditor is read-only with respect to the interpreter, wheel cache, and lock
file.  It never installs or downloads.  A PASS requires an exact official
wheel named and hashed by the supplied ``uv.lock``, a byte-checked installed
RECORD, and a one-to-one wheel RECORD mapping.  Missing evidence is BLOCKED,
not an inferred pass.
"""
from __future__ import annotations

import argparse
import base64
import csv
from datetime import datetime, timezone
import ctypes
import hashlib
import importlib
import importlib.metadata
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import runpy
import subprocess
import sys
import sysconfig
from typing import Any, Iterable
from urllib.parse import urlsplit
import zipfile

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility only
    tomllib = None  # type: ignore[assignment]


SCHEMA = "solar-pv-dependency-closure/1"
PROBE_PREFIX = "R9_DEP_CLOSURE:"
MAX_LOCK_BYTES = 50_000_000
MAX_RECORD_BYTES = 10_000_000
MAX_WHEEL_BYTES = 500_000_000
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class AuditError(RuntimeError):
    """The requested byte evidence cannot be established."""


def _unresolved(code: str, subject: str, detail: str) -> dict[str, str]:
    return {"code": code, "subject": subject, "detail": detail}


def _normal_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _regular(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


def _fingerprint(path: Path) -> dict[str, Any]:
    path = path.resolve(strict=True)
    if not _regular(path):
        raise AuditError(f"not a regular file: {path}")
    stat = path.stat()
    return {
        "path": str(path),
        "size": stat.st_size,
        "sha256": _sha256_file(path),
        "mtime_ns": stat.st_mtime_ns,
    }


def _path_key(path: Path) -> str:
    return str(path.resolve(strict=False)).casefold()


def _under(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def _safe_posix_path(value: str, *, allow_parent: bool = False) -> PurePosixPath:
    if not value or "\\" in value or "\x00" in value:
        raise AuditError("invalid RECORD or wheel path")
    if re.match(r"^[A-Za-z]:", value) or value.startswith("/"):
        raise AuditError("absolute RECORD or wheel path")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts:
        raise AuditError("invalid RECORD or wheel path")
    if any(part == ".." for part in path.parts) and not allow_parent:
        raise AuditError("wheel path traversal")
    if any(part in {"", "."} for part in path.parts):
        raise AuditError("non-canonical RECORD or wheel path")
    return path


def _record_digest(value: str) -> str:
    if not value.startswith("sha256="):
        raise AuditError("RECORD entry is not sha256")
    encoded = value[7:]
    if not encoded:
        raise AuditError("empty RECORD digest")
    try:
        decoded = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    except (ValueError, base64.binascii.Error) as exc:
        raise AuditError("invalid RECORD digest") from exc
    if len(decoded) != 32:
        raise AuditError("invalid RECORD digest length")
    return decoded.hex()


def _read_record(path: Path) -> list[dict[str, str]]:
    if not _regular(path) or path.stat().st_size > MAX_RECORD_BYTES:
        raise AuditError(f"missing, linked, or oversized RECORD: {path}")
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    try:
        text = path.read_text(encoding="utf-8", newline="")
        reader = csv.reader(io.StringIO(text))
        for row in reader:
            if len(row) != 3:
                raise AuditError(f"malformed RECORD row: {path}")
            name, digest, size = row
            _safe_posix_path(name, allow_parent=True)
            if name in seen:
                raise AuditError(f"duplicate RECORD path: {name}")
            seen.add(name)
            rows.append({"path": name, "hash": digest, "size": size})
    except (OSError, UnicodeError, csv.Error) as exc:
        raise AuditError(f"cannot read RECORD: {path}") from exc
    if not rows:
        raise AuditError(f"empty RECORD: {path}")
    return rows


def _record_target(root: Path, relative: str, environment: dict[str, Any]) -> Path:
    posix = _safe_posix_path(relative, allow_parent=True)
    candidate = root.joinpath(*posix.parts)
    resolved = candidate.resolve(strict=False)
    # A symlink anywhere in the lexical path is not accepted as byte evidence.
    current = root
    for part in posix.parts:
        current = current / part
        if current.is_symlink():
            raise AuditError(f"linked installed file: {relative}")
    allowed_roots = [
        Path(str(environment.get(key)))
        for key in ("root", "purelib", "platlib", "scripts", "data", "headers")
        if environment.get(key)
    ]
    if not any(_under(resolved, allowed) for allowed in allowed_roots):
        raise AuditError(f"RECORD path escapes interpreter roots: {relative}")
    return resolved


def _runtime_tags(interpreter: dict[str, Any]) -> dict[str, str]:
    python_tag = str(interpreter.get("python_tag", ""))
    abi_tag = str(interpreter.get("abi_tag", ""))
    if python_tag.startswith("cpython-"):
        python_tag = "cp" + python_tag.removeprefix("cpython-")
    if abi_tag.startswith("cpython-"):
        abi_tag = "cp" + abi_tag.removeprefix("cpython-")
    return {
        "python": python_tag,
        "abi": abi_tag,
        "platform": str(interpreter.get("platform_tag", "")).lower(),
    }


def _wheel_compatible(filename: str, interpreter: dict[str, Any]) -> bool:
    if not filename.endswith(".whl"):
        return False
    parts = filename[:-4].split("-")
    if len(parts) < 5:
        return False
    py_tag, abi_tag, platform_tag = parts[-3:]
    runtime = _runtime_tags(interpreter)
    py_tags = set(py_tag.split("."))
    runtime_python = runtime["python"]
    runtime_major = runtime_python[2:3] if runtime_python.startswith("cp") else runtime_python[-1:]
    python_ok = runtime_python in py_tags or f"py{runtime_major}" in py_tags or "py" in py_tags
    abi_ok = abi_tag in {"none", "abi3", runtime["abi"]}
    platform_ok = platform_tag.lower() in {"any", runtime["platform"]}
    return python_ok and abi_ok and platform_ok


def audit_lock_file(path: Path | str) -> dict[str, Any]:
    """Parse and byte-bind a uv.lock without consulting the network."""
    path = Path(path)
    if not _regular(path) or path.stat().st_size > MAX_LOCK_BYTES:
        raise AuditError(f"missing, linked, or oversized uv.lock: {path}")
    raw = path.read_bytes()
    if tomllib is None:  # pragma: no cover
        raise AuditError("tomllib is unavailable")
    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError, TypeError) as exc:
        raise AuditError(f"invalid uv.lock TOML: {path}") from exc
    if data.get("version") != 1 or not isinstance(data.get("revision"), int):
        raise AuditError("unsupported uv.lock schema")
    packages: list[dict[str, Any]] = []
    for package in data.get("package", []):
        if not isinstance(package, dict) or not isinstance(package.get("name"), str) or not isinstance(package.get("version"), str):
            raise AuditError("invalid uv.lock package")
        artifacts: list[dict[str, Any]] = []
        for wheel in package.get("wheels", []):
            if not isinstance(wheel, dict):
                raise AuditError("invalid uv.lock wheel entry")
            url = wheel.get("url")
            digest = wheel.get("hash")
            size = wheel.get("size")
            if (not isinstance(url, str) or not isinstance(digest, str)
                    or not digest.startswith("sha256:")
                    or not _SHA256_RE.fullmatch(digest[7:])
                    or type(size) is not int or size < 0):
                raise AuditError(f"invalid locked wheel for {package['name']}")
            filename = Path(urlsplit(url).path).name
            if not filename.endswith(".whl"):
                raise AuditError(f"locked artifact is not a wheel: {url}")
            artifacts.append({"url": url, "sha256": digest[7:], "size": size, "filename": filename})
        packages.append({
            "name": package["name"],
            "normalized_name": _normal_name(package["name"]),
            "version": package["version"],
            "source": package.get("source"),
            "wheels": artifacts,
        })
    return {
        "path": str(path.resolve()),
        "sha256": _sha256_bytes(raw),
        "size": len(raw),
        "version": data["version"],
        "revision": data["revision"],
        "requires_python": data.get("requires-python"),
        "packages": packages,
        "package_count": len(packages),
    }


def _lock_packages(lock: dict[str, Any], name: str, version: str) -> list[dict[str, Any]]:
    return [package for package in lock.get("packages", [])
            if package.get("normalized_name") == _normal_name(name) and package.get("version") == version]


def _official_wheel(package: dict[str, Any], artifact: dict[str, Any]) -> bool:
    source = package.get("source")
    parsed = urlsplit(str(artifact.get("url", "")))
    return (isinstance(source, dict) and source.get("registry") == "https://pypi.org/simple"
            and parsed.scheme == "https" and parsed.netloc == "files.pythonhosted.org")


def _find_locked_wheel(
    package: dict[str, Any], wheel_dir: Path, interpreter: dict[str, Any]
) -> tuple[Path | None, dict[str, Any] | None, list[dict[str, str]]]:
    unresolved: list[dict[str, str]] = []
    if not wheel_dir.is_dir() or wheel_dir.is_symlink():
        return None, None, [_unresolved("WHEEL_UNAVAILABLE", package["name"], "wheel directory is unavailable or linked")]
    candidates: list[tuple[Path, dict[str, Any]]] = []
    for artifact in package.get("wheels", []):
        if not _official_wheel(package, artifact):
            unresolved.append(_unresolved("LOCK_ARTIFACT_NOT_OFFICIAL", package["name"], artifact["url"]))
            continue
        try:
            matches = [candidate for candidate in wheel_dir.rglob(artifact["filename"])
                       if _regular(candidate) and not candidate.is_symlink()]
        except OSError as exc:
            unresolved.append(_unresolved("WHEEL_UNAVAILABLE", artifact["filename"], str(exc)))
            continue
        if len(matches) > 1:
            unresolved.append(_unresolved("WHEEL_AMBIGUOUS", artifact["filename"], "multiple local files have the locked filename"))
            continue
        if not matches:
            continue
        candidate = matches[0]
        try:
            actual_size = candidate.stat().st_size
            actual_hash = _sha256_file(candidate)
        except OSError as exc:
            unresolved.append(_unresolved("WHEEL_UNAVAILABLE", str(candidate), str(exc)))
            continue
        if actual_size != artifact["size"] or actual_hash != artifact["sha256"]:
            unresolved.append(_unresolved("WHEEL_HASH_MISMATCH", str(candidate), "bytes differ from the exact uv.lock SHA-256 or size"))
            continue
        if _wheel_compatible(candidate.name, interpreter):
            candidates.append((candidate, artifact))
    if len(candidates) == 1:
        return candidates[0][0], candidates[0][1], unresolved
    if len(candidates) > 1:
        unresolved.append(_unresolved("WHEEL_AMBIGUOUS", package["name"], "more than one compatible locked wheel is present"))
    elif not unresolved:
        unresolved.append(_unresolved("WHEEL_UNAVAILABLE", package["name"], "no local wheel matches an official locked artifact"))
    elif not any(item["code"] == "WHEEL_HASH_MISMATCH" for item in unresolved):
        unresolved.append(_unresolved("WHEEL_UNAVAILABLE", package["name"], "no compatible local wheel matches an official locked artifact"))
    return None, None, unresolved


def _parse_wheel(path: Path) -> dict[str, Any]:
    if not _regular(path) or path.stat().st_size > MAX_WHEEL_BYTES:
        raise AuditError(f"missing, linked, or oversized wheel: {path}")
    try:
        with zipfile.ZipFile(path, "r") as archive:
            infos = [info for info in archive.infolist() if not info.is_dir()]
            names: set[str] = set()
            files: dict[str, bytes] = {}
            for info in infos:
                _safe_posix_path(info.filename)
                if info.filename in names:
                    raise AuditError(f"duplicate wheel member: {info.filename}")
                names.add(info.filename)
                if ((info.external_attr >> 16) & 0o170000) == 0o120000:
                    raise AuditError(f"linked wheel member: {info.filename}")
                files[info.filename] = archive.read(info)
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        raise AuditError(f"invalid wheel archive: {path}") from exc
    record_names = [name for name in files if name.endswith(".dist-info/RECORD")]
    if len(record_names) != 1:
        raise AuditError("wheel must contain exactly one dist-info/RECORD")
    record_name = record_names[0]
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    try:
        reader = csv.reader(io.StringIO(files[record_name].decode("utf-8")))
        for row in reader:
            if len(row) != 3:
                raise AuditError("malformed wheel RECORD row")
            name, digest, size = row
            _safe_posix_path(name)
            if name in seen:
                raise AuditError(f"duplicate wheel RECORD path: {name}")
            seen.add(name)
            rows.append({"path": name, "hash": digest, "size": size})
    except (UnicodeError, csv.Error) as exc:
        raise AuditError("cannot parse wheel RECORD") from exc
    if set(files) != seen:
        raise AuditError("wheel RECORD does not correspond to wheel members")
    for row in rows:
        content = files[row["path"]]
        if row["path"] == record_name:
            if row["hash"] or row["size"]:
                raise AuditError("wheel RECORD must have an empty self-row")
        else:
            if _record_digest(row["hash"]) != _sha256_bytes(content) or int(row["size"]) != len(content):
                raise AuditError(f"wheel RECORD hash mismatch: {row['path']}")
    metadata_name = record_name.removesuffix("/RECORD") + "/METADATA"
    if metadata_name not in files:
        raise AuditError("wheel METADATA is missing")
    headers: dict[str, str] = {}
    for line in files[metadata_name].decode("utf-8").splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            if key in {"Name", "Version"}:
                headers[key] = value
    return {"record_name": record_name, "rows": rows, "files": files, "metadata": headers}


def _audit_installed_record(
    distribution: dict[str, Any], environment: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Path], list[dict[str, str]]]:
    unresolved: list[dict[str, str]] = []
    result: dict[str, Any] = {"status": "BLOCKED", "installed_files": 0, "rows": []}
    try:
        dist_info = Path(str(distribution["dist_info"])).resolve(strict=True)
        record = Path(str(distribution.get("record", dist_info / "RECORD"))).resolve(strict=True)
        if not dist_info.is_dir() or dist_info.is_symlink() or record != dist_info / "RECORD":
            raise AuditError("distribution RECORD path is not the adjacent regular RECORD")
        root = dist_info.parent
        rows = _read_record(record)
        record_name = dist_info.relative_to(root).as_posix() + "/RECORD"
        row_map: dict[str, Path] = {}
        for row in rows:
            target = _record_target(root, row["path"], environment)
            if not _regular(target):
                raise AuditError(f"missing or linked installed file: {row['path']}")
            row_map[row["path"]] = target
            if row["path"] == record_name:
                if row["hash"] or row["size"]:
                    raise AuditError("installed RECORD self-row must be empty")
            else:
                expected_hash = _record_digest(row["hash"])
                if not row["size"].isdigit() or int(row["size"]) != target.stat().st_size:
                    unresolved.append(_unresolved("INSTALLED_FILE_SIZE_MISMATCH", row["path"], "size differs from RECORD"))
                if expected_hash != _sha256_file(target):
                    unresolved.append(_unresolved("INSTALLED_FILE_HASH_MISMATCH", row["path"], "bytes differ from installed RECORD"))
        if record_name not in row_map:
            raise AuditError("installed RECORD does not contain its own row")
        result = {"status": "PASS" if not unresolved else "BLOCKED",
                  "installed_files": len(rows), "rows": rows,
                  "record_sha256": _sha256_file(record)}
        return result, row_map, unresolved
    except (AuditError, KeyError, OSError, ValueError) as exc:
        unresolved.append(_unresolved("RECORD_UNAVAILABLE", str(distribution.get("name", "unknown")), str(exc)))
        return result, {}, unresolved


def _wheel_target(member: str, wheel_record_name: str, environment: dict[str, Any]) -> Path:
    if ".data/" not in member:
        # Ordinary wheel members install into purelib/platlib, never sys.prefix.
        # In a venv these are distinct roots; a synthetic fixture where they
        # coincide must not make an incorrect real-world mapping look valid.
        if environment.get("purelib") != environment.get("platlib"):
            raise AuditError("ordinary wheel target is ambiguous between purelib and platlib")
        return Path(str(environment["purelib"])).resolve() / Path(*_safe_posix_path(member).parts)
    prefix, separator, rest = member.partition(".data/")
    if not separator or "/" not in rest:
        raise AuditError(f"unsupported wheel member mapping: {member}")
    category, _, tail = rest.partition("/")
    mapping = {"purelib": "purelib", "platlib": "platlib", "scripts": "scripts", "data": "data", "headers": "headers"}
    if category not in mapping or not tail:
        raise AuditError(f"unsupported wheel .data mapping: {member}")
    return Path(str(environment[mapping[category]])).resolve() / Path(*_safe_posix_path(tail).parts)


def audit_distribution(
    distribution: dict[str, Any],
    lock: dict[str, Any],
    wheel_dir: Path | str,
    environment: dict[str, Any],
    interpreter: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Audit one installed distribution against its exact official lock wheel."""
    interpreter = interpreter or {
        "python_tag": f"cp{sys.version_info.major}{sys.version_info.minor}" if platform.python_implementation() == "CPython" else f"py{sys.version_info.major}",
        "abi_tag": f"cp{sys.version_info.major}{sys.version_info.minor}" if platform.python_implementation() == "CPython" else "",
        "platform_tag": sysconfig.get_platform().replace("-", "_").replace(".", "_").lower(),
    }
    name = str(distribution.get("name", ""))
    version = str(distribution.get("version", ""))
    result: dict[str, Any] = {"name": name, "version": version, "verdict": "BLOCKED", "record": None, "wheel": None, "unresolved": []}
    record_result, installed_map, record_errors = _audit_installed_record(distribution, environment)
    result["record"] = record_result
    result["unresolved"].extend(record_errors)
    packages = _lock_packages(lock, name, version)
    if not packages:
        result["unresolved"].append(_unresolved("LOCK_PACKAGE_UNAVAILABLE", name, f"{name}=={version} is absent from uv.lock"))
        return result
    if len(packages) != 1:
        result["unresolved"].append(_unresolved("LOCK_PACKAGE_AMBIGUOUS", name, f"{len(packages)} matching uv.lock package entries"))
        return result
    package = packages[0]
    wheel_path, artifact, wheel_errors = _find_locked_wheel(package, Path(wheel_dir), interpreter)
    result["unresolved"].extend(wheel_errors)
    if wheel_path is None or artifact is None:
        return result
    try:
        wheel = _parse_wheel(wheel_path)
        result["wheel"] = {"path": str(wheel_path.resolve()), "hash_source": "uv.lock", "sha256": artifact["sha256"], "size": artifact["size"], "record_name": wheel["record_name"]}
        if (_normal_name(wheel["metadata"].get("Name", "")) != _normal_name(name)
                or wheel["metadata"].get("Version") != version):
            raise AuditError("wheel METADATA name/version differs from installed distribution")
        mapped: dict[str, dict[str, Any]] = {}
        for row in wheel["rows"]:
            target = _wheel_target(row["path"], wheel["record_name"], environment)
            mapped[_path_key(target)] = {"target": target, "row": row}
        if set(mapped) != set(_path_key(path) for path in installed_map.values()):
            raise AuditError("wheel RECORD and installed RECORD file sets differ")
        for item in mapped.values():
            target = item["target"]
            row = item["row"]
            installed = installed_map.get(next((key for key, path in installed_map.items() if _path_key(path) == _path_key(target)), ""))
            if installed is None or _path_key(installed) != _path_key(target):
                raise AuditError(f"wheel RECORD member is not installed: {row['path']}")
            if row["path"] != wheel["record_name"]:
                if _record_digest(row["hash"]) != _sha256_file(installed) or int(row["size"]) != installed.stat().st_size:
                    raise AuditError(f"wheel/installed bytes differ: {row['path']}")
        if result["unresolved"]:
            return result
        result["verdict"] = "PASS"
    except (AuditError, OSError, ValueError, KeyError) as exc:
        result["unresolved"].append(_unresolved("WHEEL_RECORD_UNAVAILABLE", name, str(exc)))
    return result


def _module_file_entry(name: str, path_value: str) -> tuple[dict[str, Any] | None, dict[str, str] | None]:
    try:
        path = Path(path_value).resolve(strict=True)
        if not _regular(path):
            raise AuditError("module path is not a regular file")
        return {"name": name, **_fingerprint(path)}, None
    except (AuditError, OSError) as exc:
        return None, _unresolved("LOADED_MODULE_UNAVAILABLE", name, str(exc))


def _windows_native_paths() -> tuple[list[Path], list[dict[str, str]]]:
    from ctypes import wintypes
    errors: list[dict[str, str]] = []
    try:
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        get_current = kernel32.GetCurrentProcess
        get_current.argtypes = []
        get_current.restype = wintypes.HANDLE
        enum = psapi.EnumProcessModulesEx
        enum.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_void_p), wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.DWORD]
        enum.restype = wintypes.BOOL
        get_name = psapi.GetModuleFileNameExW
        get_name.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.LPWSTR, wintypes.DWORD]
        get_name.restype = wintypes.DWORD
        capacity = 256
        handles: list[ctypes.c_void_p] = []
        while capacity <= 16384:
            array = (ctypes.c_void_p * capacity)()
            needed = wintypes.DWORD()
            if not enum(get_current(), array, ctypes.sizeof(array), ctypes.byref(needed), 0x03):
                raise OSError(ctypes.get_last_error(), "EnumProcessModulesEx failed")
            count = needed.value // ctypes.sizeof(ctypes.c_void_p)
            if count < capacity:
                handles = list(array[:count])
                break
            capacity *= 2
        if not handles:
            raise OSError("no loaded native modules returned")
        paths: list[Path] = []
        for handle in handles:
            buffer = ctypes.create_unicode_buffer(32768)
            length = get_name(get_current(), handle, buffer, len(buffer))
            if not length:
                errors.append(_unresolved("NATIVE_MODULE_UNAVAILABLE", "unknown", "GetModuleFileNameExW failed"))
            else:
                paths.append(Path(buffer.value))
        return paths, errors
    except (AttributeError, OSError, ctypes.Error) as exc:
        return [], [_unresolved("NATIVE_MODULE_ENUMERATION_FAILED", "current-process", str(exc))]


def _native_library_snapshot() -> tuple[dict[str, Any], list[dict[str, str]]]:
    if os.name == "nt":
        paths, unresolved = _windows_native_paths()
    elif sys.platform.startswith("linux"):
        paths, unresolved = [], []
        maps = Path("/proc/self/maps")
        try:
            for line in maps.read_text(encoding="utf-8", errors="replace").splitlines():
                if "/" not in line:
                    continue
                candidate = Path(line.rsplit(" ", 1)[-1])
                if candidate.suffix == ".so" or ".so." in candidate.name:
                    paths.append(candidate)
        except OSError as exc:
            unresolved.append(_unresolved("NATIVE_MODULE_ENUMERATION_FAILED", str(maps), str(exc)))
    else:
        return {"status": "BLOCKED", "libraries": [], "method": "unsupported-platform"}, [
            _unresolved("NATIVE_MODULE_ENUMERATION_UNSUPPORTED", platform.system(), "native loader enumeration is not implemented for this platform")
        ]
    libraries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in paths:
        try:
            resolved = path.resolve(strict=True)
            key = _path_key(resolved)
            if key in seen:
                continue
            seen.add(key)
            if not _regular(resolved):
                raise AuditError("native module is not a regular file")
            libraries.append(_fingerprint(resolved))
        except (AuditError, OSError) as exc:
            unresolved.append(_unresolved("NATIVE_MODULE_UNAVAILABLE", str(path), str(exc)))
    status = "COMPLETE" if not unresolved and libraries else "BLOCKED"
    return {"status": status, "method": "Windows PSAPI EnumProcessModulesEx" if os.name == "nt" else "/proc/self/maps", "libraries": sorted(libraries, key=lambda item: item["path"])}, unresolved


def collect_runtime_snapshot(modules: Iterable[str] = ()) -> dict[str, Any]:
    """Collect point-in-time interpreter, loaded-module, and native-loader evidence."""
    unresolved: list[dict[str, str]] = []
    for module in modules:
        try:
            importlib.import_module(module)
        except (ImportError, AttributeError, ValueError) as exc:
            unresolved.append(_unresolved("MODULE_IMPORT_FAILED", module, str(exc)))
    interpreter_path = Path(sys.executable).resolve()
    try:
        interpreter = _fingerprint(interpreter_path)
    except (AuditError, OSError) as exc:
        interpreter = {"path": str(interpreter_path), "status": "BLOCKED"}
        unresolved.append(_unresolved("INTERPRETER_UNAVAILABLE", str(interpreter_path), str(exc)))
    implementation = platform.python_implementation()
    version_info = sys.version_info
    interpreter.update({
        "version": sys.version,
        "implementation": implementation,
        "architecture": platform.architecture()[0],
        "python_tag": f"cp{version_info.major}{version_info.minor}" if implementation == "CPython" else f"py{version_info.major}",
        "abi_tag": f"cp{version_info.major}{version_info.minor}" if implementation == "CPython" else "",
        "platform_tag": sysconfig.get_platform().replace("-", "_").replace(".", "_").lower(),
    })
    roots = {key: sysconfig.get_path(key) for key in ("purelib", "platlib", "scripts", "data", "include")}
    roots["root"] = sys.prefix
    distributions: list[dict[str, Any]] = []
    for dist in importlib.metadata.distributions():
        name = dist.metadata.get("Name")
        if not name:
            continue
        dist_info = Path(str(getattr(dist, "_path", "")))
        distributions.append({
            "name": name,
            "version": dist.version,
            "dist_info": str(dist_info.resolve(strict=False)),
            "record": str((dist_info / "RECORD").resolve(strict=False)),
        })
    loaded_modules: list[dict[str, Any]] = []
    seen_modules: set[tuple[str, str]] = set()
    for name, module in sorted(sys.modules.items()):
        path_value = getattr(module, "__file__", None)
        if not isinstance(path_value, str):
            continue
        key = (name, path_value)
        if key in seen_modules:
            continue
        seen_modules.add(key)
        entry, error = _module_file_entry(name, path_value)
        if entry:
            loaded_modules.append(entry)
        if error:
            unresolved.append(error)
    native, native_errors = _native_library_snapshot()
    unresolved.extend(native_errors)
    return {
        "interpreter": interpreter,
        "sys_path": [str(Path(item or os.getcwd()).resolve()) for item in sys.path],
        "environment_roots": {key: str(Path(value).resolve()) for key, value in roots.items() if value},
        "distributions": sorted(distributions, key=lambda item: (_normal_name(item["name"]), item["version"], item["dist_info"])),
        "loaded_modules": sorted(loaded_modules, key=lambda item: item["name"]),
        "native_libraries": native,
        "unresolved": unresolved,
    }


def _probe_interpreter(interpreter: Path, modules: tuple[str, ...]) -> dict[str, Any]:
    module_path = Path(__file__).resolve()
    code = (
        "import contextlib, io, json, runpy, sys\n"
        f"namespace = runpy.run_path({str(module_path)!r})\n"
        "sink_out, sink_err = io.StringIO(), io.StringIO()\n"
        "with contextlib.redirect_stdout(sink_out), contextlib.redirect_stderr(sink_err):\n"
        f"    result = namespace['collect_runtime_snapshot']({modules!r})\n"
        f"sys.stdout.write({PROBE_PREFIX!r} + json.dumps(result, ensure_ascii=False, sort_keys=True))\n"
    )
    # Ignore inherited PYTHONPATH/user-site startup injection. Any startup
    # output, extra marker or nonzero exit invalidates the observation; never
    # accept the first line that merely looks like our result.
    env = os.environ.copy()
    for key in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP"):
        env.pop(key, None)
    completed = subprocess.run([str(interpreter), "-I", "-c", code], cwd=str(module_path.parents[1]),
                               env=env, capture_output=True, text=True, timeout=180, check=False)
    if completed.returncode != 0:
        raise AuditError(f"interpreter probe failed with exit code {completed.returncode}")
    if completed.stderr or len(completed.stdout.splitlines()) != 1:
        raise AuditError("interpreter probe emitted unexpected startup output")
    line = completed.stdout.rstrip("\r\n")
    if not line.startswith(PROBE_PREFIX):
        raise AuditError("interpreter probe marker missing")
    try:
        result = json.loads(line[len(PROBE_PREFIX):])
    except json.JSONDecodeError as exc:
        raise AuditError("interpreter probe returned invalid JSON") from exc
    if not isinstance(result, dict) or not isinstance(result.get("interpreter"), dict):
        raise AuditError("interpreter probe returned invalid structure")
    observed = result["interpreter"]
    if (Path(str(observed.get("path", ""))).resolve(strict=False) != interpreter.resolve(strict=True)
            or observed.get("sha256") != _sha256_file(interpreter)
            or not isinstance(result.get("distributions"), list)
            or not result["distributions"]
            or not isinstance(result.get("sys_path"), list)
            or not isinstance(result.get("loaded_modules"), list)
            or not isinstance(result.get("native_libraries"), dict)
            or not isinstance(result.get("unresolved"), list)):
        raise AuditError("interpreter identity or distribution inventory cannot be authenticated")
    return result


def _blocked_manifest(reason: dict[str, str], interpreter: Path | str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": "BLOCKED",
        "interpreter_request": str(Path(interpreter).resolve(strict=False)),
        "interpreter": None,
        "lock": None,
        "distributions": [],
        "loaded_modules": [],
        "native_libraries": {"status": "BLOCKED", "libraries": []},
        "unresolved": [reason],
        "proof_boundaries": _proof_boundaries(),
    }


def _proof_boundaries() -> list[str]:
    return [
        "The loaded-module and native-library inventory is a point-in-time snapshot; it does not prove future lazy imports.",
        "A wheel is accepted only when its local bytes match an official files.pythonhosted.org SHA-256 and size recorded in uv.lock; no network fetch is attempted.",
        "RECORD and wheel RECORD are compared byte-for-byte through their hashes and mapped installed paths; files absent from either RECORD are outside this proof.",
        "The manifest contains hashed environment identities, not a proof that an external operating-system loader will resolve every future DLL dependency.",
    ]


def audit_dependency_closure(
    *,
    interpreter: Path | str = sys.executable,
    lock_path: Path | str,
    wheel_dir: Path | str,
    output: Path | str | None = None,
    modules: Iterable[str] = (),
) -> dict[str, Any]:
    """Integration API: return and optionally write a fail-closed closure manifest."""
    interpreter = Path(interpreter)
    modules_tuple = tuple(modules)
    try:
        if not _regular(interpreter):
            manifest = _blocked_manifest(_unresolved("INTERPRETER_UNAVAILABLE", str(interpreter), "interpreter is not a regular file"), interpreter)
            if output is not None:
                write_manifest(manifest, Path(output))
            return manifest
        snapshot = _probe_interpreter(interpreter.resolve(), modules_tuple)
    except (AuditError, OSError, subprocess.SubprocessError, ValueError) as exc:
        manifest = _blocked_manifest(_unresolved("INTERPRETER_PROBE_FAILED", str(interpreter), str(exc)), interpreter)
        if output is not None:
            write_manifest(manifest, Path(output))
        return manifest
    unresolved = list(snapshot.get("unresolved", []))
    try:
        lock = audit_lock_file(lock_path)
    except (AuditError, OSError, ValueError) as exc:
        manifest = {
            "schema": SCHEMA,
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "verdict": "BLOCKED",
            "interpreter": snapshot["interpreter"],
            "sys_path": snapshot["sys_path"],
            "environment_roots": snapshot["environment_roots"],
            "lock": {"path": str(Path(lock_path).resolve(strict=False)), "status": "BLOCKED"},
            "distributions": snapshot["distributions"],
            "loaded_modules": snapshot["loaded_modules"],
            "native_libraries": snapshot["native_libraries"],
            "unresolved": unresolved + [_unresolved("LOCK_UNAVAILABLE", str(lock_path), str(exc))],
            "proof_boundaries": _proof_boundaries(),
        }
        if output is not None:
            write_manifest(manifest, Path(output))
        return manifest
    audited: list[dict[str, Any]] = []
    for distribution in snapshot["distributions"]:
        try:
            audited.append(audit_distribution(distribution, lock, wheel_dir, snapshot["environment_roots"], snapshot["interpreter"]))
        except (AuditError, OSError, ValueError, KeyError) as exc:
            audited.append({
                "name": distribution.get("name"),
                "version": distribution.get("version"),
                "verdict": "BLOCKED",
                "record": None,
                "wheel": None,
                "unresolved": [_unresolved("DISTRIBUTION_AUDIT_FAILED", str(distribution.get("name", "unknown")), str(exc))],
            })
    unresolved.extend(item for result in audited for item in result["unresolved"])
    manifest = {
        "schema": SCHEMA,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "verdict": "PASS" if not unresolved and all(result["verdict"] == "PASS" for result in audited) and snapshot["native_libraries"].get("status") == "COMPLETE" else "BLOCKED",
        "interpreter": snapshot["interpreter"],
        "sys_path": snapshot["sys_path"],
        "environment_roots": snapshot["environment_roots"],
        "lock": lock,
        "distributions": audited,
        "loaded_modules": snapshot["loaded_modules"],
        "native_libraries": snapshot["native_libraries"],
        "unresolved": unresolved,
        "proof_boundaries": _proof_boundaries(),
    }
    if output is not None:
        write_manifest(manifest, Path(output))
    return manifest


def write_manifest(manifest: dict[str, Any], output: Path) -> None:
    """Write one JSON manifest without replacing an existing evidence file."""
    output = output.resolve(strict=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", dest="interpreter", type=Path, default=Path(sys.executable))
    parser.add_argument("--lock", dest="lock_path", type=Path, required=True)
    parser.add_argument("--wheel-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--module", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        manifest = audit_dependency_closure(
            interpreter=args.interpreter,
            lock_path=args.lock_path,
            wheel_dir=args.wheel_dir,
            output=args.out,
            modules=args.module,
        )
    except (AuditError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"verdict": manifest["verdict"], "unresolved": len(manifest["unresolved"])}, sort_keys=True))
    return 0 if manifest["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
