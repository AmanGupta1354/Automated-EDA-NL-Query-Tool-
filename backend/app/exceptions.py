"""
exceptions.py — Maps internal exceptions to the shared {error, message}
JSON error shape used by every endpoint in the API doc.
"""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.cleaning import CleaningError
from app.core.file_io import UnsupportedFileTypeError
from app.core.nl_query_agent import NLQueryError
from app.session_store import (
    DatasetNotFoundError,
    InvalidSheetNameError,
    SheetSelectionRequiredError,
)


def _error_json(status_code: int, error_code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": error_code, "message": message},
    )


async def handle_dataset_not_found(request: Request, exc: DatasetNotFoundError):
    return _error_json(404, "dataset_not_found", str(exc))


async def handle_sheet_selection_required(
    request: Request, exc: SheetSelectionRequiredError
):
    return _error_json(400, "sheet_selection_required", str(exc))


async def handle_invalid_sheet_name(request: Request, exc: InvalidSheetNameError):
    return _error_json(400, "invalid_sheet_name", str(exc))


async def handle_unsupported_file_type(
    request: Request, exc: UnsupportedFileTypeError
):
    return _error_json(400, "unsupported_file_type", str(exc))


async def handle_cleaning_error(request: Request, exc: CleaningError):
    return _error_json(400, exc.code, exc.message)


async def handle_nl_query_error(request: Request, exc: NLQueryError):
    return _error_json(500, "agent_execution_failed", exc.message)


EXCEPTION_HANDLERS = [
    (DatasetNotFoundError, handle_dataset_not_found),
    (SheetSelectionRequiredError, handle_sheet_selection_required),
    (InvalidSheetNameError, handle_invalid_sheet_name),
    (UnsupportedFileTypeError, handle_unsupported_file_type),
    (CleaningError, handle_cleaning_error),
    (NLQueryError, handle_nl_query_error),
]