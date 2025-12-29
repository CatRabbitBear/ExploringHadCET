# app_core/config.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

CET_PROCESSED_PATH = DATA_DIR / "processed" / "cet_monthly.parquet"