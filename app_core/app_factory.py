from dash import Dash
from data import get_cet_monthly_with_anomalies
from .shell import get_shell_layout
from pages.overview.callbacks import register_overview_callbacks

def create_dash_app() -> Dash:
    app = Dash(__name__)

    df_cet = get_cet_monthly_with_anomalies(
        centre_year=1855,
        window_half_width=5,
    )

    app.layout = get_shell_layout(df_cet)
    register_overview_callbacks(app, df_cet)

    return app