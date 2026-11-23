import numpy as np
import pandas as pd

from stockscope.preprocessing import clean_prices, clean_revenue, standardize_dates


def test_currency_missing_dates_and_duplicates():
    raw = pd.DataFrame({
        "Date": ["2024-06-30", "bad", "2024-03-31", "2024-06-30", "2024-09-30",
                 "2024-12-31", "2025-03-31", "2025-06-30"],
        "Revenue": ["$1,234.50", "$5", " (250) ", "$1,300", "", None, "0", "inf"],
    })
    result = clean_revenue(raw)
    assert result.Revenue.tolist() == [-250.0, 1300.0, 0.0]
    assert result.Date.dt.strftime(
        "%Y-%m-%d").tolist() == ["2024-03-31", "2024-06-30", "2025-03-31"]
    assert pd.api.types.is_float_dtype(result.Revenue)
    assert clean_revenue(result).equals(result)


def test_exchange_calendar_date_preserved():
    result = standardize_dates(pd.Series(["2024-01-02 23:00:00-05:00", "invalid", None]))
    assert result.iloc[0] == pd.Timestamp("2024-01-02")
    assert result.iloc[1:].isna().all()
    assert result.dt.tz is None


def test_prices_clean_index_missing_close_invalid_volume():
    raw = pd.DataFrame({"Close": [10, None, -2, 12, 13], "Volume": [100, 200, 30, -1, None]},
                       index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03",
                                             "2024-01-04", "2024-01-05"], utc=True))
    result = clean_prices(raw)
    assert result.Close.tolist() == [10, 12, 13]
    assert result.Volume.iloc[1:].isna().all()
    assert result.Date.dt.tz is None


def test_empty_inputs_keep_schema():
    assert clean_revenue(pd.DataFrame()).columns.tolist() == ["Date", "Revenue"]
    assert clean_prices(pd.DataFrame()).empty
    assert clean_prices(pd.DataFrame({"Date": ["2024-01-01"], "Close": [np.inf]})).empty
