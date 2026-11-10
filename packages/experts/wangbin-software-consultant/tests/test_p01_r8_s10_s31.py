"""R8 bounded source and scoring controls; not independent model QA."""
from decimal import Decimal
from pathlib import Path
import re

AGENT = (Path(__file__).parents[1] / "agents" / "wangbin-software-consultant.md").read_text(encoding="utf-8")


def _lines(text):
    return [part.strip() for part in re.split(r"(?:路线|候选)\s*[AB一二][：:]", text)[1:]]


def _scope_valid(text):
    parts = _lines(text)
    return len(parts) >= 2 and all(
        ("仅当" in part or "若" in part)
        and "保留" in part and "延期" in part and "不能验收" in part
        for part in parts[:2]
    )


def test_s10_current_turn_candidates_and_lost_acceptance_controls():
    assert "集团 ERP/MES/CRM 预算不足的当轮分支" in AGENT
    assert "明确未获接受" in AGENT and "不承诺任何一路万元内可行" in AGENT
    assert "外部费" in AGENT or "许可、接口、云" in AGENT
    good = "路线 A：仅当库存优先，保留单仓出入库，延期跨组织库存，不能验收跨仓汇总。路线 B：若销售优先，保留线索跟进，延期生产派工，不能验收生产闭环。"
    assert _scope_valid(good)
    assert not _scope_valid("先确认核心流程和预算，下轮我将提供缩围方案。")
    assert not _scope_valid(good.replace("不能验收生产闭环", "可以验收生产闭环"))
    assert not _scope_valid(good.replace("若销售优先", "销售业务已经确定"))


def _update_rate(old, new, base=("30", "45"), risk=("0.10", "0.20")):
    b = tuple(map(Decimal, base))
    r = tuple(map(Decimal, risk))
    effort = tuple(x * (1 + y) for x, y in zip(b, r))
    return {"base": b, "risk": r, "effort": effort,
            "old_cost": tuple(x * Decimal(old) for x in effort),
            "new_cost": tuple(x * Decimal(new) for x in effort)}


def test_s31_old_and_new_rate_are_both_preserved():
    assert "单价与缓冲的变更事实先于重算" in AGENT
    assert "本轮由 1000→1200" in AGENT
    assert "不把本轮刚写入的现值误认为上一轮已有" in AGENT
    assert "单轮用户直接说" in AGENT and "若只改缓冲" in AGENT
    got = _update_rate("1000", "1200")
    assert got["base"] == (Decimal(30), Decimal(45))
    assert got["effort"] == (Decimal(33), Decimal(54))
    assert got["old_cost"] == (Decimal(33000), Decimal(54000))
    assert got["new_cost"] == (Decimal(39600), Decimal(64800))
    assert got["new_cost"] != got["old_cost"]
    assert got["new_cost"] != (Decimal(33000), Decimal(81000))


def test_buffer_only_changes_effort_and_cost_not_fixed_rate():
    old = _update_rate("1000", "1000")
    changed = _update_rate("1000", "1000", risk=("0.15", "0.25"))
    assert changed["base"] == old["base"]
    assert changed["effort"] == (Decimal("34.50"), Decimal("56.25"))
    assert changed["new_cost"] == (Decimal(34500), Decimal(56250))
    assert changed["new_cost"] != old["new_cost"]
