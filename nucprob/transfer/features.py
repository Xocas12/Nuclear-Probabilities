"""Features of the transfer places, built the same way as the bloc's 1956 features so that a
model fitted on the bloc can score them.

    python -m nucprob.transfer.features

Only features whose source covers every region in the same way are built (the common set,
COMMON). The definitions are the bloc's (nucprob/features/):
- population: log_pop, pop_rank_pct (within the country), log_pop_within_{25,50,100}km (the
  people of the other towns of the table within that distance), log_km_to_100k (to the nearest
  other town of 100,000+). The bloc counts neighbours down to 5,000 people; the town tables
  stop at 10,000, so the within-radius sums run a little lower here.
- administrative: national_capital, regional_centre (the seat of a first-order unit, from the
  town table), log_km_to_capital (own country's capital).
- geography: elevation_m, log_relief_10km, log_km_to_coast.
- industry: log_power_mw_25km (WRI plants commissioned by the region's year, in the same
  country).
- transport: log_airfields_{10,25,50}km (OurAirports, closed fields included, same country),
  log_km_to_rail, rail_lines_5km, log_km_to_port, log_km_to_major_river (Natural Earth).
- military, where the region has a curated table: log_km_to_naval_base, log_km_to_bomber_base
  (the bloc's log_km_to_lra_base), log_km_to_nuclear_site; see MILITARY_GROUPS.

Writes data/processed/features_transfer.parquet (place_id plus the features).
"""

import numpy as np
import pandas as pd

from nucprob.features.geography import log_km, nearest_km
from nucprob.features.military import AIRFIELD_TYPES, RADII_KM
from nucprob.features.transport import JUNCTION_KM, MAJOR_RIVER_RANK
from nucprob.geo import Points, haversine_km
from nucprob.paths import CURATED, PROCESSED, RAW
from nucprob.sources import naturalearth, terrain
from nucprob.transfer.regions import REGIONS

NE = RAW / "naturalearth"
POWER_KM = 25.0
MARGIN_DEG = 3.0  # line and point layers are cut to the region's box plus this margin
ISO3 = {
    "DE": "DEU",
    "DK": "DNK",
    "NL": "NLD",
    "BE": "BEL",
    "AT": "AUT",
    "IT": "ITA",
    "GB": "GBR",
    "JP": "JPN",
    "US": "USA",
    "CA": "CAN",
}
# Region military tables (data/curated/features/<file>) give each site a `role`; these groups
# match the bloc's military distances by meaning. The bloc's long-range-aviation bases map to
# bomber and strike bases; its nuclear sites to nuclear storage and weapons sites.
MILITARY_GROUPS = {
    "log_km_to_naval_base": ("naval_base", "submarine_base", "fleet_hq"),
    "log_km_to_lra_base": ("bomber_base", "strike_air_base", "nuclear_strike_air_base"),
    "log_km_to_nuclear_site": ("nuclear_storage", "nuclear_weapons_site", "missile_site"),
}
COMMON = [
    "log_pop",
    "pop_rank_pct",
    "log_pop_within_25km",
    "log_pop_within_50km",
    "log_pop_within_100km",
    "log_km_to_100k",
    "national_capital",
    "regional_centre",
    "log_km_to_capital",
    "elevation_m",
    "log_relief_10km",
    "log_km_to_coast",
    "log_power_mw_25km",
    *[f"log_airfields_{r}km" for r in RADII_KM],
    "log_km_to_rail",
    "rail_lines_5km",
    "log_km_to_port",
    "log_km_to_major_river",
]


def box(lat, lon, la, lo) -> np.ndarray:
    """Points (la, lo) within the box of (lat, lon) plus the margin."""
    return (
        (la >= np.nanmin(lat) - MARGIN_DEG)
        & (la <= np.nanmax(lat) + MARGIN_DEG)
        & (lo >= np.nanmin(lon) - MARGIN_DEG)
        & (lo <= np.nanmax(lon) + MARGIN_DEG)
    )


