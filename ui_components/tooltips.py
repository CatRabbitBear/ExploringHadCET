from __future__ import annotations

import os
from typing import Any, Optional

import dash_mantine_components as dmc
from dash import html
from dash_iconify import DashIconify

from app_core.tokens_colors import UI


TOOLTIPS: dict[str, str] = {
    "overview.anomaly": (
        "Anomaly means deviation from the month's baseline average "
        "(e.g., Jan vs Jan baseline), not a raw temperature."
    ),
    "overview.baseline_1961_1990": (
        "Baseline is a reference average for each month over 1961-1990, "
        "used to compare different eras fairly."
    ),
    "overview.loess_surface": (
        "LOESS is a smoothing method that highlights long-term structure "
        "while reducing month-to-month noise. It does not predict the future."
    ),
    "overview.monthly_compare": (
        "Each line is a calendar year of monthly mean temperatures, "
        "letting you compare seasonal shapes and extremes across time."
    ),
    "exceptional.definition": (
        "Exceptional months are the most unusual months in the record "
        "relative to the baseline - shown by month to avoid mixing seasonal effects."
    ),
    "winter.djf_definition": (
        "Winter is grouped as Dec–Jan–Feb (DJF) to align with how winter "
        "climate behaves across year boundaries."
    ),
    "winter.winter_year": (
        "Winter year labels DJF by the year that January belongs to "
        "(e.g., Dec 1999-Feb 2000 is '2000')."
    ),
    "method.data_source": (
        "Data comes from HadCET (Central England Temperature), "
        "a long-running regional climate series used widely in UK climate analysis."
    ),
}


DEFAULT_TOOLTIP_WIDTH = 240
DEFAULT_TOOLTIP_DELAY_MS = 300
DEFAULT_ICON_SIZE = 20


def _is_debug() -> bool:
    return os.getenv("DASH_ENV") == "development" or os.getenv("DASH_DEBUG") == "1"


def help_tooltip(
    *,
    key: Optional[str] = None,
    text: Optional[str] = None,
    width: Optional[int] = None,
    position: str = "top",
) -> Optional[Any]:
    """
    Small, consistent help-tooltip icon for titles/labels.

    Exactly one of key or text must be provided.
    """
    if (key is None) == (text is None):
        raise ValueError("Provide exactly one of key or text.")

    tooltip_text = text
    if key is not None:
        tooltip_text = TOOLTIPS.get(key)
        if tooltip_text is None:
            if _is_debug():
                tooltip_text = f"Tooltip missing: {key}"
            else:
                return dmc.Box(style={"display": "none"})

    icon = DashIconify(
        icon="tabler:info-circle",
        width=DEFAULT_ICON_SIZE,
        height=DEFAULT_ICON_SIZE,
        color=UI.text_muted,
    )

    icon_wrap = html.Span(
        icon,
        # aria-label="Help",
        role="img",
        style={
            "display": "inline-flex",
            "alignItems": "center",
            "cursor": "pointer",
            "marginLeft": "6px",
        },
    )

    return dmc.Tooltip(
        label=tooltip_text,
        multiline=True,
        w=width or DEFAULT_TOOLTIP_WIDTH,
        withArrow=True,
        position=position,
        openDelay=DEFAULT_TOOLTIP_DELAY_MS,
        children=icon_wrap,
    )
