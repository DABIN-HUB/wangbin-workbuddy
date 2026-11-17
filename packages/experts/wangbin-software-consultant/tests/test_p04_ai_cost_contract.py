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


def test_frozen_n_ai_05_short_prompt_requires_conditional_role_wbs_and_days():
    part = ai_contract()
    assert '用户只问“token 单价和 GPU/API 比较”' in part
    first = part.split("**N-AI-05 成本选型首答闭环：**", 1)[1].split("\n\n", 1)[0]
    for term in ("条件化费用公式", "同轮", "业务/产品", "AI 工程师", "后端/数据", "QA/安全", "运维", "前置", "可观察测试", "low_days/high_days", "示意情景", "AI-API-1", "AI-GPU-1", "人天", "互斥", "待询价", "币种", "计价版本", "不选定赢家"):
        assert term in first
    assert "1+2+2+1+1=7 至 2+3+3+2+2=12 人天" in first
    assert "1+3+2+1+1=8 至 2+5+3+2+2=14 人天" in first
    assert sum((1, 2, 2, 1, 1)) == 7 and sum((2, 3, 3, 2, 2)) == 12
    assert sum((1, 3, 2, 1, 1)) == 8 and sum((2, 5, 3, 2, 2)) == 14
