"""Independent SYNTHETIC candidate replay; no sealed project is modified."""
from copy import deepcopy
from decimal import Decimal
import hashlib
import os
from pathlib import Path
import subprocess
from uuid import uuid4

import pytest

from consumption_case_support import atom, axis, case, extend, load_rows, market_rows, parameter, period_row, series_header
from energy_case_support import resource_header, resource_rows
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.calculation.energy_yield import calculate_rooftop as generate
from wangbin_solar_pv.calculation.input_contract import validate_export
from wangbin_solar_pv.calculation.method_config import MethodConfig
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.intake import IntakeSession
from wangbin_solar_pv.local_files import Workspace
from wangbin_solar_pv.serialization import digest, dumps
from wangbin_solar_pv.timeseries_bundle import BundleBudget, read_bundle, write_bundle


def _metric(result, metric_id):
    return next(m for m in result["results"]["metrics"] if m["metric_id"] == metric_id)


@pytest.fixture(scope="module")
def original(request):
    scratch = Path(os.environ["TMPDIR"])
    workspace = Workspace(scratch)
    root = scratch / ("synthetic-p2-replay-" + uuid4().hex)
    root.mkdir(mode=0o700)
    identity = root.stat().st_dev, root.stat().st_ino
    from wangbin_solar_pv.calculation.break_even_replay import _remove_owned
    request.addfinalizer(lambda: _remove_owned(root, identity, workspace))
    catalog = Catalog()
    budget = BundleBudget(max_seconds=1800)
    session, original_methods = case(catalog, "industrial_rooftop", years=1)
    generation_input = session.export()
    write_bundle(root / "resource", base_export=generation_input,
                 datasets={"resource.timeseries": {"header": resource_header(catalog), "rows": resource_rows(catalog)}},
                 catalog=catalog, budget=budget)
    with read_bundle(root / "resource", catalog=catalog, budget=budget) as bundle:
        generation = generate(generation_input, original_methods, catalog=catalog, output_dir=root / "generation",
                              budget=budget, bundle=bundle)
    session, methods = extend(session, original_methods)
    session.project.values["project.cashflow_tax_basis"] = atom(catalog, "project.cashflow_tax_basis", "post_tax")
    data = methods.to_dict()
    data["parameters"].update({
        "break_even.minimum_price": parameter("break_even.minimum_price", Decimal("0")),
        "break_even.maximum_price": parameter("break_even.maximum_price", Decimal("2")),
        "break_even.price_tolerance": parameter("break_even.price_tolerance", Decimal("0.000001")),
        "break_even.maximum_iterations": parameter("break_even.maximum_iterations", 256),
        "break_even.method": parameter("break_even.method", "CERTIFIED_MONOTONE_RECALCULATION"),
    })
    methods = MethodConfig.from_dict(data)
    exported = validate_export(session.export(), catalog).export
    period = exported["project"]["values"]["tariff.periods"]["value"][0]
    price = period["fields"]["tariff.periods.sale_price"]
    period_axis = axis()
    # The resource data is independently replayable; no manifest-only shortcut.
    write_bundle(root / "original", base_export=exported,
                 datasets={"resource.timeseries": {"header": resource_header(catalog), "rows": resource_rows(catalog)},
                           "load.series": {"header": series_header(catalog, "load.series", period_axis),
                                           "rows": load_rows(catalog, period_axis)}},
                 catalog=catalog, budget=budget)
    with read_bundle(root / "original", catalog=catalog, budget=budget) as bundle:
        control = {
            "schema_version": "solar-pv-break-even-execution/1.0.0", "formula_id": "F-BREAK-EVEN-PRICE",
            "project_id": exported["project"]["project_id"], "pv_type": "industrial_rooftop", "basis": "项目税后",
            "original_input_hash": exported["input_hash"], "original_source_snapshot_id": exported["source_snapshot_id"],
            "original_dataset_content_hash": bundle.content_hash, "generation_result_hash": generation["result_hash"],
            "method_config_hash": methods.hash,
            "selector": {"field_id": "tariff.periods.sale_price", "row_id": period["row_id"],
                         "field_instance_id": price["field_instance_id"], "original_atom_hash": digest(price),
                         "unit": price["unit"], "economic_basis": price["economic_basis"]},
            "source": {"source_kind": "SYNTHETIC", "status": "ASSUMED",
                       "source_id": "SYNTHETIC:p2-replay", "source_reference": "SYNTHETIC:p2-replay:single-price",
                       "license_status": "AUTHORIZED"},
        }
        return root, catalog, budget, exported, methods, control, generation["result_hash"], bundle.content_hash


