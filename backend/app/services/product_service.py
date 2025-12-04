from __future__ import annotations

from typing import List

from app.models.domain import Product, ProductLocalizedInfo, ProductOption
from app.repositories.product_repository import ProductRepository
from app.schemas.product import (
    ProductCreate,
    ProductLocalizedInfoCreate,
    ProductUpdate,
)


class ProductService:
    def __init__(self, repo: ProductRepository) -> None:
        self.repo = repo

    def ingest(self, payload: ProductCreate) -> Product:
        product = Product(
            source_url=payload.source_url,
            source_site=payload.source_site,
            raw_title=payload.raw_title,
            raw_price=payload.raw_price,
            raw_currency=payload.raw_currency,
            exchange_rate=payload.exchange_rate,
            margin_rate=payload.margin_rate,
            vat_rate=payload.vat_rate,
            shipping_fee=payload.shipping_fee,
            raw_description=payload.raw_description,
            thumbnail_image_urls=payload.thumbnail_image_urls,
            detail_image_urls=payload.detail_image_urls,
            clean_image_urls=payload.clean_image_urls,
            clean_detail_image_urls=payload.clean_detail_image_urls,
        )
        for option in payload.options:
            product.options.append(
                ProductOption(
                    option_key=option.option_key,
                    raw_name=option.raw_name,
                    raw_price_diff=option.raw_price_diff,
                )
            )
        return self.repo.add(product)

    def update_localization(
        self, product: Product, localization: ProductLocalizedInfoCreate
    ) -> ProductLocalizedInfo:
        entry = ProductLocalizedInfo(**localization.model_dump())
        product.localizations.append(entry)
        self.repo.session.flush()
        self.repo.session.refresh(product)
        return entry

    def list(self) -> List[Product]:
        return list(self.repo.list())

    def update_pricing(self, product: Product, payload: ProductUpdate) -> Product:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        self.repo.session.flush()
        self.repo.session.refresh(product)
        return product
