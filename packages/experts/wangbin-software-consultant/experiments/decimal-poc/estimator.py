"""Standalone, structured-input Decimal effort oracle; not wired into the Expert."""
import argparse
from decimal import Decimal, InvalidOperation
import json
import sys
from pathlib import Path

TIERS = ("MVP", "Standard", "FullA", "FullB")
ROLES = ("FE", "BE", "DB", "QA")
ZERO = Decimal("0")


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


def estimate(data):
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
        with args.input.open(encoding="utf-8") as stream:
            data = json.load(stream, parse_float=Decimal,
                             parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
        result = estimate(data)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"INPUT_ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
