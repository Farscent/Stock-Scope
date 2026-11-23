"""Deterministic cleaning shared by the notebook and dashboard."""

import numpy as np
import pandas as pd

PRICE_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]
REVENUE_COLUMNS = ["Date", "Revenue"]


def standardize_dates(values: pd.Series) -> pd.Series:
    """Keep exchange-local calendar dates; remove timezone without shifting days."""
    def convert(value):
        try:
            stamp = pd.Timestamp(value)
            if pd.isna(stamp):
                return pd.NaT
            return stamp.tz_localize(None).normalize()
        except (ValueError, TypeError, OverflowError):
            return pd.NaT

    return pd.to_datetime(values.map(convert), errors="coerce")


def clean_revenue(raw: pd.DataFrame) -> pd.DataFrame:
    """Clean Date/Revenue rows in USD millions; discard invalid dates and values.

    Accept currency symbols, thousands separators and accounting negatives.
    Duplicate dates keep the last valid supplied observation; zero is valid.
    """
    frame = raw.reindex(columns=REVENUE_COLUMNS).copy()
    frame["Date"] = standardize_dates(frame["Date"])
    values = frame["Revenue"].astype("string").str.strip()
    values = values.str.replace(r"^\((.*)\)$", r"-\1", regex=True)
    values = values.str.replace(r"[$,\s]", "", regex=True)
    frame["Revenue"] = pd.to_numeric(values, errors="coerce").astype(float)
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=REVENUE_COLUMNS)
    return frame.drop_duplicates("Date", keep="last").sort_values("Date").reset_index(drop=True)


def clean_prices(raw: pd.DataFrame) -> pd.DataFrame:
    """Validate daily prices, retain missing volume, and order unique sessions."""
    frame = raw.copy()
    if "Date" not in frame and isinstance(frame.index, pd.DatetimeIndex):
        frame = frame.rename_axis("Date").reset_index()
    frame = frame.reindex(columns=PRICE_COLUMNS)
    frame["Date"] = standardize_dates(frame["Date"])
    for column in PRICE_COLUMNS[1:]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.replace([np.inf, -np.inf], np.nan).dropna(subset=["Date", "Close"])
    frame = frame.loc[frame["Close"] > 0]
    frame.loc[frame["Volume"] < 0, "Volume"] = np.nan
    return frame.drop_duplicates("Date", keep="last").sort_values("Date").reset_index(drop=True)
