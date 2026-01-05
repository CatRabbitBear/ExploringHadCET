import pandas as pd
import plotly.graph_objs as go

from data import get_loess_surface_grid
from app_core.plot_theme import CLIMATE_TEMPLATE, layout_cet_3d
from viz.utils import make_anomaly_to_rgb


ANOM_COL = "tmean_anom_1961_1990_c"


def build_cet_3d_figure(df_cet: pd.DataFrame, selected_years: list[int] | None) -> go.Figure:
    if not selected_years:
        selected_years = [int(df_cet["year"].max())]

    anomaly_to_rgb = make_anomaly_to_rgb()

    t_min = float(df_cet["tmean_c"].min())
    t_max = float(df_cet["tmean_c"].max())
    y_range = [t_min - 0.5, t_max + 0.5]

    dff = df_cet[df_cet["year"].isin(selected_years)].copy()

    monthly = (
        dff.groupby(["year", "month", "month_name"], sort=True)[["tmean_c", ANOM_COL]]
        .mean()
        .reset_index()
    )

    fig3d = go.Figure()

    month_vals = list(range(1, 13))
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # (Optional) year lines
    for year, group in monthly.groupby("year"):
        year = int(year)
        group = group.sort_values("month")

        ref_anom = float(group[ANOM_COL].mean())
        r, g, b = anomaly_to_rgb(ref_anom)

        alpha = 0.95
        color_3d = f"rgba({r},{g},{b},{alpha})"

        fig3d.add_trace(
            go.Scatter3d(
                x=group["month"],
                y=[year] * len(group),
                z=group["tmean_c"],
                mode="lines",
                name=str(year),
                line=dict(color=color_3d, width=3),
            )
        )

    months_grid, years_grid, Z_grid = get_loess_surface_grid(
        years=list(sorted(dff["year"].unique())),
        # default value_col already "tmean_loess_0p25_c"
    )

    if Z_grid.size > 0:
        fig3d.add_trace(
            go.Surface(
                x=months_grid,
                y=years_grid,
                z=Z_grid,
                opacity=0.45,
                colorscale=[[0, "#f2f2f2"], [1, "#a8a8a8"]],
                showscale=False,
                name="LOESS surface",
            )
        )

    fig3d.update_layout(template=CLIMATE_TEMPLATE)
    fig3d.update_layout(**layout_cet_3d(y_range, month_vals, month_labels))

    return fig3d