from __future__ import annotations

import csv
import io
from typing import List

from sqlalchemy.orm import Session

from app.models.domain import Product, ProductLocalizedInfo, ProductOption
from app.services.pricing import PricingService
from app.config import settings


class SmartStoreExporter:
    def __init__(self, template_config: dict | None = None) -> None:
        self.template_config = template_config or {}
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

        for product in products:
            localized: ProductLocalizedInfo | None = (
                session.query(ProductLocalizedInfo)
                .filter(
                    ProductLocalizedInfo.product_id == product.id,
                    ProductLocalizedInfo.locale == "ko-KR",
                )
                .first()
            )
            ko_title = localized.title if localized else product.raw_title
            description = localized.description if localized else ""
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
                    shipping_fee=self.template_config.get("shipping_fee"),
                    margin_rate=self.template_config.get("margin"),
                    vat_rate=self.template_config.get("vat"),
                    exchange_rate=self.template_config.get("exchange_rate"),
                )
                writer.writerow([ko_title, price, 0, "", "", description, self._primary_image(product)])
            else:
                for opt in options:
                    option_name = "옵션"
                    option_value = opt.localized_name or opt.raw_name
                    price = self.pricing.calculate_sale_price(
                        float(product.raw_price),
                        float(opt.raw_price_diff or 0),
                        shipping_fee=self.template_config.get("shipping_fee"),
                        margin_rate=self.template_config.get("margin"),
                        vat_rate=self.template_config.get("vat"),
                        exchange_rate=self.template_config.get("exchange_rate"),
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
