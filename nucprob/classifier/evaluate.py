"""The protocol's holdouts and comparison.

- Leave one plan out: fit on every other group of the scope, score each list of the left-out group.
- Spatial blocks: 5 folds of 300 km blocks on three shifted grids; a place stays on one side of a
  split in every document that holds it. One score per row: the mean of its three grids.
- Temporal: fit up to the cut year, score later documents, and the reverse.
Sealed places never enter here (nucprob.classifier.sealed reads them once).

Scope-wide readings are the positive-weighted mean of per-list PR-AUC over lists with at least
MIN_POSITIVES linked towns, so the SAC list does not hide the others: every list is also a row.
"""

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import average_precision_score

from nucprob.classifier.fit import Spec, fit_bagged
from nucprob.model.evaluate import metrics
from nucprob.model.splits import BLOCK_KM, assign_blocks, folds

MIN_POSITIVES = 2
GRID_OFFSETS = (0.0, 100.0, 200.0)
N_FOLDS = 5
N_BOOT = 2000
BOOT_SEED = 1956
TEMPORAL_CUT = 1956


def by_list(rows: pd.DataFrame, scores: dict[str, np.ndarray], holdout: str) -> list[dict]:
    """One row per list and model. A list too small to score is still a row, with no metrics."""
    out = []
    for plan, idx in rows.groupby("plan_id").indices.items():
        g = rows.iloc[idx]
        base = {
            "holdout": holdout,
            "plan_id": plan,
            "doc_type": g["doc_type"].iloc[0],
            "complete": bool(g["complete"].iloc[0]),
            "towns": len(g),
            "positives": int(g["listed"].sum()),
        }
        for name, s in scores.items():
            r = {}
            if base["positives"] >= MIN_POSITIVES and base["positives"] < base["towns"]:
                r = metrics(g["listed"], s[idx])
            out.append(base | {"model": name} | r)
    return out


def pr_auc(y: np.ndarray, s: np.ndarray) -> float:
    """Average precision with tied scores taken as one threshold: scikit-learn's number
    (tests/test_classifier.py), at a speed that makes 2,000 resamples per comparison practical."""
    order = np.argsort(-s, kind="stable")
    y, s = y[order], s[order]
    ends = np.append(np.flatnonzero(s[1:] != s[:-1]), len(s) - 1)
    hits = np.cumsum(y)[ends]
    return float(np.sum(np.diff(hits, prepend=0) * hits / (ends + 1)) / hits[-1])


def weighted_pr_auc(y: np.ndarray, s: np.ndarray, doc: np.ndarray) -> float:
    """Positive-weighted mean of per-list PR-AUC."""
    total, weight = 0.0, 0
    for d in np.unique(doc):
        k = doc == d
        n = int(y[k].sum())
        if MIN_POSITIVES <= n < k.sum():
            total += n * pr_auc(y[k], s[k])
            weight += n
    return total / weight if weight else float("nan")


def paired_bootstrap(
    y: np.ndarray,
    a: np.ndarray,
    b: np.ndarray,
    doc: np.ndarray,
    n: int = N_BOOT,
    seed: int = BOOT_SEED,
) -> dict[str, float]:
    """`a` minus `b` in the positive-weighted PR-AUC, 95% percentile interval. Resampled towns
    within each list and class score both models."""
    rng = np.random.default_rng(seed)
    strata = [np.flatnonzero((doc == d) & (y == v)) for d in np.unique(doc) for v in (0, 1)]
    strata = [s for s in strata if len(s)]
    deltas = np.empty(n)
    for i in range(n):
        idx = np.concatenate([rng.choice(s, size=len(s)) for s in strata])
        deltas[i] = weighted_pr_auc(y[idx], a[idx], doc[idx]) - weighted_pr_auc(
            y[idx], b[idx], doc[idx]
        )
    low, high = np.nanpercentile(deltas, [2.5, 97.5])
    return {
        "delta": weighted_pr_auc(y, a, doc) - weighted_pr_auc(y, b, doc),
        "low": float(low),
        "high": float(high),
        "excludes_zero": bool(low > 0 or high < 0),
    }


def _scored(rows: pd.DataFrame, scores: dict[str, np.ndarray]) -> pd.DataFrame:
    keep = rows[["plan_id", "place_id", "listed"]].reset_index(drop=True)
    return keep.assign(**scores)


def leave_one_plan_out(
    table: pd.DataFrame, models: list[Spec], n_bags: int
) -> tuple[list[dict], pd.DataFrame]:
    """Rows of `by_list`, and every held-out score, for the paired comparison."""
    out, kept = [], []
    for group in sorted(table["group"].unique()):
        test = table["group"] == group
        rows = table[test].reset_index(drop=True)
        train = table[~test].reset_index(drop=True)
        if train["listed"].sum() == 0 or rows["listed"].sum() == 0:
            continue
        scores = {m.name: fit_bagged(m, train, n_bags).score(rows) for m in models}
        out += by_list(rows, scores, f"leave-one-plan-out ({group})")
        kept.append(_scored(rows, scores))
    return out, pd.concat(kept, ignore_index=True) if kept else pd.DataFrame()


def spatial_scores(table: pd.DataFrame, models: list[Spec], n_bags: int) -> dict[str, np.ndarray]:
    """The mean of each row's held-out score on the three shifted grids."""
    table = table.reset_index(drop=True)
    total = {m.name: np.zeros(len(table)) for m in models}
    lat, lon = table["lat"].to_numpy(float), table["lon"].to_numpy(float)
    for offset in GRID_OFFSETS:
        blocks = pd.Series(assign_blocks(lat, lon, BLOCK_KM, offset), index=table.index)
        fold = folds(blocks, table["listed"], N_FOLDS, seed=int(offset))
        for f in range(N_FOLDS):
            test = fold == f
            for m in models:
                fitted = fit_bagged(m, table[~test], n_bags)
                total[m.name][test] += fitted.score(table[test]) / len(GRID_OFFSETS)
    return total


def temporal(
    table: pd.DataFrame, models: list[Spec], n_bags: int
) -> tuple[list[dict], dict[str, pd.DataFrame]]:
    out, kept = [], {}
    early = table["year"] <= TEMPORAL_CUT
    for name, train, test in (
        (f"temporal: fit up to {TEMPORAL_CUT}, score later", table[early], table[~early]),
        (
            f"temporal reversed: fit after {TEMPORAL_CUT}, score earlier",
            table[~early],
            table[early],
        ),
    ):
        if train["listed"].sum() == 0 or test.empty:
            continue
        rows = test.reset_index(drop=True)
        train = train.reset_index(drop=True)
        scores = {m.name: fit_bagged(m, train, n_bags).score(rows) for m in models}
        out += by_list(rows, scores, name)
        kept[name] = _scored(rows, scores)
    return out, kept


def calibration_curve(y: np.ndarray, p: np.ndarray, bins: int = 10) -> pd.DataFrame:
    """Observed rate against mean score in quantile bins."""
    q = pd.qcut(pd.Series(p).rank(method="first"), bins, labels=False)
    g = pd.DataFrame({"y": y, "p": p, "bin": q}).groupby("bin")
    return g.agg(n=("y", "size"), mean_score=("p", "mean"), observed=("y", "mean")).reset_index()


def cross_fit_isotonic(y: np.ndarray, p: np.ndarray, fold: np.ndarray) -> np.ndarray:
    """Isotonic calibration fitted outside each fold, so a town does not calibrate itself."""
    out = np.zeros(len(y))
    for f in np.unique(fold):
        test = fold == f
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        iso.fit(p[~test], y[~test])
        out[test] = iso.predict(p[test])
    return out
