"""Product factory operations are isolated and evidence is not platform approval."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest
import yaml

from tooling import product_factory as factory
from tooling.phase5_expert_packager import validate_source

ROOT = Path(__file__).resolve().parents[1]


def registry(root: Path, *, kind: str = "Skill", product_id: str = "sample-skill", source: bool = True) -> Path:
    (root / "products").mkdir(parents=True)
    folder = {"Skill": "skills", "Expert": "experts", "Connector": "connectors"}[kind]
    path = root / "packages" / folder / product_id
    data = {"schema_version": 1, "products": [{"id": product_id, "name": "Sample", "type": kind,
            "target_users": "test", "scenario": "test", "development": "UNKNOWN", "maintenance": "UNKNOWN",
            "status": "BACKLOG", "review_status": "NOT_TESTED", "review_evidence": "UNKNOWN",
            "versions": [{"version": "0.1.0", "source": str(path.relative_to(root)).replace('\\', '/'),
                          "candidate": "UNKNOWN", "sha256": "UNKNOWN", "date": "UNKNOWN"}]}]}
    (root / "products" / "catalog.json").write_text(json.dumps(data), encoding="utf-8")
    (root / "products" / "metrics.json").write_text(json.dumps({"schema_version": 1, "metrics": []}), encoding="utf-8")
    if source:
        path.mkdir(parents=True)
        if kind == "Skill":
            (path / "SKILL.md").write_text("---\nname: sample-skill\ndisplay_name: Sample\ndisplay_name_en: Sample\ndescription: Sample\ndescription_zh: Sample\ndescription_en: Sample\nversion: 0.1.0\nauthor: test\n---\nExample\n", encoding="utf-8")
    return path


def test_catalog_rejects_duplicate_ids_and_preserves_unknown(tmp_path: Path) -> None:
    registry(tmp_path)
    assert factory.validate_catalog(tmp_path) == []
    assert factory.get_product(tmp_path, "sample-skill")["versions"][0]["sha256"] == "UNKNOWN"
    data = factory.load_catalog(tmp_path)
    data["products"].append(dict(data["products"][0]))
    (tmp_path / "products" / "catalog.json").write_text(json.dumps(data), encoding="utf-8")
    assert any("duplicate" in x.lower() for x in factory.validate_catalog(tmp_path))


def test_init_is_type_aware_and_refuses_collision(tmp_path: Path) -> None:
    path = registry(tmp_path, source=False)
    assert factory.init_product(tmp_path, "sample-skill") == path
    assert (path / "SKILL.md").exists()
    front = yaml.safe_load((path / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
    assert front["name"] == "sample-skill"
    with pytest.raises(ValueError):
        factory.init_product(tmp_path, "sample-skill")


def test_init_refuses_reserved_candidate_path(tmp_path: Path) -> None:
    registry(tmp_path, source=False)
    archive = tmp_path / "dist/sample-skill-0.1.0-skill-candidate.zip"
    archive.parent.mkdir()
    archive.write_bytes(b"existing candidate")
    with pytest.raises(ValueError, match="candidate"):
        factory.init_product(tmp_path, "sample-skill")
    assert not (tmp_path / "packages/skills/sample-skill").exists()


def test_init_rejects_unregistered_skill_metadata_collision(tmp_path: Path) -> None:
    registry(tmp_path, source=False)
    other = tmp_path / "packages/skills/unregistered"
    other.mkdir(parents=True)
    (other / "SKILL.md").write_text("---\nname: sample-skill\n---\n", encoding="utf-8")
    with pytest.raises(ValueError, match="collision"):
        factory.init_product(tmp_path, "sample-skill")
    assert not (tmp_path / "packages/skills/sample-skill").exists()


def test_init_expert_and_connector_scaffolds_do_not_claim_old_runtime(tmp_path: Path) -> None:
    for kind, pid in (("Expert", "sample-expert"), ("Connector", "sample-connector")):
        root = tmp_path / pid
        path = registry(root, kind=kind, product_id=pid, source=False)
        template = ROOT / "packages" / ("experts/wangbin-expert-template" if kind == "Expert" else "connectors/wangbin-cli-connector-template")
        shutil.copytree(template, root / "packages" / ("experts/wangbin-expert-template" if kind == "Expert" else "connectors/wangbin-cli-connector-template"))
        built = factory.init_product(root, pid, connector_mode="cli" if kind == "Connector" else None)
        assert built == path
        if kind == "Expert":
            meta = json.loads((built / ".codebuddy-plugin/plugin.json").read_text(encoding="utf-8"))
            assert meta["name"] == pid and meta["agents"] == [f"./agents/{pid}.md"]
            assert "skills:" not in (built / "agents" / f"{pid}.md").read_text(encoding="utf-8")
        else:
            assert json.loads((built / "cli.json").read_text(encoding="utf-8")).get("auth") is None
            assert factory.validate_product(root, pid)["status"] == "FAIL"


def test_invalid_skill_frontmatter_reports_failure_instead_of_crashing(tmp_path: Path) -> None:
    path = registry(tmp_path)
    (path / "SKILL.md").write_text("---\nname: [unterminated\n---\n", encoding="utf-8")
    assert factory.validate_product(tmp_path, "sample-skill")["status"] == "FAIL"


def test_non_mapping_skill_frontmatter_reports_failure(tmp_path: Path) -> None:
    path = registry(tmp_path)
    (path / "SKILL.md").write_text("---\n- list not mapping\n---\n", encoding="utf-8")
    assert factory.validate_product(tmp_path, "sample-skill")["status"] == "FAIL"


def test_package_is_deterministic_and_independent(tmp_path: Path) -> None:
    path = registry(tmp_path)
    (path / "references").mkdir()
    (path / "references" / "guide.md").write_text("hello", encoding="utf-8")
    result = factory.package_product(tmp_path, "sample-skill")
    assert factory.package_product(tmp_path, "sample-skill")["sha256"] == result["sha256"]
    assert factory.verify_package(tmp_path, "sample-skill")["status"] == "PASS"
    assert factory.release_check(tmp_path, "sample-skill")["local_candidate"] == "BLOCKED"  # No registered tests.
    with zipfile.ZipFile(result["zip"]) as archive:
        assert sorted(archive.namelist()) == ["sample-skill/SKILL.md", "sample-skill/references/guide.md"]
    assert not (tmp_path / "packages" / "skills" / "other").exists()
    (path / "references" / "guide.md").write_text("changed", encoding="utf-8")
    assert factory.verify_package(tmp_path, "sample-skill")["status"] == "FAIL"
    with pytest.raises(ValueError):
        factory.package_product(tmp_path, "sample-skill")


def test_verify_rejects_manifest_version_tampering(tmp_path: Path) -> None:
    registry(tmp_path)
    result = factory.package_product(tmp_path, "sample-skill")
    manifest = Path(result["zip"] + ".manifest.json")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["version"] = "8.8.8"
    manifest.write_text(json.dumps(data), encoding="utf-8")
    assert factory.verify_package(tmp_path, "sample-skill")["status"] == "FAIL"


def test_package_rejects_private_and_symlink(tmp_path: Path) -> None:
    path = registry(tmp_path)
    (path / ".env").write_text("secret", encoding="utf-8")
    with pytest.raises(ValueError):
        factory.package_product(tmp_path, "sample-skill")
    (path / ".env").unlink()
    try:
        (path / "link.md").symlink_to(path / "SKILL.md")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(ValueError):
        factory.package_product(tmp_path, "sample-skill")


def test_unapproved_source_file_is_not_silently_archived(tmp_path: Path) -> None:
    path = registry(tmp_path)
    (path / "customer-records.md").write_text("private customer data", encoding="utf-8")
    with pytest.raises(ValueError, match="unapproved"):
        factory.package_product(tmp_path, "sample-skill")


def test_package_rejects_credentials_without_copying_archive(tmp_path: Path) -> None:
    path = registry(tmp_path)
    (path / "references").mkdir()
    (path / "references" / "config.json").write_text('{"api_key": "live-sensitive-secret"}', encoding="utf-8")
    with pytest.raises(ValueError, match="SECRET_PATTERN"):
        factory.package_product(tmp_path, "sample-skill")
    assert not (tmp_path / "dist").exists()


def test_catalog_rejects_invalid_version_and_source_collision(tmp_path: Path) -> None:
    registry(tmp_path)
    data = factory.load_catalog(tmp_path)
    item = data["products"][0]
    item["versions"][0]["version"] = "v1"
    item["versions"][0]["source"] = "../secret"
    (tmp_path / "products" / "catalog.json").write_text(json.dumps(data), encoding="utf-8")
    problems = factory.validate_catalog(tmp_path)
    assert any("version" in p for p in problems)
    assert any("source" in p for p in problems)


def test_backlog_and_metrics_do_not_invent_platform_evidence(tmp_path: Path) -> None:
    registry(tmp_path, source=False)
    assert factory.validate_product(tmp_path, "sample-skill")["status"] == "BLOCKED"
    assert factory.test_product(tmp_path, "sample-skill")["status"] == "NOT_TESTED"
    assert factory.release_check(tmp_path, "sample-skill")["platform"] == "BLOCKED"
    report = factory.portfolio_report(tmp_path)
    assert report["products"][0]["commercial_potential"] == "UNKNOWN"
    assert report["products"][0]["success_rate"] == "UNKNOWN"
    observed = factory.record_metric(tmp_path, "sample-skill", "exposures", 10, evidence="test observation")
    assert observed["recorded_at"].endswith("+00:00")
    assert observed["evidence_scope"]["exposures"] == "user-provided; unverified"
    assert factory.portfolio_report(tmp_path)["products"][0]["exposures"] == 10
    assert factory.portfolio_report(tmp_path)["products"][0]["success_rate"] == "UNKNOWN"


def test_portfolio_uses_only_observed_install_rate_and_costs(tmp_path: Path) -> None:
    registry(tmp_path)
    factory.record_metric(tmp_path, "sample-skill", "exposures", 20, evidence="platform export")
    factory.record_metric(tmp_path, "sample-skill", "installs", 4, evidence="platform export")
    factory.record_metric(tmp_path, "sample-skill", "development_cost", 100, evidence="ledger")
    factory.record_metric(tmp_path, "sample-skill", "maintenance_cost", 30, evidence="ledger")
    row = factory.portfolio_report(tmp_path)["products"][0]
    assert row["install_rate"] == .2
    assert row["success_rate"] == "UNKNOWN"
    assert row["total_cost"] == 130
    assert row["commercial_potential"] == "UNKNOWN"


def test_legacy_expert_validator_rejects_overlong_name(tmp_path: Path) -> None:
    original = ROOT / "packages" / "experts" / "wangbin-software-consultant"
    source = tmp_path / original.name
    shutil.copytree(original, source)
    meta_path = source / ".codebuddy-plugin" / "plugin.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["displayName"]["zh"] = "中文名称超过十五个汉字的测试用名字"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="displayName"):
        validate_source(source)


def test_phase5_validator_remains_callable_when_loaded_as_script() -> None:
    import runpy
    module = runpy.run_path(str(ROOT / "tooling/phase5_expert_packager.py"))
    assert module["validate_source"](ROOT / "packages/experts/wangbin-software-consultant")["name"] == "wangbin-software-consultant"


def test_cli_record_and_portfolio_round_trip(tmp_path: Path) -> None:
    registry(tmp_path)
    command = [sys.executable, "-m", "tooling.products"]
    recorded = subprocess.run(command + ["record", "--root", str(tmp_path), "--id", "sample-skill",
                                         "--field", "installs", "--value", "2", "--evidence", "observed report"],
                              cwd=ROOT, capture_output=True, text=True)
    assert recorded.returncode == 0, recorded.stderr
    metrics = json.loads((tmp_path / "products/metrics.json").read_text(encoding="utf-8"))
    assert metrics["metrics"][0]["installs"] == 2
    portfolio = subprocess.run(command + ["portfolio", "--root", str(tmp_path)], cwd=ROOT, capture_output=True, text=True)
    assert portfolio.returncode == 0, portfolio.stderr
    assert json.loads(portfolio.stdout)["products"][0]["installs"] == 2


def test_cli_lists_registered_products() -> None:
    result = subprocess.run([sys.executable, "-m", "tooling.products", "list", "--root", str(ROOT)], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert len(json.loads(result.stdout)["products"]) == 10


def test_release_check_reports_local_blocked_in_exit_status_and_platform_separately(tmp_path: Path) -> None:
    registry(tmp_path)
    result = factory.release_check(tmp_path, "sample-skill")
    assert result["status"] == "BLOCKED"
    assert result["local_candidate"] == "BLOCKED"
    assert result["platform"] == "BLOCKED"
    cli = subprocess.run([sys.executable, "-m", "tooling.products", "release-check", "--root", str(tmp_path), "--id", "sample-skill"], cwd=ROOT, text=True, capture_output=True)
    assert cli.returncode == 1
    assert json.loads(cli.stdout)["platform"] == "BLOCKED"


def test_release_check_keeps_platform_and_license_blockers_when_local_passes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    registry(tmp_path)
    monkeypatch.setattr(factory, "validate_product", lambda root, pid: {"status": "PASS"})
    monkeypatch.setattr(factory, "verify_package", lambda root, pid: {"status": "PASS"})
    monkeypatch.setattr(factory, "test_product", lambda root, pid: {"status": "PASS"})
    result = factory.release_check(tmp_path, "sample-skill")
    assert result["local_candidate"] == "PASS"
    assert result["license_and_dependencies"]["status"] == "BLOCKED"
    assert result["platform"] == "BLOCKED"
    assert result["status"] == "BLOCKED"


def test_register_version_selects_active_without_overwriting_historical_metrics(tmp_path: Path) -> None:
    registry(tmp_path)
    factory.record_metric(tmp_path, "sample-skill", "uses", 1, evidence="v0 observation")
    registered = factory.register_version(tmp_path, "sample-skill", "0.2.0")
    assert registered["active_version"] == "0.2.0"
    factory.record_metric(tmp_path, "sample-skill", "uses", 2, evidence="v1 observation")
    catalog = factory.load_catalog(tmp_path)
    item = catalog["products"][0]
    assert item["active_version"] == "0.2.0"
    assert [entry["version"] for entry in item["versions"]] == ["0.1.0", "0.2.0"]
    metrics = json.loads((tmp_path / "products/metrics.json").read_text(encoding="utf-8"))["metrics"]
    assert {(entry["version"], entry["uses"]) for entry in metrics} == {("0.1.0", 1), ("0.2.0", 2)}


def test_package_persists_relative_archive_evidence_and_catalog_hash(tmp_path: Path) -> None:
    registry(tmp_path)
    result = factory.package_product(tmp_path, "sample-skill")
    manifest = json.loads(Path(result["zip"] + ".manifest.json").read_text(encoding="utf-8"))
    item = factory.get_product(tmp_path, "sample-skill")
    version = item["versions"][0]
    assert not Path(manifest["archive"]).is_absolute()
    assert not Path(manifest["source"]).is_absolute()
    assert version["candidate"] == manifest["archive"]
    assert version["archive_evidence"] == manifest["archive"]
    assert version["sha256"] == result["sha256"]


def test_rejects_symlink_ancestors_and_traversing_registered_test(tmp_path: Path) -> None:
    path = registry(tmp_path)
    try:
        real_packages = tmp_path / "real-packages"
        real_packages.mkdir()
        (tmp_path / "packages").rename(tmp_path / "packages-real")
        (tmp_path / "packages").symlink_to(real_packages, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(ValueError, match="symlink"):
        factory.validate_product(tmp_path, "sample-skill")

    root = tmp_path / "traversal"
    registry(root)
    data = factory.load_catalog(root)
    data["products"][0]["test_path"] = "tests/../outside.py"
    (root / "products/catalog.json").write_text(json.dumps(data), encoding="utf-8")
    assert factory.test_product(root, "sample-skill")["status"] == "NOT_TESTED"


def test_metrics_reject_non_finite_values_and_fabricated_approval(tmp_path: Path) -> None:
    registry(tmp_path)
    for value in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError, match="finite"):
            factory.record_metric(tmp_path, "sample-skill", "uses", value, evidence="untrusted input")
    with pytest.raises(ValueError, match="verified platform"):
        factory.record_metric(tmp_path, "sample-skill", "review_result", "APPROVED", evidence="user says approved")
    result = factory.release_check(tmp_path, "sample-skill")
    assert result["review"] == "NOT_TESTED"
    assert result["license_and_dependencies"]["status"] != "PASS"
