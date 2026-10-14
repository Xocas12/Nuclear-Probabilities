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

Country controls. At a given size, the share of towns SAC listed differs a lot by country.
One pooled curve on log population cannot fit that, so any feature that tells the countries
apart gains over the pooled rule just by doing so. The baselines are therefore also fitted
with a country term (one indicator per country): the population rule plus country, and
LightGBM on the population family plus country. Each family's gain is scored over the latter.
The geography family is also scored over a location-only control (latitude and longitude),
since a distance to Moscow or to a SAC base partly just says where a town is. Next to every
pooled PR-AUC sits a within-country one: PR-AUC inside each country with at least MIN_CLASS
places of each class, averaged with weights by positives.

Writes runs/m2-check/: metrics.csv (per target, scheme and model: mean and spread over
folds; for the spatial scheme also the pooled out-of-fold PR-AUC and the within-country
PR-AUC, both averaged over the three grids), gains.csv (each comparison's PR-AUC gain over
its baseline, paired by fold, plus its pooled out-of-fold and within-country gains),
by_country.csv (pooled out-of-fold scores per country, first spatial repeat),
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
LOCATION = ["lat", "lon"]  # the location-only control for the geography family
COUNTRY_PREFIX = "country_"
MAIN = {
    "population rule": (logistic, ["log_pop"]),
    "logistic, all features": (logistic, ALL),
    "LightGBM, all features": (lightgbm, ALL),
}
RULE_COUNTRY = "population rule + country"
POP_FAMILY = "LightGBM, population family"
POP_COUNTRY = "LightGBM, population family + country"
POP_LOCATION = "LightGBM, population + location"


def ablations() -> dict:
    out = {
        POP_FAMILY: (lightgbm, POPULATION),
        "LightGBM, no anachronisms": (lightgbm, [f for f in ALL if not FEATURES[f].anachronism]),
    }
    for fam, cols in FAMILIES.items():
        if fam == "population":
            continue
        out[f"LightGBM, all but {fam}"] = (lightgbm, [f for f in ALL if f not in cols])
        out[f"LightGBM, population + {fam}"] = (lightgbm, POPULATION + cols)
    return out


def country_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """`df` with one 0/1 column per country of `country_1956`, and the names of those columns."""
    names = sorted(df["country_1956"].unique())
    cols = [COUNTRY_PREFIX + n.lower().replace(" ", "_") for n in names]
    dummies = pd.DataFrame(
        {c: (df["country_1956"] == n).astype(float) for c, n in zip(cols, names, strict=True)},
        index=df.index,
    )
    return pd.concat([df, dummies], axis=1), cols


def controls(country: list[str]) -> dict:
    """The baselines with a country term, each family over them, and the location control."""
    out = {
        RULE_COUNTRY: (logistic, ["log_pop", *country]),
        POP_COUNTRY: (lightgbm, POPULATION + country),
        POP_LOCATION: (lightgbm, POPULATION + LOCATION),
        "LightGBM, population + location + geography": (
            lightgbm,
            POPULATION + LOCATION + FAMILIES["geography"],
        ),
    }
    for fam, cols in FAMILIES.items():
        if fam != "population":
            out[f"LightGBM, population + country + {fam}"] = (lightgbm, POPULATION + country + cols)
    return out


def comparisons() -> list[tuple[str, str, str]]:
    """(what is measured, model, baseline) for gains.csv."""
    out = [
        ("country term over the population rule", RULE_COUNTRY, "population rule"),
        ("all features over the population rule", "LightGBM, all features", "population rule"),
        ("all features over the population rule + country", "LightGBM, all features", RULE_COUNTRY),
        ("all features over population + country", "LightGBM, all features", POP_COUNTRY),
        ("country term over the population family", POP_COUNTRY, POP_FAMILY),
        ("location over the population family", POP_LOCATION, POP_FAMILY),
    ]
    for fam in FAMILIES:
        if fam == "population":
            continue
        out.append((f"{fam} over population (pooled)", f"LightGBM, population + {fam}", POP_FAMILY))
        out.append(
            (
                f"{fam} over population + country",
                f"LightGBM, population + country + {fam}",
                POP_COUNTRY,
            )
        )
    out.append(
        (
            "geography over population + location",
            "LightGBM, population + location + geography",
            POP_LOCATION,
        )
    )
    return out


def within_country(y, p, country) -> tuple[float, int]:
    """PR-AUC inside each country with at least MIN_CLASS places of each class, averaged with
    weights by positives, and the number of countries scored."""
    y, p, country = np.asarray(y), np.asarray(p), np.asarray(country)
    scores, weights = [], []
    for c in np.unique(country):
        m = country == c
        pos = int(y[m].sum())
        if min(pos, int(m.sum()) - pos) < MIN_CLASS:
            continue
        scores.append(metrics(y[m], p[m])["pr_auc"])
        weights.append(pos)
    if not scores:
        return float("nan"), 0
    return float(np.average(scores, weights=weights)), len(scores)


