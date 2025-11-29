from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_session
from app.main import app


# Shared in-memory database for test cases
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
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


def create_sample_product(client: TestClient):
    payload = {
        "source_url": "https://example.com/item/1",
        "source_site": "TAOBAO",
        "raw_title": "Sample Bag",
        "raw_price": 12.5,
        "raw_currency": "CNY",
        "options": [
            {"option_key": "color:red/size:m", "raw_name": "Red / M", "raw_price_diff": 0.0}
        ],
    }
    resp = client.post("/api/products/import", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    return body["id"], body["options"][0]["id"]


def test_product_import_and_localization(client: TestClient):
    product_id, _ = create_sample_product(client)

    localization_payload = {
        "locale": "ko_KR",
        "title": "샘플 가방",
        "description": "가볍고 튼튼한 데일리 백",
        "option_display_name_format": "{color}/{size}",
    }
    resp = client.put(
        f"/api/products/{product_id}/localization", json=localization_payload
    )
    assert resp.status_code == 200, resp.text
    product = resp.json()
    assert product["localizations"][0]["title"] == "샘플 가방"


def test_order_creation_and_status_update(client: TestClient):
    product_id, option_id = create_sample_product(client)

    order_payload = {
        "external_order_id": "ORDER-001",
        "channel_name": "COUPANG",
        "customer_name": "홍길동",
        "customer_phone": "010-1234-5678",
        "customer_address": "서울시 어딘가",
        "order_datetime": datetime.utcnow().isoformat(),
        "status": "NEW",
        "total_amount_krw": 23000,
        "items": [
            {
                "product_id": product_id,
                "product_option_id": option_id,
                "quantity": 1,
                "unit_price_krw": 23000,
            }
        ],
    }
    resp = client.post("/api/orders", json=order_payload)
    assert resp.status_code == 200, resp.text
    order = resp.json()
    assert order["status"] == "NEW"
    assert order["items"][0]["product_option_id"] == option_id
    assert order["status_history"][0]["new_status"] == "NEW"

    update_resp = client.put(
        f"/api/orders/{order['id']}/status",
        params={"new_status": "OVERSEA_ORDERED", "reason": "발주 완료"},
    )
    assert update_resp.status_code == 200, update_resp.text
    updated = update_resp.json()
    assert updated["status"] == "OVERSEA_ORDERED"
    assert len(updated["status_history"]) == 2
    assert updated["status_history"][1]["new_status"] == "OVERSEA_ORDERED"


def test_shipment_creation_links_orders(client: TestClient):
    product_id, option_id = create_sample_product(client)

    order_payload = {
        "external_order_id": "ORDER-002",
        "channel_name": "NAVER",
        "customer_name": "김철수",
        "customer_phone": "010-9999-8888",
        "customer_address": "부산 somewhere",
        "order_datetime": datetime.utcnow().isoformat(),
        "status": "OVERSEA_IN_TRANSIT",
        "total_amount_krw": 15000,
        "items": [
            {
                "product_id": product_id,
                "product_option_id": option_id,
                "quantity": 2,
                "unit_price_krw": 7500,
            }
        ],
    }
    order_resp = client.post("/api/orders", json=order_payload)
    assert order_resp.status_code == 200, order_resp.text
    order_id = order_resp.json()["id"]

    shipment_payload = {
        "carrier_name": "CJ Logistics",
        "tracking_number": "TRACK123",
        "shipment_type": "OVERSEA",
        "linked_order_ids": [order_id],
    }
    shipment_resp = client.post("/api/shipments", json=shipment_payload)
    assert shipment_resp.status_code == 200, shipment_resp.text
    shipment = shipment_resp.json()
    assert shipment["tracking_number"] == "TRACK123"

    list_resp = client.get("/api/shipments")
    assert list_resp.status_code == 200, list_resp.text
    assert len(list_resp.json()) >= 1
