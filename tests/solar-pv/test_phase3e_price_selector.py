"""SYNTHETIC-only controlled price selection; no real project or cash-flow claims."""
from copy import deepcopy
from decimal import Decimal
import importlib

import pytest

from consumption_case_support import atom, axis, case, extend, market_rows, parameter, series_header
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.calculation.method_config import MethodConfig
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.serialization import digest
from wangbin_solar_pv.timeseries_bundle import BundleBudget, read_bundle, write_bundle


def _selector_module():
    try:
        return importlib.import_module("wangbin_solar_pv.calculation.break_even_execution")
    except ModuleNotFoundError:
        pytest.fail("P2-1 break_even_execution implementation is absent")


def _case(category="utility_scale_ground", *, ppa=None, market=False, field_id="tariff.periods.sale_price"):
    catalog = Catalog()
    session, upstream = case(catalog, category, years=1)
    session, methods = extend(session, upstream, ppa=ppa, market=market)
    session.project.values["project.cashflow_tax_basis"] = atom(catalog, "project.cashflow_tax_basis", "post_tax")
    if "project.ownership_mode" not in session.project.values:
        session.project.values["project.ownership_mode"] = atom(catalog, "project.ownership_mode", "owner_invested")
    data = methods.to_dict()
    data["parameters"].update({
        "break_even.minimum_price": parameter("break_even.minimum_price", Decimal("0")),
        "break_even.maximum_price": parameter("break_even.maximum_price", Decimal("2")),
        "break_even.price_tolerance": parameter("break_even.price_tolerance", Decimal("1e-8")),
        "break_even.maximum_iterations": parameter("break_even.maximum_iterations", 256),
        "break_even.method": parameter("break_even.method", "CERTIFIED_MONOTONE_RECALCULATION"),
    })
    methods = MethodConfig.from_dict(data)
    exported = session.export()
    row = exported["project"]["values"]["tariff.periods"]["value"][0]
    original = (exported["project"]["values"]["tariff.ppa_price"] if field_id == "tariff.ppa_price"
                else row["fields"][field_id])
    control = {
        "schema_version": "solar-pv-break-even-execution/1.0.0",
        "project_id": exported["project"]["project_id"], "pv_type": category,
        "formula_id": "F-BREAK-EVEN-PRICE",
        "selector": {"field_id": field_id, "row_id": None if field_id == "tariff.ppa_price" else row["row_id"],
                     "field_instance_id": original["field_instance_id"],
                     "original_atom_hash": digest(original), "unit": original["unit"],
                     "economic_basis": deepcopy(original["economic_basis"])},
        "basis": "项目税后", "original_input_hash": exported["input_hash"],
        "original_source_snapshot_id": exported["source_snapshot_id"],
        "original_dataset_content_hash": None,
        "generation_result_hash": "a" * 64, "method_config_hash": methods.hash,
        "source": {"source_id": "SYNTHETIC:explicit-selection", "source_reference": "SYNTHETIC:isolated-control",
                   "source_kind": "SYNTHETIC", "status": "ASSUMED", "license_status": "AUTHORIZED"},
    }
    return catalog, exported, methods, control


def test_strict_selector_binds_single_sourced_price_and_existing_basis():
    catalog, exported, methods, control = _case()
    selected = _selector_module().validate_price_selector(control, exported, methods, None, catalog)
    assert selected.original_atom["value"] == Decimal("0.4")
    assert selected.original_atom["field_instance_id"] == control["selector"]["field_instance_id"]
    assert selected.original_input_hash == exported["input_hash"]
    assert selected.selector_hash == digest(control)


@pytest.mark.parametrize("change", [
    lambda c: c.update(project_id="other"),
    lambda c: c.update(original_input_hash="0" * 64),
    lambda c: c.update(method_config_hash="0" * 64),
    lambda c: c.update(original_source_snapshot_id="0" * 64),
    lambda c: c["selector"].update(row_id="wrong-row"),
    lambda c: c["selector"].update(field_instance_id="wrong-instance"),
    lambda c: c["selector"].update(original_atom_hash="0" * 64),
    lambda c: c["selector"].update(field_id="tariff.transaction_fee"),
    lambda c: c["selector"].update(other_price=Decimal("0.7")),
    lambda c: c.update(basis="股东实际收付"),
    lambda c: c["source"].update(status="VERIFIED"),
])
def test_selector_rejects_unauthorized_or_wrong_identity(change):
    catalog, exported, methods, control = _case()
    change(control)
    with pytest.raises(ContractError):
        _selector_module().validate_price_selector(control, exported, methods, None, catalog)


def test_duplicate_row_identity_cannot_be_resolved_by_array_position():
    catalog, exported, methods, control = _case()
    invalid = deepcopy(exported)
    invalid["project"]["values"]["tariff.periods"]["value"].append(
        deepcopy(invalid["project"]["values"]["tariff.periods"]["value"][0]))
    with pytest.raises(ContractError):
        _selector_module().validate_price_selector(control, invalid, methods, None, catalog)


def test_selected_price_must_be_used_by_current_settlement_method():
    catalog, exported, methods, control = _case()
    data = methods.to_dict()
    data["parameters"]["settlement.price_source"] = parameter("settlement.price_source", "MARKET_SERIES")
    methods = MethodConfig.from_dict(data)
    control["method_config_hash"] = methods.hash
    with pytest.raises(ContractError):
        _selector_module().validate_price_selector(control, exported, methods, None, catalog)


@pytest.mark.parametrize("field_id,ppa,expected", [
    ("tariff.periods.avoidable_price", None, Decimal("0.8")),
    ("tariff.ppa_price", "PPA_FIXED", Decimal("0.5")),
])
def test_rooftop_self_use_quote_is_selected_without_touching_sale_price(field_id, ppa, expected):
    catalog, exported, methods, control = _case("industrial_rooftop", ppa=ppa, field_id=field_id)
    selected = _selector_module().validate_price_selector(control, exported, methods, None, catalog)
    assert selected.original_atom["value"] == expected
    assert exported["project"]["values"]["tariff.periods"]["value"][0]["fields"]["tariff.periods.sale_price"]["value"] == Decimal("0.4")


def test_market_row_requires_full_readable_d3_and_exact_one_row(tmp_path):
    catalog, exported, methods, control = _case(market=True)
    control["selector"].update(field_id="tariff.market_series.sale_price", row_id="m0",
                               field_instance_id="market-0-sale_price")
    with pytest.raises(ContractError):
        _selector_module().validate_price_selector(control, exported, methods, None, catalog)
    budget = BundleBudget(max_seconds=1800)
    period = axis()
    write_bundle(tmp_path / "market", base_export=exported,
                 datasets={"tariff.market_series": {"header": series_header(catalog, "tariff.market_series", period),
                                                      "rows": market_rows(catalog, period)}},
                 catalog=catalog, budget=budget)
    with read_bundle(tmp_path / "market", catalog=catalog, budget=budget) as bundle:
        first = next(bundle.rows("tariff.market_series"))
        control["selector"].update(original_atom_hash=digest(first["fields"]["tariff.market_series.sale_price"]),
                                   economic_basis=first["fields"]["tariff.market_series.sale_price"]["economic_basis"])
        control["original_dataset_content_hash"] = bundle.content_hash
        selected = _selector_module().validate_price_selector(control, exported, methods, bundle, catalog)
        assert selected.original_atom["field_instance_id"] == "market-0-sale_price"
        assert selected.original_dataset_content_hash == bundle.content_hash
