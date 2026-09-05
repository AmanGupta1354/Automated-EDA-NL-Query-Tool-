"""
models.py — Pydantic request/response schemas.

These mirror the API doc's JSON shapes exactly.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str
    message: str


class UploadResponse(BaseModel):
    dataset_id: str
    filename: str
    file_format: Literal["csv", "xlsx"]
    sheets: list[str] | None = None
    active_sheet: str | None = None
    needs_sheet_selection: bool
    rows: int | None = None
    columns: int | None = None
    column_names: list[str] | None = None
    eda: dict[str, Any] | None = None


class SelectSheetRequest(BaseModel):
    sheet_name: str


class SelectSheetResponse(BaseModel):
    dataset_id: str
    active_sheet: str
    rows: int
    columns: int
    column_names: list[str]
    eda: dict[str, Any]


CleaningMethod = Literal["mean", "median", "knn", "mode", "constant", "drop_rows"]


class CleanApplyRequest(BaseModel):
    column: str
    method: CleaningMethod
    value: str | float | int | None = None


class AppliedAction(BaseModel):
    column: str
    method: str
    affected_rows: int


class CleanApplyResponse(BaseModel):
    dataset_id: str
    applied: AppliedAction
    eda: dict[str, Any]


class ResetResponse(BaseModel):
    dataset_id: str
    status: Literal["reset"]
    eda: dict[str, Any]


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)


class QueryResponse(BaseModel):
    dataset_id: str
    question: str
    answer: str
    generated_code: str | None
    result_type: Literal["text", "number", "table"]


class DeleteResponse(BaseModel):
    dataset_id: str
    status: Literal["deleted"]