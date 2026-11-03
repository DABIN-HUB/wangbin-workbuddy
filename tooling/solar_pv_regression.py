"""Run scoped solar-PV regressions and certify L2 coverage from a final L3 receipt.

This is execution/evidence tooling, not a change to any test or financial contract.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
L2 = (
    "tests/solar-pv/test_phase3e_price_selector.py",
    "tests/solar-pv/test_phase3e_candidate_replay.py",
    "tests/solar-pv/test_phase3e_financial_candidate_replay.py",
    "tests/solar-pv/test_phase3e_terminal_binding.py",
    "tests/solar-pv/test_phase3e_terminal_npv.py",
    "tests/solar-pv/test_phase3e_break_even_project_npv.py",
    "tests/solar-pv/test_phase3e_break_even_project_session.py",
)
FAST = (
    "tests/solar-pv/test_phase3e_financial_metrics.py",
    "tests/solar-pv/test_phase3e_irr_roots.py",
    "tests/solar-pv/test_method_configuration.py",
)
# The whole tracked executable/test/config surface, not just the modules selected for a run.
INPUT_PREFIXES = ("services/", "tests/", "tooling/", "packages/", "products/", "docs/solar-pv/")
INPUT_FILES = {"pyproject.toml", "requirements.txt", "assets/config.yaml"}
MAX_XML_BYTES = 20_000_000
MAX_CASES = 15_000
MAX_COLLECTION_BYTES = 2_000_000
HASH_RE = re.compile(r"[0-9a-f]{64}\Z")


class GateError(Exception):
    """The evidence is insufficient to claim coverage."""


def _git(*args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True)
    return result.stdout.strip() if args == ("rev-parse", "HEAD") else result.stdout


def _inputs() -> dict[str, str]:
    names = set()
    for args in (("ls-files", "-z"), ("ls-files", "--others", "--exclude-standard", "-z")):
        names.update(os.fsdecode(item) for item in _git(*args).split(b"\0") if item)
    result = {}
    for name in sorted(names):
        if name not in INPUT_FILES and not name.startswith(INPUT_PREFIXES):
            continue
        path = ROOT / name
        if not path.is_file() or path.is_symlink() or path.resolve().is_relative_to(ROOT.resolve()) is False:
            raise GateError(f"missing, linked, or escaped input: {name}")
        result[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def _identity() -> dict:
    inputs = _inputs()
    canonical = json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()
    return {"head": _git("rev-parse", "HEAD").decode(),
            "input_sha256": hashlib.sha256(canonical).hexdigest(),
            "input_count": len(inputs), "inputs": inputs}


def _conditions() -> dict:
    packages = sorted((d.metadata["Name"].lower(), d.version)
                      for d in importlib.metadata.distributions() if d.metadata.get("Name"))
    env_keys = ("PYTHONHASHSEED", "PYTEST_ADDOPTS", "PYTEST_PLUGINS",
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD", "CI", "TZ", "LANG", "LC_ALL", "LC_CTYPE", "PATH")
    return {"platform": platform.platform(), "python": sys.executable,
            "python_version": sys.version, "pytest": importlib.metadata.version("pytest"),
            "packages_sha256": hashlib.sha256(json.dumps(packages).encode()).hexdigest(),
            "env_sha256": {key: hashlib.sha256(os.environ[key].encode()).hexdigest()
                           if key in os.environ else None for key in env_keys},
            "pythonpath": os.pathsep.join(str(ROOT / path) for path in
                                      ("services/solar-pv-engine/src", "services/document-engine/src", "")),
            "temp_policy": "distinct_sibling_roots_under_private_evidence_directory"}


def _junit(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size > MAX_XML_BYTES:
        raise GateError("missing or oversized JUnit XML")
    raw = path.read_bytes()
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise GateError("JUnit XML contains a DTD or entity")
    tree = ET.fromstring(raw)
    suites = [tree] if tree.tag == "testsuite" else list(tree)
    if not suites or tree.tag not in {"testsuites", "testsuite"} or any(s.tag != "testsuite" for s in suites):
        raise GateError("invalid JUnit suite structure")
    cases: dict[str, dict] = {}
    for suite in suites:
        children = list(suite)
        if len(children) > MAX_CASES or int(suite.get("tests", "-1")) != sum(c.tag == "testcase" for c in children):
            raise GateError("JUnit suite count mismatch")
        for case in children:
            if case.tag != "testcase" or not case.get("classname") or not case.get("name"):
                raise GateError("unexpected JUnit case")
            name = case.get("classname") + "::" + case.get("name")
            if name in cases or len(cases) >= MAX_CASES:
                raise GateError("duplicate or excessive JUnit case IDs")
            outcomes = [child for child in case if child.tag in {"skipped", "failure", "error"}]
            if len(outcomes) > 1:
                raise GateError("ambiguous JUnit outcome")
            outcome = outcomes[0].tag if outcomes else "passed"
            cases[name] = {"outcome": outcome,
                           "reason": (outcomes[0].get("message") or "") if outcomes else ""}
        for key, tag in (("failures", "failure"), ("errors", "error"), ("skipped", "skipped")):
            count = sum(any(child.tag == tag for child in case) for case in children if case.tag == "testcase")
            if int(suite.get(key, "-1")) != count:
                raise GateError(f"JUnit {key} count mismatch")
    return {"sha256": hashlib.sha256(raw).hexdigest(), "cases": cases,
            "skips": {name: case["reason"] for name, case in cases.items()
                      if case["outcome"] == "skipped"},
            "counts": {key: sum(v["outcome"] == key for v in cases.values())
                       for key in ("passed", "skipped", "failure", "error")}}


def _node_id(junit_id: str) -> str:
    module, separator, test = junit_id.partition("::")
    if not separator or not module.startswith("tests.solar-pv."):
        raise GateError(f"unexpected solar JUnit ID: {junit_id}")
    return "tests/solar-pv/" + module.removeprefix("tests.solar-pv.") + ".py::" + test


def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _receipt(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "solar-pv-regression-receipt/1" or data.get("exit_code") != 0:
        raise GateError("receipt invalid or execution failed")
    if data.get("identity_before") != data.get("identity_after"):
        raise GateError("inputs changed during run")
    return data


def _selection(tier: str, selected: list[str]) -> tuple[str, ...]:
    if tier in {"affected", "e2e"}:
        if not selected:
            raise GateError("affected/e2e requires explicit --select test path or node ID")
        for item in selected:
            path = item.split("::", 1)[0]
            if (not path.startswith("tests/solar-pv/") or not path.endswith(".py")
                    or ".." in path or not (ROOT / path).is_file() or item.startswith("-")):
                raise GateError(f"invalid test selection: {item}")
        return tuple(selected)
    if selected:
        raise GateError("--select is only allowed for affected/e2e")
    return {"fast": FAST, "collect-l2": L2,
            "l3-solar": ("tests/solar-pv",),
            "l3-workbuddy": ("tests", "--ignore=tests/solar-pv")}[tier]


def _run(args: argparse.Namespace) -> int:
    out = args.out.resolve()
    if out.exists() and any(out.iterdir()):
        raise GateError("evidence directory must be a fresh, empty directory")
    if out == ROOT or ROOT in out.parents:
        raise GateError("evidence directory must be outside the repository")
    selection = _selection(args.tier, args.select)
    out.mkdir(parents=True, exist_ok=True)
    tmp = out / "workspace-tmp"
    tmp.mkdir()
    base = out / "pytest-basetemp"
    conditions = _conditions()
    identity_before = _identity()
    command = [sys.executable, "-m", "pytest", *selection, "-q", "-ra",
               f"--basetemp={base}"]
    if args.tier == "collect-l2":
        command.append("--collect-only")
    else:
        command.append(f"--junitxml={out / 'junit.xml'}")
    env = os.environ.copy()
    env.update({"TMPDIR": str(tmp), "TEMP": str(tmp), "TMP": str(tmp),
                "PYTHONPATH": conditions["pythonpath"]})
    print("Executing:", subprocess.list2cmdline(command), flush=True)
    started = time.perf_counter()
    with (out / "output.log").open("w", encoding="utf-8") as stream:
        completed = subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                                   stderr=subprocess.STDOUT, check=False)
    elapsed = round(time.perf_counter() - started, 3)
    identity_after = _identity()
    receipt = {"schema": "solar-pv-regression-receipt/1", "tier": args.tier,
               "command": command, "exit_code": completed.returncode,
               "elapsed_seconds": elapsed, "identity_before": identity_before,
               "identity_after": identity_after, "conditions": conditions,
               "scratch": {"TMPDIR": str(tmp), "basetemp": str(base)},
               "log": "output.log", "selection": selection}
    receipt["log_sha256"] = hashlib.sha256((out / "output.log").read_bytes()).hexdigest()
    if args.tier == "collect-l2":
        text = (out / "output.log").read_bytes()
        if len(text) > MAX_COLLECTION_BYTES:
            receipt["evidence_error"] = "oversized collection log"
        else:
            output = text.decode("utf-8", errors="replace")
            nodes = [line.strip() for line in output.splitlines()
                     if line.startswith("tests/solar-pv/") and "::" in line]
            receipt["collected_ids"] = nodes
            receipt["collection_reported_count"] = int(match.group(1)) if (
                match := re.search(r"(?:^|\n)(\d+) tests? collected", output)) else None
            if not nodes or len(nodes) != len(set(nodes)) or len(nodes) != receipt["collection_reported_count"]:
                receipt["evidence_error"] = "incomplete or duplicate collection"
    elif (out / "junit.xml").exists():
        try:
            summary = _junit(out / "junit.xml")
            receipt["junit"] = {"path": "junit.xml", "sha256": summary["sha256"],
                                "counts": summary["counts"], "test_count": len(summary["cases"]),
                                "skips": summary["skips"]}
        except (GateError, ValueError, ET.ParseError) as exc:
            receipt["evidence_error"] = str(exc)
    elif completed.returncode == 0:
        receipt["evidence_error"] = "successful pytest did not produce JUnit"
    receipt["gate_exit_code"] = completed.returncode or (2 if receipt.get("evidence_error") else 0)
    _write(out / "receipt.json", receipt)
    print(f"pytest_exit={completed.returncode}; gate_exit={receipt['gate_exit_code']}; "
          f"elapsed={elapsed}s; receipt={out / 'receipt.json'}")
    return receipt["gate_exit_code"]


def _verify(args: argparse.Namespace) -> int:
    collected = _receipt(args.collection)
    solar = _receipt(args.solar)
    workbuddy = _receipt(args.workbuddy)
    if (collected["tier"], solar["tier"], workbuddy["tier"]) != (
            "collect-l2", "l3-solar", "l3-workbuddy"):
        raise GateError("incorrect receipt tiers")
    if any(item.get("gate_exit_code") != 0 or item.get("evidence_error")
           for item in (collected, solar, workbuddy)):
        raise GateError("a prerequisite evidence gate did not pass")
    if any(item["identity_before"] != solar["identity_before"] or
           item["conditions"] != solar["conditions"] for item in (collected, workbuddy)):
        raise GateError("different source/test/config identity or execution conditions")
    for receipt, path in ((collected, args.collection), (solar, args.solar), (workbuddy, args.workbuddy)):
        if receipt.get("selection") != list(_selection(receipt["tier"], [])):
            raise GateError("incorrect tier selection")
        if receipt.get("log") != "output.log" or hashlib.sha256(
                (path.parent / "output.log").read_bytes()).hexdigest() != receipt.get("log_sha256"):
            raise GateError("log identity mismatch")
        scratch = receipt.get("scratch", {})
        if not isinstance(scratch, dict) or not isinstance(scratch.get("TMPDIR"), str):
            raise GateError("missing scratch identity")
        original_root = Path(scratch["TMPDIR"]).parent
        expected_tmp, expected_base = original_root / "workspace-tmp", original_root / "pytest-basetemp"
        if (scratch != {"TMPDIR": str(expected_tmp), "basetemp": str(expected_base)} or
                expected_tmp == expected_base or original_root == ROOT or ROOT in original_root.parents):
            raise GateError("invalid or overlapping scratch directories")
        expected_command = [solar["conditions"]["python"], "-m", "pytest",
                            *_selection(receipt["tier"], []), "-q", "-ra",
                            f"--basetemp={expected_base}"]
        expected_command.append("--collect-only" if receipt["tier"] == "collect-l2"
                                else f"--junitxml={original_root / 'junit.xml'}")
        if receipt.get("command") != expected_command:
            raise GateError("execution command does not match tier policy")
    ids = collected.get("collected_ids", [])
    collection_text = (args.collection.parent / "output.log").read_text(encoding="utf-8", errors="replace")
    observed = [line.strip() for line in collection_text.splitlines()
                if line.startswith("tests/solar-pv/") and "::" in line]
    if (not ids or len(ids) != len(set(ids)) or
            len(ids) != collected.get("collection_reported_count") or
            ids != observed or
            any(not name.startswith("tests/solar-pv/") for name in ids)):
        raise GateError("incomplete, missing, or duplicate L2 collection")
    def check_junit(receipt: dict, path: Path) -> dict:
        report = receipt.get("junit", {})
        if report.get("path") != "junit.xml" or not HASH_RE.fullmatch(report.get("sha256", "")):
            raise GateError("missing JUnit identity")
        result = _junit(path.parent / "junit.xml")
        if (result["sha256"] != report["sha256"] or
                result["counts"] != report.get("counts") or
                result["skips"] != report.get("skips") or
                len(result["cases"]) != report.get("test_count")):
            raise GateError("JUnit receipt mismatch")
        if result["counts"]["failure"] or result["counts"]["error"]:
            raise GateError("JUnit contains failures or errors")
        return result
    pv = check_junit(solar, args.solar)
    wb = check_junit(workbuddy, args.workbuddy)
    if any(name.startswith("tests.solar-pv.") for name in wb["cases"]):
        raise GateError("workbuddy L3 unexpectedly includes solar cases")
    solar_by_node = {_node_id(name): case for name, case in pv["cases"].items()}
    missing = sorted(set(ids) - solar_by_node.keys())
    # Exact parameter suffixes are part of IDs. A skipped case is covered but not passed.
    if missing:
        raise GateError(f"L3 missing {len(missing)} L2 IDs: {missing[:5]}")
    covered = {name: solar_by_node[name] for name in ids}
    evidence_path = ROOT / "reports/solar-pv/phase3e-p2-4b-c-root-certification-evidence.json"
    historical = json.loads(evidence_path.read_text(encoding="utf-8"))["verification"]["l2"]
    historical_path = ROOT / historical["path"]
    if _junit(historical_path)["sha256"] != historical["sha256"]:
        raise GateError("historical L2 JUnit checksum mismatch")
    result = {"schema": "solar-pv-l2-from-l3-coverage/1", "verdict": "COVERED_WITH_SKIPS" if any(
        case["outcome"] == "skipped" for case in covered.values()) else "COVERED_ALL_PASSED",
        "identity": solar["identity_before"], "conditions": solar["conditions"],
        "l2_collected_count": len(ids), "l2_covered": covered,
        "solar_l3_junit": pv["sha256"], "solar_l3_counts": pv["counts"],
        "solar_l3_skips": pv["skips"],
        "workbuddy_l3_junit": wb["sha256"], "workbuddy_l3_counts": wb["counts"],
        "workbuddy_l3_skips": wb["skips"],
        "l2_standalone_executed": False,
        "historical_l2_seconds_avoided_if_repeated": historical["elapsed_seconds"],
        "historical_l2_junit": historical["sha256"],
        "historical_evidence_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
        "saving_basis": "P2-4B/C archived L2 elapsed; historical comparison, not a newly timed speedup",
        "receipts": [str(p.resolve()) for p in (args.collection, args.solar, args.workbuddy)]}
    if args.out:
        if args.out.exists():
            raise GateError("coverage output already exists; do not overwrite evidence")
        _write(args.out, result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def _audit_archive(args: argparse.Namespace) -> int:
    """Measure archived ID overlap only; old JUnit does not carry execution identity."""
    evidence_path = ROOT / "reports/solar-pv/phase3e-p2-4b-c-root-certification-evidence.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))["verification"]
    reports = {}
    for tier in ("l2", "solar_l3"):
        entry = evidence[tier]
        reports[tier] = _junit(ROOT / entry["path"])
        if reports[tier]["sha256"] != entry["sha256"]:
            raise GateError(f"archived {tier} JUnit checksum mismatch")
    old = {_node_id(name): outcome for name, outcome in reports["l2"]["cases"].items()}
    final = {_node_id(name): outcome for name, outcome in reports["solar_l3"]["cases"].items()}
    missing = sorted(old.keys() - final.keys())
    result = {"schema": "solar-pv-historical-id-overlap/1",
              "verdict": "HISTORICAL_ID_MATCH_ONLY" if not missing else "HISTORICAL_ID_MISSING",
              "not_a_new_l3_pass_or_current_candidate_coverage": True,
              "historical_evidence_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
              "l2_junit": reports["l2"]["sha256"], "solar_l3_junit": reports["solar_l3"]["sha256"],
              "l2_ids": len(old), "l3_ids": len(final), "missing_ids": missing,
              "l2_outcomes": reports["l2"]["counts"], "l3_outcomes": reports["solar_l3"]["counts"],
              "l2_skips": reports["l2"]["skips"],
              "l3_covered_l2": {key: final[key] for key in sorted(old.keys() & final.keys())},
              "historical_independent_l2_elapsed_seconds": evidence["l2"]["elapsed_seconds"]}
    if args.out.exists():
        raise GateError("archive audit output already exists")
    _write(args.out, result)
    print(f"historical overlap: {len(old) - len(missing)}/{len(old)}; "
          f"verdict={result['verdict']}; output={args.out}")
    return 0 if not missing else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    run = sub.add_parser("run", help="run one tier and save immutable receipt/JUnit")
    run.add_argument("--tier", choices=("fast", "affected", "e2e", "collect-l2", "l3-solar", "l3-workbuddy"), required=True)
    run.add_argument("--out", type=Path, required=True, help="fresh external evidence directory")
    run.add_argument("--select", action="append", default=[], help="explicit affected/e2e test path or node ID")
    verify = sub.add_parser("verify", help="use final L3 JUnit as L2 coverage evidence")
    for key in ("collection", "solar", "workbuddy"):
        verify.add_argument(f"--{key}", type=Path, required=True, help="receipt.json from the matching tier")
    verify.add_argument("--out", type=Path, help="new, non-existing coverage receipt path")
    audit = sub.add_parser("audit-archive", help="inspect old L2/L3 ID overlap without asserting current coverage")
    audit.add_argument("--out", type=Path, required=True, help="new output path outside the repo")
    args = parser.parse_args(argv)
    try:
        if args.action == "run":
            return _run(args)
        return _verify(args) if args.action == "verify" else _audit_archive(args)
    except (GateError, OSError, ValueError, ET.ParseError, subprocess.CalledProcessError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
