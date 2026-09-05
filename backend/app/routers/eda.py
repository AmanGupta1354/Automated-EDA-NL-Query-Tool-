"""
routers/eda.py — GET /eda/{dataset_id}
"""

from __future__ import annotations

from fastapi import APIRouter

from app.session_store import session_store

router = APIRouter(tags=["eda"])


@router.get("/eda/{dataset_id}")
async def get_eda(dataset_id: str) -> dict:
    return session_store.get_eda_report(dataset_id)