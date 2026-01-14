from __future__ import annotations

from dash import Input, Output

from viz.figures.cet_loess_topdown import build_cet_loess_topdown_figure
from viz.figures.rainfall_heatmap import build_rainfall_heatmap_figure


def register_rainfall_callbacks(app, df_cet):
    @app.callback(
        Output("loess-topdown", "figure"),
        Input("rainfall-col", "value"),  # unused, but keeps the two charts feeling “linked”
    )
    def _update_loess_topdown(_):
        # You can later add UI controls for baseline selection or contour toggle if you want.
        return build_cet_loess_topdown_figure(
            df_cet,
            loess_col="tmean_loess_0p07_c",
            baseline_col="tmean_base_1961_1990_c",
            anomaly_col=None,
            show_contours=True,
        )

    @app.callback(
        Output("rainfall-heatmap", "figure"),
        Input("rainfall-col", "value"),
        Input("rainfall-assume-anom", "checked"),
    )
    def _update_rainfall_heatmap(col, assume_anom):
        title = f"Heatmap: {col}"
        return build_rainfall_heatmap_figure(
            df_cet,
            value_col=col,
            title=title,
            assume_anomaly=bool(assume_anom),
            symmetric_anomaly_bounds=True,
        )