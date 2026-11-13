"""Independent Decimal row/member/role/branch reconciliation of synthetic model receipts."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from check_frozen_source import compare, digest, CASES

BRANCHES = ("MVP", "StandardA", "StandardB", "FullA", "FullB")
ROLES = ("FE", "BE", "DB", "QA")
ENDS = ("low", "high")
PARENTS = {"MVP": None, "StandardA": "MVP", "StandardB": "StandardA", "FullA": "StandardA", "FullB": "FullA"}
NOTICE = "人民币 1000～1500 元/人天为用户批准的示意估算参数，并非实时市场行情或正式合同报价。"


def file_sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check(input_path, output_path, *, case, anchor, approval="none"):
    input_bytes = input_path.read_bytes()
    input_hash = hashlib.sha256(input_bytes).hexdigest()
    request = json.loads(input_bytes.decode("utf-8"))
    errors = compare(request, case, anchor, approval)
    report = {"input": str(input_path), "input_sha256": input_hash,
              "output": str(output_path), "output_sha256": None, "anchor_sha256": digest(anchor),
              "case": case, "source_errors": errors[:], "errors": errors}
    if errors:
        return report
    receipt_bytes = output_path.read_bytes()
    receipt = json.loads(receipt_bytes.decode("utf-8"))
    report["output_sha256"] = hashlib.sha256(receipt_bytes).hexdigest()
    def equal(label, actual, expected):
        if actual != expected:
            errors.append(f"{label}: {actual!r} != {expected!r}")
    if not isinstance(receipt.get("tiers"), dict) or set(receipt["tiers"]) != set(BRANCHES):
        errors.append("NOT_APPLICABLE: exactly five experiment tiers required")
        return report
    if not isinstance(receipt.get("rows"), list) or len(receipt["rows"]) != len(request["work_packages"]):
        errors.append("NOT_APPLICABLE: receipt row structure mismatch")
        return report
    for key in ("scope_version", "previous_scope_version"):
        equal(key, receipt.get(key), request.get(key))
    equal("scope_changed", receipt.get("scope_changed"), request.get("scope_changed", False))
    equal("input_sha256", receipt.get("input_sha256"), input_hash)
    script = Path(__file__).resolve().parent / "skill-preview" / "wangbin-estimate-calculator" / "scripts" / "estimator.py"
    equal("script_sha256", receipt.get("script_sha256"), file_sha(script))
    equal("pricing_mode", receipt.get("pricing_mode"), request["pricing"]["mode"])
    equal("labor_is_complete_total", receipt.get("labor_is_complete_total"), False)
    mode = request["pricing"]["mode"]
    equal("currency_labor_only", receipt.get("currency_labor_only"), None if mode == "refused" else "RMB")
    equal("reference_notice", receipt.get("reference_notice"), NOTICE if mode == "reference" else None)
    equal("unit_effort", receipt.get("unit_effort"), "person-days")
    equal("outside_fees", receipt.get("outside_fees"), "UNKNOWN; inquire separately")
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
            for field, expected in (("B", base), ("R", risk), ("E", effort)):
                equal(f"{branch}.{field}.{bound}", Decimal(got[field][bound]), expected)
            if mode == "refused":
                equal(f"{branch}.labor_rmb", got.get("labor_rmb"), None)
            else:
                unit = Decimal(request["pricing"]["unit_price"]) if mode == "fixed" else Decimal("1000" if bound == "low" else "1500")
                equal(f"{branch}.labor_rmb.{bound}", Decimal(got["labor_rmb"][bound]), effort * unit)
        equal(f"{branch}.complete_project_total_rmb", got["complete_project_total_rmb"], None)
        equal(f"{branch}.condition", got.get("condition"),
              "ASSUMED_CONDITIONAL" if branch in ("StandardB", "FullB") and "I1" in ids else "SOURCE_AS_DECLARED_NOT_VERIFIED")
    report.update(branch_count=len(BRANCHES), row_count=len(rows),
                  checks="frozen source, rows, versions, members, roles, deltas, B/R/E, mode-specific labor, total")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES, required=True)
    parser.add_argument("--frozen-v1", type=Path, required=True, help="independently frozen WB-02 input, SHA pinned")
    parser.add_argument("--approval", choices=("none", "delete-S2-v2"), default="none")
    parser.add_argument("pairs", type=Path, nargs="+")
    args = parser.parse_args()
    if len(args.pairs) % 2:
        parser.error("pairs require input and output")
    failed = False
    for index in range(0, len(args.pairs), 2):
        try:
            report = check(*args.pairs[index:index+2], case=args.case, anchor=args.frozen_v1, approval=args.approval)
        except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
            report = {"case": args.case, "errors": [f"NOT_APPLICABLE: malformed or unavailable experiment input/receipt ({type(exc).__name__})"]}
        print(json.dumps(report, ensure_ascii=False))
        failed |= bool(report["errors"])
    raise SystemExit(1 if failed else 0)
