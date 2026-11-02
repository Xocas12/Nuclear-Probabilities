"""The transfer town tables: every table marks the seats of its first-order units (#11)."""

import shutil
from pathlib import Path

import pandas as pd
import pytest
from rapidfuzz import fuzz

from nucprob.transfer import places
from nucprob.transfer.features import administrative
from nucprob.transfer.labels import main_town
from nucprob.transfer.regions import REGIONS

FIXTURES = Path(__file__).parent / "fixtures"
SEATS_1961 = {
    "Wien",
    "Klagenfurt am Wörthersee",
    "Linz",
    "Salzburg",
    "Graz",
    "Innsbruck",
    "Bregenz",
}


@pytest.fixture
def popstat_raw(tmp_path, monkeypatch):
    """The real pop-stat pages when they are downloaded, else the Austria sample page."""
    if not (places.RAW / "popstat" / "austria-cities.htm").exists():
        (tmp_path / "popstat").mkdir()
        shutil.copy(
            FIXTURES / "popstat_austria_sample.htm", tmp_path / "popstat" / "austria-cities.htm"
        )
        monkeypatch.setattr(places, "RAW", tmp_path)


def table_specs() -> list[tuple[str, str]]:
    out = []
    for region in REGIONS.values():
        for country, _, spec in region.countries:
            out.append((country, spec))
    return out


@pytest.mark.parametrize(("country", "spec"), table_specs())
def test_every_transfer_town_table_marks_its_seats(country, spec, popstat_raw):
    if not spec.startswith("popstat:") and not (places.GAZ / f"{spec}.csv").exists():
        pytest.skip(f"{spec} missing")
    towns = places.load_table(spec)
    seats = pd.to_numeric(towns["admin1_seat"], errors="coerce").fillna(0)
    assert seats.sum() > 0, f"{country} ({spec}): admin1_seat is 0 for every row"


def test_austria_land_seats_are_those_of_1961(popstat_raw):
    towns = places.load_table("popstat:austria:pop_1961-03-21")
    seats = set(towns.loc[towns["admin1_seat"] == 1, "name"])
    assert seats == SEATS_1961
    # The page underlines today's seats; neither was a Land seat in 1961.
    assert not towns.loc[towns["name"].isin(["St. Pölten", "Dornbirn"]), "admin1_seat"].any()
    # Eisenstadt is a seat but under 10,000, so it is not in the universe at all.
    assert "Eisenstadt" not in set(towns["name"])


def test_austria_land_capitals_are_regional_centres(popstat_raw):
    towns = places.load_table("popstat:austria:pop_1961-03-21").reset_index(drop=True)
    towns["country"] = "Austria"
    towns["lat"] = towns["lon"] = 0.0
    towns["capital"] = towns["capital"].astype(int)
    feats = administrative(towns)
    centre = dict(zip(towns["name"], feats["regional_centre"], strict=True))
    for town in SEATS_1961:
        assert centre[town] == 1, town
    assert centre["Villach"] == 0 and centre["Leoben"] == 0


def test_popstat_seats_fail_loudly():
    d = pd.DataFrame(
        {"region": ["Tirol", "Südtirol"], "name_ru": ["Innsbruck", "Bozen"]},
    )
    with pytest.raises(ValueError, match="no seat given"):
        places.popstat_seats(d, "austria")
    with pytest.raises(ValueError, match="no first-order seats"):
        places.popstat_seats(d, "nowhere")
    seats = dict.fromkeys(places.POPSTAT_SEATS["austria"].values())
    renamed = pd.DataFrame(
        {"region": "Steiermark", "name_ru": [t.replace("Graz", "Graz-Stadt") for t in seats]}
    )
    with pytest.raises(ValueError, match="'Graz', found 0 times"):
        places.popstat_seats(renamed, "austria")


def test_the_frg_table_is_the_whole_printed_table():
    # VZ 1961 Vorbericht 3, Table 1 (p. 6): 582 towns outside Berlin, 29,720.5 thousand people.
    t = pd.read_csv(places.GAZ / "towns_frg_1961.csv", keep_default_na=False)
    assert len(t) == 583
    assert t["name"].is_unique or t["name"].duplicated().sum() == 1  # two Friedbergs
    outside = t[t["admin1"] != "Berlin"]
    assert len(outside) == 582
    assert abs(outside["pop"].sum() - 29_720_500) < 100
    # Printed in descending order of population, Bonn the capital, 11 Land seats.
    assert (t["pop"].diff() > 0).sum() == 1  # the volume prints Saarbrücken out of order
    assert t["capital"].sum() == 1 and t.loc[t["capital"].eq(1), "name"].item() == "Bonn"
    assert t["admin1_seat"].sum() == 11
    assert t["pop"].min() >= 10_000


def test_the_frg_is_in_the_universe_of_the_western_european_lists():
    countries = {c for c, _, _ in REGIONS["wp_west_1965"].countries}
    assert "FRG" in countries


# Review finding 12: a town whose coordinates come from a GeoNames entry in another first-order
# unit is a different town of a similar name.


