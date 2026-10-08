"""Natural Earth vector layers (public domain), read from their GeoJSON files."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from nucprob.geo import densify


def line_points(path: Path, spacing_km: float = 2.0, keep=None, ids: bool = False):
    """(lat, lon) of points along every line of a layer, at most `spacing_km` apart, and with
    `ids` the number of the line each point lies on. `keep(properties) -> bool` selects
    features."""
    lats, lons, nums = [], [], []
    for f in json.loads(path.read_text(encoding="utf-8"))["features"]:
        if keep is not None and not keep(f["properties"]):
            continue
        geom = f["geometry"]
        if geom is None:
            continue
        lines = geom["coordinates"] if geom["type"].startswith("Multi") else [geom["coordinates"]]
        for line in lines:
            line = np.asarray(line, float)
            lon, lat = densify(line[:, 0], line[:, 1], spacing_km)
            lats.append(lat)
            lons.append(lon)
            nums.append(np.full(len(lat), len(nums)))
    if ids:
        return np.concatenate(lats), np.concatenate(lons), np.concatenate(nums)
    return np.concatenate(lats), np.concatenate(lons)


def points(path: Path) -> pd.DataFrame:
    """A point layer: its properties plus lat and lon."""
    rows = []
    for f in json.loads(path.read_text(encoding="utf-8"))["features"]:
        lon, lat = f["geometry"]["coordinates"][:2]
        rows.append({**f["properties"], "lat": lat, "lon": lon})
    return pd.DataFrame(rows)
