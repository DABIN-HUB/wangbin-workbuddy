"""Frozen synthetic user-fact audit, outside the unchanged installation candidate.

The anchor SHA is pinned from pre-model freeze and independent QA; never create an
anchor from the model's request or receipt. Not a WorkBuddy runtime guard.
"""
import hashlib
import json
from pathlib import Path

V1_SHA = "f884e08d9314934887037c741495c291449ed682e38a2ddfd17c7ee93c3843bc"
CASES = {"WB-01": ("1200", "mvp"), "WB-02": ("1200", "v1"),
         "WB-03": ("1350", "v1"), "WB-04": (None, "v1"),
         "WB-05-unchanged": ("1200", "v1"),
         "WB-05-changed": ("1200", "delete-S2-v2"),
         "REFERENCE-v1": (None, "reference-v1")}
ROLES = ("FE", "BE", "DB", "QA")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compare(request, case, anchor, approval="none"):
    errors = []
    def equal(label, actual, expected):
        if actual != expected:
            errors.append(f"SOURCE {label}: {actual!r} != {expected!r}")
    if case not in CASES:
        return ["SOURCE unsupported case (no frozen user facts)"]
    price, variant = CASES[case]
    changed = variant == "delete-S2-v2"
    equal("approval", approval, "delete-S2-v2" if changed else "none")
    anchor_bytes = Path(anchor).read_bytes()
    if hashlib.sha256(anchor_bytes).hexdigest() != V1_SHA:
        return errors + ["SOURCE frozen v1 anchor hash mismatch"]
    original = json.loads(anchor_bytes.decode("utf-8"))
    version = "synthetic-v2" if changed else "synthetic-v1"
    equal("scope_version", request.get("scope_version"), version)
    equal("previous_scope_version", request.get("previous_scope_version"), "synthetic-v1" if changed else None)
    equal("scope_changed", request.get("scope_changed", False), changed)
    baseline = original["work_packages"]
    baseline = baseline[:2] if variant == "mvp" else [row for row in baseline if not changed or row["id"] != "S2"]
    rows = request.get("work_packages")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        return errors + ["SOURCE work_packages: array of objects required"]
    equal("row IDs", [r.get("id") for r in rows], [r["id"] for r in baseline])
    for index, (actual, old) in enumerate(zip(rows, baseline)):
        for field in ("id", "function", "source", "membership"):
            equal(f"row[{index}].{field}", actual.get(field), old[field])
        equal(f"row[{index}].scope_version", actual.get("scope_version"), version)
        roles = actual.get("roles")
        if not isinstance(roles, dict):
            errors.append(f"SOURCE row[{index}].roles missing")
            continue
        for role in ROLES:
            bounds = roles.get(role)
            for side in ("low", "high"):
                equal(f"row[{index}].{role}.{side}", bounds.get(side) if isinstance(bounds, dict) else None, old["roles"][role][side])
    equal("buffers", request.get("buffers"), original["buffers"])
    equal("outside_fees", request.get("outside_fees"), original["outside_fees"])
    pricing = request.get("pricing")
    mode = "refused" if case == "WB-04" else "reference" if variant == "reference-v1" else "fixed"
    if not isinstance(pricing, dict):
        return errors + ["SOURCE pricing missing"]
    equal("pricing.mode", pricing.get("mode"), mode)
    if mode == "fixed":
        equal("pricing.fields", set(pricing), {"mode", "unit_price", "source"})
        equal("pricing.unit_price", pricing.get("unit_price"), price)
        equal("pricing.source", pricing.get("source"),
              "SYNTHETIC WB-03 user changes 1200 to 1350" if case == "WB-03" else original["pricing"]["source"])
    else:
        equal("pricing.fields", set(pricing), {"mode"})
    return errors
