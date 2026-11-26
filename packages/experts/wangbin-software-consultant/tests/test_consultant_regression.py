"""Synthetic executor cases: no live product tree copies, release scans or host calls."""
from __future__ import annotations

import json
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tooling import product_factory as factory

NAME = "wangbin-software-consultant"
ROOT = Path(__file__).resolve().parents[4]


def _catalog(root, name=NAME):
    (root / "products").mkdir(parents=True)
    source = root / "packages" / "experts" / name
    source.mkdir(parents=True)
    row = {"id": name, "name": "Synthetic", "type": "Expert", "status": "DEVELOPING",
           "target_users": "Synthetic", "scenario": "Synthetic", "development": "UNKNOWN",
           "maintenance": "UNKNOWN", "review_status": "NOT_TESTED", "review_evidence": "UNKNOWN",
           "active_version": "1.2.0", "versions": [{"version": "1.2.0", "candidate": "UNKNOWN",
           "sha256": "UNKNOWN", "date": "UNKNOWN", "source": source.relative_to(root).as_posix()}],
           "test_path": "tests/test_legacy.py"}
    (root / "products/catalog.json").write_text(json.dumps({"schema_version": 1, "products": [row]}), encoding="utf-8")
    return source


def test_registered_consultant_routes_to_executor(tmp_path):
    _catalog(tmp_path)
    result = factory.test_product(tmp_path, NAME)
    assert result["status"] == "BLOCKED"
    assert result["id"] == NAME
    assert result["gates"]["snapshot"] == "BLOCKED"
    assert result["returncode"] != 0


def test_other_registered_product_retains_single_test_behavior(tmp_path):
    _catalog(tmp_path, "sample-expert")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_legacy.py").write_text("def test_old_entry():\n    assert 1 + 1 == 2\n", encoding="utf-8")
    (tests / "test_unrelated.py").write_text("def test_unrelated():\n    assert False\n", encoding="utf-8")
    row = factory.test_product(tmp_path, "sample-expert")
    assert row["status"] == "PASS" and row["returncode"] == 0
    assert "1 passed" in row["output"]


def test_release_check_consumes_exact_consultant_result(tmp_path, monkeypatch):
    from tooling import consultant_regression as runner
    from tooling import similarity
    _catalog(tmp_path)
    result = {"id": NAME, "status": "BLOCKED", "returncode": 1, "counts": {"passed": 2, "unexecuted": 1}}
    monkeypatch.setattr(runner, "run", lambda root: result)
    monkeypatch.setattr(factory, "validate_product", lambda root, name: {"status": "PASS"})
    monkeypatch.setattr(factory, "verify_package", lambda root, name: {"status": "PASS"})
    monkeypatch.setattr(factory, "_license_dependency_gate", lambda *a: {"status": "BLOCKED"})
    monkeypatch.setattr(similarity, "similarity_check", lambda *a: {"gates": dict.fromkeys((
        "ANTI_DUPLICATION_PASS", "FUNCTIONAL_DISTINCTNESS_PASS", "INPUT_OUTPUT_DISTINCTNESS_PASS",
        "METADATA_DISTINCTNESS_PASS", "INDEPENDENT_VALUE_PASS"), "BLOCKED")})
    release = factory.release_check(tmp_path, NAME)
    assert release["local_tests"] == result
    assert release["local_candidate"] == release["gates"]["LOCAL_TEST_PASS"] == "BLOCKED"
    assert release["publication"] == "BLOCKED"


def _exercise(tmp_path, text, blockers=None, timeout=20):
    from tooling import consultant_regression as runner
    # A miniature source image, no live repository contents except the executor itself.
    snapshot = tmp_path / "s"
    package = snapshot / "tooling"
    package.mkdir(parents=True)
    (package / "consultant_regression.py").write_bytes((ROOT / "tooling/consultant_regression.py").read_bytes())
    (snapshot / "test_case.py").write_text(text, encoding="utf-8")
    (snapshot / "conftest.py").write_text("raise RuntimeError('unrelated conftest must not load')\n", encoding="utf-8")
    output = tmp_path / "evidence"
    output.mkdir()
    return runner.execute_cases(snapshot, output, Path(sys.executable), ["test_case.py"], blockers or {}, timeout=timeout)


