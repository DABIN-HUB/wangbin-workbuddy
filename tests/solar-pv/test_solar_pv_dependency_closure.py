from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import sys
import zipfile

import pytest

from tooling import solar_pv_dependency_closure as closure


WHEEL_NAME = "demo_pkg-1.0-py3-none-any.whl"
DIST_INFO = "demo_pkg-1.0.dist-info"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _record_digest(data: bytes) -> str:
    encoded = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=")
    return "sha256=" + encoded.decode("ascii")


def _record_line(name: str, data: bytes) -> str:
    return f"{name},{_record_digest(data)},{len(data)}"


def _make_fixture(tmp_path: Path) -> tuple[dict, dict, Path]:
    site = tmp_path / "site-packages"
    site.mkdir()
    (site / "Scripts").mkdir()
    (site / "include").mkdir()
    files = {
        "demo_pkg/__init__.py": b"VALUE = 1\n",
        f"{DIST_INFO}/METADATA": (
            b"Metadata-Version: 2.1\nName: demo-pkg\nVersion: 1.0\n"
        ),
    }
    record_name = f"{DIST_INFO}/RECORD"
    record = "\n".join(
        [_record_line(name, data) for name, data in sorted(files.items())]
        + [f"{record_name},,", ""]
    ).encode("utf-8")
    files[record_name] = record
    for relative, data in files.items():
        path = site / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    wheel_dir = tmp_path / "wheelhouse"
    wheel_dir.mkdir()
    wheel_path = wheel_dir / WHEEL_NAME
    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative, data in files.items():
            archive.writestr(relative, data)

    wheel_hash = _sha256(wheel_path.read_bytes())
    lock_path = tmp_path / "uv.lock"
    lock_path.write_text(
        "\n".join(
            [
                "version = 1",
                "revision = 3",
                'requires-python = ">=3.11"',
                "",
                "[[package]]",
                'name = "demo-pkg"',
                'version = "1.0"',
                'source = { registry = "https://pypi.org/simple" }',
                "wheels = [",
                f'    {{ url = "https://files.pythonhosted.org/packages/demo/{WHEEL_NAME}", hash = "sha256:{wheel_hash}", size = {wheel_path.stat().st_size} }},',
                "]",
                "",
            ]
        ),
        encoding="utf-8",
    )
    installed = {
        "name": "demo-pkg",
        "version": "1.0",
        "dist_info": str(site / DIST_INFO),
        "record": str(site / record_name),
        "record_rows": [
            {"path": name, "hash": _record_digest(data), "size": str(len(data))}
            for name, data in sorted(files.items())
            if name != record_name
        ]
        + [{"path": record_name, "hash": "", "size": ""}],
    }
    environment = {
        "root": str(site),
        "purelib": str(site),
        "platlib": str(site),
        "scripts": str(site / "Scripts"),
        "data": str(site),
        "headers": str(site / "include"),
    }
    return installed, environment, lock_path


def test_exact_locked_wheel_and_record_bytes_close(tmp_path: Path) -> None:
    installed, environment, lock_path = _make_fixture(tmp_path)
    # A real venv's sys.prefix is not its site-packages installation directory.
    environment["root"] = str(tmp_path)
    lock = closure.audit_lock_file(lock_path)

    result = closure.audit_distribution(
        installed,
        lock,
        tmp_path / "wheelhouse",
        environment,
    )

    assert result["verdict"] == "PASS"
    assert result["wheel"]["hash_source"] == "uv.lock"
    assert result["record"]["installed_files"] == 3
    assert result["unresolved"] == []


def test_missing_wheel_fails_closed_even_when_record_matches(tmp_path: Path) -> None:
    installed, environment, lock_path = _make_fixture(tmp_path)
    lock = closure.audit_lock_file(lock_path)
    empty_wheelhouse = tmp_path / "empty-wheelhouse"
    empty_wheelhouse.mkdir()

    result = closure.audit_distribution(installed, lock, empty_wheelhouse, environment)

    assert result["verdict"] == "BLOCKED"
    assert any(item["code"] == "WHEEL_UNAVAILABLE" for item in result["unresolved"])


