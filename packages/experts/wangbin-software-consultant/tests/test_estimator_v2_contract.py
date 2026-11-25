"""B6-Q02: independent SYNTHETIC cases for frozen calculator contract 2.0 A/B.

Exercise the real CLI, not private calculator helpers. Fraction serves as an
exact, independent oracle (including values wider than Decimal's default
context). No historical customer/QA fixture or production result is an oracle.
"""
import copy
import hashlib
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/wangbin-estimate-calculator/scripts/estimator.py"
SOURCE = "SYNTHETIC: independently specified regression assumption"
NOTICE = "人民币 1000～1500 元/人天为用户批准的示意估算参数，并非实时市场行情或正式合同报价。"
SIDES = ("low", "base", "high")
# The independent M/S/F/I specification, not inferred from the receipt.
PLANS = {
    "MVP": ("M",),
    "StandardA": ("M", "S"),
    "StandardB": ("M", "S", "I"),
    "FullA": ("M", "S", "F"),
    "FullB": ("M", "S", "F", "I"),
}
PARENTS = {
    "MVP": (), "StandardA": ("MVP",), "StandardB": ("StandardA",),
    "FullA": ("StandardA",), "FullB": ("FullA", "StandardB"),
}
# Two different FE tasks in M; all the named roles have real contributions.
LEDGER = {
    "M": (("manage", "PM", "10", "12", "15"),
          ("analyze", "BA", "2", "3", "4"),
          ("screen", "FE", "1.25", "2", "3"),
          ("screen-other", "FE", "0.75", "1", "1.5")),
    "S": (("server", "BE", "4", "5", "6"), ("schema", "DB", "1", "2", "3")),
    "I": (("interface", "INT", "3", "4", "5"), ("verify", "QA", "1", "2", "3")),
    "F": (("model", "AI", "2", "4", "6"), ("deploy", "OPS", "1", "2", "4"),
          ("design", "UI", "1", "1.5", "2"), ("machine", "OT", "2", "3", "4")),
}
ROLE_IDS = ("PM", "BA", "FE", "BE", "DB", "INT", "QA", "AI", "OPS", "UI", "OT")
RISK = ("0.1", "0.2", "0.3")


def atom(value, source=SOURCE):
    return {"status": "SYNTHETIC", "value": value, "source": source}


def unknown():
    return {"status": "UNKNOWN", "source": "Amount or effort not yet established"}


def na():
    return {"status": "NOT_APPLICABLE", "source": "SYNTHETIC: explicitly outside requested work"}


def series(low, base, high):
    return {side: atom(value) for side, value in zip(SIDES, (low, base, high))}


def same(value):
    return series(value, value, value)


def coverage(work="COMPLETE", external="NOT_APPLICABLE"):
    return {"work": work, "external": external, "source": SOURCE}


def full_input():
    # Literal business data only. No import of any production constants or math.
    packages = [{"id": p, "function": "Synthetic package " + p, "source": SOURCE,
                 "scope_version": "scope-2", "assignments_complete": True,
                 "membership": [t for t, members in PLANS.items() if p in members],
                 "assignments": [{"id": task, "role": role, "effort": series(lo, b, hi)}
                                 for task, role, lo, b, hi in entries]}
                for p, entries in LEDGER.items()]
    return {"schema_version": "2.0", "scope_version": "scope-2", "quote_version": "quote-3",
            "request": {"mode": "full", "money": "all"},
            "role_catalog": [{"id": r, "name": r + " specialist"} for r in ROLE_IDS],
            "work_packages": packages, "coverage": {t: coverage() for t in PLANS},
            "buffers": {"default": series(*RISK)},
            "pricing": {"mode": "fixed", "tax_basis": "EXCLUDED", "rate": atom("1200.25")},
            "fees": []}


def select_tiers(*tiers, money="all"):
    data = full_input()
    data["request"] = {"mode": "tiers", "tiers": list(tiers), "money": money}
    data["coverage"] = {t: coverage() for t in tiers}
    return data


def scope_input(*packages, roles=None, money="all"):
    data = full_input()
    data["request"] = {"mode": "scope", "scope_id": "slice", "package_ids": list(packages), "money": money}
    if roles is not None:
        data["request"]["role_ids"] = roles
    data["coverage"] = {"slice": coverage()}
    for p in data["work_packages"]:
        p.pop("membership")
    return data


def assignments(data, package="M"):
    return next(p["assignments"] for p in data["work_packages"] if p["id"] == package)


def fee(ident, targets=("MVP",), amount="25", **changes):
    row = {"id": ident, "account_id": ident, "description": "Synthetic fee " + ident,
           "source": SOURCE, "scope_version": "scope-2", "targets": list(targets),
           "work_package_ids": [], "interface_only": False, "category": "third_party",
           "period": "once", "currency": "CNY", "tax_basis": "EXCLUDED", "cost_state": "PLANNED",
           "disposition": "quote", "calculation": {"mode": "amount", "amount": same(amount)}}
    row.update(changes)
    return row


@pytest.fixture
def cli(tmp_path):
    runs = 0

    def invoke(data, *, error=None):
        nonlocal runs
        runs += 1
        source = tmp_path / f"input-{runs}.json"
        receipt = tmp_path / f"receipt-{runs}.json"
        payload = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode("utf-8")
        source.write_bytes(payload)
        run = subprocess.run([sys.executable, "-B", str(SCRIPT), str(source), "-o", str(receipt)],
                             cwd=tmp_path, capture_output=True, timeout=20)
        assert source.read_bytes() == payload
        if error is not None:
            assert run.returncode == 2, (run.returncode, run.stdout, run.stderr)
            assert not receipt.exists()
            assert b"INPUT_ERROR:" in run.stderr
            assert error.encode("utf-8") in run.stderr, run.stderr
            return run
        assert run.returncode == 0, run.stderr
        result = json.loads(receipt.read_bytes())
        assert result["input_sha256"] == hashlib.sha256(payload).hexdigest()
        assert result["script_sha256"] == hashlib.sha256(SCRIPT.read_bytes()).hexdigest()
        return result

    return invoke


