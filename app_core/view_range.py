from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Tuple

from dash import dcc


@dataclass(frozen=True)
class ViewRange:
    start_year: int
    end_year: int


def normalize_year_range(
    start_year: int | None,
    end_year: int | None,
    min_year: int,
    max_year: int,
) -> Tuple[int, int]:
    if start_year is None or end_year is None:
        return min_year, max_year

    start = int(start_year)
    end = int(end_year)

    if start > end:
        start, end = end, start

    start = max(min_year, min(start, max_year))
    end = max(min_year, min(end, max_year))

    if start > end:
        return min_year, max_year

    return start, end


def coerce_view_range(
    data: Dict[str, Any] | None,
    *,
    min_year: int,
    max_year: int,
) -> Dict[str, int]:
    if not isinstance(data, dict):
        start, end = normalize_year_range(None, None, min_year, max_year)
        return {"start_year": start, "end_year": end}

    start = data.get("start_year")
    end = data.get("end_year")
    start, end = normalize_year_range(start, end, min_year, max_year)
    return {"start_year": start, "end_year": end}


def get_view_range(
    data: Dict[str, Any] | None,
    *,
    min_year: int,
    max_year: int,
) -> ViewRange:
    cleaned = coerce_view_range(data, min_year=min_year, max_year=max_year)
    return ViewRange(**cleaned)


def set_view_range(
    start_year: int | None,
    end_year: int | None,
    *,
    min_year: int,
    max_year: int,
) -> Dict[str, int]:
    start, end = normalize_year_range(start_year, end_year, min_year, max_year)
    return {"start_year": start, "end_year": end}


def make_view_range_store(*, min_year: int, max_year: int):
    default = ViewRange(start_year=min_year, end_year=max_year)
    return dcc.Store(
        id="global-view-range",
        data=asdict(default),
        storage_type="session",
    )
