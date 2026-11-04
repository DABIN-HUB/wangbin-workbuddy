"""Fast ingress checks for the unified Phase 3G project entry."""
from copy import deepcopy

import pytest

from test_phase3f_scenario_runner import _fixture
from wangbin_solar_pv.calculation.project_runner import run_project
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.local_files import Workspace
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
