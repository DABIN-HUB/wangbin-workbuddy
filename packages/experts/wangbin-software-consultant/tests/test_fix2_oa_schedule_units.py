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
    for boundary in ("示意", "不是客户事实或交付日期", "SSO/通道授权等待", "UAT", "返工"):
        assert boundary in route


def test_oa05_baseline_and_mixed_capacity_are_not_same_range():
    lower = Decimal("31.625")
    assert lower / (Decimal(3) * 5) != Decimal("1.58")
    assert Decimal("27.5") / (Decimal(3) * 5) != lower / (Decimal(3) * 5)
    assert Decimal("55") / (Decimal(3) * 5) != Decimal("55") / (Decimal(4) * 5)
