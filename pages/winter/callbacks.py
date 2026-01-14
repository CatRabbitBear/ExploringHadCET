from __future__ import annotations

from dash import Input, Output, State, no_update
import pandas as pd

from viz.figures.overview_2d import build_cet_2d_figure
from viz.figures.winter_boxes import build_winter_djf_boxplots
from viz.figures.winter_stats import compute_djf_bucket_stats
from viz.figures.winter_overlays import add_djf_brackets, add_first_bracket_explainers

from viz.figures.winter_layout_spec import BucketSpec
from viz.figures.winter_transition import build_winter_transition_figure


# --- Phase structure ---
PHASE_A_END = 2                         # 0..2
TRANSITION_START = PHASE_A_END + 1       # "ready" gate (button shows here) + first transition frame when autoplay starts
TRANSITION_FRAMES = 22
TRANSITION_END = TRANSITION_START + TRANSITION_FRAMES - 1

FINAL_RAW = TRANSITION_END + 1           # completed boxplots, global y-axis (no zoom)
FINAL_RESIZED = FINAL_RAW + 1            # completed boxplots, zoomed y-axis


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

    x_anchor = (n - 1) / 2.0
    # Plotly categorical padding compensation: (n + 1) behaved best empirically
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
                x_start=x_start,
                x_end=float(i),
                min_y=min_y,
                max_y=max_y,
                q1_y=q1,
                median_y=med,
                q3_y=q3,
            )
        )

    return specs


