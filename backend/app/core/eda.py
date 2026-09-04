"""
eda.py — Automated EDA profiling engine.

Single entry point: profile_dataframe(df) -> dict (JSON-serializable).

Design notes:
- This module is pandas-only and has no knowledge of sessions, dataset_ids,
  uploads, or FastAPI. It's called by the session/route layer both right
  after upload/sheet-selection (on original_df) and after every cleaning
  action (on working_df). Same function, same output shape, every time.
- Never mutates the DataFrame passed in.
- Never renders charts. Only returns bin edges / counts / value counts —
  the frontend renders these with Recharts/Chart.js.
- Output shape matches the /eda/{dataset_id} response schema. The caller
  (route layer) is responsible for adding "dataset_id" and "is_cleaned";
  this function only knows about the DataFrame itself.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

# ---- tunables -----------------------------------------------------------

HISTOGRAM_BINS = 10
TOP_N_CATEGORICAL_VALUES = 10
# A column is treated as "categorical" (vs. free-text/high-cardinality)
# in top-value reporting regardless of cardinality — we always report
# top-N, we just cap N. No separate high-cardinality suppression for now.


def _json_safe_float(value: Any) -> float | None:
    """Convert numpy/pandas scalars to plain floats, mapping NaN/inf to None
    so the output is always valid JSON (json.dumps chokes on NaN by default
    in strict mode, and even when it doesn't, NaN isn't valid JSON)."""
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _classify_columns(df: pd.DataFrame) -> dict[str, list[str]]:
    """Split columns into numeric / categorical / datetime buckets.

    - datetime: actual datetime64 dtype, OR object columns that parse
      cleanly as dates for a high fraction of non-null values.
    - numeric: any pandas numeric dtype, excluding boolean (bool is
      reported as categorical — "True/False counts" reads more naturally
      as a categorical breakdown than as a numeric summary with a
      mean of 0.6).
    - categorical: everything else (object, category, bool).
    """
    numeric: list[str] = []
    categorical: list[str] = []
    datetime_cols: list[str] = []

    for col in df.columns:
        series = df[col]

        if pd.api.types.is_datetime64_any_dtype(series):
            datetime_cols.append(col)
            continue

        if pd.api.types.is_bool_dtype(series):
            categorical.append(col)
            continue

        if pd.api.types.is_numeric_dtype(series):
            numeric.append(col)
            continue

        # object/string columns: sniff for datetime-like content.
        # Only attempt this on columns with at least one non-null value,
        # and require a strong majority to parse cleanly to avoid
        # misclassifying free-text columns that happen to contain a
        # few date-like tokens.
        non_null = series.dropna()
        if len(non_null) > 0:
            sample = non_null if len(non_null) <= 200 else non_null.sample(
                200, random_state=0
            )
            parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
            parse_rate = parsed.notna().mean()
            if parse_rate >= 0.95:
                datetime_cols.append(col)
                continue

        categorical.append(col)

    return {
        "numeric": numeric,
        "categorical": categorical,
        "datetime": datetime_cols,
    }


def _missing_value_report(df: pd.DataFrame) -> list[dict[str, Any]]:
    total_rows = len(df)
    report = []
    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        missing_pct = (
            round((missing_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
        )
        report.append(
            {
                "column": col,
                "missing_count": missing_count,
                "missing_pct": missing_pct,
            }
        )
    return report


def _histogram(series: pd.Series, bins: int = HISTOGRAM_BINS) -> dict[str, list] | None:
    """Bin edges + counts for a numeric series, ignoring NaN.
    Returns None if there's no usable numeric data (e.g. all null, or a
    single distinct value can't form a range — numpy still handles that
    case by producing a degenerate but valid single-bin histogram, so we
    only bail out on truly empty input)."""
    clean = series.dropna().astype(float)
    if len(clean) == 0:
        return None
    counts, edges = np.histogram(clean, bins=bins)
    return {
        "bin_edges": [round(float(e), 4) for e in edges],
        "counts": [int(c) for c in counts],
    }


def _numeric_summary(df: pd.DataFrame, numeric_cols: list[str]) -> list[dict[str, Any]]:
    summary = []
    for col in numeric_cols:
        series = df[col]
        clean = series.dropna()

        if len(clean) == 0:
            # Column is entirely null — report a null-shaped entry rather
            # than crashing on stats that need at least one value.
            summary.append(
                {
                    "column": col,
                    "mean": None,
                    "std": None,
                    "min": None,
                    "p25": None,
                    "p50": None,
                    "p75": None,
                    "max": None,
                    "skew": None,
                    "histogram": None,
                }
            )
            continue

        desc = clean.describe()
        skew = clean.skew() if len(clean) > 2 else None

        summary.append(
            {
                "column": col,
                "mean": _json_safe_float(desc.get("mean")),
                "std": _json_safe_float(desc.get("std")),
                "min": _json_safe_float(desc.get("min")),
                "p25": _json_safe_float(desc.get("25%")),
                "p50": _json_safe_float(desc.get("50%")),
                "p75": _json_safe_float(desc.get("75%")),
                "max": _json_safe_float(desc.get("max")),
                "skew": _json_safe_float(skew),
                "histogram": _histogram(series),
            }
        )
    return summary


def _categorical_summary(
    df: pd.DataFrame, categorical_cols: list[str], top_n: int = TOP_N_CATEGORICAL_VALUES
) -> list[dict[str, Any]]:
    summary = []
    for col in categorical_cols:
        series = df[col]
        value_counts = series.value_counts(dropna=True).head(top_n)
        summary.append(
            {
                "column": col,
                "unique_count": int(series.nunique(dropna=True)),
                "top_values": [
                    {"value": str(val), "count": int(count)}
                    for val, count in value_counts.items()
                ],
            }
        )
    return summary


def _correlation_matrix(df: pd.DataFrame, numeric_cols: list[str]) -> dict[str, Any]:
    if len(numeric_cols) < 2:
        # Correlation is undefined/meaningless with 0-1 numeric columns.
        # Return an explicit empty shape rather than omitting the key, so
        # the frontend can rely on the field always being present.
        return {"columns": numeric_cols, "matrix": []}

    corr = df[numeric_cols].corr()
    # Replace NaN (e.g. a constant column has undefined correlation) with
    # None so the matrix stays JSON-safe.
    matrix = [
        [_json_safe_float(v) for v in row]
        for row in corr.to_numpy()
    ]
    return {"columns": numeric_cols, "matrix": matrix}


def profile_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    """Profile a DataFrame and return a JSON-serializable EDA report.

    This is the single function reused for both the initial raw-data
    profile and every post-cleaning refresh. It does not mutate df.
    Output matches the /eda/{dataset_id} response schema (excluding
    dataset_id and is_cleaned, which the route/session layer adds).
    """
    column_types = _classify_columns(df)

    numeric_summary = _numeric_summary(df, column_types["numeric"])
    categorical_summary = _categorical_summary(df, column_types["categorical"])
    correlation_matrix = _correlation_matrix(df, column_types["numeric"])

    return {
        "shape": {"rows": int(len(df)), "columns": int(len(df.columns))},
        "column_types": column_types,
        "missing_values": _missing_value_report(df),
        "numeric_summary": numeric_summary,
        "categorical_summary": categorical_summary,
        "correlation_matrix": correlation_matrix,
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_usage_mb": round(
            df.memory_usage(deep=True).sum() / (1024 * 1024), 4
        ),
    }