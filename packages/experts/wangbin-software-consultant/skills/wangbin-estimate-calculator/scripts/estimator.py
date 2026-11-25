"""Versioned, structured-input Decimal calculator bundled with the Expert."""
import argparse
from decimal import Decimal, InvalidOperation, localcontext, Inexact, Rounded, DecimalException
from functools import wraps
import hashlib
import json
import os
import re
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



def exact_arithmetic(function):
    """Size context from decimal operands; never return a rounded success receipt."""
    @wraps(function)
    def wrapped(data):
        def budget(value):
            if isinstance(value, dict):
                return sum(budget(v) for v in value.values())
            if isinstance(value, list):
                return sum(budget(v) for v in value)
            if isinstance(value, (str, Decimal)):
                try:
                    number = Decimal(value)
                except InvalidOperation:
                    return 0
                if number.is_finite():
                    parts = number.as_tuple()
                    return len(parts.digits) + abs(parts.exponent) + 1
            return 0
        precision = max(28, 3 * budget(data) + 32)
        if precision > 100000:
            raise ValueError("input: exact arithmetic precision budget exceeded")
        with localcontext() as context:
            context.prec = precision
            context.traps[Inexact] = True
            context.traps[Rounded] = True
            try:
                return function(data)
            except DecimalException as exc:
                raise ValueError("input: cannot compute exactly within arithmetic limits") from exc
    return wrapped

def fixed_price_source(value):
    """Reject an explicitly unresolved source; do not authenticate free text."""
    source = text(value, "pricing.source")
    state = " ".join(source.strip().casefold().split()).rstrip(".。!！")
    if (
        re.fullmatch(
            r"(?:(?:(?:fixed )?(?:price|pricing|unit price|rate)(?: source| basis)?)(?: is|:)?\s*)?"
            r"(?:unknown|unconfirmed|not(?: yet)? confirmed|pending|tbd|not approved)",
            state,
        )
        or re.fullmatch(
            r"(?:(?:固定单价|人天单价|单价|价格|报价)(?:来源|依据)?(?:为|是|[:：])?\s*)?"
            r"(?:未知|尚未确认|未确认|待确认|未批准|未获批准|待批准|未获授权)",
            state,
        )
    ):
        raise ValueError("pricing.source: fixed price requires a user-supplied price source")
    return source


@exact_arithmetic
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
    buffer_source = text(data["buffers"]["source"], "buffers.source")
    # Match a whole missing-basis statement, never a token in a material name.
    buffer_state = " ".join(buffer_source.strip().casefold().split()).rstrip(".。!！")
    if (re.fullmatch(r"(?:(?:buffer(?: source| basis)?)(?: is|:)?\s*)?"
                     r"(?:unknown|unconfirmed|not(?: yet)? confirmed|pending|tbd)", buffer_state) or
            re.fullmatch(r"(?:(?:缓冲来源|缓冲依据|缓冲)(?:为|是|[:：])?)?"
                         r"(?:未知|尚未确认|待确认|未确认)", buffer_state)):
        raise ValueError("buffers.source: confirmed or explicit assumed basis required")
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
        fixed_price_source(price["source"])
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
        if not (re.search(r"\b(?:ASSUMED(?:_CONDITIONAL)?|SYNTHETIC)\b", source) or
                re.search(r"\bturn\s+[1-9][0-9]*\b", source) or
                re.search(r"(?:第\s*[1-9][0-9]*\s*(?:个)?(?:话轮|轮)|话轮\s*[1-9][0-9]*)(?![0-9])", source) or
                re.search(r'[^\s\\/:*?"<>|]+\s+line\s+[1-9][0-9]*\b', source) or
                (re.fullmatch(r'[^\\/:*?"<>|\x00-\x1f]+:[1-9][0-9]*', source) and
                 source.rsplit(":", 1)[0] == source.rsplit(":", 1)[0].strip() and
                 source.rsplit(":", 1)[0] not in (".", ".."))):
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


# Schema 2.0 is deliberately independent of both unversioned input contracts.
SCENARIOS = ("low", "base", "high")
KNOWN = ("CONFIRMED", "ASSUMED", "ASSUMED_CONDITIONAL", "SYNTHETIC")
COVERAGE = ("COMPLETE", "PARTIAL", "NOT_APPLICABLE")
MEMBERSHIPS = (frozenset(BRANCHES), frozenset(BRANCHES[1:]),
               frozenset(("StandardB", "FullB")), frozenset(("FullA", "FullB")))
DELTA_PAIRS = (("MVP", "StandardA"), ("StandardA", "StandardB"),
               ("StandardA", "FullA"), ("FullA", "FullB"), ("StandardB", "FullB"))
REFERENCE_NOTICE = "人民币 1000～1500 元/人天为用户批准的示意估算参数，并非实时市场行情或正式合同报价。"


def v2_fields(value, required, optional=(), where="input"):
    # Do not include caller-controlled object keys or values in errors.
    if not isinstance(value, dict) or not set(required) <= value.keys() or value.keys() - set(required) - set(optional):
        raise ValueError(where + ": invalid object fields")


def v2_choice(value, allowed, where):
    if not isinstance(value, str) or value not in allowed:
        raise ValueError(where + ": invalid choice")
    return value


def v2_array(value, where):
    if not isinstance(value, list):
        raise ValueError(where + ": expected array")
    return value


def v2_ids(value, where, *, allowed=None, nonempty=False):
    values = v2_array(value, where)
    for ident in values:
        text(ident, where)
    if (nonempty and not values) or len(set(values)) != len(values) or (
            allowed is not None and not set(values) <= set(allowed)):
        raise ValueError(where + ": invalid, unknown or duplicate ID")
    return values


