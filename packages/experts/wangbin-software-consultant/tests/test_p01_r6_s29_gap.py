"""R6 S29 source and independent Decimal guards; not model or platform QA."""
from decimal import Decimal
from pathlib import Path

AGENT = Path(__file__).resolve().parents[1] / "agents" / "wangbin-software-consultant.md"


def _s29_section():
    # Q29 makes the original S29 arithmetic conditional on current
    # monetary permission. Include its guard, not just the illustration.
    text = AGENT.read_text(encoding="utf-8")
    return text.split("**本轮所求预算比较且最新 money=labor/all", 1)[1].split("**集团 ERP/MES/CRM 预算不足", 1)[0]


def test_known_budget_gap_must_be_explicit_even_without_old_wbs():
    section = _s29_section()
    budget = Decimal("50000")
    development = Decimal("90000")
    assert development - budget == Decimal("40000")
    assert "90,000 元－预算 50,000 元＝超出 40,000 元（四万元）" in section
    assert "旧 WBS/人天/单价明细缺失" in section
    assert "不得只说「超预算」" in section
    assert "逐项复核" in section and "逐项重算" in section
    assert "预算与开发费已有两个同币种、同口径的明确金额" in section
    assert "这只是按用户所给两金额的算术比较，不等于已经核实旧报价" in section
    assert "money=none 或相关金额未获准时不算不报原数、差额、价率或示例金额" in section


def test_s29_preserves_hours_and_separates_unknown_external_costs():
    section = _s29_section()
    assert "不为凑五万元暗减人天" in section
    assert "分别说明每项缩围失去的功能或验收能力" in section
    assert "第三方/接口等外部费用未知仍标待询价，不得填零" in section
    assert "不得填零或把九万元开发费称为完整总价" in section
