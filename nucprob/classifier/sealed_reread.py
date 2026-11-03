"""Read the committed sealed scores on the blind places (configs/protocol_amendment_12.yaml).

    python -m nucprob.classifier.sealed_reread

The sealed set was scored once (nucprob.classifier.sealed, lock at runs/classifier/sealed/LOCK.json).
123 of its 273 never_scored places had been scored by M2 check runs committed on 8 October 2026
(data/curated/splits/scored_in_history.csv, from scripts/scored_history.py), so the eleventh
amendment's primary population was not blind. This fits nothing and scores nothing: it reads
runs/classifier/sealed/scores.csv.gz, refuses unless the file is the one committed at fb028cc, and
applies the eleventh amendment's reading to three populations, blind first: blind (never_scored and
in no committed run's scores), never_scored and all sealed. It writes runs/classifier/sealed/blind/
metrics.csv, comparison.csv and manifest.json (commit, input and output hashes). A comparison whose positives lie in fewer than 5 blocks of 300 km has
no block interval that measures anything (ninth amendment), so it calls no gain or loss.
"""

import datetime as dt
import json

import numpy as np
import pandas as pd

from nucprob.classifier.report import MIN_POSITIVE_BLOCKS
from nucprob.classifier.run import SAC
from nucprob.classifier.sealed import OUT, read
from nucprob.dataset import SPLITS
from nucprob.outputs import hashes, start_record
from nucprob.paths import PROCESSED
from nucprob.sources.fetch import sha256

BLIND = OUT / "blind"
# runs/classifier/sealed/scores.csv.gz as committed at fb028cc, the one scoring of the sealed set.
SCORES_SHA256 = "66580f073b0cf36f29ece7cca335be0037c46d3bd87462991a595cebc9eed3b1"


class NotTheCommittedScores(RuntimeError):
    pass


def sealed_rows(full: pd.DataFrame, scores: pd.DataFrame) -> pd.DataFrame:
    """The table's SAC rows of sealed places, in the order the scores were written."""
    sealed = full[full["sealed"].astype(bool) & full["plan_id"].eq(SAC)].reset_index(drop=True)
    if sealed["place_id"].tolist() != scores["place_id"].tolist():
        raise NotTheCommittedScores("the table's sealed rows are not the rows that were scored")
    if not (sealed["never_scored"].astype(bool) == scores["never_scored"].astype(bool)).all():
        raise NotTheCommittedScores("never_scored differs between the table and the scores")
    return sealed


def populations(sealed: pd.DataFrame, history: pd.DataFrame) -> dict[str, np.ndarray]:
    never = sealed["never_scored"].astype(bool).to_numpy()
    seen = sealed["place_id"].isin(set(history["place_id"])).to_numpy()
    return {
        "blind": never & ~seen,
        "never_scored": never,
        "all sealed": np.ones(len(sealed), bool),
    }


def measured(comp: pd.DataFrame) -> pd.DataFrame:
    """The ninth amendment's rule: too few positive blocks and the block interval is not read."""
    ok = comp["positive_blocks"] >= MIN_POSITIVE_BLOCKS
    comp = comp.assign(block_measured=ok)
    comp.loc[~ok, "verdict"] = "neither"
    return comp


def main() -> None:
    record = start_record()
    path = OUT / "scores.csv.gz"
    if sha256(path) != SCORES_SHA256:
        raise NotTheCommittedScores(f"{path} is not the file committed at fb028cc")
    scores = pd.read_csv(path)
    full = pd.read_parquet(PROCESSED / "classifier_table.parquet")
    sealed = sealed_rows(full, scores)
    sel = pd.read_csv(OUT.parent / "selection.csv")
    selected = dict(sel.loc[sel["selected"], ["scope", "model"]].to_numpy())
    cols = {tuple(c.split(" | ", 1)): scores[c].to_numpy() for c in scores.columns if " | " in c}
    history = pd.read_csv(SPLITS / "scored_in_history.csv")
    met, comp = read(sealed, cols, selected, populations=populations(sealed, history))
    comp = measured(comp)
    BLIND.mkdir(parents=True, exist_ok=True)
    met.to_csv(BLIND / "metrics.csv", index=False, float_format="%.4f")
    comp.to_csv(BLIND / "comparison.csv", index=False, float_format="%.4f")
    inputs = [path, PROCESSED / "classifier_table.parquet", OUT.parent / "selection.csv"]
    inputs.append(SPLITS / "scored_in_history.csv")
    manifest = {
        "created": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
        **record,
        "amendment": "configs/protocol_amendment_12.yaml",
        "inputs": hashes(inputs),
        "outputs": hashes([BLIND / "metrics.csv", BLIND / "comparison.csv"]),
    }
    (BLIND / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    show = ["scope", "population", "against", "rows", "positives", "positive_blocks", "delta"]
    print(comp[[*show, "low", "high", "block_low", "block_high", "verdict"]].round(3).to_string())


if __name__ == "__main__":
    main()
