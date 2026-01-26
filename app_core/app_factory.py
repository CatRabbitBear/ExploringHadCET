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


def create_dash_app(import_name: str) -> Dash:
    logger.info("Creating Dash app...")
    app = Dash(import_name, 
               suppress_callback_exceptions=True, 
               title="Exploring HadCET – UK Climate Data",
                meta_tags=[
                    {"name": "description", "content": "Interactive exploration of UK climate trends using HadCET temperature data."},
                    {"name": "viewport", "content": "width=device-width, initial-scale=1"},
                    {"property": "og:title", "content": "Exploring HadCET"},
                    {"property": "og:description", "content": "Visual exploration of UK climate trends from historical temperature data."},
                    {"property": "og:type", "content": "website"},
                ],)

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
