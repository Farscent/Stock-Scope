# Validation record

Local checks performed on 2026-11-23, Windows, Python 3.13.3.

## Environment

Created `.venv` with `--system-site-packages` to reuse available packages.
Installed versions used included pandas 2.2.3, Streamlit 1.45.1, Plotly 6.6.0,
yfinance 1.2.0 and pytest 9.1.1. This is not a claim of a clean dependency install
or of testing every allowed dependency version.

Set `STOCKSCOPE_CACHE_DIR` to the ignored workspace directory `output/yfinance`
for live checks because the default user-cache database was not writable in the
restricted environment. No cookies or generated cache files belong in Git.

## Commands and outcomes

Commands ran from the repository root; Python commands used `.venv/Scripts/python`
after creating the environment.

| Command / check | Observed outcome |
| --- | --- |
| `python -m venv --system-site-packages .venv` | Succeeded |
| `python -m pip install -e . --no-deps --no-build-isolation` | Package built and installed successfully using available dependencies |
| `python -m pip install -r requirements.txt` | Blocked fetching setuptools from the package index (WinError 10013) |
| `python -m pip install --no-build-isolation -r requirements.txt` | Build preparation succeeded; blocked fetching Ruff (same network restriction) |
| `python scripts/build_notebook.py` | Generated 22-cell research notebook |
| `python -m pytest -q` | 18 passed; deterministic, no live data required |
| `python -m compileall -q app.py src tests scripts` | Passed |
| Imports of all four functional package modules | Passed |
| `nbformat.validate` and compilation of each notebook code cell | Passed; no assignment prompt text or saved outputs in published notebook |
| `python -m nbconvert --to notebook --execute notebooks/01_stock_revenue_analysis.ipynb --output 01_stock_revenue_analysis.executed.ipynb --output-dir output --ExecutePreprocessor.timeout=120` | Completed all 10 code cells with zero cell errors; sources unavailable, so no numerical findings |
| `python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.fileWatcherType none` | Server started and printed local URL |
| HTTP GET `http://127.0.0.1:8501/_stcore/health` | `200 ok` |
| `python -m ruff check app.py src tests scripts` | Not run successfully: Ruff is absent and package installation is blocked |
| Playwright CLI browser open and snapshot | Failed fetching its package from npm with EACCES |
| Browser-control fallback | Host unavailable; no screenshot or visual breakpoint verification claimed |

The first test pass had 13 tests; the final suite has 18 after adding chart,
application and notebook integration coverage. Jupyter emitted Windows event-loop
and IPython profile permission warnings; they did not cause notebook cell failures.

## What the tests establish

- Revenue string cleaning, invalid/missing values, duplicate handling and numeric types.
- Calendar-preserving date conversion, invalid dates and missing/negative volume.
- Endpoint and session returns, unavailable one-session returns, trailing averages.
- Index normalization only after intersecting valid dates; empty/disjoint windows.
- Missing fiscal quarters do not produce a false four-row-shift year-over-year result.
- Named historical table selection, expected units and HTTP timeout/status calls.
- Yahoo adapter adjustment settings, inclusive end date, statement units and failures.
- Plotly series, moving-average values, revenue bar type and labels.
- Streamlit ticker/custom selection, refresh, metric/chart/export creation, single-session
  windows, invalid ticker and missing-price/statement states through `AppTest`.
- Every notebook code cell executes with explicitly synthetic providers, including
  seven figures and computed findings; synthetic outputs are not published as research.

## Live-data investigation and remaining checks

A direct Yahoo chart request failed with a socket permission error (WinError
10013); the TSLA statement query returned an empty frame. Notebook retrieval of
both companies' price and statement data produced explicit unavailable messages.
No successful live revenue retrieval, fresh numerical market findings or current
filing completeness is claimed. The archived reference is implemented and tested
with handcrafted HTML but was not fetched successfully in this environment.

With normal internet access, install requirements, run the notebook and inspect
TSLA/GME periods against the provider. Run Ruff and inspect the dashboard at
desktop/mobile widths before publishing a screenshot. The GitHub Actions workflow
is supplied but has not run remotely. No public deployment or repository URL exists
in this workspace.

## Final engineering and portfolio review

| Area | Review result |
| --- | --- |
| Readability | Source adapters, deterministic cleaning, analytics and figures are separate; app holds UI and caching |
| Research clarity | Eight research sections, data-derived interpretations and explicit unavailable-data conclusions |
| Methodology | Adjusted prices, fiscal dates, provenance, units, shared-date comparison and noncausal framing documented |
| Usability | Native controls, five task-oriented tabs, source dates and recovery states; visual QA remains unverified |
| Reproducibility | Relative paths, installable package, notebook kernel instructions and network-free tests; live vintages are not pinned |
| Engineering | 18 tests, offline notebook/application paths, CI definition, no extra services |
| GitHub presentation | Original README, audit, MIT license and ignore rules; original instructional notebook retained only locally |

No ML, sentiment analysis, forecasts or trading recommendations were introduced.

## Launch-path follow-up

The user's global `streamlit` command resolved to Python 3.12 while `python`
resolved to Python 3.13; the editable package had been installed only in `.venv`.
Updated `app.py` to resolve its sibling `src/` directory before importing
StockScope. Added a subprocess regression that removes the installed source path,
verifies the package is initially undiscoverable, and then runs the application
through Streamlit's AppTest with offline provider mocks. The follow-up suite
passes all 19 tests. README includes the explicit virtual-environment launch command.
