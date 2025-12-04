from __future__ import annotations

import csv
import io
from typing import List

from sqlalchemy.orm import Session

from app.models.domain import Product, ProductLocalizedInfo, ProductOption
from app.services.pricing import PricingService
from app.config import settings
from app.services.template_loader import (
    ChannelTemplate,
    ChannelTemplateLoader,
)


class SmartStoreExporter:
    def __init__(
        self,
        template_config: dict | None = None,
        locale: str | None = None,
        template_type: str = "default",
        template_loader: ChannelTemplateLoader | None = None,
    ) -> None:
        self.template_config = template_config or {}
        self.locale = locale
        self.template_type = template_type
        self.template_loader = template_loader or ChannelTemplateLoader()
        self.pricing = PricingService()

    def export_products(self, session: Session, product_ids: List[int]) -> io.StringIO:
        if not product_ids:
            raise ValueError("product_ids is empty")

        template = self.template_loader.load("smartstore", self.template_type, session)

        products: List[Product] = (
            session.query(Product).filter(Product.id.in_(product_ids)).all()
        )

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([column.header for column in template.columns])

        target_locale = self._target_locale(template)

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
            description = self._append_return_policy(description)

            options: List[ProductOption] = (
                session.query(ProductOption)
                .filter(ProductOption.product_id == product.id)
                .all()
            )

            if not options:
                row = self._build_row(
                    template,
                    product,
                    ko_title,
                    description,
                    option=None,
                )
                writer.writerow(row)
            else:
                for opt in options:
                    row = self._build_row(
                        template,
                        product,
                        ko_title,
                        description,
                        option=opt,
                    )
                    writer.writerow(row)

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
            policy_block = f'<div><img src="{image_url}" alt="return-policy" /></div>'
            return f"{description}\n{policy_block}" if description else policy_block
        return description

    def _primary_image(self, product: Product) -> str:
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

    def _target_locale(self, template: ChannelTemplate) -> str:
        return (
            self.locale
            or self.template_config.get("locale")
            or template.locale
            or "ko-KR"
        )

    def _build_row(
        self,
        template: ChannelTemplate,
        product: Product,
        title: str,
        description: str,
        option: ProductOption | None,
    ) -> list:
        price = self.pricing.calculate_sale_price(
            float(product.raw_price),
            float(option.raw_price_diff or 0) if option else 0,
            shipping_fee=self._shipping_fee(product),
            margin_rate=self._margin(product),
            vat_rate=self._vat(product),
            exchange_rate=self._exchange_rate(product),
        )

        row_context = {
            "title": title,
            "price": price,
            "stock": 0,
            "option_name": "옵션" if option else "",
            "option_value": (option.localized_name or option.raw_name) if option else "",
            "description": description,
            "primary_image": self._primary_image(product),
        }

        row: list = []
        for column in template.columns:
            if column.field not in row_context:
                raise ValueError(
                    f"Template {template.channel}/{template.template_type} references unknown field '{column.field}'"
                )
            row.append(row_context[column.field])
        return row
