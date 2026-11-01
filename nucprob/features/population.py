"""Population family (PLAN section 3.2), computed over every settlement of the place table, so
that neighbours below the universe threshold still count as neighbours. How far down the table
goes depends on the source: 5,000 in the USSR, the Czech lands, Hungary, Romania, Bulgaria and
Albania; 10,000 in East Germany, Poland and Slovakia; China's 1953 cities only; the UN's cities
of 300,000+ today in North Korea, North Vietnam and Mongolia (data/curated/gazetteer/README.md).

`pop_rank_pct` is therefore ranked only among the settlements of RANK_FLOOR or more, the floor
every country's table reaches and the floor of every transfer town table, so that a town of
10,000 is not near the middle of the ranking in one country and at the bottom in another just
because one source goes down to 5,000. Settlements below the floor get 0. The neighbour sums
still use the whole table.

`pop` is each country's census figure nearest the study date (the USSR's 1959 census) and
`pop_prewar` its last census before the war, where the place table has one.
"""

import numpy as np
import pandas as pd

from nucprob.geo import Points

RANK_FLOOR = 10_000


def rank_pct(pop: pd.Series, groups: pd.Series, floor: float = RANK_FLOOR) -> pd.Series:
    """Percentile of `pop` within its group, among the group's settlements of `floor` or more
    people; 0 below the floor."""
    return pop.where(pop >= floor).groupby(groups).rank(pct=True).fillna(0.0)


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
    out["pop_rank_pct"] = rank_pct(places["pop"], places["country_1956"])
    for r in (25, 50, 100):
        neighbours = points.within(lat, lon, r)
        sums = np.array([pop[idx].sum() - pop[i] for i, idx in enumerate(neighbours)])
        out[f"log_pop_within_{r}km"] = np.log10(1 + sums)
    big = pop >= 100_000
    dist, _ = Points(lat[big], lon[big]).nearest(lat, lon, k=2)
    self_hit = big & (dist[:, 0] < 0.01)
    out["log_km_to_100k"] = np.log10(1 + np.where(self_hit, dist[:, 1], dist[:, 0]))
    return out