def v2_locator(source):
    if re.fullmatch(r"TURN:[1-9][0-9]*", source):
        return True
    file = re.fullmatch(r"FILE:([^:\s\x00-\x1f](?:[^:\x00-\x1f]*[^:\s\x00-\x1f])?):[1-9][0-9]*", source)
    return bool(file and file[1] not in (".", ".."))


def v2_source(value, where, *, known=True):
    source = text(value, where)
    if known:
        if v2_locator(source):
            return source
        basis = re.fullmatch(r"(?:SYNTHETIC|ASSUMED|ASSUMED_CONDITIONAL): ([^\s\x00-\x1f][^\x00-\x1f]*)", source)
        if not basis or basis[1] != basis[1].strip():
            raise ValueError(where + ": source requires a locator or explicit basis")
        try:
            fixed_price_source(basis[1])
        except ValueError:
            raise ValueError(where + ": unresolved source") from None
        state = " ".join(basis[1].casefold().split()).rstrip(".。!！")
        # Reject standalone contract states and slash-separated state lists, not prose.
        state_tokens = tuple(re.sub(r"[\s_-]+", "_", part.strip()).upper()
                             for part in state.split("/"))
        contract_states = KNOWN + COVERAGE + ("UNKNOWN", "PENDING_CONFIRMATION", "CONDITIONAL",
            "SUPERSEDED", "NOT_DESIGNED_YET", "NEEDS_CONFIRMATION", "UNMAPPED",
            "TO_BE_QUOTED", "QUOTED", "BUDGETED", "ESTIMATED", "INPUT_INCOMPLETE",
            "BLOCKED", "NOT_REQUESTED", "RETAINED", "SPLIT", "MERGED", "REPLACED",
            "CANCELLED", "ADD", "REMOVE", "RETAIN", "MODIFY", "SHARED")
        if (not any(ch.isalpha() for ch in state) or
                all(token in contract_states for token in state_tokens) or
                state in ("confirmed", "not_applicable", "n/a", "none", "null", "synthetic", "assumed",
                      "assumed_conditional", "已确认", "不适用", "无", "待定", "未授权", "未获许可",
                      "待业务确认", "需业务确认", "尚待确认", "待询价", "待核", "已报价", "已批准", "已估算") or
                re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:e[+-]?[0-9]+)?", state) or
                re.fullmatch(r"(?:(?:effort|buffer|fee|amount|quantity|unit price|period count|permission|source|basis)"
                             r"(?: source| basis)?(?: is|:)?\s*)?(?:unknown|unconfirmed|pending|tbd|unapproved|"
                             r"not(?: yet)? (?:confirmed|approved|authorized|permitted))", state) or
                re.fullmatch(r"(?:(?:人天|工作量|缓冲|费用|金额|数量|期数|许可|授权|来源|依据)(?:来源|依据)?"
                             r"(?:为|是|[:：])?\s*)?(?:未知|尚未确认|待确认|未确认|未批准|未获批准|待批准|未获授权|未授权|未获许可)", state) or
                re.fullmatch(r"(?:not (?:yet )?(?:authorized|permitted|approved|granted)|unauthorized|unapproved|"
                             r"(?:permission|authorization|approval) (?:is |was )?(?:denied|refused|pending|not granted)|"
                             r"no (?:permission|authorization|approval)|未获(?:授权|许可|批准)|未(?:授权|许可|批准)|拒绝(?:授权|许可|批准|补价))", state)):
            raise ValueError(where + ": source requires a locator or explicit basis")
    return source


