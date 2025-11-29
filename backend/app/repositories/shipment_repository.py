from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.models.domain import Shipment


class ShipmentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self) -> Iterable[Shipment]:
        return self.session.query(Shipment).all()

    def get(self, shipment_id: int) -> Optional[Shipment]:
        return self.session.get(Shipment, shipment_id)

    def add(self, shipment: Shipment) -> Shipment:
        self.session.add(shipment)
        return shipment
