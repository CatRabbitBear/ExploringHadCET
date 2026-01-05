from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd

# LOESS (statsmodels)
from statsmodels.nonparametric.smoothers_lowess import lowess

from data.config import CLIMATE_DB_PATH, MONTHLY_FEATURES_PATH


MONTH_COLS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
MONTH_NAME_BY_NUM = {i + 1: name for i, name in enumerate(MONTH_COLS)}

# Locked baselines (full years, 30y each)
BASELINES: Dict[str, Tuple[int, int]] = {
    "1961_1990": (1961, 1990),
    "1881_1910": (1881, 1910),
}

# LOESS config (lock for v1)
LOESS_FRAC = 0.25
LOESS_SUFFIX = "0p25"  # used in column names


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


def read_monthly_tables(conn: sqlite3.Connection) -> pd.DataFrame:
    """
    Load temp and rainfall raw tables into one long monthly dataframe.
    Rainfall is left-joined and may be NULL prior to 1873.
    """
    df_t = pd.read_sql_query(
        """
        SELECT year, month, tmean_c
        FROM hadcet_tmean_monthly_raw
        ORDER BY year, month
        """,
        conn,
    )

    df_p = pd.read_sql_query(
        """
        SELECT year, month, prcp_mm
        FROM hadukp_prcp_monthly_raw
        ORDER BY year, month
        """,
        conn,
    )

    # Left join rainfall onto temperature
    df = df_t.merge(df_p, on=["year", "month"], how="left")

    # Basic tidy columns
    df["month_name"] = df["month"].map(MONTH_NAME_BY_NUM)
    df["date"] = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1))
    df["season"] = df["month"].apply(season_from_month)
    df["winter_year"] = [compute_winter_year(y, m) for y, m in zip(df["year"], df["month"])]
    df["decade"] = (df["year"] // 10) * 10
    df["period_bin"] = df["year"].apply(period_bin_for_year)

    # Sort
    df = df.sort_values(["year", "month"]).reset_index(drop=True)

    return df


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
        out[f"{out_prefix}_anom_{baseline_id}"] = out[value_col] - out[f"{out_prefix}_base_{baseline_id}"]

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


def validate_db_exists(db_path: Path) -> None:
    if not db_path.exists():
        raise FileNotFoundError(
            f"Missing SQLite DB at: {db_path}\n"
            "Run: python scripts/ingest_raw_to_sqlite.py"
        )


def main() -> None:
    db_path = Path(CLIMATE_DB_PATH)
    out_path = Path(MONTHLY_FEATURES_PATH)

    validate_db_exists(db_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))

    df = read_monthly_tables(conn)
    conn.close()

    # ---- Baselines + anomalies ----
    # Temperature (°C)
    df = add_monthly_baseline_anomalies(df, value_col="tmean_c", out_prefix="tmean")
    # Rename base/anom cols to include unit suffix to match your preference
    for baseline_id in BASELINES.keys():
        df = df.rename(columns={
            f"tmean_base_{baseline_id}": f"tmean_base_{baseline_id}_c",
            f"tmean_anom_{baseline_id}": f"tmean_anom_{baseline_id}_c",
        })

    # Rainfall (mm): only compute baselines where data exists (dropna inside groupby mean handles this)
    df = add_monthly_baseline_anomalies(df, value_col="prcp_mm", out_prefix="prcp")
    for baseline_id in BASELINES.keys():
        df = df.rename(columns={
            f"prcp_base_{baseline_id}": f"prcp_base_{baseline_id}_mm",
            f"prcp_anom_{baseline_id}": f"prcp_anom_{baseline_id}_mm",
        })

    # ---- LOESS (per-month over year) ----
    loess_col = f"tmean_loess_{LOESS_SUFFIX}_c"
    df = add_loess_per_month(df, value_col="tmean_c", out_col=loess_col, frac=LOESS_FRAC)
    df[f"tmean_resid_loess_{LOESS_SUFFIX}_c"] = df["tmean_c"] - df[loess_col]

    # ---- Final column order (tidy + predictable) ----
    core_cols = [
        "date", "year", "month", "month_name",
        "season", "winter_year",
        "decade", "period_bin",
        "tmean_c", "prcp_mm",
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
    df_out.to_parquet(out_path, index=False)
    print(f"Wrote: {out_path}")
    print(f"Rows: {len(df_out):,}  Years: {df_out['year'].min()}–{df_out['year'].max()}")
    print("Done.")


if __name__ == "__main__":
    main()