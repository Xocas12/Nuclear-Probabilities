"""What the labels rest on, as counted from the built tables. Readings only: no label changes here.

    python -m nucprob.classifier.link_audit

Writes, in runs/classifier/:
- link_audit_coverage.csv: SAC's complex entries by country, linked or not to a town of the universe.
- link_audit_coverage_subcomplex.csv: the same for SAC's subcomplex entries.
- link_audit_dgz.csv: unsealed SAC negatives holding a designated ground zero point as their nearest
  entry, and PR-AUC under spatial blocks with those towns counted as they are and as positive.
- link_audit_temporal.csv: which attackers supply the positives of each temporal holdout.
- link_audit_floors.csv: the smallest town of SAC's universe by country.
"""

import json

import numpy as np
import pandas as pd

from nucprob.classifier import evaluate as ev
from nucprob.classifier.run import usable
from nucprob.outputs import hashes, start_record
from nucprob.paths import PROCESSED, RUNS

OUT = RUNS / "classifier"
SAC = "us_1956_sac_complexes"
SAC_SCOPE = "single document: SAC 1956 (not a state model)"
MODELS = ["population rule", "population + country", "logistic, all permitted"]


def coverage(links: pd.DataFrame, universe: set[str], level: str = "complex") -> pd.DataFrame:
    c = links[links["level"] == level]
    linked = c["place_id"].isin(universe)
    g = c.assign(linked=linked).groupby("country_1956")["linked"]
    out = g.agg(entries="size", linked="sum").reset_index()
    total = pd.DataFrame([{"country_1956": "all", "entries": len(c), "linked": int(linked.sum())}])
    return pd.concat([out, total], ignore_index=True).assign(
        unlinked=lambda d: d["entries"] - d["linked"]
    )


def dgz_negatives(dataset: pd.DataFrame, labels: pd.DataFrame, held: pd.DataFrame) -> pd.DataFrame:
    x = dataset[["place_id", "listed", "sealed"]].merge(
        labels[["place_id", "n_dgz_points_near"]], on="place_id"
    )
    ids = set(
        x.loc[
            (x["listed"] == 0) & (x["n_dgz_points_near"] > 0) & ~x["sealed"].astype(bool),
            "place_id",
        ]
    )
    s = held[(held["scope"] == SAC_SCOPE) & (held["holdout"] == "spatial blocks")]
    y = s["listed"].to_numpy(int)
    relabelled = (y | s["place_id"].isin(ids).to_numpy()).astype(int)
    rows = []
    for m in MODELS:
        p = s[m].to_numpy()
        rows.append(
            {
                "model": m,
                "negatives_with_a_dgz_point": len(ids),
                "pr_auc_as_labelled": ev.pr_auc(y, p),
                "pr_auc_counted_positive": ev.pr_auc(relabelled, p),
            }
        )
    return pd.DataFrame(rows)


def temporal_mix(table: pd.DataFrame) -> pd.DataFrame:
    t = usable(table)
    t = t[(t["role"] == "train") & (t["listed"] == 1)]
    side = t["attacker"].map(lambda a: "US" if a == "US" else "Warsaw Pact or Soviet lesson")
    when = np.where(
        t["year"] <= ev.TEMPORAL_CUT,
        "scored by a fit after the cut",
        "scored by a fit before the cut",
    )
    return (
        t.assign(side=side, holdout=when)
        .groupby(["holdout", "side"])
        .size()
        .rename("positives")
        .reset_index()
    )


def floors(table: pd.DataFrame) -> pd.DataFrame:
    sac = table[table["plan_id"] == SAC]
    return (
        sac.groupby("country")["pop"]
        .agg(smallest_town="min", towns="size")
        .reset_index()
        .astype({"smallest_town": int})
    )


def main() -> None:
    started = start_record()
    table = pd.read_parquet(PROCESSED / "classifier_table.parquet")
    dataset = pd.read_parquet(PROCESSED / "dataset_sac1956.parquet")
    links = pd.read_parquet(PROCESSED / "sac1956_links.parquet")
    labels = pd.read_parquet(PROCESSED / "labels_sac1956.parquet")
    held = pd.read_csv(OUT / "held_out_scores.csv.gz")
    universe = set(dataset["place_id"])
    outputs = {
        "link_audit_coverage.csv": coverage(links, universe),
        "link_audit_coverage_subcomplex.csv": coverage(links, universe, "subcomplex"),
        "link_audit_dgz.csv": dgz_negatives(dataset, labels, held),
        "link_audit_temporal.csv": temporal_mix(table),
        "link_audit_floors.csv": floors(table),
    }
    for name, frame in outputs.items():
        frame.to_csv(OUT / name, index=False, float_format="%.4f")
        print(frame.to_string(index=False))
    (OUT / "link_audit_manifest.json").write_text(
        json.dumps({**started, "outputs": hashes([OUT / n for n in outputs])}, indent=2)
    )


if __name__ == "__main__":
    main()
