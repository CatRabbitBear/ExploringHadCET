from dash import Input, Output
import pandas as pd

from viz.figures.cet_2d import build_cet_2d_figure
from viz.figures.cet_3d import build_cet_3d_figure


def register_overview_callbacks(app, df_cet: pd.DataFrame):
    years = sorted(df_cet["year"].unique().astype(int).tolist())
    min_year, max_year = int(years[0]), int(years[-1])

    @app.callback(
        Output("cet-jan-dec-lines", "figure"),
        Output("cet-3d-lines", "figure"),
        Input("cet-range-preset", "value"),
    )
    def update_overview(preset: str):
        if preset == "modern":
            start, end = max(1950, min_year), max_year
        elif preset == "instrumental":
            start, end = max(1772, min_year), max_year
        elif preset == "full":
            start, end = min_year, max_year
        else:
            start, end = max(1950, min_year), max_year  # safe default

        selected_years = list(range(start, end + 1))

        fig_2d = build_cet_2d_figure(df_cet, selected_years)
        fig_3d = build_cet_3d_figure(df_cet, selected_years)
        return fig_2d, fig_3d