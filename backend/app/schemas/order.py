from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class OrderItemCreate(BaseModel):
    product_id: int
    product_option_id: Optional[int] = None
    quantity: int
    unit_price_krw: float


class OrderCreate(BaseModel):
    external_order_id: str
    channel_name: str
    customer_name: str
    customer_phone: str
    customer_address: str
    order_datetime: datetime
    status: str = "NEW"
    total_amount_krw: float
    items: List[OrderItemCreate]


class OrderItemRead(BaseModel):
    id: int
    product_id: int
    product_option_id: Optional[int]
    quantity: int
    unit_price_krw: float

    class Config:
        from_attributes = True


class OrderStatusHistoryRead(BaseModel):
    id: int
    previous_status: Optional[str]
    new_status: str
    changed_at: datetime
    reason: Optional[str]

    class Config:
        from_attributes = True


class OrderRead(BaseModel):
    id: int
    external_order_id: str
    channel_name: str
    customer_name: str
    customer_phone: str
    customer_address: str
    order_datetime: datetime
    status: str
    total_amount_krw: float
    items: List[OrderItemRead]
    status_history: List[OrderStatusHistoryRead] = []

    class Config:
        from_attributes = True
