from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

# LOESS (statsmodels)
from statsmodels.nonparametric.smoothers_lowess import lowess

from .config import BASELINES, MONTH_NAME_BY_NUM, LOESS_FRAC, LOESS_SUFFIX


REQUIRED_COLUMNS = [
    # identity / time
    "date",
    "year",
    "month",
    "month_name",
    "season",
    "winter_year",
    "decade",
    "period_bin",
    # observed
    "tmean_c",
    # baseline + anomaly
    "tmean_base_1961_1990_c",
    "tmean_anom_1961_1990_c",
    # smoothing
    "tmean_loess_0p07_c",
    "tmean_resid_loess_0p07_c",
]


def season_from_month(m: int) -> str:
    # DJF / MAM / JJA / SON
    if m in (12, 1, 2):
        return "DJF"
    if m in (3, 4, 5):
        return "MAM"
    if m in (6, 7, 8):
        return "JJA"
    return "SON"


def compute_winter_year(year: int, month: int) -> int:
    # Dec belongs to following winter_year
    return year + 1 if month == 12 else year


def period_bin_for_year(y: int) -> str:
    """
    Simple, explainable comparison bins (edit as you like).
    Keep it stable so charts don’t jump around.
    """
    if y <= 1699:
        return "1659–1699"
    if y <= 1799:
        return "1700–1799"
    if y <= 1899:
        return "1800–1899"
    if y <= 1949:
        return "1900–1949"
    if y <= 1999:
        return "1950–1999"
    return "2000–present"


def add_monthly_baseline_anomalies(
    df: pd.DataFrame,
    value_col: str,
    out_prefix: str,
) -> pd.DataFrame:
    """
    Adds month-specific climatology means and anomalies for each baseline period.

    Example outputs for value_col="tmean_c", out_prefix="tmean":
      - tmean_anom_1961_1990_c
      - tmean_base_1961_1990_c (optional but handy for debugging)
    """
    out = df.copy()

    for baseline_id, (y0, y1) in BASELINES.items():
        mask = out["year"].between(y0, y1)
        base = (
            out.loc[mask]
            .groupby("month")[value_col]
            .mean()
            .rename(f"{out_prefix}_base_{baseline_id}")
        )

        out = out.merge(base, on="month", how="left")

        # anomaly = value - monthly baseline
        out[f"{out_prefix}_anom_{baseline_id}"] = (
            out[value_col] - out[f"{out_prefix}_base_{baseline_id}"]
        )

    for baseline_id in BASELINES.keys():
        out = out.rename(
            columns={
                f"tmean_base_{baseline_id}": f"tmean_base_{baseline_id}_c",
                f"tmean_anom_{baseline_id}": f"tmean_anom_{baseline_id}_c",
            }
        )

    return out


def add_loess_per_month(
    df: pd.DataFrame,
    value_col: str,
) -> pd.DataFrame:
    """
    Applies LOWESS separately per calendar month over year.
    Writes fitted series back as a column aligned to original rows.
    """
    frac = LOESS_FRAC
    loess_col = f"tmean_loess_{LOESS_SUFFIX}_c"
    out = df.copy()
    out[loess_col] = np.nan

    # Ensure numeric
    years_all = out["year"].to_numpy(dtype=float)

    for m in range(1, 13):
        sub_idx = out.index[out["month"] == m].to_numpy()
        sub = out.loc[sub_idx, ["year", value_col]].dropna()

        if sub.empty:
            continue

        years = sub["year"].to_numpy(dtype=float)
        vals = sub[value_col].to_numpy(dtype=float)

        # Normalise x for numerical stability
        x_norm = (years - years.min()) / (years.max() - years.min() or 1.0)

        smoothed = lowess(
            endog=vals,
            exog=x_norm,
            frac=frac,
            it=3,
            return_sorted=False,
        )

        # Clamp within observed month range to avoid invented extremes
        smoothed = np.clip(smoothed, vals.min(), vals.max())

        # Write back aligned by (year, month)
        # Build a small mapping year->smooth for this month
        smooth_map = dict(zip(sub["year"].astype(int).to_list(), smoothed.tolist()))
        for i in sub_idx:
            y = int(out.at[i, "year"])
            if y in smooth_map:
                out.at[i, loess_col] = float(smooth_map[y])

    out[f"tmean_resid_loess_{LOESS_SUFFIX}_c"] = out["tmean_c"] - out[loess_col]

    return out


