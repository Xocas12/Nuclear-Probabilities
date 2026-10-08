"""Transport family (PLAN section 3.2): railways, seaports and major rivers, from Natural
Earth. Its railways and ports are today's network standing in for 1956, so those features are
flagged; rivers are not, though reservoirs filled after 1956 are drawn as lake centrelines
along the old course."""

import numpy as np
import pandas as pd

from nucprob.features.geography import log_km, nearest_km
from nucprob.geo import Points
from nucprob.paths import RAW
from nucprob.sources import naturalearth

NE = RAW / "naturalearth"
BBOX = (5.0, 15.0)  # lines and points west of 5° E or south of 15° N never reach the bloc
JUNCTION_KM = 5
MAJOR_RIVER_RANK = 6  # Natural Earth scalerank: the Volga 3, the Don and the Oka 6


def in_bbox(lat, lon) -> np.ndarray:
    return ((lon > BBOX[0]) | (lon < -160)) & (lat > BBOX[1])


def rail(places: pd.DataFrame) -> pd.DataFrame:
    lat, lon = places["lat"].to_numpy(), places["lon"].to_numpy()
    rlat, rlon, line = naturalearth.line_points(NE / "ne_10m_railroads.geojson", 1.0, ids=True)
    keep = in_bbox(rlat, rlon)
    rlat, rlon, line = rlat[keep], rlon[keep], line[keep]
    out = pd.DataFrame(index=places.index)
    out["log_km_to_rail"] = log_km(nearest_km(lat, lon, rlat, rlon))
    near = Points(rlat, rlon).within(lat, lon, JUNCTION_KM)
    out["rail_lines_5km"] = [len(np.unique(line[idx])) for idx in near]
    return out


def ports(places: pd.DataFrame) -> pd.DataFrame:
    p = naturalearth.points(NE / "ne_10m_ports.geojson")
    p = p[in_bbox(p["lat"].to_numpy(), p["lon"].to_numpy())]
    out = pd.DataFrame(index=places.index)
    out["log_km_to_port"] = log_km(
        nearest_km(places["lat"], places["lon"], p["lat"].to_numpy(), p["lon"].to_numpy())
    )
    return out


def rivers(places: pd.DataFrame) -> pd.DataFrame:
    rlat, rlon = naturalearth.line_points(
        NE / "ne_10m_rivers_lake_centerlines.geojson",
        1.0,
        keep=lambda p: p.get("scalerank") is not None and p["scalerank"] <= MAJOR_RIVER_RANK,
    )
    keep = in_bbox(rlat, rlon)
    out = pd.DataFrame(index=places.index)
    out["log_km_to_major_river"] = log_km(
        nearest_km(places["lat"], places["lon"], rlat[keep], rlon[keep])
    )
    return out


def transport(places: pd.DataFrame) -> pd.DataFrame:
    return pd.concat([rail(places), ports(places), rivers(places)], axis=1)
