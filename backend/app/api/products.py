from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_session
from app.models.domain import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductLocalizedInfoCreate, ProductRead
from app.services.product_service import ProductService

router = APIRouter(prefix="/api/products", tags=["products"])


def get_service(session: Session = Depends(get_session)) -> ProductService:
    repo = ProductRepository(session)
    return ProductService(repo)


# Ingest a product scraped from an external URL
@router.post("/import", response_model=ProductRead)
def import_product(payload: ProductCreate, service: ProductService = Depends(get_service)):
    product = service.ingest(payload)
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
