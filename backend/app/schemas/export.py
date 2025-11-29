from __future__ import annotations

from pydantic import BaseModel


class SmartStoreExportRequest(BaseModel):
    product_ids: list[int]
    template_type: str = "default"
