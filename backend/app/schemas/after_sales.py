from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.domain import (
    AfterSalesCaseStatus,
    AfterSalesCaseType,
    AfterSalesNotificationChannel,
    RefundAmountType,
    RefundStatus,
)


class AfterSalesCaseCreate(BaseModel):
    order_id: int
    order_item_id: Optional[int] = None
    shipment_id: Optional[int] = None
    case_type: AfterSalesCaseType
    customer_notification_channel: AfterSalesNotificationChannel = (
        AfterSalesNotificationChannel.IN_APP
    )
    claim_amount_krw: Optional[float] = None
    summary: Optional[str] = None
    customer_note: Optional[str] = None
    order_status_after_creation: Optional[str] = Field(
        default=None,
        description="If provided, the order status and history will be updated when the case is created.",
    )


class AfterSalesCaseStatusUpdate(BaseModel):
    new_status: AfterSalesCaseStatus
    resolution_note: Optional[str] = None
    order_status_after_update: Optional[str] = Field(
        default=None,
        description="If provided, the order status is updated alongside the case status.",
    )


class ShipmentLinkUpdate(BaseModel):
    shipment_id: int


class RefundRecordCreate(BaseModel):
    order_id: int
    order_item_id: Optional[int] = None
    shipment_id: Optional[int] = None
    after_sales_case_id: Optional[int] = None
    amount_type: RefundAmountType
    refund_amount_krw: float
    refund_currency: str = "KRW"
    status: RefundStatus = RefundStatus.REQUESTED
    refund_method: Optional[str] = None
    reason: Optional[str] = None
    order_status_after_refund: Optional[str] = Field(
        default=None,
        description="If provided, reflects refund progress on the order status history.",
    )


class RefundRecordRead(BaseModel):
    id: int
    order_id: int
    order_item_id: Optional[int]
    shipment_id: Optional[int]
    after_sales_case_id: Optional[int]
    amount_type: RefundAmountType
    refund_amount_krw: float
    refund_currency: str
    status: RefundStatus
    refund_method: Optional[str]
    reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AfterSalesCaseRead(BaseModel):
    id: int
    order_id: int
    order_item_id: Optional[int]
    shipment_id: Optional[int]
    case_type: AfterSalesCaseType
    status: AfterSalesCaseStatus
    customer_notification_channel: AfterSalesNotificationChannel
    claim_amount_krw: Optional[float]
    summary: Optional[str]
    customer_note: Optional[str]
    resolution_note: Optional[str]
    created_at: datetime
    updated_at: datetime
    refund_records: list[RefundRecordRead] = Field(default_factory=list)

    class Config:
        from_attributes = True
