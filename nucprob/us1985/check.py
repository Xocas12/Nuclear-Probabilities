"""Milestone M4 check run for the US: 1985 county features against NAPB-90's risk bands.

    python -m nucprob.us1985.check                 # rewrite the pinned record, runs/m4-us-check/
    python -m nucprob.us1985.check --rerun         # write to runs/m4-us-check-rerun/ and compare

The same design as the 1956 check run (nucprob.model.check): the population rule, logistic
regression and LightGBM on every feature, LightGBM with the population family plus each
other family and without each family, and without the anachronisms; spatial-block 5-fold
cross-validation on three shifted grids outside the sealed test, plus random 5-fold for the
main models. A check that the US pipeline joins end to end, outside the classifier protocol.

Writes runs/m4-us-check/: metrics.csv, importance.csv, manifest.json; county scores go to
data/interim/m4-us-check/oof_predictions.csv, which is not committed. runs/m4-us-check/ is pinned in
runs/milestone_hashes.json, so `--rerun` (what `make us1985` runs) writes beside it instead, with
comparison.csv: each metric of the rerun against the pinned one.
"""

import argparse
import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

from nucprob.model.cv import cross_validate, git_commit, summarise
from nucprob.model.splits import BLOCK_KM, assign_blocks, folds
from nucprob.model.zoo import lightgbm, logistic
from nucprob.paths import DATA, PROCESSED, RAW, RUNS
from nucprob.sources import history
from nucprob.sources.fetch import sha256
from nucprob.us1985.dataset import TARGETS
from nucprob.us1985.features import FEATURES

K = 5
SHIFTS_KM = (0.0, 100.0, 200.0)
RANDOM_SEEDS = (0, 1, 2)
OUT = RUNS / "m4-us-check"
RERUN = RUNS / "m4-us-check-rerun"
LOCAL = DATA / "interim" / "m4-us-check"
METRICS = ["pr_auc_mean", "roc_auc_mean", "brier_mean", "log_loss_mean", "precision_at_k_mean"]
KEYS = ["target", "scheme", "model"]


def families(cols: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for c in cols:
        out.setdefault(FEATURES[c].family, []).append(c)
    return out


def compare(pinned: pd.DataFrame, rerun: pd.DataFrame) -> pd.DataFrame:
    """One row per metric row of the pinned record: pinned value, rerun value and the difference."""
    m = pinned.merge(rerun, on=KEYS, how="outer", suffixes=("_pinned", "_rerun"), indicator=True)
    assert (m["_merge"] == "both").all(), "the rerun's rows are not the pinned record's"
    out = m[KEYS].copy()
    for c in METRICS:
        out[f"{c}_pinned"] = m[f"{c}_pinned"]
        out[f"{c}_rerun"] = m[f"{c}_rerun"]
        out[f"{c}_diff"] = (m[f"{c}_rerun"] - m[f"{c}_pinned"]).round(4)
    return out


def run(out_dir: Path, local: Path) -> None:
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
    out_dir.mkdir(parents=True, exist_ok=True)
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
    table.to_csv(out_dir / "metrics.csv", index=False, float_format="%.4f")
    # County scores with coordinates are finer than the project's limit for maps (first-order units or 0.5-degree cells), so they are
    # written outside git (data/interim/ is ignored) and only the metrics are committed.
    cols = ["fips", "census_name", "state", "lat", "lon", "pop", "band", *TARGETS]
    local.mkdir(parents=True, exist_ok=True)
    pd.concat([df[cols], *oofs], axis=1).to_csv(
        local / "oof_predictions.csv", index=False, float_format="%.4f"
    )
    pd.concat(imps).to_csv(out_dir / "importance.csv", index=False, float_format="%.4f")
    manifest = {
        "milestone": "M4 US check run",
        "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "data": {data_path.name: sha256(data_path)},
        # The live source the pinned record's copy predates (data/sources.yaml, previous_sha256),
        # and the site table read back from history.
        "inputs": {
            "ourairports/airports.csv": sha256(RAW / "ourairports" / "airports.csv"),
            history.US_MILITARY_SITES_1985.path: history.US_MILITARY_SITES_1985.sha256,
        },
        "counties_in_cv": len(df),
        "sealed_excluded": int(full["sealed"].sum()),
        "unknown_label_excluded": int(full["very_high"].isna().sum()),
        "features_used": usable,
        "targets": TARGETS,
        "models": {k: v[1] for k, v in models.items()},
        "cv": {"k": K, "block_km": BLOCK_KM, "shifts_km": SHIFTS_KM, "random_seeds": RANDOM_SEEDS},
        "note": "a check of the US feature base, outside the classifier protocol",
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    show = table[table["scheme"] == "spatial blocks"][
        ["target", "model", "pr_auc_mean", "pr_auc_std", "roc_auc_mean", "base_rate"]
    ]
    print(show.to_string(index=False, float_format=lambda v: f"{v:.3f}"))


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--rerun", action="store_true", help="write beside the pinned record and compare"
    )
    a = ap.parse_args(argv)
    if not a.rerun:
        run(OUT, LOCAL)
        return
    run(RERUN, DATA / "interim" / "m4-us-check-rerun")
    cmp = compare(pd.read_csv(OUT / "metrics.csv"), pd.read_csv(RERUN / "metrics.csv"))
    cmp.to_csv(RERUN / "comparison.csv", index=False, float_format="%.4f")
    worst = cmp["pr_auc_mean_diff"].abs()
    print(
        f"PR-AUC against the pinned record: {int((worst == 0).sum())} of {len(cmp)} rows equal, "
        f"largest difference {worst.max():.4f}"
    )


if __name__ == "__main__":
    main()
