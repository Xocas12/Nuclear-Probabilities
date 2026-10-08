"""Load GeoNames country dumps (CC BY 4.0): populated places with coordinates, feature codes,
first-level region codes, modern populations and every alternate name.

Feature codes used later: PPLC = national capital, PPLA = seat of a first-level region,
PPLA2..PPLA4 = seats of lower levels, PPL = other populated place. They describe today's
administrative map, so features built on them carry an anachronism flag.
"""

import io
import zipfile
from pathlib import Path

import pandas as pd

from nucprob.paths import RAW

COLUMNS = [
    "geonameid",
    "name",
    "asciiname",
    "alternatenames",
    "lat",
    "lon",
    "feature_class",
    "feature_code",
    "country",
    "cc2",
    "admin1",
    "admin2",
    "admin3",
    "admin4",
    "population",
    "elevation",
    "dem",
    "timezone",
    "modified",
]


def load_country(code: str, raw: Path = RAW) -> pd.DataFrame:
    """Populated places (feature class P) of one country."""
    with zipfile.ZipFile(raw / "geonames" / f"{code}.zip") as zf:
        data = zf.read(f"{code}.txt")
    df = pd.read_csv(
        io.BytesIO(data),
        sep="\t",
        header=None,
        names=COLUMNS,
        dtype={"admin1": str, "admin2": str},
        keep_default_na=False,
        na_values={"population": [""], "elevation": [""]},
        quoting=3,
    )
    df = df[df["feature_class"] == "P"].copy()
    df["population"] = pd.to_numeric(df["population"], errors="coerce").fillna(0).astype(int)
    df["dem"] = pd.to_numeric(df["dem"], errors="coerce")  # SRTM3 or GTOPO30 mean elevation, m
    return df.drop(columns=["cc2", "admin3", "admin4", "timezone", "modified"])


def load_admin1(raw: Path = RAW) -> pd.DataFrame:
    df = pd.read_csv(
        raw / "geonames" / "admin1CodesASCII.txt",
        sep="\t",
        header=None,
        names=["code", "name", "asciiname", "geonameid"],
        keep_default_na=False,
        quoting=3,
    )
    df[["country", "admin1"]] = df["code"].str.split(".", n=1, expand=True)
    return df
