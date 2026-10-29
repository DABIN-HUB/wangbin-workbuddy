"""Actual local entrypoint; formula query does not invoke numerical methods."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def test_formula_cli_writes_query_and_reports_missing_inputs(tmp_path):
    command=[sys.executable,str(ROOT/"services/solar-pv-engine/solar_pv.py"),"--workspace",str(tmp_path),"formula","--formula-id","F-DC-CAPACITY","--output","query.json"]
    proc=subprocess.run(command,cwd=tmp_path,capture_output=True,text=True,encoding="utf-8",timeout=30)
    assert proc.returncode==0,proc.stderr
    output=json.loads((tmp_path/"query.json").read_text(encoding="utf-8"))
    assert output["formula_id"]=="F-DC-CAPACITY" and output["symbols"]
    assert output["calculation_status"]=="NOT_IMPLEMENTED" and not output["can_execute_calculation"]
    assert json.loads(proc.stdout)["formula_id"]=="F-DC-CAPACITY"

def test_unknown_formula_is_not_repaired_or_executed(tmp_path):
    proc=subprocess.run([sys.executable,str(ROOT/"services/solar-pv-engine/solar_pv.py"),"--workspace",str(tmp_path),"formula","--formula-id"," F-DC-CAPACITY "],cwd=tmp_path,capture_output=True,text=True,encoding="utf-8",timeout=30)
    assert proc.returncode==2 and json.loads(proc.stderr)["error"]["code"]=="UNKNOWN_FORMULA"
