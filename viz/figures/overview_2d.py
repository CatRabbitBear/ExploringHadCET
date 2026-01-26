from __future__ import annotations

import pandas as pd
import plotly.graph_objs as go

from viz.figures.cet_cycle import prepare_cet_cycle
from viz.figures.spaghetti_base import build_spaghetti_base
from viz.figures.spaghetti_overlays import add_compare_year, add_highlight_year


def build_cet_2d_figure(
    df_cet: pd.DataFrame,
    years_range: list[int],
    highlight_year: int | None = None,
    compare_year: int | None = None,
    show_legend: bool = True,
    *,
    start_month: str = "Jan",
    start_offset: int = 0,
) -> go.Figure:
    if not years_range:
        return go.Figure()

    dff, x_labels = prepare_cet_cycle(
        df_cet,
        years_range,
        start_month=start_month,
        start_offset=start_offset,
        use_cycle_year=False,  # overview: keep grouping by calendar year
    )
    if dff.empty:
        return go.Figure()

    fig = build_spaghetti_base(df_cet, dff, x_labels, group_col="year")

    # Overlays on top (no need to skip in base builder anymore)
    if compare_year is not None:
        fig = add_compare_year(fig, dff, int(compare_year))
    if highlight_year is not None:
        fig = add_highlight_year(fig, dff, int(highlight_year))

    fig.update_layout(showlegend=show_legend)
    return fig