def test_real_replay_changes_only_one_atom_and_runs_both_3c_calculations(original):
    from wangbin_solar_pv.calculation.break_even_replay import replay_price_candidate
    root, catalog, budget, exported, methods, control, generation_hash, original_bundle_hash = original
    original_hash = digest(exported)
    with read_bundle(root / "original", catalog=catalog, budget=budget) as bundle:
        result = replay_price_candidate(control, exported, methods, bundle, root / "generation", Decimal("0.6"),
                                        catalog=catalog, budget=budget, workspace=Workspace(root), run_name="candidate-a")
    assert digest(exported) == original_hash
    assert result.original_input_hash == exported["input_hash"]
    assert result.candidate_export["input_hash"] != exported["input_hash"]
    assert validate_export(result.candidate_export, catalog).phase2_input_hash == result.candidate_export["input_hash"]
    old_rows = exported["project"]["values"]["tariff.periods"]["value"]
    new_rows = result.candidate_export["project"]["values"]["tariff.periods"]["value"]
    assert len(old_rows) == len(new_rows)
    for old, new in zip(old_rows, new_rows):
        for fid, old_atom in old["fields"].items():
            if old["row_id"] == control["selector"]["row_id"] and fid == control["selector"]["field_id"]:
                assert new["fields"][fid]["value"] == Decimal("0.6")
                assert new["fields"][fid]["source_kind"] == "ASSUMPTION"
                assert new["fields"][fid]["source_id"] == control["source"]["source_id"]
                assert control["source"]["source_reference"] in new["fields"][fid]["assumption"]["reason"]
                assert old_atom["value"] == Decimal("0.4")
            else:
                assert dumps(new["fields"][fid]) == dumps(old_atom)
    assert result.generation_result_hash == generation_hash
    assert result.original_bundle_hash == original_bundle_hash
    assert result.candidate_bundle_hash != original_bundle_hash
    with read_bundle(root / "candidate-a" / "candidate-d3", catalog=catalog, budget=budget) as candidate_bundle:
        assert candidate_bundle.content_hash == result.candidate_bundle_hash
        with read_bundle(root / "original", catalog=catalog, budget=budget) as original_bundle:
            for dataset in original_bundle.dataset_ids:
                assert (candidate_bundle.manifest["datasets"][dataset]["canonical_array_hash"]
                        == original_bundle.manifest["datasets"][dataset]["canonical_array_hash"])
                assert (candidate_bundle.manifest["datasets"][dataset]["header"]
                        == original_bundle.manifest["datasets"][dataset]["header"])
    old = _metric(result.original_revenue, "revenue.year.1")["details"]["ledger"]
    new = _metric(result.candidate_revenue, "revenue.year.1")["details"]["ledger"]
    assert old["export_sales_revenue"] == Decimal("35040.0")
    assert new["export_sales_revenue"] == Decimal("52560.0")
    assert new["export_sales_revenue"] - old["export_sales_revenue"] == Decimal("87600") * Decimal("0.2")
    assert result.original_revenue["result_hash"] != result.candidate_revenue["result_hash"]
    assert control["source"]["source_id"] in _metric(result.candidate_revenue, "revenue.year.1")["source_ids"]
    with read_bundle(root / "original", catalog=catalog, budget=budget) as bundle:
        repeat = replay_price_candidate(control, exported, methods, bundle, root / "generation", Decimal("0.6"),
                                        catalog=catalog, budget=budget, workspace=Workspace(root), run_name="candidate-b")
    assert digest(repeat.candidate_export) == digest(result.candidate_export)
    assert repeat.candidate_bundle_hash == result.candidate_bundle_hash
    assert repeat.original_revenue["result_hash"] == result.original_revenue["result_hash"]
    assert repeat.candidate_revenue["result_hash"] == result.candidate_revenue["result_hash"]


