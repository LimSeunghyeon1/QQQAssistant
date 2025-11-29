from __future__ import annotations

from datetime import datetime
from typing import List

from app.models.domain import Order, OrderItem, OrderStatusHistory
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderCreate


class OrderService:
    def __init__(self, repo: OrderRepository) -> None:
        self.repo = repo

    def create_order(self, payload: OrderCreate) -> Order:
        order = Order(
            external_order_id=payload.external_order_id,
            channel_name=payload.channel_name,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            customer_address=payload.customer_address,
            order_datetime=payload.order_datetime,
            status=payload.status,
            total_amount_krw=payload.total_amount_krw,
        )
        for item in payload.items:
            order.items.append(
                OrderItem(
                    product_id=item.product_id,
                    product_option_id=item.product_option_id,
                    quantity=item.quantity,
                    unit_price_krw=item.unit_price_krw,
                )
            )
        order.status_history.append(
            OrderStatusHistory(
                previous_status=None,
                new_status=payload.status,
                changed_at=datetime.utcnow(),
                reason="initial import",
            )
        )
        order = self.repo.add(order)
        self.repo.session.flush()
        self.repo.session.refresh(order)
        return order

    def list(self, status: str | None = None) -> List[Order]:
        return list(self.repo.list(status=status))

    def update_status(self, order: Order, new_status: str, reason: str) -> Order:
        history = OrderStatusHistory(
            previous_status=order.status,
            new_status=new_status,
            changed_at=datetime.utcnow(),
            reason=reason,
        )
        order.status = new_status
        order.status_history.append(history)
        self.repo.session.flush()
        self.repo.session.refresh(order)
        return order
