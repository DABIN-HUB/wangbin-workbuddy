"""Private, bounded original-price session for sourced SYNTHETIC NPV(p).

This is not a root solver. It saves only the authenticated original 3C/3D/3E
chain; every different price still executes the approved candidate engines.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
import os
from pathlib import Path
import re
import stat
from threading import Lock
from time import perf_counter

from ..errors import ContractError
from ..local_files import Workspace
from ..serialization import MAX_JSON_BYTES, digest, dumps, loads
from ..timeseries_bundle import BundleBudget, TimeSeriesBundle
from ..timeseries_private import Meter, checked_read, local_target
from .break_even_execution import validate_price_selector
from .break_even_financial_replay import _check_financial, _check_settlement
from .break_even_project_npv import ProjectNpvCandidate, _calculate_candidate, _npv
from .break_even_replay import _remove_owned
from .financial_ledger import calculate_financial_ledger, write_financial_bundle
from .method_config import MethodConfig
from .phase3e import calculate_sourced_project_npv, write_phase3e_bundle
from .result_contract import validate_result
from .revenue import calculate_ground, calculate_rooftop
from .terminal_disposition import validate_terminal_disposition


def _file_hashes(path, budget, required):
    """Pin every private artifact with bounded, descriptor-checked reads."""
    root = local_target(path)
    hashes = {}
    meter = Meter(budget)
    names = {p.name for p in root.iterdir()}
    for file in root.iterdir():
        metadata = file.lstat()
        if (not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1
                or getattr(file, "is_junction", lambda: False)()):
            raise ContractError("BREAK_EVEN_GENERATION_FILES_CHANGED")
        hashes[file.name] = sha256(checked_read(file, metadata.st_size, meter)).hexdigest()
    if names != {p.name for p in root.iterdir()}:
        raise ContractError("BREAK_EVEN_GENERATION_FILES_CHANGED")
    if not required <= hashes.keys():
        raise ContractError("BREAK_EVEN_GENERATION_FILES_CHANGED")
    return hashes


def _physical_files(path, budget):
    """Pin the entire 3B trace, not only its result hash."""
    return _file_hashes(path, budget, {"result.json", "receipt.json"})


def _bounded_read(path, maximum, meter):
    size = path.lstat().st_size
    if size > maximum:
        raise ContractError("BREAK_EVEN_SESSION_OUTPUT_UNSAFE")
    return checked_read(path, size, meter)


_EXECUTOR_FILES = (
    "break_even_project_npv.py", "break_even_project_session.py",
    "break_even_certification.py", "terminal_disposition.py",
    "break_even_replay.py", "break_even_financial_replay.py", "revenue.py",
    "financial_ledger.py", "terminal_binding.py", "phase3e.py",
    "financial_metrics.py", "method_config.py", "tariffs.py",
    "costs.py", "generation_evidence.py", "result_contract.py",
    "input_contract.py",
)


def _executor_identity():
    here = Path(__file__).parent
    return {name: sha256((here / name).read_bytes()).hexdigest() for name in _EXECUTOR_FILES}


def _owned_bytes(path):
    total = 0
    for file in path.rglob("*"):
        info = file.lstat()
        if (not (stat.S_ISDIR(info.st_mode) or
                 (stat.S_ISREG(info.st_mode) and info.st_nlink == 1))
                or getattr(file, "is_junction", lambda: False)()):
            raise ContractError("BREAK_EVEN_SESSION_OUTPUT_UNSAFE")
        if stat.S_ISREG(info.st_mode):
            total += info.st_size
    return total


class ProjectNpvSession:
    """One non-shareable session; the original and each candidate own private roots."""

    def __init__(self, control, original_export, methods, original_bundle,
                 generation_dir, terminal_carrier, source_documents, *,
                 catalog, budget, workspace, run_name):
        if (type(budget) is not BundleBudget or not isinstance(workspace, Workspace)
                or not isinstance(original_bundle, TimeSeriesBundle)
                or not isinstance(run_name, str)
                or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", run_name) is None):
            raise ContractError("BREAK_EVEN_EXECUTION_CONTEXT")
        scratch = os.environ.get("TMPDIR")
        if scratch is None or Path(scratch).resolve() != workspace.root.parent.resolve():
            raise ContractError("BREAK_EVEN_SCRATCH_OUTSIDE_WORKSPACE")
        if not isinstance(source_documents, dict) or any(not isinstance(v, bytes) for v in source_documents.values()):
            raise ContractError("TERMINAL_SOURCE_BYTES_MISMATCH")
        self.control = deepcopy(control)
        self.original_export = deepcopy(original_export)
        self.methods = MethodConfig.from_dict(methods.to_dict() if isinstance(methods, MethodConfig) else methods)
        self.original_bundle = original_bundle
        self.generation_dir = local_target(generation_dir)
        self.terminal_carrier = deepcopy(terminal_carrier)
        self.source_documents = dict(source_documents)
        self.catalog, self.budget, self.workspace = catalog, budget, workspace
        self.run_name = run_name
        self._lock = Lock()
        self._candidate_names = set()
        self._counts = {"original_3c": 0, "original_3d": 0, "original_3e": 0,
                        "candidate_3c": 0, "candidate_3d": 0, "candidate_3e": 0}
        self.timings = {}
        started = perf_counter()
        selected = validate_price_selector(self.control, self.original_export, self.methods,
                                           original_bundle, catalog)
        checked = validate_terminal_disposition(self.terminal_carrier, self.source_documents)
        self.original_price = selected.original_atom["value"]
        self.price_min = self.methods.require("break_even.minimum_price")
        self.price_max = self.methods.require("break_even.maximum_price")
        self.maximum_candidates = self.methods.require("break_even.maximum_iterations")
        self.executor_sha256 = _executor_identity()
        self._fingerprint = digest({"control": self.control, "export": self.original_export,
                                    "method": self.methods.to_dict(), "carrier": self.terminal_carrier,
                                    "documents": {k: sha256(v).hexdigest() for k, v in self.source_documents.items()},
                                    "catalog": {"formulas": catalog.formulas, "fields": catalog.fields,
                                                "bindings": catalog.bindings, "definition": catalog.definition_version},
                                    "d3": original_bundle.content_hash,
                                    "executor": self.executor_sha256})
        if checked.source_content_hash != self.terminal_carrier["source_content_hash"]:
            raise ContractError("BREAK_EVEN_ORIGINAL_CACHE_IDENTITY")
        self._physical = _physical_files(self.generation_dir, budget)
        self.timings["source_selector_and_3b_identity_seconds"] = perf_counter() - started
        self.root = workspace.path(run_name, json_only=False)
        if self.root.exists():
            raise ContractError("BREAK_EVEN_OUTPUT_EXISTS")
        self.root.mkdir(mode=0o700)
        identity = self.root.stat().st_dev, self.root.stat().st_ino
        try:
            settle = calculate_ground if self.control["pv_type"] == "utility_scale_ground" else calculate_rooftop
            t = perf_counter()
            self.original_revenue = settle(self.original_export, self.methods,
                generation_dir=self.generation_dir, generation_result_hash=self.control["generation_result_hash"],
                catalog=catalog, output_dir=self.root / "original-3c", budget=budget, bundle=original_bundle)
            self.timings["original_3c_and_3b_read_seconds"] = perf_counter() - t
            self._counts["original_3c"] += 1
            _check_settlement(self.original_revenue, self.original_export, self.methods,
                              original_bundle.content_hash, self.control["generation_result_hash"], catalog)
            t = perf_counter()
            self.original_financial = calculate_financial_ledger(
                self.original_export, self.methods, self.original_revenue, catalog=catalog)
            self._counts["original_3d"] += 1
            _check_financial(self.original_financial, self.original_revenue["result_hash"],
                             self.original_export, self.methods, catalog)
            write_financial_bundle(self.original_financial, self.root / "original-3d")
            self.timings["original_3d_seconds"] = perf_counter() - t
            t = perf_counter()
            generation = loads((self.generation_dir / "result.json").read_bytes())
            self.original_result = calculate_sourced_project_npv(
                self.terminal_carrier, self.source_documents, self.original_export, self.methods,
                original_bundle, generation, self.original_revenue, self.original_financial,
                catalog, basis_control=self.control, original_export=self.original_export,
                original_bundle=original_bundle)
            self.original_npv = _npv(self.original_result, catalog)
            self._counts["original_3e"] += 1
            write_phase3e_bundle(self.original_result, self.root / "original-3e")
            self.timings["original_3e_binding_and_publish_seconds"] = perf_counter() - t
            self.timings["session_open_seconds"] = perf_counter() - started
            self._original_published = {
                "original-3c": self.original_revenue,
                "original-3d": self.original_financial,
                "original-3e": self.original_result,
            }
            self._original_file_hashes = {}
            for name, expected in self._original_published.items():
                target = self.root / name
                if loads(_bounded_read(target / "result.json", MAX_JSON_BYTES, Meter(budget))) != expected:
                    raise ContractError("BREAK_EVEN_ORIGINAL_CACHE_IDENTITY")
                required = ({"result.json", "receipt.json"} if name == "original-3c"
                            else {"result.json", "result.sha256"})
                self._original_file_hashes[name] = _file_hashes(target, budget, required)
            (self.root / "session.json").write_text(dumps({
                "original_price": self.original_price, "original_npv": self.original_npv,
                "original_result_hash": self.original_result["result_hash"],
                "original_3c_hash": self.original_revenue["result_hash"],
                "original_3d_hash": self.original_financial["result_hash"],
                "phase3b_hash": generation["result_hash"],
                "terminal_source_hash": checked.source_content_hash,
                "method_config_hash": self.methods.hash,
                "original_d3_hash": original_bundle.content_hash,
                "executor_sha256": self.executor_sha256,
                "fingerprint": self._fingerprint, "timings": self.timings,
                "counts": self._counts}), encoding="utf-8")
            self._session_receipt = (self.root / "session.json").read_bytes()
            self._published_disk_bytes = _owned_bytes(self.root)
            if self._published_disk_bytes > budget.max_disk_bytes:
                raise ContractError("BREAK_EVEN_SESSION_DISK_BUDGET")
        except BaseException:
            _remove_owned(self.root, identity, workspace)
            raise

    @property
    def counts(self):
        return dict(self._counts)

    def _check_pins(self):
        current = digest({"control": self.control, "export": self.original_export,
                          "method": self.methods.to_dict(), "carrier": self.terminal_carrier,
                          "documents": {k: sha256(v).hexdigest() for k, v in self.source_documents.items()},
                          "catalog": {"formulas": self.catalog.formulas, "fields": self.catalog.fields,
                                      "bindings": self.catalog.bindings, "definition": self.catalog.definition_version},
                          "d3": self.original_bundle.content_hash,
                          "executor": _executor_identity()})
        if current != self._fingerprint or _physical_files(self.generation_dir, self.budget) != self._physical:
            raise ContractError("BREAK_EVEN_SESSION_SOURCE_CHANGED")
        for result in (self.original_revenue, self.original_financial, self.original_result):
            validate_result(result, self.catalog)
        if _bounded_read(self.root / "session.json", MAX_JSON_BYTES, Meter(self.budget)) != self._session_receipt:
            raise ContractError("BREAK_EVEN_SESSION_SOURCE_CHANGED")
        for name, expected in self._original_published.items():
            target = self.root / name
            required = ({"result.json", "receipt.json"} if name == "original-3c"
                        else {"result.json", "result.sha256"})
            if _file_hashes(target, self.budget, required) != self._original_file_hashes[name]:
                raise ContractError("BREAK_EVEN_SESSION_SOURCE_CHANGED")
        if _npv(self.original_result, self.catalog) != self.original_npv:
            raise ContractError("BREAK_EVEN_ORIGINAL_CACHE_IDENTITY")
        for fid in self.original_bundle.dataset_ids:
            for _ in self.original_bundle.rows(fid):
                pass
        if self.original_bundle.base_export != self.original_export:
            raise ContractError("BREAK_EVEN_SESSION_SOURCE_CHANGED")

    def evaluate(self, price, *, run_name):
        """Original price is read from the proven session, never a fake replay."""
        if not isinstance(price, Decimal) or not price.is_finite() or not self.price_min <= price <= self.price_max:
            raise ContractError("BREAK_EVEN_CANDIDATE_PRICE")
        if (not isinstance(run_name, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", run_name) is None
                or run_name == self.run_name):
            raise ContractError("BREAK_EVEN_RUN_NAME")
        with self._lock:
            self._check_pins()
            if price == self.original_price:
                return ProjectNpvCandidate(price, self.original_npv, self.original_npv,
                    self.original_result["result_hash"], self.original_result["result_hash"],
                    self.terminal_carrier["source_content_hash"], self.control["generation_result_hash"],
                    self.original_revenue["result_hash"], self.original_financial["result_hash"],
                    self.original_export["input_hash"], self.original_bundle.content_hash, 0.0)
            if run_name in self._candidate_names or self.workspace.path(run_name, json_only=False).exists():
                raise ContractError("BREAK_EVEN_OUTPUT_EXISTS")
            if self._counts["candidate_3c"] >= self.maximum_candidates:
                raise ContractError("BREAK_EVEN_CANDIDATE_BUDGET_EXHAUSTED")
            if self._published_disk_bytes >= self.budget.max_disk_bytes:
                raise ContractError("BREAK_EVEN_SESSION_DISK_BUDGET")
            t = perf_counter()
            output = _calculate_candidate(self.control, self.original_export, self.methods,
                self.original_bundle, self.generation_dir, price, self.terminal_carrier,
                self.source_documents, catalog=self.catalog, budget=self.budget,
                workspace=self.workspace, run_name=run_name,
                original_cache=(self.original_revenue, self.original_financial, self.original_result))
            candidate_root = self.workspace.path(run_name, json_only=False)
            identity = candidate_root.stat().st_dev, candidate_root.stat().st_ino
            try:
                size = _owned_bytes(candidate_root)
                if self._published_disk_bytes + size > self.budget.max_disk_bytes:
                    raise ContractError("BREAK_EVEN_SESSION_DISK_BUDGET")
            except BaseException:
                _remove_owned(candidate_root, identity, self.workspace)
                raise
            self._published_disk_bytes += size
            self._candidate_names.add(run_name)
            self._counts["candidate_3c"] += 1
            self._counts["candidate_3d"] += 1
            self._counts["candidate_3e"] += 1
            self.timings[run_name + "_seconds"] = perf_counter() - t
            return output
