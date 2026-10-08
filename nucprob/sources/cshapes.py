"""CShapes 2.0 (Schvitz et al. 2022, ETH Zurich; CC BY-NC-SA 4.0): state borders and capitals
by date, colonies included as their own units. Only distances derived from it are committed.
"""

import json
from functools import cache
from pathlib import Path

import numpy as np

from nucprob.bloc import STUDY_DATE
from nucprob.geo import densify
from nucprob.paths import RAW

PATH = RAW / "cshapes" / "CShapes-2.0.geojson"


@cache
def _features(path: Path = PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["features"]


def units_on(date: tuple[int, int, int] = STUDY_DATE, path: Path = PATH) -> dict[str, dict]:
    """The units in existence on `date`, by name: capital (name, lat, lon) and polygons (each a
    list of rings of [lon, lat])."""
    out = {}
    for f in _features(path):
        p = f["properties"]
        start = (p["gwsyear"], p["gwsmonth"], p["gwsday"])
        end = (p["gweyear"], p["gwemonth"], p["gweday"])
        if not start <= date <= end:
            continue
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        out[p["cntry_name"]] = {
            "capital": p["capname"],
            "cap_lat": p["caplat"],
            "cap_lon": p["caplong"],
            "polygons": polys,
        }
    return out


def boundary(units: dict[str, dict], names, spacing_km: float = 5.0):
    """(lat, lon) of points along the outlines of the named units, at most `spacing_km` apart.
    For places outside those units, the nearest such point gives the distance to their territory.
    """
    missing = set(names) - set(units)
    assert not missing, f"not in CShapes on this date: {missing}"
    lats, lons = [], []
    for name in names:
        for poly in units[name]["polygons"]:
            for ring in poly:
                ring = np.asarray(ring, float)
                lon, lat = densify(ring[:, 0], ring[:, 1], spacing_km)
                lats.append(lat)
                lons.append(lon)
    return np.concatenate(lats), np.concatenate(lons)
