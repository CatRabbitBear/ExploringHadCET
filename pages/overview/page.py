from dash import dcc
import dash_mantine_components as dmc
import pandas as pd


def get_overview_layout(df_cet: pd.DataFrame):
    years = sorted(df_cet["year"].unique())
    default_years = years[-20:] if len(years) > 20 else years

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
                            dmc.Text("Select years to display:", fw=500),
                            dcc.Dropdown(
                                id="cet-year-select",
                                options=[{"label": str(y), "value": int(y)} for y in years],
                                value=[int(y) for y in default_years],
                                multi=True,
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
                            # later: info icon / tooltip could go here
                        ],
                    ),
                    dcc.Graph(id="cet-jan-dec-lines", style={"height": "55vh"}),
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
                            dmc.Title("3D view", order=4),
                        ],
                    ),
                    dcc.Graph(id="cet-3d-lines", style={"height": "55vh"}),
                ],
            ),
        ],
    )