from dash import Input, Output
import plotly.graph_objs as go
import pandas as pd

from data import get_loess_surface_grid
from app_core.plot_theme import CLIMATE_TEMPLATE, COLORS, layout_cet_2d, layout_cet_3d, legend_highlights


def make_anomaly_to_rgb(clim_range: float = COLORS.anomaly.range_c):
    """
    anom (°C) -> (r, g, b) with a gentle diverging scheme:
    neutral around 0, soft blue for cool, soft red/orange for warm.
    """
    neutral = COLORS.anomaly.neutral_rgb
    cool    = COLORS.anomaly.cool_rgb
    warm    = COLORS.anomaly.warm_rgb

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


def make_year_to_alpha(df_cet: pd.DataFrame, alpha_min: float = 0.8, alpha_max: float = 0.95):
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

        years_available = sorted(monthly["year"].unique().astype(int).tolist())
        if not years_available:
            return go.Figure()

        first_year = years_available[0]
        latest_year = years_available[-1]
        prev_year = years_available[-2] if len(years_available) >= 2 else None

        # Mid year anchor: include only if explicitly present
        target_mid = 1855
        mid_year = target_mid if target_mid in years_available else None

        highlight_years = {first_year, latest_year}
        if prev_year is not None:
            highlight_years.add(prev_year)
        if mid_year is not None:
            highlight_years.add(mid_year)

        fig = go.Figure()

        # --- Background styling (more muted) ---
        bg_grey = (160, 160, 160)  # lighter grey
        bg_width = 1.0
        # Keep background lines subtle (texture only)
        bg_alpha_min = 0.03
        bg_alpha_max = 0.18

        def year_to_alpha_bg(year: int) -> float:
            # reuse your year_to_alpha but compress it to a subtle band
            a = year_to_alpha(year)
            # a is in ~[0.15..0.95] from your function; remap to bg band
            # map 0..1 to bg range just in case you change year_to_alpha later
            a01 = max(0.0, min(1.0, (a - 0.15) / (0.95 - 0.15)))
            return bg_alpha_min + a01 * (bg_alpha_max - bg_alpha_min)

        # --- Highlight styling ---
        hi_width = 3.6
        mid_green = COLORS.highlight.reference_green
        hi_alpha = 1.0

        # 1) Add ALL background lines first (so highlights sit on top)
        for year, group in monthly.groupby("year"):
            year = int(year)
            if year in highlight_years:
                continue

            group = group.sort_values("month")

            alpha = year_to_alpha_bg(year)
            r, g, b = bg_grey
            color = f"rgba({r},{g},{b},{alpha})"

            fig.add_trace(
                go.Scatter(
                    x=group["month_name"],
                    y=group["t_mean"],
                    mode="lines",
                    line=dict(color=color, width=bg_width),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

        # Helper to add highlight traces (painted last)
        def add_highlight(year: int, label: str, color: str):
            group = monthly[monthly["year"] == year].sort_values("month")
            fig.add_trace(
                go.Scatter(
                    x=group["month_name"],
                    y=group["t_mean"],
                    mode="lines",
                    name=label,
                    line=dict(color=color, width=hi_width),
                    showlegend=True,
                    hovertemplate=(
                        f"<b>{label}</b><br>"
                        "Month: %{x}<br>"
                        "Temp: %{y:.2f} °C"
                        "<extra></extra>"
                    ),
                )
            )

        # 2) Add highlights last, in a sensible legend order
        # First year
        g_first = monthly[monthly["year"] == first_year]
        r, g, b = anomaly_to_rgb(float(g_first["t_anom"].mean()))
        add_highlight(first_year, f"{first_year} (first)", f"rgba({r},{g},{b},{hi_alpha})")

        # Mid-year (only if present)
        if mid_year is not None:
            add_highlight(mid_year, f"{mid_year} (reference)", mid_green)

        # Previous year (if present)
        if prev_year is not None:
            g_prev = monthly[monthly["year"] == prev_year]
            r, g, b = anomaly_to_rgb(float(g_prev["t_anom"].mean()))
            add_highlight(prev_year, f"{prev_year} (previous)", f"rgba({r},{g},{b},{hi_alpha})")

        # Latest year
        g_latest = monthly[monthly["year"] == latest_year]
        r, g, b = anomaly_to_rgb(float(g_latest["t_anom"].mean()))
        add_highlight(latest_year, f"{latest_year} (latest)", f"rgba({r},{g},{b},{hi_alpha})")

        fig.update_layout(template=CLIMATE_TEMPLATE)
        fig.update_layout(**layout_cet_2d(y_range))
        fig.update_layout(**legend_highlights("Highlighted years"))

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

            alpha = 0.95
            color_3d = f"rgba({r},{g},{b},{alpha})"

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
        months_grid, years_grid, Z_grid = get_loess_surface_grid(
            years=list(sorted(dff["year"].unique()))
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