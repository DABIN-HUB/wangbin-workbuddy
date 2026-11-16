"""Both formal CLI routes reject unresolved fixed sources and preserve valid results."""
import json
from pathlib import Path
import subprocess
import sys
import pytest
SOURCE=Path(__file__).resolve().parents[1]
SCRIPT=SOURCE/"skills/wangbin-estimate-calculator/scripts/estimator.py"
BASE="5a3de264eb84a4aac66e8d8f390b8ab7255f3d8b"
GIT_PATH="packages/experts/wangbin-software-consultant/skills/wangbin-estimate-calculator/scripts/estimator.py"
@pytest.mark.parametrize("fixture",["fixture_branches_synthetic.json","fixture_synthetic.json"])
@pytest.mark.parametrize("mode,source,reject",[
 ("fixed","单价来源未知",True),("fixed","not yet confirmed",True),
 ("fixed","price source is unknown",True),("fixed","未获授权",True),("fixed","not approved",True),
 ("fixed","requirements_unknown.md:42 用户确认1200",False),
 ("fixed","not yet confirmed.md:42 user confirmed 1200",False),
 ("fixed","ASSUMED not approved",False),("fixed","SYNTHETIC illustrative user parameter",False),
 ("reference",None,False),("refused",None,False)])
def test_fixed_source_cli(tmp_path,fixture,mode,source,reject):
 data=json.loads((SOURCE/"experiments/decimal-poc"/fixture).read_bytes())
 data["pricing"]={"mode":mode}
 if mode=="fixed":data["pricing"].update(unit_price="1200",source=source)
 request=tmp_path/"input.json";request.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
 old=tmp_path/"baseline.py"
 old.write_bytes(subprocess.run(["git","show",BASE+":"+GIT_PATH],cwd=SOURCE,check=True,capture_output=True).stdout)
 receipts=[]
 for script,name in [(old,"before"),(SCRIPT,"after")]:
  receipt=tmp_path/(name+".json")
  run=subprocess.run([sys.executable,"-B",str(script),str(request),"-o",str(receipt)],capture_output=True)
  expected=2 if name=="after" and reject else 0
  assert run.returncode==expected,run.stderr
  assert receipt.exists()==(expected==0)
  if expected==2:assert b"pricing.source" in run.stderr
  else:
   value=json.loads(receipt.read_bytes());value.pop("script_sha256");receipts.append(value)
 if not reject:assert receipts[0]==receipts[1]
