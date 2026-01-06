import pandas as pd
import dash_mantine_components as dmc
from dash import html, dcc

from app_core.app_state import make_app_state_store


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
    }

    def desktop_nav():
        # link-based "pills"
        return dmc.Group(
            gap="xs",
            visibleFrom="sm",
            children=[
                dcc.Link(
                    dmc.Button(label, variant="light", size="sm"),
                    href=f"/{key}",
                    style={"textDecoration": "none"},
                )
                for key, label in SECTIONS
            ],
        )

    def mobile_nav():
        return dmc.Box(
            hiddenFrom="sm",  # 👈 Box supports responsive props
            children=[
                dmc.Menu(
                    position="bottom-end",
                    withinPortal=True,
                    children=[
                        dmc.MenuTarget(
                            dmc.Button("Sections", variant="light", size="sm")
                        ),
                        dmc.MenuDropdown(
                            children=[
                                dmc.MenuItem(
                                    dcc.Link(
                                        label,
                                        href=f"/{key}",
                                        style={
                                            "textDecoration": "none",
                                            "color": "inherit",
                                            "display": "block",
                                            "width": "100%",
                                        },
                                    )
                                )
                                for key, label in SECTIONS
                            ]
                        ),
                    ],
                )
            ],
        )

    return dmc.MantineProvider(
        theme=theme,
        children=[
            dcc.Location(id="url", refresh=False),
            make_app_state_store(),

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
                                    desktop_nav(),
                                    mobile_nav(),
                                ],
                            ),
                        ],
                    )
                ],
            ),

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