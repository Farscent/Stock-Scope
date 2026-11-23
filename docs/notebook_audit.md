# Original notebook audit

Read all 67 cells before editing (2026-11-23). The original file remains locally
at the workspace root and is explicitly excluded from Git to avoid redistributing
course instructions and branding. The replacement is independently authored.

## Inventory

| Cells (zero-based) | Purpose | Decision |
| --- | --- | --- |
| 0–4 | Branding, description, assignment navigation, local setup hint | Replace with original project context |
| 5–8 | pip commands, yfinance/pandas/requests/BeautifulSoup imports, warning suppression | Declare dependencies outside notebook; retain relevant libraries; do not suppress warnings |
| 9–12 | `make_graph`, Matplotlib price/revenue panels | Preserve separate daily/quarterly views in Plotly; remove date cutoffs |
| 13–19 | Tesla `Ticker.history(period="max")`, reset index, preview | Reuse stock retrieval purpose with explicit adjustments, timeouts and cleaning |
| 20–34 | Tesla archived HTML download, positional tbody extraction, string replacement, tail | Preserve opt-in historical methodology; semantic table validation and numeric conversion |
| 35–41 | GameStop price retrieval and index reset | Reuse common pipeline |
| 42–55 | GameStop archived HTML extraction, cleaning, previews | Reuse historical adapter; remove duplicate extraction logic |
| 56–63 | Course chart prompts/hints and two plotting calls | Replace with research charts, comparisons and computed interpretation |
| 64–66 | Course author biographies, change log and copyright | Do not redistribute; acknowledge inspiration in README |

Dependencies observed: yfinance, pandas, requests, BeautifulSoup, Matplotlib;
installation cells also requested nbformat. The graph comment records an earlier
Plotly version replaced for assignment submission. Data sources are Yahoo Finance
and IBM-hosted archived pages `revenue.htm` (Tesla) and `stock.html` (GameStop),
whose full addresses are retained in `src/stockscope/data.py`.

## Engineering and research issues

- `soup.find_all('tbody')[1]` assumes document order and does not validate company,
  quarterly frequency or units. Requests have no timeout or HTTP status check.
- Revenue cleanup removes currency punctuation and blank values but leaves
  strings, invalid dates and duplicates unvalidated. Date sorting is implicit.
- Stock adjustment relies on provider defaults; timezone handling is implicit.
  Repeated in-place index resets are not idempotent: the stored GameStop output
  includes an extra index column. Cached output is not proof of fresh execution.
- Price charts stop at 2021-06-14 and revenue at 2021-04-30, obscuring newer data.
  Archived HTML pages are snapshots, not current reporting services.
- The notebook suppresses FutureWarnings while saved outputs still contain
  deprecation warnings. Installation cells and duplicated scraping reduce reproducibility.
- There is no return normalization, volume study, numerical summary, test suite,
  provenance table, missing-data recovery or evidence-based discussion.
- Assignment headings, screenshot requests, execution prompts, help disclosures,
  decorative HTML, course navigation and course author sections span the teaching
  cells listed above. None are carried into the replacement notebook.

## Preserved analytical intent

Investigate stock-price evolution alongside business revenue for Tesla and
GameStop. Keep market and accounting frequencies distinct. Compare observed
patterns without claiming that revenue causes market moves. No forecasting,
sentiment model or investment recommendation is introduced.
