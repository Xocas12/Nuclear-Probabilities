import numpy as np
import pandas as pd

from nucprob.gazetteer.match import choose, match
from nucprob.gazetteer.names import key, latin_key, name_on, variants
from nucprob.places import EAST_GERMAN_LAENDER, population_check
from nucprob.places_bloc import CHINA_ADMIN1, EAST_GERMANY_ADMIN1


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


def namesakes() -> pd.DataFrame:
    """Same-named places in the order a GeoNames dump can list them: the hamlet first."""
    names = ["Dessau", "Dessau", "Anshan", "Anshan", "Suzhou", "Jiuquan", "Suzhou", "Zhangzhou"]
    return pd.DataFrame(
        {
            "geonameid": [11, 12, 21, 22, 31, 32, 33, 41],
            "name": names,
            "asciiname": names,
            "alternatenames": ["", "", "", "", "", "Suzhou", "", ""],
            "lat": [52.81, 51.84, 45.51, 41.12, 31.30, 39.74, 33.64, 24.51],
            "lon": [11.48, 12.25, 128.52, 122.99, 120.60, 98.52, 116.98, 117.65],
            "feature_code": ["PPL", "PPL", "PPLA4", "PPL", "PPLA2", "PPLA2", "PPLA2", "PPLA2"],
            "country": ["XX"] * 8,
            "admin1": ["13", "14", "08", "19", "04", "15", "01", "07"],
            "population": [0, 77_000, 0, 1_500_000, 6_700_000, 428_000, 5_300_000, 500_000],
        }
    )


def bloc_towns(names: list[str], regions: list[str], pops: list[float]) -> pd.DataFrame:
    """Settlements as places_bloc.frame builds them: a 1950s `pop` and no modern figure."""
    n = len(names)
    return pd.DataFrame(
        {
            "name_ru": names,
            "name_lat": names,
            "notes": [""] * n,
            "region": regions,
            "modern_pop": [np.nan] * n,
            "pop": pops,
        }
    )


def test_choose_falls_back_on_the_census_figure_when_modern_pop_is_nan():
    gn = namesakes()
    # Two PPLs tie on rank; without population evidence the first in file order (the hamlet
    # of population 0) would win.
    assert gn.at[choose([0, 1], gn, None, np.nan, 93_927.0), "geonameid"] == 12
    # A PPLA4 of population 0 outranks the PPL that is the real city unless population counts.
    assert gn.at[choose([2, 3], gn, None, np.nan, 548_900.0), "geonameid"] == 22
    # A modern figure, where there is one, still comes first.
    assert gn.at[choose([2, 3], gn, None, 1_400_000.0, 5.0), "geonameid"] == 22


def test_a_1950s_figure_does_not_pull_a_city_down_to_a_suburb_of_its_size():
    gn = pd.DataFrame(
        {
            "geonameid": [1, 2, 3, 4],
            "name": ["Weifang", "Weifang", "Nantong", "Jinsha"],
            "feature_code": ["PPL", "PPL", "PPLA2", "PPLA3"],
            "admin1": ["25", "25", "04", "04"],
            "population": [0, 9_386_705, 2_273_326, 95_647],
        }
    )
    # Weifang (148,900 in 1953) is 63 times that today; Nantong's county seat (Jinsha) is
    # nearer 1953's 260,400 than the city is. Both cities still win.
    assert gn.at[choose([0, 1], gn, "25", np.nan, 148_900.0), "geonameid"] == 2
    assert gn.at[choose([2, 3], gn, "04", np.nan, 260_400.0), "geonameid"] == 3
    # The same gaps against a modern figure keep their full weight.
    assert gn.at[choose([2, 3], gn, "04", 95_000.0), "geonameid"] == 4


def test_match_uses_pop_for_bloc_towns_without_a_modern_figure():
    out = match(
        bloc_towns(["Dessau", "Anshan"], ["Halle", "Municipality of Anshan"], [93_927, 548_900]),
        namesakes(),
    )
    assert list(out["geonameid"]) == [12, 22]
    assert list(out["gn_population"]) == [77_000, 1_500_000]


def test_match_keeps_chinese_cities_to_their_province():
    towns = bloc_towns(["Suzhou", "Zhangzhou"], ["Jiangsu", "Shandong"], [474_000, 50_000])
    out = match(towns, namesakes(), admin1_of=CHINA_ADMIN1)
    # Jiuquan (Gansu, alternate name Suzhou) is closer in population on a log scale, and the
    # Suzhou of Anhui is a PPLA2 too: only the one in Jiangsu is a candidate.
    assert out.at[0, "geonameid"] == 31
    assert out.at[0, "n_candidates"] == 1
    # The only Zhangzhou is in Fujian: left unmatched rather than put there.
    assert pd.isna(out.at[1, "geonameid"])
    assert out.at[1, "match_method"].startswith("unmatched")
    # Without the province map, population alone puts Suzhou on Jiuquan.
    assert match(towns.iloc[:1], namesakes()).at[0, "geonameid"] == 32


