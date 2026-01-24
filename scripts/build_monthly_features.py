from __future__ import annotations

from pathlib import Path
import logging

from data.config import (
    MONTHLY_FEATURES_PATH,
    HADCET_RAW_MONTHLY_PATH,
)

import data.pipeline_utils as pu
from data.schema import build_published_schema, select_published_columns
from data.transforms import (
    add_time_and_labels,
    add_monthly_baseline_anomalies,
    add_loess_per_month,
    schema_assert,
)

logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting HadCET monthly feature build")
    out_path = Path(MONTHLY_FEATURES_PATH)
    raw_path = Path(HADCET_RAW_MONTHLY_PATH)

    if not raw_path.exists():
        raise FileNotFoundError(f"Missing HadCET raw file: {raw_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    df = pu.read_hadcet_monthly_txt(raw_path)

    df = add_time_and_labels(df)

    # ---- Baselines + anomalies ----
    df = add_monthly_baseline_anomalies(df, value_col="tmean_c", out_prefix="tmean")

    # ---- LOESS (per-month over year) ----
    df = add_loess_per_month(df, value_col="tmean_c")

    schema = build_published_schema()
    df_out = select_published_columns(df, schema)

    # ---- Write parquet ----
    logger.info("Validating output schema")
    schema_assert(df_out, required_columns=schema.columns, allow_extra_columns=False)
    df_out.to_parquet(out_path, index=False)

    logger.info(
        "Wrote %s | rows=%d | years=%d–%d",
        out_path,
        len(df_out),
        df_out["year"].min(),
        df_out["year"].max(),
    )

    logger.info("Completed HadCET monthly feature build")


if __name__ == "__main__":
    main()
