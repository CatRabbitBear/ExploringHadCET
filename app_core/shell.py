import pandas as pd
import dash_mantine_components as dmc
from dash import html

from pages.overview.page import get_overview_layout


def get_shell_layout(df_cet: pd.DataFrame):
    """
    Global app shell. For now, it renders the Overview page directly.
    Later, this becomes:
      - header/nav
      - dash.page_container (when you switch to Dash Pages)
    """

    # Optional: you can move theme dict into app_core/theme.py later
    theme = {
        "fontFamily": "system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif",
        "primaryColor": "blue",
        "defaultRadius": "md",
    }

    return dmc.MantineProvider(
        theme=theme,
        children=[
            dmc.Container(
                size="lg",
                px="md",
                py="lg",
                children=[
                    # For now: just render the overview "tab" content
                    get_overview_layout(df_cet),
                ],
            )
        ],
    )