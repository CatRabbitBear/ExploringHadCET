from dash import dcc
import dash_mantine_components as dmc
import pandas as pd


def get_overview_layout(df_cet: pd.DataFrame):
    years = sorted(df_cet["year"].unique())
    min_year, max_year = int(years[0]), int(years[-1])

    # Defaults: last 50 years feels good; tweak to taste
    default_end = max_year
    default_start = max(min_year, max_year - 49)

    return dmc.Stack(
        gap="md",
        children=[
            dmc.Title("Central England Temperature – Jan–Dec by Year", order=2),

            dmc.Card(
                withBorder=True,
                shadow="sm",
                radius="md",
                children=[
                    dmc.Stack(
                        gap="xs",
                        children=[
                            dmc.Group(
                                justify="space-between",
                                align="end",
                                children=[
                                    dmc.Stack(
                                        gap=2,
                                        children=[
                                            dmc.Text("View range", fw=600),
                                            dmc.Text(
                                                "Presets keep the charts fast and the story consistent.",
                                                size="sm",
                                                c="dimmed",
                                            ),
                                        ],
                                    ),
                                    dmc.SegmentedControl(
                                        id="cet-range-preset",
                                        value="modern",
                                        data=[
                                            {"label": "Modern era", "value": "modern"},
                                            {"label": "Instrumental era", "value": "instrumental"},
                                            {"label": "Full record", "value": "full"},
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
                    dmc.Group(
                        justify="space-between",
                        children=[
                            dmc.Title("2D view", order=4),
                        ],
                    ),
                    dcc.Graph(id="cet-jan-dec-lines", style={"height": "50vh"}),
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
                                justify="space-between",
                                children=[
                                    dmc.Title("3D view (LOESS surface)", order=4),
                                ],
                            ),
                            dmc.Text(
                                "A smoothed surface of the same monthly data, coloured by anomaly relative to the baseline.",
                                size="sm",
                                c="dimmed",
                            ),
                            dcc.Graph(id="cet-3d-lines", style={"height": "60vh"}),
                        ],
                    )
                ],
            ),
        ],
    )