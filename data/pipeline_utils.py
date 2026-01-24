from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import re

from .config import MISSING_SENTINELS


def parse_value(token: str) -> float | None:
    t = token.strip()
    if t in MISSING_SENTINELS:
        return np.nan
    v = float(t)
    # Treat numeric sentinels like -99.900 as missing too
    if abs(v + 99.9) < 1e-9 or abs(v + 99.99) < 1e-9:
        return np.nan
    if abs(v + 999.0) < 1e-9:
        return np.nan
    return v


def _find_header_and_data_lines(text: str) -> list[str]:
    """
    Return only true data rows:
      Year + 12 month values + Annual
    Avoids header lines like '1974 on Parker et al.'
    """
    lines = [ln.rstrip("\n") for ln in text.splitlines()]
    data_lines: list[str] = []

    for ln in lines:
        s = ln.strip()
        if not re.match(r"^\d{4}\s+", s):
            continue

        parts = re.split(r"\s+", s)

        # Must be: Year + 12 months + Annual = 14 tokens minimum
        if len(parts) < 14:
            continue

        try:
            int(parts[0])
            for tok in parts[1:14]:
                _ = parse_value(tok)  # may be NaN
        except ValueError:
            continue

        data_lines.append(ln)

    if not data_lines:
        raise ValueError(
            "No data lines found matching: YEAR + 12 monthly values + Annual."
        )
    return data_lines


def read_hadcet_monthly_txt(path: Path) -> pd.DataFrame:
    """
    Parses HadCET-style wide table into long monthly DF:
      year, month, tmean_c
    Sentinel missing values become NaN.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    data_lines = _find_header_and_data_lines(text)

    rows = []
    for ln in data_lines:
        parts = re.split(r"\s+", ln.strip())
        year = int(parts[0])
        month_vals = parts[1:13]  # Jan..Dec
        # parts[13] is annual, ignore for now

        for i, tok in enumerate(month_vals, start=1):
            rows.append((year, i, parse_value(tok)))

    df = pd.DataFrame(rows, columns=["year", "month", "tmean_c"])
    df = df.sort_values(["year", "month"]).reset_index(drop=True)
    return df
