from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from .config import MONTHLY_FEATURES_PATH
from .grids import df_to_grid


def load_monthly_features(path: Path | None = None) -> pd.DataFrame:
    """
    App-layer loader. Reads the single processed parquet artifact.

    This must NOT rebuild from raw or touch SQLite. If missing, fail fast and
    instruct how to build.
    """
    path = path or MONTHLY_FEATURES_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Missing processed dataset: {path}\n"
            "Build it with: python scripts/build_monthly_features.py"
        )
    return pd.read_parquet(path)


def get_loess_surface_grid(
    value_col: str = "tmean_loess_0p25_c",
    years: list[int] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Returns months, years, Z grid for surface plots, derived from monthly_features parquet.
    """
    df = load_monthly_features()

    if years:
        df = df[df["year"].isin(years)]

    months, years_arr, Z = df_to_grid(
        df,
        x_col="month",
        y_col="year",
        z_col=value_col,
    )
    return months, years_arr, Z

def get_surface_grids(
    *,
    years: list[int] | None = None,
    z_col: str = "tmean_loess_0p25_c",
    surfacecolor_col: str | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray | None]:
    """
    Return x(months), y(years), Z grid, and optional surfacecolor grid.
    """
    df = load_monthly_features()

    if years:
        df = df[df["year"].isin(years)]

    months, years_arr, Z = df_to_grid(df, x_col="month", y_col="year", z_col=z_col)

    C = None
    if surfacecolor_col is not None:
        _, _, C = df_to_grid(df, x_col="month", y_col="year", z_col=surfacecolor_col)

    return months, years_arr, Z, C