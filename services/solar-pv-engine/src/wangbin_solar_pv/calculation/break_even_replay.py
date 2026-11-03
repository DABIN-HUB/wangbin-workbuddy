"""P2-2: sourced one-price Phase 2/D3 derivation and real 3B→3C replay.

This is a settlement-only scenario, not a financial cash-flow or root result.
Callers supply an exclusive private workspace and an explicit bounded D3 scratch
location; neither a sealed project nor an original evidence directory is written.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from itertools import zip_longest
import os
from pathlib import Path
import re
import shutil
import stat

from ..errors import ContractError
from ..intake import IntakeSession
from ..local_files import Workspace
from ..serialization import digest, dumps
from ..timeseries_bundle import BundleBudget, read_bundle, write_bundle
from .break_even_execution import validate_price_selector
from .input_contract import validate_export
from .method_config import MethodConfig
from .revenue import calculate_ground, calculate_rooftop


@dataclass(frozen=True, slots=True)
class CandidateReplay:
    original_input_hash: str
    candidate_export: dict
    original_bundle_hash: str
    candidate_bundle_hash: str
    generation_result_hash: str
    original_revenue: dict
    candidate_revenue: dict


def _scenario_atom(original, price, source, original_id, candidate_id, selector):
    if original["original_unit"] != original["unit"]:
        # Normalized prices require their own reversible original-unit lineage.
        raise ContractError("BREAK_EVEN_ORIGINAL_UNIT_UNSUPPORTED")
    atom = deepcopy(original)
    atom.update(value=price, original_value=price, source_kind="ASSUMPTION", provenance_kind="U",
                source_id=source["source_id"], source_url_or_attachment=source["source_reference"],
                source_section_or_cell=selector["row_id"] or selector["field_id"],
                status="ASSUMED", reviewer=None, retrieved_at=None,
                confidence_basis="Controlled price scenario only; not independently verified market evidence",
                license_status=source["license_status"],
                assumption={"reason": "Controlled price override from " + source["source_reference"],
                            "method": "single-atom settlement-only Phase 3C replay",
                            "maturity_ceiling": "L1", "noncritical": False, "decision_invariant": False},
                transformation_rule_ids=[], normalization=None,
                candidate_ids=[original_id, candidate_id])
    return atom


def _derive(exported, selected, candidate_price, catalog):
    control = selected.control
    key = control["selector"]
    fid = key["field_id"]
    project = deepcopy(validate_export(exported, catalog).project.to_dict())
    # The old atom is retained as an immutable candidate, including its entire
    # source envelope. The new candidate is distinctly sourced; no hash is edited.
    original_id = "candidate-" + digest(selected.original_atom)
    new_atom = _scenario_atom(selected.original_atom, candidate_price, control["source"],
                              original_id, "", key)
    pending = deepcopy(new_atom)
    pending["candidate_ids"] = []
    candidate_id = "candidate-" + digest(pending)
    new_atom["candidate_ids"] = [original_id, candidate_id]
    project["candidates"].setdefault(original_id, deepcopy(selected.original_atom))
    project["candidates"][candidate_id] = pending
    if fid == "tariff.ppa_price":
        project["values"][fid] = new_atom
    elif fid.startswith("tariff.periods."):
        rows = project["values"]["tariff.periods"]["value"]
        matched = [row for row in rows if row["row_id"] == key["row_id"]]
        if len(matched) != 1:
            raise ContractError("BREAK_EVEN_ROW_NOT_UNIQUE")
        matched[0]["fields"][fid] = new_atom
    # Market prices live only in D3; the candidate registry and source snapshot
    # still identify this derived Phase 2 export separately from its original.
    project["revision"] += 1
    project["history"].append({"event": "break_even_price_scenario", "field_id": fid,
                               "row_id": key["row_id"], "original_atom_hash": key["original_atom_hash"],
                               "original_candidate_id": original_id, "candidate_id": candidate_id,
                               "selector_hash": selected.selector_hash, "source_id": control["source"]["source_id"]})
    candidate = validate_export(IntakeSession.from_dict(project, catalog).export(), catalog).export
    old_values, new_values = exported["project"]["values"], candidate["project"]["values"]
    if old_values.keys() != new_values.keys():
        raise ContractError("BREAK_EVEN_UNSELECTED_INPUT_CHANGED")
    for name in old_values:
        if name != "tariff.periods" or not fid.startswith("tariff.periods."):
            if name == fid:
                continue
            if dumps(old_values[name]) != dumps(new_values[name]):
                raise ContractError("BREAK_EVEN_UNSELECTED_INPUT_CHANGED")
        else:
            a, b = old_values[name]["value"], new_values[name]["value"]
            if len(a) != len(b) or [r["row_id"] for r in a] != [r["row_id"] for r in b]:
                raise ContractError("BREAK_EVEN_UNSELECTED_INPUT_CHANGED")
            for old, new in zip(a, b):
                for child in old["fields"]:
                    if child != fid or old["row_id"] != key["row_id"]:
                        if dumps(old["fields"][child]) != dumps(new["fields"][child]):
                            raise ContractError("BREAK_EVEN_UNSELECTED_INPUT_CHANGED")
    if candidate["input_hash"] == exported["input_hash"] or candidate["source_snapshot_id"] == exported["source_snapshot_id"]:
        raise ContractError("BREAK_EVEN_DERIVED_IDENTITY")
    return candidate, new_atom


def _rows(original_bundle, fid, field_id, row_id, candidate_atom):
    count = 0
    for row in original_bundle.rows(fid):
        if fid == "tariff.market_series" and field_id == "tariff.market_series.sale_price" and row["row_id"] == row_id:
            count += 1
            row = deepcopy(row)
            row["fields"][field_id] = deepcopy(candidate_atom)
        yield row
    if field_id == "tariff.market_series.sale_price" and count != 1:
        raise ContractError("BREAK_EVEN_ROW_NOT_UNIQUE")


def _verify_bundles(original, candidate, field_id, row_id):
    if original.dataset_ids != candidate.dataset_ids:
        raise ContractError("BREAK_EVEN_DATASET_CHANGED")
    for fid in original.dataset_ids:
        a, b = original.manifest["datasets"][fid], candidate.manifest["datasets"][fid]
        if a["header"] != b["header"] or a["row_count"] != b["row_count"]:
            raise ContractError("BREAK_EVEN_DATASET_CHANGED")
        if fid != "tariff.market_series" or field_id != "tariff.market_series.sale_price":
            if a["canonical_array_hash"] != b["canonical_array_hash"]:
                raise ContractError("BREAK_EVEN_DATASET_CHANGED")
        else:
            matches = 0
            for old, new in zip_longest(original.rows(fid), candidate.rows(fid)):
                if old is None or new is None or old["row_id"] != new["row_id"]:
                    raise ContractError("BREAK_EVEN_DATASET_CHANGED")
                if old["row_id"] == row_id:
                    matches += 1
                    for key in old["fields"]:
                        if key != field_id and dumps(old["fields"][key]) != dumps(new["fields"][key]):
                            raise ContractError("BREAK_EVEN_DATASET_CHANGED")
                elif dumps(old) != dumps(new):
                    raise ContractError("BREAK_EVEN_DATASET_CHANGED")
            if matches != 1:
                raise ContractError("BREAK_EVEN_ROW_NOT_UNIQUE")


def _remove_owned(root, identity, workspace):
    # Never follow a link/junction or erase a directory whose identity changed.
    if not root.exists():
        return
    if root.parent != workspace.root or (root.stat().st_dev, root.stat().st_ino) != identity:
        raise ContractError("BREAK_EVEN_CLEANUP_UNSAFE")
    for path in (root, *root.rglob("*")):
        info = path.lstat()
        if (stat.S_ISLNK(info.st_mode) or getattr(path, "is_junction", lambda: False)()
                or (stat.S_ISREG(info.st_mode) and info.st_nlink != 1)
                or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode))):
            raise ContractError("BREAK_EVEN_CLEANUP_UNSAFE")
    shutil.rmtree(root)


def replay_price_candidate(control, original_export, methods, original_bundle, generation_dir, candidate_price, *,
                           catalog, budget, workspace, run_name):
    """Public replay always computes the original, never accepts a cache."""
    return _replay_price_candidate(control, original_export, methods, original_bundle,
                                   generation_dir, candidate_price, catalog=catalog, budget=budget,
                                   workspace=workspace, run_name=run_name, original_revenue=None)


def _replay_price_candidate(control, original_export, methods, original_bundle, generation_dir, candidate_price, *,
                            catalog, budget, workspace, run_name, original_revenue):
    """Recheck one candidate's physical trace; reuse only a session-owned original."""
    if type(budget) is not BundleBudget or not isinstance(workspace, Workspace):
        raise ContractError("BREAK_EVEN_EXECUTION_CONTEXT")
    if not isinstance(run_name, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", run_name) is None:
        raise ContractError("BREAK_EVEN_RUN_NAME")
    if not isinstance(candidate_price, Decimal) or not candidate_price.is_finite():
        raise ContractError("BREAK_EVEN_CANDIDATE_PRICE")
    method = MethodConfig.from_dict(methods.to_dict() if isinstance(methods, MethodConfig) else methods)
    selected = validate_price_selector(control, original_export, method, original_bundle, catalog)
    if (candidate_price == selected.original_atom["value"] or
            not method.require("break_even.minimum_price") <= candidate_price <= method.require("break_even.maximum_price")):
        raise ContractError("BREAK_EVEN_CANDIDATE_PRICE")
    if candidate_price < 0:
        from .break_even_execution import _record_source
        _record_source(validate_export(original_export, catalog).project.values.get("tariff.negative_price_rule"))
        method.require("settlement.negative_price_treatment")
    if original_bundle is None:
        raise ContractError("BREAK_EVEN_ORIGINAL_BUNDLE_REQUIRED")
    scratch = os.environ.get("TMPDIR")
    if scratch is None or Path(scratch).resolve() != workspace.root.parent.resolve():
        raise ContractError("BREAK_EVEN_SCRATCH_OUTSIDE_WORKSPACE")
    root = workspace.path(run_name, json_only=False)
    if root.exists():
        raise ContractError("BREAK_EVEN_OUTPUT_EXISTS")
    candidate_export, candidate_atom = _derive(original_export, selected, candidate_price, catalog)
    root.mkdir(mode=0o700)
    identity = root.stat().st_dev, root.stat().st_ino
    try:
        fid, row_id = selected.control["selector"]["field_id"], selected.control["selector"]["row_id"]
        datasets = {name: {"header": original_bundle.manifest["datasets"][name]["header"],
                           "rows": _rows(original_bundle, name, fid, row_id, candidate_atom)}
                    for name in original_bundle.dataset_ids}
        write_bundle(root / "candidate-d3", base_export=candidate_export, datasets=datasets,
                     catalog=catalog, budget=budget)
        with read_bundle(root / "candidate-d3", catalog=catalog, budget=budget) as derived:
            _verify_bundles(original_bundle, derived, fid, row_id)
            if derived.content_hash == original_bundle.content_hash:
                raise ContractError("BREAK_EVEN_DERIVED_IDENTITY")
            settle = calculate_ground if control["pv_type"] == "utility_scale_ground" else calculate_rooftop
            args = dict(generation_dir=generation_dir, generation_result_hash=control["generation_result_hash"],
                        catalog=catalog, budget=budget)
            baseline = (settle(original_export, method, output_dir=root / "original-3c",
                               bundle=original_bundle, **args)
                        if original_revenue is None else original_revenue)
            scenario = settle(candidate_export, method, output_dir=root / "candidate-3c", bundle=derived, **args)
            ledger_key = "export_sales_revenue" if fid.endswith("sale_price") else "self_value"
            def settled_amount(result):
                metrics = [m for m in result["results"]["metrics"] if m["metric_id"] == "revenue"]
                if len(metrics) != 1 or metrics[0]["status"] != "CALCULATED":
                    raise ContractError("BREAK_EVEN_REVENUE_UNAVAILABLE")
                return metrics[0]["details"]["ledger"][ledger_key]
            if settled_amount(baseline) == settled_amount(scenario):
                raise ContractError("BREAK_EVEN_PRICE_NOT_CONSUMED")
            if control["source"]["source_id"] not in next(
                    m for m in scenario["results"]["metrics"] if m["metric_id"] == "revenue")["source_ids"]:
                raise ContractError("BREAK_EVEN_CANDIDATE_SOURCE_MISSING")
            return CandidateReplay(selected.original_input_hash, deepcopy(candidate_export), original_bundle.content_hash,
                                   derived.content_hash, control["generation_result_hash"], baseline, scenario)
    except BaseException:
        _remove_owned(root, identity, workspace)
        raise
