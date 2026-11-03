"""Independent SYNTHETIC root witness and fail-closed formal certificate."""
from decimal import Decimal as D, localcontext
from inspect import signature

import pytest

from test_phase3e_financial_candidate_replay import _build_financial_case
from test_phase3e_terminal_binding import _carrier
from test_phase3e_terminal_npv import NO_DOC
from wangbin_solar_pv.calculation.break_even_certification import certify_project_root_set
from wangbin_solar_pv.calculation.break_even_project_session import ProjectNpvSession
from wangbin_solar_pv.calculation.break_even_replay import replay_price_candidate
from wangbin_solar_pv.calculation.break_even_financial_replay import replay_financial_candidate
from wangbin_solar_pv.calculation.financial_ledger import calculate_financial_ledger
from wangbin_solar_pv.calculation.financial_metrics import evaluate
from wangbin_solar_pv.calculation.phase3e import write_phase3e_bundle
from wangbin_solar_pv.calculation.revenue import calculate_rooftop
from wangbin_solar_pv.calculation.result_contract import validate_result
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.local_files import Workspace
from wangbin_solar_pv.serialization import loads
from wangbin_solar_pv.timeseries_bundle import read_bundle

PROJECT = "SYNTHETIC-BC-INDEPENDENT-ROOT"
DOCUMENT = NO_DOC.replace(b"SYNTHETIC-industrial_rooftop", PROJECT.encode("ascii"))


def _independent_npv(price):
    # Fixed independently before executing any candidate. The referenced
    # one-year model has 87,600 kWh export; self-use saving is 140,160 yuan.
    with localcontext() as ctx:
        ctx.prec = 100
        return -D(1330) + (D(65700)*price + D(140160) - D(180000) + D(200))/D("1.1")


@pytest.fixture(scope="module")
def root_case():
    base = _build_financial_case(evaluation_date="2024-12-31", project_rate=D("0.1"),
        project_id=PROJECT, opex_amount=D("180000"))
    root, catalog, budget, exported, methods, control, generation_hash = base
    generation = loads((root/"generation"/"result.json").read_bytes())
    with read_bundle(root/"original", catalog=catalog, budget=budget) as original:
        baseline = calculate_rooftop(exported, methods, generation_dir=root/"generation",
            generation_result_hash=generation_hash, catalog=catalog,
            output_dir=root/"root-witness-original-3c", budget=budget, bundle=original)
        ledger = calculate_financial_ledger(exported, methods, baseline, catalog=catalog)
        carrier = _carrier(exported, methods, original, generation, baseline, ledger,
                           terminal_date="2025-12-31", document=DOCUMENT)
        session = ProjectNpvSession(control, exported, methods, original, root/"generation",
            carrier, {"SYNTHETIC-asset-clearance": DOCUMENT}, catalog=catalog,
            budget=budget, workspace=Workspace(root), run_name="root-witness-session")
        yield base, session


def test_declared_independent_project_has_real_full_chain_root_witness(root_case):
    base, session = root_case
    root, catalog, _, _, _, _, _ = base
    assert session.control["project_id"] == PROJECT
    assert session.original_npv < 0
    assert abs(session.original_npv - _independent_npv(D("0.4"))) < D("1e-18")
    low = session.evaluate(D(0), run_name="root-witness-zero")
    high = session.evaluate(D(2), run_name="root-witness-two")
    assert low.candidate_npv < 0 < high.candidate_npv
    assert abs(low.candidate_npv - _independent_npv(D(0))) < D("1e-18")
    assert abs(high.candidate_npv - _independent_npv(D(2))) < D("1e-18")
    with localcontext() as ctx:
        ctx.prec = 100
        reference_root = D(4567) / D(7300)
    at_root = session.evaluate(reference_root, run_name="root-witness-reference")
    assert abs(at_root.candidate_npv) < D("1e-18")
    assert at_root.price == reference_root
    assert at_root.terminal_source_hash == low.terminal_source_hash == high.terminal_source_hash
    assert len({at_root.candidate_result_hash, low.candidate_result_hash,
                high.candidate_result_hash}) == 3
    for name in ("root-witness-zero", "root-witness-two", "root-witness-reference"):
        receipt = loads((root/name/"phase3e"/"execution.json").read_bytes())
        result = loads((root/name/"phase3e"/"candidate-3e"/"result.json").read_bytes())
        validate_result(result, catalog)
        assert receipt["original_reused"] is True
        assert receipt["phase3c_calculations"] == receipt["phase3d_calculations"] == receipt["phase3e_calculations"] == 1
        assert receipt["candidate_result_hash"] == result["result_hash"]
        annual = result["evidence"]["financial-ledger"]["annual"][1]
        assert annual["income_tax_cash_paid_project"] == D(0)
        assert annual["cash_tax_total_project"] == D(0)
        assert annual["vat_credit_closing"] > 0
    assert session.counts == {"original_3c": 1, "original_3d": 1, "original_3e": 1,
                              "candidate_3c": 3, "candidate_3d": 3, "candidate_3e": 3}


