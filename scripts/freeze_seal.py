"""Freeze the held-out set of the 1956 bloc, once, from what earlier runs actually scored.

    python scripts/freeze_seal.py

The sealed blocks used to be drawn from the labels (nucprob.model.splits.seal), so correcting a
label could move a block that a check run had already read into the sealed set. And the M1 slice,
drawn before the other countries existed, scored 207 USSR towns that M2 then sealed. This reads
the scored places from the last commit before the freeze and writes:

  data/curated/splits/scored_before_freeze.csv  place_id, name_1956, country_1956, run: every place
                                                an earlier run scored (a corrected match changes
                                                the id, so the name is kept too)
  data/curated/splits/sealed_blocks.csv         blocks with a place today and no M2-scored place

No label is read. Run after `make places`; the output is committed and not regenerated.
"""

import io
import subprocess

import pandas as pd

from nucprob.model.splits import assign_blocks
from nucprob.paths import CURATED, PROCESSED

BEFORE = "de2e54a"
RUNS = {
    "m1-slice": "runs/m1-slice/oof_predictions.csv",
    "m2-check": "runs/m2-check/oof_predictions.csv",
}
OUT = CURATED / "splits"


def scored(path: str) -> pd.DataFrame:
    text = subprocess.check_output(["git", "show", f"{BEFORE}:{path}"], text=True)
    return pd.read_csv(io.StringIO(text))


def keep(d: pd.DataFrame) -> pd.DataFrame:
    d = d if "country_1956" in d else d.assign(country_1956="USSR")
    return d[["place_id", "name_1956", "country_1956"]]


def main() -> None:
    m2 = scored(RUNS["m2-check"])
    read = pd.concat(
        [scored(path).pipe(keep).assign(run=run) for run, path in RUNS.items()],
        ignore_index=True,
    )
    read.sort_values(["place_id", "run"]).to_csv(OUT / "scored_before_freeze.csv", index=False)
    read_blocks = set(assign_blocks(m2["lat"].to_numpy(), m2["lon"].to_numpy()))
    places = pd.read_parquet(PROCESSED / "places_1956.parquet")
    places = places[places["in_universe"] & places["has_coords"]]
    blocks = set(assign_blocks(places["lat"].to_numpy(), places["lon"].to_numpy()))
    sealed = sorted(blocks - read_blocks)
    pd.DataFrame({"block": sealed}).to_csv(OUT / "sealed_blocks.csv", index=False)
    print(f"{len(read)} scored rows; {len(sealed)} sealed blocks of {len(blocks)}")


if __name__ == "__main__":
    main()
