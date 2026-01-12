from dash import dcc
import dash_mantine_components as dmc
import pandas as pd


def get_winter_layout(df_cet: pd.DataFrame):
    years = sorted(df_cet["year"].unique().astype(int).tolist())
    min_year, max_year = years[0], years[-1]

    return dmc.Stack(
        gap="md",
        children=[
            dmc.Title("Winter in Focus", order=2),

            # --- Stores ---
            dcc.Store(id="winter-view-mode", storage_type="local"),   # "guided" | "final"
            dcc.Store(id="winter-step", storage_type="memory"),       # 0..3
            dcc.Store(id="winter-autoplay", storage_type="memory"),   # bool
            dcc.Store(id="winter-is-mobile", storage_type="memory"),  # bool
            dcc.Store(id="winter-tick-interval-ms", storage_type="memory"),

            # --- Intervals ---
            # Init tick runs once to detect mobile and initialise state
            dcc.Interval(id="winter-init-tick", interval=50, n_intervals=0, max_intervals=1),
            # Playback tick advances steps while autoplay is True
            dcc.Interval(id="winter-tick", interval=900, n_intervals=0, disabled=True),

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
                                            dmc.Text(
                                                "Same data as the overview, re-framed Jul→Jun so winter (DJF) sits in the middle.",
                                                size="sm",
                                                c="dimmed",
                                            ),
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

                            dmc.Divider(),

                            dmc.Group(
                                justify="space-between",
                                align="center",
                                children=[
                                    dmc.Text(f"Data range: {min_year}–{max_year}", size="xs", c="dimmed"),
                                    dmc.Group(
                                        gap="xs",
                                        children=[
                                            dmc.Button("Play", id="winter-btn-play", variant="filled"),
                                            dmc.Button("Show final boxplots", id="winter-btn-final", variant="light"),
                                            dmc.Button("Replay", id="winter-btn-replay", variant="subtle"),
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
                            dmc.Text(id="winter-caption", size="sm", c="dimmed"),
                            dcc.Graph(id="winter-main-graph", style={"height": "58vh"}),
                        ],
                    )
                ],
            ),
        ],
    )