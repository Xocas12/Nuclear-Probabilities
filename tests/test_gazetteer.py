import numpy as np
import pandas as pd

from nucprob.gazetteer.match import match
from nucprob.gazetteer.names import key, latin_key, name_on, variants


def test_name_on_1956():
    assert name_on("Пермь", "до 1940 Пермь, 1940-1957 Молотов", 1956) == "Молотов"
    assert (
        name_on("Донецк", "до 1924 Юзовка, 1924-1929 Сталин, 1929-1961 Сталино", 1956) == "Сталино"
    )
    assert name_on("Донецк", "город с 1951, до 1955 Гундоровка", 1956) == "Донецк"
    assert name_on("Тольятти", "до 1964 Ставрополь", 1956) == "Ставрополь"
    assert name_on("Москва", "", 1956) == "Москва"


def test_keys_fold_other_alphabets():
    assert key("Янги-Юль") == key("Янгиюль")
    assert key("Леңгір") == key("Ленгир")
    assert key("Орёл") == key("Орел")
    assert latin_key("Kalinkavičy") == "kalinkavicy"


def test_variants_include_parentheses_and_former_names():
    assert variants("Дніпро (Дніпропетровськ)") == ["Дніпро", "Дніпропетровськ"]
    assert variants("Пермь", "до 1940 Пермь, 1940-1957 Молотов") == ["Пермь", "Молотов"]


def gazetteer() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "geonameid": [1, 2, 3, 4],
            "name": ["Gorodok", "Gorodok", "Perm", "Dnipro"],
            "asciiname": ["Gorodok", "Gorodok", "Perm", "Dnipro"],
            "alternatenames": ["Городок", "Городок", "Пермь,Молотов", "Днепр,Дніпропетровськ"],
            "lat": [55.0, 49.8, 58.0, 48.45],
            "lon": [30.0, 23.6, 56.2, 34.98],
            "feature_code": ["PPL", "PPL", "PPLA", "PPLA"],
            "country": ["UA"] * 4,
            "admin1": ["A", "B", "C", "D"],
            "population": [5000, 30000, 1_000_000, 900_000],
        }
    )


def test_match_disambiguates_by_population_and_reads_parentheses():
    settlements = pd.DataFrame(
        {
            "name_ru": ["Городок", "Пермь", "Дніпро (Дніпропетровськ)"],
            "notes": ["", "", ""],
            "region": ["X", "Y", "Z"],
            "modern_pop": [28000.0, 1_000_000.0, np.nan],
        }
    )
    out = match(settlements, gazetteer())
    assert list(out["geonameid"]) == [2, 3, 4]  # the Gorodok of ~30k, not the village
    assert out.loc[0, "match_method"] == "exact, ranked"
    assert out.loc[1, "match_method"] == "exact, unique"


def test_verkh_neyvinsky_is_not_put_on_novouralsk():
    """GeoNames carries Верх-Нейвинский only as an alternate name of Novouralsk (Sverdlovsk-44),
    so the matcher puts the 1959 village on the closed town's coordinates; the curated link
    moves it to its own place, where SAC's VERKHNE NEYVINSKIY header is."""
    from nucprob.geo import haversine_km
    from nucprob.places import apply_links

    gn = pd.DataFrame(
        {
            "geonameid": [1538636, 1487504],
            "name": ["Novoural’sk", "Verkh-Neyvinskiy"],
            "alternatenames": ["Novoural'sk,Sverdlovsk-44,Верх-Нейвинский,Новоуральск", ""],
            "lat": [57.25483, 57.27013],
            "lon": [60.09052, 60.13762],
            "admin1": ["71", "71"],
            "feature_code": ["PPLA2", "PPL"],
            "population": [93849, 5156],
            "dem": [270, 260],
        }
    )
    matched = pd.DataFrame(
        {
            "name_ru": ["Верх-Нейвинский"],
            "geonameid": [1538636.0],
            "lat": [57.25483],
            "lon": [60.09052],
            "admin1": ["71"],
            "feature_code": ["PPLA2"],
            "gn_name": ["Novoural’sk"],
            "gn_population": [93849],
            "gn_alternatenames": [gn.at[0, "alternatenames"]],
            "gn_dem": [270],
            "match_method": ["exact, unique"],
        }
    )
    out = apply_links(matched, gn, "russia")
    assert out.at[0, "geonameid"] == 1487504
    assert out.at[0, "match_method"] == "curated link"
    header = (57.2667, 60.15)  # VERKHNE NEYVINSKIY, C120-L19
    assert haversine_km(*header, out.at[0, "lat"], out.at[0, "lon"]) < 1
