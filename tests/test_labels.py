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


def test_cover_names_are_a_or_e_plants_and_ranges_by_a_closed_town():
    """Each cover-name entry is printed under an open town, carries an A/E (040-048) or
    guided-missile (210) line, and its header or one of its DGZs lies within 10 km of the
    closed town it is credited to."""
    from nucprob.labels.sac1956 import COVER_NAMES
    from nucprob.paths import CURATED

    cover = pd.read_csv(COVER_NAMES, dtype=str)
    assert dict(zip(cover["name_printed"], cover["closed_town"], strict=True)) == {
        "KYSHTYM": "Ozersk",
        "VERKHNE NEYVINSKIY": "Novouralsk",
        "KAPUSTIN YAR": "Znamensk",
    }
    cx = pd.read_csv(CURATED / "sac1956" / "complexes.csv", dtype=str).set_index("id")
    inst = pd.read_csv(CURATED / "sac1956" / "installations.csv", dtype=str)
    dgz = pd.read_csv(CURATED / "sac1956" / "dgz.csv")
    closed = pd.read_csv(CURATED / "gazetteer" / "closed_cities_1956.csv").set_index("name")
    for _, c in cover.iterrows():
        assert cx.at[c["sac_id"], "name_printed"] == c["name_printed"]
        cats = set(inst.loc[inst["complex_id"] == c["sac_id"], "category"].astype(int))
        assert cats & ({*range(40, 49)} | {210}), c["sac_id"]
        assert c["closed_place_id"] == "su-closed-" + c["closed_town"].lower()
        town = closed.loc[c["closed_town"]]
        pts = dgz.loc[dgz["complex_id"] == c["sac_id"], ["lat", "lon"]].to_numpy().tolist()
        pts.append([float(cx.at[c["sac_id"], "lat"]), float(cx.at[c["sac_id"], "lon"])])
        near = min(haversine_km(lat, lon, town["lat"], town["lon"]) for lat, lon in pts)
        assert near < 10, (c["sac_id"], near)


def test_cover_name_entries_are_credited_to_the_closed_town_too():
    from nucprob.labels.sac1956 import cover_links

    places = pd.DataFrame(
        {
            "place_id": ["su-1500997", "su-closed-ozersk", "su-552999", "su-1487504"],
            "lat": [55.7163, 55.7556, 48.58, 57.2701],
            "lon": [60.551, 60.7028, 45.72, 60.1376],
        }
    )
    links_cx = pd.DataFrame(
        {
            "id": ["C140-L36", "C120-L19", "C109-L28"],
            "top_id": ["C140-L36", "C120-L12", "C109-L28"],
            "level": ["complex", "subcomplex", "complex"],
            "name_printed": ["KYSHTYM", "VERKHNE NEYVINSKIY", "KAPUSTIN YAR"],
            "n_dgz": [2, 1, 3],
            "lat": [55.7333, 57.2667, 48.5667],
            "lon": [60.5667, 60.15, 45.7833],
            "place_id": ["su-1500997", "su-1487504", "su-552999"],
            "link_method": "coordinates",
        }
    )
    # Novouralsk and Znamensk are left out of `places`: only towns present get a copy.
    out = cover_links(links_cx, places)
    assert list(out["id"]) == ["C140-L36"]
    assert out["place_id"].iat[0] == "su-closed-ozersk"
    assert out["link_method"].iat[0] == "cover name"
    assert out["n_dgz"].iat[0] == 2  # the entry's DGZs come with it: has_dgz
    assert abs(out["dist_km"].iat[0] - 8.9) < 0.2
    assert list(links_cx["place_id"]) == ["su-1500997", "su-1487504", "su-552999"]  # kept


def test_closed_towns_are_listed_through_their_cover_names(tmp_path, monkeypatch):
    """The whole label build on six towns: the three closed towns get the entries SAC printed
    under their neighbours, which keep them too."""
    import nucprob.labels.sac1956 as sac

    rows = [
        ("su-1500997", "Кыштым", "Kyshtym", 55.7163, 60.551, 34302),
        ("su-closed-ozersk", "Озёрск", "", 55.7556, 60.7028, 50000),
        ("su-1487504", "Верх-Нейвинский", "Verkh-Neyvinskiy", 57.2701, 60.1376, 8229),
        ("su-closed-novouralsk", "Новоуральск", "", 57.2548, 60.0905, 40000),
        ("su-552999", "Капустин Яр", "Kapustin Yar", 48.5818, 45.7448, 14199),
        ("su-closed-znamensk", "Знаменск", "", 48.5842, 45.7338, 13500),
    ]
    places = pd.DataFrame(rows, columns=["place_id", "name_ru", "gn_name", "lat", "lon", "pop"])
    places = places.assign(
        name_1956=places["name_ru"],
        notes="",
        gn_alternatenames="",
        country_1956="USSR",
        has_coords=True,
    )
    places.to_parquet(tmp_path / "places_1956.parquet", index=False)
    monkeypatch.setattr(sac, "PROCESSED", tmp_path)
    links, labels, _ = sac.build()
    lab = labels.set_index("place_id")
    for town in ["su-closed-ozersk", "su-closed-novouralsk", "su-closed-znamensk"]:
        assert lab.at[town, "listed"] and lab.at[town, "has_dgz"], town
    for town in ["su-1500997", "su-1487504", "su-552999"]:
        assert lab.at[town, "listed"] and lab.at[town, "has_dgz"], town
    assert lab.at["su-closed-ozersk", "best_priority"] == 41
    assert lab.at["su-closed-ozersk", "sac_names"] == "KYSHTYM"
    assert lab.at["su-closed-novouralsk", "parent_priority"] == 56
    cover = links[links["link_method"] == "cover name"]
    assert sorted(cover["id"]) == ["C109-L28", "C120-L19", "C140-L36"]