def exact(text, expected):
    assert isinstance(text, str), text
    assert Fraction(text) == Fraction(expected)


def metric(result, status, value=None, subtotal=None):
    assert set(result) == {"status", "value", "known_subtotal", "missing"}
    assert result["status"] == status, result
    if status == "COMPLETE":
        exact(result["value"], value)
        exact(result["known_subtotal"], value)
        assert result["missing"] == []
    else:
        assert result["value"] is None, result
        if subtotal is None:
            assert result["known_subtotal"] is None, result
        else:
            exact(result["known_subtotal"], subtotal)
        if status in ("PARTIAL", "BLOCKED"):
            assert result["missing"], result
        else:
            assert result["missing"] == []


def oracle(entries, side, risk, rates):
    """Contract B=Σd, R=B*r, E=B+R, C=Σd*(1+r)*role price."""
    i = SIDES.index(side) + 2
    base = sum((Fraction(entry[i]) for entry in entries), Fraction(0))
    reserve = base * Fraction(risk)
    labor = sum((Fraction(entry[i]) * (1 + Fraction(risk)) * Fraction(rates[entry[1]])
                 for entry in entries), Fraction(0))
    return {"B": base, "R": reserve, "E": base + reserve, "labor": labor}


def check_work(view, entries, side, risk, rates):
    for key, expected in oracle(entries, side, risk, rates).items():
        metric(view[key][side], "COMPLETE", expected)


def test_unique_tasks_all_roles_five_members_and_directed_risk_deltas(cli):
    data = full_input()
    # A lower child buffer makes an E difference genuinely negative.
    overrides = {"MVP": ("0.9", "0.9", "0.9"), "StandardA": ("0", "0", "0")}
    data["buffers"]["overrides"] = {t: series(*r) for t, r in overrides.items()}
    tasks = assignments(data)
    tasks.append(copy.deepcopy(tasks[2]))
    data["work_packages"].append(copy.deepcopy(data["work_packages"][0]))
    data["work_packages"].reverse()  # ordering is not tier inheritance
    data["reported"] = {"MVP": {"B": {"low": "14", "base": "18", "high": "23.5"},
                                "R": {"low": "12.6"}, "E": {"low": "26.6"},
                                "labor": {"low": "31926.65"}, "roles": {"FE": {"low": "2"}}}}
    result = cli(data)
    assert result["status"] == "COMPLETE"
    assert set(result["results"]) == set(PLANS)
    rates = dict.fromkeys(ROLE_IDS, "1200.25")
    for tier, members in PLANS.items():
        target = result["results"][tier]
        entries = [entry for p in members for entry in LEDGER[p]]
        assert target["status"] == "COMPLETE"
        assert sorted(target["ids"]) == sorted(members)
        assert sorted(target["task_ids"]) == sorted(row[0] for row in entries)
        assert sorted(target["role_ids"]) == sorted({row[1] for row in entries})
        assert set(target["roles"]) == set(target["role_ids"])
        assert sorted(p["id"] for p in target["packages"]) == sorted(members)
        assert set(target["deltas"]) == set(PARENTS[tier])
        assert target["buffer_source"] == ("override" if tier in overrides else "default")
        for i, side in enumerate(SIDES):
            rate = overrides.get(tier, RISK)[i]
            check_work(target, entries, side, rate, rates)
            metric(target["one_time_total"][side], "COMPLETE", oracle(entries, side, rate, rates)["labor"])
            for role, view in target["roles"].items():
                check_work(view, [e for e in entries if e[1] == role], side, rate, rates)
            for pkg in target["packages"]:
                expected = LEDGER[pkg["id"]]
                check_work(pkg, expected, side, rate, rates)
                assert sorted(task["id"] for task in pkg["assignments"]) == sorted(e[0] for e in expected)
                for task in pkg["assignments"]:
                    entry = next(e for e in expected if e[0] == task["id"])
                    check_work(task, [entry], side, rate, rates)
                    assert task["effort"][side] == atom(entry[i + 2])
            for parent in PARENTS[tier]:
                added = set(members) - set(PLANS[parent])
                new_rows = [e for p in added for e in LEDGER[p]]
                common = [e for p in PLANS[parent] for e in LEDGER[p]]
                delta = target["deltas"][parent]
                assert sorted(delta["added_ids"]) == sorted(added)
                assert sorted(delta["added_task_ids"]) == sorted(e[0] for e in new_rows)
                new_b = sum(Fraction(e[i + 2]) for e in new_rows)
                added_e = new_b * (1 + Fraction(rate))
                common_effect = sum(Fraction(e[i + 2]) for e in common) * (
                    Fraction(rate) - Fraction(overrides.get(parent, RISK)[i]))
                metric(delta["B"][side], "COMPLETE", new_b)
                metric(delta["added_E"][side], "COMPLETE", added_e)
                metric(delta["common_buffer_effect"][side], "COMPLETE", common_effect)
                metric(delta["E"][side], "COMPLETE", added_e + common_effect)
    metric(result["results"]["StandardA"]["deltas"]["MVP"]["E"]["low"], "COMPLETE", "-7.6")


def test_tier_subset_and_scope_only_selected_roles(cli):
    one = cli(select_tiers("FullA"))
    assert set(one["results"]) == {"FullA"}
    assert set(one["results"]["FullA"]["ids"]) == {"M", "S", "F"}
    assert one["results"]["FullA"]["deltas"] == {}
    data = scope_input("M", "S", roles=["FE"], money="labor")
    # Explicitly unselected unknown tasks cannot poison the FE-only request.
    assignments(data)[0]["effort"]["base"] = unknown()
    target = cli(data)["results"]["slice"]
    assert target["status"] == "COMPLETE"
    assert set(target["ids"]) == {"M", "S"}
    assert set(target["task_ids"]) == {"screen", "screen-other"}
    assert target["role_ids"] == ["FE"] and target["deltas"] == {}
    for side, value in zip(SIDES, ("2", "3", "4.5")):
        metric(target["B"][side], "COMPLETE", value)
        metric(target["one_time_total"][side], "NOT_REQUESTED")
    empty = next(p for p in target["packages"] if p["id"] == "S")
    metric(empty["B"]["low"], "NOT_APPLICABLE")


