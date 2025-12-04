import asyncio
import csv
from datetime import datetime
import os
import sys
import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ.setdefault("TAOBAO_APP_KEY", "dummy")
os.environ.setdefault("TAOBAO_APP_SECRET", "dummy")

from app.database import Base, get_session
from app.models import domain  # noqa: F401
from app.models.domain import Product, ProductLocalizedInfo, ProductOption
from app.main import app
from app.services import PricingInputs, PricingService
from app.services.exporter_smartstore import SmartStoreExporter
from app.services.taobao_scraper import ScrapedOption, ScrapedProduct, TaobaoScraper
from app.services.translation_service import TranslationService


# Shared in-memory database for test cases
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def stub_taobao_scraper(monkeypatch):
    async def fake_fetch_product(self, url: str) -> ScrapedProduct:
        return ScrapedProduct(
            source_url=url,
            source_site="TAOBAO",
            title="Dummy Taobao Product",
            price=99.0,
            currency="CNY",
            image_urls=["https://example.com/img.jpg"],
            detail_image_urls=["https://example.com/detail1.jpg"],
            options=[ScrapedOption(option_key="default", raw_name="기본", raw_price_diff=0)],
        )

    monkeypatch.setattr(TaobaoScraper, "fetch_product", fake_fetch_product)


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
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def create_sample_product(client: TestClient, index: int = 1):
    payload = {
        "source_url": f"https://example.com/item/{index}",
        "source_site": "TAOBAO",
    }
    resp = client.post("/api/products/import", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    option_id = body["options"][0]["id"] if body["options"] else None
    return body["id"], option_id


def create_order(
    client: TestClient,
    *,
    product_id: int,
    product_option_id: int | None,
    external_id: str = "ORDER-001",
    status: str = "NEW",
    quantity: int = 1,
    unit_price: float = 23000,
):
    order_payload = {
        "external_order_id": external_id,
        "channel_name": "COUPANG",
        "customer_name": "홍길동",
        "customer_phone": "010-1234-5678",
        "customer_address": "서울시 어딘가",
        "order_datetime": datetime.utcnow().isoformat(),
        "status": status,
        "total_amount_krw": unit_price * quantity,
        "items": [
            {
                "product_id": product_id,
                "product_option_id": product_option_id,
                "quantity": quantity,
                "unit_price_krw": unit_price,
            }
        ],
    }
    resp = client.post("/api/orders", json=order_payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


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


def test_translation_endpoint_populates_localization(client: TestClient):
    product_id, option_id = create_sample_product(client, index=2)

    resp = client.post(
        f"/api/products/{product_id}/translate",
        json={"target_locale": "ko-KR", "provider": "gcloud"},
    )
    assert resp.status_code == 200, resp.text
    localized = resp.json()
    assert localized["locale"] == "ko-KR"

    products_resp = client.get("/api/products")
    product = next(p for p in products_resp.json() if p["id"] == product_id)
    assert product["options"][0]["localized_name"].endswith("(ko)")
    assert product["localizations"][0]["title"].endswith("(ko)")


def test_purchase_order_creation_updates_orders(client: TestClient):
    product_id, option_id = create_sample_product(client, index=3)
    order = create_order(
        client,
        product_id=product_id,
        product_option_id=option_id,
        external_id="ORDER-PO-1",
        status="NEW",
        quantity=2,
        unit_price=12000,
    )

    po_resp = client.post(
        "/api/purchase-orders", json={"order_ids": [order["id"]]}
    )
    assert po_resp.status_code == 200, po_resp.text
    purchase_orders = po_resp.json()
    assert len(purchase_orders) == 1
    purchase_order = purchase_orders[0]
    assert purchase_order["status"] == "CREATED"
    assert purchase_order["items"][0]["quantity"] == 2

    orders_resp = client.get("/api/orders")
    updated_order = next(o for o in orders_resp.json() if o["id"] == order["id"])
    assert updated_order["status"] == "PENDING_PURCHASE"
    assert any(
        h["new_status"] == "PENDING_PURCHASE" for h in updated_order["status_history"]
    )


def test_translation_service_translates_title_and_options(db_session):
    product = Product(
        source_url="https://example.com/item/translate",
        source_site="TAOBAO",
        raw_title="원본 타이틀",
        raw_description="원본 설명",
        raw_price=120.0,
        raw_currency="CNY",
    )
    option = ProductOption(
        product=product,
        option_key="color:red",
        raw_name="빨강",
        raw_price_diff=0,
    )
    db_session.add_all([product, option])
    db_session.commit()

    service = TranslationService(db_session)
    localized = service.translate_product(product.id, target_locale="ko-KR")

    assert localized.locale == "ko-KR"
    assert localized.title.endswith("(ko)")
    assert localized.description.endswith("(ko)")

    updated_option = db_session.get(ProductOption, option.id)
    assert updated_option.localized_name.endswith("(ko)")


def test_translation_service_raises_for_missing_product(db_session):
    service = TranslationService(db_session)
    with pytest.raises(LookupError):
        service.translate_product(9999)


def test_taobao_scraper_returns_default_option():
    scraper = TaobaoScraper()
    result = asyncio.run(scraper.fetch_product("https://example.com/item/scraper"))

    assert result.title == "Dummy Taobao Product"
    assert result.currency == "CNY"
    assert result.options
    assert result.options[0].option_key == "default"


def test_smartstore_export_returns_csv(client: TestClient):
    product_id, option_id = create_sample_product(client, index=4)

    localization_payload = {
        "locale": "ko-KR",
        "title": "샘플 상품",
        "description": "간단한 설명",
        "option_display_name_format": "{color}/{size}",
    }
    update_resp = client.put(
        f"/api/products/{product_id}/localization", json=localization_payload
    )
    assert update_resp.status_code == 200, update_resp.text

    export_resp = client.post(
        "/api/exports/channel/smartstore",
        json={"product_ids": [product_id], "template_type": "default"},
    )
    assert export_resp.status_code == 200, export_resp.text
    assert export_resp.headers["content-type"].startswith("text/csv")
    content = export_resp.text
    assert "상품명,판매가,재고수량" in content.splitlines()[0]
    assert "샘플 상품" in content


def test_smartstore_export_respects_requested_locale(client: TestClient):
    product_id, _ = create_sample_product(client, index=5)

    ko_localization = {
        "locale": "ko-KR",
        "title": "한국어 상품",
        "description": "한국어 설명",
        "option_display_name_format": "{color}/{size}",
    }
    en_localization = {
        "locale": "en-US",
        "title": "English Product",
        "description": "English description",
        "option_display_name_format": "{color}/{size}",
    }
    assert (
        client.put(
            f"/api/products/{product_id}/localization", json=ko_localization
        ).status_code
        == 200
    )
    assert (
        client.put(
            f"/api/products/{product_id}/localization", json=en_localization
        ).status_code
        == 200
    )

    ko_export = client.post(
        "/api/exports/channel/smartstore",
        json={
            "product_ids": [product_id],
            "template_type": "default",
            "locale": "ko-KR",
        },
    )
    en_export = client.post(
        "/api/exports/channel/smartstore",
        json={
            "product_ids": [product_id],
            "template_type": "default",
            "locale": "en-US",
        },
    )

    ko_rows = list(csv.reader(io.StringIO(ko_export.text)))
    en_rows = list(csv.reader(io.StringIO(en_export.text)))

    assert ko_rows[1][0] == "한국어 상품"
    assert ko_rows[1][5] == "한국어 설명"
    assert en_rows[1][0] == "English Product"
    assert en_rows[1][5] == "English description"


def test_export_channel_accepts_supported_channel(client: TestClient):
    product_id, _ = create_sample_product(client, index=6)

    resp = client.post(
        "/api/exports/channel/SMARTSTORE",
        json={"product_ids": [product_id], "template_type": "default"},
    )

    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/csv")


def test_export_channel_rejects_unsupported_channel(client: TestClient):
    resp = client.post(
        "/api/exports/channel/unknown",
        json={"product_ids": [1], "template_type": "default"},
    )

    assert resp.status_code == 400
    assert resp.json()["detail"] == "지원하지 않는 채널"


def test_export_endpoint_accepts_supported_channel(client: TestClient):
    product_id, _ = create_sample_product(client, index=7)

    resp = client.post(
        "/api/exports",
        params={"channel": "smartstore"},
        json={"product_ids": [product_id], "template_type": "default"},
    )

    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/csv")


def test_export_endpoint_rejects_unsupported_channel(client: TestClient):
    resp = client.post(
        "/api/exports",
        params={"channel": "unknown"},
        json={"product_ids": [1], "template_type": "default"},
    )

    assert resp.status_code == 400
    assert resp.json()["detail"] == "지원하지 않는 채널"


def test_smartstore_export_falls_back_to_available_localization(client: TestClient):
    product_id, _ = create_sample_product(client, index=6)

    ko_localization = {
        "locale": "ko-KR",
        "title": "기본 상품",
        "description": "한국어 기본 설명",
        "option_display_name_format": "{color}/{size}",
    }
    assert (
        client.put(
            f"/api/products/{product_id}/localization", json=ko_localization
        ).status_code
        == 200
    )

    export_resp = client.post(
        "/api/exports/channel/smartstore",
        json={
            "product_ids": [product_id],
            "template_type": "default",
            "locale": "en-US",
        },
    )

    rows = list(csv.reader(io.StringIO(export_resp.text)))

    assert rows[1][0] == "기본 상품"
    assert rows[1][5] == "한국어 기본 설명"


def test_pricing_service_combinations():
    service = PricingService()
    cases = [
        (PricingInputs(base_price=10, exchange_rate=1300, margin_rate=0.25, shipping_fee=4000), 21250),
        (
            PricingInputs(
                base_price=10,
                exchange_rate=1300,
                margin_rate=0.25,
                shipping_fee=4000,
                include_vat=True,
                vat_rate=0.1,
            ),
            23380,
        ),
        (PricingInputs(base_price=5, exchange_rate=1000), 5000),
        (
            PricingInputs(
                base_price=5,
                exchange_rate=1000,
                shipping_fee=2000,
                include_vat=True,
            ),
            7700,
        ),
    ]

    for inputs, expected in cases:
        assert service.calculate_sale_price(inputs) == expected


def test_smartstore_export_appends_return_policy_image(db_session):
    product = Product(
        source_url="https://example.com/policy",
        source_site="TAOBAO",
        raw_title="테스트 상품",
        raw_price=50,
        raw_currency="CNY",
    )
    db_session.add(product)
    db_session.flush()

    localization = ProductLocalizedInfo(
        product_id=product.id,
        locale="ko-KR",
        title="테스트 상품",
        description="상세 설명",
        option_display_name_format="{color}",
    )
    db_session.add(localization)
    db_session.commit()

    exporter = SmartStoreExporter(
        template_config={"return_policy_image_url": "https://example.com/return-policy.png"}
    )
    output = exporter.export_products(db_session, [product.id])
    rows = list(csv.reader(io.StringIO(output.getvalue())))

    assert "상세 설명" in rows[1][5]
    assert rows[1][5].endswith(
        'return-policy.png" alt="return-policy" /></div>'
    )
