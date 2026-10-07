"""Metrics for T1 (PLAN section 5.5): PR-AUC (primary), ROC-AUC, Brier score, log-loss and
precision@k with k the true number of targets."""

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss, roc_auc_score


def precision_at_k(y, p) -> float:
    y, p = np.asarray(y), np.asarray(p)
    k = int(y.sum())
    if k == 0:
        return float("nan")
    top = np.argsort(-p, kind="stable")[:k]
    return float(y[top].mean())


def metrics(y, p) -> dict[str, float]:
    y, p = np.asarray(y), np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    if y.min() == y.max():
        return {}
    return {
        "pr_auc": average_precision_score(y, p),
        "roc_auc": roc_auc_score(y, p),
        "brier": brier_score_loss(y, p),
        "log_loss": log_loss(y, p),
        "precision_at_k": precision_at_k(y, p),
        "base_rate": float(y.mean()),
        "n": len(y),
    }
