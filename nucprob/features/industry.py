"""Industry family (PLAN section 3.2): the Soviet defence industry active in 1956, from Dexter
and Rodionov's guide, and power plants commissioned by 1956, from WRI's database.

Both are later knowledge standing in for 1956, so every feature is flagged as an anachronism:
the guide records what existed, from post-Soviet archives, not what SAC knew; WRI's plants are
the ones that survived to be catalogued, and its commissioning years for Soviet plants are
often off (the Volga HPP is listed as 1952; it was built in 1958-61).

The guide gives no coordinates. Each entry's location string is matched to a place of the
place table by name (nucprob.gazetteer.lookup): all the names it gives must agree; a town of
the RSFSR is preferred when the string names no republic, and a region named in the string
("Moscow obl.") must hold the place. A near-miss spelling is accepted only within 200 km of the
named region's centre. A district in parentheses that was a town of its own in
1959 ("Moscow (Tushino)") takes the entry. A numbered code name ("Chelyabinsk 40") is matched
only by its other names (Ozersk), never to the city it is named after.

The features are counts per town, so they cover the USSR only; elsewhere they are missing.
"""

import numpy as np
import pandas as pd

from nucprob.bloc import STUDY_DATE
from nucprob.gazetteer.lookup import PlaceIndex
from nucprob.geo import Points, haversine_km
from nucprob.paths import PROCESSED, RAW
from nucprob.sources import cshapes, vpk

YEAR = STUDY_DATE[0]
REGION_KM = 400  # a place "in" a named region lies within this distance of the region's centre
FUZZY_REGION_KM = 200  # ... and a fuzzy match within this distance
DISTRICT_KM = 40  # a district in parentheses is looked for this close to its town
WITHIN_KM = 25
BRANCH_FEATURES = {
    "aero": {"AERO"},
    "armour": {"ARMOUR"},
    "arms": {"ARMS", "MUNS"},
    "ship": {"SHIP"},
    "elec": {"ELEC"},
    "atom": {"ATOM"},
}


class Matcher:
    """Match the guide's locations to rows of a place table."""

    def __init__(self, places: pd.DataFrame):
        self.places = places.reset_index(drop=True)
        self.index = PlaceIndex(self.places)
        self.pop = self.places["pop"].to_numpy()
        self.country = self.places["country_1956"].to_numpy()
        self.unit = self.places["unit_1956"].to_numpy()

    def _pool(self, loc: vpk.Location) -> set[int]:
        pool = np.flatnonzero(self.country == loc.country)
        if loc.republic == "russia":
            pool = pool[np.isin(self.unit[pool], ["russia", "karelo-finnish"])]
        elif loc.republic:
            pool = pool[self.unit[pool] == loc.republic]
        return set(pool.tolist())

    def _largest(self, cands) -> int:
        return max(cands, key=lambda i: self.pop[i])

    def _near(self, cands: set[int], centre: int, km: float) -> set[int]:
        p = self.places
        return {
            i
            for i in cands
            if haversine_km(
                p.at[i, "lat"], p.at[i, "lon"], p.at[centre, "lat"], p.at[centre, "lon"]
            )
            <= km
        }

    def match(self, loc: vpk.Location) -> tuple[int | None, str]:
        pool = self._pool(loc)
        if loc.country == "USSR" and loc.republic is None:
            russia = {i for i in pool if self.unit[i] in ("russia", "karelo-finnish")}
        else:
            russia = pool
        names = loc.also if loc.closed else [loc.town, *loc.also]
        found = [set(self.index.find(n)) & pool for n in names]
        found = [f for f in found if f]
        method = "name"
        if not found and not loc.closed and loc.region:
            # A near-miss spelling counts only inside the region the string names.
            centres = set(self.index.find(loc.region)) & pool
            if centres:
                fuzzy = set(self.index.fuzzy(loc.town, allowed=pool))
                fuzzy = self._near(fuzzy, self._largest(centres), FUZZY_REGION_KM)
                found = [fuzzy] if fuzzy else []
                method = "fuzzy name"
        if not found:
            return None, "unmatched"
        cands = set.intersection(*found) or found[0]
        if russia is not pool and cands & russia:
            cands &= russia
        if loc.region and len(cands) > 1:
            centres = set(self.index.find(loc.region)) & pool
            if centres:
                inside = self._near(cands, self._largest(centres), REGION_KM)
                cands = inside or cands
        pick = self._largest(cands)
        for district in loc.districts:
            near = self._near(set(self.index.find(district)) & pool, pick, DISTRICT_KM) - {pick}
            if near:
                return self._largest(near), method + ", district"
        return pick, method


