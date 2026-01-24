from __future__ import annotations
from dataclasses import dataclass

import pandas as pd

from .config import BASELINES, LOESS_SUFFIX


@dataclass(frozen=True)
class PublishedSchema:
    """
    Defines the *published* dataframe contract for the processed parquet.
    """

    columns: tuple[str, ...]
    key: tuple[str, ...] = ("year", "month")


def build_published_schema() -> PublishedSchema:
    core = (
        "date",
        "year",
        "month",
        "month_name",
        "season",
        "winter_year",
        "decade",
        "period_bin",
        "tmean_c",
    )

    baseline_cols = tuple(
        col
        for baseline_id in BASELINES.keys()
        for col in (
            f"tmean_base_{baseline_id}_c",
            f"tmean_anom_{baseline_id}_c",
        )
    )

    loess_cols = (
        f"tmean_loess_{LOESS_SUFFIX}_c",
        f"tmean_resid_loess_{LOESS_SUFFIX}_c",
    )

    return PublishedSchema(columns=core + baseline_cols + loess_cols)


def select_published_columns(df: pd.DataFrame, schema: PublishedSchema) -> pd.DataFrame:
    """
    Project df down to the published schema columns (ordered).
    Raises if required columns are missing.
    """
    missing = [c for c in schema.columns if c not in df.columns]
    if missing:
        raise KeyError(f"Cannot publish: missing columns: {missing}")

    out = df.loc[:, list(schema.columns)].copy()
    out = out.sort_values(list(schema.key)).reset_index(drop=True)
    return out
