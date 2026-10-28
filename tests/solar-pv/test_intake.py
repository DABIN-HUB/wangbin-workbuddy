"""H/M/N: local multi-round state transitions, never computed investment results."""
from copy import deepcopy
from decimal import Decimal
import pytest
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.errors import ContractError

CAT=Catalog()


def session():
    from wangbin_solar_pv.intake import IntakeSession
    return IntakeSession.new("SYNTHETIC-INTAKE","industrial_rooftop",CAT)


def test_minimal_round_normalizes_capacity_and_never_derives_cost_from_target():
    s=session()
    result=s.submit("round1",[{"field_id":"site.address","value":"SYNTHETIC explicit location"},
        {"field_id":"system.dc_capacity","value":1,"unit":"MWp"},
        {"field_id":"targets.payback_years","value":5,"unit":"year"}],expected_revision=0)
    assert result["revision"]==1 and not result["duplicate"]
    assert s.project.values["system.dc_capacity"]["value"]==Decimal("1000")
    assert "capex.items" not in s.project.values
    assert len(result["maturity"]["next_questions"])<=5
    assert s.project.values["system.dc_capacity"]["status"]=="UNVERIFIED"


def test_submission_is_idempotent_but_id_reuse_with_other_data_is_rejected():
    s=session();updates=[{"field_id":"site.total_area","value":1000,"unit":"m2"}]
    s.submit("same",updates,expected_revision=0);before=s.project.to_dict()
    assert s.submit("same",deepcopy(updates),expected_revision=0)["duplicate"]
    assert s.project.to_dict()==before
    with pytest.raises(ContractError,match="SUBMISSION_ID_REUSED"):
        s.submit("same",[{"field_id":"site.total_area","value":2000,"unit":"m2"}],expected_revision=1)
    assert s.project.to_dict()==before


def test_invalid_batch_is_atomic_and_revision_conflict_does_not_override():
    s=session();before=s.project.to_dict()
    with pytest.raises(ContractError):
        s.submit("bad",[{"field_id":"project.name","value":"SYNTHETIC"},{"field_id":"site.total_area","value":-1,"unit":"m2"}],expected_revision=0)
    assert s.project.to_dict()==before
    with pytest.raises(ContractError,match="REVISION_CONFLICT"):
        s.submit("stale",[{"field_id":"site.total_area","value":1000,"unit":"m2"}],expected_revision=99)
    assert s.project.to_dict()==before


def test_conflicting_round_preserves_candidates_and_requires_reviewed_choice():
    s=session()
    s.submit("one",[{"field_id":"site.usable_area","value":1000,"unit":"m2"}],expected_revision=0)
    s.submit("two",[{"field_id":"site.usable_area","value":1500,"unit":"m2"}],expected_revision=1)
    active=s.project.values["site.usable_area"]
    assert active["status"]=="CONFLICT" and active["value"] is None
    chosen=next(cid for cid in active["candidate_ids"] if s.project.candidates[cid]["value"]==1000)
    s.resolve("resolve1","site.usable_area",chosen,reviewer="SYNTHETIC-REVIEWER",reason="SYNTHETIC source selected, not verified",expected_revision=2)
    assert s.project.values["site.usable_area"]["value"]==1000
    assert s.project.values["site.usable_area"]["status"]=="UNVERIFIED"
    assert len(s.project.values["site.usable_area"]["candidate_ids"])==2


def test_explicit_correction_retains_old_candidate_without_fake_conflict():
    s=session();s.submit("first",[{"field_id":"site.total_area","value":1000,"unit":"m2"}],expected_revision=0)
    s.revise("correct",[{"field_id":"site.total_area","value":1200,"unit":"m2"}],expected_revision=1,reason="SYNTHETIC corrected transcription")
    assert s.project.values["site.total_area"]["value"]==1200
    assert any(c["field_id"]=="site.total_area" and c["value"]==1000 for c in s.project.candidates.values())


def test_unknown_to_known_is_not_a_conflict_and_unknown_cannot_erase_known_fact():
    s=session()
    s.submit("unknown",[{"field_id":"site.total_area","value":None,"source_kind":"UNKNOWN","missing_reason":"SYNTHETIC not known"}],expected_revision=0)
    s.submit("known",[{"field_id":"site.total_area","value":1000,"unit":"m2"}],expected_revision=1)
    assert s.project.values["site.total_area"]["status"]=="UNVERIFIED"
    s.submit("unknown-again",[{"field_id":"site.total_area","value":None,"source_kind":"UNKNOWN","missing_reason":"SYNTHETIC second source unavailable"}],expected_revision=2)
    assert s.project.values["site.total_area"]["value"]==1000


def test_user_cannot_submit_calculated_or_verified_claims_directly():
    s=session()
    for extra in [{"source_kind":"CALCULATED"},{"status":"VERIFIED"}]:
        with pytest.raises(ContractError):
            s.submit("forbidden",[{"field_id":"capex.user_budget","value":100,"unit":"currency",**extra}],expected_revision=0)
    assert "capex.user_budget" not in s.project.values


def test_explicit_review_is_separate_from_extraction_and_never_promotes_assumptions():
    s=session();s.submit("name",[{"field_id":"project.name","value":"SYNTHETIC"}],expected_revision=0)
    s.review("review1","project.name",reviewer="SYNTHETIC-HUMAN",reason="SYNTHETIC user statement checked",license_status="AUTHORIZED",expected_revision=1)
    assert s.project.values["project.name"]["status"]=="VERIFIED"
    assert any(c["status"]=="UNVERIFIED" for c in s.project.candidates.values())


def test_numeric_units_are_explicit_and_currency_conversion_has_no_invented_tax_basis():
    s=session()
    with pytest.raises(ContractError,match="UNIT_REQUIRED"):
        s.submit("missing-unit",[{"field_id":"site.total_area","value":1000}],expected_revision=0)
    s.submit("budget",[{"field_id":"project.currency","value":"CNY"},{"field_id":"capex.user_budget","value":100,"unit":"万元"}],expected_revision=0)
    r=s.project.values["capex.user_budget"]
    assert r["value"]==1000000 and r["original_value"]==100 and r["original_unit"]=="万元"
    assert r["economic_basis"] is None


def test_raw_object_array_and_predecessors_get_per_atom_provenance():
    s=session();s.submit("tasks",[{"field_id":"schedule.tasks","value":[{"row_id":"start","fields":{
        "schedule.tasks.task_id":{"value":"A"},"schedule.tasks.predecessor_ids":{"value":[]}}}]}],expected_revision=0)
    r=s.project.values["schedule.tasks"]["value"][0]
    assert r["fields"]["schedule.tasks.predecessor_ids"]["value"]==[]
    assert r["fields"]["schedule.tasks.row_id"]["value"]=="start"
    assert all(x["source_id"] and x["field_instance_id"] for x in r["fields"].values())


def test_export_is_versioned_exact_and_has_no_fake_calculation_result():
    from wangbin_solar_pv.intake import IntakeSession
    s=session();s.submit("target",[{"field_id":"targets.payback_years","value":5,"unit":"year"}],expected_revision=0)
    export=s.export(); assert export["input_hash"]==s.export()["input_hash"]
    assert export["calculation_status"]=="NOT_IMPLEMENTED"
    assert not {"results","result_hash","run_id","irr","npv"}&export.keys()
    assert export["normalized_inputs"]["targets.payback_years"]==5
    restored=IntakeSession.from_dict(s.project.to_dict(),CAT)
    assert restored.export()["input_hash"]==export["input_hash"]
