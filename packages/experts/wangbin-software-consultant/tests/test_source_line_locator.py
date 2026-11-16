"""File locators are accepted as opaque strings, not opened or verified."""
import json
from pathlib import Path
import subprocess
import sys
import pytest

SOURCE = Path(__file__).resolve().parents[1]
SCRIPT = SOURCE / "skills/wangbin-estimate-calculator/scripts/estimator.py"

@pytest.mark.parametrize("locator,valid", [
    ("pipeline confirmed",False),("return confirmed",False),("已确认话轮",False),("turn 0",False),("turn -1",False),("requirements.md line unknown",False),("第0话轮",False),("ASSUMED_CONDITIONAL interface",True),("用户第2轮确认",True),("话轮 2",True),("requirements.md:42", True), ("需求说明.md:1", True),
    ("requirements.md line 42", True), ("turn 2", True),
    ("第2话轮", True), ("ASSUMED example", True), ("SYNTHETIC fixture", True),
    ("已确认", False), ("requirements.md:0", False),
    ("requirements.md:-1", False), ("requirements.md:abc", False),
    ("requirements.md:1.5", False), (":42", False),
    ("   :42", False), ("requirements.md:01", False),
])
def test_formal_five_plan_locator_cli(tmp_path, locator, valid):
    data = json.loads((SOURCE / "tests/fixtures/precision-boundary.input.json").read_bytes())
    for row in data["work_packages"]:
        row["source"] = locator
    request = tmp_path / "request.json"
    request.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    receipt = tmp_path / "receipt.json"
    result = subprocess.run([sys.executable, "-B", str(SCRIPT), str(request), "-o", str(receipt)], capture_output=True)
    assert result.returncode == (0 if valid else 2), result.stderr
    assert receipt.exists() is valid
    if valid:
        got = json.loads(receipt.read_bytes())
        assert all(row["source"] == locator for row in got["rows"])
        assert got["tiers"]["MVP"]["B"]["low"] == "123456789012345678901234567893.4"
