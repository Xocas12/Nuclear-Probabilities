"""Features of a town as of a document's date: national capabilities, sites, power plants.

Nothing here reads a target list (tests/test_leakage.py). The site tables say when each site was
in being; nucprob.classifier.table applies them.
"""

import io
import zipfile

import numpy as np
import pandas as pd

from nucprob.features.geography import log_km, nearest_km
from nucprob.geo import Points
from nucprob.paths import CURATED, RAW
from nucprob.transfer.features import ISO3, MILITARY_GROUPS, POWER_KM
from nucprob.transfer.regions import REGIONS

BLOC = "bloc_1956"
MIN_SITES_FOR_COVERAGE = 5  # one radar in a country does not describe its defences
NMC_ZIP = RAW / "cow" / "NMCv7.zip"
NMC_FEATURES = [
    "nmc_log_cinc",
    "nmc_log_milex",
    "nmc_log_milper",
    "nmc_log_irst",
    "nmc_log_pec",
    "nmc_log_tpop",
    "nmc_log_upop",
]
MILITARY = list(MILITARY_GROUPS)
DEFENCE = ["log_km_to_sam", "log_km_to_air_defence", "log_air_defence_sites_50km"]
# Not a model feature: the same distance without the S-25 points, whose coordinates carry US
# designations on their source page and may descend from US intelligence (the table's card).
NO_S25 = "log_km_to_air_defence_no_s25"
# COW state abbreviations of the universes' country names.
COW = {
    "USSR": "RUS",
    "China": "CHN",
    "East Germany": "GDR",
    "Poland": "POL",
    "Czechoslovakia": "CZE",
    "Hungary": "HUN",
    "Romania": "ROM",
    "Bulgaria": "BUL",
    "Albania": "ALB",
    "North Korea": "PRK",
    "North Vietnam": "DRV",
    "Mongolia": "MON",
    "Japan": "JPN",
    "USA": "USA",
    "Canada": "CAN",
    "Denmark": "DEN",
    "Netherlands": "NTH",
    "Belgium": "BEL",
    "Austria": "AUS",
    "Italy": "ITA",
    "FRG": "GFR",
    "UK": "UKG",
}
# Roles of the curated tables that are air or missile defences. "sam" are missile sites;
# "any" adds fighter bases, command posts and radars.
SAM_ROLES = {"sam_system", "nike_site", "hawk_site", "raf_sam"}
OTHER_DEFENCE_ROLES = {
    "air_defence",
    "pvo_hq",
    "pvo_fighter_base",
    "radar",
    "radar_station",
    "air_defence_radar",
    "early_warning_radar",
    "raf_air_defence",
}
DEFENCE_TABLES = {
    "bloc_1956": ["military_sites_1956.csv", "bloc_air_defence_1956.csv"],
    "wp_west_1965": ["weurope_military_sites_1965.csv"],
    "uk_1980": ["uk_military_sites_1980.csv"],
}


def document_year(date) -> int:
    return int(str(date)[:4])


def nmc(path=NMC_ZIP) -> pd.DataFrame:
    """COW's state-years, with -9 as missing and the indicators logged (base 10, plus 1). The
    abridged table sits in a zip inside the download."""
    with zipfile.ZipFile(path) as outer:
        inner = io.BytesIO(outer.read("NMCv7/NMC-v7-abridged.zip"))
    with zipfile.ZipFile(inner) as z:
        d = pd.read_csv(io.BytesIO(z.read("NMC-70-abridged.csv"))).replace(-9, np.nan)
    out = d[["stateabb", "year"]].copy()
    out["nmc_log_cinc"] = np.log10(d["cinc"].clip(lower=1e-6))
    for c in ("milex", "milper", "irst", "pec", "tpop", "upop"):
        out[f"nmc_log_{c}"] = np.log10(1 + d[c])
    return out


def nmc_as_of(table: pd.DataFrame, state: str, year: int) -> pd.Series:
    """The state's last row at or before `year`; empty if it has none."""
    rows = table[(table["stateabb"] == state) & (table["year"] <= year)]
    if rows.empty:
        return pd.Series(np.nan, index=NMC_FEATURES)
    return rows.sort_values("year").iloc[-1][NMC_FEATURES]


def sites_as_of(sites: pd.DataFrame, year: int) -> pd.DataFrame:
    """Sites in being in `year`: from_year at or before it and until_year not before it. A site
    with no from_year counts only if its table puts it in role at the table's own date."""
    start = pd.to_numeric(sites["from_year"], errors="coerce")
    end = pd.to_numeric(sites["until_year"], errors="coerce")
    flag = next((c for c in sites.columns if c.startswith("in_role")), None)
    undated_ok = (
        sites[flag].astype(str).str.lower().isin(["true", "1", "yes"])
        if flag
        else pd.Series(False, index=sites.index)
    )
    keep = ((start <= year) | (start.isna() & undated_ok)) & (end.isna() | (end >= year))
    return sites[keep & sites["lat"].notna() & sites["lon"].notna()]