def test_installed_record_tamper_fails_closed(tmp_path: Path) -> None:
    installed, environment, lock_path = _make_fixture(tmp_path)
    (Path(environment["root"]) / "demo_pkg" / "__init__.py").write_bytes(b"VALUE = 2\n")
    lock = closure.audit_lock_file(lock_path)

    result = closure.audit_distribution(
        installed,
        lock,
        tmp_path / "wheelhouse",
        environment,
    )

    assert result["verdict"] == "BLOCKED"
    assert any(item["code"] == "INSTALLED_FILE_HASH_MISMATCH" for item in result["unresolved"])


def test_locked_wheel_sha_mismatch_fails_closed(tmp_path: Path) -> None:
    installed, environment, lock_path = _make_fixture(tmp_path)
    wheel_hash = closure._sha256_file(tmp_path / "wheelhouse" / WHEEL_NAME)
    lock_text = lock_path.read_text(encoding="utf-8").replace(
        f'hash = "sha256:{wheel_hash}',
        'hash = "sha256:' + "0" * 64,
    )
    lock_path.write_text(lock_text, encoding="utf-8")
    lock = closure.audit_lock_file(lock_path)

    result = closure.audit_distribution(installed, lock, tmp_path / "wheelhouse", environment)

    assert result["verdict"] == "BLOCKED"
    assert any(item["code"] == "WHEEL_HASH_MISMATCH" for item in result["unresolved"])


def test_missing_record_row_fails_closed(tmp_path: Path) -> None:
    installed, environment, lock_path = _make_fixture(tmp_path)
    record = Path(installed["record"])
    record.write_text(
        "demo_pkg/__init__.py," + _record_digest(b"VALUE = 1\n") + ",10\n",
        encoding="utf-8",
    )
    lock = closure.audit_lock_file(lock_path)

    result = closure.audit_distribution(installed, lock, tmp_path / "wheelhouse", environment)

    assert result["verdict"] == "BLOCKED"
    assert any(item["code"] == "RECORD_UNAVAILABLE" for item in result["unresolved"])


def test_runtime_snapshot_binds_interpreter_and_loaded_module() -> None:
    snapshot = closure.collect_runtime_snapshot(modules=("json",))

    assert snapshot["interpreter"]["path"] == str(Path(sys.executable).resolve())
    assert len(snapshot["interpreter"]["sha256"]) == 64
    assert any(item["name"] == "json" for item in snapshot["loaded_modules"])
    assert snapshot["native_libraries"]["status"] in {"COMPLETE", "BLOCKED"}


def test_missing_lock_still_writes_blocked_manifest(tmp_path: Path) -> None:
    output = tmp_path / "manifest.json"
    manifest = closure.audit_dependency_closure(
        interpreter=Path(sys.executable),
        lock_path=tmp_path / "missing-uv.lock",
        wheel_dir=tmp_path / "missing-wheelhouse",
        output=output,
        modules=("json",),
    )

    assert manifest["verdict"] == "BLOCKED"
    assert any(item["code"] == "LOCK_UNAVAILABLE" for item in manifest["unresolved"])
    assert json.loads(output.read_text(encoding="utf-8"))["verdict"] == "BLOCKED"


def test_interpreter_probe_ignores_injected_pythonpath_sitecustomize(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "sitecustomize.py").write_text(
        "print('R9_DEP_CLOSURE:{\"interpreter\":{\"path\":\"forged\"},\"distributions\":[]}')\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    result = closure._probe_interpreter(Path(sys.executable), ("json",))
    assert result["interpreter"]["path"] == str(Path(sys.executable).resolve())
    assert result["distributions"]


def test_nonzero_probe_output_cannot_become_a_success(monkeypatch) -> None:
    def nonzero_process(*args, **kwargs):
        return closure.subprocess.CompletedProcess(
            args[0], 3, stdout=closure.PROBE_PREFIX + "{}", stderr=""
        )
    monkeypatch.setattr(closure.subprocess, "run", nonzero_process)
    with pytest.raises(closure.AuditError, match="exit code 3"):
        closure._probe_interpreter(Path(sys.executable), ("json",))


def test_unavailable_interpreter_writes_blocked_receipt(tmp_path: Path) -> None:
    output = tmp_path / "unavailable-interpreter.json"
    result = closure.audit_dependency_closure(
        interpreter=tmp_path / "missing-python.exe",
        lock_path=tmp_path / "missing-uv.lock",
        wheel_dir=tmp_path / "missing-wheelhouse",
        output=output,
    )
    assert result["verdict"] == "BLOCKED"
    assert json.loads(output.read_text(encoding="utf-8")) == result
