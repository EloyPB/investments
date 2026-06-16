"""Rolling return charts: shared data prep plus matplotlib (CLI) and plotly (dashboard)."""

from __future__ import annotations

import datetime
from dataclasses import dataclass

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pandas.plotting import register_matplotlib_converters


# Match matplotlib default cycle (C0, C2, C7)
_COLOR_SALES = "#1f77b4"
_COLOR_DIVIDENDS = "#2ca02c"
_COLOR_MEAN = "#7f7f7f"
_COLOR_INVESTED = _COLOR_SALES

_PLOTLY_LAYOUT = dict(
    font=dict(size=14),
    paper_bgcolor="white",
    plot_bgcolor="white",
    hovermode="x unified",
    margin=dict(l=64, r=24, t=56, b=48),
    separators=",.",
)

_AXIS_TITLE = dict(font=dict(size=15))
_TICK_FONT = dict(size=13)
_TITLE = dict(font=dict(size=18), x=0, xanchor="left")


def _base_layout(title: str, x_title: str, y_title: str, height: int) -> dict:
    layout = {
        **_PLOTLY_LAYOUT,
        "title": {**_TITLE, "text": title},
        "height": height,
        "xaxis": {
            "title": {**_AXIS_TITLE, "text": x_title},
            "tickfont": _TICK_FONT,
            "hoverformat": "%Y-%m-%d",
        },
        "yaxis": {"title": {**_AXIS_TITLE, "text": y_title}, "tickfont": _TICK_FONT},
    }
    return layout


@dataclass
class RollingReturnsData:
    end_dates: pd.DatetimeIndex
    invested: np.ndarray
    out_rate: np.ndarray
    dividend_rate: np.ndarray

    @property
    def mean_return(self) -> float:
        return float(np.mean(self.out_rate + self.dividend_rate))


def compute_rolling_returns(transactions: pd.DataFrame, frequency: int = 7) -> RollingReturnsData:
    """Trailing 365-day windows stepped weekly (by default)."""
    today = datetime.date.today()
    days = int((today - transactions.index[0].date()).days / frequency) * frequency
    end_dates = pd.date_range(start=today - datetime.timedelta(days), end=today, freq=f"{frequency}D")
    start_dates = end_dates - datetime.timedelta(365)

    invested = []
    out_rate = []
    dividend_rate = []

    for start_date, end_date in zip(start_dates, end_dates):
        window = transactions[start_date:end_date]
        invested.append(window["invested"].iloc[-1])
        mean_invested = window["invested"].mean()
        out_rate.append(window["out"].sum() / mean_invested)
        dividend_rate.append(window["dividend"].sum() / mean_invested)

    return RollingReturnsData(
        end_dates=end_dates,
        invested=np.array(invested),
        out_rate=100 * np.array(out_rate),
        dividend_rate=100 * np.array(dividend_rate),
    )


def plot_rolling_returns_matplotlib(data: RollingReturnsData) -> plt.Figure:
    """Two-panel figure for the CLI (shared x-axis, compact)."""
    register_matplotlib_converters()

    fig, ax = plt.subplots(2, sharex="col", figsize=(7, 6), gridspec_kw={"height_ratios": (0.6, 1)})

    ax[0].plot(data.end_dates, data.invested, color=_COLOR_INVESTED, linewidth=2)
    ax[0].fmt_xdata = mdates.DateFormatter("%Y-%m-%d")
    ax[0].set_ylabel("Total deployed (EUR)")
    ax[0].set_ylim(bottom=0)

    ax[1].fill_between(
        data.end_dates,
        0,
        data.out_rate,
        label="Completed transactions",
        facecolor=_COLOR_SALES,
        edgecolor="k",
    )
    ax[1].fill_between(
        data.end_dates,
        data.out_rate,
        data.out_rate + data.dividend_rate,
        label="Dividends",
        facecolor=_COLOR_DIVIDENDS,
        edgecolor="k",
    )
    ax[1].plot(
        (data.end_dates[0], data.end_dates[-1]),
        [data.mean_return] * 2,
        linestyle="dashed",
        color=_COLOR_MEAN,
        label="mean trailing 12m return",
    )
    ax[1].fmt_xdata = mdates.DateFormatter("%Y-%m-%d")
    ax[1].set_ylabel("Trailing 12m realized return\n(% of avg deployed)")
    ax[1].legend(loc="upper left")
    fig.align_ylabels()
    fig.tight_layout()
    return fig


def plot_invested_plotly(data: RollingReturnsData) -> go.Figure:
    """Capital deployed over time — full-width interactive chart for Streamlit."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data.end_dates,
            y=data.invested,
            mode="lines",
            name="Capital deployed",
            line=dict(color=_COLOR_INVESTED, width=2),
            hovertemplate="%{y:,.0f} €<extra></extra>",
        )
    )
    fig.update_layout(**_base_layout("Total deployed", "Date", "EUR", height=380))
    fig.update_yaxes(rangemode="tozero", gridcolor="#e6e6e6")
    fig.update_xaxes(gridcolor="#e6e6e6")
    return fig


def plot_returns_plotly(data: RollingReturnsData) -> go.Figure:
    """Stacked trailing 12m realized return — full-width interactive chart for Streamlit."""
    total_rate = data.out_rate + data.dividend_rate
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data.end_dates,
            y=data.out_rate,
            mode="lines",
            name="sales",
            legendrank=3,
            fill="tozeroy",
            fillcolor=_COLOR_SALES,
            line=dict(color="black", width=1),
            hovertemplate="%{y:.2f}%<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data.end_dates,
            y=total_rate,
            mode="lines",
            name="dividends",
            legendrank=2,
            fill="tonexty",
            fillcolor=_COLOR_DIVIDENDS,
            line=dict(color="black", width=1),
            hovertemplate="%{customdata:.2f}%<extra></extra>",
            customdata=data.dividend_rate,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[data.end_dates[0], data.end_dates[-1]],
            y=[data.mean_return, data.mean_return],
            mode="lines",
            name="mean trailing 12m return",
            legendrank=1,
            line=dict(color=_COLOR_MEAN, width=2, dash="dash"),
            hovertemplate="%{y:.2f}%<extra></extra>",
        )
    )
    fig.update_layout(
        **_base_layout(
            "Trailing 12m realized return (% of avg deployed)",
            "Date",
            "%",
            height=440,
        ),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="white",
            bordercolor="#cccccc",
            borderwidth=1,
            font=dict(size=13),
        ),
    )
    fig.update_yaxes(gridcolor="#e6e6e6")
    fig.update_xaxes(gridcolor="#e6e6e6")
    return fig
