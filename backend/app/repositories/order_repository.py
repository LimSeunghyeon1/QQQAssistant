from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.models.domain import Order


class OrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self, status: str | None = None) -> Iterable[Order]:
        query = self.session.query(Order)
        if status:
            query = query.filter(Order.status == status)
        return query.all()

    def get(self, order_id: int) -> Optional[Order]:
        return self.session.get(Order, order_id)

    def add(self, order: Order) -> Order:
        self.session.add(order)
        return order
