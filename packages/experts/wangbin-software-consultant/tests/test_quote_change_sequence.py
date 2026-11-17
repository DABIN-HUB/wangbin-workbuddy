"""ERP synthetic sequence: price-only change then deletion, using formal CLI.
Contracts: E-07; docs/input-output-contract.md estimate equations and price priority;
S31 separate scope/fees. Not an Agent conversation or platform test.
"""
import copy
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import pytest
SOURCE=Path(__file__).resolve().parents[1]
ROLES=("FE","BE","DB","QA")

@pytest.mark.parametrize("old_price,new_price",[("1000","1200"),("1200","1350")])
@pytest.mark.parametrize("removed",["S2","I1"])
def test_price_then_delete_latest_scope(tmp_path,old_price,new_price,removed):
    original=json.loads((SOURCE/"experiments/decimal-poc/fixture_branches_synthetic.json").read_bytes())
    original["pricing"]={"mode":"fixed","unit_price":old_price,"source":"SYNTHETIC initial approved parameter"}
    changed=copy.deepcopy(original)
    changed["pricing"]={"mode":"fixed","unit_price":new_price,"source":"SYNTHETIC subsequent approved parameter"}
    deleted=copy.deepcopy(changed)
    deleted.update(previous_scope_version=changed["scope_version"],scope_version="sequence-v2",scope_changed=True)
    deleted["work_packages"]=[r for r in deleted["work_packages"] if r["id"]!=removed]
    for row in deleted["work_packages"]:row["scope_version"]="sequence-v2"
    snapshots=[original,changed,deleted];answers=[]
    script=SOURCE/"skills/wangbin-estimate-calculator/scripts/estimator.py"
    for i,data in enumerate(snapshots):
        request=tmp_path/(str(i)+".input.json");request.write_text(json.dumps(data),encoding="utf-8")
        receipt=tmp_path/(str(i)+".receipt.json")
        run=subprocess.run([sys.executable,"-B",str(script),str(request),"-o",str(receipt)],capture_output=True)
        assert run.returncode==0,run.stderr
        result=json.loads(receipt.read_bytes());answers.append(result)
        assert result["input_sha256"]==hashlib.sha256(request.read_bytes()).hexdigest()
        assert result["script_sha256"]==hashlib.sha256(script.read_bytes()).hexdigest()
        assert result["scope_version"]==data["scope_version"]
        assert result["previous_scope_version"]==data.get("previous_scope_version")
        assert result["scope_changed"]==data.get("scope_changed",False)
        assert result["outside_fees"]=="UNKNOWN; inquire separately"
        assert result["labor_is_complete_total"] is False
        assert {r["id"] for r in result["rows"]}=={r["id"] for r in data["work_packages"]}
        # Independent summation from the current input, not a previous receipt.
        with localcontext() as ctx:
            ctx.prec=100
            for plan,tier in result["tiers"].items():
                members=[r for r in data["work_packages"] if plan in r["membership"]]
                assert tier["ids"]==[r["id"] for r in members]
                for side in ("low","high"):
                    totals={role:sum((Decimal(r["roles"][role][side]) for r in members),Decimal(0)) for role in ROLES}
                    assert all(Decimal(tier["roles"][role][side])==totals[role] for role in ROLES)
                    base=sum(totals.values());risk=base*Decimal(data["buffers"][side]);effort=base+risk
                    assert Decimal(tier["B"][side])==base
                    assert Decimal(tier["R"][side])==risk
                    assert Decimal(tier["E"][side])==effort
                    assert Decimal(tier["labor_rmb"][side])==effort*Decimal(data["pricing"]["unit_price"])
                assert tier["complete_project_total_rmb"] is None
    before,repriced,latest=answers
    assert before["rows"]==repriced["rows"]
    for plan in before["tiers"]:
        for field in ("ids","roles","B","R","E","delta_ids","delta_roles","condition"):
            assert before["tiers"][plan][field]==repriced["tiers"][plan][field]
        assert before["tiers"][plan]["labor_rmb"]!=repriced["tiers"][plan]["labor_rmb"]
        assert removed not in latest["tiers"][plan]["ids"]
    if removed=="I1":
        assert latest["tiers"]["StandardA"]["B"]==latest["tiers"]["StandardB"]["B"]
        assert latest["tiers"]["FullA"]["B"]==latest["tiers"]["FullB"]["B"]
    # All input snapshots remain immutable, even after later calls.
    assert any(r["id"]==removed for r in original["work_packages"])
