"""SYNTHETIC input-contract tests; never CAT-E2E or calculation acceptance."""
from copy import deepcopy
import importlib
import importlib.util
from functools import lru_cache
import json
from pathlib import Path

import pytest

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.models import ProjectData
from wangbin_solar_pv.schemas import StrictValidator, format_checker
from synthetic_support import put_rows, record, row

TYPES = (
    "industrial_rooftop", "utility_scale_ground", "agri_pv", "fishery_pv",
    "pv_storage", "public_rooftop", "residential_pv", "pv_carport_bipv", "desert_mining",
)
PACKAGE = Path(__file__).resolve().parents[2] / "services/solar-pv-engine/src/wangbin_solar_pv"


@pytest.fixture(scope="module")
def catalog():
    return Catalog()


@pytest.fixture
def api():
    if importlib.util.find_spec("wangbin_solar_pv.categories") is None:
        return None
    return importlib.import_module("wangbin_solar_pv.categories")


@pytest.mark.parametrize("pv_type", TYPES)
def test_independent_contract_identity_and_non_calculation_status(api, catalog, pv_type):
    assert api is not None, "category input-contract API is not implemented"
    contract = api.category_contract(pv_type, catalog)
    stored = json.loads((PACKAGE / "scenarios" / pv_type / "contract.json").read_text(encoding="utf-8"))
    assert contract["pv_type"] == stored["pv_type"] == pv_type
    assert stored["contract_id"] == "solar-pv-input-category/" + pv_type + "/1.0.0"
    assert contract["input_contract_status"] == "IMPLEMENTED"
    assert contract["calculation_status"] == contract["e2e_status"] == "NOT_IMPLEMENTED"
    assert contract["restriction"] and stored["restriction"]
    assert isinstance(contract["allowed_field_ids"], list)
    assert isinstance(contract["required_special_field_ids"], list)
    assert set(contract["required_special_field_ids"]) <= set(contract["allowed_field_ids"])
    assert len(contract["allowed_field_ids"]) == len(set(contract["allowed_field_ids"]))
    assert set(contract["allowed_field_ids"]) <= catalog.fields.keys()


@pytest.mark.parametrize("pv_type", ["unknown", "PV_STORAGE", "../industrial_rooftop", "", None, []])
def test_unknown_category_cannot_select_a_file_or_silently_downgrade(api, catalog, pv_type):
    assert api is not None, "category input-contract API is not implemented"
    with pytest.raises(ContractError) as exc:
        api.category_contract(pv_type, catalog)
    assert exc.value.code == "UNKNOWN_CATEGORY"


@pytest.mark.parametrize("base", [t for t in TYPES if t != "pv_storage"])
def test_storage_composes_exact_selected_base_fields_without_claiming_calculation(api, catalog, base):
    base_contract = api.category_contract(base, catalog)
    storage = api.category_contract("pv_storage", catalog, base_pv_type=base)
    storage_only = {fid for fid, field in catalog.fields.items() if field["pv_types"] == ["pv_storage"]}
    assert set(storage["allowed_field_ids"]) == set(base_contract["allowed_field_ids"]) | storage_only
    assert set(base_contract["required_special_field_ids"]) <= set(storage["required_special_field_ids"])
    assert storage["base_pv_type"] == base
    assert storage["base_input_status"] == "SELECTED"
    assert storage["calculation_status"] == storage["base_calculation_status"] == "NOT_IMPLEMENTED"


@pytest.mark.parametrize("base", ["pv_storage", "unknown", "AGRI_PV", "", [], 1])
def test_recursive_or_invalid_storage_base_is_rejected(api, catalog, base):
    with pytest.raises(ContractError) as exc:
        api.category_contract("pv_storage", catalog, base_pv_type=base)
    assert exc.value.code == "INVALID_STORAGE_BASE"


def test_storage_missing_base_does_not_assume_a_rooftop(api, catalog):
    result = api.category_contract("pv_storage", catalog)
    assert result["base_pv_type"] is None and result["base_input_status"] == "UNKNOWN"
    assert "roof.material" not in result["allowed_field_ids"]
    assert "agri.crop_species" not in result["allowed_field_ids"]
    with pytest.raises(ContractError) as exc:
        api.category_contract("industrial_rooftop", catalog, base_pv_type="agri_pv")
    assert exc.value.code == "BASE_ONLY_FOR_STORAGE"


