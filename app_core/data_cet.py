from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd


# --- Paths -------------------------------------------------------------

# Project root = .../climate_dashboard/
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

RAW_CET_MONTHLY_PATH = DATA_DIR / "raw" / "meantemp_monthly_totals.txt"
PROCESSED_CET_MONTHLY_PATH = DATA_DIR / "processed" / "cet_monthly.parquet"


def _find_header_row(path: Path) -> int:
    """
    Find the line index of the 'Year Jan Feb ...' header row
    in the HadCET monthly text file.
    """
    with path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            # strip leading/trailing whitespace and check
            if line.strip().startswith("Year"):
                return idx
    raise ValueError(f"Could not find 'Year' header line in {path}")


def parse_raw_hadcet_monthly(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Parse the raw HadCET monthly mean temperature .txt file into a tidy DataFrame.
    """
    if path is None:
        path = RAW_CET_MONTHLY_PATH

    if not path.exists():
        raise FileNotFoundError(f"Raw HadCET file not found at {path}")

    header_row = _find_header_row(path)

    # Read as whitespace-delimited table, using the header row we found.
    # skiprows=header_row tells pandas to skip everything BEFORE the header,
    # then header=0 uses the first remaining line as column names.
    df_wide = pd.read_csv(
        path,
        sep=r"\s+",
        skiprows=header_row,
        header=0,
        engine="python",  # lets regex separators work reliably
    )

    # Normalise column names (strip extra spaces just in case)
    df_wide.columns = [c.strip() for c in df_wide.columns]

    month_cols = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    missing = [m for m in month_cols + ["Year", "Annual"] if m not in df_wide.columns]
    if missing:
        # Handy debug line if this ever fires again:
        raise ValueError(
            f"Expected columns missing in HadCET file: {missing}. "
            f"Got columns: {list(df_wide.columns)}"
        )

    # Melt to tidy long format: one row per year-month
    df_long = df_wide.melt(
        id_vars=["Year", "Annual"],
        value_vars=month_cols,
        var_name="month_name",
        value_name="t_mean",
    )

    df_long["t_mean"] = df_long["t_mean"].replace(-99.9, pd.NA)
    # df_long["annual_mean"] = df_long["annual_mean"].replace(-99.9, pd.NA)

    month_map = {name: i for i, name in enumerate(month_cols, start=1)}
    df_long["month"] = df_long["month_name"].map(month_map)

    df_long = df_long.rename(columns={"Year": "year", "Annual": "annual_mean"})
    df_long = df_long.dropna(subset=["t_mean"])

    df_long["date"] = pd.to_datetime(
        dict(year=df_long["year"], month=df_long["month"], day=1)
    )

    df_long = df_long.sort_values(["year", "month"]).reset_index(drop=True)
    df_long = df_long[
        ["date", "year", "month", "month_name", "t_mean", "annual_mean"]
    ]

    return df_long


def build_and_save_cet_monthly(
    raw_path: Optional[Path] = None,
    processed_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Parse the raw HadCET monthly file and save a processed Parquet file.

    Returns the processed DataFrame for convenience.
    """
    if raw_path is None:
        raw_path = RAW_CET_MONTHLY_PATH
    if processed_path is None:
        processed_path = PROCESSED_CET_MONTHLY_PATH

    df = parse_raw_hadcet_monthly(raw_path)

    processed_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(processed_path, index=False)

    return df


def load_cet_monthly(
    processed_path: Optional[Path] = None,
    rebuild_if_missing: bool = True,
) -> pd.DataFrame:
    """
    Load the processed HadCET monthly dataset from Parquet.

    If the processed file is missing and `rebuild_if_missing` is True,
    it will parse the raw .txt and create it automatically.
    """
    if processed_path is None:
        processed_path = PROCESSED_CET_MONTHLY_PATH

    if processed_path.exists():
        return pd.read_parquet(processed_path)

    if not rebuild_if_missing:
        raise FileNotFoundError(
            f"Processed CET file not found at {processed_path} and rebuild_if_missing=False"
        )

    # Fall back to building from raw
    return build_and_save_cet_monthly(
        raw_path=RAW_CET_MONTHLY_PATH,
        processed_path=processed_path,
    )

def add_monthly_anomalies(
    df_cet: pd.DataFrame,
    centre_year: int = 1855,
    window_half_width: int = 5,
) -> pd.DataFrame:
    """
    Adds monthly baseline and anomaly columns to a CET monthly dataframe.

    - Baseline = mean of t_mean over [centre_year - window_half_width,
                                      centre_year + window_half_width],
      computed separately for each calendar month (Jan..Dec).
    - Anomaly = t_mean - monthly_baseline.
    """
    df = df_cet.copy()

    start = centre_year - window_half_width
    end = centre_year + window_half_width

    # 11-year window around centre_year
    baseline_mask = df["year"].between(start, end)
    baseline_df = df.loc[baseline_mask]

    # One baseline per month (1..12)
    monthly_baseline = (
        baseline_df
        .groupby("month")["t_mean"]
        .mean()
        .rename("t_mean_baseline")
    )

    # Merge back onto full dataframe
    df = df.merge(
        monthly_baseline,
        on="month",
        how="left",
    )

    # Monthly anomaly = deviation from that month’s baseline
    df["t_anom"] = df["t_mean"] - df["t_mean_baseline"]

    return df