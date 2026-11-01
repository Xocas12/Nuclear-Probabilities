"""What a list's rows mean as labels, on small fixtures: designated, rejected, neither; sectors."""

import pandas as pd
import pytest

from nucprob.classifier import table as tb
from nucprob.paths import CURATED, PROCESSED
from nucprob.transfer import labels as lb

LABELS = CURATED / "labels"
needs_tables = pytest.mark.skipif(
    not (PROCESSED / "transfer_places.parquet").exists()
    or not (PROCESSED / "dataset_sac1956.parquet").exists(),
    reason="no built tables",
)


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


def test_selected_flags_are_read_from_the_file_not_assumed():
    """Rows a document rejects or does not designate must not read as designated."""
    flags = lb.selected_of("us_1945_target_committee")
    d = pd.read_csv(LABELS / "us_1945_target_committee.csv", dtype=str, keep_default_na=False)
    assert flags == dict(zip(d["seq"].astype(int), d["selected"], strict=True))
    assert {"1", "0", ""} <= set(flags.values())
    assert sum(v == "1" for v in flags.values()) < len(flags)


def test_a_town_old_name_beats_a_modern_name_several_towns_share():
    own = pd.DataFrame(
        {"name": ["Yawata", "Kokura", "Moji"], "name_today": ["Kitakyushu"] * 3, "pop": [3, 2, 1]}
    )
    assert lb.town_hits(own, "Kitakyushu (Kokura)", "Kokura Arsenal")["name"].tolist() == ["Kokura"]
    assert lb.town_hits(own, "", "Moji")["name"].tolist() == ["Moji"]
    assert len(lb.town_hits(own, "Kitakyushu", "")) == 3


def test_a_row_whose_weapon_is_not_stated_is_not_designated():
    d = pd.read_csv(LABELS / "wp_1964_csla_plan.csv", dtype=str, keep_default_na=False)
    open_rows = d[d["notes"].str.contains("Weapon type NOT stated")]
    assert len(open_rows) and (open_rows["selected"] == "").all()


def test_same_place_links_name_entries_that_exist():
    c = pd.read_csv(CURATED / "sac1956" / "complexes.csv", dtype=str)
    d = pd.read_csv(CURATED / "sac1956" / "same_place_links.csv", dtype=str)
    names = c.set_index("id")["name_printed"]
    for _, r in d.iterrows():
        assert names[r["sac_id"]] == r["name_printed"]
        assert r["basis"]


@needs_tables
def test_kokura_is_the_positive_and_stands_at_kokura():
    t = pd.read_parquet(PROCESSED / "transfer_places.parquet")
    k = t[(t["region"] == "japan_1945") & (t["name"] == "Kokura")].iloc[0]
    assert abs(k["lat"] - 33.88) < 0.02 and abs(k["lon"] - 130.88) < 0.02
    lab = pd.read_parquet(PROCESSED / "labels_transfer.parquet")
    lab = lab[lab["plan_id"] == "us_1945_target_committee"].set_index("place_id")
    y = t[(t["region"] == "japan_1945") & (t["name"] == "Yawata")].iloc[0]
    assert lab.loc[k["place_id"], "listed"] == 1
    # Yawata's only row is blank: neither designated nor rejected, so it leaves the list.
    assert y["place_id"] not in lab.index


@needs_tables
def test_corrected_sac_links_hold():
    d = pd.read_parquet(PROCESSED / "dataset_sac1956.parquet").set_index("name_1956")
    assert d.loc["Xinhailian", "listed"] == 1
    assert d.loc["Ulaanbaatar", "listed"] == 1
    assert abs(d.loc["Komárno", "lat"] - 47.76) < 0.02


def test_second_read_rows_are_cited_and_dropped_names_stay_out():
    """Lessons 27a and 24b, read on the scan (data/notes/second_read_2026-11b.md)."""
    d = pd.read_csv(LABELS / "wp_1977_gsa_lessons.csv", dtype=str, keep_default_na=False)
    new = d[d["seq"].astype(int) > 44]
    assert len(new) == 25
    assert (new["quote"] != "").all() and (new["source_page"] != "").all()
    assert not new["name_source"].str.contains("TALBURG|BORGER").any()
    weert = new[new["name_source"] == "WEERT"].iloc[0]
    assert weert["selected"] == "", "p.26 does not say Weert gets a nuclear weapon"
    assert (new.loc[new["name_source"] != "WEERT", "selected"] == "1").all()
    skip = lb.unlinked()
    for name, cls in (("WINTERSLAG", "north of"), ("THE HAGUE", "east of"), ("WEERT", "SW of")):
        row = new[new["name_source"].eq(name) & new["target_class"].str.contains(cls)].iloc[0]
        assert ("wp_1977_gsa_lessons", int(row["seq"])) in skip


@needs_tables
def test_links_the_audit_corrected_hold():
    links = pd.read_csv(PROCESSED / "transfer_links.csv", dtype=str, keep_default_na=False)
    leg = links[links["plan_id"] == "cd_1980_square_leg"].set_index("seq")
    assert leg.at["64", "town"] == "Crawley"
    assert leg.at["82", "town"] == "Dundee City"
    sac = pd.read_parquet(PROCESSED / "sac1956_links.parquet")
    assert sac.loc[sac["id"] == "C086-L07", "place_id"].isna().all()


@needs_tables
def test_every_far_name_link_on_sac_has_been_read():
    """A SAC entry tied to a town by name alone, over 25 km from its printed point, is either in
    the reviewed table or rejected. A new one fails here. Sealed places are not looked at."""
    sac = pd.read_parquet(PROCESSED / "sac1956_links.parquet")
    sealed = pd.read_parquet(PROCESSED / "classifier_table.parquet")
    sealed = set(sealed.loc[sealed["sealed"].astype(bool), "place_id"])
    far = sac[sac["link_method"].eq("name") & (sac["dist_km"] > 25)]
    far = far[~far["place_id"].isin(sealed)]
    read = pd.read_csv(CURATED / "sac1956" / "far_name_links_reviewed.csv", dtype=str)
    assert set(far["id"]) <= set(read["sac_id"])
    assert read["reading"].str.len().min() > 20
