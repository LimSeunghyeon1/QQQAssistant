from __future__ import annotations

from fastapi import FastAPI

from app.api import exports as exports_api
from app.api import orders, products, shipments
from app.api import purchase_orders
from app.database import Base, apply_schema_upgrades, engine


def init_database() -> None:
    """Initialize database schema and in-place upgrades."""

    Base.metadata.create_all(bind=engine)
    apply_schema_upgrades()


def create_app() -> FastAPI:
    """Application factory for FastAPI.

    Having a dedicated factory clarifies the startup flow and makes the module
    easier to read when imported by ASGI servers.
    """

    init_database()

    application = FastAPI(title="QQQ Purchase Agency Assistant")
    for router in (
        products.router,
        orders.router,
        shipments.router,
        exports_api.router,
        purchase_orders.router,
    ):
        application.include_router(router)

    @application.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
