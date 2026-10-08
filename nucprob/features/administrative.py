"""Administrative family (PLAN section 3.2): national and union-republic capitals as of June
1956 (data/curated/features/capitals_1956.csv), and the seats of regions and districts."""

import numpy as np
import pandas as pd

from nucprob.geo import Points
from nucprob.paths import CURATED

CAPITALS = CURATED / "features" / "capitals_1956.csv"
MATCH_KM = 15  # a capital is the largest settlement within this distance of its point


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
    out["regional_seat"] = places["feature_code"].isin(["PPLC", "PPLA"]).astype(int)
    out["district_seat"] = places["feature_code"].isin(["PPLA2"]).astype(int)
    out["city_status"] = places["is_city"].astype(int)
    return out
