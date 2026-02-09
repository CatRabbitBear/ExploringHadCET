import pandas as pd
from dash import Input, Output

from app_core.view_range import get_view_range
from pages.overview.skeletons import (
    PAGE_SKELETON_HIDDEN_STYLE,
    PAGE_SKELETON_OVERLAY_ID,
    SKELETON_2D_ID,
    SKELETON_3D_ID,
)
from viz.figures.overview_2d import build_cet_2d_figure
from viz.figures.overview_3d import build_cet_3d_figure


def register_overview_callbacks(app, df_cet: pd.DataFrame):
    years_all = sorted(df_cet["year"].unique().astype(int).tolist())
    min_year, max_year = years_all[0], years_all[-1]

    app.clientside_callback(
        """
        function(n) {
            const w = (typeof window !== "undefined") ? window.innerWidth : 1200;
            return w <= 768;
        }
        """,
        Output("overview-is-mobile", "data"),
        Input("overview-init-tick", "n_intervals"),
        prevent_initial_call=False,
    )

    @app.callback(
        Output("cet-highlight-year", "style"),
        Input("cet-highlight-mode", "value"),
    )
    def toggle_custom_year(mode: str):
        return {"display": "block"} if mode == "custom" else {"display": "none"}

    @app.callback(
        Output("cet-jan-dec-lines", "figure"),
        Output("cet-3d-lines", "figure"),
        Output(PAGE_SKELETON_OVERLAY_ID, "style"),
        Input("overview-is-mobile", "data"),
        Input("global-view-range", "data"),
        Input("cet-highlight-mode", "value"),
        Input("cet-highlight-year", "value"),
        running=[
            (Output(SKELETON_2D_ID, "visible"), True, False),
            (Output(SKELETON_3D_ID, "visible"), True, False),
        ],
    )
    def update_overview(
        is_mobile: bool | None,
        view_range_data,
        highlight_mode: str,
        highlight_year_value: str | None,
    ):
        is_mobile = bool(is_mobile)
        view_range = get_view_range(
            view_range_data, min_year=min_year, max_year=max_year
        )
        start, end = view_range.start_year, view_range.end_year

        years_range = list(range(start, end + 1))
        years_set = set(years_range)

        # --- highlight selection ---
        def clamp_to_range(y: int) -> int:
            if y in years_set:
                return y
            # clamp to nearest in-range end
            return end if y > end else start

        if highlight_mode == "previous":
            highlight_year = clamp_to_range(end - 1)
            compare_year = clamp_to_range(end)  # compare against latest
        elif highlight_mode == "reference":
            # Choose a clear reference year and clamp to available range
            ref = 1961
            highlight_year = clamp_to_range(ref)
            compare_year = clamp_to_range(end)  # compare reference to latest
        elif highlight_mode == "custom":
            try:
                y = (
                    int(highlight_year_value)
                    if highlight_year_value is not None
                    else end
                )
            except ValueError:
                y = end
            highlight_year = clamp_to_range(y)
            compare_year = None
        else:
            # latest
            highlight_year = end
            compare_year = clamp_to_range(end - 1)

        fig_2d = build_cet_2d_figure(
            df_cet,
            years_range=years_range,
            highlight_year=highlight_year,
            compare_year=compare_year,
            show_legend=not is_mobile,
            start_month="Jan",
            start_offset=0,
        )
        fig_3d = build_cet_3d_figure(df_cet, years_range, show_colorbar=not is_mobile)

        return fig_2d, fig_3d, PAGE_SKELETON_HIDDEN_STYLE
