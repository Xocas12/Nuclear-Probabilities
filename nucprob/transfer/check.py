"""Milestone M4 transfer check: does a model fitted on the bloc in 1956 rank the targets of the
smaller lists?

    python -m nucprob.transfer.check

Fits on the bloc's SAC 1956 dataset (dataset_sac1956.parquet, sealed test and unknown labels
excluded, target `listed`) with the common features only (nucprob.transfer.features.COMMON, plus the three
military distances where a region has them), and scores every list over the towns of the
countries it names. The other side's lists of targets in the bloc (NATO's mirror lists, the US
lists for China) are scored on the bloc's own 1956 places, by a model fitted without the
list's country (and without the sealed test). The population rule is the baseline. Lists with fewer than MIN_POSITIVES
linked towns are reported without metrics. A check that the transfer pipeline joins end to
end, not results: the lists are small, one-sided (exercises, defender studies) and differ in
what they count as a target.

Writes runs/m4-transfer-check/: metrics.csv, scores.csv, manifest.json.
"""

import datetime as dt
import json

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
    held_out = scores["country_1956"].fillna("")
    for name, (factory, cols) in models.items():
        scores[name] = float("nan")
        # Transfer regions: fit on the whole bloc. Bloc lists: fit without the list's country.
        for country in held_out.unique():
            train = bloc[bloc["country_1956"] != country] if country else bloc
            m = factory()
            if factory is lightgbm:
                m.set_params(n_jobs=1)  # many threads stall on a busy machine
            m.fit(train[cols], train["listed"])
            rows = held_out == country
            scores.loc[rows, name] = m.predict_proba(scores.loc[rows, cols])[:, 1]
    rows = []
    for plan, g in scores.groupby("plan_id"):
        base = {
            "plan_id": plan,
            "region": g["region"].iloc[0],
            "towns": len(g),
            "listed": int(g["listed"].sum()),
        }
        for name in models:
            r = metrics(g["listed"], g[name]) if base["listed"] >= MIN_POSITIVES else {}
            rows.append(base | {"model": name} | r)
    table = pd.DataFrame(rows)
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
