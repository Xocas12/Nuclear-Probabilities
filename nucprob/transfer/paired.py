"""Paired bootstrap of each transfer model against the population rule, list by list.

    python -m nucprob.transfer.paired

PLAN section 5.5 makes PR-AUC the primary metric because the classes are imbalanced, and the
transfer lists have base rates of 1-22%. A model-minus-rule difference read off one ROC table
says nothing about whether it could be noise, so this writes, for every scored list and every
model, the difference from the population rule in PR-AUC, ROC-AUC and precision@k with a 95%
percentile interval. The bootstrap is paired (the same resampled towns score both models) and
stratified (positives and negatives are resampled separately, so every resample keeps the
list's base rate and both classes).

Reads runs/m4-transfer-check/scores.csv and writes runs/m4-transfer-check/paired.csv.
nucprob.transfer.check calls `compare` itself after a full run; running this module alone
rebuilds paired.csv from the committed scores without the processed data. scores.csv is
rounded to four decimals, which ties a few scores, so a value rebuilt from it can differ from
metrics.csv: by under 0.005 on most lists, but by 0.33 in the logistic model's PR-AUC on the
two-town Taiwan Strait list. The population rule and "LightGBM, common" are unaffected.
"""

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from nucprob.paths import RUNS

OUT = RUNS / "m4-transfer-check"
BASELINE = "population rule"
METRICS = ("pr_auc", "roc_auc", "precision_at_k")
N_BOOT = 2000
SEED = 0
LEVEL = 0.95


def _clip(p: np.ndarray) -> np.ndarray:
    # As nucprob.model.evaluate.metrics does, so the point estimates match metrics.csv.
    return np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)


def score_rows(y: np.ndarray, p: np.ndarray) -> dict[str, np.ndarray]:
    """PR-AUC, ROC-AUC and precision@k for each row of a (resamples x towns) pair of arrays.

    PR-AUC is average precision with tied scores taken as one threshold, as scikit-learn
    computes it; ROC-AUC is the Mann-Whitney statistic with ties counted half; precision@k
    takes the k highest scores in stable order, k the number listed, as
    nucprob.model.evaluate.precision_at_k does. Every row must hold both classes.
    """
    y, p = np.atleast_2d(y).astype(int), np.atleast_2d(p).astype(float)
    n1 = y.sum(axis=1)
    n0 = y.shape[1] - n1
    order = np.argsort(-p, axis=1, kind="stable")
    ys = np.take_along_axis(y, order, axis=1)
    ps = np.take_along_axis(p, order, axis=1)
    tp = np.cumsum(ys, axis=1)
    rank = np.arange(1, y.shape[1] + 1)
    # A threshold sits at the end of each block of tied scores.
    end = np.ones_like(ps, dtype=bool)
    end[:, :-1] = ps[:, :-1] != ps[:, 1:]
    tp_end = np.maximum.accumulate(np.where(end, tp, 0), axis=1)
    prev = np.zeros_like(tp_end)
    prev[:, 1:] = tp_end[:, :-1]
    ap = np.sum(np.where(end, (tp - prev) * tp / rank, 0.0), axis=1) / n1
    ranks = rankdata(p, axis=1)
    roc = (np.sum(ranks * y, axis=1) - n1 * (n1 + 1) / 2) / (n1 * n0)
    top = rank[None, :] <= n1[:, None]
    pak = np.sum(ys * top, axis=1) / n1
    return {"pr_auc": ap, "roc_auc": roc, "precision_at_k": pak}


def paired_bootstrap(
    y, rule, model, n_boot: int = N_BOOT, seed: int = SEED, level: float = LEVEL
) -> dict[str, dict[str, float]]:
    """Model minus rule for each metric, with a percentile interval from a stratified, paired
    bootstrap. Returns {metric: {rule_value, model_value, diff, lo, hi}}."""
    y = np.asarray(y).astype(int)
    rule, model = _clip(rule), _clip(model)
    pos, neg = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
    if len(pos) == 0 or len(neg) == 0:
        raise ValueError("both classes are needed")
    rng = np.random.default_rng(seed)
    idx = np.hstack([rng.choice(pos, (n_boot, len(pos))), rng.choice(neg, (n_boot, len(neg)))])
    at_rule, at_model = score_rows(y, rule), score_rows(y, model)
    boot_rule, boot_model = score_rows(y[idx], rule[idx]), score_rows(y[idx], model[idx])
    tail = (1 - level) / 2
    out = {}
    for m in METRICS:
        lo, hi = np.quantile(boot_model[m] - boot_rule[m], [tail, 1 - tail])
        r, s = float(at_rule[m][0]), float(at_model[m][0])
        out[m] = {"rule_value": r, "model_value": s, "diff": s - r, "lo": lo, "hi": hi}
    return out


def compare(
    scores: pd.DataFrame,
    models: list[str],
    min_positives: int,
    baseline: str = BASELINE,
    n_boot: int = N_BOOT,
    seed: int = SEED,
) -> pd.DataFrame:
    """One row per list, model and metric: the rule, the model, their difference and its
    interval. Every model on a list is resampled with the same draws (one seed per run)."""
    rows = []
    for plan, g in scores.groupby("plan_id", sort=True):
        y = g["listed"].to_numpy()
        if y.sum() < min_positives:
            continue
        base = {
            "plan_id": plan,
            "region": g["region"].iloc[0],
            "towns": len(g),
            "listed": int(y.sum()),
        }
        for name in models:
            if name == baseline:
                continue
            res = paired_bootstrap(y, g[baseline], g[name], n_boot=n_boot, seed=seed)
            for metric, r in res.items():
                rows.append(base | {"model": name, "metric": metric} | r)
    table = pd.DataFrame(rows)
    table["excludes_zero"] = (table["lo"] > 0) | (table["hi"] < 0)
    return table


def write(table: pd.DataFrame, out=OUT) -> None:
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "paired.csv", index=False, float_format="%.4f")


def main() -> None:
    from nucprob.transfer.check import MIN_POSITIVES

    scores = pd.read_csv(OUT / "scores.csv")
    models = [c for c in scores.columns[scores.columns.get_loc("listed") + 1 :]]
    table = compare(scores, models, MIN_POSITIVES)
    write(table)
    show = table[table["model"] == "LightGBM, common"].pivot_table(
        index=["plan_id", "towns", "listed"], columns="metric", values=["diff", "lo", "hi"]
    )
    print(show.round(3).to_string())


if __name__ == "__main__":
    main()
