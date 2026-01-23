from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Iterable

import numpy as np
import pandas as pd
import re

# LOESS (statsmodels)
from statsmodels.nonparametric.smoothers_lowess import lowess

from data.config import (
    # CLIMATE_DB_PATH,
    MONTHLY_FEATURES_PATH,
    HADCET_RAW_MONTHLY_PATH,  # to be used instead of db
)

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

MONTH_COLS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
MONTH_NAME_BY_NUM = {i + 1: name for i, name in enumerate(MONTH_COLS)}

# Locked baselines (full years, 30y each)
BASELINES: Dict[str, Tuple[int, int]] = {
    "1961_1990": (1961, 1990),
}

# LOESS config (lock for v1)
LOESS_FRAC = 0.07
LOESS_SUFFIX = "0p07"  # used in column names

MISSING_SENTINELS = {"-99.9", "-99.99", "-999", "-999.0", "NA", "N/A", "***", "*", ""}


def parse_value(token: str) -> float | None:
    t = token.strip()
    if t in MISSING_SENTINELS:
        return np.nan
    v = float(t)
    # Treat numeric sentinels like -99.900 as missing too
    if abs(v + 99.9) < 1e-9 or abs(v + 99.99) < 1e-9:
        return np.nan
    if abs(v + 999.0) < 1e-9:
        return np.nan
    return v


def _find_header_and_data_lines(text: str) -> list[str]:
    """
    Return only true data rows:
      Year + 12 month values + Annual
    Avoids header lines like '1974 on Parker et al.'
    """
    lines = [ln.rstrip("\n") for ln in text.splitlines()]
    data_lines: list[str] = []

    for ln in lines:
        s = ln.strip()
        if not re.match(r"^\d{4}\s+", s):
            continue

        parts = re.split(r"\s+", s)

        # Must be: Year + 12 months + Annual = 14 tokens minimum
        if len(parts) < 14:
            continue

        try:
            int(parts[0])
            for tok in parts[1:14]:
                _ = parse_value(tok)  # may be NaN
        except ValueError:
            continue

        data_lines.append(ln)

    if not data_lines:
        raise ValueError(
            "No data lines found matching: YEAR + 12 monthly values + Annual."
        )
    return data_lines


def read_hadcet_monthly_txt(path: Path) -> pd.DataFrame:
    """
    Parses HadCET-style wide table into long monthly DF:
      year, month, tmean_c
    Sentinel missing values become NaN.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    data_lines = _find_header_and_data_lines(text)

    rows = []
    for ln in data_lines:
        parts = re.split(r"\s+", ln.strip())
        year = int(parts[0])
        month_vals = parts[1:13]  # Jan..Dec
        # parts[13] is annual, ignore for now

        for i, tok in enumerate(month_vals, start=1):
            rows.append((year, i, parse_value(tok)))

    df = pd.DataFrame(rows, columns=["year", "month", "tmean_c"])
    df = df.sort_values(["year", "month"]).reset_index(drop=True)
    return df


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


# def read_monthly_tables(conn: sqlite3.Connection) -> pd.DataFrame:
#     """
#     Load temp and rainfall raw tables into one long monthly dataframe.
#     Rainfall is left-joined and may be NULL prior to 1873.
#     """
#     df_t = pd.read_sql_query(
#         """
#         SELECT year, month, tmean_c
#         FROM hadcet_tmean_monthly_raw
#         ORDER BY year, month
#         """,
#         conn,
#     )

#     df_p = pd.read_sql_query(
#         """
#         SELECT year, month, prcp_mm
#         FROM hadukp_prcp_monthly_raw
#         ORDER BY year, month
#         """,
#         conn,
#     )

#     # Left join rainfall onto temperature
#     df = df_t.merge(df_p, on=["year", "month"], how="left")

#     # Basic tidy columns
#     df["month_name"] = df["month"].map(MONTH_NAME_BY_NUM)
#     df["date"] = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1))
#     df["season"] = df["month"].apply(season_from_month)
#     df["winter_year"] = [
#         compute_winter_year(y, m) for y, m in zip(df["year"], df["month"])
#     ]
#     df["decade"] = (df["year"] // 10) * 10
#     df["period_bin"] = df["year"].apply(period_bin_for_year)

#     # Sort
#     df = df.sort_values(["year", "month"]).reset_index(drop=True)
#     # print(df.columns)
#     return df


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

    return out


def add_loess_per_month(
    df: pd.DataFrame,
    value_col: str,
    out_col: str,
    frac: float,
) -> pd.DataFrame:
    """
    Applies LOWESS separately per calendar month over year.
    Writes fitted series back as a column aligned to original rows.
    """
    out = df.copy()
    out[out_col] = np.nan

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
                out.at[i, out_col] = float(smooth_map[y])

    return out


# def validate_db_exists(db_path: Path) -> None:
#     if not db_path.exists():
#         raise FileNotFoundError(
#             f"Missing SQLite DB at: {db_path}\n"
#             "Run: python scripts/ingest_raw_to_sqlite.py"
#         )


def main() -> None:
    out_path = Path(MONTHLY_FEATURES_PATH)
    raw_path = Path(HADCET_RAW_MONTHLY_PATH)

    if not raw_path.exists():
        raise FileNotFoundError(f"Missing HadCET raw file: {raw_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = read_hadcet_monthly_txt(raw_path)

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

    # ---- Baselines + anomalies ----
    # Temperature (°C)
    df = add_monthly_baseline_anomalies(df, value_col="tmean_c", out_prefix="tmean")
    # Rename base/anom cols to include unit suffix to match your preference
    for baseline_id in BASELINES.keys():
        df = df.rename(
            columns={
                f"tmean_base_{baseline_id}": f"tmean_base_{baseline_id}_c",
                f"tmean_anom_{baseline_id}": f"tmean_anom_{baseline_id}_c",
            }
        )

    # ---- LOESS (per-month over year) ----
    loess_col = f"tmean_loess_{LOESS_SUFFIX}_c"
    df = add_loess_per_month(
        df, value_col="tmean_c", out_col=loess_col, frac=LOESS_FRAC
    )
    df[f"tmean_resid_loess_{LOESS_SUFFIX}_c"] = df["tmean_c"] - df[loess_col]

    # ---- Final column order (tidy + predictable) ----
    core_cols = [
        "date",
        "year",
        "month",
        "month_name",
        "season",
        "winter_year",
        "decade",
        "period_bin",
        "tmean_c",
        "prcp_mm",
    ]

    baseline_cols = []
    for baseline_id in BASELINES.keys():
        baseline_cols += [
            f"tmean_base_{baseline_id}_c",
            f"tmean_anom_{baseline_id}_c",
            f"prcp_base_{baseline_id}_mm",
            f"prcp_anom_{baseline_id}_mm",
        ]

    loess_cols = [
        loess_col,
        f"tmean_resid_loess_{LOESS_SUFFIX}_c",
    ]

    keep_cols = [c for c in (core_cols + baseline_cols + loess_cols) if c in df.columns]
    df_out = df[keep_cols].sort_values(["year", "month"]).reset_index(drop=True)

    # ---- Write parquet ----
    schema_assert(df_out)
    df_out.to_parquet(out_path, index=False)
    print(f"Wrote: {out_path}")
    print(
        f"Rows: {len(df_out):,}  Years: {df_out['year'].min()}–{df_out['year'].max()}"
    )
    print("Done.")


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


if __name__ == "__main__":
    main()
