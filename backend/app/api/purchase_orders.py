from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_session
from app.models.domain import PurchaseOrder
from app.schemas.purchase_order import (
    PurchaseOrderCreateRequest,
    PurchaseOrderRead,
    PurchaseOrderStatusUpdateRequest,
)
from app.services.purchase_order_service import PurchaseOrderService

router = APIRouter(prefix="/api/purchase-orders", tags=["purchase_orders"])


@router.post("", response_model=list[PurchaseOrderRead])
def create_purchase_orders(
    payload: PurchaseOrderCreateRequest = Body(...),
    session: Session = Depends(get_session),
):
    service = PurchaseOrderService(session)
    purchase_orders = service.create_from_orders(
        order_ids=payload.order_ids, created_by="system"
    )
    return purchase_orders


@router.get("/{po_id}", response_model=PurchaseOrderRead)
def get_purchase_order(po_id: int, session: Session = Depends(get_session)):
    po = session.get(PurchaseOrder, po_id)
    if not po:
        raise HTTPException(status_code=404, detail="PurchaseOrder not found")
    return po


@router.put("/{po_id}/status", response_model=PurchaseOrderRead)
def update_purchase_order_status(
    po_id: int,
    payload: PurchaseOrderStatusUpdateRequest,
    session: Session = Depends(get_session),
):
    service = PurchaseOrderService(session)
    try:
        purchase_order = service.update_status(
            po_id, payload.new_status, reason=payload.reason
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return purchase_order
