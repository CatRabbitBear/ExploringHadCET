from typing import Tuple
import plotly.colors as pc

def sample_colorscale(
    colorscale_name: str,
    value: float,
    *,
    vmin: float,
    vmax: float,
) -> Tuple[int, int, int]:
    """
    Sample a Plotly colorscale at a numeric value.

    Returns an (R, G, B) tuple.
    """
    # Clamp + normalise to [0, 1]
    if vmax <= vmin:
        t = 0.5
    else:
        value = max(vmin, min(vmax, value))
        t = (value - vmin) / (vmax - vmin)

    # Get scale definition
    scale = pc.get_colorscale(colorscale_name)

    # Sample -> returns 'rgb(r,g,b)'
    rgb_str = pc.sample_colorscale(scale, t)[0]

    # Parse to ints
    nums = rgb_str[rgb_str.find("(")+1 : rgb_str.find(")")].split(",")
    return tuple(int(float(n)) for n in nums)