"""Cross-validation helpers shared by the runs (PLAN section 5.2)."""

import subprocess
from collections.abc import Callable

import numpy as np
import pandas as pd

from nucprob.model.evaluate import metrics
from nucprob.paths import ROOT

Models = dict[str, tuple[Callable, list[str]]]  # name -> (factory, feature columns)
METRICS = ["pr_auc", "roc_auc", "brier", "log_loss", "precision_at_k"]


def cross_validate(
    df: pd.DataFrame, target: str, fold_ids: np.ndarray, models: Models
) -> tuple[list[dict], pd.DataFrame]:
    """Per-fold metrics and out-of-fold predictions of every model."""
    y = df[target].to_numpy()
    rows, oof = [], pd.DataFrame(index=df.index)
    for name, (factory, cols) in models.items():
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


def summarise(rows: list[dict], keys: list[str]) -> pd.DataFrame:
    """Mean and spread over folds of every metric, per `keys`."""
    df = pd.DataFrame(rows)
    agg = df.groupby(keys)[METRICS].agg(["mean", "std"])
    agg.columns = [f"{a}_{b}" for a, b in agg.columns]
    base = df.groupby(keys)["base_rate"].mean().rename("base_rate")
    return agg.join(base).reset_index()


def git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
