"""
routers/export.py — GET /export/{dataset_id}
"""

from __future__ import annotations

from fastapi import APIRouter, Response

from app.core.file_io import export_dataframe
from app.session_store import session_store

router = APIRouter(tags=["export"])


@router.get("/export/{dataset_id}")
async def export_dataset(dataset_id: str) -> Response:
    session = session_store.get_ready_session(dataset_id)

    raw_bytes, content_type = export_dataframe(session.working_df, session.file_format)

    base_name = session.filename.rsplit(".", 1)[0]
    extension = "csv" if session.file_format == "csv" else "xlsx"
    export_filename = f"{base_name}_cleaned.{extension}"

    return Response(
        content=raw_bytes,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{export_filename}"'
        },
    )