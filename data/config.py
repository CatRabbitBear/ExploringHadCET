# app_core/config.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

CET_RAW_MONTHLY_PATH = RAW_DIR / "meantemp_monthly_totals.txt"
CET_PROCESSED_MONTHLY_PATH = PROCESSED_DIR / "cet_monthly.parquet"
CET_LOESS_SURFACE_PATH = PROCESSED_DIR / "cet_loess_surface.parquet"