"""Focused, cheap checks for distinct full-horizon synthetic source snapshots."""
from hashlib import sha256
from pathlib import Path

import pytest

from tooling.solar_pv_phase7l_full_cases import prepare, reconcile_category_obligations
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.calculation.input_contract import validate_export
from wangbin_solar_pv.calculation.method_config import MethodConfig
from wangbin_solar_pv.serialization import loads


@pytest.mark.parametrize("category", ["industrial_rooftop", "utility_scale_ground"])
def test_full_case_has_own_25_year_sourced_inputs_and_model_only_documents(tmp_path, category):
    root = tmp_path / category
    prepare(category, root)
    catalog = Catalog()
    exported = loads((root / "input.json").read_bytes())
    validate_export(exported, catalog)
    methods = MethodConfig.from_dict(loads((root / "methods.json").read_bytes()))
    values = exported["normalized_inputs"]
    assert values["project.evaluation_years"] == 25
    assert values["project.cashflow_tax_basis"] == "post_tax"
    assert len(methods.require("cash.collection_fractions")) == 25
    assert len(methods.require("cash.opex_payment_fractions")) == 25
    assert values["opex.items"][0]["fields"]["opex.items.to_year"] == 25
    assert values["roof.remaining_life"] >= 25 if category == "industrial_rooftop" else values["site.rights_expiry"] >= "2051-12-31"
    assert values["assets.replacements"]
    assert values["resource.annual_comparison"] == []  # no independent weather comparator
    source_attachment = values["attachments.register"][0]["fields"]
    assert all("NO_" not in str(value) for key, value in values.items() if key in (
        "roof.structure_report_id", "site.geotechnical_reference", "tariff.contract_id"))
    source = (root / "documents/source-material.md").read_bytes()
    assert b"SYNTHETIC" in source and b"not an approval" in source
    assert source_attachment["attachments.register.sha256"] == sha256(source).hexdigest()
    if category == "industrial_rooftop":
        assert values["load.annual_energy"] == 293460
    records = exported["source_snapshot"]["records"]
    assert any(record.get("source_url_or_attachment", "").endswith(sha256(source).hexdigest()) for record in records)
    assert exported["project"]["values"]["finance.project_discount_rate"]["source_section_or_cell"] == "PROJECT_POST_TAX_NOMINAL_CNY_YEAR_END"
    terminal = loads((root / "terminal.json").read_bytes())
    assert terminal["terminal_date"] == "2051-12-31"
    assert terminal["no_disposition"]["source"]["source_content_sha256"] == sha256((root / "terminal.txt").read_bytes()).hexdigest()
    assert len(terminal["covered_asset_ids"]) >= 4
    manifest = loads((root / "bundle/manifest.json").read_bytes())
    assert manifest["datasets"]["resource.timeseries"]["row_count"] == 8760
    assert all(dataset["header"]["source_id"] == f"SYNTHETIC-PHASE7L-{category}-v1"
               and dataset["header"]["source_url_or_attachment"].endswith(sha256(source).hexdigest())
               for dataset in manifest["datasets"].values())
    assert loads((root / "bundle/base.json").read_bytes())["input_hash"] == exported["input_hash"]


def test_ground_category_forbids_shared_catalog_field_even_when_raw_l2_says_required():
    catalog = Catalog()
    rows = [{"field_id": fid, "applicable": True, "present": False,
             "repeat_parent": None, "repeat_parent_rows": None,
             "effective": {"L2": {"requirement": "REQUIRED"}}}
            for fid in ("tariff.non_avoidable_charges", "schedule.tasks")]
    outcome = reconcile_category_obligations({"fields": rows}, "utility_scale_ground", catalog)
    assert outcome["category_disallowed_catalog_ids"] == ["tariff.non_avoidable_charges"]
    assert outcome["l2_missing_effective_ids"] == ["schedule.tasks"]