def test_absent_base_is_optional_but_explicit_unknown_base_is_required(cli):
    data = select_tiers("MVP")
    for task in assignments(data):
        task["effort"].pop("base")
    data["buffers"]["default"].pop("base")
    result = cli(data)
    assert result["status"] == result["results"]["MVP"]["status"] == "COMPLETE"
    metric(result["results"]["MVP"]["B"]["high"], "COMPLETE", "23.5")
    metric(result["results"]["MVP"]["B"]["base"], "BLOCKED")
    assignments(data)[0]["effort"]["base"] = unknown()
    result = cli(data)
    assert result["status"] == result["results"]["MVP"]["status"] == "PARTIAL"
    metric(result["results"]["MVP"]["B"]["low"], "COMPLETE", "14")
    metric(result["results"]["MVP"]["B"]["base"], "BLOCKED")


@pytest.mark.parametrize("trigger", ["buffer", "role-range", "reference"])
def test_independent_buffer_or_price_base_triggers_required_scenario(cli, trigger):
    data = select_tiers("MVP", money="labor")
    for package in data["work_packages"]:
        for task in package["assignments"]:
            task["effort"].pop("base")
    data["buffers"]["default"].pop("base")
    roles = ("PM", "BA", "FE")
    if trigger == "role-range":
        data["pricing"] = {"mode": "role", "tax_basis": "EXCLUDED", "rates": {
            "PM": {"kind": "fixed", "value": atom("800")},
            "BA": {"kind": "range", "values": {"low": atom("500"), "high": atom("900")}},
            "FE": {"kind": "fixed", "value": atom("1300")}}}
        price_pairs = ({"PM": "800", "BA": "500", "FE": "1300"},
                       {"PM": "800", "BA": "900", "FE": "1300"})
    elif trigger == "reference":
        data["pricing"] = {"mode": "reference", "tax_basis": "EXCLUDED"}
        price_pairs = ({r: "1000" for r in roles}, {r: "1500" for r in roles})
    else:
        price_pairs = ({r: "1200.25" for r in roles},) * 2
    # Control: with every relevant base absent, valid endpoints are complete.
    before = cli(data)
    assert before["status"] == before["results"]["MVP"]["status"] == "COMPLETE"
    if trigger == "buffer":
        data["buffers"]["default"]["base"] = atom("0.2")
    elif trigger == "role-range":
        data["pricing"]["rates"]["BA"]["values"]["base"] = atom("700")
    else:
        data["pricing"]["base"] = atom("1180")
    # Only one independent base trigger is supplied, never an effort base.
    # A known buffer or price cannot invent the missing base effort, but must
    # make the relevant base calculation a required, unresolved metric.
    after = cli(data)
    target = after["results"]["MVP"]
    assert after["status"] == target["status"] == "PARTIAL"
    for key in ("B", "R", "E", "labor"):
        metric(target[key]["base"], "BLOCKED")
    for side, risk, rates in zip(("low", "high"), ("0.1", "0.3"), price_pairs):
        check_work(target, LEDGER["M"], side, risk, rates)
        for key in ("B", "R", "E", "labor"):
            assert target[key][side] == before["results"]["MVP"][key][side]


def test_base_only_is_a_real_contribution_not_all_blocked(cli):
    data = scope_input("M", roles=["FE"], money="none")
    for task in assignments(data)[2:]:
        task["effort"]["low"] = unknown()
        task["effort"]["high"] = unknown()
    result = cli(data)
    target = result["results"]["slice"]
    assert result["status"] == target["status"] == "PARTIAL"
    metric(target["B"]["low"], "BLOCKED")
    metric(target["B"]["high"], "BLOCKED")
    metric(target["B"]["base"], "COMPLETE", "3")
    metric(target["R"]["base"], "COMPLETE", "0.6")
    metric(target["E"]["base"], "COMPLETE", "3.6")


@pytest.mark.parametrize("condition,expected_status,subtotal", [
    ("unknown-task", "PARTIAL", "1.25"), ("unknown-all", "BLOCKED", None),
    ("zero", "COMPLETE", None), ("na", "NOT_APPLICABLE", None),
    ("coverage", "PARTIAL", "2"), ("assignments", "PARTIAL", "2"),
])
def test_work_state_zero_unknown_and_coverage(cli, condition, expected_status, subtotal):
    data = scope_input("M", roles=["FE"], money="none")
    tasks = assignments(data)[2:]
    if condition == "unknown-task":
        tasks[1]["effort"] = {s: unknown() for s in SIDES}
    elif condition == "unknown-all":
        for task in tasks:
            task["effort"] = {s: unknown() for s in SIDES}
    elif condition in ("na", "zero"):
        for task in tasks:
            task["effort"] = ({s: na() for s in SIDES} if condition == "na" else same("0"))
        if condition == "na":
            data["coverage"]["slice"]["work"] = "NOT_APPLICABLE"
    elif condition == "coverage":
        data["coverage"]["slice"]["work"] = "PARTIAL"
    else:
        data["work_packages"][0]["assignments_complete"] = False
    result = cli(data)
    target = result["results"]["slice"]
    assert result["status"] == target["status"] == expected_status
    metric(target["B"]["low"], expected_status, "0" if condition == "zero" else None, subtotal)
    if subtotal is not None:
        metric(target["E"]["low"], "PARTIAL", subtotal=Fraction(subtotal) * Fraction("1.1"))
        if condition == "unknown-task":
            assert "screen-other" in " ".join(target["B"]["low"]["missing"])


