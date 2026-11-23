from datetime import date
from unittest.mock import Mock

import pandas as pd
import pytest

from stockscope.data import (
    DataUnavailable, fetch_historical_revenue, fetch_prices, fetch_revenue,
    parse_historical_revenue, validate_ticker,
)


def test_archive_table_is_located_by_meaning_not_index():
    html = """<table><tr><th>Unrelated</th></tr></table>
    <table><thead><tr><th>Tesla Quarterly Revenue (Millions of US $)</th></tr></thead>
    <tbody><tr><td>2020-03-31</td><td>$5,985</td></tr></tbody></table>"""
    assert parse_historical_revenue(html, "Tesla").Revenue.tolist() == [5985.0]
    with pytest.raises(DataUnavailable):
        parse_historical_revenue(html, "GameStop")
    with pytest.raises(DataUnavailable):
        parse_historical_revenue(html + html, "Tesla")


def test_http_timeout_and_status(monkeypatch):
    response = Mock(text="not a table")
    get = Mock(return_value=response)
    monkeypatch.setattr("stockscope.data.requests.get", get)
    with pytest.raises(DataUnavailable):
        fetch_historical_revenue("TSLA")
    response.raise_for_status.assert_called_once()
    assert get.call_args.kwargs["timeout"] == (5, 20)


def test_yahoo_statement_units_and_missing_data(monkeypatch):
    provider = Mock()
    provider.get_income_stmt.return_value = pd.DataFrame(
        {pd.Timestamp("2024-03-31"): [1_000_000]}, index=["TotalRevenue"])
    monkeypatch.setattr("stockscope.data.yf.Ticker", Mock(return_value=provider))
    assert fetch_revenue("TSLA").frame.Revenue.tolist() == [1.0]
    provider.get_income_stmt.return_value = pd.DataFrame()
    with pytest.raises(DataUnavailable):
        fetch_revenue("GME")
    provider.get_income_stmt.side_effect = ConnectionError("offline")
    with pytest.raises(DataUnavailable):
        fetch_revenue("TSLA")
    with pytest.raises(DataUnavailable):
        fetch_revenue("AAPL")


def test_price_dates_adjustment_currency_and_failure(monkeypatch):
    provider = Mock(history_metadata={"currency": "EUR"})
    provider.history.return_value = pd.DataFrame({"Close": [10, 11]},
                                                 index=pd.date_range("2024-01-01", periods=2))
    monkeypatch.setattr("stockscope.data.yf.Ticker", Mock(return_value=provider))
    result = fetch_prices("test", date(2024, 1, 1), date(2024, 1, 2))
    assert result.currency == "EUR"
    assert provider.history.call_args.kwargs["end"] == "2024-01-03"
    assert provider.history.call_args.kwargs["auto_adjust"] is True
    provider.history.return_value = pd.DataFrame()
    with pytest.raises(DataUnavailable):
        fetch_prices("TSLA", date(2024, 1, 1), date(2024, 1, 2))
    provider.history.side_effect = ConnectionError("offline")
    with pytest.raises(DataUnavailable):
        fetch_prices("TSLA", date(2024, 1, 1), date(2024, 1, 2))


def test_ticker_validation():
    assert validate_ticker(" brk-b ") == "BRK-B"
    with pytest.raises(ValueError):
        validate_ticker("<script>")
