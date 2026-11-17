"""Bounded synthetic date-event source acceptance; no real-client data."""
from copy import deepcopy
from datetime import date
from decimal import Decimal as D, localcontext
from hashlib import sha256

import pytest

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.calculation.dated_cash_events import (
    VERSION, validate_dated_cash_events,
)
from wangbin_solar_pv.calculation.financial_metrics import evaluate
from wangbin_solar_pv.calculation.method_config import METHOD_SCHEMA_VERSION, MethodConfig, make_parameter
from wangbin_solar_pv.calculation.phase3e import _BOUNDARY, _record_sourced_dated_npv
from wangbin_solar_pv.calculation.result_contract import empty_result, seal_result, validate_result
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.serialization import digest

_CSV = (b"kind,event_id,date,period,amount,source_id\n"
        b"RATE,,,DATED_DISCOUNT_RATE,0.1,SYNTHETIC-dated-rate\n"
        b"EVENT,base-1,2024-12-31,CONSTRUCTION,-100,SYNTHETIC-dated-events\n"
        b"EVENT,year-1,2025-06-30,OPERATING_YEAR_1,30,SYNTHETIC-dated-events\n"
        b"EVENT,year-2,2026-12-31,OPERATING_YEAR_2,90,SYNTHETIC-dated-events\n")
_CASH = [D("-100"), D("30"), D("90")]


def _source(source_id, content_hash):
    return {"source_id": source_id, "source_reference": "SYNTHETIC dated case appendix A",
            "source_kind": "SYNTHETIC", "status": "ASSUMED", "license_status": "AUTHORIZED",
            "reviewer": None, "source_content_sha256": content_hash,
            "source_location": "synthetic.csv:source_row"}


def _case():
    methods = {"schema_version": METHOD_SCHEMA_VERSION, "config_id": "synthetic-dated-case",
               "data_mode": "SYNTHETIC", "pv_types": ["industrial_rooftop"],
               "parameters": {"time.day_count": make_parameter(
                   "time.day_count", "ACT_365F", source_id="SYNTHETIC-day-count",
                   source_reference="SYNTHETIC dated case appendix B", status="ASSUMED",
                   source_kind="SYNTHETIC", license_status="AUTHORIZED",
                   pv_types=["industrial_rooftop"])}}
    exported = {"project": {"project_id": "SYNTHETIC-dated-project",
                            "pv_type": "industrial_rooftop", "values": {
                                "project.currency": {"value": "CNY"},
                                "project.price_basis": {"value": "nominal"},
                                "project.evaluation_date": {"value": "2024-12-31"},
                                "schedule.commissioning_date": {"value": "2025-01-01"}}},
                "input_hash": "a" * 64}
    financial = {"result_hash": "b" * 64}
    content_hash = sha256(_CSV).hexdigest()
    carrier = {"schema_version": VERSION,
               "binding": {"project_id": "SYNTHETIC-dated-project",
                           "pv_type": "industrial_rooftop", "scenario_id": "BASE",
                           "currency": "CNY", "cashflow_basis": "post_tax",
                           "price_basis": "nominal",
                           "evaluation_date": "2024-12-31", "terminal_date": "2026-12-31",
                           "phase2_input_hash": exported["input_hash"],
                           "method_config_hash": digest(methods),
                           "phase3d_result_hash": financial["result_hash"],
                           "selected_cash_flow_hash": digest(_CASH)},
               "source_content_sha256": content_hash,
               "event_source": _source("SYNTHETIC-dated-events", content_hash),
               "rate_source": {**_source("SYNTHETIC-dated-rate", content_hash),
                               "rate_scope": "PROJECT_POST_TAX_NOMINAL_CNY_DATED"},
               "discount_rate": D("0.1"),
               "events": [{"event_id": "base-1", "date": "2024-12-31", "period": "CONSTRUCTION",
                           "amount": D("-100"), "source_id": "SYNTHETIC-dated-events"},
                          {"event_id": "year-1", "date": "2025-06-30", "period": "OPERATING_YEAR_1",
                           "amount": D("30"), "source_id": "SYNTHETIC-dated-events"},
                          {"event_id": "year-2", "date": "2026-12-31", "period": "OPERATING_YEAR_2",
                           "amount": D("90"), "source_id": "SYNTHETIC-dated-events"}]}
    return carrier, _CSV, exported, methods, financial


