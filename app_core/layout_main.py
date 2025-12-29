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
            html.Div(
                [
                    html.Label("3D line mode:"),
                    dcc.Dropdown(
                        id="cet-3d-mode",
                        options=[
                            {"label": "Lines by year", "value": "by_year"},
                            {"label": "Lines by month", "value": "by_month"},
                        ],
                        value="by_year",
                        clearable=False,
                        style={"width": "220px", "marginRight": "1rem"},
                    ),
                    html.Label("Smoothing (years):"),
                    dcc.Dropdown(
                        id="cet-3d-smoothing",
                        options=[
                            {"label": "None", "value": 1},
                            {"label": "3-year", "value": 3},
                            {"label": "5-year", "value": 5},
                            {"label": "11-year", "value": 11},
                        ],
                        value=1,
                        clearable=False,
                        style={"width": "160px"},
                    ),
                ],
                style={"display": "flex", "alignItems": "center", "gap": "0.75rem", "marginBottom": "0.5rem"},
            ),
            dcc.Graph(
                id="cet-3d-lines",
                style={"height": "65vh"},
            ),
        ],
    )