"""Twenty scoped regression checks: rule text vs executable JSON oracle; never model QA."""
import json
import runpy
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1]
AGENT = SOURCE / "agents/wangbin-software-consultant.md"
SCRIPT = SOURCE / "skills/wangbin-estimate-calculator/scripts/estimator.py"
FIXTURE = SOURCE / "experiments/decimal-poc/fixture_branches_synthetic.json"

# Each condition checks an explicit *rule* including a negative obligation, not model output.
RULE_CASES = [
    (1, "一个 REQ 可连多个工作包", "不能"),
    (2, "一包服务多个 REQ", "共享理由"),
    (3, "UNMAPPED/NEEDS_CONFIRMATION", "不能凭名称相近"),
    (4, "`SPLIT`（一旧多新）", "旧新原始来源和 SHA"),
    (5, "`MERGED`（多旧一新）", "旧新原始来源和 SHA"),
    (6, "删除采购专属收货", "不凭依赖猜测删除"),
    (7, "共享权限、审计、接口框架、部署和测试", "只计一次"),
    (8, "Σ模块分摊=该方案共享账户金额", "守恒未证"),
    (9, "分摊只是展示", "不再叠加进总价"),
    (10, "StandardB=M∪S∪I", "FullA=M∪S∪F"),
    (11, "UNKNOWN/待询价既不能当 0", "不能断言非零"),
    (12, "UNKNOWN/待询价既不能当 0", "不并入确定总价"),
    (13, "固定价来源 UNKNOWN/未确认或未批准", "绝不静默改用参考价"),
    (14, "经来源确认的缓冲才产生 R 与 E", "缺人天/缓冲/价"),
    (15, "人天÷人数及每周工作日/可用系数", "不能把人天、人数、日历工期或人民币混成一单位"),
    (16, "已承诺不可取消成本", "未来可避免包"),
    (17, "v1/v2 旧原始输入", "不写入当前有效范围"),
    (18, "盘点若未获确认只为 CONDITIONAL", "不凭依赖猜测"),
    (19, "用户只决定业务边界", "不要求用户指定技术 WBS 编号"),
    (20, "不把空白、未读取材料或模型建议提升为 CONFIRMED", "UNKNOWN 不自动变 ASSUMED 或 0"),
]


@pytest.mark.parametrize("ident,required,negative", RULE_CASES, ids=[f"MTH-{i:02}" for i, _, _ in RULE_CASES])
def test_formal_route_has_specific_rule_and_countercondition(ident, required, negative):
    text = AGENT.read_text(encoding="utf-8")
    section = text.split("**按需的项目控制方法（MTH-01～09", 1)[1].split("### 5.2", 1)[0]
    assert required in section, f"rule {ident} absent from actual Agent"
    assert negative in section, f"negative condition {ident} absent from actual Agent"


def test_executable_unique_membership_and_unknown_total():
    """Executable structural counterexample for cases 7, 9-12, not cost allocation/model behavior."""
    estimator = runpy.run_path(str(SCRIPT))["estimate"]
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    receipt = estimator(data)
    tiers = receipt["tiers"]
    assert set(tiers) == {"MVP", "StandardA", "StandardB", "FullA", "FullB"}
    assert all(len(tier["ids"]) == len(set(tier["ids"])) for tier in tiers.values())
    assert set(tiers["StandardB"]["ids"]) - set(tiers["StandardA"]["ids"]) == set(tiers["FullB"]["ids"]) - set(tiers["FullA"]["ids"])
    assert all(tier["complete_project_total_rmb"] is None for tier in tiers.values())


def test_executable_unapproved_fixed_and_missing_buffer_refused():
    """Executable rejected input for cases 13/14; source authentication remains out of scope."""
    estimator = runpy.run_path(str(SCRIPT))["estimate"]
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    data["pricing"] = {"mode": "fixed", "unit_price": "1200", "source": "未批准"}
    with pytest.raises(ValueError, match="pricing.source"):
        estimator(data)
    data["pricing"] = {"mode": "refused"}
    data["buffers"]["source"] = "未知"
    with pytest.raises(ValueError, match="buffers.source"):
        estimator(data)
