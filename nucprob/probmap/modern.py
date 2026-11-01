"""Present-day towns described only by what can be carried across eras: population, administrative
rank and distance to the coast. No present-day military, industrial or infrastructure data enters
the modern map, so nothing here identifies a facility.

Natural Earth's populated places (public domain): a map-label set of 7,342 places, not a census. It
is selective, and thinner in some countries than others, which is one more reason the modern map is
an extrapolation. Towns below MIN_POP are dropped, as are research and weather stations.

The table is built in memory and never written out; only grid cells are published.
"""

import numpy as np
import pandas as pd

from nucprob.features.geography import log_km, nearest_km
from nucprob.features.population import rank_pct
from nucprob.geo import Points, haversine_km
from nucprob.paths import RAW
from nucprob.sources import naturalearth

PORTABLE = [
    "log_pop",
    "pop_rank_pct",
    "log_pop_within_25km",
    "log_pop_within_50km",
    "log_pop_within_100km",
    "log_km_to_100k",
    "national_capital",
    "regional_centre",
    "log_km_to_capital",
    "log_km_to_coast",
]
MIN_POP = 10_000
PLACES = RAW / "naturalearth" / "ne_10m_populated_places_simple.geojson"
TOWN_CLASSES = {
    "Populated place",
    "Populated Place",
    "Admin-1 capital",
    "Admin-1 region capital",
    "Admin-0 capital",
    "Admin-0 capital alt",
    "Admin-0 region capital",
}


def read_towns(path=PLACES) -> pd.DataFrame:
    """Columns: country (ISO alpha-3 of Natural Earth), kind, lat, lon, pop."""
    d = naturalearth.points(path)
    d = d[d["featurecla"].isin(TOWN_CLASSES) & (d["pop_max"] >= MIN_POP)]
    return pd.DataFrame(
        {
            "country": d["adm0_a3"],
            "kind": d["featurecla"].str.lower(),
            "lat": d["latitude"],
            "lon": d["longitude"],
            "pop": d["pop_max"].astype(float),
        }
    ).reset_index(drop=True)


def features(towns: pd.DataFrame) -> pd.DataFrame:
    """The classifier's definitions, within one country's towns (nucprob.transfer.features)."""
    t = towns.reset_index(drop=True)
    out = pd.DataFrame(index=t.index)
    out["log_pop"] = np.log10(t["pop"].to_numpy(float))
    out["pop_rank_pct"] = rank_pct(t["pop"], t["country"]).to_numpy()
    for r in (25, 50, 100):
        out[f"log_pop_within_{r}km"] = 0.0
    out["log_km_to_100k"] = np.nan
    lat, lon, pop = t["lat"].to_numpy(), t["lon"].to_numpy(), t["pop"].to_numpy(float)
    for _, rows in t.groupby("country").indices.items():
        pts = Points(lat[rows], lon[rows])
        for r in (25, 50, 100):
            near = pts.within(lat[rows], lon[rows], r)
            total = [pop[rows][i].sum() - pop[rows][k] for k, i in enumerate(near)]
            out.loc[rows, f"log_pop_within_{r}km"] = np.log10(1 + np.array(total))
        big = pop[rows] >= 100_000
        if big.sum() >= 2:
            dist, _ = Points(lat[rows][big], lon[rows][big]).nearest(lat[rows], lon[rows], k=2)
            self_hit = big & (dist[:, 0] < 0.01)
            out.loc[rows, "log_km_to_100k"] = np.log10(
                1 + np.where(self_hit, dist[:, 1], dist[:, 0])
            )
    capital = t["kind"].eq("admin-0 capital")
    out["national_capital"] = capital.astype(int).to_numpy()
    out["regional_centre"] = (capital | t["kind"].str.startswith("admin-1")).astype(int).to_numpy()
    caps = t[capital].sort_values("pop", ascending=False).drop_duplicates("country")
    caps = caps.set_index("country")
    out["log_km_to_capital"] = log_km(
        haversine_km(
            t["lat"], t["lon"], t["country"].map(caps["lat"]), t["country"].map(caps["lon"])
        )
    )
    clat, clon = naturalearth.line_points(RAW / "naturalearth" / "ne_10m_coastline.geojson", 5.0)
    out["log_km_to_coast"] = log_km(nearest_km(lat, lon, clat, clon))
    return out[PORTABLE]