def test_case_accounting_retains_partial_and_prerequisite_ids(tmp_path):
    result = _exercise(tmp_path, "import pytest\n"
        "def test_ok(): pass\ndef test_fail(): assert False\n"
        "@pytest.mark.skip(reason='explicit')\ndef test_skip(): pass\n"
        "def test_missing(): assert False\n", {"test_case.py::test_missing": "missing original"})
    assert result["status"] == "FAIL"
    assert result["counts"] == {"collected": 4, "selected": 3, "passed": 1, "failed": 1, "errors": 0,
                                "skipped": 1, "deselected": 0, "unexecuted": 1, "timeout": 0}
    assert result["cases"]["test_case.py::test_missing"]["status"] == "BLOCKED"
    assert result["cases"]["test_case.py::test_ok"]["status"] == "PASS"


def test_missing_prerequisite_never_counts_as_skip_or_pass(tmp_path):
    result = _exercise(tmp_path, "def test_ok(): pass\ndef test_missing(): assert False\n",
                       {"test_case.py::test_missing": "missing history"})
    assert result["status"] == "BLOCKED" and result["returncode"] != 0
    assert result["counts"]["passed"] == 1 and result["counts"]["unexecuted"] == 1
    assert result["counts"]["skipped"] == 0


def test_collection_error_is_not_empty_success(tmp_path):
    result = _exercise(tmp_path, "raise RuntimeError('collection failed')\n")
    assert result["status"] == "FAIL" and result["counts"]["errors"] > 0
    assert result["returncode"] != 0


def test_zero_cases_is_not_success(tmp_path):
    result = _exercise(tmp_path, "# deliberately empty\n")
    assert result["status"] == "FAIL" and result["counts"]["collected"] == 0


def test_timeout_preserves_completed_case(tmp_path):
    result = _exercise(tmp_path, "import time\ndef test_first(): pass\ndef test_second(): time.sleep(30)\n", timeout=4)
    assert result["status"] == "FAIL"
    assert result["counts"]["timeout"] == 1 and result["counts"]["passed"] == 1
    assert result["cases"]["test_case.py::test_second"]["status"] == "TIMEOUT"


def test_safe_path_rejects_traversal(tmp_path):
    from tooling import consultant_regression as runner
    with pytest.raises(ValueError):
        runner.safe_path(tmp_path, "../outside")
    with pytest.raises(ValueError):
        runner.safe_path(tmp_path, "C:/outside")


def test_formal_mode_rejects_symbolic_head(tmp_path):
    from tooling import consultant_regression as runner
    result = runner.run(tmp_path, mode="formal", commit="HEAD")
    assert result["status"] != "PASS" and result["returncode"] != 0


def test_case_call_failure_and_teardown_error_both_retained(tmp_path):
    result = _exercise(tmp_path, "import pytest\n"
                       "@pytest.fixture\ndef broken():\n    yield\n    raise RuntimeError('teardown')\n"
                       "def test_both(broken): assert False\n")
    assert result["status"] == "FAIL"
    assert result["counts"]["selected"] == result["counts"]["errors"] == 1
    assert result["counts"]["failed"] == 0  # one terminal case status
    assert result["phase_counts"]["call"]["failed"] == 1
    assert result["phase_counts"]["teardown"]["failed"] == 1
    assert result["pytest_exitcode"] == 1
    assert result["case_counts"]["ERROR"] == 1 and result["case_counts"]["FAIL"] == 0
    assert result["pytest_outcomes"]["call_failures"] == 1
    assert result["pytest_outcomes"]["teardown_errors"] == 1


