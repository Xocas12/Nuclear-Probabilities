"""What a list's rows mean as labels, on small fixtures: designated, rejected, neither; sectors."""

import numpy as np
import pandas as pd
import pytest
import yaml

from nucprob.classifier import table as tb
from nucprob.geo import Points
from nucprob.paths import CURATED, PROCESSED, ROOT
from nucprob.plans import plans
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
    # Square Leg's corrected links (Crawley, Dundee City) went with Great Britain's table (tenth amendment).
    assert not links["plan_id"].eq("cd_1980_square_leg").any()
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


def test_no_row_is_designated_when_its_own_notes_say_the_weapon_is_not_stated():
    """The rule of the sixth amendment, on every list, in the wordings the notes use."""
    says = (
        r"(?i)weapon type[^.;|]{0,40}not stated|not stated[^.;]{0,40}weapon type"
        r"|does not say this (?:task|target)[^.;]{0,20}nuclear"
    )
    seen = 0
    for path in LABELS.glob("*.csv"):
        d = pd.read_csv(path, dtype=str, keep_default_na=False)
        if not {"notes", "selected"} <= set(d.columns):
            continue
        rows = d[d["notes"].str.contains(says)]
        seen += len(rows)
        assert (rows["selected"] == "").all(), path.name
    assert seen >= 14


def test_every_list_with_a_linked_positive_has_a_sector_or_a_stated_reason_for_none():
    data = yaml.safe_load((LABELS / "SECTORS.yaml").read_text(encoding="utf-8"))
    boxed = {s["plan_id"] for s in data["sectors"]}
    whole = set(data["whole_universe"])
    assert not boxed & whole
    assert all(len(reason) > 20 for reason in data["whole_universe"].values())
    reg = plans()
    train = set(reg.loc[reg["role"].eq("train") & reg["attacker"].notna(), "plan_id"])
    table = PROCESSED / "classifier_table.parquet"
    if not table.exists():
        pytest.skip("no built tables")
    t = pd.read_parquet(table, columns=["plan_id", "listed"])
    held = set(t["plan_id"]) & train
    linked = set(t.loc[t["listed"].eq(1), "plan_id"]) & train
    assert linked <= boxed | whole
    assert held - linked - boxed - whole == set()


@needs_tables
def test_a_list_with_a_derived_box_keeps_only_the_towns_inside_it():
    t = pd.read_parquet(PROCESSED / "classifier_table.parquet")
    for plan, boxes in tb.sectors().items():
        g = t[t["plan_id"] == plan]
        if len(g):
            assert tb.in_sector(g, boxes).all(), plan
    assert set(t.loc[t["plan_id"] == "wp_1965_coastal_front_zealand", "lon"].round()) <= set(
        range(10, 14)
    )


@needs_tables
def test_every_sac_entry_passing_a_nearer_negative_town_has_been_read():
    """An entry linked to a place while a town the list leaves negative lies nearer its printed point:
    a new one fails here until it is read. Sealed places are not looked at."""
    links = pd.read_parquet(PROCESSED / "sac1956_links.parquet")
    d = pd.read_parquet(PROCESSED / "dataset_sac1956.parquet")
    towns = pd.read_parquet(PROCESSED / "places_1956.parquet")
    e = links[links["level"].isin(["complex", "subcomplex"]) & links["place_id"].notna()]
    e = e[~e["link_method"].isin(["cover name", "nearer town"])]
    e = e[~e["place_id"].isin(d.loc[d["sealed"].astype(bool), "place_id"])]
    neg = d[(d["listed"] == 0) & ~d["sealed"].astype(bool)]
    dist, _ = Points(neg["lat"].to_numpy(), neg["lon"].to_numpy()).nearest(
        e["lat"].to_numpy(), e["lon"].to_numpy()
    )
    passing = e[np.ravel(dist) < e["dist_km"].to_numpy() - 0.5]
    read = pd.read_csv(CURATED / "sac1956" / "nearer_negatives_reviewed.csv", dtype=str)
    assert set(passing["id"]) <= set(read["sac_id"])
    assert read["reading"].str.len().min() > 15
    moved = pd.read_csv(CURATED / "sac1956" / "nearer_town_links.csv", dtype=str)
    for _, r in moved.iterrows():
        assert links.loc[links["id"] == r["sac_id"], "place_id"].eq(r["place_id"]).all()
        assert d.loc[d["place_id"] == r["place_id"], "listed"].eq(1).all()
        assert not d["place_id"].eq(r["was_place_id"]).any()  # below the floor: labels nothing
        assert towns["place_id"].eq(r["was_place_id"]).any()


def test_every_entry_read_as_moved_is_a_nearer_town_link_and_the_reverse():
    """Undoing the KITOY or ZUYEVKA move by deleting its link row fails here, without built tables."""
    read = pd.read_csv(CURATED / "sac1956" / "nearer_negatives_reviewed.csv", dtype=str)
    links = pd.read_csv(CURATED / "sac1956" / "nearer_town_links.csv", dtype=str)
    moved = read[read["reading"].str.startswith("moved to")]
    assert set(moved["sac_id"]) == set(links["sac_id"])
    for _, r in moved.iterrows():
        town = links.loc[links["sac_id"] == r["sac_id"], "town"].iloc[0]
        assert r["nearer_negative"] == town and r["reading"].startswith(f"moved to {town}:")
    assert {"C277-L17", "C247-L22"} <= set(links["sac_id"])


def test_every_scored_list_rests_on_a_source_with_a_hash_or_a_named_record():
    """Section A of the standard: a list that enters a model or a score has a source on record."""
    sources = yaml.safe_load((ROOT / "data" / "sources.yaml").read_text(encoding="utf-8"))
    sources = sources["sources"] if isinstance(sources, dict) else sources
    by_url = {s.get("url"): s for s in sources}
    by_id = {s.get("id"): s for s in sources}
    # Label files that carry no source_url column, and the sources.yaml record each rests on.
    named = {"cd_1987_napb90_counties": "fema_napb90"}
    reg = plans()
    checked = 0
    for plan in reg.loc[reg["role"].isin(["train", "test-expectation"]), "plan_id"]:
        path = LABELS / f"{plan}.csv"
        if not path.exists():
            continue
        d = pd.read_csv(path, dtype=str, keep_default_na=False)
        if "source_url" in d:
            records = [(url, by_url.get(url)) for url in d["source_url"].unique()]
        else:
            assert plan in named, plan
            records = [(named[plan], by_id.get(named[plan]))]
        for url, s in records:
            assert s is not None, (plan, url)  # every source a list cites is in sources.yaml
            assert s.get("sha256"), (plan, url)
            assert s.get("retrieved") not in (None, "unknown"), (plan, url)
            checked += 1
    assert checked > 20
    canada = reg.set_index("plan_id").loc["cd_1956_canada_target_areas"]
    assert canada["role"] == "excluded" and canada["grade"] == "U"
