import dash_mantine_components as dmc
import pandas as pd
from dash import dcc

from pages.markdown_utils import render_md_section
from ui_components.cards import page_footer
from ui_components.tooltips import help_tooltip


def get_winter_layout(df_cet: pd.DataFrame):
    return dmc.Stack(
        gap="md",
        children=[
            dmc.Title("Winter in Focus", order=2, ta="center"),
            dmc.Group(
                justify="center",
                align="center",
                gap="xs",
                children=[
                    dmc.Title(
                        "Comparing December, January, and February across the historical record.",
                        order=3,
                        ta="center",
                    ),
                    help_tooltip(key="winter.djf_definition"),
                ],
            ),
            # --- Stores ---
            dcc.Store(
                id="winter-view-mode", storage_type="local"
            ),  # "guided" | "final"
            dcc.Store(id="winter-step", storage_type="memory"),
            dcc.Store(id="winter-autoplay", storage_type="memory"),
            dcc.Store(id="winter-is-mobile", storage_type="memory"),
            # --- Intervals ---
            dcc.Interval(
                id="winter-init-tick", interval=50, n_intervals=0, max_intervals=1
            ),
            dcc.Interval(id="winter-tick", interval=900, n_intervals=0, disabled=True),
            render_md_section(__file__, "sections/01_intro.md"),
            dmc.Card(
                withBorder=True,
                shadow="sm",
                radius="md",
                children=[
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
                                            dmc.Text("Era buckets", fw=600),
                                            dmc.Text(
                                                "Auto picks 50-year for modern, century for full record.",
                                                size="sm",
                                                c="dimmed",
                                            ),
                                        ],
                                    ),
                                    dmc.SegmentedControl(
                                        id="winter-bucket-mode",
                                        value="auto",
                                        data=[
                                            {"label": "Auto", "value": "auto"},
                                            {"label": "Centuries", "value": "century"},
                                            {"label": "50-year", "value": "50y"},
                                            {"label": "25-year", "value": "25y"},
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    )
                ],
            ),
            dmc.Card(
                withBorder=True,
                shadow="sm",
                radius="md",
                children=[
                    dmc.Stack(
                        gap="xs",
                        children=[
                            dmc.Group(
                                gap="xs",
                                align="center",
                                children=[
                                    dmc.Text(
                                        id="winter-caption", size="sm", c="dimmed"
                                    ),
                                    help_tooltip(key="winter.winter_year"),
                                ],
                            ),
                            dcc.Graph(id="winter-main-graph", className="graph-story"),
                            # --- Story controls (footer bar) ---
                            dmc.Group(
                                justify="space-between",
                                align="center",
                                mt="xs",
                                children=[
                                    dmc.Button(
                                        "◀ Back", id="winter-btn-back", variant="subtle"
                                    ),
                                    dmc.Text(
                                        id="winter-step-indicator",
                                        size="sm",
                                        c="dimmed",
                                    ),
                                    dmc.Group(
                                        gap="xs",
                                        children=[
                                            dmc.Button(
                                                "Next ▶",
                                                id="winter-btn-next",
                                                variant="filled",
                                            ),
                                            dmc.Button(
                                                "▶ Play",
                                                id="winter-btn-play",
                                                variant="light",
                                            ),
                                            dmc.Button(
                                                "Show final",
                                                id="winter-btn-final",
                                                variant="light",
                                            ),
                                            dmc.Button(
                                                "Resize y-axis",
                                                id="winter-btn-resize",
                                                variant="light",
                                            ),
                                            dmc.Button(
                                                "Reset ↺",
                                                id="winter-btn-reset",
                                                variant="subtle",
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    )
                ],
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
                next_page=("Next: Methodology", "/method"),
            ),
        ],
    )
