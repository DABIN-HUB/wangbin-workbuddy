"""D1 public identity, hard-lock and unchanged legacy input acceptance tests."""
from copy import deepcopy
from io import BytesIO
from pathlib import Path
import json
import subprocess

import pytest
from jsonschema import Draft202012Validator

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.definition_versions import (
    DEFINITION_VERSION, FROZEN_DEFINITION_VERSION, TRUSTED_DEFINITION_LOCK_HASH,
    definition_compatibility, definition_errata_schema, definition_lock_schema,
)
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.formula_bindings import FormulaBindings
from wangbin_solar_pv.intake import IntakeSession
from wangbin_solar_pv.models import ProjectData
from wangbin_solar_pv.schemas import StrictValidator
from wangbin_solar_pv.serialization import digest, dumps, loads
from wangbin_solar_pv.validation import validate_project
from synthetic_support import record, row, put_rows

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "services/solar-pv-engine/src/wangbin_solar_pv"


@pytest.fixture(scope="module")
def cat():
    return Catalog()


@pytest.mark.parametrize("kind", ["formula", "field", "metadata"])
def test_public_queries_include_full_effective_definition_identity(cat, kind):
    if kind == "formula":
        info = FormulaBindings(cat).describe("F-USABLE-AREA")
    elif kind == "field":
        info = FormulaBindings(cat).describe_field("checks.energy_balance_residual")
    else:
        info = cat.metadata("site.usable_area")
    assert info["definition_version"] == cat.definition_version == DEFINITION_VERSION
    assert info["definition_hash"] == cat.definition_hash == digest(cat.definition_manifest)
    assert info["definition_manifest"] == cat.definition_manifest
    info["definition_manifest"]["patches"][0]["id"] = "caller-change"
    assert cat.definition_manifest["patches"][0]["id"] == "E01"


def test_public_formula_instances_use_actual_row_id_not_scalar_item_boolean(cat):
    project = ProjectData.new("SYNTHETIC-D1-ROWS", "industrial_rooftop", cat)
    put_rows(project, cat, "capex.items", [row(cat, "capex.items", "alpha", {"quantity": None, "unit_price": 100}), row(cat, "capex.items", "beta", {"unit_price": 200})])
    info = FormulaBindings(cat).describe("F-CAPEX-ITEM-AMOUNT", project)
    quantity = next(s for s in info["symbols"] if s["definition"]["field_id"] == "capex.items.quantity")
    inputs = next(x for x in quantity["supporting_inputs"] if x["field_id"] == "capex.items.quantity")
    assert [x["row_id"] for x in inputs["instances"]] == ["alpha"]
    assert {x["row_id"] for x in inputs["missing_instances"]} == {"alpha", "beta"}
    assert all(type(x["row_id"]) is str for x in info["missing_instances"])


def test_errata_schema_requires_exact_six_items(cat):
    errata = loads((PACKAGE / "definition-errata.json").read_bytes())
    shortened = deepcopy(errata)
    shortened["items"].pop()
    assert list(StrictValidator(definition_errata_schema()).iter_errors(shortened))


@pytest.mark.parametrize("mutation", ["wrong-target", "wrong-file", "wrong-path", "boolean-path", "wrong-value-type", "duplicate-id"])
def test_errata_schema_binds_each_approved_item_to_its_metadata_path(mutation):
    value = loads((PACKAGE / "definition-errata.json").read_bytes())
    item = value["items"][0]
    if mutation == "wrong-target": item["target_id"] = "F-DC-CAPACITY"
    if mutation == "wrong-file": item["source_file"] = "05-formulas.json"
    if mutation == "wrong-path": item["changes"][0]["path"] = ["text_equation"]
    if mutation == "boolean-path": item["changes"][0]["path"][1] = False
    if mutation == "wrong-value-type": item["changes"][0]["after"] = {"hidden": "business-input"}
    if mutation == "duplicate-id": value["items"][1]["id"] = "E01"
    assert list(StrictValidator(definition_errata_schema()).iter_errors(value))


