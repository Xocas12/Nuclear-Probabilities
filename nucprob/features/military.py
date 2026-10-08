"""Military family (PLAN section 3.2): the bloc's military geography in June 1956, from a
curated, cited table (data/curated/features/military_sites_1956.csv), and airfields near a
place, from OurAirports.

The curated sites are military district and group-of-forces HQs, fleet HQs and naval bases,
Long-Range Aviation bomber bases, and the nuclear complex and test ranges, each with the years
it held that role. OurAirports lists today's airfields, open and closed, without dates, so its
counts are flagged as anachronisms; only airfields in the place's own 1956 country count
(CShapes borders), so that a West German airfield does not count for a town on the
inner-German border. SAC's own airfield list is a label (task T5), never a feature.
"""

import numpy as np
import pandas as pd

from nucprob.bloc import STUDY_DATE
from nucprob.geo import Points
from nucprob.paths import CURATED, RAW
from nucprob.sources import cshapes

SITES = CURATED / "features" / "military_sites_1956.csv"
HQ_KM = 15  # a place hosts an HQ within this distance
SITE_GROUPS = {
    "naval_base": ("fleet_hq", "naval_base"),
    "lra_base": ("lra_base",),
    "nuclear_site": ("nuclear_complex", "test_site"),
}

AIRFIELD_TYPES = ("large_airport", "medium_airport", "small_airport", "closed")
RADII_KM = (10, 25, 50)


def airfields_1956() -> pd.DataFrame:
    """OurAirports' airfields (heliports and seaplane bases dropped) with the bloc country
    each lay in on the study date."""
    a = pd.read_csv(RAW / "ourairports" / "airports.csv", low_memory=False)
    a = a[a["type"].isin(AIRFIELD_TYPES)]
    a = a[(a["longitude_deg"] > 5) | (a["longitude_deg"] < -160)]
    a = a[a["latitude_deg"] > 5]
    a = a.assign(country_1956=cshapes.bloc_country(a["latitude_deg"], a["longitude_deg"]))
    return a[a["country_1956"] != ""]


def airfields(places: pd.DataFrame) -> pd.DataFrame:
    a = airfields_1956()
    out = pd.DataFrame(0.0, index=places.index, columns=[f"log_airfields_{r}km" for r in RADII_KM])
    lat, lon = places["lat"].to_numpy(), places["lon"].to_numpy()
    for country, group in a.groupby("country_1956"):
        rows = np.flatnonzero(places["country_1956"].to_numpy() == country)
        if len(rows) == 0:
            continue
        tree = Points(group["latitude_deg"].to_numpy(), group["longitude_deg"].to_numpy())
        for r in RADII_KM:
            counts = [len(idx) for idx in tree.within(lat[rows], lon[rows], r)]
            out.iloc[rows, out.columns.get_loc(f"log_airfields_{r}km")] = np.log10(
                1 + np.array(counts)
            )
    return out


def military_sites(year: int = STUDY_DATE[0]) -> pd.DataFrame:
    """The curated sites that held their role in `year`."""
    sites = pd.read_csv(SITES)
    until = pd.to_numeric(sites["until_year"], errors="coerce").fillna(9999)
    start = pd.to_numeric(sites["from_year"], errors="coerce")
    return sites[(start <= year) & (until >= year) & sites["lat"].notna()]


def sites(places: pd.DataFrame) -> pd.DataFrame:
    s = military_sites()
    lat, lon = places["lat"].to_numpy(), places["lon"].to_numpy()
    out = pd.DataFrame(index=places.index)
    for col, categories in [
        ("military_district_hq", ("military_district_hq",)),
        ("fleet_hq", ("fleet_hq",)),
    ]:
        hq = s[s["category"].isin(categories)]
        near = Points(hq["lat"].to_numpy(), hq["lon"].to_numpy()).within(lat, lon, HQ_KM)
        out[col] = [int(len(idx) > 0) for idx in near]
    for name, categories in SITE_GROUPS.items():
        group = s[s["category"].isin(categories)]
        dist, _ = Points(group["lat"].to_numpy(), group["lon"].to_numpy()).nearest(lat, lon)
        out[f"log_km_to_{name}"] = np.log10(1 + dist[:, 0])
    return out


def military(places: pd.DataFrame) -> pd.DataFrame:
    parts = [airfields(places)]
    if SITES.exists():
        parts.append(sites(places))
    return pd.concat(parts, axis=1)