def pooled_and_within(df: pd.DataFrame, oof: pd.DataFrame, target: str) -> list[dict]:
    """Pooled out-of-fold PR-AUC and within-country PR-AUC of every model, on the same
    predictions."""
    y, country = df[target].to_numpy(), df["country_1956"].to_numpy()
    rows = []
    for model in oof.columns:
        p = oof[model].to_numpy()
        within, n = within_country(y, p, country)
        rows.append(
            {
                "model": model,
                "pooled_oof_pr_auc": metrics(y, p)["pr_auc"],
                "within_country_pr_auc": within,
                "countries_scored": n,
            }
        )
    return rows


def gains(rows: list[dict], scores: pd.DataFrame) -> pd.DataFrame:
    """Each comparison's PR-AUC gain over its baseline under spatial CV: paired by target, grid
    and fold (mean and spread over folds), and in pooled out-of-fold and within-country PR-AUC.
    `scores` has one row per target and model with pooled_oof_pr_auc and within_country_pr_auc.
    """
    per_fold = pd.DataFrame(rows)
    per_fold = per_fold[per_fold["scheme"] == "spatial blocks"]
    wide = per_fold.pivot_table(
        index=["target", "repeat", "fold"], columns="model", values="pr_auc"
    )
    score = scores.set_index(["target", "model"])
    out = []
    for target in wide.index.get_level_values("target").unique():
        w = wide.loc[target]
        for label, model, base in comparisons():
            if model not in w or base not in w:
                continue
            diff = w[model] - w[base]
            out.append(
                {
                    "target": target,
                    "comparison": label,
                    "model": model,
                    "baseline": base,
                    "pr_auc": w[model].mean(),
                    "baseline_pr_auc": w[base].mean(),
                    "gain_mean": diff.mean(),
                    "gain_std": diff.std(),
                    "pooled_oof_gain": score.at[(target, model), "pooled_oof_pr_auc"]
                    - score.at[(target, base), "pooled_oof_pr_auc"],
                    "within_country_gain": score.at[(target, model), "within_country_pr_auc"]
                    - score.at[(target, base), "within_country_pr_auc"],
                }
            )
    return pd.DataFrame(out)


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


def evaluate(
    df: pd.DataFrame, models: dict
) -> tuple[pd.DataFrame, pd.DataFrame, list[pd.DataFrame], list[dict]]:
    """Cross-validate every model on every target. Returns the metrics table (with the pooled
    and within-country PR-AUC for the spatial scheme), the gains table, the out-of-fold
    predictions of the first spatial grid, and the per-country rows."""
    rows, oofs, countries, scores = [], [], [], []
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
            scores += [
                {"target": target, "repeat": shift, **r} for r in pooled_and_within(df, oof, target)
            ]
            if shift == SHIFTS_KM[0]:
                oofs.append(oof.add_prefix(f"{target}: "))
                countries += by_country(df, oof, target)
        main = {k: v for k, v in models.items() if k in MAIN}
        for seed in RANDOM_SEEDS:
            fold_ids = np.random.default_rng(seed).integers(0, K, len(df))
            fold_rows, _ = cross_validate(df, target, fold_ids, main)
            rows += [{"target": target, "scheme": "random", "repeat": seed, **r} for r in fold_rows]
    scores = (
        pd.DataFrame(scores)
        .groupby(["target", "model"])[["pooled_oof_pr_auc", "within_country_pr_auc"]]
        .mean()
        .reset_index()
    )
    table = summarise(rows, ["target", "scheme", "model"]).merge(
        scores.assign(scheme="spatial blocks"), on=["target", "scheme", "model"], how="left"
    )
    return table, gains(rows, scores), oofs, countries


def main() -> None:
    data_path = PROCESSED / "dataset_sac1956.parquet"
    full = pd.read_parquet(data_path)
    df = full[~full["sealed"] & full["listed"].notna()].reset_index(drop=True)
    df, country = country_columns(df)
    OUT.mkdir(parents=True, exist_ok=True)
    models = {**MAIN, **ablations(), **controls(country)}
    table, gain, oofs, countries = evaluate(df, models)
    imps = [importance(df, target) for target in TARGETS]
    table.to_csv(OUT / "metrics.csv", index=False, float_format="%.4f")
    gain.to_csv(OUT / "gains.csv", index=False, float_format="%.4f")
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
        "country_columns": dict(zip(country, sorted(df["country_1956"].unique()), strict=True)),
        "within_country": f"PR-AUC in each country with at least {MIN_CLASS} places of each "
        "class, averaged with weights by positives",
        "cv": {"k": K, "block_km": BLOCK_KM, "shifts_km": SHIFTS_KM, "random_seeds": RANDOM_SEEDS},
        "note": "a check of the feature base, not results: the protocol is frozen at M5",
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    show = table[table["scheme"] == "spatial blocks"][
        ["target", "model", "pr_auc_mean", "pr_auc_std", "within_country_pr_auc", "base_rate"]
    ]
    print(show.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(
        gain[["target", "comparison", "gain_mean", "gain_std", "within_country_gain"]].to_string(
            index=False, float_format=lambda v: f"{v:.3f}"
        )
    )


if __name__ == "__main__":
    main()
