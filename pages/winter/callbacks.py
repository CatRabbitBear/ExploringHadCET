from __future__ import annotations

from dash import Input, Output, State, no_update
import pandas as pd

from viz.figures.overview_2d import build_cet_2d_figure
from viz.figures.winter_boxes import build_winter_djf_boxplots
from viz.figures.winter_stats import compute_djf_bucket_stats
from viz.figures.winter_overlays import add_djf_brackets

from viz.figures.winter_layout_spec import BucketSpec
from viz.figures.winter_transition import build_winter_transition_figure


TRANSITION_START = 3
TRANSITION_FRAMES = 22
TRANSITION_END = TRANSITION_START + TRANSITION_FRAMES - 1
FINAL_STEP = TRANSITION_END + 1


def ease_in_out_cubic(t: float) -> float:
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2

def ease_in_cubic(t: float) -> float:
    return t * t * t

def _set_all_trace_opacity(fig, opacity: float) -> None:
    for tr in fig.data:
        tr.opacity = opacity


def _build_transition_specs(stats_df, buckets) -> list[BucketSpec]:
    specs: list[BucketSpec] = []
    n = len(buckets)
    if n == 0 or stats_df is None or stats_df.empty:
        return specs

    # Start all brackets at a single x, slightly right-shifted (~half-month feel)
    x_anchor = (n - 1) / 2.0
    # NOTE:
    # Plotly categorical axes reserve padding at both ends.
    # Empirically, the usable visual width behaves like (n + 1) slots,
    # so we offset by (n + 1)/24 to align with the perceived Jan centre.
    x_offset = (n + 1) / 24.0
    x_start = x_anchor + x_offset

    for i, b in enumerate(buckets):
        row = stats_df.loc[stats_df["bucket"] == b]
        if row.empty:
            continue

        min_y = float(row["min_djf"].iloc[0])
        max_y = float(row["max_djf"].iloc[0])

        q1 = float(row["q1"].iloc[0]) if "q1" in row.columns else None
        q3 = float(row["q3"].iloc[0]) if "q3" in row.columns else None
        med = float(row["median"].iloc[0]) if "median" in row.columns else None

        specs.append(
            BucketSpec(
                bucket=b,
                i=i,
                x_start=x_start,      # identical start x for all buckets
                x_end=float(i),       # land on bucket index
                min_y=min_y,
                max_y=max_y,
                q1_y=q1,
                median_y=med,
                q3_y=q3,
            )
        )

    return specs


def lock_camera(fig, *, y_range, uirev: str, lock_x_autorange: bool):
    # Keep view stable within a given axis-type "world"
    fig.update_layout(uirevision=uirev)

    # Y is numeric: truly lock it
    fig.update_yaxes(range=y_range, autorange=False, fixedrange=True)

    # X differs by plot type
    if lock_x_autorange:
        fig.update_xaxes(autorange=False, fixedrange=True)
    else:
        fig.update_xaxes(autorange=True, fixedrange=True)

    return fig


