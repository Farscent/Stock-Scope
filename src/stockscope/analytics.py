"""Pure analytical functions. Returns are decimal fractions, not percentages."""

from collections.abc import Mapping

import numpy as np
import pandas as pd


def period_return(prices: pd.Series) -> float:
    """First-to-last observed adjusted-close return; require two observations."""
    values = prices.dropna()
    if len(values) < 2 or values.iloc[0] <= 0:
        return float("nan")
    return float(values.iloc[-1] / values.iloc[0] - 1)


def moving_averages(frame: pd.DataFrame, windows: tuple[int, ...] = (20, 50)) -> pd.DataFrame:
    """Trailing trading-session means; require a complete window."""
    result = frame.sort_values("Date").copy()
    for window in windows:
        if window < 1:
            raise ValueError("Moving-average windows must be positive.")
        result[f"MA{window}"] = result["Close"].rolling(window, min_periods=window).mean()
    return result


def stock_metrics(frame: pd.DataFrame) -> dict[str, float]:
    """KPIs on selected sessions only; volatility uses sample std and 252 sessions."""
    frame = frame.sort_values("Date")
    close = frame["Close"]
    daily = close.pct_change(fill_method=None).dropna()
    return {
        "latest": float(close.iloc[-1]) if len(close) else float("nan"),
        "session_change": period_return(close.tail(2)),
        "period_return": period_return(close),
        "average_volume": float(frame["Volume"].mean()),
        "volatility": float(daily.std(ddof=1) * np.sqrt(252)) if len(daily) >= 2 else float("nan"),
    }


def normalize_comparison(prices: Mapping[str, pd.DataFrame]) -> pd.DataFrame:
    """Inner-join valid dates before rebasing every series to a shared index of 100."""
    if not prices or any(frame.empty for frame in prices.values()):
        return pd.DataFrame()
    aligned = pd.concat(
        {ticker: frame.drop_duplicates("Date").set_index("Date")["Close"]
         for ticker, frame in prices.items()}, axis=1, join="inner",
    ).replace([np.inf, -np.inf], np.nan).dropna().sort_index()
    aligned = aligned.loc[(aligned > 0).all(axis=1)]
    if aligned.empty:
        return pd.DataFrame()
    return (aligned / aligned.iloc[0] * 100).rename_axis("Date").reset_index()


def revenue_growth(frame: pd.DataFrame) -> pd.DataFrame:
    """Match a fiscal quarter to a period end 350–380 days earlier.

    Nearest prior-year period within that window handles 52/53-week calendars.
    Missing quarters stay missing; a four-row shift would silently misalign gaps.
    No values are interpolated. Dates are reporting period ends, not release dates.
    """
    result = frame.sort_values("Date").copy()
    growth = []
    for row in result.itertuples():
        age = (row.Date - result["Date"]).dt.days
        candidates = result.loc[age.between(350, 380)]
        if candidates.empty:
            growth.append(np.nan)
            continue
        previous = candidates.loc[(age.loc[candidates.index] - 365).abs().idxmin(), "Revenue"]
        growth.append(row.Revenue / previous - 1 if previous > 0 else np.nan)
    result["YoY"] = growth
    return result
