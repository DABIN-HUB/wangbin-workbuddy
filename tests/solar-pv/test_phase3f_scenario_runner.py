"""Fast explicit Phase 3F scenario ingress checks (SYNTHETIC inputs only)."""
from copy import deepcopy
from decimal import Decimal as D

import pytest

from consumption_case_support import atom, case, extend, parameter
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.calculation.method_config import MethodConfig
from wangbin_solar_pv.calculation.scenario_runner import prepare_scenario, prepare_scenarios
from wangbin_solar_pv.calculation.sensitivity import scenario_calculation_graph
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.serialization import digest, dumps

SOURCE = {"source_id": "SYNTHETIC:scenario-user", "source_reference": "SYNTHETIC:declared-case",
          "source_kind": "SYNTHETIC", "status": "ASSUMED", "license_status": "AUTHORIZED"}


def _fixture():
    catalog = Catalog()
    session, methods = case(catalog, "utility_scale_ground", years=1)
    session, methods = extend(session, methods)
    rate = atom(catalog, "finance.project_discount_rate", D("0.1"))
    rate["source_section_or_cell"] = "PROJECT_POST_TAX_NOMINAL_CNY_YEAR_END"
    session.project.values["finance.project_discount_rate"] = rate
    session.project.values["finance.loan_rate"] = atom(catalog, "finance.loan_rate", D("0.05"))
    session.project.values["finance.debt_ratio"] = atom(catalog, "finance.debt_ratio", D("0.5"))
    return catalog, session.export(), methods


def _control(export, methods, *, sid="PESSIMISTIC", rid="case-one", changes=None):
    return {"scenario_id": sid, "run_id": rid, "project_id": export["project"]["project_id"],
            "pv_type": export["project"]["pv_type"], "original_input_hash": export["input_hash"],
            "original_source_snapshot_id": export["source_snapshot_id"],
            "method_config_hash": methods.hash, "changes": [] if changes is None else changes}


def _input(export, factor, fid, value, row_id=None):
    old = export["project"]["values"][fid] if row_id is None else next(
        r["fields"][fid] for r in export["project"]["values"][fid.rsplit(".", 1)[0]]["value"]
        if r["row_id"] == row_id)
    return {"factor": factor, "target_kind": "INPUT",
            "selector": {"field_id": fid, "row_id": row_id,
                         "field_instance_id": old["field_instance_id"], "original_atom_hash": digest(old)},
            "value": value, "source": deepcopy(SOURCE)}


def test_explicit_three_cases_are_isolated_and_hashable():
    catalog, export, methods = _fixture()
    before = dumps(export), dumps(methods.to_dict())
    low = _input(export, "SALE_PRICE", "tariff.periods.sale_price", D("0.35"), "flat")
    high = _input(export, "SALE_PRICE", "tariff.periods.sale_price", D("0.55"), "flat")
    controls = [_control(export, methods, sid="BASE", rid="base"),
                _control(export, methods, rid="down", changes=[low]),
                _control(export, methods, sid="OPTIMISTIC", rid="up", changes=[high])]
    cases = prepare_scenarios(controls, export, methods, catalog)
    assert (dumps(export), dumps(methods.to_dict())) == before
    assert cases["BASE"].input_export["input_hash"] == export["input_hash"]
    assert len({r.scenario_hash for r in cases.values()}) == 3
    assert len({r.input_export["input_hash"] for r in cases.values()}) == 3
    item = cases["PESSIMISTIC"]
    assert item.input_export["project"]["values"]["tariff.periods"]["value"][0]["fields"]["tariff.periods.sale_price"]["value"] == D("0.35")
    assert item.input_export["source_snapshot_id"] != export["source_snapshot_id"]
    assert "SALE_PRICE" not in item.changed_field_ids  # field IDs, never factor names
    assert item.changed_field_ids == ("tariff.periods.sale_price",)


def test_method_control_is_independent_of_input_and_consumer_graph():
    catalog, export, methods = _fixture()
    old = methods.to_dict()["parameters"]["energy.pr"] if "energy.pr" in methods.to_dict()["parameters"] else None
    config = methods.to_dict()
    config["parameters"].update({"energy.method": parameter("energy.method", "POA_PR"),
                                 "energy.pr": parameter("energy.pr", D("0.7"))})
    methods = MethodConfig.from_dict(config)
    change = {"factor": "GENERATION", "target_kind": "METHOD",
              "selector": {"parameter_id": "energy.pr", "original_parameter_hash": digest(methods.to_dict()["parameters"]["energy.pr"])},
              "value": D("0.8"), "source": deepcopy(SOURCE)}
    prepared = prepare_scenario(_control(export, methods, changes=[change]), export, methods, catalog)
    assert prepared.methods.require("energy.pr") == D("0.8")
    assert prepared.input_export["normalized_inputs"] == export["normalized_inputs"]
    assert prepared.changed_method_ids == ("energy.pr",)
    graph = scenario_calculation_graph(catalog, "utility_scale_ground", prepared.methods)
    assert graph.affected_by(method_parameter_ids=["energy.pr"]) == ["3B", "3C", "3D", "3E"]
    assert graph.affected_by(["finance.project_discount_rate"]) == ["3E"]
    assert old is None or methods.to_dict()["parameters"]["energy.pr"] == old


def test_wrong_row_source_and_unconsumed_factor_are_rejected():
    catalog, export, methods = _fixture()
    change = _input(export, "SALE_PRICE", "tariff.periods.sale_price", D("0.3"), "flat")
    for mutate in (
        lambda c: c["selector"].update(row_id="nonexistent"),
        lambda c: c["selector"].update(original_atom_hash="0"*64),
        lambda c: c["source"].update(license_status="UNKNOWN"),
        lambda c: c.update(factor="SELF_USE_RATIO"),
        lambda c: c.update(value="not a numeric price"),
    ):
        bad = deepcopy(change)
        mutate(bad)
        with pytest.raises(ContractError):
            prepare_scenario(_control(export, methods, changes=[bad]), export, methods, catalog)
    original = deepcopy(export)
    original["project"]["values"]["tariff.periods"]["value"].append(
        deepcopy(original["project"]["values"]["tariff.periods"]["value"][0]))
    with pytest.raises(ContractError):
        prepare_scenario(_control(export, methods, changes=[change]), original, methods, catalog)


def test_loan_rate_and_discount_rate_are_bound_to_different_stages():
    catalog, export, methods = _fixture()
    graph = scenario_calculation_graph(catalog, "utility_scale_ground", methods)
    assert graph.affected_by(["finance.loan_rate"]) == ["3D", "3E"]
    assert graph.affected_by(["tariff.periods.sale_price"]) == ["3C", "3D", "3E"]
    for factor, fid, value in (("LOAN_INTEREST", "finance.loan_rate", D("0.07")),
                               ("PROJECT_DISCOUNT", "finance.project_discount_rate", D("0.12"))):
        prepared = prepare_scenario(_control(export, methods, changes=[_input(export, factor, fid, value)]), export, methods, catalog)
        assert prepared.input_export["project"]["values"][fid]["value"] == value
        assert prepared.input_export["project"]["values"][fid]["source_id"] == SOURCE["source_id"]
