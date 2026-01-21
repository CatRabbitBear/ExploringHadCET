from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objs as go

from app_core.plotly_theme import CLIMATE_TEMPLATE, colorbar_standard


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


def _robust_range(
    z: np.ndarray, *, q_lo: float = 0.02, q_hi: float = 0.98
) -> tuple[float, float]:
    """Quantile-based zmin/zmax to stop a few extreme months blowing out the scale."""
    flat = z[np.isfinite(z)]
    if flat.size == 0:
        return 0.0, 1.0
    lo = float(np.quantile(flat, q_lo))
    hi = float(np.quantile(flat, q_hi))
    if lo == hi:
        hi = lo + 1.0
    return lo, hi


def build_rainfall_heatmap_figure(
    df_cet: pd.DataFrame,
    *,
    value_col: str = "prcp_anom_1881_1910_mm",
    title: str | None = None,
    # If anomalies, you probably want symmetric bounds and a diverging palette.
    assume_anomaly: bool = False,
    symmetric_anomaly_bounds: bool = True,
) -> go.Figure:
    """
    Rainfall heatmap (month vs year).
    Pass value_col to switch between:
      - prcp_mm
      - prcp_base_1961_1990_mm
      - prcp_anom_1961_1990_mm
      - prcp_anom_1881_1910_mm
      etc.
    """
    if df_cet is None or df_cet.empty:
        return go.Figure()

    if value_col not in df_cet.columns:
        return go.Figure()

    dff = df_cet[["year", "month", value_col]].copy()
    dff["year"] = dff["year"].astype(int)
    dff["month"] = dff["month"].astype(int)

    years_grid = sorted(dff["year"].unique().tolist())
    months_grid = list(range(1, 13))

    Z = (
        dff.pivot(index="year", columns="month", values=value_col)
        .reindex(index=years_grid, columns=months_grid)
        .to_numpy()
    )

    fig = go.Figure()

    # Choose scale
    if assume_anomaly:
        # Diverging anomalies, usually centred on 0
        # Use robust bounds unless you want full range.
        lo, hi = _robust_range(Z, q_lo=0.02, q_hi=0.98)
        if symmetric_anomaly_bounds:
            m = max(abs(lo), abs(hi))
            zmin, zmax = -m, m
        else:
            zmin, zmax = lo, hi

        colorscale = "RdBu"  # built-in diverging; fine for rainfall anomalies
        cbar_title = f"{value_col} (mm)"
    else:
        # Sequential for raw/base values
        zmin, zmax = _robust_range(Z, q_lo=0.02, q_hi=0.98)
        colorscale = "Viridis"
        cbar_title = f"{value_col} (mm)"

    fig.add_trace(
        go.Heatmap(
            x=months_grid,
            y=years_grid,
            z=Z,
            zmin=zmin,
            zmax=zmax,
            colorscale=colorscale,
            colorbar=colorbar_standard(cbar_title),
            # hovertemplate=(
            #     "Month: %{x}<br>"
            #     "Year: %{y}<br>"
            #     f"{value_col}: %{z:.1f} mm"
            #     "<extra></extra>"
            # ),
            name="Rainfall heatmap",
        )
    )

    fig.update_layout(template=CLIMATE_TEMPLATE)
    fig.update_layout(
        title=dict(text=title or "", x=0.0, xanchor="left") if title else None,
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
            showgrid=False,
            zeroline=False,
        ),
    )

    return fig
