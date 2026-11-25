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
    section = AGENT.split("**集团 ERP/MES/CRM 预算不足的当轮分支：**", 1)[1].split("**单价与缓冲的变更事实", 1)[0]
    assert "明确未获接受" in section
    assert "没有可核实的范围/WBS 不承诺任何一路在原约束内可行" in section
    assert "人民币 10,000 元不足以完成全集团 ERP/MES/CRM 集成" in section
    assert "money=none 或相关金额未获准时不复述一万元、不算不报金额" in section
    assert "在**本轮**提出至少两条不同的" in section
    assert "许可、接口、云及人工费均需独立核实，未知不填零" in section
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
    section = AGENT.split("**单价与缓冲的变更事实先于重算：**", 1)[1].split("## 4. 交付物", 1)[0]
    assert "原固定价 1000、本轮改为 1200 且允许显示金额时" in section
    assert "记录旧价 1000→1200、原人工费 33000/54000 元与新人工费 39600/64800 元分别已过期/当前" in section
    assert "不把本轮刚写入的现值误认为上一轮已有" in section
    assert "单轮明确给定旧→新价也须记录变更" in section
    assert "只改价不改 B/r/R/E 或范围" in section
    assert "不能假定旧价 1000 或套用历史人天" in section
    assert "若只改缓冲 r 而未改 p" in section
    assert "保持 B/范围/单价不变，重算 E 及获准 C" in section
    assert "不复述或计算禁止的金额" in section
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
