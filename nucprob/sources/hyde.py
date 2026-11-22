"""HYDE gridded population (Klein Goldewijk et al.): total, urban and rural inhabitants per
5 arc-minute cell (2160 x 4320 cells, -180..180, -90..90), by decade, and the people within a
given distance of any point at any date.

Which HYDE: version 3.2.1 (baseline scenario), from the DANS data station (CC0 on DANS; the
release readme says CC BY 3.0). HYDE 3.3 sits on geo.public.data.uu.nl, which answers automated
clients with a bot challenge, so it could not be fetched from here (see the card,
`data/curated/features/hyde.md`). 3.2.1 has the same grid and the same file names; it ends in
2017 instead of 2023.

The baseline archive is one 5.3 GB zip. `fetch()` reads only the members it needs, with HTTP
range requests, and converts each ASCII grid straight to a float32 `.npy` under
`data/raw/population_grids/hyde/` (no-data cells become 0), with a JSON log of the members.

    python -m nucprob.sources.hyde            # fetch the missing grids, then run the check
    python -m nucprob.sources.hyde --check    # the check only (city table in the card)

Use:
    grid(1960)                        -> (2160, 4320) float32 people per cell
    grid(1963, "urbc")                -> linear interpolation between 1960 and 1970
    pop_within(lat, lon, 1956, 25)    -> people within 25 km of each point
    urban_share_within(lat, lon, 1956, 25)

Discs are exact spherical caps sampled per cell row: each row is cut into `SUBROWS` strips,
each strip's longitude half-width comes from the spherical law of cosines, and the strip's
share of the row is read off a running sum along the row (people taken as spread evenly over
a cell). One running-sum table per grid is cached, so 10,000s of points take seconds.
Dates outside the stored years are clamped to the first or last year (1930, 2017).
"""

import argparse
import io
import json
import struct
import subprocess
import tempfile
import zipfile
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from nucprob.geo import EARTH_KM
from nucprob.paths import RAW

DANS_DOI = "doi:10.17026/DANS-25G-GEZ3"
DANS_FILE_ID = 5490328  # HYDE3_2_1-baseline.zip, SHA-1 0d0e4ff97deb59664ce6c34dfdeeafa08e487d20
DANS_URL = f"https://archaeology.datastations.nl/api/access/datafile/{DANS_FILE_ID}"
OUT = RAW / "population_grids" / "hyde"
YEARS = (1930, 1940, 1950, 1960, 1970, 1980, 1990, 2000, 2010, 2017)
VARIABLES = ("popc", "urbc", "rurc")  # total, urban, rural inhabitants per cell
NROWS, NCOLS, CELL = 2160, 4320, 1 / 12  # degrees; row 0 is the northernmost (90N..89.917N)
SUBROWS = 4


# --- download and conversion ---------------------------------------------------------------


class RangeFile(io.RawIOBase):
    """A read-only, seekable file over HTTP range requests (enough for zipfile)."""

    def __init__(self, url: str):
        first = requests.get(url, allow_redirects=False, timeout=60)
        self.url = first.headers.get("Location", url)  # DANS redirects to a signed S3 URL
        probe = requests.get(self.url, headers={"Range": "bytes=0-0"}, timeout=60)
        probe.raise_for_status()
        self.size = int(probe.headers["Content-Range"].split("/")[1])
        self.pos = 0

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        base = {0: 0, 1: self.pos, 2: self.size}[whence]
        self.pos = base + offset
        return self.pos

    def readinto(self, buf):
        n = min(len(buf), self.size - self.pos)
        if n <= 0:
            return 0
        r = requests.get(
            self.url, headers={"Range": f"bytes={self.pos}-{self.pos + n - 1}"}, timeout=600
        )
        r.raise_for_status()
        data = r.content
        buf[: len(data)] = data
        self.pos += len(data)
        return len(data)


def member_name(var: str, year: int) -> str:
    return f"baseline/asc/{year}AD_pop/{var}_{year}AD.asc"


