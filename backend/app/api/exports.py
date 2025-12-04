from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_session
from app.schemas.export import SmartStoreExportRequest
from app.services.exporter_smartstore import SmartStoreExporter

router = APIRouter(prefix="/api/exports", tags=["exports"])


@router.post("/channel/smartstore")
def export_smartstore(
    payload: SmartStoreExportRequest, session: Session = Depends(get_session)
):
    template_config = dict(payload.template_config)
    if payload.locale:
        template_config.setdefault("locale", payload.locale)

    exporter = SmartStoreExporter(
        template_config=template_config, locale=payload.locale
    )
    try:
        csv_buf = exporter.export_products(session, payload.product_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    export_dir = Path(settings.sales_channel_export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)
    filename = f"smartstore_products_{datetime.now():%Y%m%d%H%M%S}.csv"
    file_path = export_dir / filename
    file_path.write_text(csv_buf.getvalue(), encoding="utf-8")

    return StreamingResponse(
        iter([csv_buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=smartstore_products.csv"},
    )
