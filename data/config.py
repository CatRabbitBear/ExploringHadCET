# data/config.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # repo root (data/ is at BASE_DIR / "data")
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
DB_DIR = DATA_DIR / "db"
PROCESSED_DIR = DATA_DIR / "processed"

# Raw inputs (offline ingestion only)
HADCET_RAW_MONTHLY_PATH = RAW_DIR / "hadcet_mean_monthly.txt"
HADUKP_RAW_MONTHLY_PATH = RAW_DIR / "hadukp_cet_prcp_monthly.txt"

# SQLite (offline only)
CLIMATE_DB_PATH = DB_DIR / "uk_climate.sqlite"

# Single processed artifact (app reads ONLY this)
MONTHLY_FEATURES_PATH = PROCESSED_DIR / "monthly_features.parquet"