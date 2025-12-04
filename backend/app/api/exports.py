from __future__ import annotations

from datetime import datetime
from pathlib import Path

from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_session
from app.schemas.export import SmartStoreExportRequest
from app.services.exporter_smartstore import SmartStoreExporter

router = APIRouter(prefix="/api/exports", tags=["exports"])


def _smartstore_exporter_factory(
    payload: SmartStoreExportRequest,
) -> SmartStoreExporter:
    template_config = dict(payload.template_config)
    if payload.locale:
        template_config.setdefault("locale", payload.locale)
    return SmartStoreExporter(template_config=template_config, locale=payload.locale)


EXPORTER_FACTORIES: dict[str, Callable[[SmartStoreExportRequest], SmartStoreExporter]] = {
    "smartstore": _smartstore_exporter_factory,
}


def _get_exporter(channel: str, payload: SmartStoreExportRequest) -> SmartStoreExporter:
    factory = EXPORTER_FACTORIES.get(channel.lower())
    if not factory:
        raise ValueError("지원하지 않는 채널")
    return factory(payload)


def _export_products(
    channel: str, payload: SmartStoreExportRequest, session: Session
) -> StreamingResponse:
    exporter = _get_exporter(channel, payload)
    try:
        csv_buf = exporter.export_products(session, payload.product_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    export_dir = Path(settings.sales_channel_export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{channel}_products_{datetime.now():%Y%m%d%H%M%S}.csv"
    file_path = export_dir / filename
    file_path.write_text(csv_buf.getvalue(), encoding="utf-8")

    return StreamingResponse(
        iter([csv_buf.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={channel}_products.csv"
        },
    )


@router.post("/channel/{channel}")
def export_channel(
    channel: str, payload: SmartStoreExportRequest, session: Session = Depends(get_session)
):
    """Backward-compatible channel-based export endpoint."""
    return export(channel=channel, payload=payload, session=session)


@router.post("")
def export(
    payload: SmartStoreExportRequest,
    channel: str = Query(..., description="Sales channel to export products for"),
    session: Session = Depends(get_session),
):
    """Dispatch export requests to the appropriate channel exporter."""
    try:
        return _export_products(channel, payload, session)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