def test_worker_git_requests_are_offline_and_readonly(tmp_path):
    result = _exercise(tmp_path, "import os\n"
                       "def test_git_env():\n"
                       "    assert os.environ['GIT_NO_LAZY_FETCH'] == '1'\n"
                       "    assert os.environ['GIT_NO_REPLACE_OBJECTS'] == '1'\n"
                       "    assert os.environ['GIT_OPTIONAL_LOCKS'] == '0'\n"
                       "    assert os.environ['GIT_TERMINAL_PROMPT'] == '0'\n"
                       "    assert os.environ['GIT_ALLOW_PROTOCOL'] == ''\n")
    assert result["status"] == "PASS", result


def _mini_repo(tmp_path, runner):
    # Only the two executor modules and a synthetic selection plan, no live tree.
    paths = (runner.BASELINE, "tooling/consultant_regression.py", "tooling/consultant_regression_support.py")
    for rel in paths:
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if rel == runner.BASELINE:
            p.write_text(json.dumps({"files": paths, "case_ids": [str(i) for i in range(307)],
                                     "added_case_ids": ["new"]}), encoding="utf-8")
        else:
            p.write_bytes((ROOT / rel).read_bytes())
    (tmp_path / ".gitignore").write_text(".runtime/\n", encoding="utf-8")
    def git(*args):
        return subprocess.run(["git", "-c", "core.longpaths=true", *args], cwd=tmp_path, env=runner._env(), check=True, capture_output=True)
    git("init", "-q")
    git("add", "--", ".gitignore", *paths)
    git("-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "-qm", "fixture")
    return paths


@pytest.mark.parametrize("mode", ["development", "formal"])
def test_supervisor_rejects_different_repository(tmp_path, monkeypatch, mode):
    from tooling import consultant_regression as runner
    monkeypatch.setattr(runner, "APPROVED_FILES", _mini_repo(tmp_path, runner))
    commit = runner._git(tmp_path, "rev-parse", "HEAD").decode().strip() if mode == "formal" else None
    result = runner.run(tmp_path, mode=mode, commit=commit, python=tmp_path / "missing-python.exe")
    assert result["status"] == result["gates"]["snapshot"] == "FAIL"
    assert result["returncode"] != 0
    assert "orchestrator" in result["reason"]


def _load_mini_runner(tmp_path, runner):
    paths = _mini_repo(tmp_path, runner)
    spec = importlib.util.spec_from_file_location("tooling.mini_runner", tmp_path / paths[1])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.APPROVED_FILES = paths
    return module


def test_development_refuses_stale_loaded_runner(tmp_path):
    from tooling import consultant_regression as runner
    module = _load_mini_runner(tmp_path, runner)
    source = tmp_path / "tooling/consultant_regression.py"
    source.write_bytes(source.read_bytes() + b"\n# changed after import\n")
    result = module.run(tmp_path, python=tmp_path / "missing-python.exe")
    assert result["status"] == result["gates"]["snapshot"] == "FAIL"
    assert "orchestrator" in result["reason"]


def test_development_records_dirty_snapshot_and_loaded_module_identities(tmp_path):
    from tooling import consultant_regression as runner
    module = _load_mini_runner(tmp_path, runner)
    (tmp_path / "dirty.txt").write_text("synthetic", encoding="utf-8")
    result = module.run(tmp_path, python=tmp_path / "missing-python.exe")
    assert result["gates"]["snapshot"] == "PASS"
    assert result["gates"]["environment"] == "BLOCKED"
    assert result["worktree"]["dirty"] is True
    assert "?? dirty.txt" in result["worktree"]["status"]
    assert result["worktree_after"] == result["worktree"]
    assert set(result["loaded_modules"]) == {"tooling/consultant_regression.py", "tooling/consultant_regression_support.py"}
    for rel, row in result["loaded_modules"].items():
        assert Path(row["path"]) == tmp_path / rel
        assert row["sha256"] == result["files"][rel]["sha256"]
        assert row["canonical_sha256"] == result["files"][rel]["canonical_sha256"]


def test_formal_records_loaded_raw_and_actual_committed_hashes(tmp_path):
    from tooling import consultant_regression as runner
    module = _load_mini_runner(tmp_path, runner)
    commit = module._git(tmp_path, "rev-parse", "HEAD").decode().strip()
    result = module.run(tmp_path, mode="formal", commit=commit, python=tmp_path / "missing-python.exe")
    assert result["gates"]["snapshot"] == "PASS", result.get("reason")
    assert set(result["loaded_modules"]) == {"tooling/consultant_regression.py", "tooling/consultant_regression_support.py"}
    for rel, row in result["loaded_modules"].items():
        actual = subprocess.run(["git", "-c", "core.longpaths=true", "show", f"{commit}:{rel}"], cwd=tmp_path,
                                env=runner._env(), check=True, capture_output=True).stdout
        assert row["git_blob_sha256"] == runner.digest(actual)
        assert row["sha256"] == runner.digest((tmp_path / rel).read_bytes())
        assert row["canonical_sha256"] == result["files"][rel]["canonical_sha256"]


def test_sealed_source_binding_independent_of_missing_original():
    from tooling import consultant_regression as runner
    from tooling import consultant_regression_support as support
    rows = {f"{runner.SOURCE}/{rel}": {"canonical_sha256": "a" * 64} for rel in support.CANDIDATE_MEMBERS}
    sealed = {"status": "PASS", "blobs": {path: {"sha256": "a" * 64} for path in rows}}
    assert runner._sealed_source_binding(rows, sealed, support.CANDIDATE_MEMBERS) == "PASS"
    rows[next(iter(rows))]["canonical_sha256"] = "b" * 64
    assert runner._sealed_source_binding(rows, sealed, support.CANDIDATE_MEMBERS) == "FAIL"
    assert runner._sealed_source_binding(rows, {"status": "BLOCKED", "blobs": {}}, support.CANDIDATE_MEMBERS) == "BLOCKED"


def test_current_fixed_price_and_catalog_do_not_depend_on_history():
    from tooling import consultant_regression as runner
    module = f"{runner.SOURCE}/tests/"
    ids = [module + "test_fixed_price_source.py::test_fixed_source_cli[a]",
           module + "test_fixed_price_source.py::test_current_fixed_source_cli[a]",
           module + "test_bundled_calculator.py::test_original_catalog_identity"]
    blocked = {"status": "BLOCKED"}
    decisions = runner._prerequisites(dict.fromkeys(("price", "sealed", "legacy"), blocked), blocked, ids)
    assert set(decisions) == {ids[0]}


def test_package_gates_and_retained_receipts_are_independent(tmp_path):
    from tooling import consultant_regression as runner
    snapshot, evidence = tmp_path / "s", tmp_path / "evidence"
    evidence.mkdir()
    names = {"rebuild": "test_archive_is_deterministic_and_binds_formal_bytes",
             "rebuilt_runtime": "test_rebuilt_candidate_runtime",
             "original_runtime": "test_original_candidate_identity_and_runtime"}
    cases = {f"{runner.SOURCE}/tests/test_bundled_calculator.py::{name}":
             {"status": "FAIL" if gate == "rebuilt_runtime" else "PASS"} for gate, name in names.items()}
    for gate, name in names.items():
        directory = snapshot / "tmp-run" / (name[:30] + "0")
        directory.mkdir(parents=True)
        paths = []
        if gate == "rebuild":
            paths.extend(f"{entry}/{rel}" for entry in ("dedicated", "generic") for rel in runner.ORIGINAL)
        else:
            if gate == "rebuilt_runtime":
                paths.extend(f"dedicated/{rel}" for rel in runner.ORIGINAL)
            paths.extend(["fictional-receipt.json", "fictional-v2-receipt.json"])
        for rel in paths:
            target = directory / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"synthetic archive" if rel.endswith(".zip") else b"{}\n")
    result = {"cases": cases, "gates": {}}
    runner._package_evidence(snapshot, evidence, result)
    assert result["gates"] == {"rebuild": "PASS", "rebuilt_runtime": "FAIL", "original_runtime": "PASS"}
    for gate, rows in result["package_evidence"].items():
        for rel, identity in rows.items():
            if rel.endswith(".zip"):
                assert "retained" not in identity
            else:
                retained = evidence / identity["retained"]
                assert retained.read_bytes() == b"{}\n"
                assert runner.digest(retained.read_bytes()) == identity["sha256"]


