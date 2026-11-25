"""Bundled assets/permissions and deterministic archive, not native host QA."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
from tooling import product_factory
from tooling.phase5_expert_packager import build, validate_source, NAME

ROOT = Path(__file__).resolve().parents[4]
SOURCE = Path(__file__).resolve().parents[1]
SOURCE_REL = f"packages/experts/{NAME}"
# Immutable fifth-batch delivery identity, not HEAD or a version inferred from
# the production packager. Test-only changes must not change these nine blobs.
SEALED_COMMIT = "e376395df4e09267ef494f4e421fc49d4fbdb6dd"
SEALED_SHA256 = "d42eaa2090eb07660cbb6f712ae506a2f731e5fd62035d5ccd58fec0f236bd47"
CANDIDATE_NAME = f"{NAME}-1.2.0-expert-candidate.zip"
SCRIPT = "skills/wangbin-estimate-calculator/scripts/estimator.py"
MEMBERS = (
    ".codebuddy-plugin/plugin.json",
    f"agents/{NAME}.md",
    "avatars/expert.png",
    "README.md",
    "LICENSE",
    "skills/wangbin-estimate-calculator/SKILL.md",
    SCRIPT,
    "skills/wangbin-estimate-calculator/references/input-output-contract.md",
    "skills/wangbin-estimate-calculator/LICENSE",
)


def _copy_members(target):
    for rel in MEMBERS:
        path = target / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE / rel, path)


def _git_blob(repo, commit, rel):
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}
    run = subprocess.run(
        ["git", "--no-replace-objects", "-c", "core.longpaths=true", "show", f"{commit}:{SOURCE_REL}/{rel}"],
        cwd=repo, env=env, capture_output=True,
    )
    assert run.returncode == 0, run.stderr
    return run.stdout


@pytest.fixture
def canonical_candidate():
    repo = Path(os.environ.get("WANGBIN_CONSULTANT_TEST_SOURCE_REPO", ROOT)).resolve(strict=True)
    baseline = os.environ.get("WANGBIN_CONSULTANT_TEST_SOURCE_COMMIT", SEALED_COMMIT)
    expected = {}
    for rel in MEMBERS:
        sealed = _git_blob(repo, SEALED_COMMIT, rel)
        assert _git_blob(repo, baseline, rel) == sealed, rel
        checkout = (SOURCE / rel).read_bytes()
        if rel != "avatars/expert.png":
            checkout = checkout.replace(bytes((13, 10)), bytes((10,)))
        assert checkout == sealed, rel
        expected[f"{NAME}/{rel}"] = sealed
    return repo, expected


def _materialize(root, expected):
    for member, data in expected.items():
        rel = member.removeprefix(NAME + "/")
        path = root / SOURCE_REL / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def _assert_archive(root, expected, expected_sha256):
    archive = root / "dist" / CANDIDATE_NAME
    sidecar = archive.with_name(archive.name + ".sha256")
    manifest = archive.with_name(archive.name + ".manifest.json")
    raw = archive.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected_sha256
    assert sidecar.read_bytes() == f"{expected_sha256}  {archive.name}\n".encode("ascii")
    data = json.loads(manifest.read_bytes())
    assert data["id"] == NAME and data["version"] == "1.2.0"
    assert data["source"] == SOURCE_REL and data["archive"] == f"dist/{CANDIDATE_NAME}"
    assert data["sha256"] == expected_sha256 and data["platform"] == "BLOCKED"
    assert data["scope"] == "local archive integrity only"
    rows = [{"path": name, "sha256": hashlib.sha256(payload).hexdigest(), "size": len(payload)}
            for name, payload in sorted(expected.items())]
    assert data["members"] == rows and len(rows) == 9
    member_index = (json.dumps({"members": rows}, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    assert data["payload_snapshot_sha256"] == hashlib.sha256(member_index).hexdigest()
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.testzip() is None
        assert zipped.namelist() == sorted(expected)
        for name, payload in expected.items():
            assert zipped.read(name) == payload, name
    return archive, data, {p: p.read_bytes() for p in (archive, sidecar, manifest)}

@pytest.mark.parametrize("field", ["tools", "runtime", "dependencies", "mcpServers"])
def test_custom_permissions_remain_forbidden(tmp_path, field):
    copy = tmp_path / NAME
    _copy_members(copy)
    path = copy / ".codebuddy-plugin/plugin.json"
    meta = json.loads(path.read_text(encoding="utf-8")); meta[field] = ["Bash"]
    path.write_text(json.dumps(meta), encoding="utf-8")
    with pytest.raises(ValueError, match="external"):
        validate_source(copy)

@pytest.mark.parametrize("value", [["../external"], ["./skills/other"], []])
def test_external_or_unbound_skill_rejected(tmp_path, value):
    copy = tmp_path / NAME
    _copy_members(copy)
    path = copy / ".codebuddy-plugin/plugin.json"
    meta = json.loads(path.read_text(encoding="utf-8")); meta["skills"] = value
    path.write_text(json.dumps(meta), encoding="utf-8")
    with pytest.raises(ValueError, match="skills"):
        validate_source(copy)

def test_archive_is_deterministic_and_binds_formal_bytes(tmp_path, canonical_candidate):
    repo, expected = canonical_candidate
    dedicated = tmp_path / "dedicated"
    generic = tmp_path / "generic"
    _materialize(dedicated, expected)
    _materialize(generic, expected)
    (generic / "products").mkdir()
    shutil.copyfile(ROOT / "products/catalog.json", generic / "products/catalog.json")
    assert not (dedicated / "dist").exists() and not (generic / "dist").exists()

    # The actual delivered archive is immutable. Compression output can differ
    # between the original 3.14 and the fixed 3.12 QA runtime even when every
    # member is identical; check the historical hash against the real artifact,
    # and require both independent builds here to have identical archive bytes.
    sealed_archive, sealed_manifest, sealed_existing = _assert_archive(repo, expected, SEALED_SHA256)
    assert sealed_manifest["source_commit"] == SEALED_COMMIT
    assert sealed_manifest["source_byte_basis"] == "verified_git_blob_bytes"
    assert sealed_manifest["workbuddy_install"] == sealed_manifest["workbuddy_dialogue"] == "NOT_TESTED"
    catalog = product_factory.get_product(generic, NAME)
    assert catalog["active_version"] == "1.2.0"
    registered = next(v for v in catalog["versions"] if v["version"] == "1.2.0")
    assert registered["sha256"] == SEALED_SHA256 and registered["candidate"] == f"dist/{CANDIDATE_NAME}"

    first = build(dedicated, source_repo=repo, source_commit=SEALED_COMMIT)
    archive, manifest, existing = _assert_archive(dedicated, expected, first["sha256"])
    assert first["source_commit"] == manifest["source_commit"] == SEALED_COMMIT
    assert manifest["source_byte_basis"] == "verified_git_blob_bytes"
    assert manifest["workbuddy_install"] == manifest["workbuddy_dialogue"] == "NOT_TESTED"
    assert first["checkout_crlf_normalized_members"] == []
    assert first["members"] == manifest["members"] == sealed_manifest["members"]
    assert manifest["payload_snapshot_sha256"] == sealed_manifest["payload_snapshot_sha256"]
    with pytest.raises(FileExistsError, match="already exists"):
        build(dedicated, source_repo=repo, source_commit=SEALED_COMMIT)
    assert all(path.read_bytes() == data for path, data in existing.items())

    # Independent factory entry, in a separate initially empty output root.
    second = product_factory.package_product(generic, NAME)
    other, other_manifest, generic_existing = _assert_archive(generic, expected, first["sha256"])
    assert second["sha256"] == first["sha256"] and second["members"] == manifest["members"]
    assert other.read_bytes() == archive.read_bytes()
    assert product_factory.verify_package(generic, NAME)["status"] == "PASS"
    # Generic entry permits an identical rerun, not a different artifact set.
    product_factory.package_product(generic, NAME)
    assert all(path.read_bytes() == data for path, data in generic_existing.items())
    assert "source_commit" not in other_manifest  # canonical proof above, not a generic manifest claim

    prompt = expected[f"{NAME}/agents/{NAME}.md"].decode("utf-8")
    for rule in ("回执缺失", "input_sha256", "未作确定性工具验证",
                 "来源真实性、授权、估时合理性、业务完整性、复用、分摊、排期可行性与平台安装不由脚本认证",
                 "正式主机加载及调用须真实平台回执", "用户有效固定价/逐角色固定或区间价优先"):
        assert rule in prompt

    # Actual package entry, not a checkout script or model claim. The nine
    # members above exclude the experimental verifier and all test fixtures.
    extracted = tmp_path / "extracted"
    with zipfile.ZipFile(sealed_archive) as zipped:
        zipped.extractall(extracted)
    script = extracted / NAME / SCRIPT
    assert script.read_bytes() == expected[f"{NAME}/{SCRIPT}"]
    source = tmp_path / "fictional-input.json"
    payload = (SOURCE / "experiments/decimal-poc/fixture_synthetic.json").read_bytes()
    source.write_bytes(payload)
    receipt = tmp_path / "fictional-receipt.json"
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    run = subprocess.run([sys.executable, "-I", "-B", str(script), str(source), "-o", str(receipt)],
                         cwd=extracted, env=env, capture_output=True)
    assert run.returncode == 0, run.stderr
    result = json.loads(receipt.read_bytes())
    assert result["input_sha256"] == hashlib.sha256(payload).hexdigest()
    assert result["script_sha256"] == hashlib.sha256(expected[f"{NAME}/{SCRIPT}"]).hexdigest()
    assert result["tiers"]["MVP"]["B"] == {"low": "7", "high": "12"}
    assert result["labor_is_complete_total"] is False
    assert all(tier["complete_project_total_rmb"] is None for tier in result["tiers"].values())

    # A separate minimal 2.0 scope request verifies that the actual candidate
    # exposes the new entry as well as its historical compatibility entry.
    def sourced(value):
        return {"status": "SYNTHETIC", "source": "SYNTHETIC: fictional package check", "value": value}

    request = {
        "schema_version": "2.0", "scope_version": "fiction-v2", "quote_version": "q1",
        "request": {"mode": "scope", "money": "none", "scope_id": "fiction", "package_ids": ["F1"]},
        "role_catalog": [{"id": "BA", "name": "Business analysis"}],
        "work_packages": [{"id": "F1", "function": "fictional planning", "source": "SYNTHETIC: fictional planning",
                           "scope_version": "fiction-v2", "assignments_complete": True,
                           "assignments": [{"id": "F1-BA", "role": "BA", "effort": {"low": sourced("2"), "high": sourced("4")}}]}],
        "coverage": {"fiction": {"work": "COMPLETE", "external": "NOT_APPLICABLE", "source": "SYNTHETIC: complete fictional scope"}},
        "buffers": {"default": {"low": sourced("0.1"), "high": sourced("0.2")}},
        "pricing": {"mode": "refused", "tax_basis": "UNKNOWN"}, "fees": [],
    }
    source2 = tmp_path / "fictional-v2-input.json"
    payload2 = json.dumps(request).encode("utf-8")
    source2.write_bytes(payload2)
    receipt2 = tmp_path / "fictional-v2-receipt.json"
    run2 = subprocess.run([sys.executable, "-I", "-B", str(script), str(source2), "-o", str(receipt2)],
                          cwd=extracted, env=env, capture_output=True)
    assert run2.returncode == 0, run2.stderr
    result2 = json.loads(receipt2.read_bytes())
    assert result2["schema_version"] == "2.0" and result2["request"] == request["request"]
    assert result2["input_sha256"] == hashlib.sha256(payload2).hexdigest()
    assert result2["script_sha256"] == result["script_sha256"]
    assert set(result2["results"]) == {"fiction"}
    scope = result2["results"]["fiction"]
    assert scope["B"]["low"]["value"] == "2" and scope["B"]["high"]["value"] == "4"
    assert scope["E"]["low"]["value"] == "2.2" and scope["E"]["high"]["value"] == "4.8"
    assert all(scope["labor"][s]["value"] is None for s in ("low", "high"))
    assert all(path.read_bytes() == data for path, data in sealed_existing.items())


def test_package_rejects_uncommitted_member_bytes(tmp_path, canonical_candidate):
    repo, expected = canonical_candidate
    _materialize(tmp_path, expected)
    readme = tmp_path / SOURCE_REL / "README.md"
    readme.write_bytes(readme.read_bytes() + b"Fictional review note.")
    with pytest.raises(ValueError, match="source differs from committed blob"):
        build(tmp_path, source_repo=repo, source_commit=SEALED_COMMIT)
    assert not (tmp_path / "dist").exists()


def test_candidate_source_version_mismatch(tmp_path):
    _copy_members(tmp_path / NAME)
    config = tmp_path / NAME / ".codebuddy-plugin/plugin.json"
    meta = json.loads(config.read_bytes())
    meta["version"] = "1.1.2"
    config.write_text(json.dumps(meta), encoding="utf-8")
    with pytest.raises(ValueError, match="identity, version or type mismatched"):
        validate_source(tmp_path / NAME)


def test_formal_script_receipt_bytes_and_rejected_input(tmp_path):
    import subprocess
    import sys
    script = SOURCE / "skills/wangbin-estimate-calculator/scripts/estimator.py"
    original = SOURCE / "experiments/decimal-poc/fixture_synthetic.json"
    source = tmp_path / "input.json"
    payload = original.read_bytes(); source.write_bytes(payload)
    receipt = tmp_path / "receipt.json"
    run = subprocess.run([sys.executable, "-B", str(script), str(source), "-o", str(receipt)], capture_output=True)
    assert run.returncode == 0, run.stderr
    data = receipt.read_bytes(); result = json.loads(data)
    assert result["input_sha256"] == hashlib.sha256(payload).hexdigest()
    assert result["script_sha256"] == hashlib.sha256(script.read_bytes()).hexdigest()
    assert result["labor_is_complete_total"] is False
    assert all(tier["complete_project_total_rmb"] is None for tier in result["tiers"].values())
    source.write_bytes(b"{broken")
    refused = tmp_path / "invalid-receipt.json"
    failed = subprocess.run([sys.executable, "-B", str(script), str(source), "-o", str(refused)], capture_output=True)
    assert failed.returncode == 2 and not refused.exists()
    # Existing evidence is never overwritten, even by a valid rerun.
    source.write_bytes(payload)
    duplicate = subprocess.run([sys.executable, "-B", str(script), str(source), "-o", str(receipt)], capture_output=True)
    assert duplicate.returncode == 2 and receipt.read_bytes() == data


def test_independent_qa_high_precision_counterexample(tmp_path):
    import subprocess
    import sys
    script = SOURCE / "skills/wangbin-estimate-calculator/scripts/estimator.py"
    source = SOURCE / "tests/fixtures/precision-boundary.input.json"
    receipt = tmp_path / "exact.json"
    run = subprocess.run([sys.executable, "-B", str(script), str(source), "-o", str(receipt)], capture_output=True)
    assert run.returncode == 0, run.stderr
    result = json.loads(receipt.read_bytes())
    assert result["tiers"]["MVP"]["B"]["low"] == "123456789012345678901234567893.4"
    assert result["tiers"]["MVP"]["B"]["high"] == "123456789012345678901234567893.4"


def test_precision_budget_rejects_without_receipt(tmp_path):
    import subprocess
    import sys
    script = SOURCE / "skills/wangbin-estimate-calculator/scripts/estimator.py"
    data = json.loads((SOURCE / "tests/fixtures/precision-boundary.input.json").read_bytes())
    data["work_packages"][0]["roles"]["FE"]["low"] = "1e-100001"
    source = tmp_path / "outside.json"; source.write_text(json.dumps(data), encoding="utf-8")
    receipt = tmp_path / "outside-receipt.json"
    run = subprocess.run([sys.executable, "-B", str(script), str(source), "-o", str(receipt)], capture_output=True)
    assert run.returncode == 2 and not receipt.exists()
    assert b"precision budget exceeded" in run.stderr
