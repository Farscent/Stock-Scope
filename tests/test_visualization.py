import pandas as pd

from stockscope.analytics import moving_averages
from stockscope.visualization import comparison_chart, price_chart, revenue_chart, volume_chart


def test_plotly_series_and_labels():
    frame = pd.DataFrame({"Date": pd.date_range("2024-01-01", periods=60),
                         "Close": range(10, 70), "Volume": [100] * 60})
    figure = price_chart(moving_averages(frame), "TSLA", "USD")
    assert [trace.name for trace in figure.data] == ["TSLA", "MA20", "MA50"]
    assert figure.data[1].y[-1] == 59.5
    assert "USD" in figure.layout.yaxis.title.text
    assert list(volume_chart(frame, "TSLA").data[0].y) == [100] * 60
    revenue = frame.rename(columns={"Close": "Revenue"})
    assert revenue_chart(revenue, "TSLA").data[0].type == "bar"
    comparison = frame.rename(columns={"Close": "TSLA", "Volume": "GME"})
    assert len(comparison_chart(comparison).data) == 2
    assert len(price_chart(pd.DataFrame(), "TSLA").data) == 0