def test_invalid_source_does_not_publish_candidate(original):
    from wangbin_solar_pv.calculation.break_even_replay import replay_price_candidate
    root, catalog, budget, exported, methods, control, _, _ = original
    bad = deepcopy(control)
    bad["source"]["source_id"] = ""
    with read_bundle(root / "original", catalog=catalog, budget=budget) as bundle:
        with pytest.raises(ContractError):
            replay_price_candidate(bad, exported, methods, bundle, root / "generation", Decimal("0.6"),
                                   catalog=catalog, budget=budget, workspace=Workspace(root), run_name="bad-source")
    assert not (root / "bad-source").exists()


def test_candidate_workspace_is_private_and_separate_from_pytest(original, request):
    root = original[0]
    assert root.parent.resolve() == Path(os.environ["TMPDIR"]).resolve()
    assert root.parent.resolve() != Path(request.config.option.basetemp).resolve()
    assert Workspace(root).root == root


def test_unapproved_pytest_workspace_and_traversal_are_rejected(original, tmp_path):
    from wangbin_solar_pv.calculation.break_even_replay import replay_price_candidate

    root, catalog, budget, exported, methods, control, _, _ = original
    assert tmp_path.resolve().parent != root.parent.resolve()
    with read_bundle(root / "original", catalog=catalog, budget=budget) as bundle:
        with pytest.raises(ContractError, match="BREAK_EVEN_SCRATCH_OUTSIDE_WORKSPACE"):
            replay_price_candidate(control, exported, methods, bundle, root / "generation", Decimal("0.6"),
                                   catalog=catalog, budget=budget, workspace=Workspace(tmp_path), run_name="unapproved")
        with pytest.raises(ContractError, match="BREAK_EVEN_RUN_NAME"):
            replay_price_candidate(control, exported, methods, bundle, root / "generation", Decimal("0.6"),
                                   catalog=catalog, budget=budget, workspace=Workspace(root), run_name="../outside")
    with pytest.raises(ContractError, match="PATH_TRAVERSAL"):
        Workspace(root).path("../outside", json_only=False)
    assert not (tmp_path / "unapproved").exists()
    assert not (root.parent / "outside").exists()


def test_existing_candidate_directory_is_not_overwritten(original):
    from wangbin_solar_pv.calculation.break_even_replay import replay_price_candidate

    root, catalog, budget, exported, methods, control, _, _ = original
    existing = root / "already-present"
    existing.mkdir()
    sentinel = existing / "owned-by-other-run.txt"
    sentinel.write_text("SYNTHETIC other run", encoding="utf-8")
    with read_bundle(root / "original", catalog=catalog, budget=budget) as bundle:
        with pytest.raises(ContractError, match="BREAK_EVEN_OUTPUT_EXISTS"):
            replay_price_candidate(control, exported, methods, bundle, root / "generation", Decimal("0.6"),
                                   catalog=catalog, budget=budget, workspace=Workspace(root), run_name=existing.name)
    assert sentinel.read_text(encoding="utf-8") == "SYNTHETIC other run"


def test_workspace_rejects_real_symlink(original):
    root = original[0]
    target = root / "link-target"
    target.mkdir()
    link = root / "linked-directory"
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        target.rmdir()
        pytest.skip(f"Windows symlink privilege unavailable: {exc.errno}")
    try:
        with pytest.raises(ContractError, match="UNSAFE_LINK"):
            Workspace(link)
    finally:
        link.unlink()
        target.rmdir()


def test_workspace_rejects_real_hardlink(original):
    root = original[0]
    target = root / "hardlink-target.json"
    linked = root / "linked-file.json"
    target.write_text("{}", encoding="utf-8")
    os.link(target, linked)
    try:
        with pytest.raises(ContractError, match="HARDLINK_FILE"):
            Workspace(root).read(linked.name)
    finally:
        linked.unlink()
        target.unlink()


@pytest.mark.skipif(os.name != "nt", reason="Windows junction security check")
def test_workspace_rejects_real_windows_junction(original):
    root = original[0]
    target = root / "junction-target"
    target.mkdir()
    junction = root / "linked-junction"
    created = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(target)],
                             capture_output=True, timeout=30)
    assert created.returncode == 0, "SYNTHETIC junction fixture could not be created"
    try:
        with pytest.raises(ContractError, match="UNSAFE_LINK"):
            Workspace(junction)
    finally:
        os.rmdir(junction)
        target.rmdir()


