from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_session
from app.schemas.export import SmartStoreExportRequest
from app.services.exporter_smartstore import SmartStoreExporter

router = APIRouter(prefix="/api/exports", tags=["exports"])


@router.post("/channel/smartstore")
def export_smartstore(
    payload: SmartStoreExportRequest, session: Session = Depends(get_session)
):
    exporter = SmartStoreExporter()
    try:
        csv_buf = exporter.export_products(session, payload.product_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return StreamingResponse(
        iter([csv_buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=smartstore_products.csv"},
    )
