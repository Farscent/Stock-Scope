"""StockScope Streamlit entry point. Run: streamlit run app.py."""

from datetime import date, timedelta
import math
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

# Support `streamlit run app.py` even when the CLI belongs to a different
# environment from the one used for the editable package installation.
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from stockscope.analytics import moving_averages, normalize_comparison, revenue_growth, stock_metrics
from stockscope.data import DataResult, DataUnavailable, fetch_prices, fetch_revenue, validate_ticker
from stockscope.visualization import comparison_chart, price_chart, revenue_chart, volume_chart

st.set_page_config(page_title="StockScope | Price & Revenue", layout="wide")
st.markdown("""<style>
.block-container {padding-top:2rem; max-width:1500px;}
h1 {letter-spacing:-0.035em;} h2,h3 {letter-spacing:-0.02em;}
[data-testid="stMetricValue"] {font-variant-numeric:tabular-nums;}
[data-testid="stMetric"] {border-bottom:1px solid #CBD9CF; padding:0.8rem 0;}
[data-testid="stSidebar"] {border-right:1px solid #D4DFD6;}
::selection {background:#C5DFCF;color:#172D32;}
a {text-underline-offset:3px;}
:focus-visible {outline:2px solid #12685F;outline-offset:3px;}
@media(max-width:640px) {.block-container {padding:1.5rem 1rem;}}
</style>""", unsafe_allow_html=True)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_prices(ticker: str, start: date, end: date) -> DataResult:
    """Cache successful price responses for one hour."""
    return fetch_prices(ticker, start, end)


@st.cache_data(ttl=21600, show_spinner=False)
def cached_revenue(ticker: str) -> DataResult:
    """Cache available quarterly statements for six hours."""
    return fetch_revenue(ticker)


def number(value: float, pattern: str = ",.2f") -> str:
    return format(value, pattern) if math.isfinite(value) else "Unavailable"


def show_table(frame: pd.DataFrame, filename: str) -> None:
    """Display native-frequency observations and offer their exact CSV values."""
    st.dataframe(frame, use_container_width=True, hide_index=True)
    st.download_button("Download CSV", frame.to_csv(index=False).encode("utf-8"),
                       file_name=filename, mime="text/csv", key=filename)


with st.sidebar:
    st.title("StockScope")
    st.caption("Stock market & revenue analytics")
    selection = st.selectbox("Company", ["TSLA", "GME", "Custom ticker"])
    ticker = st.text_input("Yahoo Finance ticker",
                           "AAPL") if selection == "Custom ticker" else selection
    horizon = st.selectbox(
        "Price window", ["1 year", "3 years", "5 years", "Custom dates"], index=1)
    today = date.today()
    if horizon == "Custom dates":
        start = st.date_input("Start date", today - timedelta(days=365), max_value=today)
        end = st.date_input("End date", today, max_value=today)
    else:
        years = {"1 year": 1, "3 years": 3, "5 years": 5}[horizon]
        start, end = today - timedelta(days=365 * years), today
    ma20 = st.checkbox("20-session moving average", value=True)
    ma50 = st.checkbox("50-session moving average", value=False)
    if st.button("Refresh data", use_container_width=True):
        cached_prices.clear()
        cached_revenue.clear()
    st.caption("Prices cached 1 hour · Statements cached 6 hours. Refresh requests a new provider response.")

st.title("Stock prices, in business context.")
st.write("Explore market performance alongside reported quarterly revenue. Tesla and GameStop are the core research examples.")
try:
    ticker = validate_ticker(ticker)
except ValueError as exc:
    st.error(str(exc))
    st.stop()
if start > end:
    st.error("Choose a start date on or before the end date.")
    st.stop()

overview, revenue_tab, compare, explorer, about = st.tabs(
    ["Market overview", "Company revenue", "Compare TSLA & GME", "Data explorer", "About & methodology"]
)
prices = None
price_error = None
with st.spinner(f"Retrieving {ticker} price observations…"):
    try:
        prices = cached_prices(ticker, start, end)
    except DataUnavailable as exc:
        price_error = str(exc)

with overview:
    st.subheader(f"{ticker} · Market overview")
    if prices is None:
        st.warning(price_error)
    else:
        frame = prices.frame
        metrics = stock_metrics(frame)
        st.caption(f"Observed sessions: {frame.Date.min():%d %b %Y} – {frame.Date.max():%d %b %Y} · "
                   f"Currency: {prices.currency} · Adjusted for splits and dividends")
        columns = st.columns(4)
        for column, label, value in zip(columns,
                                        ["Latest available close", "Previous session change",
                                            "Selected period return", "Average daily volume"],
                                        [number(metrics["latest"]), number(metrics["session_change"], ".2%"),
                                            number(metrics["period_return"], ".2%"), number(metrics["average_volume"], ",.0f")]):
            column.metric(label, value)
        windows = tuple(window for window, enabled in [(20, ma20), (50, ma50)] if enabled)
        if windows and len(frame) < max(windows):
            st.caption("A moving average appears only after its full number of selected trading sessions.")
        chart_data = moving_averages(frame, windows)
        st.plotly_chart(price_chart(chart_data, ticker, prices.currency), use_container_width=True)
        st.plotly_chart(volume_chart(frame, ticker), use_container_width=True)
        st.caption("Moving averages use only selected sessions and require a full window. Session change "
                   "requires two selected observations. Volume excludes missing observations from its mean.")
        st.caption(
            f"Source: {prices.source}. Retrieved {prices.retrieved_at}. Delayed data; not real-time.")

