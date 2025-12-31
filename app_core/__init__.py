from dash import Dash
from data import get_cet_monthly_with_anomalies
from .layout_main import get_layout
from .callbacks_main import register_callbacks

def create_dash_app() -> Dash:
    app = Dash(__name__)

    df_cet = get_cet_monthly_with_anomalies(
        centre_year=1855,
        window_half_width=5,
    )

    app.layout = get_layout(df_cet)
    register_callbacks(app, df_cet)

    return app