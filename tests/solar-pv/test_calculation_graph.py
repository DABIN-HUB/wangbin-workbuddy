"""SYNTHETIC dependency DAG checks; no test-generated numerical expectations."""
import pytest
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.errors import ContractError


def nodes():
    from wangbin_solar_pv.calculation.calculation_graph import CalculationNode
    return [
        CalculationNode("revenue:FY1", "F-ENERGY-REVENUE", (), ("tariff.ppa_price",), "FY1", "OWNER_INCREMENTAL", "ENERGY_REVENUE"),
        CalculationNode("cash:FY1", "F-PROJECT-CASH-FLOW", ("revenue:FY1",), (), "FY1", "PROJECT_UNLEVERED", "DIRECT_CASH"),
        CalculationNode("npv:project", "F-NPV", ("cash:FY1",), ("finance.project_discount_rate",), "FY0..FY25", "PROJECT_UNLEVERED", "YEAR_END"),
    ]


def test_price_changes_invalidate_revenue_cash_and_npv_not_only_display():
    from wangbin_solar_pv.calculation.calculation_graph import CalculationGraph
    graph = CalculationGraph(nodes(), Catalog())
    assert graph.affected_by(["tariff.ppa_price"]) == ["revenue:FY1", "cash:FY1", "npv:project"]
    assert graph.affected_by(["finance.project_discount_rate"]) == ["npv:project"]
    assert graph.affected_by(["targets.payback_years"]) == []
    assert [n.node_id for n in graph.ordered()] == ["revenue:FY1", "cash:FY1", "npv:project"]


def test_cycle_duplicate_unregistered_field_and_dangling_edges_are_not_a_closed_graph():
    from wangbin_solar_pv.calculation.calculation_graph import CalculationGraph, CalculationNode
    catalog = Catalog()
    for malformed in [nodes() + [nodes()[0]], [CalculationNode("x", "F-NPV", ("missing",), (), "FY1", "PROJECT", "YEAR_END")],
                      [CalculationNode("x", "F-NPV", ("y",), (), "FY1", "PROJECT", "YEAR_END"), CalculationNode("y", "F-NPV", ("x",), (), "FY1", "PROJECT", "YEAR_END")],
                      [CalculationNode("x", "F-NPV", (), ("invented.field",), "FY1", "PROJECT", "YEAR_END")],
                      [CalculationNode("x", "F-NOT-REGISTERED", (), (), "FY1", "PROJECT", "YEAR_END")]]:
        with pytest.raises(ContractError):
            CalculationGraph(malformed, catalog)
