from typing import Any, Dict, Sequence, Optional, Tuple
from app_core.tokens_colors import PLOT, CLIMATE

CLIMATE_TEMPLATE: Dict[str, Any] = {
    "layout": {
        "paper_bgcolor": PLOT.background_paper,
        "plot_bgcolor": PLOT.background_plot,
        "font": {
            "family": "system-ui, -apple-system, Segoe UI, Roboto, Arial",
            "size": 12,
        },
        "hoverlabel": {
            "bgcolor": "rgba(255,255,255,0.95)",
            "bordercolor": "rgba(0,0,0,0.15)",
            "font": {"color": "rgba(0,0,0,0.85)"},
        },
        "xaxis": {"zeroline": False},
        "yaxis": {"zeroline": False},
    }
}

# ----------------------------
# Reusable layout dict helpers
# ----------------------------


def layout_cet_2d(y_range: Sequence[float]) -> Dict[str, Any]:
    """
    Base 2D layout for CET month-lines.
    Keep y_range explicit so 2D and 3D can match.
    """
    return {
        "xaxis": {
            "title": "Month",
            "showgrid": False,
            "zeroline": False,
        },
        "yaxis": {
            "title": "Mean Temp (°C)",
            "range": list(y_range),
            "showgrid": True,
            "gridcolor": PLOT.grid_2d,
            "zeroline": False,
        },
        "hovermode": "x unified",
        "margin": {"l": 40, "r": 10, "t": 60, "b": 40},
        # "plot_bgcolor": PLOT_BG,
        # "paper_bgcolor": PAPER_BG,
    }


def legend_highlights(title: str = "Highlighted years") -> Dict[str, Any]:
    """
    Standard legend styling for the 'few highlighted traces' pattern.
    """
    return {
        "legend": {
            "title": {"text": title},
            "bgcolor": PLOT.background_legend,
            "bordercolor": PLOT.border_legend,
            "borderwidth": 1,
        }
    }


def layout_cet_3d(
    z_range: Sequence[float],
    month_vals: Sequence[int],
    month_labels: Sequence[str],
    *,
    aspectratio: Optional[Dict[str, float]] = None,
    reverse_year_axis: bool = True,
    show_z_grid: bool = True,
) -> Dict[str, Any]:
    """
    Base 3D scene layout for CET.

    Notes:
    - z_range should match the 2D y_range for "front-on consistency".
    - month_vals/month_labels stay explicit for clarity.
    """
    if aspectratio is None:
        aspectratio = {"x": 1.5, "y": 3, "z": 1}

    yaxis_dict: Dict[str, Any] = {
        "title": "Year",
        "showgrid": False,
        "showbackground": False,
        "zeroline": False,
    }
    if reverse_year_axis:
        yaxis_dict["autorange"] = "reversed"

    return {
        "scene": {
            "bgcolor": PLOT.background_plot,
            "aspectmode": "manual",
            "aspectratio": aspectratio,
            "xaxis": {
                "title": "Month",
                "tickmode": "array",
                "tickvals": list(month_vals),
                "ticktext": list(month_labels),
                "showgrid": False,
                "showbackground": False,
                "zeroline": False,
            },
            "yaxis": yaxis_dict,
            "zaxis": {
                "title": "Mean Temp (°C)",
                "range": list(z_range),
                "showgrid": bool(show_z_grid),
                "gridcolor": PLOT.grid_3d,
                "zeroline": False,
            },
        },
        "margin": {"l": 0, "r": 0, "t": 40, "b": 0},
        "paper_bgcolor": PLOT.background_paper,
        # In 3D, legend tends to be noisy; often you’ll override this in callbacks
        # with showlegend=False on most traces. Keep only "legend_title" here.
        "legend_title": "Series",
        "scene_camera": {"eye": {"x": 1.6, "y": 1.2, "z": 1.1}},
    }


# ----------------------------
# Small trace-style helpers (optional)
# ----------------------------


def rgba(rgb: Tuple[int, int, int], a: float) -> str:
    r, g, b = rgb
    return f"rgba({r},{g},{b},{a})"


def muted_background_line_style(
    rgb: Tuple[int, int, int] = PLOT.history_grey,
    width: float = 1.0,
    alpha: float = 0.10,
) -> Dict[str, Any]:
    return {"color": rgba(rgb, alpha), "width": width}


def highlight_line_style(color: str, width: float = 3.6) -> Dict[str, Any]:
    return {"color": color, "width": width}
