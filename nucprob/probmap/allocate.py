"""The allocation step: delivered warheads to areas, in proportion to a town's score.

Each delivered warhead falls on a town drawn with probability equal to the town's share of the
scenario's total score, independently of the others. That is the protocol's rule and it optimises
nothing: it does not ask what a warhead would achieve, and no quantity here is maximised. The result
for an area is P = 1 - (1 - q)^W, with q the area's share of the score and W the warheads delivered.

Only the area's probability leaves this module. No per-town or per-area count of weapons is ever
returned or written.
"""

import numpy as np
import pandas as pd

MIN_CELL_DEG = 0.5


def cell_ids(lat, lon, cell_deg: float) -> pd.Series:
    """Index of each town's grid cell, by its south-west corner: `lat_lon` in degrees."""
    if cell_deg < MIN_CELL_DEG:
        raise ValueError(f"cells must be at least {MIN_CELL_DEG} degrees, got {cell_deg}")
    la = np.floor(np.asarray(lat, dtype=float) / cell_deg) * cell_deg
    lo = np.floor(np.asarray(lon, dtype=float) / cell_deg) * cell_deg
    return pd.Series([f"{a:.1f}_{b:.1f}" for a, b in zip(la, lo, strict=True)])


def score_shares(scores: np.ndarray) -> np.ndarray:
    """A town's share of the total score in each draw: rows are towns, columns are draws."""
    scores = np.asarray(scores, dtype=float)
    total = scores.sum(axis=0, keepdims=True)
    if (total <= 0).any():
        raise ValueError("a draw has no positive score to allocate")
    return scores / total


def area_shares(shares: np.ndarray, cell: np.ndarray, n_cells: int) -> np.ndarray:
    """Sum the towns' shares by cell: rows are cells, columns are draws."""
    out = np.zeros((n_cells, shares.shape[1]))
    np.add.at(out, cell, shares)
    return out


def survival(area_share: np.ndarray, warheads: np.ndarray) -> np.ndarray:
    """P(no warhead falls in the area), one attacker: (1 - q)^W, draw by draw."""
    warheads = np.asarray(warheads, dtype=float)
    if (warheads < 0).any():
        raise ValueError("warheads cannot be negative")
    return np.power(np.clip(1.0 - area_share, 0.0, 1.0), warheads)
