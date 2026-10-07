import pandas as pd

from nucprob.geo import Points, haversine_km
from nucprob.labels.sac1956 import link, name_score, place_names


def places() -> pd.DataFrame:
    # A city and its suburb 3 km apart; the SAC point sits closer to the suburb.
    return pd.DataFrame(
        {
            "place_id": ["city", "suburb", "village"],
            "name_1956": ["Горловка", "Кондратьевский", "Затон"],
            "name_ru": ["Горлівка", "Кіндратівський", "Затон"],
            "notes": ["", "", ""],
            "gn_name": ["Horlivka", "Kindrativskyi", "Zaton"],
            "gn_alternatenames": ["Gorlovka,Горловка", "", ""],
            "lat": [48.300, 48.327, 50.000],
            "lon": [38.050, 38.050, 40.000],
        }
    )


def test_haversine():
    assert abs(haversine_km(55.75, 37.62, 59.94, 30.31) - 634) < 3  # Moscow - Leningrad


def test_name_score_reads_alternate_names():
    assert name_score("GORLOVKA", place_names(places().iloc[0])) == 100


def test_link_prefers_the_named_place_over_the_nearest():
    p = places()
    targets = pd.DataFrame(
        {"name": ["GORLOVKA", "SOMEPLACE"], "lat": [48.326, 48.326], "lon": [38.05, 38.05]}
    )
    out = link(targets, p, Points(p["lat"], p["lon"]), radius_km=10)
    assert list(out["place_id"]) == ["city", "suburb"]  # named match wins; else the nearest


def test_link_leaves_far_targets_unlinked():
    p = places()
    targets = pd.DataFrame({"name": ["NOWHERE"], "lat": [45.0], "lon": [30.0]})
    out = link(targets, p, Points(p["lat"], p["lon"]), radius_km=10)
    assert out["place_id"].iloc[0] is None
