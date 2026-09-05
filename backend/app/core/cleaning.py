"""
cleaning.py — Guided, user-directed missing-data cleaning.

Single entry point: apply_cleaning_method(df, column, method, value=None)
    -> CleaningResult(df, affected_rows)

Design notes:
- Pure pandas, no session/FastAPI awareness — same separation as eda.py.
- Never called automatically. The route layer only calls this after the
  user has picked a column + method AND confirmed the action.
- Always returns a NEW DataFrame (df.copy()) rather than mutating in
  place. The session layer decides whether to assign the result onto
  working_df.
- Raises CleaningError (not a bare ValueError) for invalid
  method/column-type combinations, with a message shaped to match the
  API doc's error schema so the router can catch it and return 400
  directly.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

try:
    from sklearn.impute import KNNImputer
except ImportError:  # pragma: no cover
    KNNImputer = None


NUMERIC_METHODS = {"mean", "median", "knn", "constant", "drop_rows"}
CATEGORICAL_METHODS = {"mode", "constant", "drop_rows"}
ALL_METHODS = NUMERIC_METHODS | CATEGORICAL_METHODS


class CleaningError(Exception):
    """Raised for any invalid cleaning request — bad column, bad method
    for the column's dtype, or a missing required value. The router
    layer catches this and maps it onto the {error, message} JSON shape
    from the API doc (error code = .code, message = str(exception))."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass
class CleaningResult:
    df: pd.DataFrame
    affected_rows: int


def _is_numeric_column(df: pd.DataFrame, column: str) -> bool:
    # Bool columns are treated as categorical elsewhere (see eda.py's
    # _classify_columns) so we mirror that here: bool is NOT numeric
    # for cleaning-method validation purposes.
    series = df[column]
    return pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(
        series
    )


def _validate(df: pd.DataFrame, column: str, method: str, value) -> None:
    if column not in df.columns:
        raise CleaningError(
            "column_not_found", f"Column '{column}' does not exist in the dataset."
        )

    if method not in ALL_METHODS:
        raise CleaningError(
            "invalid_method",
            f"'{method}' is not a recognized cleaning method. "
            f"Valid methods: {sorted(ALL_METHODS)}.",
        )

    is_numeric = _is_numeric_column(df, column)
    valid_for_dtype = NUMERIC_METHODS if is_numeric else CATEGORICAL_METHODS

    if method not in valid_for_dtype:
        dtype_label = "numeric" if is_numeric else "categorical"
        raise CleaningError(
            "invalid_method_for_dtype",
            f"Method '{method}' is not valid for {dtype_label} column '{column}'. "
            f"Valid methods: {', '.join(sorted(valid_for_dtype))}.",
        )

    if method == "constant" and (value is None or (isinstance(value, str) and value == "")):
        raise CleaningError(
            "missing_value",
            "A non-empty 'value' is required when method='constant'.",
        )

    if method == "knn" and KNNImputer is None:
        raise CleaningError(
            "dependency_missing",
            "KNN imputation requires scikit-learn, which is not installed.",
        )


def _apply_numeric(
    df: pd.DataFrame, column: str, method: str, value
) -> CleaningResult:
    missing_mask = df[column].isna()
    affected_rows = int(missing_mask.sum())

    if method == "mean":
        fill_value = df[column].mean()
        df[column] = df[column].fillna(fill_value)

    elif method == "median":
        fill_value = df[column].median()
        df[column] = df[column].fillna(fill_value)

    elif method == "constant":
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            raise CleaningError(
                "invalid_value",
                f"'{value}' is not a valid numeric value for column '{column}'.",
            )
        df[column] = df[column].fillna(numeric_value)

    elif method == "knn":
        # KNNImputer needs a numeric matrix. We impute using ALL numeric
        # columns as context but only write back the target column,
        # leaving other numeric columns exactly as they were.
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        imputer = KNNImputer(n_neighbors=5)
        imputed_block = imputer.fit_transform(df[numeric_cols])
        col_idx = numeric_cols.index(column)
        df[column] = imputed_block[:, col_idx]

    elif method == "drop_rows":
        df = df.loc[~missing_mask].reset_index(drop=True)

    return CleaningResult(df=df, affected_rows=affected_rows)


def _apply_categorical(
    df: pd.DataFrame, column: str, method: str, value
) -> CleaningResult:
    missing_mask = df[column].isna()
    affected_rows = int(missing_mask.sum())

    if method == "mode":
        modes = df[column].mode(dropna=True)
        if len(modes) == 0:
            raise CleaningError(
                "no_mode_available",
                f"Column '{column}' has no non-null values, so a mode "
                f"cannot be computed. Use 'constant' or 'drop_rows' instead.",
            )
        fill_value = modes.iloc[0]
        df[column] = df[column].fillna(fill_value)

    elif method == "constant":
        df[column] = df[column].fillna(str(value))

    elif method == "drop_rows":
        df = df.loc[~missing_mask].reset_index(drop=True)

    return CleaningResult(df=df, affected_rows=affected_rows)


def apply_cleaning_method(
    df: pd.DataFrame, column: str, method: str, value=None
) -> CleaningResult:
    """Apply one confirmed cleaning action to one column.

    Returns a CleaningResult holding a NEW DataFrame (the input df is
    never mutated) and the count of rows affected (rows that had a null
    in `column` before the operation).

    Raises CleaningError for any invalid column/method/value combination.
    """
    _validate(df, column, method, value)

    working = df.copy()
    is_numeric = _is_numeric_column(working, column)

    if is_numeric:
        return _apply_numeric(working, column, method, value)
    else:
        return _apply_categorical(working, column, method, value)