from dash import dcc
import dash_mantine_components as dmc
import pandas as pd


def get_overview_layout(df_cet: pd.DataFrame):
    years = sorted(df_cet["year"].unique().astype(int).tolist())
    min_year, max_year = years[0], years[-1]

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
                        gap="sm",
                        children=[
                            dmc.Group(
                                justify="space-between",
                                align="end",
                                children=[
                                    dmc.Stack(
                                        gap=2,
                                        children=[
                                            dmc.Text("2D highlight", fw=600),
                                            dmc.Text(
                                                "One year stands out against the full context.",
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
                                                    {"label": "Latest", "value": "latest"},
                                                    {"label": "Previous", "value": "previous"},
                                                    {"label": "Reference", "value": "reference"},
                                                    {"label": "Custom", "value": "custom"},
                                                ],
                                            ),
                                            dmc.Select(
                                                id="cet-highlight-year",
                                                value=str(max_year),
                                                data=[{"value": str(y), "label": str(y)} for y in years],
                                                searchable=True,
                                                clearable=False,
                                                w=140,
                                                style={"display": "none"},  # shown only when mode == "custom"
                                            ),
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
                    dmc.Group(justify="space-between", children=[dmc.Title("2D view", order=4)]),
                    dcc.Graph(id="cet-jan-dec-lines", className="graph-2d"),
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
                            dmc.Group(justify="space-between", children=[dmc.Title("3D view (LOESS surface)", order=4)]),
                            dmc.Text(
                                "A smoothed surface of the same monthly data, coloured by anomaly relative to the baseline.",
                                size="sm",
                                c="dimmed",
                            ),
                            dcc.Graph(id="cet-3d-lines", className="graph-3d"),
                        ],
                    )
                ],
            ),
        ],
    )
