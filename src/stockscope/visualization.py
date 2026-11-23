"""Plotly charts without Streamlit state or data fetching."""

import pandas as pd
import plotly.graph_objects as go

COLORS = {"TSLA": "#12685F", "GME": "#B2532E"}


def _base(title: str, y_label: str) -> go.Figure:
    figure = go.Figure()
    figure.update_layout(
        title=title, template="plotly_white", height=390,
        margin=dict(l=20, r=20, t=55, b=35),
        paper_bgcolor="#FAFBF8", plot_bgcolor="#FAFBF8",
        font=dict(family="Arial, sans-serif", color="#172D32", size=13),
        xaxis_title="Date", yaxis_title=y_label, hovermode="x unified",
        legend=dict(orientation="h", y=1.12, title=None),
    )
    figure.update_xaxes(showgrid=False)
    figure.update_yaxes(gridcolor="#E1E8E3", zeroline=False)
    return figure


def price_chart(frame: pd.DataFrame, ticker: str, currency: str = "USD") -> go.Figure:
    """Plot adjusted closes and any precomputed trailing moving averages."""
    figure = _base(f"{ticker} · Adjusted closing price", f"Adjusted close ({currency})")
    if frame.empty:
        return figure
    figure.add_trace(go.Scatter(x=frame["Date"], y=frame["Close"], name=ticker,
                                line=dict(color=COLORS.get(ticker, "#12685F"), width=2)))
    for column, color in (("MA20", "#AE7941"), ("MA50", "#6673A4")):
        if column in frame:
            figure.add_trace(go.Scatter(x=frame["Date"], y=frame[column], name=column,
                                        line=dict(color=color, width=1.5, dash="dot")))
    return figure


def volume_chart(frame: pd.DataFrame, ticker: str) -> go.Figure:
    """Show observed daily share volume; missing volume is not replaced with zero."""
    figure = _base(f"{ticker} · Trading volume", "Shares")
    figure.update_layout(height=260)
    if not frame.empty:
        figure.add_bar(x=frame["Date"], y=frame["Volume"], name="Volume", marker_color="#789B91")
    return figure


def revenue_chart(frame: pd.DataFrame, ticker: str) -> go.Figure:
    """Keep each reported fiscal period separate, without daily interpolation."""
    figure = _base(f"{ticker} · Reported quarterly revenue", "Revenue (USD millions)")
    if not frame.empty:
        figure.add_bar(x=frame["Date"], y=frame["Revenue"], name="Revenue",
                       marker_color=COLORS.get(ticker, "#12685F"),
                       hovertemplate="Period end: %{x|%Y-%m-%d}<br>USD %{y:,.1f} million<extra></extra>")
    figure.update_xaxes(title="Fiscal period end")
    return figure


def comparison_chart(frame: pd.DataFrame) -> go.Figure:
    """Plot a pre-aligned comparison whose first shared date equals 100."""
    figure = _base("TSLA versus GME · Common-date performance", "Price index (start = 100)")
    if not frame.empty:
        for ticker in frame.columns.drop("Date"):
            figure.add_scatter(x=frame["Date"], y=frame[ticker], name=ticker,
                               mode="lines", line=dict(color=COLORS.get(ticker), width=2))
    return figure
