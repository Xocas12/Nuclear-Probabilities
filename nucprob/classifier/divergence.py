"""Whether the primary fits diverged (configs/protocol_amendment_15.yaml).

    python -m nucprob.classifier.divergence

Refits every bag of the four models on, for each scope: the whole scope, the five spatial-block folds of the
first grid, each leave-one-document-out fit with the left-out towns removed, and the two temporal fits. The bags
are drawn as nucprob.classifier.fit.fit_bagged draws them. Per bag it records, for LightGBM, the training log
loss at each iteration (its minimum and final value) and the largest absolute raw score; for the logistic
models, whether the solver stopped before max_iter, the largest coefficient and the largest decision value.

Each scope is checkpointed under data/interim/divergence/ (git-ignored), keyed by the commit, the table hash and
the code; a rerun on the same key reads it back. Writes runs/classifier/divergence/fits.csv, summary.csv and
manifest.json.
"""

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import datetime as dt
import json
from collections.abc import Iterator

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from lightgbm import LGBMClassifier
from sklearn.metrics import log_loss

from nucprob.classifier import evaluate as ev
from nucprob.classifier.fit import N_BAGS, N_THREADS, Spec, bag_rows, specs
from nucprob.classifier.run import positives_of, scopes, usable
from nucprob.model.splits import BLOCK_KM, assign_blocks, folds
from nucprob.outputs import hashes, start_record
from nucprob.paths import DATA, PROCESSED, RUNS
from nucprob.sources.fetch import sha256

OUT = RUNS / "classifier" / "divergence"
WORK = DATA / "interim" / "divergence"
SEED = 1956  # fit_bagged's default
LOSS_RISE = 0.01
MAX_RAW = 50.0
MAX_ITER = 5000


def bags(spec: Spec, train: pd.DataFrame, n_bags: int = N_BAGS, seed: int = SEED):
    """(model before fitting, row positions) of each bag, drawn exactly as fit_bagged draws them."""
    y = train["listed"].to_numpy(int)
    complete = train["complete"].to_numpy(bool)
    if complete.all():
        return [(spec.factory(), np.arange(len(train)))]
    rng = np.random.default_rng(seed)
    doc, place = train["plan_id"].to_numpy(), train["place_id"].to_numpy()
    draws = [bag_rows(y, doc, complete, place, rng) for _ in range(n_bags)]
    return [(spec.factory(seed=b), rows) for b, rows in enumerate(draws)]


def _final(model):
    return model[-1] if hasattr(model, "steps") else model


def diagnose(model, X: pd.DataFrame, y: np.ndarray) -> tuple[object, dict]:
    """Fit one bag and record the amendment's measures. Returns (fitted model, record)."""
    if isinstance(model, LGBMClassifier):
        model.fit(X, y, eval_X=(X,), eval_y=(y,), eval_metric="binary_logloss")
        curve = np.asarray(next(iter(model.evals_result_.values()))["binary_logloss"])
        raw = float(np.abs(model.predict(X, raw_score=True)).max())
        record = {
            "kind": "lightgbm",
            "loss_min": float(curve.min()),
            "loss_final": float(curve[-1]),
            "loss_argmin": int(curve.argmin()) + 1,
            "max_abs_raw": raw,
            "solver_hit_max_iter": False,
            "max_abs_coef": np.nan,
        }
        record["diverged"] = bool(
            record["loss_final"] - record["loss_min"] > LOSS_RISE or raw > MAX_RAW
        )
        return model, record
    model.fit(X, y)
    lr = _final(model)
    p = model.predict_proba(X)[:, 1]
    raw = float(np.abs(model.decision_function(X)).max())
    hit = bool(np.max(lr.n_iter_) >= lr.max_iter)
    loss = float(log_loss(y, p, labels=[0, 1]))
    record = {
        "kind": "logistic",
        "loss_min": loss,
        "loss_final": loss,
        "loss_argmin": int(np.max(lr.n_iter_)),
        "max_abs_raw": raw,
        "solver_hit_max_iter": hit,
        "max_abs_coef": float(np.abs(lr.coef_).max()),
    }
    record["diverged"] = bool(hit or raw > MAX_RAW)
    return model, record


def fit_all(spec: Spec, train: pd.DataFrame, n_bags: int = N_BAGS) -> tuple[list, list[dict]]:
    """Every bag of one fit: the fitted models (as fit_bagged would hold them) and their records."""
    y = train["listed"].to_numpy(int)
    X = train[spec.columns]

    def one(model, rows):
        return diagnose(model, X.iloc[rows], y[rows])

    done = Parallel(n_jobs=N_THREADS, prefer="threads")(
        delayed(one)(m, r) for m, r in bags(spec, train, n_bags)
    )
    return [m for m, _ in done], [r | {"bag": b} for b, (_, r) in enumerate(done)]


