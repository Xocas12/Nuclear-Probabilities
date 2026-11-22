"""Milestone M8: what drives targeting, and the single scoring of the sealed test.

    python -m nucprob.model.findings explain [--datasets a,b] [--algo lgbm]
    python -m nucprob.model.findings sealed --dataset napb90:very_high --algo lgbm

`explain` writes, per dataset, three views that should agree (PLAN section 6):
- family ablation: population alone, population plus each family, and all but each family;
  PR-AUC under spatial CV;
- permutation importance (drop in PR-AUC);
- mean |SHAP| (boosted trees).
Output goes to runs/m8-explain/ (runs/incomplete/ on an incomplete build).

`sealed` fits the chosen algorithm on every cross-validation place and scores the sealed test
blocks once, with a bootstrap confidence interval. It refuses:
- to run twice for a dataset: runs/m8-sealed/<dataset>.json is the record;
- to run on an incomplete build;
- to run if the protocol has changed.
"""

import argparse
import json

import numpy as np
import pandas as pd

from nucprob.model.evaluate import metrics
from nucprob.model.levels import manifest, out_dir
from nucprob.paths import PROCESSED, RUNS
from nucprob.playground.algos import algorithms
from nucprob.playground.datasets import load
from nucprob.playground.evaluate import evaluate, explain

DATASETS = ["sac1956", "napb90:very_high"]


def ablation(d, algo: str) -> pd.DataFrame:
    rows = []

    def score(label, sub):
        b = evaluate(sub, [algo], verbose=False)
        rows.append(
            {
                "features": label,
                "n_features": len(sub.features),
                "pr_auc": b["pr_auc_mean"].iloc[0],
                "pr_auc_std": b["pr_auc_std"].iloc[0],
            }
        )

    score("all", d)
    if "population" in d.families:
        score("population only", d.select("population"))
    for fam in d.families:
        if fam == "population":
            continue
        if "population" in d.families:
            score(f"population + {fam}", d.select(f"population,{fam}"))
        score(f"all but {fam}", d.select(drop=fam))
    return pd.DataFrame(rows)


def explain_all(datasets: list[str], algo: str) -> None:
    out = out_dir("m8-explain", datasets)
    out.mkdir(parents=True, exist_ok=True)
    for name in datasets:
        try:
            d = load(name)
        except (FileNotFoundError, KeyError) as err:
            print(f"{name}: skipped ({err})")
            continue
        print(d.summary())
        safe = name.replace(":", "_")
        ab = ablation(d, algo)
        ab.to_csv(out / f"{safe}_ablation.csv", index=False, float_format="%.4f")
        imp = explain(d, algo)
        imp.to_csv(out / f"{safe}_importance.csv", index=False, float_format="%.5f")
        print(ab.round(3).to_string(index=False))
        print(imp.head(12).round(4).to_string(index=False))
    (out / "manifest.json").write_text(
        json.dumps(manifest({"datasets": datasets, "algorithm": algo}), indent=2)
    )


def sealed(name: str, algo: str, n_boot: int = 1000, seed: int = 0) -> dict:
    if (PROCESSED / "INCOMPLETE_BUILD.txt").exists():
        raise RuntimeError("incomplete build: the sealed test is scored only on complete data")
    record = RUNS / "m8-sealed" / f"{name.replace(':', '_')}.json"
    if record.exists():
        raise RuntimeError(f"the sealed test of {name} was already scored: {record}")
    full = load(name, include_sealed=True)
    f = full.frame
    train, test = f[~f["sealed"]], f[f["sealed"]]
    model = algorithms(algo)[algo].factory().fit(train[full.features], train["y"])
    p = model.predict_proba(test[full.features])[:, 1]
    y = test["y"].to_numpy()
    point = metrics(y, p)
    rng = np.random.default_rng(seed)
    # Bootstrap over sealed blocks, so neighbours are resampled together.
    blocks = test["block"].to_numpy()
    ub = np.unique(blocks)
    boot = []
    for _ in range(n_boot):
        pick = rng.choice(ub, len(ub), replace=True)
        idx = np.concatenate([np.flatnonzero(blocks == b) for b in pick])
        m = metrics(y[idx], p[idx])
        if m:
            boot.append(m["pr_auc"])
    result = manifest(
        {
            "dataset": name,
            "algorithm": algo,
            "sealed_places": len(test),
            "metrics": point,
            "pr_auc_ci95": [float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))],
        }
    )
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return result


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="python -m nucprob.model.findings")
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("explain")
    e.add_argument("--datasets", default=",".join(DATASETS))
    e.add_argument("--algo", default="lgbm")
    s = sub.add_parser("sealed")
    s.add_argument("--dataset", required=True)
    s.add_argument("--algo", default="lgbm")
    a = p.parse_args(argv)
    if a.cmd == "explain":
        explain_all(a.datasets.split(","), a.algo)
    else:
        sealed(a.dataset, a.algo)


if __name__ == "__main__":
    main()
