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
from tooling.phase5_expert_packager import build, validate_source, NAME, _historical_blob

ROOT = Path(__file__).resolve().parents[4]
SOURCE = Path(__file__).resolve().parents[1]
SOURCE_REL = f"packages/experts/{NAME}"
# Immutable fifth-batch delivery identity, not HEAD or a version inferred from
# the production packager. Test-only changes must not change these nine blobs.
SEALED_COMMIT = "e376395df4e09267ef494f4e421fc49d4fbdb6dd"
HISTORICAL_DELIVERY = "bb603c8a8d55cd6795f51efabfd5436db0606896"
SEALED_SHA256 = "d42eaa2090eb07660cbb6f712ae506a2f731e5fd62035d5ccd58fec0f236bd47"
SEALED_MANIFEST_SHA256 = "59a7f5001637a0ba1d3537e7aa3c61d9e891d26f0ea557e31a8badb9e672c318"
SEALED_SIDECAR_SHA256 = "95407556349acc880f29cb7ee6f0992730e0d4c7799ac689eea9e400992cd1dd"
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
    return _historical_blob(repo, commit, f"{SOURCE_REL}/{rel}")


@pytest.fixture
def canonical_candidate():
    repo = Path(os.environ.get("WANGBIN_CONSULTANT_TEST_SOURCE_REPO", ROOT)).resolve(strict=True)
    active = product_factory.get_product(ROOT, NAME)["active_version"]
    baseline = HISTORICAL_DELIVERY if active in ("1.2.1", "1.2.2") else os.environ.get("WANGBIN_CONSULTANT_TEST_SOURCE_COMMIT", SEALED_COMMIT)
    expected = {}
    for rel in MEMBERS:
        sealed = _git_blob(repo, SEALED_COMMIT, rel)
        assert _git_blob(repo, baseline, rel) == sealed, rel
        expected[f"{NAME}/{rel}"] = sealed
    return repo, expected


def test_current_snapshot_matches_sealed_bytes(canonical_candidate):
    # A current-source mismatch fails this separate gate, not the independent
    # historical reconstruction or original-candidate runtime evidence.
    repo, expected = canonical_candidate
    active = product_factory.get_product(ROOT, NAME)["active_version"]
    for rel in MEMBERS:
        checkout = _git_blob(repo, HISTORICAL_DELIVERY, rel) if active in ("1.2.1", "1.2.2") else (SOURCE / rel).read_bytes()
        if rel != "avatars/expert.png":
            checkout = checkout.replace(bytes((13, 10)), bytes((10,)))
        assert checkout == expected[f"{NAME}/{rel}"], rel


def _materialize(root, expected):
    for member, data in expected.items():
        rel = member.removeprefix(NAME + "/")
        path = root / SOURCE_REL / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def _assert_archive(root, expected, expected_sha256, version="1.2.0"):
    candidate_name = f"{NAME}-{version}-expert-candidate.zip"
    archive = root / "dist" / candidate_name
    sidecar = archive.with_name(archive.name + ".sha256")
    manifest = archive.with_name(archive.name + ".manifest.json")
    raw = archive.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == expected_sha256
    assert sidecar.read_bytes() == f"{expected_sha256}  {archive.name}\n".encode("ascii")
    data = json.loads(manifest.read_bytes())
    assert data["id"] == NAME and data["version"] == version
    assert data["source"] == SOURCE_REL and data["archive"] == f"dist/{candidate_name}"
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

def test_original_candidate_identity_and_runtime(tmp_path, canonical_candidate):
    repo, expected = canonical_candidate
    candidate_root = Path(os.environ.get("WANGBIN_CONSULTANT_TEST_CANDIDATE_ROOT", repo))
    sealed_archive, sealed_manifest, sealed_existing = _assert_archive(candidate_root, expected, SEALED_SHA256)
    manifest_path = sealed_archive.with_name(sealed_archive.name + ".manifest.json")
    sidecar_path = sealed_archive.with_name(sealed_archive.name + ".sha256")
    assert hashlib.sha256(sealed_existing[manifest_path]).hexdigest() == SEALED_MANIFEST_SHA256
    assert hashlib.sha256(sealed_existing[sidecar_path]).hexdigest() == SEALED_SIDECAR_SHA256
    assert sealed_manifest["source_commit"] == SEALED_COMMIT
    assert sealed_manifest["source_byte_basis"] == "verified_git_blob_bytes"
    assert sealed_manifest["workbuddy_install"] == sealed_manifest["workbuddy_dialogue"] == "NOT_TESTED"
    _assert_candidate_runtime(tmp_path, sealed_archive, expected)
    assert all(path.read_bytes() == data for path, data in sealed_existing.items())


