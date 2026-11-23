"""Execute every notebook code cell against explicit synthetic provider fixtures."""

from pathlib import Path

import nbformat
import pandas as pd
import plotly.graph_objects as go

from stockscope.data import DataResult
from stockscope.preprocessing import clean_prices


def test_notebook_successful_analytical_path(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    notebook = nbformat.read(root / "notebooks/01_stock_revenue_analysis.ipynb", as_version=4)
    nbformat.validate(notebook)
    displayed = []

    def prices(ticker, start, end):
        frame = pd.DataFrame({"Date": pd.bdate_range(start, periods=65),
                              "Close": range(100, 165), "Volume": range(1000, 1065)})
        return DataResult(clean_prices(frame), "SYNTHETIC TEST ONLY", "2024-01-01T00:00:00Z")

    def revenue(ticker):
        frame = pd.DataFrame({"Date": pd.date_range("2023-03-31", periods=8, freq="QE"),
                              "Revenue": [float(i) for i in range(100, 108)]})
        return DataResult(frame, "SYNTHETIC TEST ONLY", "2024-01-01T00:00:00Z")

    monkeypatch.setattr("stockscope.data.fetch_prices", prices)
    monkeypatch.setattr("stockscope.data.fetch_revenue", revenue)
    monkeypatch.setattr("IPython.display.display", lambda value: displayed.append(value))
    monkeypatch.chdir(root / "notebooks")
    namespace = {}
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            exec(compile(cell.source, f"notebook-cell-{index}", "exec"), namespace)
    assert not namespace["failures"]
    assert len(namespace["comparison"]) == 65
    assert len(namespace["growth_tables"]) == 2
    assert len([item for item in displayed if isinstance(item, go.Figure)]) == 7
    assert len(namespace["findings"]) == 4
