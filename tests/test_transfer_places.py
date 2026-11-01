"""The transfer town tables: every table marks the seats of its first-order units (#11)."""

import shutil
from pathlib import Path

import pandas as pd
import pytest

from nucprob.transfer import places
from nucprob.transfer.features import administrative
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
        for country, _, spec in (*region.countries, *region.withheld):
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