revenues = {}
revenue_errors = {}
for symbol in ("TSLA", "GME"):
    try:
        revenues[symbol] = cached_revenue(symbol)
    except DataUnavailable as exc:
        revenue_errors[symbol] = str(exc)

with revenue_tab:
    st.subheader("Quarterly revenue · Two business trajectories")
    st.write("Revenue uses fiscal reporting periods, independently of the price window. Dates are period ends, not announcement dates.")
    if selection == "Custom ticker":
        st.info("Custom tickers support price analysis only. Revenue below remains focused on TSLA and GME.")
    for column, symbol in zip(st.columns(2), ("TSLA", "GME")):
        with column:
            if symbol not in revenues:
                st.warning(revenue_errors[symbol])
                continue
            result = revenues[symbol]
            growth = revenue_growth(result.frame)
            latest = growth.iloc[-1]
            st.plotly_chart(revenue_chart(growth, symbol), use_container_width=True)
            st.write(
                f"Latest reported: **{latest.Date:%Y-%m-%d}** · **USD {latest.Revenue:,.1f} million**")
            st.write(f"Quarterly year-over-year growth: **{number(latest.YoY, '.2%')}**")
            if growth.YoY.isna().all():
                st.caption("Insufficient matching prior-year periods for year-over-year growth.")
            st.caption(f"{result.source}. Retrieved {result.retrieved_at}. "
                       "Latest provider-available period; this may lag company filings.")

with compare:
    st.subheader("Compare performance on shared trading dates")
    comparison_prices = {}
    for symbol in ("TSLA", "GME"):
        if symbol == ticker:
            if prices is not None:
                comparison_prices[symbol] = prices.frame
            else:
                st.warning(price_error)
            continue
        try:
            comparison_prices[symbol] = cached_prices(symbol, start, end).frame
        except DataUnavailable as exc:
            st.warning(str(exc))
    aligned = normalize_comparison(comparison_prices) if len(
        comparison_prices) == 2 else pd.DataFrame()
    if aligned.empty or len(aligned) < 2:
        st.info("At least two shared trading dates for both companies are needed for comparison.")
    else:
        st.plotly_chart(comparison_chart(aligned), use_container_width=True)
        st.caption(f"First common date {aligned.Date.min():%Y-%m-%d} = 100; "
                   f"last common date {aligned.Date.max():%Y-%m-%d}. Adjusted prices, no forward filling.")
        records = []
        for symbol in ("TSLA", "GME"):
            stats = stock_metrics(comparison_prices[symbol].loc[
                comparison_prices[symbol].Date.isin(aligned.Date)])
            records.append({"Ticker": symbol, "Window return": number(stats["period_return"], ".2%"),
                            "Annualized daily volatility": number(stats["volatility"], ".2%")})
        st.dataframe(pd.DataFrame(records), hide_index=True, use_container_width=True)
        st.caption("Volatility is sample standard deviation of shared-session returns × √252. "
                   "A missing shared session can make a return span more than one trading day.")
    st.write("Revenue comparisons should account for scale, seasonality and different fiscal calendars. "
             "Price and revenue charts alone do not establish causation.")

with explorer:
    st.subheader("Inspect & export observations")
    st.write("Historical adjusted prices · Selected window")
    if prices is not None:
        show_table(prices.frame, f"{ticker}_adjusted_prices_{start}_{end}.csv")
    else:
        st.info("Price data is unavailable for this selection.")
    for symbol, result in revenues.items():
        st.write(f"{symbol} quarterly revenue · USD millions · All provider-available periods")
        show_table(revenue_growth(result.frame), f"{symbol}_quarterly_revenue_usd_millions.csv")
    if not revenues:
        st.info("Quarterly statements are unavailable. Refresh later to retry.")

with about:
    st.subheader("A reproducible view of prices and revenue")
    st.markdown("""
StockScope studies Tesla and GameStop through daily market observations and quarterly business revenue.

- **Sources:** Yahoo Finance through yfinance for adjusted prices and quarterly Total Revenue.
  The original IBM-hosted HTML extraction is preserved as an opt-in historical notebook methodology,
  never an automatic current-data fallback.
- **Updates:** requests are made when the app runs; successful responses are cached for one hour
  (prices) or six hours (statements). Upstream data updates independently of these caches.
- **Metrics:** latest close is the final selected observation; session change compares the final
  two selected observations; window return is last/first − 1; average volume uses observed sessions.
  All prices are adjusted with `auto_adjust=True`. Custom tickers retain their provider currency.
- **Revenue:** reported USD amounts for TSLA/GME are converted to millions. Year-over-year growth
  matches a reported period end 350–380 days earlier, nearest to 365 days, to accommodate fiscal
  calendars. Missing comparisons remain unavailable; there is no interpolation.
- **Limitations:** prices may be delayed or revised, statement coverage can be short, fiscal calendars
  differ, and provider responses can fail. Period ends are not the dates investors learned the results;
  aligning them with prices would introduce look-ahead bias. No causal or trading claims are made.

Research notebook: `notebooks/01_stock_revenue_analysis.ipynb`. Source and execution details are in the README.
""")
