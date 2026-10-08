import pandas as pd

from nucprob.features.industry import Matcher
from nucprob.gazetteer.lookup import loose
from nucprob.sources.vpk import active, branches, parse_location


def test_loose_keys_meet_across_conventions():
    assert loose("Gor'kii") == loose("Горький") == loose("Gorkiy")
    assert loose("Zaporozh'e") == loose("Запорожье")
    assert loose("Ul'yanovsk") == loose("Ульяновск")
    assert loose("Rīga") == loose("Riga")


def test_parse_location():
    loc = parse_location("Kaliningrad (Podlipki), now Korolev, Moscow obl.")
    assert (loc.town, loc.districts, loc.also, loc.region) == (
        "Kaliningrad",
        ["Podlipki"],
        ["Korolev"],
        "Moscow",
    )
    loc = parse_location("Khar'kov, Ukraine")
    assert (loc.town, loc.republic) == ("Khar'kov", "ukraine")
    loc = parse_location("Omsk (Kolomzino or Kulomzino)")
    assert (loc.town, loc.districts) == ("Omsk", ["Kolomzino", "Kulomzino"])
    loc = parse_location("Tomsk-7, former Chekist, now Seversk, Tomsk obl.")
    assert loc.closed and loc.also == ["Chekist", "Seversk"]
    assert parse_location("USSR") is None
    assert parse_location("Dresden, Germany").country == "East Germany"


def test_branches_and_activity():
    assert branches("ELEC for AERO") == {"ELEC", "AERO"}
    assert branches("ARMS and MUNS") == {"ARMS", "MUNS"}
    df = pd.DataFrame(
        {
            "start": [1941, 1958, 1939, 1944],
            "finish": [1991, 1991, 1941, 1945],
            "start2": [None, None, 1946, None],
            "finish2": [None, None, 1960, None],
        }
    )
    assert active(df, 1956).tolist() == [True, False, True, False]


def places() -> pd.DataFrame:
    rows = [
        # name_ru, name_1956, unit, lat, lon, pop
        ("Калининград", "Калининград", "russia", 54.71, 20.51, 203_570),
        ("Королёв", "Калининград", "russia", 55.92, 37.82, 41_427),
        ("Москва", "Москва", "russia", 55.75, 37.62, 5_045_905),
        ("Тушино", "Тушино", "russia", 55.83, 37.43, 89_885),
        ("Горкі", "Горкі", "belarus", 54.29, 30.99, 15_099),
        ("Нижний Новгород", "Горький", "russia", 56.33, 44.0, 941_962),
        ("Челябинск", "Челябинск", "russia", 55.15, 61.43, 688_945),
    ]
    df = pd.DataFrame(rows, columns=["name_ru", "name_1956", "unit_1956", "lat", "lon", "pop"])
    df["country_1956"] = "USSR"
    df["gn_alternatenames"] = ["", "", "Moscow,Moskva", "", "", "", ""]
    df["place_id"] = [f"su-{i}" for i in range(len(df))]
    return df


def test_matcher_resolves_homonyms_districts_and_code_names():
    m = Matcher(places())
    name = lambda loc: m.places.at[m.match(parse_location(loc))[0], "name_ru"]  # noqa: E731
    assert name("Kaliningrad (Podlipki), now Korolev, Moscow obl.") == "Королёв"
    assert name("Kaliningrad") == "Калининград"
    assert name("Kaliningrad, Moscow obl.") == "Королёв"
    assert name("Gor'kii, now Nizhnii Novgorod") == "Нижний Новгород"
    assert name("Gor'kii") == "Нижний Новгород"  # the RSFSR first when no republic is named
    assert name("Moscow (Tushino)") == "Тушино"
    assert name("Moscow (Lefortovo)") == "Москва"
    assert m.match(parse_location("Chelyabinsk 40, later Chelyabinsk 65, Ozersk"))[0] is None
