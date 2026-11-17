"""Independent SYNTHETIC root witness and fail-closed formal certificate."""
from copy import deepcopy
from hashlib import sha256
from decimal import Decimal as D, localcontext
from inspect import signature
from pathlib import Path
from threading import Lock
from types import SimpleNamespace

import pytest

from test_phase3e_financial_candidate_replay import _build_financial_case, _fee_source
from test_phase3e_terminal_binding import _carrier
from test_phase3e_terminal_npv import NO_DOC
from wangbin_solar_pv.calculation.break_even_certification import certify_project_root_set
import wangbin_solar_pv.calculation.break_even_project_session as project_session
from wangbin_solar_pv.calculation.break_even_project_session import ProjectNpvSession
from wangbin_solar_pv.calculation.break_even_replay import replay_price_candidate
from wangbin_solar_pv.calculation.break_even_financial_replay import replay_financial_candidate
from wangbin_solar_pv.calculation.financial_ledger import calculate_financial_ledger
from wangbin_solar_pv.calculation.financial_metrics import evaluate
from wangbin_solar_pv.calculation.phase3e import write_phase3e_bundle
from wangbin_solar_pv.calculation.revenue import calculate_rooftop
from wangbin_solar_pv.calculation.result_contract import empty_result, result_hash, seal_result, validate_result
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.local_files import Workspace
from wangbin_solar_pv.serialization import digest, dumps, loads
from wangbin_solar_pv.timeseries_bundle import BundleBudget, read_bundle

PROJECT = "SYNTHETIC-BC-INDEPENDENT-ROOT"
DOCUMENT = NO_DOC.replace(b"SYNTHETIC-industrial_rooftop", PROJECT.encode("ascii"))


def _independent_npv(price):
    # Fixed independently before executing any candidate. The referenced
    # one-year model has 87,600 kWh export; self-use saving is 140,160 yuan.
    # The separately declared 0.01 CNY/kWh fee is paid once in the same year;
    # high synthetic opex keeps the project's income tax and VAT cash at zero.
    with localcontext() as ctx:
        ctx.prec = 100
        return -D(1330) + (D(65700)*price + D(140160) - D(180000)
                           - D(87600)*D("0.01") + D(200))/D("1.1")


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
        original_fee = _fee_source(exported, methods, baseline, role="original")
        ledger = calculate_financial_ledger(exported, methods, baseline, catalog=catalog,
                                            trading_fee_source_bytes=original_fee)
        carrier = _carrier(exported, methods, original, generation, baseline, ledger,
                           terminal_date="2025-12-31", document=DOCUMENT)
        # Each candidate owns a different derived P2/D3/3C identity. Pre-settle
        # independently: neither the session nor 3D/3E may mint payment bytes.
        with localcontext() as ctx:
            ctx.prec = 100
            reference_root = D(41979) / D(65700)
        fee_sources = {}
        for price, label in ((D(0), "zero"), (D(2), "two"), (reference_root, "reference")):
            upstream = replay_price_candidate(control, exported, methods, original, root/"generation",
                price, catalog=catalog, budget=budget, workspace=Workspace(root),
                run_name="root-witness-fee-binding-" + label)
            assert upstream.original_revenue["result_hash"] == baseline["result_hash"]
            fee_sources[price] = _fee_source(upstream.candidate_export, methods,
                                              upstream.candidate_revenue, role="candidate")
        session = ProjectNpvSession(control, exported, methods, original, root/"generation",
            carrier, {"SYNTHETIC-asset-clearance": DOCUMENT}, catalog=catalog,
            budget=budget, workspace=Workspace(root), run_name="root-witness-session",
            original_trading_fee_source_bytes=original_fee)
        yield base, session, fee_sources


def test_declared_independent_project_has_real_full_chain_root_witness(root_case):
    base, session, fee_sources = root_case
    root, catalog, _, _, _, _, _ = base
    assert session.control["project_id"] == PROJECT
    assert session.original_npv < 0
    assert abs(session.original_npv - _independent_npv(D("0.4"))) < D("1e-18")
    low = session.evaluate(D(0), run_name="root-witness-zero",
                           candidate_trading_fee_source_bytes=fee_sources[D(0)])
    high = session.evaluate(D(2), run_name="root-witness-two",
                            candidate_trading_fee_source_bytes=fee_sources[D(2)])
    assert low.candidate_npv < 0 < high.candidate_npv
    assert abs(low.candidate_npv - _independent_npv(D(0))) < D("1e-18")
    assert abs(high.candidate_npv - _independent_npv(D(2))) < D("1e-18")
    with localcontext() as ctx:
        ctx.prec = 100
        reference_root = D(41979) / D(65700)
    at_root = session.evaluate(reference_root, run_name="root-witness-reference",
                               candidate_trading_fee_source_bytes=fee_sources[reference_root])
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
        assert annual["transaction_cost_accrued"] == D(876)
        assert annual["transaction_cost_cash_paid"] == D(876)
        assert annual["transaction_cost_payable_closing"] == 0
        assert annual["income_tax_cash_paid_project"] == D(0)
        assert annual["cash_tax_total_project"] == D(0)
        assert annual["vat_credit_closing"] > 0
    assert session.counts == {"original_3c": 1, "original_3d": 1, "original_3e": 1,
                              "candidate_3c": 3, "candidate_3d": 3, "candidate_3e": 3}


