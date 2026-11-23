import math

import pandas as pd
import pytest

from stockscope.analytics import (
    moving_averages, normalize_comparison, period_return, revenue_growth, stock_metrics,
)


def prices(values, start="2024-01-01"):
    return pd.DataFrame({"Date": pd.date_range(start, periods=len(values)), "Close": values,
                         "Volume": [100.0] * len(values)})


def test_returns_and_selected_session_metrics():
    frame = prices([100, 110, 121])
    frame.loc[1, "Volume"] = None
    result = stock_metrics(frame)
    assert result["period_return"] == pytest.approx(0.21)
    assert result["session_change"] == pytest.approx(0.1)
    assert result["average_volume"] == 100
    assert result["volatility"] == pytest.approx(0, abs=1e-12)
    assert math.isnan(period_return(pd.Series([10])))
    assert math.isnan(period_return(pd.Series([0, 10])))
    assert math.isnan(stock_metrics(frame.iloc[:1])["session_change"])
    assert math.isnan(stock_metrics(frame.iloc[:0])["latest"])


def test_moving_averages_full_trailing_window():
    result = moving_averages(prices([10, 20, 30, 40]).iloc[::-1], (2, 3))
    assert result.MA2.iloc[1:].tolist() == [15, 25, 35]
    assert result.MA2.iloc[:1].isna().all()
    assert result.MA3.iloc[:2].isna().all()
    assert result.MA3.iloc[-1] == 30
    with pytest.raises(ValueError):
        moving_averages(prices([1]), (0,))


def test_normalize_only_shared_valid_dates():
    a = prices([10, 20, 30])
    b = prices([50, 100, 150], start="2024-01-02")
    result = normalize_comparison({"TSLA": a, "GME": b})
    assert result.TSLA.tolist() == [100, 150]
    assert result.GME.tolist() == [100, 200]
    assert result.Date.min() == pd.Timestamp("2024-01-02")
    assert normalize_comparison({"TSLA": a, "GME": b.iloc[:0]}).empty
    assert normalize_comparison({"TSLA": a, "GME": prices([1], "2020-01-01")}).empty


def test_yoy_matches_periods_without_bridging_missing_quarters():
    raw = pd.DataFrame({"Date": pd.to_datetime(["2023-02-04", "2023-08-05", "2024-02-03", "2024-05-04"]),
                        "Revenue": [100, 0, 120, 140]})
    result = revenue_growth(raw)
    assert result.YoY.iloc[2] == pytest.approx(0.2)
    assert pd.isna(result.YoY.iloc[3])
    assert result.YoY.iloc[:2].isna().all()
