"""Single effective formula registry, planned modules and evidence-backed status.

Registration alone is never IMPLEMENTED_TESTED. Phase 8 storage definitions
remain present and cannot be substituted with an unbuffered consumption model.
"""
from __future__ import annotations

from copy import deepcopy
from importlib import import_module
from pathlib import Path

from ..errors import ContractError
from ..serialization import loads

_KERNEL_MODULES = ("engineering", "consumption", "costs", "accounting_ledger", "financial_metrics", "scenarios")


def _kernels():
    result = {}
    for name in _KERNEL_MODULES:
        module_name = __package__ + "." + name
        try:
            module = import_module(module_name)
        except ModuleNotFoundError as error:
            if error.name != module_name:
                raise
            continue
        for formula_id in module.FORMULA_IDS:
            if formula_id in result:
                raise ContractError("DUPLICATE_FORMULA_EXECUTOR", formula_id)
            result[formula_id] = module
    return result


def _planned_module(formula_id):
    if formula_id.startswith("F-STORAGE-"):
        return "storage (Phase8)"
    if formula_id in {"F-SELF-CONSUMPTION", "F-EXPORTED-ENERGY", "F-CURTAILED-ENERGY", "F-ENERGY-BALANCE", "F-DELIVERED-ENERGY", "F-SELF-CONSUMPTION-RATIO", "F-LOAD-COVERAGE-RATIO", "F-ENERGY-REVENUE", "F-PPA-REVENUE"}:
        return "consumption"
    if formula_id in {"F-SINGLE-FACTOR-SENSITIVITY", "F-SENSITIVITY-ELASTICITY", "F-SCENARIO-METRIC"}:
        return "scenarios"
    if formula_id in {"F-CASH-RECEIPTS", "F-DEBT-SERVICE", "F-CAPEX-PAYMENT-BALANCE"}:
        return "accounting_ledger"
    if formula_id.startswith(("F-CAPEX-", "F-TAX", "F-INCOME-", "F-VAT-", "F-OTHER-CASH-TAX", "F-DEBT-BALANCE", "F-DEBT-INTEREST", "F-INTEREST-", "F-ANNUAL-OPEX", "F-OPEX-", "F-STRAIGHT-", "F-ASSET-", "F-UNIT-INVESTMENT", "F-CASH-TAX-")):
        return "costs"
    if formula_id.startswith(("F-IRR-", "F-NPV", "F-DATED-", "F-NOMINAL-", "F-CUMULATIVE-", "F-STATIC-", "F-DISCOUNTED-", "F-DYNAMIC-", "F-LIFECYCLE-", "F-LCOE", "F-CFADS", "F-DEBT-SERVICE", "F-DSCR", "F-BREAK-", "F-WORST-", "F-INVESTMENT-", "F-PROJECT-", "F-EQUITY-", "F-CASH-")):
        return "financial_metrics"
    return "engineering"


def execution_inventory(catalog):
    catalog.definition_identity()
    kernels = _kernels()
    evidence_file = Path(__file__).with_name("execution-evidence.json")
    evidence = loads(evidence_file.read_bytes()) if evidence_file.is_file() else {}
    result = []
    for fid, definition in catalog.formulas.items():
        kernel = kernels.get(fid)
        proof = evidence.get(fid)
        verified = bool(kernel and proof and proof.get("status") == "NUMERICAL_VERIFICATION_PASS"
                        and proof.get("test_ids") and proof.get("evidence_ids")
                        and proof.get("definition_hash") == catalog.definition_hash)
        phase3 = definition.get("implementation_stage") != "Phase 8"
        if not phase3 and kernel is not None:
            raise ContractError("STORAGE_EXECUTION_OUTSIDE_PHASE3", fid)
        result.append({"formula_id": fid, "definition": deepcopy(definition),
                       "definition_version": catalog.definition_version, "definition_hash": catalog.definition_hash,
                       "phase3_applicable": phase3, "planned_module": _planned_module(fid),
                       "executor": None if kernel is None else kernel.__name__ + ":evaluate",
                       "status": "IMPLEMENTED_TESTED" if verified else "NOT_IMPLEMENTED",
                       "numerical_validation_status": "PASS" if verified else "NOT_TESTED",
                       "evidence": deepcopy(proof) if verified else None,
                       "precision_rule": "DECLARED_LOCAL_DECIMAL_CONTEXT_NO_EARLY_CENT_ROUNDING",
                       "absolute_tolerance_parameter": "precision.abs_tolerance",
                       "relative_tolerance_parameter": "precision.rel_tolerance",
                       "missing_input_policy": "BLOCKED_MISSING_INPUT_NOT_ZERO",
                       "project_applicability": "EVALUATED_SEPARATELY_FROM_PRODUCT_IMPLEMENTATION"})
    if set(kernels) - set(catalog.formulas):
        raise ContractError("UNREGISTERED_FORMULA_EXECUTOR")
    return result


def run_formula(formula_id, values, options=None, *, catalog):
    catalog.definition_identity()
    if formula_id not in catalog.formulas:
        raise ContractError("UNKNOWN_FORMULA", formula_id)
    kernel = _kernels().get(formula_id)
    if kernel is None:
        return {"status": "NOT_IMPLEMENTED", "value": None, "reason": "NO_EXECUTABLE_KERNEL", "details": {}}
    return kernel.evaluate(formula_id, values, options)