@pytest.mark.parametrize("pv_type", TYPES)
def test_category_schema_preserves_all_definitions_and_only_filters_root_keys(api, catalog, pv_type):
    original = catalog.project_schema()
    schema = api.category_schema(pv_type, catalog)
    contract = api.category_contract(pv_type, catalog)
    assert len(schema["$defs"]) == 469
    assert schema["$defs"] == original["$defs"]
    assert schema["properties"]["pv_type"] == {"const": pv_type}
    roots = {fid for fid in contract["allowed_field_ids"] if not catalog.fields[fid].get("repeat_group")}
    assert set(schema["properties"]["values"]["properties"]) == roots
    assert schema["properties"]["values"]["additionalProperties"] is False
    project = ProjectData.new("SYNTHETIC-CATEGORY", pv_type, catalog)
    assert not list(StrictValidator(schema, format_checker=format_checker()).iter_errors(project.to_dict()))
    schema["$defs"].clear()
    assert catalog.project_schema() == original


def test_storage_schema_uses_selected_base_and_retains_frozen_base_field_definition(api, catalog):
    schema = api.category_schema("pv_storage", catalog, base_pv_type="agri_pv")
    roots = schema["properties"]["values"]["properties"]
    assert "agri.crop_species" in roots and "storage.energy_capacity" in roots
    assert "roof.material" not in roots and "fishery.water_depth" not in roots
    assert schema["$defs"]["storage.base_pv_type"] == catalog.project_schema()["$defs"]["storage.base_pv_type"]


@lru_cache(maxsize=9)
def _empty_project(catalog, pv_type):
    return ProjectData.new("SYNTHETIC-CATEGORY", pv_type, catalog)


def make_project(catalog, pv_type, **values):
    project = deepcopy(_empty_project(catalog, pv_type))
    for fid, value in values.items():
        project.values[fid] = record(catalog, fid, value)
    return project


def codes(issues, severity=None):
    return {i.code for i in issues if severity is None or i.severity == severity}


@pytest.mark.parametrize("pv_type", TYPES)
def test_all_nine_types_validate_as_drafts_without_claiming_business_acceptance(api, catalog, pv_type):
    project = make_project(catalog, pv_type)
    before = deepcopy(project.to_dict())
    issues = api.validate_category(project, catalog)
    assert "NOT_IMPLEMENTED" in codes(issues, "WARNING")
    assert not codes(issues, "ERROR")
    assert project.to_dict() == before


@pytest.mark.parametrize("pv_type", TYPES)
def test_root_and_project_category_must_match(api, catalog, pv_type):
    other = next(t for t in TYPES if t != pv_type)
    project = make_project(catalog, pv_type, **{"project.pv_type": other})
    assert "CATEGORY_MISMATCH" in codes(api.validate_category(project, catalog), "ERROR")


# Every frozen dedicated field is exercised in every non-storage category;
# selected storage-base composition is tested independently above and below.
DEDICATED = [f["field_id"] for f in json.loads((PACKAGE.parents[3] / "docs/solar-pv/03-input-fields.json").read_text(encoding="utf-8"))["fields"] if len(f["pv_types"]) < len(TYPES)]


@pytest.mark.parametrize("fid", DEDICATED)
def test_every_dedicated_field_is_rejected_in_other_domains_even_when_unknown(api, catalog, fid):
    for pv_type in TYPES:
        if pv_type == "pv_storage":
            continue
        project = make_project(catalog, pv_type, **{fid: None})
        issues = api.validate_category(project, catalog)
        rejected = any(i.code == "CATEGORY_FIELD_NOT_ALLOWED" and i.field_id == fid for i in issues)
        assert rejected == (pv_type not in catalog.fields[fid]["pv_types"]), (pv_type, fid, issues)


@pytest.mark.parametrize("pv_type", [t for t in TYPES if t != "pv_storage"])
def test_storage_true_requires_storage_category(api, catalog, pv_type):
    project = make_project(catalog, pv_type, **{"project.has_storage": True})
    assert "STORAGE_CATEGORY_REQUIRED" in codes(api.validate_category(project, catalog), "ERROR")


