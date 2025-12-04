from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.domain import (
    AfterSalesCase,
    AfterSalesCaseStatus,
    AfterSalesCaseType,
    AfterSalesNotificationChannel,
    Order,
    OrderItem,
    RefundAmountType,
    RefundRecord,
    RefundStatus,
    Shipment,
)
from app.repositories.after_sales_repository import AfterSalesRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.shipment_repository import ShipmentRepository
from app.schemas.after_sales import (
    AfterSalesCaseCreate,
    AfterSalesCaseStatusUpdate,
    RefundRecordCreate,
    ShipmentLinkUpdate,
)
from app.services.order_service import OrderService


class AfterSalesService:
    def __init__(
        self,
        session: Session,
        after_sales_repo: AfterSalesRepository,
        order_repo: OrderRepository,
        shipment_repo: ShipmentRepository,
        order_service: OrderService,
    ) -> None:
        self.session = session
        self.after_sales_repo = after_sales_repo
        self.order_repo = order_repo
        self.shipment_repo = shipment_repo
        self.order_service = order_service

    def _get_order_or_404(self, order_id: int) -> Order:
        order = self.order_repo.get(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order

    def _get_order_item(self, order_item_id: int | None) -> OrderItem | None:
        if order_item_id is None:
            return None
        return self.session.get(OrderItem, order_item_id)

    def _get_shipment(self, shipment_id: int | None) -> Shipment | None:
        if shipment_id is None:
            return None
        shipment = self.shipment_repo.get(shipment_id)
        if not shipment:
            raise HTTPException(status_code=404, detail="Shipment not found")
        return shipment

    def create_case(self, payload: AfterSalesCaseCreate) -> AfterSalesCase:
        order = self._get_order_or_404(payload.order_id)
        order_item = self._get_order_item(payload.order_item_id)
        shipment = self._get_shipment(payload.shipment_id)

        case = AfterSalesCase(
            order=order,
            order_item=order_item,
            shipment=shipment,
            case_type=AfterSalesCaseType(payload.case_type),
            status=AfterSalesCaseStatus.OPEN,
            customer_notification_channel=AfterSalesNotificationChannel(
                payload.customer_notification_channel
            ),
            claim_amount_krw=payload.claim_amount_krw,
            summary=payload.summary,
            customer_note=payload.customer_note,
        )

        self.after_sales_repo.add_case(case)
        self.session.flush()
        self.session.refresh(case)

        if payload.order_status_after_creation:
            self.order_service.update_status(
                order,
                payload.order_status_after_creation,
                "after-sales case created",
            )
        return case

    def update_status(
        self, case_id: int, payload: AfterSalesCaseStatusUpdate
    ) -> AfterSalesCase:
        case = self.after_sales_repo.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="After-sales case not found")

        case.status = AfterSalesCaseStatus(payload.new_status)
        if payload.resolution_note:
            case.resolution_note = payload.resolution_note
        self.session.flush()
        self.session.refresh(case)

        if payload.order_status_after_update:
            order = self._get_order_or_404(case.order_id)
            self.order_service.update_status(
                order,
                payload.order_status_after_update,
                payload.resolution_note or "after-sales status updated",
            )
        return case

    def link_shipment(self, case_id: int, payload: ShipmentLinkUpdate) -> AfterSalesCase:
        case = self.after_sales_repo.get_case(case_id)
        if not case:
            raise HTTPException(status_code=404, detail="After-sales case not found")
        shipment = self._get_shipment(payload.shipment_id)
        case.shipment = shipment
        self.session.flush()
        self.session.refresh(case)
        return case

    def record_refund(self, payload: RefundRecordCreate) -> RefundRecord:
        order = self._get_order_or_404(payload.order_id)
        order_item = self._get_order_item(payload.order_item_id)
        shipment = self._get_shipment(payload.shipment_id)
        after_sales_case = None
        if payload.after_sales_case_id is not None:
            after_sales_case = self.after_sales_repo.get_case(payload.after_sales_case_id)
            if not after_sales_case:
                raise HTTPException(status_code=404, detail="After-sales case not found")

        refund = RefundRecord(
            order=order,
            order_item=order_item,
            shipment=shipment,
            after_sales_case=after_sales_case,
            amount_type=RefundAmountType(payload.amount_type),
            refund_amount_krw=payload.refund_amount_krw,
            refund_currency=payload.refund_currency,
            status=RefundStatus(payload.status),
            refund_method=payload.refund_method,
            reason=payload.reason,
            created_at=datetime.utcnow(),
        )
        self.after_sales_repo.add_refund(refund)
        self.session.flush()
        self.session.refresh(refund)

        if payload.order_status_after_refund:
            self.order_service.update_status(
                order,
                payload.order_status_after_refund,
                payload.reason or "refund recorded",
            )
        return refund