def test_original_catalog_identity():
    catalog = product_factory.get_product(ROOT, NAME)
    repo = Path(os.environ.get("WANGBIN_CONSULTANT_TEST_SOURCE_REPO", ROOT)).resolve(strict=True)
    historical = json.loads(_historical_blob(repo, HISTORICAL_DELIVERY, "products/catalog.json"))
    old = next(p for p in historical["products"] if p["id"] == NAME)
    assert old["active_version"] == "1.2.0"
    registered = next(v for v in catalog["versions"] if v["version"] == "1.2.0")
    assert registered["sha256"] == SEALED_SHA256 and registered["candidate"] == f"dist/{CANDIDATE_NAME}"
    assert registered == next(v for v in old["versions"] if v["version"] == "1.2.0")


def test_archive_is_deterministic_and_binds_formal_bytes(tmp_path, canonical_candidate):
    repo, expected = canonical_candidate
    dedicated = tmp_path / "dedicated"
    generic = tmp_path / "generic"
    _materialize(dedicated, expected)
    _materialize(generic, expected)
    (generic / "products").mkdir()
    (generic / "products/catalog.json").write_bytes(_historical_blob(repo, HISTORICAL_DELIVERY, "products/catalog.json"))
    assert not (dedicated / "dist").exists() and not (generic / "dist").exists()

    # Compression may differ from the historical archive; both new archives
    # must independently match the sealed blobs and each other's bytes.
    first = build(dedicated, source_repo=repo, source_commit=SEALED_COMMIT, version="1.2.0")
    archive, manifest, existing = _assert_archive(dedicated, expected, first["sha256"])
    assert first["source_commit"] == manifest["source_commit"] == SEALED_COMMIT
    assert manifest["source_byte_basis"] == "verified_git_blob_bytes"
    assert manifest["workbuddy_install"] == manifest["workbuddy_dialogue"] == "NOT_TESTED"
    assert first["checkout_crlf_normalized_members"] == []
    assert first["members"] == manifest["members"]
    with pytest.raises(FileExistsError, match="already exists"):
        build(dedicated, source_repo=repo, source_commit=SEALED_COMMIT, version="1.2.0")
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


def test_rebuilt_candidate_runtime(tmp_path, canonical_candidate):
    repo, expected = canonical_candidate
    dedicated = tmp_path / "dedicated"
    _materialize(dedicated, expected)
    assert not (dedicated / "dist").exists()
    built = build(dedicated, source_repo=repo, source_commit=SEALED_COMMIT, version="1.2.0")
    archive, manifest, existing = _assert_archive(dedicated, expected, built["sha256"])
    assert manifest["source_commit"] == SEALED_COMMIT
    _assert_candidate_runtime(tmp_path, archive, expected)
    assert all(path.read_bytes() == data for path, data in existing.items())


def _assert_candidate_runtime(tmp_path, archive, expected):

    prompt = expected[f"{NAME}/agents/{NAME}.md"].decode("utf-8")
    for rule in ("回执缺失", "input_sha256", "未作确定性工具验证",
                 "来源真实性、授权、估时合理性、业务完整性、复用、分摊、排期可行性与平台安装不由脚本认证",
                 "正式主机加载及调用须真实平台回执", "用户有效固定价/逐角色固定或区间价优先"):
        assert rule in prompt

    # Actual package entry, not a checkout script or model claim. The nine
    # members above exclude the experimental verifier and all test fixtures.
    extracted = tmp_path / "extracted"
    with zipfile.ZipFile(archive) as zipped:
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
    assert result2["script_sha256"] == hashlib.sha256(expected[f"{NAME}/{SCRIPT}"]).hexdigest()
    assert set(result2["results"]) == {"fiction"}
    scope = result2["results"]["fiction"]
    assert scope["B"]["low"]["value"] == "2" and scope["B"]["high"]["value"] == "4"
    assert scope["E"]["low"]["value"] == "2.2" and scope["E"]["high"]["value"] == "4.8"
    assert all(scope["labor"][s]["value"] is None for s in ("low", "high"))


def test_package_rejects_uncommitted_member_bytes(tmp_path, canonical_candidate):
    repo, expected = canonical_candidate
    _materialize(tmp_path, expected)
    readme = tmp_path / SOURCE_REL / "README.md"
    readme.write_bytes(readme.read_bytes() + b"Fictional review note.")
    with pytest.raises(ValueError, match="source differs from committed blob"):
        build(tmp_path, source_repo=repo, source_commit=SEALED_COMMIT, version="1.2.0")
    assert not (tmp_path / "dist").exists()