def test_both_control_schemas_are_strict_and_valid():
    for name, schema in [("definition-errata.json", definition_errata_schema()), ("definition-lock.json", definition_lock_schema())]:
        Draft202012Validator.check_schema(schema)
        value = loads((PACKAGE / name).read_bytes())
        assert not list(StrictValidator(schema).iter_errors(value))
        bad = deepcopy(value)
        bad["unapproved_fact"] = 1
        assert list(StrictValidator(schema).iter_errors(bad))
        for key in value:
            bad = deepcopy(value)
            del bad[key]
            assert list(StrictValidator(schema).iter_errors(bad))


@pytest.mark.parametrize("target", ["errata", "lock"])
@pytest.mark.parametrize("mutation", ["unknown-key", "future-version", "content", "missing", "oversize", "duplicate-json-key"])
def test_catalog_never_trusts_control_file_presence(monkeypatch, target, mutation):
    filename = "definition-errata.json" if target == "errata" else "definition-lock.json"
    value = loads((PACKAGE / filename).read_bytes())
    if mutation == "unknown-key": value["unapproved"] = True
    if mutation == "future-version": value["definition_version"] = "solar-pv-formula-definitions/999.0.0"
    if mutation == "content":
        if target == "errata": value["items"][0]["reason_zh"] += "tampered"
        else: value["definition_hash"] = "0" * 64
    payload = dumps(value).encode()
    if mutation == "oversize": payload = b" " * (128 * 1024 + 1)
    if mutation == "duplicate-json-key": payload = b'{"schema_version":"one","schema_version":"two"}'
    original = Path.open
    def injected(path, *args, **kwargs):
        if path.name == filename and path.parent == PACKAGE:
            if mutation == "missing": raise FileNotFoundError("SYNTHETIC")
            return BytesIO(payload)
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", injected)
    with pytest.raises(ContractError, match="DEFINITION_"):
        Catalog()


def test_rehashed_lock_plus_errata_still_cannot_self_authorize(monkeypatch):
    errata = loads((PACKAGE / "definition-errata.json").read_bytes())
    lock = loads((PACKAGE / "definition-lock.json").read_bytes())
    errata["items"][0]["reason_zh"] += "unauthorized"
    lock["errata_hash"] = digest(errata)
    assert digest(lock) != TRUSTED_DEFINITION_LOCK_HASH
    original = Path.open
    replacements = {"definition-errata.json": dumps(errata).encode(), "definition-lock.json": dumps(lock).encode()}
    def injected(path, *args, **kwargs):
        if path.parent == PACKAGE and path.name in replacements:
            return BytesIO(replacements[path.name])
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "open", injected)
    with pytest.raises(ContractError, match="DEFINITION_LOCK_DRIFT"):
        Catalog()


@pytest.mark.parametrize("version", ["1.0.0", "METHOD-CONTRACT-v1", "solar-pv-formula-definitions/2.0.0", " solar-pv-formula-definitions/1.0.1 ", None, [], True])
def test_unknown_definition_versions_are_rejected_not_normalized(cat, version):
    with pytest.raises(ContractError, match="UNKNOWN_DEFINITION_VERSION"):
        definition_compatibility(cat, version)


@pytest.mark.parametrize("value", ["0" * 63, "A" * 64, " " + "0" * 64, 0, False, []])
def test_hash_format_is_validated_without_repair(cat, value):
    with pytest.raises(ContractError, match="INVALID_DEFINITION_HASH"):
        definition_compatibility(cat, DEFINITION_VERSION, value)


def test_current_results_need_exact_version_and_hash(cat):
    with pytest.raises(ContractError, match="DEFINITION_HASH_REQUIRED"):
        definition_compatibility(cat, DEFINITION_VERSION)
    with pytest.raises(ContractError, match="DEFINITION_HASH_MISMATCH"):
        definition_compatibility(cat, DEFINITION_VERSION, "0" * 64)
    info = definition_compatibility(cat, DEFINITION_VERSION, cat.definition_hash)
    assert info["status"] == "EXACT_IDENTITY"
    assert info["input_compatible"] and info["results_compatible"]
    assert info["requires_recalculation"] is False


