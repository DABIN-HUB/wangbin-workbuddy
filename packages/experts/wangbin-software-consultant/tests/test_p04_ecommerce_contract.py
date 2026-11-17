"""Static D06 source contract checks, not a substitute for model or merchant QA."""
from pathlib import Path

AGENT = Path(__file__).resolve().parents[1] / "agents" / "wangbin-software-consultant.md"


def ecommerce():
    text = AGENT.read_text(encoding="utf-8")
    assert text.count("## 5G. 电商与小程序咨询") == 1
    return text.split("## 5G. 电商与小程序咨询", 1)[1].split("## 6. 隐私、合规与合作", 1)[0]


def test_product_form_and_reservation_without_implicit_payment():
    text = ecommerce()
    for phrase in ("展示型", "预约型", "B2B", "不生造 SKU、购物车或支付", "门店+时段+服务+容量", "不能先取消已确认预约", "授权订阅消息", "成熟小程序/商城 SaaS", "业务商城二开", "定制", "S06"):
        assert phrase in text


def test_payment_trust_and_race_boundaries():
    text = ecommerce()
    for phrase in ("服务端", "DECIMAL", "同键同载荷", "异载荷 409", "available >= qty", "客户端成功页≠服务端确认收款", "确实未付才取消", "迟到的真实成功支付通知", "重新核库存", "验签或验证凭证", "商户身份", "金额/币种一致", "重放不改订单/库存", "主动查询", "原路退款", "部分发货", "不能双主改库存"):
        assert phrase in text
    assert "不存支付密码" in text


def test_pages_entities_api_wbs_resources_and_platform_gate():
    text = ecommerce()
    for phrase in ("ECOM-C01", "`C04` 物流/售后", "ECOM-R01", "ECOM-M01", "`M03` 支付/退款对账", "shop_order_item", "shop_payment_event", "shop_refund_event", "shop_coupon_use", "未执行、待 DBA 审核", "POST /payments/notify", "POST /refunds", "D06-W01-BA", "W06-QA1", "CDN", "RPO/RTO", "支付商户资格", "NOT_TESTED", "N-ECOM-01/02", "N-ECOM-03/04", "N-ECOM-05/06"):
        assert phrase in text
    assert "L-01 形态/主体→02 SaaS/二开/定制" in text
    assert "→12 资金和履约签收" in text
