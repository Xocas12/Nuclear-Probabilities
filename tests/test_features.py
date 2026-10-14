import json

import numpy as np
import pandas as pd
import pytest
from PIL import Image

from nucprob.features.administrative import capitals
from nucprob.features.geography import sac_bases
from nucprob.features.population import population
from nucprob.geo import densify, haversine_km
from nucprob.paths import RAW
from nucprob.sources import cshapes, terrain


def test_densify_keeps_vertices_and_spacing():
    lon, lat = densify([0.0, 0.0, 1.0], [0.0, 1.0, 1.0], spacing_km=10)
    gaps = haversine_km(lat[:-1], lon[:-1], lat[1:], lon[1:])
    assert gaps.max() <= 10.0 + 1e-9
    assert (lon[0], lat[0]) == (0.0, 0.0) and (lon[-1], lat[-1]) == (1.0, 1.0)
    assert any((x, y) == (0.0, 1.0) for x, y in zip(lon, lat, strict=True))


def test_densify_does_not_sweep_across_the_antimeridian():
    lon, _ = densify([179.9, -179.9], [65.0, 65.0], spacing_km=1)
    assert len(lon) == 2


def test_terrain_pixel_maths():
    x, y = terrain.to_pixel(0.0, 0.0, 7)
    assert (float(x), float(y)) == (16384.0, 16384.0)
    assert terrain.radius_px(0.0, 10.0, 7) == pytest.approx(10_000 / (156543.034 / 128), rel=1e-6)


def test_terrarium_decoding(tmp_path):
    rgb = np.zeros((256, 256, 3), dtype=np.uint8)
    rgb[...] = (128, 0, 0)  # 0 m
    rgb[0, 0] = (128, 100, 128)  # 100.5 m
    rgb[0, 1] = (127, 156, 0)  # -100 m
    path = tmp_path / "t.png"
    Image.fromarray(rgb).save(path)
    elev = terrain.decode(path)
    assert elev[1, 1] == 0 and elev[0, 0] == 100.5 and elev[0, 1] == -100


def test_cshapes_units_on_picks_the_unit_valid_on_the_date(tmp_path):
    square = [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]

    def unit(name, start, end):
        return {
            "type": "Feature",
            "properties": {
                "cntry_name": name,
                "capname": "C",
                "caplat": 0.5,
                "caplong": 0.5,
                **dict(zip(["gwsyear", "gwsmonth", "gwsday"], start, strict=True)),
                **dict(zip(["gweyear", "gwemonth", "gweday"], end, strict=True)),
            },
            "geometry": {"type": "Polygon", "coordinates": square},
        }

    path = tmp_path / "c.geojson"
    features = [unit("Old", (1946, 1, 1), (1955, 5, 4)), unit("New", (1955, 5, 5), (1990, 10, 2))]
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    units = cshapes.units_on((1956, 6, 15), path)
    assert list(units) == ["New"]
    lat, lon = cshapes.boundary(units, ["New"], spacing_km=20)
    assert len(lat) > 5 and lat.min() == 0 and lon.max() == 1


def test_population_features_rank_within_country_and_skip_self():
    places = pd.DataFrame(
        {
            "lat": [50.0, 50.1, 51.0, 40.0],
            "lon": [30.0, 30.0, 30.0, 20.0],
            "pop": [200_000, 20_000, 150_000, 50_000],
            "pop_year": 1959,
            "pop_prewar": [100_000, np.nan, 150_000, 50_000],
            "pop_prewar_year": 1939,
            "country_1956": ["USSR", "USSR", "USSR", "Bulgaria"],
        }
    )
    f = population(places)
    assert f["pop_rank_pct"].tolist() == [1.0, 1 / 3, 2 / 3, 1.0]
    assert f["pop_prewar_missing"].tolist() == [0, 1, 0, 0]
    assert f["growth_prewar"].iloc[0] == pytest.approx(np.log10(2) / 20)
    km = 10 ** f["log_km_to_100k"] - 1
    # the first place's nearest other 100k+ town is the third, ~111 km away, not itself
    assert km.iloc[0] == pytest.approx(111.2, abs=1)
    assert km.iloc[1] == pytest.approx(11.1, abs=0.5)


def test_sac_bases_in_1956():
    bases = sac_bases(1956)
    assert len(bases) >= 10
    assert bases["lat"].between(-90, 90).all() and bases["lon"].between(-180, 180).all()
    # SAC's Spanish bases (Torrejón, Zaragoza, Morón) opened 1957-59 (PLAN section 3.2).
    assert not bases["country"].str.contains("Spain").any()


@pytest.mark.skipif(
    not (RAW / "cshapes" / "CShapes-2.0.geojson").exists(), reason="CShapes not downloaded"
)
def test_national_capitals_agree_with_cshapes():
    from nucprob.bloc import COUNTRIES

    units = cshapes.units_on()
    caps = capitals()
    for _, row in caps[caps["level"] == "national"].iterrows():
        unit = units[COUNTRIES[row["country_1956"]].cshapes]
        assert haversine_km(row["lat"], row["lon"], unit["cap_lat"], unit["cap_lon"]) < 10


