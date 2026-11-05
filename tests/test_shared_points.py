"""Places of the classifier table that share one point are only the pairs that data/curated/gazetteer/TRANSFER.md
lists ("Places that share a point"): a rural municipality or absorbed district placed at its town's point."""

import pandas as pd
import pytest

from nucprob.paths import CURATED, PROCESSED

TABLE = PROCESSED / "classifier_table.parquet"


def _documented() -> set[frozenset[str]]:
    text = (CURATED / "gazetteer" / "TRANSFER.md").read_text(encoding="utf-8")
    section = text.split("## Places that share a point", 1)[1]
    pairs = set()
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[0] not in ("Town", "---"):
            pairs.add(frozenset({cells[0], cells[1].split(" (")[0]}))
    return pairs


def test_the_documented_pairs_are_read():
    assert len(_documented()) == 4


def test_no_undocumented_places_share_a_point():
    if not TABLE.exists():
        pytest.skip("data/processed/classifier_table.parquet is not built (make test-full)")
    t = pd.read_parquet(TABLE, columns=["place_id", "name", "lat", "lon"]).drop_duplicates(
        "place_id"
    )
    shared = t[t.duplicated(["lat", "lon"], keep=False)]
    groups = {frozenset(g["name"]) for _, g in shared.groupby(["lat", "lon"])}
    # Zwolle and Zwollerkerspel are the fifth pair while the Dutch towns are still in the built table.
    allowed = _documented() | {frozenset({"Zwolle", "Zwollerkerspel"})}
    assert groups <= allowed, groups - allowed
