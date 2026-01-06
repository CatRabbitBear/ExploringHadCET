import pandas as pd
import dash_mantine_components as dmc
from dash import html, dcc


SECTIONS = [
    ("overview", "Overview"),
    ("exceptional", "Exceptional Months"),
    ("winter", "Winter in Focus"),
    ("rainfall", "Monthly Rainfall"),
    ("method", "Methodology"),
]


def get_shell_layout(df_cet: pd.DataFrame):
    theme = {
        "fontFamily": "system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif",
        "primaryColor": "blue",
        "defaultRadius": "md",
        # optional: keep defaults, or customise later
        # "breakpoints": {"sm": "48em", ...}
    }

    return dmc.MantineProvider(
        theme=theme,
        children=[
            dcc.Store(id="nav-section-store", data="overview"),

            # --- Sticky header ---
            dmc.Box(
                style={
                    "position": "sticky",
                    "top": 0,
                    "zIndex": 1000,
                    "background": "var(--mantine-color-body)",
                    "borderBottom": "1px solid var(--mantine-color-gray-3)",
                },
                children=[
                    dmc.Container(
                        size="lg",
                        px="md",
                        py="sm",
                        children=[
                            dmc.Group(
                                justify="space-between",
                                align="center",
                                children=[
                                    dmc.Group(
                                        gap="xs",
                                        children=[
                                            dmc.Title("UK Climate Dashboard", order=3),
                                            dmc.Badge("v1", variant="light"),
                                        ],
                                    ),

                                    # Desktop tabs (visible from sm and up)
                                    dmc.Tabs(
                                        id="nav-tabs",
                                        value="overview",
                                        variant="pills",
                                        visibleFrom="sm",
                                        children=[
                                            dmc.TabsList(
                                                children=[
                                                    dmc.TabsTab(label, value=key)
                                                    for key, label in SECTIONS
                                                ]
                                            )
                                        ],
                                    ),

                                    # Mobile select (hidden from sm and up => only < sm)
                                    dmc.Select(
                                        id="nav-select",
                                        value="overview",
                                        data=[{"value": key, "label": label} for key, label in SECTIONS],
                                        w=220,
                                        searchable=False,
                                        clearable=False,
                                        hiddenFrom="sm",
                                    ),
                                ],
                            ),
                        ],
                    )
                ],
            ),

            # --- Main content ---
            dmc.Container(
                size="lg",
                px="md",
                py="lg",
                children=[
                    html.Div(id="page-content"),
                ],
            ),
        ],
    )