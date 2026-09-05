"""
routers/cleaning.py — POST /clean/apply/{dataset_id}, POST /reset/{dataset_id}
"""

from __future__ import annotations

from fastapi import APIRouter

from app.models import CleanApplyRequest, CleanApplyResponse, ResetResponse
from app.session_store import session_store

router = APIRouter(tags=["cleaning"])


@router.post("/clean/apply/{dataset_id}", response_model=CleanApplyResponse)
async def apply_cleaning(dataset_id: str, body: CleanApplyRequest) -> dict:
    return session_store.apply_cleaning(
        dataset_id, body.column, body.method, body.value
    )


@router.post("/reset/{dataset_id}", response_model=ResetResponse)
async def reset_dataset(dataset_id: str) -> dict:
    return session_store.reset(dataset_id)