def defence_industry(places: pd.DataFrame, year: int = YEAR) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Counts of the guide's establishments active in `year`, per place (row positions of
    `places`), and the table of entries with the place each was matched to."""
    entries = vpk.main_series(vpk.load())
    entries = entries[vpk.active(entries, year)].copy()
    matcher = Matcher(places)
    found = {}
    for text in entries["location"].unique():
        loc = vpk.parse_location(text)
        found[text] = (None, "no location") if loc is None else matcher.match(loc)
    entries["place_pos"] = entries["location"].map(lambda t: found[t][0])
    entries["match"] = entries["location"].map(lambda t: found[t][1])
    entries["place_id"] = entries["place_pos"].map(
        lambda i: None if pd.isna(i) else places["place_id"].iat[int(i)]
    )
    hit = entries[entries["place_pos"].notna()].copy()
    hit["place_pos"] = hit["place_pos"].astype(int)
    hit["branches"] = hit["branch"].map(vpk.branches)
    counts = pd.DataFrame(0, index=range(len(places)), columns=[])
    by_place = hit.groupby("place_pos")
    counts["total"] = by_place.size()
    counts["factories"] = hit[hit["type"] == "z"].groupby("place_pos").size()
    counts["design"] = hit[hit["type"].isin(["kb", "nii"])].groupby("place_pos").size()
    counts["large"] = hit[hit["size"] == "3"].groupby("place_pos").size()
    for name, wanted in BRANCH_FEATURES.items():
        mask = hit["branches"].map(lambda b, w=wanted: bool(b & w))
        counts[name] = hit[mask].groupby("place_pos").size()
    return counts.fillna(0).astype(int), entries


def power_plants(places: pd.DataFrame, year: int = YEAR, km: float = WITHIN_KM) -> np.ndarray:
    """Capacity (MW, today's) of WRI plants commissioned by `year` within `km` of each place,
    counting only plants that lay in the place's own 1956 country (CShapes borders)."""
    w = pd.read_csv(RAW / "wri" / "global_power_plant_database.csv", low_memory=False)
    w = w[(w["commissioning_year"] <= year) & ((w["longitude"] > 5) | (w["longitude"] < -160))]
    w = w.assign(country_1956=cshapes.bloc_country(w["latitude"], w["longitude"]))
    out = np.zeros(len(places))
    for country, plants in w[w["country_1956"] != ""].groupby("country_1956"):
        rows = np.flatnonzero(places["country_1956"].to_numpy() == country)
        if len(rows) == 0:
            continue
        tree = Points(plants["latitude"].to_numpy(), plants["longitude"].to_numpy())
        near = tree.within(places["lat"].to_numpy()[rows], places["lon"].to_numpy()[rows], km)
        mw = plants["capacity_mw"].to_numpy()
        out[rows] = [mw[idx].sum() for idx in near]
    return out


def industry(places: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=places.index)
    counts, entries = defence_industry(places)
    ussr = places["country_1956"].eq("USSR").to_numpy()
    for col in ["total", "factories", "design", "large", *BRANCH_FEATURES]:
        out[f"log_vpk_{col}"] = np.where(ussr, np.log10(1 + counts[col].to_numpy()), np.nan)
    total = counts["total"].to_numpy()
    near = Points(places["lat"].to_numpy(), places["lon"].to_numpy()).within(
        places["lat"].to_numpy(), places["lon"].to_numpy(), WITHIN_KM
    )
    around = np.array([total[idx].sum() for idx in near])
    out["log_vpk_within_25km"] = np.where(ussr, np.log10(1 + around), np.nan)
    out["log_power_mw_25km"] = np.log10(1 + power_plants(places))
    report = entries.groupby(["location", "match"], dropna=False).agg(
        entries=("name", "size"), place_id=("place_id", "first")
    )
    report.reset_index().sort_values("entries", ascending=False).to_csv(
        PROCESSED / "vpk_1956_locations.csv", index=False
    )
    return out