def located_places() -> pd.DataFrame:
    path = places.PROCESSED / "transfer_places.parquet"
    if not path.exists():
        pytest.skip("data/processed/transfer_places.parquet not built")
    t = pd.read_parquet(path)
    return t[t["lat"].notna()]


def test_no_two_towns_of_a_region_share_a_point_across_first_order_units():
    # A UK row is a district at its council's seat, and a few seats lay outside the district
    # (uk_districts_1981_seats.md); those are the only points meant to be shared across units.
    t = located_places()
    t = t[t["match_method"] != "district seat"]
    n = t.groupby(["region", "lat", "lon"])["admin1"].transform("nunique")
    clash = t.loc[n > 1, ["region", "name", "admin1", "lat", "lon"]]
    assert clash.empty, clash.to_string()


def test_a_matched_towns_geonames_unit_agrees_with_its_table_unit():
    t = located_places()
    t = t[t["match_method"].isin(["name", "fuzzy"]) & (t["admin1"] != "")]
    wrong = []
    for country, g in t.groupby("country"):
        units = places.admin1_crosswalk(country)
        for row in g.itertuples():
            if row.gn_admin1 not in units[row.admin1][0]:
                wrong.append((country, row.name, row.admin1, row.gn_name, row.gn_admin1))
    assert not wrong, wrong


def test_towns_on_one_point_of_a_unit_are_one_place_by_name():
    # The same point in the same unit is fine only for a town and its own rural municipality,
    # or for parts of one town today. Unrelated names on one point are a false match.
    t = located_places()
    t = t[t["match_method"] != "district seat"]
    n = t.groupby(["region", "lat", "lon"])["name"].transform("size")
    alien = []
    for row in t[n > 1].itertuples():
        own = places.key(row.name)
        today = places.key(row.name_today)
        gn = places.key(row.gn_name)
        if max(fuzz.partial_ratio(own, gn), fuzz.partial_ratio(today, gn) if today else 0) < 85:
            alien.append((row.region, row.name, row.admin1, row.gn_name))
    assert not alien, alien


@pytest.mark.parametrize(("country", "spec"), table_specs())
def test_the_crosswalk_covers_every_table_unit(country, spec, popstat_raw):
    if not spec.startswith("popstat:") and not (places.GAZ / f"{spec}.csv").exists():
        pytest.skip(f"{spec} missing")
    units = places.admin1_crosswalk(country)
    towns = places.load_table(spec)
    # The build leaves out the US table's territories (the universe is the 48 states and DC).
    notes = towns.get("notes", pd.Series("", index=towns.index)).astype(str)
    towns = towns[~notes.str.contains("Territory, outside", case=False)]
    table = set(towns["admin1"].astype(str)) - {""}
    assert table <= set(units), sorted(table - set(units))


@pytest.fixture
def toy_gazetteer(monkeypatch):
    g = pd.DataFrame(
        [
            ("Milan", "Milan", "Mirano,Milano", "PPLA", "09", "MI", 1_300_000, 45.46, 9.19),
            ("Mirano", "Mirano", "", "PPLA3", "20", "VE", 26_000, 45.49, 12.11),
            ("Munich", "Munich", "Monaco", "PPLA", "02", "M", 1_200_000, 48.14, 11.58),
            ("Monaco", "Monaco", "", "PPL", "02", "X", 0, 48.70, 13.46),
            ("Bari", "Bari", "", "PPLA", "13", "BA", 320_000, 41.12, 16.87),
        ],
        columns=[
            "name",
            "asciiname",
            "alternatenames",
            "feature_code",
            "admin1",
            "admin2",
            "population",
            "lat",
            "lon",
        ],
    )
    monkeypatch.setattr(places.geonames, "load_country", lambda code: g)
    units = {
        "Venezia": ({"20"}, {"VE"}),
        "Milano": ({"09"}, {"MI"}),
        "Monaco": ({"02"}, set()),
        "Bari": ({"13"}, {"BA"}),
    }
    return places.Gazetteer("XX", units)


def test_a_town_is_matched_only_in_its_own_unit(toy_gazetteer):
    gaz = toy_gazetteer
    i, _ = gaz.find("Mirano", admin1="Venezia", pop=18_000)
    assert gaz.g.at[i, "name"] == "Mirano"
    assert gaz.find("Mirano", admin1="Bari", pop=18_000) == (None, "not found")
    with pytest.raises(ValueError, match="admin1_crosswalk"):
        gaz.find("Mirano", admin1="Atlantis")


def test_a_hamlet_of_the_same_name_does_not_beat_the_city(toy_gazetteer):
    gaz = toy_gazetteer
    i, _ = gaz.find("Monaco", admin1="Monaco", pop=1_000_000)
    assert gaz.g.at[i, "name"] == "Munich"


def test_a_target_on_a_shared_point_links_to_the_town_not_its_rural_municipality():
    towns = pd.DataFrame(
        {"name": ["Ibbenbüren, Land", "Ibbenbüren", "Zwolle"], "pop": [20_098, 15_676, 55_805]}
    )
    assert main_town(towns.iloc[:2])["name"] == "Ibbenbüren"
    assert main_town(towns)["name"] == "Zwolle"
