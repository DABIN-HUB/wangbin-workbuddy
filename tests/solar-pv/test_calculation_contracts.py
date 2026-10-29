"""SYNTHETIC Phase3A input, explicit-method and numerical-result contracts."""
from copy import deepcopy
from decimal import Decimal

import pytest

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.intake import IntakeSession


def exports():
    catalog = Catalog()
    return catalog, IntakeSession.new("SYNTHETIC-CONTRACT", "industrial_rooftop", catalog).export()


def test_public_calculation_input_revalidates_original_phase2_export():
    from wangbin_solar_pv.calculation.input_contract import validate_export
    catalog, exported = exports()
    accepted = validate_export(exported, catalog)
    assert accepted.phase2_input_hash == exported["input_hash"]
    assert accepted.project.project_id == "SYNTHETIC-CONTRACT"
    assert accepted.export == exported


def test_calculation_input_accepts_canonical_json_roundtrip_without_changing_identity():
    from wangbin_solar_pv.calculation.input_contract import validate_export
    from wangbin_solar_pv.serialization import dumps, loads
    catalog, exported = exports()
    session = IntakeSession.from_dict(exported["project"], catalog)
    session.submit("SYNTHETIC-ORDER", [{"field_id": "project.name", "value": "SYNTHETIC canonical roundtrip"}], expected_revision=0)
    exported = session.export()
    accepted = validate_export(loads(dumps(exported)), catalog)
    assert accepted.phase2_input_hash == exported["input_hash"]
    assert accepted.phase2_source_snapshot_id == exported["source_snapshot_id"]


def test_composite_identity_revalidates_mutable_wrappers_at_public_boundary():
    from wangbin_solar_pv.calculation.input_contract import validate_export, calculation_identity
    from wangbin_solar_pv.calculation.method_config import MethodConfig
    catalog, exported = exports()
    validated = validate_export(exported, catalog)
    methods = MethodConfig.from_dict({"schema_version": "solar-pv-method-config/1.0.0", "config_id": "SYNTHETIC", "data_mode": "SYNTHETIC", "pv_types": ["industrial_rooftop"], "parameters": {}})
    validated.project.project_id = "SYNTHETIC-MUTATED"
    with pytest.raises(ContractError):
        calculation_identity(validated, methods, catalog)
    forged = MethodConfig({**methods.to_dict(), "unexpected": "SYNTHETIC"})
    with pytest.raises(ContractError):
        calculation_identity(validate_export(exported, catalog), forged, catalog)


@pytest.mark.parametrize("key", ["schema_version", "input_hash", "source_snapshot_id", "normalized_inputs", "provenance_records", "source_snapshot", "scenario_config", "input_maturity", "calculation_status", "result_contract_status", "input_module_version"])
def test_public_calculation_input_rejects_every_forged_derived_export_member(key):
    from wangbin_solar_pv.calculation.input_contract import validate_export
    catalog, exported = exports()
    exported[key] = "SYNTHETIC-FORGED"
    with pytest.raises(ContractError):
        validate_export(exported, catalog)


def test_public_calculation_input_rejects_forged_field_even_with_regenerated_export_hash():
    from wangbin_solar_pv.calculation.input_contract import validate_export
    catalog, exported = exports()
    exported["project"]["values"]["project.pv_type"]["status"] = "VERIFIED"
    with pytest.raises(ContractError):
        validate_export(exported, catalog)


def test_method_configuration_never_creates_default_values():
    from wangbin_solar_pv.calculation.method_config import MethodConfig, make_parameter
    parameter = make_parameter("precision.digits", 80, source_id="SYNTHETIC:precision", source_reference="SYNTHETIC declared numerical policy", status="ASSUMED", source_kind="SYNTHETIC")
    config = MethodConfig.from_dict({"schema_version": "solar-pv-method-config/1.0.0", "config_id": "SYNTHETIC-METHOD", "data_mode": "SYNTHETIC", "pv_types": ["industrial_rooftop"], "parameters": {"precision.digits": parameter}})
    assert config.require("precision.digits") == 80
    with pytest.raises(ContractError, match="BLOCKED_METHOD_REVIEW"):
        config.require("thermal.a")
    assert config.to_dict()["parameters"].keys() == {"precision.digits"}


@pytest.mark.parametrize("key,value", [("value", True), ("value", 12), ("unit", "currency"), ("status", "UNKNOWN"), ("value_type", "string"), ("meaning_zh", ""), ("english_name", ""), ("version", "99.0.0"), ("source_id", None), ("source_reference", ""), ("boundary_id", ""), ("unexpected", 1)])
def test_parameter_metadata_and_value_are_strictly_validated(key, value):
    from wangbin_solar_pv.calculation.method_config import MethodConfig, make_parameter
    parameter = make_parameter("precision.digits", 80, source_id="SYNTHETIC:precision", source_reference="SYNTHETIC declared numerical policy", status="ASSUMED", source_kind="SYNTHETIC")
    parameter[key] = value
    with pytest.raises(ContractError):
        MethodConfig.from_dict({"schema_version": "solar-pv-method-config/1.0.0", "config_id": "SYNTHETIC-METHOD", "data_mode": "SYNTHETIC", "pv_types": ["industrial_rooftop"], "parameters": {"precision.digits": parameter}})


