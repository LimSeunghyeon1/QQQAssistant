from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.models.domain import Product


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> Iterable[Product]:
        return self.session.query(Product).all()

    def get(self, product_id: int) -> Optional[Product]:
        return self.session.get(Product, product_id)

    def add(self, product: Product) -> Product:
        self.session.add(product)
        return product
