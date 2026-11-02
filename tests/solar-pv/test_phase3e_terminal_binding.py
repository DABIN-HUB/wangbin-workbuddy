"""R1-2A binds sourced terminal facts to actual candidate 3B→3C→3D results."""
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal as D
from hashlib import sha256

import pytest

from test_phase3e_financial_candidate_replay import _execute, financial_case
from test_phase3e_terminal_disposition import _source
from wangbin_solar_pv.calculation.terminal_disposition import VERSION

from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.serialization import digest, loads
from wangbin_solar_pv.timeseries_bundle import read_bundle

DOC = (b"SYNTHETIC asset_id=SYNTHETIC-asset no additional recovery "
       b"tax_treatment=NO_DISPOSITION_TAX "
       b"working_capital_treatment=LEDGER_ALREADY_RECOVERED 2027-12-31")


def test_terminal_binding_gate_exists():
    from wangbin_solar_pv.calculation import terminal_binding
    assert callable(terminal_binding.bind_terminal_candidate)


def test_terminal_tax_and_cash_reconciliation_gate_exists():
    from wangbin_solar_pv.calculation import terminal_binding
    assert callable(terminal_binding.reconcile_terminal_cash)


def _candidate(info, replay, *, candidate):
    root, catalog, budget, original, methods, _, _ = info
    replay_root = root / "financial-first"
    export = replay.settlement.candidate_export if candidate else original
    settlement = replay.settlement.candidate_revenue if candidate else replay.settlement.original_revenue
    financial = replay.candidate_financial if candidate else replay.original_financial
    bundle_dir = replay_root / "candidate-d3" if candidate else root / "original"
    generation = loads((root / "generation" / "result.json").read_bytes())
    return export, methods, bundle_dir, generation, settlement, financial, catalog, budget


def _carrier(export, methods, bundle, generation, settlement, financial, *, terminal_date="2027-12-31", document=DOC):
    project = export["project"]
    currency = project["values"]["project.currency"]["value"]
    evaluation = project["values"]["project.evaluation_date"]["value"]
    source = {
        "project_id": project["project_id"], "pv_type": project["pv_type"],
        "evaluation_date": evaluation, "terminal_date": terminal_date, "currency": currency,
        "mode": "NO_DISPOSITION", "covered_asset_ids": ["SYNTHETIC-asset"],
        "events": [],
        "no_disposition": {
            "covered_asset_ids": ["SYNTHETIC-asset"], "reason": "no additional recovery",
            "tax_treatment": "NO_DISPOSITION_TAX",
            "working_capital_treatment": "LEDGER_ALREADY_RECOVERED",
            "source": _source("no additional recovery", document),
        },
    }
    declaration = source["no_disposition"]["source"]
    declaration.update(source_id="SYNTHETIC-asset-clearance", source_timestamp=terminal_date,
                       source_section_or_cell="SYNTHETIC-asset",
                       effective_to=terminal_date, source_content_sha256=sha256(document).hexdigest())
    binding = {
        "project_id": project["project_id"], "pv_type": project["pv_type"],
        "evaluation_date": evaluation, "currency": currency, "scenario_id": financial["scenario_id"],
        "phase2_input_hash": export["input_hash"],
        "phase2_source_snapshot_id": export["source_snapshot_id"],
        "method_config_hash": methods.hash, "d3_content_hash": bundle.content_hash,
        "phase3b_result_hash": generation["result_hash"],
        "phase3c_result_hash": settlement["result_hash"],
        "phase3d_result_hash": financial["result_hash"], "basis": "项目税后",
    }
    return {"schema_version": VERSION, "source": source, "source_content_hash": digest(source), "binding": binding}


@pytest.fixture(scope="module")
def replay_once(financial_case):
    return _execute(financial_case, D("0.6"), "financial-first")


@pytest.fixture(scope="module")
def bound_case(financial_case, replay_once):
    info = _candidate(financial_case, replay_once, candidate=True)
    export, methods, bundle_dir, generation, settlement, financial, catalog, budget = info
    with read_bundle(bundle_dir, catalog=catalog, budget=budget) as bundle:
        carrier = _carrier(export, methods, bundle, generation, settlement, financial)
    return info, carrier


