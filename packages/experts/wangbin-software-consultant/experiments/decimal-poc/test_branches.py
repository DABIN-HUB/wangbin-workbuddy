"""Five-plan synthetic contract, negative CLI and package provenance regression."""
import copy
from decimal import Decimal
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from estimator import estimate

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixture_branches_synthetic.json"
ROLES = ("FE", "BE", "DB", "QA")
PLAN = ("MVP", "StandardA", "StandardB", "FullA", "FullB")


class BranchTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def fails(self, marker):
        with self.assertRaisesRegex(ValueError, marker):
            estimate(self.data)

    def test_five_sets_and_exact_amounts(self):
        result = estimate(self.data)
        expected = {"MVP": ("16", "26"), "StandardA": ("30", "52"),
                    "StandardB": ("37", "63"), "FullA": ("36", "62"),
                    "FullB": ("43", "73")}
        self.assertEqual(tuple(result["tiers"]), PLAN)
        for plan, (lo, hi) in expected.items():
            tier = result["tiers"][plan]
            self.assertEqual(tier["B"], {"low": lo, "high": hi})
            for side in ("low", "high"):
                rows = [r for r in result["rows"] if r["id"] in tier["ids"]]
                self.assertEqual(sum(Decimal(r["row"][side]) for r in rows), Decimal(tier["B"][side]))
                for role in ROLES:
                    self.assertEqual(sum(Decimal(r["roles"][role][side]) for r in rows),
                                     Decimal(tier["roles"][role][side]))
                self.assertEqual(sum(Decimal(tier["roles"][role][side]) for role in ROLES), Decimal(tier["B"][side]))
                self.assertEqual(Decimal(tier["R"][side]), Decimal(tier["B"][side]) * Decimal(self.data["buffers"][side]))
                self.assertEqual(Decimal(tier["E"][side]), Decimal(tier["B"][side]) + Decimal(tier["R"][side]))
                self.assertEqual(Decimal(tier["labor_rmb"][side]), Decimal(tier["E"][side]) * 1200)
                self.assertIsNone(tier["complete_project_total_rmb"])
        self.assertEqual(result["tiers"]["FullB"]["delta_ids"], ["I1"])
        self.assertNotIn("I1", result["tiers"]["FullA"]["ids"])
        self.assertNotIn("I1", result["tiers"]["StandardA"]["ids"])
        self.assertEqual(result["tiers"]["StandardB"]["delta_ids"], ["I1"])
        self.assertEqual(result["tiers"]["FullA"]["delta_ids"], ["C1"])
        self.assertEqual(result["tiers"]["FullB"]["ids"].count("I1"), 1)

    def test_identical_replay(self):
        original = estimate(self.data)
        self.data["work_packages"].append(copy.deepcopy(self.data["work_packages"][-1]))
        self.assertEqual(original, estimate(self.data))

    def test_conflict(self):
        row = copy.deepcopy(self.data["work_packages"][-1]); row["source"] = "ASSUMED changed"
        self.data["work_packages"].append(row)
        self.fails("conflicting work package")

    def test_invalid_membership(self):
        self.data["work_packages"][-2]["membership"] = ["FullB", "FullB"]
        self.fails("duplicate plan")

    def test_missing_interface_branch(self):
        self.data["work_packages"][-2]["membership"] = ["FullB"]
        self.fails("inconsistent")

    def test_legacy_tier_conflicts(self):
        self.data["work_packages"][0]["tier"] = "MVP"
        self.fails("unknown=.*tier")

    def test_version(self):
        self.data["work_packages"][0]["scope_version"] = "old"
        self.fails("scope version mismatch")

    def test_reported_mismatch(self):
        tier = estimate(self.data)["tiers"]["StandardA"]
        self.data["reported"] = {"StandardA": {"roles": copy.deepcopy(tier["roles"]), "B": copy.deepcopy(tier["B"])}}
        self.data["reported"]["StandardA"]["roles"]["BE"]["low"] = "10"
        self.fails("StandardA BE low")

    def test_refuse(self):
        self.data["pricing"] = {"mode": "refused"}
        result = estimate(self.data)
        self.assertIsNone(result["currency_labor_only"])
        for tier in result["tiers"].values():
            self.assertIsNone(tier["labor_rmb"])

    def test_reference(self):
        self.data["pricing"] = {"mode": "reference"}
        result = estimate(self.data)
        self.assertEqual(result["tiers"]["MVP"]["labor_rmb"], {"low": "17600.00", "high": "46800.00"})
        self.assertIn("并非实时市场行情", result["reference_notice"])

    def test_missing_role(self):
        del self.data["work_packages"][0]["roles"]["FE"]
        self.fails("missing=.*FE")

    def test_nonfinite(self):
        for value in ("NaN", "Infinity", "-Infinity", "-1", "unknown"):
            with self.subTest(value=value):
                self.data["work_packages"][0]["roles"]["FE"]["low"] = value
                self.fails("out of range|invalid decimal")

    def test_invalid_buffer_and_price(self):
        self.data["buffers"]["high"] = "Infinity"; self.fails("out of range")
        self.data["buffers"]["high"] = "0.2"
        self.data["pricing"] = {"mode": "roles", "source": "ASSUMED"}; self.fails("pricing.mode")

    def test_missing_source(self):
        self.data["work_packages"][0]["source"] = "confirmed"
        self.fails("traceable")

    def test_cli_exclusive_output_and_input(self):
        with tempfile.TemporaryDirectory(dir=os.environ["POC_SCRATCH"]) as directory:
            target = Path(directory) / "result.json"
            command = [sys.executable, str(HERE / "estimator.py"), str(FIXTURE), "-o", str(target)]
            first = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            result = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(result["tiers"]["FullB"]["B"]["low"], "43")
            old = target.read_bytes()
            repeated = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(repeated.returncode, 2)
            self.assertEqual(target.read_bytes(), old)
            same = subprocess.run([sys.executable, str(HERE / "estimator.py"), str(FIXTURE), "-o", str(FIXTURE)], capture_output=True, text=True)
            self.assertEqual(same.returncode, 2)

    def test_cli_negative_json(self):
        with tempfile.TemporaryDirectory(dir=os.environ["POC_SCRATCH"]) as directory:
            root = Path(directory)
            bad = root / "bad.json"; bad.write_text('{"private secret":NaN}', encoding="utf-8")
            output = root / "bad-output.json"
            run = subprocess.run([sys.executable, str(HERE / "estimator.py"), str(bad), "-o", str(output)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertNotIn("private secret", run.stderr)
            self.assertFalse(output.exists())

    def test_cli_symlink(self):
        with tempfile.TemporaryDirectory(dir=os.environ["POC_SCRATCH"]) as directory:
            root = Path(directory)
            output = root / "bad-output.json"
            link = root / "link.json"
            try:
                link.symlink_to(FIXTURE)
            except OSError:
                self.skipTest("Windows symlink permission unavailable; not a PASS")
            run = subprocess.run([sys.executable, str(HERE / "estimator.py"), str(link), "-o", str(output)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
