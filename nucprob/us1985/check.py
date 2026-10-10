"""Milestone M4 check run for the US: 1985 county features against NAPB-90's risk bands.

    python -m nucprob.us1985.check

The same design as the 1956 check run (nucprob.model.check): the population rule, logistic
regression and LightGBM on every feature, LightGBM with the population family plus each
other family and without each family, and without the anachronisms; spatial-block 5-fold
cross-validation on three shifted grids outside the sealed test, plus random 5-fold for the
main models. A check that the US pipeline joins end to end, not results (the protocol is
frozen at M5).

Writes runs/m4-us-check/: metrics.csv, oof_predictions.csv, importance.csv, manifest.json.
"""

import datetime as dt
import json

import numpy as np
import pandas as pd

from nucprob.model.cv import cross_validate, git_commit, summarise
from nucprob.model.splits import BLOCK_KM, assign_blocks, folds
from nucprob.model.zoo import lightgbm, logistic
from nucprob.paths import PROCESSED, RUNS
from nucprob.sources.fetch import sha256
from nucprob.us1985.dataset import TARGETS
from nucprob.us1985.features import FEATURES

K = 5
SHIFTS_KM = (0.0, 100.0, 200.0)
RANDOM_SEEDS = (0, 1, 2)
OUT = RUNS / "m4-us-check"


def families(cols: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for c in cols:
        out.setdefault(FEATURES[c].family, []).append(c)
    return out


def main() -> None:
    data_path = PROCESSED / "dataset_napb90.parquet"
    full = pd.read_parquet(data_path)
    df = full[~full["sealed"] & full["very_high"].notna()].reset_index(drop=True)
    usable = [c for c in FEATURES if df[c].notna().any()]
    fams = families(usable)
    pop = fams["population"]
    main_models = {
        "population rule": (logistic, ["log_pop"]),
        "logistic, all features": (logistic, usable),
        "LightGBM, all features": (lightgbm, usable),
    }
    models = {
        **main_models,
        "LightGBM, population family": (lightgbm, pop),
        "LightGBM, no anachronisms": (
            lightgbm,
            [c for c in usable if not FEATURES[c].anachronism],
        ),
    }
    for fam, cols in fams.items():
        if fam != "population":
            models[f"LightGBM, population + {fam}"] = (lightgbm, pop + cols)
            models[f"LightGBM, all but {fam}"] = (lightgbm, [c for c in usable if c not in cols])
    OUT.mkdir(parents=True, exist_ok=True)
    rows, oofs, imps = [], [], []
    for target in TARGETS:
        for shift in SHIFTS_KM:
            blocks = pd.Series(
                assign_blocks(df["lat"].to_numpy(), df["lon"].to_numpy(), BLOCK_KM, shift)
            )
            fold_rows, oof = cross_validate(
                df, target, folds(blocks, df[target], K, int(shift)), models
            )
            rows += [
                {"target": target, "scheme": "spatial blocks", "repeat": shift, **r}
                for r in fold_rows
            ]
            if shift == SHIFTS_KM[0]:
                oofs.append(oof.add_prefix(f"{target}: "))
        for seed in RANDOM_SEEDS:
            ids = np.random.default_rng(seed).integers(0, K, len(df))
            fold_rows, _ = cross_validate(df, target, ids, main_models)
            rows += [{"target": target, "scheme": "random", "repeat": seed, **r} for r in fold_rows]
        gbm = lightgbm().fit(df[usable], df[target])
        imps.append(
            pd.DataFrame(
                {
                    "target": target,
                    "feature": usable,
                    "family": [FEATURES[c].family for c in usable],
                    "lightgbm_gain": gbm.booster_.feature_importance("gain"),
                }
            ).sort_values("lightgbm_gain", ascending=False)
        )
    table = summarise(rows, ["target", "scheme", "model"])
    table.to_csv(OUT / "metrics.csv", index=False, float_format="%.4f")
    cols = ["fips", "census_name", "state", "lat", "lon", "pop", "band", *TARGETS]
    pd.concat([df[cols], *oofs], axis=1).to_csv(
        OUT / "oof_predictions.csv", index=False, float_format="%.4f"
    )
    pd.concat(imps).to_csv(OUT / "importance.csv", index=False, float_format="%.4f")
    manifest = {
        "milestone": "M4 US check run",
        "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "data": {data_path.name: sha256(data_path)},
        "counties_in_cv": len(df),
        "sealed_excluded": int(full["sealed"].sum()),
        "unknown_label_excluded": int(full["very_high"].isna().sum()),
        "features_used": usable,
        "targets": TARGETS,
        "models": {k: v[1] for k, v in models.items()},
        "cv": {"k": K, "block_km": BLOCK_KM, "shifts_km": SHIFTS_KM, "random_seeds": RANDOM_SEEDS},
        "note": "a check of the US feature base, not results: the protocol is frozen at M5",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    show = table[table["scheme"] == "spatial blocks"][
        ["target", "model", "pr_auc_mean", "pr_auc_std", "roc_auc_mean", "base_rate"]
    ]
    print(show.to_string(index=False, float_format=lambda v: f"{v:.3f}"))


if __name__ == "__main__":
    main()
