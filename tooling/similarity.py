"""Conservative, evidence-limited cross-product similarity inventory.

Similarity metrics are review aids, never WorkBuddy compliance thresholds.
"""
from __future__ import annotations

import ast
import hashlib
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

import yaml


COLUMN_NAMES = {"FIELDS", "REQUIRED_COLUMNS", "BALANCE_COLUMNS", "RECEIPT_COLUMNS", "ISSUE_COLUMNS", "MASTER_COLUMNS"}
CORE_FUNCTIONS = {"analyze", "analyze_csv", "_calculate"}


def _literal_columns(node: ast.AST) -> set[str]:
    if not isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return set()
    return {value.value for value in node.elts if isinstance(value, ast.Constant) and isinstance(value.value, str)}


def _profile(root: Path, product: dict, source: Path) -> dict:
    result = {"id": product["id"], "type": product["type"], "source_available": source.is_dir(),
              "metadata": {"name": product.get("name", ""), "target_users": product.get("target_users", ""),
                           "scenario": product.get("scenario", ""), "description_zh": "", "description_en": ""},
              "scripts": [], "input_fields": [], "output_fields": [], "functions": [], "core_functions": [],
              "evidence": []}
    if not source.is_dir():
        return result
    skill = source / "SKILL.md"
    if skill.is_file() and not skill.is_symlink():
        text = skill.read_text(encoding="utf-8")
        if text.startswith("---\n"):
            try:
                front = yaml.safe_load(text.split("---", 2)[1])
                if isinstance(front, dict):
                    for key in ("display_name", "display_name_en", "description_zh", "description_en"):
                        result["metadata"][key] = str(front.get(key) or "")
                    result["evidence"].append(skill.relative_to(root).as_posix())
            except yaml.YAMLError:
                pass
    inputs: set[str] = set()
    outputs: set[str] = set()
    functions: list[dict] = []
    for script in sorted((source / "scripts").glob("*.py")):
        if script.is_symlink() or script.stat().st_size > 1_048_576:
            continue
        relative = script.relative_to(root).as_posix()
        try:
            tree = ast.parse(script.read_text(encoding="utf-8"), filename=relative)
        except (SyntaxError, OSError, UnicodeError):
            continue
        result["scripts"].append(relative)
        result["evidence"].append(relative)
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id in COLUMN_NAMES for target in node.targets):
                inputs.update(_literal_columns(node.value))
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = ast.Module(body=node.body, type_ignores=[])
            shape = ast.dump(body, include_attributes=False)
            # Exact equality includes constants, computation, and error handling,
            # but not the function name or local source location.
            keys = set()
            if node.name in CORE_FUNCTIONS:
                for child in ast.walk(node):
                    if isinstance(child, ast.Return) and isinstance(child.value, ast.Dict):
                        keys.update(key.value for key in child.value.keys
                                    if isinstance(key, ast.Constant) and isinstance(key.value, str))
                outputs.update(keys)
            functions.append({"name": node.name, "path": f"{relative}:{node.lineno}",
                              "sha256": hashlib.sha256(shape.encode("utf-8")).hexdigest(),
                              "nodes": [type(child).__name__ for child in ast.walk(body)],
                              "core": node.name in CORE_FUNCTIONS})
    result.update(input_fields=sorted(inputs), output_fields=sorted(outputs),
                  functions=functions, core_functions=sorted({f["name"] for f in functions if f["core"]}))
    return result


