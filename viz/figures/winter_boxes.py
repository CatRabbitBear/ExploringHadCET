from __future__ import annotations

import pandas as pd
import plotly.graph_objs as go

from app_core.plot_theme import CLIMATE_TEMPLATE, layout_cet_2d


DJF_MONTHS = {12, 1, 2}


def _bucket_label(year: int, mode: str) -> str:
    if mode == "century":
        start = (year // 100) * 100
        return f"{start}s"
    if mode == "50y":
        start = (year // 50) * 50
        return f"{start}–{start+49}"
    if mode == "25y":
        start = (year // 25) * 25
        return f"{start}–{start+24}"
    # fallback
    start = (year // 100) * 100
    return f"{start}s"


def _bucket_sort_key(label: str) -> int:
    # Extract the first number for ordering
    # "1700s" -> 1700, "1850–1899" -> 1850
    digits = ""
    for ch in label:
        if ch.isdigit():
            digits += ch
        elif digits:
            break
    return int(digits) if digits else 0


def build_winter_djf_boxplots(
    df_cet: pd.DataFrame,
    years_range: list[int],
    bucket_mode: str = "century",
) -> go.Figure:
    if not years_range:
        return go.Figure()

    dff = df_cet[df_cet["year"].isin(years_range)][["year", "month", "tmean_c"]].copy()
    if dff.empty:
        return go.Figure()

    # Filter DJF only
    dff = dff[dff["month"].isin(DJF_MONTHS)].copy()
    if dff.empty:
        return go.Figure()

    # Bucket per calendar year (good enough for now; we'll refine later if we want "winter-year" handling)
    dff["bucket"] = dff["year"].astype(int).map(lambda y: _bucket_label(y, bucket_mode))

    # Order buckets chronologically
    buckets = sorted(dff["bucket"].unique().tolist(), key=_bucket_sort_key)

    # Consistent y-range with your CET layout
    t_min = float(df_cet["tmean_c"].min())
    t_max = float(df_cet["tmean_c"].max())
    y_range = [t_min - 0.5, t_max + 0.5]

    fig = go.Figure()

    # One box trace per bucket (categorical x)
    for b in buckets:
        vals = dff.loc[dff["bucket"] == b, "tmean_c"]
        if vals.empty:
            continue

        fig.add_trace(
            go.Box(
                y=vals,
                x=[b] * len(vals),   # categorical
                name=b,
                boxpoints=False,     # keep clean; later we can add points toggle
                whiskerwidth=0.7,
                line=dict(width=1.4),
                showlegend=False,
                hovertemplate=(
                    f"<b>{b}</b><br>"
                    "DJF Temp: %{y:.2f} °C"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(template=CLIMATE_TEMPLATE)
    fig.update_layout(**layout_cet_2d(y_range))

    fig.update_layout(
        margin=dict(l=40, r=10, t=40, b=55),
        xaxis=dict(
            type="category",
            categoryorder="array",
            categoryarray=buckets,
            title="Era bucket",
        ),
        yaxis=dict(
            title="Mean temperature (°C)",
        ),
    )

    return fig