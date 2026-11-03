"""Intervals for the document identification check (configs/protocol_amendment_13.yaml).

    python -m nucprob.classifier.identification

The sixth amendment's check asks how often a classifier names a row's document from its columns, with folds
grouped by place, against always naming the largest document. This module recomputes that check, stops if it
differs from runs/classifier/document_identification.csv, and adds what the thirteenth amendment fixed:
- a place-clustered bootstrap of each set's out-of-fold predictions (accuracy, accuracy minus the largest
  document's share, accuracy minus "all permitted");
- the accuracy spread over 10 further place-grouped splits;
- a capacity probe: the same at 300 boosting iterations instead of 60.

Writes runs/classifier/identification/intervals.csv, splits.csv, capacity.csv and manifest.json. Each step
is checkpointed under data/interim/identification/; the manifest lists the steps still pending, and the report
says which readings are pending until none is.
"""

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "3")

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold, cross_val_predict

from nucprob.classifier.features import DEFENCE, MILITARY, NMC_FEATURES
from nucprob.classifier.fit import ALL_FEATURES
from nucprob.classifier.run import positives_of, scopes, usable
from nucprob.classifier.sensitivity import without
from nucprob.outputs import hashes, start_record
from nucprob.paths import DATA, PROCESSED, ROOT, RUNS
from nucprob.sources.fetch import sha256

OUT = RUNS / "classifier" / "identification"
WORK = DATA / "interim" / "identification"  # checkpoints, git-ignored
SCOPE = "global, all attacker documents"
SETS = {
    "all permitted": ALL_FEATURES,
    "no national power": without(NMC_FEATURES),
    "no source markers": without(NMC_FEATURES, DEFENCE, MILITARY),
    "population only": ["log_pop"],
}
REFERENCE = "all permitted"
N_BOOT, SEED = 2000, 1956
SPLIT_SEEDS = range(10)
ITERATIONS, PROBE_ITERATIONS = 60, 300


def predict(rows: pd.DataFrame, columns: list[str], cv, max_iter: int = ITERATIONS) -> np.ndarray:
    """Out-of-fold document predictions, as the sixth amendment's check makes them."""
    return cross_val_predict(
        HistGradientBoostingClassifier(max_iter=max_iter, max_depth=4, random_state=0),
        rows[columns],
        codes(rows),
        cv=cv,
        groups=rows["place_id"].to_numpy(),
    )


def codes(rows: pd.DataFrame) -> np.ndarray:
    return rows["plan_id"].astype("category").cat.codes.to_numpy()


def place_resamples(places: np.ndarray, n: int = N_BOOT, seed: int = SEED) -> list[np.ndarray]:
    """Row indices of n resamples that draw places with replacement and keep each place's rows together."""
    _, inverse = np.unique(places, return_inverse=True)
    members = pd.Series(np.arange(len(places))).groupby(inverse).apply(np.asarray).to_list()
    rng = np.random.default_rng(seed)
    return [
        np.concatenate([members[k] for k in rng.integers(0, len(members), len(members))])
        for _ in range(n)
    ]


def verdict(lo: float, hi: float) -> str:
    if lo > 0:
        return "above"
    if hi < 0:
        return "below"
    return "cannot be told apart"


def intervals(
    y: np.ndarray, preds: dict[str, np.ndarray], resamples: list[np.ndarray]
) -> pd.DataFrame:
    """Per set: accuracy, its gap to the largest document's share and to the reference set, each with a
    95% percentile interval over the same place resamples."""
    largest = np.bincount(y).argmax()
    hit = {name: (p == y).astype(float) for name, p in preds.items()}
    base = (y == largest).astype(float)
    out = []
    for name in preds:
        acc = np.array([hit[name][r].mean() for r in resamples])
        over = np.array([hit[name][r].mean() - base[r].mean() for r in resamples])
        vs = np.array([hit[name][r].mean() - hit[REFERENCE][r].mean() for r in resamples])
        row = {
            "columns": name,
            "rows": len(y),
            "accuracy": hit[name].mean(),
            "accuracy_lo": np.percentile(acc, 2.5),
            "accuracy_hi": np.percentile(acc, 97.5),
            "largest_document_share": base.mean(),
            "over_largest": hit[name].mean() - base.mean(),
            "over_largest_lo": np.percentile(over, 2.5),
            "over_largest_hi": np.percentile(over, 97.5),
            "over_reference": hit[name].mean() - hit[REFERENCE].mean(),
            "over_reference_lo": np.percentile(vs, 2.5),
            "over_reference_hi": np.percentile(vs, 97.5),
        }
        row["over_largest_verdict"] = verdict(row["over_largest_lo"], row["over_largest_hi"])
        row["over_reference_verdict"] = (
            "" if name == REFERENCE else verdict(row["over_reference_lo"], row["over_reference_hi"])
        )
        out.append(row)
    return pd.DataFrame(out)


