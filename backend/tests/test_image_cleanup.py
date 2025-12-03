from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest
import importlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
importlib.invalidate_caches()
from PIL import Image, ImageDraw
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import domain  # noqa: F401
from app.services.image_cleanup import ImageCleanupService
from app.services.product_import_service import ProductImportService
from app.services.taobao_scraper import ScrapedProduct


def _build_test_image(tmp_path: Path, text: str = "SECRET") -> Path:
    image = Image.new("RGB", (200, 100), color="white")
    draw = ImageDraw.Draw(image)
    draw.text((20, 35), text, fill="black")
    path = tmp_path / "source.png"
    image.save(path)
    return path


def test_cleanup_masks_text(tmp_path: Path):
    source = _build_test_image(tmp_path)
    service = ImageCleanupService(storage_dir=tmp_path / "storage")

    original_boxes = service._detect_text_regions(Image.open(source))
    assert original_boxes, "Should detect at least one text region"

    cleaned_urls = asyncio.run(service.cleanup_images([str(source)]))
    cleaned_path = Path(cleaned_urls[0])
    assert cleaned_path.exists()

    original = Image.open(source).convert("RGB")
    cleaned = Image.open(cleaned_path).convert("RGB")
    x1, y1, x2, y2 = original_boxes[0]
    center = ((x1 + x2) // 2, (y1 + y2) // 2)
    assert original.getpixel(center) != cleaned.getpixel(center)


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_importer_persists_clean_urls(db_session, tmp_path: Path):
    source = _build_test_image(tmp_path)
    storage_dir = tmp_path / "storage"
    service = ImageCleanupService(storage_dir=storage_dir)

    class FakeScraper:
        async def fetch_product(self, url: str) -> ScrapedProduct:
            return ScrapedProduct(
                source_url=url,
                source_site="TAOBAO",
                title="Demo",
                price=12.5,
                currency="CNY",
                image_urls=[str(source)],
                detail_image_urls=[str(source)],
                options=[],
            )

    importer = ProductImportService(db_session, image_cleanup_service=service)
    importer.scrapers["TAOBAO"] = FakeScraper()

    product = asyncio.run(importer.import_product("local://item/123", "TAOBAO"))
    db_session.refresh(product)

    assert product.image_urls == [str(source)]
    assert product.detail_image_urls == [str(source)]
    assert product.clean_image_urls and product.clean_image_urls[0] != str(source)
    assert product.clean_detail_image_urls and product.clean_detail_image_urls[0] != str(source)
    assert Path(product.clean_image_urls[0]).exists()
    assert Path(product.clean_detail_image_urls[0]).exists()