def _current_catalog():
    return {"products": [{"id": NAME, "active_version": "1.2.1", "versions": [
        {"version": "1.2.1", "source": f"packages/experts/{NAME}",
         "candidate": f"dist/{NAME}-1.2.1-expert-candidate.zip", "archive_evidence": "UNKNOWN",
         "source_commit": "UNKNOWN", "sha256": "UNKNOWN"}]}]}


def test_current_unsealed_registration_does_not_pass(tmp_path):
    from tooling import consultant_regression_support as support
    current = support.inspect_current(tmp_path, {}, _current_catalog())
    assert current["status"] == current["source_binding"] == current["integrity"] == current["archive_binding"] == "BLOCKED"
    assert not (tmp_path / "dist").exists()


def test_current_wrong_historical_commit_cannot_be_current_seal():
    from tooling import consultant_regression_support as support
    repo = Path(os.environ.get("WANGBIN_CONSULTANT_TEST_SOURCE_REPO", ROOT))
    catalog = _current_catalog()
    entry = catalog["products"][0]["versions"][0]
    entry["source_commit"] = support.SEALED_COMMIT
    historical = support.inspect_history(repo)["sealed"]
    assert historical["status"] == "PASS"
    rows = {path: {"canonical_sha256": row["sha256"]} for path, row in historical["blobs"].items()}
    current = support.inspect_current(repo, rows, catalog)
    assert current["status"] == current["source_binding"] == "FAIL"
    assert current["integrity"] == "BLOCKED"


