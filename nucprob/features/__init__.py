"""Features of the place universe as of the plan's date (PLAN section 3.2).

    python -m nucprob.features

Writes data/processed/features_ussr1959.parquet: one row per settlement with coordinates,
one column per feature of nucprob.features.registry. Coordinates themselves are not features
(PLAN section 3, rules): they enter only the spatial splits and spatial models.
"""

import numpy as np
import pandas as pd

from nucprob.features.registry import FEATURES
from nucprob.gazetteer.names import key
from nucprob.geo import Points
from nucprob.paths import PROCESSED

# Capitals as of June 1956 (the study's date), by their name in the place table.
NATIONAL_CAPITAL = {"Москва"}
REPUBLIC_CAPITALS = {
    "Москва",
    "Київ",
    "Мінск",
    "Vilnius",
    "Rīga",
    "Tallinn",
    "Chișinău",
    "თბილისი",
    "Երևան",
    "Bakı",
    "Алматы",
    "Ташкент",
    "Aşgabat",
    "Бишкек",
    "Душанбе",
    "Петрозаводск",
}


def is_one_of(names: pd.Series, wanted: set[str]) -> pd.Series:
    keys = {key(n) for n in wanted}
    return names.map(lambda n: key(str(n)) in keys)


def population(places: pd.DataFrame) -> pd.DataFrame:
    """Population family, computed over every settlement of the table (>= 5,000 in 1959), so
    neighbours below the universe threshold still count as neighbours."""
    lat, lon = places["lat"].to_numpy(), places["lon"].to_numpy()
    pop = places["pop_1959"].to_numpy()
    points = Points(lat, lon)
    out = pd.DataFrame(index=places.index)
    out["log_pop_1959"] = np.log10(pop)
    out["log_pop_1939"] = np.log10(places["pop_1939"])
    out["pop_1939_missing"] = places["pop_1939"].isna().astype(int)
    out["growth_1939_59"] = (out["log_pop_1959"] - out["log_pop_1939"]).fillna(0.0)
    out["pop_rank_pct"] = places["pop_1959"].rank(pct=True)
    for r in (25, 50, 100):
        neighbours = points.within(lat, lon, r)
        sums = np.array([pop[idx].sum() - pop[i] for i, idx in enumerate(neighbours)])
        out[f"log_pop_within_{r}km"] = np.log10(1 + sums)
    big = pop >= 100_000
    big_points = Points(lat[big], lon[big])
    dist, _ = big_points.nearest(lat, lon, k=2)
    self_hit = big & (dist[:, 0] < 0.01)
    nearest = np.where(self_hit, dist[:, 1], dist[:, 0])
    out["log_km_to_100k"] = np.log10(1 + nearest)
    return out


def administrative(places: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=places.index)
    out["national_capital"] = is_one_of(places["name_ru"], NATIONAL_CAPITAL).astype(int)
    out["republic_capital"] = is_one_of(places["name_ru"], REPUBLIC_CAPITALS).astype(int)
    out["regional_seat"] = places["feature_code"].isin(["PPLC", "PPLA"]).astype(int)
    out["district_seat"] = places["feature_code"].isin(["PPLA2"]).astype(int)
    out["city_status"] = places["is_city"].astype(int)
    return out


def build() -> pd.DataFrame:
    places = pd.read_parquet(PROCESSED / "places_ussr1959.parquet")
    places = places[places["has_coords"]].reset_index(drop=True)
    feats = pd.concat([population(places), administrative(places)], axis=1)
    missing = set(FEATURES) - set(feats.columns)
    assert not missing, f"features in the registry but not built: {missing}"
    return pd.concat([places[["place_id"]], feats[list(FEATURES)]], axis=1)


def main() -> None:
    feats = build()
    feats.to_parquet(PROCESSED / "features_ussr1959.parquet", index=False)
    caps = feats[feats["republic_capital"] == 1]
    print(
        f"{len(feats)} settlements x {len(FEATURES)} features; republic capitals found: {len(caps)} of 16"
    )


if __name__ == "__main__":
    main()
