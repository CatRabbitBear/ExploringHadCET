from __future__ import annotations

from dash import dcc, html
import dash_mantine_components as dmc


RAIN_COL_OPTIONS = [
    ("prcp_mm", "Rainfall (mm)"),
    ("prcp_base_1961_1990_mm", "Rainfall baseline 1961–1990 (mm)"),
    ("prcp_anom_1961_1990_mm", "Rainfall anomaly vs 1961–1990 (mm)"),
    ("prcp_base_1881_1910_mm", "Rainfall baseline 1881–1910 (mm)"),
    ("prcp_anom_1881_1910_mm", "Rainfall anomaly vs 1881–1910 (mm)"),
]


def get_rainfall_layout() -> html.Div:
    return html.Div(
        [
            dmc.Stack(
                [
                    dmc.Title("Rainfall", order=2),

                    dmc.Text(
                        "A quick visual test: if nothing jumps out in ~10 seconds, "
                        "rainfall may simply be too noisy at monthly scale — except possibly in winter.",
                        size="sm",
                        c="dimmed",
                    ),

                    dmc.Group(
                        [
                            dmc.Select(
                                id="rainfall-col",
                                label="Rainfall column",
                                value="prcp_mm",
                                data=[{"value": v, "label": lbl} for v, lbl in RAIN_COL_OPTIONS],
                                w=340,
                                searchable=False,
                                clearable=False,
                            ),
                            dmc.Switch(
                                id="rainfall-assume-anom",
                                label="Treat selected column as anomaly (diverging scale)",
                                checked=False,
                                mt=22,
                            ),
                        ],
                        align="flex-end",
                        gap="md",
                    ),

                    dmc.SimpleGrid(
                        cols=2,
                        spacing="md",
                        # breakpoints=[
                        #     {"maxWidth": 1100, "cols": 1},
                        # ],
                        children=[
                            dmc.Card(
                                withBorder=True,
                                radius="md",
                                p="md",
                                children=[
                                    dmc.Text("LOESS top-down (anomaly colours + optional contours)", fw=600, mb="xs"),
                                    dcc.Graph(
                                        id="loess-topdown",
                                        config={"displayModeBar": False},
                                        style={"height": "520px"},
                                    ),
                                ],
                            ),
                            dmc.Card(
                                withBorder=True,
                                radius="md",
                                p="md",
                                children=[
                                    dmc.Text("Rainfall heatmap", fw=600, mb="xs"),
                                    dcc.Graph(
                                        id="rainfall-heatmap",
                                        config={"displayModeBar": False},
                                        style={"height": "520px"},
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
                gap="md",
            )
        ],
        style={"padding": "12px"},
    )