def _validate(carrier, raw, export, methods, financial):
    return validate_dated_cash_events(
        carrier, raw, exported=export, methods=methods, financial=financial,
        scenario_id="BASE", cashflow_basis="post_tax", selected_cash_flow=_CASH,
        terminal_date="2026-12-31")


def _reject(code, carrier, raw, export, methods, financial):
    with pytest.raises(ContractError) as error:
        _validate(carrier, raw, export, methods, financial)
    assert error.value.code == code


def test_independent_synthetic_table_recalculates_dated_npv_without_annual_substitution(tmp_path):
    carrier, raw, export, methods, financial = _case()
    original = tmp_path / "independent-synthetic-cash-events.csv"
    original.write_bytes(raw)
    dated = _validate(carrier, original.read_bytes(), export, methods, financial)
    assert dated.source_sha256 == sha256(original.read_bytes()).hexdigest()
    assert dated.year_fractions[0] == 0
    with localcontext() as ctx:
        ctx.prec = 80
        independent_fractions = tuple(
            D((date.fromisoformat(event["date"]) - date(2024, 12, 31)).days) / D(365)
            for event in carrier["events"])
        assert dated.year_fractions == independent_fractions
        expected = sum((amount / (D("1.1") ** tau)
                        for amount, tau in zip(_CASH, independent_fractions)), D(0))
        annual = sum((amount / D("1.1") ** year for year, amount in enumerate(_CASH)), D(0))
        actual = evaluate("F-DATED-NPV", {
            "finance.cash_event_ids": [e["event_id"] for e in carrier["events"]],
            "finance.dated_cash_flows": list(dated.amounts),
            "finance.cash_event_year_fraction": list(dated.year_fractions),
            "finance.selected_discount_rate": dated.discount_rate,
            "finance.cash_flow_basis": "项目税后"})
    assert actual["status"] == "CALCULATED" and abs(actual["value"] - expected) < D("1e-55")
    assert actual["value"] != annual


def test_missing_terminal_event_blocks_coverage():
    carrier, raw, export, methods, financial = _case()
    carrier["events"].pop()
    raw = raw.rsplit(b"EVENT,year-2", 1)[0]
    content_hash = sha256(raw).hexdigest()
    carrier["source_content_sha256"] = content_hash
    for key in ("event_source", "rate_source"):
        carrier[key]["source_content_sha256"] = content_hash
    _reject("DATED_CASH_PERIOD_COVERAGE", carrier, raw, export, methods, financial)


def test_duplicate_event_id_blocks_even_when_csv_matches():
    carrier, raw, export, methods, financial = _case()
    carrier["events"][1]["event_id"] = "base-1"
    _reject("DATED_CASH_DUPLICATE_EVENT", carrier, raw, export, methods, financial)


def test_wrong_raw_digest_blocks():
    carrier, raw, export, methods, financial = _case()
    carrier["source_content_sha256"] = "0" * 64
    _reject("DATED_CASH_SOURCE_HASH_MISMATCH", carrier, raw, export, methods, financial)


def test_wrong_cashflow_basis_blocks():
    carrier, raw, export, methods, financial = _case()
    carrier["binding"]["cashflow_basis"] = "pre_tax"
    _reject("DATED_CASH_SOURCE_BINDING_MISMATCH", carrier, raw, export, methods, financial)


def test_unreviewed_source_blocks():
    carrier, raw, export, methods, financial = _case()
    carrier["event_source"]["license_status"] = "REQUIRES_REVIEW"
    _reject("DATED_CASH_SOURCE_UNREVIEWED", carrier, raw, export, methods, financial)


