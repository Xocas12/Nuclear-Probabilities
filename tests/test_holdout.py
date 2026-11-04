"""The held-out set of the 1956 bloc is frozen and independent of the labels."""

import pandas as pd
import pytest

from nucprob.dataset import SPLITS, held_out
from nucprob.labels.sac1956 import NAME_LINK, name_score, simple


def towns() -> pd.DataFrame:
    read = pd.read_csv(SPLITS / "scored_before_freeze.csv")
    m2 = read[read["run"].eq("m2-check")].iloc[0]
    m1 = read[
        read["run"].eq("m1-slice")
        & ~read["place_id"].isin(read.loc[read["run"].eq("m2-check"), "place_id"])
    ].iloc[0]
    block = pd.read_csv(SPLITS / "sealed_blocks.csv")["block"].iloc[0]
    return pd.DataFrame(
        {
            "place_id": [m2["place_id"], "xx-renamed", m1["place_id"], "xx-new", "xx-outside"],
            "name_1956": ["a", m2["name_1956"], "b", "c", "d"],
            "country_1956": ["A", m2["country_1956"], "A", "A", "A"],
            "block": [block, block, block, block, "no_such_block"],
        }
    )


def test_a_place_a_check_run_cross_validated_is_never_sealed():
    out = held_out(towns())
    assert out["sealed"].tolist() == [False, False, True, True, False]


def test_never_scored_excludes_what_the_m1_slice_scored():
    assert held_out(towns())["never_scored"].tolist() == [False, False, False, True, False]


def test_the_labels_play_no_part():
    # held_out takes no label column; adding one cannot change the answer
    t = towns()
    a = held_out(t)["sealed"].tolist()
    b = held_out(t.assign(listed=[1, 1, 1, 1, 1]))["sealed"].tolist()
    assert a == b


def test_name_links_need_a_close_name():
    # The two links the threshold was raised for, scored as the labels score them.
    assert name_score("FALKENBURG E GER", [simple("Eilenburg")]) < NAME_LINK
    assert name_score("LANY CZECH", [simple("Slany")]) < NAME_LINK
    assert name_score("INTA", [simple("Inta")]) >= NAME_LINK


def test_the_history_scan_reads_scores_from_csv_and_from_maps_with_a_score():
    import importlib.util

    from nucprob.paths import ROOT

    spec = importlib.util.spec_from_file_location("sh", ROOT / "scripts" / "scored_history.py")
    sh = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sh)
    csv = b"place_id,name_1956,lat\nsu-1,A,1\n"
    assert sh.scored_in("runs/x/oof_predictions.csv", csv).values.tolist() == [
        ["su-1", "A", "USSR"]
    ]
    html = (
        b'[{"id":"cs-1","name":"B","country":"Czechoslovakia","p":{"listed":[0.1]}},'
        b'{"id":"cs-2","name":"C","country":"Czechoslovakia","p":null}]'
    )
    assert sh.scored_in("runs/x/map.html", html)["place_id"].tolist() == ["cs-1"]


def test_the_places_scored_in_history_are_sealed_ones_the_scan_found():
    """scored_in_history.csv is the scan's output: every place in it was scored by a committed run
    before the sealed scoring, and 123 of them are among the 273 never_scored places."""
    from nucprob.paths import PROCESSED

    h = pd.read_csv(SPLITS / "scored_in_history.csv")
    assert set(h["path"]) <= {
        "runs/m1-slice/oof_predictions.csv",
        "runs/m2-check/oof_predictions.csv",
        "runs/m2-check/map.html",
    }
    path = PROCESSED / "dataset_sac1956.parquet"
    if not path.exists():
        pytest.skip("data/processed/dataset_sac1956.parquet is not built (make dataset)")
    d = pd.read_parquet(path, columns=["place_id", "sealed", "never_scored"])
    assert set(h["place_id"]) <= set(d.loc[d["sealed"], "place_id"])
    ns = set(d.loc[d["never_scored"], "place_id"])
    assert len(ns & set(h["place_id"])) == 123 and len(ns - set(h["place_id"])) == 150
