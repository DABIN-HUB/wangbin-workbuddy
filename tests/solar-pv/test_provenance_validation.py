"""B/F/J/M: typed values, raw preservation, provenance and input consistency."""
from copy import deepcopy
from decimal import Decimal
import pytest

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.models import ProjectData

CATALOG = Catalog()


def api():
    from wangbin_solar_pv.provenance import make_record, register_candidate
    from wangbin_solar_pv.validation import validate_record, validate_project
    return make_record, register_candidate, validate_record, validate_project


def record(fid, value, **kwargs):
    make, _, _, _ = api()
    return make(CATALOG, fid, value, source_kind="USER_PROVIDED", source_id="SYNTHETIC-USER",
                source_url_or_attachment="SYNTHETIC:statement", source_section_or_cell="statement 1",
                confidence_basis="SYNTHETIC explicit fictional statement, not a real project", license_status="AUTHORIZED", **kwargs)


def valid_value(field):
    c = field["constraints"]
    if "enum" in c:
        return c["enum"][0]
    if field["type"] == "array":
        return []
    if field["type"] == "boolean":
        return False
    if field["type"] in {"number", "integer"}:
        lo = c.get("minimum", c.get("exclusiveMinimum", 0))
        value = Decimal(str(lo)) + (1 if "exclusiveMinimum" in c else 0)
        if "maximum" in c:
            value = min(value, Decimal(str(c["maximum"])))
        return int(value) if field["type"] == "integer" else value
    if c.get("format") == "date":
        return "2024-02-29"
    if c.get("format") == "date-time":
        return "2024-02-29T00:00:00+08:00"
    if field["field_id"].endswith(".currency"):
        return "CNY"
    if field["field_id"].endswith(".row_id"):
        return "SYNTHETIC-ROW"
    if "start_time" in field["field_id"]:
        return "00:00"
    if "end_time" in field["field_id"]:
        return "24:00"
    if "pattern" in c:
        # Other patterns are date/month or SHA digests; choose explicitly.
        if "sha256" in field["field_id"]:
            return "a" * 64
        if "month" in field["field_id"]:
            return "2024-02"
        return "00:00"
    return "SYNTHETIC"


@pytest.mark.parametrize("fid", list(CATALOG.fields))
def test_each_of_469_fields_validates_as_a_typed_serializable_record(fid):
    _, _, validate, _ = api()
    rec = record(fid, valid_value(CATALOG.fields[fid]))
    assert not [i for i in validate(rec, CATALOG) if i.severity == "ERROR"], fid
    assert rec["field_id"] == fid
    assert rec["original_value"] == valid_value(CATALOG.fields[fid])
    assert rec["status"] == "UNVERIFIED"


@pytest.mark.parametrize("fid", list(CATALOG.fields))
def test_each_field_rejects_wrong_type_instead_of_coercing(fid):
    _, _, validate, _ = api()
    rec = record(fid, valid_value(CATALOG.fields[fid]))
    rec["value"] = {"not": "a scalar or array"}
    assert any(i.code == "FIELD_SCHEMA" for i in validate(rec, CATALOG)), fid


@pytest.mark.parametrize("fid,bad", [("site.total_area", 0), ("site.latitude", 91),
    ("site.longitude", -181), ("system.module_count", True), ("system.module_count", 1.5),
    ("system.module_count", "1"), ("project.sales_mode", "invented"),
    ("schedule.commissioning_date", "2023-02-29"), ("resource.timeseries.timestamp", "2024-01-01T00:00:00"),
    ("tariff.periods.start_time", "29:59"), ("tariff.periods.start_time", "24:00"), ("tariff.periods.end_time", "24:01")])
def test_field_boundaries_reject_illegal_values(fid, bad):
    _, _, validate, _ = api()
    rec = record(fid, valid_value(CATALOG.fields[fid]))
    rec["value"] = bad
    assert any(i.severity == "ERROR" for i in validate(rec, CATALOG))


def test_unknown_and_assumption_are_never_verified_facts():
    make, _, validate, _ = api()
    unknown = make(CATALOG, "site.total_area", None, source_kind="UNKNOWN", missing_reason="SYNTHETIC not supplied")
    assert unknown["status"] == "UNKNOWN" and unknown["value"] is None
    assert not validate(unknown, CATALOG)
    assumed = make(CATALOG, "system.annual_degradation", Decimal("0.005"), source_kind="ASSUMPTION",
        source_id="SYNTHETIC-ASSUMPTION", confidence_basis="SYNTHETIC scenario only",
        assumption={"reason":"SYNTHETIC", "method":"editable scenario", "lower":0, "upper":Decimal("0.01"),
                    "maturity_ceiling":"L1", "noncritical":False, "decision_invariant":False})
    assert assumed["status"] == "ASSUMED"
    assumed["status"] = "VERIFIED"
    assert any(i.code == "ASSUMPTION_NOT_FACT" for i in validate(assumed, CATALOG))
    unknown["value"] = 0
    assert any(i.code == "UNKNOWN_MUST_BE_NULL" for i in validate(unknown, CATALOG))


