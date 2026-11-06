"""M04 uses the frozen, sourced resource-monthly inputs rather than energy output."""
from pathlib import Path

import pytest

from wangbin_solar_pv.report_export import ReportModel, _sheet_data
from wangbin_solar_pv.serialization import loads

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("category", ["industrial_rooftop", "utility_scale_ground"])
def test_full_case_resource_monthly_is_bound_and_separate_from_generation(category):
    path = ROOT / "reports/solar-pv/phase7l-r1-full-cases" / category / "project/canonical.json"
    result = loads(path.read_bytes())
    metrics = tuple(result["results"]["metrics"])
    model = ReportModel(result, metrics, {metric["metric_id"]: metric for metric in metrics})
    headers, resource = _sheet_data(model, "M04", "资源月度", category)
    _, generation = _sheet_data(model, "M06", "发电预测-月度", category)
    assert len(resource) == len(generation) == 12
    assert [row[0] for row in resource] == list(range(1, 13))
    assert headers[1:5] == ["GHI (kWh/㎡)", "DNI (kWh/㎡)", "DHI (kWh/㎡)", "POA (kWh/㎡)"]
    first = result["inputs"]["normalized"]["resource.monthly"][0]["fields"]
    assert resource[0][1] == first["resource.monthly.ghi"]
    assert resource[0][4] == first["resource.monthly.poa"]
    assert resource[0][5] == first["resource.monthly.ambient_temperature"]
    assert resource[0][6] == first["resource.monthly.wind_speed"]
    assert "SYNTHETIC-PHASE7L-" in resource[0][-1]
    assert resource[0][2] != generation[0][1]
    assert generation[0][2] == "energy.monthly.year.1"
    result["source_snapshot"]["phase2"]["records"] = []
    _, unbound = _sheet_data(model, "M04", "资源月度", category)
    assert len(unbound) == 1 and unbound[0][1] == "UNKNOWN"
