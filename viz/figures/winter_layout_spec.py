from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BucketSpec:
    bucket: str
    i: int
    x_start: float
    x_end: float
    min_y: float
    max_y: float

    # Optional boxplot structure (for morphing)
    q1_y: Optional[float] = None
    median_y: Optional[float] = None
    q3_y: Optional[float] = None