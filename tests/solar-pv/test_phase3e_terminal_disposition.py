"""R1-1: bounded SYNTHETIC terminal source contract, not a real receipt."""
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256

import pytest

from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.serialization import digest, dumps, loads


DOCUMENT = b"SYNTHETIC terminal asset-1 CNY asset_id=asset-1 transaction_id=asset-sale-1 category=ASSET_DISPOSITION project_boundary=PROJECT_UNLEVERED ledger_booking=false receipt=500 cost=10 income_tax=20 other_tax=2 vat_cash=3 tax_included=false; 2026-12-31"
NO_DISPOSITION_DOCUMENT = b"SYNTHETIC terminal asset-1 CNY asset_id=asset-1 no additional recovery; tax_treatment=NO_DISPOSITION_TAX working_capital_treatment=LEDGER_ALREADY_RECOVERED; 2026-12-31"


def _source(excerpt, document=DOCUMENT):
    return {
        "source_id": "SYNTHETIC-terminal-document", "source_kind": "SYNTHETIC",
        "source_reference": "SYNTHETIC:terminal-document", "source_section_or_cell": "asset-1",
        "source_excerpt": excerpt, "source_content_sha256": sha256(document).hexdigest(),
        "source_status": "ASSUMED", "economic_status": "SYNTHETIC_ASSUMPTION",
        "source_timestamp": "2025-01-01", "effective_from": "2025-01-01",
        "effective_to": "2026-12-31", "reviewer": "SYNTHETIC-reviewer",
        "license_status": "AUTHORIZED",
    }


def _fact(amount, excerpt):
    return {"amount": amount, "date": "2026-12-31", "currency": "CNY", "unit": "CNY",
            "source": _source(excerpt)}


def _carrier():
    source = {
        "project_id": "SYNTHETIC-project", "pv_type": "industrial_rooftop",
        "evaluation_date": "2025-01-01", "terminal_date": "2026-12-31", "currency": "CNY",
        "mode": "EVENTS", "covered_asset_ids": ["asset-1"],
        "events": [{
            "event_id": "disposition-1", "asset_id": "asset-1",
            "transaction_id": "asset-sale-1", "disposal_object": "SYNTHETIC module",
            "category": "ASSET_DISPOSITION", "project_boundary": "PROJECT_UNLEVERED",
            "ledger_booking": {"already_recorded": False, "ledger_event_id": None},
            "receipt": _fact(Decimal("500"), "receipt=500"),
            "direct_cost": _fact(Decimal("10"), "cost=10"),
            "income_tax_cash": _fact(Decimal("20"), "income_tax=20"),
            "other_tax_cash": _fact(Decimal("2"), "other_tax=2"),
            "vat_cash": _fact(Decimal("3"), "vat_cash=3"),
            "tax_included": False,
        }],
        "no_disposition": None,
    }
    binding = {
        "project_id": "SYNTHETIC-project", "pv_type": "industrial_rooftop",
        "evaluation_date": "2025-01-01", "currency": "CNY", "scenario_id": "BASE",
        "phase2_input_hash": "a" * 64, "phase2_source_snapshot_id": "b" * 64,
        "method_config_hash": "c" * 64, "d3_content_hash": "d" * 64,
        "phase3b_result_hash": "e" * 64, "phase3c_result_hash": "f" * 64,
        "phase3d_result_hash": "0" * 64, "basis": "项目税后",
    }
    return {"schema_version": "solar-pv-project-terminal-disposition/1.0.0",
            "source": source, "source_content_hash": digest(source), "binding": binding}


def _validate(carrier, documents=None):
    from wangbin_solar_pv.calculation.terminal_disposition import validate_terminal_disposition
    return validate_terminal_disposition(loads(dumps(carrier)), documents or {"SYNTHETIC-terminal-document": DOCUMENT})


def test_source_bytes_and_economic_identity_are_checked():
    carrier = _carrier()
    checked = _validate(carrier)
    assert checked.source_content_hash == carrier["source_content_hash"]
    assert checked.source["events"][0]["receipt"]["amount"] == Decimal("500")
    changed_binding = deepcopy(carrier)
    changed_binding["binding"]["phase3d_result_hash"] = "1" * 64
    assert _validate(changed_binding).source_content_hash == checked.source_content_hash
    with pytest.raises(ContractError):
        _validate(carrier, {"SYNTHETIC-terminal-document": b"changed evidence"})
    altered = deepcopy(carrier)
    altered["source"]["events"][0]["receipt"]["amount"] = Decimal("501")
    with pytest.raises(ContractError):
        _validate(altered)


@pytest.mark.parametrize("mutate", [
    lambda c: c.update(schema_version="unknown"),
    lambda c: c["source"].update(currency="USD"),
    lambda c: c["source"].update(unapproved="value"),
    lambda c: c["source"]["events"].append(deepcopy(c["source"]["events"][0])),
    lambda c: c["source"]["events"][0]["receipt"].update(amount="500"),
    lambda c: c["source"]["events"][0]["receipt"].update(amount=Decimal("NaN")),
    lambda c: c["source"]["events"][0]["receipt"].update(unit="USD"),
    lambda c: c["source"]["events"][0]["receipt"].update(date="2027-01-01"),
    lambda c: c["source"]["events"][0]["receipt"].update(source={}),
    lambda c: c["source"]["events"][0]["ledger_booking"].update(already_recorded=True),
    lambda c: c["source"].update(events=[]),
])
def test_invalid_source_does_not_become_cash(mutate):
    carrier = _carrier()
    mutate(carrier)
    try:
        carrier["source_content_hash"] = digest(carrier["source"])
    except ContractError:
        pass
    with pytest.raises(ContractError):
        _validate(carrier)


def test_no_disposition_requires_explicit_coverage_and_sourced_reason():
    carrier = _carrier()
    source = carrier["source"]
    source["mode"] = "NO_DISPOSITION"
    source["events"] = []
    source["no_disposition"] = {
        "covered_asset_ids": ["asset-1"], "reason": "no additional recovery",
        "tax_treatment": "NO_DISPOSITION_TAX", "working_capital_treatment": "LEDGER_ALREADY_RECOVERED",
        "source": _source("no additional recovery", NO_DISPOSITION_DOCUMENT),
    }
    source["no_disposition"]["source"]["source_id"] = "SYNTHETIC-no-disposition-document"
    source["no_disposition"]["source"]["source_timestamp"] = "2026-12-31"
    carrier["source_content_hash"] = digest(source)
    assert _validate(carrier, {"SYNTHETIC-no-disposition-document": NO_DISPOSITION_DOCUMENT}).source["mode"] == "NO_DISPOSITION"
    source["no_disposition"] = None
    carrier["source_content_hash"] = digest(source)
    with pytest.raises(ContractError):
        _validate(carrier)


def test_source_effective_window_does_not_extend_financial_horizon():
    carrier = _carrier()
    carrier["source"]["events"][0]["receipt"]["date"] = "2027-01-01"
    carrier["source"]["events"][0]["receipt"]["source"]["effective_to"] = "2027-01-01"
    carrier["source_content_hash"] = digest(carrier["source"])
    with pytest.raises(ContractError):
        _validate(carrier)


def test_rehashed_amount_cannot_exceed_its_verified_source_excerpt():
    carrier = _carrier()
    carrier["source"]["events"][0]["receipt"]["amount"] = Decimal("501")
    carrier["source_content_hash"] = digest(carrier["source"])
    with pytest.raises(ContractError):
        _validate(carrier)
