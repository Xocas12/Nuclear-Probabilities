"""Administrative family (PLAN section 3.2): national and union-republic capitals as of June
1956 (data/curated/features/capitals_1956.csv), the centres of first-order regions and of
autonomous units as of June 1956 (data/curated/features/admin_centres_1956.csv: oblasts, krais
and ASSRs, including the oblasts abolished in 1957; voivodeships, Bezirke, kraje, counties,
regions, okrugs, provinces), and today's district seats from GeoNames.
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
    out["district_seat"] = places["feature_code"].isin(["PPLA2"]).astype(int)
    out["city_status"] = places["is_city"].astype(int)
    return out
