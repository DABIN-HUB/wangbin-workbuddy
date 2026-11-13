"""Standalone structured-input Decimal effort oracle; not wired into the Expert."""
import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
import sys
from pathlib import Path

TIERS = ("MVP", "Standard", "FullA", "FullB")
ROLES = ("FE", "BE", "DB", "QA")
ZERO = Decimal("0")
BRANCHES = ("MVP", "StandardA", "StandardB", "FullA", "FullB")
PARENTS = {"MVP": None, "StandardA": "MVP", "StandardB": "StandardA",
           "FullA": "StandardA", "FullB": "FullA"}


def fields(value, required, optional=(), where="input"):
    if not isinstance(value, dict):
        raise ValueError(f"{where}: expected object")
    absent = set(required) - value.keys()
    extra = value.keys() - set(required) - set(optional)
    if absent or extra:
        raise ValueError(f"{where}: missing={sorted(absent)} unknown={sorted(extra)}")


def number(value, where, *, maximum=None):
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f"{where}: expected decimal string")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{where}: invalid decimal") from exc
    if not result.is_finite() or result < ZERO or (maximum is not None and result > maximum):
        raise ValueError(f"{where}: out of range")
    return result


def text(value, where):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where}: nonempty text required")
    return value


def fmt(value):
    return format(value, "f")


