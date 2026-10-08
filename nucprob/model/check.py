"""Milestone M2 check run: the full 1956 feature base, every bloc country in the place table,
SAC 1956 labels (PLAN section 9).

    python -m nucprob.model.check

A check that every feature family joins end to end and a first look at what each adds; not
results, since the protocol is frozen only at M5. Models: the population rule; logistic
regression and LightGBM on every feature; LightGBM without each family in turn, with the
population family plus each other family, and without the features flagged as anachronisms.
Spatial-block 5-fold cross-validation on three shifted grids, outside the sealed test, and
random 5-fold cross-validation for the three main models, to show the leak between
neighbours. The sealed test is not touched.

Writes runs/m2-check/: metrics.csv (per target, scheme and model: mean and spread over
folds), by_country.csv (pooled out-of-fold scores per country, first spatial repeat),
oof_predictions.csv, importance.csv and manifest.json.
"""

import datetime as dt
import json

import numpy as np
import pandas as pd

from nucprob.features.registry import FEATURES, by_family
from nucprob.model.cv import cross_validate, git_commit, summarise
from nucprob.model.evaluate import metrics
from nucprob.model.splits import BLOCK_KM, assign_blocks, folds
from nucprob.model.zoo import lightgbm, logistic
from nucprob.paths import PROCESSED, RUNS
from nucprob.sources.fetch import sha256

TARGETS = {
    "listed": "on the list (complex or sub-complex within 10 km)",
    "has_dgz": "given at least one DGZ",
}
K = 5
SHIFTS_KM = (0.0, 100.0, 200.0)
RANDOM_SEEDS = (0, 1, 2)
OUT = RUNS / "m2-check"
MIN_CLASS = 10  # a country is scored on its own only with this many places of each class

ALL = list(FEATURES)
FAMILIES = by_family(ALL)
POPULATION = FAMILIES["population"]
MAIN = {
    "population rule": (logistic, ["log_pop"]),
    "logistic, all features": (logistic, ALL),
    "LightGBM, all features": (lightgbm, ALL),
}


def ablations() -> dict:
    out = {
        "LightGBM, population family": (lightgbm, POPULATION),
        "LightGBM, no anachronisms": (lightgbm, [f for f in ALL if not FEATURES[f].anachronism]),
    }
    for fam, cols in FAMILIES.items():
        if fam == "population":
            continue
        out[f"LightGBM, all but {fam}"] = (lightgbm, [f for f in ALL if f not in cols])
        out[f"LightGBM, population + {fam}"] = (lightgbm, POPULATION + cols)
    return out


def by_country(df: pd.DataFrame, oof: pd.DataFrame, target: str) -> list[dict]:
    rows = []
    for country, idx in df.groupby("country_1956").groups.items():
        y = df.loc[idx, target].to_numpy()
        if min(y.sum(), (1 - y).sum()) < MIN_CLASS:
            continue
        for model in oof.columns:
            m = metrics(y, oof.loc[idx, model].to_numpy())
            rows.append({"target": target, "country": country, "model": model, **m})
    return rows


def importance(df: pd.DataFrame, target: str) -> pd.DataFrame:
    y = df[target]
    gbm = lightgbm().fit(df[ALL], y)
    lr = logistic().fit(df[ALL], y)
    return pd.DataFrame(
        {
            "target": target,
            "feature": ALL,
            "family": [FEATURES[f].family for f in ALL],
            "lightgbm_gain": gbm.booster_.feature_importance("gain"),
            "logistic_coef_std": lr[-1].coef_[0],
        }
    ).sort_values("lightgbm_gain", ascending=False)


def main() -> None:
    data_path = PROCESSED / "dataset_sac1956.parquet"
    full = pd.read_parquet(data_path)
    df = full[~full["sealed"] & full["listed"].notna()].reset_index(drop=True)
    OUT.mkdir(parents=True, exist_ok=True)
    models = {**MAIN, **ablations()}
    rows, oofs, imps, countries = [], [], [], []
    for target in TARGETS:
        for shift in SHIFTS_KM:
            blocks = pd.Series(
                assign_blocks(df["lat"].to_numpy(), df["lon"].to_numpy(), BLOCK_KM, shift)
            )
            fold_rows, oof = cross_validate(
                df, target, folds(blocks, df[target], K, seed=int(shift)), models
            )
            rows += [
                {"target": target, "scheme": "spatial blocks", "repeat": shift, **r}
                for r in fold_rows
            ]
            if shift == SHIFTS_KM[0]:
                oofs.append(oof.add_prefix(f"{target}: "))
                countries += by_country(df, oof, target)
        for seed in RANDOM_SEEDS:
            fold_ids = np.random.default_rng(seed).integers(0, K, len(df))
            fold_rows, _ = cross_validate(df, target, fold_ids, MAIN)
            rows += [{"target": target, "scheme": "random", "repeat": seed, **r} for r in fold_rows]
        imps.append(importance(df, target))
    table = summarise(rows, ["target", "scheme", "model"])
    table.to_csv(OUT / "metrics.csv", index=False, float_format="%.4f")
    pd.DataFrame(countries).to_csv(OUT / "by_country.csv", index=False, float_format="%.4f")
    cols = ["place_id", "country_1956", "name_1956", "gn_name", "lat", "lon", "pop", *TARGETS]
    pd.concat([df[cols], *oofs], axis=1).to_csv(
        OUT / "oof_predictions.csv", index=False, float_format="%.4f"
    )
    pd.concat(imps).to_csv(OUT / "importance.csv", index=False, float_format="%.4f")
    manifest = {
        "milestone": "M2 check run",
        "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "data": {data_path.name: sha256(data_path)},
        "places_in_cv": len(df),
        "places_by_country": df["country_1956"].value_counts().to_dict(),
        "sealed_places_excluded": int(full["sealed"].sum()),
        "unknown_label_places_excluded": int(full["listed"].isna().sum()),
        "targets": TARGETS,
        "models": {k: v[1] for k, v in models.items()},
        "cv": {"k": K, "block_km": BLOCK_KM, "shifts_km": SHIFTS_KM, "random_seeds": RANDOM_SEEDS},
        "note": "a check of the feature base, not results: the protocol is frozen at M5",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    show = table[table["scheme"] == "spatial blocks"][
        ["target", "model", "pr_auc_mean", "pr_auc_std", "roc_auc_mean", "base_rate"]
    ]
    print(show.to_string(index=False, float_format=lambda v: f"{v:.3f}"))


if __name__ == "__main__":
    main()
