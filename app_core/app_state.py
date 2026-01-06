from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict

from dash import dcc


# keep this small: UI knobs only (not data)
@dataclass(frozen=True)
class AppState:
    era: str = "modern"           # "modern" | "instrumental" | "full"
    baseline: str = "1961_1990"   # future-proofing


DEFAULT_STATE = AppState()


VALID_ERA = {"modern", "instrumental", "full"}


def coerce_app_state(data: Dict[str, Any] | None) -> Dict[str, Any]:
    """
    Merge untrusted store data onto defaults and validate.
    Always returns a dict safe to store back into dcc.Store.
    """
    base = asdict(DEFAULT_STATE)

    if not isinstance(data, dict):
        return base

    merged = {**base, **data}

    if merged.get("era") not in VALID_ERA:
        merged["era"] = base["era"]

    # baseline validation can come later if you add more options
    if not isinstance(merged.get("baseline"), str):
        merged["baseline"] = base["baseline"]

    return merged


def make_app_state_store():
    return dcc.Store(
        id="app-state",
        data=asdict(DEFAULT_STATE),
        storage_type="session",  # survives refresh in same tab, nice UX
    )