@pytest.mark.parametrize("work,status", [("NOT_APPLICABLE", "NOT_APPLICABLE"), ("PARTIAL", "BLOCKED")])
def test_empty_scope_requires_evidence_not_default_zero(cli, work, status):
    data = scope_input(money="none")
    data["coverage"]["slice"]["work"] = work
    result = cli(data)
    assert result["status"] == status
    metric(result["results"]["slice"]["B"]["low"], status)


def test_partial_parent_child_comparison_keeps_only_known_increment(cli):
    data = select_tiers("StandardA", "StandardB", money="none")
    assignments(data, "I")[1]["effort"]["low"] = unknown()
    result = cli(data)
    assert result["status"] == "PARTIAL"
    child = result["results"]["StandardB"]
    metric(child["B"]["low"], "PARTIAL", subtotal="22")
    delta = child["deltas"]["StandardA"]
    assert delta["added_ids"] == ["I"]
    assert set(delta["added_task_ids"]) == {"interface", "verify"}
    metric(delta["B"]["low"], "PARTIAL", subtotal="3")
    metric(delta["added_E"]["low"], "PARTIAL", subtotal="3.3")
    metric(delta["E"]["low"], "PARTIAL", subtotal="3.3")
    metric(delta["B"]["high"], "COMPLETE", "8")


def test_unknown_buffer_and_override_without_base_preserve_independent_B(cli):
    data = select_tiers("MVP", "StandardA", money="labor")
    data["buffers"]["overrides"] = {"StandardA": {"low": unknown(), "high": atom("0.4")}}
    result = cli(data)
    assert result["status"] == "PARTIAL"
    target = result["results"]["StandardA"]
    metric(target["B"]["low"], "COMPLETE", "19")
    metric(target["R"]["low"], "BLOCKED")
    metric(target["E"]["base"], "BLOCKED")  # no silent default fallback
    metric(target["labor"]["low"], "BLOCKED")
    metric(target["E"]["high"], "COMPLETE", Fraction("32.5") * Fraction("1.4"))
    metric(target["deltas"]["MVP"]["B"]["low"], "COMPLETE", "5")
    metric(target["deltas"]["MVP"]["E"]["low"], "BLOCKED")


@pytest.mark.parametrize("mode,prices,reference", [
    ("fixed", {"PM": ("1200.25",)*3, "BA": ("1200.25",)*3, "FE": ("1200.25",)*3}, False),
    ("role", {"PM": ("800",)*3, "BA": ("500", "700", "900"), "FE": ("1300",)*3}, False),
    ("reference", {r: ("1000", "1180", "1500") for r in ("PM", "BA", "FE")}, True),
    ("mixed-fixed", {"PM": ("800",)*3, "BA": ("500", "700", "900"), "FE": ("1100",)*3}, False),
    ("mixed-reference", {"PM": ("800",)*3, "BA": ("500", "700", "900"), "FE": ("1000", "1180", "1500")}, True),
])
def test_price_modes_independent_role_and_scenario_products(cli, mode, prices, reference):
    data = select_tiers("MVP", money="labor")
    explicit = {"PM": {"kind": "fixed", "value": atom("800")},
                "BA": {"kind": "range", "values": series("500", "700", "900")}}
    permission = "AUTHORIZED: TURN:7"
    if mode == "role":
        data["pricing"] = {"mode": "role", "tax_basis": "EXCLUDED", "rates": {
            **explicit, "FE": {"kind": "fixed", "value": atom("1300")}}}
    elif mode == "reference":
        data["pricing"] = {"mode": "reference", "tax_basis": "EXCLUDED", "base": atom("1180")}
    elif mode.startswith("mixed-"):
        fallback = ({"kind": "fixed", "value": atom("1100")} if mode == "mixed-fixed" else
                    {"kind": "reference", "base": atom("1180")})
        data["pricing"] = {"mode": "mixed", "tax_basis": "EXCLUDED", "rates": explicit,
                           "fallback": fallback, "fallback_roles": ["FE"], "permission_source": permission}
    result = cli(data)
    target = result["results"]["MVP"]
    assert result["status"] == "COMPLETE"
    assert result["reference_notice"] == (NOTICE if reference else None)
    for i, side in enumerate(SIDES):
        rates = {role: values[i] for role, values in prices.items()}
        check_work(target, LEDGER["M"], side, RISK[i], rates)
        for role in rates:
            check_work(target["roles"][role], [e for e in LEDGER["M"] if e[1] == role], side, RISK[i], rates)
    for task in target["packages"][0]["assignments"]:
        assert task["prices"]["low"]["permission_source"] == (
            permission if task["role"] == "FE" and mode.startswith("mixed-") else None)


def test_reference_never_invents_midpoint_and_missing_role_price_is_partial(cli):
    data = select_tiers("MVP")
    data["pricing"] = {"mode": "reference", "tax_basis": "EXCLUDED"}
    result = cli(data)
    assert result["status"] == "PARTIAL"  # actual base effort requires an independent price
    target = result["results"]["MVP"]
    metric(target["labor"]["low"], "COMPLETE", "15400")
    metric(target["labor"]["base"], "BLOCKED")
    data["pricing"] = {"mode": "mixed", "tax_basis": "EXCLUDED", "rates": {
        "PM": {"kind": "fixed", "value": atom("800")}}, "fallback": {"kind": "fixed", "value": atom("1000")},
        "fallback_roles": ["FE"], "permission_source": "AUTHORIZED: FILE:permission.md:3"}
    target = cli(data)["results"]["MVP"]
    metric(target["labor"]["low"], "PARTIAL", subtotal="11000")  # (10*800+2*1000)*1.1
    metric(target["roles"]["BA"]["labor"]["low"], "BLOCKED")
    metric(target["one_time_total"]["low"], "BLOCKED")


