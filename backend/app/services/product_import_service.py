from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.domain import Product, ProductOption
from app.services.image_cleanup import ImageCleanupService
from app.services.taobao_scraper import ScrapedOption, ScrapedProduct, TaobaoScraper


class ProductImportService:
    def __init__(
        self,
        session: Session,
        *,
        image_cleanup_service: ImageCleanupService | None = None,
    ) -> None:
        self.session = session
        self.scrapers = {"TAOBAO": TaobaoScraper()}
        self.image_cleanup_service = image_cleanup_service or ImageCleanupService()

    async def import_product(self, source_url: str, source_site: str) -> Product:
        scraper = self.scrapers.get(source_site.upper())
        if not scraper:
            raise ValueError("Unsupported source_site")

        existing = (
            self.session.query(Product).filter(Product.source_url == source_url).first()
        )
        if existing:
            return existing

        scraped: ScrapedProduct = await scraper.fetch_product(source_url)

        if not scraped.options:
            scraped.options = [
                ScrapedOption(option_key="default", raw_name="Default", raw_price_diff=0.0)
            ]

        clean_image_urls = await self.image_cleanup_service.cleanup_images(
            scraped.image_urls
        )
        clean_detail_image_urls = await self.image_cleanup_service.cleanup_images(
            scraped.detail_image_urls
        )

        product = Product(
            source_url=scraped.source_url,
            source_site=scraped.source_site,
            raw_title=scraped.title,
            raw_price=scraped.price,
            raw_currency=scraped.currency,
            image_urls=scraped.image_urls,
            detail_image_urls=scraped.detail_image_urls,
            clean_image_urls=clean_image_urls,
            clean_detail_image_urls=clean_detail_image_urls,
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
