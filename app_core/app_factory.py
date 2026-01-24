import logging

from dash import Dash
from data import load_monthly_features

from .shell import get_shell_layout
from .shell_callbacks import (
    register_page_router_callback,
    register_view_range_callbacks,
)
from pages.overview.callbacks import register_overview_callbacks
from pages.exceptional.callbacks import register_exceptional_callbacks
from pages.winter.callbacks import register_winter_callbacks

logger = logging.getLogger(__name__)


def create_dash_app() -> Dash:
    logger.info("Creating Dash app...")
    app = Dash(__name__, suppress_callback_exceptions=True)

    df_cet = load_monthly_features()
    logger.info("Monthly features data loaded.")

    app.layout = get_shell_layout(df_cet)

    # register_shell_callbacks(app, df_cet)
    register_page_router_callback(app, df_cet)
    register_view_range_callbacks(app, df_cet)

    # page-specific callbacks
    register_overview_callbacks(app, df_cet)
    register_exceptional_callbacks(app, df_cet)
    register_winter_callbacks(app, df_cet)

    logger.info("Dash app created successfully.")

    return app
