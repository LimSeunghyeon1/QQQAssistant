from datetime import datetime
import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base, get_session
from app.main import app
from app.models.domain import (
    AfterSalesCaseStatus,
    AfterSalesCaseType,
    AfterSalesNotificationChannel,
    Order,
    OrderItem,
    Product,
    ProductOption,
    RefundAmountType,
    RefundStatus,
)


engine = create_engine(
    "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    def override_get_session():
        session = TestingSessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def product_and_option():
    session = TestingSessionLocal()
    product = Product(
        source_url="https://example.com/item/1",
        source_site="TAOBAO",
        raw_title="테스트 상품",
        raw_description="desc",
        raw_price=10,
        raw_currency="CNY",
        exchange_rate=180.0,
        margin_rate=10.0,
        vat_rate=10.0,
        shipping_fee=3000,
        image_urls=[],
        detail_image_urls=[],
    )
    option = ProductOption(option_key="default", raw_name="단일", raw_price_diff=0)
    product.options.append(option)
    session.add(product)
    session.commit()
    session.refresh(product)
    session.refresh(option)
    session.close()
    return product.id, option.id


def create_order(
    client: TestClient, product_id: int, option_id: int | None
) -> tuple[int, int]:
    resp = client.post(
        "/api/orders",
        json={
            "external_order_id": "ORDER-100",
            "channel_name": "COUPANG",
            "customer_name": "고객",
            "customer_phone": "010-0000-0000",
            "customer_address": "서울",
            "order_datetime": datetime.utcnow().isoformat(),
            "status": "NEW",
            "total_amount_krw": 12000,
            "items": [
                {
                    "product_id": product_id,
                    "product_option_id": option_id,
                    "quantity": 1,
                    "unit_price_krw": 12000,
                }
            ],
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    return data["id"], data["items"][0]["id"]


def test_create_after_sales_case_updates_order_history(client: TestClient, product_and_option):
    product_id, option_id = product_and_option
    order_id, order_item_id = create_order(client, product_id, option_id)

    payload = {
        "order_id": order_id,
        "order_item_id": order_item_id,
        "case_type": AfterSalesCaseType.RETURN.value,
        "customer_notification_channel": AfterSalesNotificationChannel.IN_APP.value,
        "summary": "상품 불량",
        "order_status_after_creation": "AFTER_SALES",
    }

    resp = client.post("/api/after-sales/cases", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == AfterSalesCaseStatus.OPEN.value

    session = TestingSessionLocal()
    refreshed_order = session.get(Order, order_id)
    assert refreshed_order.status == "AFTER_SALES"
    assert len(refreshed_order.status_history) == 2
    assert refreshed_order.status_history[-1].new_status == "AFTER_SALES"
    session.close()


def test_update_case_status_and_link_shipment(client: TestClient, product_and_option):
    product_id, option_id = product_and_option
    order_id, order_item_id = create_order(client, product_id, option_id)

    case_resp = client.post(
        "/api/after-sales/cases",
        json={
        "order_id": order_id,
        "order_item_id": order_item_id,
            "case_type": AfterSalesCaseType.EXCHANGE.value,
        },
    )
    case_id = case_resp.json()["id"]

    shipment_resp = client.post(
        "/api/shipments",
        json={
            "carrier_name": "CJ",
            "tracking_number": "RET-001",
            "shipment_type": "RETURN",
            "linked_order_ids": [order_id],
        },
    )
    shipment_id = shipment_resp.json()["id"]

    update_resp = client.put(
        f"/api/after-sales/cases/{case_id}/status",
        json={
            "new_status": AfterSalesCaseStatus.WAITING_REFUND.value,
            "resolution_note": "재배송 준비",
            "order_status_after_update": "WAITING_REFUND",
        },
    )
    assert update_resp.status_code == 200

    link_resp = client.put(
        f"/api/after-sales/cases/{case_id}/shipment",
        json={"shipment_id": shipment_id},
    )
    assert link_resp.status_code == 200
    assert link_resp.json()["shipment_id"] == shipment_id

    session = TestingSessionLocal()
    refreshed_order = session.get(Order, order_id)
    assert refreshed_order.status == "WAITING_REFUND"
    assert refreshed_order.status_history[-1].new_status == "WAITING_REFUND"
    session.close()


def test_record_refund_updates_order_history(client: TestClient, product_and_option):
    product_id, option_id = product_and_option
    order_id, order_item_id = create_order(client, product_id, option_id)

    case_resp = client.post(
        "/api/after-sales/cases",
        json={
            "order_id": order_id,
            "order_item_id": order_item_id,
            "case_type": AfterSalesCaseType.RETURN.value,
        },
    )
    case_id = case_resp.json()["id"]

    refund_resp = client.post(
        "/api/after-sales/refunds",
        json={
            "order_id": order_id,
            "order_item_id": order_item_id,
            "after_sales_case_id": case_id,
            "amount_type": RefundAmountType.FULL.value,
            "refund_amount_krw": 12000,
            "status": RefundStatus.PROCESSED.value,
            "reason": "전액 환불",
            "order_status_after_refund": "REFUND_COMPLETED",
        },
    )
    assert refund_resp.status_code == 200, refund_resp.text

    session = TestingSessionLocal()
    refreshed_order = session.get(Order, order_id)
    assert refreshed_order.status == "REFUND_COMPLETED"
    assert refreshed_order.status_history[-1].new_status == "REFUND_COMPLETED"

    order_item = session.get(OrderItem, order_item_id)
    assert order_item.refund_records[0].refund_amount_krw == 12000
    session.close()
