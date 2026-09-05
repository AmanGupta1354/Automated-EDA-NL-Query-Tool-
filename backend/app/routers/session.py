"""
routers/session.py — DELETE /dataset/{dataset_id}
"""

from __future__ import annotations

from fastapi import APIRouter

from app.models import DeleteResponse
from app.session_store import session_store

router = APIRouter(tags=["session"])


@router.delete("/dataset/{dataset_id}", response_model=DeleteResponse)
async def delete_dataset(dataset_id: str) -> DeleteResponse:
    session_store.delete(dataset_id)
    return DeleteResponse(dataset_id=dataset_id, status="deleted")