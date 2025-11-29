from __future__ import annotations

import csv
import io
from typing import List

from sqlalchemy.orm import Session

from app.models.domain import Product, ProductLocalizedInfo, ProductOption


class SmartStoreExporter:
    def __init__(self, template_config: dict | None = None) -> None:
        self.template_config = template_config or {}

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

            options: List[ProductOption] = (
                session.query(ProductOption)
                .filter(ProductOption.product_id == product.id)
                .all()
            )

            if not options:
                writer.writerow([ko_title, product.raw_price, 0, "", "", description, ""])
            else:
                for opt in options:
                    option_name = "옵션"
                    option_value = opt.localized_name or opt.raw_name
                    writer.writerow(
                        [
                            ko_title,
                            float(product.raw_price) + float(opt.raw_price_diff or 0),
                            0,
                            option_name,
                            option_value,
                            description,
                            "",
                        ]
                    )

        output.seek(0)
        return output
