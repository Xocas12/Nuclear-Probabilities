"""Join the US counties, their 1985 features and the NAPB-90 labels into one modelling table.

    python -m nucprob.us1985.dataset

Labels (data/curated/napb90/counties.csv, matched by FIPS code): the county's highest
direct-effects band in NAPB-90 (band_rank 4 very high >=10 psi ... 0 no risk). Two targets:
- `very_high`: the county reaches 10 psi or more, i.e. lies at or next to an aim point;
- `medium_plus`: the county reaches 2 psi or more.
Counties NAPB-90 does not list under their 1985 FIPS code (counties formed after the boundaries
it used: La Paz AZ 1983, Cibola NM 1981; Alaska's Aleutians East and West, 1987) have no label.

Writes data/processed/dataset_napb90.parquet, with spatial blocks and a sealed test, as for
the 1956 dataset (nucprob.model.splits).
"""

import pandas as pd

from nucprob.model.splits import assign_blocks, seal
from nucprob.paths import CURATED, PROCESSED
from nucprob.us1985.features import FEATURES

PLACE_COLUMNS = ["fips", "census_name", "state", "lat", "lon", "pop", "area_sqmi"]
TARGETS = {
    "very_high": "highest risk very high (>=10 psi)",
    "medium_plus": "highest risk medium or worse (>=2 psi)",
}


def build() -> pd.DataFrame:
    counties = pd.read_parquet(PROCESSED / "us_counties_1985.parquet")
    features = pd.read_parquet(PROCESSED / "features_us1985.parquet")
    labels = pd.read_csv(CURATED / "napb90" / "counties.csv", dtype={"fips": str})
    labels = labels[labels["fips"].notna()][["fips", "band", "band_rank"]]
    df = counties[PLACE_COLUMNS].merge(features, on="fips").merge(labels, on="fips", how="left")
    known = df["band_rank"].notna()
    df["very_high"] = (df["band_rank"] >= 4).astype(float).where(known)
    df["medium_plus"] = (df["band_rank"] >= 2).astype(float).where(known)
    df["block"] = assign_blocks(df["lat"].to_numpy(), df["lon"].to_numpy())
    df["sealed"] = seal(df["block"], df["very_high"].fillna(0))
    assert df[list(FEATURES)].columns.size == len(FEATURES)
    return df


def main() -> None:
    df = build()
    df.to_parquet(PROCESSED / "dataset_napb90.parquet", index=False)
    cv = df[~df["sealed"] & df["very_high"].notna()]
    print(
        f"{len(df)} counties in {df['block'].nunique()} blocks; label unknown "
        f"{int(df['very_high'].isna().sum())}; sealed {int(df['sealed'].sum())}; "
        f"cross-validation {len(cv)} (very high {cv['very_high'].mean():.1%}, "
        f"medium or worse {cv['medium_plus'].mean():.1%})"
    )


if __name__ == "__main__":
    main()
