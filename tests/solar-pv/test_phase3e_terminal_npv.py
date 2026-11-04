"""Full real SYNTHETIC 3B→3C→3D→sourced 3E year-end project NPV."""
from copy import deepcopy
from contextlib import nullcontext
from decimal import Decimal as D, localcontext

import pytest

from test_phase3e_financial_candidate_replay import _build_financial_case, _execute
from test_phase3e_terminal_binding import _carrier
from wangbin_solar_pv.calculation.result_contract import validate_result
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.serialization import digest, dumps, loads
from wangbin_solar_pv.timeseries_bundle import read_bundle

NO_DOC = (b"SYNTHETIC asset_id=SYNTHETIC-asset no additional recovery "
          b"tax_treatment=NO_DISPOSITION_TAX "
          b"working_capital_treatment=LEDGER_ALREADY_RECOVERED "
          b"project_id=SYNTHETIC-industrial_rooftop terminal_date=2025-12-31")


def test_sourced_npv_entry_exists():
    from wangbin_solar_pv.calculation.phase3e import calculate_sourced_project_npv
    assert callable(calculate_sourced_project_npv)


@pytest.fixture(scope="module")
def npv_case():
    base = _build_financial_case(evaluation_date="2024-12-31", project_rate=D("0.1"))
    first = _execute(base, D("0.6"), "npv-six")
    second = _execute(base, D("0.8"), "npv-eight")
    return base, first, second


def _calculation(base, replay, replay_name, candidate, *, override=None,
                 document=NO_DOC, source_document=None, repeat_after_json=False):
    from wangbin_solar_pv.calculation.phase3e import calculate_sourced_project_npv
    root, catalog, budget, exported, methods, control, _ = base
    export = replay.settlement.candidate_export if candidate else exported
    settlement = replay.settlement.candidate_revenue if candidate else replay.settlement.original_revenue
    financial = replay.candidate_financial if candidate else replay.original_financial
    bundle_dir = root / replay_name / "candidate-d3" if candidate else root / "original"
    generation = loads((root / "generation" / "result.json").read_bytes())
    with read_bundle(root / "original", catalog=catalog, budget=budget) as original_bundle:
        candidate_context = (read_bundle(bundle_dir, catalog=catalog, budget=budget)
                             if candidate else nullcontext(original_bundle))
        with candidate_context as bundle:
            carrier = _carrier(export, methods, bundle, generation, settlement, financial,
                               terminal_date="2025-12-31", document=document)
            if override is not None:
                override(carrier)
            result = calculate_sourced_project_npv(
                carrier, {"SYNTHETIC-asset-clearance": document if source_document is None else source_document}, export,
                methods, bundle, generation, settlement, financial, catalog,
                basis_control=control, original_export=exported, original_bundle=original_bundle)
            if repeat_after_json:
                roundtrip = lambda value: loads(dumps(value))
                replayed = calculate_sourced_project_npv(
                    roundtrip(carrier), {"SYNTHETIC-asset-clearance": document}, roundtrip(export),
                    methods, bundle, roundtrip(generation), roundtrip(settlement), roundtrip(financial), catalog,
                    basis_control=roundtrip(control), original_export=roundtrip(exported),
                    original_bundle=original_bundle)
                validate_result(replayed, catalog)
                assert replayed["result_hash"] == result["result_hash"]
    validate_result(result, catalog)
    return carrier, result, financial


def _metric(result, name):
    return next(m for m in result["results"]["metrics"] if m["metric_id"] == name)


