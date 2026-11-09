"""P-01 source and arithmetic contract checks, NOT model or WorkBuddy dialogue QA."""
from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path

import pytest

from tooling.expert_rules import validate_prompt_expert

SOURCE = Path(__file__).resolve().parents[1]
AGENT = SOURCE / "agents" / "wangbin-software-consultant.md"
OLD = json.loads((SOURCE / "tests" / "scenarios.json").read_text(encoding="utf-8"))
FOCUS = ("S02", "S10", "S12", "S13", "S14", "S17", "S23", "S27", "S28", "S29", "S30", "S31", "S32")


def test_official_agent_entry_and_old_rules_preserved():
    """The manifest's agent is a documented entry; other files are not assumed loaded."""
    meta = validate_prompt_expert(SOURCE, name="wangbin-software-consultant", version="1.0.0", category="12-IndustryConsultant")
    assert meta["agents"] == ["./agents/wangbin-software-consultant.md"]
    body = AGENT.read_text(encoding="utf-8")
    for legacy in ("不要求登录其他系统", "每轮最多三个", "已确认", "合理假设", "待确认", "变更记录", "MVP", "单体", "Modbus", "33000/54000", "第三方费未知", "不索取客户名单"):
        assert legacy in body
    assert meta.get("skills") is None and "skills:" not in body.split("---", 2)[1]


def test_all_old_scenarios_and_focus_are_intact():
    assert [case["id"] for case in OLD] == [f"S{i:02}" for i in range(1, 33)]
    assert set(FOCUS) <= {case["id"] for case in OLD}
    assert all(case["user"] and case["expected"] for case in OLD)


def test_p01_contract_has_complete_lifecycle_and_deliverable_rows():
    body = AGENT.read_text(encoding="utf-8")
    lifecycle = body.split("### 5.3", 1)[1].split("### 5.4", 1)[0]
    outputs = body.split("### 5.4", 1)[1].split("### 5.5", 1)[0]
    assert re.findall(r"^\| L-(\d\d) ", lifecycle, re.M) == [f"{i:02}" for i in range(1, 13)]
    assert re.findall(r"^\| O-(\d\d) ", outputs, re.M) == [f"{i:02}" for i in range(1, 15)]
    assert all(len(row.split("|")) >= 4 for row in lifecycle.splitlines() if row.startswith("| L-"))
    for token in ("旧值", "页面", "API", "WBS", "过期", "三年 TCO", "许可证", "来源", "待询价", "最多三个"):
        assert token in body


@pytest.mark.parametrize("case_id", FOCUS)
def test_focus_scenario_is_frozen_not_model_approved(case_id):
    """Presence is only source coverage; this never calls or scores a model."""
    old = next(item for item in OLD if item["id"] == case_id)
    contract = (SOURCE / "docs" / "acceptance-cases.md").read_text(encoding="utf-8")
    assert old["user"].strip() and re.search(rf"^\| {case_id} \| .+ \| .+ \| .+ \|$", contract, re.M)
    assert "模型运行均 NOT_TESTED" in contract


def estimate(low: str, high: str, risk_low: str, risk_high: str, price_low: str, price_high: str):
    """Independent Decimal reference oracle; no platform invocation is implied."""
    effort_low = Decimal(low) * (1 + Decimal(risk_low))
    effort_high = Decimal(high) * (1 + Decimal(risk_high))
    return (effort_low, effort_high), (effort_low * Decimal(price_low), effort_high * Decimal(price_high))


def test_reference_prices_and_rate_change_keep_effort():
    effort, fixed = estimate("30", "45", ".10", ".20", "1000", "1000")
    changed_effort, changed = estimate("30", "45", ".10", ".20", "1200", "1200")
    default_effort, default = estimate("30", "45", ".10", ".20", "1000", "1500")
    assert effort == changed_effort == default_effort == (Decimal("33"), Decimal("54"))
    assert fixed == (Decimal("33000"), Decimal("54000"))
    assert changed == (Decimal("39600"), Decimal("64800"))
    assert default == (Decimal("33000"), Decimal("81000"))
    # Unknown external costs have no numeric input, hence none of the above is a complete total.
    assert "外部费用未知" in OLD[30]["user"]


def test_role_days_are_additive_not_doubled_by_throughput():
    assert Decimal("1") + Decimal("1") == Decimal("2")
    assert Decimal("1.5") + Decimal("1.5") == Decimal("3")
    assert Decimal("2") + Decimal("2") == Decimal("4")
    assert Decimal("5") + Decimal("5") == Decimal("10")
    assert Decimal("1") + Decimal("0") == Decimal("1")  # Backend only.
    body = AGENT.read_text(encoding="utf-8")
    assert "只作合理性校核，不能再计一次工时" in body
    assert "FE 为不适用" in body


def test_no_old_zip_assumption_or_model_pass_claim():
    body = AGENT.read_text(encoding="utf-8")
    assert "本 Agent 文本规则不证明平台自动使用 Decimal" in body
    assert "未声明的 skills" in body
    assert "别把静态规则/本地测试当真实模型" in body
