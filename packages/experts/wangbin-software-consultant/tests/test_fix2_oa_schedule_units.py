"""FIX2 OA-05 deterministic source/units regression; not native model QA."""
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "agents" / "wangbin-software-consultant.md"


def test_oa05_same_buffered_bounds_in_summary_body_and_final():
    text = SOURCE.read_text(encoding="utf-8")
    route = text.split('- OA 的“SSO 待办通知排期”：', 1)[1].split('\n', 1)[0]
    lower, upper = Decimal("31.625"), Decimal("55")
    capacity = Decimal(3) * Decimal(5)
    rounded = [str((value / capacity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)) for value in (lower, upper)]
    assert rounded == ["2.11", "3.67"]
    assert "同一范围未舍入的含缓冲 E_L/E_H" in route
    assert "E_L÷(n×d)..E_H÷(n×d)" in route
    assert "草案摘要、正文排期与末答" in route
    assert "2.11～3.67 周" in route
    assert "1.58～3.67 周" not in route
    # CLR-Q4/Q9–12 distinguish the retained E/capacity illustration from
    # the actual resource-constrained schedule based on B and the same R.
    for boundary in ("示意", "不是客户事实、基础任务排期或交付日期", "SSO/通道授权等待", "UAT",
                     "含储备投入的理想产能下界", "禁止用基础 B、其它范围或不同 n 拼出该下界",
                     "分别以 B 的低高情景排任务", "分列同一 R 储备", "已含工作或储备不得再次累加"):
        assert boundary in route
    quote = text.split("## 3. 工作量与报价计算协议", 1)[1].split("## 4. 交付物", 1)[0]
    assert "不在下界之上重复累加工作、折减、储备/返工或等待" in quote
    schedule = text.split("**O-10 资源约束下的文字排期", 1)[1].split("### 资源、上线", 1)[0]
    for boundary in ("从基础 B 构造上述排期", "保留同一 R 的风险储备容量",
                     "等待本身不是开发人天", "已在 B 或已安排的储备/等待不得再加",
                     "不能再次给 R 计费"):
        assert boundary in schedule


def test_oa05_baseline_and_mixed_capacity_are_not_same_range():
    lower = Decimal("31.625")
    assert lower / (Decimal(3) * 5) != Decimal("1.58")
    assert Decimal("27.5") / (Decimal(3) * 5) != lower / (Decimal(3) * 5)
    assert Decimal("55") / (Decimal(3) * 5) != Decimal("55") / (Decimal(4) * 5)
