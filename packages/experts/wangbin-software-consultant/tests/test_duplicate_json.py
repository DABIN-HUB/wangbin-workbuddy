"""Ambiguous raw JSON cannot silently replace refusal with a price."""
import json
from pathlib import Path
import subprocess
import sys
import pytest
SOURCE=Path(__file__).resolve().parents[1]
@pytest.mark.parametrize("members,rc", [
 ('"mode":"refused","mode":"fixed","unit_price":"1000","source":"SYNTHETIC price"',2),
 ('"mode":"fixed","unit_price":"1000","source":"SYNTHETIC price","mode":"refused"',2),
 ('"mode":"refused","mode":"refused"',2),
 ('"mode":"refused"',0),
 ('"mode":"fixed","unit_price":"1000","source":"SYNTHETIC price"',0)])
def test_raw_duplicate_pricing_cli(tmp_path,members,rc):
    data=json.loads((SOURCE/"tests/fixtures/precision-boundary.input.json").read_bytes())
    data["pricing"]={"mode":"refused"}
    payload=json.dumps(data).replace('"mode": "refused"',members)
    request=tmp_path/"input.json";request.write_text(payload,encoding="utf-8")
    receipt=tmp_path/"receipt.json"
    result=subprocess.run([sys.executable,"-B",str(SOURCE/"skills/wangbin-estimate-calculator/scripts/estimator.py"),str(request),"-o",str(receipt)],capture_output=True)
    assert result.returncode==rc,result.stderr
    assert receipt.exists()==(rc==0)
    if rc==2: assert b"duplicate JSON object field" in result.stderr
    elif 'refused' in members: assert json.loads(receipt.read_bytes())["tiers"]["MVP"]["labor_rmb"] is None
