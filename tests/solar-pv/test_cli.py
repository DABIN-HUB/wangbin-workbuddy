"""Real subprocess acceptance of the local-only JSON intake boundary (SYNTHETIC)."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / "services/solar-pv-engine/solar_pv.py"
SOURCE = ROOT / "services/solar-pv-engine/src"


def run_cli(workspace, *args, expected=0):
    env = dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run([sys.executable, str(ENTRY), "--workspace", str(workspace), *map(str, args)],
                            cwd=workspace, env=env, capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert result.returncode == expected, (result.returncode, result.stdout, result.stderr)
    return result


def packet(root, data, name="packet.json"):
    path = root / name
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path.name


def new(root):
    return run_cli(root, "new", "--project-id", "SYNTHETIC", "--pv-type", "industrial_rooftop", "--state", "project.json")


def read(root, name="project.json"):
    return json.loads((root / name).read_text(encoding="utf-8"))


def error(root, *args, code):
    result = run_cli(root, *args, expected=2)
    data = json.loads(result.stderr)
    assert data["error"]["code"] == code
    assert set(data["error"]) == {"code", "field_id"}
    assert str(root) not in result.stderr and "Traceback" not in result.stderr
    return data["error"]


def test_new_and_status_are_real_commands_without_private_data_logs(tmp_path):
    result = new(tmp_path)
    summary = json.loads(result.stdout)
    assert summary["revision"] == 0
    assert summary["maturity"]["current_level"] == "L1_DRAFT"
    assert 0 < len(summary["next_questions"]) <= 5
    assert "SYNTHETIC" not in result.stdout
    project = read(tmp_path)
    assert project["project_id"] == "SYNTHETIC" and project["revision"] == 0
    assert project["values"]["project.pv_type"]["status"] == "UNVERIFIED"
    assert json.loads(run_cli(tmp_path, "status", "--state", "project.json").stdout)["revision"] == 0


def update(root, command, data, revision, *, expected=0):
    return run_cli(root, command, "--state", "project.json", "--input", packet(root, data),
                   "--expected-revision", revision, expected=expected)


def test_multiround_cli_conflict_revision_idempotency_review_remove_and_export(tmp_path):
    new(tmp_path)
    first = {"submission_id": "round1", "updates": [{"field_id": "site.total_area", "value": 1000, "unit": "m2"}]}
    assert json.loads(update(tmp_path, "submit", first, 0).stdout)["revision"] == 1
    before = (tmp_path / "project.json").read_bytes()
    assert json.loads(update(tmp_path, "submit", first, 0).stdout)["duplicate"]
    assert (tmp_path / "project.json").read_bytes() == before
    update(tmp_path, "submit", {"submission_id": "round2", "updates": [
        {"field_id": "site.total_area", "value": 1200, "unit": "m2"}]}, 1)
    project = read(tmp_path)
    assert project["values"]["site.total_area"]["status"] == "CONFLICT"
    chosen = next(cid for cid, record in project["candidates"].items()
                  if record["field_id"] == "site.total_area" and record["value"] == 1200)
    update(tmp_path, "resolve", {"submission_id": "resolve1", "field_id": "site.total_area", "candidate_id": chosen,
                               "reviewer": "SYNTHETIC-HUMAN", "reason": "SYNTHETIC checked choice"}, 2)
    assert read(tmp_path)["values"]["site.total_area"]["status"] == "UNVERIFIED"
    update(tmp_path, "review", {"submission_id": "review1", "field_id": "site.total_area", "reviewer": "SYNTHETIC-HUMAN",
                              "reason": "SYNTHETIC checked evidence", "license_status": "AUTHORIZED"}, 3)
    assert read(tmp_path)["values"]["site.total_area"]["status"] == "VERIFIED"
    update(tmp_path, "revise", {"submission_id": "correct", "reason": "SYNTHETIC correction", "updates": [
        {"field_id": "site.total_area", "value": 1300, "unit": "m2"}]}, 4)
    assert read(tmp_path)["values"]["site.total_area"]["value"] == 1300
    run_cli(tmp_path, "export", "--state", "project.json", "--output", "normalized.json")
    exported = read(tmp_path, "normalized.json")
    assert exported["normalized_inputs"]["site.total_area"] == 1300
    assert exported["calculation_status"] == "NOT_IMPLEMENTED"
    assert "results" not in exported
    update(tmp_path, "remove", {"submission_id": "remove1", "field_ids": ["site.total_area"], "reason": "SYNTHETIC retract"}, 5)
    assert "site.total_area" not in read(tmp_path)["values"]
    assert read(tmp_path)["revision"] == 6


def test_real_txt_parse_then_explicit_accept_is_not_review(tmp_path):
    new(tmp_path)
    original = (tmp_path / "project.json").read_bytes()
    (tmp_path / "SYNTHETIC.txt").write_text("项目名称：SYNTHETIC屋顶\n直流装机：1.25 MWp\n", encoding="utf-8")
    result = run_cli(tmp_path, "parse", "--attachment", "SYNTHETIC.txt", "--input-root", str(tmp_path), "--output", "parsed.json")
    summary = json.loads(result.stdout)
    assert summary["status"] == "PARSED" and summary["candidate_count"] == 2
    assert "SYNTHETIC" not in result.stdout
    assert (tmp_path / "project.json").read_bytes() == original
    parsed = read(tmp_path, "parsed.json")
    assert all(record["status"] == "UNVERIFIED" for record in parsed["candidates"])
    chosen = next(i for i, record in enumerate(parsed["candidates"]) if record["field_id"] == "system.dc_capacity")
    selection = {"submission_id": "accept1", "parsed_file": "parsed.json", "indices": [chosen]}
    update(tmp_path, "accept", selection, 0)
    assert json.loads(update(tmp_path, "accept", selection, 0).stdout)["duplicate"]
    project = read(tmp_path)
    assert project["values"]["system.dc_capacity"]["value"] == 1250
    assert project["values"]["system.dc_capacity"]["status"] == "UNVERIFIED"
    assert "project.name" not in project["values"]
    assert project["revision"] == 1


def test_parse_no_deterministic_candidates_is_nonzero_partial(tmp_path):
    (tmp_path / "SYNTHETIC.txt").write_text("SYNTHETIC ordinary prose without declared engineering data", encoding="utf-8")
    result = run_cli(tmp_path, "parse", "--attachment", "SYNTHETIC.txt", "--input-root", str(tmp_path), "--output", "parsed.json", expected=3)
    summary = json.loads(result.stdout)
    assert summary["status"] == "PARTIAL" and summary["candidate_count"] == 0
    assert read(tmp_path, "parsed.json")["candidates"] == []
    assert not (tmp_path / "project.json").exists()


@pytest.mark.parametrize("raw,code", [
    ('{"submission_id":"a","submission_id":"b","updates":[]}', "DUPLICATE_JSON_KEY"),
    ('{"submission_id":"a","updates":[NaN]}', "NON_FINITE_NUMBER"),
    ('{"submission_id":"a","updates":[Infinity]}', "NON_FINITE_NUMBER"),
    ('SYNTHETIC_PRIVATE_CANARY_INVALID', "INVALID_JSON"),
], ids=["duplicate-key", "nan", "infinity", "invalid"])
def test_strict_packet_json_errors_preserve_state(tmp_path, raw, code):
    new(tmp_path)
    original = (tmp_path / "project.json").read_bytes()
    (tmp_path / "bad.json").write_text(raw, encoding="utf-8")
    result = error(tmp_path, "submit", "--state", "project.json", "--input", "bad.json", "--expected-revision", 0, code=code)
    assert result["field_id"] is None
    assert (tmp_path / "project.json").read_bytes() == original
    assert not list(tmp_path.glob("*.lock"))


def test_decimal_roundtrip_uses_exact_numeric_tokens_not_float(tmp_path):
    new(tmp_path)
    (tmp_path / "exact.json").write_text('{"submission_id":"exact","updates":[{"field_id":"site.total_area","value":1234.123456789012345678901,"unit":"m2"}]}', encoding="utf-8")
    run_cli(tmp_path, "submit", "--state", "project.json", "--input", "exact.json", "--expected-revision", 0)
    assert '1234.123456789012345678901' in (tmp_path / "project.json").read_text(encoding="utf-8")


@pytest.mark.parametrize("command,extra,code", [
    ("submit", {"updates": [{"field_id": "site.total_area", "value": 1}]}, "UNIT_REQUIRED"),
    ("revise", {"updates": [{"field_id": "site.total_area", "value": 1, "unit": "m2"}], "reason": ""}, "CHANGE_REASON_REQUIRED"),
    ("review", {"field_id": "project.pv_type", "reviewer": "SYNTHETIC", "reason": "SYNTHETIC", "license_status": "UNKNOWN"}, "REVIEW_EVIDENCE_REQUIRED"),
    ("submit", {"updates": [], "unexpected": "SYNTHETIC"}, "INVALID_COMMAND_PACKET"),
    ("submit", {"updates": [], "action": "review"}, "INVALID_COMMAND_PACKET"),
    ("accept", {"parsed_file": 123, "indices": [0]}, "INVALID_COMMAND_PACKET"),
], ids=["unit", "revision-reason", "review-evidence", "unknown-key", "action-mismatch", "bad-path-type"])
def test_command_error_contract_and_atomic_rejection(tmp_path, command, extra, code):
    new(tmp_path)
    original = (tmp_path / "project.json").read_bytes()
    path = packet(tmp_path, {"submission_id": "invalid", **extra})
    detail = error(tmp_path, command, "--state", "project.json", "--input", path, "--expected-revision", 0, code=code)
    if code == "UNIT_REQUIRED":
        assert detail["field_id"] == "site.total_area"
    assert (tmp_path / "project.json").read_bytes() == original
    assert not list(tmp_path.glob("*.lock")) and not list(tmp_path.glob(".solar-pv-*.tmp"))


def test_revision_conflict_and_submission_id_reuse_do_not_write(tmp_path):
    new(tmp_path)
    first = {"submission_id": "first", "updates": [{"field_id": "project.name", "value": "SYNTHETIC_PRIVATE_CANARY"}]}
    update(tmp_path, "submit", first, 0)
    original = (tmp_path / "project.json").read_bytes()
    for data, revision, code in [
        ({"submission_id": "stale", "updates": first["updates"]}, 0, "REVISION_CONFLICT"),
        ({"submission_id": "first", "updates": [{"field_id": "project.name", "value": "OTHER"}]}, 1, "SUBMISSION_ID_REUSED"),
    ]:
        path = packet(tmp_path, data)
        result = error(tmp_path, "submit", "--state", "project.json", "--input", path, "--expected-revision", revision, code=code)
        assert result["field_id"] is None
        assert (tmp_path / "project.json").read_bytes() == original
    assert "SYNTHETIC_PRIVATE_CANARY" not in run_cli(tmp_path, "status", "--state", "project.json").stdout


@pytest.mark.parametrize("path,code", [
    ("../project.json", "PATH_TRAVERSAL"),
    ("nested/../project.json", "PATH_TRAVERSAL"),
    (".env", "JSON_PATH_REQUIRED"),
    ("project.txt", "JSON_PATH_REQUIRED"),
    ("stream.json:secret", "INVALID_LOCAL_PATH"),
    ("NUL.json", "INVALID_LOCAL_PATH"),
    ("missing/project.json", "PARENT_DIRECTORY_REQUIRED"),
], ids=["parent", "embedded-parent", "env", "suffix", "ads", "reserved", "parent-missing"])
def test_state_path_boundary(tmp_path, path, code):
    (tmp_path / ".env").write_text("SYNTHETIC_PRIVATE_CANARY", encoding="utf-8")
    result = run_cli(tmp_path, "status", "--state", path, expected=2)
    assert json.loads(result.stderr)["error"]["code"] == code
    assert "SYNTHETIC_PRIVATE_CANARY" not in result.stderr


def test_workspace_must_exist_and_absolute_outside_paths_are_rejected(tmp_path):
    error(tmp_path, "--workspace", str(tmp_path / "missing"), "status", "--state", "project.json", code="WORKSPACE_REQUIRED")
    error(tmp_path, "status", "--state", str(tmp_path.parent / "outside.json"), code="PATH_OUTSIDE_WORKSPACE")
    error(tmp_path, "status", "--state", "missing.json", code="FILE_NOT_FOUND")


@pytest.mark.parametrize("kind", ["state", "packet", "parsed-file", "export", "parse-output"])
def test_all_json_roles_are_confined_to_workspace(tmp_path, kind):
    new(tmp_path)
    if kind == "state":
        args = ["status", "--state", "../outside.json"]
    elif kind == "packet":
        args = ["submit", "--state", "project.json", "--input", "../outside.json", "--expected-revision", 0]
    elif kind == "parsed-file":
        selection = packet(tmp_path, {"submission_id": "accept", "parsed_file": "../outside.json", "indices": [0]})
        args = ["accept", "--state", "project.json", "--input", selection, "--expected-revision", 0]
    elif kind == "export":
        args = ["export", "--state", "project.json", "--output", "../outside.json"]
    else:
        args = ["parse", "--attachment", "not-read.txt", "--input-root", str(tmp_path), "--output", "../outside.json"]
    error(tmp_path, *args, code="PATH_TRAVERSAL")
    assert read(tmp_path)["revision"] == 0


def test_no_overwrite_new_export_and_parse(tmp_path):
    new(tmp_path)
    original = (tmp_path / "project.json").read_bytes()
    error(tmp_path, "new", "--project-id", "OTHER", "--pv-type", "industrial_rooftop", "--state", "project.json", code="OUTPUT_EXISTS")
    packet(tmp_path, {"SYNTHETIC": "existing"}, "output.json")
    existing = (tmp_path / "output.json").read_bytes()
    error(tmp_path, "export", "--state", "project.json", "--output", "output.json", code="OUTPUT_EXISTS")
    error(tmp_path, "parse", "--attachment", "not-read.txt", "--input-root", str(tmp_path), "--output", "output.json", code="OUTPUT_EXISTS")
    assert (tmp_path / "output.json").read_bytes() == existing
    assert (tmp_path / "project.json").read_bytes() == original


def test_future_schema_rejected_instead_of_migrated(tmp_path):
    new(tmp_path)
    project = read(tmp_path)
    project["schema_version"] = "solar-pv-project/999.0.0"
    packet(tmp_path, project, "future.json")
    result = run_cli(tmp_path, "status", "--state", "future.json", expected=2)
    assert json.loads(result.stderr)["error"]["code"] == "SCHEMA_VALIDATION_FAILED"
    assert "SYNTHETIC" not in result.stderr


def test_hardlink_json_and_nonregular_file_are_rejected(tmp_path):
    new(tmp_path)
    os.link(tmp_path / "project.json", tmp_path / "linked.json")
    error(tmp_path, "status", "--state", "linked.json", code="HARDLINK_FILE")
    error(tmp_path, "status", "--state", "project.json", code="HARDLINK_FILE")
    (tmp_path / "directory.json").mkdir()
    error(tmp_path, "status", "--state", "directory.json", code="NOT_REGULAR_FILE")


def test_oversize_json_rejected_before_decoding(tmp_path):
    from wangbin_solar_pv.serialization import MAX_JSON_BYTES
    with (tmp_path / "large.json").open("wb") as stream:
        stream.truncate(MAX_JSON_BYTES + 1)
    error(tmp_path, "status", "--state", "large.json", code="JSON_SIZE_LIMIT")


def test_existing_exclusive_lock_is_not_removed_or_overwritten(tmp_path):
    new(tmp_path)
    original = (tmp_path / "project.json").read_bytes()
    (tmp_path / "project.json.lock").write_text("SYNTHETIC-other-owner", encoding="utf-8")
    data = packet(tmp_path, {"submission_id": "one", "updates": [{"field_id": "project.name", "value": "SYNTHETIC"}]})
    error(tmp_path, "submit", "--state", "project.json", "--input", data, "--expected-revision", 0, code="STATE_LOCKED")
    assert (tmp_path / "project.json.lock").read_text(encoding="utf-8") == "SYNTHETIC-other-owner"
    assert (tmp_path / "project.json").read_bytes() == original


def test_digest_check_rejects_noncooperating_state_change_and_cleans_temp(tmp_path):
    from wangbin_solar_pv.errors import ContractError
    from wangbin_solar_pv.local_files import Workspace
    workspace = Workspace(tmp_path)
    workspace.create("project.json", {"SYNTHETIC": 1})
    _, old_digest = workspace.read("project.json")
    with workspace.lock("project.json"):
        (tmp_path / "project.json").write_text('{"SYNTHETIC":2}', encoding="utf-8")
        with pytest.raises(ContractError, match="STATE_CHANGED"):
            workspace.replace("project.json", {"SYNTHETIC": 3}, old_digest)
    assert read(tmp_path) == {"SYNTHETIC": 2}
    assert not list(tmp_path.glob(".solar-pv-*.tmp")) and not list(tmp_path.glob("*.lock"))


def test_lock_cleanup_never_deletes_other_owner_replacement(tmp_path):
    from wangbin_solar_pv.local_files import Workspace
    workspace = Workspace(tmp_path)
    replacement = tmp_path / "other.lock"
    with workspace.lock("project.json"):
        replacement.write_text("SYNTHETIC-other-owner", encoding="utf-8")
        os.replace(replacement, tmp_path / "project.json.lock")
    assert (tmp_path / "project.json.lock").read_text(encoding="utf-8") == "SYNTHETIC-other-owner"


def test_concurrent_same_revision_only_one_writer_commits(tmp_path):
    new(tmp_path)
    env = dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    processes = []
    for name in ("one", "two"):
        path = packet(tmp_path, {"submission_id": name, "updates": [{"field_id": "project.name", "value": "SYNTHETIC-" + name}]}, name + ".json")
        processes.append(subprocess.Popen([sys.executable, str(ENTRY), "--workspace", str(tmp_path), "submit", "--state", "project.json",
                                           "--input", path, "--expected-revision", "0"], cwd=tmp_path, env=env,
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8"))
    outputs = [process.communicate(timeout=60) for process in processes]
    assert sorted(process.returncode for process in processes) == [0, 2]
    loser = next(output for process, output in zip(processes, outputs) if process.returncode == 2)
    assert json.loads(loser[1])["error"]["code"] in {"STATE_LOCKED", "REVISION_CONFLICT"}
    assert read(tmp_path)["revision"] == 1 and len(read(tmp_path)["submission_ids"]) == 1
    assert not list(tmp_path.glob("*.lock")) and not list(tmp_path.glob(".solar-pv-*.tmp"))


def test_source_entry_module_entry_and_help_are_cwd_independent(tmp_path):
    env = dict(os.environ, PYTHONPATH=str(SOURCE), PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run([sys.executable, "-m", "wangbin_solar_pv", "--help"], cwd=tmp_path, env=env,
                            capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert result.returncode == 0
    assert "--workspace" in result.stdout and "--baseline-dir" in result.stdout
    assert "不计算、不联网" in result.stdout
    help_result = run_cli(tmp_path, "accept", "--help")
    assert "parsed_file" in help_result.stdout and "indices" in help_result.stdout
    assert "KNOWN_LIMIT" in result.stdout and "沙箱" in result.stdout


@pytest.mark.parametrize("role", ["file", "ancestor", "workspace"])
def test_real_symlinks_are_rejected_in_all_path_positions(tmp_path, role):
    real = tmp_path / "real"
    real.mkdir()
    new(real)
    link = tmp_path / ("link.json" if role == "file" else "link")
    try:
        link.symlink_to(real / "project.json" if role == "file" else real, target_is_directory=role != "file")
    except OSError as exc:
        pytest.skip(f"Windows symlink privilege unavailable: {exc.errno}")
    try:
        if role == "workspace":
            error(tmp_path, "--workspace", str(link), "status", "--state", "project.json", code="UNSAFE_LINK")
        else:
            error(tmp_path, "status", "--state", "link.json" if role == "file" else "link/project.json", code="UNSAFE_LINK")
    finally:
        link.unlink()


@pytest.mark.skipif(os.name != "nt", reason="Windows reparse/junction acceptance")
@pytest.mark.parametrize("role", ["ancestor", "workspace"])
def test_real_windows_junction_rejected_even_inside_authorized_root(tmp_path, role):
    real = tmp_path / "real"
    real.mkdir()
    new(real)
    junction = tmp_path / "junction"
    result = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(real)], capture_output=True, timeout=30)
    assert result.returncode == 0, "SYNTHETIC junction fixture could not be created"
    try:
        if role == "workspace":
            error(tmp_path, "--workspace", str(junction), "status", "--state", "project.json", code="UNSAFE_LINK")
        else:
            error(tmp_path, "status", "--state", "junction/project.json", code="UNSAFE_LINK")
    finally:
        os.rmdir(junction)


@pytest.mark.skipif(os.name != "nt", reason="Real Windows sharing-violation failure, no mock")
def test_actual_replace_failure_preserves_original_state_and_cleans_files(tmp_path):
    import ctypes
    from ctypes import wintypes
    new(tmp_path)
    before = (tmp_path / "project.json").read_bytes()
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                       wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    # Permit reads/writes but deny delete/rename, leaving JSON reads functional.
    handle = create(str(tmp_path / "project.json"), 0x80000000, 0x3, None, 3, 0x80, None)
    assert handle != ctypes.c_void_p(-1).value
    try:
        data = packet(tmp_path, {"submission_id": "blocked", "updates": [{"field_id": "project.name", "value": "SYNTHETIC"}]})
        error(tmp_path, "submit", "--state", "project.json", "--input", data, "--expected-revision", 0, code="LOCAL_PERMISSION_DENIED")
    finally:
        assert close(handle)
    assert (tmp_path / "project.json").read_bytes() == before
    assert not list(tmp_path.glob("*.lock")) and not list(tmp_path.glob(".solar-pv-*.tmp"))


def test_arbitrary_unknown_field_is_not_echoed_as_public_error_field_id(tmp_path):
    new(tmp_path)
    path = packet(tmp_path, {"submission_id": "resolve-invalid", "field_id": "synthetic_private_canary.secret",
                             "candidate_id": "absent", "reviewer": "SYNTHETIC", "reason": "SYNTHETIC"})
    result = run_cli(tmp_path, "resolve", "--state", "project.json", "--input", path, "--expected-revision", 0, expected=2)
    assert json.loads(result.stderr) == {"error": {"code": "INVALID_CONFLICT_CHOICE", "field_id": None}}
    assert "synthetic_private_canary" not in result.stderr


def test_parse_partial_candidates_can_be_selected_but_are_never_verified(tmp_path):
    new(tmp_path)
    (tmp_path / "SYNTHETIC.txt").write_text("项目名称：SYNTHETIC\nsite.total_area: 1000\n", encoding="utf-8")
    result = run_cli(tmp_path, "parse", "--attachment", "SYNTHETIC.txt", "--input-root", ".", "--output", "parsed.json", expected=3)
    assert json.loads(result.stdout)["status"] == "PARTIAL"
    update(tmp_path, "accept", {"submission_id": "partial", "parsed_file": "parsed.json", "indices": [0]}, 0)
    assert read(tmp_path)["values"]["project.name"]["status"] == "UNVERIFIED"
    assert "site.total_area" not in read(tmp_path)["values"]


def test_parse_blank_real_docx_reports_needs_ocr_not_recognition_success(tmp_path):
    from docx import Document
    Document().save(tmp_path / "SYNTHETIC.docx")
    result = run_cli(tmp_path, "parse", "--attachment", "SYNTHETIC.docx", "--input-root", ".", "--output", "parsed.json", expected=4)
    assert json.loads(result.stdout)["status"] == "NEEDS_OCR"
    assert read(tmp_path, "parsed.json")["candidates"] == []


def test_parse_blocked_attachment_does_not_log_original_or_absolute_path(tmp_path):
    (tmp_path / "SYNTHETIC.env").write_text("SYNTHETIC_PRIVATE_CANARY", encoding="utf-8")
    result = run_cli(tmp_path, "parse", "--attachment", "SYNTHETIC.env", "--input-root", ".", "--output", "parsed.json", expected=2)
    assert json.loads(result.stdout)["status"] == "BLOCKED"
    assert set(json.loads(result.stderr)["error"]) == {"code", "field_id"}
    assert "SYNTHETIC_PRIVATE_CANARY" not in result.stdout + result.stderr
    assert str(tmp_path) not in result.stdout + result.stderr


def test_retry_original_submission_after_later_revision_returns_current_status(tmp_path):
    new(tmp_path)
    first = {"submission_id": "first", "updates": [{"field_id": "site.total_area", "value": 1000, "unit": "m2"}]}
    update(tmp_path, "submit", first, 0)
    update(tmp_path, "submit", {"submission_id": "later", "updates": [{"field_id": "project.name", "value": "SYNTHETIC"}]}, 1)
    before = (tmp_path / "project.json").read_bytes()
    result = json.loads(update(tmp_path, "submit", first, 0).stdout)
    assert result["duplicate"] and result["revision"] == 2
    assert (tmp_path / "project.json").read_bytes() == before


def test_argument_errors_do_not_echo_private_argument_or_path(tmp_path):
    result = run_cli(tmp_path, "synthetic_private_canary", expected=2)
    assert json.loads(result.stderr) == {"error": {"code": "CLI_ARGUMENT_ERROR", "field_id": None}}
    assert "synthetic_private_canary" not in result.stderr
