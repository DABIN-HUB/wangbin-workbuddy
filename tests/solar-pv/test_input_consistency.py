"""Four Phase1 corrections plus cross-field data audits (no forecasting)."""
from copy import deepcopy
from decimal import Decimal
import pytest
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.models import ProjectData
from wangbin_solar_pv.validation import validate_project
from synthetic_support import record,row,put_rows,scalar_item

CAT = Catalog()


def project():
    return ProjectData.new("SYNTHETIC-CONSISTENCY","industrial_rooftop",CAT)


def codes(p):
    return {i.code for i in validate_project(p,CAT)}


def test_predecessor_empty_is_confirmed_no_parent_not_missing_scalar_text():
    p=project()
    put_rows(p,CAT,"schedule.tasks",[row(CAT,"schedule.tasks","first",{"task_id":"A","predecessor_ids":[]})])
    assert not codes(p)
    p.values["schedule.tasks"]["value"][0]["fields"]["schedule.tasks.predecessor_ids"]["value"]="A"
    assert "FIELD_SCHEMA" in codes(p)


def test_unknown_predecessors_do_not_become_empty():
    p=project()
    r=row(CAT,"schedule.tasks","first",{"task_id":"A"})
    r["fields"]["schedule.tasks.predecessor_ids"]=record(CAT,"schedule.tasks.predecessor_ids",None,
        source_kind="UNKNOWN",status="UNKNOWN",instance_id="SYNTHETIC-PRED",missing_reason="SYNTHETIC not confirmed")
    put_rows(p,CAT,"schedule.tasks",[r])
    assert "PREDECESSORS_UNKNOWN" in codes(p)


@pytest.mark.parametrize("kind,expected",[("self","TASK_SELF_REFERENCE"),("missing","TASK_REFERENCE_MISSING"),("cycle","TASK_CYCLE")])
def test_task_graph_rejects_invalid_links_and_cycles(kind,expected):
    p=project();fid="schedule.tasks.predecessor_ids"
    a=scalar_item(CAT,fid,"A" if kind in {"self","cycle"} else "MISSING","SYNTHETIC-PRED-A")
    b=scalar_item(CAT,fid,"B","SYNTHETIC-PRED-B")
    rows=[row(CAT,"schedule.tasks","ra",{"task_id":"A","predecessor_ids":[b] if kind=="cycle" else [a]})]
    if kind=="cycle": rows.append(row(CAT,"schedule.tasks","rb",{"task_id":"B","predecessor_ids":[a]}))
    put_rows(p,CAT,"schedule.tasks",rows)
    assert expected in codes(p)


def test_source_metadata_is_per_atom_and_duplicate_instances_are_rejected():
    p=project()
    a=row(CAT,"load.series","a",{"timestamp":"2024-01-01T00:00:00+08:00","interval_minutes":60,"energy":1})
    b=row(CAT,"load.series","b",{"timestamp":"2024-01-01T01:00:00+08:00","interval_minutes":60,"energy":1})
    b["fields"]["load.series.energy"]["field_instance_id"]=a["fields"]["load.series.energy"]["field_instance_id"]
    put_rows(p,CAT,"load.series",[a,b])
    assert "DUPLICATE_INSTANCE_ID" in codes(p)
    del p.values["load.series"]["value"][0]["fields"]["load.series.energy"]["source_id"]
    assert "FIELD_SCHEMA" in codes(p)


def test_two_timezone_spellings_of_one_instant_are_duplicates():
    p=project()
    rows=[row(CAT,"load.series", "a",{"timestamp":"2024-01-01T08:00:00+08:00","energy":1,"interval_minutes":60}),
          row(CAT,"load.series", "b",{"timestamp":"2024-01-01T00:00:00Z","energy":1,"interval_minutes":60})]
    put_rows(p,CAT,"load.series",rows)
    assert "DUPLICATE_TIMESTAMP" in codes(p)