def read_member(raw: io.BufferedReader, info: zipfile.ZipInfo) -> bytes:
    """One member's uncompressed bytes. The archive uses Deflate64 (method 9), which Python's
    zipfile cannot read, so the member's local header and data are copied into a one-member
    zip in memory and Info-ZIP `unzip -p` (which reads Deflate64) inflates it; unzip checks
    the CRC."""
    raw.seek(info.header_offset)
    local = raw.read(30)
    name_len, extra_len = struct.unpack("<HH", local[26:30])
    rest = raw.read(name_len + extra_len + info.compress_size)
    body = local + rest
    name = info.filename.encode()
    central = (
        struct.pack(
            "<4s6H3L5H2L",
            b"PK\x01\x02",
            20,
            local[4] | local[5] << 8,
            info.flag_bits,
            info.compress_type,
            *struct.unpack("<HH", local[10:14]),
            info.CRC,
            info.compress_size,
            info.file_size,
            len(name),
            0,
            0,
            0,
            0,
            0,
            0,
        )
        + name
    )
    end = struct.pack("<4s4H2LH", b"PK\x05\x06", 0, 0, 1, 1, len(central), len(body), 0)
    with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
        tmp.write(body + central + end)
        tmp.flush()
        return subprocess.run(["unzip", "-p", tmp.name], check=True, capture_output=True).stdout


def parse_asc(text: str) -> np.ndarray:
    """An ESRI ASCII grid as float32, no-data cells set to 0."""
    lines = text.split("\n", 6)
    header = {k.lower(): float(v) for k, v in (ln.split() for ln in lines[:6])}
    values = np.array(lines[6].split(), dtype=np.float32)
    nrows, ncols = int(header["nrows"]), int(header["ncols"])
    assert (nrows, ncols) == (NROWS, NCOLS), header
    values = values.reshape(nrows, ncols)
    values[values == header.get("nodata_value", -9999)] = 0
    return values


def path(var: str, year: int, out: Path = OUT) -> Path:
    return out / f"{var}_{year}.npy"


def fetch(years=YEARS, variables=VARIABLES, out: Path = OUT) -> None:
    """Convert the missing (variable, year) grids; log member CRCs and sizes."""
    out.mkdir(parents=True, exist_ok=True)
    log_path = out / "members.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {}
    todo = [(v, y) for y in years for v in variables if not path(v, y, out).exists()]
    if not todo:
        return
    raw = io.BufferedReader(RangeFile(DANS_URL), 4 << 20)
    archive = zipfile.ZipFile(raw)
    for var, year in todo:
        info = archive.getinfo(member_name(var, year))
        text = read_member(raw, info).decode("ascii")
        arr = parse_asc(text)
        np.save(path(var, year, out), arr)
        log[info.filename] = {
            "crc32": f"{info.CRC:08x}",
            "file_size": info.file_size,
            "compress_size": info.compress_size,
            "npy": path(var, year, out).name,
            "total": float(arr.sum(dtype=np.float64)),
        }
        log_path.write_text(json.dumps(log, indent=1, sort_keys=True))
        print(f"{var} {year}: {arr.sum(dtype=np.float64) / 1e6:,.0f} million")


# --- grids ---------------------------------------------------------------------------------


@lru_cache(maxsize=64)
def stored(var: str, year: int) -> np.ndarray:
    return np.load(path(var, year), mmap_mode="r")


def bracket(year: float) -> tuple[int, int, float]:
    """The stored years around `year` and the weight of the later one (clamped at the ends)."""
    year = float(np.clip(year, YEARS[0], YEARS[-1]))
    i = int(np.searchsorted(YEARS, year, side="right")) - 1
    i = min(i, len(YEARS) - 2)
    y0, y1 = YEARS[i], YEARS[i + 1]
    return y0, y1, (year - y0) / (y1 - y0)


def grid(year: float, var: str = "popc") -> np.ndarray:
    """People per cell (float32, row 0 = north) at `year`, linear between stored years."""
    y0, y1, w = bracket(year)
    if w == 0:
        return np.asarray(stored(var, y0))
    if w == 1:
        return np.asarray(stored(var, y1))
    return ((1 - w) * stored(var, y0) + w * stored(var, y1)).astype(np.float32)


