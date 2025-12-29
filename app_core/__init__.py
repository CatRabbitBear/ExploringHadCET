from dash import Dash
from .config import CET_PROCESSED_PATH
from .data_cet import load_cet_monthly, add_monthly_anomalies
from .layout_main import get_layout
from .callbacks_main import register_callbacks


def create_dash_app() -> Dash:
    app = Dash(__name__)

    # Load data once at startup
    df_cet = load_cet_monthly(CET_PROCESSED_PATH)
    df_cet = add_monthly_anomalies(df_cet, centre_year=1855, window_half_width=5)

    # Layout
    app.layout = get_layout(df_cet)

    # Callbacks
    register_callbacks(app, df_cet)

    return app