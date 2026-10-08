"""Small geometry helpers on the sphere (no GIS stack needed for the slice)."""

import numpy as np
from sklearn.neighbors import BallTree

EARTH_KM = 6371.0088


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in km; arguments in degrees, broadcastable."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dlat, dlon = p2 - p1, np.radians(np.asarray(lon2) - np.asarray(lon1))
    a = np.sin(dlat / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dlon / 2) ** 2
    return 2 * EARTH_KM * np.arcsin(np.sqrt(a))


class Points:
    """Nearest-neighbour and radius queries on a set of (lat, lon) points."""

    def __init__(self, lat, lon):
        self.tree = BallTree(np.radians(np.column_stack([lat, lon])), metric="haversine")

    def nearest(self, lat, lon, k: int = 1):
        """(distances in km, indices), each of shape (n, k)."""
        dist, idx = self.tree.query(np.radians(np.column_stack([lat, lon])), k=k)
        return dist * EARTH_KM, idx

    def within(self, lat, lon, radius_km: float):
        """For each query point, the indices of the points within `radius_km`."""
        return self.tree.query_radius(
            np.radians(np.column_stack([lat, lon])), r=radius_km / EARTH_KM
        )


def densify(lon, lat, spacing_km: float):
    """The vertices of a line (lon, lat in degrees) plus points interpolated between them, so
    that no two consecutive points are more than `spacing_km` apart. A segment that jumps across
    the 180th meridian is left as it is."""
    lon, lat = np.asarray(lon, float), np.asarray(lat, float)
    if len(lon) < 2:
        return lon, lat
    dlon, dlat = np.diff(lon), np.diff(lat)
    seg = haversine_km(lat[:-1], lon[:-1], lat[1:], lon[1:])
    n = np.maximum(1, np.ceil(seg / spacing_km)).astype(int)
    n[np.abs(dlon) > 180] = 1
    i = np.repeat(np.arange(len(seg)), n)
    t = np.concatenate([np.arange(k) / k for k in n])
    return (
        np.append(lon[i] + t * dlon[i], lon[-1]),
        np.append(lat[i] + t * dlat[i], lat[-1]),
    )
