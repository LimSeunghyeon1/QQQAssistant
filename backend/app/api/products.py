from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_session
from app.models.domain import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import (
    ProductCreate,
    ProductImportRequest,
    ProductLocalizedInfoCreate,
    ProductLocalizedInfoRead,
    ProductRead,
    ProductTranslateRequest,
)
from app.services.product_import_service import ProductImportService
from app.services.product_service import ProductService
from app.services.translation_service import TranslationService

router = APIRouter(prefix="/api/products", tags=["products"])


def get_service(session: Session = Depends(get_session)) -> ProductService:
    repo = ProductRepository(session)
    return ProductService(repo)


# Ingest a product scraped from an external URL
@router.post("/import", response_model=ProductRead)
async def import_product(
    payload: ProductImportRequest, session: Session = Depends(get_session)
):
    importer = ProductImportService(session)
    try:
        product = await importer.import_product(
            source_url=payload.source_url, source_site=payload.source_site
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return product


@router.get("", response_model=list[ProductRead])
def list_products(service: ProductService = Depends(get_service)):
    return service.list()


@router.put("/{product_id}/localization", response_model=ProductRead)
def update_localization(
    product_id: int,
    payload: ProductLocalizedInfoCreate,
    service: ProductService = Depends(get_service),
    session: Session = Depends(get_session),
):
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    service.update_localization(product, payload)
    return product


@router.post("/{product_id}/translate", response_model=ProductLocalizedInfoRead)
def translate_product(
    product_id: int,
    payload: ProductTranslateRequest,
    session: Session = Depends(get_session),
):
    service = TranslationService(session)
    try:
        return service.translate_product(
            product_id, target_locale=payload.target_locale, provider=payload.provider
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
