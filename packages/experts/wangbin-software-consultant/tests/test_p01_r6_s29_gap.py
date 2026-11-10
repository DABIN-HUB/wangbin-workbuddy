"""R6 S29 source and independent Decimal guards; not model or platform QA."""
from decimal import Decimal
from pathlib import Path

AGENT = Path(__file__).resolve().parents[1] / "agents" / "wangbin-software-consultant.md"


def test_known_budget_gap_must_be_explicit_even_without_old_wbs():
    section = AGENT.read_text(encoding="utf-8").split("**预算与开发费已有两个同币种", 1)[1].split("示例复核：", 1)[0]
    budget = Decimal("50000")
    development = Decimal("90000")
    assert development - budget == Decimal("40000")
    assert "90,000 元－预算 50,000 元＝超出 40,000 元（四万元）" in section
    assert "旧 WBS/人天/单价明细缺失" in section
    assert "不得只说「超预算」" in section
    assert "逐项复核" in section and "逐项重算" in section


def test_s29_preserves_hours_and_separates_unknown_external_costs():
    section = AGENT.read_text(encoding="utf-8").split("**预算与开发费已有两个同币种", 1)[1].split("示例复核：", 1)[0]
    assert "不为凑五万元暗减人天" in section
    assert "分别说明每项缩围失去的功能或验收能力" in section
    assert "第三方/接口等外部费用未知仍标待询价，不得填零" in section
    assert "不得填零或把九万元开发费称为完整总价" in section