def trainings(rows: pd.DataFrame) -> Iterator[tuple[str, str, pd.DataFrame]]:
    """(holdout kind, fit, training rows) of the amendment's fits, as nucprob.classifier.evaluate makes them."""
    yield "whole scope", "all rows", rows
    lat, lon = rows["lat"].to_numpy(float), rows["lon"].to_numpy(float)
    offset = ev.GRID_OFFSETS[0]
    blocks = pd.Series(assign_blocks(lat, lon, BLOCK_KM, offset), index=rows.index)
    fold = folds(blocks, rows["listed"], ev.N_FOLDS, seed=int(offset))
    for f in range(ev.N_FOLDS):
        yield "spatial blocks, first grid", f"fold {f}", rows[fold != f]
    for group in sorted(rows["group"].unique()):
        test = rows["group"] == group
        held = rows[test]
        train = rows[~test]
        train = train[~train["place_id"].isin(held["place_id"])].reset_index(drop=True)
        if train["listed"].sum() == 0 or held["listed"].sum() == 0:
            continue
        yield "leave one document out", str(group), train
    early = rows["year"] <= ev.TEMPORAL_CUT
    for name, train, test in (
        ("fit up to cut", rows[early], rows[~early]),
        ("fit after cut", rows[~early], rows[early]),
    ):
        if train["listed"].sum() == 0 or test.empty:
            continue
        yield "temporal", name, train.reset_index(drop=True)


def scope_records(name: str, rows: pd.DataFrame, n_bags: int = N_BAGS) -> pd.DataFrame:
    out = []
    for holdout, label, train in trainings(rows):
        for spec in specs():
            _, records = fit_all(spec, train, n_bags)
            out += [
                {"scope": name, "holdout": holdout, "fit": label, "model": spec.name} | r
                for r in records
            ]
        print(f"  {holdout}: {label}", flush=True)
    return pd.DataFrame(out)


def summarise(fits: pd.DataFrame) -> pd.DataFrame:
    fits = fits.assign(loss_rise=fits["loss_final"] - fits["loss_min"])
    return (
        fits.groupby(["scope", "holdout", "model"], sort=False)
        .agg(
            fits=("diverged", "size"),
            diverged=("diverged", "sum"),
            solver_hit_max_iter=("solver_hit_max_iter", "sum"),
            largest_abs_raw=("max_abs_raw", "max"),
            largest_loss_rise=("loss_rise", "max"),
        )
        .reset_index()
    )


def _slug(name: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in name)[:60]


def main() -> None:
    started = start_record()
    table_path = PROCESSED / "classifier_table.parquet"
    full = pd.read_parquet(table_path)
    groups, _ = scopes(usable(full), positives_of(full))
    key = {
        "git_commit": started["git_commit"],
        "git_dirty": started["git_dirty"],
        "table_sha256": sha256(table_path),
        "code_sha256": sha256(__file__),
    }
    WORK.mkdir(parents=True, exist_ok=True)
    parts = []
    for name, rows in groups.items():
        path, meta = WORK / f"{_slug(name)}.csv", WORK / f"{_slug(name)}.json"
        if (
            path.exists()
            and meta.exists()
            and json.loads(meta.read_text()) == key
            and not key["git_dirty"]
        ):
            parts.append(pd.read_csv(path))
            print(f"--- {name}: from checkpoint", flush=True)
            continue
        print(f"--- {name}: {len(rows)} rows", flush=True)
        part = scope_records(name, rows)
        part.to_csv(path, index=False)
        meta.write_text(json.dumps(key, indent=2))
        parts.append(part)
    fits = pd.concat(parts, ignore_index=True)
    OUT.mkdir(parents=True, exist_ok=True)
    fits.to_csv(OUT / "fits.csv", index=False, float_format="%.6g")
    summarise(fits).to_csv(OUT / "summary.csv", index=False, float_format="%.6g")
    written = ["fits.csv", "summary.csv"]
    manifest = {
        "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        **started,
        "amendment": "configs/protocol_amendment_15.yaml",
        "table_sha256": key["table_sha256"],
        "bags": N_BAGS,
        "seed": SEED,
        "loss_rise": LOSS_RISE,
        "max_abs_raw": MAX_RAW,
        "outputs": hashes(OUT / f for f in written),
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
