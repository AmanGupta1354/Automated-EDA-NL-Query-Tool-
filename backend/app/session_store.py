"""
session_store.py — In-memory session state for the single-dataset lifecycle.

This is the ONLY place that holds original_df/working_df in memory. Every
router calls into SessionStore rather than touching DataFrames directly,
so there's one source of truth for "what does the current session look
like right now."

Lifecycle states a session can be in:
- PENDING_SHEET_SELECTION: multi-sheet XLSX was uploaded; dataset_id
  exists but original_df/working_df are not yet set. Only
  select_sheet() is valid to call next.
- READY: original_df/working_df are set. EDA/cleaning/query/export are
  all valid.

No FastAPI imports here — this module is framework-agnostic so it's
easy to unit test and easy to swap the transport layer later if needed.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

from cleaning import CleaningError, apply_cleaning_method
from eda import profile_dataframe
from file_io import ParsedUpload

SessionState = Literal["pending_sheet_selection", "ready"]


class DatasetNotFoundError(Exception):
    """Session expired, was deleted, or the dataset_id is simply invalid.
    Maps to the API doc's dataset_not_found error."""

    pass


class SheetSelectionRequiredError(Exception):
    """Raised when an operation (EDA, clean, query, export) is attempted
    on a session that's still waiting on POST /select-sheet."""

    pass


class InvalidSheetNameError(Exception):
    """Raised when select_sheet() is called with a sheet name that
    wasn't in the uploaded workbook."""

    pass


@dataclass
class SessionData:
    dataset_id: str
    filename: str
    file_format: str  # "csv" | "xlsx"
    state: SessionState

    # Only populated once state == "ready"
    original_df: pd.DataFrame | None = None
    working_df: pd.DataFrame | None = None
    active_sheet: str | None = None

    # Only populated while state == "pending_sheet_selection"
    pending_sheets: dict[str, pd.DataFrame] = field(default_factory=dict)

    @property
    def is_cleaned(self) -> bool:
        """True if working_df currently differs from original_df.
        Drives the API's is_cleaned flag (frontend uses this to show/hide
        Start Over and label the dashboard Raw vs Cleaned)."""
        if self.original_df is None or self.working_df is None:
            return False
        if self.working_df.shape != self.original_df.shape:
            return True
        return not self.working_df.equals(self.original_df)


class SessionStore:
    """Thread-safe in-memory store. A simple lock is enough here since
    this is demo-scale, single-process, single-dataset-per-session —
    no need for anything fancier than serializing access to the dict."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionData] = {}
        self._lock = threading.Lock()

    # ---- creation -------------------------------------------------------

    def create_from_parsed_upload(
        self, filename: str, parsed: ParsedUpload
    ) -> SessionData:
        """Create a new session from a freshly parsed upload.
        If the upload needs sheet selection, the session starts in
        PENDING_SHEET_SELECTION state with original_df/working_df unset."""
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
            # Not an error the API doc defines explicitly, but it's a
            # genuine misuse case (selecting a sheet twice) — treat it
            # as a no-op-safe validation error rather than silently
            # overwriting an already-cleaned working_df.
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

    # ---- retrieval --------------------------------------------------------

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

    # ---- EDA --------------------------------------------------------------

    def get_eda_report(self, dataset_id: str) -> dict:
        session = self.get_session(dataset_id)
        self._require_ready(session)
        report = profile_dataframe(session.working_df)
        report["dataset_id"] = dataset_id
        report["is_cleaned"] = session.is_cleaned
        return report

    # ---- cleaning -----------------------------------------------------

    def apply_cleaning(
        self, dataset_id: str, column: str, method: str, value=None
    ) -> dict:
        """Apply a confirmed cleaning action and return the updated EDA
        report plus the applied-action summary, matching the
        POST /clean/apply/{id} response schema. Raises CleaningError
        (bubbled up unchanged) for any invalid request — the router
        catches that and returns 400."""
        session = self.get_session(dataset_id)
        self._require_ready(session)

        result = apply_cleaning_method(
            session.working_df, column, method, value
        )

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

    # ---- reset --------------------------------------------------------

    def reset(self, dataset_id: str) -> dict:
        session = self.get_session(dataset_id)
        self._require_ready(session)

        with self._lock:
            session.working_df = session.original_df.copy()

        report = profile_dataframe(session.working_df)
        report["dataset_id"] = dataset_id
        report["is_cleaned"] = False  # always false immediately after reset

        return {"dataset_id": dataset_id, "status": "reset", "eda": report}

    # ---- deletion -------------------------------------------------------

    def delete(self, dataset_id: str) -> None:
        # Idempotent-ish: raises if it was never there, matching the
        # dataset_not_found error shape for a delete on a bad id.
        self.get_session(dataset_id)
        with self._lock:
            del self._sessions[dataset_id]


# Module-level singleton — FastAPI routers import this directly.
# (Fine for single-process demo scale; a multi-worker deployment would
# need this backed by something shared like Redis instead.)
session_store = SessionStore()