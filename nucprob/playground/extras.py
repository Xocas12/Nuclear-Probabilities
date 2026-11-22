"""Extra features that can be added to any dataset, because they need only a place's
coordinates, its country and the plan's year:
- `hyde`: people within 25, 50 and 100 km and the urban share within 25 km, from the HYDE 3.2.1
  historical population grids, interpolated to the plan's year (nucprob.sources.hyde);
- `facilities`: for groups of Wikidata facility classes open in the plan's year, the number
  within 25 km and the distance to the nearest (nucprob.sources.wikidata_facilities).
  Undated items are left out by default, because they would be anachronisms;
- `country`: the target country's regime, economy, military capability, alliances and nuclear
  status in the plan's year (nucprob.sources.country_year).

    from nucprob.playground import load
    from nucprob.playground.extras import add_extras
    ds = add_extras(load("pooled"))

These are new and coarser than the hand-built features. Wikidata's coverage is uneven (dense
for the US and Western Europe, thin for the Soviet bloc), so the facility features partly
measure Wikidata, and the country features are constant within a single-country dataset (they
are dropped there).
"""

from functools import cache

import numpy as np
import pandas as pd

from nucprob.geo import Points
from nucprob.playground.datasets import Data

FACILITY_GROUPS = {
    "military": (
        "military_base",
        "air_base",
        "naval_base",
        "missile_site",
        "launch_site",
        "radar_station",
        "military_hq",
        "arsenal",
        "weapons_storage",
        "bunker",
        "military_academy",
        "shipyard",
    ),
    "nuclear": ("nuclear_facility", "nuclear_power_plant", "nuclear_test_site"),
    "energy": ("power_station", "hydroelectric", "oil_refinery"),
    "industry": ("factory", "steelworks", "chemical_plant", "aluminium_smelter", "mine"),
    "transport": ("port", "rail_junction", "airport"),
    "research": ("research_institute",),
    "government": ("parliament", "government_seat"),
}
COUNTRY_COLUMNS = [
    "vdem_polyarchy",
    "vdem_regime",
    "polity2",
    "mad_gdppc",
    "nmc_cinc",
    "nmc_milex",
    "us_troops",
    "nato",
    "warsaw_pact",
    "nuc_arsenal",
    "host_us_nukes",
    "host_ussr_nukes",
]


def hyde_features(f: pd.DataFrame) -> pd.DataFrame:
    from nucprob.sources import hyde

    out = pd.DataFrame(index=f.index, dtype=float)
    for year, g in f.groupby("year"):
        lat, lon = g["lat"].to_numpy(), g["lon"].to_numpy()
        for km in (25, 50, 100):
            out.loc[g.index, f"hyde_log_pop_{km}km"] = np.log10(
                1 + hyde.pop_within(lat, lon, year, km)
            )
        out.loc[g.index, "hyde_urban_share_25km"] = hyde.urban_share_within(lat, lon, year, 25)
    return out


@cache
def _facilities():
    from nucprob.sources import wikidata_facilities as wf

    return wf.load()


def facility_features(f: pd.DataFrame, include_undated: bool = False) -> pd.DataFrame:
    from nucprob.sources import wikidata_facilities as wf

    df = _facilities()
    out = pd.DataFrame(index=f.index, dtype=float)
    for year, g in f.groupby("year"):
        lat, lon = g["lat"].to_numpy(), g["lon"].to_numpy()
        for group, classes in FACILITY_GROUPS.items():
            act = wf.active(int(year), classes, include_undated=include_undated, df=df)
            act = act[act["lat"].notna()]
            if act.empty:
                out.loc[g.index, f"wd_{group}_25km"] = 0.0
                out.loc[g.index, f"wd_log_km_to_{group}"] = np.nan
                continue
            pts = Points(act["lat"].to_numpy(), act["lon"].to_numpy())
            near = pts.within(lat, lon, 25)
            out.loc[g.index, f"wd_{group}_25km"] = np.log10(1 + np.array([len(i) for i in near]))
            dist, _ = pts.nearest(lat, lon)
            out.loc[g.index, f"wd_log_km_to_{group}"] = np.log10(1 + np.ravel(dist))
    return out


def country_features(f: pd.DataFrame) -> pd.DataFrame:
    """Country-year columns for each row's `nation` (the state; `country` may be a state of the
    US or a Soviet republic)."""
    from nucprob.sources import country_year as cy

    f = f.assign(country=f["nation"] if "nation" in f else f["country"])
    rows = {}
    keys = f[["country", "year"]].fillna({"country": ""}).drop_duplicates()
    for name, year in keys.itertuples(index=False):
        hit = cy.lookup(name, int(year)) if name else None
        rows[(name, year)] = (
            {c: pd.to_numeric(hit.get(c), errors="coerce") for c in COUNTRY_COLUMNS}
            if hit is not None
            else {}
        )
    out = pd.DataFrame(
        [rows[(n, y)] for n, y in zip(f["country"].fillna(""), f["year"], strict=True)],
        index=f.index,
        columns=COUNTRY_COLUMNS,
    ).astype(float)
    for c in ("mad_gdppc", "nmc_milex", "us_troops"):
        out[c] = np.log10(1 + out[c])
    return out.rename(columns={c: f"cy_{c}" for c in COUNTRY_COLUMNS})


def add_extras(
    data: Data, which=("hyde", "facilities", "country"), include_undated: bool = False
) -> Data:
    """A copy of `data` with the extra feature families appended."""
    f = data.frame.copy()
    parts = {}
    if "hyde" in which:
        parts["hyde_population"] = hyde_features(f)
    if "facilities" in which:
        parts["facilities"] = facility_features(f, include_undated)
    if "country" in which:
        parts["country"] = country_features(f)
    feats, fams = list(data.features), dict(data.families)
    for fam, cols in parts.items():
        keep = [c for c in cols.columns if cols[c].notna().any() and cols[c].nunique() > 1]
        f[keep] = cols[keep]
        feats += keep
        if keep:
            fams[fam] = keep
    return Data(data.name + "+extras", data.description, f, feats, fams, data.note)