def test_derived_export_preserves_an_unselected_price_row_and_original_candidate():
    from test_phase3e_price_selector import _case
    from wangbin_solar_pv.calculation.break_even_execution import validate_price_selector
    from wangbin_solar_pv.calculation.break_even_replay import _derive

    catalog, old_export, methods, control = _case()
    session = IntakeSession.from_dict(old_export["project"], catalog)
    rows = session.project.values["tariff.periods"]["value"]
    old_end = rows[0]["fields"]["tariff.periods.effective_to"]
    old_end["value"] = old_end["original_value"] = "2029-12-31"
    rows.append(period_row(catalog, "unselected", first="2030-01-01", price=Decimal("0.7"), avoid=None))
    old_export = validate_export(session.export(), catalog).export
    original = old_export["project"]["values"]["tariff.periods"]["value"][0]["fields"]["tariff.periods.sale_price"]
    control["selector"]["original_atom_hash"] = digest(original)
    control["original_input_hash"] = old_export["input_hash"]
    control["original_source_snapshot_id"] = old_export["source_snapshot_id"]
    selected = validate_price_selector(control, old_export, methods, None, catalog)
    candidate, new_atom = _derive(old_export, selected, Decimal("0.6"), catalog)
    new_rows = candidate["project"]["values"]["tariff.periods"]["value"]
    assert dumps(new_rows[1]) == dumps(old_export["project"]["values"]["tariff.periods"]["value"][1])
    assert new_rows[0]["fields"]["tariff.periods.sale_price"]["value"] == Decimal("0.6")
    assert candidate["project"]["candidates"]["candidate-" + digest(original)] == original
    assert candidate["input_hash"] != old_export["input_hash"]
    assert new_atom["source_kind"] == "ASSUMPTION"


def test_d3_budget_rejects_full_original_before_any_candidate_directory(original):
    root, catalog, _, exported, _, _, _, _ = original
    with pytest.raises(ContractError):
        read_bundle(root / "original", catalog=catalog, budget=BundleBudget(max_rows=100))
    assert not (root / "budget-rejected").exists()


def test_wrong_generation_hash_cleans_only_the_owned_unpublished_run(original):
    from wangbin_solar_pv.calculation.break_even_replay import replay_price_candidate

    root, catalog, budget, exported, methods, control, _, _ = original
    bad = deepcopy(control)
    bad["generation_result_hash"] = "0" * 64
    original_manifest = root / "original" / "manifest.json"
    generation_result = root / "generation" / "result.json"
    originals = {path: hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in (original_manifest, generation_result)}
    sibling = root.parent / ("synthetic-p2-sibling-" + uuid4().hex)
    sibling.mkdir(mode=0o700)
    sentinel = sibling / "keep.txt"
    sentinel.write_text("SYNTHETIC independent task", encoding="utf-8")
    try:
        with read_bundle(root / "original", catalog=catalog, budget=budget) as bundle:
            with pytest.raises(ContractError):
                replay_price_candidate(bad, exported, methods, bundle, root / "generation", Decimal("0.6"),
                                       catalog=catalog, budget=budget, workspace=Workspace(root), run_name="wrong-3b")
        assert sentinel.read_text(encoding="utf-8") == "SYNTHETIC independent task"
    finally:
        sentinel.unlink()
        sibling.rmdir()
    assert not (root / "wrong-3b").exists()
    assert (root / "generation" / "result.json").is_file()
    assert (root / "original" / "manifest.json").is_file()
    assert all(hashlib.sha256(path.read_bytes()).hexdigest() == value for path, value in originals.items())


