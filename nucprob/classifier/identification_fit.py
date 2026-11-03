"""Whether the document identification classifier diverged, and the check read again with it regularised
(configs/protocol_amendment_14.yaml, post hoc).

    python -m nucprob.classifier.identification_fit

For each column set of the identification check and each fold of its place-grouped split, the classifier as run
(l2_regularization 0) and with l2_regularization 1.0: largest absolute raw score on training rows, best and
final training accuracy over the boosting iterations, held-out accuracy. Then the four sets' out-of-fold
predictions at 1.0 with the thirteenth amendment's place bootstrap.

Writes runs/classifier/identification/divergence.csv, regularised.csv and fit_manifest.json.
"""

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "3")

import datetime as dt
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import GroupKFold

from nucprob.classifier import identification as ident
from nucprob.classifier.run import positives_of, scopes, usable
from nucprob.outputs import hashes, start_record
from nucprob.paths import PROCESSED
from nucprob.sources.fetch import sha256

L2 = (0.0, 1.0)
REGULARISED = 1.0
DIVERGED_DROP = 0.05


def fit_fold(X: pd.DataFrame, y: np.ndarray, train: np.ndarray, test: np.ndarray, l2: float):
    m = HistGradientBoostingClassifier(
        max_iter=ident.ITERATIONS, max_depth=4, random_state=0, l2_regularization=l2
    ).fit(X.iloc[train], y[train])
    staged = [float((p == y[train]).mean()) for p in m.staged_predict(X.iloc[train])]
    held = m.predict(X.iloc[test])
    record = {
        "max_abs_raw_score": float(np.abs(m.decision_function(X.iloc[train])).max()),
        "train_accuracy_best": max(staged),
        "train_accuracy_final": staged[-1],
        "test_accuracy": float((held == y[test]).mean()),
    }
    record["diverged"] = (
        record["train_accuracy_best"] - record["train_accuracy_final"] > DIVERGED_DROP
    )
    return record, held


def main() -> None:
    started = start_record()
    full = pd.read_parquet(PROCESSED / "classifier_table.parquet")
    groups, _ = scopes(usable(full), positives_of(full))
    rows = groups[ident.SCOPE].reset_index(drop=True)
    y, places = ident.codes(rows), rows["place_id"].to_numpy()
    split = list(GroupKFold(4).split(rows, y, places))
    records, regularised = [], {}
    for name, columns in ident.SETS.items():
        X = rows[columns]
        oof = np.full(len(y), -1)
        for fold, (train, test) in enumerate(split):
            for l2 in L2:
                record, held = fit_fold(X, y, train, test, l2)
                records.append({"columns": name, "fold": fold, "l2_regularization": l2} | record)
                if l2 == REGULARISED:
                    oof[test] = held
        assert (oof >= 0).all()
        regularised[name] = oof
        print(name, flush=True)
    out = ident.OUT
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_csv(out / "divergence.csv", index=False, float_format="%.4f")
    resamples = ident.place_resamples(places)
    ident.intervals(y, regularised, resamples).to_csv(
        out / "regularised.csv", index=False, float_format="%.4f"
    )
    written = ["divergence.csv", "regularised.csv"]
    manifest = {
        "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        **started,
        "amendment": "configs/protocol_amendment_14.yaml",
        "table_sha256": sha256(PROCESSED / "classifier_table.parquet"),
        "l2_regularization": REGULARISED,
        "resamples": ident.N_BOOT,
        "seed": ident.SEED,
        "outputs": hashes(out / f for f in written),
    }
    (out / "fit_manifest.json").write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