def _registered_candidate(version):
    repo = Path(os.environ.get("WANGBIN_CONSULTANT_TEST_SOURCE_REPO", ROOT)).resolve(strict=True)
    catalog = product_factory.get_product(ROOT, NAME)
    assert catalog["active_version"] in ("1.2.1", "1.2.2")
    if version == "1.2.1" and catalog["active_version"] == "1.2.2":
        historical = json.loads(_historical_blob(repo, "977358c17c1e38ff35a7a1357cecf6b15805a70c", "products/catalog.json"))
        prior = next(p for p in historical["products"] if p["id"] == NAME)
        entry = next(v for v in prior["versions"] if v["version"] == version)
        assert entry == next(v for v in catalog["versions"] if v["version"] == version)
        assert entry["source_commit"] == "7d58e65c80f603c4cdf295a6f2722d48a903568a"
    else:
        assert catalog["active_version"] == version
        entry = next(v for v in catalog["versions"] if v["version"] == version)
    commit = entry["source_commit"]
    expected = {f"{NAME}/{rel}": _git_blob(repo, commit, rel) for rel in MEMBERS}
    assert json.loads(expected[f"{NAME}/.codebuddy-plugin/plugin.json"])["version"] == version
    return repo, entry, expected


def _snapshot_matches_registered_seal(current_candidate):
    repo, entry, expected = current_candidate
    version = entry["version"]
    active = product_factory.get_product(ROOT, NAME)["active_version"]
    prior_commit = "7d58e65c80f603c4cdf295a6f2722d48a903568a" if version == "1.2.2" else SEALED_COMMIT
    for rel in MEMBERS:
        checkout = (_git_blob(repo, "977358c17c1e38ff35a7a1357cecf6b15805a70c", rel)
                    if active != version else (SOURCE / rel).read_bytes())
        if rel != "avatars/expert.png":
            checkout = checkout.replace(bytes((13, 10)), bytes((10,)))
        assert checkout == expected[f"{NAME}/{rel}"], rel
        if rel not in (".codebuddy-plugin/plugin.json", f"agents/{NAME}.md", "README.md"):
            assert checkout == _git_blob(repo, prior_commit, rel), rel


def _archive_is_deterministic(tmp_path, current_candidate):
    repo, entry, expected = current_candidate
    dedicated, generic = tmp_path / "dedicated", tmp_path / "generic"
    for target in (dedicated, generic):
        _materialize(target, expected)
        assert not (target / "dist").exists()
    (generic / "products").mkdir()
    if entry["version"] == "1.2.1" and product_factory.get_product(ROOT, NAME)["active_version"] == "1.2.2":
        (generic / "products/catalog.json").write_bytes(_historical_blob(repo, "977358c17c1e38ff35a7a1357cecf6b15805a70c", "products/catalog.json"))
    else:
        shutil.copyfile(ROOT / "products/catalog.json", generic / "products/catalog.json")
    first = build(dedicated, source_repo=repo, source_commit=entry["source_commit"], version=entry["version"])
    archive, manifest, existing = _assert_archive(dedicated, expected, first["sha256"], entry["version"])
    assert first["source_commit"] == manifest["source_commit"] == entry["source_commit"]
    assert manifest["source_byte_basis"] == "verified_git_blob_bytes"
    assert manifest["workbuddy_install"] == manifest["workbuddy_dialogue"] == "NOT_TESTED"
    assert first["checkout_crlf_normalized_members"] == []
    assert first["members"] == manifest["members"]
    with pytest.raises(FileExistsError, match="already exists"):
        build(dedicated, source_repo=repo, source_commit=entry["source_commit"], version=entry["version"])
    assert all(path.read_bytes() == data for path, data in existing.items())
    second = product_factory.package_product(generic, NAME)
    other, other_manifest, generic_existing = _assert_archive(generic, expected, first["sha256"], entry["version"])
    assert second["sha256"] == first["sha256"] and second["members"] == manifest["members"]
    assert other.read_bytes() == archive.read_bytes()
    assert product_factory.verify_package(generic, NAME)["status"] == "PASS"
    product_factory.package_product(generic, NAME)
    assert all(path.read_bytes() == data for path, data in generic_existing.items())
    assert "source_commit" not in other_manifest


def _rebuilt_runtime(tmp_path, current_candidate):
    repo, entry, expected = current_candidate
    dedicated = tmp_path / "dedicated"
    _materialize(dedicated, expected)
    assert not (dedicated / "dist").exists()
    built = build(dedicated, source_repo=repo, source_commit=entry["source_commit"], version=entry["version"])
    archive, manifest, existing = _assert_archive(dedicated, expected, built["sha256"], entry["version"])
    assert manifest["source_commit"] == entry["source_commit"]
    _assert_candidate_runtime(tmp_path, archive, expected)
    assert all(path.read_bytes() == data for path, data in existing.items())


