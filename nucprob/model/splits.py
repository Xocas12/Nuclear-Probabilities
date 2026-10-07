"""Spatial blocks and splits (PLAN section 5.2).

Places are grouped into square blocks of about BLOCK_KM on a side (sinusoidal projection), so
neighbouring towns, which share their targeting, stay on the same side of a split.
- The sealed test is SEALED_SHARE of the blocks, chosen with a fixed seed and balanced on the
  label; it is scored once, at the end (milestone M8), and excluded from everything before.
- Cross-validation assigns the remaining blocks to folds, balancing the positives per fold.
"""

import numpy as np
import pandas as pd

from nucprob.geo import EARTH_KM

BLOCK_KM = 300.0
SEALED_SHARE = 0.2
SEALED_SEED = 1956


def assign_blocks(lat, lon, size_km: float = BLOCK_KM, offset_km: float = 0.0) -> np.ndarray:
    """Block label "i_j" of each point on a grid of `size_km`, shifted by `offset_km`."""
    lat_r, lon_r = np.radians(lat), np.radians(lon)
    x = EARTH_KM * lon_r * np.cos(lat_r) + offset_km
    y = EARTH_KM * lat_r + offset_km
    i, j = np.floor(x / size_km).astype(int), np.floor(y / size_km).astype(int)
    return np.array([f"{a}_{b}" for a, b in zip(i, j, strict=True)])


def balanced_groups(blocks: pd.Series, y: pd.Series, n: int, seed: int) -> dict[str, int]:
    """Assign blocks to n groups: blocks in random order, each to the group with the fewest
    positives so far (ties: fewest places), so every group gets a similar share of positives."""
    rng = np.random.default_rng(seed)
    stats = pd.DataFrame({"block": blocks, "y": y}).groupby("block")["y"].agg(["sum", "size"])
    order = rng.permutation(stats.index.to_numpy())
    # Large blocks first, so the greedy balance has room to work.
    order = sorted(order, key=lambda b: -stats.at[b, "size"])
    pos, size = np.zeros(n), np.zeros(n)
    out = {}
    for b in order:
        g = int(np.lexsort((size, pos))[0])
        out[b] = g
        pos[g] += stats.at[b, "sum"]
        size[g] += stats.at[b, "size"]
    return out


def seal(
    blocks: pd.Series, y: pd.Series, share: float = SEALED_SHARE, seed: int = SEALED_SEED
) -> pd.Series:
    """True for places in the sealed test blocks."""
    groups = balanced_groups(blocks, y, round(1 / share), seed)
    return blocks.map(groups).eq(0)


def folds(blocks: pd.Series, y: pd.Series, k: int = 5, seed: int = 0) -> np.ndarray:
    groups = balanced_groups(blocks, y, k, seed)
    return blocks.map(groups).to_numpy()