def _pair(left: dict, right: dict) -> dict:
    inputs_l, inputs_r = set(left["input_fields"]), set(right["input_fields"])
    outputs_l, outputs_r = set(left["output_fields"]), set(right["output_fields"])
    exact = [{"left": a["path"], "right": b["path"], "name": a["name"]}
             for a in left["functions"] for b in right["functions"] if a["sha256"] == b["sha256"]]
    core_exact = any(a["core"] and a["sha256"] == b["sha256"]
                     for a in left["functions"] for b in right["functions"])
    shape = SequenceMatcher(None,
                            [node for f in left["functions"] for node in f["nodes"]],
                            [node for f in right["functions"] for node in f["nodes"]], autojunk=True).ratio()
    shared_metadata = [key for key in ("name", "target_users", "scenario", "description_zh", "description_en")
                       if left["metadata"].get(key) and left["metadata"].get(key) == right["metadata"].get(key)]
    if not all((left["scripts"], right["scripts"], inputs_l, inputs_r, outputs_l, outputs_r)):
        classification = "INSUFFICIENT_EVIDENCE"
        reason = "A source script or extractable input/output contract is missing; human review is necessary."
    elif core_exact and inputs_l == inputs_r and outputs_l == outputs_r:
        classification = "LIKELY_DUPLICATE"
        reason = "An exact core function and the same extracted input/output contract require duplicate review."
    elif inputs_l == inputs_r or outputs_l == outputs_r or core_exact:
        classification = "OVERLAP_REVIEW"
        reason = "Input/output contracts or core implementations overlap; independent value needs review."
    else:
        classification = "DISTINCT"
        reason = "Extracted contracts and core implementations differ; independent service value still needs human review."
    return {"left": left["id"], "right": right["id"], "classification": classification,
            "reason": reason, "review_status": "REVIEW_REQUIRED",
            "code": {"ast_node_sequence_ratio": round(shape, 4), "exact_functions": exact,
                     "core_exact": core_exact, "method": "Python AST node sequence; descriptive only, no official threshold"},
            "function_overlap": {"core_left": left["core_functions"], "core_right": right["core_functions"],
                                 "semantic_review": "REVIEW_REQUIRED"},
            "metadata": {"identical_nonempty_fields": shared_metadata},
            "input_output": {"shared_inputs": sorted(inputs_l & inputs_r), "left_only_inputs": sorted(inputs_l - inputs_r),
                             "right_only_inputs": sorted(inputs_r - inputs_l), "shared_outputs": sorted(outputs_l & outputs_r),
                             "left_only_outputs": sorted(outputs_l - outputs_r), "right_only_outputs": sorted(outputs_r - outputs_l)},
            "independent_value": "REVIEW_REQUIRED", "human_confirmation": [
                "Compare actual algorithms, decisions, users and service necessity; a structural score is not compliance evidence.",
                "Confirm current marketplace metadata and real platform review separately."]}


def similarity_check(root: Path, product_id: str | None = None) -> dict:
    """Compare every registered product, or one product against every peer."""
    # Import here to preserve the existing product factory import graph.
    from .product_factory import _source, load_catalog, validate_catalog

    findings = validate_catalog(root)
    if findings:
        raise ValueError("; ".join(findings))
    products = load_catalog(root)["products"]
    if product_id is not None and product_id not in {item["id"] for item in products}:
        raise ValueError(f"unregistered product: {product_id}")
    profiles = [_profile(root, item, _source(root, item)) for item in products]
    pairs = [_pair(left, right) for left, right in combinations(profiles, 2)
             if product_id is None or product_id in {left["id"], right["id"]}]
    gates = {"ANTI_DUPLICATION_PASS": "REVIEW_REQUIRED", "FUNCTIONAL_DISTINCTNESS_PASS": "REVIEW_REQUIRED",
             "INPUT_OUTPUT_DISTINCTNESS_PASS": "REVIEW_REQUIRED", "METADATA_DISTINCTNESS_PASS": "REVIEW_REQUIRED",
             "INDEPENDENT_VALUE_PASS": "REVIEW_REQUIRED", "LICENSE_PASS": "BLOCKED",
             "LOCAL_TEST_PASS": "NOT_TESTED", "WORKBUDDY_RUNTIME_PASS": "NOT_TESTED", "PUBLISH_READY": "BLOCKED"}
    return {"status": "REVIEW_REQUIRED", "scope": "internal source/metadata comparison; not WorkBuddy certification",
            "product_id": product_id, "product_count": len(profiles), "pair_count": len(pairs),
            "profiles": [{key: value for key, value in p.items() if key != "functions"} for p in profiles
                         if product_id is None or p["id"] == product_id],
            "pairs": pairs, "gates": gates,
            "manual_review": "Code signatures cannot establish lawful asset differentiation, market necessity, or platform approval."}