def test_current_and_historical_prerequisites_are_independent():
    from tooling import consultant_regression as runner
    prefix = f"{runner.SOURCE}/tests/test_bundled_calculator.py::"
    ids = [prefix + name for name in ("test_original_candidate_identity_and_runtime",
        "test_current_121_snapshot_matches_registered_seal", "test_current_121_archive_is_deterministic",
        "test_current_121_rebuilt_runtime", "test_current_121_original_runtime", "test_current_121_rejects_uncommitted_bytes")]
    pending = {"source_binding": "BLOCKED", "status": "BLOCKED"}
    assert set(runner._current_prerequisites(pending, ids)) == set(ids[1:])
    assert set(runner._current_prerequisites({"source_binding": "PASS", "status": "BLOCKED"}, ids)) == {ids[4]}
    assert runner._current_prerequisites({"source_binding": "PASS", "status": "PASS"}, ids) == {}
    history = dict.fromkeys(("price", "sealed", "legacy", "delivery"), {"status": "PASS"})
    assert set(runner._prerequisites(history, {"status": "BLOCKED"}, ids)) == {ids[0]}


def test_current_package_evidence_requires_current_archive_paths(tmp_path):
    from tooling import consultant_regression as runner
    snapshot, evidence = tmp_path / "s", tmp_path / "evidence"
    evidence.mkdir()
    test = "test_current_121_archive_is_deterministic"
    directory = snapshot / "tmp-run" / (test[:30] + "0")
    directory.mkdir(parents=True)
    case = f"{runner.SOURCE}/tests/test_bundled_calculator.py::{test}"
    result = {"gates": {}, "cases": {case: {"status": "PASS"}}}
    # Historical paths alone cannot substantiate a current rebuild.
    for entry in ("dedicated", "generic"):
        for rel in runner.ORIGINAL:
            path = directory / entry / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"fictional historical evidence")
    runner._package_evidence(snapshot, evidence, result, current=True)
    assert result["gates"]["current_rebuild"] == "FAIL"
    assert result["gates"]["rebuild"] == "BLOCKED"
