"""Explicitly missing buffer provenance cannot produce a successful quote."""
import json
from pathlib import Path
import subprocess
import sys
import pytest
SOURCE = Path(__file__).resolve().parents[1]
@pytest.mark.parametrize("source,rc", [("缓冲来源未知",2),("not yet confirmed",2),("buffer source is unknown",2),("缓冲尚未确认",2),("requirements_unknown.md:42 用户确认缓冲10%/20%",0),("not yet confirmed.md:42 user confirmed buffer",0),("SYNTHETIC explicit assumption; customer not yet confirmed",0),("unknown",2),(" UNKNOWN ",2),("unconfirmed",2),("not confirmed",2),("pending",2),("tbd",2),("未知",2),("待确认",2),("未确认",2),("SYNTHETIC illustrative assumption, not approved customer buffer",0),("第2话轮用户确认10%/20%",0)])
def test_formal_cli_buffer_basis(tmp_path,source,rc):
    data=json.loads((SOURCE/"tests/fixtures/precision-boundary.input.json").read_bytes())
    data["work_packages"]=data["work_packages"][:1]
    for role in data["work_packages"][0]["roles"].values(): role.update(low="1",high="1")
    data["buffers"]["source"]=source
    request=tmp_path/"input.json";request.write_text(json.dumps(data),encoding="utf-8")
    receipt=tmp_path/"receipt.json"
    result=subprocess.run([sys.executable,"-B",str(SOURCE/"skills/wangbin-estimate-calculator/scripts/estimator.py"),str(request),"-o",str(receipt)],capture_output=True)
    assert result.returncode==rc,result.stderr
    assert receipt.exists()==(rc==0)
    if rc==0: assert json.loads(receipt.read_bytes())["tiers"]["MVP"]["E"]=={"low":"4.4","high":"4.8"}


@pytest.mark.parametrize("case",["buffer-unknown-explicit-cn","buffer-unconfirmed-sentence"])
def test_independent_qa_original_buffer_state(tmp_path,case):
    request=SOURCE/"tests/fixtures"/(case+".input.json")
    receipt=tmp_path/"receipt.json"
    result=subprocess.run([sys.executable,"-B",str(SOURCE/"skills/wangbin-estimate-calculator/scripts/estimator.py"),str(request),"-o",str(receipt)],capture_output=True)
    assert result.returncode==2 and not receipt.exists()
    assert b"buffers.source" in result.stderr
