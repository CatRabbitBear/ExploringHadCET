from __future__ import annotations

import pandas as pd
import plotly.graph_objs as go

from app_core.palette import winter_bucket_color


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

    # Slightly stagger label y so they don't collide too much
    # (visual only; safe even if not perfect)
    label_stagger = 0.12

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
            x0=x_dec, y0=max_y,
            x1=x_feb, y1=max_y,
            line=dict(color=line_col, width=2.4),
            layer="above",
        )

        # Horizontal min line (Dec->Feb)
        fig.add_shape(
            type="line",
            xref="x",
            yref="y",
            x0=x_dec, y0=min_y,
            x1=x_feb, y1=min_y,
            line=dict(color=line_col, width=2.4),
            layer="above",
        )

        # Vertical connector at Jan
        fig.add_shape(
            type="line",
            xref="x",
            yref="y",
            x0=x_jan, y0=min_y,
            x1=x_jan, y1=max_y,
            line=dict(color=line_col, width=2.4),
            layer="above",
        )

        # Optional label near the top-right of the bracket
        if show_labels and (i % max(1, label_every) == 0):
            label_on_top = (i % 2 == 0)

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
                xanchor="left",  # push label to the right of Feb
                yanchor="bottom" if label_on_top else "top",
                opacity=0.95,
            )

    return fig