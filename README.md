# StockScope — Stock Market & Revenue Analytics Dashboard

A Python analytics project connecting daily stock-market observations with
quarterly business revenue. Tesla (TSLA) and GameStop (GME) remain the primary
research examples. A research notebook and an interactive Streamlit dashboard
share the same tested data pipeline.

## Dashboard Preview

The dashboard provides five views: **Market overview**, **Company revenue**,
**Compare TSLA & GME**, **Data explorer**, and **About & methodology**. Sidebar
controls select the ticker, price window, moving averages and refresh behavior.
<img width="1808" height="994" alt="image" src="https://github.com/user-attachments/assets/36ae7c2e-8f67-401d-a6a9-ea8638cc84cd" />
<img width="1815" height="997" alt="image" src="https://github.com/user-attachments/assets/e5464f4f-7535-4f3a-9ab5-dae75a3b180c" />
<img width="1818" height="994" alt="image" src="https://github.com/user-attachments/assets/5d0c7bcf-458e-4f8c-849b-0b27645e761d" />
<img width="1320" height="962" alt="image" src="https://github.com/user-attachments/assets/3cb8b519-8cd4-40f5-b7ad-6ee802334414" />
<img width="1813" height="996" alt="image" src="https://github.com/user-attachments/assets/5700b38a-96a8-4fdd-b7f7-9239f73d26a1" />


**Streamlit deployment:** deployed
https://stock-scope-dashboard.streamlit.app

## Problem Statement

Stock prices and company revenue answer different questions. Comparing them
requires explicit adjustments, valid dates, consistent units, and respect for
daily market versus quarterly accounting frequencies. This project makes that
workflow reviewable without implying a causal relationship.

## Project Objectives

- Collect and validate historical prices and reported quarterly revenue.
- Examine returns, price evolution, trading activity and revenue trends.
- Compare TSLA/GME performance on shared trading dates, starting at index 100.
- Provide reproducible research, transparent limitations and reusable code.

## Key Features

- TSLA/GME selection and optional Yahoo custom tickers for price analysis.
- Inclusive date windows, refresh, explicit adjusted prices and actual last dates.
- Closing price, session change, selected-period return and average-volume KPIs.
- Interactive Plotly prices, optional 20/50-session averages and volume charts.
- Quarterly TSLA/GME revenue in USD millions and matched prior-year growth.
- Common-date performance comparison, returns and annualized daily volatility.
- Sortable data tables and CSV downloads, with graceful source-failure messages.
- One-hour price caching and six-hour statement caching using `st.cache_data`.

## Technology Stack

Python 3.11+, pandas, NumPy, yfinance, requests, BeautifulSoup, Plotly,
Streamlit, Jupyter, pytest and Ruff. Dependency ranges live in `pyproject.toml`;
`requirements.txt` installs the package and development/notebook tools.

## Project Architecture

```text
StockScope/
├── app.py
├── src/stockscope/
│   ├── __init__.py
│   ├── data.py                 # provider adapters and provenance
│   ├── preprocessing.py        # deterministic validation and cleaning
│   ├── analytics.py            # metrics, averages, alignment and growth
│   └── visualization.py        # pure Plotly figure builders
├── notebooks/01_stock_revenue_analysis.ipynb
├── tests/
│   ├── test_preprocessing.py
│   ├── test_analytics.py
│   ├── test_data.py
│   ├── test_visualization.py
│   ├── test_app.py
│   └── test_notebook.py
├── scripts/build_notebook.py   # editable notebook narrative source
├── docs/
│   ├── notebook_audit.md
│   └── validation.md
├── assets/
├── .streamlit/config.toml
├── .github/workflows/tests.yml
├── PRODUCT.md
├── DESIGN.md
├── pyproject.toml
├── requirements.txt
├── .gitignore
└── LICENSE
```

The original course notebook is retained locally and ignored by Git. No course
logos, instructions, screenshots or bundled archived pages are redistributed.

## Data Sources

