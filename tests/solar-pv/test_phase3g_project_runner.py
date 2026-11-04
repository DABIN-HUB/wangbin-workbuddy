"""Fast ingress checks for the unified Phase 3G project entry."""
from copy import deepcopy

import pytest

from test_phase3f_scenario_runner import _fixture
from wangbin_solar_pv.calculation.energy_yield import _metric
from wangbin_solar_pv.calculation.formula_execution import formula_execution_map
from wangbin_solar_pv.calculation.project_runner import run_project
from wangbin_solar_pv.calculation.result_contract import empty_result, seal_result
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.local_files import Workspace
from wangbin_solar_pv.serialization import digest
from wangbin_solar_pv.timeseries_bundle import BundleBudget


def test_project_requires_a_pinned_generation_pair_before_creating_output(tmp_path):
    catalog, export, methods = _fixture()
    with pytest.raises(ContractError) as blocked:
        run_project(export, methods, bundle_dir=tmp_path / "absent-d3",
                    catalog=catalog, budget=BundleBudget(), workspace=Workspace(tmp_path),
                    run_id="base", generation_dir=tmp_path / "absent-3b")
    assert blocked.value.code == "PROJECT_EXECUTION_CONTEXT"
    assert not (tmp_path / "base").exists()


def test_project_revalidates_source_before_entering_a_bundle(tmp_path):
    catalog, export, methods = _fixture()
    altered = deepcopy(export)
    altered["normalized_inputs"]["project.evaluation_years"] = 2
    with pytest.raises(ContractError) as rejected:
        run_project(altered, methods, bundle_dir=tmp_path / "absent-d3",
                    catalog=catalog, budget=BundleBudget(), workspace=Workspace(tmp_path),
                    run_id="tampered")
    assert rejected.value.code == "INPUT_EXPORT_INTEGRITY_MISMATCH"
    assert not (tmp_path / "tampered").exists()


def test_formula_map_distinguishes_old_placeholder_from_current_blocker():
    catalog, export, _ = _fixture()
    result = empty_result(project_id=export["project"]["project_id"],
                          pv_type=export["project"]["pv_type"],
                          evaluation_date="2026-01-01", currency="CNY", scenario_id="BASE",
                          input_hash="a", source_snapshot_id="b",
                          baseline_hashes=catalog.baseline_hashes,
                          definition_version=catalog.definition_version,
                          definition_hash=catalog.definition_hash)
    result["boundaries"]["PROJECT"] = {"phase": "3E"}
    _metric(result, catalog, "legacy.npv", None, "CNY", "F-NPV", "PROJECT", "LIFECYCLE",
            status="NOT_IMPLEMENTED", reason="OLDER_STAGE")
    _metric(result, catalog, "financial.phase3e.project_npv", None, "CNY", "F-NPV",
            "PROJECT", "LIFECYCLE", status="BLOCKED_MISSING_INPUT",
            reason="NO_TERMINAL_CASH")
    mapping = formula_execution_map(seal_result(result), catalog)
    by_id = {row["formula_id"]: row for row in mapping["formulas"]}
    assert len(by_id) == len(catalog.formulas)
    assert by_id["F-NPV"]["project_status"] == "BLOCKED_MISSING_INPUT"
    assert by_id["F-NPV"]["blocked_reasons"] == ["NO_TERMINAL_CASH"]
    assert by_id["F-BREAK-EVEN-PRICE"]["project_status"] != "CALCULATED"
    assert sum(mapping["project_counts"].values()) == len(catalog.formulas)
    assert mapping["mapping_hash"] == digest({k: v for k, v in mapping.items() if k != "mapping_hash"})
