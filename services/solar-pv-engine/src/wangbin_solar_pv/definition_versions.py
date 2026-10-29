"""Pinned, versioned metadata overlays; no numerical method or input migration.

The packaged errata and lock are data, not trust anchors. The reviewed lock digest
below is the trust anchor; changing either data file requires a code review too.
Original 03/05 documents and the twelve baseline hashes remain untouched.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re

from .errors import ContractError
from .schemas import StrictValidator
from .serialization import digest, loads

FROZEN_DEFINITION_VERSION = "solar-pv-formula-definitions/1.0.0"
DEFINITION_VERSION = "solar-pv-formula-definitions/1.0.1"
TRUSTED_DEFINITION_LOCK_HASH = "058a01916a16070b34a771560286a5f337831354066b4e0325a616c2365361cd"
_MAX_CONTROL_BYTES = 128 * 1024
_HASH = {"type": "string", "pattern": "^[0-9a-f]{64}$"}


def _object(properties):
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


def definition_errata_schema():
    """Exactly E01..E06, bound to approved targets and metadata paths.

    Schema forbids hidden business fields and executable-expression patches;
    the pinned lock additionally fixes every before/after value byte-for-byte
    under the existing canonical JSON contract.
    """
    text = {"type": "string", "minLength": 1, "maxLength": 4000}
    field_ids = {"type": "array", "minItems": 1, "maxItems": 469,
                 "uniqueItems": True,
                 "items": {"type": "string", "pattern": "^[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)+$"}}

    def change(path, before, after):
        return _object({"path": {"const": path}, "before": before, "after": after})

    role = change(["every_symbol_definition", 0, "role"], {"const": "input"}, {"const": "output"})
    specs = [
        ("E01", "formula", "F-USABLE-AREA", "05-formula-extensions.json", [role]),
        ("E02", "formula", "F-CAPEX-ITEM-AMOUNT", "05-formula-extensions.json", [role]),
        ("E03", "formula", "F-NOMINAL-REAL-RATE", "05-formulas.json", [
            change(["unit"], {"const": "1/年"}, {"const": "1"}),
            change(["dimensional_check"], text, text)]),
        ("E04", "formula", "F-ENERGY-AGGREGATION", "05-formulas.json", [
            change(["subscript_definition", "逐个下标词素"], text, text)]),
        ("E05", "formula", "F-BREAK-EVEN-PRICE", "05-formulas.json", [
            change(["subscript_definition", "逐个下标词素"], text, text)]),
        ("E06", "binding", "checks.energy_balance_residual", "05-field-bindings.json", [
            change(["input_field_ids"], field_ids, field_ids)]),
    ]
    items = []
    for eid, kind, target, filename, changes in specs:
        items.append(_object({
            "id": {"const": eid}, "target_kind": {"const": kind},
            "target_id": {"const": target}, "source_file": {"const": filename},
            "reason_zh": text,
            "changes": {"type": "array", "minItems": len(changes), "maxItems": len(changes),
                        "prefixItems": changes, "items": False},
        }))
    return _object({
        "schema_version": {"const": "solar-pv-definition-errata/1.0.0"},
        "definition_version": {"const": DEFINITION_VERSION},
        "frozen_definition_version": {"const": FROZEN_DEFINITION_VERSION},
        "approval_reference": {"const": "19-phase3-approved-implementation-contract.md#D1"},
        "items": {"type": "array", "minItems": 6, "maxItems": 6,
                  "prefixItems": items, "items": False},
    })


def definition_lock_schema():
    baseline_files = (
        "00-original-user-baseline.md", "00-baseline-manifest.json", "01-product-requirements.md",
        "03-input-data-dictionary.md", "03-input-fields.json", "05-formulas.json",
        "05-formula-extensions.json", "05-field-bindings.json", "06-glossary.json",
        "06-glossary-extensions.json", "07-category-boundaries.md", "08-baseline-contract.json",
    )
    # Return detached schemas: callers must not mutate our private constraints.
    return deepcopy(_object({
        "schema_version": {"const": "solar-pv-definition-lock/1.0.0"},
        "definition_version": {"const": DEFINITION_VERSION},
        "baseline_hashes": _object({name: _HASH for name in baseline_files}),
        "errata_hash": _HASH, "frozen_definition_hash": _HASH,
        "effective_definition_hash": _HASH, "input_schema_hash": _HASH,
        "definition_hash": _HASH,
    }))


def _read_control(path, schema):
    try:
        with path.open("rb") as stream:
            data = stream.read(_MAX_CONTROL_BYTES + 1)
        result = loads(data, max_bytes=_MAX_CONTROL_BYTES)
    except (OSError, ContractError) as exc:
        raise ContractError("DEFINITION_CONTROL_UNAVAILABLE") from exc
    if next(StrictValidator(schema).iter_errors(result), None) is not None:
        raise ContractError("DEFINITION_CONTROL_SCHEMA")
    return result


def _frozen_hash(catalog):
    return digest({"definition_version": FROZEN_DEFINITION_VERSION,
                   "baseline_hashes": catalog.baseline_hashes,
                   "formulas": catalog.frozen_formulas, "bindings": catalog.frozen_bindings})


def _effective_hash(formulas, bindings):
    return digest({"formulas": formulas, "bindings": bindings})


def load_effective_definitions(catalog):
    """Apply only the reviewed package overlay, never files from baseline_dir."""
    package = Path(__file__).resolve().parent
    errata = _read_control(package / "definition-errata.json", definition_errata_schema())
    lock = _read_control(package / "definition-lock.json", definition_lock_schema())
    if digest(lock) != TRUSTED_DEFINITION_LOCK_HASH:
        raise ContractError("DEFINITION_LOCK_DRIFT")
    if lock["baseline_hashes"] != catalog.baseline_hashes:
        raise ContractError("DEFINITION_BASELINE_DRIFT")
    if digest(errata) != lock["errata_hash"] or _frozen_hash(catalog) != lock["frozen_definition_hash"]:
        raise ContractError("DEFINITION_CONTENT_DRIFT")
    formulas, bindings = deepcopy(catalog.frozen_formulas), deepcopy(catalog.frozen_bindings)
    ids = []
    for item in errata["items"]:
        ids.append(item["id"])
        target = (formulas if item["target_kind"] == "formula" else bindings).get(item["target_id"])
        if target is None:
            raise ContractError("DEFINITION_TARGET_UNKNOWN")
        for change in item["changes"]:
            parent = target
            try:
                for token in change["path"][:-1]:
                    parent = parent[token]
                key = change["path"][-1]
                if parent[key] != change["before"]:
                    raise ContractError("DEFINITION_PATCH_PRECONDITION")
                parent[key] = deepcopy(change["after"])
            except (KeyError, IndexError, TypeError) as exc:
                raise ContractError("DEFINITION_PATCH_PATH") from exc
    if len(ids) != len(set(ids)):
        raise ContractError("DEFINITION_DUPLICATE_ERRATUM")
    manifest = {
        "schema_version": "solar-pv-definition-manifest/1.0.0",
        "definition_version": DEFINITION_VERSION,
        "frozen_definition_version": FROZEN_DEFINITION_VERSION,
        "baseline_hashes": deepcopy(catalog.baseline_hashes),
        "frozen_definition_hash": _frozen_hash(catalog),
        "errata_hash": digest(errata),
        "effective_definition_hash": _effective_hash(formulas, bindings),
        "input_schema_hash": digest(catalog.project_schema()),
        "patches": deepcopy(errata["items"]),
        "compatibility": {"frozen": "INPUT_ONLY_RECALCULATE", "current": "EXACT_IDENTITY"},
    }
    if any(manifest[k] != lock[k] for k in ("effective_definition_hash", "input_schema_hash")) or digest(manifest) != lock["definition_hash"]:
        raise ContractError("DEFINITION_MANIFEST_DRIFT")
    return formulas, bindings, manifest


def definition_compatibility(catalog, version, definition_hash=None):
    """Classify identity only; never rewrite an input, old result, or its hash.

    Frozen version accepts an omitted historical hash; if supplied it must match.
    Current results always need both the version and exact hash. Unknown versions
    cannot be treated as input- or result-compatible by lexical version ordering.
    """
    if not isinstance(version, str) or version not in {FROZEN_DEFINITION_VERSION, DEFINITION_VERSION}:
        raise ContractError("UNKNOWN_DEFINITION_VERSION")
    if definition_hash is not None and (not isinstance(definition_hash, str) or re.fullmatch(r"[0-9a-f]{64}", definition_hash) is None):
        raise ContractError("INVALID_DEFINITION_HASH")
    lock = _read_control(Path(__file__).resolve().parent / "definition-lock.json", definition_lock_schema())
    if digest(lock) != TRUSTED_DEFINITION_LOCK_HASH:
        raise ContractError("DEFINITION_LOCK_DRIFT")
    manifest = catalog.definition_manifest
    if (catalog.definition_hash != lock["definition_hash"]
            or catalog.definition_version != DEFINITION_VERSION or digest(manifest) != catalog.definition_hash
            or _effective_hash(catalog.formulas, catalog.bindings) != manifest["effective_definition_hash"]
            or _frozen_hash(catalog) != manifest["frozen_definition_hash"]):
        raise ContractError("DEFINITION_IDENTITY_DRIFT")
    legacy = version == FROZEN_DEFINITION_VERSION
    expected = manifest["frozen_definition_hash"] if legacy else catalog.definition_hash
    if not legacy and definition_hash is None:
        raise ContractError("DEFINITION_HASH_REQUIRED")
    if definition_hash is not None and definition_hash != expected:
        raise ContractError("DEFINITION_HASH_MISMATCH")
    return {"version": version, "definition_hash": expected,
            "current_definition_version": catalog.definition_version,
            "current_definition_hash": catalog.definition_hash,
            "status": "INPUT_ONLY_RECALCULATE" if legacy else "EXACT_IDENTITY",
            "input_compatible": True, "results_compatible": not legacy,
            "requires_recalculation": legacy,
            "migration_policy": "PRESERVE_INPUT_AND_OLD_RESULT_HASHES; EXPLICIT_NEW_CALCULATION_ONLY"}
