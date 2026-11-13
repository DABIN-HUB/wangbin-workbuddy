"""Focused negative source and pricing-mode regression; original fixtures stay immutable."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from check_frozen_source import compare
from reconcile_model_receipt import check

HERE = Path(__file__).resolve().parent
EVIDENCE = Path("F:/ideaWorkSpace/wangbin-workbuddy-delivery/experts/wangbin-software-consultant/calc-integration-01")
V1 = EVIDENCE / "WB-02-input.json"
SCRIPT = HERE / "skill-preview/wangbin-estimate-calculator/scripts/estimator.py"
SCRATCH = Path("C:/Users/wangbin/AppData/Local/hermes/profiles/wb-developer/cache/scratch")


class SourceAndPrice(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads(V1.read_text(encoding="utf-8"))

    def request(self):
        return copy.deepcopy(self.original)

    def test_unchanged(self):
        self.assertEqual(compare(self.request(), "WB-05-unchanged", V1), [])

    def test_all_versions_jointly_changed(self):
        item = self.request()
        item.update(scope_version="synthetic-v3", previous_scope_version="synthetic-v2", scope_changed=True)
        for row in item["work_packages"]:
            row["scope_version"] = "synthetic-v3"
        self.assertIn("SOURCE scope_version", str(compare(item, "WB-02", V1)))

    def test_same_label_changed_payload_and_effort(self):
        for field, change in (("function", "new function"), ("source", "new origin"),
                              ("membership", ["MVP"]), ("roles", None)):
            with self.subTest(field=field):
                item = self.request()
                if field == "roles":
                    item["work_packages"][0]["roles"]["QA"]["low"] = "99"
                else:
                    item["work_packages"][0][field] = change
                self.assertTrue(compare(item, "WB-02", V1))

    def test_unapproved_deletion(self):
        item = self.request()
        item["work_packages"] = [r for r in item["work_packages"] if r["id"] != "S2"]
        self.assertTrue(compare(item, "WB-05-unchanged", V1))

    def test_authorized_v2_only_deletion(self):
        item = json.loads((EVIDENCE / "WB-05-input.json").read_text(encoding="utf-8"))
        self.assertEqual(compare(item, "WB-05-changed", V1, "delete-S2-v2"), [])
        self.assertTrue(compare(item, "WB-05-changed", V1, "none"))
        self.assertTrue(compare(item, "WB-05-unchanged", V1))

    def test_approved_price_only(self):
        for case in ("WB-02", "WB-03", "WB-04"):
            with self.subTest(case=case):
                request = EVIDENCE / (case + "-input.json")
                # Frozen old receipts retain their old script identity; do not rewrite them.
                historical = EVIDENCE / (case + "-expected.json")
                self.assertTrue(any("script_sha256" in error for error in check(request, historical, case=case, anchor=V1)["errors"]))
                with tempfile.TemporaryDirectory() as temporary:
                    receipt = Path(temporary) / "receipt.json"
                    run = subprocess.run([sys.executable, str(SCRIPT), str(request), "-o", str(receipt)], capture_output=True)
                    self.assertEqual(run.returncode, 0, run.stderr)
                    self.assertEqual(check(request, receipt, case=case, anchor=V1)["errors"], [])
        item = self.request()
        item["pricing"]["unit_price"] = "1350"
        self.assertTrue(compare(item, "WB-02", V1))

    def test_reference_and_refused_mode(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
            base = Path(temporary)
            for mode, case in (("reference", "REFERENCE-v1"), ("refused", "WB-04")):
                with self.subTest(mode=mode):
                    item = self.request()
                    item["pricing"] = {"mode": mode}
                    source = base / (mode + ".json")
                    receipt = base / (mode + "-receipt.json")
                    source.write_text(json.dumps(item), encoding="utf-8")
                    process = subprocess.run([sys.executable, "-B", str(SCRIPT), str(source), "-o", str(receipt)], capture_output=True)
                    self.assertEqual(process.returncode, 0, process.stderr)
                    self.assertEqual(check(source, receipt, case=case, anchor=V1)["errors"], [])
                    got = json.loads(receipt.read_text(encoding="utf-8"))
                    if mode == "refused":
                        self.assertIsNone(got["currency_labor_only"])
                        self.assertTrue(all(tier["labor_rmb"] is None for tier in got["tiers"].values()))
                    else:
                        self.assertEqual(got["tiers"]["MVP"]["labor_rmb"], {"low": "17600.00", "high": "46800.00"})

    def test_wrong_anchor(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
            fake = Path(temporary) / "anchor.json"
            fake.write_text(json.dumps(self.request()), encoding="utf-8")
            self.assertTrue(compare(self.request(), "WB-02", fake))

    def test_reject_non_five_scheme(self):
        with tempfile.TemporaryDirectory(dir=SCRATCH) as temporary:
            receipt = json.loads((EVIDENCE / "WB-02-expected.json").read_text(encoding="utf-8"))
            del receipt["tiers"]["StandardB"]
            path = Path(temporary) / "receipt.json"
            path.write_text(json.dumps(receipt), encoding="utf-8")
            report = check(V1, path, case="WB-02", anchor=V1)
            self.assertIn("NOT_APPLICABLE", str(report["errors"]))


if __name__ == "__main__":
    unittest.main()
