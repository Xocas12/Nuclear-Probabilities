"""One row per place and document, described as of the document's date.

    python -m nucprob.classifier.table

Every document of the registry with role `train` or `test-expectation` and a place universe gets
its towns, with the common features (nucprob.transfer.features.COMMON), the military distances,
the defence features and the target state's national capabilities (COW NMC v7).

As of the document's date:
- national capabilities: the state's last year at or before the document (`nmc`);
- power plants and military and defence sites: only those dated at or before the document, for
  the Western European towns, whose documents run from 1961 to 1977 (`document_year_features`).
  The site table was compiled as of 1965, with 3 sites dated 1966, so a 1977 document sees it as of
  about 1965: stale, not later knowledge. Undated sites the table holds as in role in 1965 count
  for every document, including those of 1961 and 1964: for those two the dating is not known.
  Town populations are the 1961 census for all of them.
- The 1956 bloc towns serve the US documents of 1956-64 with features of June 1956.

A list complete only within the sector its document concerns (data/curated/labels/SECTORS.yaml)
keeps its positives and the towns inside the sector. Towns outside say nothing about the document.

Not covered: NAPB-90, whose units are US counties with their own features (nucprob/us1985); the
SAC airfield list, which is a list of airfields, not towns.

Writes data/processed/classifier_table.parquet.
"""

from collections.abc import Iterable, Mapping

import numpy as np
import pandas as pd
import yaml

from nucprob.classifier.features import (
    BLOC,
    COW,
    DEFENCE,
    MILITARY,
    NMC_FEATURES,
    add_defence,
    document_year,
    document_year_features,
    nmc,
    nmc_as_of,
)
from nucprob.model.splits import BLOCK_KM, assign_blocks
from nucprob.paths import CURATED, PROCESSED
from nucprob.plans import plans
from nucprob.transfer.features import COMMON

SAC = "us_1956_sac_complexes"
ID_COLUMNS = ["plan_id", "group", "attacker", "doc_type", "grade", "complete", "role", "year"]


def sectors() -> dict[str, list[Mapping]]:
    path = CURATED / "labels" / "SECTORS.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {s["plan_id"]: s["include"] for s in data.get("sectors", [])}


def in_sector(t: pd.DataFrame, boxes: list[Mapping]) -> pd.Series:
    """Inside any of the country's boxes, or a positive. A country with no box lies outside."""
    keep = t["listed"].astype(bool)
    for b in boxes:
        keep |= (
            (t["country"] == b["country"])
            & t["lat"].between(b.get("lat_min", -90), b.get("lat_max", 90))
            & t["lon"].between(b.get("lon_min", -180), b.get("lon_max", 180))
        )
    return keep


def bloc_towns() -> pd.DataFrame:
    d = pd.read_parquet(PROCESSED / "dataset_sac1956.parquet")
    d = d.rename(columns={"country_1956": "country", "unit_1956": "admin1"})
    return d[
        [
            "place_id",
            "country",
            "admin1",
            "name_1956",
            "lat",
            "lon",
            "pop",
            "log_pop_prewar",
            *COMMON,
            *MILITARY,
            "listed",
            "sealed",
            "never_scored",
        ]
    ].rename(columns={"name_1956": "name"})


def transfer_towns() -> pd.DataFrame:
    f = pd.read_parquet(PROCESSED / "features_transfer.parquet")
    p = pd.read_parquet(PROCESSED / "transfer_places.parquet")
    keep = ["place_id", "region", "name", "admin1", "lat", "lon", "pop"]
    return f.merge(p[keep], on=["place_id", "region"], how="left")


def assemble(registry: pd.DataFrame | None = None) -> pd.DataFrame:
    reg = plans() if registry is None else registry
    reg = reg[reg["role"].isin(["train", "test-expectation"])].copy()
    reg["year"] = reg["date"].map(document_year)
    labels = pd.read_parquet(PROCESSED / "labels_transfer.parquet")
    bloc = bloc_towns()
    towns = transfer_towns()
    table_nmc = nmc()
    boxes = sectors()
    parts = []
    for _, doc in reg.iterrows():
        plan, year = doc["plan_id"], doc["year"]
        if plan == SAC:
            t = bloc[bloc["listed"].notna()].copy()
            t["n_targets"] = np.nan
            t = add_defence(t, BLOC)
        else:
            lab = labels[labels["plan_id"] == plan]
            if lab.empty:
                continue
            region = lab["region"].iloc[0]
            if region == BLOC:
                t = lab[["place_id", "n_targets", "listed"]].merge(bloc.drop(columns="listed"))
                t = add_defence(t, BLOC)
            else:
                t = lab[["place_id", "region", "n_targets", "listed"]].merge(
                    towns, on=["place_id", "region"]
                )
                t["sealed"], t["never_scored"] = False, False
                if region == "wp_west_1965":
                    t = document_year_features(t, year)
                else:
                    t = add_defence(t, region)
        if plan in boxes:
            t = t[in_sector(t, boxes[plan])].reset_index(drop=True)
        for c in ID_COLUMNS:
            t[c] = doc[c]
        states = t["country"].map(COW)
        values = {s: nmc_as_of(table_nmc, s, year) for s in states.dropna().unique()}
        for c in NMC_FEATURES:
            t[c] = states.map({s: v[c] for s, v in values.items()}).astype(float)
        parts.append(t)
    out = pd.concat(parts, ignore_index=True)
    out["listed"] = out["listed"].astype(int)
    out["block"] = assign_blocks(out["lat"].to_numpy(), out["lon"].to_numpy(), BLOCK_KM)
    return out


def counts(table: pd.DataFrame, by: Iterable[str] = ("plan_id",)) -> pd.DataFrame:
    return table.groupby(list(by), dropna=False).agg(
        towns=("listed", "size"), positives=("listed", "sum"), sealed=("sealed", "sum")
    )


def main() -> None:
    t = assemble()
    t.to_parquet(PROCESSED / "classifier_table.parquet", index=False)
    print(counts(t, ["attacker", "doc_type", "plan_id"]).to_string())
    print(t[[*DEFENCE, *NMC_FEATURES]].isna().groupby(t["country"]).mean().round(2).to_string())


if __name__ == "__main__":
    main()