def test_tariff_halves_cover_a_day_without_overlap_or_midnight_wrap():
    p=project()
    rows=[row(CAT,"tariff.periods","am",{"start_time":"00:00","end_time":"12:00","season":"all","weekday_rule":"all"}),
          row(CAT,"tariff.periods","pm",{"start_time":"12:00","end_time":"24:00","season":"all","weekday_rule":"all"})]
    put_rows(p,CAT,"tariff.periods",rows)
    assert not {"TARIFF_OVERLAP","TARIFF_COVERAGE_GAP","TARIFF_CROSS_MIDNIGHT"}&codes(p)
    p.values["tariff.periods"]["value"][1]["fields"]["tariff.periods.start_time"]["value"]="11:00"
    assert "TARIFF_OVERLAP" in codes(p)


def test_cash_metadata_cannot_mix_price_year_tax_or_currency():
    p=project()
    basis={"currency":"CNY","price_year":2026,"tax_basis":"inclusive","price_basis":"nominal"}
    r=row(CAT,"capex.items","cost",{"quantity":2,"unit_price":100,"amount":200,"currency":"CNY","tax_included":True})
    for name in ["unit_price","amount"]:
        r["fields"]["capex.items."+name]["economic_basis"]=deepcopy(basis)
    r["fields"]["capex.items.amount"]["economic_basis"]["price_year"]=2025
    put_rows(p,CAT,"capex.items",[r])
    assert "ECONOMIC_BASIS_CONFLICT" in codes(p)


def test_negative_price_needs_contract_rule_instead_of_absolute_value():
    p=project()
    r=row(CAT,"tariff.periods","price",{"start_time":"00:00","end_time":"24:00","sale_price":Decimal("-0.1")})
    put_rows(p,CAT,"tariff.periods",[r])
    assert "NEGATIVE_PRICE_REQUIRES_RULE" in codes(p)
    assert r["fields"]["tariff.periods.sale_price"]["value"]==Decimal("-0.1")


def test_quote_amount_lineage_cannot_point_to_another_cost_row():
    p=project()
    a=row(CAT,"capex.items","a",{"quantity":2,"unit_price":100})
    b=row(CAT,"capex.items","b",{"quantity":3,"unit_price":100})
    amount=record(CAT,"capex.items.amount",200,instance_id="SYNTHETIC-COMPUTED-AMOUNT",source_kind="CALCULATED",
        formula_id="F-CAPEX-ITEM-AMOUNT",formula_version=CAT.baseline_version,run_id="SYNTHETIC-RUN",
        upstream_instance_ids=[b["fields"]["capex.items.quantity"]["field_instance_id"],b["fields"]["capex.items.unit_price"]["field_instance_id"]])
    a["fields"]["capex.items.amount"]=amount
    put_rows(p,CAT,"capex.items",[a,b])
    assert "AMOUNT_LINEAGE_ROW_MISMATCH" in codes(p)


def test_wrong_month_days_and_duplicate_months_are_not_filled_or_corrected():
    p=project()
    p.values["resource.period_start"]=record(CAT,"resource.period_start","2024-01-01")
    put_rows(p,CAT,"resource.monthly",[row(CAT,"resource.monthly","feb",{"month":2,"days":28}),
                                    row(CAT,"resource.monthly","feb2",{"month":2,"days":29})])
    old=deepcopy(p.to_dict())
    assert {"RESOURCE_MONTH_DUPLICATE","MONTH_DAYS_MISMATCH"}<=codes(p)
    assert old==p.to_dict()


def test_future_finance_and_generation_values_are_not_accepted_as_input_ids():
    from wangbin_solar_pv.errors import ContractError
    with pytest.raises(ContractError):
        record(CAT,"results.irr",Decimal("0.5"))
    p=project();p.values["targets.payback_years"]=record(CAT,"targets.payback_years",5)
    assert "results.irr" not in p.values
    assert "system.dc_capacity" not in p.values
