"""What a list's rows mean as labels, on small fixtures: designated, rejected, neither; sectors."""

import pandas as pd

from nucprob.classifier import table as tb
from nucprob.transfer import labels as lb


def fixture(monkeypatch, flags):
    towns = pd.DataFrame(
        {
            "place_id": ["a", "b", "c", "d"],
            "country": "X",
            "sealed": False,
        }
    )
    monkeypatch.setattr(lb, "universes", lambda: [("r", {"X": "XX"}, towns, ("L",))])
    monkeypatch.setattr(lb, "selected_of", lambda plan: flags)
    return pd.DataFrame(
        {
            "plan_id": "L",
            "seq": list(flags),
            "target_country": "X",
            "place_id": ["a", "b", "c"][: len(flags)],
        }
    )


def test_only_a_designated_row_makes_a_positive(monkeypatch):
    lab = lb.labels(fixture(monkeypatch, {1: "1", 2: "0", 3: ""})).set_index("place_id")
    assert lab.at["a", "listed"] == 1
    # Rejected: considered, and a negative. Tokyo in 1945 is the case.
    assert lab.at["b", "listed"] == 0 and lab.at["b", "n_rejected"] == 1
    # Neither designated nor rejected: not on the list as a positive or a negative.
    assert "c" not in lab.index
    # Never named: an ordinary town of the list.
    assert lab.at["d", "listed"] == 0


def test_a_town_designated_in_one_row_and_undecided_in_another_is_positive(monkeypatch):
    links = fixture(monkeypatch, {1: "1", 2: ""})
    links["place_id"] = ["a", "a"]
    lab = lb.labels(links).set_index("place_id")
    assert lab.at["a", "listed"] == 1


def test_a_list_with_no_selected_column_designates_every_row(tmp_path, monkeypatch):
    (tmp_path / "L.csv").write_text("seq,name\n1,x\n2,y\n")
    monkeypatch.setattr(lb, "LABELS", tmp_path)
    assert lb.selected_of("L") == {1: "1", 2: "1"}


def test_sector_keeps_towns_inside_and_every_positive():
    t = pd.DataFrame(
        {
            "country": ["FRG", "FRG", "FRG", "Italy", "Italy"],
            "lat": [54.0, 48.0, 48.0, 46.0, 41.0],
            "lon": [10.0, 10.0, 10.0, 11.0, 12.0],
            "listed": [0, 0, 1, 0, 0],
        }
    )
    boxes = [{"country": "FRG", "lat_min": 50}, {"country": "Italy", "lat_min": 44.5}]
    assert tb.in_sector(t, boxes).tolist() == [True, False, True, True, False]
