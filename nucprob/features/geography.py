"""Geography and reach (PLAN section 3.2): terrain, the sea, the capitals, the NATO frontier,
SAC's overseas bases and the continental United States, as of June 1956.

Distances are great-circle distances in km to the nearest point of a line or set of points,
logged as log10(1 + km).
"""

import numpy as np
import pandas as pd

from nucprob.bloc import CONUS, COUNTRIES, NATO_1956, STUDY_DATE
from nucprob.features.administrative import capitals
from nucprob.geo import Points, haversine_km
from nucprob.paths import CURATED, RAW
from nucprob.sources import cshapes, naturalearth, terrain

SAC_BASES = CURATED / "features" / "sac_bases_1956.csv"
RELIEF_KM = 10


def log_km(km) -> np.ndarray:
    return np.log10(1 + np.asarray(km, float))


def nearest_km(lat, lon, target_lat, target_lon) -> np.ndarray:
    dist, _ = Points(target_lat, target_lon).nearest(lat, lon)
    return dist[:, 0]


def sac_bases(year: int = STUDY_DATE[0]) -> pd.DataFrame:
    """SAC's overseas bases in service in `year` (data/curated/features/sac_bases_1956.csv)."""
    bases = pd.read_csv(SAC_BASES)
    return bases[(bases["sac_from"] <= year) & (bases["sac_until"] >= year)]


def capital_of(places: pd.DataFrame) -> pd.DataFrame:
    """Coordinates of each place's first-order capital: its union republic's in the USSR, its
    country's elsewhere."""
    caps = capitals()
    republics = caps[caps["level"] == "union republic"].set_index("unit")
    national = caps[caps["level"] == "national"].set_index("country_1956")
    lat, lon = [], []
    for country, unit in zip(places["country_1956"], places["unit_1956"], strict=True):
        row = republics.loc[unit] if country == "USSR" else national.loc[country]
        lat.append(row["lat"])
        lon.append(row["lon"])
    return pd.DataFrame({"lat": lat, "lon": lon}, index=places.index)


def geography(places: pd.DataFrame) -> pd.DataFrame:
    lat, lon = places["lat"].to_numpy(), places["lon"].to_numpy()
    out = pd.DataFrame(index=places.index)
    terr = terrain.relief(lat, lon, RELIEF_KM)
    out["elevation_m"] = terr["elevation_m"].to_numpy()
    out["log_relief_10km"] = np.log10(1 + terr["relief_m"].to_numpy())
    coast = naturalearth.line_points(RAW / "naturalearth" / "ne_10m_coastline.geojson")
    out["log_km_to_coast"] = log_km(nearest_km(lat, lon, *coast))
    moscow = capitals().query("level == 'national' and country_1956 == 'USSR'").iloc[0]
    out["log_km_to_moscow"] = log_km(haversine_km(lat, lon, moscow["lat"], moscow["lon"]))
    cap = capital_of(places)
    out["log_km_to_capital"] = log_km(haversine_km(lat, lon, cap["lat"], cap["lon"]))
    units = cshapes.units_on(STUDY_DATE)
    out["log_km_to_nato"] = log_km(nearest_km(lat, lon, *cshapes.boundary(units, NATO_1956)))
    bloc = {c.cshapes for c in COUNTRIES.values()}
    outside = [name for name in units if name not in bloc]
    out["log_km_to_frontier"] = log_km(nearest_km(lat, lon, *cshapes.boundary(units, outside)))
    bases = sac_bases()
    out["log_km_to_sac_base"] = log_km(nearest_km(lat, lon, bases["lat"], bases["lon"]))
    out["log_km_to_conus"] = log_km(nearest_km(lat, lon, *cshapes.boundary(units, [CONUS])))
    return out
