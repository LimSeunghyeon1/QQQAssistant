from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_session
from app.models.domain import Order
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderCreate, OrderRead
from app.services.order_service import OrderService

router = APIRouter(prefix="/api/orders", tags=["orders"])


def get_service(session: Session = Depends(get_session)) -> OrderService:
    repo = OrderRepository(session)
    return OrderService(repo)


@router.post("", response_model=OrderRead)
def create_order(payload: OrderCreate, service: OrderService = Depends(get_service)):
    order = service.create_order(payload)
    return order


@router.get("", response_model=list[OrderRead])
def list_orders(status: str | None = None, service: OrderService = Depends(get_service)):
    return service.list(status=status)


@router.put("/{order_id}/status", response_model=OrderRead)
def update_status(
    order_id: int,
    new_status: str,
    reason: str,
    service: OrderService = Depends(get_service),
    session: Session = Depends(get_session),
):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    updated = service.update_status(order, new_status, reason)
    return updated