def test_future_price_row_with_no_settled_energy_does_not_publish_candidate(original):
    from wangbin_solar_pv.calculation.break_even_replay import replay_price_candidate

    root, catalog, budget, exported, methods, control, _, _ = original
    session = IntakeSession.from_dict(exported["project"], catalog)
    rows = session.project.values["tariff.periods"]["value"]
    end = rows[0]["fields"]["tariff.periods.effective_to"]
    end["value"] = end["original_value"] = "2029-12-31"
    rows.append(period_row(catalog, "future", first="2030-01-01", price=Decimal("0.4")))
    future_export = validate_export(session.export(), catalog).export
    future = rows[1]["fields"]["tariff.periods.sale_price"]
    control = deepcopy(control)
    control["selector"].update(row_id="future", field_instance_id=future["field_instance_id"],
                               original_atom_hash=digest(future))
    control["original_input_hash"] = future_export["input_hash"]
    control["original_source_snapshot_id"] = future_export["source_snapshot_id"]
    with read_bundle(root / "original", catalog=catalog, budget=budget) as original_bundle:
        datasets = {name: {"header": original_bundle.manifest["datasets"][name]["header"],
                           "rows": original_bundle.rows(name)} for name in original_bundle.dataset_ids}
        write_bundle(root / "original-future", base_export=future_export, datasets=datasets,
                     catalog=catalog, budget=budget)
    with read_bundle(root / "original-future", catalog=catalog, budget=budget) as future_bundle:
        control["original_dataset_content_hash"] = future_bundle.content_hash
        with pytest.raises(ContractError, match="BREAK_EVEN_PRICE_NOT_CONSUMED"):
            replay_price_candidate(control, future_export, methods, future_bundle, root / "generation", Decimal("0.6"),
                                   catalog=catalog, budget=budget, workspace=Workspace(root), run_name="unobserved")
    assert not (root / "unobserved").exists()
    assert (root / "original-future" / "manifest.json").is_file()


def test_market_8760_candidate_rebinds_only_selected_row(tmp_path):
    from test_phase3e_price_selector import _case
    from wangbin_solar_pv.calculation.break_even_execution import validate_price_selector
    from wangbin_solar_pv.calculation.break_even_replay import _derive, _rows, _verify_bundles

    catalog, exported, methods, control = _case(market=True)
    period = axis()
    budget = BundleBudget(max_seconds=1800)
    write_bundle(tmp_path / "market-original", base_export=exported,
                 datasets={"tariff.market_series": {"header": series_header(catalog, "tariff.market_series", period),
                                                      "rows": market_rows(catalog, period)}},
                 catalog=catalog, budget=budget)
    with read_bundle(tmp_path / "market-original", catalog=catalog, budget=budget) as original_bundle:
        first = next(original_bundle.rows("tariff.market_series"))
        old = first["fields"]["tariff.market_series.sale_price"]
        control["selector"].update(field_id="tariff.market_series.sale_price", row_id=first["row_id"],
                                   field_instance_id=old["field_instance_id"], original_atom_hash=digest(old),
                                   economic_basis=old["economic_basis"])
        control["original_dataset_content_hash"] = original_bundle.content_hash
        selected = validate_price_selector(control, exported, methods, original_bundle, catalog)
        candidate_export, candidate_atom = _derive(exported, selected, Decimal("0.6"), catalog)
        write_bundle(tmp_path / "market-derived", base_export=candidate_export,
                     datasets={"tariff.market_series": {
                         "header": original_bundle.manifest["datasets"]["tariff.market_series"]["header"],
                         "rows": _rows(original_bundle, "tariff.market_series", "tariff.market_series.sale_price",
                                       first["row_id"], candidate_atom)}},
                     catalog=catalog, budget=budget)
        with read_bundle(tmp_path / "market-derived", catalog=catalog, budget=budget) as derived:
            _verify_bundles(original_bundle, derived, "tariff.market_series.sale_price", first["row_id"])
            assert original_bundle.manifest["datasets"]["tariff.market_series"]["row_count"] == 8760
            assert derived.manifest["datasets"]["tariff.market_series"]["row_count"] == 8760
            assert derived.content_hash != original_bundle.content_hash
            assert (derived.manifest["datasets"]["tariff.market_series"]["canonical_array_hash"]
                    != original_bundle.manifest["datasets"]["tariff.market_series"]["canonical_array_hash"])
            updated = next(derived.rows("tariff.market_series"))["fields"]["tariff.market_series.sale_price"]
            assert updated["value"] == Decimal("0.6")
            assert updated["source_id"] == control["source"]["source_id"]
            assert next(derived.rows("tariff.market_series"))["row_id"] == first["row_id"]
            assert next(original_bundle.rows("tariff.market_series"))["fields"]["tariff.market_series.sale_price"] == old
