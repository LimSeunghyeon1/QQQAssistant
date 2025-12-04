import csv
import io
import json
import os
import csv
import io
import json
import os
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base
from app.models.domain import Product, ProductLocalizedInfo
from app.services.exporter_smartstore import SmartStoreExporter
from app.services.template_loader import ChannelTemplateLoader


engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def temp_loader(tmp_path: Path) -> ChannelTemplateLoader:
    base_path = tmp_path / "channel_formats"
    base_path.mkdir(parents=True, exist_ok=True)
    return ChannelTemplateLoader(base_path=base_path)


def _create_product(db_session) -> Product:
    product = Product(
        source_url="https://example.com/template",  # type: ignore[arg-type]
        source_site="TAOBAO",  # type: ignore[arg-type]
        raw_title="템플릿 상품",
        raw_price=10,
        raw_currency="CNY",
        image_urls=["https://example.com/img.jpg"],
    )
    db_session.add(product)
    db_session.flush()

    localization = ProductLocalizedInfo(
        product_id=product.id,
        locale="ko-KR",
        title="템플릿 상품",
        description="템플릿 설명",
        option_display_name_format="{color}",
    )
    db_session.add(localization)
    db_session.commit()
    return product


def test_smartstore_export_uses_default_template(db_session):
    product = _create_product(db_session)

    exporter = SmartStoreExporter()
    output = exporter.export_products(db_session, [product.id])
    rows = list(csv.reader(io.StringIO(output.getvalue())))

    assert rows[0] == [
        "상품명",
        "판매가",
        "재고수량",
        "옵션명",
        "옵션값",
        "상세설명",
        "대표이미지URL",
    ]


def test_template_loader_missing_template(temp_loader, db_session):
    with pytest.raises(ValueError, match="Template smartstore/custom not found"):
        temp_loader.load("smartstore", "custom", db_session)


def test_template_loader_invalid_template(temp_loader, db_session):
    bad_template = temp_loader.base_path / "smartstore_default.json"
    bad_template.write_text(json.dumps({"columns": [{"header": "상품명"}]}), encoding="utf-8")

    with pytest.raises(ValueError, match="missing a 'field'"):
        temp_loader.load("smartstore", "default", db_session)