| Dataset | Source | Frequency and scope |
| --- | --- | --- |
| Adjusted OHLC prices and volume | [Yahoo Finance](https://finance.yahoo.com/) through [yfinance](https://github.com/ranaroussi/yfinance) | Daily, selected inclusive window; provider currency |
| Total Revenue | Yahoo quarterly income statements through `get_income_stmt(freq="quarterly")` | Reported quarters, TSLA/GME, USD converted to millions |
| Optional historical reference | IBM-hosted archived `revenue.htm` and `stock.html`; URLs in `data.py` | Historical snapshots only, explicitly opt-in in notebook |

Quarterly statement retrieval is attempted independently for each company. An
empty or failed response stays unavailable; there is no annual/TTM substitution,
invented data, or silent fallback to an archive. Latest provider-available revenue
does not guarantee the latest company filing. Sources retain their own usage
terms; the code license does not grant financial-data redistribution rights.

## Methodology

1. Fetch daily history with explicit `auto_adjust=True`, bounded request timeout
   and an inclusive user end date (Yahoo's exclusive end is advanced one day).
2. Keep exchange-local calendar dates, remove timezones without shifting days,
   coerce numeric fields, discard invalid dates/closes, sort, and deduplicate dates.
   Missing volume remains missing; it is not set to zero.
3. Convert revenue currency strings to numbers, remove invalid/missing values,
   retain genuine zeros, validate dates and order unique quarterly observations.
4. Calculate window return as `last / first - 1`. Session change uses the final
   two **selected** observations. Both require two observations. Average volume
   excludes missing volume. Latest close retains the ticker's source currency.
5. Calculate trailing 20/50-session averages using only selected data and complete
   windows. Rebase TSLA/GME to 100 **after** an inner join on valid dates in the
   selected window. Volatility uses sample return standard deviation × √252.
6. Keep quarterly revenue independent of the price date filter. Match a prior
   reported fiscal period 350–380 days earlier, nearest 365 days, for year-over-year
   growth. This accommodates 52/53-week calendars; gaps or zero bases yield no rate.
   No revenue is interpolated or resampled to daily observations.
7. Preserve the archived extraction as a separate adapter that validates semantic
   table headings and two-column structure instead of relying on HTML table indices.

## Analytical Highlights

The notebook computes endpoint returns, peak observed trading-volume dates,
revenue coverage and growth, and normalized comparison endpoints from each run.
Interpretations appear next to the charts. No fixed market return or revenue
growth is claimed in this README: findings depend on the selected window and the
retrieved data vintage. Share-price levels alone do not measure business scale;
revenue growth alone does not establish profitability or valuation.

## Installation

From a terminal with Python 3.11 or later:

```bash
git clone <repository-url>
cd <repository-folder>
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Or on macOS/Linux:

```bash
source .venv/bin/activate
```

Then install from the repository root:

```bash
pip install -r requirements.txt
```

No API key is required. Yahoo and optional archive access require an internet
connection. For a read-only user profile, optionally set `STOCKSCOPE_CACHE_DIR`
to a writable directory for yfinance's cache. Do not commit cookies or secrets.

## Running the Dashboard

```bash
streamlit run app.py
```

Open the local URL Streamlit prints (normally `http://localhost:8501`). Select
TSLA or GME, choose a price window, then open the revenue and comparison tabs.
Custom ticker revenue is intentionally unsupported. **Refresh data** clears both
application caches and requests fresh provider responses; it cannot force Yahoo
to update its upstream records. Delayed data is never described as real-time.

If `python` and `streamlit` point to different Python installations, launch with
the project interpreter explicitly (Windows PowerShell):

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The entry point also resolves `src/` relative to `app.py`, so local package
discovery does not depend on an editable install in the Streamlit CLI's environment.
Third-party dependencies must still be installed in the interpreter running the app.

## Running the Notebook

Register the installed environment and start Jupyter:

```bash
python -m ipykernel install --user --name stockscope --display-name "Python (StockScope)"
jupyter lab notebooks/01_stock_revenue_analysis.ipynb
```

Select **Python (StockScope)** and run all cells. Set `START`/`END` in the setup
cell to change the research window. `USE_HISTORICAL_REFERENCE = True` enables
separately labeled archived extraction examples; the default is `False`.

To execute a copy from the root without changing the source notebook:

```bash
jupyter nbconvert --to notebook --execute notebooks/01_stock_revenue_analysis.ipynb --ExecutePreprocessor.kernel_name=stockscope --output-dir output --output 01_stock_revenue_analysis.executed.ipynb
```

The committed notebook keeps outputs clear for a clean rerun. Missing providers
produce explicit messages and no fabricated conclusions. `scripts/build_notebook.py`
can regenerate the notebook after narrative changes; it overwrites that notebook.

## Testing and Validation

```bash
python -m pytest -q
python -m ruff check app.py src tests scripts
python -m compileall -q app.py src tests scripts
```

Tests use small synthetic data and mocked providers, never live requests. They
cover cleaning, missing values, date handling, returns, moving averages,
normalization, fiscal-period growth matching, HTTP validation, figure contents,
and Streamlit selection/refresh/missing-data flows. See
[the validation record](docs/validation.md) for commands actually run and their
outcomes, including network restrictions. A passing mock test is not a successful
live Yahoo integration check.

A GitHub Actions workflow runs the deterministic suite and Ruff on Python 3.11
and 3.13 after a push or pull request. That remote workflow has not been run locally.

## Limitations

- yfinance is an unofficial client; Yahoo coverage, schema and availability can change.
- Yahoo may delay/revise prices and limit quarterly history. Responses can be empty.
- The fiscal matching window is a date heuristic, not a filing-backed fiscal identifier.
- Period ends precede information release; plotting them against prices is not an
  event study and must not be interpreted as a causal or predictive relationship.
- Adjusted series can change after corporate actions; exact reruns require saved
  data vintages, which are not bundled here. Dependency ranges are not a lockfile.
- Trading windows with fewer than two observations have no return. Volatility
  needs at least two returns and assumes 252 sessions; missing shared sessions
  can create multi-session intervals. Return comparisons exclude currency conversion.
- Local validation had blocked outbound network access; financial conclusions
  and successful live statement retrieval could not be verified there.

## Future Improvements

Validate statements against company/SEC filings, track fiscal identifiers and
earnings-release timestamps, add permitted data-vintage snapshots, pin a tested
deployment environment, and extend business context with profitability measures.
No machine learning, forecasting, sentiment analysis or trading recommendations
are included in this version.

## Acknowledgments

This project originated from an **IBM Python for Data Science learning assignment**
on stock and revenue extraction. It was independently rewritten and extended
with a modular pipeline, research narrative, Streamlit dashboard and automated
tests. IBM's instructional material and course assets are not reproduced. Thanks
to the maintainers of the open-source libraries used here.

Newly authored code and documentation are available under the [MIT License](LICENSE).
