"""The held-out set of the 1956 bloc is frozen and independent of the labels."""

import pandas as pd

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
