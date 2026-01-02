from dash import html, dcc
import pandas as pd

def get_layout(df_cet: pd.DataFrame):
    years = sorted(df_cet["year"].unique())
    default_years = years[-20:] if len(years) > 20 else years

    return html.Div(
        style={"maxWidth": "1100px", "margin": "0 auto", "padding": "1rem"},
        children=[
            html.H1("Central England Temperature – Jan–Dec by Year"),

            html.Div(
                [
                    html.Label("Select years to display:"),
                    dcc.Dropdown(
                        id="cet-year-select",
                        options=[{"label": str(y), "value": int(y)} for y in years],
                        value=[int(y) for y in default_years],
                        multi=True,
                    ),
                ],
                style={"marginBottom": "1rem"},
            ),

            html.H3("2D view"),
            dcc.Graph(
                id="cet-jan-dec-lines",
                style={"height": "55vh"},
            ),

            html.H3("3D view"),

            dcc.Graph(
                id="cet-3d-lines",
                style={"height": "55vh"},
            )
        ],
    )