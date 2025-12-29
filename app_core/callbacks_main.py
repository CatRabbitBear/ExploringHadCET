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

def make_year_to_alpha(df_cet: pd.DataFrame, alpha_min: float = 1.0, alpha_max: float = 1.0):
    """
    Map year -> alpha between alpha_min (earliest) and alpha_max (latest).
    """
    min_year = int(df_cet["year"].min())
    max_year = int(df_cet["year"].max())

    def year_to_alpha(year: int) -> float:
        if max_year == min_year:
            return alpha_max
        t = (year - min_year) / (max_year - min_year)
        return alpha_min + t * (alpha_max - alpha_min)

    return year_to_alpha

def make_anomaly_to_rgb(clim_range: float = 3.0):
    """
    Return a function anom -> (r, g, b) with a gentle diverging scheme:

    - 0°C anomaly ~ light neutral grey
    - negative anomalies ~ soft blue
    - positive anomalies ~ soft red/orange
    - full saturation only near ±clim_range
    """
    neutral = (210, 210, 210)
    cool    = (120, 160, 210)   # soft blue
    warm    = (220, 150, 130)   # soft red/orange

    def interp(c_from, c_to, t: float):
        return tuple(int(c_from[i] + t * (c_to[i] - c_from[i])) for i in range(3))

    def anomaly_to_rgb(anom: float):
        if pd.isna(anom):
            return neutral

        # clamp to [-clim_range, +clim_range]
        a = max(-clim_range, min(clim_range, anom))

        if abs(a) < 0.1:
            # near-zero anomaly: neutral-ish
            return neutral
        elif a < 0:
            # colder than baseline
            t = abs(a) / clim_range
            return interp(neutral, cool, t)
        else:
            # warmer than baseline
            t = a / clim_range
            return interp(neutral, warm, t)

    return anomaly_to_rgb

def register_callbacks(app, df_cet: pd.DataFrame):
    anomaly_to_rgb = make_anomaly_to_rgb()
    year_to_alpha = make_year_to_alpha(df_cet)

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
            # group = group.sort_values("month")
            # color = year_to_color(int(year))
            ref_anom = float(group["t_anom"].mean())  # or .iloc[-1]
            # colour from anomaly, alpha from time
            r, g, b = anomaly_to_rgb(ref_anom)
            alpha = year_to_alpha(year)
            color = f"rgba({r},{g},{b},{alpha})"

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
        Input("cet-3d-mode", "value"),
        Input("cet-3d-smoothing", "value"),
    )
    def update_cet_3d_lines(selected_years, mode, smooth_years):
        if not selected_years:
            selected_years = [int(df_cet["year"].max())]

        dff = df_cet[df_cet["year"].isin(selected_years)].copy()

        # keep t_mean and t_anom for use in colours and smoothing
        monthly = (
            dff.groupby(["year", "month", "month_name"], sort=True)[["t_mean", "t_anom"]]
            .mean()
            .reset_index()
        )

        # For by_month mode we support smoothing across years
        if smooth_years and smooth_years > 1:
            monthly = monthly.sort_values(["month", "year"])
            monthly["t_smooth"] = (
                monthly
                .groupby("month")["t_mean"]
                .transform(
                    lambda s: s.rolling(
                        window=smooth_years, center=True, min_periods=1
                    ).mean()
                )
            )

        fig3d = go.Figure()

        month_vals = list(range(1, 13))
        month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        if mode == "by_month":
            # Each trace = one month evolving through years
            for month, group in monthly.groupby("month"):
                group = group.sort_values("year")

                # Use smoothed temps if available
                z_col = "t_smooth" if ("t_smooth" in group.columns and smooth_years > 1) else "t_mean"

                # Use the *mean anomaly for that month across all years* for hue,
                # so Julians, Januaries etc each have a characteristic colour.
                ref_anom = float(group["t_anom"].mean())
                r, g, b = anomaly_to_rgb(ref_anom)

                # Alpha is a bit tricky here (line spans many years).
                # We'll take alpha for the most recent year in the selected range
                # so more recent months look slightly more solid overall.
                latest_year = int(group["year"].max())
                alpha = year_to_alpha(latest_year)

                color = f"rgba({r},{g},{b},{alpha})"

                fig3d.add_trace(
                    go.Scatter3d(
                        x=[month] * len(group),  # month on x
                        y=group["year"],  # year on y
                        z=group[z_col],  # temp on z
                        mode="lines",
                        name=month_labels[month - 1],
                        line=dict(color=color, width=4),
                    )
                )

        else:
            # Lines by year: each trace = year, month→temp
            for year, group in monthly.groupby("year"):
                year = int(year)
                group = group.sort_values("month")

                # average anomaly for that year
                ref_anom = float(group["t_anom"].mean())
                r, g, b = anomaly_to_rgb(ref_anom)
                alpha = year_to_alpha(year)
                color = f"rgba({r},{g},{b},{alpha})"

                fig3d.add_trace(
                    go.Scatter3d(
                        x=group["month"],  # month on x
                        y=[year] * len(group),  # year on y
                        z=group["t_mean"],  # temp on z
                        mode="lines",
                        name=str(year),
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
            legend_title="Series",
        )

        fig3d.update_layout(
            scene_camera=dict(
                eye=dict(x=1.6, y=1.2, z=1.1),
            )
        )

        return fig3d