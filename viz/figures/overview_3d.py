import pandas as pd
import plotly.graph_objs as go

from data import get_surface_grids
from app_core.plotly_theme import CLIMATE_TEMPLATE, layout_cet_3d
from app_core.tokens_colors import CLIMATE


LOESS_COL = "tmean_loess_0p07_c"
BASELINE_COL = "tmean_base_1961_1990_c"  # month-specific baseline mean
SURF_COL = "tmean_loess_anom_1961_1990_c"  # computed on the fly below


def build_cet_3d_figure(
    df_cet: pd.DataFrame, selected_years: list[int] | None
) -> go.Figure:
    if not selected_years:
        selected_years = [int(df_cet["year"].max())]

    # For y-range, use LOESS if present; fallback to tmean_c
    if LOESS_COL in df_cet.columns:
        t_min = float(df_cet[LOESS_COL].min())
        t_max = float(df_cet[LOESS_COL].max())
    else:
        t_min = float(df_cet["tmean_c"].min())
        t_max = float(df_cet["tmean_c"].max())

    y_range = [t_min - 0.5, t_max + 0.5]

    # We’ll derive years list from selection
    years_sel = sorted(set(int(y) for y in selected_years))

    # Surface anomaly is LOESS - monthly baseline (month-specific climatology)
    # We'll compute this anomaly in-memory by temporarily loading the parquet through get_surface_grids:
    # easiest approach: ensure the parquet already has BASELINE_COL and LOESS_COL (it does).
    # To avoid adding a new parquet column right now, compute SURF_COL in a small temp df inside the helper:
    #
    # Since get_surface_grids reads parquet internally, we can't pass a computed expression.
    # So: do a quick local compute from df_cet (already passed in) and grid it ourselves? That would duplicate code.
    #
    # Better: compute SURF_COL once in df_cet before calling this figure builder (in your callback),
    # OR: (simplest) compute SURF_COL in df_cet here, then grid via pivot directly.
    #
    # We'll do the simple local compute + pivot (no extra helper changes needed).

    dff = df_cet[df_cet["year"].isin(years_sel)].copy()
    if LOESS_COL not in dff.columns or BASELINE_COL not in dff.columns:
        return go.Figure()

    dff[SURF_COL] = dff[LOESS_COL] - dff[BASELINE_COL]

    # Build grids locally
    months_grid = sorted(dff["month"].unique().astype(int).tolist())
    years_grid = sorted(dff["year"].unique().astype(int).tolist())

    Z_grid = (
        dff.pivot(index="year", columns="month", values=LOESS_COL)
        .reindex(index=years_grid, columns=months_grid)
        .to_numpy()
    )

    C_grid = (
        dff.pivot(index="year", columns="month", values=SURF_COL)
        .reindex(index=years_grid, columns=months_grid)
        .to_numpy()
    )

    fig3d = go.Figure()

    month_vals = list(range(1, 13))
    month_labels = [
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

    if Z_grid.size > 0:
        fig3d.add_trace(
            go.Surface(
                x=months_grid,
                y=years_grid,
                z=Z_grid,
                surfacecolor=C_grid,
                opacity=1.0,
                cmin=CLIMATE.anomaly_cmin(),
                cmax=CLIMATE.anomaly_cmax(),
                colorscale=CLIMATE.anomaly_colorscale,  # diverging, warm=red, cool=blue
                colorbar=dict(
                    title="Anomaly (°C)",
                    # titleside="right",
                    len=0.65,
                    thickness=14,
                ),
                contours=dict(
                    z=dict(
                        show=True,
                        usecolormap=False,
                        highlight=False,
                        color="rgba(0,0,0,0.25)",
                        project=dict(z=False),
                    )
                ),
                lighting=dict(
                    ambient=0.9,
                    diffuse=0.01,
                    roughness=0.8,
                    specular=0.00,
                    fresnel=0.00,
                ),
                lightposition=dict(x=6.5, y=1850, z=5),
                showscale=True,
                name="LOESS surface",
                hovertemplate=(
                    "Month: %{x}<br>"
                    "Year: %{y}<br>"
                    "LOESS temp: %{z:.2f} °C<br>"
                    "LOESS anomaly: %{surfacecolor:.2f} °C"
                    "<extra></extra>"
                ),
            )
        )

    fig3d.update_layout(template=CLIMATE_TEMPLATE)
    fig3d.update_layout(**layout_cet_3d(y_range, month_vals, month_labels))

    # A couple of layout nudges that usually help “pop”
    fig3d.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        scene=dict(
            camera=dict(eye=dict(x=1.6, y=1.35, z=0.9)),
            aspectratio=dict(x=1.1, y=1.8, z=0.8),
        ),
    )

    return fig3d
