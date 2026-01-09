from dash import Input, Output
import pandas as pd

from viz.figures.overview_2d import build_cet_2d_figure
from viz.figures.winter_boxes import build_winter_djf_boxplots


def register_winter_callbacks(app, df_cet: pd.DataFrame):
    years_all = sorted(df_cet["year"].unique().astype(int).tolist())
    min_year, max_year = years_all[0], years_all[-1]

    @app.callback(
        Output("winter-phase-a", "figure"),
        Output("winter-phase-b", "figure"),
        Input("winter-range-preset", "value"),
        Input("winter-bucket-mode", "value"),
    )
    def update_winter(range_preset: str, bucket_mode: str):
        # --- range selection (mirror Overview) ---
        if range_preset == "modern":
            start, end = max(1950, min_year), max_year
        elif range_preset == "instrumental":
            start, end = max(1772, min_year), max_year
        elif range_preset == "full":
            start, end = min_year, max_year
        else:
            start, end = max(1950, min_year), max_year

        years_range = list(range(start, end + 1))

        # Phase A: Jul->Jun cycle view
        # (no highlights yet; keep it clean for workbench)
        fig_a = build_cet_2d_figure(
            df_cet,
            years_range=years_range,
            highlight_year=end,        # harmless default
            compare_year=None,         # keep Phase A uncluttered for now
            start_month="Jul",
            start_offset=-1,
        )
        fig_a.update_layout(
            title=None,
            showlegend=False,  # texture only
        )

        # Phase B: DJF distributions by era buckets, categorical x-axis
        fig_b = build_winter_djf_boxplots(
            df_cet=df_cet,
            years_range=years_range,
            bucket_mode=bucket_mode,
        )

        return fig_a, fig_b