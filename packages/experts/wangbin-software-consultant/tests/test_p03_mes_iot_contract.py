"""P03 static contract regression; not model, protocol, or platform validation."""
from decimal import Decimal
from pathlib import Path


AGENT = Path(__file__).resolve().parents[1] / "agents" / "wangbin-software-consultant.md"


def _section(start: str, end: str) -> str:
    source = AGENT.read_text(encoding="utf-8")
    assert source.count(start) == 1
    return source.split(start, 1)[1].split(end, 1)[0]


def test_mes_is_separate_from_monitoring_and_has_auditable_exceptions():
    mes = _section("## 5D. MES 制造执行咨询", "## 5E. 工业 IoT 与 MES 关联")
    for phrase in ("不可变随工单快照", "跨班交接", "返工复检", "报废", "lot-R", "lot-F", "outbox", "同一键同载荷", "异载荷 409", "ERP 主责", "MES 主责", "MES-P01", "MES-P04", "W07-QA1", "NOT_TESTED"):
        assert phrase in mes


def test_iot_protocols_quality_and_ambiguous_binding():
    iot = _section("## 5E. 工业 IoT 与 MES 关联", "## 6. 隐私、合规与合作")
    for phrase in ("Modbus TCP/RTU", "OPC UA", "IEC 60870-5-104", "MQTT", "source_time", "receive_time", "Bad/Uncertain", "断网", "按原键重传", "AMBIGUOUS/PENDING_REVIEW", "mes_telemetry_binding", "IOT-P01", "IOT-P05", "只想看 PLC 状态", "NOT_TESTED"):
        assert phrase in iot
    assert "未经真实设备联调写 NOT_TESTED" in iot
    assert "不能推出 GB、CPU 核数或网关台数" in iot


def test_sample_capacity_is_math_not_site_sizing():
    iot = _section("## 5E. 工业 IoT 与 MES 关联", "## 6. 隐私、合规与合作")
    rate = Decimal(500) * Decimal(100) / Decimal(5)
    assert rate == 10_000
    assert rate * 86400 == 864_000_000
    assert f"500×100÷5={rate:,.0f} 点值/秒" in iot
    assert f"{rate:,.0f}×86400={rate*86400:,.0f} 点值/日" in iot
    assert "纯示意" in iot


def test_frozen_n_mes_05_short_prompt_requires_both_rates_without_hardware_guarantee():
    prompt = "500 台×100 点/5秒"
    iot = _section("## 5E. 工业 IoT 与 MES 关联", "## 5F. WMS 仓储作业咨询")
    assert f"用户只给“{prompt}”时" in iot
    assert "本轮同时写出 10,000 点值/秒和 864,000,000 点值/日" in iot
    assert "不因用户没写“每天”就省略日点值" in iot
    assert "全天连续、所有点同频" in iot
    assert "不能推出 GB、CPU 核数或网关台数" in iot
