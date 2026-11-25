"""Both formal CLI routes reject unresolved fixed sources and preserve valid results."""
import hashlib
import json
import os
from decimal import Decimal
from pathlib import Path
import subprocess
import sys
import pytest
from tooling.phase5_expert_packager import _historical_blob

SOURCE=Path(__file__).resolve().parents[1]
ROOT=Path(__file__).resolve().parents[4]
SCRIPT=SOURCE/"skills/wangbin-estimate-calculator/scripts/estimator.py"
BASE="5a3de264eb84a4aac66e8d8f390b8ab7255f3d8b"
GIT_PATH="packages/experts/wangbin-software-consultant/skills/wangbin-estimate-calculator/scripts/estimator.py"
FIXTURES=["fixture_branches_synthetic.json","fixture_synthetic.json"]
CASES=[
 ("fixed","单价来源未知",True),("fixed","not yet confirmed",True),
 ("fixed","price source is unknown",True),("fixed","未获授权",True),("fixed","not approved",True),
 ("fixed","requirements_unknown.md:42 用户确认1200",False),
 ("fixed","not yet confirmed.md:42 user confirmed 1200",False),
 ("fixed","ASSUMED not approved",False),("fixed","SYNTHETIC illustrative user parameter",False),
 ("reference",None,False),("refused",None,False)]


def _request(tmp_path,fixture,mode,source):
 data=json.loads((SOURCE/"experiments/decimal-poc"/fixture).read_bytes())
 data["pricing"]={"mode":mode}
 if mode=="fixed":data["pricing"].update(unit_price="1200",source=source)
 request=tmp_path/"input.json";request.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
 return request


@pytest.mark.parametrize("fixture",FIXTURES)
@pytest.mark.parametrize("mode,source,reject",CASES)
def test_fixed_source_cli(tmp_path,fixture,mode,source,reject):
 request=_request(tmp_path,fixture,mode,source)
 old=tmp_path/"baseline.py"
 repo=Path(os.environ.get("WANGBIN_CONSULTANT_TEST_SOURCE_REPO",ROOT)).resolve(strict=True)
 old.write_bytes(_historical_blob(repo,BASE,GIT_PATH))
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


@pytest.mark.parametrize("fixture",FIXTURES)
@pytest.mark.parametrize("mode,source,reject",CASES)
def test_current_fixed_source_cli(tmp_path,fixture,mode,source,reject):
 """Exercise all current paths even when the historical comparison is blocked."""
 request=_request(tmp_path,fixture,mode,source)
 receipt=tmp_path/"current.json"
 run=subprocess.run([sys.executable,"-I","-B",str(SCRIPT),str(request),"-o",str(receipt)],capture_output=True)
 assert run.returncode==(2 if reject else 0),run.stderr
 assert receipt.exists()==(not reject)
 if reject:
  assert b"pricing.source" in run.stderr
  return
 result=json.loads(receipt.read_bytes())
 assert result["input_sha256"]==hashlib.sha256(request.read_bytes()).hexdigest()
 assert result["script_sha256"]==hashlib.sha256(SCRIPT.read_bytes()).hexdigest()
 assert result["pricing_mode"]==mode
 assert result["labor_is_complete_total"] is False
 # Hand-summed fixture person-days, independent of the historical script.
 base=({"MVP":(16,26),"StandardA":(30,52),"StandardB":(37,63),"FullA":(36,62),"FullB":(43,73)}
       if fixture==FIXTURES[0] else {"MVP":(7,12),"Standard":(12,21),"FullA":(18,31),"FullB":(25,42)})
 assert set(result["tiers"])==set(base)
 for tier,(lo,hi) in base.items():
  row=result["tiers"][tier]
  for side,days,buffer,reference_price in (("low",lo,Decimal("0.10"),1000),("high",hi,Decimal("0.20"),1500)):
   effort=days*(1+buffer)
   assert Decimal(row["B"][side])==days
   assert Decimal(row["E"][side])==effort
   if mode=="refused":assert row["labor_rmb"] is None
   else:assert Decimal(row["labor_rmb"][side])==effort*(1200 if mode=="fixed" else reference_price)
  assert row["complete_project_total_rmb"] is None
