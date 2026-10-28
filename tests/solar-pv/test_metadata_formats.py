"""Metadata times are evidence, not unchecked display strings."""
import pytest
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.validation import validate_record
from synthetic_support import record


@pytest.mark.parametrize("key",["last_updated","retrieved_at"])
def test_evidence_timestamp_always_requires_explicit_timezone(key):
    cat=Catalog(); r=record(cat,"site.usable_area",100)
    r[key]="2026-10-28T12:00:00"
    assert any(i.code=="FIELD_SCHEMA" for i in validate_record(r,cat))


def test_normalization_cannot_be_a_silently_mislabeled_identity():
    cat=Catalog();r=record(cat,"system.dc_capacity",1,original_unit="MWp")
    r["value"]=1
    assert any(i.code=="NORMALIZATION_REPLAY_MISMATCH" for i in validate_record(r,cat))
