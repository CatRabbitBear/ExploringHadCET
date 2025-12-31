from dash import Input, Output
import plotly.graph_objs as go
import pandas as pd

from data.cet_surface import get_cet_loess_surface_grid


def make_anomaly_to_rgb(clim_range: float = 3.0):
    """
    anom (°C) -> (r, g, b) with a gentle diverging scheme:
    neutral around 0, soft blue for cool, soft red/orange for warm.
    """
    neutral = (210, 210, 210)
    cool    = (120, 160, 210)   # soft blue
    warm    = (220, 150, 130)   # soft red/orange

    def interp(c_from, c_to, t: float):
        return tuple(int(c_from[i] + t * (c_to[i] - c_from[i])) for i in range(3))

    def anomaly_to_rgb(anom: float):
        if pd.isna(anom):
            return neutral

        a = max(-clim_range, min(clim_range, anom))

        if abs(a) < 0.1:
            return neutral
        elif a < 0:
            t = abs(a) / clim_range
            return interp(neutral, cool, t)
        else:
            t = a / clim_range
            return interp(neutral, warm, t)

    return anomaly_to_rgb


def make_year_to_alpha(df_cet: pd.DataFrame, alpha_min: float = 0.15, alpha_max: float = 0.95):
    """
    Map year -> alpha between alpha_min (earliest) and alpha_max (latest).
    Used mainly for 2D; 3D will clamp to avoid washed-out lines.
    """
    min_year = int(df_cet["year"].min())
    max_year = int(df_cet["year"].max())

    def year_to_alpha(year: int) -> float:
        if max_year == min_year:
            return alpha_max
        t = (year - min_year) / (max_year - min_year)
        return alpha_min + t * (alpha_max - alpha_min)

    return year_to_alpha


def register_callbacks(app, df_cet: pd.DataFrame):
    anomaly_to_rgb = make_anomaly_to_rgb()
    year_to_alpha = make_year_to_alpha(df_cet)

    # Global temp range for consistent 2D/3D scaling
    t_min = float(df_cet["t_mean"].min())
    t_max = float(df_cet["t_mean"].max())
    y_range = [t_min - 0.5, t_max + 0.5]

    # ---------------- 2D JAN–DEC LINES ----------------

    @app.callback(
        Output("cet-jan-dec-lines", "figure"),
        Input("cet-year-select", "value"),
    )
    def update_cet_lines(selected_years):
        if not selected_years:
            selected_years = [int(df_cet["year"].max())]

        dff = df_cet[df_cet["year"].isin(selected_years)].copy()

        monthly = (
            dff.groupby(["year", "month", "month_name"], sort=True)[["t_mean", "t_anom"]]
            .mean()
            .reset_index()
        )

        fig = go.Figure()

        for year, group in monthly.groupby("year"):
            year = int(year)
            group = group.sort_values("month")

            ref_anom = float(group["t_anom"].mean())
            r, g, b = anomaly_to_rgb(ref_anom)
            alpha = year_to_alpha(year)  # 2D alpha can go fairly low
            color = f"rgba({r},{g},{b},{alpha})"

            fig.add_trace(
                go.Scatter(
                    x=group["month_name"],
                    y=group["t_mean"],
                    mode="lines",  # lines only, no markers
                    name=str(year),
                    line=dict(color=color, width=1.5),
                )
            )

        fig.update_layout(
            xaxis=dict(
                title="Month",
                showgrid=False,
                zeroline=False,
                tickangle=0,
            ),
            yaxis=dict(
                title="Mean Temp (°C)",
                range=y_range,
                showgrid=True,
                gridcolor="rgba(0,0,0,0.08)",
                zeroline=False,
            ),
            legend_title="Year",
            hovermode="x unified",
            margin=dict(l=40, r=10, t=60, b=40),
            plot_bgcolor="#f8f9fb",
            paper_bgcolor="#ffffff",
        )

        # soften legend a bit
        fig.update_layout(
            legend=dict(
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="rgba(0,0,0,0.1)",
                borderwidth=1,
            )
        )

        return fig

    # ---------------- 3D VIEW: LINES BY YEAR + LOESS SURFACE ----------------

    @app.callback(
        Output("cet-3d-lines", "figure"),
        Input("cet-year-select", "value"),
    )
    def update_cet_3d_lines(selected_years):
        if not selected_years:
            selected_years = [int(df_cet["year"].max())]

        dff = df_cet[df_cet["year"].isin(selected_years)].copy()

        monthly = (
            dff.groupby(["year", "month", "month_name"], sort=True)[["t_mean", "t_anom"]]
            .mean()
            .reset_index()
        )

        fig3d = go.Figure()

        month_vals = list(range(1, 13))
        month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        # Lines by year (no markers)
        for year, group in monthly.groupby("year"):
            year = int(year)
            group = group.sort_values("month")

            ref_anom = float(group["t_anom"].mean())
            r, g, b = anomaly_to_rgb(ref_anom)

            # in 3D, don't let alpha get too low or it goes weirdly white
            alpha_2d = year_to_alpha(year)
            alpha_3d = max(0.7, alpha_2d)
            color_3d = f"rgba({r},{g},{b},{alpha_3d})"

            fig3d.add_trace(
                go.Scatter3d(
                    x=group["month"],          # month on x
                    y=[year] * len(group),     # year on y
                    z=group["t_mean"],         # temp on z
                    mode="lines",
                    name=str(year),
                    line=dict(color=color_3d, width=3),
                )
            )

        # LOESS surface using the data-layer helper
        months_grid, years_grid, Z_grid = get_cet_loess_surface_grid(
            selected_years=list(sorted(dff["year"].unique())),
            frac=0.25,
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

        fig3d.update_layout(
            scene=dict(
                xaxis=dict(
                    title="Month",
                    tickmode="array",
                    tickvals=month_vals,
                    ticktext=month_labels,
                    showgrid=False,
                    showbackground=False,
                    zeroline=False,
                ),
                yaxis=dict(
                    title="Year",
                    showgrid=False,
                    showbackground=False,
                    zeroline=False,
                ),
                zaxis=dict(
                    title="Mean Temp (°C)",
                    range=y_range,
                    showgrid=True,
                    gridcolor="rgba(0,0,0,0.12)",
                    zeroline=False,
                ),
            ),
            margin=dict(l=0, r=0, t=40, b=0),
            legend_title="Series",
            paper_bgcolor="#ffffff",
        )

        fig3d.update_layout(
            scene_camera=dict(
                eye=dict(x=1.6, y=1.2, z=1.1),
            )
        )

        return fig3d