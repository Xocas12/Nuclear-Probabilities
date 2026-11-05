"""The bootstrap seed check of configs/protocol_amendment_18.yaml.

    python -m nucprob.classifier.seed_check

Reads the committed held-out scores and comparison.csv and refits nothing. For every comparison of
REPORT's primary table (each scope's selected candidate against both baselines, each holdout and list
set) it repeats the protocol's town and block bootstraps under seeds 1 to 20 and gives each seed's
verdict by the protocol's rule. Writes runs/classifier/seed_check.csv (one row per comparison and seed),
seed_check_summary.csv (one row per comparison) and seed_check_manifest.json.

The resampling draws exactly what nucprob.classifier.evaluate draws for the same seed; only the
PR-AUC of each resample is computed in one pass over all lists rather than list by list
(tests/test_seed_check.py checks both against evaluate under seed 1956).
"""

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import datetime as dt
import json

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from nucprob.classifier import evaluate as ev
from nucprob.classifier.run import SAC
from nucprob.outputs import hashes, start_record
from nucprob.paths import RUNS
from nucprob.sources.fetch import sha256

SEEDS = tuple(range(1, 21))
OUT = RUNS / "classifier"
AMENDMENT = "configs/protocol_amendment_18.yaml"


def fast_weighted_pr_auc(y: np.ndarray, s: np.ndarray, code: np.ndarray, n_docs: int) -> float:
    """ev.weighted_pr_auc, with `code` the list as integers 0..n_docs-1: per list, average precision
    with tied scores as one threshold, weighted by positives, over lists with
    MIN_POSITIVES <= positives < towns."""
    order = np.lexsort((-s, code))
    y, s, code = y[order], s[order], code[order]
    size = np.bincount(code, minlength=n_docs)
    pos = np.bincount(code, weights=y, minlength=n_docs)
    start = np.concatenate([[0], np.cumsum(size)[:-1]])
    n = len(y)
    last = np.ones(n, bool)
    last[:-1] = (s[1:] != s[:-1]) | (code[1:] != code[:-1])
    cum = np.cumsum(y)
    before = np.concatenate([[0], cum])[start][code]  # positives before each row's list
    hits = cum - before
    rank = np.arange(n) - start[code] + 1
    ends = np.flatnonzero(last)
    h, d = hits[ends], code[ends]
    prev = np.concatenate([[0], h[:-1]])
    prev[np.concatenate([[True], d[1:] != d[:-1]])] = 0
    terms = np.bincount(d, weights=(h - prev) * h / rank[ends], minlength=n_docs)
    ok = (pos >= ev.MIN_POSITIVES) & (pos < size)
    weight = pos[ok].sum()
    return float(terms[ok].sum() / weight) if weight else float("nan")


def bootstraps(y, a, b, doc, block, seed: int, n: int = ev.N_BOOT) -> dict[str, float]:
    """ev.paired_bootstrap and ev.block_bootstrap under one seed: the same draws, the same bounds."""
    names, code = np.unique(doc, return_inverse=True)
    k = len(names)

    def delta(idx):
        return fast_weighted_pr_auc(y[idx], a[idx], code[idx], k) - fast_weighted_pr_auc(
            y[idx], b[idx], code[idx], k
        )

    rng = np.random.default_rng(seed)
    strata = [np.flatnonzero((doc == d) & (y == v)) for d in names for v in (0, 1)]
    strata = [s for s in strata if len(s)]
    town = np.array(
        [delta(np.concatenate([rng.choice(s, size=len(s)) for s in strata])) for _ in range(n)]
    )
    rng = np.random.default_rng(seed)
    members = [np.flatnonzero(block == j) for j in np.unique(block)]
    blocks = np.array(
        [
            delta(
                np.concatenate([members[j] for j in rng.integers(len(members), size=len(members))])
            )
            for _ in range(n)
        ]
    )
    low, high = np.nanpercentile(town, [2.5, 97.5])
    out = {"low": float(low), "high": float(high)}
    if np.isnan(blocks).all():
        return out | {"block_low": np.nan, "block_high": np.nan}
    block_low, block_high = np.nanpercentile(blocks, [2.5, 97.5])
    return out | {"block_low": float(block_low), "block_high": float(block_high)}


def rule(r) -> str:
    """The protocol's verdict (nucprob.classifier.report.verdict), from one seed's bounds."""
    from nucprob.classifier.report import verdict

    return verdict(r)


