from __future__ import annotations

from typing import Iterable, Optional, Tuple, Any

import numpy as np
import pandas as pd


def df_to_grid(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    z_col: str,
    x_values: Optional[Iterable[Any]] = None,
    y_values: Optional[Iterable[Any]] = None,
    sort_x: bool = True,
    sort_y: bool = True,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert a long-form DataFrame with columns [x_col, y_col, z_col]
    into a regular 2D grid suitable for surface plots.

    Returns:
        x_vals: 1D array of x values (columns order)
        y_vals: 1D array of y values (index order)
        Z:      2D array of shape (len(y_vals), len(x_vals))

    Notes:
    - Uses pivot under the hood.
    - If x_values / y_values are provided, the grid is reindexed to them.
    - Assumes (x, y) pairs are unique or can be aggregated safely beforehand.
    """
    if df.empty:
        raise ValueError("df_to_grid: input DataFrame is empty")

    # Determine axis values
    if x_values is None:
        x_vals = df[x_col].unique()
        if sort_x:
            x_vals = np.sort(x_vals)
    else:
        x_vals = np.array(list(x_values))

    if y_values is None:
        y_vals = df[y_col].unique()
        if sort_y:
            y_vals = np.sort(y_vals)
    else:
        y_vals = np.array(list(y_values))

    # Pivot into a 2D grid: index = y, columns = x
    grid_df = (
        df.pivot(index=y_col, columns=x_col, values=z_col)
        .reindex(index=y_vals, columns=x_vals)
    )

    Z = grid_df.to_numpy()

    return x_vals, y_vals, Z