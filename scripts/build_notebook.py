"""Author the research notebook. Run from the repository root when editing its narrative."""

from pathlib import Path

import nbformat as nbf

cells = []


def markdown(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip()))


def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip()))


markdown("""
# StockScope — Stock Market & Revenue Analytics

## 1. Introduction

### Background and problem statement
Market prices summarize investors' changing expectations; revenue records realized
business activity over a reporting period. Studying them together is useful, but
their frequencies, units and information dates differ. Tesla (TSLA) and GameStop
(GME) provide two contrasting research examples without requiring a forecasting model.

### Objectives
Build a reproducible pipeline for daily adjusted prices and quarterly revenue,
validate observations, explore price and revenue evolution, and compare performance
on a shared trading-date basis. This notebook shares its implementation with the
Streamlit dashboard rather than maintaining a second analytical pipeline.

### Research questions
1. How do adjusted price paths, returns and daily trading volume differ within the chosen window?
2. What quarterly revenue patterns and year-over-year changes are observable?
3. How does a shared index change the comparison relative to raw share prices?
4. What can these observations support, and what remains uncertain?
""")
markdown("""
## 2. Data Sources and Methodology

**Prices:** Yahoo Finance via yfinance, daily frequency, explicitly adjusted for
splits and dividends (`auto_adjust=True`). These adjusted prices are retrospective
series, not raw execution prices. The provider's observation dates and currencies
are retained. Exchange-local trading dates are standardized without UTC day shifts.

**Revenue:** Yahoo's quarterly income statements, specifically Total Revenue for
TSLA/GME, reported in USD and converted to **USD millions**. Coverage is often
limited to recent quarters. Missing financial statements remain unavailable.
Fiscal period ends are not earnings-release dates. No daily revenue is synthesized.

**Historical extraction:** the original work located quarterly revenue in
IBM-hosted archived HTML examples. A separate opt-in adapter below demonstrates
that methodology using company/quarterly/revenue headers, two-column validation,
HTTP status checks and timeouts. These pages are historical references, never a
live financial service or an automatic substitute for current statements.

**Limitations:** provider outages, short statement histories, revisions, delays,
different fiscal calendars and corporate actions affect interpretation. No causal
model connects price movements to revenue. This is descriptive research, not advice.

Use the repository environment (`pip install -r requirements.txt`) and select its
Jupyter kernel before running all cells. No cell installs packages. Re-running
retrieves a new vintage of data, so observations and conclusions may change.
""")
code("""
from datetime import date, timedelta
from pathlib import Path
import sys

import pandas as pd
import plotly.io as pio
from IPython.display import Markdown, display

# Work from either the repository root or notebooks/; no absolute user paths.
ROOT = Path.cwd() if (Path.cwd() / 'pyproject.toml').exists() else Path.cwd().parent
if not (ROOT / 'src' / 'stockscope').is_dir():
    raise RuntimeError('Open this notebook from the repository root or notebooks/ directory.')
sys.path.insert(0, str(ROOT / 'src'))

from stockscope.data import DataUnavailable, fetch_prices, fetch_revenue, fetch_historical_revenue
from stockscope.preprocessing import clean_prices, clean_revenue
from stockscope.analytics import stock_metrics, moving_averages, normalize_comparison, revenue_growth
from stockscope.visualization import price_chart, revenue_chart, volume_chart, comparison_chart

pio.renderers.default = 'notebook_connected'
TICKERS = ('TSLA', 'GME')
END = date.today()
START = END - timedelta(days=365 * 5)
USE_HISTORICAL_REFERENCE = False  # Explicit opt-in; never mixed with fresh statements.
print(f'Inclusive price request: {START} to {END}; revenue: all provider-available quarters.')
""")
markdown("""
## 3. Data Collection

Collect each company and dataset independently. A failed source must not remove
the other company's results. Record retrieval time separately from the last
observation date. An unavailable-data execution verifies notebook control flow;
it cannot validate live financial results.
""")
code("""
price_results, revenue_results, failures = {}, {}, []
for ticker in TICKERS:
    for kind, fetcher, target in (
        ('Prices', lambda symbol: fetch_prices(symbol, START, END), price_results),
        ('Quarterly revenue', fetch_revenue, revenue_results),
    ):
        try:
            target[ticker] = fetcher(ticker)
        except DataUnavailable as exc:
            failures.append({'Ticker': ticker, 'Dataset': kind, 'Status': str(exc)})

if failures:
    display(pd.DataFrame(failures))
provenance = []
for kind, results in [('Prices', price_results), ('Quarterly revenue', revenue_results)]:
    for ticker, result in results.items():
        provenance.append({'Ticker': ticker, 'Dataset': kind, 'Rows': len(result.frame),
            'First observation': result.frame.Date.min(), 'Last observation': result.frame.Date.max(),
            'Retrieved UTC': result.retrieved_at, 'Currency': result.currency, 'Source': result.source})
display(pd.DataFrame(provenance))
""")
markdown("""
### Optional historical extraction reference

Enable the configuration flag above to inspect the archived method. Results stay
in a dedicated dictionary and are explicitly labeled historical. Dates and values
are read from the source, not inferred from saved chart images or reconstructed.
No archived page or educational instructions are bundled with this repository.
""")
code("""
historical_examples = {}
if USE_HISTORICAL_REFERENCE:
    for ticker in TICKERS:
        try:
            result = fetch_historical_revenue(ticker)
            historical_examples[ticker] = result
            display(Markdown(f'**{ticker}: HISTORICAL SNAPSHOT**, last period {result.frame.Date.max():%Y-%m-%d}'))
            display(result.frame.tail())
            print(result.source)
        except DataUnavailable as exc:
            print(f'{ticker} historical reference unavailable: {exc}')
else:
    print('Historical archive access disabled. No historical snapshot is presented as current.')
""")
markdown("""
## 4. Data Cleaning and Preprocessing

The adapters use shared deterministic cleaners. Revenue currency strings lose
dollar signs, commas and whitespace and become numeric; blanks, invalid numeric
values and invalid dates are discarded. Accounting negatives are supported and
zero remains valid. Prices require valid positive closes; missing volume remains
missing rather than becoming zero. Infinite values are invalid.

Dates become timezone-naive calendar dates, observations are sorted ascending,
and duplicate dates keep the last valid supplied row. There is no forward fill
or interpolation. The following revalidation checks idempotency and reports
post-cleaning quality; it does not claim a raw-source rejection count.
""")
code("""
prices = {ticker: clean_prices(result.frame) for ticker, result in price_results.items()}
revenues = {ticker: clean_revenue(result.frame) for ticker, result in revenue_results.items()}
quality = []
for kind, frames in [('Prices', prices), ('Revenue', revenues)]:
    for ticker, frame in frames.items():
        original = (price_results if kind == 'Prices' else revenue_results)[ticker].frame
        assert frame.equals(original), 'Cleaning must be idempotent.'
        assert frame.Date.is_monotonic_increasing and not frame.Date.duplicated().any()
        quality.append({'Ticker': ticker, 'Dataset': kind, 'Clean rows': len(frame),
                        'Duplicate dates': int(frame.Date.duplicated().sum()),
                        'Missing cells': int(frame.isna().sum().sum()),
                        'Date dtype': str(frame.Date.dtype)})
display(pd.DataFrame(quality))
""")
markdown("""
## 5. Exploratory Data Analysis

### Overview and descriptive statistics
Inspect coverage before comparing outcomes. Financial statement availability
need not match the daily price window. Adjusted share prices are measured per
share; quarterly revenue measures the business and has a different scale.
""")
code("""
for ticker in TICKERS:
    display(Markdown(f'### {ticker}'))
    if ticker in prices:
        display(prices[ticker].head())
        display(prices[ticker][['Close', 'Volume']].describe())
    if ticker in revenues:
        display(revenues[ticker].tail())
        display(revenues[ticker][['Revenue']].describe())
    if ticker not in prices and ticker not in revenues:
        print('Neither source returned valid observations. No financial findings can be computed.')
""")
markdown("""
### Stock price evolution and trading volume
Use full 20/50-session trailing means within the requested window. The first
19/49 observations have no corresponding mean. Returns compare observed endpoint
closes; daily volatility uses sample standard deviation multiplied by √252.
Neither measure predicts future outcomes.
""")
code("""
for ticker, frame in prices.items():
    display(price_chart(moving_averages(frame), ticker, price_results[ticker].currency))
    metrics = stock_metrics(frame)
    display(Markdown(f'**Observed price path:** {ticker} changed by {metrics["period_return"]:.2%} '
        f'from {frame.Date.min():%Y-%m-%d} to {frame.Date.max():%Y-%m-%d}. '
        'The endpoint return does not describe intervening drawdowns.'))
    display(volume_chart(frame, ticker))
    peak = frame.dropna(subset=['Volume']).sort_values('Volume').tail(1)
    if not peak.empty:
        row = peak.iloc[0]
        display(Markdown(f'**Observed activity:** largest selected daily volume was {row.Volume:,.0f} '
            f'shares on {row.Date:%Y-%m-%d}. Volume alone does not identify the reason for trading.'))
if not prices:
    display(Markdown('**Price analysis unavailable:** no valid prices were retrieved.'))
""")
markdown("""
### Revenue evolution and quarterly year-over-year growth
Bars represent separate reported quarters in USD millions. Compare a quarter
with a reported period end 350–380 days earlier, nearest 365 days, to allow
52/53-week fiscal calendars. A missing or zero prior-year base yields no growth
rate. This date heuristic is disclosed and should be checked against filings
before drawing detailed fiscal conclusions.
""")
code("""
growth_tables = {}
for ticker, frame in revenues.items():
    growth = revenue_growth(frame)
    growth_tables[ticker] = growth
    display(revenue_chart(frame, ticker))
    display(growth)
    latest = growth.iloc[-1]
    interpretation = (f'**Observed revenue:** {ticker} reported USD {latest.Revenue:,.1f} million '
                      f'for the period ended {latest.Date:%Y-%m-%d}. ')
    interpretation += (f'The matched prior-year change is {latest.YoY:.2%}.' if pd.notna(latest.YoY)
                       else 'A valid matched prior-year growth rate is unavailable.')
    display(Markdown(interpretation + ' This is the latest provider-available period, not a claim of filing completeness.'))
if not revenues:
    display(Markdown('**Revenue analysis unavailable:** no valid quarterly statements were retrieved.'))
""")
markdown("""
## 6. Comparative Analysis

### Normalized stock performance
Inner-join valid dates within the chosen window, then set both series to 100
on the first shared date. No pre-window prices or forward-filled observations
enter the comparison. This separates relative price performance from arbitrary
per-share levels and share-split histories.
""")
code("""
comparison = normalize_comparison(prices) if set(prices) == set(TICKERS) else pd.DataFrame()
comparison_stats = []
if len(comparison) >= 2:
    display(comparison_chart(comparison))
    for ticker in TICKERS:
        shared = prices[ticker].loc[prices[ticker].Date.isin(comparison.Date)]
        metrics = stock_metrics(shared)
        comparison_stats.append({'Ticker': ticker, 'Window return': metrics['period_return'],
                                 'Annualized daily volatility': metrics['volatility']})
    display(pd.DataFrame(comparison_stats).set_index('Ticker').style.format('{:.2%}'))
    last = comparison.iloc[-1]
    display(Markdown(f'**Observed comparison:** starting on {comparison.Date.min():%Y-%m-%d}, '
        f'the index ends at TSLA {last.TSLA:.2f} and GME {last.GME:.2f} '
        f'on {comparison.Date.max():%Y-%m-%d}. These endpoints are specific to this window.'))
else:
    display(Markdown('**Comparison unavailable:** at least two shared dates for both companies are required.'))
""")
markdown("""
### Revenue trends and business context
Compare reported quarter values, year-over-year growth where available and
coverage explicitly. Tesla and GameStop operate different businesses; revenue
scale is not a profitability or valuation comparison. Fiscal calendars and
seasonality can differ. A simple price/revenue correlation would conflate
frequencies and information dates, so it is deliberately omitted.
""")
code("""
revenue_summary = []
for ticker, frame in growth_tables.items():
    last = frame.iloc[-1]
    revenue_summary.append({'Ticker': ticker, 'Available quarters': len(frame),
        'First period': frame.Date.min(), 'Last period': last.Date,
        'Latest revenue (USD million)': last.Revenue, 'Latest YoY (fraction)': last.YoY})
display(pd.DataFrame(revenue_summary))
if len(revenue_summary) == 2:
    display(Markdown('**Interpretation:** the table compares each company’s latest available quarter, '
        'which may have different period ends. Compare equivalent fiscal periods and company filings '
        'before attributing differences to business performance.'))
""")
markdown("""
## 7. Key Findings and Discussion

The summary below is generated from this execution, not from remembered prices
or fabricated historical figures. Missing sources reduce the questions that can
be answered. Changes in prices can reflect expectations, liquidity and many
other factors that this descriptive dataset cannot identify.
""")
code("""
findings = []
for ticker, frame in prices.items():
    metrics = stock_metrics(frame)
    findings.append(f'{ticker}: {len(frame):,} daily observations; selected adjusted-price '
                    f'return {metrics["period_return"]:.2%}.')
for ticker, frame in growth_tables.items():
    findings.append(f'{ticker}: {len(frame)} reported quarters; revenue coverage ends '
                    f'{frame.Date.max():%Y-%m-%d}.')
if not findings:
    findings.append('No live observations were retrieved. This execution supports no numerical market or revenue conclusions.')
display(Markdown('\\n'.join('- ' + item for item in findings)))
display(Markdown('**Business interpretation:** price performance and revenue growth answer different '
    'questions. Neither a rising share price nor rising revenue establishes stronger profitability. '
    'Revenue release dates, valuation, costs and market context would be needed for a richer explanation.'))
""")
markdown("""
## 8. Conclusion and Future Improvements

This project turns two company examples into a reusable descriptive workflow:
explicit sources, validated data, separate financial frequencies, common-date
price comparisons and computed findings. Availability determines the strength
of the conclusions; unavailable data is itself a reproducibility limitation,
not a reason to manufacture a result.

Future improvements include filing-backed revenue validation, earnings-release
timestamps, retrieval-vintage snapshots where redistribution is permitted,
fiscal-period identifiers and additional financial context such as margins.
Keep deterministic tests separate from optional live integration checks.

The Streamlit application reuses these modules for interactive exploration and
CSV export. See the README for installation, data access limits, attribution and
the test commands. No forecasting or trading recommendations are included.
""")

notebook = nbf.v4.new_notebook(cells=cells)
notebook.metadata.kernelspec = {
    "display_name": "Python 3 (ipykernel)", "language": "python", "name": "python3"}
notebook.metadata.language_info = {"name": "python", "version": "3.11"}
target = Path("notebooks/01_stock_revenue_analysis.ipynb")
target.parent.mkdir(exist_ok=True)
nbf.write(notebook, target)
print(f"Wrote {target}: {len(cells)} cells")