def v2_number(value, where, maximum=None):
    if not isinstance(value, str) or not re.fullmatch(
            r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", value):
        raise ValueError(where + ": expected decimal string")
    return number(value, where, maximum=maximum)


def v2_atom(atom, where, maximum=None):
    v2_fields(atom, ("status", "source"), ("value",), where)
    state = v2_choice(atom["status"], KNOWN + ("UNKNOWN", "NOT_APPLICABLE"), where + ".status")
    v2_source(atom["source"], where + ".source", known=state != "UNKNOWN")
    if state in KNOWN:
        v2_number(atom.get("value"), where + ".value", maximum)
    elif atom.get("value") is not None:
        raise ValueError(where + ": unknown/inapplicable value must be absent or null")
    return atom


def v2_series(series, where, maximum=None):
    v2_fields(series, ("low", "high"), ("base",), where)
    for side, atom in series.items():
        v2_atom(atom, where + "." + side, maximum)
    states = {a["status"] for a in series.values()}
    if "NOT_APPLICABLE" in states and states != {"NOT_APPLICABLE"}:
        raise ValueError(where + ": inconsistent applicability")
    known = [Decimal(series[s]["value"]) for s in SCENARIOS
             if s in series and series[s]["status"] in KNOWN]
    if known != sorted(known):
        raise ValueError(where + ": unordered scenario values")
    return series


def v2_na(series):
    return series["low"]["status"] == "NOT_APPLICABLE"


def v2_at(series, side):
    if side in series:
        return series[side]
    if v2_na(series):
        return series["low"]
    return {"status": "UNKNOWN", "source": "independent base not supplied"}


def v2_rate(rate, where, *, fallback=False):
    if not isinstance(rate, dict):
        raise ValueError(where + ": expected rate object")
    kind = v2_choice(rate.get("kind"), ("fixed", "reference") if fallback else ("fixed", "range"), where + ".kind")
    if kind == "fixed":
        v2_fields(rate, ("kind", "value"), where=where)
        v2_atom(rate["value"], where + ".value")
    elif kind == "range":
        v2_fields(rate, ("kind", "values"), where=where)
        v2_series(rate["values"], where + ".values")
    else:
        v2_fields(rate, ("kind",), ("base",), where)
        if "base" in rate:
            v2_atom(rate["base"], where + ".base")
            if rate["base"]["status"] == "NOT_APPLICABLE" or (
                    rate["base"]["status"] in KNOWN and not
                    Decimal("1000") <= Decimal(rate["base"]["value"]) <= Decimal("1500")):
                raise ValueError(where + ": incompatible reference base")
    return rate


def v2_pricing(pricing, roles):
    if not isinstance(pricing, dict):
        raise ValueError("pricing: expected object")
    mode = v2_choice(pricing.get("mode"), ("refused", "reference", "fixed", "role", "mixed"), "pricing.mode")
    required, optional = {
        "refused": ((), ()), "reference": ((), ("base",)), "fixed": (("rate",), ()),
        "role": (("rates",), ()),
        "mixed": (("rates", "fallback", "fallback_roles", "permission_source"), ()),
    }[mode]
    v2_fields(pricing, ("mode", "tax_basis", *required), optional, "pricing")
    v2_choice(pricing["tax_basis"], ("INCLUDED", "EXCLUDED", "UNKNOWN"), "pricing.tax_basis")
    if mode == "reference":
        v2_rate({"kind": "reference", **({"base": pricing["base"]} if "base" in pricing else {})}, "pricing", fallback=True)
    elif mode == "fixed":
        v2_atom(pricing["rate"], "pricing.rate")
    elif mode in ("role", "mixed"):
        rates = pricing["rates"]
        if not isinstance(rates, dict) or rates.keys() - roles.keys():
            raise ValueError("pricing.rates: unknown role or invalid object")
        for rate in rates.values():
            v2_rate(rate, "pricing.rates.entry")
        if mode == "mixed":
            fallback_roles = v2_ids(pricing["fallback_roles"], "pricing.fallback_roles", allowed=roles, nonempty=True)
            if set(fallback_roles) & rates.keys():
                raise ValueError("pricing: explicit and fallback roles overlap")
            permission = text(pricing["permission_source"], "pricing.permission_source")
            if not permission.startswith("AUTHORIZED: ") or not v2_locator(permission[len("AUTHORIZED: "):]):
                raise ValueError("pricing.permission_source: explicit authorization locator required")
            v2_rate(pricing["fallback"], "pricing.fallback", fallback=True)


def v2_price(pricing, role, side):
    """Select only an authorized role price; retain the actual atom and permission."""
    mode = pricing["mode"]
    permission = None
    if mode == "refused":
        return {"status": "UNKNOWN", "source": "labor pricing refused"}, False, permission, False
    if mode == "fixed":
        rate = {"kind": "fixed", "value": pricing["rate"]}
    elif mode == "reference":
        rate = {"kind": "reference", **({"base": pricing["base"]} if "base" in pricing else {})}
    elif role in pricing["rates"]:
        rate = pricing["rates"][role]
    elif mode == "mixed" and role in pricing["fallback_roles"]:
        rate = pricing["fallback"]
        permission = pricing["permission_source"]
    else:
        return {"status": "UNKNOWN", "source": "no authorized role price"}, False, permission, False
    if rate["kind"] == "fixed":
        return rate["value"], False, permission, False
    if rate["kind"] == "range":
        return v2_at(rate["values"], side), False, permission, "base" in rate["values"]
    if side == "base":
        return rate.get("base", {"status": "UNKNOWN", "source": "independent reference base not supplied"}), False, permission, "base" in rate
    return {"status": "ASSUMED", "source": "R5 reference price", "value": "1000" if side == "low" else "1500"}, True, permission, "base" in rate


def v2_insert(unique, row, where):
    ident = row["id"]
    if ident in unique and unique[ident] != row:
        raise ValueError(where + ": conflicting ID")
    unique.setdefault(ident, row)


def v2_fee(row, version, targets, packages, scoped):
    where = "fees.entry"
    v2_fields(row, ("id", "account_id", "description", "source", "scope_version", "targets",
                   "work_package_ids", "interface_only", "category", "period", "currency",
                   "tax_basis", "cost_state", "disposition", "calculation"), ("period_count",), where)
    for key in ("id", "account_id", "description"):
        text(row[key], where + "." + key)
    v2_source(row["source"], where + ".source")
    if row["scope_version"] != version or not isinstance(row["interface_only"], bool):
        raise ValueError(where + ": scope version or interface flag invalid")
    linked = v2_ids(row["work_package_ids"], where + ".work_package_ids", allowed=packages)
    for target in v2_ids(row["targets"], where + ".targets", allowed=targets, nonempty=True):
        if not set(linked) <= set(targets[target]):
            raise ValueError(where + ": linked work not in fee target")
        if not scoped and (row["interface_only"] or any(frozenset(packages[p]["membership"]) == MEMBERSHIPS[2] for p in linked)) and target not in ("StandardB", "FullB"):
            raise ValueError(where + ": interface-only fee outside B tier")
    category = v2_choice(row["category"], ("third_party", "deployment", "service", "maintenance", "tax"), where + ".category")
    period = v2_choice(row["period"], ("once", "month", "year"), where + ".period")
    if category == "deployment" and period != "once":
        raise ValueError(where + ": deployment must be one-time")
    if not isinstance(row["currency"], str) or not re.fullmatch(r"[A-Z]{3}", row["currency"]):
        raise ValueError(where + ": invalid currency code")
    tax = v2_choice(row["tax_basis"], ("INCLUDED", "EXCLUDED", "UNKNOWN", "SEPARATE"), where + ".tax_basis")
    if (category == "tax") != (tax == "SEPARATE"):
        raise ValueError(where + ": inconsistent separate tax")
    v2_choice(row["cost_state"], ("PLANNED", "INCURRED", "COMMITTED", "UNKNOWN"), where + ".cost_state")
    disposition = v2_choice(row["disposition"], ("quote", "included_in_labor", "excluded"), where + ".disposition")
    if disposition == "included_in_labor" and not linked:
        raise ValueError(where + ": included fee requires work link")
    calc = row["calculation"]
    if not isinstance(calc, dict):
        raise ValueError(where + ".calculation: expected object")
    mode = v2_choice(calc.get("mode"), ("amount", "quantity_price"), where + ".calculation.mode")
    if mode == "amount":
        v2_fields(calc, ("mode", "amount"), where=where + ".calculation")
        v2_series(calc["amount"], where + ".calculation.amount")
    else:
        v2_fields(calc, ("mode", "quantity", "unit_price", "unit"), where=where + ".calculation")
        text(calc["unit"], where + ".calculation.unit")
        v2_series(calc["quantity"], where + ".calculation.quantity")
        v2_series(calc["unit_price"], where + ".calculation.unit_price")
        if v2_na(calc["quantity"]) != v2_na(calc["unit_price"]):
            raise ValueError(where + ": inconsistent fee applicability")
    if "period_count" in row:
        if period == "once":
            raise ValueError(where + ": period_count requires recurring fee")
        v2_series(row["period_count"], where + ".period_count")
    return row


def v2_fee_na(row):
    calc = row["calculation"]
    return v2_na(calc["amount"] if calc["mode"] == "amount" else calc["quantity"])


def v2_normalize(data):
    v2_fields(data, ("schema_version", "scope_version", "quote_version", "request", "role_catalog",
                     "work_packages", "coverage", "buffers", "pricing", "fees"),
              ("previous_scope_version", "scope_changed", "reported"))
    version = text(data["scope_version"], "scope_version")
    text(data["quote_version"], "quote_version")
    changed, previous = data.get("scope_changed", False), data.get("previous_scope_version")
    if not isinstance(changed, bool) or changed != (previous is not None) or (
            previous is not None and text(previous, "previous_scope_version") == version):
        raise ValueError("scope change: invalid version pair")
    request = data["request"]
    if not isinstance(request, dict):
        raise ValueError("request: expected object")
    mode = v2_choice(request.get("mode"), ("full", "tiers", "scope"), "request.mode")
    required = {"full": (), "tiers": ("tiers",), "scope": ("scope_id", "package_ids")}[mode]
    v2_fields(request, ("mode", "money", *required), ("role_ids",) if mode == "scope" else (), "request")
    v2_choice(request["money"], ("none", "labor", "external", "all"), "request.money")
    if mode == "scope":
        scope = text(request["scope_id"], "request.scope_id")
        if scope in BRANCHES:
            raise ValueError("request.scope_id: reserved tier name")
        keys = [scope]
    else:
        keys = list(BRANCHES) if mode == "full" else v2_ids(request["tiers"], "request.tiers", allowed=BRANCHES, nonempty=True)
    roles, names = {}, set()
    for row in v2_array(data["role_catalog"], "role_catalog"):
        v2_fields(row, ("id", "name"), where="role_catalog.entry")
        ident = text(row["id"], "role_catalog.id")
        name = text(row["name"], "role_catalog.name").strip().casefold()
        if ident in roles or name in names:
            raise ValueError("role_catalog: duplicate role ID or name")
        roles[ident] = row
        names.add(name)
    selected_roles = set(v2_ids(request["role_ids"], "request.role_ids", allowed=roles, nonempty=True)) if "role_ids" in request else set(roles)
    packages, assignment_owner = {}, {}
    for row in v2_array(data["work_packages"], "work_packages"):
        v2_fields(row, ("id", "function", "source", "scope_version", "assignments_complete", "assignments") +
                  (() if mode == "scope" else ("membership",)), ("membership",) if mode == "scope" else (), "work_packages.entry")
        ident = text(row["id"], "work_packages.id")
        text(row["function"], "work_packages.function")
        v2_source(row["source"], "work_packages.source")
        if row["scope_version"] != version or not isinstance(row["assignments_complete"], bool):
            raise ValueError("work_packages: invalid scope version or completeness flag")
        if "membership" in row and frozenset(v2_ids(row["membership"], "work_packages.membership", allowed=BRANCHES, nonempty=True)) not in MEMBERSHIPS:
            raise ValueError("work_packages.membership: invalid member set")
        assignments = {}
        for assignment in v2_array(row["assignments"], "work_packages.assignments"):
            v2_fields(assignment, ("id", "role", "effort"), where="work_packages.assignments.entry")
            task = text(assignment["id"], "work_packages.assignments.id")
            v2_choice(assignment["role"], roles, "work_packages.assignments.role")
            v2_series(assignment["effort"], "work_packages.assignments.effort")
            if task in assignment_owner and assignment_owner[task] != ident:
                raise ValueError("work_packages.assignments: task shared across packages")
            assignment_owner[task] = ident
            v2_insert(assignments, assignment, "work_packages.assignments")
        # Compare original duplicate packages before discarding repeated tasks.
        v2_insert(packages, row, "work_packages")
    packages = {ident: {**row, "assignments": list({a["id"]: a for a in row["assignments"]}.values())}
                for ident, row in packages.items()}
    targets = ({keys[0]: v2_ids(request["package_ids"], "request.package_ids", allowed=packages)} if mode == "scope" else
               {key: [p for p, row in packages.items() if key in row["membership"]] for key in keys})
    coverage = data["coverage"]
    if not isinstance(coverage, dict) or coverage.keys() != targets.keys():
        raise ValueError("coverage: must match requested targets")
    for key, state in coverage.items():
        v2_fields(state, ("work", "external", "source"), where="coverage.entry")
        v2_choice(state["work"], COVERAGE, "coverage.work")
        v2_choice(state["external"], COVERAGE, "coverage.external")
        v2_source(state["source"], "coverage.source", known=state["work"] != "PARTIAL" or state["external"] != "PARTIAL")
        if state["work"] == "NOT_APPLICABLE" and any(
                not packages[p]["assignments_complete"] or any(a["role"] in selected_roles and not v2_na(a["effort"])
                for a in packages[p]["assignments"]) for p in targets[key]):
            raise ValueError("coverage.work: inapplicability conflicts with work")
        if state["work"] == "COMPLETE" and not any(
                a["role"] in selected_roles and not v2_na(a["effort"])
                for p in targets[key] for a in packages[p]["assignments"]):
            raise ValueError("coverage.work: no applicable assignments requires explicit inapplicability or partial coverage")
    if mode == "full" and any(state["work"] == "COMPLETE" for state in coverage.values()) and not targets["MVP"] and any(
            not v2_na(a["effort"]) for row in packages.values() for a in row["assignments"]):
        raise ValueError("work_packages: complete full development requires base membership")
    buffers = data["buffers"]
    v2_fields(buffers, ("default",), ("overrides",) if mode != "scope" else (), "buffers")
    v2_series(buffers["default"], "buffers.default", Decimal("1"))
    overrides = buffers.get("overrides", {})
    if not isinstance(overrides, dict) or overrides.keys() - targets.keys():
        raise ValueError("buffers.overrides: invalid target")
    for series in overrides.values():
        v2_series(series, "buffers.overrides.entry", Decimal("1"))
    v2_pricing(data["pricing"], roles)
    fees = {}
    for row in v2_array(data["fees"], "fees"):
        v2_fee(row, version, targets, packages, mode == "scope")
        v2_insert(fees, row, "fees")
    for key in keys:
        relevant = [f for f in fees.values() if key in f["targets"]]
        accounts = [f["account_id"] for f in relevant if f["disposition"] != "excluded"]
        if len(accounts) != len(set(accounts)):
            raise ValueError("fees: duplicate active account for target")
        quoted = [f for f in relevant if f["disposition"] == "quote"]
        if coverage[key]["external"] == "NOT_APPLICABLE" and any(not v2_fee_na(f) for f in quoted):
            raise ValueError("coverage.external: conflicts with applicable quoted fees")
        if coverage[key]["external"] == "COMPLETE" and not any(not v2_fee_na(f) for f in quoted):
            raise ValueError("coverage.external: no independent fees requires explicit inapplicability")
    return roles, selected_roles, packages, targets, fees


def v2_metric(status, value=None, subtotal=None, missing=()):
    return {"status": status, "value": fmt(value) if value is not None else None,
            "known_subtotal": fmt(subtotal) if subtotal is not None else None,
            "missing": list(dict.fromkeys(missing))}


def v2_complete(value):
    return v2_metric("COMPLETE", value, value)


def v2_atom_metric(atom, missing):
    if atom["status"] in KNOWN:
        return v2_complete(Decimal(atom["value"]))
    if atom["status"] == "NOT_APPLICABLE":
        return v2_metric("NOT_APPLICABLE")
    return v2_metric("BLOCKED", missing=[missing])


def v2_sum(metrics, gaps=()):
    """Sum only actual contributions; incomplete empty inputs never become zero."""
    missing = list(gaps)
    values = []
    for metric in metrics:
        if metric["known_subtotal"] is not None:
            values.append(Decimal(metric["known_subtotal"]))
        missing.extend(metric["missing"])
        if metric["status"] in ("BLOCKED", "PARTIAL") and not metric["missing"]:
            missing.append("incomplete contribution")
    if missing:
        return v2_metric("PARTIAL", subtotal=sum(values, ZERO), missing=missing) if values else v2_metric("BLOCKED", missing=missing)
    if values:
        return v2_complete(sum(values, ZERO))
    return v2_metric("NOT_APPLICABLE")


def v2_product(metric, atom, missing):
    if metric["status"] in ("NOT_APPLICABLE", "NOT_REQUESTED"):
        return metric.copy()
    if atom["status"] not in KNOWN or metric["known_subtotal"] is None:
        gaps = metric["missing"] + ([missing] if atom["status"] not in KNOWN else [])
        return v2_metric("BLOCKED", missing=gaps)
    result = Decimal(metric["known_subtotal"]) * Decimal(atom["value"])
    if metric["status"] == "COMPLETE":
        return v2_complete(result)
    return v2_metric("PARTIAL", subtotal=result, missing=metric["missing"])


def v2_task(assignment, buffers, pricing, labor_allowed):
    result = {**assignment, "B": {}, "R": {}, "E": {}, "labor": {}}
    used_reference = False
    base_metrics = set()
    applicable = not v2_na(assignment["effort"])
    if applicable and "base" in assignment["effort"]:
        base_metrics.update(("B", "R", "E"))
    if applicable and "base" in buffers:
        base_metrics.update(("R", "E"))
    if labor_allowed:
        result["prices"] = {}
    for side in SCENARIOS:
        prefix = "task:" + assignment["id"] + ":" + side
        base = v2_atom_metric(v2_at(assignment["effort"], side), prefix + ":effort")
        buffer = v2_at(buffers, side)
        risk = v2_product(base, buffer, prefix + ":buffer")
        # E must cover the same work as R, not B alone if the buffer is missing.
        effort = v2_product(base, {"status": "CONFIRMED", "value": fmt(Decimal("1") + Decimal(buffer["value"]))}
                            if buffer["status"] in KNOWN else buffer, prefix + ":buffer")
        if labor_allowed:
            price, reference, permission, price_base = v2_price(pricing, assignment["role"], side)
            if applicable and ("E" in base_metrics or price_base):
                base_metrics.add("labor")
            cost = v2_product(effort, price, prefix + ":price")
            result["prices"][side] = {"rate": price, "permission_source": permission, "reference": reference}
            used_reference |= reference and cost["known_subtotal"] is not None
        else:
            cost = v2_metric("NOT_REQUESTED")
        for key, metric in (("B", base), ("R", risk), ("E", effort), ("labor", cost)):
            result[key][side] = metric
    return result, used_reference, base_metrics


def v2_aggregate(rows, gaps, labor_allowed):
    return {key: {side: v2_metric("NOT_REQUESTED") if key == "labor" and not labor_allowed else
                  v2_sum([row[key][side] for row in rows], gaps) for side in SCENARIOS}
            for key in ("B", "R", "E", "labor")}


def v2_status(metrics):
    metrics = [m for m in metrics if m["status"] != "NOT_REQUESTED"]
    if all(m["status"] in ("COMPLETE", "NOT_APPLICABLE") for m in metrics):
        return "COMPLETE" if any(m["status"] == "COMPLETE" for m in metrics) else "NOT_APPLICABLE"
    return "PARTIAL" if any(m["known_subtotal"] is not None for m in metrics) else "BLOCKED"


def v2_required(series, base=False):
    # Base is optional until a relevant input supplies it; other scenarios remain independent.
    return [series[side] for side in SCENARIOS if side != "base" or base]


def v2_fee_base(row):
    if row["disposition"] != "quote" or v2_fee_na(row):
        return False
    calc = row["calculation"]
    return any("base" in calc[key] for key in (("amount",) if calc["mode"] == "amount" else ("quantity", "unit_price")))


def v2_fee_row(row):
    result = {**row, "amount": {}, "term_amount": {}}
    for side in SCENARIOS:
        reason = "fee:" + row["id"] + ":" + side
        calc = row["calculation"]
        if row["disposition"] != "quote":
            amount = v2_metric("NOT_REQUESTED")
        elif calc["mode"] == "amount":
            amount = v2_atom_metric(v2_at(calc["amount"], side), reason + ":amount")
        else:
            amount = v2_product(v2_atom_metric(v2_at(calc["quantity"], side), reason + ":quantity"),
                                v2_at(calc["unit_price"], side), reason + ":unit_price")
        if row["period"] == "once" or row["disposition"] != "quote":
            term = v2_metric("NOT_REQUESTED")
        elif amount["status"] == "NOT_APPLICABLE" or ("period_count" in row and v2_na(row["period_count"])):
            term = v2_metric("NOT_APPLICABLE")
        else:
            term = v2_product(amount, v2_at(row["period_count"], side) if "period_count" in row else {"status": "UNKNOWN"}, reason + ":period_count")
        result["amount"][side], result["term_amount"][side] = amount, term
    return result


def v2_group_key(row):
    return tuple(row[k] for k in ("currency", "tax_basis", "period", "category"))


def v2_fees(fees, coverage, allowed):
    if not allowed:
        return {"status": "NOT_REQUESTED", "rows": [], "groups": [], "missing": []}, []
    rows = [v2_fee_row(row) for row in fees]
    quoted = [row for row in rows if row["disposition"] == "quote"]
    buckets = {}
    for row in quoted:
        buckets.setdefault(v2_group_key(row), []).append(row)
    gaps = ["external coverage incomplete"] if coverage == "PARTIAL" else []
    groups = []
    for key, members in buckets.items():
        group = dict(zip(("currency", "tax_basis", "period", "category"), key))
        group["fee_ids"] = [row["id"] for row in members]
        group["amount"] = {side: v2_sum([row["amount"][side] for row in members], gaps) for side in SCENARIOS}
        group["term_amount"] = {side: v2_metric("NOT_REQUESTED") if key[2] == "once" else
                                v2_sum([row["term_amount"][side] for row in members], gaps) for side in SCENARIOS}
        if key[2] != "once":
            group["term_basis"] = "sum of individually declared line terms, not a common billing horizon"
            group["period_counts"] = {row["id"]: row.get("period_count") for row in members}
        groups.append(group)
    # Missing optional billing terms do not invalidate the independent per-period amounts.
    required = [metric for g in groups for metric in v2_required(
        g["amount"], any(v2_fee_base(row) for row in buckets[v2_group_key(g)]))]
    for row in quoted:
        if "period_count" in row:
            required.extend(v2_required(row["term_amount"], not v2_fee_na(row) and (
                v2_fee_base(row) or "base" in row["period_count"])))
    if gaps:
        required.append(v2_metric("BLOCKED", missing=gaps))
    if not required:
        required.append(v2_metric("NOT_APPLICABLE"))
    missing = list(dict.fromkeys(gap for metric in required for gap in metric["missing"]))
    return {"status": v2_status(required), "rows": rows, "groups": groups, "missing": missing}, required


def v2_one_time(labor, fee_result, coverage, pricing, money):
    total = {"currency": None, "tax_basis": None}
    if money != "all":
        return {**total, **{s: v2_metric("NOT_REQUESTED") for s in SCENARIOS}}
    one_time = [row for row in fee_result["rows"] if row["disposition"] == "quote" and row["period"] == "once" and not v2_fee_na(row)]
    bases = {(row["currency"], row["tax_basis"]) for row in one_time}
    if any(m["status"] != "NOT_APPLICABLE" for m in labor.values()):
        bases.add(("CNY", pricing["tax_basis"]))
    basis_ok = len(bases) <= 1 and all(tax in ("INCLUDED", "EXCLUDED") for _, tax in bases)
    if bases and basis_ok:
        total["currency"], total["tax_basis"] = next(iter(bases))
    for side in SCENARIOS:
        metrics = [labor[side]] + [row["amount"][side] for row in one_time]
        reasons = ["one-time coverage incomplete"] if coverage == "PARTIAL" else []
        if not basis_ok:
            reasons.append("incompatible currency or tax basis")
        if pricing["mode"] == "refused":
            reasons.append("labor pricing refused")
        reasons.extend(gap for m in metrics for gap in m["missing"])
        if reasons or any(m["status"] not in ("COMPLETE", "NOT_APPLICABLE") for m in metrics):
            total[side] = v2_metric("BLOCKED", missing=reasons or ["one-time contributions incomplete"])
        else:
            total[side] = v2_sum(metrics)
    return total


def v2_target(data, key, selected, roles, selected_roles, packages, fees):
    coverage = data["coverage"][key]
    pricing, money = data["pricing"], data["request"]["money"]
    labor_allowed = money in ("labor", "all")
    overrides = data["buffers"].get("overrides", {})
    buffers = overrides.get(key, data["buffers"]["default"])
    work_gaps = ["work coverage incomplete"] if coverage["work"] == "PARTIAL" else []
    outputs, tasks, used_reference = [], [], False
    base_metrics = set()
    for ident in selected:
        row = packages[ident]
        assignments = []
        gaps = [] if row["assignments_complete"] else ["package:" + ident + ":assignments incomplete"]
        work_gaps.extend(gaps)
        for assignment in row["assignments"]:
            if assignment["role"] not in selected_roles:
                continue
            result, referenced, task_base = v2_task(assignment, buffers, pricing, labor_allowed)
            base_metrics.update(task_base)
            used_reference |= referenced
            assignments.append(result)
        tasks.extend(assignments)
        outputs.append({**row, "assignments": assignments, **v2_aggregate(assignments, gaps, labor_allowed)})
    actual_roles = [r for r in roles if any(task["role"] == r for task in tasks)]
    role_results = {r: {**roles[r], **v2_aggregate([task for task in tasks if task["role"] == r], work_gaps, labor_allowed)} for r in actual_roles}
    totals = v2_aggregate(tasks, work_gaps, labor_allowed)
    # The three views have one shared atomic ledger; check subtotal closure explicitly.
    for metric in ("B", "R", "E", "labor"):
        for side in SCENARIOS:
            terms = totals[metric][side]["known_subtotal"]
            for view in (outputs, role_results.values()):
                subtotal = v2_sum([row[metric][side] for row in view], work_gaps)["known_subtotal"]
                if (terms is None) != (subtotal is None) or (terms is not None and Decimal(terms) != Decimal(subtotal)):
                    raise ValueError("work: task/role/package reconciliation failed")
    fee_result, fee_required = v2_fees([f for f in fees.values() if key in f["targets"]], coverage["external"], money in ("external", "all"))
    total = v2_one_time(totals["labor"], fee_result, coverage["external"], pricing, money)
    required = [metric for m in ("B", "R", "E", "labor") for metric in v2_required(totals[m], m in base_metrics)]
    total_base = "labor" in base_metrics or any(v2_fee_base(row) for row in fee_result["rows"] if row["period"] == "once")
    required += fee_required + v2_required(total, total_base)
    result = {"status": v2_status(required), "ids": selected, "task_ids": [a["id"] for a in tasks],
              "role_ids": actual_roles, "coverage": coverage, "buffers": buffers,
              "buffer_source": "override" if key in overrides else "default", "packages": outputs,
              "roles": role_results, **totals, "fees": fee_result, "one_time_total": total,
              "deltas": {}}
    if labor_allowed:
        result["labor_currency"] = "CNY"
        result["labor_tax_basis"] = pricing["tax_basis"]
    return result, used_reference, required


def v2_closed(metric):
    return metric["status"] in ("COMPLETE", "NOT_APPLICABLE")


def v2_difference(after, before, missing):
    if not v2_closed(after) or not v2_closed(before):
        return v2_metric("BLOCKED", missing=after["missing"] + before["missing"] + [missing])
    return v2_complete(Decimal(after["value"] or "0") - Decimal(before["value"] or "0"))


def v2_delta_amount(metric, gap):
    # For an explicitly closed comparison, an empty increment is exactly zero.
    if metric["status"] == "NOT_APPLICABLE":
        return v2_metric("BLOCKED", missing=[gap]) if gap else v2_complete(ZERO)
    if gap:
        return v2_metric("PARTIAL" if metric["known_subtotal"] is not None else "BLOCKED",
                         subtotal=Decimal(metric["known_subtotal"]) if metric["known_subtotal"] is not None else None,
                         missing=metric["missing"] + [gap])
    return metric


def v2_fee_deltas(parent, child):
    if parent["fees"]["status"] == "NOT_REQUESTED":
        return []
    p_groups = {v2_group_key(g): g for g in parent["fees"]["groups"]}
    c_groups = {v2_group_key(g): g for g in child["fees"]["groups"]}
    result = []
    for key in dict.fromkeys([*p_groups, *c_groups]):
        def amount(target, groups, field, side):
            if key in groups:
                return groups[key][field][side]
            return v2_metric("BLOCKED", missing=["external coverage incomplete"]) if target["coverage"]["external"] == "PARTIAL" else v2_metric("NOT_APPLICABLE")
        group = dict(zip(("currency", "tax_basis", "period", "category"), key))
        group["parent_fee_ids"] = p_groups.get(key, {}).get("fee_ids", [])
        group["child_fee_ids"] = c_groups.get(key, {}).get("fee_ids", [])
        if key[2] != "once":
            group["term_basis"] = "difference of individually declared line terms, not a common billing horizon"
        for field in ("amount", "term_amount"):
            for side in SCENARIOS:
                if field == "term_amount" and key[2] == "once":
                    metric = v2_metric("NOT_REQUESTED")
                elif key[1] == "UNKNOWN":
                    metric = v2_metric("BLOCKED", missing=["fee tax basis not comparable"])
                else:
                    metric = v2_difference(amount(child, c_groups, field, side), amount(parent, p_groups, field, side), "fee comparison incomplete")
                group.setdefault(field, {})[side] = metric
        result.append(group)
    return result


def v2_deltas(results):
    for parent_key, child_key in DELTA_PAIRS:
        if parent_key not in results or child_key not in results:
            continue
        parent, child = results[parent_key], results[child_key]
        parent_tasks = set(parent["task_ids"])
        parent_packages = set(parent["ids"])
        added = [a for row in child["packages"] for a in row["assignments"] if a["id"] not in parent_tasks]
        common = [a for row in child["packages"] for a in row["assignments"] if a["id"] in parent_tasks]
        delta = {"added_ids": [p for p in child["ids"] if p not in parent_packages],
                 "added_task_ids": [a["id"] for a in added], "B": {}, "added_E": {},
                 "common_buffer_effect": {}, "E": {}, "fees": v2_fee_deltas(parent, child)}
        for side in SCENARIOS:
            gap = None if v2_closed(parent["B"][side]) and v2_closed(child["B"][side]) else "parent/child base incomplete"
            delta["B"][side] = v2_delta_amount(v2_sum([a["B"][side] for a in added]), gap)
            effort_gap = gap or (None if v2_closed(parent["E"][side]) and v2_closed(child["E"][side]) else "parent/child effort incomplete")
            delta["added_E"][side] = v2_delta_amount(v2_sum([a["E"][side] for a in added]), effort_gap)
            shared = v2_sum([a["B"][side] for a in common])
            p_rate, c_rate = v2_at(parent["buffers"], side), v2_at(child["buffers"], side)
            if shared["status"] == "NOT_APPLICABLE":
                effect = shared
            elif p_rate["status"] in KNOWN and c_rate["status"] in KNOWN:
                effect = v2_product(shared, {"status": "CONFIRMED", "value": fmt(Decimal(c_rate["value"]) - Decimal(p_rate["value"]))}, "buffer comparison incomplete")
            else:
                effect = v2_metric("BLOCKED", missing=shared["missing"] + ["buffer comparison incomplete"])
            delta["common_buffer_effect"][side] = v2_delta_amount(effect, effort_gap)
            delta["E"][side] = v2_sum([delta["added_E"][side], delta["common_buffer_effect"][side]])
            for key in ("B", "E"):
                if delta[key][side]["status"] == "COMPLETE":
                    actual = v2_difference(child[key][side], parent[key][side], "comparison incomplete")
                    # Compare exact amounts, not their decimal text scale.
                    if actual["status"] != "COMPLETE" or Decimal(delta[key][side]["value"]) != Decimal(actual["value"]):
                        raise ValueError("delta: comparison reconciliation failed")
        child["deltas"][parent_key] = delta


def v2_reported(reported, results):
    if not isinstance(reported, dict) or reported.keys() - results.keys():
        raise ValueError("reported: invalid target object")
    def check(claims, computed):
        v2_fields(claims, (), SCENARIOS, "reported.scenarios")
        for side, value in claims.items():
            expected = v2_number(value, "reported.value")
            metric = computed[side]
            if metric["status"] != "COMPLETE" or Decimal(metric["value"]) != expected:
                raise ValueError("reported: claim not fully supported or mismatched")
    for target, claims in reported.items():
        v2_fields(claims, (), ("B", "R", "E", "labor", "roles"), "reported.entry")
        for key, claim in claims.items():
            if key == "roles":
                if not isinstance(claim, dict) or claim.keys() - results[target]["roles"].keys():
                    raise ValueError("reported.roles: invalid role object")
                for role, sides in claim.items():
                    check(sides, results[target]["roles"][role]["B"])
            else:
                check(claim, results[target][key])


def estimate_v2(data):
    roles, selected_roles, packages, targets, fees = v2_normalize(data)
    results, reference, required = {}, False, []
    for key, selected in targets.items():
        result, used_reference, metrics = v2_target(data, key, selected, roles, selected_roles, packages, fees)
        results[key] = result
        reference |= used_reference
        required.extend(metrics)
    v2_deltas(results)
    v2_reported(data.get("reported", {}), results)
    return {"schema_version": "2.0", "scope_version": data["scope_version"],
            "quote_version": data["quote_version"], "previous_scope_version": data.get("previous_scope_version"),
            "scope_changed": data.get("scope_changed", False), "request": data["request"],
            "status": v2_status(required), "results": results,
            "reference_notice": REFERENCE_NOTICE if reference else None}


@exact_arithmetic
def estimate(data):
    if isinstance(data, dict) and "schema_version" in data:
        if data["schema_version"] != "2.0":
            raise ValueError("schema_version: unsupported version")
        return estimate_v2(data)
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
        fixed_price_source(pricing["source"])
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


def unique_json_object(pairs):
    """Reject ambiguous snapshots instead of silently selecting a last value."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("input: duplicate JSON object field")
        result[key] = value
    return result


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
        data = json.loads(input_bytes.decode("utf-8"), object_pairs_hook=unique_json_object, parse_float=Decimal,
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
    except (OSError, ValueError, UnicodeError, RecursionError) as exc:
        # Malformed encoding/nesting and I/O errors must not expose document text or paths.
        detail = str(exc) if isinstance(exc, ValueError) and not isinstance(exc, (json.JSONDecodeError, UnicodeError)) else "invalid JSON or inaccessible file"
        print(f"INPUT_ERROR: {detail}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