def test_user_statement_not_auto_verified_and_evidence_has_real_locator():
    _, _, validate, _ = api()
    rec = record("grid.opinion_status", "confirmed")
    assert rec["status"] == "UNVERIFIED"
    rec["status"] = "VERIFIED"
    assert any(i.code == "VERIFICATION_EVIDENCE_REQUIRED" for i in validate(rec, CATALOG))
    rec["reviewer"] = "SYNTHETIC-REVIEWER"
    assert not [i for i in validate(rec, CATALOG) if i.severity == "ERROR"]
    rec["source_section_or_cell"] = None
    assert any(i.code == "VERIFICATION_EVIDENCE_REQUIRED" for i in validate(rec, CATALOG))


def test_normalization_retains_original_value_unit_and_transformation():
    make, _, validate, _ = api()
    rec = make(CATALOG, "system.dc_capacity", 1, original_unit="MWp", source_kind="USER_PROVIDED",
               source_id="SYNTHETIC", confidence_basis="SYNTHETIC explicit unit")
    assert rec["original_value"] == 1 and rec["original_unit"] == "MWp"
    assert rec["value"] == Decimal("1000") and rec["unit"] == "kWp"
    assert rec["transformation_rule_ids"]
    assert not [i for i in validate(rec, CATALOG) if i.severity == "ERROR"]


def test_conflicts_preserve_both_candidates_without_silent_override():
    _, register, _, _ = api()
    project = ProjectData.new("SYNTHETIC-CONFLICT", "industrial_rooftop", CATALOG)
    first = register(project, record("site.usable_area", 1000), CATALOG)
    second = register(project, record("site.usable_area", 1500), CATALOG)
    assert first != second
    assert len(project.candidates) == 2
    active = project.values["site.usable_area"]
    assert active["status"] == "CONFLICT" and active["value"] is None
    assert set(active["candidate_ids"]) == {first, second}
    assert sorted(r["value"] for r in project.candidates.values()) == [1000, 1500]


def test_calculated_amount_requires_formula_version_run_and_upstream_instances():
    make, _, validate, _ = api()
    rec = make(CATALOG, "capex.items.amount", 200, source_kind="CALCULATED", source_id="SYNTHETIC-RUN",
        confidence_basis="SYNTHETIC deterministic upstream, not executed in Phase2")
    assert any(i.code == "CALCULATION_LINEAGE_REQUIRED" for i in validate(rec, CATALOG))
    rec.update(formula_id="F-CAPEX-ITEM-AMOUNT", formula_version="SOLAR-PV-1.0.0", run_id="SYNTHETIC-RUN",
               upstream_instance_ids=["SYNTHETIC-quantity", "SYNTHETIC-unit-price"])
    assert not [i for i in validate(rec, CATALOG) if i.severity == "ERROR"]


def test_cross_field_consistency_never_changes_inputs_or_fakes_missing_capacity():
    _, _, _, validate = api()
    project = ProjectData.new("SYNTHETIC-SIZE", "industrial_rooftop", CATALOG)
    project.values = {"site.total_area": record("site.total_area",100), "site.usable_area":record("site.usable_area",120)}
    old = deepcopy(project.to_dict())
    assert any(i.code == "USABLE_AREA_EXCEEDS_TOTAL" for i in validate(project, CATALOG))
    assert project.to_dict() == old
    assert "system.dc_capacity" not in project.values


def test_all_source_kinds_are_explicit_and_not_promoted():
    make, _, validate, _ = api()
    for kind, origin in [("USER_PROVIDED","U"),("DOCUMENT_EXTRACTED","D"),("EXTERNAL_SOURCE","D"),("CALCULATED","C")]:
        rec = make(CATALOG,"capex.items.amount",10,source_kind=kind,source_id="SYNTHETIC",
                   confidence_basis="SYNTHETIC", source_url_or_attachment="SYNTHETIC:attachment")
        assert rec["provenance_kind"] == origin
        assert rec["status"] == "UNVERIFIED"


def test_economic_basis_mixing_is_not_a_currency_conversion():
    from wangbin_solar_pv.validation import compatible_economic_basis
    a = {"currency":"CNY","price_year":2025,"tax_basis":"inclusive","price_basis":"nominal"}
    b = {**a,"price_year":2026}
    assert not compatible_economic_basis(a,b)
    assert not compatible_economic_basis(a,{**a,"tax_basis":"exclusive"})
    assert compatible_economic_basis(a,deepcopy(a))