@lru_cache(maxsize=24)
def row_cumsum(var: str, year: int) -> np.ndarray:
    """(NROWS, NCOLS + 1) running sums along each row, float64, starting at 0."""
    g = np.asarray(stored(var, year), dtype=np.float64)
    out = np.zeros((NROWS, NCOLS + 1))
    np.cumsum(g, axis=1, out=out[:, 1:])
    return out


def periodic_cumsum(cs: np.ndarray, rows: np.ndarray, x: np.ndarray) -> np.ndarray:
    """People in `rows` from column edge 0 to fractional column `x` (any real number; the
    grid wraps in longitude), with people spread evenly within a cell."""
    turns = np.floor(x / NCOLS)
    r = x - turns * NCOLS
    j = np.minimum(r.astype(np.int64), NCOLS - 1)
    f = r - j
    left, right = cs[rows, j], cs[rows, j + 1]
    return turns * cs[rows, NCOLS] + left + f * (right - left)


def disc_strips(lat, lon, km: float):
    """For each point, the rows, strip weights and column half-widths of its disc's strips."""
    lat = np.asarray(lat, float)[:, None]
    lon = np.asarray(lon, float)[:, None]
    delta = km / EARTH_KM  # angular radius, radians
    reach = np.degrees(delta)
    nstrips = int(np.ceil(2 * reach / CELL) + 2) * SUBROWS
    top = np.floor((90 - (lat + reach)) / CELL) * CELL  # degrees south of 90N of the first row
    k = np.arange(nstrips)[None, :]
    south = top + (k + 0.5) * CELL / SUBROWS  # strip centres, degrees south of the pole
    rows = np.floor(south / CELL).astype(np.int64)
    slat = 90 - south
    phi0, phi = np.radians(lat), np.radians(slat)
    with np.errstate(invalid="ignore", divide="ignore"):
        cosdl = (np.cos(delta) - np.sin(phi0) * np.sin(phi)) / (np.cos(phi0) * np.cos(phi))
    inside = (np.abs(slat - lat) <= reach) & (rows >= 0) & (rows < NROWS)
    half = np.degrees(np.arccos(np.clip(np.nan_to_num(cosdl, nan=-1.0), -1, 1))) / CELL
    x = (lon + 180) / CELL
    return np.clip(rows, 0, NROWS - 1), inside / SUBROWS, x - half, x + half


def within_stored(var: str, year: int, lat, lon, km: float, chunk: int = 4096) -> np.ndarray:
    cs = row_cumsum(var, year)
    lat, lon = np.atleast_1d(lat).astype(float), np.atleast_1d(lon).astype(float)
    out = np.empty(len(lat))
    for s in range(0, len(lat), chunk):
        rows, weight, x0, x1 = disc_strips(lat[s : s + chunk], lon[s : s + chunk], km)
        part = periodic_cumsum(cs, rows, x1) - periodic_cumsum(cs, rows, x0)
        out[s : s + chunk] = (weight * part).sum(axis=1)
    return out


def within(var: str, lat, lon, year: float, km: float) -> np.ndarray:
    y0, y1, w = bracket(year)
    a = within_stored(var, y0, lat, lon, km)
    if w == 0:
        return a
    return (1 - w) * a + w * within_stored(var, y1, lat, lon, km)


def pop_within(lat, lon, year: float, km: float) -> np.ndarray:
    """People within `km` (great-circle) of each point at `year` (fractional years allowed)."""
    return within("popc", lat, lon, year, km)


def urban_share_within(lat, lon, year: float, km: float) -> np.ndarray:
    """Urban people / all people within `km` of each point (NaN where nobody lives)."""
    urb = within("urbc", lat, lon, year, km)
    tot = within("popc", lat, lon, year, km)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(tot > 0, urb / tot, np.nan)


# --- check against census-based city figures ----------------------------------------------