def primary(comp: pd.DataFrame, selection: pd.DataFrame) -> pd.DataFrame:
    """The comparisons of REPORT's primary table."""
    from nucprob.classifier.report import HOLDOUTS, PLUS, RULE, SCOPES

    best = selection[selection["selected"]].set_index("scope")["model"]
    keep = (
        comp["scope"].isin(SCOPES)
        & comp["holdout"].isin(HOLDOUTS)
        & comp["against"].isin((RULE, PLUS))
        & (comp["model"] == comp["scope"].map(best))
    )
    out = comp[keep]
    return out[~out.duplicated(["scope", "holdout", "lists", "against"])].reset_index(drop=True)


def part_of(scores: pd.DataFrame, scope: str, holdout: str, lists: str) -> pd.DataFrame:
    p = scores[(scores["scope"] == scope) & (scores["holdout"] == holdout)]
    return p[p["plan_id"] != SAC] if lists == "lists other than SAC" else p


def one(part: pd.DataFrame, model: str, against: str, seed: int) -> dict:
    return {"seed": seed} | bootstraps(
        part["listed"].to_numpy(int),
        part[model].to_numpy(),
        part[against].to_numpy(),
        part["plan_id"].to_numpy(),
        part["block"].to_numpy(),
        seed,
    )


def summarise(per_seed: pd.DataFrame, rows: pd.DataFrame) -> pd.DataFrame:
    key = ["scope", "holdout", "lists", "against"]
    out = []
    for _, r in rows.iterrows():
        g = per_seed.merge(pd.DataFrame([r[key]]), on=key)
        committed = rule(r)
        counts = g["verdict"].value_counts()
        out.append(
            dict(r[[*key, "model"]])
            | {
                "verdict_seed_1956": committed,
                "seeds": len(g),
                "seeds_gain": int(counts.get("gain", 0)),
                "seeds_loss": int(counts.get("loss", 0)),
                "seeds_neither": int(counts.get("neither", 0)),
                "seeds_not_a_reading": int(counts.get("not a reading", 0)),
                "seed_stable": bool((g["verdict"] == committed).all()),
                "min_low": g["low"].min(),
                "max_high": g["high"].max(),
                "min_block_low": g["block_low"].min(),
                "max_block_high": g["block_high"].max(),
            }
        )
    return pd.DataFrame(out)


def main() -> None:
    started = start_record()
    comp = pd.read_csv(OUT / "comparison.csv")
    rows = primary(comp, pd.read_csv(OUT / "selection.csv"))
    scores = pd.read_csv(OUT / "held_out_scores.csv.gz")
    tasks = [(r, seed) for _, r in rows.iterrows() for seed in SEEDS]
    print(f"{len(rows)} comparisons x {len(SEEDS)} seeds", flush=True)
    results = Parallel(n_jobs=3, verbose=5)(
        delayed(one)(
            part_of(scores, r["scope"], r["holdout"], r["lists"]), r["model"], r["against"], seed
        )
        for r, seed in tasks
    )
    per_seed = []
    for (r, _), res in zip(tasks, results, strict=True):
        row = (
            dict(
                r[
                    [
                        "scope",
                        "holdout",
                        "lists",
                        "model",
                        "against",
                        "train_positives_min",
                        "constant_score",
                        "positives",
                    ]
                ]
            )
            | res
        )
        row["verdict"] = rule(row)
        per_seed.append(row)
    per_seed = pd.DataFrame(per_seed)
    per_seed.to_csv(OUT / "seed_check.csv", index=False, float_format="%.4f")
    summarise(per_seed, rows).to_csv(
        OUT / "seed_check_summary.csv", index=False, float_format="%.4f"
    )
    manifest = {
        "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        **started,
        "amendment": AMENDMENT,
        "seeds": list(SEEDS),
        "bootstrap": ev.N_BOOT,
        "inputs": hashes(
            OUT / f for f in ("comparison.csv", "selection.csv", "held_out_scores.csv.gz")
        ),
        "outputs": hashes(OUT / f for f in ("seed_check.csv", "seed_check_summary.csv")),
    }
    (OUT / "seed_check_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"done; {sha256(OUT / 'seed_check_summary.csv')[:12]}", flush=True)


if __name__ == "__main__":
    main()