def test_original_price_is_reused_without_neighboring_fake_price(root_case):
    _, session, _ = root_case
    before = session.counts
    original = session.evaluate(session.original_price, run_name="root-witness-original-lookup")
    assert original.candidate_npv == session.original_npv
    assert original.candidate_result_hash == session.original_result["result_hash"]
    assert session.counts == before


def test_cannot_certify_unproven_executable_root_or_legacy_interpolation(root_case):
    _, session, _ = root_case
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
    _, session, _ = root_case
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


@pytest.mark.parametrize("name", ("original-3c", "original-3d", "original-3e"))
@pytest.mark.parametrize("mutation", ("in_place", "replacement"))
def test_resealed_in_memory_original_cannot_return_unpublished_hash(tmp_path, monkeypatch, name, mutation):
    # Exercise the real published-file pin without rerunning the multi-minute
    # root witness. Results are valid and resealed; only NPV is stubbed because
    # the minimal NOT_IMPLEMENTED results have no project NPV metric.
    monkeypatch.setattr(project_session, "_npv", lambda *_: D(10))
    session = object.__new__(ProjectNpvSession)
    session.control = {"generation_result_hash": "generation"}
    session.original_export = {"input_hash": "input"}
    session.methods = SimpleNamespace(to_dict=lambda: {})
    session.terminal_carrier = {"source_content_hash": "terminal"}
    session.source_documents = {}
    session.original_trading_fee_source_bytes = None
    session.catalog = SimpleNamespace(formulas={}, fields={}, bindings={}, definition_version="test",
                                      definition_hash="definition", baseline_hashes={}, definition_identity=lambda: None)
    session.original_bundle = SimpleNamespace(content_hash="bundle", dataset_ids=(), base_export=session.original_export)
    session.generation_dir = tmp_path / "generation"
    session.generation_dir.mkdir()
    (session.generation_dir / "result.json").write_text("{}", encoding="utf-8")
    (session.generation_dir / "receipt.json").write_text("{}", encoding="utf-8")
    session.budget = BundleBudget()
    session._physical = project_session._physical_files(session.generation_dir, session.budget)
    session._fingerprint = digest({
        "control": session.control, "export": session.original_export,
        "method": session.methods.to_dict(), "carrier": session.terminal_carrier,
        "documents": {}, "original_trading_fee_source_sha256": None,
        "catalog": {"formulas": session.catalog.formulas, "fields": session.catalog.fields,
                    "bindings": session.catalog.bindings, "definition": session.catalog.definition_version},
        "d3": session.original_bundle.content_hash,
        "executor": project_session._executor_identity(),
    })
    session.root = tmp_path / "session"
    session.root.mkdir()
    session._original_published = {}
    session._original_file_hashes = {}
    for stage in ("original-3c", "original-3d", "original-3e"):
        result = empty_result(project_id="SYNTHETIC-PIN", pv_type="industrial_rooftop",
            evaluation_date="2024-12-31", currency="CNY", scenario_id="BASE",
            input_hash="input", source_snapshot_id="snapshot", baseline_hashes={},
            definition_version="test", definition_hash="definition")
        result["evidence"]["stage"] = stage
        result = seal_result(result)
        validate_result(result, session.catalog)
        folder = session.root / stage
        folder.mkdir()
        (folder / "result.json").write_text(dumps(result), encoding="utf-8")
        if stage == "original-3c":
            (folder / "receipt.json").write_text("{}", encoding="utf-8")
        else:
            (folder / "result.sha256").write_text(result["result_hash"], encoding="utf-8")
        session._original_published[stage] = result
        session._original_file_hashes[stage] = project_session._file_hashes(
            folder, session.budget, {"result.json", "receipt.json"} if stage == "original-3c"
            else {"result.json", "result.sha256"})
    session.original_revenue = session._original_published["original-3c"]
    session.original_financial = session._original_published["original-3d"]
    session.original_result = session._original_published["original-3e"]
    session.original_npv = D(10)
    (session.root / "session.json").write_text("{}", encoding="utf-8")
    session._session_receipt = (session.root / "session.json").read_bytes()
    session.original_price = D("0.5")
    session.price_min, session.price_max = D(0), D(2)
    session.run_name = "session"
    session._lock = Lock()
    published_hash = session.original_result["result_hash"]
    assert session.evaluate(session.original_price, run_name="published-original-lookup").original_result_hash == published_hash
    memory_result = (deepcopy(session._original_published[name]) if mutation == "replacement"
                     else session._original_published[name])
    memory_result["evidence"]["resealed"] = True
    memory_result["result_hash"] = result_hash(memory_result)
    validate_result(memory_result, session.catalog)
    if mutation == "replacement":
        setattr(session, {"original-3c": "original_revenue", "original-3d": "original_financial",
                          "original-3e": "original_result"}[name], memory_result)
    assert memory_result["result_hash"] != loads(
        (session.root / name / "result.json").read_bytes())["result_hash"]
    with pytest.raises(ContractError, match="BREAK_EVEN_ORIGINAL_CACHE_IDENTITY"):
        session.evaluate(session.original_price, run_name="unpublished-original-lookup")


def test_session_executor_pins_trading_fee_validator_and_its_schema():
    identity = project_session._executor_identity()
    executor_dir = Path(project_session.__file__).parent
    for relative in ("trading_fee_payment.py", "schema/trading-fee-payment.schema.json"):
        assert identity[relative] == sha256((executor_dir / relative).read_bytes()).hexdigest()