def _original_runtime(tmp_path, current_candidate):
    repo, entry, expected = current_candidate
    root = Path(os.environ.get("WANGBIN_CONSULTANT_TEST_CANDIDATE_ROOT", repo))
    archive, manifest, existing = _assert_archive(root, expected, entry["sha256"], entry["version"])
    assert entry["archive_evidence"] == entry["candidate"] == f"dist/{archive.name}"
    assert manifest["source_commit"] == entry["source_commit"]
    assert manifest["source_byte_basis"] == "verified_git_blob_bytes"
    assert manifest["workbuddy_install"] == manifest["workbuddy_dialogue"] == "NOT_TESTED"
    if entry["version"] == "1.2.1":
        assert entry["sha256"] == "27294e72c36a345af178fff0a9c4f224778f7f1588e6e96ec6a4e14ae0a9a926"
        assert hashlib.sha256(existing[archive.with_name(archive.name + ".manifest.json")]).hexdigest() == "d73d4e16ed15b95e406b04d8689ddd20284a20a52ddd4a79f64f080aadd788bd"
        assert hashlib.sha256(existing[archive.with_name(archive.name + ".sha256")]).hexdigest() == "3345fbab71330987e1abd72615072368b4e2629d0650284e503ce78a33f59f96"
    _assert_candidate_runtime(tmp_path, archive, expected)
    assert all(path.read_bytes() == data for path, data in existing.items())


def _rejects_uncommitted_bytes(tmp_path, current_candidate):
    repo, entry, expected = current_candidate
    _materialize(tmp_path, expected)
    readme = tmp_path / SOURCE_REL / "README.md"
    readme.write_bytes(readme.read_bytes() + b"Fictional review note.")
    with pytest.raises(ValueError, match="source differs from committed blob"):
        build(tmp_path, source_repo=repo, source_commit=entry["source_commit"], version=entry["version"])
    assert not (tmp_path / "dist").exists()


@pytest.fixture
def candidate_121():
    return _registered_candidate("1.2.1")


def test_current_121_snapshot_matches_registered_seal(candidate_121):
    _snapshot_matches_registered_seal(candidate_121)


def test_current_121_archive_is_deterministic(tmp_path, candidate_121):
    _archive_is_deterministic(tmp_path, candidate_121)


def test_current_121_rebuilt_runtime(tmp_path, candidate_121):
    _rebuilt_runtime(tmp_path, candidate_121)


def test_current_121_original_runtime(tmp_path, candidate_121):
    _original_runtime(tmp_path, candidate_121)


def test_current_121_rejects_uncommitted_bytes(tmp_path, candidate_121):
    _rejects_uncommitted_bytes(tmp_path, candidate_121)


@pytest.fixture
def candidate_122():
    return _registered_candidate("1.2.2")


def test_current_122_snapshot_matches_registered_seal(candidate_122):
    _snapshot_matches_registered_seal(candidate_122)


def test_current_122_archive_is_deterministic(tmp_path, candidate_122):
    _archive_is_deterministic(tmp_path, candidate_122)


def test_current_122_rebuilt_runtime(tmp_path, candidate_122):
    _rebuilt_runtime(tmp_path, candidate_122)


def test_current_122_original_runtime(tmp_path, candidate_122):
    _original_runtime(tmp_path, candidate_122)


def test_current_122_rejects_uncommitted_bytes(tmp_path, candidate_122):
    _rejects_uncommitted_bytes(tmp_path, candidate_122)


def test_candidate_source_version_mismatch(tmp_path):
    _copy_members(tmp_path / NAME)
    config = tmp_path / NAME / ".codebuddy-plugin/plugin.json"
    meta = json.loads(config.read_bytes())
    meta["version"] = "1.1.2"
    config.write_text(json.dumps(meta), encoding="utf-8")
    with pytest.raises(ValueError, match="identity, version or type mismatched"):
        validate_source(tmp_path / NAME)


def test_candidate_explicit_version_is_strict(tmp_path):
    copy = tmp_path / NAME
    _copy_members(copy)
    active = product_factory.get_product(ROOT, NAME)["active_version"]
    assert validate_source(copy)["version"] == active == "1.2.2"
    for previous in ("1.2.0", "1.2.1"):
        with pytest.raises(ValueError, match="identity, version or type mismatched"):
            validate_source(copy, version=previous)
    with pytest.raises(ValueError, match="unsupported"):
        validate_source(copy, version="1.2.3")


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
