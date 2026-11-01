"""The protocol's repeat without anachronistic features, under spatial blocks.

    python -m nucprob.classifier.sensitivity

Today's data standing in for a document's date (data/FEATURES.md flags them; the defence tables'
S-25 points are handled in the defence reading) are removed from both candidates in every scope.
Writes runs/classifier/no_anachronisms.csv: each candidate with and without them, paired.
"""

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import pandas as pd

from nucprob.classifier import evaluate as ev
from nucprob.classifier.fit import ALL_FEATURES, N_BAGS, Spec, lightgbm_quiet, logistic_all
from nucprob.classifier.run import positives_of, scopes, usable
from nucprob.features.registry import FEATURES
from nucprob.paths import PROCESSED, RUNS

OUT = RUNS / "classifier"


def flagged() -> list[str]:
    return [f for f in ALL_FEATURES if f in FEATURES and FEATURES[f].anachronism]


def clean_columns() -> list[str]:
    drop = set(flagged())
    return [f for f in ALL_FEATURES if f not in drop]


def main() -> None:
    full = pd.read_parquet(PROCESSED / "classifier_table.parquet")
    groups, _ = scopes(usable(full), positives_of(full))
    out = []
    for scope, rows in groups.items():
        models = [
            Spec("logistic", logistic_all, ALL_FEATURES),
            Spec("logistic, none flagged", logistic_all, clean_columns()),
            Spec("LightGBM", lightgbm_quiet, ALL_FEATURES),
            Spec("LightGBM, none flagged", lightgbm_quiet, clean_columns()),
        ]
        s = ev.spatial_scores(rows, models, N_BAGS)
        y, doc = rows["listed"].to_numpy(int), rows["plan_id"].to_numpy()
        for name in ("logistic", "LightGBM"):
            r = ev.paired_bootstrap(y, s[f"{name}, none flagged"], s[name], doc)
            out.append(
                {
                    "scope": scope,
                    "model": name,
                    "with_all_pr_auc": ev.weighted_pr_auc(y, s[name], doc),
                    "none_flagged_pr_auc": ev.weighted_pr_auc(y, s[f"{name}, none flagged"], doc),
                    "removed": ", ".join(flagged()),
                }
                | r
            )
        print(scope, flush=True)
    pd.DataFrame(out).to_csv(OUT / "no_anachronisms.csv", index=False, float_format="%.4f")


if __name__ == "__main__":
    main()
