"""FIX1 targeted source/units regression, not an independent model or platform verdict."""
from decimal import Decimal
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "agents" / "wangbin-software-consultant.md"


def section(start, end):
    text = SOURCE.read_text(encoding="utf-8")
    return text.split(start, 1)[1].split(end, 1)[0]


def test_wms_row_column_and_conditional_ba():
    wms = section("## 5F. WMS 仓储作业咨询", "## 5G. 电商与小程序咨询")
    assert "冻结批次不得预留/发运" in wms
    assert "只有存在独立 BA 工作包、来源及验收才入列" in wms
    assert "不宣称不实的“严格一致”" in wms
    assert "B、R、E 及许可下的条件人工费" in wms
    row = [(0, 0), (0, 0), (0, 0), (0, 0), (1, 1)]
    columns = [(6, 10), (2, 3), (7, 11), (5, 6), (10, 12)]
    assert tuple(map(sum, zip(*row))) == (1, 1)
    assert tuple(map(sum, zip(*columns))) == (30, 42)
    assert "行和是 `1/1`" in wms and "B 是 `30/42`" in wms


def test_mes_batches_burst_and_units():
    mes = section("## 5E. 工业 IoT 与 MES 关联", "## 5F. WMS 仓储作业咨询")
    points_per_second = Decimal(500) * 100 / 5
    assert points_per_second == 10000
    assert points_per_second * 86400 == 864000000
    assert points_per_second / 5000 == Decimal(10) / 5 == 2
    assert points_per_second / 100 == 100
    assert (Decimal(10) * 5000 / 1) / points_per_second == 5
    for phrase in ("2 批/秒", "120 批/分钟", "100 设备批/秒", "1 秒突发窗口", "5 倍", "正文、容量表、架构图与摘要", "不从纯示意推固定 CPU/GB"):
        assert phrase in mes


def test_s18_people_vs_weeks():
    source = section("- **未知需求却要求定日（S18）：**", "- **五年旧订单迁新 CRM（S20）：**")
    effort = Decimal(120)
    weekly = Decimal(4) * 5 * Decimal("0.8")
    gap = effort - weekly * 6
    assert (weekly, gap, gap / weekly, gap / (6 * 5 * Decimal("0.8"))) == (16, 24, Decimal("1.5"), 1)
    for phrase in ("96 人天", "缺 24 人天", "=1.5 周", "不是 1.5 人", "=1 人", "不能据此保证某日完成"):
        assert phrase in source
