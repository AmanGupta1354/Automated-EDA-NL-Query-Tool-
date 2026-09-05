"""
routers/upload.py — POST /upload, POST /select-sheet/{dataset_id}
"""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from app.core.eda import profile_dataframe
from app.core.file_io import read_upload
from app.models import SelectSheetRequest, SelectSheetResponse, UploadResponse
from app.session_store import session_store

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_dataset(file: UploadFile = File(...)) -> UploadResponse:
    raw_bytes = await file.read()
    parsed = read_upload(file.filename, raw_bytes)
    session = session_store.create_from_parsed_upload(file.filename, parsed)

    if session.state == "pending_sheet_selection":
        return UploadResponse(
            dataset_id=session.dataset_id,
            filename=session.filename,
            file_format=session.file_format,
            sheets=list(session.pending_sheets.keys()),
            active_sheet=None,
            needs_sheet_selection=True,
            rows=None,
            columns=None,
            column_names=None,
            eda=None,
        )

    eda_report = profile_dataframe(session.working_df)
    eda_report["dataset_id"] = session.dataset_id
    eda_report["is_cleaned"] = False

    return UploadResponse(
        dataset_id=session.dataset_id,
        filename=session.filename,
        file_format=session.file_format,
        sheets=None,
        active_sheet=session.active_sheet,
        needs_sheet_selection=False,
        rows=len(session.working_df),
        columns=len(session.working_df.columns),
        column_names=list(session.working_df.columns),
        eda=eda_report,
    )


@router.post("/select-sheet/{dataset_id}", response_model=SelectSheetResponse)
async def select_sheet(
    dataset_id: str, body: SelectSheetRequest
) -> SelectSheetResponse:
    session = session_store.select_sheet(dataset_id, body.sheet_name)

    eda_report = profile_dataframe(session.working_df)
    eda_report["dataset_id"] = dataset_id
    eda_report["is_cleaned"] = False

    return SelectSheetResponse(
        dataset_id=dataset_id,
        active_sheet=session.active_sheet,
        rows=len(session.working_df),
        columns=len(session.working_df.columns),
        column_names=list(session.working_df.columns),
        eda=eda_report,
    )