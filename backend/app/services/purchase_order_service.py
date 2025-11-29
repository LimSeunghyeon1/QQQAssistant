from __future__ import annotations

from collections import defaultdict
from typing import List

from sqlalchemy.orm import Session

from app.models.domain import (
    Order,
    OrderItem,
    OrderStatusHistory,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseOrderSourceLink,
    PurchaseOrderStatusHistory,
)


class PurchaseOrderService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_from_orders(
        self, order_ids: List[int] | None = None, created_by: str | None = None
    ) -> List[PurchaseOrder]:
        query = self.session.query(Order).filter(Order.status == "NEW")
        if order_ids:
            query = query.filter(Order.id.in_(order_ids))
        orders: List[Order] = query.all()

        if not orders:
            return []

        group_map: dict[tuple[int, int | None], List[OrderItem]] = defaultdict(list)
        for order in orders:
            for item in order.items:
                key = (item.product_id, item.product_option_id)
                group_map[key].append(item)

        purchase_order = PurchaseOrder(
            supplier_name="TAOBAO_DEFAULT",
            status="CREATED",
            currency="CNY",
            total_amount=0,
            created_by=created_by,
        )
        self.session.add(purchase_order)
        self.session.flush()

        created_history = PurchaseOrderStatusHistory(
            purchase_order_id=purchase_order.id,
            previous_status=None,
            new_status="CREATED",
            reason="Purchase order created",
        )
        self.session.add(created_history)

        total_amount = 0
        for (product_id, option_id), items in group_map.items():
            quantity = sum(i.quantity for i in items)
            unit_cost = float(items[0].unit_price_krw or 0)
            line_total = unit_cost * quantity

            po_item = PurchaseOrderItem(
                purchase_order_id=purchase_order.id,
                product_id=product_id,
                product_option_id=option_id,
                quantity=quantity,
                unit_cost=unit_cost,
                line_total=line_total,
            )
            self.session.add(po_item)
            self.session.flush()

            total_amount += line_total

            for i in items:
                link = PurchaseOrderSourceLink(
                    purchase_order_item_id=po_item.id,
                    order_id=i.order_id,
                    order_item_id=i.id,
                    source_quantity=i.quantity,
                )
                self.session.add(link)

        purchase_order.total_amount = total_amount
        self.session.add(purchase_order)

        for order in orders:
            order.status = "PENDING_PURCHASE"
            history = OrderStatusHistory(
                order_id=order.id,
                previous_status="NEW",
                new_status="PENDING_PURCHASE",
                reason="Aggregated into purchase order",
            )
            self.session.add(history)
            self.session.add(order)

        self.session.flush()
        return [purchase_order]

    def update_status(
        self, purchase_order_id: int, new_status: str, reason: str | None = None
    ) -> PurchaseOrder:
        purchase_order = self.session.get(PurchaseOrder, purchase_order_id)
        if not purchase_order:
            raise LookupError("Purchase order not found")

        history = PurchaseOrderStatusHistory(
            purchase_order_id=purchase_order.id,
            previous_status=purchase_order.status,
            new_status=new_status,
            reason=reason,
        )
        purchase_order.status = new_status
        self.session.add(purchase_order)
        self.session.add(history)
        self.session.flush()
        return purchase_order
