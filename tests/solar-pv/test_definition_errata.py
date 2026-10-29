"""D1 metadata only: approved errata never establishes numerical implementation."""
from copy import deepcopy

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.formula_bindings import FormulaBindings
from wangbin_solar_pv.models import ProjectData
from synthetic_support import record, row, put_rows


def test_e02_capex_amount_is_output_and_quote_is_preserved():
    cat = Catalog()
    fid = "F-CAPEX-ITEM-AMOUNT"
    symbol = next(s for s in cat.formulas[fid]["every_symbol_definition"] if s["symbol"] == "C_i")
    assert symbol["role"] == "output"
    assert cat.frozen_formulas[fid]["every_symbol_definition"][0]["role"] == "input"
    project = ProjectData.new("SYNTHETIC-D1-E02", "industrial_rooftop", cat)
    put_rows(project, cat, "capex.items", [row(cat, "capex.items", "quoted", {"quantity": 2, "unit_price": 100, "amount": 250})])
    before = deepcopy(project.to_dict())
    info = FormulaBindings(cat).describe(fid, project)
    assert "capex.items.amount" not in info["required_parameters"]
    assert "capex.items.amount" not in info["conditional_parameters"]
    assert "capex.items.amount" not in info["missing_variable_field_ids"]
    assert "capex.items.amount" not in info["missing_input_field_ids"]
    assert {"capex.items.quantity", "capex.items.unit_price"} <= set(info["required_parameters"] + info["conditional_parameters"])
    assert project.to_dict() == before
    assert project.values["capex.items"]["value"][0]["fields"]["capex.items.amount"]["value"] == 250
    assert info["calculation_status"] == "NOT_IMPLEMENTED"


def test_e01_usable_area_is_output_not_a_required_or_missing_input():
    cat = Catalog()
    fid = "F-USABLE-AREA"
    formula = cat.formulas[fid]
    symbol = next(s for s in formula["every_symbol_definition"] if s["symbol"] == "A_use")
    assert symbol["role"] == "output"
    assert cat.frozen_formulas[fid]["every_symbol_definition"][0]["role"] == "input"
    project = ProjectData.new("SYNTHETIC-D1-E01", "industrial_rooftop", cat)
    info = FormulaBindings(cat).describe(fid, project)
    assert "site.usable_area" not in info["required_parameters"]
    assert "site.usable_area" not in info["conditional_parameters"]
    assert "site.usable_area" not in info["missing_variable_field_ids"]
    assert "site.usable_area" not in info["missing_input_field_ids"]
    project.values["site.usable_area"] = record(cat, "site.usable_area", 99)
    before = deepcopy(project.to_dict())
    FormulaBindings(cat).describe(fid, project)
    assert project.to_dict() == before
    assert cat.fields["site.usable_area"]["field_id"] == "site.usable_area"
    assert info["can_execute_calculation"] is False


def test_e03_nominal_real_rate_is_dimensionless_annual_step_metadata():
    cat = Catalog()
    fid = "F-NOMINAL-REAL-RATE"
    current, frozen = cat.formulas[fid], cat.frozen_formulas[fid]
    assert current["unit"] == "1"
    assert "无量纲" in current["dimensional_check"]
    assert "年度" in current["dimensional_check"]
    assert "复利" in current["dimensional_check"]
    assert frozen["unit"] == "1/年"
    for key in ("latex", "text_equation", "input_field_ids", "output_field_id", "every_symbol_definition", "unit_convention", "assumptions", "calculation_boundary"):
        assert current[key] == frozen[key]
    assert FormulaBindings(cat).describe(fid)["formula"] == current


def test_e04_aggregation_b_is_energy_boundary_not_tax_equity_basis():
    cat = Catalog()
    fid = "F-ENERGY-AGGREGATION"
    current, frozen = cat.formulas[fid], cat.frozen_formulas[fid]
    tokens = current["subscript_definition"]["逐个下标词素"]
    assert "b=同一物理能量边界" in tokens
    assert "股权" not in tokens and "税前" not in tokens
    assert "项目/股权" in frozen["subscript_definition"]["逐个下标词素"]
    for key in ("latex", "text_equation", "every_symbol_definition", "input_field_ids", "output_field_id", "set_and_range_definition", "calculation_boundary"):
        assert current[key] == frozen[key]
    assert FormulaBindings(cat).describe(fid)["formula"] == current


def test_e05_break_even_p_is_solved_settlement_price_not_period_index():
    cat = Catalog()
    fid = "F-BREAK-EVEN-PRICE"
    current, frozen = cat.formulas[fid], cat.frozen_formulas[fid]
    tokens = current["subscript_definition"]["逐个下标词素"]
    assert "p=待求结算电价" in tokens
    assert "p=月/年" not in tokens
    assert "p=月/年" in frozen["subscript_definition"]["逐个下标词素"]
    for key in ("latex", "text_equation", "every_symbol_definition", "input_field_ids", "output_field_id", "set_and_range_definition", "calculation_boundary", "assumptions"):
        assert current[key] == frozen[key]
    symbol = next(s for s in FormulaBindings(cat).describe(fid)["symbols"] if s["definition"]["symbol"] == "p")
    assert symbol["definition"]["field_id"] is None
    assert symbol["binding_status"] == "SYMBOLIC_INDEX_OR_SOLVER_PARAMETER"


def _energy_raw_lineage(cat):
    # Independent traversal of the approved frozen producer/dependency graph;
    # do not use the corrected residual binding to generate the expectation.
    pending = list(cat.frozen_formulas["F-ENERGY-BALANCE"]["input_field_ids"])
    visited, raw = set(), set()
    while pending:
        domain = pending.pop()
        if domain in visited:
            continue
        visited.add(domain)
        binding = cat.frozen_bindings[domain]
        raw.update(binding["input_field_ids"])
        for producer in binding["producer_formula_ids"]:
            pending.extend(cat.frozen_formulas[producer]["input_field_ids"])
    return raw


def test_e06_energy_balance_supporting_raw_lineage_uses_energy_dependencies():
    cat = Catalog()
    key = "checks.energy_balance_residual"
    expected = _energy_raw_lineage(cat)
    assert set(cat.bindings[key]["input_field_ids"]) == expected
    assert {"load.series.energy", "resource.timeseries.poa", "grid.export_power_limit", "site.timezone"} <= expected
    assert not any(fid.startswith(("finance.", "capex.")) for fid in expected)
    assert cat.frozen_bindings[key]["input_field_ids"] == ["finance.working_capital", "finance.debt_schedule", "capex.items"]
    for name in ("producer_formula_ids", "consumer_formula_ids", "kind", "formula_field_id"):
        assert cat.bindings[key][name] == cat.frozen_bindings[key][name]
    info = FormulaBindings(cat).describe_field(key)
    assert {x["field_id"] for x in info["supporting_inputs"]} == expected
    assert info["binding_status"] == "NOT_COMPUTED" and info["execution_status"] == "NOT_IMPLEMENTED"
    project = ProjectData.new("SYNTHETIC-D1-E06", "industrial_rooftop", cat)
    query = FormulaBindings(cat).describe_field(key, project)
    assert not any(fid.startswith(("finance.", "capex.")) for fid in query["missing_input_field_ids"])
