from __future__ import annotations

import pandas as pd

DJF_MONTHS = {12, 1, 2}


def _bucket_sort_key(label: str) -> int:
    # "1700s" -> 1700, "1850–1899" -> 1850
    digits = ""
    for ch in label:
        if ch.isdigit():
            digits += ch
        elif digits:
            break
    return int(digits) if digits else 0


def bucket_label(year: int, mode: str, last_year_in_data: int) -> str:
    """
    Century buckets: '1700s'
    Span buckets: '1950–1999' with final bucket capped to last_year_in_data (e.g. '2000–2025').
    """
    year = int(year)
    last_year_in_data = int(last_year_in_data)

    if mode == "century":
        start = (year // 100) * 100
        return f"{start}s"

    if mode == "50y":
        span = 50
    elif mode == "25y":
        span = 25
    else:
        # fallback to century-like labeling
        start = (year // 100) * 100
        return f"{start}s"

    start = (year // span) * span
    end = min(start + span - 1, last_year_in_data)
    return f"{start}–{end}"


def compute_djf_bucket_stats(
    df_cet: pd.DataFrame,
    years_range: list[int],
    bucket_mode: str,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Returns:
      stats_df with columns: bucket, n, min_djf, max_djf
      buckets ordered list for consistent plotting/colouring
    """
    if not years_range:
        return pd.DataFrame(), []

    dff = df_cet[df_cet["year"].isin(years_range)][["year", "month", "tmean_c"]].copy()
    if dff.empty:
        return pd.DataFrame(), []

    dff = dff[dff["month"].isin(DJF_MONTHS)].copy()
    if dff.empty:
        return pd.DataFrame(), []

    last_year = max(years_range)

    dff["bucket"] = dff["year"].astype(int).map(lambda y: bucket_label(y, bucket_mode, last_year))

    stats = (
        dff.groupby("bucket")["tmean_c"]
        .agg(
            n="count",
            min_djf="min",
            max_djf="max",
            q1=lambda s: float(s.quantile(0.25)),
            median=lambda s: float(s.quantile(0.50)),
            q3=lambda s: float(s.quantile(0.75)),
        )
        .reset_index()
    )

    buckets = sorted(stats["bucket"].unique().tolist(), key=_bucket_sort_key)

    # Ensure stats sorted in same order
    stats["bucket_sort"] = stats["bucket"].map(_bucket_sort_key)
    stats = stats.sort_values("bucket_sort").drop(columns=["bucket_sort"])

    return stats, buckets