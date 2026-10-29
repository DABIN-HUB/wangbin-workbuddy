from decimal import Decimal

import pytest

from wangbin_solar_pv.calculation.common import calculated
from wangbin_solar_pv.calculation.losses import loss_ledger
from wangbin_solar_pv.calculation.method_config import MethodConfig, make_parameter
from wangbin_solar_pv.calculation.temperature import cell_temperature, prepare_temperature
from wangbin_solar_pv.errors import ContractError


D = Decimal


def parameter(parameter_id, value, *, status="ASSUMED", source_kind="SYNTHETIC", source_reference=None):
    return make_parameter(
        parameter_id,
        value,
        source_id=f"SYNTHETIC:{parameter_id}",
        source_reference=source_reference or f"SYNTHETIC declared {parameter_id}",
        status=status,
        source_kind=source_kind,
    )


def methods(**values):
    parameters = {
        "precision.digits": parameter("precision.digits", 80),
        "thermal.method": parameter("thermal.method", "SANDIA"),
        "thermal.a": parameter("thermal.a", D("0")),
        "thermal.b": parameter("thermal.b", D("0")),
        "thermal.delta_temperature": parameter("thermal.delta_temperature", D("3")),
        "thermal.minimum_cell_temperature": parameter("thermal.minimum_cell_temperature", D("-40")),
        "thermal.maximum_cell_temperature": parameter("thermal.maximum_cell_temperature", D("120")),
        "constants.stc_irradiance": parameter("constants.stc_irradiance", D("1")),
    }
    parameters.update({key: parameter(key, value) for key, value in values.items()})
    return MethodConfig.from_dict({
        "schema_version": "solar-pv-method-config/1.0.0",
        "config_id": "SYNTHETIC-TEMP",
        "data_mode": "SYNTHETIC",
        "pv_types": ["industrial_rooftop"],
        "parameters": parameters,
    })


def loss(kind, rate, *, sequence, boundary="DC", loss_id=None, source_ids=("SYNTHETIC:loss",), included=False):
    return {
        "id": loss_id or kind,
        "kind": kind,
        "rate": rate,
        "sequence": sequence,
        "boundary": boundary,
        "included_in_source": included,
        "source_ids": list(source_ids),
    }


def test_sandia_temperature_uses_exact_decimal_equation_and_exp_zero_reference():
    result = cell_temperature(D("0.001"), D("25"), D("0"), methods=methods())
    assert result == calculated(D("26.003"), details=result["details"])
    assert result["details"]["module_temp"] == D("26")
    assert result["details"]["method"] == "SANDIA"
    assert "thermal.a" in result["details"]["parameter_ids"]
    assert result["details"]["source_refs"]["thermal.a"] == "SYNTHETIC declared thermal.a"


def test_zero_irradiance_is_a_real_nighttime_model_case():
    low = cell_temperature(D("0"), D("-20"), D("4"), methods=methods())
    high = cell_temperature(D("0"), D("80"), D("4"), methods=methods())
    assert low["value"] == D("-20")
    assert high["value"] == D("80")
    assert low["details"]["module_temp"] == D("-20")


def test_prepared_temperature_reuses_immutable_snapshot_and_does_not_hold_config():
    prepared = prepare_temperature(methods())
    methods().to_dict()["parameters"]["thermal.a"]["value"] = D("-9")
    result = prepared.evaluate(D("0"), D("25"), D("1"))
    metadata = prepared.metadata
    metadata["parameter_ids"].append("forged")
    assert result["value"] == D("25")
    assert "forged" not in prepared.metadata["parameter_ids"]
    assert not hasattr(prepared, "methods")


def test_supplied_cell_temperature_never_uses_ambient_as_cell():
    config = methods(**{"thermal.method": "CELL_TEMPERATURE_SUPPLIED"})
    # CELL_TEMPERATURE_SUPPLIED is method-only; the model parameters are not read.
    result = cell_temperature(D("0"), D("25"), D("5"), methods=config, supplied_cell_c=D("42"))
    assert result["value"] == D("42")
    assert result["details"]["module_temp"] is None


def test_not_required_pr_is_not_a_time_temperature_model():
    config = methods(**{"thermal.method": "NOT_REQUIRED_PR"})
    result = cell_temperature(D("0"), D("25"), D("5"), methods=config)
    assert result["status"] == "NOT_APPLICABLE"
    assert result["value"] is None


@pytest.mark.parametrize("poa,ambient,wind", [
    (D("-0.1"), D("25"), D("1")),
    (D("0.1"), D("-273.16"), D("1")),
    (D("0.1"), D("25"), D("-1")),
    (0.1, D("25"), D("1")),
])
def test_temperature_rejects_negative_absolute_zero_wind_and_float_inputs(poa, ambient, wind):
    with pytest.raises(ContractError):
        cell_temperature(poa, ambient, wind, methods=methods())