def test_no_disposition_has_independent_decimal_cashflow_and_npv(npv_case):
    base, replay, other = npv_case
    observed = []
    for result_set, name, candidate, price in (
        (replay, "npv-six", False, D("0.4")),
        (replay, "npv-six", True, D("0.6")),
        (other, "npv-eight", True, D("0.8")),
    ):
        carrier, result, financial = _calculation(base, result_set, name, candidate,
                                                  repeat_after_json=price == D("0.6"))
        year = financial["evidence"]["financial-ledger"]["annual"][1]
        sale = D("87600") * price
        assert year["invoiced_gross"] == sale
        assert year["revenue_cash_receipts"] == sale * D("0.75")
        assert year["working_capital_release"] == D("200")
        # Phase 3D's approved tax schedule uses the default 28-digit Decimal
        # context; Phase 3E's frozen financial kernels then use 80 digits.
        with localcontext() as ctx:
            ctx.prec = 28
            tax_base = sale - D("100") - D("1000")
            tax_paid = max(D(0), tax_base - D("34000")) * D("0.25") * D("0.5")
            vat_paid = sale - sale / D("1.13") - D("143")
        assert year["cash_tax_total_project"] == tax_paid + vat_paid
        with localcontext() as ctx:
            ctx.prec = 80
            expected = [D("-1330"), sale * D("0.75") + year["self_use_avoided_expenditure"]
                        - D("113") - tax_paid - vat_paid + D("200")]
            expected_npv = expected[0] + expected[1] / D("1.1")
        bridge = result["evidence"]["phase3e-terminal-reconciliation"]
        assert bridge["terminal_cash"] == [D(0), D(0)]
        assert bridge["additional_project_tax"] == [D(0), D(0)]
        assert bridge["ledger_income_tax"][1] == tax_paid
        assert bridge["ledger_vat_cash_net_of_refunds"][1] == vat_paid
        assert bridge["working_capital_release_already_in_ledger"] == D("200")
        assert _metric(result, "financial.phase3e.project_cash_flow")["value"] == expected
        assert _metric(result, "financial.phase3e.project_pretax_cash_flow")["value"][1] - expected[1] == tax_paid
        assert abs(_metric(result, "financial.phase3e.project_npv")["value"] - expected_npv) < D("1e-55")
        assert "finance.project_discount_rate" in _metric(result, "financial.phase3e.project_npv")["input_field_ids"]
        irr = _metric(result, "financial.phase3e.project_irr")
        assert irr["status"] == "BLOCKED_MISSING_INPUT" and irr["value"] is None
        assert irr["reason"] == "IRR_METHOD_CONTROLS_INCOMPLETE"
        assert set(irr["details"]["missing_method_parameter_ids"]) == {
            "irr.method", "irr.minimum_rate", "irr.maximum_rate",
            "irr.root_tolerance", "irr.maximum_degree",
        }
        assert _metric(result, "financial.phase3e.dated-npv")["status"] == "BLOCKED_MISSING_INPUT"
        assert result["status"] == "PARTIAL" and result["maturity"]["real_project"] == "NOT_VERIFIED"
        assert result["evidence"]["phase3e-financial"]["terminal_cash"] != "BLOCKED_MISSING_INPUT"
        assert result["source_snapshot"]["phase3e_terminal"]["phase3d_result_hash"] == financial["result_hash"]
        from wangbin_solar_pv.calculation.phase3e import write_phase3e_bundle
        target = base[0] / name / ("candidate-3e" if candidate else "original-3e")
        write_phase3e_bundle(result, target)
        published = loads((target / "result.json").read_bytes())
        validate_result(published, base[1])
        assert published["result_hash"] == result["result_hash"]
        assert (target / "result.sha256").read_text().strip() == result["result_hash"]
        observed.append((carrier, result, expected))
    assert len({item[0]["source_content_hash"] for item in observed}) == 1
    assert len({item[1]["result_hash"] for item in observed}) == 3
    assert len({digest(item[0]["binding"]) for item in observed}) == 3
    assert len({tuple(item[2]) for item in observed}) == 3


def test_rebound_old_candidate_and_unknown_terminal_date_never_publish_npv(npv_case):
    base, replay, other = npv_case
    baseline, _, _ = _calculation(base, replay, "npv-six", False)
    def old_claim(carrier):
        carrier["binding"] = deepcopy(baseline["binding"])
    with pytest.raises(ContractError):
        _calculation(base, replay, "npv-six", True, override=old_claim)
    def wrong_date(carrier):
        carrier["source"]["terminal_date"] = "2026-12-31"
        carrier["source_content_hash"] = digest(carrier["source"])
    with pytest.raises(ContractError):
        _calculation(base, replay, "npv-six", True, override=wrong_date)
    with pytest.raises(ContractError, match="TERMINAL_SOURCE_BYTES_MISMATCH"):
        _calculation(base, replay, "npv-six", True, source_document=NO_DOC + b" altered")
    without_project = NO_DOC.replace(b"project_id=SYNTHETIC-industrial_rooftop ", b"")
    with pytest.raises(ContractError, match="TERMINAL_SOURCE_SCOPE_UNPROVEN"):
        _calculation(base, replay, "npv-six", True, document=without_project)
    def synthetic_as_verified(carrier):
        carrier["source"]["no_disposition"]["source"]["source_status"] = "VERIFIED"
        carrier["source_content_hash"] = digest(carrier["source"])
    with pytest.raises(ContractError, match="SYNTHETIC_IS_NOT_VERIFIED"):
        _calculation(base, replay, "npv-six", True, override=synthetic_as_verified)
