import pandas as pd
import plotly.graph_objs as go

from app_core.plot_theme import CLIMATE_TEMPLATE, COLORS, layout_cet_2d, legend_highlights
from viz.utils import make_anomaly_to_rgb, make_year_to_alpha


ANOM_COL = "tmean_anom_1961_1990_c"   # switchable later


def build_cet_2d_figure(df_cet: pd.DataFrame, selected_years: list[int] | None) -> go.Figure:
    if not selected_years:
        selected_years = [int(df_cet["year"].max())]

    anomaly_to_rgb = make_anomaly_to_rgb()
    year_to_alpha = make_year_to_alpha(df_cet)

    t_min = float(df_cet["tmean_c"].min())
    t_max = float(df_cet["tmean_c"].max())
    y_range = [t_min - 0.5, t_max + 0.5]

    dff = df_cet[df_cet["year"].isin(selected_years)].copy()

    # Already monthly, but keep the shape the same as before
    monthly = (
        dff.groupby(["year", "month", "month_name"], sort=True)[["tmean_c", ANOM_COL]]
        .mean()
        .reset_index()
    )

    years_available = sorted(monthly["year"].unique().astype(int).tolist())
    if not years_available:
        return go.Figure()

    first_year = years_available[0]
    latest_year = years_available[-1]
    prev_year = years_available[-2] if len(years_available) >= 2 else None

    target_mid = 1855
    mid_year = target_mid if target_mid in years_available else None

    highlight_years = {first_year, latest_year}
    if prev_year is not None:
        highlight_years.add(prev_year)
    if mid_year is not None:
        highlight_years.add(mid_year)

    fig = go.Figure()

    bg_grey = (160, 160, 160)
    bg_width = 1.0
    bg_alpha_min = 0.03
    bg_alpha_max = 0.18

    def year_to_alpha_bg(year: int) -> float:
        a = year_to_alpha(year)
        a01 = max(0.0, min(1.0, (a - 0.15) / (0.95 - 0.15)))
        return bg_alpha_min + a01 * (bg_alpha_max - bg_alpha_min)

    hi_width = 3.6
    mid_green = COLORS.highlight.reference_green
    hi_alpha = 1.0

    # Background lines first
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
                y=group["tmean_c"],
                mode="lines",
                line=dict(color=color, width=bg_width),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    def add_highlight(year: int, label: str, color: str):
        group = monthly[monthly["year"] == year].sort_values("month")
        fig.add_trace(
            go.Scatter(
                x=group["month_name"],
                y=group["tmean_c"],
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

    g_first = monthly[monthly["year"] == first_year]
    r, g, b = anomaly_to_rgb(float(g_first[ANOM_COL].mean()))
    add_highlight(first_year, f"{first_year} (first)", f"rgba({r},{g},{b},{hi_alpha})")

    if mid_year is not None:
        add_highlight(mid_year, f"{mid_year} (reference)", mid_green)

    if prev_year is not None:
        g_prev = monthly[monthly["year"] == prev_year]
        r, g, b = anomaly_to_rgb(float(g_prev[ANOM_COL].mean()))
        add_highlight(prev_year, f"{prev_year} (previous)", f"rgba({r},{g},{b},{hi_alpha})")

    g_latest = monthly[monthly["year"] == latest_year]
    r, g, b = anomaly_to_rgb(float(g_latest[ANOM_COL].mean()))
    add_highlight(latest_year, f"{latest_year} (latest)", f"rgba({r},{g},{b},{hi_alpha})")

    fig.update_layout(template=CLIMATE_TEMPLATE)
    fig.update_layout(**layout_cet_2d(y_range))
    fig.update_layout(**legend_highlights("Highlighted years"))

    return fig