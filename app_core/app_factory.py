from dash import Dash
from data import load_monthly_features
from .shell import get_shell_layout
from pages.overview.callbacks import register_overview_callbacks

def create_dash_app() -> Dash:
    app = Dash(__name__)

    df_cet = load_monthly_features()

    app.layout = get_shell_layout(df_cet)
    register_overview_callbacks(app, df_cet)

    return app