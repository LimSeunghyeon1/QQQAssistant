from __future__ import annotations

from typing import List

from app.models.domain import OrderShipmentLink, Shipment
from app.repositories.order_repository import OrderRepository
from app.repositories.shipment_repository import ShipmentRepository
from app.schemas.shipment import ShipmentCreate


class ShipmentService:
    def __init__(self, shipments: ShipmentRepository, orders: OrderRepository) -> None:
        self.shipments = shipments
        self.orders = orders

    def create(self, payload: ShipmentCreate) -> Shipment:
        shipment = Shipment(
            carrier_name=payload.carrier_name,
            tracking_number=payload.tracking_number,
            shipment_type=payload.shipment_type,
            shipped_at=payload.shipped_at,
            delivered_at=payload.delivered_at,
        )
        for order_id in payload.linked_order_ids:
            order = self.orders.get(order_id)
            if order:
                link = OrderShipmentLink(order=order, shipment=shipment)
                shipment.orders.append(link)
        return self.shipments.add(shipment)

    def list(self) -> List[Shipment]:
        return list(self.shipments.list())
