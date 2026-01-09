from __future__ import annotations

import pandas as pd

# Canonical month order
MONTHS = [
    (1, "Jan"), (2, "Feb"), (3, "Mar"), (4, "Apr"), (5, "May"), (6, "Jun"),
    (7, "Jul"), (8, "Aug"), (9, "Sep"), (10, "Oct"), (11, "Nov"), (12, "Dec"),
]
MONTH_NUM_TO_ABBR = {m: abbr for m, abbr in MONTHS}
MONTH_ABBR_TO_NUM = {abbr.lower(): m for m, abbr in MONTHS}


def _normalize_start_month(start_month: str) -> int:
    sm = (start_month or "").strip().lower()
    if sm.isdigit():
        n = int(sm)
        if 1 <= n <= 12:
            return n
    if sm[:3] in MONTH_ABBR_TO_NUM:
        return MONTH_ABBR_TO_NUM[sm[:3]]
    raise ValueError(f"Unknown start_month={start_month!r}. Use 'Jan'..'Dec' or 1..12.")


def build_cycle_axis_labels(start_month: str) -> list[str]:
    start_num = _normalize_start_month(start_month)
    ordered = list(range(start_num, 13)) + list(range(1, start_num))
    return [MONTH_NUM_TO_ABBR[m] for m in ordered]


def prepare_cet_cycle(
    df_cet: pd.DataFrame,
    years_range: list[int],
    *,
    start_month: str = "Jan",
    start_offset: int = 0,
    use_cycle_year: bool = False,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Returns (dff, x_labels) where dff contains:
      - year, month, month_name, tmean_c
      - cycle_label (categorical x)
      - cycle_order (0..11 for sorting)
      - optionally cycle_year (for "Jul(-1) .. Jun(0)" season-year grouping)

    start_month:
      'Jan' -> Jan..Dec
      'Jul' -> Jul..Jun

    start_offset:
      Controls year label convention if you later use cycle_year.
      For example, with start_month='Jul':
        start_offset = 0  -> label by the year containing Jan..Jun (ending year)
        start_offset = -1 -> label by the year containing Jul..Dec (starting year)

    For now (overview spaghetti), cycle_year isn't required; grouping by 'year' is fine.
    """
    if not years_range:
        return pd.DataFrame(), build_cycle_axis_labels(start_month)

    cols = ["year", "month", "month_name", "tmean_c"]
    dff = df_cet[df_cet["year"].isin(years_range)][cols].copy()
    if dff.empty:
        return dff, build_cycle_axis_labels(start_month)

    start_num = _normalize_start_month(start_month)

    # cycle_order: 0..11 with start_month at 0
    # Example start_month=Jul(7): Jul->0 ... Dec->5, Jan->6 ... Jun->11
    dff["cycle_order"] = (dff["month"] - start_num) % 12

    # cycle_label: stable abbreviated labels in correct cyclic order
    x_labels = build_cycle_axis_labels(start_month)
    # month_name might already be 'Jan'.. 'Dec' — we use it, but ensure it matches x_labels
    # If month_name is full (e.g. January), switch to MONTH_NUM_TO_ABBR
    if not set(dff["month_name"].astype(str).str[:3].str.title()).issubset(set(MONTH_NUM_TO_ABBR.values())):
        dff["cycle_label"] = dff["month"].map(MONTH_NUM_TO_ABBR)
    else:
        dff["cycle_label"] = dff["month_name"].astype(str).str[:3].str.title()

    # Optional: a "cycle_year" for seasonal-year grouping (useful later for winter focus)
    if use_cycle_year:
        # Months BEFORE start_month belong to the *next* cycle year (ending-year convention)
        # e.g. start_month=Jul: Jan..Jun shift +1
        shift_next = (dff["month"] < start_num).astype(int)
        # start_offset lets you choose whether you want ending year (0) or starting year (-1) etc.
        dff["cycle_year"] = dff["year"] + shift_next + int(start_offset)

    return dff, x_labels