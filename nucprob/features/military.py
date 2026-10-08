"""Military family (PLAN section 3.2): airfields near a place, from OurAirports.

OurAirports lists today's airfields, open and closed, without dates, so the counts are flagged
as anachronisms. Only airfields in the place's own 1956 country count (CShapes borders), so
that a West German airfield does not count for a town on the inner-German border. SAC's own
airfield list is a label (task T5), never a feature.
"""

import numpy as np
import pandas as pd

from nucprob.geo import Points
from nucprob.paths import RAW
from nucprob.sources import cshapes

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


def military(places: pd.DataFrame) -> pd.DataFrame:
    return airfields(places)