def capacity(y: np.ndarray, at: dict[int, dict[str, np.ndarray]], resamples) -> pd.DataFrame:
    """ "no source markers" minus "all permitted" at each iteration count, and the amendment's call."""
    a, b = "no source markers", REFERENCE
    out = []
    for n, preds in at.items():
        ha, hb = (preds[a] == y).astype(float), (preds[b] == y).astype(float)
        d = np.array([ha[r].mean() - hb[r].mean() for r in resamples])
        lo, hi = np.percentile(d, 2.5), np.percentile(d, 97.5)
        out.append(
            {
                "max_iter": n,
                "all_permitted": hb.mean(),
                "no_source_markers": ha.mean(),
                "difference": ha.mean() - hb.mean(),
                "difference_lo": lo,
                "difference_hi": hi,
                "excludes_zero": bool(lo > 0 or hi < 0),
            }
        )
    frame = pd.DataFrame(out).set_index("max_iter")
    explained = (
        frame.at[ITERATIONS, "excludes_zero"] and not frame.at[PROBE_ITERATIONS, "excludes_zero"]
    )
    frame["call"] = "explained by capacity" if explained else "not explained"
    return frame.reset_index()


def step_key() -> dict:
    """What a checkpoint must share with this run to be reused: this module, the locked dependencies
    and the table."""
    return {
        "code_sha256": sha256(Path(__file__)),
        "uv_lock_sha256": sha256(ROOT / "uv.lock"),
        "table_sha256": sha256(PROCESSED / "classifier_table.parquet"),
    }


def checkpoint(name: str, key: dict, compute) -> tuple[dict, dict] | None:
    """A step's predictions, from its checkpoint under data/interim/identification/ if one with the same
    key exists, else computed now and saved. Returns (predictions, record of the run that made them)."""
    path = WORK / f"{name}.npz"
    meta = WORK / f"{name}.json"
    if path.exists() and meta.exists():
        record = json.loads(meta.read_text())
        if record["key"] == key:
            with np.load(path) as z:
                return {k: z[k] for k in z.files}, record
    preds = compute()
    WORK.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **preds)
    record = {"key": key, **start_record()}
    meta.write_text(json.dumps(record, indent=2))
    return preds, record


def write(y, places, done: dict[str, dict], records: dict[str, dict], started: dict) -> None:
    """Every output the finished steps allow, and a manifest that names the steps still pending."""
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    first = done["original split"]
    resamples = place_resamples(places)
    intervals(y, first, resamples).to_csv(OUT / "intervals.csv", index=False, float_format="%.4f")
    written.append("intervals.csv")
    seeds = [s for s in SPLIT_SEEDS if f"split {s}" in done]
    if seeds:
        spread = pd.DataFrame(
            [
                {"seed": s, "columns": k, "accuracy": float((done[f"split {s}"][k] == y).mean())}
                for s in seeds
                for k in SETS
            ]
        )
        spread.groupby("columns", sort=False)["accuracy"].agg(
            splits="count", min="min", median="median", max="max"
        ).reset_index().to_csv(OUT / "splits.csv", index=False, float_format="%.4f")
        written.append("splits.csv")
    if "capacity probe" in done:
        at = {ITERATIONS: first, PROBE_ITERATIONS: done["capacity probe"]}
        capacity(y, at, resamples).to_csv(OUT / "capacity.csv", index=False, float_format="%.4f")
        written.append("capacity.csv")
    manifest = {
        "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        **started,
        "amendment": "configs/protocol_amendment_13.yaml",
        "table_sha256": sha256(PROCESSED / "classifier_table.parquet"),
        "resamples": N_BOOT,
        "seed": SEED,
        "steps": {
            name: {"git_commit": r["git_commit"], "git_dirty": r["git_dirty"]}
            for name, r in records.items()
        },
        "pending": [name for name in STEPS if name not in done],
        "outputs": hashes(OUT / f for f in written),
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))


STEPS = ["original split", "capacity probe", *(f"split {s}" for s in SPLIT_SEEDS)]


def main() -> None:
    """Each step is saved when it finishes, and the outputs and manifest are rewritten after it, so a run
    cut off by time leaves what it finished and the next run starts where it stopped."""
    started = start_record()
    full = pd.read_parquet(PROCESSED / "classifier_table.parquet")
    groups, _ = scopes(usable(full), positives_of(full))
    rows = groups[SCOPE].reset_index(drop=True)
    y, places = codes(rows), rows["place_id"].to_numpy()
    key = step_key()
    work = {
        "original split": lambda: {k: predict(rows, c, GroupKFold(4)) for k, c in SETS.items()},
        "capacity probe": lambda: {
            k: predict(rows, SETS[k], GroupKFold(4), max_iter=PROBE_ITERATIONS)
            for k in ("all permitted", "no source markers")
        },
    } | {
        f"split {s}": (
            lambda s=s: {
                k: predict(rows, c, GroupKFold(4, shuffle=True, random_state=s))
                for k, c in SETS.items()
            }
        )
        for s in SPLIT_SEEDS
    }
    done, records = {}, {}
    for name in STEPS:
        done[name], records[name] = checkpoint(name.replace(" ", "_"), key, work[name])
        if name == "original split":
            committed = pd.read_csv(RUNS / "classifier" / "document_identification.csv")
            committed = committed.set_index("columns")
            for k, p in done[name].items():
                acc = round(float((p == y).mean()), 4)
                assert acc == committed.at[k, "accuracy"], k
        write(y, places, done, records, started)
        print(name, flush=True)


if __name__ == "__main__":
    main()