def population(p: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=p.index)
    pop = p["pop"].to_numpy(float)
    out["log_pop"] = np.log10(pop)
    out["pop_rank_pct"] = p.groupby("country")["pop"].rank(pct=True)
    for r in (25, 50, 100):
        out[f"log_pop_within_{r}km"] = np.nan
    out["log_km_to_100k"] = np.nan
    for _, g in p.groupby("region"):
        lat, lon, gp = g["lat"].to_numpy(), g["lon"].to_numpy(), g["pop"].to_numpy(float)
        pts = Points(lat, lon)
        for r in (25, 50, 100):
            near = pts.within(lat, lon, r)
            sums = [gp[idx].sum() - gp[i] for i, idx in enumerate(near)]
            out.loc[g.index, f"log_pop_within_{r}km"] = np.log10(1 + np.array(sums))
        big = gp >= 100_000
        dist, _ = Points(lat[big], lon[big]).nearest(lat, lon, k=2)
        self_hit = big & (dist[:, 0] < 0.01)
        out.loc[g.index, "log_km_to_100k"] = np.log10(
            1 + np.where(self_hit, dist[:, 1], dist[:, 0])
        )
    return out


def administrative(p: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=p.index)
    out["national_capital"] = p["capital"].astype(int)
    out["regional_centre"] = (p["admin1_seat"].astype(int) | p["capital"].astype(int)).astype(int)
    caps = p[p["capital"] == 1].drop_duplicates("country").set_index("country")
    clat = p["country"].map(caps["lat"])
    clon = p["country"].map(caps["lon"])
    out["log_km_to_capital"] = log_km(haversine_km(p["lat"], p["lon"], clat, clon))
    return out


def geography(p: pd.DataFrame) -> pd.DataFrame:
    lat, lon = p["lat"].to_numpy(), p["lon"].to_numpy()
    out = pd.DataFrame(index=p.index)
    terr = terrain.relief(lat, lon, 10.0)
    out["elevation_m"] = terr["elevation_m"].to_numpy()
    out["log_relief_10km"] = np.log10(1 + terr["relief_m"].to_numpy())
    clat, clon = naturalearth.line_points(NE / "ne_10m_coastline.geojson", 1.0)
    k = box(lat, lon, clat, clon)
    out["log_km_to_coast"] = log_km(nearest_km(lat, lon, clat[k], clon[k]))
    return out


def by_country(p: pd.DataFrame, plat, plon, pcountry, fn) -> np.ndarray:
    """fn(tree, rows) per country, over the points of that country only."""
    out = np.zeros(len(p))
    codes = p["gn_code"].to_numpy()
    for code in np.unique(codes):
        rows = np.flatnonzero(codes == code)
        sel = pcountry == code
        if not sel.any():
            continue
        out[rows] = fn(Points(plat[sel], plon[sel]), sel, rows)
    return out


def industry(p: pd.DataFrame) -> pd.DataFrame:
    w = pd.read_csv(RAW / "wri" / "global_power_plant_database.csv", low_memory=False)
    w = w[w["commissioning_year"].notna()]
    to2 = {v: k for k, v in ISO3.items()}
    w = w.assign(code=w["country"].map(to2))
    w = w[w["code"].notna()]
    lat, lon = p["lat"].to_numpy(), p["lon"].to_numpy()
    mw = w["capacity_mw"].to_numpy()
    year = p["year"].to_numpy()
    built = w["commissioning_year"].to_numpy()

    def fn(tree, sel, rows):
        near = tree.within(lat[rows], lon[rows], POWER_KM)
        m, b = mw[sel], built[sel]
        return [m[idx][b[idx] <= year[r]].sum() for r, idx in zip(rows, near, strict=True)]

    out = pd.DataFrame(index=p.index)
    total = by_country(
        p, w["latitude"].to_numpy(), w["longitude"].to_numpy(), w["code"].to_numpy(), fn
    )
    out["log_power_mw_25km"] = np.log10(1 + total)
    return out