def test_temperature_rejects_model_domain_and_missing_or_unreviewed_parameters():
    with pytest.raises(ContractError, match="THERMAL_MODEL_TEMPERATURE_DOMAIN"):
        cell_temperature(D("2"), D("25"), D("1"), methods=methods(**{"thermal.maximum_cell_temperature": D("26")}))
    constrained = methods()
    constrained_data = constrained.to_dict()
    constrained_data["parameters"]["thermal.maximum_cell_temperature"]["value"] = D("26")
    constrained_data["parameters"]["thermal.maximum_cell_temperature"]["source_kind"] = "DOCUMENT_EXTRACTED"
    constrained_data["parameters"]["thermal.maximum_cell_temperature"]["source_id"] = "P3-METHOD-SANDIA-MODULE"
    constrained_data["parameters"]["thermal.maximum_cell_temperature"]["source_reference"] = "P3-METHOD-SANDIA-MODULE"
    constrained = MethodConfig.from_dict(constrained_data)
    with pytest.raises(ContractError, match="THERMAL_MODEL_TEMPERATURE_DOMAIN"):
        cell_temperature(D("2"), D("25"), D("1"), methods=constrained)
    incomplete = methods()
    data = incomplete.to_dict()
    del data["parameters"]["thermal.b"]
    with pytest.raises(ContractError, match="BLOCKED_METHOD_REVIEW"):
        cell_temperature(D("0.1"), D("25"), D("1"), methods=MethodConfig.from_dict(data))
    unreviewed = methods()
    data = unreviewed.to_dict()
    data["parameters"]["thermal.a"]["status"] = "UNVERIFIED"
    data["parameters"]["thermal.a"]["source_kind"] = "DOCUMENT_EXTRACTED"
    data["parameters"]["thermal.a"]["source_id"] = "P3-METHOD-SANDIA-MODULE"
    data["parameters"]["thermal.a"]["source_reference"] = "P3-METHOD-SANDIA-MODULE"
    unreviewed = MethodConfig.from_dict(data)
    with pytest.raises(ContractError, match="BLOCKED_METHOD_REVIEW"):
        prepare_temperature(unreviewed)


def test_temperature_rejects_private_or_invalid_parameter_source():
    data = methods().to_dict()
    data["parameters"]["thermal.a"]["source_reference"] = "file:///private/model.csv"
    with pytest.raises(ContractError, match="PRIVATE_PATH_REFERENCE"):
        MethodConfig.from_dict(data)


def test_loss_ledger_applies_source_ordered_multiplication_and_conserves_energy():
    records = [
        loss("soiling", D("0.10"), sequence=2),
        loss("shading", D("0.20"), sequence=1),
    ]
    result = loss_ledger(D("100"), records, boundary="DC")
    assert result["status"] == "CALCULATED"
    assert [row["loss_id"] for row in result["details"]["items"]] == ["shading", "soiling"]
    assert result["details"]["items"][0]["before"] == D("100")
    assert result["details"]["items"][0]["after"] == D("80.00")
    assert result["details"]["items"][1]["after"] == D("72.0000")
    assert result["value"] == D("72.0000")
    assert sum((row["lost"] for row in result["details"]["items"]), D("0")) + result["value"] == D("100")


def test_loss_ledger_preserves_frozen_kind_sequence_and_supports_each_boundary():
    for boundary, kind in [("DC", "dc_cable"), ("AC", "ac_cable"), ("GRID", "export_line")]:
        result = loss_ledger(D("10"), [loss(kind, D("0.1"), sequence=7, boundary=boundary)], boundary=boundary)
        row = result["details"]["items"][0]
        assert row["kind"] == kind
        assert row["sequence"] == 7
        assert row["boundary"] == boundary
        assert row["source_ids"] == ["SYNTHETIC:loss"]


def test_loss_ledger_accepts_zero_energy_but_rejects_unknown_or_missing_evidence():
    result = loss_ledger(D("0"), [loss("temperature", D("0.5"), sequence=1)], boundary="DC")
    assert result["value"] == D("0")
    with pytest.raises(ContractError):
        loss_ledger(D("10"), [loss("not_a_frozen_kind", D("0.1"), sequence=1)], boundary="DC")
    with pytest.raises(ContractError):
        loss_ledger(D("10"), [loss("temperature", D("0.1"), sequence=1, source_ids=())], boundary="DC")


@pytest.mark.parametrize("bad", [
    [loss("temperature", D("-0.1"), sequence=1)],
    [loss("temperature", D("1.1"), sequence=1)],
    [loss("temperature", D("0.1"), sequence=1, boundary="AC")],
    [loss("temperature", D("0.1"), sequence=1, included=True)],
    [loss("temperature", D("0.1"), sequence=1), loss("temperature", D("0.2"), sequence=2)],
])
def test_loss_ledger_rejects_invalid_rates_wrong_boundaries_inclusion_and_duplicate_ids(bad):
    with pytest.raises(ContractError):
        loss_ledger(D("10"), bad, boundary="DC", upstream_included=("temperature",))


def test_loss_ledger_rejects_upstream_duplicate_deduction_and_keeps_unknown_out_of_zero():
    with pytest.raises(ContractError, match="LOSS_ALREADY_INCLUDED"):
        loss_ledger(D("10"), [loss("temperature", D("0.1"), sequence=1)], boundary="DC", upstream_included=("temperature",))
    with pytest.raises(ContractError):
        loss_ledger(D("10"), [loss("temperature", D("0.1"), sequence=1)], boundary="DC", digits=33)