def test_admin_centres_table():
    from nucprob.bloc import COUNTRIES
    from nucprob.features.administrative import admin_centres

    a = admin_centres()
    assert a["unit"].is_unique
    assert set(a["country_1956"]) <= set(COUNTRIES)
    assert (a["centre"] != "").all() and (a["centre_today"] != "").all()
    ussr = a[a["country_1956"] == "USSR"]
    assert (ussr["republic"] != "").all()
    # oblasts of 1954-57 are in; the Izmail oblast (abolished 1954) is not
    assert {"Арзамасская область", "Каменская область"} <= set(ussr["unit"])
    assert "Измаильская область" not in set(ussr["unit"])


def test_centre_positions_prefer_the_largest_namesake_of_the_republic():
    from nucprob.features.administrative import centre_positions

    places = pd.DataFrame(
        {
            "name_ru": ["Киров", "Киров", "Kirovabad"],
            "name_1956": ["Киров", "Киров", "Kirovabad"],
            "republic": ["russia", "russia", "azerbaijan"],
            "country_1956": "USSR",
            "pop": [16_647, 252_416, 116_000],
        }
    )
    centres = pd.DataFrame(
        {
            "country_1956": ["USSR"],
            "republic": ["russia"],
            "unit": ["Кировская область"],
            "level": ["oblast"],
            "centre": ["Киров"],
            "centre_today": ["Киров"],
        }
    )
    assert centre_positions(places, centres) == {"Кировская область": 1}


def test_military_sites_in_june_1956():
    from nucprob.features.military import military_sites

    sites = military_sites()
    assert len(sites) >= 100
    assert set(sites["category"]) >= {"military_district_hq", "fleet_hq", "lra_base", "naval_base"}
    assert "Tauride Military District HQ" not in set(sites["site"])  # disbanded spring 1956
    assert sites["lat"].between(-90, 90).all() and sites["source"].str.len().gt(0).all()
    # SAC's own lists are never a source of this table (leakage guard)
    assert not sites["source"].str.contains("ebb538|nukevault|nuclearsecrecy", case=False).any()


def test_district_seat_is_read_at_each_countrys_district_tier():
    """#10: GeoNames' admin2 is a different tier in each country. East German Kreis seats are
    PPLA3 (admin2 is the Regierungsbezirk, absent in the east), so Wismar and Weimar must count;
    a Chinese prefecture seat (PPLA2) must not; Romania's PPLA2 is the commune and the Czech lands
    have almost no coded okres seats, so the feature is missing there."""
    from nucprob.features.administrative import administrative

    # feature codes as GeoNames gives them: Wismar 2807465, Weimar 2812482, Halle 2911522
    places = pd.DataFrame(
        {
            "name_ru": ["Wismar", "Weimar", "Halle", "Тверь", "Кимры", "Baoding", "Xushui", "Cluj"],
            "country_1956": ["East Germany"] * 3 + ["USSR"] * 2 + ["China"] * 2 + ["Romania"],
            "country_today": ["DE", "DE", "DE", "RU", "RU", "CN", "CN", "RO"],
            "feature_code": ["PPLA3", "PPLA3", "PPL", "PPLA", "PPLA2", "PPLA2", "PPLA3", "PPLA2"],
            "lat": [53.89, 50.98, 51.48, 56.86, 56.87, 38.87, 39.02, 46.77],
            "lon": [11.47, 11.33, 11.97, 35.90, 37.36, 115.48, 115.66, 23.60],
            "pop": [30_000, 64_000, 290_000, 240_000, 40_000, 200_000, 30_000, 155_000],
            "is_city": True,
        }
    )
    places["name_1956"] = places["name_ru"]
    seat = administrative(places)["district_seat"]
    assert seat.iloc[:3].tolist() == [1, 1, 0]  # Wismar, Weimar (Kreis seats); Halle
    assert seat.iloc[3:7].tolist() == [0, 1, 0, 1]  # oblast centre, raion; prefecture, county
    assert seat.iloc[7:].isna().all()  # Romania: GeoNames has no district tier


def test_district_seat_note_names_every_country_off_the_default():
    from nucprob.features.administrative import DISTRICT_CODE
    from nucprob.features.registry import FEATURES

    f = FEATURES["district_seat"]
    assert "PPLA2 (" not in f.source and "PPLA3" in f.note
    names = {"DE": "Germany", "CN": "China", "MD": "Moldova", "AZ": "Azerbaijan"}
    names |= {"LV": "Latvia", "EE": "Estonia", "CZ": "Czech", "RO": "Romania"}
    names |= {"TM": "Turkmenistan", "KP": "North Korea"}
    assert set(names) == set(DISTRICT_CODE)
    assert all(n in f.note for n in names.values())
