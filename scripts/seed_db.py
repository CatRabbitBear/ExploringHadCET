from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Tuple, Dict

from pydantic import BaseModel, Field, ValidationError, field_validator


# -----------------------------
# Pydantic models
# -----------------------------

class MonthlyObservation(BaseModel):
    dataset: str = Field(..., pattern=r"^(hadcet_tmean|hadukp_prcp)$")
    year: int = Field(..., ge=1500, le=3000)
    month: int = Field(..., ge=1, le=12)
    value: Optional[float]

    @field_validator("value")
    @classmethod
    def value_is_finite(cls, v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        if v != v:
            raise ValueError("value cannot be NaN")
        if v in (float("inf"), float("-inf")):
            raise ValueError("value cannot be infinite")
        return v


class YearAnnual(BaseModel):
    dataset: str = Field(..., pattern=r"^(hadcet_tmean|hadukp_prcp)$")
    year: int = Field(..., ge=1500, le=3000)
    annual: float


# -----------------------------
# Parsing helpers
# -----------------------------

MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def _find_header_and_data_lines(text: str) -> List[str]:
    """
    Return only true data rows:
      Year + 12 month values + Annual
    Avoids header lines like '1974 on Parker et al.'
    """
    lines = [ln.rstrip("\n") for ln in text.splitlines()]
    data_lines: List[str] = []

    for ln in lines:
        s = ln.strip()
        if not re.match(r"^\d{4}\s+", s):
            continue

        parts = re.split(r"\s+", s)

        # Must be: Year + 12 months + Annual = 14 tokens minimum
        if len(parts) < 14:
            continue

        # Hard-validate numeric shape: year int, and 13 numeric fields following (12 months + annual)
        try:
            int(parts[0])
            # allow sentinels in the 12 months + annual slot
            for tok in parts[1:14]:
                _ = parse_value(tok)  # may be None
        except ValueError:
            continue

        data_lines.append(ln)

    if not data_lines:
        raise ValueError("No data lines found matching: YEAR + 12 monthly values + Annual.")
    return data_lines

MISSING_SENTINELS = {"-99.9", "-99.99", "-999", "-999.0", "NA", "N/A", "***", "*", ""}

def parse_value(token: str) -> Optional[float]:
    t = token.strip()
    if t in MISSING_SENTINELS:
        return None
    # Handle numeric strings
    v = float(t)
    # Treat -99.9 style numerics even if written as -99.900
    if abs(v + 99.9) < 1e-9 or abs(v + 99.99) < 1e-9:
        return None
    if abs(v + 999.0) < 1e-9:
        return None
    return v

def parse_wide_monthly_table(
    path: Path,
    dataset: str,
    *,
    allow_negative: bool,
) -> Tuple[List[MonthlyObservation], List[YearAnnual]]:
    """
    Parses HadCET/HadUKP-style wide tables:
      Year Jan Feb ... Dec Annual
    Returns:
      - list of MonthlyObservation
      - list of YearAnnual
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    data_lines = _find_header_and_data_lines(text)

    monthly: List[MonthlyObservation] = []
    annuals: List[YearAnnual] = []

    for ln in data_lines:
        # split on whitespace
        parts = re.split(r"\s+", ln.strip())
        # Expect: Year + 12 months + Annual  => 14 tokens
        # Some sources can include missing values; we'll fail fast if unexpected.
        if len(parts) < 14:
            raise ValueError(f"Unexpected row token count ({len(parts)}) for line: {ln}")

        year = int(parts[0])
        month_vals = parts[1:13]
        annual_val = float(parts[13])

        # Annual record (optional but useful for audits)
        annuals.append(YearAnnual(dataset=dataset, year=year, annual=annual_val))

        for i, raw_v in enumerate(month_vals):
            # Some files may use placeholders like -99.9; adapt if you encounter that later.
            v = parse_value(raw_v)

            # rainfall: if v is not None, it must be >= 0
            if dataset == "hadukp_prcp" and v is not None and v < 0:
                raise ValueError(f"Unexpected negative rainfall for {dataset}: year={year} month={i + 1} v={v}")

            monthly.append(MonthlyObservation(dataset=dataset, year=year, month=i+1, value=v))

    return monthly, annuals


# -----------------------------
# DB layer
# -----------------------------

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id TEXT PRIMARY KEY,
    ran_at TEXT NOT NULL,
    hadcet_source TEXT,
    hadukp_source TEXT,
    rows_inserted INTEGER NOT NULL DEFAULT 0,
    rows_updated  INTEGER NOT NULL DEFAULT 0,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS hadcet_tmean_monthly_raw (
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
    tmean_c REAL,
    source_version TEXT,
    ingested_at TEXT NOT NULL,
    PRIMARY KEY (year, month)
);

CREATE TABLE IF NOT EXISTS hadukp_prcp_monthly_raw (
    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
    prcp_mm REAL CHECK(prcp_mm >= 0),
    source_version TEXT,
    ingested_at TEXT NOT NULL,
    PRIMARY KEY (year, month)
);

-- Optional year-level annual values (kept separate to avoid repetition)
CREATE TABLE IF NOT EXISTS hadcet_tmean_yearly_raw (
    year INTEGER PRIMARY KEY,
    annual_c REAL NOT NULL,
    source_version TEXT,
    ingested_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hadukp_prcp_yearly_raw (
    year INTEGER PRIMARY KEY,
    annual_mm REAL NOT NULL,
    source_version TEXT,
    ingested_at TEXT NOT NULL
);
"""


@dataclass
class UpsertStats:
    inserted: int = 0
    updated: int = 0


def upsert_monthly(
    conn: sqlite3.Connection,
    dataset: str,
    rows: List[MonthlyObservation],
    *,
    source_version: Optional[str],
    ingested_at: str,
) -> UpsertStats:
    stats = UpsertStats()

    if dataset == "hadcet_tmean":
        table = "hadcet_tmean_monthly_raw"
        col = "tmean_c"
    elif dataset == "hadukp_prcp":
        table = "hadukp_prcp_monthly_raw"
        col = "prcp_mm"
    else:
        raise ValueError(f"Unknown dataset: {dataset}")

    cur = conn.cursor()

    # We'll do a simple read-then-upsert for correctness and accurate stats.
    # With ~a few thousand rows, this is totally fine.
    for r in rows:
        cur.execute(f"SELECT {col} FROM {table} WHERE year=? AND month=?", (r.year, r.month))
        existing = cur.fetchone()
        if existing is None:
            cur.execute(
                f"INSERT INTO {table} (year, month, {col}, source_version, ingested_at) VALUES (?, ?, ?, ?, ?)",
                (r.year, r.month, r.value, source_version, ingested_at),
            )
            stats.inserted += 1
        else:
            old_val = existing[0]
            if old_val != r.value:
                cur.execute(
                    f"UPDATE {table} SET {col}=?, source_version=?, ingested_at=? WHERE year=? AND month=?",
                    (r.value, source_version, ingested_at, r.year, r.month),
                )
                stats.updated += 1

    return stats


def upsert_yearly(
    conn: sqlite3.Connection,
    dataset: str,
    rows: List[YearAnnual],
    *,
    source_version: Optional[str],
    ingested_at: str,
) -> None:
    if dataset == "hadcet_tmean":
        table = "hadcet_tmean_yearly_raw"
        col = "annual_c"
    elif dataset == "hadukp_prcp":
        table = "hadukp_prcp_yearly_raw"
        col = "annual_mm"
    else:
        raise ValueError(f"Unknown dataset: {dataset}")

    cur = conn.cursor()
    for r in rows:
        cur.execute(f"SELECT {col} FROM {table} WHERE year=?", (r.year,))
        existing = cur.fetchone()
        if existing is None:
            cur.execute(
                f"INSERT INTO {table} (year, {col}, source_version, ingested_at) VALUES (?, ?, ?, ?)",
                (r.year, r.annual, source_version, ingested_at),
            )
        else:
            old_val = float(existing[0])
            if old_val != float(r.annual):
                cur.execute(
                    f"UPDATE {table} SET {col}=?, source_version=?, ingested_at=? WHERE year=?",
                    (r.annual, r.annual, source_version, ingested_at, r.year),
                )


def init_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn


# -----------------------------
# Main
# -----------------------------

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def main() -> None:
    root = Path(__file__).resolve().parents[1]  # repo root (scripts/seed_db.py)
    raw_dir = root / "data" / "raw"
    db_path = root / "data" / "db" / "uk_climate.sqlite"

    hadcet_path = raw_dir / "hadcet_mean_monthly.txt"
    hadukp_path = raw_dir / "hadukp_cet_prcp_monthly.txt"

    if not hadcet_path.exists():
        raise FileNotFoundError(f"Missing file: {hadcet_path}")
    if not hadukp_path.exists():
        raise FileNotFoundError(f"Missing file: {hadukp_path}")

    # Optional source versions: you can swap this later for HTTP Last-Modified / ETag / sha256.
    hadcet_version = f"file:{hadcet_path.name}"
    hadukp_version = f"file:{hadukp_path.name}"

    ingested_at = utc_now_iso()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    conn = init_db(db_path)

    # Parse + validate via Pydantic
    try:
        hadcet_monthly, hadcet_yearly = parse_wide_monthly_table(
            hadcet_path,
            dataset="hadcet_tmean",
            allow_negative=True,
        )
        hadukp_monthly, hadukp_yearly = parse_wide_monthly_table(
            hadukp_path,
            dataset="hadukp_prcp",
            allow_negative=False,
        )
    except ValidationError as ve:
        raise SystemExit(f"Pydantic validation failed:\n{ve}") from ve

    # Upsert
    stats_a = upsert_monthly(conn, "hadcet_tmean", hadcet_monthly, source_version=hadcet_version, ingested_at=ingested_at)
    upsert_yearly(conn, "hadcet_tmean", hadcet_yearly, source_version=hadcet_version, ingested_at=ingested_at)

    stats_b = upsert_monthly(conn, "hadukp_prcp", hadukp_monthly, source_version=hadukp_version, ingested_at=ingested_at)
    upsert_yearly(conn, "hadukp_prcp", hadukp_yearly, source_version=hadukp_version, ingested_at=ingested_at)

    total_inserted = stats_a.inserted + stats_b.inserted
    total_updated = stats_a.updated + stats_b.updated

    # Log ingestion run
    conn.execute(
        "INSERT OR REPLACE INTO ingestion_runs (run_id, ran_at, hadcet_source, hadukp_source, rows_inserted, rows_updated, notes) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            run_id,
            ingested_at,
            hadcet_version,
            hadukp_version,
            total_inserted,
            total_updated,
            "seed_db run",
        ),
    )
    conn.commit()
    conn.close()

    print(f"DB: {db_path}")
    print(f"Inserted: {total_inserted}  Updated: {total_updated}")
    print("Done.")


if __name__ == "__main__":
    main()