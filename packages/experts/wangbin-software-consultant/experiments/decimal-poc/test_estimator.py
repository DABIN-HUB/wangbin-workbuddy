"""Focused stdlib tests; R5 input is an optional external controlled evidence file."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from estimator import estimate

HERE = Path(__file__).resolve().parent


class EstimatorTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((HERE / "fixture_synthetic.json").read_text(encoding="utf-8"))

    def fails(self, message):
        with self.assertRaisesRegex(ValueError, message):
            estimate(self.data)

    def test_row_roles(self):
        self.assertEqual(estimate(self.data)["rows"][0]["row"], {"low": "7", "high": "12"})

    def test_tier_reconciliation(self):
        result = estimate(self.data)
        for tier in result["tiers"].values():
            for side in ("low", "high"):
                self.assertEqual(sum(int(tier["roles"][r][side]) for r in ("FE", "BE", "DB", "QA")), int(tier["B"][side]))

    def test_all_four_cumulative_tiers(self):
        self.assertEqual([estimate(self.data)["tiers"][t]["B"]["low"] for t in ("MVP", "Standard", "FullA", "FullB")], ["7", "12", "18", "25"])

    def test_delta_columns(self):
        self.assertEqual(estimate(self.data)["tiers"]["FullB"]["delta_roles"]["BE"], {"low": "3", "high": "5"})

    def test_duplicate_identical_not_charged(self):
        original = estimate(self.data)
        self.data["work_packages"].append(copy.deepcopy(self.data["work_packages"][0]))
        self.assertEqual(estimate(self.data), original)

    def test_duplicate_conflicting_rejected(self):
        row = copy.deepcopy(self.data["work_packages"][0]); row["roles"]["FE"]["low"] = "3"
        self.data["work_packages"].append(row)
        self.fails("conflicting work package ID")

    def test_negative(self):
        self.data["work_packages"][0]["roles"]["FE"]["low"] = "-1"
        self.fails("out of range")

    def test_inverted(self):
        self.data["work_packages"][0]["roles"]["FE"]["low"] = "4"
        self.fails("low exceeds high")

    def test_unknown_not_zero(self):
        self.data["work_packages"][0]["roles"]["FE"]["low"] = "unknown"
        self.fails("invalid decimal")

    def test_missing_role(self):
        del self.data["work_packages"][0]["roles"]["QA"]
        self.fails("missing=.*QA")

    def test_unknown_field(self):
        self.data["work_packages"][0]["unexpected"] = 1
        self.fails("unknown=.*unexpected")

    def test_independent_buffers(self):
        tier = estimate(self.data)["tiers"]["MVP"]
        self.assertEqual((tier["R"], tier["E"]), ({"low": "0.70", "high": "2.40"}, {"low": "7.70", "high": "14.40"}))

    def test_reference_price(self):
        self.assertEqual(estimate(self.data)["tiers"]["MVP"]["labor_rmb"], {"low": "7700.00", "high": "21600.00"})

    def test_fixed_overrides_reference(self):
        self.data["pricing"] = {"mode": "fixed", "unit_price": "1200", "source": "fictional user"}
        self.assertEqual(estimate(self.data)["tiers"]["MVP"]["labor_rmb"], {"low": "9240.00", "high": "17280.00"})

    def test_price_only_change_preserves_effort(self):
        old = estimate(self.data)["tiers"]["MVP"]
        self.data["pricing"] = {"mode": "fixed", "unit_price": "1200", "source": "fictional user"}
        new = estimate(self.data)["tiers"]["MVP"]
        self.assertEqual((old["B"], old["R"], old["E"]), (new["B"], new["R"], new["E"]))

    def test_refusal_no_rmb(self):
        self.data["pricing"] = {"mode": "refused"}
        self.assertIsNone(estimate(self.data)["tiers"]["MVP"]["labor_rmb"])

    def test_unknown_third_party_no_total(self):
        result = estimate(self.data)
        self.assertIsNone(result["tiers"]["MVP"]["complete_project_total_rmb"])
        self.assertIn("UNKNOWN", result["outside_fees"])

    def test_synthetic_reported_role_mismatch(self):
        result = estimate(self.data)["tiers"]["Standard"]
        self.data["reported"] = {"Standard": {"roles": copy.deepcopy(result["roles"]), "B": copy.deepcopy(result["B"])}}
        self.data["reported"]["Standard"]["roles"]["BE"]["low"] = "0"
        self.fails("Standard BE low")

    def test_reported_true_match(self):
        result = estimate(self.data)["tiers"]["Standard"]
        self.data["reported"] = {"Standard": {"roles": copy.deepcopy(result["roles"]), "B": copy.deepcopy(result["B"])}}
        self.assertIn("tiers", estimate(self.data))

    def test_scope_change_requires_new_version(self):
        self.data["scope_changed"] = True
        self.data["previous_scope_version"] = "fiction-v1"
        self.fails("new version")

    def test_version_mismatch(self):
        self.data["work_packages"][0]["scope_version"] = "older"
        self.fails("scope version mismatch")

    def test_repeat_deterministic(self):
        self.assertEqual(estimate(self.data), estimate(copy.deepcopy(self.data)))

    def test_s30_real_transcription_detects_reported_mismatch(self):
        source = os.environ.get("S30_POC_INPUT")
        raw = os.environ.get("S30_POC_RAW")
        if not source or not raw:
            self.skipTest("set S30_POC_INPUT and S30_POC_RAW to controlled original evidence")
        content = Path(raw).read_bytes()
        self.assertEqual(hashlib.sha256(content).hexdigest(), "18949697dbff9a62cfaf46f31e39f4e569b81b34adb5766fb2d3027e2d6f81fb")
        lines = content.decode("utf-8").splitlines()
        data = json.loads(Path(source).read_text(encoding="utf-8"))
        for row in data["work_packages"]:
            line_no = int(row["source"].removeprefix("stdout.bin line "))
            self.assertIn("| " + row["id"] + "／", lines[line_no - 1])
            cells = [cell.strip() for cell in lines[line_no - 1].split("|")[1:-1]]
            for role, cell in zip(("FE", "BE", "DB", "QA"), cells[2:6]):
                low_high = cell.replace("～", "~").split("~")
                self.assertEqual([row["roles"][role][side] for side in ("low", "high")],
                                 low_high if len(low_high) == 2 else low_high * 2)
        self.assertIn("6～10／10～17／5～9／5～9", lines[27])
        result = estimate(data)["tiers"]["Standard"]
        self.assertEqual(result["B"], {"low": "30", "high": "52"})
        self.assertEqual([result["roles"][r]["low"] for r in ("FE", "BE", "DB", "QA")], ["6", "12", "6", "6"])
        data["reported"] = {"Standard": {"roles": {"FE": {"low": "6", "high": "10"}, "BE": {"low": "10", "high": "17"}, "DB": {"low": "5", "high": "9"}, "QA": {"low": "5", "high": "9"}}, "B": {"low": "30", "high": "52"}}}
        with self.assertRaisesRegex(ValueError, "Standard BE low"):
            estimate(data)

    def test_cli_valid_and_invalid_json_exit_codes(self):
        with tempfile.TemporaryDirectory(dir=os.environ["POC_SCRATCH"]) as directory:
            output = Path(directory) / "output.json"
            good = subprocess.run([sys.executable, str(HERE / "estimator.py"), str(HERE / "fixture_synthetic.json"), "-o", str(output)], capture_output=True, text=True)
            self.assertEqual(good.returncode, 0, good.stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["scope_version"], "fiction-v1")
            bad = Path(directory) / "bad.json"; bad.write_text("{oops", encoding="utf-8")
            failure = subprocess.run([sys.executable, str(HERE / "estimator.py"), str(bad), "-o", str(output)], capture_output=True, text=True)
            self.assertEqual(failure.returncode, 2)
            self.assertIn("INPUT_ERROR", failure.stderr)

    def test_cli_missing_input_exit_code(self):
        with tempfile.TemporaryDirectory(dir=os.environ["POC_SCRATCH"]) as directory:
            result = subprocess.run([sys.executable, str(HERE / "estimator.py"), str(Path(directory) / "missing.json"), "-o", str(Path(directory) / "out.json")], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
