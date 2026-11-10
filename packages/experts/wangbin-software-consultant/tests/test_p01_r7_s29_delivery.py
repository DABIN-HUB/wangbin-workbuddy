"""Developer-side output examples: distinguish delivered cuts from future promises.

This is a bounded regression for the acceptance rubric, not independent model QA.
"""
from decimal import Decimal
import re


def delivered_candidates(answer: str) -> list[str]:
    """Conservative check of numbered, per-candidate output; human QA checks semantics."""
    blocks = re.split(r"(?m)^\s*(?:候选|方案)\s*[一二三四1-4][：:、.]", answer)
    result = []
    for block in blocks[1:]:
        if (re.search(r"(?:仅当|如果|若).{0,35}(?:原范围|旧范围|原方案).{0,35}(?:包含|包括|有)", block)
                and re.search(r"延期|删除|简化|改为", block)
                and re.search(r"保留", block)
                and re.search(r"失去|无法验收|不再验收", block)
                and re.search(r"风险|前提", block)
                and re.search(r"确认", block)):
            result.append(block)
    return result


R6_PROMISE = """按你给的数，开发费 90,000 元－预算上限 50,000 元＝超出 40,000 元。
请提供原工作包及人天，指出哪些功能可以延期或删减；我会先列出每项缩减会失去的功能或验收能力，再重算。"""
DELIVERED = """按你给的数，开发费 90,000 元－预算 50,000 元＝超出 40,000 元；旧 WBS 未核实，原人天/单价不改，外部接口费另待询价。
候选一：仅当原范围包含自定义统计报表，才考虑延期自定义筛选和图表；保留核心业务录入和查询，但首期失去自定义统计和报表导出验收。风险是手工汇总费时；前提是普通查询能满足日常使用。请确认原报表是否在旧范围、业务必需指标和原 WBS 后再估算。
候选二：若旧范围包括第三方自动同步，可改为带格式校验的人工导入，保留核心数据处理；首期失去实时同步与失败自动恢复验收。风险是人工导入延迟及误录；前提是数据提供方能按时给合规文件。请确认同步时效是否必需、原接口包和原人天后再估算。
不能凭四万元倒推节省人天或保证五万元内交付；确认后仅重算受影响工作包，不重复计保留项和已删项。"""


def test_prior_r6_future_promise_is_not_delivery():
    assert Decimal("90000") - Decimal("50000") == Decimal("40000")
    assert delivered_candidates(R6_PROMISE) == []


def test_positive_two_distinct_conditional_cuts_each_with_loss_and_confirmation():
    candidates = delivered_candidates(DELIVERED)
    assert len(candidates) == 2
    assert "报表导出验收" in candidates[0]
    assert "失败自动恢复验收" in candidates[1]
    assert "外部接口费另待询价" in DELIVERED
    assert "原人天/单价不改" in DELIVERED


def test_missing_loss_or_unconditional_module_does_not_count():
    without_loss = DELIVERED.replace("失去实时同步与失败自动恢复验收", "实现实时同步与失败自动恢复")
    assert len(delivered_candidates(without_loss)) == 1
    asserted_fact = DELIVERED.replace("仅当原范围包含自定义统计报表", "你已确认原范围包含自定义统计报表")
    assert len(delivered_candidates(asserted_fact)) == 1
