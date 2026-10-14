"""Milestone M4 transfer check: does a model fitted on the bloc in 1956 rank the targets of the
smaller lists?

    python -m nucprob.transfer.check

Fits on the bloc's SAC 1956 dataset (dataset_sac1956.parquet, sealed test and unknown labels
excluded, target `listed`) with the common features only (nucprob.transfer.features.COMMON, plus the three
military distances where a region has them), and scores every list over the towns of the
countries it names. A model that uses the military distances scores only towns that have them:
the bloc never lacks one, so LightGBM would send a missing distance down the 0 km branch. A
list with any town left unscored gets no metrics for that model (the US, Canada and Japan
lists, and the Hungarian war game, whose Italian towns outside the 1965 table's scope have
none). The other side's lists of targets in the bloc (NATO's mirror lists, the US lists for China) are scored on the bloc's own 1956 places, by a model fitted without the
list's country (and without the sealed test). The population rule is the baseline. Lists with fewer than MIN_POSITIVES
linked towns are reported without metrics. A check that the transfer pipeline joins end to
end, not results: the lists are small, one-sided (exercises, defender studies) and differ in
what they count as a target.

Writes runs/m4-transfer-check/: metrics.csv, scores.csv, manifest.json.
"""

import datetime as dt
import json
from collections.abc import Callable

import pandas as pd

from nucprob.model.cv import git_commit
from nucprob.model.evaluate import metrics
from nucprob.model.zoo import lightgbm, logistic
from nucprob.paths import PROCESSED, RUNS
from nucprob.sources.fetch import sha256
from nucprob.transfer.features import COMMON, MILITARY_GROUPS
from nucprob.transfer.labels import BLOC

OUT = RUNS / "m4-transfer-check"
MIN_POSITIVES = 2


def score(
    bloc: pd.DataFrame,
    scores: pd.DataFrame,
    models: dict[str, tuple[Callable, list[str]]],
    military: list[str],
) -> pd.DataFrame:
    """Adds one score column per model to `scores`. Transfer regions are scored by a model
    fitted on the whole bloc, bloc lists by one fitted without the list's country.

    A model that uses the military distances leaves a town unscored (NaN) where any of them is
    missing: the bloc has no missing military distance, so LightGBM learns no direction for
    NaN and would score the town as if it sat on a naval base, a bomber base and a nuclear
    site at once (0 km)."""
    held_out = scores["country_1956"].fillna("")
    for name, (factory, cols) in models.items():
        scores[name] = float("nan")
        usable = scores[[c for c in cols if c in military]].notna().all(axis=1)
        for country in held_out.unique():
            rows = (held_out == country) & usable
            if not rows.any():
                continue
            train = bloc[bloc["country_1956"] != country] if country else bloc
            m = factory()
            if factory is lightgbm:
                m.set_params(n_jobs=1)  # many threads stall on a busy machine
            m.fit(train[cols], train["listed"])
            scores.loc[rows, name] = m.predict_proba(scores.loc[rows, cols])[:, 1]
    return scores


def metrics_table(scores: pd.DataFrame, models) -> pd.DataFrame:
    """One row per list and model. No metrics for a list with fewer than MIN_POSITIVES linked
    towns, or for a model that left any of the list's towns unscored."""
    rows = []
    for plan, g in scores.groupby("plan_id"):
        base = {
            "plan_id": plan,
            "region": g["region"].iloc[0],
            "towns": len(g),
            "listed": int(g["listed"].sum()),
        }
        for name in models:
            ok = base["listed"] >= MIN_POSITIVES and g[name].notna().all()
            r = metrics(g["listed"], g[name]) if ok else {}
            rows.append(base | {"model": name} | r)
    return pd.DataFrame(rows)


def main() -> None:
    bloc_path = PROCESSED / "dataset_sac1956.parquet"
    full = pd.read_parquet(bloc_path)
    bloc = full[~full["sealed"] & full["listed"].notna()].reset_index(drop=True)
    feats = pd.read_parquet(PROCESSED / "features_transfer.parquet")
    labels = pd.read_parquet(PROCESSED / "labels_transfer.parquet")
    military = [c for c in MILITARY_GROUPS if c in bloc]
    models = {
        "population rule": (logistic, ["log_pop"]),
        "logistic, common": (logistic, COMMON),
        "LightGBM, common": (lightgbm, COMMON),
        "LightGBM, common + military": (lightgbm, COMMON + military),
    }
    bloc_feats = full[["place_id", "country_1956", *COMMON, *military]].assign(region=BLOC)
    feats = pd.concat([feats, bloc_feats], ignore_index=True)
    scores = labels.merge(feats, on=["place_id", "region"], how="left")
    scores = score(bloc, scores, models, military)
    table = metrics_table(scores, models)
    OUT.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUT / "metrics.csv", index=False, float_format="%.4f")
    keep = ["plan_id", "region", "place_id", "country", "n_targets", "listed", *models]
    scores[keep].to_csv(OUT / "scores.csv", index=False, float_format="%.4f")
    manifest = {
        "milestone": "M4 transfer check",
        "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "data": {
            p.name: sha256(p)
            for p in (
                bloc_path,
                PROCESSED / "features_transfer.parquet",
                PROCESSED / "labels_transfer.parquet",
            )
        },
        "train": {"rows": len(bloc), "positives": int(bloc["listed"].sum())},
        "bloc_lists": "fitted without the list's country (leave-country-out)",
        "models": {k: v[1] for k, v in models.items()},
        "min_positives": MIN_POSITIVES,
        "note": "a check of the transfer pipeline, not results: the protocol is frozen at M5",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    show = table.pivot_table(index=["plan_id", "towns", "listed"], columns="model", values="pr_auc")
    print(show.round(3).to_string())
    roc = table.pivot_table(index="plan_id", columns="model", values="roc_auc")
    print(roc.round(3).to_string())


if __name__ == "__main__":
    main()