def test_storage_false_conflicts_with_storage_category(api, catalog):
    project = make_project(catalog, "pv_storage", **{"project.has_storage": False})
    assert "STORAGE_FLAG_CONFLICT" in codes(api.validate_category(project, catalog), "ERROR")


@pytest.mark.parametrize("pv_type,fid", [("pv_carport_bipv", "carport_bipv.subtype"), ("desert_mining", "desert_mining.subtype")])
def test_subtype_missing_or_invalid_never_defaults_to_roof(api, catalog, pv_type, fid):
    project = make_project(catalog, pv_type)
    issues = api.validate_category(project, catalog)
    assert any(i.code == "CATEGORY_SUBTYPE_UNKNOWN" and i.field_id == fid and i.severity == "WARNING" for i in issues)
    assert fid not in project.values
    for value in catalog.fields[fid]["constraints"]["enum"]:
        project.values[fid] = record(catalog, fid, value)
        assert "CATEGORY_SUBTYPE_INVALID" not in codes(api.validate_category(project, catalog))
        assert "CATEGORY_SUBTYPE_UNKNOWN" not in codes(api.validate_category(project, catalog))
    project.values[fid] = record(catalog, fid, "industrial_rooftop")
    assert "CATEGORY_SUBTYPE_INVALID" in codes(api.validate_category(project, catalog), "ERROR")


def test_unknown_runtime_category_becomes_issue_not_exception(api, catalog):
    project = make_project(catalog, "industrial_rooftop")
    project.pv_type = "../invalid"
    assert "UNKNOWN_CATEGORY" in codes(api.validate_category(project, catalog), "ERROR")


@pytest.mark.parametrize("mode", ["self_use_surplus_export", "full_export", "off_grid", "hybrid", "undecided"])
def test_industrial_rooftop_accepts_all_frozen_sales_modes(api, catalog, mode):
    project = make_project(catalog, "industrial_rooftop", **{"project.sales_mode": mode})
    assert "CATEGORY_SALES_MODE_INVALID" not in codes(api.validate_category(project, catalog))


@pytest.mark.parametrize("mode", ["self_use_surplus_export", "full_export", "off_grid", "hybrid", "undecided"])
def test_ground_only_full_export_or_explicitly_pending_draft(api, catalog, mode):
    project = make_project(catalog, "utility_scale_ground", **{"project.sales_mode": mode})
    issues = api.validate_category(project, catalog)
    assert ("CATEGORY_SALES_MODE_INVALID" in codes(issues, "ERROR")) == (mode not in {"full_export", "undecided"})
    assert ("CATEGORY_SALES_MODE_UNKNOWN" in codes(issues, "WARNING")) == (mode == "undecided")


@pytest.mark.parametrize("fid", ["roof.material", "roof.allowable_additional_load", "load.annual_energy", "load.proposed_self_use_ratio", "load.monthly_bills", "load.series", "tariff.non_avoidable_charges"])
def test_ground_cannot_accept_roof_or_industrial_load_fields_even_null(api, catalog, fid):
    project = make_project(catalog, "utility_scale_ground", **{fid: None})
    issues = api.validate_category(project, catalog)
    assert any(i.code == "CATEGORY_FIELD_NOT_ALLOWED" and i.field_id == fid for i in issues)
    schema = api.category_schema("utility_scale_ground", catalog)
    assert list(StrictValidator(schema, format_checker=format_checker()).iter_errors(project.to_dict()))


@pytest.mark.parametrize("group,name,value", [
    ("capex.items", "category", "roof_reinforcement"),
    ("opex.items", "category", "roof_rent"),
    ("tariff.periods", "avoidable_price", 1),
])
def test_ground_rejects_rooftop_costs_and_avoidable_price_nested_in_shared_arrays(api, catalog, group, name, value):
    project = make_project(catalog, "utility_scale_ground")
    put_rows(project, catalog, group, [row(catalog, group, "SYNTHETIC-ROW", {name: value})])
    issues = api.validate_category(project, catalog)
    expected = "CATEGORY_FIELD_NOT_ALLOWED" if name == "avoidable_price" else "CATEGORY_COST_NOT_ALLOWED"
    fid = group + "." + name
    target = next(i for i in issues if i.code == expected and i.field_id == fid)
    assert target.instance_id == project.values[group]["value"][0]["fields"][fid]["field_instance_id"]


