from dataclasses import dataclass
from typing import List, Sequence, Tuple, Union

from app_core.color_utils import sample_colorscale
from app_core.mantine_theme import THEME

PlotlyColorscale = Union[str, List[list]]  # allow string or explicit list later

FALLBACK_CYAN_SHADES: Tuple[str, ...] = (
    "#e3fafc",
    "#c5f6fa",
    "#99e9f2",
    "#66d9e8",
    "#3bc9db",
    "#22b8cf",
    "#15aabf",
    "#1098ad",
    "#0c8599",
    "#0b7285",
)


def rgb(rgb_: Tuple[int, int, int]) -> str:
    r, g, b = rgb_
    return f"rgb({r},{g},{b})"


def rgba(rgb_: Tuple[int, int, int], a: float = 1.0) -> str:
    r, g, b = rgb_
    return f"rgba({r},{g},{b},{a})"


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    h = hex_color.strip().lstrip("#")
    if len(h) != 6:
        raise ValueError(f"Expected 6-char hex color, got: {hex_color}")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def primary_shade_rgb(shade: int) -> Tuple[int, int, int]:
    primary_name = str(THEME.get("primaryColor", "cyan"))
    colors = THEME.get("colors", {})
    shades = colors.get(primary_name, FALLBACK_CYAN_SHADES)
    if not isinstance(shades, Sequence) or len(shades) < 10:
        shades = FALLBACK_CYAN_SHADES
    return hex_to_rgb(str(shades[shade]))


@dataclass(frozen=True)
class UIPalette:
    surface: str
    surface_alt: str
    border: str
    text_muted: str


@dataclass(frozen=True)
class ClimatePalette:
    anomaly_colorscale: PlotlyColorscale
    anomaly_range_c: float
    reference_green: str

    def anomaly_cmin(self) -> float:
        return -self.anomaly_range_c

    def anomaly_cmax(self) -> float:
        return +self.anomaly_range_c

    def sample_anomaly_rgb(self, value: float) -> tuple[int, int, int]:
        return sample_colorscale(
            self.anomaly_colorscale,
            value,
            vmin=-self.anomaly_range_c,
            vmax=+self.anomaly_range_c,
        )


@dataclass(frozen=True)
class PlotPalette:
    background_paper: str
    background_plot: str
    background_legend: str
    border_legend: str
    grid_2d: str
    grid_3d: str
    history_grey: Tuple[int, int, int]
    annotation_text: str
    annotation_bg: str
    annotation_border: str
    line_compare: str
    line_highlight: str
    contour_rgb: Tuple[int, int, int]


@dataclass(frozen=True)
class RecencyPalette:
    old_grey: Tuple[int, int, int]
    new_green: Tuple[int, int, int]


UI = UIPalette(
    surface="var(--mantine-color-body)",
    surface_alt="var(--mantine-color-gray-0)",
    border="var(--mantine-color-gray-3)",
    text_muted="var(--mantine-color-dimmed)",
)

CLIMATE = ClimatePalette(
    anomaly_colorscale="RdBu_r",  # "RdBu_r" "Jet"
    anomaly_range_c=3.0,
    reference_green="rgba(80, 140, 110, 1.0)",
)

PLOT = PlotPalette(
    background_paper="#ffffff",
    background_plot="#f8f9fb",
    background_legend="rgba(255,255,255,0.85)",
    border_legend="rgba(0,0,0,0.12)",
    grid_2d="rgba(0,0,0,0.08)",
    grid_3d="rgba(0,0,0,0.12)",
    history_grey=(160, 160, 160),
    annotation_text="rgba(0,0,0,0.45)",
    annotation_bg="rgba(255,255,255,0.80)",
    annotation_border="rgba(0,0,0,0.08)",
    line_compare=rgba(primary_shade_rgb(7), 0.55),
    line_highlight=rgba(primary_shade_rgb(6), 1.0),
    contour_rgb=(0, 0, 0),
)

RECENCY = RecencyPalette(
    old_grey=(235, 238, 242),
    new_green=(45, 190, 105),
)

# Winter/era categorical colours
WINTER_BUCKET_RGB: Sequence[Tuple[int, int, int]] = [
    (31, 119, 180),  # blue
    (255, 127, 14),  # orange
    (44, 160, 44),  # green
    (214, 39, 40),  # red
    (148, 103, 189),  # purple
    (140, 86, 75),  # brown
    (227, 119, 194),  # pink
    (127, 127, 127),  # grey
    (188, 189, 34),  # olive
    (23, 190, 207),  # cyan
]


def winter_bucket_color(i: int, alpha: float = 0.9) -> str:
    """Stable categorical colour for winter era buckets."""
    rgb_ = WINTER_BUCKET_RGB[i % len(WINTER_BUCKET_RGB)]
    return rgba(rgb_, alpha)
