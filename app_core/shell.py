import pandas as pd
import dash_mantine_components as dmc
from dash import html, dcc

from app_core.app_state import make_app_state_store
from app_core.view_range import make_view_range_store
from app_core.mantine_theme import THEME


SECTIONS = [
    ("overview", "Overview"),
    ("exceptional", "Exceptional Months"),
    ("winter", "Winter in Focus"),
    ("method", "Methodology"),
]


def get_shell_layout(df_cet: pd.DataFrame):
    years = sorted(df_cet["year"].unique().astype(int).tolist())
    min_year, max_year = years[0], years[-1]

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
        theme=THEME,
        children=[
            dcc.Location(id="url", refresh=False),
            make_app_state_store(),
            make_view_range_store(min_year=min_year, max_year=max_year),
            dmc.Box(
                # style={
                #     "position": "sticky",
                #     "top": 0,
                #     "zIndex": 1000,
                #     "background": "var(--mantine-color-body)",
                #     "borderBottom": "1px solid var(--mantine-color-gray-3)",
                # },
                className="app-header app-header--elevated",
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
                                            dmc.Title(
                                                "Exploring UK Temperature Records",
                                                order=1,
                                            ),
                                            dmc.Badge("v1", variant="light"),
                                        ],
                                    ),
                                    dmc.Group(
                                        gap="xs",
                                        align="center",
                                        children=[
                                            dmc.Text(
                                                "Years shown", size="sm", c="dimmed"
                                            ),
                                            dmc.SegmentedControl(
                                                id="global-range-preset",
                                                value="instrumental",
                                                size="xs",
                                                data=[
                                                    {
                                                        "label": "Modern era",
                                                        "value": "modern",
                                                    },
                                                    {
                                                        "label": "Instrumental era",
                                                        "value": "instrumental",
                                                    },
                                                    {
                                                        "label": "Full record",
                                                        "value": "full",
                                                    },
                                                ],
                                            ),
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
