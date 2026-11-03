"""Score the sealed places once (configs/protocol.yaml, evaluation.holdouts.sealed, and
configs/protocol_amendment_11.yaml, which fixes the reading before any score exists).

    python -m nucprob.classifier.sealed

Fits each scope's models on every usable (non-sealed) row of that scope and scores the sealed bloc
places on the SAC list: the `never_scored` places first, since only they are blind, and the whole
sealed set beside them. Writes runs/classifier/sealed/: metrics.csv (every model, with a stratified
bootstrap interval for PR-AUC), comparison.csv (each scope's selected candidate against population +
country, the primary reading, and against the population rule, with the stratified and block
intervals) and LOCK.json, which holds the time, the git commit and the protocol's hashes and is taken
before any score exists. With the lock present it refuses to run: a sealed set read twice is not sealed.
"""

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

from nucprob.classifier.evaluate import BOOT_SEED, N_BOOT, block_bootstrap, paired_bootstrap, pr_auc
from nucprob.classifier.fit import N_BAGS, fit_bagged, specs
from nucprob.classifier.run import SAC, positives_of, scopes, usable
from nucprob.model.cv import git_commit
from nucprob.model.evaluate import metrics
from nucprob.paths import PROCESSED, ROOT, RUNS
from nucprob.sources.fetch import sha256

OUT = RUNS / "classifier" / "sealed"
AMENDMENT = ROOT / "configs" / "protocol_amendment_11.yaml"
BASELINES = ("population + country", "population rule")
POPULATIONS = ("never_scored", "all sealed")


class AlreadyScored(RuntimeError):
    pass


def claim(lock: Path, record: dict) -> None:
    """Take the lock before any score exists; refuse if it is taken."""
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(lock, "x", encoding="utf-8") as fh:
            json.dump(record, fh, indent=2)
    except FileExistsError as e:
        raise AlreadyScored(f"{lock} exists: the sealed set has been scored") from e


def pr_auc_interval(y: np.ndarray, s: np.ndarray, n: int = N_BOOT, seed: int = BOOT_SEED):
    """95% percentile interval of one model's PR-AUC, towns resampled within class."""
    rng = np.random.default_rng(seed)
    strata = [np.flatnonzero(y == v) for v in (0, 1)]
    draws = np.empty(n)
    for i in range(n):
        idx = np.concatenate([rng.choice(k, size=len(k)) for k in strata])
        draws[i] = pr_auc(y[idx], s[idx])
    low, high = np.percentile(draws, [2.5, 97.5])
    return float(low), float(high)


def read(
    sealed: pd.DataFrame,
    scores: dict[tuple[str, str], np.ndarray],
    selected: dict[str, str],
    n: int = N_BOOT,
    populations: dict[str, np.ndarray] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The amendment's reading of scores already made: (metrics, comparison). `scores` maps
    (scope, model) to one score per row of `sealed`; `selected` maps scope to its candidate.
    `populations` maps a name to a row mask; by default the eleventh amendment's two, never_scored
    and all sealed. The first population's comparison with population + country is the primary."""
    if populations is None:
        populations = {
            "never_scored": sealed["never_scored"].astype(bool).to_numpy(),
            "all sealed": np.ones(len(sealed), bool),
        }
    first = next(iter(populations))
    rows, comp = [], []
    y_all = sealed["listed"].to_numpy(int)
    doc_all = sealed["plan_id"].to_numpy()
    block_all = sealed["block"].to_numpy()
    for population, keep in populations.items():
        y, doc, block = y_all[keep], doc_all[keep], block_all[keep]
        for (scope, model), s in scores.items():
            m = metrics(y, s[keep])
            if m:
                m["pr_auc_low"], m["pr_auc_high"] = pr_auc_interval(y, s[keep], n)
            rows.append(
                {
                    "scope": scope,
                    "model": model,
                    "population": population,
                    "positives": int(y.sum()),
                }
                | m
            )
        for scope, cand in selected.items():
            for against in BASELINES:
                a, b = scores[(scope, cand)][keep], scores[(scope, against)][keep]
                r = paired_bootstrap(y, a, b, doc, n=n) | block_bootstrap(y, a, b, doc, block, n=n)
                gain = r["excludes_zero"] and r["block_excludes_zero"]
                comp.append(
                    {
                        "scope": scope,
                        "population": population,
                        "primary": population == first and against == BASELINES[0],
                        "model": cand,
                        "against": against,
                        "positives": int(y.sum()),
                        "rows": len(y),
                        "blocks": len(np.unique(block)),
                        "positive_blocks": len(np.unique(block[y == 1])),
                        "base_rate": float(y.mean()),
                        "a_pr_auc": pr_auc(y, a),
                        "b_pr_auc": pr_auc(y, b),
                    }
                    | r
                    | {"verdict": ("gain" if r["delta"] > 0 else "loss") if gain else "neither"}
                )
    return pd.DataFrame(rows), pd.DataFrame(comp)


def main() -> None:
    claim(
        OUT / "LOCK.json",
        {
            "scored": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            "git_commit": git_commit(),
            "protocol_sha256": sha256(ROOT / "configs" / "protocol.yaml"),
            "amendment_11_sha256": sha256(AMENDMENT),
            "table_sha256": sha256(PROCESSED / "classifier_table.parquet"),
        },
    )
    full = pd.read_parquet(PROCESSED / "classifier_table.parquet")
    table = usable(full)
    groups, _ = scopes(table, positives_of(full))
    sel = pd.read_csv(RUNS / "classifier" / "selection.csv")
    selected = dict(sel.loc[sel["selected"], ["scope", "model"]].to_numpy())
    sealed = full[full["sealed"].astype(bool) & full["plan_id"].eq(SAC)].reset_index(drop=True)
    scores = {}
    for scope, train in groups.items():
        for m in specs():
            scores[(scope, m.name)] = fit_bagged(m, train, N_BAGS).score(sealed)
    pd.DataFrame(
        {"place_id": sealed["place_id"], "never_scored": sealed["never_scored"].astype(bool)}
        | {f"{scope} | {model}": s for (scope, model), s in scores.items()}
    ).to_csv(OUT / "scores.csv.gz", index=False, float_format="%.6f")
    met, comp = read(sealed, scores, selected)
    met.to_csv(OUT / "metrics.csv", index=False, float_format="%.4f")
    comp.to_csv(OUT / "comparison.csv", index=False, float_format="%.4f")
    print(comp.round(3).to_string(index=False))
    print("scored once; lock at", OUT / "LOCK.json")


if __name__ == "__main__":
    main()