def test_original_price_is_reused_without_neighboring_fake_price(root_case):
    _, session = root_case
    before = session.counts
    original = session.evaluate(session.original_price, run_name="root-witness-original-lookup")
    assert original.candidate_npv == session.original_npv
    assert original.candidate_result_hash == session.original_result["result_hash"]
    assert session.counts == before


def test_cannot_certify_unproven_executable_root_or_legacy_interpolation(root_case):
    _, session = root_case
    legacy = evaluate("F-BREAK-EVEN-PRICE", {
        "sensitivity.price_search_domain": [D(0), D(2)],
        "sensitivity.price_cash_flow_vector": {"prices": [D(0), D(2)],
                                                 "cash_flows": [[D(-1), D(-1)], [D(-1), D(3)]]},
        "finance.npv": D(0),
        "finance.selected_discount_rate": D(0), "finance.cash_flow_basis": "PROJECT_POST_TAX",
    })
    assert legacy["status"] == "CALCULATED"
    assert legacy["details"]["method"] == "PIECEWISE_AFFINE_SAMPLE_INTERPOLATION"
    formal = certify_project_root_set(session)
    validate_result(formal, session.catalog)
    metric = next(m for m in formal["results"]["metrics"]
                  if m["metric_id"] == "financial.phase3e.break-even-price")
    assert metric["status"] == "BLOCKED_MISSING_INPUT" and metric["value"] is None
    assert metric["reason"] == "BLOCKED_ROOT_SET_COMPLETENESS_UNPROVEN"
    assert formal["evidence"]["phase3e-break-even-root-certification"]["root_count_certified"] is None
    assert formal["result_hash"] != session.original_result["result_hash"]
    assert "PIECEWISE_AFFINE_SAMPLE_INTERPOLATION" not in str(formal["evidence"]["phase3e-break-even-root-certification"])
    write_phase3e_bundle(formal, session.workspace.path("root-witness-blocked-certification", json_only=False))
    assert "original_revenue" not in signature(replay_price_candidate).parameters
    assert "original_financial" not in signature(replay_financial_candidate).parameters


def test_in_place_source_or_control_changes_invalidate_original_cache(root_case):
    _, session = root_case
    original = session.control["basis"]
    session.control["basis"] = "项目税前"
    try:
        with pytest.raises(ContractError, match="BREAK_EVEN_SESSION_SOURCE_CHANGED"):
            session.evaluate(D("0.7"), run_name="root-witness-rejected")
    finally:
        session.control["basis"] = original
    assert not session.workspace.path("root-witness-rejected", json_only=False).exists()
    sidecar = session.root / "original-3e" / "result.sha256"
    original_sidecar = sidecar.read_bytes()
    sidecar.write_bytes(b"tampered\n")
    try:
        with pytest.raises(ContractError, match="BREAK_EVEN_SESSION_SOURCE_CHANGED"):
            session.evaluate(D("0.7"), run_name="root-witness-tampered-sidecar")
    finally:
        sidecar.write_bytes(original_sidecar)
    assert not session.workspace.path("root-witness-tampered-sidecar", json_only=False).exists()
    with pytest.raises(ContractError, match="BREAK_EVEN_CANDIDATE_PRICE"):
        session.evaluate(D(-1), run_name="root-witness-negative")
