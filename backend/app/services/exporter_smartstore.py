from __future__ import annotations

import csv
import io
from typing import List

from sqlalchemy.orm import Session

from app.models.domain import Product, ProductLocalizedInfo, ProductOption
from app.services.pricing import PricingService
from app.config import settings


class SmartStoreExporter:
    def __init__(self, template_config: dict | None = None, locale: str | None = None) -> None:
        self.template_config = template_config or {}
        self.locale = locale
        self.pricing = PricingService()

    def export_products(self, session: Session, product_ids: List[int]) -> io.StringIO:
        if not product_ids:
            raise ValueError("product_ids is empty")

        products: List[Product] = (
            session.query(Product).filter(Product.id.in_(product_ids)).all()
        )

        output = io.StringIO()
        writer = csv.writer(output)
        header = [
            "상품명",
            "판매가",
            "재고수량",
            "옵션명",
            "옵션값",
            "상세설명",
            "대표이미지URL",
        ]
        writer.writerow(header)

        target_locale = (
            self.locale or self.template_config.get("locale") or "ko-KR"
        )

        for product in products:
            localizations: List[ProductLocalizedInfo] = list(product.localizations)
            localized = next(
                (loc for loc in localizations if loc.locale == target_locale), None
            )

            fallback_localized = localized or (localizations[0] if localizations else None)

            ko_title = self._pick_title(product, localized, fallback_localized)
            description = self._pick_description(
                product, localized, fallback_localized, localizations
            )
            policy_image = self.template_config.get("return_policy_image_url")
            if policy_image:
                policy_block = f'<div><img src="{policy_image}" alt="return-policy" /></div>'
                description = f"{description}\n{policy_block}" if description else policy_block

            options: List[ProductOption] = (
                session.query(ProductOption)
                .filter(ProductOption.product_id == product.id)
                .all()
            )

            if not options:
                price = self.pricing.calculate_sale_price(
                    float(product.raw_price),
                    shipping_fee=self._shipping_fee(product),
                    margin_rate=self._margin(product),
                    vat_rate=self._vat(product),
                    exchange_rate=self._exchange_rate(product),
                )
                writer.writerow([ko_title, price, 0, "", "", description, self._primary_image(product)])
            else:
                for opt in options:
                    option_name = "옵션"
                    option_value = opt.localized_name or opt.raw_name
                    price = self.pricing.calculate_sale_price(
                        float(product.raw_price),
                        float(opt.raw_price_diff or 0),
                        shipping_fee=self._shipping_fee(product),
                        margin_rate=self._margin(product),
                        vat_rate=self._vat(product),
                        exchange_rate=self._exchange_rate(product),
                    )
                    writer.writerow(
                        [
                            ko_title,
                            price,
                            0,
                            option_name,
                            option_value,
                            description,
                            self._primary_image(product),
                        ]
                    )

        output.seek(0)
        return output

    def _pick_title(
        self,
        product: Product,
        localized: ProductLocalizedInfo | None,
        fallback_localized: ProductLocalizedInfo | None,
    ) -> str:
        if localized and localized.title:
            return localized.title
        if fallback_localized and fallback_localized.title:
            return fallback_localized.title
        return product.raw_title

    def _pick_description(
        self,
        product: Product,
        localized: ProductLocalizedInfo | None,
        fallback_localized: ProductLocalizedInfo | None,
        all_localizations: List[ProductLocalizedInfo],
    ) -> str:
        if localized and localized.description:
            return localized.description
        if fallback_localized and fallback_localized.description:
            return fallback_localized.description
        for loc in all_localizations:
            if loc.description:
                return loc.description
        return product.raw_description or ""

    def _append_return_policy(self, description: str) -> str:
        image_url = self.template_config.get("return_policy_image_url") or settings.return_policy_image_url
        if image_url:
            return f"{description}<br/><img src=\"{image_url}\" alt=\"return_policy\" />"
        return description

    def _primary_image(self, product: Product) -> str:
        if product.clean_image_urls:
            return product.clean_image_urls[0]
        if product.image_urls:
            return product.image_urls[0]
        return ""

    def _exchange_rate(self, product: Product) -> float | None:
        if product.exchange_rate is not None:
            return float(product.exchange_rate)
        exchange_rate = self.template_config.get("exchange_rate")
        return float(exchange_rate) if exchange_rate is not None else None

    def _margin(self, product: Product) -> float | None:
        if product.margin_rate is not None:
            return float(product.margin_rate)
        margin = self.template_config.get("margin")
        return float(margin) if margin is not None else None

    def _vat(self, product: Product) -> float | None:
        if product.vat_rate is not None:
            return float(product.vat_rate)
        vat = self.template_config.get("vat")
        return float(vat) if vat is not None else None

    def _shipping_fee(self, product: Product) -> float | None:
        if product.shipping_fee is not None:
            return float(product.shipping_fee)
        shipping_fee = self.template_config.get("shipping_fee")
        return float(shipping_fee) if shipping_fee is not None else None
