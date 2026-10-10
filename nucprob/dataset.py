"""Join the universe, its features and its labels into one modelling table.

    python -m nucprob.dataset

Writes data/processed/dataset_sac1956.parquet: one row per settlement of the universe
(>= 10,000 people near the study date) with coordinates; place columns, every feature of the
registry, the SAC 1956 labels, the spatial block and the split (sealed test or
cross-validation).
"""

import pandas as pd

from nucprob.features.registry import FEATURES
from nucprob.model.splits import assign_blocks, seal
from nucprob.paths import PROCESSED

PLACE_COLUMNS = [
    "place_id",
    "country_1956",
    "unit_1956",
    "region",
    "name_ru",
    "name_1956",
    "gn_name",
    "lat",
    "lon",
    "pop",
    "pop_year",
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
    "part2_has_dgz",
    "part2_n_dgz",
]


def build() -> pd.DataFrame:
    places = pd.read_parquet(PROCESSED / "places_1956.parquet")
    features = pd.read_parquet(PROCESSED / "features_1956.parquet")
    labels = pd.read_parquet(PROCESSED / "labels_sac1956.parquet")
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
    # Part II: known only where the excerpt shows it (nucprob.labels.sac1956.part2_labels).
    df["part2_has_dgz"] = df["part2_has_dgz"].mask(unknown)
    df["part2_n_dgz"] = df["part2_n_dgz"].mask(unknown)
    assert df[list(FEATURES)].columns.size == len(FEATURES)
    return df.reset_index(drop=True)


def main() -> None:
    df = build()
    df.to_parquet(PROCESSED / "dataset_sac1956.parquet", index=False)
    cv = df[~df["sealed"] & df["listed"].notna()]
    print(
        f"label unknown (entry may be on a page lost from the scan): {int(df['listed'].isna().sum())}"
    )
    print(
        f"{len(df)} settlements in {df['block'].nunique()} blocks; sealed test: {int(df['sealed'].sum())} "
        f"settlements ({df['sealed'].mean():.0%}); cross-validation: {len(cv)} "
        f"(listed {cv['listed'].mean():.1%}, with a DGZ {cv['has_dgz'].mean():.1%})"
    )
    p2 = df["part2_has_dgz"]
    print(
        f"Part II aim point known for {int(p2.notna().sum())} settlements: "
        f"{int((p2 == 1).sum())} keep one, {int((p2 == 0).sum())} have none "
        f"({int(((p2 == 0) & (df['has_dgz'] == 1)).sum())} of them lost Part I's)"
    )


if __name__ == "__main__":
    main()
