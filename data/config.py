from pathlib import Path
from typing import Dict, Tuple

BASE_DIR = (
    Path(__file__).resolve().parent.parent
)  # repo root (data/ is at BASE_DIR / "data")
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Raw inputs (offline ingestion only)
HADCET_RAW_MONTHLY_PATH = RAW_DIR / "hadcet_mean_monthly.txt"

# Single processed artifact (app reads ONLY this)
MONTHLY_FEATURES_PATH = PROCESSED_DIR / "monthly_features.parquet"


MISSING_SENTINELS = {"-99.9", "-99.99", "-999", "-999.0", "NA", "N/A", "***", "*", ""}

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