def test_missing_day_count_source_blocks():
    carrier, raw, export, methods, financial = _case()
    del methods["parameters"]["time.day_count"]
    _reject("BLOCKED_METHOD_REVIEW", carrier, raw, export, methods, financial)


def test_changed_upstream_ledger_blocks():
    carrier, raw, export, methods, financial = _case()
    financial["result_hash"] = "c" * 64
    _reject("DATED_CASH_SOURCE_BINDING_MISMATCH", carrier, raw, export, methods, financial)


def test_synthetic_date_source_records_a_sealed_phase3e_metric():
    carrier, raw, export, config, financial = _case()
    catalog = Catalog()
    result = empty_result(
        project_id="SYNTHETIC-dated-project", pv_type="industrial_rooftop",
        evaluation_date="2024-12-31", currency="CNY", scenario_id="BASE",
        input_hash="x" * 64, source_snapshot_id="x" * 64,
        baseline_hashes=catalog.baseline_hashes,
        definition_version=catalog.definition_version, definition_hash=catalog.definition_hash)
    result["boundaries"][_BOUNDARY] = {"phase": "3E", "cashflow_timing": "DATE_EVENT"}
    result["source_snapshot"]["methods"] = deepcopy(config)
    result["inputs"]["identity_payload"] = {"source_snapshot_id": "x" * 64}
    result["evidence"]["phase3e-financial"] = {}
    outcome = _record_sourced_dated_npv(
        result, catalog, export, MethodConfig.from_dict(config), financial,
        carrier, raw, "项目税后", _CASH, "2026-12-31")
    assert outcome["status"] == "CALCULATED"
    assert outcome["value"] == result["results"]["metrics"][0]["value"]
    assert outcome["value"] == result["evidence"]["phase3e-financial"]["dated_npv"]
    assert result["inputs"]["identity_payload"]["dated_cash_source_sha256"] == sha256(raw).hexdigest()
    assert validate_result(seal_result(result), catalog)["results"]["metrics"][0]["status"] == "CALCULATED"


def test_event_outside_declared_operating_year_blocks():
    carrier, raw, export, methods, financial = _case()
    carrier["events"][1]["date"] = "2026-06-30"
    raw = raw.replace(b"EVENT,year-1,2025-06-30", b"EVENT,year-1,2026-06-30")
    content_hash = sha256(raw).hexdigest()
    carrier["source_content_sha256"] = content_hash
    for key in ("event_source", "rate_source"):
        carrier[key]["source_content_sha256"] = content_hash
    _reject("DATED_CASH_EVENT_PERIOD", carrier, raw, export, methods, financial)


def test_independent_rate_and_event_source_ids_cannot_collide():
    carrier, raw, export, methods, financial = _case()
    carrier["rate_source"]["source_id"] = carrier["event_source"]["source_id"]
    _reject("DATED_CASH_SOURCE_ID_CONFLICT", carrier, raw, export, methods, financial)


def test_large_cancelling_cash_events_cannot_hide_a_small_unreconciled_amount():
    carrier, raw, export, methods, financial = _case()
    extra = (("large", "100000000000000000000000000000"),
             ("small", "0.01"),
             ("large-offset", "-100000000000000000000000000000"))
    events = [{"event_id": event_id, "date": "2025-06-30", "period": "OPERATING_YEAR_1",
               "amount": D(amount), "source_id": "SYNTHETIC-dated-events"}
              for event_id, amount in extra]
    carrier["events"][1:1] = events
    insert = b"".join(f"EVENT,{event_id},2025-06-30,OPERATING_YEAR_1,{amount},SYNTHETIC-dated-events\n".encode()
                      for event_id, amount in extra)
    raw = raw.replace(b"EVENT,year-1", insert + b"EVENT,year-1")
    source_hash = sha256(raw).hexdigest()
    carrier["source_content_sha256"] = source_hash
    carrier["event_source"]["source_content_sha256"] = source_hash
    carrier["rate_source"]["source_content_sha256"] = source_hash
    _reject("DATED_CASH_LEDGER_RECONCILIATION", carrier, raw, export, methods, financial)
