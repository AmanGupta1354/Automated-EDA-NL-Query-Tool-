"""
session_store.py — In-memory session state for the single-dataset lifecycle.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

from app.core.cleaning import CleaningError, apply_cleaning_method
from app.core.eda import profile_dataframe
from app.core.file_io import ParsedUpload

SessionState = Literal["pending_sheet_selection", "ready"]


class DatasetNotFoundError(Exception):
    pass


class SheetSelectionRequiredError(Exception):
    pass


class InvalidSheetNameError(Exception):
    pass


@dataclass
class SessionData:
    dataset_id: str
    filename: str
    file_format: str
    state: SessionState

    original_df: pd.DataFrame | None = None
    working_df: pd.DataFrame | None = None
    active_sheet: str | None = None

    pending_sheets: dict[str, pd.DataFrame] = field(default_factory=dict)

    @property
    def is_cleaned(self) -> bool:
        if self.original_df is None or self.working_df is None:
            return False
        if self.working_df.shape != self.original_df.shape:
            return True
        return not self.working_df.equals(self.original_df)


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionData] = {}
        self._lock = threading.Lock()

    def create_from_parsed_upload(
        self, filename: str, parsed: ParsedUpload
    ) -> SessionData:
        dataset_id = str(uuid.uuid4())

        if parsed.needs_sheet_selection:
            session = SessionData(
                dataset_id=dataset_id,
                filename=filename,
                file_format=parsed.file_format,
                state="pending_sheet_selection",
                pending_sheets=parsed.sheets,
            )
        else:
            df = parsed.single_df
            session = SessionData(
                dataset_id=dataset_id,
                filename=filename,
                file_format=parsed.file_format,
                state="ready",
                original_df=df.copy(),
                working_df=df.copy(),
                active_sheet=None,
            )

        with self._lock:
            self._sessions[dataset_id] = session
        return session

    def select_sheet(self, dataset_id: str, sheet_name: str) -> SessionData:
        session = self.get_session(dataset_id)

        if session.state != "pending_sheet_selection":
            raise SheetSelectionRequiredError(
                f"Dataset '{dataset_id}' is not awaiting sheet selection."
            )

        if sheet_name not in session.pending_sheets:
            available = ", ".join(session.pending_sheets.keys())
            raise InvalidSheetNameError(
                f"Sheet '{sheet_name}' not found. Available sheets: {available}."
            )

        df = session.pending_sheets[sheet_name]
        with self._lock:
            session.original_df = df.copy()
            session.working_df = df.copy()
            session.active_sheet = sheet_name
            session.state = "ready"
            session.pending_sheets = {}
        return session

    def get_session(self, dataset_id: str) -> SessionData:
        session = self._sessions.get(dataset_id)
        if session is None:
            raise DatasetNotFoundError(
                "Session expired or dataset_id invalid. Please re-upload."
            )
        return session

    def _require_ready(self, session: SessionData) -> None:
        if session.state != "ready":
            raise SheetSelectionRequiredError(
                f"Dataset '{session.dataset_id}' requires sheet selection "
                f"before this operation. Call POST /select-sheet first."
            )

    def get_ready_session(self, dataset_id: str) -> SessionData:
        """Public accessor for routes that need direct access to
        working_df (e.g. the NL-Query and export routes) rather than a
        pre-shaped report dict."""
        session = self.get_session(dataset_id)
        self._require_ready(session)
        return session

    def get_eda_report(self, dataset_id: str) -> dict:
        session = self.get_session(dataset_id)
        self._require_ready(session)
        report = profile_dataframe(session.working_df)
        report["dataset_id"] = dataset_id
        report["is_cleaned"] = session.is_cleaned
        return report

    def apply_cleaning(
        self, dataset_id: str, column: str, method: str, value=None
    ) -> dict:
        session = self.get_session(dataset_id)
        self._require_ready(session)

        result = apply_cleaning_method(session.working_df, column, method, value)

        with self._lock:
            session.working_df = result.df

        report = profile_dataframe(session.working_df)
        report["dataset_id"] = dataset_id
        report["is_cleaned"] = session.is_cleaned

        return {
            "dataset_id": dataset_id,
            "applied": {
                "column": column,
                "method": method,
                "affected_rows": result.affected_rows,
            },
            "eda": report,
        }

    def reset(self, dataset_id: str) -> dict:
        session = self.get_session(dataset_id)
        self._require_ready(session)

        with self._lock:
            session.working_df = session.original_df.copy()

        report = profile_dataframe(session.working_df)
        report["dataset_id"] = dataset_id
        report["is_cleaned"] = False

        return {"dataset_id": dataset_id, "status": "reset", "eda": report}

    def delete(self, dataset_id: str) -> None:
        self.get_session(dataset_id)
        with self._lock:
            del self._sessions[dataset_id]


session_store = SessionStore()