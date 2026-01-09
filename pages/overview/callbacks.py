from dash import Input, Output
import pandas as pd

from viz.figures.overview_2d import build_cet_2d_figure
from viz.figures.overview_3d import build_cet_3d_figure


def register_overview_callbacks(app, df_cet: pd.DataFrame):
    years_all = sorted(df_cet["year"].unique().astype(int).tolist())
    min_year, max_year = years_all[0], years_all[-1]

    @app.callback(
        Output("cet-highlight-year", "style"),
        Input("cet-highlight-mode", "value"),
    )
    def toggle_custom_year(mode: str):
        return {"display": "block"} if mode == "custom" else {"display": "none"}

    @app.callback(
        Output("cet-jan-dec-lines", "figure"),
        Output("cet-3d-lines", "figure"),
        Input("cet-range-preset", "value"),
        Input("cet-highlight-mode", "value"),
        Input("cet-highlight-year", "value"),
    )
    def update_overview(range_preset: str, highlight_mode: str, highlight_year_value: str | None):
        # --- range selection ---
        if range_preset == "modern":
            start, end = max(1950, min_year), max_year
        elif range_preset == "instrumental":
            start, end = max(1772, min_year), max_year
        elif range_preset == "full":
            start, end = min_year, max_year
        else:
            start, end = max(1950, min_year), max_year

        years_range = list(range(start, end + 1))
        years_set = set(years_range)

        # --- highlight selection ---
        def clamp_to_range(y: int) -> int:
            if y in years_set:
                return y
            # clamp to nearest in-range end
            return end if y > end else start

        if highlight_mode == "previous":
            highlight_year = clamp_to_range(end - 1)
            compare_year = clamp_to_range(end)   # compare against latest
        elif highlight_mode == "reference":
            # Choose a clear reference year and clamp to available range
            ref = 1961
            highlight_year = clamp_to_range(ref)
            compare_year = clamp_to_range(end)   # compare reference to latest
        elif highlight_mode == "custom":
            try:
                y = int(highlight_year_value) if highlight_year_value is not None else end
            except ValueError:
                y = end
            highlight_year = clamp_to_range(y)
            compare_year = None
        else:
            # latest
            highlight_year = end
            compare_year = clamp_to_range(end - 1)

        fig_2d = build_cet_2d_figure(
            df_cet,
            years_range=years_range,
            highlight_year=highlight_year,
            compare_year=compare_year,
            start_month="Jan",
            start_offset=0,
        )
        fig_3d = build_cet_3d_figure(df_cet, years_range)

        return fig_2d, fig_3d