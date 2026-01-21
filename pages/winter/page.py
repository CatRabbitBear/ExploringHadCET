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
            dcc.Store(id="winter-step", storage_type="memory"),
            dcc.Store(id="winter-autoplay", storage_type="memory"),
            dcc.Store(id="winter-is-mobile", storage_type="memory"),

            # --- Intervals ---
            dcc.Interval(id="winter-init-tick", interval=50, n_intervals=0, max_intervals=1),
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
                            dmc.Text(id="winter-caption", size="sm", c="dimmed"),

                            dcc.Graph(id="winter-main-graph", className="graph-story"),

                            # --- Story controls (footer bar) ---
                            dmc.Group(
                                justify="space-between",
                                align="center",
                                mt="xs",
                                children=[
                                    dmc.Button("◀ Back", id="winter-btn-back", variant="subtle"),

                                    dmc.Text(id="winter-step-indicator", size="sm", c="dimmed"),

                                    dmc.Group(
                                        gap="xs",
                                        children=[
                                            dmc.Button("Next ▶", id="winter-btn-next", variant="filled"),
                                            dmc.Button("▶ Play", id="winter-btn-play", variant="light"),
                                            dmc.Button("Show final", id="winter-btn-final", variant="light"),
                                            dmc.Button("Resize y-axis", id="winter-btn-resize", variant="light"),
                                            dmc.Button("Reset ↺", id="winter-btn-reset", variant="subtle"),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    )
                ],
            ),
        ],
    )
