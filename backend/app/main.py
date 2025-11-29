from __future__ import annotations

from fastapi import FastAPI

from app.api import orders, products, shipments
from app.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="QQQ Purchase Agency Assistant")
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(shipments.router)


@app.get("/health")
def healthcheck():
    return {"status": "ok"}
