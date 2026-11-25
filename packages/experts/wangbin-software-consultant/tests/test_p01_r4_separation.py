"""R4 arithmetic oracle and source-order guards; not model/WorkBuddy QA."""
from decimal import Decimal
from pathlib import Path

AGENT = Path(__file__).resolve().parents[1] / "agents" / "wangbin-software-consultant.md"


def aggregate(rows, included, risk_low, risk_high, rate=None):
    selected = [row for row in rows if row[0] in included]
    base = tuple(sum((sum((Decimal(value) for value in row[side]), Decimal(0)) for row in selected), Decimal(0)) for side in (1, 2))
    effort = (base[0] * (1 + Decimal(risk_low)), base[1] * (1 + Decimal(risk_high)))
    cost = None if rate is None else tuple(day * Decimal(rate) for day in effort)
    return base, effort, cost


def test_rate_refusal_preserves_cumulative_effort_and_conditional_interface():
    # Role triples: FE, BE, specialist. Values are fictional, not an ERP quote.
    rows = [
        ("A", ("1", "2", "0"), ("2", "3", "0")),
        ("B", ("0", "1", "1"), ("0", "2", "2")),
        ("C", ("2", "1", "0"), ("3", "2", "1")),
        ("D", ("0", "2", "1"), ("1", "3", "2")),
    ]
    mvp = aggregate(rows, {"A", "B"}, ".10", ".20")
    standard = aggregate(rows, {"A", "B", "C"}, ".10", ".20")
    full = aggregate(rows, {"A", "B", "C", "D"}, ".10", ".20")
    assert mvp == ((Decimal(5), Decimal(9)), (Decimal("5.50"), Decimal("10.80")), None)
    assert standard[0] == (Decimal(8), Decimal(15))
    assert full[0] == (Decimal(11), Decimal(21))
    assert aggregate(rows, {"A", "B", "C", "D"}, ".10", ".20", "1200")[:2] == full[:2]
    assert aggregate(rows, {"A", "B", "C", "D"}, ".10", ".20", "1200")[2] != aggregate(rows, {"A", "B", "C", "D"}, ".10", ".20", "1000")[2]
    assert aggregate(rows, {"A", "B", "C"}, ".10", ".20")[0] == standard[0]


def test_source_explicitly_separates_effort_from_currency():
    text = AGENT.read_text(encoding="utf-8")
    section = text.split("## 3. 工作量与报价计算协议", 1)[1].split("## 4. 交付物", 1)[0]
    # R5 superseded R4's explicit-consent requirement; CLR-Q18/26/29
    # distinguish requested targets, unknowns, and labor vs external fees.
    assert "A 工作量先于 B 获准计价；外费依据独立" in section
    decision = section.split("**统一决策顺序", 1)[1].split("**S12 / 有界 OA", 1)[0]
    assert decision.index("逐行逐列核对和求所求方案 B_L/B_H") < decision.index("金额权限依页首先锁定")
    assert "已有逐行数值不准以估时待评审、无工具或第三方费未知拒绝加总" in decision
    assert "缓冲有用户值或清楚标记的示意风险依据才给数值 E，否则保留 B 与条件 E 式" in decision
    assert "只要人天/不要金额→money=none 所有费用不算不报" in decision
    assert "明确拒参考价且无其他有效价→refused 不算人工，但获准外费可独立核算" in decision
    assert "许可不抹掉 B/E；金额未知只阻断对应指标/相应完整合计，不能抹有据其他项" in decision
    assert "长表按同版 ID 分组与 §5J 续交，不缩掉已确认范围或把已核小计作完整" in section
    assert "完整三类报价依 MTH-06/08 交 MVP=M、StandardA=M∪S、StandardB=M∪S∪I、FullA=M∪S∪F、FullB=M∪S∪F∪I 的各自成员和 B" in section