def test_frozen_definitions_allow_input_only_and_never_relabel_old_results(cat):
    old_result = {"definition_version": FROZEN_DEFINITION_VERSION, "result_hash": "SYNTHETIC-OLD-UNCHANGED"}
    before = deepcopy(old_result)
    info = definition_compatibility(cat, FROZEN_DEFINITION_VERSION)
    assert info["status"] == "INPUT_ONLY_RECALCULATE"
    assert info["input_compatible"] and not info["results_compatible"]
    assert info["requires_recalculation"] is True
    assert definition_compatibility(cat, FROZEN_DEFINITION_VERSION, cat.definition_manifest["frozen_definition_hash"]) == info
    with pytest.raises(ContractError, match="DEFINITION_HASH_MISMATCH"):
        definition_compatibility(cat, FROZEN_DEFINITION_VERSION, cat.definition_hash)
    assert old_result == before


def test_in_memory_effective_mutation_invalidates_compatibility_identity():
    catalog = Catalog()
    catalog.formulas["F-USABLE-AREA"]["text_equation"] = "unauthorized"
    with pytest.raises(ContractError, match="DEFINITION_IDENTITY_DRIFT"):
        definition_compatibility(catalog, DEFINITION_VERSION, catalog.definition_hash)


def test_rehashed_in_memory_catalog_cannot_self_authorize():
    catalog = Catalog()
    catalog.formulas["F-USABLE-AREA"]["text_equation"] = "unauthorized"
    catalog.definition_manifest["effective_definition_hash"] = digest({"formulas": catalog.formulas, "bindings": catalog.bindings})
    catalog.definition_hash = digest(catalog.definition_manifest)
    with pytest.raises(ContractError, match="DEFINITION_IDENTITY_DRIFT"):
        definition_compatibility(catalog, DEFINITION_VERSION, catalog.definition_hash)


def test_lock_schema_requires_exact_original_baseline_names():
    value = loads((PACKAGE / "definition-lock.json").read_bytes())
    sha = value["baseline_hashes"].pop("03-input-fields.json")
    value["baseline_hashes"]["unapproved-fields.json"] = sha
    assert list(StrictValidator(definition_lock_schema()).iter_errors(value))


def test_exported_lock_schema_cannot_mutate_private_hash_constraints():
    schema = definition_lock_schema()
    schema["properties"]["definition_hash"]["pattern"] = ".*"
    value = loads((PACKAGE / "definition-lock.json").read_bytes())
    value["definition_hash"] = "NOT-A-SHA256"
    assert list(StrictValidator(definition_lock_schema()).iter_errors(value))


@pytest.mark.parametrize("kind", ["formula", "field", "metadata"])
def test_public_query_rejects_unapproved_in_memory_definitions(kind):
    catalog = Catalog()
    catalog.formulas["F-USABLE-AREA"]["text_equation"] = "unauthorized"
    with pytest.raises(ContractError, match="DEFINITION_IDENTITY_DRIFT"):
        if kind == "formula": FormulaBindings(catalog).describe("F-USABLE-AREA")
        elif kind == "field": FormulaBindings(catalog).describe_field("site.usable_area")
        else: catalog.metadata("site.usable_area")


def _legacy_catalog():
    # Execute the actual pre-D1 adapter from the pinned starting commit, read-only.
    proc = subprocess.run(["git", "show", "554c08859489d5fa2d8447f94c6494c9ed4bdb2a:services/solar-pv-engine/src/wangbin_solar_pv/catalog.py"], cwd=ROOT, capture_output=True, check=True)
    namespace = {"__name__": "wangbin_solar_pv._d1_legacy_test", "__package__": "wangbin_solar_pv", "__file__": str(PACKAGE / "catalog.py")}
    exec(compile(proc.stdout, "<pinned-pre-D1-catalog>", "exec"), namespace)
    return namespace["Catalog"]()


def test_legacy_project_export_input_and_source_hashes_and_schema_are_unchanged(cat):
    legacy = _legacy_catalog()
    assert cat.fields == legacy.fields and cat.baseline_hashes == legacy.baseline_hashes
    assert len(cat.fields) == 469 and len(cat.formulas) == 89 and len(cat.bindings) == 281
    assert cat.project_schema() == legacy.project_schema()
    assert digest(cat.project_schema()) == cat.definition_manifest["input_schema_hash"]
    project = ProjectData.new("SYNTHETIC-PRE-D1", "industrial_rooftop", legacy)
    project.values["site.total_area"] = record(legacy, "site.total_area", 1000)
    project.values["site.usable_area"] = record(legacy, "site.usable_area", 900)
    old_export = IntakeSession(project, legacy).export()
    before = deepcopy(old_export)
    restored = ProjectData.from_dict(old_export["project"], cat)
    assert not [i for i in validate_project(restored, cat) if i.severity == "ERROR"]
    current = IntakeSession(restored, cat).export()
    assert current == old_export
    assert current["input_hash"] == old_export["input_hash"]
    assert current["source_snapshot_id"] == old_export["source_snapshot_id"]
    assert old_export == before


