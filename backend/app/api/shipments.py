from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_session
from app.repositories.order_repository import OrderRepository
from app.repositories.shipment_repository import ShipmentRepository
from app.schemas.shipment import ShipmentCreate, ShipmentRead
from app.services.shipment_service import ShipmentService

router = APIRouter(prefix="/api/shipments", tags=["shipments"])


def get_service(session: Session = Depends(get_session)) -> ShipmentService:
    shipments = ShipmentRepository(session)
    orders = OrderRepository(session)
    return ShipmentService(shipments, orders)


@router.post("", response_model=ShipmentRead)
def create_shipment(
    payload: ShipmentCreate, service: ShipmentService = Depends(get_service)
):
    return service.create(payload)


@router.get("", response_model=list[ShipmentRead])
def list_shipments(service: ShipmentService = Depends(get_service)):
    return service.list()
