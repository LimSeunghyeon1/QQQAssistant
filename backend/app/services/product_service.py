from __future__ import annotations

from typing import List

from app.models.domain import Product, ProductLocalizedInfo, ProductOption
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductLocalizedInfoCreate


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
        return entry

    def list(self) -> List[Product]:
        return list(self.repo.list())
