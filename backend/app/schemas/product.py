from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ProductOptionCreate(BaseModel):
    option_key: str
    raw_name: str
    raw_price_diff: float = 0


class ProductLocalizedInfoCreate(BaseModel):
    locale: str = "ko-KR"
    title: str
    description: Optional[str] = None
    option_display_name_format: Optional[str] = None


class ProductImportRequest(BaseModel):
    source_url: str
    source_site: str = "TAOBAO"


class ProductTranslateRequest(BaseModel):
    target_locale: str = "ko-KR"
    provider: str = "gcloud"


class ProductCreate(BaseModel):
    source_url: str
    source_site: str
    raw_title: str
    raw_price: float
    raw_currency: str
    exchange_rate: Optional[float] = Field(default=None, gt=0)
    margin_rate: Optional[float] = None
    vat_rate: Optional[float] = None
    shipping_fee: Optional[float] = Field(default=None, ge=0)
    raw_description: Optional[str] = None
    thumbnail_image_urls: List[str] = Field(default_factory=list)
    detail_image_urls: List[str] = Field(default_factory=list)
    clean_image_urls: List[str] = Field(default_factory=list)
    clean_detail_image_urls: List[str] = Field(default_factory=list)
    options: List[ProductOptionCreate] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    exchange_rate: Optional[float] = Field(default=None, gt=0)
    margin_rate: Optional[float] = None
    vat_rate: Optional[float] = None
    shipping_fee: Optional[float] = Field(default=None, ge=0)


class ProductOptionRead(BaseModel):
    id: int
    option_key: str
    raw_name: str
    raw_price_diff: float
    localized_name: Optional[str] = None

    class Config:
        from_attributes = True


class ProductLocalizedInfoRead(BaseModel):
    id: int
    locale: str
    title: str
    description: Optional[str]
    option_display_name_format: Optional[str]

    class Config:
        from_attributes = True


class ProductRead(BaseModel):
    id: int
    source_url: str
    source_site: str
    raw_title: str
    raw_price: float
    raw_currency: str
    exchange_rate: Optional[float] = None
    margin_rate: Optional[float] = None
    vat_rate: Optional[float] = None
    shipping_fee: Optional[float] = None
    image_urls: list[str]
    detail_image_urls: list[str]
    clean_image_urls: list[str]
    clean_detail_image_urls: list[str]
    created_at: datetime
    options: List[ProductOptionRead] = []
    localizations: List[ProductLocalizedInfoRead] = []

    class Config:
        from_attributes = True
