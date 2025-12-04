from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_session
from app.repositories.after_sales_repository import AfterSalesRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.shipment_repository import ShipmentRepository
from app.schemas.after_sales import (
    AfterSalesCaseCreate,
    AfterSalesCaseRead,
    AfterSalesCaseStatusUpdate,
    RefundRecordCreate,
    RefundRecordRead,
    ShipmentLinkUpdate,
)
from app.services.after_sales_service import AfterSalesService
from app.services.order_service import OrderService

router = APIRouter(prefix="/api/after-sales", tags=["after_sales"])


def get_service(session: Session = Depends(get_session)) -> AfterSalesService:
    after_sales_repo = AfterSalesRepository(session)
    order_repo = OrderRepository(session)
    shipment_repo = ShipmentRepository(session)
    order_service = OrderService(order_repo)
    return AfterSalesService(
        session, after_sales_repo, order_repo, shipment_repo, order_service
    )


@router.post("/cases", response_model=AfterSalesCaseRead)
def create_case(
    payload: AfterSalesCaseCreate, service: AfterSalesService = Depends(get_service)
):
    return service.create_case(payload)


@router.put("/cases/{case_id}/status", response_model=AfterSalesCaseRead)
def update_case_status(
    case_id: int,
    payload: AfterSalesCaseStatusUpdate,
    service: AfterSalesService = Depends(get_service),
):
    return service.update_status(case_id, payload)


@router.put("/cases/{case_id}/shipment", response_model=AfterSalesCaseRead)
def link_shipment(
    case_id: int,
    payload: ShipmentLinkUpdate,
    service: AfterSalesService = Depends(get_service),
):
    return service.link_shipment(case_id, payload)


@router.post("/refunds", response_model=RefundRecordRead)
def record_refund(
    payload: RefundRecordCreate, service: AfterSalesService = Depends(get_service)
):
    refund = service.record_refund(payload)
    if not refund:
        raise HTTPException(status_code=400, detail="Failed to record refund")
    return refund
