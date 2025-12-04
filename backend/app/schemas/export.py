from __future__ import annotations

from pydantic import BaseModel, Field


class SmartStoreExportRequest(BaseModel):
    product_ids: list[int]
    template_type: str = "default"
    template_config: dict = Field(default_factory=dict)
    locale: str | None = None
