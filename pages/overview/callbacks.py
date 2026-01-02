from dash import Input, Output
import pandas as pd

from viz.figures.cet_2d import build_cet_2d_figure
from viz.figures.cet_3d import build_cet_3d_figure


def register_overview_callbacks(app, df_cet: pd.DataFrame):

    @app.callback(
        Output("cet-jan-dec-lines", "figure"),
        Input("cet-year-select", "value"),
    )
    def update_cet_lines(selected_years):
        return build_cet_2d_figure(df_cet, selected_years)

    @app.callback(
        Output("cet-3d-lines", "figure"),
        Input("cet-year-select", "value"),
    )
    def update_cet_3d_lines(selected_years):
        return build_cet_3d_figure(df_cet, selected_years)