def _bind(info, carrier, *, export=None, settlement=None, financial=None, document=DOC):
    from wangbin_solar_pv.calculation.terminal_binding import bind_terminal_candidate
    baseline, methods, bundle_dir, generation, current, ledger, catalog, budget = info
    with read_bundle(bundle_dir, catalog=catalog, budget=budget) as bundle:
        return bind_terminal_candidate(carrier, {"SYNTHETIC-asset-clearance": document},
                                       export or baseline, methods, bundle, generation,
                                       settlement or current, financial or ledger, catalog)


def test_real_candidate_identity_and_asset_coverage(bound_case, financial_case, replay_once):
    info, carrier = bound_case
    bound = _bind(info, carrier)
    assert bound.source_content_hash == carrier["source_content_hash"]
    assert bound.financial_result_hash == info[5]["result_hash"]
    assert bound.asset_ids == ("SYNTHETIC-asset",)
    original_info = _candidate(financial_case, replay_once, candidate=False)
    with read_bundle(original_info[2], catalog=original_info[6], budget=original_info[7]) as original_bundle:
        original_carrier = _carrier(original_info[0], original_info[1], original_bundle,
                                    original_info[3], original_info[4], original_info[5])
    assert _bind(original_info, original_carrier).source_content_hash == bound.source_content_hash
    assert original_carrier["binding"] != carrier["binding"]
    with pytest.raises(ContractError):
        _bind(info, original_carrier)


@pytest.mark.parametrize("field", [
    "phase3d_result_hash", "phase3c_result_hash", "phase3b_result_hash", "d3_content_hash",
    "phase2_input_hash", "phase2_source_snapshot_id", "method_config_hash", "scenario_id",
    "project_id", "evaluation_date", "basis",
])
def test_mutated_claim_cannot_spoof_current_result(bound_case, field):
    info, carrier = bound_case
    bad = deepcopy(carrier)
    bad["binding"][field] = "项目税前" if field == "basis" else "f" * 64
    if field in {"project_id", "evaluation_date"}:
        bad["source"][field] = bad["binding"][field]
        bad["source_content_hash"] = digest(bad["source"])
    with pytest.raises(ContractError):
        _bind(info, bad)


def test_resealed_mismatched_upstream_and_incomplete_asset_cover_rejected(bound_case):
    from wangbin_solar_pv.calculation.result_contract import seal_result
    info, carrier = bound_case
    bad = deepcopy(info[5])
    bad["inputs"]["upstream_settlement_result_hash"] = "1" * 64
    with pytest.raises(ContractError):
        _bind(info, carrier, financial=seal_result(bad))
    bad = deepcopy(carrier)
    bad["source"]["covered_asset_ids"] = ["not-in-ledger"]
    bad["source"]["no_disposition"]["covered_asset_ids"] = ["not-in-ledger"]
    bad["source_content_hash"] = digest(bad["source"])
    with pytest.raises(ContractError):
        _bind(info, bad)


def test_missing_year_end_method_blocks_cash_and_unproven_events_remain_blocked(bound_case):
    from wangbin_solar_pv.calculation.terminal_binding import reconcile_terminal_cash
    info, carrier = bound_case
    bound = _bind(info, carrier)
    with pytest.raises(ContractError, match="BLOCKED_METHOD_REVIEW: time.cashflow_timing"):
        reconcile_terminal_cash(bound, info[5], info[0], info[1], {"SYNTHETIC-asset-clearance": DOC})
    # Rehashing an unsupported event claim cannot supply 3D booking evidence.
    forged_source = {**bound.source, "mode": "EVENTS"}
    forged = replace(bound, source=forged_source, source_content_hash=digest(forged_source))
    with pytest.raises(ContractError, match="TERMINAL_TRANSACTION_LEDGER_PROOF_MISSING"):
        reconcile_terminal_cash(forged, info[5], info[0], info[1], {"SYNTHETIC-asset-clearance": DOC})
