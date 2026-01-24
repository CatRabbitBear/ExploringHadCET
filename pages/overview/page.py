from dash import dcc
import dash_mantine_components as dmc
import pandas as pd

from pages.markdown_utils import render_md_section
from ui_components.cards import page_footer
from ui_components.tooltips import help_tooltip


def get_overview_layout(df_cet: pd.DataFrame):
    years = sorted(df_cet["year"].unique().astype(int).tolist())
    min_year, max_year = years[0], years[-1]

    return dmc.Stack(
        gap="md",
        children=[
            dmc.Title(
                "What the Central England Temperature Record Shows",
                order=2,
                ta="center",
            ),
            dmc.Title(
                "Monthly mean temperatures presented in historical context",
                order=3,
                ta="center",
                fs="italic",
            ),
            render_md_section(__file__, "sections/01_intro.md"),
            dmc.Card(
                withBorder=True,
                shadow="sm",
                radius="md",
                my="md",
                children=[
                    dmc.Group(
                        gap="xs",
                        align="center",
                        children=[
                            dmc.Title(
                                "How Monthly Temperatures Compare Year by Year", order=2
                            ),
                            help_tooltip(key="overview.monthly_compare"),
                        ],
                    ),
                    dcc.Graph(id="cet-jan-dec-lines", className="graph-2d"),
                    dmc.Stack(
                        gap="sm",
                        children=[
                            dmc.Group(
                                justify="space-between",
                                align="end",
                                children=[
                                    dmc.Stack(
                                        gap=2,
                                        children=[
                                            dmc.Text("Highlighted year", fw=600),
                                            dmc.Text(
                                                "View a particular year against the full context.",
                                                size="sm",
                                                c="dimmed",
                                            ),
                                        ],
                                    ),
                                    dmc.Group(
                                        gap="sm",
                                        align="end",
                                        children=[
                                            dmc.SegmentedControl(
                                                id="cet-highlight-mode",
                                                value="latest",
                                                data=[
                                                    {
                                                        "label": "Latest",
                                                        "value": "latest",
                                                    },
                                                    {
                                                        "label": "Previous",
                                                        "value": "previous",
                                                    },
                                                    {
                                                        "label": "Reference",
                                                        "value": "reference",
                                                    },
                                                    {
                                                        "label": "Custom",
                                                        "value": "custom",
                                                    },
                                                ],
                                            ),
                                            dmc.Select(
                                                id="cet-highlight-year",
                                                value=str(max_year),
                                                data=[
                                                    {"value": str(y), "label": str(y)}
                                                    for y in years
                                                ],
                                                searchable=True,
                                                clearable=False,
                                                w=140,
                                                style={
                                                    "display": "none"
                                                },  # shown only when mode == "custom"
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
            render_md_section(__file__, "sections/02_2d_discussion.md"),
            dmc.Card(
                withBorder=True,
                shadow="sm",
                radius="md",
                my="md",
                children=[
                    dmc.Stack(
                        gap="xs",
                        children=[
                            dmc.Group(
                                gap="xs",
                                align="center",
                                children=[
                                    dmc.Title("A Smoothed View Across Years", order=2),
                                    help_tooltip(key="overview.loess_surface"),
                                ],
                            ),
                            dmc.Text(
                                [
                                    "A smoothed surface of the same monthly data, coloured by anomaly ",
                                    help_tooltip(key="overview.anomaly"),
                                    " relative to the baseline ",
                                    help_tooltip(key="overview.baseline_1961_1990"),
                                    ".",
                                ],
                                size="sm",
                                c="dimmed",
                            ),
                            dcc.Graph(id="cet-3d-lines", className="graph-3d"),
                        ],
                    )
                ],
            ),
            render_md_section(__file__, "sections/03_3d_discussion.md"),
            page_footer(
                github_url="https://github.com/CatRabbitBear/UKClimateDashboard",
                linkedin_url="https://www.linkedin.com/in/anthony-cokayne-34a719356/",
                related_links=[
                    (
                        "Met Office HadCET data",
                        "https://www.metoffice.gov.uk/hadobs/hadcet/data/download.html",
                    ),
                ],
                next_page=("Next: Exceptional months", "/exceptional"),
            ),
        ],
    )
