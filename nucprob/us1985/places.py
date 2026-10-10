"""The universe of US counties in 1985.

    python -m nucprob.us1985.places

Every county (and county equivalent: parishes, boroughs, census areas, independent cities) of
the 50 states and DC in the Census Bureau's 1990 cartographic boundaries (co99_d90), with its
population from the Census Bureau's intercensal estimates (1980 census, 1985 estimate), its
land area and centroid from the boundary file. The universe is every county: unlike the 1956
towns there is no population threshold, since the label (NAPB-90's risk band) covers them all.

Writes data/processed/us_counties_1985.parquet.
"""

import numpy as np
import pandas as pd
import shapefile
from shapely.geometry import shape
from shapely.ops import unary_union

from nucprob.paths import PROCESSED
from nucprob.sources import census_us

SHP = census_us.DIR / "co99_d90" / "co99_d90"
SQM_PER_SQMI = 2.589988e6
EARTH_R_KM = 6371.0088


def geometries() -> pd.DataFrame:
    """One row per county FIPS code: its (multi)polygon, merged over the file's parts."""
    reader = shapefile.Reader(str(SHP), encoding="latin-1")
    fields = [f[0] for f in reader.fields[1:]]
    parts: dict[str, list] = {}
    names: dict[str, str] = {}
    for sr in reader.iterShapeRecords():
        rec = dict(zip(fields, sr.record, strict=True))
        fips = f"{rec['ST']}{rec['CO']}"
        parts.setdefault(fips, []).append(shape(sr.shape.__geo_interface__))
        names[fips] = rec["NAME"]
    rows = [
        {"fips": f, "shape_name": names[f], "geometry": unary_union(g)} for f, g in parts.items()
    ]
    return pd.DataFrame(rows)


def area_sqmi(geom) -> float:
    """Approximate area of a lon/lat polygon: planar area scaled by cos(latitude)."""
    lat = np.radians(geom.centroid.y)
    deg = np.radians(1.0) * EARTH_R_KM * 1000
    return geom.area * deg * deg * np.cos(lat) / SQM_PER_SQMI


def build() -> pd.DataFrame:
    all_rows = census_us.estimates()
    est = all_rows[all_rows["level"] == "county"].rename(columns={"name": "census_name"})
    st = all_rows[all_rows["level"] == "state"]
    states = pd.Series(st["name"].to_numpy(), index=st["fips"].str[:2])
    geo = geometries()
    df = est.merge(geo, on="fips", how="left")
    df["state_fips"] = df["fips"].str[:2]
    df["state"] = df["state_fips"].map(states)
    point = df["geometry"].map(lambda g: g.representative_point() if g is not None else None)
    df["lat"] = point.map(lambda p: p.y if p is not None else np.nan)
    df["lon"] = point.map(lambda p: p.x if p is not None else np.nan)
    df["area_sqmi"] = df["geometry"].map(lambda g: area_sqmi(g) if g is not None else np.nan)
    df["pop"] = df["pop_1985"]
    df["has_geometry"] = df["geometry"].notna()
    return df


def main() -> None:
    df = build()
    out = df.drop(columns=["geometry"])
    out.to_parquet(PROCESSED / "us_counties_1985.parquet", index=False)
    print(
        f"{len(out)} counties, {int(out['has_geometry'].sum())} with a boundary; "
        f"1985 population {out['pop'].sum():,.0f}"
    )
    missing = out[~out["has_geometry"]]
    if len(missing):
        print("no boundary:", ", ".join(missing["fips"] + " " + missing["census_name"]))


if __name__ == "__main__":
    main()