@pytest.mark.parametrize("money", ["none", "labor", "external", "all"])
def test_money_permission_does_not_leak_unrequested_values(cli, money):
    data = select_tiers("MVP", "StandardA", money=money)
    price, shared, extra = "1234567.891", "9876543.219", "2468.135"
    data["pricing"]["rate"] = atom(price)
    data["fees"] = [fee("charge", targets=("MVP", "StandardA"), amount=shared),
                    fee("extra", targets=("StandardA",), amount=extra)]
    for target_id in ("MVP", "StandardA"):
        data["coverage"][target_id]["external"] = "COMPLETE"
    result = cli(data)
    assert result["status"] == "COMPLETE"
    raw = json.dumps(result, ensure_ascii=False)
    labor_allowed = money in ("all", "labor")
    external_allowed = money in ("all", "external")
    if not labor_allowed:
        assert price not in raw and '"prices"' not in raw
        assert result["reference_notice"] is None
    if not external_allowed:
        assert shared not in raw and extra not in raw
    for target_id, target in result["results"].items():
        entries = [entry for package in PLANS[target_id] for entry in LEDGER[package]]
        fee_total = Fraction(shared) + (Fraction(extra) if target_id == "StandardA" else 0)
        views = [target, *target["roles"].values(), *target["packages"],
                 *(task for package in target["packages"] for task in package["assignments"])]
        for side, risk in zip(SIDES, RISK):
            expected_labor = oracle(entries, side, risk, {r: price for r in ROLE_IDS})["labor"]
            if not labor_allowed:
                for view in views:
                    metric(view["labor"][side], "NOT_REQUESTED")
                    assert "prices" not in view
            else:
                metric(target["labor"][side], "COMPLETE", expected_labor)
            if not external_allowed:
                assert target["fees"]["rows"] == target["fees"]["groups"] == []
                assert target["fees"]["status"] == "NOT_REQUESTED"
            else:
                rows = {row["id"]: row for row in target["fees"]["rows"]}
                assert set(rows) == ({"charge", "extra"} if target_id == "StandardA" else {"charge"})
                metric(rows["charge"]["amount"][side], "COMPLETE", shared)
                if target_id == "StandardA":
                    metric(rows["extra"]["amount"][side], "COMPLETE", extra)
                assert len(target["fees"]["groups"]) == 1
                metric(target["fees"]["groups"][0]["amount"][side], "COMPLETE", fee_total)
            metric(target["one_time_total"][side], "COMPLETE" if money == "all" else "NOT_REQUESTED",
                   expected_labor + fee_total if money == "all" else None)
    delta = result["results"]["StandardA"]["deltas"]["MVP"]["fees"]
    if not external_allowed:
        assert delta == []
    else:
        assert len(delta) == 1
        for side in SIDES:
            metric(delta[0]["amount"][side], "COMPLETE", extra)
            metric(delta[0]["term_amount"][side], "NOT_REQUESTED")


def test_refused_labor_does_not_refuse_authorized_external_fee(cli):
    data = select_tiers("MVP")
    data["pricing"] = {"mode": "refused", "tax_basis": "UNKNOWN"}
    data["coverage"]["MVP"]["external"] = "COMPLETE"
    data["fees"] = [fee("charge", amount="39.5")]
    result = cli(data)
    target = result["results"]["MVP"]
    assert result["status"] == "PARTIAL"
    metric(target["labor"]["low"], "BLOCKED")
    metric(target["fees"]["rows"][0]["amount"]["low"], "COMPLETE", "39.5")
    metric(target["one_time_total"]["low"], "BLOCKED")
    assert result["reference_notice"] is None


def groups(target):
    return {(g["currency"], g["tax_basis"], g["period"], g["category"]): g for g in target["fees"]["groups"]}


def test_fee_accounts_alternative_prices_periods_quantity_and_dispositions(cli):
    a, b = "StandardA", "StandardB"
    data = select_tiers(a, b)
    for t in (a, b):
        data["coverage"][t]["external"] = "COMPLETE"
    monthly = fee("cloud", (a, b), period="month", category="service", calculation={
        "mode": "quantity_price", "unit": "instance", "quantity": series("2", "3", "4"),
        "unit_price": series("10.25", "11", "12.5")}, period_count=series("2", "3", "4"))
    data["fees"] = [fee("license-a", (a,), "80", account_id="license"),
                    fee("license-b", (b,), "65", account_id="license"),
                    fee("integration", (b,), "30", interface_only=True, work_package_ids=["I"]),
                    fee("deployment", (a, b), "15", category="deployment", work_package_ids=["S"]),
                    monthly, copy.deepcopy(monthly),
                    fee("cloud-extra", (a, b), "1.5", period="month", category="service", period_count=same("5")),
                    fee("support", (a, b), "120", period="year", category="maintenance"),
                    fee("included", (a, b), "1000", disposition="included_in_labor", work_package_ids=["M"]),
                    fee("excluded", (a, b), "2000", disposition="excluded", cost_state="INCURRED")]
    result = cli(data)
    assert result["status"] == "COMPLETE"
    assert set(result["results"]) == {a, b}
    for t, one_time, license_id in ((a, 95, "license-a"), (b, 110, "license-b")):
        target = result["results"][t]
        rows = {r["id"]: r for r in target["fees"]["rows"]}
        assert len(rows) == len(target["fees"]["rows"])
        assert set(rows) == {license_id, "deployment", "cloud", "cloud-extra", "support", "included", "excluded"} | ({"integration"} if t == b else set())
        assert rows["excluded"]["cost_state"] == "INCURRED"
        metric(rows["included"]["amount"]["low"], "NOT_REQUESTED")
        metric(rows["excluded"]["amount"]["low"], "NOT_REQUESTED")
        g = groups(target)
        month = g[("CNY", "EXCLUDED", "month", "service")]
        assert set(month["fee_ids"]) == {"cloud", "cloud-extra"}
        for i, side in enumerate(SIDES):
            cloud = Fraction(("20.5", "33", "50")[i])
            metric(rows["cloud"]["amount"][side], "COMPLETE", cloud)
            metric(month["amount"][side], "COMPLETE", cloud + Fraction("1.5"))
            metric(month["term_amount"][side], "COMPLETE", cloud * (i + 2) + Fraction("7.5"))
            metric(rows["support"]["amount"][side], "COMPLETE", "120")
            metric(rows["support"]["term_amount"][side], "BLOCKED")  # optional billing term absent
            entries = [e for p in PLANS[t] for e in LEDGER[p]]
            labor = oracle(entries, side, RISK[i], dict.fromkeys(ROLE_IDS, "1200.25"))["labor"]
            metric(target["one_time_total"][side], "COMPLETE", labor + one_time)
        assert target["one_time_total"]["currency"] == "CNY"
        assert target["one_time_total"]["tax_basis"] == "EXCLUDED"
    delta = result["results"][b]["deltas"][a]["fees"]
    third_party = next(g for g in delta if g["category"] == "third_party")
    metric(third_party["amount"]["low"], "COMPLETE", "15")  # 65+30-80
    assert third_party["parent_fee_ids"] == ["license-a"]
    assert set(third_party["child_fee_ids"]) == {"license-b", "integration"}


