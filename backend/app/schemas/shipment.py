from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ShipmentCreate(BaseModel):
    carrier_name: str
    tracking_number: str
    shipment_type: str
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    linked_order_ids: List[int] = []


class ShipmentRead(BaseModel):
    id: int
    carrier_name: str
    tracking_number: str
    shipment_type: str
    shipped_at: Optional[datetime]
    delivered_at: Optional[datetime]
    last_status: Optional[str]

    class Config:
        from_attributes = True
