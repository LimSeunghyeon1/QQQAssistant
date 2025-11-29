from __future__ import annotations

from fastapi import FastAPI

from app.api import orders, products, shipments
from app.api import exports as exports_api
from app.api import purchase_orders
from app.database import Base, apply_schema_upgrades, engine

Base.metadata.create_all(bind=engine)
apply_schema_upgrades()

app = FastAPI(title="QQQ Purchase Agency Assistant")
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(shipments.router)
app.include_router(exports_api.router)
app.include_router(purchase_orders.router)


@app.get("/health")
def healthcheck():
    return {"status": "ok"}
