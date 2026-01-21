from __future__ import annotations

import pandas as pd
import plotly.graph_objs as go

from app_core.tokens_colors import winter_bucket_color


def add_djf_brackets(
    fig: go.Figure,
    stats_df: pd.DataFrame,
    buckets: list[str],
    *,
    x_dec: str = "Dec",
    x_jan: str = "Jan",
    x_feb: str = "Feb",
    show_labels: bool = True,
    label_every: int = 1,
    max_buckets: int | None = None,  # NEW
) -> go.Figure:
    """
    Overlay DJF min/max 'brackets' onto a Jul–Jun spaghetti figure.

    Bracket design:
      - top horizontal line: Dec -> Feb at y=max_djf
      - bottom horizontal line: Dec -> Feb at y=min_djf
      - vertical connector at Jan: min_djf -> max_djf
    """
    if stats_df is None or stats_df.empty or not buckets:
        return fig

    # limit drawn buckets (for step-by-step teaching)
    if max_buckets is not None:
        buckets = buckets[: max(0, int(max_buckets))]

    for i, b in enumerate(buckets):
        row = stats_df.loc[stats_df["bucket"] == b]
        if row.empty:
            continue

        min_y = float(row["min_djf"].iloc[0])
        max_y = float(row["max_djf"].iloc[0])

        line_col = winter_bucket_color(i, alpha=0.92)

        # Horizontal max line (Dec->Feb)
        fig.add_shape(
            type="line",
            xref="x",
            yref="y",
            x0=x_dec,
            y0=max_y,
            x1=x_feb,
            y1=max_y,
            line=dict(color=line_col, width=2.4),
            layer="above",
        )

        # Horizontal min line (Dec->Feb)
        fig.add_shape(
            type="line",
            xref="x",
            yref="y",
            x0=x_dec,
            y0=min_y,
            x1=x_feb,
            y1=min_y,
            line=dict(color=line_col, width=2.4),
            layer="above",
        )

        # Vertical connector at Jan
        fig.add_shape(
            type="line",
            xref="x",
            yref="y",
            x0=x_jan,
            y0=min_y,
            x1=x_jan,
            y1=max_y,
            line=dict(color=line_col, width=2.4),
            layer="above",
        )

        # Optional label near the top-right of the bracket
        if show_labels and (i % max(1, label_every) == 0):
            label_on_top = i % 2 == 0

            label_y = max_y if label_on_top else min_y
            label_y_offset = 0.18 if label_on_top else -0.18

            fig.add_annotation(
                x=x_feb,
                y=label_y + label_y_offset,
                xref="x",
                yref="y",
                text=b,
                showarrow=False,
                font=dict(size=11, color=line_col),
                xanchor="left",
                yanchor="bottom" if label_on_top else "top",
                opacity=0.95,
            )

    return fig


def add_first_bracket_explainers(
    fig: go.Figure,
    stats_df: pd.DataFrame,
    buckets: list[str],
    *,
    x_feb: str = "Feb",
    text_top: str | None = None,
    text_bottom: str | None = None,
    x_shift_px: int = 28,
    y_shift_top_px: int = 0,
    y_shift_bottom_px: int = 0,
) -> go.Figure:
    """
    Add two arrow+label annotations explaining what the first DJF bracket means.

    Intended for the teaching step where only the first bracket is shown:
      - Top label points to max_djf (warmest DJF month in the bucket)
      - Bottom label points to min_djf (coldest DJF month in the bucket)

    Uses paper-pixel offsets (ax/ay) so placement stays stable across y-range locks.
    """
    if stats_df is None or stats_df.empty or not buckets:
        return fig

    b0 = buckets[0]
    row = stats_df.loc[stats_df["bucket"] == b0]
    if row.empty:
        return fig

    min_y = float(row["min_djf"].iloc[0])
    max_y = float(row["max_djf"].iloc[0])

    col = winter_bucket_color(0, alpha=0.95)

    # Default texts (keep them plain-English)
    if text_top is None:
        text_top = f"Warmest winter month (DJF) in {b0}"
    if text_bottom is None:
        text_bottom = f"Coldest winter month (DJF) in {b0}"

    # Top arrow: point to the max bar near Feb
    fig.add_annotation(
        x=x_feb,
        y=max_y,
        xref="x",
        yref="y",
        text=text_top,
        showarrow=True,
        arrowcolor=col,
        arrowwidth=2,
        arrowsize=1.0,
        ax=x_shift_px,  # text to the right of the point
        ay=-24 + y_shift_top_px,  # slightly above
        xanchor="left",
        yanchor="bottom",
        font=dict(size=12, color=col),
        bgcolor="rgba(255,255,255,0.80)",
        bordercolor="rgba(0,0,0,0.08)",
        borderwidth=1,
        opacity=0.98,
    )

    # Bottom arrow: point to the min bar near Feb
    fig.add_annotation(
        x=x_feb,
        y=min_y,
        xref="x",
        yref="y",
        text=text_bottom,
        showarrow=True,
        arrowcolor=col,
        arrowwidth=2,
        arrowsize=1.0,
        ax=x_shift_px,  # text to the right of the point
        ay=24 + y_shift_bottom_px,  # slightly below
        xanchor="left",
        yanchor="top",
        font=dict(size=12, color=col),
        bgcolor="rgba(255,255,255,0.80)",
        bordercolor="rgba(0,0,0,0.08)",
        borderwidth=1,
        opacity=0.98,
    )

    return fig
