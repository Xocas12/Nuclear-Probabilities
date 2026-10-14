"""Administrative family (PLAN section 3.2): national and union-republic capitals as of June
1956 (data/curated/features/capitals_1956.csv), the centres of first-order regions and of
autonomous units as of June 1956 (data/curated/features/admin_centres_1956.csv: oblasts, krais
and ASSRs, including the oblasts abolished in 1957; voivodeships, Bezirke, kraje, counties,
regions, okrugs, provinces), and today's district seats from GeoNames.

GeoNames codes the seat of a place's admin2 unit PPLA2, but admin2 is a different tier in each
country, so a district seat is read at the level of the country's own district tier (the tier
just above the commune: raion, powiat, járás, Kreis, okres, county). DISTRICT_CODE gives that
level by GeoNames country.
"""

import numpy as np
import pandas as pd

from nucprob.gazetteer.lookup import PlaceIndex
from nucprob.geo import Points
from nucprob.paths import CURATED

CAPITALS = CURATED / "features" / "capitals_1956.csv"
CENTRES = CURATED / "features" / "admin_centres_1956.csv"
MATCH_KM = 15  # a capital is the largest settlement within this distance of its point
AUTONOMY = ("autonomous oblast", "national okrug")

# GeoNames feature code of a seat of today's district tier, by the GeoNames country of the place
# (`country_today`). Countries not listed use PPLA2 (admin2 is the district tier there: raion,
# powiat, járás, obshtina, okres in Slovakia). None: GeoNames does not code that tier's seats,
# so the feature is missing there rather than 0.
DISTRICT_CODE: dict[str, str | None] = {
    "DE": "PPLA3",  # Kreise are admin3; admin2 is the Regierungsbezirk, absent in the east
    "CN": "PPLA3",  # counties are admin3; admin2 is the prefecture
    "MD": "PPLA",  # raions are admin1
    "AZ": "PPLA",  # rayons are admin1
    "LV": "PPLA",  # novadi are admin1; admin2 is the parish
    "EE": "PPLA",  # maakonnad (the former raions) are admin1; admin2 is the parish
    "CZ": None,  # 3 of 98 okres seats are coded
    "RO": None,  # admin2 is the commune; there is no tier between județ and commune
    "TM": None,  # 3 of 57 etrap seats are coded
    "KP": None,  # 3 of about 200 city and county seats are coded
}
DEFAULT_DISTRICT_CODE = "PPLA2"


def capitals() -> pd.DataFrame:
    return pd.read_csv(CAPITALS)


def locate(places: pd.DataFrame, lat, lon, within_km: float = MATCH_KM) -> np.ndarray:
    """For each point, the row position of the largest settlement within `within_km` (-1 if
    none)."""
    points = Points(places["lat"].to_numpy(), places["lon"].to_numpy())
    pop = places["pop"].to_numpy()
    out = []
    for idx in points.within(np.atleast_1d(lat), np.atleast_1d(lon), within_km):
        out.append(int(idx[np.argmax(pop[idx])]) if len(idx) else -1)
    return np.array(out)


def admin_centres() -> pd.DataFrame:
    return pd.read_csv(CENTRES, keep_default_na=False)


def centre_positions(places: pd.DataFrame, centres: pd.DataFrame) -> dict[str, int | None]:
    """Row position in `places` of each unit's centre: the largest settlement of the unit's
    country (and union republic) that carries the centre's 1956 or present name."""
    index = PlaceIndex(places)
    country = places["country_1956"].to_numpy()
    republic = places["republic"].fillna("").to_numpy() if "republic" in places else None
    pop = places["pop"].to_numpy()
    out = {}
    for _, row in centres.iterrows():
        cands = {i for name in (row["centre"], row["centre_today"]) for i in index.find(name)}
        cands = {i for i in cands if country[i] == row["country_1956"]}
        if row["republic"] and republic is not None:
            cands = {i for i in cands if republic[i] == row["republic"]}
        out[row["unit"]] = max(cands, key=lambda i: pop[i]) if cands else None
    return out


def district_seat(places: pd.DataFrame) -> pd.Series:
    """1 where GeoNames codes the place as a seat of its country's district tier (and not of a
    higher unit), 0 elsewhere, missing where GeoNames does not code that tier."""
    level = places["country_today"].map(lambda c: DISTRICT_CODE.get(c, DEFAULT_DISTRICT_CODE))
    flag = (places["feature_code"] == level).astype(float)
    return flag.mask(level.isna())


def administrative(places: pd.DataFrame) -> pd.DataFrame:
    caps = capitals()
    out = pd.DataFrame(index=places.index)
    for col, levels in [
        ("national_capital", ["national"]),
        ("republic_capital", ["union republic", "constituent capital"]),
    ]:
        rows = caps[caps["level"].isin(levels)]
        hit = locate(places, rows["lat"], rows["lon"])
        flag = np.zeros(len(places), dtype=int)
        flag[hit[hit >= 0]] = 1
        out[col] = flag
    centres = admin_centres()
    found = centre_positions(places, centres)
    for col, autonomy in [("regional_centre", False), ("autonomy_centre", True)]:
        units = centres.loc[centres["level"].isin(AUTONOMY) == autonomy, "unit"]
        flag = np.zeros(len(places), dtype=int)
        flag[[found[u] for u in units if found[u] is not None]] = 1
        out[col] = flag
    out["district_seat"] = district_seat(places)
    out["city_status"] = places["is_city"].astype(int)
    return out
