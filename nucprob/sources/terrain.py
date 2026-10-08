"""Elevation from the AWS Terrain Tiles: open data from Mapzen/Tilezen, merged from SRTM,
GMTED2010, ETOPO1 and other sources (https://registry.opendata.aws/terrain-tiles/), in the
"terrarium" PNG encoding.

    python -m nucprob.sources.terrain   # fetch the tiles the place table needs

Tiles are cached in data/raw/terrain/<zoom>/<x>/<y>.png (git-ignored), and data/raw/terrain/
tiles.csv records each tile's sha256. At zoom 7 a pixel is about 1.2 km wide at the equator and
0.7 km at 55° N: enough for elevation and local relief within 10 km of a town.
"""

import sys
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

from nucprob.paths import PROCESSED, RAW
from nucprob.sources.fetch import download, sha256

ZOOM = 7
URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
DIR = RAW / "terrain"
TILE = 256
M_PER_PX_Z0 = 2 * np.pi * 6378137 / TILE  # metres per pixel at the equator at zoom 0


def to_pixel(lat, lon, z: int = ZOOM):
    """Global Web Mercator pixel coordinates (x, y) at zoom z."""
    n = TILE * 2**z
    x = (np.asarray(lon, float) + 180) / 360 * n
    y = (1 - np.arcsinh(np.tan(np.radians(lat))) / np.pi) / 2 * n
    return x, y


def radius_px(lat, radius_km: float, z: int = ZOOM):
    return radius_km * 1000 / (M_PER_PX_Z0 * np.cos(np.radians(lat)) / 2**z)


def tile_path(z: int, x: int, y: int) -> Path:
    return DIR / str(z) / str(x) / f"{y}.png"


def decode(path: Path) -> np.ndarray:
    """Elevation in metres (sea floor negative) of one terrarium tile."""
    rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32)
    return rgb[..., 0] * 256 + rgb[..., 1] + rgb[..., 2] / 256 - 32768


@lru_cache(maxsize=1024)
def tile(z: int, x: int, y: int) -> np.ndarray:
    path = tile_path(z, x, y)
    if not path.exists():
        download(URL.format(z=z, x=x, y=y), path)
    return decode(path)


def _bounds(lat: float, lon: float, radius_km: float, z: int):
    px, py = to_pixel(lat, lon, z)
    r = radius_px(lat, radius_km, z)
    last = TILE * 2**z - 1
    x0, x1 = int(np.floor(px - r)), int(np.floor(px + r))
    y0, y1 = max(0, int(np.floor(py - r))), min(last, int(np.floor(py + r)))
    return float(px), float(py), float(r), x0, x1, y0, y1


def tiles_for(lat, lon, radius_km: float, z: int = ZOOM) -> set[tuple[int, int, int]]:
    """Every tile a window of `radius_km` around each point touches."""
    out = set()
    for la, lo in zip(np.atleast_1d(lat), np.atleast_1d(lon), strict=True):
        _, _, _, x0, x1, y0, y1 = _bounds(la, lo, radius_km, z)
        for ty in range(y0 // TILE, y1 // TILE + 1):
            for tx in range(x0 // TILE, x1 // TILE + 1):
                out.add((z, tx % 2**z, ty))
    return out


def fetch(tiles, workers: int = 16) -> None:
    todo = sorted(t for t in tiles if not tile_path(*t).exists())
    if not todo:
        return
    print(f"fetching {len(todo)} terrain tiles", file=sys.stderr)
    with ThreadPoolExecutor(workers) as pool:
        list(pool.map(lambda t: download(URL.format(z=t[0], x=t[1], y=t[2]), tile_path(*t)), todo))


def window(lat: float, lon: float, radius_km: float, z: int = ZOOM):
    """Elevations of the pixels whose centres lie within `radius_km` of the point, and the
    elevation of the pixel the point falls in."""
    px, py, r, x0, x1, y0, y1 = _bounds(lat, lon, radius_km, z)
    grid = np.empty((y1 - y0 + 1, x1 - x0 + 1), dtype=np.float32)
    for ty in range(y0 // TILE, y1 // TILE + 1):
        for tx in range(x0 // TILE, x1 // TILE + 1):
            arr = tile(z, tx % 2**z, ty)
            gx0, gx1 = max(x0, tx * TILE), min(x1, tx * TILE + TILE - 1)
            gy0, gy1 = max(y0, ty * TILE), min(y1, ty * TILE + TILE - 1)
            grid[gy0 - y0 : gy1 - y0 + 1, gx0 - x0 : gx1 - x0 + 1] = arr[
                gy0 - ty * TILE : gy1 - ty * TILE + 1, gx0 - tx * TILE : gx1 - tx * TILE + 1
            ]
    yy, xx = np.mgrid[y0 : y1 + 1, x0 : x1 + 1]
    inside = np.hypot(xx + 0.5 - px, yy + 0.5 - py) <= r
    return grid[inside], float(grid[int(py) - y0, int(px) - x0])


def relief(lat, lon, radius_km: float = 10.0, z: int = ZOOM) -> pd.DataFrame:
    """Per point: elevation (m) and local relief (highest minus lowest point within
    `radius_km`, m). The sea counts as 0 m, so a coastal town's relief is its land's, not the
    sea floor's."""
    lat, lon = np.atleast_1d(lat), np.atleast_1d(lon)
    fetch(tiles_for(lat, lon, radius_km, z))
    px, py = to_pixel(lat, lon, z)
    order = np.lexsort((px // TILE, py // TILE))  # tile by tile, for the cache
    elev, rel = np.empty(len(lat)), np.empty(len(lat))
    for i in order:
        values, centre = window(lat[i], lon[i], radius_km, z)
        values = np.maximum(values, 0)
        elev[i] = max(centre, 0)
        rel[i] = values.max() - values.min()
    return pd.DataFrame({"elevation_m": elev, "relief_m": rel})


def record() -> None:
    """Write data/raw/terrain/tiles.csv: every cached tile and its sha256."""
    rows = [
        {"tile": p.relative_to(DIR).as_posix(), "sha256": sha256(p)}
        for p in sorted(DIR.glob("*/*/*.png"))
    ]
    pd.DataFrame(rows).to_csv(DIR / "tiles.csv", index=False)
    print(f"{len(rows)} tiles recorded in {DIR / 'tiles.csv'}")


def main() -> None:
    places = pd.read_parquet(PROCESSED / "places_1956.parquet")
    places = places[places["has_coords"]]
    fetch(tiles_for(places["lat"].to_numpy(), places["lon"].to_numpy(), 10.0))
    record()


if __name__ == "__main__":
    main()
