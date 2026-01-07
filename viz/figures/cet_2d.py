import pandas as pd
import plotly.graph_objs as go

from app_core.plot_theme import CLIMATE_TEMPLATE, layout_cet_2d
from viz.utils import make_year_to_alpha


def build_cet_2d_figure(
    df_cet: pd.DataFrame,
    years_range: list[int],
    highlight_year: int,
    compare_year: int | None = None,
) -> go.Figure:
    if not years_range:
        return go.Figure()

    # Subset once (fast)
    dff = df_cet[df_cet["year"].isin(years_range)][["year", "month", "month_name", "tmean_c"]].copy()
    if dff.empty:
        return go.Figure()

    # y-range matches what you've been using
    t_min = float(df_cet["tmean_c"].min())
    t_max = float(df_cet["tmean_c"].max())
    y_range = [t_min - 0.5, t_max + 0.5]

    # background alpha mapping (based on full df range; ok)
    year_to_alpha = make_year_to_alpha(df_cet, alpha_min=0.03, alpha_max=0.16)

    fig = go.Figure()

    # --- Background "texture" (no hover, no legend) ---
    bg_rgb = (140, 140, 140)
    bg_width = 1.0

    for y, g in dff.groupby("year"):
        y = int(y)
        if y == highlight_year or (compare_year is not None and y == compare_year):
            continue

        g = g.sort_values("month")
        a = year_to_alpha(y)
        r, gg, b = bg_rgb

        fig.add_trace(
            go.Scatter(
                x=g["month_name"],
                y=g["tmean_c"],
                mode="lines",
                line=dict(color=f"rgba({r},{gg},{b},{a})", width=bg_width),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # --- Compare line (optional) ---
    if compare_year is not None:
        g = dff[dff["year"] == compare_year].sort_values("month")
        if not g.empty:
            fig.add_trace(
                go.Scatter(
                    x=g["month_name"],
                    y=g["tmean_c"],
                    mode="lines",
                    name=str(compare_year),
                    line=dict(color="rgba(60,60,60,0.85)", width=2, dash="dot"),
                    hovertemplate=(
                        f"<b>{compare_year}</b><br>"
                        "Month: %{x}<br>"
                        "Temp: %{y:.2f} °C"
                        "<extra></extra>"
                    ),
                )
            )

    # --- Highlight line ---
    g = dff[dff["year"] == highlight_year].sort_values("month")
    if not g.empty:
        fig.add_trace(
            go.Scatter(
                x=g["month_name"],
                y=g["tmean_c"],
                mode="lines",
                name=str(highlight_year),
                line=dict(color="rgba(20,20,20,1.0)", width=3.6),
                hovertemplate=(
                    f"<b>{highlight_year}</b><br>"
                    "Month: %{x}<br>"
                    "Temp: %{y:.2f} °C"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(template=CLIMATE_TEMPLATE)
    fig.update_layout(**layout_cet_2d(y_range))

    # A couple small readability nudges
    fig.update_layout(
        margin=dict(l=40, r=10, t=40, b=35),
        legend=dict(
            title=dict(text="Highlighted"),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="rgba(0,0,0,0.12)",
            borderwidth=1,
        ),
    )

    return fig