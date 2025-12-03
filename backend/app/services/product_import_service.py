from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.domain import Product, ProductOption
from app.services.image_cleanup import ImageCleanupService
from app.services.taobao_scraper import ScrapedProduct, TaobaoScraper


class ProductImportService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.scrapers = {"TAOBAO": TaobaoScraper()}
        self.image_cleanup = ImageCleanupService()

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

        cleaned_thumbs = self.image_cleanup.clean_images(scraped.image_urls)
        cleaned_details = self.image_cleanup.clean_images(scraped.detail_image_urls)

        product = Product(
            source_url=scraped.source_url,
            source_site=scraped.source_site,
            raw_title=scraped.title,
            raw_price=scraped.price,
            raw_currency=scraped.currency,
            raw_description=scraped.description_html,
            thumbnail_image_urls=scraped.image_urls,
            detail_image_urls=scraped.detail_image_urls,
            clean_image_urls=cleaned_thumbs,
            clean_detail_image_urls=cleaned_details,
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
