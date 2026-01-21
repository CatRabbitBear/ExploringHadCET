from __future__ import annotations

import pandas as pd
import plotly.graph_objs as go

from app_core.plotly_theme import CLIMATE_TEMPLATE, colorbar_standard, contour_line_color
from app_core.tokens_colors import CLIMATE


MONTH_LABELS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def build_cet_loess_topdown_figure(
    df_cet: pd.DataFrame,
    *,
    loess_col: str = "tmean_loess_0p07_c",
    baseline_col: str = "tmean_base_1961_1990_c",
    # If you pass an explicit anomaly column that already exists, we’ll use it.
    # Otherwise we compute it as loess - baseline.
    anomaly_col: str | None = None,
    show_contours: bool = True,
    contour_line_alpha: float = 0.25,
) -> go.Figure:
    """
    2D top-down view of the LOESS surface:
      - Heatmap colors represent LOESS anomaly vs month-specific baseline
      - Optional contour lines represent the LOESS absolute temperature

    Axes:
      x = month (1..12)
      y = year
    """
    if df_cet is None or df_cet.empty:
        return go.Figure()

    if loess_col not in df_cet.columns or baseline_col not in df_cet.columns:
        return go.Figure()

    dff = df_cet[["year", "month", loess_col, baseline_col]].copy()
    dff["year"] = dff["year"].astype(int)
    dff["month"] = dff["month"].astype(int)

    if anomaly_col and anomaly_col in df_cet.columns:
        dff = df_cet[["year", "month", loess_col, anomaly_col]].copy()
        dff["year"] = dff["year"].astype(int)
        dff["month"] = dff["month"].astype(int)
        dff["_anom"] = dff[anomaly_col]
    else:
        dff["_anom"] = dff[loess_col] - dff[baseline_col]

    years_grid = sorted(dff["year"].unique().tolist())
    months_grid = list(range(1, 13))

    # Build grids
    Z_loess = (
        dff.pivot(index="year", columns="month", values=loess_col)
        .reindex(index=years_grid, columns=months_grid)
        .to_numpy()
    )

    Z_anom = (
        dff.pivot(index="year", columns="month", values="_anom")
        .reindex(index=years_grid, columns=months_grid)
        .to_numpy()
    )

    fig = go.Figure()

    # Heatmap: anomaly coloring (same diverging palette as your surfacecolor)
    fig.add_trace(
        go.Heatmap(
            x=months_grid,
            y=years_grid,
            z=Z_anom,
            zmin=CLIMATE.anomaly_cmin(),
            zmax=CLIMATE.anomaly_cmax(),
            colorscale=CLIMATE.anomaly_colorscale,
            colorbar=colorbar_standard("LOESS anomaly (°C)"),
            hovertemplate=(
                "Month: %{x}<br>"
                "Year: %{y}<br>"
                "LOESS anomaly: %{z:.2f} °C"
                "<extra></extra>"
            ),
            name="LOESS anomaly",
        )
    )

    if show_contours:
        # Contours: absolute LOESS temperature (thin dark lines)
        # Use a Contour trace with no fill and no colorbar.
        fig.add_trace(
            go.Contour(
                x=months_grid,
                y=years_grid,
                z=Z_loess,
                contours=dict(
                    coloring="none",
                    showlabels=False,
                ),
                line=dict(
                    color=contour_line_color(contour_line_alpha),
                    width=1,
                ),
                showscale=False,
                hoverinfo="skip",
                name="LOESS contours",
            )
        )

    # Layout + axes
    fig.update_layout(template=CLIMATE_TEMPLATE)
    fig.update_layout(
        margin=dict(l=50, r=20, t=20, b=40),
        xaxis=dict(
            title="Month",
            tickmode="array",
            tickvals=months_grid,
            ticktext=MONTH_LABELS,
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(
            title="Year",
            autorange=False,
            range=[min(years_grid), max(years_grid)],
            showgrid=False,
            zeroline=False,
        ),
    )

    return fig
