from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from statsmodels.nonparametric.smoothers_lowess import lowess

from .config import CET_LOESS_SURFACE_PATH
from .cet_monthly import load_cet_monthly
from .grids import df_to_grid


def build_cet_loess_surface(
    frac: float = 0.25,
    surface_path: Path | str = CET_LOESS_SURFACE_PATH,
) -> pd.DataFrame:
    """
    Build a smoothed CET monthly surface using per-month LOWESS over years.

    Returns a long-form DataFrame:
        year, month, t_loess

    - Smoothing is done separately for each calendar month (1..12).
    - Each month’s smoothed series is *clamped* to that month’s observed
      min/max, so we never invent insane values.
    """
    df = load_cet_monthly()
    surface_path = Path(surface_path)

    # Make sure we have clean ints
    df = df.copy()
    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)

    all_years = np.sort(df["year"].unique())
    rows = []

    for m in range(1, 13):
        sub = df[df["month"] == m].sort_values("year")

        if sub.empty:
            continue

        years = sub["year"].to_numpy(dtype=float)
        temps = sub["t_mean"].to_numpy(dtype=float)

        # Normalise x a bit to help LOWESS numerically
        x_norm = (years - years.min()) / (years.max() - years.min() or 1.0)

        # 1D LOWESS: y ~ f(x_norm)
        smoothed = lowess(
            endog=temps,
            exog=x_norm,
            frac=frac,          # smoothness; tweak 0.2–0.4
            it=3,
            return_sorted=False,
        )

        # Clamp to observed range for that month (no invented extremes)
        t_min = temps.min()
        t_max = temps.max()
        smoothed = np.clip(smoothed, t_min, t_max)

        # Collect rows
        for y, t_s in zip(years, smoothed):
            rows.append(
                {
                    "year": int(y),
                    "month": int(m),
                    "t_loess": float(t_s),
                }
            )

    surface_df = pd.DataFrame(rows).sort_values(["year", "month"]).reset_index(drop=True)

    surface_path.parent.mkdir(parents=True, exist_ok=True)
    surface_df.to_parquet(surface_path, index=False)

    return surface_df


def load_cet_loess_surface(
    frac: float = 0.25,
    surface_path: Path | str = CET_LOESS_SURFACE_PATH,
) -> pd.DataFrame:
    """
    Load the CET LOESS surface if it exists; otherwise build it.

    For now we assume a single 'frac' for the stored surface; if you later
    want multiple smoothness levels, you can encode 'frac' in the filename.
    """
    surface_path = Path(surface_path)
    if surface_path.exists():
        return pd.read_parquet(surface_path)

    # Build with the requested frac if missing
    return build_cet_loess_surface(frac=frac, surface_path=surface_path)


def get_cet_loess_surface_grid(
    selected_years: list[int] | None = None,
    frac: float = 0.25,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convenience helper for the app layer.

    Returns:
        months: 1D array of month values (x-axis)
        years:  1D array of year values (y-axis)
        Z:      2D array of smoothed temps (°C) shape (len(years), len(months))

    Optionally restricts to a subset of years.
    """
    df_surface = load_cet_loess_surface(frac=frac)

    if selected_years is not None and len(selected_years) > 0:
        df_surface = df_surface[df_surface["year"].isin(selected_years)]

    # x_col = "month", y_col = "year"
    months, years, Z = df_to_grid(
        df_surface,
        x_col="month",
        y_col="year",
        z_col="t_loess",
        # we let df_to_grid sort by default
    )

    return months, years, Z