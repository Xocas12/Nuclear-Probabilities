"""Milestone M1, the vertical slice: USSR only, 1959 universe, population and administrative
features, SAC 1956 labels; the population rule against logistic regression and LightGBM.

    python -m nucprob.model.slice

Spatial-block cross-validation (5 folds of 300 km blocks, repeated on three shifted grids) on the
places outside the sealed test; random 5-fold cross-validation alongside, to show how much
neighbouring places leaking across folds inflates scores. The sealed test is not touched.

Writes runs/m1-slice/: metrics.csv (per target, scheme, model: mean and spread over folds),
oof_predictions.csv (out-of-fold P(target) from the first spatial repeat), importance.csv and
manifest.json (git commit, data hashes, settings). The slice's numbers check that every join
works end to end; they are not results (PLAN section 9).
"""

import datetime as dt
import json
import subprocess

import numpy as np
import pandas as pd

from nucprob.model.evaluate import metrics
from nucprob.model.splits import BLOCK_KM, assign_blocks, folds
from nucprob.model.zoo import ALL, MODELS, lightgbm, logistic
from nucprob.paths import PROCESSED, ROOT, RUNS
from nucprob.sources.fetch import sha256

TARGETS = {
    "listed": "on the list (complex or sub-complex within 10 km)",
    "has_dgz": "given at least one DGZ",
}
K = 5
SHIFTS_KM = (0.0, 100.0, 200.0)  # repeats of the spatial CV on shifted block grids
RANDOM_SEEDS = (0, 1, 2)
OUT = RUNS / "m1-slice"


def cross_validate(
    df: pd.DataFrame, target: str, fold_ids: np.ndarray
) -> tuple[list[dict], pd.DataFrame]:
    """Per-fold metrics and out-of-fold predictions of every model."""
    y = df[target].to_numpy()
    rows, oof = [], pd.DataFrame(index=df.index)
    for name, (factory, cols) in MODELS.items():
        pred = np.full(len(df), np.nan)
        for f in np.unique(fold_ids):
            test = fold_ids == f
            model = factory()
            model.fit(df.loc[~test, cols], y[~test])
            pred[test] = model.predict_proba(df.loc[test, cols])[:, 1]
            m = metrics(y[test], pred[test])
            if m:
                rows.append({"model": name, "fold": int(f), **m})
        oof[name] = pred
    return rows, oof


def summarise(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    keys = ["target", "scheme", "model"]
    agg = df.groupby(keys)[["pr_auc", "roc_auc", "brier", "log_loss", "precision_at_k"]].agg(
        ["mean", "std"]
    )
    agg.columns = [f"{a}_{b}" for a, b in agg.columns]
    base = df.groupby(keys)["base_rate"].mean().rename("base_rate")
    return agg.join(base).reset_index()


def importance(df: pd.DataFrame, target: str) -> pd.DataFrame:
    """LightGBM gain and standardised logistic coefficients, fitted on all CV places."""
    y = df[target]
    gbm = lightgbm().fit(df[ALL], y)
    lr = logistic().fit(df[ALL], y)
    coef = lr[-1].coef_[0]
    return pd.DataFrame(
        {
            "target": target,
            "feature": ALL,
            "lightgbm_gain": gbm.booster_.feature_importance("gain"),
            "logistic_coef_std": coef,
        }
    ).sort_values("lightgbm_gain", ascending=False)


def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> None:
    data_path = PROCESSED / "dataset_sac1956.parquet"
    full = pd.read_parquet(data_path)
    df = full[~full["sealed"] & full["listed"].notna()].reset_index(drop=True)
    gap = full[~full["sealed"] & full["listed"].isna()].reset_index(drop=True)
    OUT.mkdir(parents=True, exist_ok=True)
    rows, oofs, imps = [], [], []
    for target in TARGETS:
        for shift in SHIFTS_KM:
            blocks = pd.Series(
                assign_blocks(df["lat"].to_numpy(), df["lon"].to_numpy(), BLOCK_KM, shift)
            )
            fold_rows, oof = cross_validate(
                df, target, folds(blocks, df[target], K, seed=int(shift))
            )
            rows += [
                {"target": target, "scheme": "spatial blocks", "repeat": shift, **r}
                for r in fold_rows
            ]
            if shift == SHIFTS_KM[0]:
                oofs.append(oof.add_prefix(f"{target}: "))
        rng_rows = []
        for seed in RANDOM_SEEDS:
            fold_ids = np.random.default_rng(seed).integers(0, K, len(df))
            fold_rows, _ = cross_validate(df, target, fold_ids)
            rng_rows += [
                {"target": target, "scheme": "random", "repeat": seed, **r} for r in fold_rows
            ]
        rows += rng_rows
        imps.append(importance(df, target))
    table = summarise(rows)
    table.to_csv(OUT / "metrics.csv", index=False, float_format="%.4f")
    cols = [
        "place_id",
        "name_1956",
        "gn_name",
        "country_1956",
        "unit_1956",
        "lat",
        "lon",
        "pop",
        *TARGETS,
    ]
    preds = pd.concat([df[cols], *oofs], axis=1).assign(label_gap="")
    # Settlements whose label was lost with a page of the scan: predicted by models fitted on
    # every cross-validation place (they are never scored).
    gap_preds = gap[[*cols, "label_gap"]].copy()
    for target in TARGETS:
        for name, (factory, feats) in MODELS.items():
            model = factory().fit(df[feats], df[target])
            gap_preds[f"{target}: {name}"] = model.predict_proba(gap[feats])[:, 1]
    preds = pd.concat([preds, gap_preds], ignore_index=True)
    preds.to_csv(OUT / "oof_predictions.csv", index=False, float_format="%.4f")
    pd.concat(imps).to_csv(OUT / "importance.csv", index=False, float_format="%.4f")
    manifest = {
        "milestone": "M1 vertical slice",
        "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        "git_commit": git_commit(),
        "data": {data_path.name: sha256(data_path)},
        "places_in_cv": len(df),
        "sealed_places_excluded": int(full["sealed"].sum()),
        "unknown_label_places_excluded": len(gap),
        "targets": TARGETS,
        "models": {k: v[1] for k, v in MODELS.items()},
        "cv": {"k": K, "block_km": BLOCK_KM, "shifts_km": SHIFTS_KM, "random_seeds": RANDOM_SEEDS},
        "note": "slice numbers check the joins end to end; they are not results (PLAN section 9)",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    show = table[
        [
            "target",
            "scheme",
            "model",
            "pr_auc_mean",
            "pr_auc_std",
            "roc_auc_mean",
            "brier_mean",
            "precision_at_k_mean",
            "base_rate",
        ]
    ]
    print(show.to_string(index=False, float_format=lambda v: f"{v:.3f}"))


if __name__ == "__main__":
    main()