def add_time_and_labels(df: pd.DataFrame) -> pd.DataFrame:
    # Basic tidy columns (same as before)
    df["month_name"] = df["month"].map(MONTH_NAME_BY_NUM)
    df["date"] = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1))
    df["season"] = df["month"].apply(season_from_month)
    df["winter_year"] = [
        compute_winter_year(y, m) for y, m in zip(df["year"], df["month"])
    ]
    df["decade"] = (df["year"] // 10) * 10
    df["period_bin"] = df["year"].apply(period_bin_for_year)

    df = df.sort_values(["year", "month"]).reset_index(drop=True)

    return df


def schema_assert(
    df: pd.DataFrame,
    *,
    required_columns: Iterable[str] = REQUIRED_COLUMNS,
    allow_extra_columns: bool = True,
) -> None:
    """
    Assert that df conforms to the minimum expected CET monthly feature schema.

    This is intentionally permissive:
      - requires AT LEAST the required columns
      - allows extra columns (for transition / refactor phase)

    Raises AssertionError on hard failures.
    """

    # -------------------------
    # Column presence
    # -------------------------
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise AssertionError(f"Missing required columns: {missing}")

    if not allow_extra_columns:
        extra = [c for c in df.columns if c not in required_columns]
        if extra:
            raise AssertionError(f"Unexpected extra columns: {extra}")

    # -------------------------
    # Row-level integrity
    # -------------------------
    if df.empty:
        raise AssertionError("DataFrame is empty")

    # (year, month) uniqueness
    if df.duplicated(subset=["year", "month"]).any():
        dupes = df[df.duplicated(subset=["year", "month"], keep=False)]
        raise AssertionError(
            f"Duplicate (year, month) rows detected:\n{dupes[['year','month']].head()}"
        )

    # -------------------------
    # Basic type / range checks
    # -------------------------
    # month range
    if not df["month"].between(1, 12).all():
        bad = df.loc[~df["month"].between(1, 12), ["year", "month"]]
        raise AssertionError(f"Invalid month values detected:\n{bad.head()}")

    # year sanity (loose bounds)
    if df["year"].min() < 1500 or df["year"].max() > 3000:
        raise AssertionError(
            f"Year range looks implausible: {df['year'].min()}–{df['year'].max()}"
        )

    # tmean_c must be finite
    # tmean_c: allow NaN, but forbid +/- inf
    t = df["tmean_c"].to_numpy(dtype=float)

    if np.isinf(t).any():
        bad = df.loc[np.isinf(df["tmean_c"]), ["year", "month", "tmean_c"]]
        raise AssertionError(f"Infinite tmean_c values:\n{bad.head()}")

    # Optional: warn if missing values exist (don’t fail in this phase)
    n_missing = int(pd.isna(df["tmean_c"]).sum())
    if n_missing:
        print(
            f"[schema_assert] WARN | tmean_c has {n_missing} missing values (NaN allowed in this phase)"
        )

    # -------------------------
    # Derived column sanity
    # -------------------------
    # date alignment (month start)
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        raise AssertionError("Column 'date' must be datetime64")

    if not (df["date"].dt.day == 1).all():
        raise AssertionError("Column 'date' must be first day of month")

    # winter_year logic: Dec -> year+1, else year
    expected_wy = np.where(df["month"] == 12, df["year"] + 1, df["year"])
    if not (df["winter_year"].to_numpy() == expected_wy).all():
        bad = df.loc[df["winter_year"] != expected_wy, ["year", "month", "winter_year"]]
        raise AssertionError(f"winter_year mismatch detected:\n{bad.head()}")

    # anomaly consistency: check only where all operands exist
    m = (
        df[["tmean_c", "tmean_base_1961_1990_c", "tmean_anom_1961_1990_c"]]
        .notna()
        .all(axis=1)
    )

    if m.any():
        diff = (
            df.loc[m, "tmean_c"]
            - df.loc[m, "tmean_base_1961_1990_c"]
            - df.loc[m, "tmean_anom_1961_1990_c"]
        )

        if not np.allclose(diff.to_numpy(dtype=float), 0.0, atol=1e-6):
            # show a couple of offending rows for fast debugging
            bad = df.loc[m].loc[
                ~np.isclose(diff, 0.0, atol=1e-6),
                [
                    "year",
                    "month",
                    "tmean_c",
                    "tmean_base_1961_1990_c",
                    "tmean_anom_1961_1990_c",
                ],
            ]
            raise AssertionError(
                f"Anomaly consistency failed on non-NaN rows:\n{bad.head()}"
            )

    m = (
        df[["tmean_c", "tmean_loess_0p07_c", "tmean_resid_loess_0p07_c"]]
        .notna()
        .all(axis=1)
    )
    if m.any():
        diff = (
            df.loc[m, "tmean_c"]
            - df.loc[m, "tmean_loess_0p07_c"]
            - df.loc[m, "tmean_resid_loess_0p07_c"]
        )
        if not np.allclose(diff.to_numpy(dtype=float), 0.0, atol=1e-6):
            bad = df.loc[m].loc[
                ~np.isclose(diff, 0.0, atol=1e-6),
                [
                    "year",
                    "month",
                    "tmean_c",
                    "tmean_loess_0p07_c",
                    "tmean_resid_loess_0p07_c",
                ],
            ]
            raise AssertionError(
                f"LOESS residual consistency failed on non-NaN rows:\n{bad.head()}"
            )

    # -------------------------
    # Lightweight diagnostics (non-fatal, but useful)
    # -------------------------
    print(
        f"[schema_assert] OK | rows={len(df):,} "
        f"years={df['year'].min()}–{df['year'].max()} "
        f"mean={df['tmean_c'].mean():.2f}°C "
        f"std={df['tmean_c'].std():.2f}°C"
    )
