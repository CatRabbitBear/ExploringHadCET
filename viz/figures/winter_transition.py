from __future__ import annotations

from typing import Iterable, Sequence

import plotly.graph_objs as go

from app_core.plotly_theme import CLIMATE_TEMPLATE, layout_cet_2d
from app_core.tokens_colors import winter_bucket_color

from viz.figures.winter_layout_spec import BucketSpec


def _interp(a: float, b: float, t: float) -> float:
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return (1 - t) * a + t * b


def build_winter_transition_figure(
    *,
    specs: Sequence[BucketSpec],
    t: float,
    y_range: list[float],
    show_boxes: bool = True,
    show_fill: bool = False,
    show_median: bool = True,
    bracket_alpha: float = 0.95,
    box_line_alpha: float = 0.95,
    box_fill_alpha: float = 0.14,
    cap_width: float = 0.42,
    box_half_width: float = 0.22,
) -> go.Figure:
    """
    Transition figure: numeric x-axis, hidden ticks.
    Each bucket is drawn as:
      - a bracket token: vertical line min->max (plus caps)
      - optional box: q1->q3 rectangle outline + optional fill + median line

    IMPORTANT:
      - The transition graph is told x_start and x_end in BucketSpec (no guessing).
      - If q1/q3/median aren't present on BucketSpec, boxes are skipped gracefully.
    """
    fig = go.Figure()

    cap_width_start = cap_width
    cap_width_end = box_half_width
    cap_w = (1 - t) * cap_width_start + t * cap_width_end

    n = len(specs)
    if n == 0:
        fig.update_layout(template=CLIMATE_TEMPLATE)
        fig.update_layout(**layout_cet_2d(y_range))
        fig.update_xaxes(visible=False)
        return fig

    # Draw each bucket as its own trace(s) for easy opacity / tweaking
    for s in specs:
        x = _interp(float(s.x_start), float(s.x_end), float(t))
        i = int(s.i)
        col = winter_bucket_color(i, alpha=bracket_alpha)

        # --- bracket (min->max) ---
        fig.add_trace(
            go.Scatter(
                x=[x, x],
                y=[float(s.min_y), float(s.max_y)],
                mode="lines",
                line=dict(color=col, width=2),
                hoverinfo="skip",
                showlegend=False,
            )
        )

        # caps (top & bottom)
        fig.add_trace(
            go.Scatter(
                x=[x - cap_w, x + cap_w, None, x - cap_w, x + cap_w],
                y=[
                    float(s.max_y),
                    float(s.max_y),
                    None,
                    float(s.min_y),
                    float(s.min_y),
                ],
                mode="lines",
                line=dict(color=col, width=2),
                hoverinfo="skip",
                showlegend=False,
            )
        )

        # --- optional box / median (if available on spec) ---
        if show_boxes and (s.q1_y is not None) and (s.q3_y is not None):
            q1 = float(getattr(s, "q1_y"))
            q3 = float(getattr(s, "q3_y"))
            med = float(getattr(s, "median_y")) if hasattr(s, "median_y") else None

            box_col = winter_bucket_color(i, alpha=box_line_alpha)
            fill_col = (
                winter_bucket_color(i, alpha=box_fill_alpha)
                if show_fill
                else "rgba(0,0,0,0)"
            )

            # Box outline as a closed polyline
            fig.add_trace(
                go.Scatter(
                    x=[
                        x - box_half_width,
                        x + box_half_width,
                        x + box_half_width,
                        x - box_half_width,
                        x - box_half_width,
                    ],
                    y=[q1, q1, q3, q3, q1],
                    mode="lines",
                    line=dict(color=box_col, width=2.2),
                    fill="toself" if show_fill else None,
                    fillcolor=fill_col if show_fill else None,
                    hoverinfo="skip",
                    showlegend=False,
                )
            )

            # Median line
            if show_median and med is not None:
                fig.add_trace(
                    go.Scatter(
                        x=[x - box_half_width, x + box_half_width],
                        y=[med, med],
                        mode="lines",
                        line=dict(color=box_col, width=2.2),
                        hoverinfo="skip",
                        showlegend=False,
                    )
                )

    # Layout: numeric x, hidden ticks
    fig.update_layout(template=CLIMATE_TEMPLATE)
    fig.update_layout(**layout_cet_2d(y_range))

    x_min = min(float(s.x_end) for s in specs)
    x_max = max(float(s.x_end) for s in specs)

    padding = 0.8
    fig.update_xaxes(
        visible=False,
        range=[x_min - padding, x_max + padding],
        fixedrange=True,
    )
    fig.update_yaxes(range=y_range)

    fig.update_layout(
        margin=dict(l=40, r=10, t=40, b=35),
        showlegend=False,
    )

    return fig
