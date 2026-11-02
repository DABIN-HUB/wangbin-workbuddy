"""Sourced one-price full-chain project NPV; no root claim from samples."""
from decimal import Decimal as D, localcontext

import pytest

from test_phase3e_terminal_binding import _carrier
from test_phase3e_terminal_npv import NO_DOC, npv_case
from wangbin_solar_pv.calculation.break_even_project_npv import calculate_price_project_npv
from wangbin_solar_pv.calculation.result_contract import validate_result
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.local_files import Workspace
from wangbin_solar_pv.serialization import loads
from wangbin_solar_pv.timeseries_bundle import read_bundle


def test_one_candidate_recalculates_original_and_sourced_project_npv(npv_case):
    base, replay, _ = npv_case
    root, catalog, budget, exported, methods, control, generation_hash = base
    generation = loads((root / "generation" / "result.json").read_bytes())
    with read_bundle(root / "original", catalog=catalog, budget=budget) as original_bundle:
        carrier = _carrier(
            exported, methods, original_bundle, generation,
            replay.settlement.original_revenue, replay.original_financial,
            terminal_date="2025-12-31", document=NO_DOC)
        result = calculate_price_project_npv(
            control, exported, methods, original_bundle, root / "generation", D("0.6"),
            carrier, {"SYNTHETIC-asset-clearance": NO_DOC}, catalog=catalog, budget=budget,
            workspace=Workspace(root), run_name="npv-callback-six")
    with localcontext() as ctx:
        ctx.prec = 28
        sale = D("87600") * D("0.6")
        income_paid = max(D(0), sale - D("100") - D("1000") - D("34000")) * D("0.25") * D("0.5")
        vat_paid = sale - sale / D("1.13") - D("143")
    with localcontext() as ctx:
        ctx.prec = 80
        # Only the original physical 3B self-use evidence is price-invariant.
        self_use = replay.candidate_financial["evidence"]["financial-ledger"]["annual"][1]["self_use_avoided_expenditure"]
        expected = -D("1330") + (sale * D("0.75") + self_use
                                  - D("113") - income_paid - vat_paid + D("200")) / D("1.1")
    assert abs(result.candidate_npv - expected) < D("1e-55")
    assert result.original_npv > 0 and result.candidate_npv > 0
    assert result.candidate_result_hash != result.original_result_hash
    assert result.terminal_source_hash == carrier["source_content_hash"]
    assert result.phase3b_result_hash == generation_hash
    assert result.phase3c_result_hash == replay.settlement.candidate_revenue["result_hash"]
    assert result.phase3d_result_hash == replay.candidate_financial["result_hash"]
    assert result.elapsed_seconds > 0
    receipt = loads((root / "npv-callback-six" / "phase3e" / "execution.json").read_bytes())
    assert receipt["candidate_price"] == D("0.6")
    assert receipt["candidate_npv"] == result.candidate_npv
    assert receipt["candidate_result_hash"] == result.candidate_result_hash
    assert receipt["elapsed_seconds"] == D(str(result.elapsed_seconds))
    assert (receipt["replay_calls"], receipt["phase3c_calculations"],
            receipt["phase3d_calculations"], receipt["phase3e_calculations"]) == (1, 2, 2, 2)
    for side in ("original", "candidate"):
        target = root / "npv-callback-six" / "phase3e" / f"{side}-3e"
        published = loads((target / "result.json").read_bytes())
        validate_result(published, catalog)
        assert published["result_hash"] == getattr(result, f"{side}_result_hash")
        assert (target / "result.sha256").read_text().strip() == published["result_hash"]
        break_even = next(m for m in published["results"]["metrics"]
                          if m["formula_id"] == "F-BREAK-EVEN-PRICE")
        assert break_even["status"] != "CALCULATED"


def test_altered_source_bytes_rejected_before_replay(npv_case):
    base, replay, _ = npv_case
    root, catalog, budget, exported, methods, control, _ = base
    generation = loads((root / "generation" / "result.json").read_bytes())
    with read_bundle(root / "original", catalog=catalog, budget=budget) as original_bundle:
        carrier = _carrier(
            exported, methods, original_bundle, generation,
            replay.settlement.original_revenue, replay.original_financial,
            terminal_date="2025-12-31", document=NO_DOC)
        with pytest.raises(ContractError, match="TERMINAL_SOURCE_BYTES_MISMATCH"):
            calculate_price_project_npv(
                control, exported, methods, original_bundle, root / "generation", D("0.7"),
                carrier, {"SYNTHETIC-asset-clearance": NO_DOC + b" altered"},
                catalog=catalog, budget=budget, workspace=Workspace(root),
                run_name="npv-callback-invalid")
    assert not (root / "npv-callback-invalid").exists()
