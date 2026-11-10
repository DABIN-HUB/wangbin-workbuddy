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
    assert section.index("A 工作量先于 B 人民币计价") < section.index("完成 A 后才处理 B")
    assert "拒绝参考价时写“人民币未计算：未获单价”" in section
    assert "不能先给长表再拒绝汇总" in section
    assert "绝不能在已输出明细之后用【未验证】代替三档 B 和 E" in section