def estimate_branches(data):
    """Five explicit member sets; neither StandardB nor FullA inherits the other."""
    fields(data, ("scope_version", "work_packages", "buffers", "pricing", "outside_fees"),
           ("previous_scope_version", "scope_changed", "reported", "label"))
    version = text(data["scope_version"], "scope_version")
    changed = data.get("scope_changed", False)
    previous = data.get("previous_scope_version")
    if not isinstance(changed, bool) or changed != (previous is not None):
        raise ValueError("scope change requires previous_scope_version and scope_changed=true")
    if previous is not None and text(previous, "previous_scope_version") == version:
        raise ValueError("scope change requires a new version")
    fields(data["buffers"], ("low", "high", "source"), where="buffers")
    rates = {s: number(data["buffers"][s], "buffers." + s, maximum=Decimal("1"))
             for s in ("low", "high")}
    text(data["buffers"]["source"], "buffers.source")
    fields(data["pricing"], ("mode",), ("unit_price", "source"), "pricing")
    price = data["pricing"]
    mode = price["mode"]
    if mode not in ("fixed", "reference", "refused"):
        raise ValueError("pricing.mode: fixed/reference/refused required")
    unit = ZERO
    if mode == "fixed":
        if set(price) != {"mode", "unit_price", "source"}:
            raise ValueError("fixed price needs unit_price and source")
        unit = number(price["unit_price"], "pricing.unit_price")
        text(price["source"], "pricing.source")
    elif set(price) != {"mode"}:
        raise ValueError("reference/refused cannot supply a price")
    fields(data["outside_fees"], ("status",), where="outside_fees")
    if data["outside_fees"]["status"] != "unknown":
        raise ValueError("outside fees: only explicit unknown supported")
    rows = data["work_packages"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("work_packages: nonempty array required")
    unique = {}
    for index, row in enumerate(rows):
        where = f"work_packages[{index}]"
        fields(row, ("id", "function", "source", "scope_version", "roles", "membership"),
               ("new",), where)
        ident = text(row["id"], where + ".id")
        text(row["function"], where + ".function")
        source = text(row["source"], where + ".source")
        if not ("ASSUMED" in source or "SYNTHETIC" in source or
                "turn " in source or "话轮" in source or "line " in source):
            raise ValueError(where + ".source: require traceable turn/line or ASSUMED/SYNTHETIC")
        if row["scope_version"] != version:
            raise ValueError(where + ": scope version mismatch; change requires new snapshot")
        if "new" in row and not isinstance(row["new"], bool):
            raise ValueError(where + ".new: boolean required")
        members = row["membership"]
        if (not isinstance(members, list) or not members or
                any(not isinstance(m, str) or m not in BRANCHES for m in members) or
                len(set(members)) != len(members)):
            raise ValueError(where + ".membership: invalid or duplicate plan")
        fields(row["roles"], ROLES, where=where + ".roles")
        for role in ROLES:
            fields(row["roles"][role], ("low", "high"), where=where + ".roles." + role)
            low = number(row["roles"][role]["low"], where + "." + role + ".low")
            high = number(row["roles"][role]["high"], where + "." + role + ".high")
            if low > high:
                raise ValueError(where + "." + role + ": low exceeds high")
        if ident in unique:
            if row != unique[ident]:
                raise ValueError("conflicting work package ID")
            continue
        unique[ident] = row
    member_sets = {tier: {ident for ident, row in unique.items()
                          if tier in row["membership"]} for tier in BRANCHES}
    m, a, b, fa, fb = (member_sets[t] for t in BRANCHES)
    if not m or not (m <= a and m <= b and m <= fa and m <= fb and
                    a <= b and a <= fa and b <= fb and fa <= fb and
                    b - a == fb - fa and fa - a == fb - b and
                    not ((b - a) & (fa - a))):
        raise ValueError("membership: inconsistent MVP/StandardA/StandardB/FullA/FullB")
    output_rows = []
    for row in unique.values():
        totals = {side: sum((number(row["roles"][r][side], r + side) for r in ROLES), ZERO)
                  for side in ("low", "high")}
        output_rows.append({"id": row["id"], "function": row["function"],
                            "source": row["source"], "scope_version": version,
                            "membership": row["membership"], "roles": row["roles"],
                            "row": {s: fmt(v) for s, v in totals.items()}})
    results = {}
    for tier in BRANCHES:
        included = [r for r in output_rows if r["id"] in member_sets[tier]]
        roles = {role: {s: sum((number(r["roles"][role][s], role + s)
                                 for r in included), ZERO) for s in ("low", "high")}
                 for role in ROLES}
        base = {s: sum((number(r["row"][s], s) for r in included), ZERO)
                for s in ("low", "high")}
        for side in ("low", "high"):
            if sum((roles[r][side] for r in ROLES), ZERO) != base[side]:
                raise ValueError("role/row reconciliation failed")
        risk = {s: base[s] * rates[s] for s in ("low", "high")}
        effort = {s: base[s] + risk[s] for s in ("low", "high")}
        parent = PARENTS[tier]
        delta_ids = member_sets[tier] - member_sets[parent] if parent else member_sets[tier]
        if mode == "refused":
            cost = None
        else:
            prices = {"low": unit, "high": unit} if mode == "fixed" else {
                "low": Decimal("1000"), "high": Decimal("1500")}
            cost = {s: fmt(effort[s] * prices[s]) for s in ("low", "high")}
        results[tier] = {"ids": [r["id"] for r in included], "parent": parent,
                         "delta_ids": [r["id"] for r in output_rows if r["id"] in delta_ids],
                         "delta_roles": {r: {s: fmt(roles[r][s] -
                                  (number(results[parent]["roles"][r][s], s) if parent else ZERO))
                                               for s in ("low", "high")} for r in ROLES},
                         "roles": {r: {s: fmt(v) for s, v in sides.items()}
                                   for r, sides in roles.items()},
                         "B": {s: fmt(v) for s, v in base.items()},
                         "R": {s: fmt(v) for s, v in risk.items()},
                         "E": {s: fmt(v) for s, v in effort.items()},
                         "labor_rmb": cost, "complete_project_total_rmb": None,
                         "condition": "ASSUMED_CONDITIONAL" if tier in ("StandardB", "FullB")
                         and b - a else "SOURCE_AS_DECLARED_NOT_VERIFIED"}
    reported = data.get("reported", {})
    if not isinstance(reported, dict) or set(reported) - set(BRANCHES):
        raise ValueError("reported: invalid tiers")
    for tier, claims in reported.items():
        fields(claims, ("roles", "B"), where="reported." + tier)
        fields(claims["roles"], ROLES, where="reported." + tier + ".roles")
        fields(claims["B"], ("low", "high"), where="reported." + tier + ".B")
        for side in ("low", "high"):
            value = number(claims["B"][side], "reported.B." + side)
            claimed = ZERO
            for role in ROLES:
                fields(claims["roles"][role], ("low", "high"), where="reported.roles." + role)
                role_value = number(claims["roles"][role][side], "reported.roles." + role + side)
                claimed += role_value
                if role_value != number(results[tier]["roles"][role][side], side):
                    raise ValueError(f"{tier} {role} {side}: reported mismatch")
            if value != claimed or value != number(results[tier]["B"][side], side):
                raise ValueError(f"{tier} {side}: reported role/row/B mismatch")
    return {"scope_version": version, "previous_scope_version": previous,
            "scope_changed": changed, "rows": output_rows, "tiers": results,
            "pricing_mode": mode, "outside_fees": "UNKNOWN; inquire separately",
            "labor_is_complete_total": False, "unit_effort": "person-days",
            "currency_labor_only": "RMB" if mode != "refused" else None,
            "reference_notice": "人民币 1000～1500 元/人天为用户批准的示意估算参数，并非实时市场行情或正式合同报价。"
            if mode == "reference" else None}


def estimate(data):
    if isinstance(data, dict) and isinstance(data.get("work_packages"), list) and any(
            isinstance(row, dict) and "membership" in row for row in data["work_packages"]):
        return estimate_branches(data)
    fields(data, ("scope_version", "work_packages", "buffers", "pricing", "outside_fees"),
           ("previous_scope_version", "scope_changed", "reported", "label"))
    version = text(data["scope_version"], "scope_version")
    changed = data.get("scope_changed", False)
    if not isinstance(changed, bool):
        raise ValueError("scope_changed: boolean required")
    previous = data.get("previous_scope_version")
    if changed != (previous is not None):
        raise ValueError("scope change requires previous_scope_version and scope_changed=true")
    if previous is not None and (text(previous, "previous_scope_version") == version):
        raise ValueError("scope change requires a new version")
    fields(data["buffers"], ("low", "high", "source"), where="buffers")
    rates = {side: number(data["buffers"][side], f"buffers.{side}", maximum=Decimal("1"))
             for side in ("low", "high")}
    text(data["buffers"]["source"], "buffers.source")
    fields(data["pricing"], ("mode",), ("unit_price", "source"), "pricing")
    pricing = data["pricing"]
    mode = pricing["mode"]
    if mode not in ("fixed", "reference", "refused"):
        raise ValueError("pricing.mode: fixed/reference/refused required")
    unit = ZERO
    if mode == "fixed":
        if set(pricing) != {"mode", "unit_price", "source"}:
            raise ValueError("fixed price needs unit_price and source")
        unit = number(pricing["unit_price"], "pricing.unit_price")
        text(pricing["source"], "pricing.source")
    elif set(pricing) != {"mode"}:
        raise ValueError("reference/refused cannot supply a price")
    fields(data["outside_fees"], ("status",), where="outside_fees")
    if data["outside_fees"]["status"] != "unknown":
        raise ValueError("outside fees: only explicit unknown supported by this POC")
    rows = data["work_packages"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("work_packages: nonempty array required")
    unique = {}
    for index, row in enumerate(rows):
        where = f"work_packages[{index}]"
        fields(row, ("id", "function", "source", "tier", "new", "roles", "scope_version"), where=where)
        ident = text(row["id"], where + ".id")
        text(row["function"], where + ".function")
        text(row["source"], where + ".source")
        if row["scope_version"] != version:
            raise ValueError(where + ": scope version mismatch; change requires new snapshot")
        if row["tier"] not in TIERS or not isinstance(row["new"], bool):
            raise ValueError(where + ": invalid tier/new")
        fields(row["roles"], ROLES, where=where + ".roles")
        for role in ROLES:
            fields(row["roles"][role], ("low", "high"), where=f"{where}.roles.{role}")
            low = number(row["roles"][role]["low"], f"{where}.{role}.low")
            high = number(row["roles"][role]["high"], f"{where}.{role}.high")
            if low > high:
                raise ValueError(f"{where}.{role}: low exceeds high")
        if ident in unique:
            if row != unique[ident]:
                raise ValueError(f"conflicting work package ID: {ident}")
            continue
        unique[ident] = row
    output_rows = []
    for row in unique.values():
        role_values = {role: {side: number(row["roles"][role][side], role + side)
                              for side in ("low", "high")} for role in ROLES}
        totals = {side: sum((role_values[role][side] for role in ROLES), ZERO)
                  for side in ("low", "high")}
        output_rows.append({"id": row["id"], "tier": row["tier"], "new": row["new"],
                            "function": row["function"], "source": row["source"],
                            "roles": row["roles"], "row": {s: fmt(v) for s, v in totals.items()}})
    results = {}
    previous_roles = {role: {s: ZERO for s in ("low", "high")} for role in ROLES}
    for tier in TIERS:
        included = [r for r in output_rows if TIERS.index(r["tier"]) <= TIERS.index(tier)]
        role_totals = {role: {s: sum((number(r["roles"][role][s], s) for r in included), ZERO)
                              for s in ("low", "high")} for role in ROLES}
        base = {s: sum((number(r["row"][s], s) for r in included), ZERO) for s in ("low", "high")}
        for side in ("low", "high"):
            if sum((role_totals[role][side] for role in ROLES), ZERO) != base[side]:
                raise ValueError("role/row reconciliation failed")
        risk = {s: base[s] * rates[s] for s in ("low", "high")}
        effort = {s: base[s] + risk[s] for s in ("low", "high")}
        delta = {role: {s: role_totals[role][s] - previous_roles[role][s]
                        for s in ("low", "high")} for role in ROLES}
        if mode == "refused":
            cost = None
        else:
            prices = {"low": unit, "high": unit} if mode == "fixed" else {
                "low": Decimal("1000"), "high": Decimal("1500")}
            cost = {s: fmt(effort[s] * prices[s]) for s in ("low", "high")}
        results[tier] = {"ids": [r["id"] for r in included],
                         "roles": {role: {s: fmt(v) for s, v in sides.items()}
                                   for role, sides in role_totals.items()},
                         "delta_roles": {role: {s: fmt(v) for s, v in sides.items()}
                                         for role, sides in delta.items()},
                         "B": {s: fmt(v) for s, v in base.items()},
                         "R": {s: fmt(v) for s, v in risk.items()},
                         "E": {s: fmt(v) for s, v in effort.items()},
                         "labor_rmb": cost, "complete_project_total_rmb": None}
        previous_roles = role_totals
    reported = data.get("reported", {})
    if not isinstance(reported, dict) or set(reported) - set(TIERS):
        raise ValueError("reported: invalid tiers")
    for tier, claims in reported.items():
        fields(claims, ("roles", "B"), where="reported." + tier)
        fields(claims["roles"], ROLES, where="reported." + tier + ".roles")
        fields(claims["B"], ("low", "high"), where="reported." + tier + ".B")
        for side in ("low", "high"):
            claimed_base = number(claims["B"][side], "reported.B." + side)
            claimed_roles = ZERO
            for role in ROLES:
                fields(claims["roles"][role], ("low", "high"), where="reported.roles." + role)
                value = number(claims["roles"][role][side], "reported.roles." + role + side)
                claimed_roles += value
                actual = number(results[tier]["roles"][role][side], "calculated.role")
                if value != actual:
                    raise ValueError(f"{tier} {role} {side}: reported {value} != calculated {actual}")
            if claimed_base != number(results[tier]["B"][side], "calculated.B") or claimed_roles != claimed_base:
                raise ValueError(f"{tier} {side}: reported role/row/B mismatch")
    return {"scope_version": version, "previous_scope_version": previous, "scope_changed": changed,
            "rows": output_rows, "tiers": results, "pricing_mode": mode,
            "outside_fees": "UNKNOWN; inquire separately", "labor_is_complete_total": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if (".." in args.input.parts or ".." in args.output.parts or
                any(p.is_symlink() for path in (args.input, args.output)
                    for p in (path, *path.parents)) or not args.input.is_file()):
            raise ValueError("input/output: symbolic link or missing input refused")
        if args.input.resolve() == args.output.resolve() or not args.output.parent.is_dir():
            raise ValueError("output: input overwrite or missing output directory refused")
        input_bytes = args.input.read_bytes()
        data = json.loads(input_bytes.decode("utf-8"), parse_float=Decimal,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        result = estimate(data)
        result["input_sha256"] = hashlib.sha256(input_bytes).hexdigest()
        result["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        # Exclusive create: never truncate input, old results, or evidence. Remove only
        # an incomplete file created by this invocation if writing fails.
        descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        except (OSError, ValueError):
            args.output.unlink()
            raise
    except (OSError, ValueError, json.JSONDecodeError, UnicodeError) as exc:
        # No user text or raw paths in stderr: errors name only validated fields.
        detail = str(exc) if isinstance(exc, ValueError) and not isinstance(exc, json.JSONDecodeError) else "invalid JSON or inaccessible file"
        print(f"INPUT_ERROR: {detail}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
