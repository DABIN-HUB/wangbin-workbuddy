"""Independent Decimal row/member/role/branch reconciliation of synthetic model receipts."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path

BRANCHES = ("MVP", "StandardA", "StandardB", "FullA", "FullB")
ROLES = ("FE", "BE", "DB", "QA")
ENDS = ("low", "high")
PARENTS = {"MVP": None, "StandardA": "MVP", "StandardB": "StandardA", "FullA": "StandardA", "FullB": "FullA"}


def file_sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check(input_path, output_path):
    request, receipt = (json.loads(p.read_text(encoding="utf-8")) for p in (input_path, output_path))
    errors = []
    def equal(label, actual, expected):
        if actual != expected:
            errors.append(f"{label}: {actual!r} != {expected!r}")
    for key in ("scope_version", "previous_scope_version"):
        equal(key, receipt.get(key), request.get(key))
    equal("scope_changed", receipt.get("scope_changed"), request.get("scope_changed", False))
    equal("input_sha256", receipt.get("input_sha256"), file_sha(input_path))
    script = Path(__file__).resolve().parent / "skill-preview" / "wangbin-estimate-calculator" / "scripts" / "estimator.py"
    equal("script_sha256", receipt.get("script_sha256"), file_sha(script))
    equal("pricing_mode", receipt.get("pricing_mode"), request["pricing"]["mode"])
    equal("labor_is_complete_total", receipt.get("labor_is_complete_total"), False)
    equal("currency_labor_only", receipt.get("currency_labor_only"), "RMB")
    rows = request["work_packages"]
    equal("row count", len(receipt["rows"]), len(rows))
    equal("row ids", [r["id"] for r in receipt["rows"]], [r["id"] for r in rows])
    for source, got in zip(rows, receipt["rows"]):
        for field in ("id", "function", "source", "scope_version", "membership", "roles"):
            equal(f"{source['id']}.{field}", got[field], source[field])
        for bound in ENDS:
            expected = sum((Decimal(source["roles"][role][bound]) for role in ROLES), Decimal(0))
            equal(f"{source['id']}.row.{bound}", Decimal(got["row"][bound]), expected)
    for branch in BRANCHES:
        got = receipt["tiers"][branch]
        selected = [r for r in rows if branch in r["membership"]]
        ids = [r["id"] for r in selected]
        equal(f"{branch}.ids", got["ids"], ids)
        equal(f"{branch}.unique", len(ids), len(set(ids)))
        parent = PARENTS[branch]
        equal(f"{branch}.parent", got["parent"], parent)
        delta = [id for id in ids if parent is None or id not in receipt["tiers"][parent]["ids"]]
        equal(f"{branch}.delta_ids", got["delta_ids"], delta)
        for field, subset in (("roles", selected), ("delta_roles", [r for r in selected if r["id"] in delta])):
            for role in ROLES:
                for bound in ENDS:
                    expected = sum((Decimal(row["roles"][role][bound]) for row in subset), Decimal(0))
                    equal(f"{branch}.{field}.{role}.{bound}", Decimal(got[field][role][bound]), expected)
        for bound in ENDS:
            base = sum((Decimal(row["roles"][role][bound]) for row in selected for role in ROLES), Decimal(0))
            risk = base * Decimal(request["buffers"][bound])
            effort = base + risk
            unit = Decimal(request["pricing"]["unit_price"])
            for field, expected in (("B", base), ("R", risk), ("E", effort), ("labor_rmb", effort * unit)):
                equal(f"{branch}.{field}.{bound}", Decimal(got[field][bound]), expected)
        equal(f"{branch}.complete_project_total_rmb", got["complete_project_total_rmb"], None)
    return {"input": str(input_path), "input_sha256": file_sha(input_path), "output": str(output_path),
            "output_sha256": file_sha(output_path), "branch_count": len(BRANCHES), "row_count": len(rows),
            "checks": "all row fields, version, members, role bounds, deltas, B/R/E/labor, total", "errors": errors}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pairs", type=Path, nargs="+")
    args = parser.parse_args()
    if len(args.pairs) % 2:
        parser.error("pairs require input and output")
    failed = False
    for index in range(0, len(args.pairs), 2):
        report = check(*args.pairs[index:index+2])
        print(json.dumps(report, ensure_ascii=False))
        failed |= bool(report["errors"])
    raise SystemExit(1 if failed else 0)