@pytest.mark.parametrize("change", ["currency", "tax", "separate-tax", "unknown-tax", "unknown-fee", "partial-coverage"])
def test_fee_groups_keep_incompatible_or_incomplete_total_blocked(cli, change):
    data = select_tiers("MVP")
    data["coverage"]["MVP"]["external"] = "COMPLETE"
    other = fee("other", amount="12")
    if change == "currency":
        other["currency"] = "USD"
    elif change == "tax":
        other["tax_basis"] = "INCLUDED"
    elif change == "separate-tax":
        other.update(category="tax", tax_basis="SEPARATE")
    elif change == "unknown-tax":
        other["tax_basis"] = "UNKNOWN"
    elif change == "unknown-fee":
        other["calculation"]["amount"] = {s: unknown() for s in SIDES}
    else:
        data["coverage"]["MVP"]["external"] = "PARTIAL"
    data["fees"] = [fee("known", amount="7.5"), other]
    result = cli(data)
    target = result["results"]["MVP"]
    assert result["status"] == "PARTIAL"
    metric(target["labor"]["low"], "COMPLETE", Fraction("15.4") * Fraction("1200.25"))
    metric(target["one_time_total"]["low"], "BLOCKED")
    g = groups(target)
    known_group = g[("CNY", "EXCLUDED", "once", "third_party")]
    if change in ("unknown-fee", "partial-coverage"):
        metric(known_group["amount"]["low"], "PARTIAL", subtotal="7.5" if change == "unknown-fee" else "19.5")
    else:
        metric(known_group["amount"]["low"], "COMPLETE", "7.5")
        metric(g[(other["currency"], other["tax_basis"], "once", other["category"])]["amount"]["low"], "COMPLETE", "12")
        assert target["one_time_total"]["currency"] is None


@pytest.mark.parametrize("price", ["0", "5.25"])
def test_fee_base_only_contributes_to_status_and_unknown_quantity_is_not_zero(cli, price):
    data = scope_input(money="external")
    data["coverage"]["slice"] = coverage("NOT_APPLICABLE", "COMPLETE")
    data["fees"] = [fee("monthly", ("slice",), period="month", category="service", calculation={
        "mode": "quantity_price", "unit": "instance",
        "quantity": {"low": unknown(), "base": atom("3"), "high": unknown()},
        "unit_price": same(price)}, period_count=same("2"))]
    result = cli(data)
    target = result["results"]["slice"]
    assert result["status"] == target["status"] == target["fees"]["status"] == "PARTIAL"
    row = target["fees"]["rows"][0]
    metric(row["amount"]["low"], "BLOCKED")
    metric(row["amount"]["base"], "COMPLETE", 3 * Fraction(price))
    metric(row["term_amount"]["base"], "COMPLETE", 6 * Fraction(price))
    metric(row["amount"]["high"], "BLOCKED")


def test_period_count_base_is_required_only_for_term_not_one_time(cli):
    data = select_tiers("MVP")
    for t in assignments(data):
        t["effort"].pop("base")
    data["buffers"]["default"].pop("base")
    data["coverage"]["MVP"]["external"] = "COMPLETE"
    row = fee("recurring", period="year", category="maintenance", period_count=series("2", "3", "4"))
    row["calculation"]["amount"].pop("base")
    data["fees"] = [row]
    result = cli(data)
    target = result["results"]["MVP"]
    assert result["status"] == "PARTIAL"
    metric(target["fees"]["rows"][0]["term_amount"]["low"], "COMPLETE", "50")
    metric(target["fees"]["rows"][0]["term_amount"]["base"], "BLOCKED")
    metric(target["one_time_total"]["low"], "COMPLETE", Fraction("15.4") * Fraction("1200.25"))


def test_scope_and_quote_identity_new_price_changes_amount_not_effort(cli):
    data = select_tiers("MVP")
    data.update(previous_scope_version="scope-1", scope_changed=True)
    data["work_packages"][0]["source"] = "TURN:12"
    assignments(data)[0]["effort"]["low"] = atom("10", "FILE:unknown-prices-notes.md:4")
    first = cli(data)
    data["quote_version"] = "quote-4"
    data["pricing"]["rate"] = atom("900.5", "ASSUMED_CONDITIONAL: synthetic price if approved later")
    second = cli(data)
    for result, quote, price in ((first, "quote-3", "1200.25"), (second, "quote-4", "900.5")):
        assert (result["schema_version"], result["scope_version"], result["quote_version"],
                result["previous_scope_version"], result["scope_changed"]) == ("2.0", "scope-2", quote, "scope-1", True)
        target = result["results"]["MVP"]
        assert target["packages"][0]["source"] == "TURN:12"
        assert target["packages"][0]["assignments"][0]["effort"]["low"]["source"] == "FILE:unknown-prices-notes.md:4"
        metric(target["B"]["low"], "COMPLETE", "14")
        metric(target["labor"]["low"], "COMPLETE", Fraction("15.4") * Fraction(price))
    assert first["input_sha256"] != second["input_sha256"]
    assert first["script_sha256"] == second["script_sha256"]


