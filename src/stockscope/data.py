"""External adapters: Yahoo Finance and opt-in archived HTML methodology."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import os
import re

from bs4 import BeautifulSoup
import pandas as pd
import requests
import yfinance as yf

from stockscope.preprocessing import clean_prices, clean_revenue

HISTORICAL_URLS = {
    "TSLA": "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/"
            "IBMDeveloperSkillsNetwork-PY0220EN-SkillsNetwork/labs/project/revenue.htm",
    "GME": "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/"
           "IBMDeveloperSkillsNetwork-PY0220EN-SkillsNetwork/labs/project/stock.html",
}
COMPANIES = {"TSLA": "Tesla", "GME": "GameStop"}

# Optional override for containers or read-only user profiles. Normal installations
# retain yfinance's standard user cache location.
if os.environ.get("STOCKSCOPE_CACHE_DIR"):
    yf.set_tz_cache_location(os.environ["STOCKSCOPE_CACHE_DIR"])


class DataUnavailable(RuntimeError):
    """Expected provider failure or unavailable dataset."""


@dataclass
class DataResult:
    """A dataset with explicit provenance; timestamps describe retrieval only."""

    frame: pd.DataFrame
    source: str
    retrieved_at: str
    currency: str = "USD"
    historical: bool = False


def validate_ticker(ticker: str) -> str:
    """Accept common Yahoo ticker punctuation while bounding user input."""
    ticker = ticker.strip().upper()
    if not re.fullmatch(r"[A-Z0-9^][A-Z0-9.^=\-]{0,19}", ticker):
        raise ValueError("Enter a valid Yahoo Finance ticker (up to 20 characters).")
    return ticker


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fetch_prices(ticker: str, start: date, end: date) -> DataResult:
    """Fetch inclusive dates with explicit split/dividend adjustment and timeout."""
    ticker = validate_ticker(ticker)
    if start > end:
        raise ValueError("Start date must be on or before end date.")
    try:
        instrument = yf.Ticker(ticker)
        raw = instrument.history(
            start=start.isoformat(), end=(end + timedelta(days=1)).isoformat(),
            auto_adjust=True, actions=False, timeout=20, raise_errors=True,
        )
        frame = clean_prices(raw)
        frame = frame.loc[frame["Date"].between(pd.Timestamp(start), pd.Timestamp(end))]
        if frame.empty:
            raise DataUnavailable(f"No price observations for {ticker} in this window.")
        try:
            metadata = instrument.history_metadata or {}
            currency = metadata.get("currency") or "currency unavailable"
        except Exception:
            # A failed metadata lookup must not discard valid price observations.
            currency = "currency unavailable"
    except DataUnavailable:
        raise
    except Exception as exc:
        raise DataUnavailable(
            f"Price data unavailable for {ticker}. Check the ticker, dates or connection and retry."
        ) from exc
    return DataResult(frame.reset_index(drop=True), "Yahoo Finance via yfinance; auto_adjust=True",
                      _timestamp(), currency=currency)


def fetch_revenue(ticker: str) -> DataResult:
    """Retrieve reported quarterly Total Revenue for the two USD-reporting examples.

    Yahoo's available statement history is often short. No annual/TTM substitution.
    """
    ticker = validate_ticker(ticker)
    if ticker not in COMPANIES:
        raise DataUnavailable("Quarterly revenue is supported for TSLA and GME only.")
    try:
        statements = yf.Ticker(ticker).get_income_stmt(freq="quarterly")
        revenue_key = next((key for key in ("TotalRevenue", "Total Revenue")
                            if key in statements.index), None)
        if statements.empty or revenue_key is None:
            raise DataUnavailable(f"No quarterly Total Revenue statement available for {ticker}.")
        values = statements.loc[revenue_key]
        raw = pd.DataFrame({"Date": values.index, "Revenue": values.to_numpy()})
        raw["Revenue"] = pd.to_numeric(raw["Revenue"], errors="coerce") / 1_000_000
        frame = clean_revenue(raw)
        if frame.empty:
            raise DataUnavailable(f"No valid quarterly revenue observations for {ticker}.")
    except DataUnavailable:
        raise
    except Exception as exc:
        raise DataUnavailable(f"Quarterly revenue unavailable for {ticker}; retry later.") from exc
    return DataResult(frame, "Yahoo Finance quarterly income statement: Total Revenue (USD millions)",
                      _timestamp())


def parse_historical_revenue(html: str, company: str) -> pd.DataFrame:
    """Locate a named quarterly revenue table by semantic heading, never position."""
    soup = BeautifulSoup(html, "html.parser")
    matches = []
    for table in soup.find_all("table"):
        headers = " ".join(item.get_text(" ", strip=True)
                           for item in table.find_all(["th", "caption"]))
        if not all(word.lower() in headers.lower() for word in (company, "quarterly", "revenue")):
            continue
        if "million" not in headers.lower() or not any(unit in headers.lower() for unit in ("us $", "usd")):
            raise DataUnavailable("Historical revenue table must explicitly identify USD millions.")
        rows = []
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if cells and len(cells) != 2:
                raise DataUnavailable("Historical revenue table must have two data columns.")
            if len(cells) == 2:
                rows.append([cell.get_text(strip=True) for cell in cells])
        frame = clean_revenue(pd.DataFrame(rows, columns=["Date", "Revenue"]))
        if not frame.empty:
            matches.append(frame)
    if len(matches) != 1:
        raise DataUnavailable(
            "Expected one named, nonempty quarterly revenue table; archive may have changed.")
    return matches[0]


def fetch_historical_revenue(ticker: str) -> DataResult:
    """Opt-in historical reference only. Never called as an automatic live fallback."""
    if ticker not in HISTORICAL_URLS:
        raise ValueError("Historical examples are limited to TSLA and GME.")
    try:
        response = requests.get(HISTORICAL_URLS[ticker], timeout=(5, 20))
        response.raise_for_status()
        frame = parse_historical_revenue(response.text, COMPANIES[ticker])
    except (requests.RequestException, ValueError) as exc:
        raise DataUnavailable("Historical reference could not be retrieved or parsed.") from exc
    return DataResult(frame, f"Historical IBM-hosted reference: {HISTORICAL_URLS[ticker]}",
                      _timestamp(), historical=True)
