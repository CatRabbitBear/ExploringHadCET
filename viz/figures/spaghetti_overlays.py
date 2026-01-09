from __future__ import annotations

import pandas as pd
import plotly.graph_objs as go


def add_compare_year(fig: go.Figure, dff: pd.DataFrame, year: int) -> go.Figure:
    g = dff[dff["year"] == year].sort_values("cycle_order")
    if g.empty:
        return fig

    fig.add_trace(
        go.Scatter(
            x=g["cycle_label"],
            y=g["tmean_c"],
            mode="lines",
            name=str(year),
            line=dict(color="rgba(60,60,60,0.85)", width=2, dash="dot"),
            hovertemplate=(
                f"<b>{year}</b><br>"
                "Month: %{x}<br>"
                "Temp: %{y:.2f} °C"
                "<extra></extra>"
            ),
        )
    )
    return fig


def add_highlight_year(fig: go.Figure, dff: pd.DataFrame, year: int) -> go.Figure:
    g = dff[dff["year"] == year].sort_values("cycle_order")
    if g.empty:
        return fig

    fig.add_trace(
        go.Scatter(
            x=g["cycle_label"],
            y=g["tmean_c"],
            mode="lines",
            name=str(year),
            line=dict(color="rgba(20,20,20,1.0)", width=3.6),
            hovertemplate=(
                f"<b>{year}</b><br>"
                "Month: %{x}<br>"
                "Temp: %{y:.2f} °C"
                "<extra></extra>"
            ),
        )
    )
    return fig