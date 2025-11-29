from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PurchaseOrderSourceLinkRead(BaseModel):
    id: int
    order_id: int
    order_item_id: int
    source_quantity: int

    class Config:
        from_attributes = True


class PurchaseOrderItemRead(BaseModel):
    id: int
    product_id: int
    product_option_id: Optional[int] = None
    sku: Optional[str]
    unit_cost: float
    quantity: int
    line_total: float
    source_links: list[PurchaseOrderSourceLinkRead] = []

    class Config:
        from_attributes = True


class PurchaseOrderRead(BaseModel):
    id: int
    supplier_name: str
    status: str
    currency: str
    total_amount: float
    expected_arrival_date: Optional[datetime] = None
    created_at: datetime
    created_by: Optional[str] = None
    items: list[PurchaseOrderItemRead] = []

    class Config:
        from_attributes = True


class PurchaseOrderCreateRequest(BaseModel):
    order_ids: Optional[list[int]] = None


class PurchaseOrderStatusUpdateRequest(BaseModel):
    new_status: str
    reason: Optional[str] = None