def transport(p: pd.DataFrame) -> pd.DataFrame:
    lat, lon = p["lat"].to_numpy(), p["lon"].to_numpy()
    out = pd.DataFrame(index=p.index)
    a = pd.read_csv(RAW / "ourairports" / "airports.csv", low_memory=False)
    a = a[a["type"].isin(AIRFIELD_TYPES) & a["iso_country"].isin(ISO3)]
    for r in RADII_KM:

        def fn(tree, sel, rows, r=r):
            return [len(idx) for idx in tree.within(lat[rows], lon[rows], r)]

        n = by_country(
            p,
            a["latitude_deg"].to_numpy(),
            a["longitude_deg"].to_numpy(),
            a["iso_country"].to_numpy(),
            fn,
        )
        out[f"log_airfields_{r}km"] = np.log10(1 + n)
    rlat, rlon, line = naturalearth.line_points(NE / "ne_10m_railroads.geojson", 1.0, ids=True)
    k = box(lat, lon, rlat, rlon)
    rlat, rlon, line = rlat[k], rlon[k], line[k]
    out["log_km_to_rail"] = log_km(nearest_km(lat, lon, rlat, rlon))
    near = Points(rlat, rlon).within(lat, lon, JUNCTION_KM)
    out["rail_lines_5km"] = [len(np.unique(line[idx])) for idx in near]
    ports = naturalearth.points(NE / "ne_10m_ports.geojson")
    plat, plon = ports["lat"].to_numpy(), ports["lon"].to_numpy()
    k = box(lat, lon, plat, plon)
    out["log_km_to_port"] = log_km(nearest_km(lat, lon, plat[k], plon[k]))
    vlat, vlon = naturalearth.line_points(
        NE / "ne_10m_rivers_lake_centerlines.geojson",
        1.0,
        keep=lambda q: q.get("scalerank") is not None and q["scalerank"] <= MAJOR_RIVER_RANK,
    )
    k = box(lat, lon, vlat, vlon)
    out["log_km_to_major_river"] = log_km(nearest_km(lat, lon, vlat[k], vlon[k]))
    return out


def military(p: pd.DataFrame) -> pd.DataFrame:
    """Distances to the region's curated military sites, where it has a table; NaN elsewhere."""
    out = pd.DataFrame(np.nan, index=p.index, columns=list(MILITARY_GROUPS))
    for region_id, region in REGIONS.items():
        path = CURATED / "features" / region.military
        rows = p.index[p["region"] == region_id]
        if not region.military or not path.exists() or not len(rows):
            continue
        s = pd.read_csv(path)
        if "in_role" in s:
            s = s[s["in_role"].astype(str).str.lower().isin(["true", "1", "yes"])]
        s = s[s["lat"].notna() & s["lon"].notna()]
        for name, roles in MILITARY_GROUPS.items():
            pick = s[s["role"].isin(roles)]
            if len(pick):
                out.loc[rows, name] = log_km(
                    nearest_km(
                        p.loc[rows, "lat"],
                        p.loc[rows, "lon"],
                        pick["lat"].to_numpy(),
                        pick["lon"].to_numpy(),
                    )
                )
    return out


def places() -> pd.DataFrame:
    p = pd.read_parquet(PROCESSED / "transfer_places.parquet")
    p = p[p["lat"].notna()].reset_index(drop=True)
    code = {c: g for r in REGIONS.values() for c, g, _ in r.countries}
    p["gn_code"] = p["country"].map(code)
    p["year"] = p["region"].map({k: r.year for k, r in REGIONS.items()})
    return p


def build() -> pd.DataFrame:
    p = places()
    parts = [population(p), administrative(p), geography(p), industry(p), transport(p)]
    feats = pd.concat(parts, axis=1)[COMMON]
    feats = pd.concat([feats, military(p)], axis=1)
    return pd.concat([p[["place_id", "region", "country"]], feats], axis=1)


def main() -> None:
    f = build()
    f.to_parquet(PROCESSED / "features_transfer.parquet", index=False)
    print(f.groupby("region")[COMMON[:6]].mean().round(2).to_string())
    print(f.isna().sum()[lambda s: s > 0].to_string())


if __name__ == "__main__":
    main()