def test_cli_writes_effective_definition_identity_not_just_archival_baseline(cat, tmp_path):
    import sys
    target = tmp_path / "effective-query.json"
    proc = subprocess.run([sys.executable, str(ROOT / "services/solar-pv-engine/solar_pv.py"), "--workspace", str(tmp_path), "formula", "--formula-id", "F-USABLE-AREA", "--output", target.name], cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", timeout=30)
    assert proc.returncode == 0, proc.stderr
    info = loads(target.read_bytes())
    assert info["definition_hash"] == cat.definition_hash
    assert info["definition_version"] == cat.definition_version
    assert info["definition_manifest"] == cat.definition_manifest
    assert info["formula"]["every_symbol_definition"][0]["role"] == "output"
    assert info["baseline_reference"]["files"] == cat.baseline_hashes
    assert info["can_execute_calculation"] is False


def test_arbitrary_overlay_in_external_baseline_directory_is_not_trusted(cat, tmp_path):
    import shutil
    for name in cat.baseline_hashes:
        shutil.copyfile(cat.baseline_dir / name, tmp_path / name)
    (tmp_path / "definition-errata.json").write_text('{"unapproved_fact": "must-not-load"}', encoding="utf-8")
    (tmp_path / "definition-lock.json").write_text('{"unapproved_hash": "must-not-load"}', encoding="utf-8")
    other = Catalog(tmp_path)
    assert other.definition_hash == cat.definition_hash
    assert other.formulas == cat.formulas


def test_frozen_namespaces_and_every_equation_preserved_independently(cat):
    formulas = {f["formula_id"]: f for name in ("05-formulas.json", "05-formula-extensions.json") for f in cat.documents[name]["formulas"]}
    bindings = {b["formula_field_id"]: b for b in cat.documents["05-field-bindings.json"]["bindings"]}
    fields = {f["field_id"]: f for f in cat.documents["03-input-fields.json"]["fields"]}
    assert cat.frozen_formulas == formulas
    assert cat.frozen_bindings == bindings
    assert cat.fields == fields
    assert cat.formulas.keys() == formulas.keys()
    assert cat.bindings.keys() == bindings.keys()
    for fid, frozen in formulas.items():
        for key in ("formula_id", "text_equation", "latex", "input_field_ids", "output_field_id", "calculation_boundary", "assumptions", "precedence", "test_status"):
            assert cat.formulas[fid][key] == frozen[key]
    assert cat.frozen_formulas is not cat.formulas
    assert cat.frozen_bindings is not cat.bindings


def test_exact_patch_diff_is_limited_to_seven_approved_metadata_leaves(cat):
    before = {"formula": cat.frozen_formulas, "binding": cat.frozen_bindings}
    after = {"formula": cat.formulas, "binding": cat.bindings}
    observed = set()
    def walk(a, b, path):
        if type(a) is dict and type(b) is dict:
            assert a.keys() == b.keys()
            for key in a: walk(a[key], b[key], path + (key,))
        elif type(a) is list and type(b) is list and len(a) == len(b):
            for i, (x, y) in enumerate(zip(a, b)): walk(x, y, path + (i,))
        elif a != b:
            observed.add(path)
    walk(before, after, ())
    expected = {(p["target_kind"], p["target_id"], *c["path"]) for p in cat.definition_manifest["patches"] for c in p["changes"]}
    assert len(cat.definition_manifest["patches"]) == 6
    assert len(expected) == 7
    assert observed == expected
    assert cat.documents["05-formulas.json"]["formulas"] == [cat.frozen_formulas[x["formula_id"]] for x in cat.documents["05-formulas.json"]["formulas"]]
