"""UI integration with synthetic fixtures only; no provider calls or fake financial claims."""

from datetime import date
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from stockscope.data import DataResult, DataUnavailable

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_launch_without_editable_package_install():
    """The app must discover src even if its interpreter has no installed package."""
    script = f"""
import importlib.util
from pathlib import Path
import sys
from unittest.mock import Mock

source = Path({str(APP.parent / 'src')!r}).resolve()
sys.path = [entry for entry in sys.path if Path(entry).resolve() != source]
assert importlib.util.find_spec('stockscope') is None

import yfinance as yf
from streamlit.testing.v1 import AppTest
yf.Ticker = Mock(side_effect=ConnectionError('offline regression test'))
app = AppTest.from_file({str(APP)!r}).run(timeout=30)
assert not app.exception, [error.message for error in app.exception]
assert len(app.tabs) == 5
"""
    result = subprocess.run([sys.executable, "-c", script],
                            cwd=APP.parent, capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.fixture(autouse=True)
def reset_streamlit_cache():
    import streamlit as st
    st.cache_data.clear()
    yield
    st.cache_data.clear()


def synthetic_prices(ticker, start, end):
    dates = pd.bdate_range(start, end)
    frame = pd.DataFrame({"Date": dates, "Close": [100.0 + i for i in range(len(dates))],
                          "Volume": [1000.0] * len(dates)})
    return DataResult(frame, "SYNTHETIC TEST FIXTURE", "2024-01-01T00:00:00+00:00")


def synthetic_revenue(ticker):
    return DataResult(pd.DataFrame({"Date": pd.date_range("2023-03-31", periods=8, freq="QE"),
                                    "Revenue": [100.0 + i for i in range(8)]}),
                      "SYNTHETIC TEST FIXTURE", "2024-01-01T00:00:00+00:00")


def test_selection_custom_ticker_charts_and_refresh(monkeypatch):
    price_fetch = Mock(side_effect=synthetic_prices)
    revenue_fetch = Mock(side_effect=synthetic_revenue)
    monkeypatch.setattr("stockscope.data.fetch_prices", price_fetch)
    monkeypatch.setattr("stockscope.data.fetch_revenue", revenue_fetch)
    app = AppTest.from_file(APP).run(timeout=30)
    assert not app.exception
    assert len(app.metric) == 4
    assert app.metric[0].value != "Unavailable"
    assert len(app.get("plotly_chart")) == 5
    assert len(app.get("download_button")) == 3
    app.selectbox[0].select("GME").run()
    assert not app.exception
    assert "GME" in app.subheader[0].value
    app.selectbox[0].select("Custom ticker").run()
    app.text_input[0].set_value("MSFT").run()
    assert not app.exception
    assert "MSFT" in app.subheader[0].value
    before = price_fetch.call_count
    app.button[0].click().run()
    assert price_fetch.call_count > before
    assert not app.exception
    app.selectbox[1].select("Custom dates").run()
    app.date_input[0].set_value(date(2024, 1, 2))
    app.date_input[1].set_value(date(2024, 1, 2)).run()
    assert not app.exception
    assert app.metric[1].value == "Unavailable"
    assert app.metric[2].value == "Unavailable"


def test_missing_financial_data_and_invalid_ticker(monkeypatch):
    monkeypatch.setattr("stockscope.data.fetch_prices", synthetic_prices)
    monkeypatch.setattr("stockscope.data.fetch_revenue", Mock(
        side_effect=DataUnavailable("Statement unavailable")))
    app = AppTest.from_file(APP).run(timeout=30)
    assert not app.exception
    assert len(app.warning) == 2
    assert len(app.metric) == 4
    app.selectbox[0].select("Custom ticker").run()
    app.text_input[0].set_value("<bad>").run()
    assert not app.exception
    assert "valid Yahoo" in app.error[0].value


def test_total_network_failure_keeps_methodology_available(monkeypatch):
    monkeypatch.setattr("stockscope.data.fetch_prices", Mock(
        side_effect=DataUnavailable("Prices offline")))
    monkeypatch.setattr("stockscope.data.fetch_revenue", Mock(
        side_effect=DataUnavailable("Statements offline")))
    app = AppTest.from_file(APP).run(timeout=30)
    assert not app.exception
    assert len(app.tabs) == 5
    assert len(app.metric) == 0
    assert len(app.warning) >= 3