# Reference figures are read from files, never typed in:
# - UN WUP 2018 file 12 (urban agglomerations, census-based; its coordinates are used);
# - pop-stat.mashke.org, Russia page: 1959 census, city proper within today's boundaries,
#   with coordinates from the WUP row of the same city.
WUP_CHECKS = [  # WUP agglomeration name, country, year
    ("New York-Newark", "United States of America", 1950),
    ("Chicago", "United States of America", 1960),
    ("Los Angeles-Long Beach-Santa Ana", "United States of America", 1970),
    ("London", "United Kingdom", 1950),
    ("Paris", "France", 1960),
    ("Berlin", "Germany", 1960),
    ("Warszawa (Warsaw)", "Poland", 1960),
    ("Budapest", "Hungary", 1970),
    ("Praha (Prague)", "Czechia", 1960),
    ("Moskva (Moscow)", "Russian Federation", 1960),
    ("Kyiv (Kiev)", "Ukraine", 1960),
    ("Tokyo", "Japan", 1960),
    ("Beijing", "China", 1950),
    ("Mumbai (Bombay)", "India", 1970),
    ("Al-Qahirah (Cairo)", "Egypt", 1960),
    ("São Paulo", "Brazil", 1980),
]
POPSTAT_CHECKS = [  # pop-stat name (Russia page), WUP name for the coordinates
    ("Москва", "Moskva (Moscow)"),
    ("Санкт-Петербург", "Sankt Peterburg (Saint Petersburg)"),
    ("Новосибирск", "Novosibirsk"),
    ("Екатеринбург", "Yekaterinburg"),
]


def reference_figures() -> list[dict]:
    from nucprob.sources import historical_cities, popstat

    wup = historical_cities.load_wup()
    notes = historical_cities.wup_notes()
    rows = []
    for name, country, year in WUP_CHECKS:
        r = wup[(wup["name"] == name) & (wup["country"] == country) & (wup["year"] == year)]
        r = r.iloc[0]
        note = "" if pd.isna(r["note"]) else notes.get(int(r["note"]), "")
        rows.append(
            dict(
                city=name,
                lat=r["lat"],
                lon=r["lon"],
                year=year,
                ref=r["pop"],
                source="WUP 2018 agglomeration" + (f" (note {r['note']})" if note else ""),
            )
        )
    russia = popstat.parse(RAW / "popstat" / "russia-cities.htm", "russia")
    for name_ru, wup_name in POPSTAT_CHECKS:
        pop = russia.loc[russia["name_ru"] == name_ru, "pop_1959-01-15"].iloc[0]
        r = wup[wup["name"] == wup_name].iloc[0]
        rows.append(
            dict(
                city=f"{wup_name.split(' (')[0]} (city)",
                lat=r["lat"],
                lon=r["lon"],
                year=1959,
                ref=pop,
                source="1959 census, city proper (pop-stat)",
            )
        )
    return rows


def check(radii=(25, 50)) -> list[dict]:
    rows = reference_figures()
    for r in rows:
        for km in radii:
            r[f"hyde_{km}"] = float(pop_within([r["lat"]], [r["lon"]], r["year"], km)[0])
        r["urban_share_25"] = float(urban_share_within([r["lat"]], [r["lon"]], r["year"], 25)[0])
    return rows


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="only print the census check")
    args = parser.parse_args(argv)
    if not args.check:
        fetch()
    print(
        "| city | year | reference | HYDE 25 km | ratio | HYDE 50 km | ratio | urban share "
        "25 km | reference figure |"
    )
    print("|---|---|---:|---:|---:|---:|---:|---:|---|")
    for r in check():
        print(
            f"| {r['city']} | {r['year']} | {r['ref'] / 1e6:.2f} M | {r['hyde_25'] / 1e6:.2f} M "
            f"| {r['hyde_25'] / r['ref']:.2f} | {r['hyde_50'] / 1e6:.2f} M | "
            f"{r['hyde_50'] / r['ref']:.2f} | {r['urban_share_25']:.2f} | {r['source']} |"
        )


if __name__ == "__main__":
    main()