def test_methods_and_their_evidence_change_composite_input_identity():
    from wangbin_solar_pv.calculation.method_config import MethodConfig, make_parameter
    from wangbin_solar_pv.calculation.input_contract import validate_export, calculation_identity
    catalog, exported = exports()
    p = make_parameter("precision.digits", 80, source_id="SYNTHETIC:precision", source_reference="SYNTHETIC declared numerical policy", status="ASSUMED", source_kind="SYNTHETIC")
    data = {"schema_version": "solar-pv-method-config/1.0.0", "config_id": "SYNTHETIC-METHOD", "data_mode": "SYNTHETIC", "pv_types": ["industrial_rooftop"], "parameters": {"precision.digits": p}}
    first = calculation_identity(validate_export(exported, catalog), MethodConfig.from_dict(data), catalog)
    data["parameters"]["precision.digits"]["source_reference"] += " revision"
    second = calculation_identity(validate_export(exported, catalog), MethodConfig.from_dict(data), catalog)
    assert first["input_hash"] != second["input_hash"]
    assert first["source_snapshot_id"] != second["source_snapshot_id"]
    assert first["phase2_input_hash"] == second["phase2_input_hash"] == exported["input_hash"]


def test_local_precision_is_independent_of_ambient_decimal_context():
    from decimal import localcontext
    from wangbin_solar_pv.calculation.common import number, precision_context
    assert number(Decimal("1.2345678901234567890123456789")) == Decimal("1.2345678901234567890123456789")
    with localcontext() as ambient:
        ambient.prec = 5
        with precision_context(80):
            assert Decimal(1) / Decimal(3) == Decimal("0." + "3" * 80)
        assert ambient.prec == 5
    for invalid in [True, "1.2", 0.1, Decimal("NaN"), Decimal("Infinity")]:
        with pytest.raises(ContractError):
            number(invalid)


def test_result_contract_has_all_frozen_roots_and_reproducible_hash():
    from wangbin_solar_pv.calculation.result_contract import seal_result, validate_result, result_schema, empty_result
    from wangbin_solar_pv.serialization import dumps, loads
    catalog, exported = exports()
    result = empty_result(project_id="SYNTHETIC-CONTRACT", pv_type="industrial_rooftop", evaluation_date="2026-01-01", currency="CNY", scenario_id="SYNTHETIC-BASE", input_hash=exported["input_hash"], source_snapshot_id=exported["source_snapshot_id"], baseline_hashes=catalog.baseline_hashes, definition_version=catalog.definition_version, definition_hash=catalog.definition_hash)
    required = set("schema_version model_version run_id input_hash source_snapshot_id result_hash project_id pv_type scenario_id created_at evaluation_date currency maturity status boundaries inputs source_snapshot formula_snapshot results findings evidence artifact_manifest".split())
    assert required <= set(result)
    assert required <= set(result_schema()["required"])
    validate_result(result, catalog)
    second = deepcopy(result)
    second.update(run_id="different-run", created_at="2026-01-02T00:00:00+00:00", artifact_manifest=[{"status": "NOT_IMPLEMENTED"}])
    assert seal_result(second)["result_hash"] == result["result_hash"]
    assert loads(dumps(result)) == result
    second["scenario_id"] = "SYNTHETIC-CHANGED"
    assert seal_result(second)["result_hash"] != result["result_hash"]
    result["inputs"]["forged"] = Decimal(123)
    with pytest.raises(ContractError, match="RESULT_HASH_MISMATCH"):
        validate_result(result, catalog)


def test_registry_preserves_89_definitions_without_pretending_numerical_implementation():
    from wangbin_solar_pv.calculation.execution_registry import execution_inventory
    catalog = Catalog()
    inventory = execution_inventory(catalog)
    assert len(inventory) == 89
    assert len({r["formula_id"] for r in inventory}) == 89
    assert sum(r["phase3_applicable"] for r in inventory) == 82
    assert sum(not r["phase3_applicable"] for r in inventory) == 7
    for row in inventory:
        assert row["definition"]["text_equation"] == catalog.formulas[row["formula_id"]]["text_equation"]
        assert row["definition_version"] == catalog.definition_version
        if row["evidence"] is None:
            assert row["status"] == "NOT_IMPLEMENTED"
            assert row["numerical_validation_status"] == "NOT_TESTED"
        else:
            assert row["status"] == "IMPLEMENTED_TESTED"
            assert row["executor"] is not None
            assert row["evidence"]["test_ids"] and row["evidence"]["evidence_ids"]
            assert row["evidence"]["definition_hash"] == catalog.definition_hash
        if not row["phase3_applicable"]:
            assert row["executor"] is None and row["status"] == "NOT_IMPLEMENTED"


@pytest.mark.parametrize("gate", ["real_project", "four_files", "platform"])
def test_phase3_result_schema_cannot_promote_deferred_release_gates(gate):
    from wangbin_solar_pv.calculation.result_contract import empty_result, result_schema
    from wangbin_solar_pv.schemas import StrictValidator
    result = empty_result(project_id="SYNTHETIC-SCHEMA-ONLY", pv_type="industrial_rooftop", evaluation_date="2026-01-01", currency="CNY", scenario_id="SYNTHETIC", input_hash="SYNTHETIC-NONEXECUTED", source_snapshot_id="SYNTHETIC-NONEXECUTED", baseline_hashes={}, definition_version="SYNTHETIC-SCHEMA-ONLY", definition_hash="0" * 64)
    assert StrictValidator(result_schema()).is_valid(result)
    result["maturity"][gate] = "PASS"
    assert not StrictValidator(result_schema()).is_valid(result)
