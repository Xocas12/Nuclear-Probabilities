"""Features of US counties as of 1985 (PLAN section 3.2, applied to the US for NAPB-90).

    python -m nucprob.us1985.features

Every feature names its sources and flags later knowledge (FEATURES below; the table is
written to data/FEATURES_US.md). None reads NAPB-90 or another US target list: the label
sources are guarded in tests/test_leakage.py.

Distances run from the county's representative point (a point inside it, near its centre);
"in the county" counts use the 1990 boundary. Writes data/processed/features_us1985.parquet.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
import shapely
from shapely import STRtree

from nucprob.features.geography import log_km, nearest_km
from nucprob.geo import Points, haversine_km
from nucprob.paths import CURATED, PROCESSED, RAW, ROOT
from nucprob.sources import naturalearth, terrain
from nucprob.us1985 import places as us_places

YEAR = 1985
NE = RAW / "naturalearth"
CENSUS = ("census_us_estimates_1980s", "census_us_boundaries_1990")
CAPITALS = ("curated:features/us_capitals_1985.csv",)
MILITARY = ("curated:features/us_military_sites_1985.csv",)
WRI = ("wri_gppd",)
WRI_NOTE = (
    "plants still operating in the database's year whose commissioning year is 1985 or earlier"
)
NE_IDS = ("naturalearth_10m_*",)
# Roles of the curated military table, grouped into distance features.
MILITARY_ROLES = {
    "log_km_to_sac_base": (
        "sac_bomber",
        "sac_bomber_b1b",
        "sac_tanker",
        "sac_reconnaissance",
    ),
    "log_km_to_icbm": (
        "icbm_wing",
        "icbm_wing_titan",
        "icbm_wing_peacekeeper",
        "missile_field",
        "icbm_test_base",
    ),
    "log_km_to_ssbn_base": ("ssbn_base",),
    "log_km_to_naval_base": ("naval_base", "naval_shipyard", "fleet_hq", "ssbn_base"),
    "log_km_to_army_post": ("army_major_post", "army_corps_division_hq", "marine_corps_base"),
    "log_km_to_air_base": ("usaf_tac", "usaf_mac", "usaf_other"),
    "log_km_to_nuclear_weapons_site": ("nuclear_weapons_complex",),
    "log_km_to_command_centre": ("command_centre",),
}


@dataclass(frozen=True)
class Feature:
    family: str
    source: str
    sources: tuple[str, ...]
    anachronism: bool = False
    note: str = ""


FEATURES = {
    "log_pop": Feature("population", "Census Bureau estimate, July 1985", CENSUS),
    "log_density": Feature("population", "1985 estimate over the 1990 boundary's area", CENSUS),
    "growth_1980_85": Feature("population", "1980 census to 1985 estimate", CENSUS),
    "log_pop_within_50km": Feature(
        "population", "1985 estimates", CENSUS, note="counties whose point lies within 50 km"
    ),
    "log_pop_within_100km": Feature("population", "1985 estimates", CENSUS),
    "state_capital": Feature("administrative", "state capitals", CAPITALS),
    "national_capital": Feature("administrative", "Washington, D.C.", CAPITALS),
    "log_km_to_state_capital": Feature("administrative", "state capitals", CAPITALS),
    "log_km_to_washington": Feature("administrative", "Washington, D.C.", CAPITALS),
    "log_area": Feature("geography", "1990 boundary", CENSUS),
    "elevation_m": Feature(
        "geography", "AWS Terrain Tiles", ("aws_terrain_tiles",), True, "today's terrain"
    ),
    "log_relief_10km": Feature("geography", "AWS Terrain Tiles", ("aws_terrain_tiles",), True),
    "log_km_to_coast": Feature("geography", "Natural Earth coastline", NE_IDS),
    "log_power_mw_county": Feature("industry", "WRI power plants", WRI, True, WRI_NOTE),
    "log_power_mw_25km": Feature("industry", "WRI power plants", WRI, True, WRI_NOTE),
    "log_km_to_rail": Feature("transport", "Natural Earth railroads", NE_IDS, True),
    "rail_lines_10km": Feature("transport", "Natural Earth railroads", NE_IDS, True),
    "log_km_to_port": Feature("transport", "Natural Earth ports", NE_IDS, True),
    "log_km_to_major_river": Feature("transport", "Natural Earth rivers", NE_IDS),
    "log_airports_county": Feature(
        "transport", "OurAirports", ("ourairports",), True, "today's list, open and closed"
    ),
    **{
        name: Feature("military", "curated US military sites, mid-1985", MILITARY)
        for name in MILITARY_ROLES
    },
    "military_sites_county": Feature("military", "curated US military sites", MILITARY),
}


def within_sum(lat, lon, values, km: float) -> np.ndarray:
    near = Points(lat, lon).within(lat, lon, km)
    return np.array([values[idx].sum() for idx in near])


def in_county(geoms: list, lat, lon) -> np.ndarray:
    """Index (into geoms) of the county each point falls in, -1 for none."""
    tree = STRtree(geoms)
    pts = shapely.points(np.asarray(lon, float), np.asarray(lat, float))
    out = np.full(len(pts), -1)
    hit_pts, hit_geoms = tree.query(pts, predicate="within")
    out[hit_pts] = hit_geoms
    return out


def population(c: pd.DataFrame) -> pd.DataFrame:
    lat, lon, pop = c["lat"].to_numpy(), c["lon"].to_numpy(), c["pop"].to_numpy(float)
    out = pd.DataFrame(index=c.index)
    out["log_pop"] = np.log10(pop)
    out["log_density"] = np.log10(pop / c["area_sqmi"])
    out["growth_1980_85"] = pop / c["pop_1980"] - 1
    for km in (50, 100):
        out[f"log_pop_within_{km}km"] = np.log10(within_sum(lat, lon, pop, km))
    return out


def administrative(c: pd.DataFrame) -> pd.DataFrame:
    caps = pd.read_csv(CURATED / "features" / "us_capitals_1985.csv", dtype={"fips": str})
    pts = c.set_index("fips")[["lat", "lon", "state_fips"]]
    caps = caps.join(pts, on="fips")
    out = pd.DataFrame(index=c.index)
    out["state_capital"] = c["fips"].isin(caps.loc[caps["role"] == "state capital", "fips"])
    out["national_capital"] = c["fips"].isin(caps.loc[caps["role"] == "national capital", "fips"])
    own = c["state_fips"].map(caps.set_index("state_fips")[["lat", "lon"]].to_dict("index"))
    out["log_km_to_state_capital"] = log_km(
        [
            haversine_km(la, lo, o["lat"], o["lon"]) if isinstance(o, dict) else np.nan
            for la, lo, o in zip(c["lat"], c["lon"], own, strict=True)
        ]
    )
    dc = caps[caps["role"] == "national capital"].iloc[0]
    out["log_km_to_washington"] = log_km(haversine_km(c["lat"], c["lon"], dc["lat"], dc["lon"]))
    return out.astype({"state_capital": int, "national_capital": int})


def geography(c: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=c.index)
    out["log_area"] = np.log10(c["area_sqmi"])
    rel = terrain.relief(c["lat"].to_numpy(), c["lon"].to_numpy(), 10.0)
    out["elevation_m"] = rel["elevation_m"].to_numpy()
    out["log_relief_10km"] = np.log10(1 + rel["relief_m"].to_numpy())
    clat, clon = naturalearth.line_points(NE / "ne_10m_coastline.geojson", 2.0)
    keep = (clon < -60) & (clat > 15)
    out["log_km_to_coast"] = log_km(nearest_km(c["lat"], c["lon"], clat[keep], clon[keep]))
    return out


def industry(c: pd.DataFrame, geoms: list) -> pd.DataFrame:
    w = pd.read_csv(RAW / "wri" / "global_power_plant_database.csv", low_memory=False)
    w = w[(w["country"] == "USA") & (w["commissioning_year"] <= YEAR)]
    plat, plon, mw = (
        w["latitude"].to_numpy(),
        w["longitude"].to_numpy(),
        w["capacity_mw"].to_numpy(),
    )
    out = pd.DataFrame(index=c.index)
    idx = in_county(geoms, plat, plon)
    per = np.bincount(idx[idx >= 0], weights=mw[idx >= 0], minlength=len(c))
    out["log_power_mw_county"] = np.log10(1 + per)
    near = Points(plat, plon).within(c["lat"].to_numpy(), c["lon"].to_numpy(), 25.0)
    out["log_power_mw_25km"] = np.log10(1 + np.array([mw[i].sum() for i in near]))
    return out


def transport(c: pd.DataFrame, geoms: list) -> pd.DataFrame:
    lat, lon = c["lat"].to_numpy(), c["lon"].to_numpy()
    us = lambda la, lo: (lo < -60) & (la > 15)  # noqa: E731
    out = pd.DataFrame(index=c.index)
    rlat, rlon, line = naturalearth.line_points(NE / "ne_10m_railroads.geojson", 1.0, ids=True)
    k = us(rlat, rlon)
    rlat, rlon, line = rlat[k], rlon[k], line[k]
    out["log_km_to_rail"] = log_km(nearest_km(lat, lon, rlat, rlon))
    near = Points(rlat, rlon).within(lat, lon, 10.0)
    out["rail_lines_10km"] = [len(np.unique(line[i])) for i in near]
    p = naturalearth.points(NE / "ne_10m_ports.geojson")
    p = p[us(p["lat"].to_numpy(), p["lon"].to_numpy())]
    out["log_km_to_port"] = log_km(nearest_km(lat, lon, p["lat"].to_numpy(), p["lon"].to_numpy()))
    vlat, vlon = naturalearth.line_points(
        NE / "ne_10m_rivers_lake_centerlines.geojson",
        1.0,
        keep=lambda q: q.get("scalerank") is not None and q["scalerank"] <= 6,
    )
    k = us(vlat, vlon)
    out["log_km_to_major_river"] = log_km(nearest_km(lat, lon, vlat[k], vlon[k]))
    a = pd.read_csv(RAW / "ourairports" / "airports.csv", low_memory=False)
    a = a[
        (a["iso_country"] == "US")
        & a["type"].isin(["large_airport", "medium_airport", "small_airport"])
    ]
    idx = in_county(geoms, a["latitude_deg"].to_numpy(), a["longitude_deg"].to_numpy())
    out["log_airports_county"] = np.log10(1 + np.bincount(idx[idx >= 0], minlength=len(c)))
    return out


def military(c: pd.DataFrame, geoms: list) -> pd.DataFrame:
    path = CURATED / "features" / "us_military_sites_1985.csv"
    out = pd.DataFrame(index=c.index)
    if not path.exists():
        for name in [*MILITARY_ROLES, "military_sites_county"]:
            out[name] = np.nan
        return out
    s = pd.read_csv(path)
    s = s[s["in_role_1985"].astype(str).str.lower().isin(["true", "1", "yes"])]
    s = s[s["lat"].notna() & s["lon"].notna()]
    for name, roles in MILITARY_ROLES.items():
        pick = s[s["role"].isin(roles)]
        out[name] = (
            log_km(nearest_km(c["lat"], c["lon"], pick["lat"].to_numpy(), pick["lon"].to_numpy()))
            if len(pick)
            else np.nan
        )
    idx = in_county(geoms, s["lat"].to_numpy(), s["lon"].to_numpy())
    out["military_sites_county"] = np.bincount(idx[idx >= 0], minlength=len(c))
    return out


def build() -> pd.DataFrame:
    c = pd.read_parquet(PROCESSED / "us_counties_1985.parquet")
    geo = us_places.geometries().set_index("fips")["geometry"]
    geoms = [geo[f] for f in c["fips"]]
    parts = [
        population(c),
        administrative(c),
        geography(c),
        industry(c, geoms),
        transport(c, geoms),
        military(c, geoms),
    ]
    out = pd.concat([c[["fips"]], *parts], axis=1)
    assert set(out.columns) - {"fips"} == set(FEATURES), set(out.columns) ^ set(FEATURES)
    return out


def write_table() -> None:
    lines = [
        "# US county features, as of 1985",
        "",
        "Generated by `python -m nucprob.us1985.features` from `FEATURES` in "
        "`nucprob/us1985/features.py`.",
        "",
        "| Feature | Family | Source | Sources | Later knowledge | Note |",
        "|---|---|---|---|---|---|",
        *(
            f"| `{n}` | {f.family} | {f.source} | {', '.join(f.sources)} | "
            f"{'yes' if f.anachronism else ''} | {f.note} |"
            for n, f in FEATURES.items()
        ),
    ]
    (ROOT / "data" / "FEATURES_US.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    out = build()
    out.to_parquet(PROCESSED / "features_us1985.parquet", index=False)
    write_table()
    print(f"{len(out)} counties, {len(FEATURES)} features; missing values:")
    print(out.isna().sum()[lambda s: s > 0].to_string() or "none")


if __name__ == "__main__":
    main()