def register_winter_callbacks(app, df_cet: pd.DataFrame):
    years_all = sorted(df_cet["year"].unique().astype(int).tolist())
    min_year, max_year = years_all[0], years_all[-1]

    # --- 0) One-shot client-side mobile detection ---
    app.clientside_callback(
        """
        function(n) {
            const w = (typeof window !== "undefined") ? window.innerWidth : 1200;
            return w <= 768;
        }
        """,
        Output("winter-is-mobile", "data"),
        Input("winter-init-tick", "n_intervals"),
        prevent_initial_call=False,
    )

    # --- 1) Initialise mode ---
    @app.callback(
        Output("winter-autoplay", "data"),
        Output("winter-step", "data"),
        Output("winter-view-mode", "data"),
        Input("winter-is-mobile", "data"),
        State("winter-view-mode", "data"),
        prevent_initial_call=False,
    )
    def init_mode(is_mobile: bool | None, persisted_mode: str | None):
        if persisted_mode in ("guided", "final"):
            if persisted_mode == "final":
                return False, FINAL_STEP, "final"
            return False, 0, "guided"

        if is_mobile:
            return False, FINAL_STEP, "final"
        return False, 0, "guided"

    # --- 2) Buttons ---
    @app.callback(
        Output("winter-autoplay", "data", allow_duplicate=True),
        Output("winter-step", "data", allow_duplicate=True),
        Output("winter-view-mode", "data", allow_duplicate=True),
        Input("winter-btn-play", "n_clicks"),
        Input("winter-btn-final", "n_clicks"),
        Input("winter-btn-replay", "n_clicks"),
        State("winter-step", "data"),
        prevent_initial_call=True,
    )
    def handle_buttons(n_play, n_final, n_replay, step):
        from dash import ctx

        trigger = ctx.triggered_id
        step = int(step) if step is not None else 0

        if trigger == "winter-btn-final":
            return False, FINAL_STEP, "final"

        if trigger == "winter-btn-replay":
            return False, 0, "guided"

        if trigger == "winter-btn-play":
            if step >= FINAL_STEP:
                step = 0
            return True, step, "guided"

        return no_update, no_update, no_update

    # --- 3) Interval enable/disable ---
    @app.callback(
        Output("winter-tick", "disabled"),
        Input("winter-autoplay", "data"),
        prevent_initial_call=False,
    )
    def toggle_interval(autoplay: bool | None):
        return not bool(autoplay)

    # --- 4) Step advancement ---
    @app.callback(
        Output("winter-step", "data", allow_duplicate=True),
        Output("winter-autoplay", "data", allow_duplicate=True),
        Input("winter-tick", "n_intervals"),
        State("winter-autoplay", "data"),
        State("winter-step", "data"),
        prevent_initial_call=True,
    )
    def tick_step(n, autoplay: bool | None, step: int | None):
        if not autoplay:
            return no_update, no_update

        step = int(step) if step is not None else 0
        step_next = step + 1

        if step_next >= FINAL_STEP:
            return FINAL_STEP, False  # stop at final
        return step_next, True

    # --- 5) Render (Phase A -> Transition -> Phase B) ---
    @app.callback(
        Output("winter-main-graph", "figure"),
        Output("winter-caption", "children"),
        Input("winter-range-preset", "value"),
        Input("winter-bucket-mode", "value"),
        Input("winter-view-mode", "data"),
        Input("winter-step", "data"),
    )
    def render_winter(range_preset: str, bucket_mode: str, view_mode: str | None, step: int | None):
        # Range selection
        if range_preset == "modern":
            start, end = max(1950, min_year), max_year
        elif range_preset == "instrumental":
            start, end = max(1772, min_year), max_year
        elif range_preset == "full":
            start, end = min_year, max_year
        else:
            start, end = max(1950, min_year), max_year

        years_range = list(range(start, end + 1))

        # Bucket defaults
        if bucket_mode == "auto" or bucket_mode is None:
            bucket_mode_eff = "50y" if range_preset == "modern" else "century"
        else:
            bucket_mode_eff = bucket_mode

        view_mode = view_mode if view_mode in ("guided", "final") else "guided"
        step = int(step) if step is not None else (FINAL_STEP if view_mode == "final" else 0)

        # Global y-range for honesty (rescale is later)
        t_min = float(df_cet["tmean_c"].min())
        t_max = float(df_cet["tmean_c"].max())
        y_range = [t_min - 0.5, t_max + 0.5]

        # Captions
        captions = {
            0: "Step 0: Same data as the overview, re-framed Jul→Jun so winter (DJF) sits in the middle.",
            1: "Step 1: Coloured brackets show the coldest and warmest DJF month within each era bucket.",
            2: "Step 2: Focus on the winter brackets — the background context fades back.",
        }

        # Add one caption per transition frame (3..TRANSITION_END)
        for k in range(TRANSITION_START, TRANSITION_END + 1):
            frac = (k - TRANSITION_START + 1) / TRANSITION_FRAMES
            captions[k] = f"Step 2: Brackets separate into era buckets… ({int(frac * 100)}%)"

        captions[FINAL_STEP] = "Step 3: Final DJF boxplots by era (scale adjustment comes next)."
        caption = captions.get(step, captions[0])

        if view_mode == "final":
            step = FINAL_STEP

        # Shared stats (min/max + quartiles)
        stats_df, buckets = compute_djf_bucket_stats(df_cet, years_range, bucket_mode=bucket_mode_eff)
        specs = _build_transition_specs(stats_df, buckets)

        # --- Phase A ---
        if step <= 2:
            fig = build_cet_2d_figure(
                df_cet,
                years_range=years_range,
                highlight_year=end,
                compare_year=None,
                start_month="Jul",
                start_offset=-1,
            )
            fig.update_layout(title=None, showlegend=False)

            if step >= 1:
                fig = add_djf_brackets(fig, stats_df=stats_df, buckets=buckets, show_labels=True, label_every=1)

            if step == 2:
                _set_all_trace_opacity(fig, 0.08)

            fig = lock_camera(fig, y_range=y_range, uirev="winter_cat_v1", lock_x_autorange=False)
            return fig, caption

        # --- Transition ---
        if TRANSITION_START <= step <= TRANSITION_END:
            denom = max(1, (TRANSITION_FRAMES - 1))
            t = (step - TRANSITION_START) / denom
            # t = ease_in_out_cubic(t)
            t = ease_in_cubic(t)

            show_boxes = t >= 0.45
            show_fill = t >= 0.70

            fig_t = build_winter_transition_figure(
                specs=specs,
                t=t,
                y_range=y_range,
                show_boxes=show_boxes,
                show_fill=show_fill,
                show_median=True,
                bracket_alpha=0.95,
                box_line_alpha=0.95,
                box_fill_alpha=0.14,
            )
            fig_t = lock_camera(fig_t, y_range=y_range, uirev="winter_num_v1", lock_x_autorange=True)
            return fig_t, caption

        # --- Phase B final ---
        fig_b = build_winter_djf_boxplots(df_cet=df_cet, years_range=years_range, bucket_mode=bucket_mode_eff)
        fig_b.update_layout(title=None)
        fig_b = lock_camera(fig_b, y_range=y_range, uirev="winter_cat_v1", lock_x_autorange=False)
        return fig_b, caption

    # --- 6) Variable tick interval: fast during transition ---
    @app.callback(
        Output("winter-tick", "interval"),
        Input("winter-step", "data"),
        Input("winter-autoplay", "data"),
    )
    def set_tick_interval(step, autoplay):
        if not autoplay:
            return 900  # default (disabled anyway)

        step = int(step or 0)
        if TRANSITION_START <= step <= TRANSITION_END:
            return 120
        return 1200