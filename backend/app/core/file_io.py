"""
file_io.py — Reading uploaded files and exporting cleaned data.

Two responsibilities only:
- read_upload(): turn raw uploaded bytes into either a single DataFrame
  (CSV or single-sheet XLSX) or a dict of sheet_name -> DataFrame
  (multi-sheet XLSX), so the caller can decide whether sheet selection
  is needed.
- export_dataframe(): turn a DataFrame back into bytes in the same
  format it was uploaded in.

No session awareness here — this module doesn't know about dataset_id,
original_df/working_df, or any session state.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import pandas as pd

SUPPORTED_FORMATS = {"csv", "xlsx"}


class UnsupportedFileTypeError(Exception):
    """Raised when the uploaded filename doesn't end in .csv or .xlsx.
    Maps directly to the API doc's 400 unsupported_file_type error."""

    pass


@dataclass
class ParsedUpload:
    file_format: str  # "csv" | "xlsx"
    # Exactly one of the following two is populated:
    single_df: pd.DataFrame | None  # CSV or single-sheet XLSX
    sheets: dict[str, pd.DataFrame] | None  # multi-sheet XLSX, name -> df

    @property
    def needs_sheet_selection(self) -> bool:
        return self.sheets is not None


def _infer_format(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".csv"):
        return "csv"
    if lower.endswith(".xlsx"):
        return "xlsx"
    raise UnsupportedFileTypeError(
        f"'{filename}' is not a supported file type. Only .csv and .xlsx are supported."
    )


def read_upload(filename: str, raw_bytes: bytes) -> ParsedUpload:
    """Parse uploaded file bytes based on the filename's extension.

    - .csv -> always a single DataFrame.
    - .xlsx with 1 sheet -> single DataFrame (auto-selected, no picker needed).
    - .xlsx with 2+ sheets -> dict of sheet_name -> DataFrame; caller must
      prompt the user to pick one before anything else happens.

    Raises UnsupportedFileTypeError for any other extension.
    """
    file_format = _infer_format(filename)
    buffer = io.BytesIO(raw_bytes)

    if file_format == "csv":
        df = pd.read_csv(buffer)
        return ParsedUpload(file_format="csv", single_df=df, sheets=None)

    # xlsx
    excel_file = pd.ExcelFile(buffer)
    sheet_names = excel_file.sheet_names

    if len(sheet_names) == 1:
        df = excel_file.parse(sheet_names[0])
        return ParsedUpload(file_format="xlsx", single_df=df, sheets=None)

    sheets = {name: excel_file.parse(name) for name in sheet_names}
    return ParsedUpload(file_format="xlsx", single_df=None, sheets=sheets)


def export_dataframe(df: pd.DataFrame, file_format: str) -> tuple[bytes, str]:
    """Serialize a DataFrame back to bytes in the given format.

    Returns (raw_bytes, content_type) so the router can set the response
    headers directly per the API doc:
      csv  -> text/csv
      xlsx -> application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    """
    if file_format == "csv":
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        return buffer.getvalue().encode("utf-8"), "text/csv"

    if file_format == "xlsx":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Sheet1")
        return (
            buffer.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    raise UnsupportedFileTypeError(f"Cannot export unknown format '{file_format}'.")