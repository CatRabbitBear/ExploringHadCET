from __future__ import annotations

from dash import Input, Output

from viz.figures.cet_loess_topdown import build_cet_loess_topdown_figure
from viz.figures.rainfall_heatmap import build_rainfall_heatmap_figure
from app_core.view_range import get_view_range


def register_rainfall_callbacks(app, df_cet):
    years_all = sorted(df_cet["year"].unique().astype(int).tolist())
    min_year, max_year = years_all[0], years_all[-1]

    @app.callback(
        Output("loess-topdown", "figure"),
        Input("rainfall-col", "value"),  # unused, but keeps the two charts feeling "linked"
        Input("global-view-range", "data"),
    )
    def _update_loess_topdown(_, view_range_data):
        view_range = get_view_range(view_range_data, min_year=min_year, max_year=max_year)
        df_view = df_cet[
            (df_cet["year"].astype(int) >= view_range.start_year)
            & (df_cet["year"].astype(int) <= view_range.end_year)
        ]
        # You can later add UI controls for baseline selection or contour toggle if you want.
        return build_cet_loess_topdown_figure(
            df_view,
            loess_col="tmean_loess_0p07_c",
            baseline_col="tmean_base_1961_1990_c",
            anomaly_col=None,
            show_contours=True,
        )

    @app.callback(
        Output("rainfall-heatmap", "figure"),
        Input("rainfall-col", "value"),
        Input("rainfall-assume-anom", "checked"),
        Input("global-view-range", "data"),
    )
    def _update_rainfall_heatmap(col, assume_anom, view_range_data):
        view_range = get_view_range(view_range_data, min_year=min_year, max_year=max_year)
        df_view = df_cet[
            (df_cet["year"].astype(int) >= view_range.start_year)
            & (df_cet["year"].astype(int) <= view_range.end_year)
        ]
        title = f"Heatmap: {col}"
        return build_rainfall_heatmap_figure(
            df_view,
            value_col=col,
            title=title,
            assume_anomaly=bool(assume_anom),
            symmetric_anomaly_bounds=True,
        )
