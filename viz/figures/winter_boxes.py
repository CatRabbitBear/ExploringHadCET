from __future__ import annotations

import pandas as pd
import plotly.graph_objs as go

from app_core.plotly_theme import CLIMATE_TEMPLATE, layout_cet_2d
from app_core.tokens_colors import winter_bucket_color
from viz.figures.winter_stats import DJF_MONTHS, bucket_label, _bucket_sort_key


def build_winter_djf_boxplots(
    df_cet: pd.DataFrame,
    years_range: list[int],
    bucket_mode: str = "century",
    opacity: float = 1.0,
) -> go.Figure:
    if not years_range:
        return go.Figure()

    dff = df_cet[df_cet["year"].isin(years_range)][["year", "month", "tmean_c"]].copy()
    if dff.empty:
        return go.Figure()

    dff = dff[dff["month"].isin(DJF_MONTHS)].copy()
    if dff.empty:
        return go.Figure()

    last_year = max(years_range)
    dff["bucket"] = (
        dff["year"].astype(int).map(lambda y: bucket_label(y, bucket_mode, last_year))
    )

    buckets = sorted(dff["bucket"].unique().tolist(), key=_bucket_sort_key)

    # For now, keep y-range global (your later step will introduce winter-only scaling)
    t_min = float(df_cet["tmean_c"].min())
    t_max = float(df_cet["tmean_c"].max())
    y_range = [t_min - 0.5, t_max + 0.5]

    fig = go.Figure()

    for i, b in enumerate(buckets):
        vals = dff.loc[dff["bucket"] == b, "tmean_c"]
        if vals.empty:
            continue

        c_line = winter_bucket_color(i, alpha=0.95)
        c_fill = winter_bucket_color(i, alpha=0.18)

        fig.add_trace(
            go.Box(
                y=vals,
                x=[b] * len(vals),
                name=b,
                boxpoints=False,
                whiskerwidth=0.7,
                line=dict(width=1.5, color=c_line),
                fillcolor=c_fill,
                showlegend=False,
                hovertemplate=(
                    f"<b>{b}</b><br>" "DJF Temp: %{y:.2f} °C" "<extra></extra>"
                ),
                opacity=opacity,
            )
        )

    fig.update_layout(template=CLIMATE_TEMPLATE)
    fig.update_layout(**layout_cet_2d(y_range))
    fig.update_layout(
        margin=dict(l=40, r=10, t=40, b=35),
        xaxis=dict(
            type="category",
            categoryorder="array",
            categoryarray=buckets,
            title="Era bucket",
        ),
        yaxis=dict(title="Mean temperature (°C)"),
    )

    return fig
