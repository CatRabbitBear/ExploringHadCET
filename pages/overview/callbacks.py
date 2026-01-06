from dash import Input, Output, State
import pandas as pd

from app_core.app_state import coerce_app_state
from viz.figures.cet_2d import build_cet_2d_figure
from viz.figures.cet_3d import build_cet_3d_figure


def register_overview_callbacks(app, df_cet: pd.DataFrame):
    years = sorted(df_cet["year"].unique().astype(int).tolist())
    min_year, max_year = int(years[0]), int(years[-1])

    # 1) Overview control writes into global app-state
    @app.callback(
        Output("app-state", "data"),
        Input("cet-range-preset", "value"),
        State("app-state", "data"),
    )
    def persist_era_to_app_state(preset: str, app_state: dict):
        state = coerce_app_state(app_state)
        # only update the field we care about
        state["era"] = preset or state["era"]
        return coerce_app_state(state)

    # 2) Figures read from app-state (single source of truth)
    @app.callback(
        Output("cet-jan-dec-lines", "figure"),
        Output("cet-3d-lines", "figure"),
        Input("app-state", "data"),
    )
    def update_overview(app_state: dict):
        state = coerce_app_state(app_state)
        era = state["era"]

        if era == "modern":
            start, end = max(1950, min_year), max_year
        elif era == "instrumental":
            start, end = max(1772, min_year), max_year
        elif era == "full":
            start, end = min_year, max_year
        else:
            start, end = max(1950, min_year), max_year  # safe default

        selected_years = list(range(start, end + 1))

        fig_2d = build_cet_2d_figure(df_cet, selected_years)
        fig_3d = build_cet_3d_figure(df_cet, selected_years)
        return fig_2d, fig_3d