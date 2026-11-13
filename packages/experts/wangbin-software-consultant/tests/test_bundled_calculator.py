"""Bundled assets/permissions and deterministic archive, not native host QA."""
import hashlib
import json
import shutil
from pathlib import Path
import pytest
from tooling.phase5_expert_packager import build, validate_source, NAME

SOURCE = Path(__file__).resolve().parents[1]

@pytest.mark.parametrize("field", ["tools", "runtime", "dependencies", "mcpServers"])
def test_custom_permissions_remain_forbidden(tmp_path, field):
    copy = tmp_path / NAME
    shutil.copytree(SOURCE, copy, ignore=shutil.ignore_patterns("__pycache__"))
    path = copy / ".codebuddy-plugin/plugin.json"
    meta = json.loads(path.read_text(encoding="utf-8")); meta[field] = ["Bash"]
    path.write_text(json.dumps(meta), encoding="utf-8")
    with pytest.raises(ValueError, match="external"):
        validate_source(copy)

@pytest.mark.parametrize("value", [["../external"], ["./skills/other"], []])
def test_external_or_unbound_skill_rejected(tmp_path, value):
    copy = tmp_path / NAME
    shutil.copytree(SOURCE, copy, ignore=shutil.ignore_patterns("__pycache__"))
    path = copy / ".codebuddy-plugin/plugin.json"
    meta = json.loads(path.read_text(encoding="utf-8")); meta["skills"] = value
    path.write_text(json.dumps(meta), encoding="utf-8")
    with pytest.raises(ValueError, match="skills"):
        validate_source(copy)

def test_archive_is_deterministic_and_binds_formal_bytes(tmp_path):
    target = tmp_path / "packages/experts" / NAME
    shutil.copytree(SOURCE, target, ignore=shutil.ignore_patterns("__pycache__"))
    first = build(tmp_path); second = build(tmp_path)
    assert first["sha256"] == second["sha256"]
    assert len(first["members"]) == 9
    rows = {r["path"]: r for r in first["members"]}
    rel = "skills/wangbin-estimate-calculator/scripts/estimator.py"
    assert rows[NAME + "/" + rel]["sha256"] == hashlib.sha256((SOURCE / rel).read_bytes()).hexdigest()
    prompt = (SOURCE / "agents" / (NAME + ".md")).read_text(encoding="utf-8")
    for rule in ("回执缺失", "input_sha256", "未作确定性工具验证", "不作为客户运行时防护", "角色分价"):
        assert rule in prompt


def test_formal_script_receipt_bytes_and_rejected_input(tmp_path):
    import subprocess
    import sys
    script = SOURCE / "skills/wangbin-estimate-calculator/scripts/estimator.py"
    original = SOURCE / "experiments/decimal-poc/fixture_synthetic.json"
    source = tmp_path / "input.json"
    payload = original.read_bytes(); source.write_bytes(payload)
    receipt = tmp_path / "receipt.json"
    run = subprocess.run([sys.executable, "-B", str(script), str(source), "-o", str(receipt)], capture_output=True)
    assert run.returncode == 0, run.stderr
    data = receipt.read_bytes(); result = json.loads(data)
    assert result["input_sha256"] == hashlib.sha256(payload).hexdigest()
    assert result["script_sha256"] == hashlib.sha256(script.read_bytes()).hexdigest()
    assert result["labor_is_complete_total"] is False
    assert all(tier["complete_project_total_rmb"] is None for tier in result["tiers"].values())
    source.write_bytes(b"{broken")
    refused = tmp_path / "invalid-receipt.json"
    failed = subprocess.run([sys.executable, "-B", str(script), str(source), "-o", str(refused)], capture_output=True)
    assert failed.returncode == 2 and not refused.exists()
    # Existing evidence is never overwritten, even by a valid rerun.
    source.write_bytes(payload)
    duplicate = subprocess.run([sys.executable, "-B", str(script), str(source), "-o", str(receipt)], capture_output=True)
    assert duplicate.returncode == 2 and receipt.read_bytes() == data
