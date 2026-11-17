"""P04 token-cost contract regression; static evidence is not model QA."""
from decimal import Decimal
from pathlib import Path


AGENT = Path(__file__).resolve().parents[1] / "agents" / "wangbin-software-consultant.md"


def ai_contract():
    text = AGENT.read_text(encoding="utf-8")
    return text.split("## 5H. AI 应用与 SaaS 服务咨询", 1)[1].split("## 6. 隐私、合规与合作", 1)[0]


def model_cost(input_tokens, output_tokens, input_price, output_price):
    million = Decimal(1_000_000)
    return (Decimal(input_tokens) / million * Decimal(input_price),
            Decimal(output_tokens) / million * Decimal(output_price))


def test_frozen_token_cost_and_fallback_contract():
    part = ai_contract()
    assert "N-AI-05 短算式发送前门槛" in part
    assert "2000 / 1,000,000 × 2 = 0.004 美元" in part
    assert "500 / 1,000,000 × 8 = 0.004 美元" in part
    assert "0.004 + 0.004 = 0.008 美元/次" in part
    for phrase in ("人工示意，未作确定性工具验证", "不继续尝试绕审批", "不套用此例", "待核项", "同一供应商调用或重放事件只入账一次", "配额", "硬上限", "API vs 自托管 GPU", "W06-QA2"):
        assert phrase in part
    header = AGENT.read_text(encoding="utf-8").split("# 软件需求与报价专家", 1)[0]
    assert "不得只留未求值公式" in header
    assert "不得声称 Decimal 已验证" in header


def test_exact_cost_and_missing_price_boundary():
    input_cost, output_cost = model_cost(2000, 500, 2, 8)
    assert (input_cost, output_cost, input_cost + output_cost) == (Decimal("0.004"), Decimal("0.004"), Decimal("0.008"))
    assert model_cost(0, 0, 2, 8) == (Decimal(0), Decimal(0))
    # Price is UNKNOWN, never silently substituted by the frozen fictional example.
    assert "币种或单位缺失/冲突时不套用此例" in ai_contract()
