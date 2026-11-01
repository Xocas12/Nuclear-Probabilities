"""Score the sealed places once (configs/protocol.yaml, evaluation.holdouts.sealed).

    python -m nucprob.classifier.sealed

Fits the scope's models on every non-sealed row and scores the sealed bloc places on the SAC list:
the `never_scored` places first, since only they are blind, and the whole sealed set beside them.
Writes runs/classifier/sealed/ and a lock file holding the time, the git commit and the protocol's
hash. With the lock present it refuses to run: a sealed set read twice is not sealed.
"""

import datetime as dt
import json
from pathlib import Path

import pandas as pd

from nucprob.classifier.fit import N_BAGS, fit_bagged, specs
from nucprob.classifier.run import SAC, scopes, usable
from nucprob.model.cv import git_commit
from nucprob.model.evaluate import metrics
from nucprob.paths import PROCESSED, ROOT, RUNS
from nucprob.sources.fetch import sha256

OUT = RUNS / "classifier" / "sealed"


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


def main() -> None:
    claim(
        OUT / "LOCK.json",
        {
            "scored": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
            "git_commit": git_commit(),
            "protocol_sha256": sha256(ROOT / "configs" / "protocol.yaml"),
        },
    )
    full = pd.read_parquet(PROCESSED / "classifier_table.parquet")
    table = usable(full)
    groups, _ = scopes(table)
    sealed = full[full["sealed"].astype(bool) & full["plan_id"].eq(SAC)].reset_index(drop=True)
    rows = []
    for scope, train in groups.items():
        for m in specs():
            s = fit_bagged(m, train, N_BAGS).score(sealed)
            for label, keep in (
                ("never_scored", sealed["never_scored"].astype(bool)),
                ("all sealed", pd.Series(True, index=sealed.index)),
            ):
                rows.append(
                    {"scope": scope, "model": m.name, "population": label}
                    | metrics(sealed.loc[keep, "listed"], s[keep.to_numpy()])
                )
    pd.DataFrame(rows).to_csv(OUT / "metrics.csv", index=False, float_format="%.4f")
    print(pd.DataFrame(rows).round(3).to_string(index=False))
    print("scored once; lock at", OUT / "LOCK.json")


if __name__ == "__main__":
    main()
