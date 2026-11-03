"""List the sealed places that any run committed a model score for before the sealed set was scored.

    uv run python scripts/scored_history.py

scripts/freeze_seal.py read what earlier runs had scored from one commit, de2e54a. The M2 check had
been run and committed three times before that (b094d1d, e599d9c, e80681b, all 8 October), on a
place table that has changed since, and those versions scored places that de2e54a's version did
not. This walks every commit before LOCKED (the commit the sealed scoring ran at), reads every
runs/**/oof_predictions.csv and every map under runs/ that carries a score ("p" not null), and
writes data/curated/splits/scored_in_history.csv: place_id, path, first and last commit, for each
sealed place of data/processed/dataset_sac1956.parquet that one of them scored. A place is matched by id and, as in
nucprob.dataset.held_out, by 1956 name and country, since a corrected match changes the id. No label
and no sealed score is read.
"""

import io
import re
import subprocess

import pandas as pd

from nucprob.paths import CURATED, PROCESSED, ROOT

LOCKED = "6258036"
OUT = CURATED / "splits" / "scored_in_history.csv"
SCORED_PLACE = re.compile(
    r'\{"id":"([a-z]{2,3}-\d+)","name":"((?:[^"\\]|\\.)*)"[^{}]*?"country":"([^"]*)"[^{}]*?"p":\{'
)


def git(*args: str) -> bytes:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, check=True).stdout


def scored_in(path: str, data: bytes) -> pd.DataFrame:
    """Rows (place_id, name_1956, country_1956) that a committed run output gives a score."""
    if path.endswith("oof_predictions.csv"):
        d = pd.read_csv(io.BytesIO(data))
        if "place_id" not in d:
            return pd.DataFrame(columns=["place_id", "name_1956", "country_1956"])
        d = d if "country_1956" in d else d.assign(country_1956="USSR")
        return d[["place_id", "name_1956", "country_1956"]]
    if path.endswith(".html"):
        text = data.decode("utf-8", "replace")
        rows = [(m.group(1), m.group(2), m.group(3)) for m in SCORED_PLACE.finditer(text)]
        return pd.DataFrame(rows, columns=["place_id", "name_1956", "country_1956"])
    return pd.DataFrame(columns=["place_id", "name_1956", "country_1956"])


def history(sealed: pd.DataFrame) -> pd.DataFrame:
    ids = set(sealed["place_id"])
    by_name = {
        (c, n): p
        for p, n, c in sealed[["place_id", "name_1956", "country_1956"]].itertuples(index=False)
    }
    commits = git("rev-list", "--reverse", f"{LOCKED}~1").decode().split()
    blobs: dict[str, set[str]] = {}
    hits: dict[tuple[str, str], list[str]] = {}
    for c in commits:
        for line in git("ls-tree", "-r", c, "--", "runs/").decode().splitlines():
            meta, path = line.split("\t", 1)
            if not (path.endswith("oof_predictions.csv") or path.endswith(".html")):
                continue
            blob = meta.split()[2]
            if blob not in blobs:
                d = scored_in(path, git("cat-file", "blob", blob))
                found = set(d["place_id"]) & ids
                found |= {
                    by_name[k]
                    for k in zip(d["country_1956"], d["name_1956"], strict=True)
                    if k in by_name
                }
                blobs[blob] = found
            for p in blobs[blob]:
                hits.setdefault((p, path), []).append(c[:7])
    rows = [
        {"place_id": p, "path": path, "first_commit": cs[0], "last_commit": cs[-1]}
        for (p, path), cs in hits.items()
    ]
    return pd.DataFrame(rows, columns=["place_id", "path", "first_commit", "last_commit"])


def main() -> None:
    t = pd.read_parquet(PROCESSED / "dataset_sac1956.parquet")
    sealed = t[t["sealed"].astype(bool)]
    h = history(sealed).sort_values(["place_id", "path"])
    h.to_csv(OUT, index=False)
    ns = set(sealed.loc[sealed["never_scored"].astype(bool), "place_id"])
    print(
        f"{h['place_id'].nunique()} sealed places scored in history, "
        f"{len(set(h['place_id']) & ns)} of them never_scored ({len(ns)})"
    )


if __name__ == "__main__":
    main()