def load_defence_sites(region: str) -> pd.DataFrame:
    """The region's air and missile defence sites, with `role`, lat, lon and years. The bloc's
    1956 tables keep only what they put in being in June 1956."""
    parts = []
    for name in DEFENCE_TABLES.get(region, []):
        path = CURATED / "features" / name
        if not path.exists():
            continue
        s = pd.read_csv(path)
        if "category" in s.columns and "role" not in s.columns:
            s = s.rename(columns={"category": "role"})
        # A point for the whole system, in central Moscow: not a site (its card says so).
        s = s[s["site"] != "S-25 Berkut system, Moscow area"]
        s = s[s["role"].isin(SAM_ROLES | OTHER_DEFENCE_ROLES)]
        if "in_june_1956" in s.columns:
            s = s[s["in_june_1956"].astype(str).str.lower().eq("yes")]
        parts.append(s)
    if not parts:
        return pd.DataFrame()
    # One point per site and role: an airfield with three regiments is one air-defence site, and
    # a few rows repeat across the 1956 tables.
    sites = pd.concat(parts, ignore_index=True)
    place = [sites["lat"].round(2), sites["lon"].round(2), sites["role"]]
    return sites[~pd.concat(place, axis=1).duplicated()].reset_index(drop=True)


def defence_features(lat, lon, sites: pd.DataFrame) -> pd.DataFrame:
    """Distance to the nearest missile site and nearest defence of any kind, and the number of
    defence sites within 50 km. NaN where the table has none of that kind."""
    lat, lon = np.asarray(lat, dtype=float), np.asarray(lon, dtype=float)
    out = pd.DataFrame(np.nan, index=range(len(lat)), columns=DEFENCE)
    if sites.empty:
        return out
    sam = sites[sites["role"].isin(SAM_ROLES)]
    if len(sam):
        out["log_km_to_sam"] = log_km(
            nearest_km(lat, lon, sam["lat"].to_numpy(), sam["lon"].to_numpy())
        )
    slat, slon = sites["lat"].to_numpy(float), sites["lon"].to_numpy(float)
    out["log_km_to_air_defence"] = log_km(nearest_km(lat, lon, slat, slon))
    near = Points(slat, slon).within(lat, lon, 50.0)
    out["log_air_defence_sites_50km"] = np.log10(1 + np.array([len(i) for i in near]))
    return out


def military_as_of(lat, lon, sites: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(np.nan, index=range(len(lat)), columns=MILITARY)
    for name, roles in MILITARY_GROUPS.items():
        pick = sites[sites["role"].isin(roles)]
        if len(pick):
            out[name] = log_km(nearest_km(lat, lon, pick["lat"].to_numpy(), pick["lon"].to_numpy()))
    return out


def power_as_of(p: pd.DataFrame, year: int) -> np.ndarray:
    """log10(1 + MW) of WRI plants commissioned by `year` within POWER_KM, same country."""
    w = pd.read_csv(RAW / "wri" / "global_power_plant_database.csv", low_memory=False)
    w = w[w["commissioning_year"].notna() & (w["commissioning_year"] <= year)]
    code = {c: g for r in REGIONS.values() for c, g, _ in r.countries}
    out = np.zeros(len(p))
    lat, lon = p["lat"].to_numpy(float), p["lon"].to_numpy(float)
    for country, rows in p.groupby("country").indices.items():
        sel = w[w["country"] == ISO3.get(code.get(country, ""), "")]
        if sel.empty:
            continue
        near = Points(sel["latitude"].to_numpy(), sel["longitude"].to_numpy()).within(
            lat[rows], lon[rows], POWER_KM
        )
        mw = sel["capacity_mw"].to_numpy()
        out[rows] = [mw[i].sum() for i in near]
    return np.log10(1 + out)


def document_year_features(towns: pd.DataFrame, year: int) -> pd.DataFrame:
    """Replaces the date-dependent columns of Western European towns by their value in `year`."""
    towns = towns.reset_index(drop=True).copy()
    towns["log_power_mw_25km"] = power_as_of(towns, year)
    region = REGIONS["wp_west_1965"]
    sites = sites_as_of(pd.read_csv(CURATED / "features" / region.military), year)
    lat, lon = towns["lat"].to_numpy(float), towns["lon"].to_numpy(float)
    mil = military_as_of(lat, lon, sites)
    deff = defence_features(lat, lon, sites[sites["role"].isin(SAM_ROLES | OTHER_DEFENCE_ROLES)])
    towns[MILITARY] = mil.to_numpy()
    towns[DEFENCE] = deff.to_numpy()
    # A town outside the table's documented scope has no distances (issue #9).
    for country, units in region.military_scope.items():
        out = (towns["country"] == country) & ~towns["admin1"].isin(units)
        towns.loc[out, MILITARY + DEFENCE] = np.nan
    return towns


def add_defence(towns: pd.DataFrame, region: str, year: int) -> pd.DataFrame:
    """Defence features of the bloc or the UK. A bloc country with fewer than
    MIN_SITES_FOR_COVERAGE rows gets NaN, not a distance across a border: in the 1956 tables that
    leaves the USSR alone."""
    towns = towns.reset_index(drop=True).copy()
    sites = load_defence_sites(region)
    if region == "uk_1980":
        sites = sites_as_of(sites, year)
    deff = defence_features(towns["lat"], towns["lon"], sites)
    towns[DEFENCE] = deff.to_numpy()
    if region == BLOC and not sites.empty:
        rest = sites[sites["role"] != "sam_system"]
        towns[NO_S25] = log_km(
            nearest_km(towns["lat"], towns["lon"], rest["lat"].to_numpy(), rest["lon"].to_numpy())
        )
    if region == BLOC and not sites.empty:
        n = sites["country_1956"].value_counts()
        covered = set(n[n >= MIN_SITES_FOR_COVERAGE].index)
        towns.loc[~towns["country"].isin(covered), [*DEFENCE, NO_S25]] = np.nan
    return towns