# Mutate one otherwise valid synthetic request at a time. Error paths prevent
# incidental earlier schema errors from passing the intended rejection check.
@pytest.mark.parametrize("path,value,error", [
    (("schema_version",), "3.0", "schema_version"),
    (("schema_version",), 2, "schema_version"),
    (("quote_version",), "", "quote_version"),
    (("scope_version",), "stale", "scope version"),
    (("scope_changed",), True, "scope change"),
    (("request", "tiers"), ["MVP", "MVP"], "request.tiers"),
    (("request", "money"), "maybe", "request.money"),
    (("coverage",), {}, "coverage"),
    (("role_catalog", 1, "id"), "PM", "duplicate role"),
    (("role_catalog", 1, "name"), " pm specialist ", "duplicate role"),
    (("work_packages", 0, "membership"), ["MVP", "FullA"], "membership"),
    (("work_packages", 0, "scope_version"), "scope-old", "scope version"),
    (("work_packages", 0, "assignments_complete"), "true", "completeness flag"),
    (("work_packages", 0, "assignments", 0, "role"), "unlisted", "assignments.role"),
    (("work_packages", 0, "assignments", 0, "effort", "low", "value"), 10, "expected decimal string"),
    (("work_packages", 0, "assignments", 0, "effort", "low", "value"), True, "expected decimal string"),
    (("work_packages", 0, "assignments", 0, "effort", "low", "value"), "-1", "out of range"),
    (("work_packages", 0, "assignments", 0, "effort", "low", "value"), "NaN", "expected decimal string"),
    (("work_packages", 0, "assignments", 0, "effort", "low", "value"), "1_000", "expected decimal string"),
    (("work_packages", 0, "assignments", 0, "effort", "base", "value"), "16", "unordered scenario"),
    (("work_packages", 0, "assignments", 0, "effort", "low", "status"), "UNKNOWN", "absent or null"),
    (("work_packages", 0, "assignments", 0, "effort", "low"), na(), "inconsistent applicability"),
    (("buffers", "default", "high", "value"), "1.01", "out of range"),
    (("pricing", "rate", "source"), "1000", "source"),
    (("pricing", "rate", "source"), "TURN:01", "source"),
    (("pricing", "rate", "source"), "FILE:..:1", "source"),
    (("pricing", "rate", "source"), "SYNTHETIC: UNKNOWN / NOT_APPLICABLE", "source"),
    (("pricing", "rate", "source"), "ASSUMED: PENDING_CONFIRMATION", "source"),
    (("pricing", "rate", "source"), "ASSUMED: UNMAPPED/NEEDS_CONFIRMATION", "source"),
    (("pricing", "rate", "source"), "ASSUMED: UNKNOWN/TO_BE_QUOTED", "source"),
    (("pricing", "rate", "source"), "ASSUMED: permission denied", "source"),
    (("reported",), {"MVP": {"B": {"low": "13"}}}, "reported: claim"),
    (("reported",), {"MVP": {"roles": {"FE": {"low": "1.25"}}}}, "reported: claim"),
])
def test_reject_invalid_schema_identity_numeric_source_and_reported(cli, path, value, error):
    data = select_tiers("MVP")
    container = data
    for k in path[:-1]:
        container = container[k]
    container[path[-1]] = value
    cli(data, error=error)


@pytest.mark.parametrize("case,error", [
    ("package", "work_packages: conflicting ID"),
    ("task", "assignments: conflicting ID"),
    ("reused-task", "task shared across packages"),
    ("unknown-scope-package", "request.package_ids"),
    ("unknown-scope-role", "request.role_ids"),
    ("empty-complete", "no applicable assignments"),
    ("na-with-work", "inapplicability conflicts with work"),
    ("reported-partial", "reported: claim"),
    ("missing-high", "effort: invalid object fields"),
    ("extra-field", "invalid object fields"),
])
def test_reject_conflicting_work_and_false_coverage(cli, case, error):
    data = select_tiers("MVP")
    if case == "package":
        row = copy.deepcopy(data["work_packages"][0]); row["function"] = "different package"
        data["work_packages"].append(row)
    elif case == "task":
        task = copy.deepcopy(assignments(data)[0]); task["effort"] = same("11")
        assignments(data).append(task)
    elif case == "reused-task":
        assignments(data, "S").append(copy.deepcopy(assignments(data)[0]))
    elif case == "unknown-scope-package":
        data = scope_input("unknown")
    elif case == "unknown-scope-role":
        data = scope_input("M", roles=["unknown"])
    elif case == "empty-complete":
        data = scope_input("S", roles=["FE"])
    elif case == "na-with-work":
        data["coverage"]["MVP"]["work"] = "NOT_APPLICABLE"
    elif case == "reported-partial":
        data["coverage"]["MVP"]["work"] = "PARTIAL"
        data["reported"] = {"MVP": {"B": {"low": "14"}}}
    elif case == "missing-high":
        assignments(data)[0]["effort"].pop("high")
    else:
        data["request"]["package_ids"] = ["M"]
    cli(data, error=error)


@pytest.mark.parametrize("permission", ["TURN:3", "AUTHORIZED: TURN:0", "AUTHORIZED: FILE:notes.md:01", "ASSUMED: permission granted", "AUTHORIZED: UNKNOWN"])
def test_mixed_price_requires_separate_authorization_locator(cli, permission):
    data = select_tiers("MVP")
    data["pricing"] = {"mode": "mixed", "tax_basis": "EXCLUDED", "rates": {},
                       "fallback": {"kind": "fixed", "value": atom("900")},
                       "fallback_roles": ["PM"], "permission_source": permission}
    cli(data, error="pricing.permission_source")


