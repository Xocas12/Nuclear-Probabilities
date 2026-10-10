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


def test_part2_labels_known_only_where_the_excerpt_shows_it():
    from nucprob.labels.sac1956 import part2_labels

    links_cx = pd.DataFrame(
        {
            "place_id": ["moscow", "bugulma", "abdulino", "praha", "kladno"],
            "id": ["C166-L18", "C035-L31", "C002-L04", "C209-L41", "C211-L20"],
            "top_id": ["C166-L18", "C035-L31", "C002-L04", "C209-L41", "C209-L41"],
        }
    )
    ids = pd.Index(["moscow", "bugulma", "abdulino", "praha", "kladno", "unlisted"])
    out = part2_labels(links_cx, ids)
    has = out["part2_has_dgz"]
    assert has["moscow"] == 1 and has["praha"] == 1 and has["kladno"] == 1
    assert has["bugulma"] == 0 and out.at["bugulma", "part2_n_dgz"] == 0  # whole, aim point dropped
    assert has["unlisted"] == 0  # Part II lists only Part I complexes
    assert pd.isna(has["abdulino"])  # not in the excerpt
    assert pd.isna(out.at["moscow", "part2_n_dgz"])  # cut by a skipped page: a floor only
