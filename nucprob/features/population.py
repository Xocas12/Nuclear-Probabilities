"""Population family (PLAN section 3.2), computed over every settlement of the place table
(>= 5,000 people), so that neighbours below the universe threshold still count as neighbours.

`pop` is each country's census figure nearest the study date (the USSR's 1959 census) and
`pop_prewar` its last census before the war, where the place table has one.
"""

import numpy as np
import pandas as pd

from nucprob.geo import Points


def population(places: pd.DataFrame) -> pd.DataFrame:
    lat, lon = places["lat"].to_numpy(), places["lon"].to_numpy()
    pop = places["pop"].to_numpy(dtype=float)
    points = Points(lat, lon)
    out = pd.DataFrame(index=places.index)
    out["log_pop"] = np.log10(pop)
    out["log_pop_prewar"] = np.log10(places["pop_prewar"])
    out["pop_prewar_missing"] = places["pop_prewar"].isna().astype(int)
    years = places["pop_year"] - places["pop_prewar_year"]
    out["growth_prewar"] = ((out["log_pop"] - out["log_pop_prewar"]) / years).fillna(0.0)
    out["pop_rank_pct"] = places.groupby("country_1956")["pop"].rank(pct=True)
    for r in (25, 50, 100):
        neighbours = points.within(lat, lon, r)
        sums = np.array([pop[idx].sum() - pop[i] for i, idx in enumerate(neighbours)])
        out[f"log_pop_within_{r}km"] = np.log10(1 + sums)
    big = pop >= 100_000
    dist, _ = Points(lat[big], lon[big]).nearest(lat, lon, k=2)
    self_hit = big & (dist[:, 0] < 0.01)
    out["log_km_to_100k"] = np.log10(1 + np.where(self_hit, dist[:, 1], dist[:, 0]))
    return out
