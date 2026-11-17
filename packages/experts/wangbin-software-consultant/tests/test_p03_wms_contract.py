"""WMS source contract checks; never substitutes for independent model/site QA."""
import csv
from decimal import Decimal
from pathlib import Path

PRODUCT = Path(__file__).resolve().parents[1]
AGENT = PRODUCT / "agents" / "wangbin-software-consultant.md"
MATRIX = PRODUCT / "docs" / "traceability.csv"


def wms():
    text = AGENT.read_text(encoding="utf-8")
    assert text.count("## 5F. WMS 仓储作业咨询") == 1
    return text.split("## 5F. WMS 仓储作业咨询", 1)[1].split("## 6. 隐私、合规与合作", 1)[0]


def test_wms_flow_and_lot_inventory_concurrency():
    source = wms()
    for phrase in ("ERP 库存模块", "成熟 WMS", "开源业务产品二开", "窄范围定制", "ASN-A", "待上架", "错位", "容量超限", "效期", "reserved", "blocked", "available=on_hand-reserved-blocked", "版本 CAS", "409", "已拣", "已复核", "已交运", "盘盈盘亏", "审批后", "wms_stock_ledger", "wms_stock_balance", "NULL 绕开唯一"):
        assert phrase in source
    # Illustrative event arithmetic only; never customer stock evidence.
    assert Decimal(10) - Decimal(8) == 2
    assert Decimal(8) - Decimal(1) - Decimal(5) == 2


def test_web_pda_weak_network_and_security():
    source = wms()
    for prefix, count in (("WMS-W", 7), ("WMS-D", 6)):
        for number in range(1, count + 1):
            assert f"{prefix}{number:02d}" in source
    for phrase in ("扫码后焦点回输入框", "先扫位后扫货", "服务端每次重验", "稳定请求 ID", "同键同载荷原回执", "异载荷 409", "加密存储", "重新在线验权", "不声称已经离线同步", "现场实测"):
        assert phrase in source


def test_integration_cost_and_acceptance_boundaries():
    source = wms()
    for phrase in ("ERP 主责采购/销售业务源单", "电商主责订单", "TMS 主责承运", "库存总量的**唯一权威**", "超时查询后同键重试", "对账按组织/仓/SKU/批次/货主", "N-WMS-01", "N-WMS-06", "S03/S09", "N-X-02/05", "W03-PDA1", "W05-INT1", "W06-SITE1", "W06-QA1", "Decimal 合同", "UNKNOWN 不填 0", "NOT_TESTED"):
        assert phrase in source
    assert "不是现有可调用端点" in source


def test_wms_frd_mapping_without_relabeling_iot():
    with MATRIX.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    wms_rows = [r for r in rows if r["requirement_id"].startswith("D05-")]
    assert len(wms_rows) == 10
    assert all(r["implementation_task"] == "P03-T04" and r["final_status"] == "PENDING" for r in wms_rows)
    assert next(r for r in rows if r["requirement_id"] == "D04-01")["implementation_task"] == "P03-T01"
