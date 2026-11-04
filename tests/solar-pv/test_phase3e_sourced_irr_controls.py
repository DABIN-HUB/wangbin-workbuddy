"""Fast sourced IRR control and canonical-result checks; no full replay."""
from decimal import Decimal as D

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.calculation.method_config import MethodConfig, make_parameter
from wangbin_solar_pv.calculation.phase3e import _BOUNDARY, _metric, _record_sourced_project_irr
from wangbin_solar_pv.calculation.result_contract import empty_result, seal_result, validate_result
from wangbin_solar_pv.serialization import digest


IRR = {
    "irr.method": "EXACT_RATIONAL_POLYNOMIAL_ISOLATION",
    "irr.minimum_rate": D("0"),
    "irr.maximum_rate": D("1"),
    "irr.root_tolerance": D("0.000000000001"),
    "irr.maximum_degree": 2,
}


def _methods(values, *, unreviewed=None):
    parameters = {}
    for parameter_id, value in values.items():
        parameters[parameter_id] = make_parameter(
            parameter_id, value, source_id=f"SYNTHETIC:{parameter_id}",
            source_reference="SYNTHETIC explicitly declared IRR control",
            source_kind="USER_PROVIDED" if parameter_id == unreviewed else "SYNTHETIC",
            status="UNVERIFIED" if parameter_id == unreviewed else "ASSUMED",
            license_status="REQUIRES_REVIEW" if parameter_id == unreviewed else "AUTHORIZED",
            pv_types=["industrial_rooftop"],
        )
    return MethodConfig.from_dict({
        "schema_version": "solar-pv-method-config/1.0.0",
        "config_id": "SYNTHETIC-IRR-CONTROLS", "data_mode": "SYNTHETIC",
        "pv_types": ["industrial_rooftop"], "parameters": parameters,
    })


def _result(catalog, methods):
    result = empty_result(
        project_id="SYNTHETIC-IRR", pv_type="industrial_rooftop",
        evaluation_date="2025-12-31", currency="CNY", scenario_id="BASE",
        input_hash="pending", source_snapshot_id="pending",
        baseline_hashes=catalog.baseline_hashes,
        definition_version=catalog.definition_version, definition_hash=catalog.definition_hash,
    )
    result["source_snapshot"] = {"methods": methods.to_dict()}
    result["source_snapshot_id"] = digest(result["source_snapshot"])
    result["inputs"].update(identity_payload={"source_snapshot_id": result["source_snapshot_id"]},
                            used_sources=[], used_fields=[])
    result["input_hash"] = digest(result["inputs"]["identity_payload"])
    result["boundaries"][_BOUNDARY] = {"phase": "3E"}
    result["maturity"]["calculation"] = "PARTIAL"
    result["status"] = "PARTIAL"
    _metric(result, catalog, "financial.phase3e.project_irr", "F-IRR-PROJECT", None,
            "1", "2_PERIODS", status="BLOCKED_MISSING_INPUT",
            reason="BLOCKED_UPSTREAM_PROJECT_CASH_FLOW")
    return result


def _calculate(values, cash, *, unreviewed=None):
    catalog = Catalog()
    methods = _methods(values, unreviewed=unreviewed)
    result = _result(catalog, methods)
    _record_sourced_project_irr(result, catalog, methods, cash, f"{len(cash)}_PERIODS")
    validate_result(seal_result(result), catalog)
    return next(metric for metric in result["results"]["metrics"]
                if metric["metric_id"] == "financial.phase3e.project_irr")


def test_missing_or_partial_irr_controls_block_without_default_rate():
    cash = [D("-100"), D("110")]
    for values in ({}, {"irr.minimum_rate": D("0")}):
        metric = _calculate(values, cash)
        assert metric["status"] == "BLOCKED_MISSING_INPUT" and metric["value"] is None
        assert metric["reason"] == "IRR_METHOD_CONTROLS_INCOMPLETE"
        assert set(metric["details"]["missing_method_parameter_ids"]) == set(IRR) - set(values)


def test_unreviewed_irr_control_and_degree_budget_do_not_calculate():
    unreviewed = _calculate(IRR, [D("-100"), D("110")], unreviewed="irr.root_tolerance")
    assert unreviewed["status"] == "BLOCKED_METHOD_REVIEW"
    assert unreviewed["value"] is None
    assert unreviewed["details"]["unreviewed_method_parameter_ids"] == ["irr.root_tolerance"]
    budget = _calculate({**IRR, "irr.maximum_degree": 1},
                        [D("-100"), D("60"), D("60")])
    assert budget["status"] == "BLOCKED_METHOD_REVIEW"
    assert budget["reason"] == "IRR_DEGREE_BUDGET" and budget["value"] is None


def test_sourced_irr_calculates_only_with_complete_declared_domain():
    metric = _calculate(IRR, [D("-100"), D("110")])
    assert metric["status"] == "CALCULATED"
    assert abs(metric["value"] - D("0.1")) < IRR["irr.root_tolerance"]
    assert metric["details"]["domain"] == {"minimum": D("0"), "maximum": D("1")}
    assert metric["details"]["root_count"] == 1
    assert set(IRR) <= set(metric["method_parameter_ids"])
    assert set(metric["source_ids"]) == {f"SYNTHETIC:{parameter_id}" for parameter_id in IRR}
    multiple = _calculate(IRR, [D("-100"), D("230"), D("-132")])
    assert multiple["status"] == "UNDEFINED" and multiple["value"] is None
    assert multiple["reason"] == "MULTIPLE_ROOTS"
    assert multiple["details"]["root_count"] == 2