@pytest.mark.parametrize("kind", ["self_use", "self_use_savings", "self_consumption", "avoided_purchase_cost", "roof_lease", "roof_rent", "企业自用节省", "屋顶租赁"])
def test_ground_rejects_self_use_or_roof_income_models(api, catalog, kind):
    project = make_project(catalog, "utility_scale_ground")
    put_rows(project, catalog, "revenue.other_items", [row(catalog, "revenue.other_items", "SYNTHETIC-REVENUE", {"kind": kind})])
    assert "CATEGORY_REVENUE_NOT_ALLOWED" in codes(api.validate_category(project, catalog), "ERROR")


@pytest.mark.parametrize("group,name,value", [
    ("capex.items", "category", "land"),
    ("capex.items", "category", "grid_export"),
    ("opex.items", "category", "land_rent"),
    ("tariff.periods", "sale_price", 1),
    ("tariff.market_series", "sale_price", 1),
])
def test_ground_keeps_legitimate_land_export_costs_and_sales_prices(api, catalog, group, name, value):
    project = make_project(catalog, "utility_scale_ground", **{"project.sales_mode": "full_export"})
    put_rows(project, catalog, group, [row(catalog, group, "SYNTHETIC-GROUND", {name: value})])
    assert not codes(api.validate_category(project, catalog), "ERROR")


def test_ground_unknown_other_income_requires_review_not_automatic_business_support(api, catalog):
    project = make_project(catalog, "utility_scale_ground")
    put_rows(project, catalog, "revenue.other_items", [row(catalog, "revenue.other_items", "SYNTHETIC-OTHER", {"kind": "SYNTHETIC unspecified contract income"})])
    issues = api.validate_category(project, catalog)
    assert "CATEGORY_REVENUE_REVIEW_REQUIRED" in codes(issues, "WARNING")
    assert "NOT_IMPLEMENTED" in codes(issues)


@pytest.mark.parametrize("pv_type", ["industrial_rooftop", "utility_scale_ground"])
def test_shared_catalog_scope_does_not_mutate_when_contract_narrows(api, catalog, pv_type):
    before = deepcopy(catalog.fields)
    contract = api.category_contract(pv_type, catalog)
    project = make_project(catalog, pv_type)
    api.validate_category(project, catalog)
    assert catalog.fields == before
    assert "utility_scale_ground" in catalog.fields["load.annual_energy"]["pv_types"]
    assert ("load.annual_energy" in contract["allowed_field_ids"]) == (pv_type == "industrial_rooftop")


@pytest.mark.parametrize("base", [None, "pv_storage", "unknown", "utility_scale_ground "])
def test_storage_validator_rejects_illegal_base_or_warns_when_missing(api, catalog, base):
    project = make_project(catalog, "pv_storage", **{"project.has_storage": True})
    if base is not None:
        project.values["storage.base_pv_type"] = record(catalog, "storage.base_pv_type", base)
    before = deepcopy(project.to_dict())
    issues = api.validate_category(project, catalog)
    if base is None:
        assert "STORAGE_BASE_UNKNOWN" in codes(issues, "WARNING")
        assert not codes(issues, "ERROR")
    else:
        assert "INVALID_STORAGE_BASE" in codes(issues, "ERROR")
    assert "NOT_IMPLEMENTED" in codes(issues)
    assert project.to_dict() == before


@pytest.mark.parametrize("status", ["UNKNOWN", "CONFLICT"])
def test_storage_unknown_or_conflicted_base_is_not_inferred_from_other_inputs(api, catalog, status):
    project = make_project(catalog, "pv_storage", **{"roof.material": "SYNTHETIC roof"})
    project.values["storage.base_pv_type"] = record(catalog, "storage.base_pv_type", None, status=status)
    issues = api.validate_category(project, catalog)
    assert "STORAGE_BASE_UNKNOWN" in codes(issues, "WARNING")
    assert any(i.code == "CATEGORY_FIELD_NOT_ALLOWED" and i.field_id == "roof.material" for i in issues)


