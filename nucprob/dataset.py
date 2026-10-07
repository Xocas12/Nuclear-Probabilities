"""Join the universe, its features and its labels into one modelling table.

    python -m nucprob.dataset

Writes data/processed/dataset_ussr1959.parquet: one row per settlement of the universe
(>= 10,000 people in 1959) with coordinates; place columns, every feature of the registry,
the labels, the spatial block and the split (sealed test or cross-validation).
"""

import pandas as pd

from nucprob.features.registry import FEATURES
from nucprob.model.splits import assign_blocks, seal
from nucprob.paths import PROCESSED

PLACE_COLUMNS = [
    "place_id",
    "republic",
    "region",
    "name_ru",
    "name_1956",
    "gn_name",
    "lat",
    "lon",
    "pop_1959",
]
LABEL_COLUMNS = [
    "listed",
    "has_dgz",
    "n_dgz",
    "n_dgz_points_near",
    "n_complexes",
    "n_subcomplexes",
    "n_installations",
    "best_priority",
    "best_tier",
    "parent_priority",
    "sac_names",
    "label_gap",
]


def build() -> pd.DataFrame:
    places = pd.read_parquet(PROCESSED / "places_ussr1959.parquet")
    features = pd.read_parquet(PROCESSED / "features_ussr1959.parquet")
    labels = pd.read_parquet(PROCESSED / "labels_ussr1959.parquet")
    df = places[places["in_universe"] & places["has_coords"]][PLACE_COLUMNS]
    df = df.merge(features, on="place_id", how="left").merge(
        labels[["place_id", *LABEL_COLUMNS]], on="place_id", how="left"
    )
    df["listed"] = df["listed"].fillna(False).astype(int)
    df["has_dgz"] = df["has_dgz"].fillna(False).astype(int)
    df["label_gap"] = df["label_gap"].fillna("")
    df["block"] = assign_blocks(df["lat"].to_numpy(), df["lon"].to_numpy())
    df["sealed"] = seal(df["block"], df["listed"])
    # A settlement whose entry may be on a page lost from the scan has no label.
    unknown = df["label_gap"] != ""
    df["listed"] = df["listed"].astype(float).mask(unknown)
    df["has_dgz"] = df["has_dgz"].astype(float).mask(unknown)
    assert df[list(FEATURES)].columns.size == len(FEATURES)
    return df.reset_index(drop=True)


def main() -> None:
    df = build()
    df.to_parquet(PROCESSED / "dataset_ussr1959.parquet", index=False)
    cv = df[~df["sealed"] & df["listed"].notna()]
    print(
        f"label unknown (entry may be on a page lost from the scan): {int(df['listed'].isna().sum())}"
    )
    print(
        f"{len(df)} settlements in {df['block'].nunique()} blocks; sealed test: {int(df['sealed'].sum())} "
        f"settlements ({df['sealed'].mean():.0%}); cross-validation: {len(cv)} "
        f"(listed {cv['listed'].mean():.1%}, with a DGZ {cv['has_dgz'].mean():.1%})"
    )


if __name__ == "__main__":
    main()
