"""K: query frozen methods, never execute or manufacture a formula-ledger value."""
from copy import deepcopy
import pytest
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.models import ProjectData
from wangbin_solar_pv.errors import ContractError
from synthetic_support import record, row, put_rows

CAT=Catalog()


@pytest.mark.parametrize("formula_id",sorted(CAT.formulas))
def test_all_89_formulas_expose_every_symbol_and_frozen_boundary(formula_id):
    from wangbin_solar_pv.formula_bindings import FormulaBindings
    result=FormulaBindings(CAT).describe(formula_id)
    original=CAT.formulas[formula_id]
    assert result["formula"]==original
    assert len(result["symbols"])==len(original["every_symbol_definition"])
    assert result["calculation_status"]=="NOT_IMPLEMENTED"
    assert result["can_execute_calculation"] is False
    assert result["input_presence_evaluated"] is False
    assert result["missing_input_field_ids"]==[]
    for symbol,expected in zip(result["symbols"],original["every_symbol_definition"]):
        assert symbol["definition"]==expected
        if expected["field_id"] is None:
            assert symbol["binding"] is None and symbol["binding_status"]=="SYMBOLIC_INDEX_OR_SOLVER_PARAMETER"
        else:
            assert symbol["binding"]==CAT.bindings[expected["field_id"]]
        assert symbol["data_type"]
        for field in symbol["supporting_inputs"]:
            assert field["type"]==CAT.fields[field["field_id"]]["type"]
            assert field["source_requirements"]==CAT.fields[field["field_id"]]["provenance_kinds"]
            assert field["availability"]=="NOT_EVALUATED"


@pytest.mark.parametrize("field_id",sorted(CAT.bindings))
def test_all_281_formula_domain_bindings_have_explicit_state_not_zero(field_id):
    from wangbin_solar_pv.formula_bindings import FormulaBindings
    info=FormulaBindings(CAT).describe_field(field_id)
    assert info["binding"]==CAT.bindings[field_id]
    assert "value" not in info
    if info["binding"]["kind"] in {"CALCULATION_LEDGER_STATE","CALCULATED_OR_VALIDATED_LEDGER_OUTPUT"}:
        assert info["binding_status"]=="NOT_COMPUTED"


def test_missing_variables_identify_exact_catalog_inputs_not_just_generic_failure():
    from wangbin_solar_pv.formula_bindings import FormulaBindings
    p=ProjectData.new("SYNTHETIC-EMPTY","industrial_rooftop",CAT)
    info=FormulaBindings(CAT).describe("F-DC-CAPACITY",p)
    assert {"system.module_count","system.module_power"}<=set(info["missing_input_field_ids"])
    assert {"equipment.module_count","equipment.module_power_kwp"}<=set(info["missing_variable_field_ids"])
    assert info["can_execute_calculation"] is False


def test_available_input_does_not_claim_transformation_or_output_has_been_computed():
    from wangbin_solar_pv.formula_bindings import FormulaBindings
    p=ProjectData.new("SYNTHETIC-AVAILABLE","industrial_rooftop",CAT)
    p.values["system.module_count"]=record(CAT,"system.module_count",100)
    p.values["system.module_power"]=record(CAT,"system.module_power",500)
    before=deepcopy(p.to_dict());info=FormulaBindings(CAT).describe("F-DC-CAPACITY",p)
    assert not info["missing_input_field_ids"]
    assert "capacity.dc_kwp" in info["uncomputed_formula_field_ids"]
    assert info["can_execute_calculation"] is False and p.to_dict()==before
    assert "system.dc_capacity" not in p.values


def test_no_debt_is_condition_not_applicable_not_zero_debt_service():
    from wangbin_solar_pv.formula_bindings import FormulaBindings
    p=ProjectData.new("SYNTHETIC-NO-DEBT","industrial_rooftop",CAT)
    p.values["finance.debt_ratio"]=record(CAT,"finance.debt_ratio",0)
    info=FormulaBindings(CAT).describe_field("debt.annual_interest_rate",p)
    assert all(x["requirement"]["requirement"]=="NOT_APPLICABLE" for x in info["supporting_inputs"])
    assert not info["missing_input_field_ids"] and "value" not in info


def test_each_array_atom_is_checked_not_hidden_by_a_present_container():
    from wangbin_solar_pv.formula_bindings import FormulaBindings
    p=ProjectData.new("SYNTHETIC-ATOMS","industrial_rooftop",CAT)
    put_rows(p,CAT,"capex.items",[row(CAT,"capex.items","a",{"quantity":2,"unit_price":100}),row(CAT,"capex.items","b",{"quantity":None,"unit_price":200})])
    info=FormulaBindings(CAT).describe("F-CAPEX-ITEM-AMOUNT",p)
    assert "capex.items.quantity" in info["missing_input_field_ids"]
    assert any(x["field_id"]=="capex.items.quantity" for x in info["missing_instances"])


def test_unverified_constant_temperature_and_unknown_formula_stay_explicit():
    from wangbin_solar_pv.formula_bindings import FormulaBindings
    api=FormulaBindings(CAT)
    assert api.describe_field("constants.stc_cell_temperature_c")["binding_status"]=="CONSTANT_UNVERIFIED"
    with pytest.raises(ContractError,match="UNKNOWN_FORMULA"):
        api.describe(" F-DC-CAPACITY ")
    assert CAT.bindings["constants.stc_cell_temperature_c"]["constant_definition"]["value"] is None
