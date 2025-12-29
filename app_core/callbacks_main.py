from dash import Input, Output
import plotly.graph_objs as go
import pandas as pd


def make_year_to_color(df_cet: pd.DataFrame):
    """
    Map year -> RGBA colour using:
      - 3-stop gradient for RGB (early -> mid -> recent)
      - alpha increasing with recency (early faint, recent strong)
    """
    min_year = int(df_cet["year"].min())
    max_year = int(df_cet["year"].max())

    c0 = (220, 220, 220)   # early (light grey)
    c1 = (140, 180, 160)   # mid (muted green/teal)
    c2 = ( 20, 120,  60)   # recent (deeper green)

    alpha_min = 0.10
    alpha_max = 0.90

    def interp(a, b, t):
        return tuple(int(a[i] + t * (b[i] - a[i])) for i in range(3))

    def year_to_color(year: int) -> str:
        if max_year == min_year:
            r, g, b = c2
            alpha = alpha_max
            return f"rgba({r},{g},{b},{alpha})"

        t = (year - min_year) / (max_year - min_year)

        # RGB: 3-stop gradient
        if t <= 0.5:
            t2 = t / 0.5
            r, g, b = interp(c0, c1, t2)
        else:
            t2 = (t - 0.5) / 0.5
            r, g, b = interp(c1, c2, t2)

        # Alpha: linear with time
        alpha = alpha_min + t * (alpha_max - alpha_min)

        return f"rgba({r},{g},{b},{alpha})"

    return year_to_color


def register_callbacks(app, df_cet: pd.DataFrame):
    year_to_color = make_year_to_color(df_cet)

    @app.callback(
        Output("cet-jan-dec-lines", "figure"),
        Input("cet-year-select", "value"),
    )
    def update_cet_lines(selected_years):
        if not selected_years:
            selected_years = [int(df_cet["year"].max())]

        dff = df_cet[df_cet["year"].isin(selected_years)].copy()

        monthly = (
            dff.groupby(["year", "month", "month_name"], sort=True)["t_mean"]
            .mean()
            .reset_index()
        )

        fig = go.Figure()

        for year, group in monthly.groupby("year"):
            group = group.sort_values("month")
            color = year_to_color(int(year))

            fig.add_trace(
                go.Scatter(
                    x=group["month_name"],
                    y=group["t_mean"],
                    mode="lines+markers",
                    name=str(int(year)),
                    line=dict(color=color),
                    marker=dict(color=color, size=4),
                )
            )

        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Mean Temp (°C)",
            legend_title="Year",
            hovermode="x unified",
            margin=dict(l=40, r=10, t=60, b=40),
        )

        return fig

    @app.callback(
        Output("cet-3d-lines", "figure"),
        Input("cet-year-select", "value"),
    )
    def update_cet_3d_lines(selected_years):
        if not selected_years:
            selected_years = [int(df_cet["year"].max())]

        dff = df_cet[df_cet["year"].isin(selected_years)].copy()

        monthly = (
            dff.groupby(["year", "month", "month_name"], sort=True)["t_mean"]
            .mean()
            .reset_index()
        )

        fig3d = go.Figure()

        month_vals = list(range(1, 13))
        month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        for year, group in monthly.groupby("year"):
            group = group.sort_values("month")
            color = year_to_color(int(year))

            fig3d.add_trace(
                go.Scatter3d(
                    x=group["month"],  # month → x
                    y=[year] * len(group),  # year  → y
                    z=group["t_mean"],  # temp  → z (up)
                    mode="lines",
                    name=str(int(year)),
                    line=dict(color=color, width=4),
                )
            )

        fig3d.update_layout(
            scene=dict(
                xaxis=dict(
                    title="Month",
                    tickmode="array",
                    tickvals=month_vals,
                    ticktext=month_labels,
                ),
                yaxis=dict(
                    title="Year",
                ),
                zaxis=dict(
                    title="Mean Temp (°C)",
                ),
            ),
            margin=dict(l=0, r=0, t=40, b=0),
            legend_title="Year",
        )

        # Start with a camera that looks along the year axis a bit,
        # so you get a sense of time running left→right & temp up.
        fig3d.update_layout(
            scene_camera=dict(
                eye=dict(x=1.6, y=1.2, z=1.1),
            )
        )

        return fig3d