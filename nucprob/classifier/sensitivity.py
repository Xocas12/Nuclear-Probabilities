"""The protocol's repeats, under spatial blocks: what the selected model's gain rests on.

    python -m nucprob.classifier.sensitivity

Each scope's selected candidate against population + country, with features removed:
- `none flagged`: today's data standing in for a document's date (data/FEATURES.md flags them);
- `strict as-of`: also the defence tables, most of them post-Soviet knowledge of the sites;
- `no national power`: COW values identify the document (one value per country and year);
- `no source markers`: no defence, military or national-power columns, whose presence or absence
  marks which table, and so which document, a row came from.

Then the Soviet towns of the SAC list, whose population is the 1959 census for a June 1956 document:
the population rule and LightGBM on the 1939 census instead (earlier than the document, and missing
for towns founded after it), against the same on 1959.

Writes runs/classifier/sensitivity.csv and runs/classifier/ussr_population.csv.
"""

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from nucprob.classifier import evaluate as ev
from nucprob.classifier.features import DEFENCE, MILITARY, NMC_FEATURES
from nucprob.classifier.fit import (
    ALL_FEATURES,
    FAMILIES,
    N_BAGS,
    Spec,
    lightgbm_quiet,
    logistic_all,
    logistic_country,
)
from nucprob.classifier.run import SAC, positives_of, scopes, usable
from nucprob.features.registry import FEATURES
from nucprob.paths import PROCESSED, RUNS

OUT = RUNS / "classifier"
PLUS = "population + country"
FACTORY = {"logistic, all permitted": logistic_all, "LightGBM, all permitted": lightgbm_quiet}


def flagged() -> list[str]:
    return [f for f in ALL_FEATURES if f in FEATURES and FEATURES[f].anachronism]


def clean_columns() -> list[str]:
    drop = set(flagged())
    return [f for f in ALL_FEATURES if f not in drop]


def without(*groups: list[str]) -> list[str]:
    drop = {c for g in groups for c in g}
    return [f for f in ALL_FEATURES if f not in drop]


VARIANTS = {
    "all permitted": ALL_FEATURES,
    "none flagged": clean_columns(),
    "strict as-of": without(flagged(), DEFENCE),
    "no national power": without(NMC_FEATURES),
    "no source markers": without(NMC_FEATURES, DEFENCE, MILITARY),
}


def repeat_scope(scope: str, rows: pd.DataFrame, selected: str) -> list[dict]:
    models = [Spec(PLUS, logistic_country, ["log_pop", "country"])]
    models += [Spec(k, FACTORY[selected], cols) for k, cols in VARIANTS.items()]
    s = ev.spatial_scores(rows, models, N_BAGS)
    y, doc = rows["listed"].to_numpy(int), rows["plan_id"].to_numpy()
    block = rows["block"].to_numpy()
    out = []
    for variant, cols in VARIANTS.items():
        out.append(
            {
                "scope": scope,
                "model": selected,
                "variant": variant,
                "features": len(cols),
                "positives": int(y.sum()),
                "a_pr_auc": ev.weighted_pr_auc(y, s[variant], doc),
                "b_pr_auc": ev.weighted_pr_auc(y, s[PLUS], doc),
            }
            | ev.paired_bootstrap(y, s[variant], s[PLUS], doc)
            | ev.block_bootstrap(y, s[variant], s[PLUS], doc, block)
        )
    return out


def imputed_logistic(seed: int = 0):
    return make_pipeline(
        SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=5000)
    )


def ussr_population(table: pd.DataFrame) -> pd.DataFrame:
    """The Soviet published no town census between 1939 and 1959."""
    su = table[(table["plan_id"] == SAC) & (table["country"] == "USSR")].reset_index(drop=True)
    su = su.assign(
        prewar_missing=su["log_pop_prewar"].isna().astype(float),
        log_pop_prewar=su["log_pop_prewar"].where(su["log_pop_prewar"] > 0),
    )
    # Every population column is the 1959 count or built on it.
    later = set(FAMILIES["population"])
    rest = [c for c in without(flagged(), DEFENCE) if c not in later]
    models = [
        Spec("rule, 1959", imputed_logistic, ["log_pop"]),
        Spec("rule, 1939", imputed_logistic, ["log_pop_prewar", "prewar_missing"]),
        Spec("LightGBM, 1959", lightgbm_quiet, ["log_pop", *rest]),
        Spec("LightGBM, 1939", lightgbm_quiet, ["log_pop_prewar", "prewar_missing", *rest]),
    ]
    s = ev.spatial_scores(su, models, N_BAGS)
    y, doc, block = su["listed"].to_numpy(int), su["plan_id"].to_numpy(), su["block"].to_numpy()
    out = []
    for kind in ("rule", "LightGBM"):
        a, b = s[f"{kind}, 1939"], s[f"{kind}, 1959"]
        out.append(
            {
                "model": kind,
                "towns": len(su),
                "positives": int(y.sum()),
                "towns_without_1939": int(su["prewar_missing"].sum()),
                "pr_auc_1939": ev.weighted_pr_auc(y, a, doc),
                "pr_auc_1959": ev.weighted_pr_auc(y, b, doc),
            }
            | ev.paired_bootstrap(y, a, b, doc)
            | ev.block_bootstrap(y, a, b, doc, block)
        )
    return pd.DataFrame(out)


def main() -> None:
    full = pd.read_parquet(PROCESSED / "classifier_table.parquet")
    table = usable(full)
    groups, _ = scopes(table, positives_of(full))
    best = pd.read_csv(OUT / "selection.csv")
    best = best[best["selected"]].set_index("scope")["model"]
    ussr_population(table).to_csv(OUT / "ussr_population.csv", index=False, float_format="%.4f")
    out = []
    # Smallest first, and written after each: a cut-off run still leaves what it finished.
    for scope, rows in sorted(groups.items(), key=lambda kv: len(kv[1])):
        out += repeat_scope(scope, rows, best[scope])
        print(scope, flush=True)
        pd.DataFrame(out).to_csv(OUT / "sensitivity.csv", index=False, float_format="%.4f")
    assert np.isfinite(pd.DataFrame(out)["delta"]).all()


if __name__ == "__main__":
    main()
