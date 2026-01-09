from __future__ import annotations

import math
import pandas as pd
import dash_mantine_components as dmc
import plotly.graph_objs as go
from dash import Input, Output

from app_core.palette import CLIMATE, UI

ANOM_COL = "tmean_anom_1961_1990_c"
BASE_COL = "tmean_base_1961_1990_c"
TMEAN_COL = "tmean_c"

MONTHS = [
    (1, "Jan"), (2, "Feb"), (3, "Mar"), (4, "Apr"),
    (5, "May"), (6, "Jun"), (7, "Jul"), (8, "Aug"),
    (9, "Sep"), (10, "Oct"), (11, "Nov"), (12, "Dec"),
]


# --- Recency palette (tweak to taste) ---
OLD_GREY = (235, 238, 242)   # light grey
NEW_GREEN = (45, 190, 105)   # bold green


def _clamp01(t: float) -> float:
    return max(0.0, min(1.0, t))


def _lerp(a: int, b: int, t: float) -> int:
    return int(round(a + (b - a) * t))


def _rgb_lerp(c0: tuple[int, int, int], c1: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = _clamp01(t)
    return (_lerp(c0[0], c1[0], t), _lerp(c0[1], c1[1], t), _lerp(c0[2], c1[2], t))


def _year_to_recency_rgb(year: int, min_year: int, max_year: int) -> tuple[int, int, int]:
    if max_year == min_year:
        return NEW_GREEN
    t = (year - min_year) / (max_year - min_year)
    # Optional: bias towards highlighting recent years more aggressively
    # e.g. gamma < 1 boosts recent contrast
    gamma = 0.75
    t = t ** gamma
    return _rgb_lerp(OLD_GREY, NEW_GREEN, t)


def _fmt(x: float | None, decimals: int = 1) -> str:
    if x is None:
        return "—"
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return "—"
    return f"{x:.{decimals}f}"


def _text_color_for_bg(rgb: tuple[int, int, int]) -> str:
    # Proper luminance for legibility
    r, g, b = rgb
    luminance = 0.2126 * (r / 255) + 0.7152 * (g / 255) + 0.0722 * (b / 255)
    return "black" if luminance > 0.62 else "white"


def _compute_exceptional_events(
    df_cet: pd.DataFrame,
    *,
    mode: str,
    top_n: int,
) -> pd.DataFrame:
    """
    Returns tidy events: one row per (month, rank) entry in the top-N table.
    Columns: month, month_name, rank, year, tmean, anom, baseline
    """
    required = {"year", "month", ANOM_COL, TMEAN_COL}
    missing = required - set(df_cet.columns)
    if missing:
        return pd.DataFrame(columns=["month", "month_name", "rank", "year", "tmean", "anom", "baseline"])

    dff = df_cet.dropna(subset=[ANOM_COL, TMEAN_COL]).copy()

    rows: list[dict] = []
    for m, mlabel in MONTHS:
        sub = dff[dff["month"] == m].copy()

        # baseline: constant per month in your parquet (month-specific climatology)
        base_val = None
        if BASE_COL in sub.columns:
            base_series = sub[BASE_COL].dropna()
            base_val = float(base_series.iloc[0]) if len(base_series) else None

        sub = sub.sort_values(ANOM_COL, ascending=(mode != "warm")).head(top_n)

        for i, (_, r) in enumerate(sub.iterrows(), start=1):
            year = int(r["year"])
            tmean = float(r[TMEAN_COL]) if pd.notna(r[TMEAN_COL]) else None
            anom = float(r[ANOM_COL]) if pd.notna(r[ANOM_COL]) else None

            rows.append(
                {
                    "month": m,
                    "month_name": mlabel,
                    "rank": i,
                    "year": year,
                    "tmean": tmean,
                    "anom": anom,
                    "baseline": base_val,
                }
            )

    return pd.DataFrame(rows)

def _build_rank_labels(mode: str, top_n: int) -> dmc.Stack:
    if mode == "warm":
        labels = ["Warmest", "2nd", "3rd"] + [f"{i}th" for i in range(4, top_n + 1)]
    else:
        labels = ["Coldest", "2nd", "3rd"] + [f"{i}th" for i in range(4, top_n + 1)]

    items = []
    for i in range(top_n):
        items.append(
            dmc.Paper(
                p="xs",
                radius="md",
                withBorder=False,
                style={
                    "background": "transparent",
                    "minHeight": "56px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "flex-end",
                },
                children=dmc.Text(labels[i], size="sm", fw=700 if i == 0 else 500, c="dimmed"),
            )
        )

    return dmc.Stack(
        gap="xs",
        children=[
            dmc.Text("Rank", fw=700, ta="right"),
            dmc.Text(" ", size="xs"),  # tiny spacer to align with month header baseline line
            *items,
        ],
    )


def _build_month_column(
    dff: pd.DataFrame,
    month: int,
    month_label: str,
    *,
    mode: str,
    top_n: int,
    detailed: bool,
    color_by_anom: bool,
    min_year: int,
    max_year: int,
) -> dmc.Stack:
    sub = dff[dff["month"] == month].copy()

    base_val = None
    if BASE_COL in sub.columns:
        base_series = sub[BASE_COL].dropna()
        base_val = float(base_series.iloc[0]) if len(base_series) else None

    # sort for hot/cold
    sub = sub.sort_values(ANOM_COL, ascending=(mode != "warm")).head(top_n)

    cells = []
    for i in range(top_n):
        if i < len(sub):
            row = sub.iloc[i]
            year = int(row["year"])
            tmean = float(row[TMEAN_COL]) if pd.notna(row[TMEAN_COL]) else None
            anom = float(row[ANOM_COL]) if pd.notna(row[ANOM_COL]) else None

            # --- Colouring strategy ---
            if color_by_anom and anom is not None:
                r, g, b = CLIMATE.sample_anomaly_rgb(float(anom))
                bg_rgb = (int(r), int(g), int(b))
            else:
                bg_rgb = _year_to_recency_rgb(year, min_year, max_year)

            fg = _text_color_for_bg(bg_rgb)
            bg = f"rgb({bg_rgb[0]},{bg_rgb[1]},{bg_rgb[2]})"

            if not detailed:
                content = dmc.Text(str(year), fw=800, ta="center", c=fg)
            else:
                content = dmc.Stack(
                    gap=2,
                    children=[
                        dmc.Text(str(year), fw=800, ta="center", c=fg),
                        dmc.Text(f"{_fmt(tmean, 1)} °C", size="sm", ta="center", c=fg),
                        dmc.Text(f"{_fmt(anom, 1)} °C", size="sm", fw=700, ta="center", c=fg),
                    ],
                )
        else:
            bg = UI.surface_alt
            content = dmc.Text("—", ta="center", c=UI.text_muted)

        cells.append(
            dmc.Paper(
                p="xs",
                radius="md",
                withBorder=True,
                style={
                    "background": bg,
                    "borderColor": UI.border,
                    "minHeight": "56px" if not detailed else "82px",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                },
                children=content,
            )
        )

    header = dmc.Stack(
        gap=0,
        children=[
            dmc.Text(month_label, fw=800, ta="center"),
            dmc.Text(f"{_fmt(base_val, 1)}° (61–90)", size="xs", ta="center", c="dimmed"),
        ],
    )

    return dmc.Stack(gap="xs", children=[header, *cells])

def _build_exceptional_timeline_figure(
    events: pd.DataFrame,
    *,
    title: str,
    mode: str,
    color_by_anom: bool,
    min_year: int,
    max_year: int,
) -> go.Figure:
    fig = go.Figure()

    if events.empty:
        fig.update_layout(
            template="plotly_white",
            title=title,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        return fig

    # y lanes = rank (1..N) but we invert visually so rank 1 is on top
    top_n = int(events["rank"].max())

    # Build marker colors per row
    colors = []
    text_colors = []
    for _, r in events.iterrows():
        year = int(r["year"])
        anom = r["anom"]

        if color_by_anom and anom is not None and pd.notna(anom):
            rr, gg, bb = CLIMATE.sample_anomaly_rgb(float(anom))
            bg_rgb = (int(rr), int(gg), int(bb))
        else:
            bg_rgb = _year_to_recency_rgb(year, min_year, max_year)

        colors.append(f"rgb({bg_rgb[0]},{bg_rgb[1]},{bg_rgb[2]})")
        text_colors.append(_text_color_for_bg(bg_rgb))

    # Optional: hover detail
    hover = (
        "<b>%{customdata[0]}</b><br>"
        "Year: %{x}<br>"
        "Rank: %{customdata[1]}<br>"
        "Mean: %{customdata[2]} °C<br>"
        "Anom: %{customdata[3]} °C"
        "<extra></extra>"
    )

    customdata = []
    for _, r in events.iterrows():
        base = r["baseline"]
        base_str = f"{_fmt(base, 1)}° (61–90)" if base is not None else "—"
        customdata.append(
            [
                f"{r['month_name']} (baseline {base_str})",
                int(r["rank"]),
                _fmt(r["tmean"], 1),
                _fmt(r["anom"], 1),
            ]
        )

    # y plotting: invert so 1 is top
    y_vals = (top_n + 1) - events["rank"].astype(int)

    fig.add_trace(
        go.Scatter(
            x=events["year"],
            y=y_vals,
            mode="markers",
            marker=dict(
                size=10 if top_n <= 3 else 8,
                color=colors,
                line=dict(width=0),  # no outlines = cleaner “timeline” vibe
                opacity=0.95,
            ),
            customdata=customdata,
            hovertemplate=hover,
            showlegend=False,
        )
    )

    # Make it feel like a timeline:
    # - y axis hidden
    # - x grid only (subtle)
    # - keep height modest
    fig.update_layout(
        template="plotly_white",
        title=dict(text=title, x=0.0, xanchor="left", font=dict(size=16)),
        margin=dict(l=10, r=10, t=45, b=30),
        height=180 if top_n <= 3 else 220,
    )

    fig.update_xaxes(
        title="Year",
        showgrid=True,
        gridcolor="rgba(0,0,0,0.08)",
        zeroline=False,
    )

    fig.update_yaxes(
        visible=False,
        showgrid=False,
        zeroline=False,
        range=[0.5, top_n + 0.5],
    )

    # Optional subtle rank labels on the left as annotations (keeps y-axis hidden)
    ann = []
    label0 = "Warmest" if mode == "warm" else "Coldest"
    for rnk in range(1, top_n + 1):
        y = (top_n + 1) - rnk
        lab = label0 if rnk == 1 else f"{rnk}"
        ann.append(
            dict(
                x=min_year,
                y=y,
                xref="x",
                yref="y",
                xanchor="right",
                text=lab,
                showarrow=False,
                font=dict(size=11, color="rgba(0,0,0,0.45)"),
                align="right",
            )
        )
    fig.update_layout(annotations=ann)

    return fig


def build_exceptional_grid(
    df_cet: pd.DataFrame,
    *,
    mode: str,
    top_n: int,
    detailed: bool,
    color_by_anom: bool,
) -> dmc.SimpleGrid:
    required = {"year", "month", ANOM_COL, TMEAN_COL}
    missing = required - set(df_cet.columns)
    if missing:
        return dmc.SimpleGrid(cols=1, children=[dmc.Alert(f"Missing columns: {sorted(missing)}", color="red")])

    dff = df_cet.dropna(subset=[ANOM_COL, TMEAN_COL]).copy()

    # Recency scaling should be based on the *full* dataset to keep meaning stable
    years_all = df_cet["year"].dropna().astype(int)
    min_year, max_year = int(years_all.min()), int(years_all.max())

    # rank labels + 12 month columns
    # Use responsive cols: 1 rank column + months (wrap on mobile)
    return dmc.SimpleGrid(
        cols={"base": 2, "sm": 3, "md": 5, "lg": 7, "xl": 13},
        spacing="xs",
        verticalSpacing="xs",
        children=[
            dmc.Stack(
                gap="xs",
                children=[
                    dmc.Text(" ", fw=700),  # aligns with month headers
                    dmc.Text(" ", size="xs"),
                    _build_rank_labels(mode, top_n),
                ],
            ),
            *[
                _build_month_column(
                    dff,
                    m,
                    label,
                    mode=mode,
                    top_n=top_n,
                    detailed=detailed,
                    color_by_anom=color_by_anom,
                    min_year=min_year,
                    max_year=max_year,
                )
                for m, label in MONTHS
            ],
        ],
    )


def register_exceptional_callbacks(app, df_cet: pd.DataFrame):
    # stable recency scaling from full dataset
    years_all = df_cet["year"].dropna().astype(int)
    min_year, max_year = int(years_all.min()), int(years_all.max())

    @app.callback(
        Output("exc-hot-grid", "children"),
        Output("exc-cold-grid", "children"),
        Output("exc-hot-timeline", "figure"),
        Output("exc-cold-timeline", "figure"),
        Input("exc-more-detail", "checked"),
        Input("exc-top-n", "value"),
        Input("exc-color-by", "checked"),
    )
    def update_exceptional(detailed: bool, top_n: int, color_by_anom: bool):
        top_n = int(top_n or 3)
        top_n = max(3, min(12, top_n))

        # 1) Build event lists ONCE (shared by grid + timeline)
        hot_events = _compute_exceptional_events(df_cet, mode="warm", top_n=top_n)
        cold_events = _compute_exceptional_events(df_cet, mode="cold", top_n=top_n)

        # 2) Grids (re-use your existing renderer)
        hot_grid = build_exceptional_grid(
            df_cet, mode="warm", top_n=top_n, detailed=bool(detailed), color_by_anom=bool(color_by_anom)
        )
        cold_grid = build_exceptional_grid(
            df_cet, mode="cold", top_n=top_n, detailed=bool(detailed), color_by_anom=bool(color_by_anom)
        )

        # 3) Timelines
        hot_fig = _build_exceptional_timeline_figure(
            hot_events,
            title="Hot months over time",
            mode="warm",
            color_by_anom=bool(color_by_anom),
            min_year=min_year,
            max_year=max_year,
        )
        cold_fig = _build_exceptional_timeline_figure(
            cold_events,
            title="Cold months over time",
            mode="cold",
            color_by_anom=bool(color_by_anom),
            min_year=min_year,
            max_year=max_year,
        )

        return hot_grid, cold_grid, hot_fig, cold_fig