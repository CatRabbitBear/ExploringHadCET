from __future__ import annotations

import pandas as pd
import plotly.graph_objs as go

from app_core.plotly_theme import CLIMATE_TEMPLATE, layout_cet_2d
from viz.utils import make_year_to_alpha


def build_spaghetti_base(
    df_cet: pd.DataFrame,
    dff: pd.DataFrame,
    x_labels: list[str],
    *,
    group_col: str = "year",
) -> go.Figure:
    """
    Draw faint year lines as background texture. No overlays/highlights.
    group_col is typically 'year' for overview, but later could be 'cycle_year'.
    """
    if dff.empty:
        return go.Figure()

    # y-range matches your existing behaviour
    t_min = float(df_cet["tmean_c"].min())
    t_max = float(df_cet["tmean_c"].max())
    y_range = [t_min - 0.5, t_max + 0.5]

    year_to_alpha = make_year_to_alpha(df_cet, alpha_min=0.03, alpha_max=0.16)

    fig = go.Figure()

    bg_rgb = (140, 140, 140)
    bg_width = 1.0
    r, gg, b = bg_rgb

    # IMPORTANT: sort by cycle_order, not month, to support Jul->Jun etc.
    for y, g in dff.groupby(group_col):
        g = g.sort_values("cycle_order")
        # if group_col isn't 'year', just use a constant alpha or map by actual year column
        if group_col == "year":
            a = year_to_alpha(int(y))
        else:
            # Map alpha by the *ending year* if present, otherwise a fallback
            try:
                a = year_to_alpha(int(y))
            except Exception:
                a = 0.08

        fig.add_trace(
            go.Scatter(
                x=g["cycle_label"],
                y=g["tmean_c"],
                mode="lines",
                line=dict(color=f"rgba({r},{gg},{b},{a})", width=bg_width),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    fig.update_layout(template=CLIMATE_TEMPLATE)
    fig.update_layout(**layout_cet_2d(y_range))

    # Force categorical order so Plotly doesn't reorder labels
    fig.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=x_labels,
    )

    # Your readability nudges (kept)
    fig.update_layout(
        margin=dict(l=40, r=10, t=40, b=35),
        legend=dict(
            title=dict(text="Highlighted"),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="rgba(0,0,0,0.12)",
            borderwidth=1,
        ),
    )

    return fig