@pytest.mark.parametrize("base,fid,other", [
    ("industrial_rooftop", "roof.material", "agri.crop_species"),
    ("utility_scale_ground", "site.geotechnical_reference", "roof.material"),
    ("agri_pv", "agri.crop_species", "fishery.water_depth"),
    ("fishery_pv", "fishery.water_depth", "agri.crop_species"),
    ("public_rooftop", "public.asset_authorization", "residential.property_consent"),
    ("residential_pv", "residential.property_consent", "public.asset_authorization"),
    ("pv_carport_bipv", "carport_bipv.subtype", "desert_mining.subtype"),
    ("desert_mining", "desert_mining.subtype", "carport_bipv.subtype"),
])
def test_selected_storage_base_preserves_its_own_domain_and_rejects_others(api, catalog, base, fid, other):
    project = make_project(catalog, "pv_storage", **{"storage.base_pv_type": base, fid: None, other: None})
    issues = api.validate_category(project, catalog)
    assert not any(i.code == "CATEGORY_FIELD_NOT_ALLOWED" and i.field_id == fid for i in issues)
    assert any(i.code == "CATEGORY_FIELD_NOT_ALLOWED" and i.field_id == other for i in issues)
    assert "STORAGE_BASE_UNKNOWN" not in codes(issues)
    assert "NOT_IMPLEMENTED" in codes(issues)


@pytest.mark.parametrize("group,name,value,expected", [
    ("capex.items", "category", "roof_reinforcement", "CATEGORY_COST_NOT_ALLOWED"),
    ("opex.items", "category", "roof_rent", "CATEGORY_COST_NOT_ALLOWED"),
    ("revenue.other_items", "kind", "self_use_savings", "CATEGORY_REVENUE_NOT_ALLOWED"),
    ("tariff.periods", "avoidable_price", 1, "CATEGORY_FIELD_NOT_ALLOWED"),
])
def test_storage_ground_base_inherits_ground_cost_and_revenue_boundaries(api, catalog, group, name, value, expected):
    project = make_project(catalog, "pv_storage", **{"storage.base_pv_type": "utility_scale_ground"})
    put_rows(project, catalog, group, [row(catalog, group, "SYNTHETIC-STORAGE-GROUND", {name: value})])
    assert expected in codes(api.validate_category(project, catalog), "ERROR")


@pytest.mark.parametrize("mode", ["self_consumption", "hybrid"])
def test_ground_storage_self_consumption_dispatch_is_an_explicit_scheme_conflict(api, catalog, mode):
    project = make_project(catalog, "pv_storage", **{"storage.base_pv_type": "utility_scale_ground", "storage.dispatch_mode": mode})
    issues = api.validate_category(project, catalog)
    assert "STORAGE_BASE_DISPATCH_CONFLICT" in codes(issues, "ERROR")
    assert "NOT_IMPLEMENTED" in codes(issues)


def test_ground_storage_positive_discharge_to_load_is_not_a_no_storage_fallback(api, catalog):
    project = make_project(catalog, "pv_storage", **{"storage.base_pv_type": "utility_scale_ground", "storage.dispatch_mode": "arbitrage"})
    put_rows(project, catalog, "storage.dispatch", [row(catalog, "storage.dispatch", "SYNTHETIC-DISPATCH", {"discharge_to_load": 1})])
    assert "STORAGE_BASE_DISPATCH_CONFLICT" in codes(api.validate_category(project, catalog), "ERROR")


@pytest.mark.parametrize("mode", ["arbitrage", "contract_dispatch"])
def test_ground_storage_non_load_scheme_is_only_validated_input_not_computation(api, catalog, mode):
    project = make_project(catalog, "pv_storage", **{"storage.base_pv_type": "utility_scale_ground", "storage.dispatch_mode": mode, "project.sales_mode": "full_export"})
    issues = api.validate_category(project, catalog)
    assert not codes(issues, "ERROR")
    assert "NOT_IMPLEMENTED" in codes(issues)
