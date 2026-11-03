"""Intervals for the document identification check (configs/protocol_amendment_13.yaml).

    python -m nucprob.classifier.identification

The sixth amendment's check asks how often a classifier names a row's document from its columns, with folds
grouped by place, against always naming the largest document. This module recomputes that check, stops if it
differs from runs/classifier/document_identification.csv, and adds what the thirteenth amendment fixed:
- a place-clustered bootstrap of each set's out-of-fold predictions (accuracy, accuracy minus the largest
  document's share, accuracy minus "all permitted");
- the accuracy spread over 10 further place-grouped splits;
- a capacity probe: the same at 300 boosting iterations instead of 60.

Writes runs/classifier/identification/intervals.csv, splits.csv, capacity.csv and manifest.json.
"""

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "3")

import datetime as dt
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold, cross_val_predict

from nucprob.classifier.features import DEFENCE, MILITARY, NMC_FEATURES
from nucprob.classifier.fit import ALL_FEATURES
from nucprob.classifier.run import positives_of, scopes, usable
from nucprob.classifier.sensitivity import without
from nucprob.outputs import hashes, start_record
from nucprob.paths import PROCESSED, RUNS
from nucprob.sources.fetch import sha256

OUT = RUNS / "classifier" / "identification"
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


def main() -> None:
    started = start_record()
    full = pd.read_parquet(PROCESSED / "classifier_table.parquet")
    groups, _ = scopes(usable(full), positives_of(full))
    rows = groups[SCOPE].reset_index(drop=True)
    y = codes(rows)
    preds = {name: predict(rows, cols, GroupKFold(4)) for name, cols in SETS.items()}

    committed = pd.read_csv(RUNS / "classifier" / "document_identification.csv").set_index(
        "columns"
    )
    for name, p in preds.items():
        assert round(float((p == y).mean()), 4) == committed.at[name, "accuracy"], name
    print("reproduces document_identification.csv", flush=True)

    resamples = place_resamples(rows["place_id"].to_numpy())
    OUT.mkdir(parents=True, exist_ok=True)
    intervals(y, preds, resamples).to_csv(OUT / "intervals.csv", index=False, float_format="%.4f")

    spread = []
    for seed in SPLIT_SEEDS:
        cv = GroupKFold(4, shuffle=True, random_state=seed)
        for name, cols in SETS.items():
            acc = float((predict(rows, cols, cv) == y).mean())
            spread.append({"seed": seed, "columns": name, "accuracy": acc})
        print("split", seed, flush=True)
    spread = pd.DataFrame(spread)
    summary = (
        spread.groupby("columns", sort=False)["accuracy"]
        .agg(splits="count", min="min", median="median", max="max")
        .reset_index()
    )
    summary.to_csv(OUT / "splits.csv", index=False, float_format="%.4f")

    probe = {
        n: preds
        if n == ITERATIONS
        else {
            k: predict(rows, SETS[k], GroupKFold(4), max_iter=n)
            for k in ("all permitted", "no source markers")
        }
        for n in (ITERATIONS, PROBE_ITERATIONS)
    }
    capacity(y, probe, resamples).to_csv(OUT / "capacity.csv", index=False, float_format="%.4f")

    written = ["intervals.csv", "splits.csv", "capacity.csv"]
    manifest = {
        "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        **started,
        "amendment": "configs/protocol_amendment_13.yaml",
        "table_sha256": sha256(PROCESSED / "classifier_table.parquet"),
        "resamples": N_BOOT,
        "seed": SEED,
        "outputs": hashes(OUT / f for f in written),
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
