from dash import html, dcc
import dash_mantine_components as dmc
import pandas as pd

from pages.markdown_utils import render_md_section
from pages.exceptional.skeletons import build_exceptional_page_skeleton_overlay
from ui_components.cards import page_footer
from ui_components.tooltips import help_tooltip


def get_exceptional_layout(df_cet: pd.DataFrame):
    content = dmc.Stack(
        gap="md",
        children=[
            dmc.Group(
                justify="center",
                align="center",
                gap="xs",
                children=[
                    dmc.Title(
                        "Exceptional Months in the Temperature Record",
                        order=2,
                        ta="center",
                    ),
                    help_tooltip(key="exceptional.definition"),
                ],
            ),
            dmc.Title(
                "Identifying the most unusual warm and cold months using a fixed historical baseline.",
                order=3,
                ta="center",
                fs="italic",
            ),
            render_md_section(__file__, "sections/01_intro.md"),
            # --- Controls ---
            dmc.Card(
                withBorder=True,
                shadow="sm",
                radius="md",
                children=dmc.Stack(
                    gap="sm",
                    children=[
                        dmc.Group(
                            justify="space-between",
                            align="center",
                            children=[
                                dmc.Switch(
                                    id="exc-more-detail",
                                    label="More detail",
                                    description="Show mean temp and anomaly in each cell.",
                                    checked=False,
                                ),
                                dmc.Badge(id="exc-view-range", variant="light"),
                            ],
                        ),
                        dmc.Accordion(
                            variant="separated",
                            radius="md",
                            children=[
                                dmc.AccordionItem(
                                    [
                                        dmc.AccordionControl("Advanced"),
                                        dmc.AccordionPanel(
                                            dmc.Stack(
                                                gap="sm",
                                                children=[
                                                    dmc.Group(
                                                        justify="space-between",
                                                        align="center",
                                                        children=[
                                                            dmc.Switch(
                                                                id="exc-color-by",
                                                                checked=False,
                                                                label="Colour by anomaly (RdBu)",
                                                                description="Overrides recency colouring.",
                                                            ),
                                                            dmc.Text(
                                                                "Top N per month",
                                                                fw=600,
                                                            ),
                                                        ],
                                                    ),
                                                    dmc.Slider(
                                                        id="exc-top-n",
                                                        value=3,
                                                        min=3,
                                                        max=12,
                                                        step=1,
                                                        marks=[
                                                            {"value": 3, "label": "3"},
                                                            {"value": 5, "label": "5"},
                                                            {
                                                                "value": 10,
                                                                "label": "10",
                                                            },
                                                            {
                                                                "value": 12,
                                                                "label": "12",
                                                            },
                                                        ],
                                                    ),
                                                ],
                                            )
                                        ),
                                    ],
                                    value="advanced",
                                )
                            ],
                        ),
                    ],
                ),
            ),
            # --- Warm section: table then timeline ---
            dmc.Card(
                withBorder=True,
                shadow="sm",
                radius="md",
                children=dmc.Stack(
                    gap="sm",
                    children=[
                        dmc.Group(
                            justify="space-between",
                            children=[
                                dmc.Title("Warm anomalies", order=4),
                                dmc.Badge("Ranked warmest-by-month", variant="light"),
                            ],
                        ),
                        html.Div(id="exc-hot-grid"),
                        dmc.Divider(my="xs"),
                        dmc.Stack(
                            gap=4,
                            children=[
                                dmc.Text("Warm timeline", fw=700),
                                dmc.Text(
                                    "Markers show when the top-ranked warm months occur in the record "
                                    "(y-position is just rank; the focus is the year axis).",
                                    size="sm",
                                    c="dimmed",
                                ),
                                dcc.Graph(
                                    id="exc-hot-timeline",
                                    config={"displayModeBar": False},
                                    className="graph-timeline",
                                ),
                            ],
                        ),
                    ],
                ),
            ),
            # --- Cold section: table then timeline ---
            dmc.Card(
                withBorder=True,
                shadow="sm",
                radius="md",
                children=dmc.Stack(
                    gap="sm",
                    children=[
                        dmc.Group(
                            justify="space-between",
                            children=[
                                dmc.Title("Cold anomalies", order=4),
                                dmc.Badge("Ranked coldest-by-month", variant="light"),
                            ],
                        ),
                        html.Div(id="exc-cold-grid"),
                        dmc.Divider(my="xs"),
                        dmc.Stack(
                            gap=4,
                            children=[
                                dmc.Text("Cold timeline", fw=700),
                                dmc.Text(
                                    "Same idea as above, for cold anomalies.",
                                    size="sm",
                                    c="dimmed",
                                ),
                                dcc.Graph(
                                    id="exc-cold-timeline",
                                    config={"displayModeBar": False},
                                    className="graph-timeline",
                                ),
                            ],
                        ),
                    ],
                ),
            ),
            render_md_section(__file__, "sections/02_discussion.md"),
            page_footer(
                github_url="https://github.com/CatRabbitBear/UKClimateDashboard",
                linkedin_url="https://www.linkedin.com/in/anthony-cokayne-34a719356/",
                related_links=[
                    (
                        "Met Office HadCET data",
                        "https://www.metoffice.gov.uk/hadobs/hadcet/data/download.html",
                    ),
                ],
                next_page=("Next: Winter In Focus", "/winter"),
            ),
        ],
    )

    return dmc.Box(
        style={"position": "relative"},
        children=[content, build_exceptional_page_skeleton_overlay()],
    )
