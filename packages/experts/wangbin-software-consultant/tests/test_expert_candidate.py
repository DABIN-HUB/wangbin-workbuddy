"""Local static/packaging checks; these do not simulate WorkBuddy conversations."""
from __future__ import annotations

import io
import json
import shutil
import subprocess
import zipfile
from decimal import Decimal
from pathlib import Path

import pytest

from tooling.phase5_expert_packager import MEMBERS, NAME, VERSION, build, validate_source

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "packages" / "experts" / NAME
SCENARIOS = json.loads((Path(__file__).parent / "scenarios.json").read_text(encoding="utf-8"))


def test_expert_schema_and_prompt_are_self_contained():
    meta = validate_source(SOURCE)
    prompt = (SOURCE / "agents" / f"{NAME}.md").read_text(encoding="utf-8")
    assert len(meta["displayDescription"]["zh"]) in range(40, 51)
    assert meta["defaultInitPrompt"] == meta["quickPrompts"][0]
    for section in ("已确认", "合理假设", "待确认", "MVP", "标准", "完整定制", "前端", "后端", "数据库", "接口", "测试", "部署", "沟通", "第三方", "维护", "验收", "单体", "Modbus", "OPC UA", "IEC104", "MQTT"):
        assert section in prompt
    assert not set(meta).intersection({"dependencies", "runtime", "mcpServers", "tools"})
    assert "不要求登录其他系统" in prompt
    assert "每轮最多三个" in prompt


def test_invalid_agent_name_is_rejected(tmp_path: Path):
    copy = tmp_path / NAME
    shutil.copytree(SOURCE, copy, ignore=shutil.ignore_patterns("tests"))
    config = copy / ".codebuddy-plugin" / "plugin.json"
    meta = json.loads(config.read_text(encoding="utf-8"))
    meta["agentName"] = "different"
    config.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="agentName"):
        validate_source(copy)


def test_zip_members_are_exact_and_source_identical():
    """Replay 1.0.0 source identity from its immutable Git baseline, NOT a historical release ZIP.

    The historical ZIP is absent, and the Phase 5 report describes four members
    while the committed packager declares five. Never rebuild the old dist name
    from today's changed Agent, or mistake this in-memory replay for that ZIP.
    Historical release ZIP byte/hash comparison remains NOT_TESTED.
    """
    baseline = "67d0fe8cfa5d71b53cc46d79bbaec620638dd1e0"
    def old_bytes(rel: str) -> bytes:
        return subprocess.run(
            ["git", "show", f"{baseline}:packages/experts/{NAME}/{rel}"],
            cwd=ROOT, check=True, capture_output=True,
        ).stdout

    original = {f"{NAME}/{rel}": old_bytes(rel) for rel in MEMBERS}
    identity = json.loads(original[f"{NAME}/.codebuddy-plugin/plugin.json"])
    assert (identity["name"], identity["version"], identity["agents"]) == (
        NAME, VERSION, [f"./agents/{NAME}.md"])
    assert set(original) == {f"{NAME}/{rel}" for rel in MEMBERS}
    memory = io.BytesIO()
    with zipfile.ZipFile(memory, "w", compression=zipfile.ZIP_DEFLATED) as candidate:
        for member, payload in sorted(original.items()):
            candidate.writestr(member, payload)
    with zipfile.ZipFile(io.BytesIO(memory.getvalue())) as candidate:
        assert candidate.testzip() is None
        assert candidate.namelist() == sorted(original)
        for member, payload in original.items():
            assert candidate.read(member) == payload
    # Today's Agent changed after the baseline. Comparing it to a 1.0.0 ZIP
    # would falsely claim historical source identity; preserve both histories.
    assert original[f"{NAME}/agents/{NAME}.md"] != (SOURCE / "agents" / f"{NAME}.md").read_bytes()


def test_pricing_reference_example_recalculates_without_unknown_third_party_cost():
    base_low, base_high = Decimal("30"), Decimal("45")
    effort_low = base_low * (1 + Decimal("0.10"))
    effort_high = base_high * (1 + Decimal("0.20"))
    assert (effort_low, effort_high) == (Decimal("33"), Decimal("54"))
    assert (effort_low * 1000, effort_high * 1000) == (Decimal("33000"), Decimal("54000"))
    assert (effort_low * 1200, effort_high * 1200) == (Decimal("39600"), Decimal("64800"))
    prompt = (SOURCE / "agents" / f"{NAME}.md").read_text(encoding="utf-8")
    assert "33/54" in prompt and "33000/54000" in prompt
    assert "第三方费未知" in prompt


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s["id"] for s in SCENARIOS])
def test_scenario_catalog_is_complete_static_data(scenario: dict[str, str]):
    assert len(SCENARIOS) >= 30
    assert len({item["id"] for item in SCENARIOS}) == len(SCENARIOS)
    assert all(scenario.get(key, "").strip() for key in ("id", "topic", "user", "expected"))
    assert not any(word in scenario["user"] for word in ("真实密码", "真实Token"))
