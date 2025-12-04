from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.domain import Product, ProductOption
from app.services.taobao_scraper import (
    ScrapeFailed,
    ScrapedOption,
    ScrapedProduct,
    TaobaoScraper,
)


class ProductImportService:
    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session
        self.scrapers = {
            "TAOBAO": TaobaoScraper(source_site="TAOBAO"),
            "1688": TaobaoScraper(
                source_site="1688", item_source_market="CBU_MARKET"
            ),
        }

    async def import_product(self, source_url: str, source_site: str) -> Product:
        scraper = self.scrapers.get(source_site.upper())
        if not scraper:
            raise ValueError("Unsupported source_site")

        existing = (
            self.session.query(Product).filter(Product.source_url == source_url).first()
        )
        if existing:
            return existing

        try:
            scraped: ScrapedProduct = await scraper.fetch_product(source_url)
        except ScrapeFailed as exc:
            raise ValueError(
                "상품 정보를 불러오지 못했습니다. URL을 확인하고 다시 시도해주세요."
            ) from exc

        if not scraped.options:
            scraped.options = [
                ScrapedOption(option_key="default", raw_name="Default", raw_price_diff=0.0)
            ]

        product = Product(
            source_url=scraped.source_url,
            source_site=scraped.source_site,
            raw_title=scraped.title,
            raw_price=scraped.price,
            raw_currency=scraped.currency,
            image_urls=scraped.image_urls,
            detail_image_urls=scraped.detail_image_urls,
        )
        self.session.add(product)
        self.session.flush()

        for opt in scraped.options:
            option = ProductOption(
                product_id=product.id,
                option_key=opt.option_key,
                raw_name=opt.raw_name,
                raw_price_diff=opt.raw_price_diff or 0,
            )
            self.session.add(option)

        self.session.flush()
        return product