@pytest.mark.parametrize("case,error", [
    ("duplicate-account", "duplicate active account"), ("conflicting-ID", "fees: conflicting ID"),
    ("interface-in-A", "interface-only fee"), ("link-outside-target", "linked work not in fee target"),
    ("extra-target", "fees.entry.targets"), ("old-version", "scope version"),
    ("recurring-deployment", "deployment must be one-time"), ("once-count", "period_count requires recurring"),
    ("tax-basis", "inconsistent separate tax"), ("bad-currency", "invalid currency"),
    ("no-included-link", "included fee requires work link"), ("false-na", "conflicts with applicable quoted fees"),
    ("empty-complete", "no independent fees"), ("quantity-na-mismatch", "inconsistent fee applicability"),
])
def test_reject_invalid_fee_accounts_targets_and_basis(cli, case, error):
    data = select_tiers("MVP")
    data["coverage"]["MVP"]["external"] = "COMPLETE"
    row = fee("charge")
    data["fees"] = [row]
    if case == "duplicate-account":
        data["fees"].append(fee("different", account_id="charge"))
    elif case == "conflicting-ID":
        data["fees"].append(fee("charge", amount="55"))
    elif case == "interface-in-A":
        row["interface_only"] = True
    elif case == "link-outside-target":
        row["work_package_ids"] = ["I"]
    elif case == "extra-target":
        row["targets"] = ["MVP", "FullB"]
    elif case == "old-version":
        row["scope_version"] = "scope-1"
    elif case == "recurring-deployment":
        row.update(category="deployment", period="month")
    elif case == "once-count":
        row["period_count"] = same("2")
    elif case == "tax-basis":
        row["category"] = "tax"
    elif case == "bad-currency":
        row["currency"] = "cny"
    elif case == "no-included-link":
        row["disposition"] = "included_in_labor"
    elif case == "false-na":
        data["coverage"]["MVP"]["external"] = "NOT_APPLICABLE"
    elif case == "empty-complete":
        data["fees"] = []
    else:
        row["calculation"] = {"mode": "quantity_price", "unit": "item",
                              "quantity": {s: na() for s in SIDES}, "unit_price": same("1")}
    cli(data, error=error)


def test_exact_decimal_above_default_precision_with_fraction_oracle(cli):
    data = scope_input("M", roles=["FE"])
    first, second = assignments(data)[2:]
    large = "123456789012345678901234567890123456789.1234567890123456789"
    tiny = "0.000000000000000000000000000000000000000000000000000000001"
    risk = "0.123456789012345678901234567890123456789"
    price = "98765432109876543210.01234567890123456789"
    first["effort"], second["effort"] = same(large), same(tiny)
    data["buffers"]["default"] = same(risk)
    data["pricing"]["rate"] = atom(price)
    data["coverage"]["slice"]["external"] = "COMPLETE"
    data["fees"] = [fee("tiny-extra", ("slice",), tiny)]
    target = cli(data)["results"]["slice"]
    base = Fraction(large) + Fraction(tiny)
    reserve = base * Fraction(risk)
    labor = (base + reserve) * Fraction(price)
    metric(target["B"]["low"], "COMPLETE", base)
    metric(target["R"]["low"], "COMPLETE", reserve)
    metric(target["E"]["low"], "COMPLETE", base + reserve)
    metric(target["labor"]["low"], "COMPLETE", labor)
    metric(target["one_time_total"]["low"], "COMPLETE", labor + Fraction(tiny))


def test_reject_precision_budget_and_duplicate_json_fields(cli):
    data = select_tiers("MVP")
    assignments(data)[0]["effort"]["low"]["value"] = "1e-100001"
    cli(data, error="precision budget exceeded")
    cli(b'{"schema_version":"2.0","schema_version":"2.0"}', error="duplicate JSON object field")


@pytest.mark.parametrize("five", [False, True], ids=["legacy-four", "legacy-five"])
def test_unversioned_cli_preserves_legacy_outputs(cli, five):
    # Distinct small legacy case, not the new v2 schema or historical output.
    roles = ("FE", "BE", "DB", "QA")
    packages = []
    for index, p in enumerate(("M", "S", "F", "I"), 1):
        row = {"id": p, "function": "Synthetic " + p, "source": "SYNTHETIC independent example",
               "scope_version": "legacy", "roles": {r: {"low": str(index), "high": str(index + 1)} for r in roles}}
        if five:
            row["membership"] = [t for t, members in PLANS.items() if p in members]
        else:
            row.update(tier=("MVP", "Standard", "FullA", "FullB")[index - 1], new=index != 1)
        packages.append(row)
    data = {"scope_version": "legacy", "work_packages": packages,
            "buffers": {"low": "0.1", "high": "0.2", "source": "SYNTHETIC independent risk"},
            "pricing": {"mode": "fixed", "unit_price": "1250", "source": "SYNTHETIC independent price"},
            "outside_fees": {"status": "unknown"}}
    expected = PLANS if five else {"MVP": ("M",), "Standard": ("M", "S"), "FullA": ("M", "S", "F"), "FullB": ("M", "S", "F", "I")}
    result = cli(data)
    assert "schema_version" not in result and "results" not in result
    assert set(result["tiers"]) == set(expected)
    for tier, members in expected.items():
        row = result["tiers"][tier]
        assert set(row["ids"]) == set(members)
        for side, increment, risk in (("low", 0, Fraction("0.1")), ("high", 1, Fraction("0.2"))):
            base = 4 * sum({"M": 1, "S": 2, "F": 3, "I": 4}[p] + increment for p in members)
            exact(row["B"][side], base)
            exact(row["R"][side], base * risk)
            exact(row["E"][side], base * (1 + risk))
            exact(row["labor_rmb"][side], base * (1 + risk) * 1250)
        assert row["complete_project_total_rmb"] is None
    assert result["labor_is_complete_total"] is False
