"""Features of the place universe as of the plan's date (PLAN section 3.2).

    python -m nucprob.features

Writes data/processed/features_1956.parquet: one row per settlement with coordinates, one column
per feature of nucprob.features.registry, and features_1956_registry.csv, the registry itself
(family, sources, anachronism flag) for the record. Coordinates are not features (PLAN
section 3, rules): they enter only the spatial splits and spatial models.
"""

import pandas as pd

from nucprob.features.administrative import administrative
from nucprob.features.geography import geography
from nucprob.features.industry import industry
from nucprob.features.population import population
from nucprob.features.registry import FEATURES
from nucprob.paths import PROCESSED

FAMILIES = [population, administrative, geography, industry]


def build(places: pd.DataFrame | None = None) -> pd.DataFrame:
    if places is None:
        places = pd.read_parquet(PROCESSED / "places_1956.parquet")
    places = places[places["has_coords"]].reset_index(drop=True)
    feats = pd.concat([f(places) for f in FAMILIES], axis=1)
    missing = set(FEATURES) - set(feats.columns)
    assert not missing, f"features in the registry but not built: {missing}"
    extra = set(feats.columns) - set(FEATURES)
    assert not extra, f"features built but not in the registry: {extra}"
    return pd.concat([places[["place_id"]], feats[list(FEATURES)]], axis=1)


def registry() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "feature": name,
                "family": f.family,
                "source": f.source,
                "sources": " ".join(f.sources),
                "anachronism": f.anachronism,
                "note": f.note,
            }
            for name, f in FEATURES.items()
        ]
    )


def main() -> None:
    feats = build()
    feats.to_parquet(PROCESSED / "features_1956.parquet", index=False)
    registry().to_csv(PROCESSED / "features_1956_registry.csv", index=False)
    print(f"{len(feats)} settlements x {len(FEATURES)} features")
    print(feats.drop(columns="place_id").describe().T.round(2).to_string())


if __name__ == "__main__":
    main()