def lock_camera(fig, *, y_range, uirev: str, lock_x_autorange: bool):
    fig.update_layout(uirevision=uirev)
    fig.update_yaxes(range=y_range, autorange=False, fixedrange=True)

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
                return False, FINAL_RESIZED, "final"
            return False, 0, "guided"

        if is_mobile:
            return False, FINAL_RESIZED, "final"
        return False, 0, "guided"

    # --- 2) Footer bar buttons: Back / Next / Play / Final / Resize / Reset ---
    @app.callback(
        Output("winter-autoplay", "data", allow_duplicate=True),
        Output("winter-step", "data", allow_duplicate=True),
        Output("winter-view-mode", "data", allow_duplicate=True),
        Input("winter-btn-back", "n_clicks"),
        Input("winter-btn-next", "n_clicks"),
        Input("winter-btn-play", "n_clicks"),
        Input("winter-btn-final", "n_clicks"),
        Input("winter-btn-resize", "n_clicks"),   # NEW BUTTON
        Input("winter-btn-reset", "n_clicks"),
        State("winter-step", "data"),
        prevent_initial_call=True,
    )
    def handle_footer_buttons(n_back, n_next, n_play, n_final, n_resize, n_reset, step):
        from dash import ctx

        trigger = ctx.triggered_id
        step = int(step) if step is not None else 0

        if trigger == "winter-btn-reset":
            return False, 0, "guided"

        # "Show final" always means the resized final (for mobile / skip)
        if trigger == "winter-btn-final":
            return False, FINAL_RESIZED, "final"

        # Resize button upgrades raw-final -> resized-final
        if trigger == "winter-btn-resize":
            return False, FINAL_RESIZED, "guided"

        if trigger == "winter-btn-back":
            return False, max(0, step - 1), "guided"

        if trigger == "winter-btn-next":
            # Step forward through Phase A only and stop at the gate
            next_step = min(TRANSITION_START, step + 1)
            return False, next_step, "guided"

        if trigger == "winter-btn-play":
            # Start autoplay from the transition start, regardless of current step
            return True, TRANSITION_START, "guided"

        return no_update, no_update, no_update

    # --- 3) Interval enable/disable ---
    @app.callback(
        Output("winter-tick", "disabled"),
        Input("winter-autoplay", "data"),
        prevent_initial_call=False,
    )
    def toggle_interval(autoplay: bool | None):
        return not bool(autoplay)

    # --- 4) Step advancement while autoplay is on ---
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

        step = int(step) if step is not None else TRANSITION_START
        step_next = step + 1

        # End autoplay by landing on the completed boxplots (GLOBAL y-axis)
        if step_next >= TRANSITION_END:
            return FINAL_RAW, False

        return step_next, True

    # --- 5) Control bar state (show/hide/disable + indicator text) ---
    @app.callback(
        Output("winter-btn-back", "disabled"),
        Output("winter-btn-next", "style"),
        Output("winter-btn-play", "style"),
        Output("winter-btn-resize", "style"),   # NEW
        Output("winter-btn-reset", "style"),
        Output("winter-step-indicator", "children"),
        Input("winter-step", "data"),
        Input("winter-autoplay", "data"),
        Input("winter-view-mode", "data"),
        prevent_initial_call=False,
    )
    def update_controls(step, autoplay, view_mode):
        step = int(step or 0)
        autoplay = bool(autoplay)
        view_mode = view_mode if view_mode in ("guided", "final") else "guided"

        style_show = {"display": "inline-flex"}
        style_hide = {"display": "none"}

        # Back disabled only at very start
        back_disabled = (step <= 0)

        # Primary controls
        show_next = (step < TRANSITION_START) and (not autoplay) and (view_mode != "final")
        show_play = (step == TRANSITION_START) and (not autoplay) and (view_mode != "final")

        # Resize shows when animation has finished but y-axis isn't zoomed yet
        show_resize = (step == FINAL_RAW) and (not autoplay) and (view_mode != "final")

        # Reset shows after playback starts, or when you're at either final step, or in summary view
        show_reset = autoplay or (step >= FINAL_RAW) or (view_mode == "final")

        next_style = style_show if show_next else style_hide
        play_style = style_show if show_play else style_hide
        resize_style = style_show if show_resize else style_hide
        reset_style = style_show if show_reset else style_hide

        # Indicator
        if view_mode == "final":
            indicator = "Summary view"
        elif autoplay:
            indicator = "Playing…"
        else:
            if step < TRANSITION_START:
                indicator = f"Step {step + 1} of {PHASE_A_END + 1}"
            elif step == TRANSITION_START:
                indicator = "Ready to animate"
            elif TRANSITION_START <= step <= TRANSITION_END:
                pct = int(100 * (step - TRANSITION_START) / max(1, (TRANSITION_FRAMES - 1)))
                indicator = f"Animating… {pct}%"
            elif step == FINAL_RAW:
                indicator = "Boxplots ready"
            else:
                indicator = "Zoomed view"

        return back_disabled, next_style, play_style, resize_style, reset_style, indicator

    # --- 6) Variable tick interval: fast during transition ---
    @app.callback(
        Output("winter-tick", "interval"),
        Input("winter-step", "data"),
        Input("winter-autoplay", "data"),
        prevent_initial_call=False,
    )
    def set_tick_interval(step, autoplay):
        if not autoplay:
            return 900

        step = int(step or TRANSITION_START)
        if TRANSITION_START <= step <= TRANSITION_END:
            return 120
        return 900

    # --- 7) Render ---
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
        step = int(step) if step is not None else (FINAL_RESIZED if view_mode == "final" else 0)
        if view_mode == "final":
            step = FINAL_RESIZED

        # Global y-range for honesty (zoom is a later explicit step)
        t_min = float(df_cet["tmean_c"].min())
        t_max = float(df_cet["tmean_c"].max())
        y_range = [t_min - 0.5, t_max + 0.5]

        # Shared stats (min/max + quartiles)
        stats_df, buckets = compute_djf_bucket_stats(df_cet, years_range, bucket_mode=bucket_mode_eff)
        specs = _build_transition_specs(stats_df, buckets)

        # Captions
        if step == 0:
            caption = "Step 1: Same data as the overview, re-framed Jul→Jun so winter (DJF) sits in the middle."
        elif step == 1:
            caption = "Step 2: One bracket summarises winter range: warmest and coldest DJF month in that era."
        elif step == 2:
            caption = "Step 3: Add all era brackets so you can compare winter ranges over time."
        elif step == TRANSITION_START:
            caption = "Ready: press Play to see brackets separate into eras and evolve into boxplots."
        elif TRANSITION_START <= step <= TRANSITION_END:
            caption = "Now the brackets separate into era buckets and evolve into boxplots."
        elif step == FINAL_RAW:
            caption = "Boxplots complete. Optional: resize the y-axis to remove empty space."
        else:
            caption = "Final: DJF boxplots by era (y-axis zoomed to winter range)."

        # --- Phase A ---
        if step <= PHASE_A_END:
            fig = build_cet_2d_figure(
                df_cet,
                years_range=years_range,
                highlight_year=None,
                compare_year=None,
                start_month="Jul",
                start_offset=-1,
            )
            fig.update_layout(title=None, showlegend=False)

            if step >= 1:
                # first bucket bracket + explainers
                fig = add_djf_brackets(
                    fig,
                    stats_df=stats_df,
                    buckets=buckets,
                    show_labels=True,
                    label_every=1,
                    max_buckets=1,
                )
                fig = add_first_bracket_explainers(fig, stats_df=stats_df, buckets=buckets)

            if step >= 2:
                fig = add_djf_brackets(fig, stats_df=stats_df, buckets=buckets, show_labels=True, label_every=1)
                _set_all_trace_opacity(fig, 0.15)

            fig = lock_camera(fig, y_range=y_range, uirev="winter_cat_v1", lock_x_autorange=False)
            return fig, caption

        # --- Ready gate (no animation yet, just lets Play appear) ---
        if step == TRANSITION_START and step not in range(TRANSITION_START, TRANSITION_END + 1):
            # This branch is mostly defensive; in practice TRANSITION_START is also the first transition frame.
            pass

        # --- Transition ---
        if TRANSITION_START <= step <= TRANSITION_END:
            denom = max(1, (TRANSITION_FRAMES - 1))
            t = (step - TRANSITION_START) / denom
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

        # --- Phase B: raw final (global y-axis) OR resized final (winter-only y-axis) ---
        fig_b = build_winter_djf_boxplots(df_cet=df_cet, years_range=years_range, bucket_mode=bucket_mode_eff)
        fig_b.update_layout(title=None)

        # Raw final keeps the global y-axis (so it visually matches the end of the transition)
        if step == FINAL_RAW:
            fig_b = lock_camera(fig_b, y_range=y_range, uirev="winter_cat_v1", lock_x_autorange=False)
            return fig_b, caption

        # Resized final (winter-only range)
        winter_min = float(stats_df["min_djf"].min())
        winter_max = float(stats_df["max_djf"].max())
        pad = 0.6
        winter_range = [winter_min - pad, winter_max + pad]

        fig_b.update_layout(uirevision="winter_cat_v1")
        fig_b.update_yaxes(range=winter_range, autorange=False, fixedrange=True)
        fig_b.update_xaxes(autorange=True, fixedrange=True)

        return fig_b, caption