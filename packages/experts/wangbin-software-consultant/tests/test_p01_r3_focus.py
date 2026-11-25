"""R3 scope and Decimal reference guards; NOT model-behavior QA."""
from decimal import Decimal
from pathlib import Path

AGENT = Path(__file__).resolve().parents[1] / "agents" / "wangbin-software-consultant.md"


def test_finite_quote_precedence_and_no_framework_exemption():
    body = AGENT.read_text(encoding="utf-8")
    assert "「只要报价框架」表示交付形式精简" in body
    assert "不表示免除已可估算情景的逐包数字" in body
    assert "先遵守用户本轮指定的交付物和最新已确认范围" in body
    assert "不以审批细则、现有系统或第三方价格未知" in body
    assert "只有连这样有界的场景都不能构建时" in body
    assert "1000～1500 元/人天" in body
    # CLR-Q20/29 retain fixed-price precedence while respecting the
    # latest monetary permission and allowing authorized role pricing.
    policy = body.split("**统一决策顺序", 1)[1].split("**S12 / 有界 OA", 1)[0]
    assert "用户有效固定价/逐角色固定或区间价优先" in policy
    assert "指定价来源未知/未确认/未批准、角色缺价不默换参考" in policy
    assert "未给价且未拒绝可按 R5 reference" in policy
    assert "只要人天/不要金额→money=none 所有费用不算不报" in policy
    # Retain the no-tool/no-delay guard, not a mandate to execute without
    # approval: short reliable arithmetic is allowed, other gaps disclosed.
    assert "已有逐行数值不准以估时待评审、无工具或第三方费未知拒绝加总" in policy
    header = body.split("# 软件需求与报价专家", 1)[0]
    assert "若有据数值、许可及单位已齐且可用少量短算式可靠复核，给可见算式与实际数值" in header
    assert "否则给条件式与具体缺口，不模拟成功、重试被阻工具或绕过审批" in header


def test_r3_reference_arithmetic_is_additive_and_rate_changes_only_fee():
    # Independent fixture, not a sample quote to paste into the Agent.
    rows = [(Decimal("1"), Decimal("2")), (Decimal("1.5"), Decimal("3")),
            (Decimal("2"), Decimal("4")), (Decimal("1"), Decimal("1.5"))]
    low, high = (sum(side, Decimal("0")) for side in zip(*rows))
    assert (low, high) == (Decimal("5.5"), Decimal("10.5"))
    effort = (low * Decimal("1.10"), high * Decimal("1.20"))
    assert effort == (Decimal("6.050"), Decimal("12.600"))
    fixed = tuple(day * Decimal("1375") for day in effort)
    changed = tuple(day * Decimal("1300") for day in effort)
    assert fixed == (Decimal("8318.750"), Decimal("17325.000"))
    assert changed == (Decimal("7865.000"), Decimal("16380.000"))
    assert tuple(day * rate for day, rate in zip(effort, (Decimal("1000"), Decimal("1500")))) == (Decimal("6050.000"), Decimal("18900.000"))


def test_incremental_scope_recomputes_without_duplicating_base():
    base = (Decimal("5.5"), Decimal("10.5"))
    addition = (Decimal("2"), Decimal("3"))
    standard = tuple(a + b for a, b in zip(base, addition))
    full = tuple(a + b for a, b in zip(standard, (Decimal("1"), Decimal("2"))))
    assert standard == (Decimal("7.5"), Decimal("13.5"))
    assert full == (Decimal("8.5"), Decimal("15.5"))
    assert tuple(a - b for a, b in zip(standard, base)) == addition
    assert tuple(a - b for a, b in zip(full, standard)) == (Decimal("1"), Decimal("2"))
