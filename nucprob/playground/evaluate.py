"""Cross-validate algorithms on a dataset, score a model trained on one dataset on another, and
explain a fitted model.

Cross-validation schemes:
- `spatial` (default): folds of 300 km blocks with balanced positives (PLAN section 5.2);
- `random`: random folds (optimistic: neighbours leak across folds);
- `country`: leave one country (or state, or republic) out.
"""

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

from nucprob.model.evaluate import metrics
from nucprob.model.splits import folds
from nucprob.paths import RUNS
from nucprob.playground.algos import algorithms
from nucprob.playground.datasets import Data

METRICS = ["pr_auc", "roc_auc", "brier", "log_loss", "precision_at_k"]


def fold_ids(data: Data, scheme: str = "spatial", k: int = 5, seed: int = 0) -> np.ndarray:
    f = data.frame
    if scheme == "spatial":
        return folds(f["block"], f["y"], k, seed)
    if scheme == "random":
        return np.random.default_rng(seed).integers(0, k, len(f))
    if scheme == "country":
        codes, _ = pd.factorize(f["country"].fillna("?"))
        return codes
    raise ValueError(f"unknown scheme {scheme}: spatial, random or country")


def evaluate(
    data: Data,
    algos: str | list[str] = "fast",
    scheme: str = "spatial",
    k: int = 5,
    seed: int = 0,
    out: str | Path | None = None,
    verbose: bool = True,
) -> pd.DataFrame:
    """Per-algorithm mean and spread of each metric over folds; out-of-fold predictions are
    written with the leaderboard when `out` is given."""
    ids = fold_ids(data, scheme, k, seed)
    X, y = data.X, data.y.to_numpy()
    rows, oof = [], pd.DataFrame({"id": data.frame["id"], "y": y, "fold": ids})
    for name, algo in algorithms(algos).items():
        pred = np.full(len(y), np.nan)
        for fold in np.unique(ids):
            test = ids == fold
            if y[~test].min() == y[~test].max():
                continue
            model = algo.factory().fit(X[~test], y[~test])
            pred[test] = model.predict_proba(X[test])[:, 1]
            m = metrics(y[test], pred[test])
            if m:
                rows.append({"algorithm": name, "fold": int(fold), **m})
        oof[name] = pred
        if verbose:
            ok = ~np.isnan(pred)
            m = metrics(y[ok], pred[ok]) or {}
            print(
                f"  {name:12s} pooled PR-AUC {m.get('pr_auc', np.nan):.3f}  "
                f"ROC-AUC {m.get('roc_auc', np.nan):.3f}"
            )
    board = _board(rows)
    if out is not None:
        _write(out, data, board, oof, {"scheme": scheme, "k": k, "seed": seed})
    return board


def _board(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    agg = df.groupby("algorithm")[METRICS].agg(["mean", "std"])
    agg.columns = [f"{a}_{b}" for a, b in agg.columns]
    agg["folds"] = df.groupby("algorithm").size()
    agg["base_rate"] = df.groupby("algorithm")["base_rate"].mean()
    return agg.sort_values("pr_auc_mean", ascending=False).reset_index()


def transfer(
    train: Data, test: Data, algos: str | list[str] = "fast", verbose: bool = True
) -> pd.DataFrame:
    """Fit on all of `train` with the features both datasets share; score `test`."""
    cols = [c for c in train.features if c in test.features]
    if not cols:
        raise ValueError("the two datasets share no features")
    rows = []
    for name, algo in algorithms(algos).items():
        model = algo.factory().fit(train.frame[cols], train.y)
        p = model.predict_proba(test.frame[cols])[:, 1]
        m = metrics(test.y.to_numpy(), p) or {}
        rows.append({"algorithm": name, **m})
        if verbose:
            print(
                f"  {name:12s} PR-AUC {m.get('pr_auc', np.nan):.3f}  ROC-AUC {m.get('roc_auc', np.nan):.3f}"
            )
    board = pd.DataFrame(rows)
    board.attrs["features"] = cols
    return board.sort_values("pr_auc", ascending=False) if "pr_auc" in board else board


def explain(data: Data, algo: str = "lgbm", n_repeats: int = 5, seed: int = 0) -> pd.DataFrame:
    """Permutation importance (drop in PR-AUC on the training data, so a guide, not a test) and,
    for tree models where shap is installed, mean |SHAP|."""
    from sklearn.inspection import permutation_importance

    a = algorithms(algo)[algo]
    model = a.factory().fit(data.X, data.y)
    pi = permutation_importance(
        model, data.X, data.y, scoring="average_precision", n_repeats=n_repeats, random_state=seed
    )
    out = pd.DataFrame(
        {
            "feature": data.features,
            "family": [
                next((f for f, c in data.families.items() if x in c), "") for x in data.features
            ],
            "perm_importance": pi.importances_mean,
            "perm_std": pi.importances_std,
        }
    )
    try:
        import shap

        if a.family == "boosting":
            sv = shap.TreeExplainer(model).shap_values(data.X)
            sv = sv[1] if isinstance(sv, list) else sv
            out["mean_abs_shap"] = np.abs(np.asarray(sv)).mean(axis=0)
    except Exception as err:  # shap is optional; a failure only drops the column
        out.attrs["shap_error"] = str(err)
    return out.sort_values("perm_importance", ascending=False).reset_index(drop=True)


def run_dir(label: str) -> Path:
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%d-%H%M%S")
    safe = label.replace(":", "_").replace("/", "_")
    return RUNS / "playground" / f"{stamp}-{safe}"


def _write(out, data: Data, board, oof, cv: dict) -> None:
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    board.to_csv(out / "leaderboard.csv", index=False, float_format="%.4f")
    oof.to_csv(out / "oof_predictions.csv", index=False, float_format="%.4f")
    meta = {
        "dataset": data.name,
        "rows": len(data.frame),
        "positives": int(data.y.sum()),
        "features": data.features,
        "cv": cv,
        "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
    }
    (out / "manifest.json").write_text(json.dumps(meta, indent=2))