def test_match_lets_a_bezirk_span_the_laender_it_was_divided_between():
    # Bezirk Leipzig's unambiguous towns are Saxon, so the inferred region map sends the whole
    # Bezirk to Saxony (13), whose Meuselwitz is a hamlet; Meuselwitz itself (Kreis Altenburg)
    # has been in Thuringia (15) since 1990.
    gn = pd.DataFrame(
        {
            "geonameid": [1, 2, 3, 4],
            "name": ["Leipzig", "Wurzen", "Meuselwitz", "Meuselwitz"],
            "asciiname": ["Leipzig", "Wurzen", "Meuselwitz", "Meuselwitz"],
            "alternatenames": [""] * 4,
            "lat": [51.34, 51.37, 51.17, 51.04],
            "lon": [12.37, 12.74, 14.75, 12.30],
            "feature_code": ["PPLA2", "PPL", "PPL", "PPL"],
            "country": ["DE"] * 4,
            "admin1": ["13", "13", "13", "15"],
            "population": [600_000, 16_000, 0, 10_148],
        }
    )
    towns = bloc_towns(
        ["Leipzig", "Wurzen", "Meuselwitz"], ["Leipzig"] * 3, [620_000, 23_000, 10_820]
    )
    assert match(towns, gn).at[2, "geonameid"] == 3
    out = match(towns, gn, admin1_of=EAST_GERMANY_ADMIN1)
    assert list(out["geonameid"]) == [1, 2, 4]
    assert out.at[2, "match_method"] == "exact, region"


def test_region_maps_use_geonames_codes():
    # GeoNames admin1 codes of China (admin1CodesASCII.txt): 01-16, 18-26, 28-33.
    codes = {f"{i:02d}" for i in range(1, 34)} - {"17", "27"}
    assert all(c in codes for cs in CHINA_ADMIN1.values() for c in cs)
    assert {"Liaodong", "Liaoxi", "Rehe", "Songjiang", "Suiyuan", "Xikang"} <= set(CHINA_ADMIN1)
    assert all(c in EAST_GERMAN_LAENDER for cs in EAST_GERMANY_ADMIN1.values() for c in cs)
    assert len(EAST_GERMANY_ADMIN1) == 15  # the 14 Bezirke and East Berlin


def test_population_check_lists_matches_to_a_place_of_no_or_few_people():
    places = pd.DataFrame(
        {
            "place_id": ["dd-1", "dd-2", "cn-3", "cn-4", "su-x5"],
            "country_1956": ["East Germany", "East Germany", "China", "China", "USSR"],
            "republic": ["east germany", "east germany", "china", "china", "russia"],
            "region": ["Halle", "Halle", "Jiangsu", "Anhui", "X"],
            "name_ru": ["Dessau", "Roßlau", "Suzhou", "Tunxi", "Город"],
            "pop": [93_927.0, 16_449.0, 474_000.0, 50_000.0, 12_000.0],
            "pop_year": [1956, 1956, 1953, 1953, 1959],
            "geonameid": [11.0, 2.0, 32.0, 4.0, np.nan],
            "gn_name": ["Dessau", "Roßlau", "Jiuquan", "Tunxi", np.nan],
            "gn_population": [0.0, 13_000.0, 428_000.0, 4_000.0, np.nan],
            "feature_code": ["PPL", "PPL", "PPLA2", "PPL", np.nan],
            "admin1": ["13", "14", "15", "01", np.nan],
            "lat": [52.81, 51.88, 39.74, 29.71, np.nan],
            "lon": [11.48, 12.24, 98.52, 118.31, np.nan],
            "n_candidates": [2, 1, 1, 1, 0],
            "match_method": ["exact, ranked", *["exact, unique"] * 3, "unmatched"],
        }
    )
    reviewed = pd.DataFrame(
        {
            "republic": ["china", "east germany"],
            "name": ["Tunxi", "Dessau"],
            "geonameid": [4, 12],  # Dessau's note is for another place than the one matched
            "explanation": ["a district, without a population", "the town"],
        }
    )
    out = population_check(places, reviewed)
    assert list(out["name_ru"]) == ["Tunxi", "Dessau"]  # by country, then population
    assert list(out["check"]) == [
        "GeoNames population under a tenth of pop",
        "GeoNames population 0",
    ]
    assert list(out["explanation"]) == ["a district, without a population", ""]
