from dash import dcc
import dash_mantine_components as dmc
import pandas as pd


def get_winter_layout(df_cet: pd.DataFrame):
    years = sorted(df_cet["year"].unique().astype(int).tolist())
    min_year, max_year = years[0], years[-1]

    return dmc.Stack(
        gap="md",
        children=[
            dmc.Title("Winter in Focus – Workbench", order=2),
            dmc.Text(
                "Temporary layout to tune Phase A (Jul–Jun spaghetti) and Phase B (DJF boxplots by era) "
                "before we merge them into a single guided visual.",
                size="sm",
                c="dimmed",
            ),

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
                                            dmc.Text("View range", fw=600),
                                            dmc.Text("Keep it fast and comparable.", size="sm", c="dimmed"),
                                        ],
                                    ),
                                    dmc.SegmentedControl(
                                        id="winter-range-preset",
                                        value="modern",
                                        data=[
                                            {"label": "Modern era", "value": "modern"},
                                            {"label": "Instrumental era", "value": "instrumental"},
                                            {"label": "Full record", "value": "full"},
                                        ],
                                    ),
                                ],
                            ),

                            dmc.Divider(),

                            dmc.Group(
                                justify="space-between",
                                align="end",
                                children=[
                                    dmc.Stack(
                                        gap=2,
                                        children=[
                                            dmc.Text("Era buckets (Phase B)", fw=600),
                                            dmc.Text(
                                                "Choose how distributions are grouped on the x-axis.",
                                                size="sm",
                                                c="dimmed",
                                            ),
                                        ],
                                    ),
                                    dmc.SegmentedControl(
                                        id="winter-bucket-mode",
                                        value="century",
                                        data=[
                                            {"label": "Centuries", "value": "century"},
                                            {"label": "50-year", "value": "50y"},
                                            {"label": "25-year", "value": "25y"},
                                        ],
                                    ),
                                ],
                            ),

                            dmc.Text(f"Data range: {min_year}–{max_year}", size="xs", c="dimmed"),
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
                            dmc.Group(justify="space-between", children=[dmc.Title("Phase A – Jul–Jun (winter centred)", order=4)]),
                            dmc.Text(
                                "Same year-lines idea as Overview, but the cycle starts in July so DJF sits in the middle.",
                                size="sm",
                                c="dimmed",
                            ),
                            dcc.Graph(id="winter-phase-a", style={"height": "45vh"}),
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
                            dmc.Group(justify="space-between", children=[dmc.Title("Phase B – DJF distributions by era (boxplots)", order=4)]),
                            dmc.Text(
                                "Each box summarises winter months (Dec–Jan–Feb) for an era bucket, shown side-by-side.",
                                size="sm",
                                c="dimmed",
                            ),
                            dcc.Graph(id="winter-phase-b", style={"height": "45vh"}),
                        ],
                    )
                ],
            ),
        ],
    )